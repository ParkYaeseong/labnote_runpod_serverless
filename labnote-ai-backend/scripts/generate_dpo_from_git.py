import os
import re
import json
import redis
import requests
import argparse
import uuid
from typing import Dict, List, Optional

# --- 정규 표현식 ---
UO_BLOCK_EXTRACT_PATTERN = re.compile(
    r"(### \[(?P<uo_id>U[A-Z]{2,3}\d{3}).*?\n.*?)(?=### \[U[A-Z]{2,3}\d{3}|\Z)", re.DOTALL
)

def _extract_section_content(uo_block: str, section_name: str) -> Optional[str]:
    pattern = re.compile(r"#### " + re.escape(section_name) + r"\n(.*?)(?=\n####|\n------------------------------------------------------------------------)", re.DOTALL)
    match = pattern.search(uo_block)
    if match:
        content = match.group(1).strip()
        return None if content.startswith('(') else content
    return None

def find_original_prompt(r: redis.Redis, workflow_file: str, uo_id: str, section: str) -> Optional[str]:
    """Redis를 스캔하여 가장 오래된 원본 프롬프트를 찾습니다."""
    keys = r.keys(f"dpo:preference:*")
    oldest_ts = float('inf')
    original_prompt = None

    for key in keys:
        data_str = r.get(key)
        if not data_str: continue
        data = json.loads(data_str)
        meta = data.get("metadata", {})
        
        if meta.get("workflow_file") == workflow_file and \
           meta.get("unit_operation_id") == uo_id and \
           meta.get("section") == section:
            
            # 타임스탬프를 비교하여 가장 오래된 기록을 찾음
            try:
                ts = float(meta.get("timestamp_unix", float('inf')))
                if ts < oldest_ts:
                    oldest_ts = ts
                    original_prompt = data.get("prompt")
            except (ValueError, TypeError):
                continue

    return original_prompt

def main():
    parser = argparse.ArgumentParser(description="Generate DPO data from git diff.")
    parser.add_argument("--prev-file", required=True, help="Path to the previous version of the file.")
    parser.add_argument("--curr-file", required=True, help="Path to the current version of the file.")
    args = parser.parse_args()

    # --- 환경 변수에서 정보 가져오기 ---
    redis_url = os.getenv("REDIS_URL")
    redis_password = os.getenv("REDIS_PASSWORD")
    backend_api_url = os.getenv("BACKEND_API_URL")
    
    if not all([redis_url, backend_api_url]):
        print("Error: Environment variables REDIS_URL, BACKEND_API_URL must be set.")
        exit(1)

    try:
        r = redis.Redis.from_url(redis_url, password=redis_password, decode_responses=True)
        r.ping()
    except Exception as e:
        print(f"Error connecting to Redis: {e}")
        exit(1)

    with open(args.prev_file, 'r', encoding='utf-8') as f:
        prev_content = f.read()
    with open(args.curr_file, 'r', encoding='utf-8') as f:
        curr_content = f.read()

    prev_uos = {m.group('uo_id'): m.group(0) for m in UO_BLOCK_EXTRACT_PATTERN.finditer(prev_content)}
    curr_uos = {m.group('uo_id'): m.group(0) for m in UO_BLOCK_EXTRACT_PATTERN.finditer(curr_content)}

    workflow_file = os.path.basename(args.curr_file)
    
    for uo_id, current_block in curr_uos.items():
        previous_block = prev_uos.get(uo_id)
        if not previous_block:
            continue # UO 블록이 새로 추가된 경우, 비교 대상이 없으므로 건너뜀

        for section in ["Method", "Reagent", "Consumables", "Equipment", "Input", "Output", "Results & Discussions"]:
            prev_section_content = _extract_section_content(previous_block, section)
            curr_section_content = _extract_section_content(current_block, section)

            # 내용이 존재하고, 이전 버전과 현재 버전이 다를 경우에만 DPO 데이터 생성
            if curr_section_content and prev_section_content and prev_section_content != curr_section_content:
                
                original_prompt = find_original_prompt(r, workflow_file, uo_id, section)
                if not original_prompt:
                    print(f"Warning: Could not find original prompt for {workflow_file}/{uo_id}/{section}. Skipping.")
                    continue

                dpo_payload = {
                    "prompt": original_prompt,
                    "chosen": curr_section_content, # 최종본이 chosen
                    "rejected": [prev_section_content], # 이전 버전이 rejected
                    "metadata": {
                        "source": "git_commit_finalized",
                        "commit_author": os.getenv("COMMIT_AUTHOR"),
                        "commit_message": os.getenv("COMMIT_MESSAGE"),
                        "commit_hash": os.getenv("COMMIT_HASH"),
                        "workflow_file": workflow_file,
                        "unit_operation_id": uo_id,
                        "section": section,
                    }
                }
                
                # API로 전송
                try:
                    response = requests.post(
                        f"{backend_api_url}/record_git_feedback",
                        json=dpo_payload,
                        headers={'Content-Type': 'application/json'}
                    )
                    response.raise_for_status()
                    print(f"Successfully sent DPO data for {uo_id}/{section}")
                except requests.exceptions.RequestException as e:
                    print(f"Error sending DPO data for {uo_id}/{section}: {e}")

if __name__ == "__main__":
    main()