import os

# RunPod 환경에서 main 모듈이 로드되기 전에 서버리스 플래그를 설정해
# FastAPI 앱 초기화 시 RAG 파이프라인이 반드시 구성되도록 한다.
os.environ.setdefault("RUNPOD_SERVERLESS", "true")

from typing import Any, Dict

import runpod
from fastapi.testclient import TestClient
from main import app  # FastAPI 앱 객체를 직접 임포트
import rag_pipeline as rag_module # RAG 모듈 임포트

LABNOTE_BACKEND_URL = os.getenv("LABNOTE_BACKEND_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT = int(os.getenv("LABNOTE_RUNPOD_TIMEOUT", "600"))

# --- 서버리스 환경을 위한 전역 초기화 ---
# RunPod 워커가 처음 시작될 때 RAG 파이프라인을 초기화합니다.
# 이 객체는 워커가 살아있는 동안 재사용됩니다.

def _normalize_path(path: str) -> str:
    return path if path.startswith('/') else f'/{path}'
 
# Uvicorn을 별도로 실행할 필요 없이, TestClient가 앱을 직접 로드합니다.
# FastAPI의 lifespan 컨텍스트 매니저가 TestClient에 의해 자동으로 관리됩니다.
client = TestClient(app)


def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    """RunPod 서버리스 핸들러 함수."""
    request_payload: Dict[str, Any] = job.get("input") or {}

    print(f"[RunPod Handler] Incoming payload: {request_payload}")

    method = str(request_payload.get("method", "POST")).upper()
    path = request_payload.get("path")
    body = request_payload.get("body")

    if not path:
        # path가 없는 요청은 명시적으로 에러 처리
        raise ValueError("Request payload must include a 'path' key (e.g., '/api/chat', '/populate_note').")

    normalized_path = _normalize_path(path)

    try:
        if method == "GET":
            response = client.get(normalized_path, params=body or {})
        else:
            response = client.request(method, normalized_path, json=body or {})

        response.raise_for_status()
        return response.json()
    except Exception as exc:
        # TestClient는 HTTP 에러를 직접 발생시키므로 httpx.HTTPStatusError가 필요 없습니다.
        error_detail = getattr(exc, 'detail', str(exc))
        raise RuntimeError(
            f"Error processing request for {method} {normalized_path}: {error_detail}"
        ) from exc


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
