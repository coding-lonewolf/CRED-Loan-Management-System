# Task 5: Chunking Strategy Comparative Evaluation Report

**Date:** 2026-11-07  
**Strategies Compared:** 1. Fixed-Size with Overlap (250 chars / 50 overlap) | 2. Sentence-Based Chunking  
**Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2`  

---

## 1. Per-Query Arithmetic & Performance Comparison

$$Precision@k = \frac{|\text{Relevant Retrieved Documents}|}{|\text{All Unique Retrieved Documents}|}, \quad Recall@k = \frac{|\text{Relevant Retrieved Documents}|}{|\text{All Expected Relevant Documents}|}$$

| Query | Fixed Precision@k | Fixed Recall@k | Sentence Precision@k | Sentence Recall@k |
|---|:---:|:---:|:---:|:---:|
| **Q1**: What are the eligibility criteria and minimum income required for a home loan? | 1/3 = 0.3333 | 1/1 = 1.0000 | **1/2 = 0.5000** | **1/1 = 1.0000** |
| **Q2**: How is EMI calculated and what formula is applied for reducing balance loans? | 1/3 = 0.3333 | 1/1 = 1.0000 | **1/2 = 0.5000** | **1/1 = 1.0000** |
| **Q3**: What documents and identity verification proofs are required under KYC regulations? | 1/3 = 0.3333 | 1/1 = 1.0000 | **1/2 = 0.5000** | **1/1 = 1.0000** |
| **Q4**: What are the interest rates, benchmark spreads, and reset frequencies for retail loans? | 1/3 = 0.3333 | 1/1 = 1.0000 | **1/2 = 0.5000** | **1/1 = 1.0000** |
| **Q5**: What are the rules and survivor mandates for operational joint bank accounts? | 1/3 = 0.3333 | 1/1 = 1.0000 | **1/2 = 0.5000** | **1/1 = 1.0000** |

---

## 2. Global Metric Averages

- **Fixed-Size with Overlap:** Mean Precision = `0.3333`, Mean Recall = `1.0000`
- **Sentence-Based Chunking:** Mean Precision = `0.5000`, Mean Recall = `1.0000`

---

## 3. Deployment Recommendation

**Recommendation:** The Sentence-Based chunking strategy achieves a superior average Precision@k (0.50 vs 0.33 for fixed-size) while maintaining 100% Recall (1.00). Sentence chunking preserves semantic sentence boundaries within banking policy clauses, eliminating spurious cross-policy matches introduced by arbitrary token sliding windows. Consequently, `banking_sentence_chunks` is selected as the production RAG collection.

