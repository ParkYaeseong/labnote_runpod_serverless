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
    echo ">>> GPU Short Summary"
    nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu --format=csv,noheader,nounits || true
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
# Ollama 엔진 라이브러리는 기본값을 강제하지 않고 자동 탐지에 맡깁니다.
# 외부에서 OLLAMA_LLM_LIBRARY가 지정된 경우에만 그대로 사용합니다.
if [ -n "${OLLAMA_LLM_LIBRARY:-}" ]; then
    export OLLAMA_LLM_LIBRARY
else
    echo ">>> OLLAMA_LLM_LIBRARY not set; using autodetect."
    unset OLLAMA_LLM_LIBRARY || true
fi
export OLLAMA_FLASH_ATTENTION="${OLLAMA_FLASH_ATTENTION:-true}"
export OLLAMA_MAX_LOADED_MODELS="${OLLAMA_MAX_LOADED_MODELS:-2}"
export OLLAMA_KEEP_ALIVE="${OLLAMA_KEEP_ALIVE:-5m}"
export NVIDIA_DRIVER_CAPABILITIES="${NVIDIA_DRIVER_CAPABILITIES:-compute,utility}"
export LD_LIBRARY_PATH="/usr/local/cuda/lib64:/usr/local/cuda/lib:/usr/lib/x86_64-linux-gnu:/usr/lib/ollama:/usr/lib/ollama/cuda_v12:/usr/lib/ollama/cuda_v13:${LD_LIBRARY_PATH}"
export OLLAMA_ACCELERATE="${OLLAMA_ACCELERATE:-1}"

# GPU 디버깅/로깅 설정
export OLLAMA_DEBUG=1
export OLLAMA_LOG_LEVEL="${OLLAMA_LOG_LEVEL:-debug}"
export GGML_LOG_LEVEL="${GGML_LOG_LEVEL:-debug}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

# Runpod의 Network Storage 경로를 OLLAMA_MODELS로 지정합니다.
# 이 경로는 Runpod Serverless Endpoint 설정의 Volume Mount Path와 일치해야 합니다. (예: /runpod-volume)
export OLLAMA_MODELS=/runpod-volume/ollama_models
export OLLAMA_LIBRARY_PATH="/usr/lib/ollama"

# --- 2. 추가 진단: 환경/경로/라이브러리 ---
echo ">>> [DIAGNOSIS] Environment summary (selected)"
echo "OLLAMA_USE_GPU=${OLLAMA_USE_GPU}"
echo "OLLAMA_LLM_LIBRARY=${OLLAMA_LLM_LIBRARY}"
echo "OLLAMA_NUM_GPU=${OLLAMA_NUM_GPU}"
echo "OLLAMA_GPU_DEVICE=${OLLAMA_GPU_DEVICE}"
echo "OLLAMA_MODELS=${OLLAMA_MODELS}"
echo "OLLAMA_LIBRARY_PATH=${OLLAMA_LIBRARY_PATH}"
echo "OLLAMA_LOG_LEVEL=${OLLAMA_LOG_LEVEL}"
echo "GGML_LOG_LEVEL=${GGML_LOG_LEVEL}"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES}"
echo "LD_LIBRARY_PATH=${LD_LIBRARY_PATH}"
echo ">>> which/versions"
which ollama || true
ollama --version || true
python3 -V || true
python3 - <<'PY' || true
import torch, json, os
print('[PyTorch]', torch.__version__, 'cuda_is_available=', torch.cuda.is_available())
if torch.cuda.is_available():
    print('cuda_version=', torch.version.cuda)
    print('device_name=', torch.cuda.get_device_name(0))
PY
echo ">>> List CUDA/Ollama libs"
ls -la /usr/lib/ollama 2>/dev/null || true
ls -la /usr/lib/ollama/cuda_* 2>/dev/null || true
command -v ldconfig >/dev/null 2>&1 && ldconfig -p | grep -Ei "(cublas|cuda|nvrtc|ggml)" || true

# Redis 서버 연결을 위한 환경 변수 설정
export REDIS_URL="redis://localhost:6379/0"

REDIS_DATA_DIR="/runpod-volume/redis-data"
DEFAULT_REDIS_DIR="/var/lib/redis-stack"
mkdir -p "${REDIS_DATA_DIR}"

# Redis 기본 데이터 디렉터리를 영속 스토리지에 바인딩합니다.
if [ ! -L "${DEFAULT_REDIS_DIR}" ]; then
    if [ -d "${DEFAULT_REDIS_DIR}" ] && [ "$(ls -A "${DEFAULT_REDIS_DIR}")" ]; then
        echo ">>> Migrating existing Redis data into persistent storage."
        cp -a "${DEFAULT_REDIS_DIR}/." "${REDIS_DATA_DIR}/"
    fi
    rm -rf "${DEFAULT_REDIS_DIR}"
    ln -s "${REDIS_DATA_DIR}" "${DEFAULT_REDIS_DIR}"
    echo ">>> Redis data directory bound to ${REDIS_DATA_DIR}."
else
    echo ">>> Redis data directory already linked to persistent storage."
fi

if [ -f "${DEFAULT_REDIS_DIR}/dump.rdb" ]; then
    echo ">>> Detected existing Redis snapshot at ${DEFAULT_REDIS_DIR}/dump.rdb."
