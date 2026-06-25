# 📊 Final Presentation: Securitisation Risk Analytics & Platform Architecture
## Pool ID: ZAAUTO2024-1 (500 Indian Auto Loans)
**Candidate: Manish Kumar**  
**Role: Lead Securitisation Data Analyst & Risk Architect**  
**Transaction Code: 483553A**  

---

## 🛝 SLIDE 1: Title & Overview
### Transaction: Pool ZAAUTO2024-1
* **Asset Class**: Secured Retail Auto Loans (India)
* **Pool Size**: 500 Loans
* **Original Balance**: INR 54.61 Cr (INR 546,073,700.00)
* **Current Balance**: INR 31.78 Cr (INR 317,785,202.14)
* **Pool Factor**: 0.5819 (41.8% seasoned/amortised)
* **Structure**: Senior PTCs (75%), Mezzanine PTCs (15%), Equity/Residual (10%), Reserve Account (2% target)
* **Lead Architect**: Manish Kumar

---

## 🛝 SLIDE 2: India Securitisation Market & Regulatory Environment
### Regulatory Compliance under RBI 2021 Directions
* **Minimum Holding Period (MHP)**: Verified that all retail loans have completed a minimum of 6 months on the originator's books prior to pool cut-off.
* **Minimum Retention Requirement (MRR)**: Originator retains 5% of pool book value (satisfied via the first-loss Equity/Residual tranche) to align interests.
* **True Sale & Bankruptcy Remoteness**: Complete legal transfer of loans from originator's balance sheet to the bankrupt-remote SPV trust.
* **SMA Classifications**: Real-time tracking of Special Mention Accounts (SMA-0/1/2) and Non-Performing Assets (NPA) according to RBI asset classification rules.

---

## 🛝 SLIDE 3: Star Schema Data Model
### High-Performance Power BI Data Architecture
* **Dimension Tables (1-to-Many Relationships)**:
  * `DimLoan`: LoanID, PoolID, ServicerID, OriginalTerm, InterestRate, LTV
  * `DimBorrower`: BorrowerID, Age, Income, CIBIL_Score, DTI_Ratio
  * `DimVehicle`: VehicleType, Make, Model, Value, Age
  * `DimGeography`: Region, State
  * `DimDate`: Calendar Date, Year, Quarter, MonthName, FiscalYear
* **Fact Tables (Transaction Registers)**:
  * `FactMonthlyPerformance`: 6,000 historical loan-month records tracking DPD, balances, roll flags, SMA categories.
  * `FactStaticPool`: 375 rows tracking cohort vintage curves (Months on Book, net losses).
  * `FactDynamicLoss`: 12 monthly rows tracking cash collections, prepayments, and dynamic pool balances.

---

## 🛝 SLIDE 4: Pool Demographics & Baseline Metrics
### High-Quality Prime Portfolio Characteristics
* **Interest Rate Profile (WAC)**: **10.95%** (ranging from 7.00% to 15.00%).
* **Weighted Average Maturity (WAM)**: **45.14 Months** remaining.
* **Weighted Average Loan Age (WALA)**: **16.76 Months** on book.
* **Collateral Cushion (LTV)**: WA LTV decreased from **78.12%** at origination to **67.54%** currently, providing strong loss protection.
* **Credit bureau Profile**: Average current CIBIL score is **742.44** (origination was 751.59). granular, creditworthy borrower pool.
* **Geographic Spread**: Highly diversified across East (24.2%), North (21.3%), West (20.1%), South (18.8%), and Central (15.5%) regions.
* **Vehicle Mix**: MUVs (25.9%) and SUVs (30.0%) represent **55.9%** of outstanding collateral.

---

## 🛝 SLIDE 5: Historical Delinquency & Roll Rate Transition Matrix
### real-time Credit Migration Auditing
* **Delinquency Breakdown (Latest Snapshot)**:
  * Standard (0 DPD): **89.64%** of pool (INR 284.87m)
  * SMA-0 (1-30 DPD): **7.77%** of pool (INR 24.70m)
  * SMA-1 (31-60 DPD): **4.48%** of pool (INR 14.24m)
  * SMA-2 (61-90 DPD): **5.28%** of pool (INR 16.77m)
  * NPA/Default (90+ DPD): **4.86%** of pool (INR 15.44m)
* **Transition Matrix Highlights**:
  * **Cure Rate (1-29 DPD to Current)**: **45.0%** of early delinquencies cure.
  * **Default Roll Rate (SMA-2 to NPA)**: **32.0%** transition rate, highlighting SMA-2 as a critical early warning threshold.

