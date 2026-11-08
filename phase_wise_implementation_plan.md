# Cred Banking & FinTech Capstone — Phase-wise Implementation Plan

**Source:** Project Guideline.docx  
**Track:** Banking & FinTech (Cred)  
**Duration:** 14 days  
**Total marks:** 100  
**Submission:** One public GitHub repository containing the complete project.

> This plan is based on the uploaded project guideline. It covers all 16 tasks across the four project parts. Suggested implementation choices are identified as recommendations rather than requirements where applicable.

---

## 1. Project overview

The goal is to build one integrated banking support agent that:

- Answers loan-policy questions using a knowledge base authored for the project.
- Looks up loan application records from a deterministic dataset.
- Maintains conversation history within a session.
- Uses input and output guardrails.
- Has its draft reviewed by an independent AutoGen team.
- Exposes the application through FastAPI.
- Includes evaluation, structured observability, runtime controls, caching, and governance.

### Marks allocation

| Project part | Tasks | Marks |
|---|---:|---:|
| Part 1 — Dataset Design & RAG Core | 1–5 | 30 |
| Part 2 — CrewAI Multi-Agent Orchestration with Tools, Memory & Guardrails | 6–10 | 30 |
| Part 3 — Evaluation, Observability & FastAPI Deployment | 11–13 | 20 |
| Part 4 — Resilience & Governance | 14–16 | 20 |
| **Total** | **1–16** | **100** |

## 2. Overall architecture

```text
Customer / Support Staff
        |
        v
FastAPI: HTTP endpoints + WebSocket
        |
        v
Request handling and input guardrails
(PII masking, prompt-injection detection, budget)
        |
        v
CrewAI multi-agent crew
  |             |
  |             +--> Lookup Agent --> Loan application lookup tool
  |
  +--> Retrieval Agent --> RAG tool --> Selected ChromaDB collection
        |
        v
Response Composer --> Pydantic structured response
        |
        v
Output groundedness check
        |
        v
AutoGen review team
(Policy Compliance Reviewer + Final Editor)
        |
        v
Final response to user

Supporting components:
- Dataset: deterministic loan application records
- Knowledge base: 12+ banking-policy Markdown documents
- ChromaDB: separate fixed-size and sentence-based collections
- Session memory: LangChain in-process history
- Observability: JSONL logs with trace IDs and timings
- Governance: least autonomy, risk classification, request budget
- Cache: normalized-query cache for grounded generation
- Evaluation: 15-query LLM-as-judge test set
```

---

# 3. Phase-wise implementation plan

The 14-day schedule below is a proposed execution plan. Task requirements and acceptance criteria are taken from the project guideline.

## Phase 1 — Dataset engineering and knowledge-base creation

**Schedule:** Days 1–2  
**Project part:** Part 1 — Dataset Design & RAG Core  
**Tasks:** 1 and 2

### Task 1 — Design and validate the loan application dataset

**Objective:** Create a seeded, deterministic Python generator that produces a `LOAN_APPLICATIONS` list containing at least 40 records.

#### Required record fields

| Field | Requirement |
|---|---|
| `record_id` | Unique application identifier |
| `category` | Loan category |
| `status` | Application status |
| `loan_amount_inr` | Loan amount in INR |
| `days_since_created` | Integer from 0 through 30 |
| `flagged_for_fraud_review` | Boolean |

#### Required category vocabulary

- Personal Loan
- Home Loan
- Auto Loan
- Education Loan
- Business Loan

Every required category must have at least three records.

#### Required status vocabulary

- Submitted
- Under Review
- Approved
- Rejected
- Disbursed

Every required status must appear at least once.

#### Other validation requirements

- At least 40 total records.
- Fraud-flagged percentage must be between 10% and 30%, inclusive.
- If the first random draw does not meet the fraud percentage band, change the seed or weights and regenerate. Do not hand-edit individual records to force the percentage.
- Print and report counts per category, counts per status, and the fraud-flagged percentage.
- State the loan-amount range and explain the reasoning in one sentence.

#### Implementation steps

1. Define the category and status vocabularies.
2. Choose a random seed and document it.
3. Define category/status weights and document them.
4. Choose realistic loan-amount ranges and document the reasoning.
5. Generate records programmatically.
6. Validate field types, uniqueness, ranges, category counts, status coverage, and fraud percentage.
7. Print a validation summary.
8. Run the generator twice and confirm reproducibility.

#### Deliverables

- `dataset.py`
- `LOAN_APPLICATIONS` list
- Dataset validation output
- Category and status count report
- Fraud percentage report
- README documentation of seed, weights, and amount ranges

#### Completion checklist

- [ ] At least 40 records generated.
- [ ] Every required category appears at least three times.
- [ ] Every required status appears at least once.
- [ ] All required fields are present.
- [ ] `days_since_created` is an integer from 0 to 30.
- [ ] Fraud percentage is between 10% and 30%.
- [ ] Generator is deterministic.
- [ ] Dataset design choices are documented.

### Task 2 — Write the banking knowledge base

**Objective:** Author at least 12 policy documents, each containing 2–5 sentences or more as specified by the guideline, covering every required topic.

#### Required documents

