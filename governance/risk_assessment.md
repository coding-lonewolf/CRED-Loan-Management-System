# AI Governance Framework & Risk Assessment

## 1. Risk Classification & Justification

### Classification: HIGH RISK

Under the system risk categorization taxonomy (Low / Medium / High), the **Cred Banking & FinTech Domain Support Agent** is formally classified as a **High-Risk AI System**.

### Justification

The operational domain of this agent encompasses core retail banking services, credit card fee structures, customer identity verification (KYC), and individual retail loan applications with financial exposure reaching up to INR 75,00,000. In accordance with Reserve Bank of India (RBI) IT Governance guidelines and the Digital Personal Data Protection (DPDP) Act 2023, automated systems interacting with sensitive financial assets carry substantial inherent risks:

1. **Consequences of Incorrect Financial Information:** Generative hallucinations regarding interest calculation conventions, prepayment penalty exemptions, or foreclosure timelines can directly induce customer financial misdirection, missed EMI penalties, distorted debt servicing, and severe regulatory non-compliance liability for the lending institution.
2. **Unauthorized Access to Loan Records:** Permitting arbitrary or unauthenticated agents to inspect customer loan files (`record_id`, sanction amounts, approval statuses) breaches strict banking secrecy duties and customer financial confidentiality covenants.
3. **Severe PII Exposure Impact:** Financial customer interactions regularly present statutory personal identifiers—Permanent Account Number (PAN), 12-digit Aadhaar credentials, and 9-to-18-digit core banking account numbers. Leakage or unmasked logging of these credentials enables identity theft, financial fraud, and statutory penalties under DPDP 2023 and the Information Technology Act 2000.
4. **Flawed Escalation Scoring Risks:** The designed escalation score combines fraud indicators with application age. If an erroneous system fails to flag an active fraud inquiry (\(F=1\)), high-risk fraudulent transactions proceed unchecked. Conversely, false-positive escalations flood human compliance desks, leading to severe operational backlogs and degraded customer trust.

---

## 2. Four-Layer AI Governance Model

To mitigate the High-Risk profile identified above, this system institutes an end-to-end four-layer defense-in-depth governance framework:

| Layer | Governance Domain | Controls Implemented in System |
|---|---|---|
| **Layer 1: Data Governance** | Input validation, PII hygiene, KB integrity | • Deterministic regex PII masking (PAN, Aadhaar, Account numbers)<br>• Pre-write sanitization before disk logging<br>• Immutable 60-record deterministic synthetic dataset (`seed=20261026`)<br>• Version-controlled 12-document banking policy repository |
| **Layer 2: Model & Agent Governance** | Output constraints, hallucination defense, peer auditing | • Bounded Pydantic schema validation (`BankingResponse`)<br>• Cosine similarity groundedness guardrail threshold (\(\ge 0.50\))<br>• Deterministic ReAct orchestration with strict argument dispatch<br>• Independent two-agent AutoGen review team (`RoundRobinGroupChat`, 2 turns) with structured verdict verification (`VerdictModel`) |
| **Layer 3: Application Governance** | Least autonomy, role segregation, access control | • Strict tool permission matrix restricting tool dispatch by agent identity<br>• Lookup tool restricted strictly to the Lookup Agent<br>• Retrieval Agent and Response Composer denied access to loan record lookups<br>• Pure-synthesis isolation for the Response Composer (0 tools) |
| **Layer 4: Runtime Governance** | Resource caps, abuse prevention, audit tracking | • Deterministic per-request token budget ceiling (2,000 tokens)<br>• Intentional oversized request interception and blocking<br>• Normalized response caching for general policy questions<br>• Structured single-line JSONL audit logging with mandatory `trace_id` and latency metrics |

---

## 3. Application Layer: Least Autonomy Tool Access Matrix

Under the principle of least autonomy, each agent is granted only the absolute minimum tool privileges required to satisfy its declared role. No agent possesses blanket access to system capabilities.

| Agent | Role | Authorized Tools | Denied Tools | Least Autonomy Justification |
|---|---|---|---|---|
| **Retrieval Agent** | Policy document search | `search_knowledge_base`, `RAGTool`, `rag_policy_retrieval_tool` | `check_loan_application_status`, `LoanLookupTool` | Retrieval agent must only consult public banking policy; allowing loan lookups risks unauthorized customer record queries. |
| **Lookup Agent** | Application record lookup | `check_loan_application_status`, `LoanLookupTool` | `search_knowledge_base`, `RAGTool` | Lookup agent only queries internal application status; policy retrieval is segregated to the Retrieval Agent. |
| **Response Composer** | Draft synthesis | *None (Zero tools)* | *All tools* | Composer operates solely as an aggregator and formatter; granting tool invocation creates circular execution risks and prompt injection vectors. |

### Technical Enforcement

Enforced in `governance/tool_permissions.py` via `validate_agent_tool_access()` and `execute_tool_with_governance()`. Unauthorized tool invocation raises `PermissionDeniedError` and immediately halts execution before any data access occurs.

---

## 4. Runtime Layer: Per-Request Budget Management

### Policy Specifications

- **Token Ceiling:** Maximum **2,000 tokens** per request cycle.
- **Estimated Cost Ceiling:** Simulated **$0.05 USD** per request cycle (assuming \$0.000025 per token).
- **Overhead Allowances:**
  - Base System Prompt & ReAct Guidance: 350 tokens
  - RAG Retrieved Context Chunks: 450 tokens
  - Maximum Permitted User Query Payload: 1,200 tokens (~4,500 characters)

### Deterministic Simulation Clarification

Because this solution operates under `MOCK_LLM` with telemetry and remote network egress disabled, the token and cost budget manager (`governance/budget_manager.py`) functions as a deterministic architectural control. It models production token consumption and enforces denial of service (DoS) and oversized prompt injection guards without incurring cloud vendor API billing.

### Interception & Rejection Workflow

```
Customer Query ──> [Estimate Input Tokens]
                         │
                         ▼
             [Add System + RAG Overhead]
                         │
                         ▼
           Is Total Tokens > 2,000 Limit?
                     /        \
                   YES         NO
                   /             \
                  ▼               ▼
     [Raise BudgetExceededError]   [Proceed to Execution]
     [Log Rejection in JSONL]
     [Return 422/BLOCKED]
```

