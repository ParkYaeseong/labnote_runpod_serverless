## ⚙️ RunPod Serverless 베이스 이미지

RunPod Serverless에서 LabNote 백엔드를 실행할 때 사용하는 베이스 이미지는 이 디렉터리의 `Dockerfile.base`와 루트의 `build_and_push.sh`로 관리합니다.

1. **이미지 빌드/푸시**
   - `./build_and_push.sh <TAG>` 실행 시 Step 1에서 `Dockerfile.base`를 기반으로 `mimikyou0607/labnote-ai-base:<TAG>`와 `:latest`를 빌드·푸시합니다.
   - 베이스 이미지는 Redis Stack, Ollama, Python 가상환경(필수 패키지), 모델 캐시 경로 등을 미리 포함하므로 서버리스 워커는 코드만 내려받아 바로 실행할 수 있습니다.

2. **구성 요소**
   - **Redis Stack**: `/opt/redis-stack`에 설치되며, `start.sh`가 동일 경로의 설정 파일을 사용해 기동합니다.
   - **Ollama**: 최신 릴리스를 수동 설치하여 `/usr/local/bin/ollama`로 배치하고, 모델 라이브러리는 `/usr/local/lib/ollama`에 포함됩니다.
   - **Python 가상환경**: `/opt/venv`에 구축되며, `labnote-ai-backend/requirements.txt`를 미리 설치해 런타임 의존성을 충족합니다.
   - **GPU 지원 기반 이미지**: `runpod/pytorch:*` 이미지를 상속해 CUDA/NVIDIA 드라이버가 사전 구성되어 있습니다.

3. **사용 패턴**
   - Step 2에서 생성되는 최종 앱 이미지(`labnote-ai-app`)는 베이스 이미지를 FROM으로 사용하며, 최신 애플리케이션 코드를 클론한 뒤 `start.sh`로 서비스를 구동합니다.
   - 베이스 이미지를 최신 상태로 유지해야 할 경우(새 모델 추가, 시스템 패키지 업데이트 등) Step 1을 재실행한 뒤 Step 2를 이어서 수행합니다.

> 로컬에서 실험하고 싶다면 아래 "🏁 시작하기" 절의 스크립트를 사용하면 됩니다. 다만 RunPod Serverless 배포만 필요하다면 `build_and_push.sh`만으로 환경이 준비됩니다.

# Labnote LLM Server

## 📝 개요

**Labnote LLM Server**는 연구 및 개발 환경을 위한 강력한 LLM(거대 언어 모델) 백엔드 시스템입니다. Ollama를 통해 최신 오픈소스 LLM을 손쉽게 로컬에서 구동하고, Redis를 벡터 데이터베이스로 활용하여 RAG(Retrieval-Augmented Generation) 파이프라인을 구축할 수 있습니다.

또한, DPO(Direct Preference Optimization) 학습 파이프라인을 지원하여 특정 도메인에 맞는 모델을 직접 튜닝하고, 자동화된 스크립트를 통해 손쉽게 배포할 수 있는 환경을 제공합니다.

## 🚀 주요 특징

  * **로컬 LLM 구동**: `Ollama`를 사용하여 Llama3, Mixtral 등 다양한 최신 LLM을 로컬 환경에서 직접 실행합니다.
  * **고성능 벡터 DB**: `Redis Stack`을 벡터 데이터베이스로 활용하여 대규모 문서 임베딩 및 빠른 유사도 검색을 지원합니다.
  * **모델 튜닝 및 배포 자동화**: DPO 학습을 위한 환경이 구성되어 있으며, 학습된 모델을 GGUF 형식으로 변환하고 Ollama에 등록하는 과정을 `deploy_model.sh` 스크립트로 자동화합니다.
  * **간편한 환경 구축**: `setup.sh` 스크립트 하나로 시스템 의존성, 모델 다운로드, 환경 설정까지 한 번에 완료할 수 있습니다.
  * **컨테이너 기반 개발 환경**: `docker-compose.yml`을 통해 Ollama와 Redis를 포함한 전체 개발 환경을 컨테이너로 손쉽게 관리할 수 있습니다.
  * **유연한 모델 관리**: `llama3.1:8b`를 기본 모델로 사용하며, `mixtral`, `llama3.1:70b`, `gpt-oss:120b` 등 추가적인 모델을 손쉽게 다운로드하고 사용할 수 있습니다.