| # | Document topic | Required coverage |
|---:|---|---|
| 1 | Loan eligibility criteria | Eligibility by loan type |
| 2 | EMI calculation rules | EMI calculation method and rules |
| 3 | Credit-card fee structure | Applicable card fees and charges |
| 4 | KYC document requirements | Required identity and address documents |
| 5 | Fraud-dispute resolution process | Reporting, investigation, and resolution |
| 6 | Account-closure process | Closure requirements and procedure |
| 7 | Interest-rate slabs | Interest-rate categories or slabs |
| 8 | Prepayment-penalty rules | Part-payment and foreclosure rules |
| 9 | Minimum-balance requirements | Minimum balance and related requirements |
| 10 | Credit-score impact factors | Factors affecting credit score |
| 11 | Joint-account rules | Joint ownership and account operation |
| 12 | NRI-account eligibility | NRI account eligibility requirements |

#### Implementation steps

1. Create a `knowledge_base/` directory.
2. Create one Markdown file for each required topic.
3. Write the policy content in your own words.
4. Ensure each document has the required minimum sentence count.
5. Keep policy statements internally consistent.
6. Use fabricated/illustrative banking policy values where needed and label them as illustrative rather than actual regulatory requirements.
7. Review each document against the topic checklist.

#### Deliverables

- At least 12 Markdown files in `knowledge_base/`
- A document inventory in the README

#### Completion checklist

- [ ] At least 12 documents exist.
- [ ] Every required topic is covered.
- [ ] Each document meets the sentence requirement.
- [ ] Content is original and written for this brief.

---

## Phase 2 — RAG engine and retrieval evaluation

**Schedule:** Days 3–4  
**Project part:** Part 1 — Dataset Design & RAG Core  
**Tasks:** 3, 4, and 5

### Task 3 — Implement and index two chunking strategies

**Objective:** Chunk every knowledge-base document using both required strategies, embed every chunk locally, and index each strategy in its own ChromaDB collection.

#### Required strategies

1. **Fixed-size with overlap**
2. **Sentence-based**

#### Required technical components

- Free, local SentenceTransformers embedding model.
- ChromaDB.
- Separate collection for each chunking strategy.
- `collection.upsert()` for indexing.
- Metadata that maps each chunk back to its parent document.

#### Suggested collection names

- `banking_fixed_chunks`
- `banking_sentence_chunks`

These names are implementation suggestions; the requirement is that the collections are separate.

#### Suggested chunk metadata

```python
{
    "document_name": "emi_calculation.md",
    "chunk_id": "emi_001",
    "chunking_strategy": "fixed_size"
}
```

#### Implementation steps

1. Read all Markdown documents.
2. Implement fixed-size chunking with overlap.
3. Implement sentence-based chunking.
4. Assign stable, unique chunk IDs.
5. Store parent document and strategy metadata.
6. Load a free local SentenceTransformers model.
7. Embed every chunk in both sets.
8. Create the two ChromaDB collections.
9. Upsert each set into its corresponding collection.
10. Verify collection counts and test retrieval from both.

#### Deliverables

- `chunking.py`
- `embeddings.py`
- `vector_store.py`
- Persistent ChromaDB index or reproducible indexing script
- Collection verification output

#### Completion checklist

- [ ] Both chunking strategies are implemented.
- [ ] Every chunk is embedded locally.
- [ ] Two separate ChromaDB collections exist.
- [ ] `upsert()` is used.
- [ ] Parent-document metadata is retained.
- [ ] Both collections return sensible results for a sample query.

### Task 4 — Implement grounded generation and calibrate the fallback threshold

**Objective:** Retrieve relevant chunks and generate answers using only retrieved context, with an empirically calibrated “I don't know” threshold.

#### Required behaviour

1. Accept a query.
2. Embed the query using the local model.
3. Retrieve top-k chunks from a collection.
4. Measure top-1 cosine similarity.
5. Compare the measured similarity with a threshold.
6. If retrieval is insufficient, return an “I don't know” fallback.
7. Otherwise, generate an answer using only retrieved context.

#### Calibration requirements

Measure top-1 cosine similarity for:

- At least 3 in-scope queries.
- At least 2 deliberately out-of-scope queries.

Choose the threshold based on the two clusters actually observed. Do not use an untested preset such as 0.5, 0.6, or 0.7.

If the measured clusters overlap, document the limitation instead of claiming that the threshold perfectly separates them.

#### Demonstration requirements

- At least 5 real in-scope queries.
- At least 1 deliberately out-of-scope query that triggers the fallback.
- Measured similarity values.
- Selected threshold and explanation in `README.md`.

#### Implementation steps

1. Implement the retrieval function.
2. Return top-k chunks and similarity scores.
3. Run the calibration queries.
4. Record top-1 cosine similarity for each query.
5. Inspect the in-scope and out-of-scope score distributions.
6. Select and document a threshold supported by the measurements.
7. Implement the fallback.
8. Generate responses constrained to retrieved context.
9. Save demonstration transcripts.

#### Deliverables

- `retrieval.py`
- `generation.py`
- Calibration results
- Five in-scope and one out-of-scope demonstration
- README threshold explanation

#### Completion checklist

