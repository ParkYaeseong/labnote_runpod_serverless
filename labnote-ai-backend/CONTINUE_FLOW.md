# Continue Slash Command Processing

이 문서는 VS Code Continue 확장 프로그램에서 들어온 요청이 LabNote 백엔드에서 어떤 라우터와 오케스트레이터를 거쳐 분석되고 실행되는지 단계별로 정리합니다.

## 1. 요청 진입 경로

1. **Continue 설정**
   - `config.yaml`에서 모델을 `labnote-backend`로 지정하고 `apiBase`를 RunPod Serverless 엔드포인트(`https://api.runpod.ai/v2/<ENDPOINT_ID>/runsync`)로 설정합니다.
   - Continue는 Slash Command(`/populate …`) 또는 일반 채팅을 JSON 형식으로 RunPod API에 POST합니다.

2. **RunPod Serverless 핸들러 (`labnote-ai-backend/runpod_handler.py`)**
   - RunPod가 전달한 `job['input']`을 읽어 `method`, `path`, `body`를 구성합니다.
   - `path`가 비어 있으면 하위 호환을 위해 `/v1/chat/completions`을 기본값으로 사용합니다.
   - FastAPI 백엔드가 컨테이너 내부에서 `uvicorn main:app`으로 기동되어 있으며, 핸들러는 내부 URL(`LABNOTE_BACKEND_URL`, 기본 `http://127.0.0.1:8000`)로 HTTP 요청을 프록시합니다.

3. **FastAPI 라우터**
   - Continue가 지정한 `path` 값에 따라 서로 다른 엔드포인트로 분기합니다.
     - `/v1/chat/completions` : OpenAI 호환 인터페이스. Continue Slash Command는 이 경로를 사용합니다.
     - `/populate_note` : VS Code 자체 확장이 직접 호출하는 전용 엔드포인트 (Populate Section 버튼).

## 2. `/v1/chat/completions` 처리 과정

### 2.1 요청 정규화 (`openai_compat` in `main.py:1516`)

1. **메타데이터 추출**
   - `messages`, `model`, `context`, `file_content`, `experiment_goal`, `file_path` 등을 파싱합니다.
   - 누락된 경우에는 `_extract_file_content_from_messages`/`_infer_experiment_goal` 등 유틸을 통해 복원합니다.

2. **대화 로그 관리**
   - Stateless 동작을 위해 클라이언트가 전달한 `context` 안에 Slash Command 진행상황, 선택지 등을 보관합니다.
   - `conversation['messages']`에 사용자 발화를 축적한 뒤 `chat()` 코루틴으로 넘깁니다.

### 2.2 명령 분석 (`chat` in `main.py`)

`chat()` 함수는 `request.model` 값과 메시지 문자열을 조합해 다음과 같이 분기합니다.

| 조건 | 수행 동작 |
| --- | --- |
| `model != "labnote-backend"` | 일반 대화 흐름으로 바로 이동. 기본 모델(`LLM_MODEL`) 또는 명시된 모델을 사용해 Ollama API 호출. |
| `model == "labnote-backend"` & 인터랙티브 상태 | `_handle_interactive_populate_flow`로 현재 진행 단계(예: UO·Section 입력 유도)를 계속 수행. |
| `model == "labnote-backend"` & `/populate` 명령 매칭 | `_execute_populate_flow`를 호출해 실제 섹션 초안 생성을 진행. |
| 위 조건에 해당하지 않음 | 일반 대화 흐름으로 폴백. |

Slash Command 문자열은 정규식으로 감지합니다.
```python
populate_match = re.search(r"^\s*/populate\s+(?P<user_input>[^\n`]+)", query, re.IGNORECASE | re.MULTILINE)
populate_triggered = re.search(r"^\s*/populate\b", query, re.IGNORECASE | re.MULTILINE)
```

### 2.3 에이전트 오케스트레이션

`_execute_populate_flow()`에서 다음 컴포넌트를 조합합니다.

1. **SOP/RAG 조회 (`agents.py → rag_module.rag_pipeline`)**
   - `rag_pipeline.retrieve_context()`가 Redis 벡터스토어에서 상위 문맥을 가져옵니다. 초기화 시점에 `sop/` 폴더의 Markdown을 Chunk 단위로 임베딩하고, Redis 인덱스가 없으면 자동으로 생성합니다.

2. **LangGraph 기반 멀티 에이전트 (`agents.run_agent_team`)**
   - `StateGraph`를 이용해 Specialist Agents → Supervisor Agent 순으로 구성된 워크플로우를 실행합니다.
   - Specialist는 여러 모델(`llama3.1:8b`, `mixtral`, `llama3.1:70b`, `gpt-oss:120b`)로 병렬 초안을 생성하고, Supervisor는 `gpt-oss:120b`(폴백: `llama3.1:70b`)로 점수를 계산해 최종 옵션을 선별합니다.

3. **DPO 피드백 루프**
   - 사용자가 VS Code에서 옵션을 선택하면 `/record_preference`가 호출되어 Git 저장소와 SQLite에 데이터를 적재합니다.
   - Continue 플로우에서는 `/populate` 대화 중 선택지를 서버가 상태 없이 다시 안내하기 때문에, 클라이언트가 `context`에 최종 초안을 포함해 전달하면 연속된 명령도 처리할 수 있습니다.

### 2.4 일반 대화 폴백

Slash Command 조건에 해당하지 않으면 `ollama.AsyncClient().chat()`으로 일반 응답을 생성합니다. 이때도 `_post_process_content()`를 통해 불필요한 문구를 제거하고, 최종 응답과 함께 업데이트된 `context`를 돌려줍니다.

## 3. 응답 반환

- `openai_compat`는 OpenAI 호환 형식(JSON)으로 결과를 반환합니다.
- `context` 필드에는 Continue가 이후 요청에 재전달해야 할 상태(Slash Command 진행 정보 등)가 포함됩니다.
- Stream 옵션이 들어오면 Server-Sent Events 형식으로 같은 로직을 스트리밍합니다.

## 4. 요약

1. Continue → RunPod Serverless → FastAPI `/v1/chat/completions` 순서로 요청이 이동합니다.
2. `model == "labnote-backend"`인 요청만 Slash Command와 Populate 흐름을 처리합니다.
3. 명령 감지 후에는 RAG + LangGraph 에이전트(`run_agent_team`)가 초안을 생성합니다.
4. 결과는 OpenAI 호환 응답과 함께 클라이언트 `context`에 담겨 반환되며, 후속 명령은 이 context를 통해 계속 이어집니다.

이 구조 덕분에 RunPod와 같은 서버리스 환경에서도 상태를 최소화하면서 Slash Command + 멀티 에이전트 워크플로우를 안전하게 실행할 수 있습니다.
