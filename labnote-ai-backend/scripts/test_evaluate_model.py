import pytest
import asyncio
import json
import sqlite3
import os
from unittest.mock import patch, AsyncMock

# Add script path to sys.path to import from evaluate_model
import sys
# The path should be relative to the project root where pytest is run
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

from evaluate_model import run_evaluation, init_db

# Use the test DB path from the environment, set in conftest.py
TEST_DB_PATH = os.getenv("EVALUATION_DB_PATH", "./test_evaluation_results.db")

@pytest.mark.asyncio
async def test_run_evaluation_pipeline(tmp_path):
    """
    evaluate_model.py의 전체 파이프라인을 테스트합니다.
    - LLM API 호출을 모킹합니다.
    - 임시 파일 시스템(tmp_path)을 사용하여 데이터셋과 로그 파일을 관리합니다.
    - 평가 결과가 DB와 로그 파일에 올바르게 저장되는지 확인합니다.
    """
    # 1. 테스트 환경 설정
    # 임시 평가 데이터셋 파일 생성
    eval_dataset_path = tmp_path / "test_dataset.json"
    eval_dataset_content = [{"prompt": "What is synthetic biology?"}]
    with open(eval_dataset_path, 'w') as f:
        json.dump(eval_dataset_content, f)

    # 임시 로그 파일 경로 설정
    output_log_path = tmp_path / "test_log.json"

    # 2. 외부 의존성 모킹 (LLM API 호출)
    # call_llm_api가 호출될 때마다 미리 정의된 응답을 반환하도록 설정
    async def mock_llm_api_side_effect(system_prompt, user_prompt, model_name):
        if model_name == "model-a":
            return "Response from Model A"
        elif model_name == "model-b":
            return "Response from Model B is better."
        elif model_name == "judge-model":
            # 심판 모델의 응답은 JSON 형식이어야 함
            return json.dumps({
                "winner": "Model B",
                "justification": "Model B provided a more detailed answer."
            })
        return "Unknown model response"

    # 'evaluate_model.call_llm_api'를 모킹 (sys.path 추가로 인해 모듈 이름이 'evaluate_model'이 됨)
    # AsyncMock을 사용하여 비동기 함수를 모킹
    with patch('evaluate_model.call_llm_api', new_callable=AsyncMock) as mock_call_llm_api:
        mock_call_llm_api.side_effect = mock_llm_api_side_effect

        # 3. 테스트 대상 함수 실행
        # DB 초기화
        init_db()
        
        await run_evaluation(
            model_a="model-a",
            model_b="model-b",
            judge_model="judge-model",
            eval_dataset_path=str(eval_dataset_path),
            output_log_path=str(output_log_path)
        )

        # 4. 결과 검증
        # 4.1. 로그 파일이 올바르게 생성되었는지 확인
        assert os.path.exists(output_log_path)
        with open(output_log_path, 'r') as f:
            log_data = json.load(f)
            assert len(log_data) == 1
            assert log_data[0]["prompt"] == "What is synthetic biology?"
            assert log_data[0]["model_a_response"] == "Response from Model A"
            assert log_data[0]["model_b_response"] == "Response from Model B is better."
            assert log_data[0]["evaluation"]["winner"] == "Model B"

        # 4.2. 데이터베이스에 평가 결과가 올바르게 저장되었는지 확인
        assert os.path.exists(TEST_DB_PATH)
        with sqlite3.connect(TEST_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT model_a_name, model_b_name, win_count_b, loss_count_b, tie_count, win_rate_b FROM evaluations")
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == "model-a"
            assert row[1] == "model-b"
            assert row[2] == 1  # win_count_b
            assert row[3] == 0  # loss_count_b
            assert row[4] == 0  # tie_count
            assert row[5] == 100.0  # win_rate_b