# Agentic System Implementation

This document provides a detailed breakdown of the agentic implementation in the `value-investing-agentic` project, focusing on the LangGraph architecture and recommendations for updated technologies.

## 1. High-Level Architecture: The Research Line

The project implements a **Sequential Research Pipeline** with a sophisticated filtering mechanism at the start. It uses **LangGraph** to model this process as a state machine.

### The Workflow (`src/graph/workflow.py`)
1.  **Discovery (Entry)**: Fast, cheap filter to check if a signal (e.g., Insider Trade) is interesting.
2.  **Conditional Gate**:
    *   If **Interesting** → Proceed to Deep Research.
    *   If **Not Interesting** → End immediately (saves cost).
3.  **Deep Research**: Performs multi-level analysis (Context → History → Fundamentals → Synthesis).
4.  **Context**: Adds industry trends and peer comparisons.
5.  **Validation**: A "Critic" agent checks for hallucinations or logical flaws.
6.  **Synthesis**: Produces the final JSON report.

---

## 2. Deep Dive: The Agents

The system uses a **multi-model strategy** (router pattern) to balance cost and intelligence.

| Agent | Model | Role & Logic |
| :--- | :--- | :--- |
| **Discovery** | **Qwen-2.5-72B** | **The Gatekeeper.** It receives a raw signal (e.g., "Promoter bought 5%"). It evaluates: *Is this routine or a special situation?* It sets the `is_interesting` flag in the state. Qwen is used here for its high speed and strong reasoning at a lower cost than GPT-4. |
| **Deep Research** | **DeepSeek V3** | **The Analyst.** It performs 4 specific calls (Basic Context, Historical Patterns, Fundamentals, Synthesis). It uses the `DataCollector` tool to fetch real financial data before prompting the LLM. DeepSeek V3 is excellent for code/financial reasoning. |
| **Context** | **DeepSeek V3** | **The Strategist.** Adds macro context. It answers: *Is the industry growing? Who are the peers?* It helps distinguish a good company in a bad sector versus a true outlier. |
| **Validation** | **Qwen-2.5-72B** | **The Critic.** It reads the generated research and asks: *Do the stats match the conclusion? Are there contradictions?* It sets a `verified` flag. |
| **Synthesis** | **DeepSeek V3** | **The Editor.** Takes all previous outputs (Research, Context, Validation notes) and compiles a structured JSON report with a catchy headline, analysis, and risk assessment. |

---

## 3. LangGraph Knowledge: "Why & What"

We use **LangGraph** to orchestrate this process. Here is the technical breakdown of *why* and *how* it works:

### State Management (`ResearchState` in `src/graph/state.py`)
*   **Why used:** Agents need a shared "memory". Instead of passing massive strings, a `TypedDict` keeps track of structured data (`level1_context`, `final_insight`, etc.).
*   **Mechanism:** When an agent returns `{"key": "value"}`, LangGraph updates the central state.

### Conditional Edges (`workflow.add_conditional_edges`)
*   **Why used:** To save money and time. You don't want to perform deep research on a routine $500 insider trade.
*   **Mechanism:** The `_should_continue_research` function checks `state['is_interesting']` and routes to either `deep_research` or `END`.

### Separation of Concerns
*   Each agent is a pure function (node). It takes the current state, does one specific job, and returns an update. This makes debugging easy—you can check the state after the `Discovery` node to see exactly why it rejected a signal.

---

## 4. Updated Technologies & Modernization

The current implementation uses `langgraph==0.2.28`. While functional, there are several "Modern LangGraph" patterns and features we could adopt to make it robust:

### A. Structured State Reducers (Critical)
*   **Current:** Agents manually append to lists: `current_path + ["discovery"]`. This is prone to race conditions if we ever run parallel nodes.
*   **Updated:** Use `Annotated` with `operator.add` or `add_messages`.
    ```python
    from operator import add
    from typing import Annotated

    class ResearchState(TypedDict):
        research_path: Annotated[List[str], add] # Automatically appends!
    ```
    *Result: Agents just return `{"research_path": ["discovery"]}` and it gets added automatically.*

### B. Structured Output (Reliability)
*   **Current:** `SynthesisAgent` asks for JSON and then uses `try/except` and string slicing (`response.find('{')`) to parse it. This is fragile.
*   **Updated:** Use **Tool Calling** or **Structured Output** (available in modern LangChain/LangGraph).
    ```python
    from pydantic import BaseModel

    class Insight(BaseModel):
        headline: str
        analysis: str
        score: float

    # Validates and forces JSON automatically
    structured_llm = llm.with_structured_output(Insight)
    response = structured_llm.invoke(messages)
    ```

### C. Subgraphs (Performance)
*   **Current:** `DeepResearchAgent` runs Level 1 -> 2 -> 3 -> 4 sequentially inside one big function.
*   **Updated:** Turn "Deep Research" into its own **Subgraph**. Level 1, 2, and 3 (Fundamentals, History, Context) could likely run **in parallel**, reducing total execution time by 60%.

### D. Persistence (Time Travel)
*   **Current:** The graph runs in memory. If it crashes, progress is lost.
*   **Updated:** Add a `checkpointer` (Postgres or Memory).
    ```python
    from langgraph.checkpoint.memory import MemorySaver
    workflow.compile(checkpointer=MemorySaver())
    ```
    *Benefit: You can "pause" after Discovery to have a human approve the Deep Research cost, or "rewind" to the validation step if the output is bad.*

### Summary Table

| Component | Current Implementation | Updated Recommendation |
| :--- | :--- | :--- |
| **Logic Flow** | Linear Script in Node | **Subgraphs** (Parallelize research levels) |
| **Output Parsing** | `json.loads` + String slicing | **`.with_structured_output(Pydantic)`** |
| **State Updates** | Manual List concatenation | **`Annotated[list, add]`** reducers |
| **Persistence** | None (In-memory) | **PostgresCheckpointer** for production resume |
