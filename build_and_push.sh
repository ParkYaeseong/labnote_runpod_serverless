#!/bin/bash
# 이 스크립트는 베이스 이미지와 최종 애플리케이션 이미지를 빌드하고
# Docker Hub에 푸시하는 과정을 자동화합니다.

# 스크립트 실행 중 오류가 발생하면 즉시 중단합니다.
set -e

# TLS 인증서 번들을 명시적으로 지정하여 사설 루트 인증서가 있는 환경에서도 curl이 실패하지 않도록 합니다.
export CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# --- 변수 설정 ---
# Docker Hub 사용자 이름 또는 조직 이름
DOCKER_USERNAME="mimikyou0607"

# 이미지 이름
BASE_IMAGE_NAME="labnote-ai-base"
APP_IMAGE_NAME="labnote-ai-app"

# 버전 태그 설정
if [ -n "$1" ]; then
    TAG="$1"
else
    TAG=$(date +%Y%m%d-%H%M%S)
    echo "⚠️ 버전 태그가 제공되지 않았습니다. 현재 시간($TAG)을 태그로 사용합니다."
fi

# 최종 이미지 이름 조합
FULL_BASE_IMAGE_NAME="${DOCKER_USERNAME}/${BASE_IMAGE_NAME}:${TAG}"
FULL_APP_IMAGE_NAME="${DOCKER_USERNAME}/${APP_IMAGE_NAME}:${TAG}"
LATEST_APP_IMAGE_NAME="${DOCKER_USERNAME}/${APP_IMAGE_NAME}:latest"

# GitHub 토큰 파일 경로
GITHUB_TOKEN_FILE="github_token.txt"

# --- 사전 확인 ---
# GitHub 토큰 파일이 존재하는지 확인합니다.
if [ ! -f "$GITHUB_TOKEN_FILE" ]; then
    echo "❌ 오류: GitHub 토큰 파일('$GITHUB_TOKEN_FILE')을 찾을 수 없습니다."
    echo "스크립트를 실행하기 전에 토큰 파일을 생성해주세요."
    exit 1
fi

echo "🚀 이미지 빌드 및 푸시를 시작합니다..."

# --- 1. 베이스 이미지 빌드 및 푸시 ---
#echo "--- Step 1/2: 베이스 이미지(${FULL_BASE_IMAGE_NAME}) 빌드 및 푸시 ---"
#DOCKER_BUILDKIT=1 docker buildx build \
#    -f Dockerfile.base \
#    -t "${FULL_BASE_IMAGE_NAME}" \
#    -t "${DOCKER_USERNAME}/${BASE_IMAGE_NAME}:latest" \
#    --push .

# --- 2. 최종 애플리케이션 이미지 빌드 및 푸시 ---
echo "--- Step 2/2: 최종 앱 이미지(${FULL_APP_IMAGE_NAME}) 빌드 및 푸시 ---"
DOCKER_BUILDKIT=1 docker buildx build \
    --secret id=github_token,src=${GITHUB_TOKEN_FILE} \
    --build-arg DOCKER_USERNAME=${DOCKER_USERNAME} \
    --build-arg BASE_IMAGE_NAME=${BASE_IMAGE_NAME} \
    --build-arg BASE_IMAGE_TAG=latest \
    -f Dockerfile \
    -t "${FULL_APP_IMAGE_NAME}" \
    -t "${LATEST_APP_IMAGE_NAME}" \
    --push .

echo "✅ 모든 이미지가 성공적으로 빌드 및 푸시되었습니다!"