- [ ] At least three in-scope calibration scores measured.
- [ ] At least two out-of-scope calibration scores measured.
- [ ] Threshold chosen from observed scores.
- [ ] Five in-scope demonstrations pass.
- [ ] One out-of-scope demonstration triggers fallback.
- [ ] Threshold and measured values appear in README.

### Task 5 — Evaluate and compare both chunking strategies

**Objective:** Compare fixed-size and sentence-based retrieval using document-level precision and recall on the same five or more queries.

#### Required evaluation method

1. Use the same at least five queries from Task 4.
2. Define expected relevant parent documents for each query.
3. Retrieve top-k chunks from the fixed-size collection.
4. Map chunks to parent documents.
5. Deduplicate parent documents.
6. Calculate document-level precision and recall.
7. Repeat for the sentence-based collection.
8. Show per-query arithmetic for both collections.
9. Write a 2–3 sentence recommendation citing the measured numbers.

#### Formulas

\[
Precision@k =
\frac{\text{Relevant retrieved documents}}
{\text{All unique retrieved documents}}
\]

\[
Recall@k =
\frac{\text{Relevant retrieved documents}}
{\text{All expected relevant documents}}
\]

#### Required report structure

| Query | Fixed precision | Fixed recall | Sentence precision | Sentence recall |
|---|---:|---:|---:|---:|
| Query 1 | Measured | Measured | Measured | Measured |
| Query 2 | Measured | Measured | Measured | Measured |
| Query 3 | Measured | Measured | Measured | Measured |
| Query 4 | Measured | Measured | Measured | Measured |
| Query 5 | Measured | Measured | Measured | Measured |

Show the numerator and denominator for every individual calculation, not only the final decimal values.

#### Deliverables

- `evaluation.py`
- Per-query arithmetic for both collections
- Comparison report
- 2–3 sentence deployment recommendation

#### Completion checklist

- [ ] Same queries used for both collections.
- [ ] Chunks mapped to parent documents.
- [ ] Parent documents deduplicated.
- [ ] Precision and recall calculated separately.
- [ ] Per-query arithmetic displayed.
- [ ] Recommendation cites actual results.

**Phase 2 exit condition:** Both collections are indexed and evaluated. Select the recommended collection and treat it as the fixed RAG input for Part 2.

---

## Phase 3 — Loan lookup business logic

**Schedule:** Day 5  
**Project part:** Part 2 — CrewAI Multi-Agent Orchestration  
**Task:** 6

### Task 6 — Build the loan application status tool and escalation score

**Objective:** Implement a deterministic lookup function using `dataset.py`.

#### Required function

```python
def check_loan_application_status(record_id: str) -> dict:
    ...
```

#### Required return information

- Application status
- Loan amount in INR
- Designed escalation score between 0 and 1

The score must combine:

- `flagged_for_fraud_review`
- A normalized recency/age signal derived from `days_since_created`

#### Suggested scoring design

The following is a proposed formula, not a formula prescribed by the guideline:

\[
R = \frac{days\_since\_created}{30}
\]

\[
S = 0.7F + 0.3R
\]

Where:

- \(F=1\) if fraud review is flagged, otherwise \(F=0\).
- \(R\) is normalized application age.
- \(S\) is the escalation score.

#### Implementation steps

1. Import `LOAN_APPLICATIONS`.
2. Create a lookup structure keyed by `record_id`.
3. Find the requested application.
4. Handle unknown IDs.
5. Normalize application age.
6. Calculate the score using the documented formula.
7. Analyse the generated score distribution.
8. Select an escalation threshold justified by the dataset.
9. Return the required fields.
10. Test flagged and unflagged records.

#### Deliverables

- `loan_lookup_tool.py`
- Scoring formula
- Threshold justification
- Lookup test results

#### Completion checklist

- [ ] Correct application lookup.
- [ ] Correct status and amount.
- [ ] Score combines fraud flag and normalized age.
- [ ] Score is always in `[0, 1]`.
- [ ] Escalation threshold is justified by generated-data distribution.
- [ ] Unknown IDs are handled safely.

---

## Phase 4 — CrewAI agents, memory, structured outputs, and guardrails

**Schedule:** Days 6–7  
**Project part:** Part 2  
**Tasks:** 7, 8, 9, and 10

### Task 7 — Build the CrewAI multi-agent crew

**Objective:** Build and execute a crew with at least three agents.

#### Required agents

| Agent | Responsibility | Tool |
|---|---|---|
| Retrieval Agent | Retrieves banking-policy information | RAG retrieval tool |
| Lookup Agent | Retrieves loan application details | `check_loan_application_status` |
| Response Composer | Combines agent outputs into one final draft | No mandatory tool |

#### Implementation steps

1. Wrap the selected RAG pipeline as a CrewAI tool.
2. Wrap the loan lookup function as a CrewAI tool.
3. Create the Retrieval Agent.
4. Create the Lookup Agent.
5. Create the Response Composer.
6. Define CrewAI tasks and dependencies.
7. Configure the crew.
8. Execute using `.kickoff()`.
9. Demonstrate a policy query that invokes the RAG tool.
10. Demonstrate a separate application query that invokes the lookup tool.
11. Capture tool invocation evidence.

#### MOCK_LLM requirements

