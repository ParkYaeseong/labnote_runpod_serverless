#!/bin/bash
# DPO 학습, 모델 배포, FastAPI 서버 실행을 자동화하는 스크립트

set -e # 오류 발생 시 스크립트 즉시 중단

echo "🚀 LabNote AI 전체 파이프라인을 시작합니다."

# .env 파일이 있는지 확인하고 로드합니다.
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ .env 파일을 찾을 수 없습니다. 파이프라인을 중단합니다."
    exit 1
fi

# --- 1. DPO 학습 실행 ---
echo "--- Step 1/4: DPO 모델 학습을 시작합니다 ---"
python labnote-dpo-trainer-data/run_dpo_training.py

# --- 2. 모델 배포 스크립트 실행 ---
echo "--- Step 2/4: 학습된 모델을 Ollama에 배포합니다 ---"
(cd ../labnote-llm-server && sh deploy_model.sh)

# --- 3. 모델 성능 평가 ---
echo "--- Step 3/4: 새로 배포된 모델의 성능을 평가합니다 ---"
export $(grep -v '^#' .env | xargs) # deploy_model.sh에 의해 변경된 .env 파일을 다시 로드
echo ">>> 평가 대상 모델(Model B): $LLM_MODEL"
python scripts/evaluate_model.py --model-b "$LLM_MODEL"

# --- 4. FastAPI 서버 실행 ---
echo "--- Step 4/4: FastAPI 서버를 실행합니다 ---"

# Ollama 서버가 준비될 때까지 대기
echo ">>> Waiting for Ollama server to be ready..."
max_retries=30
retry_count=0
while ! curl -s http://127.0.0.1:11434 > /dev/null; do
    if [ $retry_count -ge $max_retries ]; then
        echo "❌ Ollama server did not start within the expected time. Aborting."
        exit 1
    fi
    echo "    - Ollama not ready yet. Retrying in 5 seconds... ($((retry_count+1))/$max_retries)"
    sleep 5
    retry_count=$((retry_count+1))
done
echo "✅ Ollama server is ready."


# 기존 uvicorn 프로세스 종료
echo ">>> 실행 중인 uvicorn 프로세스를 확인하고 정상적으로 종료합니다."
# uvicorn 프로세스를 찾아서 종료 (host와 port를 기준으로 찾음)
# pgrep의 -f 옵션이 자기 자신을 찾는 것을 방지하기 위해 [u]vicorn 패턴을 사용하고,
# kill -9 대신 정상 종료(SIGTERM) 신호를 보내 어플리케이션이 리소스를 안전하게 해제하도록 합니다.
if pgrep -f "[u]vicorn main:app.*--port 8000" > /dev/null
then
    pgrep -f "[u]vicorn main:app.*--port 8000" | xargs kill
    echo ">>> 기존 uvicorn 프로세스를 정상적으로 종료했습니다. 잠시 대기합니다..."
    sleep 2 # 프로세스가 완전히 종료될 시간을 줍니다.
fi

# nohup으로 백그라운드에서 서버 재시작
echo ">>> uvicorn main:app --host 0.0.0.0 --port 8000"
echo "서버가 백그라운드에서 실행됩니다. 로그는 nohup.out 파일을 확인하세요."
nohup uvicorn main:app --host 0.0.0.0 --port 8000 &

echo "✅ 전체 파이프라인이 완료되었습니다."
