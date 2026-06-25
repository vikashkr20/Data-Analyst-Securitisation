# 🏦 Securitisation Risk Analytics & Simulator Platform
## Project Code: 483553A | Pool ID: ZAAUTO2024-1 (500 Indian Auto Loans)
**Candidate: Manish Kumar** | **Role: Lead Securitisation Data Analyst & Risk Architect**

---

## 📖 Overview
This repository contains the complete end-to-end analytical framework, validation workbooks, interactive dashboard, and automated test suite for the securitisation transaction of **Pool ZAAUTO2024-1**. The transaction consists of **500 standard auto loans originated in India**, structured with credit tranches (Senior: 75% @ 8%, Mezzanine: 15% @ 10%, Equity: 10% @ residual) and backed by a 2% Reserve Account.

The project features a **three-tier architecture** that translates raw credit data tapes into actionable credit modeling insights and investor reporting dashboards, verified by a comprehensive unit testing framework.

---

## 🛠️ Repository Contents

### 1. Interactive Web Application
* **[simulation_app.py](file:///c:/Users/Manish%20Kumar/OneDrive/New%20folder/OneDrive/Desktop/DATA%20ANALYST/DATA%20ANALYST%20-%20SECURITISATION%20AI%20AGENT/simulation_app.py)**: The *Securitisation Risk Arena* Streamlit dashboard featuring 8 analytical modules:
  1. **Portfolio Overview**: Executive KPIs, regional distribution, and billing vs collections.
  2. **Delinquency & Roll Rate**: Roll-rate transition heatmaps, RBI SMA classifications (SMA-0/1/2/NPA), and cure rates.
  3. **Vintage Analysis**: Cohort loss development curves showing peak defaults.
  4. **IFRS 9 ECL Framework**: Staging classification and reconciliation of the provisioning gap.
  5. **Cash Flow Waterfall**: Tranche payment step-down visualization.
  6. **What-If Stress Simulator**: Scenario stress engine (Moderate, Severe, Crisis) for default/recovery multipliers.
  7. **Investor Reporting**: Monthly servicer reports and raw data tape exports.
  8. **🎮 Campaign Mode**: An educational 8-level simulation game testing structured finance knowledge.

### 2. Analytical Documentation
* **[MainReport.md](file:///c:/Users/Manish%20Kumar/OneDrive/New%20folder/OneDrive/Desktop/DATA%20ANALYST/DATA%20ANALYST%20-%20SECURITISATION%20AI%20AGENT/MainReport.md)**: 40+ page in-depth analytical report covering regulatory directions (RBI 2021 Directions), risk modeling, case studies (2008 US Subprime & 2018 IL&FS liquidity crisis), and baseline pool audit results.
* **[FinalPresentation.md](file:///c:/Users/Manish%20Kumar/OneDrive/New%20folder/OneDrive/Desktop/DATA%20ANALYST/DATA%20ANALYST%20-%20SECURITISATION%20AI%20AGENT/FinalPresentation.md)**: A 10-slide markdown presentation mapping transaction scope, star schemas, credit migrations, provisioning variances, waterfall cash flows, and stress tests.

### 3. Automated Excel Validation Workbooks
* **[DAX_Dictionary.xlsx](file:///c:/Users/Manish%20Kumar/OneDrive/New%20folder/OneDrive/Desktop/DATA%20ANALYST/DATA%20ANALYST%20-%20SECURITISATION%20AI%20AGENT/DAX_Dictionary.xlsx)**: Definition dictionary for 86 Power BI DAX measures, table relationships, and calculation groups.
* **[ECL_Validation.xlsx](file:///c:/Users/Manish%20Kumar/OneDrive/New%20folder/OneDrive/Desktop/DATA%20ANALYST/DATA%20ANALYST%20-%20SECURITISATION%20AI%20AGENT/ECL_Validation.xlsx)**: Loan-level IFRS 9 ECL calculation engine (12M and Lifetime ECL comparisons), transition matrices, and stage migration trends.
* **[Waterfall_Validation.xlsx](file:///c:/Users/Manish%20Kumar/OneDrive/New%20folder/OneDrive/Desktop/DATA%20ANALYST/DATA%20ANALYST%20-%20SECURITISATION%20AI%20AGENT/Waterfall_Validation.xlsx)**: Monthly tranche allocations (priority of payments waterfall), reserve account top-ups, and trigger status checks.

### 4. Power BI Modeling Assets
* **[dax_measures.dax](file:///c:/Users/Manish%20Kumar/OneDrive/New%20folder/OneDrive/Desktop/DATA%20ANALYST/DATA%20ANALYST%20-%20SECURITISATION%20AI%20AGENT/dax_measures.dax)**: Pre-written production-quality DAX code for all 86 measures ready to copy-paste into Power BI Desktop.
* **[Securitisation_Dashboard.pbix](file:///c:/Users/Manish%20Kumar/OneDrive/New%20folder/OneDrive/Desktop/DATA%20ANALYST/DATA%20ANALYST%20-%20SECURITISATION%20AI%20AGENT/Securitisation_Dashboard.pbix)**: Power BI Desktop dashboard file configured with imported CSV tables, relationships, DAX measures, and RLS roles.

---

## 📈 Core Analytical Insights (ZAAUTO2024-1 Audit)

1. **IFRS 9 Provisioning Deficit (Key Finding)**:
   * **Required ECL (Computed)**: INR 18,460,823.89 (incorporates 12M ECL for Stage 1, 1.5x Lifetime factor for Stage 2, and 2.0x Lifetime factor for Stage 3).
   * **Provided ECL (Data Tape)**: INR 11,662,952.90.
   * **Provisioning Variance**: **INR 6,797,870.99** (a **58.28% deficit**). The originator failed to apply lifetime loss multipliers to Stage 2 and 3 loans in the raw data tape.
2. **Vintage Performance**:
   * The worst-performing origination cohort is the **2021-Q2 vintage** which reached a peak Cumulative Net Loss Rate of **1.67%** at MOB 36.
   * Modern cohorts (2023-2024) are tracking significantly flatter (< 0.6% losses), showing tighter underwriting standards and credit cut-offs over time.
3. **Waterfall Cash Flows (Dec 2023 vs Oct 2024)**:
   * The transaction structures a constant **1.11x Overcollateralisation Ratio** under baseline conditions.
   * In December 2023, collections of INR 21.08m cover Senior Note total payments of INR 16.01m and Mezzanine Note payments of INR 3.34m, leaving INR 1.70m in residual cash to the Equity/Residual holder.
4. **Stress Testing Resilience**:
   * **Moderate Stress** (2.0x defaults, 15% recovery haircut): Structure is safe. Senior rating remains AAA(so).
   * **Severe Stress** (3.0x defaults, 30% recovery haircut): Breaches the 2% cumulative net loss trigger, shifting the waterfall to **sequential payout mode** to protect senior investors. Senior rating AA+(so).
   * **Crisis Mode** (5.0x defaults, 50% recovery haircut): Completely erodes the Mezzanine and Equity tranches. Senior Note suffers principal write-downs. Senior rating downgraded to BBB-(so).

---

## 🚀 Quick Start Guide

### Local Launch (One-Click batch script)
Double-click the **`RUN_APP.bat`** file in the project folder. This will automatically:
1. Install Python packages listed in `requirements.txt`.
2. Regenerate the three Excel validation workbooks.
3. Run the **56 unit tests** verifying calculations.
4. Launch the Streamlit dashboard in your default browser at `http://localhost:8501`.

### Manual CLI Startup
Open your terminal in the project directory and run:
```powershell
# Install requirements
pip install -r requirements.txt

# Run the test suite
python -m pytest tests/ -v

# Launch the Streamlit dashboard
python -m streamlit run simulation_app.py
```

### Containerized Deployment (Docker)
Ensure Docker Desktop is running, then execute:
```bash
# Build and launch containers
docker-compose up --build
```
The app will be accessible at `http://localhost:8501`.

---

## 🧪 Testing and DevOps Architecture
* **Unit Tests**: Executing `python -m pytest tests/ -v` validates **56 unit tests** covering mathematical correctness, ECL stages, roll flags, prepayments, and cash flow priority matching.
* **Docker Support**: Containerized using a multi-stage `Dockerfile` running on a lightweight `python:3.10-slim` image.
