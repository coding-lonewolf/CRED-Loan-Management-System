# Task 15: AI Governance & Runtime Controls Demonstration Transcript

**Date:** 2026-11-07  
**Governance Framework:** Four-Layer Model (Data, Model, Application, Runtime)  
**Risk Classification:** HIGH RISK (Retail Banking & Statutory Customer Identifiers)  

---

## 1. Application Layer: Least Autonomy Matrix Enforcement

| Agent Name | Target Tool | Expected Permission | Observed Result | Status |
|---|---|:---:|---|:---:|
| **Lookup Agent** | `check_loan_application_status` | **ALLOWED** | Success: Executed status lookup for `CL-10021` | **PASS** |
| **Retrieval Agent** | `search_knowledge_base` | **ALLOWED** | Success: Executed policy RAG search | **PASS** |
| **Retrieval Agent** | `check_loan_application_status` | **DENIED** | Intercepted: `PermissionDeniedError` raised | **PASS** |
| **Response Composer** | `check_loan_application_status` | **DENIED** | Intercepted: `PermissionDeniedError` raised | **PASS** |
| **Response Composer** | `search_knowledge_base` | **DENIED** | Intercepted: `PermissionDeniedError` raised | **PASS** |
| **Lookup Agent** | `search_knowledge_base` | **DENIED** | Intercepted: `PermissionDeniedError` raised | **PASS** |

---

## 2. Runtime Layer: Per-Request Budget Management

- **Per-Request Token Ceiling:** 2,000 tokens
- **Simulated Cost Ceiling:** $0.0500 USD (at $0.000025 per token)
- **Clarification:** Token/cost estimates under `MOCK_LLM` are deterministic architectural simulations for governance, not live API bills.

### Test Scenarios

#### Scenario A: Standard Customer Query (In Budget)
- **Query:** *"What is the minimum credit score required for a personal loan?"*
- **Estimated Input Tokens:** 14 tokens
- **Orchestration Overhead Tokens:** 800 tokens (350 system + 450 RAG context)
- **Total Estimated Tokens:** 814 / 2,000 tokens
- **Simulated Cost:** $0.020350 USD
- **Enforcement Decision:** **APPROVED**

#### Scenario B: Deliberately Oversized Query (Exceeds Budget Ceiling)
- **Query Length:** 7,850 characters (~1,300 words)
- **Estimated Input Tokens:** 1,729 tokens
- **Orchestration Overhead Tokens:** 800 tokens
- **Total Estimated Tokens:** 2,529 / 2,000 tokens
- **Simulated Cost:** $0.063225 USD
- **Enforcement Decision:** **BLOCKED**
- **Rejection Reason:** *"Query payload is too large (1729 input tokens + 800 overhead tokens = 2529 total > 2000 limit). Rejection enforced to prevent resource starvation."*

---

## 3. Governance Audit Summary

```json
{
  "total_inspections": 6,
  "approved_requests": 3,
  "rejected_requests": 3,
  "max_budget_limit_tokens": 2000,
  "max_cost_limit_usd": 0.05
}
```

