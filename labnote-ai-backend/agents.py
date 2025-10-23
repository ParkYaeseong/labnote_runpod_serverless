import os
import re
import logging
import asyncio
import json
from typing import List, Dict, TypedDict, Annotated, Tuple, Optional

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# Local imports
import rag_pipeline as rag_module
from llm_utils import call_llm_api

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Agent State Definition ---
class AgentState(TypedDict):
    query: str
    uo_block: str
    uo_id: str
    uo_name: str
    section_to_populate: str
    related_context: str
    # ⭐️ 변경점: Supervisor Agent를 위한 상태 추가
    drafts: List[Dict[str, str]] # [{'model': 'llama3.1:8b', 'content': '...'}, ...]
    feedback: str # Supervisor의 재작성 요구사항
    final_options: List[str] # 최종 사용자에게 보여줄 옵션
    messages: Annotated[list, add_messages]


# --- Helper function for content extraction ---
def _extract_section_content(uo_block: str, section_name: str) -> str:
    """Helper to extract content of a specific section from a UO block."""
    pattern = re.compile(r"#### " + re.escape(section_name) + r"\n(.*?)(?=\n####|\n------------------------------------------------------------------------)", re.DOTALL)
    match = pattern.search(uo_block)
    if match:
        content = match.group(1).strip()
        return content if content and not content.startswith('(') else "(not specified)"
    return "(not specified)"

async def _generate_drafts(state: AgentState) -> AgentState:
    """
    Specialist Agent들의 역할을 수행하는 함수.
    여러 LLM을 동시에 호출하여 섹션에 대한 초안들을 생성합니다.
    """
    query = state['query']
    uo_id = state['uo_id']
    uo_name = state['uo_name']
    section = state['section_to_populate']
    uo_block = state['uo_block']
    feedback = state.get('feedback', '') # 재작성 시 피드백 활용
    related_context = state.get('related_context', '')

    logger.info(f"Generating drafts for UO '{uo_id}' - Section '{section}'")
    input_context = _extract_section_content(uo_block, "Input")
    rag_query = f"Find the specific procedure or list of items for the '{section}' section of the unit operation '{uo_id}: {uo_name}' related to the experiment: {query}"

    pipeline = rag_module.get_rag_pipeline()
    context_docs = pipeline.retrieve_context(rag_query, k=3)
    rag_context = pipeline.format_context_for_prompt(context_docs)

    base_user_prompt = f"""
- **Experiment Goal**: '{query}'
- **Unit Operation**: '{uo_id}: {uo_name}'
- **Section to Write**: '{section}'
- **Inputs**: '{input_context}'
"""
    if "No relevant context found" not in rag_context:
        base_user_prompt += f"\n--- **Relevant SOP Context** ---\n{rag_context}\n---"

    if related_context:
        base_user_prompt += (
            "\n--- **Related Workflow Excerpts (Same Folder)** ---\n"
            f"{related_context}\n"
            "---\n"
            "Use these excerpts purely as references to maintain consistency. "
            "Do not copy sentences verbatim; adapt the procedures to the current experiment. "
            "If any excerpt contains code, diffs, or implementation notes (e.g., lines starting with `def`, `//`, or `Changes:`), "
            "interpret the intent in natural language and DO NOT output code or changelog text in your draft."
        )

    # 재작성 요청이 있을 경우 프롬프트에 피드백 추가
    if feedback:
        base_user_prompt += f"\n**IMPORTANT FEEDBACK FOR REVISION**: {feedback}\nPlease regenerate the content reflecting this feedback."

    base_user_prompt += f"""
---
### Formatting Rules
1. 답변은 제공된 모든 문장이 영어인 경우에만 영어로 작성하고, 그렇지 않으면 한국어로 작성합니다.
2. 반드시 `### {section}` 헤딩으로 시작한 뒤 줄바꿈하고, 번호 목록(`1.`, `2.` ...)만 제공합니다.
3. 각 항목은 명령형 한두 문장으로 작성하며, 가능한 경우 구체적인 수치·시간·장비 조건을 포함합니다.
4. "Answer", "ANS:", "결론" 등의 접두사나 경고, 책임 회피 문구, 마무리 인사 등 부가 설명은 절대 추가하지 않습니다.
5. 필요한 정보가 없으면 추측하지 말고 `(not specified)`라고만 적습니다.
6. 코드, 의사코드, 템플릿 플레이스홀더(`def ...`, `{{ ... }}`, `if (...) {{`, `Changes:` 등)를 출력하지 말고, 반드시 실험 절차 또는 자원 설명으로만 작성합니다.
"""

    prompt_preview = base_user_prompt[:400].replace("\n", " ")
    logger.info(
        "Draft prompt prepared | uo=%s | section=%s | chars=%d",
        uo_id,
        section,
        len(base_user_prompt)
    )
    logger.debug("Draft prompt preview: %s%s", prompt_preview, "..." if len(base_user_prompt) > 400 else "")


    system_prompt = "You are a specialized scientific assistant. Your task is to generate a comprehensive and well-structured response for a specific section of a lab note, using the provided context. The response should be clear, detailed, and directly applicable to the experiment. Your answer MUST be only the list or method itself, without any extra conversation or explanation."

    models_to_use = [
        os.getenv("LLM_MODEL", "llama3.1:8b"),
        "mixtral",
        "llama3.1:70b",
        "gpt-oss:120b",
    ]
    tasks = [
        call_llm_api(system_prompt, base_user_prompt, model_name)
        for model_name in models_to_use
    ]
    
    generated_contents = await asyncio.gather(*tasks)
    
    drafts = []
    for model_name, content in zip(models_to_use, generated_contents):
        if content and not content.startswith("(LLM Error"):
            drafts.append({'model': model_name, 'content': content})
            logger.info("Draft generated by %s:%s%s", model_name, os.linesep, content.strip())

    state['drafts'] = drafts
    return state


