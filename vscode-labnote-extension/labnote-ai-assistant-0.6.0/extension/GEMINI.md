# GEMINI.md

이 문서는 LabNote AI Assistant의 코드 구조를 분석하고, 현재 개발 목표를 명확히 하기 위해 작성되었습니다.

## 🎯 현재 목표

1.  **섹션 채우기 기능 오류 수정**: 현재 커서 위치를 기반으로 Unit Operation 및 섹션 컨텍스트를 분석하고, AI 백엔드를 통해 받은 제안을 Webview에 표시하는 기능의 오류를 해결합니다.
2.  **Visual Editor 수정 오류 해결**: Visual Editor (WYSIWYG) 모드에서 문서를 수정할 때 원본 마크다운 파일의 내용이 비정상적으로 변경되는 문제를 해결합니다.

---

## 🔬 목표 1: 섹션 채우기 기능 수정

### 1. 기능 흐름

사용자가 'AI로 채우기' 명령을 실행하면, 확장 프로그램은 다음 단계를 거칩니다.

1.  **컨텍스트 분석 (`findSectionContext`)**: 현재 커서 위치에서 가장 가까운 `### [UO ID]` 블록과 `#### Section`을 찾아내어 어떤 Unit Operation의 어떤 섹션을 채울 것인지 식별합니다.
2.  **API 호출**: 분석된 컨텍스트 정보(파일 전체 내용, UO ID, 섹션 이름, 실험 목표)를 FastAPI 백엔드의 `/populate_note` 엔드포인트로 전송합니다.
3.  **Webview 표시**: 백엔드로부터 받은 여러 개의 텍스트 초안(options)을 Webview에 표시하여 사용자가 선택하고 수정할 수 있도록 합니다.
4.  **내용 적용 및 학습**: 사용자가 최종 내용을 선택하고 '적용 및 AI 학습' 버튼을 누르면, 해당 내용이 문서에 적용되고 사용자의 선택은 DPO(Direct Preference Optimization) 데이터로 백엔드에 전송됩니다.

### 2. 코드 구조 분석

#### **VS Code Extension (`vscode-labnote-extension`)**

* **`extension.ts`**:
    * `populateSectionFlow` 함수에서 전체 프로세스가 시작됩니다.
    * `findSectionContext` 함수를 호출하여 현재 문서와 커서 위치를 기반으로 컨텍스트를 분석합니다.
    * `processAndApplyPopulation` 함수 내에서 백엔드 API (`/populate_note`)를 호출하고, 응답으로 받은 `options`를 `createPopulateWebviewPanel` 함수에 전달하여 Webview를 생성합니다.
    * Webview에서 사용자가 'applyAndLearn' 메시지를 보내면, 문서의 해당 부분을 수정하고 백엔드의 `/record_preference` API를 호출하여 사용자 피드백을 전송합니다.
    * **핵심 수정 로직 (`findSectionContext` in `extension.js`)**:
        * YAML Front Matter에서 실험 목표(`query`)를 추출합니다.
        * 커서 위치(`vscode.Position`)를 기준으로 위로 탐색하며 `### [U...ID]` 형태의 Unit Operation 블록과 `#### Section` 형태의 섹션 이름을 찾습니다.
        * 찾아낸 UO ID와 섹션 이름을 바탕으로 문서 전체를 다시 스캔하여 정확한 플레이스홀더 `(method used in this step)`의 위치(`vscode.Range`)를 식별합니다. 이 2단계 탐색 방식은 정확도를 높이지만, 현재 이 부분에서 오류가 발생하는 것으로 보입니다.


---

## 🎨 목표 2: Visual Editor 수정 오류 해결

### 1. 문제점

Visual Editor에서 내용을 수정하면, 마크다운으로 변환되는 과정에서 YAML Front Matter나 특정 마크다운 구문(`---`)이 깨져 파일이 비정상적으로 저장됩니다.

### 2. 해결 방안: Quarto Visual Editor 통합 (제안)

현재 `LabnoteEditorProvider.ts`에 구현된 Visual Editor는 `markdown-it` 라이브러리로 마크다운을 HTML로, `turndown` 라이브러리로 HTML을 마크다운으로 변환합니다. 이 과정에서 발생하는 문제를 해결하기 위해, 보다 안정적이고 마크다운 호환성이 높은 **Quarto Visual Editor**를 통합하는 것을 목표로 합니다.

### 3. 코드 구조 분석

* **`LabnoteEditorProvider.ts`**:
    * `resolveCustomTextEditor` 메소드에서 Custom Editor를 초기화하고 Webview의 콘텐츠를 설정합니다.
    * `getWebviewContent` 메소드는 Webview의 전체 HTML 구조를 생성합니다. 현재 여기에 `markdown-it`와 `turndown` 스크립트를 CDN으로 불러오고 있습니다.
    * **문제의 원인**: `turndownService`가 YAML Front Matter (`---`)나 수평선 (`---`)을 올바르게 처리하지 못해 발생하는 것으로 보입니다. 현재 코드에는 이를 해결하기 위한 `yamlFrontMatter`와 `horizontalRule` 규칙이 추가되어 있지만, 완벽하게 작동하지 않는 것으로 추정됩니다.
    * **수정 방향**: `turndown` 라이브러리 대신 Quarto의 파서를 사용하거나, `turndown`의 규칙을 더욱 정교하게 다듬어 YAML 블록과 본문 콘텐츠를 명확히 구분하여 변환하도록 수정해야 합니다.