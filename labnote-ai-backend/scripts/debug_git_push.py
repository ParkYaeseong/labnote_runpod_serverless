import os
import git
from pathlib import Path
import uuid
import logging
from dotenv import load_dotenv # <-- 이 줄을 추가하세요

# 스크립트가 실행될 때 .env 파일을 로드합니다.
# 스크립트는 scripts/ 안에 있으므로, 부모 디렉토리의 .env 파일을 찾도록 경로를 지정합니다.
dotenv_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=dotenv_path) # <-- 이 줄을 추가하세요

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_git_push():
    """독립적으로 Git Push를 테스트하는 함수"""
    token = os.getenv("GIT_AUTH_TOKEN")
    repo_url = os.getenv("DPO_TRAINER_REPO_URL")
    local_path_str = "./labnote-dpo-trainer-data-debug" # 테스트를 위해 임시 로컬 경로 사용
    local_path = Path(local_path_str)

    logger.info(f"--- Git Push Debug Test ---")

    # 토큰이 None이 아닌지 먼저 확인합니다.
    if not token:
        logger.error("❌ FAILED: GIT_AUTH_TOKEN not found in environment. Please check your .env file.")
        return

    logger.info(f"Attempting to use GIT_AUTH_TOKEN: '{token[:4]}...{token[-4:]}'") # 토큰 일부만 로깅

    if not repo_url:
        logger.error("Error: DPO_TRAINER_REPO_URL is not set.")
        return

    repo_url_with_token = repo_url.replace("https://", f"https://oauth2:{token}@")

    try:
        # 1. 저장소 클론 또는 열기
        if local_path.exists():
            logger.info(f"Existing repo found at '{local_path_str}'. Pulling changes...")
            repo = git.Repo(local_path)
            repo.remotes.origin.pull()
        else:
            logger.info(f"Cloning repo to '{local_path_str}'...")
            repo = git.Repo.clone_from(repo_url_with_token, local_path)

        # 2. 테스트 파일 생성 및 커밋
        data_dir = local_path / "data"
        data_dir.mkdir(exist_ok=True)
        test_file = data_dir / f"test_{uuid.uuid4()}.txt"
        with open(test_file, 'w') as f:
            f.write("This is a debug test.")

        repo.index.add([str(test_file.resolve())])
        repo.index.commit("Debug: Test commit from Vessl.ai server")
        logger.info("Test file committed.")

        # 3. 푸시
        origin = repo.remote(name='origin')
        logger.info("Pushing to remote...")
        origin.push()

        logger.info("✅ SUCCESS: Git push was successful!")

    except git.exc.GitCommandError as e:
        logger.error(f"❌ FAILED: Git command failed!")
        logger.error(f"  - Command: {e.command}")
        logger.error(f"  - Exit Code: {e.status}")
        logger.error(f"  - Stderr: {e.stderr}")
    except Exception as e:
        logger.error(f"❌ FAILED: An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    test_git_push()