- Extend `crewai.llms.base_llm.BaseLLM`.
- Do not require API keys or network access for graded transcripts.
- Parse the model's generated text, not the ReAct system-prompt template, when interpreting tool observations.
- Dispatch tool calls using their declared argument schema rather than matching tool names.
- Set `CREWAI_DISABLE_TELEMETRY=true` (or `OTEL_SDK_DISABLED=true`) before crew execution.

#### Deliverables

- `mock_llm.py`
- `rag_tool.py`
- `loan_lookup_tool.py`
- `retrieval_agent.py`
- `lookup_agent.py`
- `composer_agent.py`
- `crew.py`
- Tool invocation transcripts

#### Completion checklist

- [ ] At least three agents.
- [ ] RAG tool invoked through `.kickoff()`.
- [ ] Lookup tool invoked through `.kickoff()`.
- [ ] Different sample queries demonstrate the two tools.
- [ ] Custom CrewAI MOCK_LLM works.
- [ ] Telemetry disabled before execution.

### Task 8 — Add session-based memory

**Objective:** Maintain conversation history across turns within one process run and demonstrate a separate fresh conversation with no prior state.

#### Suggested technology

- `InMemoryChatMessageHistory`
- `RunnableWithMessageHistory`
- Session IDs

#### Implementation steps

1. Create a session history store.
2. Implement a history retrieval function.
3. Connect history to the conversation pipeline.
4. Store user and assistant messages.
5. Run a multi-turn conversation using one session ID.
6. Demonstrate that a later turn uses previously supplied context.
7. Start a different session ID.
8. Demonstrate that the previous session's context is absent.

#### Required transcripts

**Existing session**

- User supplies an application ID.
- User later asks for its status without repeating the ID.
- System correctly uses the prior session context.

**Fresh session**

- User asks for the status without providing an ID.
- System asks for the application ID because no prior context is available.

#### Deliverables

- `session_memory.py`
- Existing-session transcript
- Fresh-session transcript

#### Completion checklist

- [ ] Session history is maintained within the process.
- [ ] Context carries across turns.
- [ ] Separate session starts with no previous context.
- [ ] Both transcripts are saved.

### Task 9 — Add Pydantic structured output

**Objective:** Ensure every CrewAI response conforms to a declared Pydantic schema and is validated in code.

#### Implementation steps

1. Define a Pydantic `BaseModel`.
2. Add fields appropriate to policy and application queries.
3. Configure the supported CrewAI structured response mechanism (`response_format`).
4. Validate every final crew response.
5. Handle invalid output safely.

#### Suggested fields

```python
class BankingResponse(BaseModel):
    query_type: str
    answer: str
    record_id: str | None = None
    application_status: str | None = None
    loan_amount_inr: int | None = None
    escalation_score: float | None = None
    sources: list[str]
    grounded: bool
```

Add suitable field constraints, including a `[0, 1]` constraint for escalation scores.

#### Deliverables

- `response_schema.py`
- CrewAI structured-output configuration
- Validation demonstration

#### Completion checklist

- [ ] Pydantic model defined.
- [ ] CrewAI configured to produce structured output.
- [ ] Every final response validated.
- [ ] Invalid responses handled.

### Task 10 — Implement guardrails

**Objective:** Implement input-side PII masking, prompt-injection detection, and output-side groundedness checks.

#### A. PII masking

Required fixed-format fields:

- PAN number
- Aadhaar number
- Bank account number

Implementation steps:

1. Define field-specific regular expressions.
2. Detect matching values in user input.
3. Mask the values before agent processing.
4. Apply the same masking before logging.
5. Demonstrate masking with fabricated examples.

Applicant names and income figures are explicitly out of scope for the keyless MOCK_LLM-only masking requirement. Use fabricated values only.

#### B. Prompt-injection detection

Implementation steps:

1. Define suspicious instruction patterns and/or deterministic detection rules.
2. Detect malicious instructions before agent execution.
3. Block or safely reject the request.
4. Record a safe detection result.
5. Demonstrate with a deliberate injection test.

#### C. Output-side groundedness

Implementation steps:

1. Capture the retrieved context.
2. Check whether the query has sufficient retrieval support.
3. Constrain generation to the retrieved context.
4. Check the response against the available evidence.
5. Refuse unsupported questions or claims.

Similarity alone is a relevance signal; it does not prove that every generated sentence is factually supported. Under MOCK_LLM, document this limitation and use deterministic checks.

#### Deliverables

- `pii_masking.py`
- `prompt_injection.py`
- `groundedness.py`
- Three deliberate guardrail test transcripts

#### Completion checklist

- [ ] PAN masking demonstrated.
- [ ] Aadhaar masking demonstrated.
- [ ] Bank account masking demonstrated.
- [ ] Prompt injection detected and blocked.
- [ ] Unsupported question triggers groundedness fallback.

---

## Phase 5 — FastAPI deployment and structured logging

**Schedule:** Days 8–9  
**Project part:** Part 3 — Evaluation, Observability & FastAPI Deployment  
**Tasks:** 11 and 12

### Task 11 — Deploy through FastAPI

**Objective:** Expose the existing CrewAI application through at least two HTTP endpoints and one WebSocket endpoint.

#### Required endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/ask` | POST | Submit a banking query |
| `/add-document` | POST | Add a knowledge-base document |
| `/ws/chat` | WebSocket | Real-time multi-turn chat |

