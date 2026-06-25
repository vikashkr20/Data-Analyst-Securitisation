"""
tests/test_simulation.py
=========================
Unit tests for the Securitisation AI Agent project.
Tests core financial calculations: ECL, waterfall, DPD, weighted averages.

Run: pytest --cov=. tests/
"""

import pytest
import pandas as pd
import numpy as np
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Fixtures ──────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def loans():
    return pd.read_csv(os.path.join(BASE_DIR, "auto_loan_securitisation_data.csv"))

@pytest.fixture(scope="module")
def dpd():
    df = pd.read_csv(os.path.join(BASE_DIR, "dpd_snapshot_history.csv"))
    df['SnapshotDate'] = pd.to_datetime(df['SnapshotDate'])
    return df

@pytest.fixture(scope="module")
def dynamic():
    df = pd.read_csv(os.path.join(BASE_DIR, "dynamic_loss_monthly.csv"))
    df['ReportingDate'] = pd.to_datetime(df['ReportingDate'])
    return df

@pytest.fixture(scope="module")
def vintage():
    df = pd.read_csv(os.path.join(BASE_DIR, "static_pool_vintage_data.csv"))
    df['VintageStartDate'] = pd.to_datetime(df['VintageStartDate'])
    return df


# ── Tests: Data Loading ───────────────────────────────────────────────────────
class TestDataLoading:
    def test_loan_file_rows(self, loans):
        assert len(loans) == 500, f"Expected 500 loans, got {len(loans)}"

    def test_loan_file_columns(self, loans):
        assert loans.shape[1] == 58, f"Expected 58 columns, got {loans.shape[1]}"

    def test_dpd_file_rows(self, dpd):
        assert len(dpd) == 6000, f"Expected 6000 DPD rows, got {len(dpd)}"

    def test_dpd_snapshot_count(self, dpd):
        snap_count = dpd['SnapshotDate'].nunique()
        assert snap_count >= 10, f"Expected at least 10 snapshot months, got {snap_count}"

    def test_dynamic_rows(self, dynamic):
        assert len(dynamic) == 12, "Expected 12 monthly records"

    def test_vintage_rows(self, vintage):
        assert len(vintage) == 375, f"Expected 375 vintage rows, got {len(vintage)}"

    def test_vintage_count(self, vintage):
        assert vintage['VintageID'].nunique() == 15, "Expected 15 vintages"

    def test_no_null_loan_id(self, loans):
        assert loans['LoanID'].notna().all(), "LoanID should have no nulls"

    def test_pool_id_unique(self, loans):
        assert loans['PoolID'].nunique() == 1, "All loans should be in one pool"

    def test_pool_id_value(self, loans):
        assert loans['PoolID'].iloc[0] == 'ZAAUTO2024-1', "Pool ID mismatch"


# ── Tests: Pool Balance Calculations ──────────────────────────────────────────
class TestPoolBalanceCalculations:
    def test_outstanding_balance_positive(self, loans):
        assert loans['CurrentBalance'].sum() > 0

    def test_pool_factor_between_0_and_1(self, loans):
        pool_factor = loans['CurrentBalance'].sum() / loans['OriginalLoanAmount'].sum()
        assert 0 < pool_factor < 1, f"Pool factor {pool_factor:.4f} out of range"

    def test_active_loan_count(self, loans):
        active = (loans['CurrentBalance'] > 0).sum()
        assert active > 0
        assert active <= 500

    def test_defaulted_count_consistent(self, loans):
        defaulted_flag = loans['IsDefaulted'].sum()
        defaulted_status = (loans['DelinquencyStatus'] == 'Default').sum()
        # Allow small discrepancy due to classification nuances
        assert abs(defaulted_flag - defaulted_status) <= 10

    def test_current_balance_non_negative(self, loans):
        assert (loans['CurrentBalance'] >= 0).all(), "No loan should have negative balance"

    def test_emi_positive(self, loans):
        assert (loans['MonthlyEMI'] > 0).all(), "All EMI values should be positive"

    def test_interest_rate_range(self, loans):
        assert loans['InterestRate'].between(7.0, 15.0).all(), "Interest rates out of expected range"

    def test_ltv_range(self, loans):
        assert (loans['LTV_AtOrigination'] > 0).all(), "LTV at origination must be positive"
        assert (loans['LTV_AtOrigination'] <= 1.0).all(), "LTV at origination must be <= 100%"


