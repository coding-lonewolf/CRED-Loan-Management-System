# Task 1: Dataset Generation & Validation Transcript

**Date:** 2026-11-07  
**Seed:** `20261026`  
**Total Records:** 60  
**Amount Range:** INR 50,000 to INR 7,425,000  
**Fraud Review Flag Rate:** 18.33% (11/60 records)  

---

## 1. Category Distribution (Target: >= 3 records per category)

| Loan Category | Record Count | Meets Requirement (>=3) |
|---|:---:|:---:|
| Auto Loan | 12 | **PASS** |
| Business Loan | 12 | **PASS** |
| Education Loan | 12 | **PASS** |
| Home Loan | 12 | **PASS** |
| Personal Loan | 12 | **PASS** |

---

## 2. Status Distribution (Target: All 5 statuses represented)

| Application Status | Record Count | Status Present |
|---|:---:|:---:|
| Approved | 11 | **PASS** |
| Disbursed | 9 | **PASS** |
| Rejected | 7 | **PASS** |
| Submitted | 15 | **PASS** |
| Under Review | 18 | **PASS** |

---

## 3. Fraud Review Validation

- **Target Band:** 10.0% to 30.0%
- **Observed Rate:** **18.33%** (11 out of 60 records)
- **Validation Status:** **PASS (Strictly within required bounds)**