The paths are examples; equivalent endpoints are acceptable.

#### Implementation steps

1. Create the FastAPI application.
2. Load the existing RAG and CrewAI components.
3. Define Pydantic request/response models.
4. Implement the query endpoint.
5. Implement document ingestion and indexing.
6. Implement WebSocket chat.
7. Maintain session context across WebSocket messages.
8. Catch `WebSocketDisconnect`.
9. Verify that a disconnect does not crash the server.
10. Test the endpoints.

#### Deliverables

- `main.py`
- `api_models.py`
- HTTP endpoint code
- WebSocket code
- API test results

#### Completion checklist

- [ ] At least two working HTTP endpoints.
- [ ] One working WebSocket endpoint.
- [ ] Pydantic models used where applicable.
- [ ] Multi-turn WebSocket works.
- [ ] Client disconnect handled safely.

### Task 12 — Add structured logging

**Objective:** Write one JSON Lines log entry per request with a trace ID and timing information.

#### Required log information

| Field | Purpose |
|---|---|
| `trace_id` | Request correlation |
| `timestamp` | Request time |
| `request_type` | HTTP or WebSocket |
| `request_duration_ms` | Processing duration |
| `status` | Success/failure |
| `query_type` | Policy/application query |

Additional fields may include cache status, session ID, retrieval time, and agent execution time.

#### Implementation steps

1. Generate a unique trace ID for each request.
2. Record request start time.
3. Apply PII masking.
4. Log only sanitized request text.
5. Execute the request.
6. Record execution duration.
7. Record the final request status.
8. Write exactly one JSON object per request line.
9. Handle exceptions without exposing raw PII.
10. Inspect the log file for sensitive values.

#### Deliverables

- `structured_logger.py`
- `application.jsonl`
- Logging demonstration

#### Completion checklist

- [ ] One JSONL entry per request.
- [ ] Every entry has a trace ID.
- [ ] Timing information recorded.
- [ ] Request text masked before logging.
- [ ] No raw fixed-format PII appears on disk.

### Task 13 — Evaluate with LLM-as-judge

**Objective:** Evaluate 15 queries on Accuracy, Grounding, Completeness, and Safety under MOCK_LLM.

#### Test-set requirements

- Exactly 15 queries.
- At least one query for each of the 12 required knowledge-base topics.
- At least two deliberately out-of-scope or edge-case queries.

#### Required evaluation dimensions

| Metric | Evaluation purpose |
|---|---|
| Accuracy | Correctness of the response |
| Grounding | Support from retrieved context |
| Completeness | Coverage of relevant aspects |
| Safety | Compliance with safety and privacy requirements |

#### Implementation steps

1. Create the 15-query evaluation set.
2. Include all 12 required knowledge-base topics.
3. Include at least two out-of-scope or edge-case questions.
4. Execute the complete system on every query.
5. Capture the query, response, and relevant context.
6. Create an LLM-as-judge prompt.
7. Score all four dimensions for every query.
8. Calculate each metric's average across 15 queries.
9. Save detailed results.

A consistent 1–5 scoring scale is a suggested choice; the guideline requires the four scores but does not prescribe their numerical scale.

#### Deliverables

- `test_queries.py`
- `llm_judge.py`
- `evaluation_runner.py`
- Per-query evaluation results
- Four average scores

#### Completion checklist

- [ ] 15 queries evaluated.
- [ ] All 12 knowledge-base topics represented.
- [ ] At least two out-of-scope or edge-case queries.
- [ ] Four scores per query.
- [ ] Four averages reported.
- [ ] Evaluation runs under MOCK_LLM.

---

## Phase 6 — AutoGen independent review stage

**Schedule:** Day 10  
**Project part:** Part 4 — Resilience & Governance  
**Task:** 14

### Task 14 — Build a two-agent AutoGen review team

**Objective:** Review the CrewAI Composer's draft answer using an independent two-agent AutoGen team.

#### Required agents

| Agent | Responsibility |
|---|---|
| Policy-Compliance-Reviewer | Checks support from retrieved context and policy compliance |
| Final-Editor | Approves the draft unchanged or revises it |

#### Required orchestration

- Use `RoundRobinGroupChat`.
- Set `max_turns=2`.
- Pass the CrewAI draft and original retrieved context to the team.
- Configure the Final-Editor with a Pydantic structured output.

#### Required verdict model

```python
class VerdictModel(BaseModel):
    approved: bool
    final_answer: str
    reason: str
```

#### Important AutoGen configuration

When using:

```python
output_content_type=VerdictModel
```

The team must also be created with:

```python
custom_message_types=[
    StructuredMessage[VerdictModel]
]
```

The guideline warns that failing to register the structured message type can cause a `ValueError`.

#### Implementation steps

1. Configure AutoGen AgentChat and Core.
2. Configure MOCK_LLM.
3. Create the Policy-Compliance-Reviewer.
4. Create the Final-Editor.
5. Create the Pydantic verdict model.
6. Register the structured message type with the team.
7. Configure `RoundRobinGroupChat(max_turns=2)`.
8. Pass the Composer's draft and original retrieved context.
9. Capture the verdict.
10. Return the approved/revised answer.

#### Mandatory demonstrations

**Demonstration 1 — Approve unchanged**

