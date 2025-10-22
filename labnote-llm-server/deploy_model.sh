#!/bin/bash
# DPO 학습 완료 후 모델 변환, 등록, .env 업데이트를 자동화하는 스크립트

# --- 설정 (필요에 따라 수정) ---
set -e # 오류 발생 시 스크립트 즉시 중단

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}/stubs${PYTHONPATH:+:$PYTHONPATH}"

# llama.cpp 프로젝트 경로는 환경 변수로부터 읽어옵니다.
# 예: export LLAMA_CPP_PATH="/root/llama.cpp"
if [ -z "${LLAMA_CPP_PATH}" ]; then
    echo "ℹ️ LLAMA_CPP_PATH not set, defaulting to /root/llama.cpp"
    LLAMA_CPP_PATH="/root/llama.cpp"
fi

if [ ! -d "${LLAMA_CPP_PATH}" ]; then
    echo "❌ LLAMA_CPP_PATH 디렉터리가 존재하지 않습니다: ${LLAMA_CPP_PATH}"
    exit 1
fi

CONVERT_SCRIPT="${LLAMA_CPP_PATH}/convert-hf-to-gguf.py"
if [ ! -f "${CONVERT_SCRIPT}" ]; then
    ALT_CONVERT_SCRIPT="${LLAMA_CPP_PATH}/convert_hf_to_gguf.py"
    if [ -f "${ALT_CONVERT_SCRIPT}" ]; then
        CONVERT_SCRIPT="${ALT_CONVERT_SCRIPT}"
    else
        echo "❌ GGUF 변환 스크립트를 찾을 수 없습니다:"
        echo "   - ${CONVERT_SCRIPT}"
        echo "   - ${ALT_CONVERT_SCRIPT}"
        echo "   llama.cpp 저장소 최신 버전에서 convert_hf_to_gguf.py 스크립트 위치를 확인해주세요."
        exit 1
    fi
fi

QUANTIZE_BIN="${LLAMA_CPP_PATH}/build/bin/quantize"
if [ ! -x "${QUANTIZE_BIN}" ]; then
    ALT_QUANTIZE_BIN="${LLAMA_CPP_PATH}/build/bin/llama-quantize"
    if [ -x "${ALT_QUANTIZE_BIN}" ]; then
        QUANTIZE_BIN="${ALT_QUANTIZE_BIN}"
    else
        echo "❌ 양자화 바이너리를 찾을 수 없습니다:"
        echo "   - ${QUANTIZE_BIN}"
        echo "   - ${ALT_QUANTIZE_BIN}"
        echo "   llama.cpp에서 빌드가 완료되었는지(cmake --build ...) 확인해주세요."
        exit 1
    fi
fi

# DPO 학습으로 생성된 모델 경로 (필요 시 환경 변수로 재정의 가능)
TRAINED_MODEL_DIR="${TRAINED_MODEL_DIR:-../labnote-ai-backend/llama3.1-8b-dpo-v1}"
if [ ! -d "${TRAINED_MODEL_DIR}" ]; then
    ALT_TRAINED_MODEL_DIR="../llama3.1-8b-dpo-v1"
    if [ -d "${ALT_TRAINED_MODEL_DIR}" ]; then
        TRAINED_MODEL_DIR="${ALT_TRAINED_MODEL_DIR}"
    else
        echo "❌ 학습된 모델 디렉터리를 찾을 수 없습니다:"
        echo "   - ${TRAINED_MODEL_DIR}"
        echo "   - ${ALT_TRAINED_MODEL_DIR}"
        echo "   DPO 학습이 성공적으로 완료되었는지 확인하세요."
        exit 1
    fi
fi

# GGUF로 변환된 모델을 저장할 경로
GGUF_OUTPUT_DIR="./gguf_models"

