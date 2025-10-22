# syntax=docker/dockerfile:1.4

# 이 파일은 자주 바뀌는 애플리케이션 코드를 빌드하기 위한 파일입니다.
# 사전에 빌드된 베이스 이미지를 기반으로 하므로 빌드 속도가 매우 빠릅니다.

# 1. 미리 빌드해둔 베이스 이미지를 사용합니다.
# 이 베이스 이미지는 OS, Python 패키지, LLM 모델 등 무거운 부분을 모두 포함하고 있습니다.
ARG DOCKER_USERNAME=mimikyou0607
ARG BASE_IMAGE_NAME=labnote-ai-base
ARG BASE_IMAGE_TAG=latest
FROM ${DOCKER_USERNAME}/${BASE_IMAGE_NAME}:${BASE_IMAGE_TAG} AS final

# 작업 디렉토리를 베이스 이미지와 동일하게 설정합니다.
WORKDIR /app

# 4. Git 저장소 복제 및 서브모듈 초기화 (보안 마운트 사용)
# git clone과 submodule 업데이트 모두 인증이 필요하므로, secret을 마운트한 단일 RUN 명령으로 처리합니다.
RUN --mount=type=secret,id=github_token,required=true \
    git config --global url."https://oauth2:$(cat /run/secrets/github_token)@github.com/".insteadOf "https://github.com/" && \
    git clone https://github.com/sblabkribb/labnote-ai-backend.git /app/labnote-ai-backend && \
    cd /app/labnote-ai-backend && \
    git submodule sync --recursive && \
    git submodule update --init --force --recursive

# RunPod 서버리스 런타임 지원 패키지 설치 (베이스 이미지에 없을 가능성 대비)
RUN /opt/venv/bin/pip install --no-cache-dir runpod

# 6. 시작 스크립트 복사 및 실행 권한 부여
COPY start.sh .
RUN chmod +x ./start.sh

# 7. 포트 노출 (FastAPI 백엔드 포트)
EXPOSE 8000

# 8. 컨테이너 시작 명령어 설정
CMD ["./start.sh"]