Use a draft that is already supported by the retrieved context.

**Demonstration 2 — Revise**

Deliberately inject an unsupported claim into a test draft. Demonstrate that the review team identifies it and revises the answer.

#### Deliverables

- `autogen_review.py`
- `verdict_schema.py`
- Approval transcript
- Revision transcript

#### Completion checklist

- [ ] Two AutoGen agents configured.
- [ ] Round-robin team runs with two turns.
- [ ] Draft and original retrieved context passed to team.
- [ ] Pydantic verdict returned.
- [ ] One draft approved unchanged.
- [ ] One deliberately flawed draft revised.

---

## Phase 7 — AI governance, runtime budget, and caching

**Schedule:** Days 11–12  
**Project part:** Part 4  
**Tasks:** 15 and 16

### Task 15 — Apply the four-layer AI-governance model

**Objective:** Document and implement governance controls, with explicit enforcement of least autonomy and a runtime request budget.

#### A. Application layer — Least autonomy

Only the Lookup Agent may call `check_loan_application_status`.

Implementation steps:

1. Register the lookup tool only with the Lookup Agent.
2. Do not register it with Retrieval Agent.
3. Do not register it with Response Composer.
4. Add permission validation if appropriate.
5. Demonstrate that other agents cannot call the lookup tool.
6. Explain the principle of least autonomy in the README.

Required access matrix:

| Agent | Lookup tool |
|---|---|
| Retrieval Agent | Denied |
| Lookup Agent | Allowed |
| Response Composer | Denied |

#### B. Risk classification

Classify the application using the guideline's Low/Medium/High scheme.

The project handles financial data and loan applications. Under the guideline's examples, financial data is High Risk.

Document a paragraph justifying the classification, considering the consequences of incorrect financial information, unauthorized access, PII exposure, and incorrect escalation recommendations.

#### C. Runtime layer — Per-request token/cost budget

Implementation steps:

1. Define a maximum request budget.
2. Estimate the request's token/cost requirement.
3. Apply a per-request budget check.
4. Reject requests exceeding the limit.
5. Record the rejection.
6. Demonstrate an intentionally oversized request.

The numerical budget is a design choice. Make clear that a MOCK_LLM token/cost budget is a deterministic simulation, not an actual API bill.

#### D. Document the four layers

The guideline explicitly describes Application and Runtime controls. For a complete implementation framework, document the remaining Data and Model/Agent controls as proposed layers:

| Layer | Suggested controls |
|---|---|
| Data | Input validation, PII protection, knowledge-base integrity |
| Model/Agent | Constrained outputs, grounding, independent review |
| Application | Least autonomy, tool permissions |
| Runtime | Budget enforcement, execution limits, monitoring |

#### Deliverables

- `tool_permissions.py`
- `budget_manager.py`
- `risk_assessment.md`
- Unauthorized-tool-access demonstration
- Budget rejection transcript

#### Completion checklist

- [ ] Lookup tool is available only to Lookup Agent.
- [ ] Unauthorized access is blocked or never granted.
- [ ] Risk level is classified and justified.
- [ ] Per-request budget enforced.
- [ ] Oversized request rejected.
- [ ] Four governance layers documented.

### Task 16 — Implement response caching

**Objective:** Cache grounded-generation results by normalized query text and demonstrate a real cache hit.

#### Implementation steps

1. Create an in-memory cache.
2. Normalize query text.
3. Use normalized text as the cache key.
4. Check the cache before retrieval/generation.
5. Return cached grounded-generation results on a hit.
6. Execute retrieval/generation on a miss.
7. Store the result.
8. Track hit/miss counters or timings.
9. Demonstrate a repeated identical query.

#### Example normalization

```python
def normalize_query(query: str) -> str:
    return " ".join(query.lower().split())
```

#### Required demonstration

- First request: cache miss and normal processing.
- Second equivalent request: cache hit and no redundant generation/tool call.
- Before/after evidence: call counter or timing comparison.

Cache only appropriate grounded-generation results. Do not use a query-only cache key for personalized application-status responses, which need fresh record lookup.

#### Deliverables

- `response_cache.py`
- Cache statistics
- Before/after demonstration transcript

#### Completion checklist

- [ ] In-memory cache implemented.
- [ ] Query normalization implemented.
- [ ] Repeated query produces a real hit.
- [ ] Redundant generation/tool call avoided.
- [ ] Before/after evidence recorded.

---

## Phase 8 — Integration, end-to-end testing, and GitHub submission

**Schedule:** Days 13–14  
**Scope:** All 16 tasks

### Step 1 — Integrate the complete request lifecycle

Recommended processing order:

1. Receive request through FastAPI.
2. Generate trace ID.
3. Apply input PII masking.
4. Detect prompt injection.
5. Enforce runtime budget.
6. Check applicable response cache.
7. Invoke CrewAI.
8. Retrieve policy information or application data.
9. Generate structured response.
10. Apply groundedness validation.
11. Submit the draft and original retrieved context to AutoGen.
12. Validate the final verdict.
13. Return the final answer.
14. Write structured logs.

### Step 2 — Run end-to-end scenarios

