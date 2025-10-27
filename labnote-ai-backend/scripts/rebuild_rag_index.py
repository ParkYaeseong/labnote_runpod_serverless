import argparse
import logging
import sys

from rag_pipeline import RAGPipeline  # pylint: disable=import-error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild the Redis vector index used for LabNote RAG.\n"
            "This will re-embed all SOP documents and persist the results "
            "to the configured Redis instance (typically backed by RunPod network storage)."
        )
    )
    parser.add_argument(
        "--keep-documents",
        action="store_true",
        help=(
            "Drop the index metadata but keep existing Redis HASH documents. "
            "By default both the index and underlying documents are removed."
        ),
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    args = parse_args()

    try:
        pipeline = RAGPipeline(auto_initialize=False)
        pipeline.rebuild_index(delete_documents=not args.keep_documents)
        logging.info("RAG index rebuild completed successfully.")
    except Exception as exc:  # pylint: disable=broad-except
        logging.exception("RAG index rebuild failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
