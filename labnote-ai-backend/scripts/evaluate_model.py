import os
import json
import asyncio
import argparse
import logging
from typing import List, Dict
from dotenv import load_dotenv
import re
import sqlite3
import datetime

# 프로젝트 루트의 유틸리티를 가져오기 위해 경로 추가
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from llm_utils import call_llm_api

# --- 초기 설정 ---
load_dotenv(dotenv_path='../.env')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 데이터베이스 설정 ---
DB_PATH = os.getenv("EVALUATION_DB_PATH", "evaluation_results.db")

def init_db():
    """SQLite 데이터베이스를 초기화하고 evaluations 테이블을 생성합니다."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                model_a_name TEXT NOT NULL,
                model_b_name TEXT NOT NULL,
                judge_model_name TEXT NOT NULL,
                total_prompts INTEGER NOT NULL,
                win_count_b INTEGER NOT NULL,
                loss_count_b INTEGER NOT NULL,
                tie_count INTEGER NOT NULL,
                error_count INTEGER NOT NULL,
                win_rate_b REAL NOT NULL,
                evaluation_log_path TEXT
            )
        """)
        logger.info(f"Database initialized at '{DB_PATH}'")

def save_evaluation_to_db(summary: Dict):
    """평가 요약 정보를 SQLite 데이터베이스에 저장합니다."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO evaluations VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(summary.values()))
        logger.info(f"Evaluation summary for '{summary['model_b_name']}' saved to database.")

# --- 심판(Judge)을 위한 프롬프트 템플릿 ---
JUDGE_SYSTEM_PROMPT = "You are a fair and impartial AI evaluator. Your task is to compare two AI-generated responses to a user's prompt and determine which one is better. Your evaluation should be based on helpfulness, accuracy, detail, and adherence to the prompt's instructions. Your output MUST be a valid JSON object."

JUDGE_USER_PROMPT_TEMPLATE = """
Please evaluate the two responses from different AI models (Model A and Model B) for the given user prompt.

[USER PROMPT]
{prompt}

[MODEL A RESPONSE]
{response_a}

[MODEL B RESPONSE]
{response_b}

[TASK]
Compare the two responses and decide which one is better. Your decision should be one of "Model A", "Model B", or "Tie". Provide a brief justification for your choice.

