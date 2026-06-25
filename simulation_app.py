"""
simulation_app.py — Securitisation Risk Arena
===============================================
A gamified securitisation risk simulation platform built with Streamlit.
Loads 4 CSV datasets and provides 8 interactive dashboard pages.

Run: streamlit run simulation_app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import warnings
warnings.filterwarnings("ignore")

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Securitisation Risk Arena",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stApp { background-color: #0E1117; }

    .metric-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #16213e 100%);
        border: 1px solid #2d3561;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin: 4px;
    }
    .metric-label { color: #8892a4; font-size: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { color: #FFB300; font-size: 26px; font-weight: 700; margin: 6px 0; }
    .metric-delta { color: #00C853; font-size: 12px; }
    .metric-delta.neg { color: #FF4444; }

    .section-header {
        background: linear-gradient(90deg, #1F3864 0%, #0E1117 100%);
        border-left: 4px solid #FFB300;
        padding: 12px 20px;
        border-radius: 0 8px 8px 0;
        margin: 16px 0 12px 0;
        color: #FFFFFF;
        font-size: 18px;
        font-weight: 600;
    }

    .trigger-safe {
        background: linear-gradient(135deg, #0d2416 0%, #0a1f12 100%);
        border: 1px solid #00C853;
        border-radius: 8px;
        padding: 12px 16px;
        color: #00C853;
        font-weight: 600;
    }
    .trigger-breach {
        background: linear-gradient(135deg, #2d0a0a 0%, #1a0505 100%);
        border: 1px solid #FF4444;
        border-radius: 8px;
        padding: 12px 16px;
        color: #FF4444;
        font-weight: 600;
    }

    .level-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #16213e 100%);
        border: 1px solid #2d3561;
        border-radius: 12px;
        padding: 20px;
        margin: 8px 0;
    }

    .score-badge {
        background: linear-gradient(135deg, #FFB300 0%, #FF6F00 100%);
        color: #000;
        font-size: 20px;
        font-weight: 700;
        padding: 10px 24px;
        border-radius: 50px;
        display: inline-block;
        margin: 8px 0;
    }

    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1b2a 0%, #1a1f2e 100%);
        border-right: 1px solid #2d3561;
    }

    .stSelectbox > div > div { background: #1a1f2e; border: 1px solid #2d3561; }
    .stSlider > div > div { background: #FFB300; }

    h1 { color: #FFFFFF; font-weight: 700; }
    h2 { color: #FFB300; font-weight: 600; }
    h3 { color: #8892a4; font-weight: 500; }
</style>
""", unsafe_allow_html=True)


# ── Data Loading ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@st.cache_data
def load_data():
    loans   = pd.read_csv(os.path.join(BASE_DIR, "auto_loan_securitisation_data.csv"))
    dpd     = pd.read_csv(os.path.join(BASE_DIR, "dpd_snapshot_history.csv"))
    dynamic = pd.read_csv(os.path.join(BASE_DIR, "dynamic_loss_monthly.csv"))
    vintage = pd.read_csv(os.path.join(BASE_DIR, "static_pool_vintage_data.csv"))

    loans['OriginationDate'] = pd.to_datetime(loans['OriginationDate'])
    loans['CutoffDate']      = pd.to_datetime(loans['CutoffDate'])
    dpd['SnapshotDate']      = pd.to_datetime(dpd['SnapshotDate'])
    dynamic['ReportingDate'] = pd.to_datetime(dynamic['ReportingDate'])
    vintage['VintageStartDate'] = pd.to_datetime(vintage['VintageStartDate'])

    # Computed fields on loans
    loans['Calc_Stage'] = loans.apply(lambda r: 3 if (r['IsDefaulted'] or r['DelinquencyDays'] >= 120)
                                      else (2 if r['DelinquencyDays'] >= 60 else 1), axis=1)
    loans['ECL_Computed'] = loans.apply(lambda r:
        r['PD_Estimate'] * r['LGD_Estimate'] * r['EAD'] * (1.0 if r['Calc_Stage'] == 1
        else 1.5 if r['Calc_Stage'] == 2 else 2.0), axis=1)

    return loans, dpd, dynamic, vintage

loans, dpd, dynamic, vintage = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏦 Securitisation Risk Arena")
    st.markdown("**Pool**: ZAAUTO2024-1 | 500 Loans")
    st.markdown("---")

    page = st.radio("📊 Navigate", [
        "1 · Portfolio Overview",
        "2 · Delinquency & Roll Rate",
        "3 · Vintage Analysis",
        "4 · IFRS 9 ECL Framework",
        "5 · Cash Flow Waterfall",
        "6 · Stress Testing",
        "7 · Investor Reporting",
        "8 · 🎮 Campaign Mode"
    ])

    st.markdown("---")
    st.markdown(f"**Loans**: {len(loans):,}")
    st.markdown(f"**Outstanding**: ₹{loans['CurrentBalance'].sum()/1e7:.1f} Cr")
    st.markdown(f"**Pool Factor**: {loans['CurrentBalance'].sum()/loans['OriginalLoanAmount'].sum():.4f}")

# ── Helper Functions ──────────────────────────────────────────────────────────
PLOTLY_THEME = dict(
    paper_bgcolor='#0E1117',
    plot_bgcolor='#1a1f2e',
    font=dict(color='#8892a4', family='Inter'),
    xaxis=dict(gridcolor='#2d3561', zerolinecolor='#2d3561'),
    yaxis=dict(gridcolor='#2d3561', zerolinecolor='#2d3561'),
)
GOLD    = '#FFB300'
RED     = '#FF4444'
GREEN   = '#00C853'
BLUE    = '#2196F3'
PURPLE  = '#9C27B0'
TEAL    = '#00BCD4'
ORANGE  = '#FF5722'

def metric_card(label, value, delta=None, delta_neg=False):
    delta_html = ""
    if delta:
        cls = "neg" if delta_neg else ""
        delta_html = f'<div class="metric-delta {cls}">{delta}</div>'
    return f"""<div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>"""