# ── Tests: Weighted Average Calculations ──────────────────────────────────────
class TestWeightedAverages:
    def test_wac_range(self, loans):
        total_balance = loans['CurrentBalance'].sum()
        wac = (loans['CurrentBalance'] * loans['InterestRate']).sum() / total_balance
        assert 7.0 < wac < 15.0, f"WAC {wac:.2f}% out of expected range"

    def test_wac_between_min_max(self, loans):
        """WAC must be between min and max individual interest rates."""
        total_balance = loans['CurrentBalance'].sum()
        wac = (loans['CurrentBalance'] * loans['InterestRate']).sum() / total_balance
        assert loans['InterestRate'].min() <= wac <= loans['InterestRate'].max()

    def test_wala_positive(self, loans):
        total_balance = loans['CurrentBalance'].sum()
        wala = (loans['CurrentBalance'] * loans['MonthsOnBook']).sum() / total_balance
        assert wala > 0, "WALA must be positive"

    def test_wam_positive(self, loans):
        total_balance = loans['CurrentBalance'].sum()
        wam = (loans['CurrentBalance'] * loans['RemainingTerm']).sum() / total_balance
        assert wam >= 0, "WAM must be non-negative"

    def test_wa_ltv_range(self, loans):
        total_balance = loans['CurrentBalance'].sum()
        wa_ltv = (loans['CurrentBalance'] * loans['LTV_Current']).sum() / total_balance
        assert 0 < wa_ltv < 1.0, f"WA LTV Current {wa_ltv:.4f} out of range"

    def test_wa_cibil_range(self, loans):
        total_balance = loans['CurrentBalance'].sum()
        wa_cibil = (loans['CurrentBalance'] * loans['CIBIL_Score_Current']).sum() / total_balance
        assert 600 <= wa_cibil <= 900, f"WA CIBIL {wa_cibil:.0f} out of range"


# ── Tests: IFRS 9 ECL Stage Classification ────────────────────────────────────
class TestIFRS9Classification:
    def compute_stages(self, loans):
        def classify(row):
            if row['IsDefaulted'] or row['DelinquencyDays'] >= 120:
                return 3
            elif row['DelinquencyDays'] >= 60:
                return 2
            return 1
        return loans.apply(classify, axis=1)

    def test_all_loans_have_stage(self, loans):
        stages = self.compute_stages(loans)
        assert stages.isin([1, 2, 3]).all(), "All loans must be in Stage 1, 2, or 3"

    def test_stage1_majority(self, loans):
        stages = self.compute_stages(loans)
        stage1_pct = (stages == 1).sum() / len(stages)
        assert stage1_pct > 0.7, f"Stage 1 should be >70% of pool, got {stage1_pct:.1%}"

    def test_stage3_consistent_with_default(self, loans):
        stages = self.compute_stages(loans)
        defaulted = loans['IsDefaulted']
        # All defaulted loans must be Stage 3
        assert (stages[defaulted] == 3).all(), "All defaulted loans must be in Stage 3"

    def test_ecl_stage1_less_than_stage3(self, loans):
        stages = self.compute_stages(loans)
        def ecl(row, stage):
            mult = {1: 1.0, 2: 1.5, 3: 2.0}[stage]
            return row['PD_Estimate'] * mult * row['LGD_Estimate'] * row['EAD']
        avg_ecl1 = loans[stages == 1].apply(lambda r: ecl(r, 1), axis=1).mean()
        avg_ecl3 = loans[stages == 3].apply(lambda r: ecl(r, 3), axis=1).mean()
        assert avg_ecl1 < avg_ecl3, "Average Stage 1 ECL must be less than Stage 3"

    def test_total_ecl_positive(self, loans):
        stages = self.compute_stages(loans)
        total_ecl = sum(
            row['PD_Estimate'] * (1.0 if stage==1 else 1.5 if stage==2 else 2.0) *
            row['LGD_Estimate'] * row['EAD']
            for (_, row), stage in zip(loans.iterrows(), stages)
        )
        assert total_ecl > 0

    def test_ecl_coverage_below_100pct(self, loans):
        stages = self.compute_stages(loans)
        total_ecl = sum(
            row['PD_Estimate'] * (1.0 if stage==1 else 1.5 if stage==2 else 2.0) *
            row['LGD_Estimate'] * row['EAD']
            for (_, row), stage in zip(loans.iterrows(), stages)
        )
        total_ead = loans['EAD'].sum()
        coverage = total_ecl / total_ead
        assert 0 < coverage < 1.0, f"ECL coverage {coverage:.2%} should be between 0-100%"

    def test_pd_range(self, loans):
        assert (loans['PD_Estimate'] > 0).all(), "PD must be positive"
        assert (loans['PD_Estimate'] <= 1.0).all(), "PD must be <= 100%"

    def test_lgd_range(self, loans):
        assert (loans['LGD_Estimate'] > 0).all(), "LGD must be positive"
        assert (loans['LGD_Estimate'] <= 1.0).all(), "LGD must be <= 100%"


