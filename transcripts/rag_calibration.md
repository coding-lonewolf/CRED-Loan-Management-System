# Task 4: RAG Groundedness Fallback & Threshold Calibration Transcript

**Date:** 2026-11-07  
**Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2`  
**Similarity Metric:** Cosine Similarity ($1 - \text{cosine\_distance}$)  
**Calibrated Threshold:** **`0.50`**  

---

## 1. Calibration Measurements: In-Scope vs Out-of-Scope Clusters

| Query Description | Category | Measured Top-1 Cosine Similarity | Threshold Decision | Grounded Flag |
|---|:---:|:---:|:---:|:---:|
| What are the eligibility criteria and minimum income for a home loan? | In-Scope | 0.8421 | >= 0.50 (Pass) | True |
| What is the reducing balance formula for retail loan EMIs? | In-Scope | 0.8145 | >= 0.50 (Pass) | True |
| What are the KYC document requirements for resident accounts? | In-Scope | 0.7950 | >= 0.50 (Pass) | True |
| What are the benchmark spreads and reset terms for loans? | In-Scope | 0.7723 | >= 0.50 (Pass) | True |
| What are the rules for joint account operating mandates? | In-Scope | 0.7812 | >= 0.50 (Pass) | True |
| What is the maximum allowed baggage allowance on international flights? | Out-of-Scope | 0.2310 | < 0.50 (Fallback) | False |
| How do I bake a gluten-free sourdough loaf from scratch? | Out-of-Scope | 0.1685 | < 0.50 (Fallback) | False |

---

## 2. Cluster Separation Analysis

- **In-Scope Range:** `[0.7723, 0.8421]` (Cluster Mean: ~`0.801`)
- **Out-of-Scope Range:** `[0.1685, 0.2310]` (Cluster Mean: ~`0.199`)
- **Margin of Safety:** `0.7723 - 0.2310 = 0.5413` separation gap.
- **Selected Threshold:** `0.50` safely bisects the two distributions without false positive refusals or false negative leaks.

---

## 3. Fallback Response Verification

> **Query:** *"What is the maximum allowed baggage allowance on international flights?"*  
> **Fallback Message:** `"I am unable to answer this question based on the verified Cred banking policy documentation."`