| Scenario | Expected behaviour |
|---|---|
| Banking policy question | RAG retrieves relevant policy |
| Loan status question | Lookup Agent retrieves application |
| Fraud-flagged application | Escalation score calculated |
| Multi-turn conversation | Previous session context retained |
| New session | Previous context absent |
| PAN/Aadhaar/account supplied | PII masked |
| Prompt injection | Request safely blocked |
| Unsupported query | Fallback returned |
| Unsupported claim in draft | AutoGen revises |
| Oversized request | Budget rejection |
| Repeated query | Cache hit |
| WebSocket disconnect | Server remains operational |

### Step 3 — Save execution transcripts

Recommended repository structure:

```text
transcripts/
    dataset_validation.md
    rag_calibration.md
    rag_comparison.md
    crew_execution.md
    session_memory.md
    guardrail_tests.md
    api_tests.md
    llm_judge_results.md
    autogen_review.md
    governance_tests.md
    cache_demo.md
```

### Step 4 — Complete README.md

The README should include:

1. Project title.
2. Confirmation that the Cred Banking & FinTech track was completed.
3. Project objective.
4. Architecture.
5. Technology stack.
6. Dataset seed, weights, and amount ranges.
7. Dataset validation results.
8. Knowledge-base document inventory.
9. Chunking strategies and embedding model.
10. ChromaDB collection names.
11. Measured similarity scores and chosen threshold.
12. Precision/recall results and deployment recommendation.
13. Escalation formula and threshold justification.
14. CrewAI architecture and tool invocation.
15. MOCK_LLM implementation and zero-network execution.
16. Session memory demonstrations.
17. Pydantic structured output.
18. Guardrail demonstrations.
19. FastAPI endpoint instructions.
20. Structured logging.
21. Four evaluation scores and averages.
22. AutoGen review results.
23. Governance and risk classification.
24. Runtime budget demonstration.
25. Cache hit demonstration.
26. Installation and execution instructions.

### Step 5 — Prepare the public GitHub repository

The complete project must be submitted through one public GitHub repository link.

The repository should contain:

- Dataset generator and validation.
- All knowledge-base documents.
- RAG and evaluation code.
- CrewAI agents and tools.
- Session memory and guardrails.
- FastAPI deployment.
- Structured logging.
- AutoGen review team.
- Governance and caching.
- Test code and execution transcripts.
- README and requirements.

Do not submit PDFs, screenshots, slide decks, presentations, videos, or audio; the guideline says these are not required or accepted.

---

# 4. Recommended GitHub repository structure

```text
cred-banking-ai-agent/
│
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── dataset/
│   ├── __init__.py
│   ├── dataset.py
│   └── validation.py
│
├── knowledge_base/
│   ├── loan_eligibility.md
│   ├── emi_calculation.md
│   ├── credit_card_fees.md
│   ├── kyc_requirements.md
│   ├── fraud_disputes.md
│   ├── account_closure.md
│   ├── interest_rates.md
│   ├── prepayment_rules.md
│   ├── minimum_balance.md
│   ├── credit_score.md
│   ├── joint_accounts.md
│   └── nri_accounts.md
│
├── rag/
│   ├── chunking.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── retrieval.py
│   ├── generation.py
│   └── evaluation.py
│
├── tools/
│   ├── rag_tool.py
│   └── loan_lookup_tool.py
│
├── agents/
│   ├── mock_llm.py
│   ├── retrieval_agent.py
│   ├── lookup_agent.py
│   ├── composer_agent.py
│   └── crew.py
│
├── memory/
│   └── session_memory.py
│
├── schemas/
│   ├── response_schema.py
│   ├── api_models.py
│   └── verdict_schema.py
│
├── guardrails/
│   ├── pii_masking.py
│   ├── prompt_injection.py
│   └── groundedness.py
│
├── review/
│   └── autogen_review.py
│
├── governance/
│   ├── tool_permissions.py
│   ├── budget_manager.py
│   └── risk_assessment.md
│
├── cache/
│   └── response_cache.py
│
├── evaluation/
│   ├── test_queries.py
│   ├── llm_judge.py
│   └── evaluation_runner.py
│
├── api/
│   ├── main.py
│   ├── routes.py
│   └── websocket.py
│
├── logging/
│   └── structured_logger.py
│
├── tests/
│   ├── test_dataset.py
│   ├── test_rag.py
│   ├── test_lookup.py
│   ├── test_crew.py
│   ├── test_memory.py
│   ├── test_guardrails.py
│   ├── test_api.py
│   ├── test_review.py
│   ├── test_governance.py
│   └── test_cache.py
│
├── transcripts/
│   ├── dataset_validation.md
│   ├── rag_evaluation.md
│   ├── crew_execution.md
│   ├── memory_demo.md
│   ├── guardrails_demo.md
│   ├── api_demo.md
│   ├── judge_results.md
│   ├── autogen_review.md
│   └── governance_cache_demo.md
│
├── chroma_db/
└── logs/
```

**Repository notes:**

- Keep generated ChromaDB files out of Git if they become large; include a reproducible indexing script.
- Do not commit API keys or real personal information.
- Keep dataset generation deterministic.
- Use fabricated applicant data.
- Ensure the vector database can be rebuilt from the Markdown knowledge base.

---

# 5. Fourteen-day execution schedule