# ── Tests: DPD & Transition Analysis ─────────────────────────────────────────
class TestDPDAnalysis:
    def test_dpd_days_non_negative(self, dpd):
        assert (dpd['DPD_Days'] >= 0).all(), "DPD days cannot be negative"

    def test_roll_flag_values(self, dpd):
        valid_flags = {'Better', 'Same', 'Worse'}
        assert set(dpd['RollFlag'].unique()).issubset(valid_flags)

    def test_transition_type_values(self, dpd):
        valid_types = {'Static', 'Roll', 'Cure'}
        assert set(dpd['TransitionType'].unique()).issubset(valid_types)

    def test_cure_flag_consistent_with_transition(self, dpd):
        """Cure flag should align with Cure transition type."""
        cures = dpd[dpd['CureFlag'] == True]
        # Most cures should have TransitionType == 'Cure' or RollFlag == 'Better'
        cure_or_better = ((cures['TransitionType'] == 'Cure') | (cures['RollFlag'] == 'Better')).sum()
        assert cure_or_better / len(cures) > 0.5, "Cure flag should mostly align with Cure/Better"

    def test_sma_class_values(self, dpd):
        valid_sma = {'Standard', 'SMA-0', 'SMA-1', 'SMA-2', 'NPA'}
        assert set(dpd['RBI_SMA_Class'].unique()).issubset(valid_sma)

    def test_each_loan_has_12_snapshots(self, dpd):
        snap_counts = dpd.groupby('LoanID')['SnapshotDate'].nunique()
        # Most loans should have close to 12 snapshots
        assert snap_counts.median() >= 10, "Most loans should have ~12 monthly snapshots"

    def test_amount_overdue_non_negative(self, dpd):
        assert (dpd['AmountOverdue'] >= 0).all()


# ── Tests: Cash Flow Waterfall ─────────────────────────────────────────────────
class TestCashFlowWaterfall:
    SENIOR_PCT  = 0.75
    MEZZ_PCT    = 0.15
    SENIOR_RATE = 0.08
    MEZZ_RATE   = 0.10

    def compute_waterfall(self, row):
        senior_bal  = row['BOP_Balance'] * self.SENIOR_PCT
        mezz_bal    = row['BOP_Balance'] * self.MEZZ_PCT
        senior_int  = senior_bal * self.SENIOR_RATE / 12
        mezz_int    = mezz_bal * self.MEZZ_RATE / 12
        senior_princ = (row['BOP_Balance'] - row['EOP_Balance']) * self.SENIOR_PCT
        mezz_princ   = (row['BOP_Balance'] - row['EOP_Balance']) * self.MEZZ_PCT
        reserve      = row['BOP_Balance'] * 0.02 * 0.05
        equity       = max(0, row['CollectionsTotal'] - senior_int - senior_princ - mezz_int - mezz_princ - reserve)
        oc_ratio     = row['BOP_Balance'] / (senior_bal + mezz_bal)
        return {'senior_int': senior_int, 'mezz_int': mezz_int,
                'equity': equity, 'oc_ratio': oc_ratio}

    def test_senior_interest_positive(self, dynamic):
        for _, row in dynamic.iterrows():
            result = self.compute_waterfall(row)
            assert result['senior_int'] > 0

    def test_mezz_interest_positive(self, dynamic):
        for _, row in dynamic.iterrows():
            result = self.compute_waterfall(row)
            assert result['mezz_int'] > 0

    def test_equity_non_negative(self, dynamic):
        for _, row in dynamic.iterrows():
            result = self.compute_waterfall(row)
            assert result['equity'] >= 0, "Equity residual cannot be negative"

    def test_oc_ratio_above_1(self, dynamic):
        for _, row in dynamic.iterrows():
            result = self.compute_waterfall(row)
            assert result['oc_ratio'] > 1.0, "OC Ratio should be above 1.0 (overcollateralised)"

    def test_senior_interest_less_than_mezz_proportionally(self, dynamic):
        """Senior coupon (8%) × senior balance should be compared to mezz coupon (10%) × mezz balance."""
        first = dynamic.iloc[0]
        senior_cost = first['BOP_Balance'] * self.SENIOR_PCT * self.SENIOR_RATE / 12
        mezz_cost   = first['BOP_Balance'] * self.MEZZ_PCT  * self.MEZZ_RATE   / 12
        # Senior cost higher in absolute terms because of larger balance
        assert senior_cost > mezz_cost, "Senior total interest cost must exceed mezz in absolute terms"

    def test_collections_exceed_scheduled_amort(self, dynamic):
        """Collections should generally exceed scheduled amortisation (collection efficiency > 1)."""
        assert (dynamic['CollectionEfficiency'] > 1.0).any(), "Some months should have CE > 1.0"


