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
    
    echo "    - Pulling base models: nomic-embed-text, mixtral, llama3.1:8b, llama3.1:70b, gpt-oss:120b..."
    ollama pull nomic-embed-text > /dev/null
    ollama pull mixtral > /dev/null
    ollama pull llama3.1:8b > /dev/null
    ollama pull llama3.1:70b > /dev/null
    ollama pull gpt-oss:120b > /dev/null
    echo "    - Base models pulled."

    # --- 4. HF 기반 모델 준비 안내 (필요 시) ---
    echo ">>> (Step 4/5) Preparing directories for optional Hugging Face checkpoints..."
    BASE_MODEL_NAME="Meta-Llama-3.1-8B-Instruct"
    DPO_MODEL_PATH="${PERSISTENT_DIR}/models/hf/${BASE_MODEL_NAME}"
    if [ -d "${DPO_MODEL_PATH}" ]; then
        echo "    - Found existing HF base model at ${DPO_MODEL_PATH}."
    else
        echo "    - ⚠️  HF base model not found at ${DPO_MODEL_PATH}."
        echo "       Meta Llama 3.1 weights require a Hugging Face acceptance token."
        echo "       Please download 'meta-llama/Meta-Llama-3.1-8B-Instruct' manually"
        echo "       and place it in this directory before running the DPO pipeline."
    fi

    # 임시 Ollama 종료
    kill $OLLAMA_PID
    sleep 5
    
    # --- 5. 설치 완료 플래그 생성 ---
    echo ">>> (Step 5/6) First-time setup complete. Creating flag file."
    touch "${SETUP_FLAG}"
fi

# --- 6. 서비스 시작 (매번 실행) ---
echo ">>> (Step 6/6) Starting core services..."

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
INFERENCE_MODEL_NAME="llama3.1:8b"
# 'ollama list'에 모델 이름이 없는 경우에만 다시 pull
if ! ollama list | grep -q "${INFERENCE_MODEL_NAME}"; then
    echo "    - Inference model '${INFERENCE_MODEL_NAME}' not found locally. Pulling from Ollama registry..."
    ollama pull "${INFERENCE_MODEL_NAME}"
    echo ">>> Inference LLM '${INFERENCE_MODEL_NAME}' is now available."
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
BASE_MODEL_PATH="${PERSISTENT_DIR}/models/hf/Meta-Llama-3.1-8B-Instruct"
NEW_MODEL_NAME="llama3.1-8b-dpo-v1"

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
