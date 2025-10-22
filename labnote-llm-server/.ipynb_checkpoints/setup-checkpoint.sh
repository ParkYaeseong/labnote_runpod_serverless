#!/bin/bash
# Vessl.ai Service 환경에 최적화된 AI 백엔드 환경 설정 스크립트
# 최초 1회만 전체 설치를 수행하고, 이후에는 영속성 볼륨을 통해 빠르게 시작합니다.
set -e

# --- 1. 영속성 볼륨 설정 및 설치 완료 확인 ---
# Vessl 서비스 설정의 Mount Path와 일치해야 합니다.
PERSISTENT_DIR="/persistent"
# 설치 완료 여부를 확인할 플래그 파일 (버전 관리를 위해 v1 추가)
SETUP_FLAG="${PERSISTENT_DIR}/.setup_complete_v1"

# 영속 볼륨에 모델과 데이터를 저장할 디렉토리 생성
mkdir -p "${PERSISTENT_DIR}/models/hf"
mkdir -p "${PERSISTENT_DIR}/models/gguf"
mkdir -p "${PERSISTENT_DIR}/ollama_models" # Ollama가 모델을 저장할 경로

# 플래그 파일이 존재하면, 무거운 설치 작업을 모두 건너뜁니다.
if [ -f "${SETUP_FLAG}" ]; then
    echo "✅ Setup has already been completed. Skipping installation and downloads."
else
    echo "🚀 Performing first-time setup... This will take a while."
    
    # --- 2. 시스템 및 필수 도구 설치 (최초 1회) ---
    echo ">>> (Step 1/5) Updating package lists and installing prerequisites..."
    apt-get update > /dev/null
    apt-get install -y curl gpg > /dev/null
    pip install -q huggingface_hub[cli]
    echo ">>> Prerequisites are up to date."

    # --- 3. Redis Stack 서버 설치 (최초 1회) ---
    echo ">>> (Step 2/5) Setting up Redis Stack Server..."
    curl -fsSL https://packages.redis.io/gpg | gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/redis.list > /dev/null
    apt-get update > /dev/null
    apt-get install -y redis-stack-server > /dev/null
    echo ">>> Redis installed."
    
    # --- 4. Ollama 설치 및 모든 모델 다운로드 (최초 1회) ---
    echo ">>> (Step 3/5) Setting up Ollama and downloading all models to persistent storage..."
    curl -fsSL https://ollama.com/install.sh | sh
    
    # Ollama가 모델을 영속 볼륨에 저장하도록 환경 변수 설정
    export OLLAMA_MODELS="${PERSISTENT_DIR}/ollama_models"
    
    # 백그라운드에서 Ollama 임시 실행
    ollama serve &
    OLLAMA_PID=$!
    # Ollama 서버가 시작될 시간을 충분히 줍니다.
    sleep 10
    
    echo "    - Pulling base models: nomic-embed-text, mixtral, llama3:70b..."
    ollama pull nomic-embed-text > /dev/null
    ollama pull mixtral > /dev/null
    ollama pull llama3:70b > /dev/null
    echo "    - Base models pulled."

    # DPO 기본 모델 다운로드 (영속 볼륨에)
    DPO_MODEL_PATH="${PERSISTENT_DIR}/models/hf/Llama3-OpenBioLLM-8B"
    echo "    - Downloading DPO base model to ${DPO_MODEL_PATH}..."
    huggingface-cli download aaditya/Llama3-OpenBioLLM-8B --local-dir "${DPO_MODEL_PATH}" --local-dir-use-symlinks False
    echo "    - DPO base model downloaded."

    # 추론용 GGUF 모델 다운로드 (영속 볼륨에)
    GGUF_MODEL_FILE_PATH="${PERSISTENT_DIR}/models/gguf/llama3-openbiollm-8b.Q4_K_M.gguf"
    echo "    - Downloading Inference GGUF model to ${GGUF_MODEL_FILE_PATH}..."
    huggingface-cli download MoMonir/Llama3-OpenBioLLM-8B-GGUF \
        llama3-openbiollm-8b.Q4_K_M.gguf \
        --local-dir "${PERSISTENT_DIR}/models/gguf" --local-dir-use-symlinks False
    echo "    - GGUF model downloaded."
    
    # 임시 Ollama 종료
    kill $OLLAMA_PID
    sleep 5
    
    # --- 5. 설치 완료 플래그 생성 ---
    echo ">>> (Step 4/5) First-time setup complete. Creating flag file."
    touch "${SETUP_FLAG}"
