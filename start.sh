#!/bin/bash
# 스크립트 실행 중 오류가 발생하면 즉시 중단합니다.
set -e

# --- 1. 진단: 마운트된 저장소 확인 ---
echo "--- [DIAGNOSIS] Verifying storage mounts ---"
echo ">>> Displaying mounted filesystems (df -h):"
df -h
echo "---"
echo ">>> Listing root directory contents (ls -la /):"
ls -la /
echo "---"
echo ">>> Listing /runpod-volume contents (ls -la /runpod-volume):"
ls -la /runpod-volume || echo "    - /runpod-volume does not exist or is empty."
echo "--- [DIAGNOSIS] Verification complete ---"

# 환경 변수 설정
export LABNOTE_BACKEND_URL="http://127.0.0.1:8000"
export OLLAMA_HOST=0.0.0.0
export OLLAMA_BASE_URL="http://127.0.0.1:11434"
export EMBEDDING_MODEL="nomic-embed-text"

# Runpod의 Network Storage 경로를 OLLAMA_MODELS로 지정합니다.
# 이 경로는 Runpod Serverless Endpoint 설정의 Volume Mount Path와 일치해야 합니다. (예: /runpod-volume)
export OLLAMA_MODELS=/runpod-volume/ollama_models

# Redis 서버 연결을 위한 환경 변수 설정
export REDIS_URL="redis://localhost:6379/0"

# 모델 저장 디렉토리 생성
mkdir -p $OLLAMA_MODELS

# Redis 권장 설정: vm.overcommit_memory=1 적용 시도 (권한 부족 시 경고만 출력)
if command -v sysctl >/dev/null 2>&1; then
    current_overcommit=$(sysctl -n vm.overcommit_memory 2>/dev/null || echo "")
    if [ "$current_overcommit" != "1" ] && [ -n "$current_overcommit" ]; then
        if sysctl -w vm.overcommit_memory=1 >/dev/null 2>&1; then
            echo ">>> vm.overcommit_memory set to 1 for Redis stability."
        else
            echo ">>> WARNING: Could not set vm.overcommit_memory=1. Continuing with existing configuration."
        fi
    fi
fi

# --- 3. 핵심 서비스 시작 ---
echo ">>> Starting core services..."

# Redis 서버 시작 (백그라운드)
REDIS_CONF="/opt/redis-stack/etc/redis-stack.conf"
if ! pgrep -f redis-stack-server > /dev/null; then
    # Runpod 환경에서는 로그를 stdout으로 보내는 것이 디버깅에 유리하므로 백그라운드 실행을 사용합니다.
    redis-stack-server "${REDIS_CONF}" &
    echo ">>> Redis Stack Server started."
else
    echo ">>> Redis Stack Server is already running."
fi

# Ollama 서버 시작 (백그라운드)
# OLLAMA_MODELS 환경 변수를 사용하여 영속성 볼륨에 모델을 저장하도록 합니다.
ollama serve &

echo ">>> Waiting for Ollama server to be ready..."
max_retries=30
retry_count=0
while ! curl -s --fail http://127.0.0.1:11434 > /dev/null; do
    if [ $retry_count -ge $max_retries ]; then
        echo "❌ Ollama server did not start within the expected time. Aborting."
        exit 1
    fi
    echo "    - Ollama not ready yet. Retrying in 2 seconds... ($((retry_count+1))/$max_retries)"
    sleep 2
    retry_count=$((retry_count+1))
done
echo "✅ Ollama server is ready."

# --- 4. 필수 모델 확인 및 다운로드 (최초 실행 시) ---
echo ">>> Checking for required models in persistent storage..."

REQUIRED_MODELS=(
    "nomic-embed-text"
    "llama3.1:8b"
    "mixtral"
    "llama3.1:70b"
    "gpt-oss:120b"
)

for model in "${REQUIRED_MODELS[@]}"; do
    if ! ollama list | grep -q "^${model}"; then
        echo "    - Model '${model}' not found. Pulling from registry... (This may take a while on first run)"
        # ollama pull 명령어의 출력을 직접 스트리밍하여 진행 상황을 확인합니다.
        # 실패 시 set -e에 의해 스크립트가 중단됩니다.
        if ! ollama pull "${model}"; then
            echo "❌ Failed to pull model: ${model}. Aborting." >&2
            exit 1
        fi
    else
        echo "    - Model '${model}' already exists."
    fi
done
echo "✅ All required models are available."

# 백엔드 메인 API 서버 실행 (포그라운드)
# 이 프로세스가 컨테이너의 메인 프로세스가 되어 요청을 처리합니다.
echo "Starting LabNote AI Backend server on port 8000 (foreground)..."
cd /app/labnote-ai-backend
# Runpod Serverless 환경에서는 uvicorn을 직접 실행하는 대신, runpod_handler.py를 실행합니다.
python -u runpod_handler.py
