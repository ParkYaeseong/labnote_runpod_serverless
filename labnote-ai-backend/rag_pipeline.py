import os
import logging
from typing import List, Optional
from dotenv import load_dotenv
import redis

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
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL")
        self.embedding_model = os.getenv("EMBEDDING_MODEL")
        self.index_name = "labnote_index"
        self.docs_directory = "./sop"

        if not all([self.redis_url, self.ollama_base_url, self.embedding_model]):
            raise ValueError("Required environment variables are missing. Check your .env file.")

        self.embeddings = NomicEmbeddings(model=self.embedding_model, base_url=self.ollama_base_url)
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

    def _initialize_vector_store(self) -> Optional[Redis]:
        """
        **개선점**: 최신 langchain-redis의 `schema` 요구사항 변경에 대응하도록 로직을 수정합니다.
        이제 `from_existing_index` 대신, Redis 클라이언트로 직접 인덱스 존재 여부를 확인하는
        더욱 안정적인 방식을 사용합니다.
        """
        try:
            # 먼저 Redis 클라이언트로 인덱스가 존재하는지 직접 확인합니다.
            client = redis.from_url(self.redis_url)
            client.ping() # 연결 확인
            
            # 인덱스 정보를 조회하여 존재 여부를 확인
            client.ft(self.index_name).info()
            
            logging.info(f"Existing Redis index '{self.index_name}' found. Connecting...")
            # 인덱스가 존재하면, from_existing_index를 안전하게 호출합니다.
            return Redis.from_existing_index(
                embedding=self.embeddings,
                index_name=self.index_name,
                redis_url=self.redis_url
            )
            
        except Exception: # 인덱스가 없거나 Redis 연결 실패 시
            logging.warning(f"Index '{self.index_name}' not found or Redis connection failed. Attempting to create a new index.")
            splits = self._load_and_split_documents()
            
            if not splits:
                logging.error(f"Cannot create index because no documents were found.")
                return None

            logging.info("Creating new index and embedding documents...")
            vector_store = Redis.from_documents(
                documents=splits,
                embedding=self.embeddings,
                redis_url=self.redis_url,
                index_name=self.index_name
            )
            logging.info(f"Successfully created and populated new index '{self.index_name}'.")
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

# ⭐️ [수정] 모듈 로드 시 객체가 바로 생성되지 않도록 변경합니다.
# 대신, main.py의 lifespan에서 필요할 때 생성합니다.
rag_pipeline: Optional[RAGPipeline] = None

def get_embeddings():
    """
    초기화된 RAGPipeline 인스턴스에서 임베딩 모델 객체를 반환합니다.
    """
    if rag_pipeline is None or rag_pipeline.embeddings is None:
        raise RuntimeError("RAG pipeline or embeddings not initialized.")
    return rag_pipeline.embeddings    