## 🛠️ 최근 업데이트 (2025-10-14)

- **기본 모델 전환**: 추론 기본값을 `llama3.1:8b`로 교체하여 범용성과 명령 순응도를 강화했습니다.
- **설치 스크립트 조정**: `setup.sh`는 이제 Ollama에서 `llama3.1:8b`를 직접 pull 하며, Hugging Face 기반 가중치는 수동 배치를 전제로 안내합니다.
- **DPO 산출물 명명 변경**: DPO 파이프라인에서 생성되는 모델은 `llama3.1-8b-dpo-v1` 이름으로 등록됩니다.
- **문서 및 설정 갱신**: `.env` 예시, 배포 스크립트, VS Code 연동 가이드가 새 모델 이름을 반영하도록 정리되었습니다.

## 📊 시스템 아키텍처

아래 다이어그램은 Labnote LLM Server의 전체적인 구조와 구성 요소 간의 상호작용을 보여줍니다.

```mermaid
graph TD
    subgraph "Client Application"
        A[FastAPI Backend]
    end

    subgraph "Core Services (Docker / Local)"
        B[Ollama Server]
        C[Redis Stack]
    end

    subgraph "Language Models"
        D[Inference LLM: llama3.1:8b]
        E[Embedding Model: nomic-embed-text]
        F[Additional LLMs: mixtral, llama3.1:70b, gpt-oss:120b]
    end

    subgraph "Model Training & Deployment"
        G[DPO Base Model]
        H(deploy_model.sh)
        I[New DPO Model]
    end

    A -- "LLM Inference" --> B
    A -- "Vector Store" --> C
    B -- "Serves" --> D
    B -- "Serves" --> E
    B -- "Serves" --> F

    G -- "Fine-tuning" --> H
    H -- "Creates" --> I
    I -- "Registers to" --> B

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    style C fill:#ccf,stroke:#333,stroke-width:2px
```

## 🏁 시작하기

> RunPod Serverless를 사용하는 경우 이 절은 로컬 개발/디버깅 목적에만 필요합니다. 배포만 진행한다면 `build_and_push.sh` Step 1만 실행하면 됩니다.

### 사전 요구사항

  * Linux 기반 운영체제 (Ubuntu 권장)
  * NVIDIA GPU 및 NVIDIA Container Toolkit (GPU 가속을 사용하는 경우)
  * Python 3.8 이상
  * `curl`, `gpg` 등 기본적인 커맨드라인 도구

### 1\. 자동 설치 (`setup.sh` 사용)

가장 간편한 방법은 제공된 `setup.sh` 스크립트를 실행하는 것입니다. 이 스크립트는 다음 작업을 자동으로 수행합니다:

1.  시스템 패키지 업데이트 및 필수 도구 설치
2.  Redis Stack 서버 설치 및 실행
3.  Ollama 설치 및 `nomic-embed-text` 임베딩 모델 다운로드
4.  추론 및 보조 모델(`llama3.1:8b`, `mixtral`, `llama3.1:70b`, `gpt-oss:120b`) Pull
5.  Meta Llama 3.1 Instruct HF 체크포인트를 둘 디렉터리 생성(수동 배치를 안내)
6.  `.env` 파일 생성 및 Python 의존성 설치 (`requirements.txt` 기반)

<!-- end list -->

```bash
chmod +x setup.sh
./setup.sh
```

### 2\. Docker를 이용한 설치 (`docker-compose.yml` 사용)