async def supervisor_agent(state: AgentState) -> AgentState:
    """
    Supervisor Agent. 생성된 초안들을 평가하고 다음 단계를 결정합니다.
    """
    logger.info(f"Supervisor Agent: Evaluating drafts for UO '{state['uo_id']}' - Section '{state['section_to_populate']}'")
    drafts = state['drafts']
    if not drafts:
        logger.warning("Supervisor: No drafts to evaluate. Ending.")
        state['final_options'] = ["AI가 초안을 생성하지 못했습니다. 다시 시도해주세요."]
        return state

    # 평가를 위한 프롬프트 구성
    evaluation_prompt = """
You are a highly experienced principal investigator reviewing lab notes. Evaluate the following drafts for the '{section}' section of a protocol. For each draft, provide a score (out of 10) and a brief justification based on these criteria:
1.  **Structural Integrity (구조적 완성도)**: Is the format (e.g., Markdown list, numbered steps) clear and well-organized?
2.  **Specificity and Detail (내용의 구체성)**: Does it include specific, quantitative details like reagent concentrations, times, equipment models, etc.?
3.  **SOP Relevance (SOP 연관성)**: How well does it incorporate information from the provided SOP context?

**Format your response strictly as a JSON object, like this example:**
[
  {{"draft_index": 0, "model": "llama3.1:8b", "score": 8.5, "justification": "Clear steps, but lacks specific buffer concentrations."}},
  {{"draft_index": 1, "model": "mixtral", "score": 7.0, "justification": "Too generic and misses key details from the SOP."}},
  {{"draft_index": 2, "model": "llama3.1:70b", "score": 9.2, "justification": "Excellent detail and structure, accurately reflects the SOP."}},
  {{"draft_index": 3, "model": "gpt-oss:120b", "score": 9.5, "justification": "Most thorough and precise, integrates SOP cues flawlessly."}}
]

--- DRAFTS TO EVALUATE ---
{draft_texts}
"""
    draft_texts = "\n\n---\n\n".join([f"**Draft {i} (from {d['model']})**:\n{d['content']}" for i, d in enumerate(drafts)])
    
    # gpt-oss:120b를 채점자로 사용하고, 실패 시 llama3.1:70b로 폴백합니다.
    scoring_llms = ["gpt-oss:120b", "llama3.1:70b"]
    response_str = None
    last_error: Optional[Exception] = None
    for scoring_llm in scoring_llms:
        try:
            logger.info("Calling Scoring LLM (%s) to evaluate drafts.", scoring_llm)
            response_str = await call_llm_api(
                system_prompt="You are an expert lab note reviewer. Your output must be a valid JSON array of objects.",
                user_prompt=evaluation_prompt.format(section=state['section_to_populate'], draft_texts=draft_texts),
                model_name=scoring_llm
            )
            if response_str:
                break
        except Exception as exc:  # pylint: disable=broad-except
            last_error = exc
            logger.exception("Supervisor: Scoring with %s failed. Trying fallback if available.", scoring_llm)

    if not response_str:
        logger.error("Supervisor: All scoring attempts failed. Last error: %s", last_error)
        state['final_options'] = ["AI가 초안을 평가하지 못했습니다. 다시 시도해주세요."]
        return state
    
    try:
        # LLM의 응답에서 JSON만 추출
        json_match = re.search(r'\[.*\]', response_str, re.DOTALL)
        if not json_match:
            raise json.JSONDecodeError("No JSON array found in the LLM response.", response_str, 0)
        evaluations = json.loads(json_match.group(0))
        logger.info(f"Supervisor: Parsed evaluations: {evaluations}")
    except (json.JSONDecodeError, IndexError) as e:
        logger.error(f"Supervisor: Failed to parse JSON from scoring LLM. Error: {e}. Response: {response_str}")
        # 평가 실패 시, 원본 초안들을 그대로 사용
        state['final_options'] = [f"--- {d['model']}의 제안 ---\n\n{d['content']}" for d in drafts]
        state['feedback'] = '' # 피드백 없음
        return state

    # 점수가 가장 높은 초안 찾기
    best_draft_eval = max(evaluations, key=lambda x: x.get('score', 0))
    highest_score = best_draft_eval.get('score', 0)
    
    # 품질 기준(8.5점)을 통과했는지 확인
    if highest_score >= 8.0:
        logger.info(f"Supervisor: Quality threshold passed with score {highest_score}. Finalizing options.")
        # 고품질 초안들만 필터링하여 사용자에게 제공
        high_quality_drafts = [
            drafts[e['draft_index']] for e in evaluations if e.get('score', 0) >= 8.0
        ]
        state['final_options'] = [f"--- {d['model']}의 제안 (품질 점수: {next(e['score'] for e in evaluations if e['draft_index'] == i)}) ---\n\n{d['content']}" for i, d in enumerate(drafts) if d in high_quality_drafts]
        state['feedback'] = '' # 재작성 필요 없음
    else:
        logger.info(f"Supervisor: Quality threshold NOT passed (highest score: {highest_score}). Requesting revision.")
        # 재작성을 위한 피드백 생성
        feedback_points = [f"Draft from {e['model']} was critiqued: '{e['justification']}'" for e in evaluations]
        state['final_options'] = [] # 최종 옵션 없음
        state['feedback'] = f"The previous drafts were not detailed enough (top score was {highest_score}). Specific feedback: {' '.join(feedback_points)}. Please generate a much more detailed and specific version."

    return state