else
    echo ">>> No Redis snapshot found; index will be created on first use."
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
OLLAMA_SERVE_LOG="/tmp/ollama.log"
rm -f "${OLLAMA_SERVE_LOG}" || true
echo ">>> Starting Ollama server (logging to ${OLLAMA_SERVE_LOG})"
(
  set -o pipefail
  ollama serve 2>&1 | sed -u 's/^/[ollama] /'
) >> "${OLLAMA_SERVE_LOG}" &

wait_for_http "http://127.0.0.1:11434" "Ollama server"

# Ollama 초기 로그 요약 및 GPU 탐지 결과 표시
echo ">>> Ollama initial log (last 80 lines)"
tail -n 80 "${OLLAMA_SERVE_LOG}" 2>/dev/null || true
echo ">>> Ollama compute summary from logs"
grep -E "(inference compute|entering low vram mode|cuda|cublas)" "${OLLAMA_SERVE_LOG}" | tail -n 40 || true

echo ">>> GPU state after Ollama start"
nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu --format=csv,noheader,nounits || true

# 만약 GPU 라이브러리가 사용자 요청으로 스킵되었거나 총 VRAM=0B로 감지되면
# 1회에 한해 OLLAMA_LLM_LIBRARY/FLASH_ATTENTION을 초기화하고 재시작을 시도합니다.
if grep -qE "skipping available library at users request|total vram\"=\"0 B\"" "${OLLAMA_SERVE_LOG}"; then
    echo ">>> WARNING: Ollama logs indicate GPU libs skipped or total VRAM=0B. Attempting one-time remediation..."
    pkill -f "ollama serve" || true
    unset OLLAMA_LLM_LIBRARY || true
    export OLLAMA_FLASH_ATTENTION=false
    echo ">>> Relaunching Ollama with autodetect (FLASH_ATTENTION=false)"
    (
      set -o pipefail
      ollama serve 2>&1 | sed -u 's/^/[ollama] /'
    ) >> "${OLLAMA_SERVE_LOG}" &
    wait_for_http "http://127.0.0.1:11434" "Ollama server"
    echo ">>> Ollama compute summary after remediation"
    tail -n 80 "${OLLAMA_SERVE_LOG}" 2>/dev/null | grep -E "(inference compute|entering low vram mode|cuda|cublas)" | tail -n 40 || true
    echo ">>> GPU state after remediation"
    nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu --format=csv,noheader,nounits || true
fi

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
# 진단: 설치된 모델 목록과 API 태그 출력
echo ">>> Installed Ollama models (CLI)"
ollama list || true
echo ">>> Installed Ollama models (REST)"
curl -s http://127.0.0.1:11434/api/tags || true

# 선택적 GPU 셀프 테스트 (ENABLE_GPU_SELFTEST=1일 때만)
if [ "${ENABLE_GPU_SELFTEST:-0}" = "1" ]; then
    echo ">>> Running optional GPU self-test (short generation)"
    echo ">>> GPU state (before):"
    nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu --format=csv,noheader,nounits || true
    echo ">>> Generating 16 tokens with llama3.1:8b"
    curl -s -H "Content-Type: application/json" \
      -d '{"model":"llama3.1:8b","prompt":"hello","options":{"num_predict":16}}' \
      http://127.0.0.1:11434/api/generate | head -c 400 || true
    echo
    echo ">>> GPU state (after):"
    nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu --format=csv,noheader,nounits || true
fi

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

if [ "${FORCE_RAG_REINDEX:-0}" = "1" ]; then
    echo ">>> FORCE_RAG_REINDEX=1 detected. Rebuilding Redis vector index..."
    REINDEX_ARGS=()
    if [ "${FORCE_RAG_KEEP_DOCUMENTS:-0}" = "1" ]; then
        REINDEX_ARGS+=(--keep-documents)
    fi
    if ! /opt/venv/bin/python /app/labnote-ai-backend/scripts/rebuild_rag_index.py "${REINDEX_ARGS[@]}"; then
        echo "❌ RAG index rebuild failed. Aborting startup." >&2
        exit 1
    fi
fi

# 백엔드 메인 API 서버 실행 (포그라운드)
# 이 프로세스가 컨테이너의 메인 프로세스가 되어 요청을 처리합니다.
echo "Starting LabNote AI Backend server on port 8000 (foreground)..."
cd /app/labnote-ai-backend

backup_redis_snapshot() {
    echo ">>> Requesting Redis to persist in-memory data to disk..."
    if redis-cli SAVE >/dev/null 2>&1; then
        echo ">>> Redis snapshot saved under ${DEFAULT_REDIS_DIR}/dump.rdb."
    else
        echo ">>> WARNING: redis-cli SAVE failed; snapshot may be outdated."
    fi
}

trap backup_redis_snapshot EXIT

# Runpod Serverless 환경에서는 uvicorn을 직접 실행하는 대신, runpod_handler.py를 실행합니다.
if [ "${LABNOTE_HTTP:-0}" = "1" ]; then
    echo ">>> LABNOTE_HTTP=1 detected. Starting FastAPI via uvicorn on :8000"
    exec /opt/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
else
    python -u runpod_handler.py
fi
