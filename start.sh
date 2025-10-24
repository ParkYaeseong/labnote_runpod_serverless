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

if command -v nvidia-smi >/dev/null 2>&1; then
    echo ">>> GPU Diagnostics (nvidia-smi)"
    nvidia-smi
else
    echo ">>> WARNING: nvidia-smi not found. GPU may not be visible inside the container."
fi

# 환경 변수 설정
export LABNOTE_BACKEND_URL="http://127.0.0.1:8000"
export OLLAMA_HOST=0.0.0.0
export OLLAMA_BASE_URL="http://127.0.0.1:11434"
export EMBEDDING_MODEL="nomic-embed-text"

# GPU 가속 설정 (Ollama)
export OLLAMA_USE_GPU=1
export OLLAMA_NUM_GPU="${OLLAMA_NUM_GPU:-1}"
export OLLAMA_GPU_DEVICE="${OLLAMA_GPU_DEVICE:-0}"
export OLLAMA_LLM_LIBRARY="${OLLAMA_LLM_LIBRARY:-cublas}"
export OLLAMA_FLASH_ATTENTION="${OLLAMA_FLASH_ATTENTION:-true}"
export OLLAMA_MAX_LOADED_MODELS="${OLLAMA_MAX_LOADED_MODELS:-2}"
export OLLAMA_KEEP_ALIVE="${OLLAMA_KEEP_ALIVE:-5m}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export NVIDIA_VISIBLE_DEVICES="${NVIDIA_VISIBLE_DEVICES:-all}"
export NVIDIA_DRIVER_CAPABILITIES="${NVIDIA_DRIVER_CAPABILITIES:-compute,utility}"
export LD_LIBRARY_PATH="/usr/local/cuda/lib64:/usr/local/cuda/lib:/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH}"
export OLLAMA_ACCELERATE="${OLLAMA_ACCELERATE:-1}"

# Runpod의 Network Storage 경로를 OLLAMA_MODELS로 지정합니다.
# 이 경로는 Runpod Serverless Endpoint 설정의 Volume Mount Path와 일치해야 합니다. (예: /runpod-volume)
export OLLAMA_MODELS=/runpod-volume/ollama_models

# Redis 서버 연결을 위한 환경 변수 설정
export REDIS_URL="redis://localhost:6379/0"

REDIS_DATA_DIR="/runpod-volume/redis-data"
mkdir -p "${REDIS_DATA_DIR}"
mkdir -p /var/lib/redis-stack

# 기존 Redis 스냅샷이 존재하면 복원합니다.
if [ -f "${REDIS_DATA_DIR}/dump.rdb" ]; then
    echo ">>> Restoring Redis snapshot from persistent storage."
    cp "${REDIS_DATA_DIR}/dump.rdb" /var/lib/redis-stack/dump.rdb
fi

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

# --- 유틸리티 함수 ---
wait_for_redis() {
    local retries=30
    local delay=2
    local attempt=0
    echo ">>> Waiting for Redis to accept connections..."
    while ! redis-cli -u "${REDIS_URL}" PING >/dev/null 2>&1; do
        if [ "${attempt}" -ge "${retries}" ]; then
            echo "❌ Redis did not become ready in time. Aborting." >&2
            exit 1
        fi
        attempt=$((attempt + 1))
        echo "    - Redis not ready yet. Retrying in ${delay}s... (${attempt}/${retries})"
        sleep "${delay}"
    done
    echo "✅ Redis is ready."
}

wait_for_http() {
    local url=$1
    local service_name=$2
    local retries=30
    local delay=2
    local attempt=0
    echo ">>> Waiting for ${service_name} (${url})..."
    while ! curl -s --fail "${url}" >/dev/null; do
        if [ "${attempt}" -ge "${retries}" ]; then
            echo "❌ ${service_name} did not start within the expected time. Aborting." >&2
            exit 1
        fi
        attempt=$((attempt + 1))
        echo "    - ${service_name} not ready yet. Retrying in ${delay} seconds... (${attempt}/${retries})"
        sleep "${delay}"
    done
    echo "✅ ${service_name} is ready."
}

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

wait_for_redis

# Ollama 서버 시작 (백그라운드)
# OLLAMA_MODELS 환경 변수를 사용하여 영속성 볼륨에 모델을 저장하도록 합니다.
ollama serve &

wait_for_http "http://127.0.0.1:11434" "Ollama server"

# --- 4. 필수 모델 확인 및 다운로드 (최초 실행 시) ---
echo ">>> Checking for required models in persistent storage..."

REQUIRED_MODELS=(
    "nomic-embed-text"
    "llama3.1:8b"
    "mixtral"
    "llama3.1:70b"
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

# --- 5. 백엔드 환경 변수 백업 ---
BACKEND_DIR="/app/labnote-ai-backend"
ENV_FILE="${BACKEND_DIR}/.env"
if [ ! -f "${ENV_FILE}" ]; then
    cat <<EOF > "${ENV_FILE}"
REDIS_URL="${REDIS_URL}"
OLLAMA_BASE_URL="${OLLAMA_BASE_URL}"
EMBEDDING_MODEL="${EMBEDDING_MODEL}"
LLM_MODEL="${INFERENCE_MODEL_NAME}"
EOF
    echo ">>> Generated ${ENV_FILE} for server runtime."
else
    echo ">>> Found existing ${ENV_FILE}; keeping current configuration."
fi

# 백엔드 메인 API 서버 실행 (포그라운드)
# 이 프로세스가 컨테이너의 메인 프로세스가 되어 요청을 처리합니다.
echo "Starting LabNote AI Backend server on port 8000 (foreground)..."
cd /app/labnote-ai-backend

backup_redis_snapshot() {
    echo ">>> Saving Redis snapshot to persistent storage..."
    if redis-cli SAVE >/dev/null 2>&1; then
        cp /var/lib/redis-stack/dump.rdb "${REDIS_DATA_DIR}/dump.rdb"
        echo ">>> Redis snapshot saved to ${REDIS_DATA_DIR}/dump.rdb."
    else
        echo ">>> WARNING: redis-cli SAVE failed; snapshot not updated."
    fi
}

trap backup_redis_snapshot EXIT

# Runpod Serverless 환경에서는 uvicorn을 직접 실행하는 대신, runpod_handler.py를 실행합니다.
python -u runpod_handler.py