| Day | Planned work | Tasks |
|---|---|---|
| 1 | Dataset generation and validation | 1 |
| 2 | Create 12 banking policy documents | 2 |
| 3 | Chunking, embeddings, ChromaDB | 3 |
| 4 | Grounded generation and retrieval evaluation | 4, 5 |
| 5 | Loan lookup and escalation scoring | 6 |
| 6 | CrewAI agents and tool integration | 7 |
| 7 | Memory, Pydantic and guardrails | 8, 9, 10 |
| 8 | FastAPI HTTP and WebSocket endpoints | 11 |
| 9 | Structured logging and LLM-as-judge | 12, 13 |
| 10 | AutoGen review | 14 |
| 11 | Least autonomy and risk classification | 15 |
| 12 | Runtime budget and response caching | 15, 16 |
| 13 | End-to-end integration and testing | All |
| 14 | README, transcripts and GitHub submission | All |

### Time allocation

| Workstream | Days |
|---|---:|
| Dataset and RAG | 4 |
| CrewAI and guardrails | 3 |
| FastAPI and evaluation | 2 |
| AutoGen and governance | 3 |
| Integration and submission | 2 |
| **Total** | **14** |

---

# 6. Important technical requirements and pitfalls

| Area | Requirement |
|---|---|
| MOCK_LLM | Must work without API keys or network access |
| CrewAI LLM | Extend `crewai.llms.base_llm.BaseLLM` |
| Tool dispatch | Use the tool's declared argument schema |
| ReAct parsing | Parse generated model text, not the system-prompt example `Observation:` |
| Telemetry | Set `CREWAI_DISABLE_TELEMETRY=true` before crew execution |
| RAG calibration | Use measured cosine similarity scores |
| ChromaDB | Separate collections for both strategies |
| Evaluation | Deduplicate parent documents before precision/recall |
| Session memory | Demonstrate existing and fresh sessions |
| Structured output | Validate every CrewAI response |
| Logging | Mask PII before writing request text to disk |
| AutoGen | `RoundRobinGroupChat(max_turns=2)` |
| AutoGen output | Register `StructuredMessage[VerdictModel]` |
| Governance | Only Lookup Agent receives lookup-tool access |
| Runtime | Reject requests exceeding the per-request budget |
| Cache | Demonstrate a real cache hit and avoided redundant work |

## 7. Final project acceptance checklist

Use this checklist before submitting the repository.

### Part 1 — Dataset and RAG

- [ ] Task 1: Deterministic dataset with at least 40 valid records.
- [ ] Task 2: Twelve or more banking policy documents.
- [ ] Task 3: Two chunking strategies and two ChromaDB collections.
- [ ] Task 4: Empirically calibrated grounded generation.
- [ ] Task 5: Per-query document-level precision and recall for both collections.

### Part 2 — Multi-agent orchestration

- [ ] Task 6: Loan lookup and designed escalation score.
- [ ] Task 7: Three CrewAI agents and actual tool invocation.
- [ ] Task 8: Multi-turn memory and fresh-session demonstration.
- [ ] Task 9: Pydantic structured output and validation.
- [ ] Task 10: PII, prompt-injection, and groundedness guardrails.

### Part 3 — Deployment and evaluation

- [ ] Task 11: Two HTTP endpoints and one WebSocket endpoint.
- [ ] Task 12: JSONL structured logging with trace IDs and PII masking.
- [ ] Task 13: Fifteen-query evaluation with four scores per query and averages.

### Part 4 — Resilience and governance

- [ ] Task 14: AutoGen review approval and revision demonstrations.
- [ ] Task 15: Least autonomy, risk classification, and runtime budget rejection.
- [ ] Task 16: Normalized-query caching with a demonstrated cache hit.

### Submission

- [ ] One public GitHub repository.
- [ ] Complete source code and knowledge base.
- [ ] `requirements.txt`.
- [ ] README confirms MOCK_LLM and zero API-key execution.
- [ ] All required transcripts included.
- [ ] Repository reproducibly rebuilds the vector database.

---

## 8. Implementation recommendations

1. **Implement MOCK_LLM early.** Do not leave custom CrewAI and AutoGen mock execution until the final integration stage.
2. **Freeze the RAG collection before CrewAI integration.** Complete the two-collection evaluation and select one deployment strategy first.
3. **Keep business logic deterministic.** Escalation, PII masking, permission checks, budgets, and cache behaviour should be controlled by Python functions.
4. **Keep AutoGen independent.** The review team must inspect the Composer's draft against the original retrieved context.
5. **Reserve the final two days for integration.** Avoid adding new features during the submission stage.

## 9. Recommended starting milestone

Begin with **Phase 1 — Tasks 1 and 2**.

The first implementation milestone should produce:

```text
dataset.py
    |
    +-- LOAN_APPLICATIONS
    +-- Dataset validation
    +-- Category counts
    +-- Status counts
    +-- Fraud percentage

knowledge_base/
    |
    +-- 12 banking policy Markdown documents
```

Once these two deliverables are validated, proceed to Phase 2 and build the dual-strategy RAG pipeline.

**Project completion principle:** Every task should have working code, a deliberate test case, recorded evidence, and corresponding README documentation. A function existing in the repository is not sufficient evidence that its acceptance criterion has been met.
