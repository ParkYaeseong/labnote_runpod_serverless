## Continue Slash Command Integration Notes

### 배경
- VSCode 확장(`vscode-labnote-extension`)은 `/api/chat` 호출 시 `file_content`, `experiment_goal`을 명시적으로 전달하지만, Continue 확장은 OpenAI 호환 `/v1/chat/completions` 엔드포인트만 사용하며 해당 필드를 추가하지 않습니다.
- `chat()` 내부 `/populate` 경로는 두 필드를 필수로 요구하므로, Continue에서는 항상 `"Error: To populate the section..."` 응답을 받는 문제가 있었습니다.

### 2025-10-18 변경 요약
- `/populate` 명령을 빈 인자로 호출하면 백엔드가 대화형 플로우를 시작해 유닛 오퍼레이션 ID와 섹션명을 순차적으로 질문합니다.
- `main.py`에 `_execute_populate_flow()`를 도입해 `/populate` 실행 경로를 단일 함수로 분리하고, DPO 피드백에 필요한 컨텍스트 저장 로직을 재사용합니다.
- `_handle_interactive_populate_flow()`와 `_extract_uo_and_section_from_text()`를 추가해 사용자가 `WD010` 또는 `Method`처럼 부분 입력만 주었을 때도 자연스럽게 값을 보완합니다.
- `/populate WD010`처럼 섹션이 비어 있는 경우 자동으로 인터랙티브 모드로 전환해 동일한 안내를 제공합니다.
- 같은 폴더에 있는 다른 워크플로우 파일에서 동일한 UO/섹션을 찾아 초안 작성 시 참고 컨텍스트로 전달합니다. Continue/VSCode 모두 `file_path` 힌트가 있으면 우선 사용하고, 없을 경우 문서 내 `](./*.md)` 링크를 스캔해 추가합니다.
- 워크플로우 참조 시 코드/변경 로그처럼 보이는 조각은 자동으로 걸러지며, 남은 텍스트도 "코드나 diff는 무시하고 실험 단계로 재해석"하도록 에이전트 프롬프트에 명시했습니다.

### 2025-10-15 변경 요약
- `main.py`에 아래 보조 함수들을 추가했습니다.
  - `_normalize_message_content()`: OpenAI 메시지 포맷이 문자열 또는 structured content 배열일 때 모두를 문자열로 정규화.
  - `_extract_file_content_from_messages()`: 가장 최근 유저 메시지의 코드 블록(예: ```markdown, ```labnote/...)에서 랩노트 전체 내용을 복원하도록 info string을 일반화.
  - `_infer_experiment_goal()`: 추출한 문서에서 front matter(`experiment_goal`, `goal`, `title`) 또는 최상위 `##` 헤딩을 기반으로 실험 목표를 도출.
- `/v1/chat/completions` 진입 시 위 함수들을 사용하여 누락된 `file_content`, `experiment_goal`을 보강하고, 끝내도 파생되지 않으면 `"Experiment goal not provided."`로 기본값을 설정합니다.
- OpenAI 호환 응답 포맷이 Continue 클라이언트 기대치와 동일하도록 `created`, `model`, `usage` 필드를 추가했습니다.
- Continue 요청 디버깅을 위해 `openai_compat()` 초반에 요청 요약 로그(마지막 메시지 프리뷰, 추출된 컨텍스트 길이)를 남기도록 했습니다.
- `/populate` 명령은 실제 입력 행(`^/populate ...`)만 탐지하도록 정규식을 조정해, 설명용 텍스트나 다른 코드 블록에 포함된 예시를 잘못 파싱하지 않도록 했습니다.

### 사용/확장 가이드
1. **Continue Slash Command 흐름**
   - Continue는 slash command 템플릿에 활성 파일 전체를 ```markdown``` 블록으로 삽입합니다.
   - 새 전처리 함수들은 해당 블록에서 데이터를 추출하므로 추가적인 설정 변경 없이 `/populate` 명령이 작동합니다.
   - 이제 `/populate`만 입력해도 백엔드가 `유닛 오퍼레이션 ID → 섹션명` 순으로 질문하므로, 사용자는 차례대로 `WD010`, `Method`처럼 답하면 됩니다. 언제든 `취소`라고 입력하면 흐름이 초기화됩니다.
   - 백엔드는 같은 폴더의 다른 워크플로우 파일을 자동으로 읽어 동일 UO/섹션의 기존 내용을 참고합니다. Continue 템플릿에 `filepath:` 주석을 추가하거나, 문서 상단에서 `](./*.md)` 링크로 관련 워크플로우를 명시하면 정확도가 높아집니다.
   - VSCode 확장의 `Populate Section` 명령(기본 단축키 `Ctrl+Shift+P`)도 동일한 로직을 사용하므로, 관련 워크플로우 `.md` 파일을 같은 폴더에 두기만 하면 됩니다.
2. **문서 구조 요구 사항**
   - front matter 예시:
     ```yaml
     ---
     title: WD070 Vector Design - Design_of_sensor_construction
     experimenter: Wonjae, Hongyeon, Haseong
     experiment_goal: Vector design for sensor construction
     ---
     ```
   - front matter에 `experiment_goal`이 없을 경우 첫 번째 `## [...]` 헤딩을 사용합니다. 문서 템플릿을 변경할 때 이 규칙을 유지하면 됩니다.
