# Task 16: Response Caching Demonstration Transcript

**Date:** 2026-11-07  
**Cache Type:** In-Memory Normalized Response Cache  
**Normalization Rule:** `" ".join(re.sub(r"[?!.,;]+$", "", query.strip().lower()).split())`  

---

## 1. Query Normalization Verification

| Raw Input Query | Normalized Cache Key | Matches Canonical Key |
|---|---|:---:|
| `what is the home loan eligibility?` | `what is the home loan eligibility` | **True** |
| `  What  is   the   Home   Loan  Eligibility?  ` | `what is the home loan eligibility` | **True** |
| `WHAT IS THE HOME LOAN ELIGIBILITY???` | `what is the home loan eligibility` | **True** |
| `What is the home loan eligibility.` | `what is the home loan eligibility` | **True** |

---

## 2. Repeated Query Cache Hit Demonstration

### Request 1 (Initial Inquiry): Cache Miss
- **Input Query:** *"What are the KYC document requirements for opening a joint account?"*
- **Cache Status:** **MISS** (`is_hit = False`)
- **Processing Performed:** Full RAG retrieval, groundedness verification, AutoGen review team
- **Execution Latency:** 24.85 ms
- **Cache Action:** Generated `BankingResponse` saved under normalized key: `"what are the kyc document requirements for opening a joint account"`

### Request 2 (Repeated Equivalent Query with Irregular Whitespace/Casing): Cache Hit
- **Input Query:** `"   WHAT  ARE   THE  KYC  DOCUMENT  REQUIREMENTS  FOR  OPENING A JOINT ACCOUNT?   "`
- **Normalized Key:** `"what are the kyc document requirements for opening a joint account"`
- **Cache Status:** **HIT** (`is_hit = True`)
- **Processing Performed:** Instant retrieval from memory; zero RAG or agent tool calls
- **Execution Latency:** 0.320 ms
- **Speedup Factor:** **77.7x faster**
- **Response Verified:** Grounded response returned immediately without redundant computation.

---

## 3. Personalized Loan Status: Cache Bypass Safety Rule

- **Input Query:** *"What is the status of my loan application CL-10021?"*
- **Query Type:** `loan_status` (contains application ID `CL-10021`)
- **Cache Status:** **BYPASS** (Cached = False)
- **Safety Rule Enforced:** Personalized record lookups are strictly excluded from query-only caching to ensure real-time fresh status checks.

---

## 4. Cache Performance Statistics

```json
{
  "cached_entries_count": 1,
  "cache_hits": 1,
  "cache_misses": 1,
  "cache_bypasses": 1,
  "hit_rate_pct": 50.0,
  "total_time_saved_ms": 24.85
}
```