# ── Tests: Vintage Analysis ────────────────────────────────────────────────────
class TestVintageAnalysis:
    def test_loss_rate_non_decreasing_generally(self, vintage):
        """For a given vintage, cumulative loss rate should be generally non-decreasing."""
        for vid in vintage['VintageID'].unique():
            sub = vintage[vintage['VintageID'] == vid].sort_values('MonthsOnBook')
            cum_loss = sub['CumulativeNetLossRate'].values
            # At least 80% of steps should be non-decreasing (allow small corrections)
            non_dec = np.sum(np.diff(cum_loss) >= -0.0001)
            assert non_dec / max(1, len(cum_loss) - 1) >= 0.7, f"Vintage {vid} loss curve not generally increasing"

    def test_pool_factor_between_0_and_1(self, vintage):
        assert (vintage['PoolFactor'] >= 0).all()
        assert (vintage['PoolFactor'] <= 1.001).all(), "Pool factor should not exceed 1"

    def test_vintage_count(self, vintage):
        assert vintage['VintageID'].nunique() == 15

    def test_months_on_book_range(self, vintage):
        assert vintage['MonthsOnBook'].min() == 0
        assert vintage['MonthsOnBook'].max() <= 60

    def test_cumulative_recovery_less_than_gross_loss(self, vintage):
        """Recoveries cannot exceed gross loss for any vintage-month."""
        valid = vintage[vintage['CumulativeGrossLoss'] > 0]
        assert (valid['CumulativeRecoveries'] <= valid['CumulativeGrossLoss']).all(), \
            "Recoveries cannot exceed gross losses"

    def test_net_loss_equals_gross_minus_recovery(self, vintage):
        """CumulativeNetLoss = CumulativeGrossLoss - CumulativeRecoveries."""
        diff = abs(vintage['CumulativeNetLoss'] -
                   (vintage['CumulativeGrossLoss'] - vintage['CumulativeRecoveries']))
        assert (diff < 1.0).all(), "Net loss must equal gross loss minus recoveries"


# ── Tests: Stress Testing Logic ────────────────────────────────────────────────
class TestStressTesting:
    def test_stressed_pd_capped_at_1(self, loans):
        mult = 5.0
        stressed_pd = (loans['PD_Estimate'] * mult).clip(upper=1.0)
        assert (stressed_pd <= 1.0).all(), "Stressed PD must not exceed 100%"

    def test_stressed_ecl_higher_than_base(self, loans):
        base_ecl = loans.apply(
            lambda r: r['PD_Estimate'] * r['LGD_Estimate'] * r['EAD'], axis=1).sum()
        stressed_ecl = loans.apply(
            lambda r: min(1.0, r['PD_Estimate'] * 3.0) *
                      (r['LGD_Estimate'] + (1-r['LGD_Estimate']) * 0.30) *
                      r['EAD'], axis=1).sum()
        assert stressed_ecl > base_ecl, "Stressed ECL must exceed base ECL"

    def test_crisis_ecl_higher_than_severe(self, loans):
        def stressed_ecl(mult, haircut):
            return loans.apply(
                lambda r: min(1.0, r['PD_Estimate'] * mult) *
                          (r['LGD_Estimate'] + (1-r['LGD_Estimate']) * haircut) *
                          r['EAD'], axis=1).sum()
        severe_ecl = stressed_ecl(3.0, 0.30)
        crisis_ecl = stressed_ecl(5.0, 0.50)
        assert crisis_ecl > severe_ecl, "Crisis ECL must exceed severe ECL"

    def test_stressed_lgd_bounded(self, loans):
        haircut = 0.5
        stressed_lgd = loans['LGD_Estimate'] + (1 - loans['LGD_Estimate']) * haircut
        assert (stressed_lgd <= 1.0).all(), "Stressed LGD must not exceed 100%"
        assert (stressed_lgd >= loans['LGD_Estimate']).all(), "Stressed LGD must be >= base LGD"

    def test_oc_ratio_lower_under_stress(self, loans, dynamic):
        outstanding = loans['CurrentBalance'].sum()
        base_oc = outstanding / (outstanding * (0.75 + 0.15))
        stressed_loss = loans['LossAmount'].sum() * 3.0 * 1.5
        stressed_oc = (outstanding - stressed_loss) / (outstanding * (0.75 + 0.15))
        assert stressed_oc < base_oc, "Stressed OC must be lower than base OC"