fi

# --- 6. 서비스 시작 (매번 실행) ---
echo ">>> (Step 5/5) Starting core services..."

# Redis가 실행 중이 아니면 백그라운드에서 실행
if ! pgrep -f redis-stack-server > /dev/null; then
    redis-stack-server --daemonize yes
    echo ">>> Redis Stack Server started."
else
    echo ">>> Redis is already running."
fi

# Ollama가 실행 중이 아니면 백그라운드에서 실행 (영속 볼륨 경로 사용)
if ! pgrep -f "ollama serve" > /dev/null; then
    export OLLAMA_MODELS="${PERSISTENT_DIR}/ollama_models"
    export OLLAMA_HOST=0.0.0.0 # 외부 접속 허용
    ollama serve &
    sleep 5 # 서버 초기화 시간
    echo ">>> Ollama server started from persistent storage on 0.0.0.0."
else
    echo ">>> Ollama is already running."
fi

# --- 7. 추론 모델 Ollama에 등록 (매번 확인 후 필요시 실행) ---
INFERENCE_MODEL_NAME="biollama3"
GGUF_MODEL_FILE_PATH="${PERSISTENT_DIR}/models/gguf/llama3-openbiollm-8b.Q4_K_M.gguf"
# 'ollama list'에 모델 이름이 없는 경우에만 새로 생성
if ! ollama list | grep -q "${INFERENCE_MODEL_NAME}"; then
    echo "    - Inference model '${INFERENCE_MODEL_NAME}' not found in Ollama. Registering from GGUF..."
    cat <<EOF > /tmp/Modelfile
FROM ${GGUF_MODEL_FILE_PATH}
TEMPLATE """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{{ .System }}<|eot_id|><|start_header_id|>user<|end_header_id|>

{{ .Prompt }}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
PARAMETER stop "<|eot_id|>"
PARAMETER stop "<|end_of_text|>"
EOF
    ollama create "${INFERENCE_MODEL_NAME}" -f /tmp/Modelfile
    echo ">>> Inference LLM '${INFERENCE_MODEL_NAME}' registered."
else
    echo ">>> Inference LLM '${INFERENCE_MODEL_NAME}' already exists."
fi

# --- 8. Python 의존성 설치 및 .env 파일 생성 ---
echo ">>> Setting up backend environment..."
# Vessl 실행 명령어의 cd 명령어를 고려하여 경로를 고정합니다.
BACKEND_DIR="/root/labnote-ai-backend"

# .env 파일이 없으면 생성
if [ ! -f "${BACKEND_DIR}/.env" ]; then
    echo "    - Creating .env file..."
    cat << EOF > "${BACKEND_DIR}/.env"
# Backend Server Configuration
REDIS_URL="redis://localhost:6379/0"
OLLAMA_BASE_URL="http://127.0.0.1:11434"

# Model Configuration
EMBEDDING_MODEL="nomic-embed-text"
LLM_MODEL="${INFERENCE_MODEL_NAME}"

# DPO Training Configuration
BASE_MODEL_PATH="${PERSISTENT_DIR}/models/hf/Llama3-OpenBioLLM-8B"
NEW_MODEL_NAME="biollama3-v2-dpo"

# DPO Git Repository Configuration (토큰은 Vessl Secret 사용 권장)
DPO_TRAINER_REPO_URL="https://github.com/sblabkribb/labnote-dpo-trainer.git"
DPO_REPO_LOCAL_PATH="${BACKEND_DIR}/labnote-dpo-trainer-data"
GIT_AUTH_TOKEN="YOUR_GITHUB_TOKEN"
EOF
fi

# 의존성 패키지는 매번 빠르게 확인/설치합니다.
pip install -r "${BACKEND_DIR}/requirements.txt" > /dev/null
echo ">>> Python dependencies are up to date."
echo "--- Setup script finished. The application is ready to start. ---"