# Ollama에 등록할 새 모델의 이름
RAW_OLLAMA_MODEL_NAME="${NEW_OLLAMA_MODEL_NAME:-llama3.1-8b-dpo-v1}"
SANITIZED_MODEL_NAME=$(printf '%s' "${RAW_OLLAMA_MODEL_NAME}" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9-' '-' | sed 's/--*/-/g')
SANITIZED_MODEL_NAME="${SANITIZED_MODEL_NAME#-}"
SANITIZED_MODEL_NAME="${SANITIZED_MODEL_NAME%-}"
if [ -z "${SANITIZED_MODEL_NAME}" ]; then
    echo "❌ 유효한 Ollama 모델 이름을 생성하지 못했습니다. NEW_OLLAMA_MODEL_NAME 환경 변수를 확인하세요."
    exit 1
fi
if [ "${RAW_OLLAMA_MODEL_NAME}" != "${SANITIZED_MODEL_NAME}" ]; then
    echo "ℹ️  Ollama 모델 이름을 '${RAW_OLLAMA_MODEL_NAME}' → '${SANITIZED_MODEL_NAME}' 로 정규화했습니다."
fi
NEW_OLLAMA_MODEL_NAME="${SANITIZED_MODEL_NAME}"

# 양자화(Quantization) 방식 (예: Q4_K_M, Q5_K_M 등)
QUANTIZE_METHOD="Q4_K_M"

# --- 스크립트 시작 ---
echo "🚀 DPO 모델 배포 자동화를 시작합니다."

# 1. GGUF 변환 및 양자화
echo "Step 1/4: llama.cpp를 사용하여 모델을 GGUF로 변환 및 양자화합니다..."
mkdir -p "${GGUF_OUTPUT_DIR}"
GGUF_FILE_PATH="${GGUF_OUTPUT_DIR}/llama3.1-8b-instruct.${QUANTIZE_METHOD}.gguf"
GGUF_FILE_PATH_ABS="$(cd "${SCRIPT_DIR}" && readlink -f "${GGUF_FILE_PATH}")"
if [ -z "${GGUF_FILE_PATH_ABS}" ]; then
    echo "❌ GGUF 파일 경로를 확인할 수 없습니다."
    exit 1
fi

# FP16 GGUF로 변환
python3 "${CONVERT_SCRIPT}" "${TRAINED_MODEL_DIR}" \
  --outfile "${GGUF_FILE_PATH}.fp16" \
  --outtype f16

# 지정된 방식으로 양자화
"${QUANTIZE_BIN}" "${GGUF_FILE_PATH}.fp16" "${GGUF_FILE_PATH}" "${QUANTIZE_METHOD}"

echo "✅ GGUF 변환 완료: ${GGUF_FILE_PATH}"

# 2. Modelfile 동적 생성
echo "Step 2/4: 새 모델을 위한 Modelfile을 생성합니다..."
MODLEFILE_PATH="${GGUF_OUTPUT_DIR}/Modelfile"
cat <<EOF > "${MODLEFILE_PATH}"
FROM ${GGUF_FILE_PATH_ABS}
TEMPLATE """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{{ .System }}<|eot_id|><|start_header_id|>user<|end_header_id|>

{{ .Prompt }}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
PARAMETER stop "<|eot_id|>"
PARAMETER stop "<|end_of_text|>"
EOF
echo "✅ Modelfile 생성 완료: ${MODLEFILE_PATH}"

# 3. Ollama에 새 모델 등록
echo "Step 3/4: Ollama에 '${NEW_OLLAMA_MODEL_NAME}' 모델을 생성합니다..."
if ! ollama create "${NEW_OLLAMA_MODEL_NAME}" -f "${MODLEFILE_PATH}"; then
    echo "❌ Ollama 모델 생성에 실패했습니다. 모델 이름 규칙을 확인하거나 Ollama 로그를 확인하세요."
    exit 1
fi
echo "✅ Ollama 모델 등록 완료."

# 4. .env 파일의 LLM_MODEL 업데이트
echo "Step 4/4: .env 파일의 LLM_MODEL을 새 버전으로 업데이트합니다..."
ENV_FILE="../labnote-ai-backend/.env"
if [ -f "$ENV_FILE" ]; then
    # 기존 .env 파일 백업
    cp "$ENV_FILE" "$ENV_FILE.bak"
    # LLM_MODEL 값을 새로운 모델 이름으로 변경 (sed 명령어 활용)
    sed -i -e "s/^LLM_MODEL=.*/LLM_MODEL=${NEW_OLLAMA_MODEL_NAME}/" "$ENV_FILE"
    echo "✅ .env 파일 업데이트 완료. 이전 설정은 .env.bak 파일에 백업되었습니다."
else
    echo "⚠️ 경고: .env 파일을 찾을 수 없어 업데이트하지 못했습니다."
fi

echo "🎉 모든 배포 과정이 성공적으로 완료되었습니다!"
