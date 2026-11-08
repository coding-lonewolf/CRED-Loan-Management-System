# EMI Calculation Rules
Document Type: Loan Calculation Policy / Knowledge-Base Article
Market: India
Calculation Method: Fixed-rate reducing balance
Version: 1.0
Description
For a standard reducing-balance loan with a fixed interest rate, the Equated Monthly Instalment (EMI) is calculated using the principal, monthly interest rate, and total number of monthly instalments. The formula is EMI = P × r × (1+r)^n / ((1+r)^n − 1), where P is the loan principal, r is the monthly interest rate expressed as a decimal, and n is the tenure in months. Convert an annual nominal interest rate to a monthly rate by dividing it by 12 and then by 100; for example, 12% per annum gives a monthly rate of 0.01. If the interest rate is zero, calculate the EMI as P ÷ n. Under the reducing-balance method, interest for each period is calculated on the outstanding principal, and the remaining EMI amount reduces the principal. The EMI estimate assumes regular monthly payments, a constant interest rate, and a full repayment schedule. It does not automatically include processing fees, insurance premiums, taxes, late charges, prepayment costs, or other contractual amounts. A customer-facing calculation must state the principal, annual interest rate, tenure, repayment frequency, and whether additional charges are excluded. The result should be presented as an estimate unless verified against the lender's repayment schedule. For floating-rate loans or rate changes, the EMI or tenure may be revised according to the loan agreement. Round displayed amounts to the nearest rupee, while retaining adequate precision during calculation.
Formula Variables
Variable	Meaning
P	Loan principal
r	Monthly interest rate as a decimal
n	Total number of monthly instalments
EMI	Fixed monthly instalment under the stated assumptions


Calculation Disclaimer
This formula is intended for standard fixed-rate, monthly, reducing-balance loans. Actual repayment amounts may differ where the lender applies different day-count conventions, payment dates, rate-reset rules, rounding methods, fees, or other contractual terms. Do not invent missing inputs; request the principal, interest rate, and tenure before calculating an EMI.
Suggested Knowledge-Base Metadata
document_id: EMI-CALCULATION-RULES-001
document_type: loan_calculation_policy
topic: emi_calculation
market: India
calculation_method: reducing_balance
repayment_frequency: monthly
version: "1.0"
status: active