Respond with a JSON object in the following format:
{{
  "winner": "Model A" | "Model B" | "Tie",
  "justification": "Your reasoning here."
}}
"""

# --- 핵심 기능 함수 ---

async def get_model_response(prompt: str, model_name: str) -> str:
    """지정된 모델로부터 프롬프트에 대한 응답을 생성합니다."""
    system_prompt = "You are a helpful scientific assistant. Provide a direct and detailed answer to the user's request."
    return await call_llm_api(system_prompt, prompt, model_name)

async def evaluate_pair(prompt: str, response_a: str, response_b: str, judge_model: str) -> Dict:
    """심판 LLM을 사용하여 두 응답 중 어느 것이 더 나은지 평가합니다."""
    judge_prompt = JUDGE_USER_PROMPT_TEMPLATE.format(
        prompt=prompt,
        response_a=response_a,
        response_b=response_b
    )
    
    evaluation_str = await call_llm_api(JUDGE_SYSTEM_PROMPT, judge_prompt, judge_model)
    
    try:
        # LLM 응답에서 JSON 객체만 정확히 추출
        json_match = re.search(r'\{.*\}', evaluation_str, re.DOTALL)
        if not json_match:
            raise json.JSONDecodeError("No JSON object found in the LLM response.", evaluation_str, 0)
        
        evaluation = json.loads(json_match.group(0))
        if "winner" not in evaluation or "justification" not in evaluation:
            raise ValueError("Judge response missing 'winner' or 'justification' key.")
        return evaluation
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse judge's response. Error: {e}. Response: {evaluation_str}")
        return {"winner": "Error", "justification": f"Parsing failed: {e}"}

async def run_evaluation(model_a: str, model_b: str, judge_model: str, eval_dataset_path: str, output_log_path: str):
    """
    모델 성능 평가 파이프라인을 실행하는 메인 함수.
    """
    logger.info(f"🚀 Starting evaluation...")
    logger.info(f"  - Model A (Baseline): {model_a}")
    logger.info(f"  - Model B (Candidate): {model_b}")
    logger.info(f"  - Judge Model: {judge_model}")
    logger.info(f"  - Evaluation Dataset: {eval_dataset_path}")

    # 1. 평가 데이터셋 로드
    try:
        with open(eval_dataset_path, 'r', encoding='utf-8') as f:
            eval_data = json.load(f)
            if not isinstance(eval_data, list) or not all("prompt" in item for item in eval_data):
                 raise ValueError("Evaluation data must be a JSON list of objects, each with a 'prompt' key.")
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        logger.error(f"❌ Failed to load or parse evaluation dataset: {e}")
        return

    # 2. 각 프롬프트에 대해 평가 실행
    results = []
    scores = {"Model A": 0, "Model B": 0, "Tie": 0, "Error": 0}

    for i, item in enumerate(eval_data):
        prompt = item["prompt"]
        logger.info(f"--- Evaluating prompt {i+1}/{len(eval_data)} ---")
        
        # 두 모델의 응답을 동시에 생성
        response_a, response_b = await asyncio.gather(
            get_model_response(prompt, model_a),
            get_model_response(prompt, model_b)
        )

        # 심판의 평가 받기
        evaluation = await evaluate_pair(prompt, response_a, response_b, judge_model)
        
        winner = evaluation.get("winner", "Error")
        scores[winner] = scores.get(winner, 0) + 1
            
        result_entry = {
            "prompt": prompt,
            "model_a_response": response_a,
            "model_b_response": response_b,
            "evaluation": evaluation
        }
        results.append(result_entry)
        
        logger.info(f"  -> Winner: {winner}. Justification: {evaluation.get('justification', 'N/A')}")

    # 3. 결과 요약 및 출력
    total_comparisons = len(eval_data)
    win_rate_b = (scores["Model B"] / total_comparisons) * 100 if total_comparisons > 0 else 0
    loss_rate_b = (scores["Model A"] / total_comparisons) * 100 if total_comparisons > 0 else 0
    tie_rate = (scores["Tie"] / total_comparisons) * 100 if total_comparisons > 0 else 0

    logger.info("\n--- 📊 Evaluation Summary ---")
    logger.info(f"Total Prompts: {total_comparisons}")
    logger.info(f"Model B ('{model_b}') Win Rate: {win_rate_b:.2f}% ({scores['Model B']} wins)")
    logger.info(f"Model B ('{model_b}') Loss Rate: {loss_rate_b:.2f}% ({scores['Model A']} wins)")
    logger.info(f"Tie Rate: {tie_rate:.2f}% ({scores['Tie']} ties)")
    if scores["Error"] > 0:
        logger.warning(f"Evaluation Errors: {scores['Error']}")
    logger.info("--------------------------\n")

    # 4. 상세 로그 파일 저장
    try:
        with open(output_log_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Detailed evaluation log saved to '{output_log_path}'")
    except IOError as e:
        logger.error(f"❌ Failed to save evaluation log: {e}")

    # 5. 데이터베이스에 요약 결과 저장
    summary_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "model_a_name": model_a,
        "model_b_name": model_b,
        "judge_model_name": judge_model,
        "total_prompts": total_comparisons,
        "win_count_b": scores["Model B"],
        "loss_count_b": scores["Model A"],
        "tie_count": scores["Tie"],
        "error_count": scores["Error"],
        "win_rate_b": win_rate_b,
        "evaluation_log_path": output_log_path
    }
    save_evaluation_to_db(summary_data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate DPO model performance using a judge LLM.")
    parser.add_argument("--model-a", type=str, default="llama3.1:8b", help="Name of the baseline model (Model A).")
    parser.add_argument("--model-b", type=str, required=True, help="Name of the new candidate model to evaluate (Model B).")
    parser.add_argument("--judge-model", type=str, default="llama3.1:70b", help="Name of the judge model.")
    parser.add_argument("--dataset", type=str, default="evaluation_dataset.json", help="Path to the evaluation dataset JSON file.")
    parser.add_argument("--output-log", type=str, default="evaluation_log.json", help="Path to save the detailed evaluation log JSON file.")
    
    args = parser.parse_args()

    # 데이터베이스 초기화
    init_db()

    # 비동기 메인 함수 실행
    asyncio.run(run_evaluation(
        model_a=args.model_a,
        model_b=args.model_b,
        judge_model=args.judge_model,
        eval_dataset_path=args.dataset,
        output_log_path=args.output_log
    ))