def section_header(text):
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — PORTFOLIO OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "1 · Portfolio Overview":
    st.title("📊 Portfolio Dashboard — ZAAUTO2024-1")
    st.markdown("**Auto Loan ABS | India | Originator: Zetheta Structured Finance**")

    # KPI Row
    total_balance = loans['CurrentBalance'].sum()
    orig_balance  = loans['OriginalLoanAmount'].sum()
    pool_factor   = total_balance / orig_balance
    active_count  = (loans['CurrentBalance'] > 0).sum()
    wac = (loans['CurrentBalance'] * loans['InterestRate']).sum() / total_balance
    avg_cibil = (loans['CurrentBalance'] * loans['CIBIL_Score_Current']).sum() / total_balance
    ecl_total = loans['ECL_Computed'].sum()
    delinq_30plus = loans[loans['DelinquencyDays'] >= 30]['CurrentBalance'].sum()
    delinq_rate = delinq_30plus / total_balance

    cols = st.columns(6)
    kpis = [
        ("Total Outstanding", f"₹{total_balance/1e7:.2f} Cr"),
        ("Active Loans", f"{active_count:,}"),
        ("Pool Factor", f"{pool_factor:.4f}"),
        ("WAC", f"{wac:.2f}%"),
        ("WA CIBIL Score", f"{avg_cibil:.0f}"),
        ("30+ DPD Rate", f"{delinq_rate:.2%}"),
    ]
    for col, (label, val) in zip(cols, kpis):
        with col:
            st.markdown(metric_card(label, val), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        section_header("Delinquency Status Distribution")
        delinq_counts = loans.groupby('DelinquencyStatus')['CurrentBalance'].sum().reset_index()
        delinq_counts.columns = ['Status', 'Balance']
        color_map = {
            'Current': GREEN, '1-29 DPD': GOLD, '30-59 DPD': ORANGE,
            '60-89 DPD': '#FF7043', '90-119 DPD': RED, '120+ DPD': '#B71C1C',
            'Default': '#7B1FA2', 'Repossessed': '#311B92'
        }
        fig = px.pie(delinq_counts, values='Balance', names='Status',
                     color='Status', color_discrete_map=color_map,
                     hole=0.45)
        fig.update_layout(**PLOTLY_THEME, height=340, legend=dict(x=1, y=0.5))
        fig.update_traces(textfont_size=11, textposition='inside')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        section_header("Balance by Region")
        region_bal = loans.groupby('Region')['CurrentBalance'].sum().reset_index().sort_values('CurrentBalance', ascending=True)
        fig2 = px.bar(region_bal, x='CurrentBalance', y='Region', orientation='h',
                      color='CurrentBalance', color_continuous_scale=[[0, '#1a1f2e'], [1, GOLD]])
        fig2.update_layout(**PLOTLY_THEME, height=340,
                           xaxis_title="Outstanding Balance (₹)",
                           coloraxis_showscale=False)
        fig2.update_traces(text=region_bal['CurrentBalance'].apply(lambda x: f"₹{x/1e7:.1f}Cr"),
                           textposition='outside', textfont_color=WHITE if False else '#8892a4')
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        section_header("Balance by Vehicle Type")
        vtype_bal = loans.groupby('VehicleType')['CurrentBalance'].sum().reset_index().sort_values('CurrentBalance', ascending=False)
        fig3 = px.bar(vtype_bal, x='VehicleType', y='CurrentBalance',
                      color='CurrentBalance', color_continuous_scale=[[0, '#1a1f2e'], [1, TEAL]])
        fig3.update_layout(**PLOTLY_THEME, height=320, xaxis_title="", yaxis_title="Balance (₹)", coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        section_header("Monthly Collections vs Billing")
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(x=dynamic['ReportingDate'].dt.strftime('%b-%y'),
                              y=dynamic['CollectionsTotal'], name='Collections',
                              marker_color=GREEN, opacity=0.8))
        fig4.add_trace(go.Bar(x=dynamic['ReportingDate'].dt.strftime('%b-%y'),
                              y=dynamic['BillingAmount'], name='Billing Due',
                              marker_color=GOLD, opacity=0.8))
        fig4.update_layout(**PLOTLY_THEME, height=320, barmode='group',
                           xaxis_title="", yaxis_title="Amount (₹)")
        st.plotly_chart(fig4, use_container_width=True)

    section_header("Pool Stratification — by State")
    state_data = loans.groupby('State').agg(
        Loan_Count=('LoanID', 'count'),
        Total_Balance=('CurrentBalance', 'sum'),
        Avg_CIBIL=('CIBIL_Score_Current', 'mean'),
        Avg_LTV=('LTV_Current', 'mean'),
        Delinquent_30Plus=('DelinquencyDays', lambda x: (x >= 30).sum())
    ).reset_index().sort_values('Total_Balance', ascending=False)
    state_data['Balance_Cr'] = (state_data['Total_Balance'] / 1e7).round(2)
    state_data['Delinq_Rate'] = (state_data['Delinquent_30Plus'] / state_data['Loan_Count']).map('{:.1%}'.format)
    state_data['Avg_CIBIL'] = state_data['Avg_CIBIL'].round(0).astype(int)
    state_data['Avg_LTV'] = state_data['Avg_LTV'].map('{:.2%}'.format)
    st.dataframe(state_data[['State','Loan_Count','Balance_Cr','Avg_CIBIL','Avg_LTV','Delinq_Rate']].rename(
        columns={'Balance_Cr': 'Balance (₹ Cr)'}), use_container_width=True, height=300)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — DELINQUENCY & ROLL RATE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "2 · Delinquency & Roll Rate":
    st.title("📉 Delinquency & Roll Rate Analysis")

    # Monthly DPD trend
    section_header("Monthly DPD Distribution Trend")
    bucket_order = ['Current', '1-29 DPD', '30-59 DPD', '60-89 DPD', '90-119 DPD', '120+ DPD', 'Default', 'Repossessed']
    bucket_colors = [GREEN, GOLD, ORANGE, '#FF7043', RED, '#B71C1C', PURPLE, '#311B92']

    monthly_dpd = dpd.groupby(['SnapshotDate', 'DPD_Bucket'])['LoanID'].count().reset_index()
    monthly_dpd.columns = ['Date', 'Bucket', 'Count']
    monthly_dpd['Date_str'] = monthly_dpd['Date'].dt.strftime('%b-%y')

    fig = go.Figure()
    for bucket, color in zip(bucket_order, bucket_colors):
        sub = monthly_dpd[monthly_dpd['Bucket'] == bucket]
        if not sub.empty:
            fig.add_trace(go.Scatter(x=sub['Date_str'], y=sub['Count'], name=bucket,
                                     mode='lines+markers', line=dict(color=color, width=2),
                                     marker=dict(size=6)))
    fig.update_layout(**PLOTLY_THEME, height=350, xaxis_title="", yaxis_title="Loan Count",
                      legend=dict(x=1, y=0.5))
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        section_header("Roll Rate Transition Matrix (%)")
        bucket_short = ['Current', '1-29', '30-59', '60-89', '90-119', '120+', 'Default']
        full_labels  = ['Current', '1-29 DPD', '30-59 DPD', '60-89 DPD', '90-119 DPD', '120+ DPD', 'Default']

        trans = dpd[dpd['DPD_Bucket_Prior'].isin(full_labels) & dpd['DPD_Bucket'].isin(full_labels)].copy()
        matrix = pd.crosstab(trans['DPD_Bucket_Prior'], trans['DPD_Bucket'])
        matrix = matrix.reindex(index=full_labels, columns=full_labels, fill_value=0)
        matrix_pct = matrix.div(matrix.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)

        fig2 = go.Figure(go.Heatmap(
            z=matrix_pct.values * 100,
            x=bucket_short,
            y=bucket_short,
            colorscale=[[0, '#1a1f2e'], [0.4, GOLD], [1, RED]],
            text=np.round(matrix_pct.values * 100, 1),
            texttemplate='%{text}%',
            textfont=dict(size=10),
            hovertemplate='From: %{y}<br>To: %{x}<br>Rate: %{z:.1f}%<extra></extra>'
        ))
        fig2.update_layout(**PLOTLY_THEME, height=380,
                           xaxis_title="To Bucket", yaxis_title="From Bucket")
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        section_header("RBI SMA Classification — Latest Month")
        latest = dpd[dpd['SnapshotDate'] == dpd['SnapshotDate'].max()]
        sma_counts = latest.groupby('RBI_SMA_Class').agg(
            Count=('LoanID', 'count'),
            Balance=('CurrentBalance', 'sum')
        ).reset_index()
        sma_order = ['Standard', 'SMA-0', 'SMA-1', 'SMA-2', 'NPA']
        sma_colors = [GREEN, GOLD, ORANGE, RED, PURPLE]
        sma_counts['RBI_SMA_Class'] = pd.Categorical(sma_counts['RBI_SMA_Class'], categories=sma_order, ordered=True)
        sma_counts = sma_counts.sort_values('RBI_SMA_Class')
        fig3 = make_subplots(rows=1, cols=2, subplot_titles=['By Count', 'By Balance'])
        fig3.add_trace(go.Bar(x=sma_counts['RBI_SMA_Class'], y=sma_counts['Count'],
                              marker_color=sma_colors[:len(sma_counts)], showlegend=False), row=1, col=1)
        fig3.add_trace(go.Bar(x=sma_counts['RBI_SMA_Class'], y=sma_counts['Balance'] / 1e7,
                              marker_color=sma_colors[:len(sma_counts)], showlegend=False,
                              text=(sma_counts['Balance'] / 1e7).round(1), texttemplate='₹%{text}Cr'), row=1, col=2)
        fig3.update_layout(**PLOTLY_THEME, height=380)
        st.plotly_chart(fig3, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        section_header("Monthly Cure Rate Trend")
        cure_trend = dpd.groupby('SnapshotDate').agg(
            Total=('LoanID', 'count'), Cures=('CureFlag', 'sum')
        ).reset_index()
        cure_trend['CureRate'] = cure_trend['Cures'] / cure_trend['Total']
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=cure_trend['SnapshotDate'].dt.strftime('%b-%y'),
                                   y=cure_trend['CureRate'] * 100, mode='lines+markers',
                                   name='Cure Rate %', line=dict(color=GREEN, width=2.5),
                                   fill='tozeroy', fillcolor='rgba(0,200,83,0.1)'))
        fig4.update_layout(**PLOTLY_THEME, height=280, yaxis_title="Cure Rate (%)")
        st.plotly_chart(fig4, use_container_width=True)

    with col4:
        section_header("Consecutive Months Delinquent Distribution")
        latest_dpd = dpd[dpd['SnapshotDate'] == dpd['SnapshotDate'].max()]
        cmd_dist = latest_dpd['ConsecutiveMonthsDelinquent'].value_counts().sort_index().reset_index()
        cmd_dist.columns = ['Months', 'Count']
        fig5 = px.bar(cmd_dist, x='Months', y='Count',
                      color='Count', color_continuous_scale=[[0, GREEN], [1, RED]])
        fig5.update_layout(**PLOTLY_THEME, height=280,
                           xaxis_title="Consecutive Months Delinquent",
                           yaxis_title="Loan Count", coloraxis_showscale=False)
        st.plotly_chart(fig5, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — VINTAGE ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "3 · Vintage Analysis":
    st.title("📈 Vintage / Static Pool Analysis")

    section_header("Cumulative Net Loss Rate by Vintage — Loss Curves")
    vintages_list = sorted(vintage['VintageID'].unique())
    color_scale = px.colors.qualitative.Set2 + px.colors.qualitative.Pastel

    fig = go.Figure()
    for i, vid in enumerate(vintages_list):
        sub = vintage[vintage['VintageID'] == vid].sort_values('MonthsOnBook')
        fig.add_trace(go.Scatter(
            x=sub['MonthsOnBook'],
            y=sub['CumulativeNetLossRate'] * 100,
            name=vid, mode='lines',
            line=dict(color=color_scale[i % len(color_scale)], width=2),
            hovertemplate=f'<b>{vid}</b><br>Month: %{{x}}<br>Loss Rate: %{{y:.3f}}%<extra></extra>'
        ))
    fig.update_layout(**PLOTLY_THEME, height=420,
                      xaxis_title="Months on Book", yaxis_title="Cumulative Net Loss Rate (%)",
                      legend=dict(x=1, y=0.5, font=dict(size=10)))
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        section_header("Pool Factor by Vintage Over Time")
        fig2 = go.Figure()
        for i, vid in enumerate(vintages_list[:8]):  # show top 8 for clarity
            sub = vintage[vintage['VintageID'] == vid].sort_values('MonthsOnBook')
            fig2.add_trace(go.Scatter(
                x=sub['MonthsOnBook'], y=sub['PoolFactor'],
                name=vid, mode='lines',
                line=dict(color=color_scale[i % len(color_scale)], width=2)
            ))
        fig2.update_layout(**PLOTLY_THEME, height=340,
                           xaxis_title="Months on Book", yaxis_title="Pool Factor",
                           legend=dict(x=1, y=0.5, font=dict(size=9)))
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        section_header("Original Pool Balance by Vintage")
        orig_by_vintage = vintage.groupby('VintageID')['OriginalPoolBalance'].first().reset_index()
        orig_by_vintage = orig_by_vintage.sort_values('VintageID')
        fig3 = px.bar(orig_by_vintage, x='VintageID', y='OriginalPoolBalance',
                      color='OriginalPoolBalance',
                      color_continuous_scale=[[0, '#1a1f2e'], [1, GOLD]])
        fig3.update_layout(**PLOTLY_THEME, height=340,
                           xaxis_title="Vintage", yaxis_title="Original Pool Balance (₹)",
                           xaxis_tickangle=45, coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

    section_header("Vintage Summary Table — Current Performance")
    vintage_summary = vintage.groupby('VintageID').agg(
        Original_Loans=('OriginalLoanCount', 'first'),
        Orig_Balance_Cr=('OriginalPoolBalance', lambda x: x.iloc[0] / 1e7),
        Latest_Pool_Factor=('PoolFactor', 'last'),
        Max_Cum_Loss_Rate=('CumulativeNetLossRate', 'max'),
        Latest_Delinq_30Plus=('CurrentDelinq30Plus', 'last'),
        Peak_Marginal_Loss=('MarginalLossRate', 'max'),
        Months_Tracked=('MonthsOnBook', 'max')
    ).reset_index()
    vintage_summary['Orig_Balance_Cr'] = vintage_summary['Orig_Balance_Cr'].round(2)
    vintage_summary['Latest_Pool_Factor'] = vintage_summary['Latest_Pool_Factor'].map('{:.4f}'.format)
    vintage_summary['Max_Cum_Loss_Rate'] = vintage_summary['Max_Cum_Loss_Rate'].map('{:.3%}'.format)
    vintage_summary['Latest_Delinq_30Plus'] = vintage_summary['Latest_Delinq_30Plus'].map('{:.2%}'.format)
    vintage_summary['Peak_Marginal_Loss'] = vintage_summary['Peak_Marginal_Loss'].map('{:.4%}'.format)
    st.dataframe(vintage_summary, use_container_width=True, height=350)

    section_header("Compare Two Vintages Side-by-Side")
    c1, c2 = st.columns(2)
    v1 = c1.selectbox("Vintage A", vintages_list, index=0)
    v2 = c2.selectbox("Vintage B", vintages_list, index=min(4, len(vintages_list)-1))

    sub1 = vintage[vintage['VintageID'] == v1].sort_values('MonthsOnBook')
    sub2 = vintage[vintage['VintageID'] == v2].sort_values('MonthsOnBook')

    fig4 = make_subplots(rows=1, cols=2,
                          subplot_titles=[f"Cumulative Loss Rate", "Pool Factor"],
                          shared_xaxes=False)
    fig4.add_trace(go.Scatter(x=sub1['MonthsOnBook'], y=sub1['CumulativeNetLossRate']*100,
                               name=v1, line=dict(color=GOLD, width=2.5)), row=1, col=1)
    fig4.add_trace(go.Scatter(x=sub2['MonthsOnBook'], y=sub2['CumulativeNetLossRate']*100,
                               name=v2, line=dict(color=TEAL, width=2.5)), row=1, col=1)
    fig4.add_trace(go.Scatter(x=sub1['MonthsOnBook'], y=sub1['PoolFactor'],
                               name=v1, line=dict(color=GOLD, width=2.5), showlegend=False), row=1, col=2)
    fig4.add_trace(go.Scatter(x=sub2['MonthsOnBook'], y=sub2['PoolFactor'],
                               name=v2, line=dict(color=TEAL, width=2.5), showlegend=False), row=1, col=2)
    fig4.update_layout(**PLOTLY_THEME, height=320)
    st.plotly_chart(fig4, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — IFRS 9 ECL
# ══════════════════════════════════════════════════════════════════════════════
elif page == "4 · IFRS 9 ECL Framework":
    st.title("🔢 IFRS 9 Expected Credit Loss Framework")

    stage_counts = loans.groupby('Calc_Stage').agg(
        Count=('LoanID', 'count'),
        Balance=('CurrentBalance', 'sum'),
        EAD=('EAD', 'sum'),
        ECL=('ECL_Computed', 'sum'),
        Avg_PD=('PD_Estimate', 'mean'),
        Avg_LGD=('LGD_Estimate', 'mean')
    ).reset_index()
    stage_counts['Coverage'] = stage_counts['ECL'] / stage_counts['EAD']
    stage_counts['Stage_Label'] = stage_counts['Calc_Stage'].map({1: 'Stage 1\n(12M ECL)', 2: 'Stage 2\n(Lifetime)', 3: 'Stage 3\n(Impaired)'})

    cols = st.columns(4)
    total_ecl = loans['ECL_Computed'].sum()
    total_ead = loans['EAD'].sum()
    kpis = [
        ("Stage 1 Loans", f"{stage_counts[stage_counts['Calc_Stage']==1]['Count'].sum():,}"),
        ("Stage 2 Loans", f"{stage_counts[stage_counts['Calc_Stage']==2]['Count'].sum():,}"),
        ("Stage 3 Loans", f"{stage_counts[stage_counts['Calc_Stage']==3]['Count'].sum():,}"),
        ("Total ECL Provision", f"₹{total_ecl/1e7:.2f} Cr"),
    ]
    for col, (label, val) in zip(cols, kpis):
        with col:
            st.markdown(metric_card(label, val), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        section_header("ECL by Stage — Waterfall")
        stage_ecl = stage_counts[['Stage_Label', 'ECL']].copy()
        stage_ecl['ECL_Lakh'] = stage_ecl['ECL'] / 1e5
        fig = go.Figure(go.Waterfall(
            name="ECL", orientation="v",
            measure=["relative", "relative", "relative", "total"],
            x=["Stage 1\n(12M)", "Stage 2\n(LT)", "Stage 3\n(LT)", "Total ECL"],
            y=[stage_counts[stage_counts['Calc_Stage']==1]['ECL'].sum() / 1e5,
               stage_counts[stage_counts['Calc_Stage']==2]['ECL'].sum() / 1e5,
               stage_counts[stage_counts['Calc_Stage']==3]['ECL'].sum() / 1e5, 0],
            connector=dict(line=dict(color=BLUE)),
            increasing=dict(marker=dict(color=GOLD)),
            totals=dict(marker=dict(color=TEAL)),
            texttemplate='₹%{y:.0f}L',
        ))
        fig.update_layout(**PLOTLY_THEME, height=340, yaxis_title="ECL (₹ Lakhs)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        section_header("Stage Distribution — Loan Count")
        fig2 = px.pie(stage_counts, values='Count',
                      names=['Stage 1 (Performing)', 'Stage 2 (SICR)', 'Stage 3 (Impaired)'],
                      color_discrete_sequence=[GREEN, GOLD, RED], hole=0.5)
        fig2.update_layout(**PLOTLY_THEME, height=340)
        st.plotly_chart(fig2, use_container_width=True)

    with col3:
        section_header("ECL Coverage by Stage")
        fig3 = px.bar(stage_counts,
                      x=['Stage 1', 'Stage 2', 'Stage 3'],
                      y=stage_counts['Coverage'] * 100,
                      color=['Stage 1', 'Stage 2', 'Stage 3'],
                      color_discrete_sequence=[GREEN, GOLD, RED])
        fig3.update_layout(**PLOTLY_THEME, height=340, yaxis_title="ECL Coverage (%)", showlegend=False)
        fig3.update_traces(text=(stage_counts['Coverage']*100).round(2), texttemplate='%{text}%', textposition='outside')
        st.plotly_chart(fig3, use_container_width=True)

    section_header("PD vs LGD Scatter — by IFRS 9 Stage")
    fig4 = px.scatter(loans, x='PD_Estimate', y='LGD_Estimate',
                      color='Calc_Stage', size='EAD',
                      color_continuous_scale=[[0, GREEN], [0.5, GOLD], [1, RED]],
                      hover_data=['LoanID', 'DelinquencyDays', 'ECL_Computed'],
                      opacity=0.7,
                      labels={'PD_Estimate': 'PD Estimate', 'LGD_Estimate': 'LGD Estimate', 'Calc_Stage': 'Stage'})
    fig4.update_layout(**PLOTLY_THEME, height=380)
    st.plotly_chart(fig4, use_container_width=True)

    section_header("ECL Summary by Stage")
    summary = stage_counts.copy()
    summary['Balance_Cr']  = (summary['Balance'] / 1e7).round(2)
    summary['EAD_Cr']      = (summary['EAD'] / 1e7).round(2)
    summary['ECL_Lakhs']   = (summary['ECL'] / 1e5).round(2)
    summary['Coverage_Pct'] = (summary['Coverage'] * 100).round(2)
    summary['Avg_PD_Pct']  = (summary['Avg_PD'] * 100).round(3)
    summary['Avg_LGD_Pct'] = (summary['Avg_LGD'] * 100).round(2)
    summary['Stage'] = summary['Calc_Stage'].map({1: 'Stage 1 (12M ECL)', 2: 'Stage 2 (Lifetime)', 3: 'Stage 3 (Lifetime)'})
    st.dataframe(summary[['Stage', 'Count', 'Balance_Cr', 'EAD_Cr', 'ECL_Lakhs', 'Coverage_Pct', 'Avg_PD_Pct', 'Avg_LGD_Pct']].rename(
        columns={'Balance_Cr':'Balance (₹Cr)', 'EAD_Cr':'EAD (₹Cr)', 'ECL_Lakhs':'ECL (₹L)',
                 'Coverage_Pct':'Coverage %', 'Avg_PD_Pct':'Avg PD %', 'Avg_LGD_Pct':'Avg LGD %'}),
        use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — CASH FLOW WATERFALL
# ══════════════════════════════════════════════════════════════════════════════
elif page == "5 · Cash Flow Waterfall":
    st.title("💰 Cash Flow Waterfall — Tranche Allocation")

    # Waterfall computation
    SENIOR_PCT, MEZZ_PCT = 0.75, 0.15
    SENIOR_RATE, MEZZ_RATE = 0.08, 0.10
    OC_TRIGGER, DELINQ_TRIGGER, LOSS_TRIGGER = 1.05, 0.003, 0.002

    dyn2 = dynamic.sort_values('ReportingDate').copy()
    dyn2['Senior_Bal']       = dyn2['BOP_Balance'] * SENIOR_PCT
    dyn2['Mezz_Bal']         = dyn2['BOP_Balance'] * MEZZ_PCT
    dyn2['Senior_Int']       = dyn2['Senior_Bal'] * SENIOR_RATE / 12
    dyn2['Mezz_Int']         = dyn2['Mezz_Bal']   * MEZZ_RATE   / 12
    dyn2['Senior_Princ']     = (dyn2['BOP_Balance'] - dyn2['EOP_Balance']) * SENIOR_PCT
    dyn2['Mezz_Princ']       = (dyn2['BOP_Balance'] - dyn2['EOP_Balance']) * MEZZ_PCT
    dyn2['Reserve']          = (dyn2['BOP_Balance'] * 0.02 * 0.05).clip(lower=0)
    dyn2['Equity']           = (dyn2['CollectionsTotal'] - dyn2['Senior_Int'] - dyn2['Senior_Princ']
                                - dyn2['Mezz_Int'] - dyn2['Mezz_Princ'] - dyn2['Reserve']).clip(lower=0)
    dyn2['OC_Ratio']         = dyn2['BOP_Balance'] / (dyn2['Senior_Bal'] + dyn2['Mezz_Bal'])
    dyn2['Excess_Spread_A']  = dyn2['CollectionsTotal'] / dyn2['BOP_Balance'] * 12 - SENIOR_RATE*SENIOR_PCT - MEZZ_RATE*MEZZ_PCT
    dyn2['OC_Breach']        = dyn2['OC_Ratio'] < OC_TRIGGER
    dyn2['Delinq_Breach']    = dyn2['MonthlyDefaultRate'] > DELINQ_TRIGGER
    dyn2['Loss_Breach']      = dyn2['MonthlyNetLossRate'] > LOSS_TRIGGER
    dyn2['DateLabel']        = dyn2['ReportingDate'].dt.strftime('%b-%y')

    # KPI row
    latest_dyn = dyn2.iloc[-1]
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown(metric_card("OC Ratio", f"{latest_dyn['OC_Ratio']:.3f}x",
                           "✅ Safe" if not latest_dyn['OC_Breach'] else "🔴 Breach",
                           delta_neg=latest_dyn['OC_Breach']), unsafe_allow_html=True)
    with col2: st.markdown(metric_card("Excess Spread", f"{latest_dyn['Excess_Spread_A']:.2%}"), unsafe_allow_html=True)
    with col3: st.markdown(metric_card("Senior Int (Latest)", f"₹{latest_dyn['Senior_Int']/1e5:.1f}L"), unsafe_allow_html=True)
    with col4: st.markdown(metric_card("Equity Residual (Latest)", f"₹{latest_dyn['Equity']/1e5:.1f}L"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    section_header("Latest Month Waterfall — Collections Flow")
    ld = dyn2.iloc[-1]
    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "relative", "relative", "total"],
        x=["Collections\nIn", "Senior\nInterest", "Senior\nPrincipal", "Mezz\nInterest",
           "Mezz\nPrincipal", "Reserve\nAccount", "Equity\nResidual"],
        y=[ld['CollectionsTotal']/1e5,
           -ld['Senior_Int']/1e5, -ld['Senior_Princ']/1e5,
           -ld['Mezz_Int']/1e5, -ld['Mezz_Princ']/1e5,
           -ld['Reserve']/1e5, 0],
        connector=dict(line=dict(color=BLUE, width=1)),
        increasing=dict(marker=dict(color=GREEN)),
        decreasing=dict(marker=dict(color=RED)),
        totals=dict(marker=dict(color=GOLD)),
        texttemplate='₹%{y:.1f}L',
    ))
    fig.update_layout(**PLOTLY_THEME, height=360, yaxis_title="Amount (₹ Lakhs)")
    st.plotly_chart(fig, use_container_width=True)

    col2a, col2b = st.columns(2)

    with col2a:
        section_header("Monthly Tranche Distributions")
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=dyn2['DateLabel'], y=dyn2['Senior_Int']/1e5, name='Senior Interest', marker_color=BLUE))
        fig2.add_trace(go.Bar(x=dyn2['DateLabel'], y=dyn2['Senior_Princ']/1e5, name='Senior Principal', marker_color='#1565C0'))
        fig2.add_trace(go.Bar(x=dyn2['DateLabel'], y=dyn2['Mezz_Int']/1e5, name='Mezz Interest', marker_color=ORANGE))
        fig2.add_trace(go.Bar(x=dyn2['DateLabel'], y=dyn2['Mezz_Princ']/1e5, name='Mezz Principal', marker_color='#E65100'))
        fig2.add_trace(go.Bar(x=dyn2['DateLabel'], y=dyn2['Equity']/1e5, name='Equity Residual', marker_color=GREEN))
        fig2.update_layout(**PLOTLY_THEME, height=360, barmode='stack',
                           yaxis_title="Amount (₹ Lakhs)", xaxis_title="")
        st.plotly_chart(fig2, use_container_width=True)

    with col2b:
        section_header("OC Ratio & Excess Spread Trend")
        fig3 = make_subplots(specs=[[{"secondary_y": True}]])
        fig3.add_trace(go.Scatter(x=dyn2['DateLabel'], y=dyn2['OC_Ratio'],
                                   name='OC Ratio', line=dict(color=GOLD, width=2.5)), secondary_y=False)
        fig3.add_hline(y=OC_TRIGGER, line_dash="dash", line_color=RED,
                       annotation_text="OC Trigger 1.05×")
        fig3.add_trace(go.Bar(x=dyn2['DateLabel'], y=dyn2['Excess_Spread_A']*100,
                               name='Excess Spread %', marker_color=GREEN, opacity=0.5), secondary_y=True)
        fig3.update_layout(**PLOTLY_THEME, height=360)
        fig3.update_yaxes(title_text="OC Ratio (×)", secondary_y=False)
        fig3.update_yaxes(title_text="Excess Spread (%)", secondary_y=True)
        st.plotly_chart(fig3, use_container_width=True)

    section_header("Trigger Status — All 12 Months")
    trigger_df = dyn2[['DateLabel','MonthlyDefaultRate','MonthlyNetLossRate','OC_Ratio',
                         'OC_Breach','Delinq_Breach','Loss_Breach']].copy()
    trigger_df['Delinq Rate'] = (trigger_df['MonthlyDefaultRate'] * 100).round(3).astype(str) + '%'
    trigger_df['Loss Rate']   = (trigger_df['MonthlyNetLossRate']  * 100).round(3).astype(str) + '%'
    trigger_df['OC']          = trigger_df['OC_Ratio'].round(4).astype(str) + '×'
    trigger_df['Delinq Status'] = trigger_df['Delinq_Breach'].map({True: '🔴 BREACH', False: '🟢 Safe'})
    trigger_df['Loss Status']   = trigger_df['Loss_Breach'].map({True: '🔴 BREACH', False: '🟢 Safe'})
    trigger_df['OC Status']     = trigger_df['OC_Breach'].map({True: '🔴 BREACH', False: '🟢 Safe'})
    st.dataframe(trigger_df[['DateLabel','Delinq Rate','Delinq Status','Loss Rate','Loss Status','OC','OC Status']].rename(
        columns={'DateLabel': 'Month'}), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — STRESS TESTING
# ══════════════════════════════════════════════════════════════════════════════
elif page == "6 · Stress Testing":
    st.title("⚡ What-If Stress Testing Simulator")

    # Scenario presets
    presets = st.columns(4)
    scenario = "Custom"
    for col, (name, vals) in zip(presets, [
        ("Base Case",    (1.0, 0,  0,   0)),
        ("Moderate",     (2.0, 15, -20, 100)),
        ("Severe",       (3.0, 30, -35, 250)),
        ("🔴 Crisis",    (5.0, 50, -50, 500)),
    ]):
        if col.button(name, use_container_width=True):
            scenario = name
            st.session_state['stress_mult']    = vals[0]
            st.session_state['rec_haircut']    = vals[1]
            st.session_state['prepay_change']  = vals[2]
            st.session_state['rate_shock']     = vals[3]

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        mult    = st.slider("Default Rate Multiplier (×)", 1.0, 5.0,
                            float(st.session_state.get('stress_mult', 1.0)), 0.1)
        haircut = st.slider("Recovery Rate Haircut (%)", 0, 50,
                            int(st.session_state.get('rec_haircut', 0)), 5)
    with col2:
        prepay  = st.slider("Prepayment Speed Change (%)", -50, 50,
                            int(st.session_state.get('prepay_change', 0)), 5)
        rate_sh = st.slider("Interest Rate Shock (bps)", 0, 500,
                            int(st.session_state.get('rate_shock', 0)), 25)

    # Compute stressed metrics
    stressed = loans.copy()
    stressed['S_PD']  = (stressed['PD_Estimate']  * mult).clip(upper=1.0)
    stressed['S_LGD'] = stressed['LGD_Estimate'] + (1 - stressed['LGD_Estimate']) * (haircut / 100)
    stressed['S_ECL'] = stressed.apply(lambda r:
        r['S_PD'] * r['S_LGD'] * r['EAD'] * (1.0 if r['Calc_Stage']==1 else 1.5 if r['Calc_Stage']==2 else 2.0), axis=1)
    stressed['S_NetLoss'] = stressed['LossAmount'] * (1 + (mult-1)*0.5) * (1 + haircut/100)

    base_ecl       = loans['ECL_Computed'].sum()
    stressed_ecl   = stressed['S_ECL'].sum()
    base_loss      = loans['NetLoss'].sum()
    stressed_loss  = stressed['S_NetLoss'].sum()
    outstanding    = loans['CurrentBalance'].sum()
    base_oc        = outstanding / (outstanding * (0.75 + 0.15))
    stressed_oc    = (outstanding - stressed_loss) / (outstanding * (0.75 + 0.15))
    stressed_delinq = loans['Delinquency_30Plus_Rate'] if hasattr(loans, 'Delinquency_30Plus_Rate') else \
                     loans[loans['DelinquencyDays'] >= 30]['CurrentBalance'].sum() / outstanding * mult

    # Results comparison
    section_header("Stressed vs Base Case — Comparison")
    comp_cols = st.columns(4)
    metrics = [
        ("Total ECL",      f"₹{base_ecl/1e7:.2f}Cr",    f"₹{stressed_ecl/1e7:.2f}Cr",    stressed_ecl > base_ecl),
        ("Net Loss",       f"₹{base_loss/1e5:.1f}L",     f"₹{stressed_loss/1e5:.1f}L",     stressed_loss > base_loss),
        ("OC Ratio",       f"{base_oc:.3f}×",             f"{stressed_oc:.3f}×",             stressed_oc < 1.05),
        ("ECL / Balance",  f"{base_ecl/outstanding:.2%}", f"{stressed_ecl/outstanding:.2%}", True),
    ]
    for col, (label, base_val, stress_val, is_bad) in zip(comp_cols, metrics):
        with col:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-label">{label}</div>
                <div style="color:#8892a4;font-size:12px">BASE</div>
                <div style="color:#8892a4;font-size:18px;font-weight:600">{base_val}</div>
                <div style="color:#FFB300;font-size:11px;margin:4px 0">▼ STRESSED</div>
                <div style="color:{'#FF4444' if is_bad else '#00C853'};font-size:22px;font-weight:700">{stress_val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        section_header("ECL Distribution — Base vs Stressed")
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=loans['ECL_Computed'], name='Base ECL',
                                    marker_color=GREEN, opacity=0.7, nbinsx=40))
        fig.add_trace(go.Histogram(x=stressed['S_ECL'], name='Stressed ECL',
                                    marker_color=RED, opacity=0.7, nbinsx=40))
        fig.update_layout(**PLOTLY_THEME, height=340, barmode='overlay',
                          xaxis_title="ECL per Loan (₹)", yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        section_header("Trigger Proximity — Stressed Scenario")
        triggers = {
            'Delinquency\n(vs 0.3%)':   (loans[loans['DelinquencyDays']>=30].shape[0]/len(loans)*mult, 0.003),
            'Net Loss Rate\n(vs 0.2%)':  (stressed_loss/outstanding/12, 0.002),
            'OC Ratio\n(vs 1.05×)':      (stressed_oc, 1.05),
        }
        fig2 = go.Figure()
        for name, (current, threshold) in triggers.items():
            pct = min(100, current / threshold * 100) if name != 'OC Ratio\n(vs 1.05×)' else \
                  max(0, 100 - (current - threshold) / threshold * 100)
            color = RED if pct >= 100 else (ORANGE if pct >= 80 else GREEN)
            fig2.add_trace(go.Bar(x=[name], y=[pct], marker_color=color,
                                  text=[f'{pct:.0f}% of limit'], textposition='outside'))
        fig2.add_hline(y=100, line_dash="dash", line_color=RED, annotation_text="Trigger Threshold")
        fig2.update_layout(**PLOTLY_THEME, height=340, yaxis_title="% of Trigger Limit",
                           showlegend=False, yaxis_range=[0, 130])
        st.plotly_chart(fig2, use_container_width=True)

    if stressed_oc < 1.05:
        st.markdown('<div class="trigger-breach">🔴 OC TRIGGER BREACH — Equity cash trap activated under this stress scenario!</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="trigger-safe">🟢 All triggers safe under this scenario. OC Ratio maintained above 1.05×</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 7 — INVESTOR REPORTING
# ══════════════════════════════════════════════════════════════════════════════
elif page == "7 · Investor Reporting":
    st.title("📋 Investor Reporting — Monthly Servicer Report")

    month_options = dynamic.sort_values('ReportingDate')['ReportingDate'].dt.strftime('%B %Y').tolist()
    selected_month = st.selectbox("Select Reporting Month", month_options, index=len(month_options)-1)
    sel_row = dynamic[dynamic['ReportingDate'].dt.strftime('%B %Y') == selected_month].iloc[0]

    st.markdown(f"### 📄 Servicer Report — {selected_month}")
    st.markdown("**Securitisation Pool**: ZAAUTO2024-1 | **Servicers**: HDFC Bank, ICICI Auto, Bajaj Finance")
    st.markdown("---")

    # 6 report sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "1. Pool Summary", "2. Delinquency", "3. Loss & Recovery",
        "4. Prepayment", "5. Waterfall", "6. Trigger Status"
    ])

    SENIOR_PCT, MEZZ_PCT = 0.75, 0.15
    SENIOR_RATE, MEZZ_RATE = 0.08, 0.10

    with tab1:
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("BOP Balance", f"₹{sel_row['BOP_Balance']/1e7:.2f} Cr")
        with c2: st.metric("EOP Balance", f"₹{sel_row['EOP_Balance']/1e7:.2f} Cr")
        with c3: st.metric("Loan Count (EOP)", f"{sel_row['EOP_LoanCount']:,}")
        c4, c5, c6 = st.columns(3)
        with c4: st.metric("Pool Factor", f"{sel_row['EOP_Balance']/dynamic['BOP_Balance'].iloc[0]:.4f}")
        with c5: st.metric("WAC", f"{(loans['CurrentBalance']*loans['InterestRate']).sum()/loans['CurrentBalance'].sum():.2f}%")
        with c6: st.metric("Scheduled Amort", f"₹{sel_row['ScheduledAmort']/1e7:.2f} Cr")

    with tab2:
        snap = dpd[dpd['SnapshotDate'].dt.strftime('%B %Y') == selected_month]
        if snap.empty:
            snap = dpd[dpd['SnapshotDate'] == dpd['SnapshotDate'].max()]
        total_snap = len(snap)
        total_bal = snap['CurrentBalance'].sum()
        delinq_data = []
        for bucket in ['Current', '1-29 DPD', '30-59 DPD', '60-89 DPD', '90-119 DPD', '120+ DPD', 'Default']:
            sub = snap[snap['DPD_Bucket'] == bucket]
            delinq_data.append({
                'DPD Bucket': bucket,
                'Count': len(sub),
                'Balance (₹ Cr)': round(sub['CurrentBalance'].sum()/1e7, 2),
                'Count %': f"{len(sub)/total_snap*100:.1f}%",
                'Balance %': f"{sub['CurrentBalance'].sum()/total_bal*100:.1f}%"
            })
        st.dataframe(pd.DataFrame(delinq_data), use_container_width=True)

    with tab3:
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Gross Loss", f"₹{sel_row['GrossLoss_ThisMonth']/1e5:.1f}L")
        with c2: st.metric("Recoveries", f"₹{sel_row['Recoveries_ThisMonth']/1e5:.1f}L")
        with c3: st.metric("Net Loss", f"₹{sel_row['NetLoss_ThisMonth']/1e5:.1f}L")
        c4, c5 = st.columns(2)
        with c4: st.metric("Monthly Default Rate", f"{sel_row['MonthlyDefaultRate']:.3%}")
        with c5: st.metric("Monthly Net Loss Rate", f"{sel_row['MonthlyNetLossRate']:.3%}")

    with tab4:
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("SMM", f"{sel_row['SMM']:.4f}")
        with c2: st.metric("CPR (Annualised)", f"{sel_row['CPR_Annualised']:.2%}")
        with c3: st.metric("Prepayments", f"₹{sel_row['Prepayments_ThisMonth']/1e5:.1f}L")
        st.metric("Collection Efficiency", f"{sel_row['CollectionEfficiency']:.2%}",
                  help="CollectionsTotal / BillingAmount — >100% means extra payments received")

    with tab5:
        senior_bal = sel_row['BOP_Balance'] * SENIOR_PCT
        mezz_bal   = sel_row['BOP_Balance'] * MEZZ_PCT
        senior_int = senior_bal * SENIOR_RATE / 12
        mezz_int   = mezz_bal * MEZZ_RATE / 12
        oc         = sel_row['BOP_Balance'] / (senior_bal + mezz_bal)
        xs         = sel_row['CollectionsTotal'] / sel_row['BOP_Balance'] * 12 - SENIOR_RATE*SENIOR_PCT - MEZZ_RATE*MEZZ_PCT
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Senior Interest", f"₹{senior_int/1e5:.1f}L")
        with c2: st.metric("Mezz Interest", f"₹{mezz_int/1e5:.1f}L")
        with c3: st.metric("OC Ratio", f"{oc:.3f}×")
        with c4: st.metric("Excess Spread", f"{xs:.2%}")

    with tab6:
        delinq_breach = sel_row['MonthlyDefaultRate'] > 0.003
        loss_breach   = sel_row['MonthlyNetLossRate']  > 0.002
        oc_val        = sel_row['BOP_Balance'] / (sel_row['BOP_Balance'] * (SENIOR_PCT + MEZZ_PCT))
        oc_breach     = oc_val < 1.05

        for name, val, thresh, breach, unit in [
            ("Delinquency Trigger", sel_row['MonthlyDefaultRate'], 0.003, delinq_breach, "%"),
            ("Loss Trigger",        sel_row['MonthlyNetLossRate'],  0.002, loss_breach,   "%"),
            ("OC Trigger",          oc_val,                         1.05,  oc_breach,     "×"),
        ]:
            val_str = f"{val:.3%}" if unit == "%" else f"{val:.3f}×"
            thr_str = f"{thresh:.3%}" if unit == "%" else f"{thresh:.2f}×"
            status_class = "trigger-breach" if breach else "trigger-safe"
            status_icon  = "🔴 BREACH" if breach else "🟢 Safe"
            st.markdown(f'<div class="{status_class}"><b>{name}</b> | Current: {val_str} | Threshold: {thr_str} | Status: {status_icon}</div><br>', unsafe_allow_html=True)

    st.markdown("---")
    section_header("Rating Agency Data Tape Export")
    tape_cols = ['LoanID', 'PoolID', 'OriginalLoanAmount', 'CurrentBalance', 'InterestRate',
                 'OriginalTerm', 'RemainingTerm', 'MonthsOnBook', 'LTV_AtOrigination', 'LTV_Current',
                 'CIBIL_Score_Origination', 'CIBIL_Score_Current', 'DelinquencyStatus', 'DelinquencyDays',
                 'IFRS9_Stage', 'PD_Estimate', 'LGD_Estimate', 'EAD', 'ECL_Provision',
                 'Region', 'State', 'VehicleType', 'VehicleMake', 'VehicleYear',
                 'IsNewVehicle', 'HasInsurance', 'ServicerName']
    tape_df = loans[tape_cols].head(20)
    st.dataframe(tape_df, use_container_width=True, height=250)
    csv_data = loans[tape_cols].to_csv(index=False)
    st.download_button("⬇️ Download Full Data Tape (500 Loans)", csv_data,
                       "ZAAUTO2024-1_DataTape.csv", "text/csv", use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 8 — CAMPAIGN MODE (GAMIFIED)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "8 · 🎮 Campaign Mode":
    st.title("🎮 Securitisation Risk Arena — Campaign Mode")
    st.markdown("**Play 8 progressive levels to master securitisation analytics!**")

    # Session state init
    for key, default in [('score', 0), ('current_level', 1), ('completed', set()), ('level_scores', {})]:
        if key not in st.session_state:
            st.session_state[key] = default

    # Score header
    score_pct = st.session_state['score'] / 800 * 100
    st.markdown(f'<div class="score-badge">🏆 Score: {st.session_state["score"]} / 800</div>', unsafe_allow_html=True)
    st.progress(min(1.0, score_pct / 100))
    st.markdown(f"**Levels Completed**: {len(st.session_state['completed'])} / 8")
    st.markdown("---")

    # Level selector
    level = st.selectbox("🎯 Select Level",
                         [f"Level {i}" for i in range(1, 9)],
                         index=st.session_state['current_level'] - 1)
    level_num = int(level.split(" ")[1])

    levels = {
        1: {
            "title": "Data Foundation",
            "narrative": "You've just joined Meridian Structured Finance as Lead Data Analyst. Your first task: assess the health of the ZAAUTO2024-1 pool.",
            "task": "What is the 30+ DPD delinquency rate for the pool? (as a % of outstanding balance, 1 decimal)",
            "type": "numeric",
            "answer": round(loans[loans['DelinquencyDays']>=30]['CurrentBalance'].sum() / loans['CurrentBalance'].sum() * 100, 1),
            "tolerance": 1.0,
            "hint": "Formula: SUM(Balance where DPD >= 30) ÷ SUM(Total Balance) × 100",
            "explanation": "The delinquency rate is computed using CALCULATE with FILTER(DelinquencyDays >= 30) in DAX. Understanding the delinquency bucket split is the foundation of all securitisation risk analytics.",
            "points": 100
        },
        2: {
            "title": "Time Intelligence",
            "narrative": "The CRO wants a trend update. You need to identify the worst-performing month.",
            "task": "Which month had the HIGHEST net loss?",
            "type": "choice",
            "choices": dynamic.sort_values('ReportingDate')['ReportingDate'].dt.strftime('%B %Y').tolist(),
            "answer": dynamic.loc[dynamic['NetLoss_ThisMonth'].idxmax(), 'ReportingDate'].strftime('%B %Y'),
            "explanation": "Time intelligence uses DATESYTD, PREVIOUSMONTH, and DATESINPERIOD in DAX. Peak loss months indicate collateral performance deterioration.",
            "points": 100
        },
        3: {
            "title": "Weighted Averages",
            "narrative": "Rating agency S&P requests the pool's weighted average coupon for their LEVELS model.",
            "task": "Calculate the Weighted Average Coupon (WAC) of the pool. Enter to 2 decimal places (e.g., 11.05 for 11.05%).",
            "type": "numeric",
            "answer": round((loans['CurrentBalance'] * loans['InterestRate']).sum() / loans['CurrentBalance'].sum(), 2),
            "tolerance": 0.2,
            "hint": "WAC = Σ(Balance × Interest Rate) ÷ Σ(Balance)",
            "explanation": "WAC in DAX: DIVIDE(SUMX(loans, CurrentBalance * InterestRate), SUM(CurrentBalance)). This is the pool's blended yield and drives excess spread calculations.",
            "points": 100
        },
        4: {
            "title": "Concentration Risk",
            "narrative": "Your risk committee needs to assess geographic concentration before the quarterly board meeting.",
            "task": "Which STATE has the highest loan balance concentration in the pool?",
            "type": "choice",
            "choices": sorted(loans.groupby('State')['CurrentBalance'].sum().sort_values(ascending=False).head(8).index.tolist()),
            "answer": loans.groupby('State')['CurrentBalance'].sum().idxmax(),
            "explanation": "TOPN and RANKX in DAX identify concentration. Geographic concentration is measured by HHI = Σ(StateShare²). >0.25 indicates high concentration risk.",
            "points": 100
        },
        5: {
            "title": "Waterfall Wizard",
            "narrative": "The senior noteholder trustee requests the equity residual payment for the first reporting month.",
            "task": f"What is the Equity Residual payment for {dynamic['ReportingDate'].iloc[0].strftime('%B %Y')}? (Enter ₹ in Lakhs, 1 decimal, e.g., 45.2)",
            "type": "numeric",
            "answer": round(max(0, dynamic.iloc[0]['CollectionsTotal']
                           - dynamic.iloc[0]['BOP_Balance']*0.75*0.08/12
                           - (dynamic.iloc[0]['BOP_Balance']-dynamic.iloc[0]['EOP_Balance'])*0.75
                           - dynamic.iloc[0]['BOP_Balance']*0.15*0.10/12
                           - (dynamic.iloc[0]['BOP_Balance']-dynamic.iloc[0]['EOP_Balance'])*0.15) / 1e5, 1),
            "tolerance": 10.0,
            "hint": "Equity = Collections - Senior Interest - Senior Principal - Mezz Interest - Mezz Principal - Reserve",
            "explanation": "The DAX waterfall uses sequential CALCULATE steps. Each allocation step reduces available cash before flowing to the next priority. Errors cascade through all lower tranches.",
            "points": 100
        },
        6: {
            "title": "IFRS 9 ECL",
            "narrative": "Your Ind AS 109 team needs the Stage 3 count for the provision computation.",
            "task": "How many loans are in IFRS 9 Stage 3 (DelinquencyDays ≥ 120 OR IsDefaulted = True)?",
            "type": "numeric",
            "answer": float(((loans['DelinquencyDays'] >= 120) | (loans['IsDefaulted'] == True)).sum()),
            "tolerance": 2.0,
            "hint": "Stage 3 = loans where DPD ≥ 120 OR IsDefaulted = TRUE. Use CALCULATE + FILTER in DAX.",
            "explanation": "IFRS 9 Stage 3 triggers lifetime ECL. The SWITCH(TRUE(), ...) pattern in DAX handles multi-condition classification elegantly with CALCULATE for ECL aggregation per stage.",
            "points": 100
        },
        7: {
            "title": "Stress Testing",
            "narrative": "RBI stress test guidelines require a 3× default rate scenario. Calculate the stressed ECL.",
            "task": "Under Severe Stress (3× default rate, 30% recovery haircut), what is the Total Stressed ECL? (Enter ₹ in Lakhs, 0 decimal)",
            "type": "numeric",
            "answer": round(loans.apply(lambda r:
                min(1.0, r['PD_Estimate']*3) * (r['LGD_Estimate']+(1-r['LGD_Estimate'])*0.30) * r['EAD'] *
                (1.0 if r['Calc_Stage']==1 else 1.5 if r['Calc_Stage']==2 else 2.0), axis=1).sum() / 1e5),
            "tolerance": 20.0,
            "hint": "Stressed PD = MIN(1.0, PD × 3.0) | Stressed LGD = LGD + (1-LGD) × 0.30",
            "explanation": "What-if parameters in Power BI enable dynamic stress testing. SELECTEDVALUE() retrieves the slicer value. The DAX pattern: MIN(1, [PD]*MultiplierParam) allows the model to cap PD at 100%.",
            "points": 100
        },
        8: {
            "title": "🔴 CRISIS MODE",
            "narrative": "⚠️ CRISIS ALERT: Delinquencies spiked 40% overnight! Rating agency demands emergency data tape! Board wants stress report by EOD! You have 3 tasks to complete.",
            "task": "Crisis Multi-Challenge: Answer all 3 questions correctly to earn full 200 points!",
            "type": "crisis",
            "questions": [
                {"q": "Which trigger is MOST LIKELY breached first under 5× stress?", "choices": ["OC Trigger", "Loss Trigger", "Delinquency Trigger", "Reserve Trigger"], "answer": "Loss Trigger"},
                {"q": f"Under Crisis stress (5× PD, 50% haircut), Total ECL in ₹ Lakhs (± ₹50L tolerance)?", "answer": round(loans.apply(lambda r: min(1.0, r['PD_Estimate']*5) * (r['LGD_Estimate']+(1-r['LGD_Estimate'])*0.50) * r['EAD'] * (1.0 if r['Calc_Stage']==1 else 1.5 if r['Calc_Stage']==2 else 2.0), axis=1).sum() / 1e5), "tolerance": 50},
                {"q": "Which vintage has the HIGHEST peak cumulative net loss rate?", "choices": sorted(vintage['VintageID'].unique()), "answer": vintage.groupby('VintageID')['CumulativeNetLossRate'].max().idxmax()},
            ],
            "explanation": "Crisis mode tests your ability to rapidly prioritize: Loss triggers typically breach first due to compounding net loss acceleration. Advanced DAX patterns (CALCULATETABLE, nested context transitions) enable real-time multi-pool crisis dashboards.",
            "points": 200
        }
    }

    ldata = levels[level_num]
    st.markdown(f'<div class="level-card"><h3>Level {level_num}: {ldata["title"]}</h3><p style="color:#8892a4">{ldata["narrative"]}</p></div>', unsafe_allow_html=True)
    st.markdown(f"**📋 Task**: {ldata['task']}")

    already_done = level_num in st.session_state['completed']
    if already_done:
        st.success(f"✅ Level {level_num} completed! Score earned: {st.session_state['level_scores'].get(level_num, 0)} pts")
        st.info(f"💡 **Explanation**: {ldata['explanation']}")
    else:
        if ldata['type'] == 'numeric':
            if 'hint' in ldata:
                with st.expander("💡 Hint"):
                    st.markdown(ldata['hint'])
            ans = st.number_input("Your Answer:", value=0.0, step=0.1, key=f"ans_{level_num}")
            if st.button(f"✅ Submit Level {level_num}", key=f"sub_{level_num}", use_container_width=True):
                if abs(ans - ldata['answer']) <= ldata['tolerance']:
                    st.session_state['score'] += ldata['points']
                    st.session_state['completed'].add(level_num)
                    st.session_state['level_scores'][level_num] = ldata['points']
                    st.session_state['current_level'] = min(8, level_num + 1)
                    st.success(f"🎉 Correct! +{ldata['points']} points! Answer: {ldata['answer']:.2f}")
                    st.info(f"💡 {ldata['explanation']}")
                else:
                    st.error(f"❌ Incorrect. Your answer: {ans:.2f} | Correct: {ldata['answer']:.2f} (±{ldata['tolerance']})")

        elif ldata['type'] == 'choice':
            user_choice = st.selectbox("Select your answer:", ldata['choices'], key=f"ch_{level_num}")
            if st.button(f"✅ Submit Level {level_num}", key=f"sub_{level_num}", use_container_width=True):
                if user_choice == ldata['answer']:
                    st.session_state['score'] += ldata['points']
                    st.session_state['completed'].add(level_num)
                    st.session_state['level_scores'][level_num] = ldata['points']
                    st.session_state['current_level'] = min(8, level_num + 1)
                    st.success(f"🎉 Correct! +{ldata['points']} points!")
                    st.info(f"💡 {ldata['explanation']}")
                else:
                    st.error(f"❌ Incorrect. Correct answer: **{ldata['answer']}**")

        elif ldata['type'] == 'crisis':
            st.markdown("### 🔴 Crisis Mode — 3 Tasks")
            answers_correct = []
            for i, q in enumerate(ldata['questions']):
                st.markdown(f"**Task {i+1}**: {q['q']}")
                if 'choices' in q:
                    resp = st.selectbox(f"Answer {i+1}:", q['choices'], key=f"crisis_{level_num}_{i}")
                    answers_correct.append(resp == q['answer'])
                else:
                    resp = st.number_input(f"Answer {i+1} (₹ Lakhs):", value=0.0, step=1.0, key=f"crisis_n_{level_num}_{i}")
                    answers_correct.append(abs(resp - q['answer']) <= q['tolerance'])

            if st.button("🔴 Submit Crisis Challenge", use_container_width=True):
                correct_count = sum(answers_correct)
                earned = int(ldata['points'] * correct_count / len(ldata['questions']))
                st.session_state['score'] += earned
                st.session_state['completed'].add(level_num)
                st.session_state['level_scores'][level_num] = earned
                if correct_count == len(ldata['questions']):
                    st.balloons()
                    st.success(f"🏆 PERFECT SCORE! All {len(ldata['questions'])} tasks correct! +{earned} points!")
                else:
                    st.warning(f"⚠️ {correct_count}/{len(ldata['questions'])} correct. +{earned} points.")
                st.info(f"💡 {ldata['explanation']}")
                for i, (q, correct) in enumerate(zip(ldata['questions'], answers_correct)):
                    status = "✅" if correct else "❌"
                    st.markdown(f"{status} Task {i+1}: Correct answer = **{q['answer']}**")

    if level_num in st.session_state['completed'] and level_num < 8:
        if st.button(f"➡️ Next Level: {levels[level_num+1]['title']}", use_container_width=True):
            st.session_state['current_level'] = level_num + 1

    if len(st.session_state['completed']) == 8:
        st.balloons()
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#FFB300,#FF6F00);padding:30px;border-radius:16px;text-align:center;margin-top:20px">
            <h1 style="color:#000;margin:0">🏆 CAMPAIGN COMPLETE!</h1>
            <h2 style="color:#000">Final Score: {st.session_state['score']} / 800</h2>
            <p style="color:#1a1a1a;font-size:18px">You have mastered Securitisation Risk Analytics!</p>
        </div>""", unsafe_allow_html=True)