핵심 서비스인 Ollama와 Redis만 빠르게 실행하고 싶다면 Docker Compose를 사용할 수 있습니다. 이 방법은 로컬 시스템을 깔끔하게 유지하면서 개발 환경을 구성할 때 유용합니다.

1.  **Docker 및 Docker Compose 설치**: 시스템에 Docker와 Docker Compose가 설치되어 있는지 확인합니다.

2.  **`docker-compose.yml` 설정 확인**:

      * `ollama_data`, `redis_data` 볼륨을 통해 데이터가 영구적으로 저장됩니다.
      * GPU를 사용하려면 `docker-compose.yml` 파일 내의 `deploy` 섹션 주석을 해제하세요.

3.  **서비스 실행**:

    ```bash
    docker-compose up -d
    ```

      * **Ollama**: `http://localhost:11434` 에서 실행됩니다.
      * **Redis Insight**: `http://localhost:8001` 에서 데이터베이스 GUI에 접근할 수 있습니다.

## 🛠️ 사용법

### FastAPI 백엔드 서버 실행

`setup.sh`를 통해 모든 설정이 완료되었다면, 다음 명령어로 백엔드 서버를 시작할 수 있습니다.

```bash
cd labnote-ai-backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### DPO 학습 파이프라인 실행 (선택 사항)

모델을 직접 튜닝하고 싶다면 다음 스크립트를 실행하세요.

```bash
cd labnote-ai-backend
python scripts/run_dpo_training.py
```

## 📦 모델 관리

### DPO 학습 모델 배포

DPO 학습이 완료된 후, `deploy_model.sh` 스크립트를 사용하여 새로운 모델을 배포할 수 있습니다. 이 스크립트는 다음 과정을 자동화합니다:

1.  `llama.cpp`를 사용하여 학습된 모델을 GGUF 형식으로 변환하고 양자화합니다.
2.  새로운 모델을 위한 `Modelfile`을 동적으로 생성합니다.
3.  Ollama에 새 모델을 등록합니다 (`llama3.1-8b-dpo-v1` 이름으로).
4.  `.env` 파일의 `LLM_MODEL` 변수를 새로 등록된 모델 이름으로 자동 업데이트합니다.

<!-- end list -->

```bash
# 스크립트 실행 전, LLAMA_CPP_PATH 등 내부 변수를 자신의 환경에 맞게 수정하세요.
chmod +x deploy_model.sh
./deploy_model.sh
```

## 📜 주요 스크립트 설명

  * **`setup.sh`**: 전체 백엔드 개발 환경을 처음부터 끝까지 자동으로 구축합니다. 모델 다운로드, 서비스 설치, 환경 설정 등을 모두 포함합니다.
  * **`deploy_model.sh`**: DPO 학습이 완료된 모델을 GGUF로 변환하고, 양자화하여 Ollama에 등록한 뒤, `.env` 파일까지 업데이트하는 배포 자동화 스크립트입니다.
  * **`docker-compose.yml`**: Ollama와 Redis 서비스를 컨테이너 환경에서 실행하고 관리하기 위한 설정 파일입니다.
  * **`requirements.txt`**: FastAPI, LangChain, Ollama, Pydantic 등 백엔드 서버 운영과 DPO 학습에 필요한 모든 Python 라이브러리 목록입니다.

## ⚙️ 환경 설정 (`.env`)

`setup.sh` 스크립트는 프로젝트 루트에 `.env` 파일을 자동으로 생성합니다. 주요 설정은 다음과 같습니다.

```dotenv
# Backend Server Configuration
REDIS_URL="redis://localhost:6379/0"
OLLAMA_BASE_URL="http://127.0.0.1:11434"

# Model Configuration
EMBEDDING_MODEL="nomic-embed-text"
LLM_MODEL="llama3.1:8b"

# DPO Training Configuration
BASE_MODEL_PATH="/persistent/models/hf/Meta-Llama-3.1-8B-Instruct"
NEW_MODEL_NAME="llama3.1-8b-dpo-v1"
```
