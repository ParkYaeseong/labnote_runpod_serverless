import json
import os
import logging
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional, Union
from dotenv import load_dotenv
import redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError, ResponseError as RedisResponseError

from langchain_community.vectorstores.redis import Redis
from langchain_community.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

class NomicEmbeddings(OllamaEmbeddings):
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        prefixed_texts = [f"search_document: {text}" for text in texts]
        return super().embed_documents(prefixed_texts)

    def embed_query(self, text: str) -> List[float]:
        prefixed_text = f"search_query: {text}"
        return super().embed_query(prefixed_text)

class RAGPipeline:
    def __init__(self, *, auto_initialize: bool = True):
        self.redis_url = os.getenv("REDIS_URL")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL")
        self.embedding_model = os.getenv("EMBEDDING_MODEL")
        self.index_name = "labnote_index"
        self.docs_directory = "./sop"
        schema_path = os.getenv("REDIS_SCHEMA_PATH", "/runpod-volume/redis-data/labnote_index_schema.json")
        self.schema_path = Path(schema_path)
        self._cached_schema: Optional[Dict] = self._load_schema_from_disk()

        if not all([self.redis_url, self.ollama_base_url, self.embedding_model]):
            raise ValueError("Required environment variables are missing. Check your .env file.")
        self.embeddings = NomicEmbeddings(model=self.embedding_model, base_url=self.ollama_base_url)
        self.vector_store: Optional[Redis] = None
        if auto_initialize:
            self.vector_store = self._initialize_vector_store()

    def _load_and_split_documents(self) -> List[Document]:
        logging.info(f"Loading documents from '{self.docs_directory}'...")
        loader = DirectoryLoader(
            self.docs_directory, glob="**/*.md", loader_cls=UnstructuredMarkdownLoader,
            show_progress=True, use_multithreading=True
        )
        documents = loader.load()
        if not documents:
            logging.warning(f"No Markdown documents (.md) found in '{self.docs_directory}'.")
            return []

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
        splits = text_splitter.split_documents(documents)
        logging.info(f"Loaded and split {len(documents)} documents into {len(splits)} chunks.")
        return splits

    def _load_schema_from_disk(self) -> Optional[Dict]:
        if not self.schema_path.exists():
            return None
        try:
            with self.schema_path.open("r", encoding="utf-8") as handle:
                schema = json.load(handle)
            logging.info("Loaded Redis schema cache from %s.", self.schema_path)
            return schema
        except Exception as exc:  # pylint: disable=broad-except
            logging.warning("Failed to read cached Redis schema at %s: %s", self.schema_path, exc)
            return None

    def _save_schema_to_disk(self, schema: Dict) -> None:
        try:
            self.schema_path.parent.mkdir(parents=True, exist_ok=True)
            with self.schema_path.open("w", encoding="utf-8") as handle:
                json.dump(schema, handle)
            logging.info("Persisted Redis schema definition to %s.", self.schema_path)
        except Exception as exc:  # pylint: disable=broad-except
            logging.warning("Could not persist Redis schema to %s: %s", self.schema_path, exc)

    @staticmethod
    def _decode_scalar(value):
        if isinstance(value, bytes):
            try:
                return value.decode("utf-8")
            except UnicodeDecodeError:
                return value.decode("utf-8", errors="ignore")
        return value

    @classmethod
    def _coerce_value(cls, value):
        if isinstance(value, dict):
            return {cls._decode_scalar(k): cls._coerce_value(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            if all(isinstance(item, (list, tuple)) and len(item) == 2 for item in value):
                return {
                    cls._decode_scalar(k): cls._coerce_value(v) for k, v in value  # type: ignore
                }
            return [cls._coerce_value(item) for item in value]  # type: ignore
        return cls._decode_scalar(value)

    @classmethod
    def _coerce_attribute(cls, attr) -> Dict:
        if isinstance(attr, dict):
            return {cls._decode_scalar(k): cls._coerce_value(v) for k, v in attr.items()}
        if isinstance(attr, (list, tuple)):
            if all(isinstance(item, (list, tuple)) and len(item) == 2 for item in attr):
                pairs = attr
            else:
                items = list(attr)
                pairs = [
                    (items[i], items[i + 1]) for i in range(0, len(items) - 1, 2)
                    if items[i] is not None
                ]
            coerced = {}
            for key, value in pairs:  # type: ignore
                coerced_key = cls._decode_scalar(key)
                if coerced_key is None:
                    continue
                coerced[coerced_key] = cls._coerce_value(value)
            return coerced
        return {}

    @staticmethod
    def _schema_from_index_info(index_name: str, info: Dict) -> Optional[Dict]:
        attributes = info.get("attributes") or info.get("Attributes")
        if not attributes:
            return None

        fields: List[Dict] = []
        normalized_attributes: List[Dict] = []
        for attr in attributes:
            normalized = RAGPipeline._coerce_attribute(attr)
            if normalized:
                normalized_attributes.append(normalized)

        if not normalized_attributes:
            return None

        for attr in normalized_attributes:
            attr_type = (attr.get("type") or attr.get("TYPE") or "").upper()
            name = attr.get("attribute") or attr.get("ATTRIBUTE") or attr.get("identifier")
            if not name:
                continue

            if attr_type == "TEXT":
                fields.append({"name": name, "type": "TEXT"})
            elif attr_type == "TAG":
                tag_schema = {"name": name, "type": "TAG"}
                separator = attr.get("SEPARATOR") or attr.get("separator")
                if separator:
                    tag_schema["separator"] = separator
                fields.append(tag_schema)
            elif attr_type == "VECTOR":
                vector_schema: Dict[str, object] = {
                    "name": name,
                    "type": "VECTOR",
                    "algorithm": attr.get("algorithm") or attr.get("ALGORITHM") or "HNSW",
                    "distance_metric": attr.get("distance_metric")
                    or attr.get("DISTANCE_METRIC")
                    or "COSINE",
                }
                dims = attr.get("dims") or attr.get("DIM")
                if dims is not None:
                    vector_schema["dims"] = int(dims)
                datatype = attr.get("datatype") or attr.get("TYPE") or attr.get("data_type")
                if datatype:
                    vector_schema["datatype"] = datatype

                extra_raw = attr.get("attributes") or attr.get("ATTRIBUTES") or {}
                extra = RAGPipeline._coerce_attribute(extra_raw) if extra_raw else {}
                for key, value in extra.items():
                    vector_schema[key.lower()] = value
                fields.append(vector_schema)

        if not fields:
            return None

        prefixes_raw = info.get("prefixes") or info.get("PREFIXES") or ["doc"]
        prefixes_value = RAGPipeline._coerce_value(prefixes_raw)
        if isinstance(prefixes_value, (list, tuple)):
            prefixes = [str(item) for item in prefixes_value]
        else:
            prefixes = [str(prefixes_value)]

        index_options_raw = (
            info.get("index_options")
            or info.get("INDEX_OPTIONS")
            or {}
        )
        index_options = RAGPipeline._coerce_attribute(index_options_raw) if index_options_raw else {}
        if isinstance(prefixes, str):
            prefixes = [prefixes]

        return {
            "index": {
                "name": index_name,
                "prefix": prefixes,
                "storage_type": index_options.get("storage_type", "hash"),
            },
            "fields": fields,
        }

    def _default_schema(self, vector_dimensions: int) -> Dict:
        return {
            "index": {
                "name": self.index_name,
                "prefix": ["doc"],
                "storage_type": "hash",
            },
            "fields": [
                {"name": "content", "type": "TEXT"},
                {"name": "metadata", "type": "TEXT"},
                {
                    "name": "content_vector",
                    "type": "VECTOR",
                    "algorithm": "HNSW",
                    "dims": vector_dimensions,
                    "distance_metric": "COSINE",
                    "datatype": "FLOAT32",
                },
            ],
        }

    def _prepare_schema(self, client: redis.Redis) -> Optional[Dict]:
        if self._cached_schema:
            return self._cached_schema

        try:
            info = client.ft(self.index_name).info()
        except Exception as exc:  # pylint: disable=broad-except
            logging.warning(
                "Unable to fetch Redis index metadata for '%s': %s", self.index_name, exc
            )
            info = None

        schema: Optional[Dict] = None
        if info:
            schema = self._schema_from_index_info(self.index_name, info)
            if schema:
                self._cached_schema = schema
                self._save_schema_to_disk(schema)
                return schema

        try:
            sample_vector = self.embeddings.embed_query("schema probe")
            schema = self._default_schema(len(sample_vector))
            self._cached_schema = schema
            self._save_schema_to_disk(schema)
            logging.info(
                "Falling back to default Redis schema definition (dimension=%s).",
                len(sample_vector),
            )
            return schema
        except Exception as exc:  # pylint: disable=broad-except
            logging.error("Failed to derive embedding dimension for schema: %s", exc)
            return None

    def _initialize_vector_store(self) -> Optional[Redis]:
        """
        Redis에 기존 벡터 인덱스가 존재하면 재사용하고, 없으면 새로 생성합니다.
        """
        try:
            client = redis.from_url(self.redis_url)
            client.ping()
        except (RedisConnectionError, RedisError) as exc:
            logging.error(
                "Redis connection failure while verifying index '%s': %s",
                self.index_name,
                exc,
            )
            raise

        try:
            index_info = client.ft(self.index_name).info()
        except RedisResponseError as exc:
            error_text = str(exc)
            if "Unknown Index name" not in error_text:
                logging.error(
                    "Redis index introspection failed for '%s': %s",
                    self.index_name,
                    error_text,
                )
                raise
            logging.warning(
                "Redis index '%s' is missing; will rebuild from SOP documents. Reason: %s",
                self.index_name,
                error_text,
            )
            return self._create_index(client)

        return self._connect_existing_index(client, index_info)

    def _connect_existing_index(self, client: redis.Redis, index_info: Dict) -> Redis:
        schema = self._cached_schema
        if not schema:
            schema = self._schema_from_index_info(self.index_name, index_info)
            if schema:
                self._cached_schema = schema
                self._save_schema_to_disk(schema)

        if not schema:
            schema = self._prepare_schema(client)

        if not schema:
            raise RuntimeError("Unable to determine Redis index schema for reuse.")

        logging.info("Existing Redis index '%s' found. Connecting...", self.index_name)
        try:
            return Redis.from_existing_index(
                embedding=self.embeddings,
                index_name=self.index_name,
                redis_url=self.redis_url,
                schema=schema,
            )
        except TypeError as exc:
            logging.warning(
                "Redis.from_existing_index signature mismatch, retrying with schema dict copy: %s",
                exc,
            )
            return Redis.from_existing_index(
                embedding=self.embeddings,
                index_name=self.index_name,
                redis_url=self.redis_url,
                schema=dict(schema),
            )

    def _create_index(self, client: redis.Redis) -> Redis:
        splits = self._load_and_split_documents()
        if not splits:
            raise RuntimeError("Cannot create index because no documents were found.")

        logging.info("Creating new index and embedding documents...")
        try:
            sample_vector = self.embeddings.embed_query("schema probe (create)")
            schema = self._default_schema(len(sample_vector))
            vector_store = Redis.from_documents(
                documents=splits,
                embedding=self.embeddings,
                redis_url=self.redis_url,
                index_name=self.index_name,
                schema=schema,
            )
            self._cached_schema = schema
            self._save_schema_to_disk(schema)
        except Exception as exc:  # pylint: disable=broad-except
            logging.exception("Failed to create Redis index '%s': %s", self.index_name, exc)
            raise

        logging.info("Successfully created and populated new index '%s'.", self.index_name)
        return vector_store

    def _drop_index(self, client: redis.Redis, *, delete_documents: bool = True) -> None:
        try:
            client.ft(self.index_name).dropindex(delete_documents=delete_documents)
            logging.info(
                "Dropped Redis index '%s' (delete_documents=%s).",
                self.index_name,
                delete_documents,
            )
        except RedisResponseError as exc:
            if "Unknown Index name" in str(exc):
                logging.info(
                    "Redis index '%s' did not exist; nothing to drop.", self.index_name
                )
            else:
                raise
        self._cached_schema = None

    def rebuild_index(self, *, delete_documents: bool = True) -> Redis:
        """
        강제로 기존 인덱스를 삭제하고 SOP 문서로부터 다시 임베딩합니다.
        서버리스 환경에서 SOP가 업데이트된 경우, 별도 잡/포드에서
        본 메서드를 호출해 영속 Redis 볼륨에 최신 임베딩을 반영할 수 있습니다.
        """
        client = redis.from_url(self.redis_url)
        self._drop_index(client, delete_documents=delete_documents)
        vector_store = self._create_index(client)
        self.vector_store = vector_store
        return vector_store

    def retrieve_context(self, query: str, k: int = 5) -> List[Document]:
        if not self.vector_store:
            logging.warning("Vector store is not available. Cannot retrieve context.")
            return []
        
        logging.info(f"Retrieving top {k} documents for query: '{query}'")
        return self.vector_store.similarity_search(query, k=k)

    def format_context_for_prompt(self, documents: List[Document]) -> str:
        if not documents:
            return "No relevant context found in the SOPs."

        context_parts = []
        for doc in documents:
            source = doc.metadata.get('source', 'Unknown').split(os.path.sep)[-1]
            context_parts.append(f"--- CONTEXT FROM: {source} ---\n{doc.page_content}")
        return "\n\n".join(context_parts)


class NullRAGPipeline:
    """
    Lightweight fallback pipeline used when the real RAG pipeline cannot be
    initialised (e.g. missing environment variables or Redis/Ollama failures).
    It preserves the public interface so that existing call-sites do not need
    additional guards and the application can continue to serve requests with
    degraded functionality instead of crashing.
    """

    def __init__(self, error: Optional[Exception] = None):
        self.vector_store = None
        self.embeddings = None
        self._error = error
        self._warned = False

    def _log_once(self, query: Optional[str] = None) -> None:
        if not self._warned:
            details = f" ({self._error})" if self._error else ""
            logging.warning(
                "RAG pipeline unavailable%s; returning no SOP context%s.",
                details,
                f" for query '{query}'" if query else ""
            )
            self._warned = True

    def retrieve_context(self, query: str, k: int = 5) -> List[Document]:
        self._log_once(query)
        return []

    def format_context_for_prompt(self, documents: List[Document]) -> str:
        self._log_once()
        return "No relevant context found in the SOPs."

rag_pipeline: Optional[Union[RAGPipeline, NullRAGPipeline]] = None
_pipeline_lock: Lock = Lock()

def get_rag_pipeline() -> Union[RAGPipeline, NullRAGPipeline]:
    """
    Lazily initialize the shared RAG pipeline so serverless workers can recover
    from partial startup or missing warmup stages.
    """
    global rag_pipeline
    if rag_pipeline is None:
        with _pipeline_lock:
            if rag_pipeline is None:
                logging.info("Lazy-initializing RAG pipeline on first access.")
                try:
                    rag_pipeline = RAGPipeline()
                except Exception as exc:  # pylint: disable=broad-except
                    logging.exception("Unable to initialise RAG pipeline: %s", exc)
                    rag_pipeline = NullRAGPipeline(exc)
    return rag_pipeline

def get_embeddings():
    """
    초기화된 RAGPipeline 인스턴스에서 임베딩 모델 객체를 반환합니다.
    """
    pipeline = get_rag_pipeline()
    if getattr(pipeline, "embeddings", None) is None:
        raise RuntimeError("RAG pipeline or embeddings not initialized.")
    return pipeline.embeddings    