3. **추가 규칙을 넣고 싶다면**
   - `_infer_experiment_goal()` 내에서 다른 헤딩 패턴을 탐지하도록 정규식을 확장하면 됩니다.
   - Continue가 메시지 포맷을 변경하는 경우 `_normalize_message_content()` 또는 `/populate` 패턴(`re.search(r"/populate ...")`)을 업데이트해야 합니다.
   - 로그가 너무 장황해지면 `openai_compat()` 내 `logger.info` 호출을 `debug`로 낮추고 로깅 레벨을 조정하세요.
4. **유닛 테스트/회귀 테스트**
   - 최소한 다음 시나리오를 수동 확인하세요.
     - front matter에 `experiment_goal`이 있는 문서.
     - front matter에 `experiment_goal`이 없고 `## [Workflow]` 헤딩만 있는 문서.
     - 코드 블록 없이 호출했을 때: 기존과 동일하게 오류가 반환되어야 합니다.

### 향후 TODO
- `_infer_experiment_goal()`에 labnote 템플릿의 다른 구조(예: `## Experiment Goal`) 파싱 로직을 추가.
- 자동화된 단위 테스트(FastAPI TestClient)로 `/v1/chat/completions` happy-path와 오류 케이스 확인.

### 2025-10-16 개선 계획 (Continue 사용자 경험)
1. **중복 선택 방지 / 피드백 상태 고정**
   - [x] Populate 응답 후 같은 UO/섹션에서 동일한 번호를 반복 선택하면 “이미 기록되었습니다” 안내만 반환하도록 가드 로직을 추가합니다.
2. **Continue에서 자동 삽입 지원**
   - [ ] `/v1/chat/completions` JSON 응답에 `metadata={"uo_id": ..., "section": ..., "content": ...}` 구조를 추가하고, Continue slash command 핸들러가 이를 읽어 활성 문서에 바로 삽입하도록 확장합니다(사용자 스크립트 또는 snippets API 사용).
   - [ ] 과도기 단계로는 최종 응답에 마크다운 코드블록(```insert ... ```)을 감싸 제공하여 Continue의 “Apply Diff” 기능을 활용하도록 가이드합니다.
3. **선택 영역 기반 Populate 실행**
   - [ ] Continue `config.yaml`에 이미 제공되는 `active_file_content` 외에 `selected_text` 컨텍스트(사용자가 Ctrl+L 또는 마우스 드래그로 지정한 부분이 자동 전달됨)를 활용해 `/populate` 프롬프트에 선택 텍스트를 별도 블록으로 포함합니다.
   - [ ] 백엔드 `_find_last_populate_command()`를 확장해 선택 텍스트 내 `#### <Section>` 및 인접 `### [UO ...]` 헤더를 우선 탐색하여 UO/섹션을 자동 추론합니다. 실패 시 전체 파일로 fallback 하고, 필요한 최소 선택 범위를 안내합니다.

### 2025-10-17 개선 계획 (Continue 파일 첨부 연동)
1. **파일 업로드 경로 마련**
   - [ ] Continue의 `@` 첨부 기능 및 드래그 앤 드롭으로 전달되는 `attachments` 메타데이터를 파싱하고, 미지원 시 사용자 정의 플러그인으로 백엔드 `/attachments` (신규) 엔드포인트에 업로드하도록 가이드합니다.
   - [ ] 업로드 파일은 임시 디렉토리 또는 S3 등 안전한 저장소에 보관하며, 응답으로 파일 식별자/메타데이터를 반환합니다.
   - [ ] Microsoft의 PDF MCP(Multi-Modal Connector)를 활용해 PDF 내 텍스트/테이블 추출을 대체하거나 보조 수단으로 검토합니다.
2. **PPT/PDF 내용 추출 파이프라인**
   - [ ] `.pptx` → `python-pptx`, `.pdf` → `PyMuPDF`/`pdfminer.six` 혹은 Microsoft PDF MCP를 활용해 텍스트와 표/슬라이드 메모를 구조화된 JSON으로 변환합니다.
   - [ ] 추출 단계에서 실험 조건(장비 설정, 파라미터, 제약사항)을 강조하여 요약 벡터를 생성하고, 필요 시 임시 RAG 인덱스에 추가합니다.
3. **프로토콜 수정 명령 설계**
   - [ ] Continue slash command `/revise_protocol`를 정의해 사용자 입력 + 첨부된 파일 목록을 함께 전달:
     ```
     /revise_protocol {{user_input}}
     {{#each attachments}}
     ```file
     {{this.filename}}
     {{this.content}}
     ```
     {{/each}}
     ```markdown
     {{active_file_content}}
     ```
     ```
   - [ ] 백엔드 `chat()`에서 `/revise_protocol`을 감지해 첨부 파일 요약 결과를 기반으로 프로토콜 관련 섹션(Method 등)을 갱신하는 에이전트 플로우를 구성합니다.
4. **보안 및 운영 고려**
   - [ ] 허용 확장자(`.ppt`, `.pptx`, `.pdf`)와 크기 제한(예: 20MB)을 명시하고, 업로드 실패 시 사용자 친화적 메시지를 반환합니다.
   - [ ] 업로드 파일은 일정 기간 이후 자동 삭제하고, 감사 로그에 파일 접근 내역을 남겨 데이터 보안을 확보합니다.
