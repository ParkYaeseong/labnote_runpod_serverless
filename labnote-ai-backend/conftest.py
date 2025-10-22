import pytest
import os
import sqlite3
from fastapi.testclient import TestClient
from unittest.mock import patch

# main.py를 import하기 전에 환경변수를 설정해야 합니다.
TEST_DB_PATH = "./test_evaluation_results.db"
os.environ["EVALUATION_DB_PATH"] = TEST_DB_PATH

from main import app

@pytest.fixture(scope="session")
def client():
    """FastAPI 테스트 클라이언트 Fixture"""
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown_db():
    """
    각 테스트 함수 실행 전후로 테스트 데이터베이스를 초기화하고 삭제합니다.
    """
    # 테스트 실행 전: 기존 테스트 DB 파일 삭제
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    # main.py의 _init_feedback_db()와 evaluate_model.py의 init_db()가
    # 이 경로에 DB를 생성하도록 유도합니다.
    
    yield # 테스트 실행

    # 테스트 실행 후: 테스트 DB 파일 삭제
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)