import subprocess
import time
import httpx
import runpod

# FastAPI 서버를 백그라운드에서 실행
subprocess.Popen(["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"])

# 서버가 시작될 때까지 잠시 대기
time.sleep(10)

client = httpx.AsyncClient()

def handler(job):
    """
    RunPod 서버리스 핸들러 함수.
    job['input']에는 API 요청에 대한 모든 정보가 포함됩니다.
    """
    # RunPod에서 받은 요청 페이로드를 추출합니다.
    request_payload = job['input']

    # FastAPI 애플리케이션의 해당 엔드포인트로 요청을 전달합니다.
    # 여기서는 '/v1/chat/completions'를 예시로 사용합니다.
    # 실제 운영 시에는 job input에 따라 엔드포인트를 동적으로 결정해야 할 수 있습니다.
    response = httpx.post("http://127.0.0.1:8000/v1/chat/completions", json=request_payload, timeout=600)

    # FastAPI 서버의 응답을 그대로 반환합니다.
    return response.json()


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