---

## 🛝 SLIDE 6: Vintage Analysis & Loss Development Curves
### static Pool Performance & Underwriting Trends
* **Worst Cohort**: The **2021-Q2 vintage** represents the worst performing cohort, reaching a peak Cumulative Net Loss Rate of **1.67%** at month 36 on book.
* **Underwriting Improvements**: More recent cohorts are tracking significantly flatter. The **2023-Q1 vintage** has a cumulative net loss of only **0.62%** at month 18 on book, proving tighter credit controls.
* **Extrapolated Lifetime Pool Loss**: Log-linear extrapolation projects a lifetime pool net loss rate of **1.85%**, well within structural loss cushions.

---

## 🛝 SLIDE 7: IFRS 9 ECL Provisioning Framework & Gap Analysis
### Audit Variance: Computed vs. Provided ECL
* **IFRS 9 Credit Risk Stages**:
  * **Stage 1 (DPD <= 30)**: Count=443, Balance=INR 284.14m (ECL Coverage = 1.16%)
  * **Stage 2 (30 < DPD <= 90)**: Count=34, Balance=INR 20.78m (ECL Coverage = 20.85% - incorporates 1.5x lifetime factor)
  * **Stage 3 (DPD > 90 / Default)**: Count=23, Balance=INR 12.86m (ECL Coverage = 80.40% - incorporates 2.0x lifetime factor)
* **The Provisioning Gap (Key Finding)**:
  * **Total ECL Computed**: **INR 18,460,823.89**
  * **Total ECL Provided (Data Tape)**: **INR 11,662,952.90**
  * **Under-provisioning Gap**: **INR 6,797,870.99** (a 58.28% deficit due to originator failing to apply lifetime multipliers for Stage 2 & 3).

---

## 🛝 SLIDE 8: Cash Flow Waterfall Structure & Tranche Allocations
### Payment Priorities & Cash Distributions

| Payout Component | December 2023 (INR) | October 2024 (INR) |
| :--- | :---: | :---: |
| **BOP Pool Balance** | 542,637,916.38 | 481,475,300.96 |
| **Total Collections** | 21,079,067.54 | 14,856,931.25 |
| **Senior Note Interest (8%)** | 2,713,189.58 | 2,407,376.50 |
| **Senior Note Principal (75%)** | 13,292,236.73 | 8,494,347.05 |
| **Mezzanine Note Interest (10%)**| 678,297.40 | 601,844.13 |
| **Mezzanine Note Principal (15%)**| 2,658,447.35 | 1,698,869.41 |
| **Reserve Account Top-Up** | 34,737.93 | 33,089.88 |
| **Equity Tranche Residual** | 1,702,158.55 | 1,621,404.27 |
* **Reserve Account Performance**: Maintained at target level (2.0% of pool balance), absorbing early payment delays.

---

## 🛝 SLIDE 9: Stress Testing & Capital Adequacy
### What-If Scenario Analysis
* **Moderate Stress (2.0x defaults, 15% recovery haircut)**:
  * Stressed ECL: INR 40.25m. Stressed OC: 1.08x. No trigger breaches. Senior tranche remains AAA(so).
* **Severe Stress (3.0x defaults, 30% recovery haircut)**:
  * Stressed ECL: INR 67.82m. Loss trigger breached. Cash flow redirects to sequential mode, stopping Mezzanine principal distribution. Senior rating AA+(so).
* **Crisis Mode (5.0x defaults, 50% recovery haircut)**:
  * Stressed ECL: INR 124.31m. Stressed OC falls below 1.0 (0.94x). Equity and Mezzanine tranches completely eroded. Senior tranche faces principal write-downs, downgraded to BBB-(so).

---

## 🛝 SLIDE 10: System Design: Securitisation Risk Arena & Conclusions
### Key Achievements & Strategic Recommendations
* **The Platform**: Built an 8-page Streamlit application ("Securitisation Risk Arena") combining portfolio overview, vintage, ECL, waterfall, stress simulator, and a **gamified 8-level educational simulator**.
* **DevOps**: Fully dockerized with automated `pytest` suite verifying 56/56 tests.
* **Recommendations**:
  1. Force the originator to plug the **INR 6.80m ECL provisioning deficit**.
  2. Implement real-time HHI concentration and SMA-2 tracking in Power BI.
  3. Deploy the containerized dashboard for institutional investors.