# --- Agent Nodes ---
async def specialist_agent_node(state: AgentState) -> AgentState:
    # 비동기 함수를 LangGraph 노드에서 실행하기 위해 await 사용
    return await _generate_drafts(state)

async def supervisor_agent_node(state: AgentState) -> AgentState:
    return await supervisor_agent(state)

# --- Routing Logic ---
def route_after_supervision(state: AgentState) -> str:
    if state.get('feedback'):
        logger.info("Routing: Feedback exists. Looping back to specialist agents.")
        return "specialist_agents"
    else:
        logger.info("Routing: No feedback. Proceeding to end.")
        return END

# --- Graph Definition ---
def create_agent_graph():
    graph = StateGraph(AgentState)
    
    graph.add_node("specialist_agents", specialist_agent_node)
    graph.add_node("supervisor", supervisor_agent_node)
    
    graph.set_entry_point("specialist_agents")
    graph.add_edge("specialist_agents", "supervisor")
    
    # Supervisor 평가 후 조건부 라우팅
    graph.add_conditional_edges(
        "supervisor",
        route_after_supervision,
        {
            "specialist_agents": "specialist_agents",
            END: END
        }
    )
    
    agent_graph = graph.compile()
    logger.info("Supervisor-led agent graph compiled successfully.")
    return agent_graph

# --- Main execution function ---
async def run_agent_team(
    query: str,
    file_content: str,
    section: str,
    uo_id: str,
    related_context: str = ""
) -> Dict:
    # 1. file_content에서 uo_id에 해당하는 uo_block 전체를 찾습니다.
    uo_block_pattern = re.compile(
        r"(###\s*\\?\[" + re.escape(uo_id) + r".*?\][\s\S]*?)(?=\n###\s*\\?\[U[A-Z]|\Z)",
        re.DOTALL
    )
    uo_block_match = uo_block_pattern.search(file_content)
    uo_block = uo_block_match.group(1).strip() if uo_block_match else ""

    # 2. uo_block에서 uo_name을 추출합니다.
    match = re.search(r"###\s*\\?\[" + re.escape(uo_id) + r"(?:\s+(.*?))?\\?\]", uo_block)
    if not match:
        logger.error(f"Could not parse UO header for '{uo_id}'. UO Block Snippet:\n---\n{uo_block[:200]}\n---")
        uo_name = uo_id
    else:
        captured_name = match.group(1) if match.lastindex else None
        uo_name = (captured_name or uo_id).strip()

    initial_state = AgentState(
        query=query,
        uo_block=uo_block,
        uo_id=uo_id,
        uo_name=uo_name,
        section_to_populate=section,
        related_context=related_context or "",
        drafts=[],
        feedback='',
        final_options=[],
        messages=[]
    )
    
    graph = create_agent_graph()
    # ⭐️ [FIX] 비동기 그래프를 await으로 실행합니다.
    final_state = await graph.ainvoke(initial_state)
    
    return {
        "uo_id": uo_id,
        "section": section,
        "options": final_state.get('final_options', []),
        "feedback": final_state.get('feedback')
    }
