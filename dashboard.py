import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io

# 1. Setup & Caching
st.set_page_config(page_title="Digital Marketing Dashboard", layout="wide")

# --- CUSTOM CSS FOR METRIC CARDS ---
st.markdown("""
<style>
    /* Styling untuk Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.2s ease-in-out;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        border-color: #471470; /* Brand Color Hover */
    }

    /* Label Metrik (Judul Kecil di atas angka) */
    div[data-testid="stMetricLabel"] {
        font-size: 14px;
        color: #666;
        font-weight: 500;
    }

    /* Angka Metrik */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #333;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv('marketing_data.csv')
    df['created_date'] = pd.to_datetime(df['created_date'])
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("File 'marketing_data.csv' not found. Please run the data processing script first.")
    st.stop()

st.title("Digital Marketing Campaign Performance")
st.markdown("Analysis of Ads Performance by Skena Data Team")


# 2. Sidebar Filter (Interaktif)
# Logo Skena Data
try:
    st.sidebar.image("logo-skena-datav3.png", use_container_width=True)
except Exception:
    pass # Graceful fallback if image issues occur

st.sidebar.header("Filter Settings")

# Collapsible Filter: Periode Waktu
with st.sidebar.expander("📅 Periode Waktu", expanded=True):
    # Filter Date Range
    min_date = df['created_date'].min()
    max_date = df['created_date'].max()

    start_date, end_date = st.date_input(
        "Select Date Range",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

# Collapsible Filter: Kategori
with st.sidebar.expander("🏢 Filter Kategori", expanded=True):
    # Filter Client
    client_list = df['client_name'].unique().tolist()
    selected_clients = st.multiselect(
        "Select Client(s)",
        options=client_list,
        default=client_list
    )

    # Filter Campaign Objective (New)
    objective_list = df['campaign_objective'].unique().tolist()
    selected_objectives = st.multiselect(
        "Select Campaign Objective",
        options=objective_list,
        default=objective_list
    )

# Apply Filters
mask = (df['client_name'].isin(selected_clients)) & \
       (df['campaign_objective'].isin(selected_objectives)) & \
       (df['created_date'] >= pd.to_datetime(start_date)) & \
       (df['created_date'] <= pd.to_datetime(end_date))

filtered_df = df[mask]

if filtered_df.empty:
    st.warning("No data available based on the current filters.")
    st.stop()

# =====================================================================
# MAIN LAYOUT STRUCTURE
# =====================================================================
overview_tab, deep_dive_tab, strategy_tab = st.tabs(["📊 Overview & KPI", "🔍 Deep Dive Analysis", "📝 Strategic Recommendations"])

# =====================================================================
# TAB 1: OVERVIEW & KPI
# =====================================================================
with overview_tab:
    st.header("Executive Summary")
    
    # --- LOGIKA PERHITUNGAN DELTA (PREVIOUS PERIOD) ---
    # 1. Hitung durasi filter saat ini
    current_start = pd.to_datetime(start_date)
    current_end = pd.to_datetime(end_date)
    delta_days = (current_end - current_start).days
    
    # 2. Tentukan periode sebelumnya (Previous Period) dengan durasi yang sama
    prev_end = current_start - pd.Timedelta(days=1)
    prev_start = prev_end - pd.Timedelta(days=delta_days)
    
    # 3. Filter data untuk periode sebelumnya
    # Kita tetap respect filter Client/Objective, cuma ganti tanggal
    mask_prev = (df['client_name'].isin(selected_clients)) & \
                (df['campaign_objective'].isin(selected_objectives)) & \
                (df['created_date'] >= prev_start) & \
                (df['created_date'] <= prev_end)
    
    prev_filtered_df = df[mask_prev]
    
    # 4. Helper Function untuk menghitung Delta %
    def calculate_delta(current_val, prev_val, is_percentage=False):
        if prev_val == 0:
            return None # Tidak ada data sebelumnya
        diff = current_val - prev_val
        percent_change = (diff / prev_val) * 100
        
        if is_percentage:
            return f"{diff:.2f}% (pts)" # Untuk metrik persen (CTR), tampilkan selisih poin
        else:
            return f"{percent_change:+.1f}% vs Prev"

    # --- HITUNG CURRENT METRICS ---
    curr_spend = filtered_df['amount_spent'].sum()
    curr_purchase = filtered_df['purchase_value'].sum()
    curr_roas = filtered_df['roas'].mean()
    curr_cpc = filtered_df['cpc'].mean()
    curr_ctr = filtered_df['ctr_percentage'].mean()

    # --- HITUNG PREVIOUS METRICS ---
    prev_spend = prev_filtered_df['amount_spent'].sum()
    prev_purchase = prev_filtered_df['purchase_value'].sum()
    prev_roas = prev_filtered_df['roas'].mean() if not prev_filtered_df.empty else 0
    prev_cpc = prev_filtered_df['cpc'].mean() if not prev_filtered_df.empty else 0
    prev_ctr = prev_filtered_df['ctr_percentage'].mean() if not prev_filtered_df.empty else 0

    # --- TAMPILKAN METRICS DENGAN DELTA ---
    col1, col2, col3, col4, col5 = st.columns(5)

    def format_idr(value):
        if value >= 1_000_000_000:
            return f"IDR {value / 1_000_000_000:.2f} M"
        elif value >= 1_000_000:
            return f"IDR {value / 1_000_000:.2f} Mio"
        else:
            return f"IDR {value:,.0f}"

    col1.metric(
        "Total Spend", 
        format_idr(curr_spend), 
        delta=calculate_delta(curr_spend, prev_spend),
        delta_color="inverse" # Spend naik = Merah (Inverse)
    )
    col2.metric(
        "Total Purchase Value", 
        format_idr(curr_purchase), 
        delta=calculate_delta(curr_purchase, prev_purchase)
    )
    col3.metric(
        "Avg ROAS", 
        f"{curr_roas:.2f}", 
        delta=calculate_delta(curr_roas, prev_roas)
    )
    col4.metric(
        "Avg CPC", 
        format_idr(curr_cpc), 
        delta=calculate_delta(curr_cpc, prev_cpc),
        delta_color="inverse" # CPC naik = Merah
    )
    col5.metric(
        "Avg CTR", 
        f"{curr_ctr:.2f}%", 
        delta=calculate_delta(curr_ctr, prev_ctr, is_percentage=True)
    )

    # Dynamic Caption for Context
    if not prev_filtered_df.empty:
        st.caption(f"ℹ️ *Perbandingan dilakukan terhadap periode sebelumnya ({prev_start.strftime('%d %b')} - {prev_end.strftime('%d %b %Y')})*")
    else:
        st.caption("ℹ️ *Data periode sebelumnya tidak tersedia untuk perbandingan (Awal data tercapai atau rentang waktu terlalu luas).*")
    
    st.markdown("---")

    # --- AUTOMATED DATA HIGHLIGHTS (NLG) ---
    st.subheader("💡 Automated Data Highlights")
    
    # 1. Insight: Market Dominance
    if not filtered_df.empty:
        top_client_data = filtered_df.groupby('client_name')['purchase_value'].sum().sort_values(ascending=False).head(1)
        top_client_name = top_client_data.index[0]
        top_client_val = top_client_data.values[0]
        total_rev = filtered_df['purchase_value'].sum()
        dominance_pct = (top_client_val / total_rev * 100) if total_rev > 0 else 0
        
        insight_1 = f"**{top_client_name}** mendominasi pasar dengan kontribusi omzet sebesar **{dominance_pct:.1f}%** dari total pendapatan."
    else:
        insight_1 = "Data tidak cukup untuk analisis dominasi pasar."

    # 2. Insight: Cost Trend
    if not prev_filtered_df.empty:
        spend_diff = curr_spend - prev_spend
        spend_pct = (spend_diff / prev_spend * 100) if prev_spend > 0 else 0
        trend_text = "naik" if spend_diff > 0 else "turun"
        insight_2 = f"Total biaya iklan (Spend) **{trend_text} {abs(spend_pct):.1f}%** dibandingkan periode sebelumnya."
    else:
        insight_2 = "Perbandingan biaya dengan periode lalu tidak tersedia."

    # 3. Insight: Efficiency Winner
    if not filtered_df.empty:
        best_obj_data = filtered_df.groupby('campaign_objective')['roas'].mean().sort_values(ascending=False).head(1)
        best_obj_name = best_obj_data.index[0]
        best_obj_val = best_obj_data.values[0]
        insight_3 = f"Strategi **{best_obj_name}** adalah yang paling efisien dengan rata-rata ROAS **{best_obj_val:.2f}x**."
    else:
        insight_3 = "Data ROAS tidak tersedia."

    st.info(f"""
    *   {insight_1}
    *   {insight_2}
    *   {insight_3}
    """)
    
    st.markdown("---")

    # 4. Visualisasi Utama (KPI Charts)
    col_chart1, col_chart2 = st.columns(2)

    # Grafik 1 (Line Chart): Tren Bulanan with Anomaly Detection
    daily_trend = filtered_df.groupby('created_date')[['amount_spent', 'purchase_value']].sum().reset_index()
    
    # --- ANOMALY DETECTION LOGIC ---
    try:
        if len(daily_trend) > 7:
            daily_trend['rolling_mean'] = daily_trend['purchase_value'].rolling(window=7).mean()
            daily_trend['rolling_std'] = daily_trend['purchase_value'].rolling(window=7).std()
            # Define Anomaly: Value > Mean + 2*Std (Spike) or Value < Mean - 2*Std (Drop)
            daily_trend['is_anomaly'] = ((daily_trend['purchase_value'] > (daily_trend['rolling_mean'] + 2 * daily_trend['rolling_std'])) | 
                                         (daily_trend['purchase_value'] < (daily_trend['rolling_mean'] - 2 * daily_trend['rolling_std'])))
            anomalies = daily_trend[daily_trend['is_anomaly']]
        else:
            anomalies = pd.DataFrame()
    except Exception:
        anomalies = pd.DataFrame()

    daily_trend_melted = daily_trend.melt(id_vars='created_date', value_vars=['amount_spent', 'purchase_value'], var_name='Metric', value_name='Value')

    fig_line = px.line(
        daily_trend_melted, 
        x='created_date', 
        y='Value', 
        color='Metric',
        title="Daily Trend: Spend vs Purchase Value (with Anomaly Detection)",
        template="plotly_white"
    )
    
    # Add Anomaly Markers
    if not anomalies.empty:
        fig_line.add_trace(go.Scatter(
            x=anomalies['created_date'],
            y=anomalies['purchase_value'],
            mode='markers',
            name='Anomaly (Spike/Drop)',
            marker=dict(color='red', size=10, symbol='x'),
            text=['Anomaly Detected'] * len(anomalies),
            hoverinfo='text+x+y'
        ))

    col_chart1.plotly_chart(fig_line, use_container_width=True)

    # Grafik 2 (Pie Chart - New): Proporsi Spend by Client
    spend_by_client = filtered_df.groupby('client_name')['amount_spent'].sum().reset_index()
    fig_pie = px.pie(
        spend_by_client,
        values='amount_spent',
        names='client_name',
        title="Total Ad Spend Distribution by Client",
        template="plotly_white"
    )
    col_chart2.plotly_chart(fig_pie, use_container_width=True)


    col_chart3, col_chart4 = st.columns(2)

    # Grafik 3 (Bar Chart): ROAS by Campaign Objective
    roas_by_obj = filtered_df.groupby('campaign_objective')['roas'].mean().reset_index()
    fig_bar = px.bar(
        roas_by_obj,
        x='campaign_objective',
        y='roas',
        color='campaign_objective',
        title="Average ROAS by Campaign Objective",
        template="plotly_white"
    )
    col_chart3.plotly_chart(fig_bar, use_container_width=True)

    # Grafik 4 (Scatter Plot): CPC vs CTR (Efficiency)
    fig_scatter = px.scatter(
        filtered_df, 
        x='cpc', 
        y='ctr_percentage', 
        color='client_name',
        size='amount_spent', # Bubble size based on spend
        title="Ad Efficiency: CPC vs CTR (Size = Spend)",
        hover_data=['campaign_objective'],
        template="plotly_white"
    )
    col_chart4.plotly_chart(fig_scatter, use_container_width=True)

    # Performance Metrics Section (New Analysis)
    st.markdown("---")
    st.header("Performance Metrics")
    st.markdown("""
    Di bagian ini, kita akan menjawab pertanyaan fundamental mengenai kesehatan performa iklan secara keseluruhan. Kita akan melihat seberapa efisien iklan menarik perhatian (CTR) dan seberapa efektif iklan menghasilkan uang (Omzet & ROAS).

    **Pertanyaan Kunci:**
    1.  Berapa nilai CTR keseluruhan?
    2.  Bagaimana perbandingan CTR antara *Traffic* vs *Sales*?
    3.  Berapa total Omzet yang dihasilkan?
    4.  Berapa ROAS keseluruhan?
    """)

    # Calculations on Filtered Data
    # 1. Overall CTR
    total_clicks_metric = filtered_df['clicks'].sum()
    total_impressions_metric = filtered_df['impressions'].sum()
    overall_ctr = (total_clicks_metric / total_impressions_metric * 100) if total_impressions_metric > 0 else 0

    # 2. Total Purchase Value (Omzet)
    total_omzet_metric = filtered_df['purchase_value'].sum()

    # 3. Overall ROAS
    total_spend_metric = filtered_df['amount_spent'].sum()
    overall_roas_metric = (total_omzet_metric / total_spend_metric) if total_spend_metric > 0 else 0

    # 4. ROAS (Sales Only)
    sales_only_df = filtered_df[filtered_df['campaign_objective'] == 'Sales']
    sales_spend = sales_only_df['amount_spent'].sum()
    sales_rev = sales_only_df['purchase_value'].sum()
    roas_sales_only = (sales_rev / sales_spend) if sales_spend > 0 else 0

    # Display Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Overall CTR", f"{overall_ctr:.2f}%")
    m2.metric("Total Omzet", format_idr(total_omzet_metric))
    m3.metric("Overall ROAS (Blended)", f"{overall_roas_metric:.2f}x")
    m4.metric("ROAS (Sales Only)", f"{roas_sales_only:.2f}x")

    # Visualizations for Performance Metrics
    col_perf1, col_perf2 = st.columns(2)

    # Chart A: CTR Comparison
    ctr_by_obj = filtered_df.groupby('campaign_objective')[['clicks', 'impressions']].sum().reset_index()
    ctr_by_obj['ctr'] = (ctr_by_obj['clicks'] / ctr_by_obj['impressions']) * 100

    fig_ctr = px.bar(
        ctr_by_obj, 
        x='campaign_objective', 
        y='ctr',
        text_auto='.2f',
        title="A.2: Click-Through Rate (CTR) Comparison",
        color='campaign_objective',
        template="plotly_white",
        labels={'ctr': 'CTR (%)'}
    )
    fig_ctr.update_traces(textposition='outside')
    fig_ctr.update_layout(yaxis_range=[0, max(ctr_by_obj['ctr']) * 1.2]) # Add space for text
    col_perf1.plotly_chart(fig_ctr, use_container_width=True)

    # Chart B: Spend vs Revenue
    fin_data = pd.DataFrame({
        'Metric': ['Total Spend', 'Total Revenue'],
        'Value': [total_spend_metric, total_omzet_metric]
    })

    fig_fin = px.bar(
        fin_data, 
        x='Metric', 
        y='Value', 
        text_auto='.2s', 
        title="A.3 & A.4: Total Spend vs Revenue",
        color='Metric',
        template="plotly_white",
        color_discrete_sequence=['#ff7f0e', '#2ca02c'] 
    )
    fig_fin.update_traces(textposition='outside')
    col_perf2.plotly_chart(fig_fin, use_container_width=True)


# =====================================================================
# TAB 2: DEEP DIVE ANALYSIS
# =====================================================================
with deep_dive_tab:
    # ---------------------------------------------------------------------
    # NAVIGATION SETUP (Radio as Tabs)
    # ---------------------------------------------------------------------
    
    # Custom CSS to style Radio Buttons as Tabs
    st.markdown("""
        <style>
        div.row-widget.stRadio > div {
            flex-direction: row;
            justify-content: flex-start;
            gap: 10px;
            width: 100%;
        }
        div.row-widget.stRadio > div > label {
            background-color: #f0f2f6;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            border: 1px solid #e0e0e0;
            font-weight: 600;
            color: #555;
            flex-grow: 1;
            text-align: center;
        }
        div.row-widget.stRadio > div > label[data-baseweb="radio"] {
            background-color: #471470;
            color: white;
            border-color: #471470;
        }
        div.row-widget.stRadio > div > label:hover {
            background-color: #f9f9f9;
            border-color: #471470;
            color: #471470;
        }
        </style>
    """, unsafe_allow_html=True)

    # Navigation Options
    nav_options = ['📈 Time & Trend Analysis', '🏢 Industry & Client Breakdown', '🔻 Marketing Funnel Analysis', '🎯 Strategy & Quadrant Matrix']
    
    # Render Navigation (Radio)
    selection = st.radio(
        "Navigate Analysis:", 
        nav_options, 
        horizontal=True, 
        label_visibility="collapsed"
    )
    
    st.markdown("---")

    # ---------------------------------------------------------------------
    # SECTION 1: Trend & Time Series Analysis
    # ---------------------------------------------------------------------
    if selection == '📈 Time & Trend Analysis':
        st.header("Analisis Utama: Trend & Time Series Analysis")
        st.markdown("""
        Di bagian ini, kita akan melihat pergerakan performa iklan dari waktu ke waktu untuk mendeteksi pola pertumbuhan dan musiman.

        **Pertanyaan Kunci:**
        1.  Bagaimana tren performa iklan dari bulan ke bulan?
        2.  Kapan terjadi lonjakan omzet yang signifikan?
        3.  Apakah Ramadhan dan Akhir Pekan (Seasonality) memberikan dampak positif?
        """)

        # --- 1. Persiapan Data Time Series ---
        # Agregasi Bulanan
        filtered_df['month'] = filtered_df['created_date'].dt.to_period('M')
        monthly_trend = filtered_df.groupby('month')[['purchase_value', 'amount_spent']].sum().reset_index()
        monthly_trend['roas'] = np.where(monthly_trend['amount_spent'] > 0, monthly_trend['purchase_value'] / monthly_trend['amount_spent'], 0)
        monthly_trend['month_str'] = monthly_trend['month'].astype(str)

        # Agregasi Harian
        daily_trend = filtered_df.groupby('created_date')[['purchase_value']].sum().reset_index()

        # Seasonality Data
        ramadhan_perf = filtered_df.groupby('is_ramadhan')[['purchase_value']].mean().reset_index()
        ramadhan_perf['status'] = ramadhan_perf['is_ramadhan'].map({True: 'Ramadhan', False: 'Normal Days'})

        weekend_perf = filtered_df.groupby('is_weekend')[['purchase_value']].mean().reset_index()
        weekend_perf['status'] = weekend_perf['is_weekend'].map({True: 'Weekend', False: 'Weekday'})

        # --- HITUNG SUMMARY METRICS SECTION 2 ---
        # 1. Best Month
        best_month_row = monthly_trend.loc[monthly_trend['purchase_value'].idxmax()]
        best_month_name = best_month_row['month_str']
        best_month_val = best_month_row['purchase_value']

        # 2. Ramadhan Lift
        avg_rev_ramadhan = filtered_df[filtered_df['is_ramadhan']]['purchase_value'].mean()
        avg_rev_normal = filtered_df[~filtered_df['is_ramadhan']]['purchase_value'].mean()
        if avg_rev_normal > 0:
            ramadhan_lift = ((avg_rev_ramadhan - avg_rev_normal) / avg_rev_normal) * 100
        else:
            ramadhan_lift = 0

        # 3. Weekend Lift
        avg_rev_weekend = filtered_df[filtered_df['is_weekend']]['purchase_value'].mean()
        avg_rev_weekday = filtered_df[~filtered_df['is_weekend']]['purchase_value'].mean()
        if avg_rev_weekday > 0:
            weekend_lift = ((avg_rev_weekend - avg_rev_weekday) / avg_rev_weekday) * 100
        else:
            weekend_lift = 0

        # 4. Peak Daily Revenue
        peak_daily_date = daily_trend.loc[daily_trend['purchase_value'].idxmax(), 'created_date'].strftime('%d %b %Y')
        peak_daily_val = daily_trend['purchase_value'].max()

        # --- TAMPILKAN SUMMARY METRICS ---
        col_s2_1, col_s2_2, col_s2_3, col_s2_4 = st.columns(4)

        col_s2_1.metric("Best Month", best_month_name, format_idr(best_month_val))
        col_s2_2.metric("Ramadhan Impact", f"{ramadhan_lift:+.2f}%", "vs Normal Days")
        col_s2_3.metric("Weekend Impact", f"{weekend_lift:+.2f}%", "vs Weekdays")
        col_s2_4.metric("Highest Daily Rev", format_idr(peak_daily_val), peak_daily_date)

        st.markdown("---")

        # --- 2. Visualisasi ---

        # B.1: Tren Bulanan Omzet & ROAS (Dual Axis)
        fig_b1 = go.Figure()

        # Bar Chart (Omzet)
        fig_b1.add_trace(go.Bar(
            x=monthly_trend['month_str'],
            y=monthly_trend['purchase_value'],
            name='Omzet (Revenue)',
            marker_color='skyblue',
            opacity=0.8
        ))

        # Line Chart (ROAS)
        fig_b1.add_trace(go.Scatter(
            x=monthly_trend['month_str'],
            y=monthly_trend['roas'],
            name='ROAS',
            yaxis='y2',
            line=dict(color='crimson', width=3),
            mode='lines+markers'
        ))

        fig_b1.update_layout(
            title='B.1: Tren Bulanan Omzet & ROAS (2023)',
            xaxis_title='Bulan',
            yaxis=dict(title='Total Omzet (Rupiah)', showgrid=False),
            yaxis2=dict(title='ROAS (x)', overlaying='y', side='right', showgrid=False),
            legend=dict(x=0, y=1.1, orientation='h'),
            template='plotly_white'
        )
        st.plotly_chart(fig_b1, use_container_width=True)

        # B.2: Tren Harian (Daily Revenue) dengan Highlight Ramadhan & Anomaly
        # --- ANOMALY DETECTION LOGIC (TAB 2) ---
        try:
            if len(daily_trend) > 7:
                daily_trend['rolling_mean'] = daily_trend['purchase_value'].rolling(window=7).mean()
                daily_trend['rolling_std'] = daily_trend['purchase_value'].rolling(window=7).std()
                daily_trend['is_anomaly'] = ((daily_trend['purchase_value'] > (daily_trend['rolling_mean'] + 2 * daily_trend['rolling_std'])) | 
                                             (daily_trend['purchase_value'] < (daily_trend['rolling_mean'] - 2 * daily_trend['rolling_std'])))
                anomalies_b2 = daily_trend[daily_trend['is_anomaly']]
            else:
                anomalies_b2 = pd.DataFrame()
        except Exception:
            anomalies_b2 = pd.DataFrame()

        fig_b2 = px.line(
            daily_trend, 
            x='created_date', 
            y='purchase_value', 
            title='B.2: Tren Omzet Harian (with Anomaly Detection)',
            labels={'purchase_value': 'Omzet Harian', 'created_date': 'Tanggal'},
            line_shape='linear'
        )
        fig_b2.update_traces(line_color='seagreen')

        # Highlight Ramadhan Area
        ramadhan_start = pd.Timestamp('2023-03-22')
        ramadhan_end = pd.Timestamp('2023-04-21')

        fig_b2.add_vrect(
            x0=ramadhan_start, x1=ramadhan_end, 
            fillcolor="orange", opacity=0.2, 
            layer="below", line_width=0,
            annotation_text="Ramadhan", annotation_position="top left"
        )
        
        # Add Anomaly Markers
        if not anomalies_b2.empty:
            fig_b2.add_trace(go.Scatter(
                x=anomalies_b2['created_date'],
                y=anomalies_b2['purchase_value'],
                mode='markers',
                name='Anomaly',
                marker=dict(color='red', size=8, symbol='x'),
                text=['Anomaly Detected'] * len(anomalies_b2),
                hoverinfo='text+x+y'
            ))
            
        st.plotly_chart(fig_b2, use_container_width=True)

        # B.3: Seasonality Impact (Side by Side)
        col_season1, col_season2 = st.columns(2)

        # Efek Ramadhan
        fig_ramadhan = px.bar(
            ramadhan_perf, 
            x='status', 
            y='purchase_value', 
            title='Efek Ramadhan (Avg Omzet Harian)',
            color='status',
            color_discrete_map={'Normal Days': 'gray', 'Ramadhan': 'orange'},
            template='plotly_white',
            text_auto='.2s'
        )
        fig_ramadhan.update_layout(showlegend=False)
        col_season1.plotly_chart(fig_ramadhan, use_container_width=True)

        # Efek Weekend
        fig_weekend = px.bar(
            weekend_perf, 
            x='status', 
            y='purchase_value', 
            title='Efek Weekend (Avg Omzet Harian)',
            color='status',
            color_discrete_map={'Weekday': 'lightblue', 'Weekend': 'navy'},
            template='plotly_white',
            text_auto='.2s'
        )
        fig_weekend.update_layout(showlegend=False)
        col_season2.plotly_chart(fig_weekend, use_container_width=True)
        

    # ---------------------------------------------------------------------
    # SECTION 2: Industry & Account Analysis
    # ---------------------------------------------------------------------
    elif selection == '🏢 Industry & Client Breakdown':
        st.header("Analisis Utama: Industry & Account Analysis")
        st.markdown("""
        Di bagian ini, kita akan membedah performa berdasarkan kategori industri dan akun klien. Tujuannya adalah menemukan sektor mana yang paling menguntungkan (Winning Industry) dan klien mana yang menjadi "Hero Account".

        **Pertanyaan Kunci:**
        1.  Industri mana dengan total dan rata-rata omzet tertinggi?
        2.  Siapa klien (Client) yang menyumbang revenue terbesar?
        3.  Industri mana yang paling efisien (ROAS tertinggi)?
        """)

        # --- PREPARE DATA SECTION 3 ---
        # C.1 & C.3: Analisis Per Industri
        # Agregasi Sum dan Mean
        industry_perf = filtered_df.groupby('industry')[['purchase_value', 'amount_spent']].agg(['sum', 'mean']).reset_index()
        # Flatten Columns
        industry_perf.columns = ['industry', 'total_revenue', 'avg_daily_revenue', 'total_spend', 'avg_daily_spend']
        # Hitung ROAS
        industry_perf['roas'] = np.where(industry_perf['total_spend'] > 0, industry_perf['total_revenue'] / industry_perf['total_spend'], 0)

        # Sorting
        industry_sorted_rev = industry_perf.sort_values('total_revenue', ascending=False)
        industry_sorted_roas = industry_perf.sort_values('roas', ascending=False)

        # C.2: Analisis Per Akun Klien
        client_perf = filtered_df.groupby(['client_name', 'industry'])[['purchase_value', 'amount_spent']].sum().reset_index()
        client_perf['roas'] = np.where(client_perf['amount_spent'] > 0, client_perf['purchase_value'] / client_perf['amount_spent'], 0)
        client_top_rev = client_perf.sort_values('purchase_value', ascending=False)

        # --- HITUNG SUMMARY METRICS SECTION 3 ---
        # 1. Winning Industry
        winning_ind_row = industry_sorted_rev.iloc[0]
        winning_ind_name = winning_ind_row['industry']
        winning_ind_val = winning_ind_row['total_revenue']

        # 2. Hero Account
        hero_client_row = client_top_rev.iloc[0]
        hero_client_name = hero_client_row['client_name']
        hero_client_val = hero_client_row['purchase_value']

        # 3. Most Efficient Industry
        efficient_ind_row = industry_sorted_roas.iloc[0]
        efficient_ind_name = efficient_ind_row['industry']
        efficient_ind_roas = efficient_ind_row['roas']

        # --- TAMPILKAN SUMMARY METRICS ---
        col_s3_1, col_s3_2, col_s3_3 = st.columns(3)
        col_s3_1.metric("Winning Industry (Omzet)", winning_ind_name, format_idr(winning_ind_val))
        col_s3_2.metric("Hero Account (Client)", hero_client_name, format_idr(hero_client_val))
        col_s3_3.metric("Most Efficient Ind (ROAS)", efficient_ind_name, f"{efficient_ind_roas:.2f}x")

        # --- VISUALISASI SECTION 3 ---
        col_ind1, col_ind2 = st.columns(2)

        # C.1: Total Revenue per Industri (Bar Chart)
        fig_c1 = px.bar(
            industry_sorted_rev,
            x='industry',
            y='total_revenue',
            title="C.1: Total Omzet per Industri (Winning Industry)",
            text_auto='.2s',
            template="plotly_white",
            color='industry',
            color_discrete_sequence=px.colors.qualitative.Pastel # Mimic soft colors
        )
        fig_c1.update_traces(showlegend=False)
        fig_c1.update_layout(yaxis_title="Total Revenue (Rupiah)")
        col_ind1.plotly_chart(fig_c1, use_container_width=True)

        # C.3: Efisiensi Iklan (ROAS) per Industri (Bar Chart)
        fig_c3 = px.bar(
            industry_sorted_roas,
            x='industry',
            y='roas',
            title="C.3: Efisiensi Iklan (ROAS) per Industri",
            text_auto='.2f',
            template="plotly_white",
            color='industry',
            color_discrete_sequence=['green', 'limegreen', 'lightgreen'] # Custom green palette logic approximation
        )
        fig_c3.update_traces(showlegend=False)
        fig_c3.update_layout(yaxis_title="ROAS (x)")
        col_ind2.plotly_chart(fig_c3, use_container_width=True)

        # C.2: Peringkat Klien Berdasarkan Omzet (Bar Chart Colored by Industry)
        fig_c2 = px.bar(
            client_top_rev,
            x='client_name',
            y='purchase_value',
            color='industry', # Hue equivalent
            title="C.2: Peringkat Klien Berdasarkan Omzet",
            text_auto='.2s',
            template="plotly_white",
            labels={'purchase_value': 'Total Revenue', 'client_name': 'Klien'}
        )
        fig_c2.update_layout(xaxis={'categoryorder': 'total descending'})
        st.plotly_chart(fig_c2, use_container_width=True)

        st.markdown("---")

        # --- VISUALISASI HIERARKI (TREEMAP) ---
        st.markdown("### 🗺️ Industry & Client Hierarchy Map (Treemap)")
        st.info("""
        **Cara Membaca Peta Wilayah Bisnis Ini:**
        Bayangkan grafik di bawah ini sebagai **Peta Wilayah Kekuasaan** bisnis Anda.
        
        *   **Luas Wilayah (Ukuran Kotak):** Menunjukkan seberapa besar kontribusi Omzet (Revenue) dari setiap Klien/Industri. *Semakin besar kotaknya, semakin 'kaya' wilayah tersebut.*
        *   **Iklim Bisnis (Warna):** Menunjukkan efisiensi penggunaan budget (ROAS).
            *   🟢 **Hijau:** Wilayah Subur (Sangat Efisien, Profit Tinggi).
            *   🔴 **Merah:** Wilayah Kritis (Boros Biaya, Hasil Sedikit).
            
        **Insight Cepat:** Carilah kotak yang **Besar tapi Merah/Kuning**. Itu adalah area di mana Anda mendapatkan banyak omzet, tapi dengan biaya yang mungkin terlalu mahal (Inefisien).
        """)

        # Prepare Data for Treemap (Ensure consistent data source)
        treemap_data = client_perf.copy()
        
        # Create Treemap
        fig_treemap = px.treemap(
            treemap_data,
            path=[px.Constant("All Industries"), 'industry', 'client_name'],
            values='purchase_value',
            color='roas',
            color_continuous_scale='RdYlGn',
            color_continuous_midpoint=treemap_data['roas'].mean(), # Center color scale at average
            title="<b>Market Map:</b> Revenue (Size) & Efficiency (Color) Distribution",
            hover_data={'purchase_value': ':,.0f', 'roas': ':.2f', 'amount_spent': ':,.0f'},
            template="plotly_white"
        )
        
        fig_treemap.update_traces(textinfo="label+value+percent entry")
        fig_treemap.update_layout(margin=dict(t=50, l=25, r=25, b=25), height=600)
        
        st.plotly_chart(fig_treemap, use_container_width=True)


    # ---------------------------------------------------------------------
    # SECTION 3: Marketing Funnel Analysis
    # ---------------------------------------------------------------------
    elif selection == '🔻 Marketing Funnel Analysis':
        st.header("Marketing Conversion Funnel")
        st.markdown("""
        **Memahami Perjalanan Pelanggan (Customer Journey):**
        Visualisasi di bawah ini adalah **Corong Penjualan (Sales Funnel)** yang menunjukkan seberapa efektif iklan Anda menggiring audiens dari sekadar "Melihat" hingga "Membeli".
        
        **Urutan Tahapan:**
        1.  👀 **Impressions (Views):** Total kali iklan Anda muncul di layar. (Tahap *Awareness*)
        2.  👆 **Clicks (Traffic):** Jumlah orang yang tertarik dan mengklik iklan Anda. (Tahap *Interest*)
        3.  🛒 **Add to Cart (Intent):** Jumlah orang yang cukup serius hingga memasukkan produk ke keranjang. (Tahap *Desire*)
        4.  💰 **Purchase (Sales):** Jumlah orang yang akhirnya menyelesaikan pembayaran. (Tahap *Action*)
        
        *Analisis ini krusial untuk menemukan "kebocoran" (drop-off). Misalnya, jika banyak Klik tapi sedikit Purchase, mungkin ada masalah di Website/Harga.*
        """)

        # 1. Prepare Funnel Data
        # Check if 'add_to_cart' exists in columns, if not use 0
        atc_val = filtered_df['add_to_cart'].sum() if 'add_to_cart' in filtered_df.columns else 0
        
        funnel_data = dict(
            number=[
                filtered_df['impressions'].sum(),
                filtered_df['clicks'].sum(),
                atc_val,
                filtered_df['purchase'].sum()
            ],
            stage=["Impressions (Views)", "Clicks (Traffic)", "Add to Cart (Intent)", "Purchase (Sales)"]
        )
        funnel_df = pd.DataFrame(funnel_data)
        
        # 2. Visualization
        col_funnel1, col_funnel2 = st.columns([3, 1])
        
        with col_funnel1:
            fig_funnel = px.funnel(
                funnel_df, 
                x='number', 
                y='stage', 
                title="<b>Marketing Conversion Funnel</b>",
                template="plotly_white",
                color='stage',
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_funnel.update_traces(textinfo="value+percent previous")
            st.plotly_chart(fig_funnel, use_container_width=True)
            
        with col_funnel2:
            st.subheader("Conversion Rates")
            
            # CTR
            ctr = (funnel_data['number'][1] / funnel_data['number'][0] * 100) if funnel_data['number'][0] > 0 else 0
            st.metric("CTR (View to Click)", f"{ctr:.2f}%", help="Persentase audiens yang mengklik iklan setelah melihatnya. (Benchmark Global: 1-2%)")
            
            # Click to ATC
            atc_rate = (funnel_data['number'][2] / funnel_data['number'][1] * 100) if funnel_data['number'][1] > 0 else 0
            st.metric("Click to Cart Rate", f"{atc_rate:.2f}%", help="Persentase pengunjung yang tertarik hingga memasukkan produk ke keranjang. Jika rendah, periksa konten Landing Page.")
            
            # Cart to Purchase
            cart_conv = (funnel_data['number'][3] / funnel_data['number'][2] * 100) if funnel_data['number'][2] > 0 else 0
            st.metric("Cart to Purchase", f"{cart_conv:.2f}%", help="Persentase user yang 'Check Out' dan membayar. Jika rendah, periksa harga atau kemudahan metode pembayaran.")
            
            # Overall Conv Rate
            overall_cv = (funnel_data['number'][3] / funnel_data['number'][1] * 100) if funnel_data['number'][1] > 0 else 0
            st.metric("Overall CV Rate", f"{overall_cv:.2f}%", help="Conversion Rate total dari Klik hingga Purchase. (Benchmark E-commerce: 2-3%)")

        st.info("💡 **Tips:** Jika *CTR* rendah, perbaiki kreatif iklan (Gambar/Video). Jika *Click-to-Cart* rendah, perbaiki Landing Page. Jika *Cart-to-Purchase* rendah, perbaiki proses Checkout/Harga.")


    # ---------------------------------------------------------------------
    # SECTION 4: Strategic Analysis (Quadrant & Simulation)
    # ---------------------------------------------------------------------
    elif selection == '🎯 Strategy & Quadrant Matrix':
        st.header("Analisis Strategis: Pemetaan Masalah & Simulasi Solusi")
        st.markdown("""
        Sebelum menuliskan rekomendasi bisnis, kita perlu memvisualisasikan posisi setiap klien dan mensimulasikan dampak dari rekomendasi kita.

        Kita akan melakukan dua hal:
        1.  **Quadrant Analysis (Matrix Biaya vs Efisiensi):** Memetakan klien ke dalam 4 kuadran (Stars, Cash Cows, Question Marks, Bleeders) untuk menentukan strategi spesifik per akun.
        2.  **Simulasi Realokasi Budget:** Menghitung estimasi kenaikan omzet jika kita memindahkan sebagian budget dari *Traffic* (yang tidak menghasilkan omzet langsung) ke *Sales*.
        """)

        # --- 1. Persiapan Data untuk Quadrant Analysis ---
        client_matrix = filtered_df.groupby('client_name')[['purchase_value', 'amount_spent']].sum().reset_index()
        client_matrix['roas'] = np.where(client_matrix['amount_spent'] > 0, client_matrix['purchase_value'] / client_matrix['amount_spent'], 0)

        # Thresholds
        avg_roas_client = client_matrix['roas'].mean()
        avg_spend_client = client_matrix['amount_spent'].mean()

        # --- 2. Simulasi Realokasi Budget ---
        # Hitung Traffic Spend
        traffic_spend = filtered_df[filtered_df['campaign_objective'] == 'Traffic']['amount_spent'].sum()

        # Benchmark ROAS Sales (Dynamic from current filter)
        sales_only_data = filtered_df[filtered_df['campaign_objective'] == 'Sales']
        if not sales_only_data.empty and sales_only_data['amount_spent'].sum() > 0:
            sales_roas_benchmark = sales_only_data['purchase_value'].sum() / sales_only_data['amount_spent'].sum()
        else:
            sales_roas_benchmark = 1.62 # Fallback to global average/hardcoded if no sales data

        # --- TAMPILKAN EXECUTIVE SUMMARY (SIMULASI) ---
        st.subheader("Simulasi Strategi: Re-alokasi Budget Traffic ke Sales")
        
        # Interactive Slider
        reallocation_pct = st.slider("Geser untuk menentukan % Budget Traffic yang akan dipindahkan:", 
                                     min_value=0, max_value=100, value=50, step=5)
        
        # Simulasi Dinamis
        budget_moved = traffic_spend * (reallocation_pct / 100)
        potential_revenue_gain = budget_moved * sales_roas_benchmark
        current_total_rev = filtered_df['purchase_value'].sum()
        projected_growth_pct = (potential_revenue_gain / current_total_rev * 100) if current_total_rev > 0 else 0

        col_sim1, col_sim2, col_sim3, col_sim4 = st.columns(4)

        col_sim1.metric("Traffic Budget (Potential Saving)", format_idr(traffic_spend))
        col_sim2.metric(f"Proposed Shift ({reallocation_pct}%)", format_idr(budget_moved))
        col_sim3.metric("Est. Revenue Gain", format_idr(potential_revenue_gain), f"ROAS {sales_roas_benchmark:.2f}x")
        col_sim4.metric("Projected Growth", f"+{projected_growth_pct:.2f}%")

        st.markdown("---")

        # --- 3. Visualisasi Quadrant Analysis (Plotly) ---
        # Prepare Plotly Figure
        fig_quadrant = px.scatter(
            client_matrix,
            x='amount_spent',
            y='roas',
            text='client_name',
            size='amount_spent', # Bubble size
            color='client_name', # Color by client for aesthetics
            title="<b>Client Performance Matrix: Spend vs ROAS</b>",
            labels={'amount_spent': 'Total Ad Spend (IDR)', 'roas': 'ROAS (x)'},
            template='plotly_white',
            hover_data={'purchase_value': True, 'amount_spent': ':.2s', 'roas': ':.2f'}
        )

        fig_quadrant.update_traces(
            textposition='top center',
            textfont=dict(size=11, family="Arial", color='black'),
            marker=dict(opacity=0.9, line=dict(width=1, color='White'), sizemode='area', sizeref=2.*max(client_matrix['amount_spent'])/(60.**2)) # Adjust bubble scaling
        )

        # Determine Axis Limits for Shapes (Add padding for aesthetics)
        # Use dynamic ranges instead of starting from 0 to focus on the spread
        x_max = client_matrix['amount_spent'].max() * 1.15
        y_max = client_matrix['roas'].max() * 1.15
        x_min = client_matrix['amount_spent'].min() * 0.85
        y_min = client_matrix['roas'].min() * 0.85

        fig_quadrant.update_layout(
            xaxis_range=[x_min, x_max], 
            yaxis_range=[y_min, y_max],
            showlegend=False, # Hide legend to keep it clean, names are on bubbles
            height=600, # Taller canvas
            title_font=dict(size=20),
            xaxis=dict(showgrid=True, gridcolor='#f0f0f0'),
            yaxis=dict(showgrid=True, gridcolor='#f0f0f0')
        )

        # Add Quadrant Backgrounds (Shapes) - Softer Pastel Palette
        # 1. STAR (Top Right) - Soft Green
        fig_quadrant.add_shape(type="rect",
            x0=avg_spend_client, y0=avg_roas_client, x1=x_max, y1=y_max,
            fillcolor="#e8f5e9", opacity=0.6, layer="below", line_width=0,
        )
        # 2. ALERT (Bottom Right) - Soft Red
        fig_quadrant.add_shape(type="rect",
            x0=avg_spend_client, y0=y_min, x1=x_max, y1=avg_roas_client,
            fillcolor="#ffebee", opacity=0.6, layer="below", line_width=0,
        )
        # 3. POTENTIAL (Top Left) - Soft Orange/Yellow
        fig_quadrant.add_shape(type="rect",
            x0=x_min, y0=avg_roas_client, x1=avg_spend_client, y1=y_max,
            fillcolor="#fff8e1", opacity=0.6, layer="below", line_width=0,
        )
        # 4. LOW PRIORITY (Bottom Left) - Soft Grey
        fig_quadrant.add_shape(type="rect",
            x0=x_min, y0=y_min, x1=avg_spend_client, y1=avg_roas_client,
            fillcolor="#f5f5f5", opacity=0.6, layer="below", line_width=0,
        )

        # Add Threshold Lines (Sleeker Look)
        fig_quadrant.add_hline(y=avg_roas_client, line_dash="dot", line_color="#555", line_width=2, annotation_text=f"Avg ROAS: {avg_roas_client:.2f}", annotation_position="bottom left")
        fig_quadrant.add_vline(x=avg_spend_client, line_dash="dot", line_color="#555", line_width=2, annotation_text="Avg Spend", annotation_position="top left")

        # Add Quadrant Labels (Styled Annotations)
        def add_quadrant_label(x, y, text, color):
            fig_quadrant.add_annotation(
                x=x, y=y, 
                text=text, 
                showarrow=False, 
                font=dict(color=color, size=14, family="Arial Black"),
                bgcolor="rgba(255,255,255,0.7)", # Semi-transparent background for readability
                bordercolor=color,
                borderwidth=1,
                borderpad=4,
                align="center"
            )

        add_quadrant_label(x_max*0.9, y_max*0.95, "STAR CLIENT\n(Scale Up)", "green")
        add_quadrant_label(x_max*0.9, y_min+(y_max*0.1), "ALERT / FIX\n(Optimize)", "#d32f2f") # Darker red for text
        add_quadrant_label(x_max*0.15, y_max*0.95, "POTENTIAL\n(Experiment)", "#f57c00") # Darker orange for text
        add_quadrant_label(x_max*0.15, y_min+(y_max*0.1), "LOW PRIORITY\n(Monitor)", "grey")

        st.plotly_chart(fig_quadrant, use_container_width=True)
        
        st.markdown("---")
        
        # --- SIMULATOR TINGKAT LANJUT (ANTAR KLIEN) ---
        st.subheader("🔀 Simulator Tingkat Lanjut: Realokasi Antar Klien")
        st.markdown("Gunakan alat ini untuk memindahkan budget dari **Klien Boros (ROAS Rendah)** ke **Klien Potensial (ROAS Tinggi)**.")
        
        sim_col1, sim_col2, sim_col3 = st.columns(3)
        
        # 1. Pilih Source (Asal Dana)
        with sim_col1:
            # Sort clients by ROAS ascending (Lowest ROAS first - candidates for cut)
            client_roas_sorted = client_matrix.sort_values('roas', ascending=True)
            source_client = st.selectbox("Ambil Budget Dari (Source):", client_roas_sorted['client_name'].unique())
            
            source_data = client_matrix[client_matrix['client_name'] == source_client].iloc[0]
            st.caption(f"ROAS Saat Ini: **{source_data['roas']:.2f}x** | Spend: {format_idr(source_data['amount_spent'])}")
            
        # 2. Pilih Target (Tujuan Dana)
        with sim_col2:
            # Sort clients by ROAS descending (Highest ROAS first - candidates for boost)
            client_roas_desc = client_matrix.sort_values('roas', ascending=False)
            # Exclude selected source
            target_opts = [c for c in client_roas_desc['client_name'].unique() if c != source_client]
            target_client = st.selectbox("Pindahkan Ke (Target):", target_opts)
            
            if target_client:
                target_data = client_matrix[client_matrix['client_name'] == target_client].iloc[0]
                st.caption(f"ROAS Saat Ini: **{target_data['roas']:.2f}x** | Spend: {format_idr(target_data['amount_spent'])}")
            else:
                target_data = None

        # 3. Tentukan Nominal / Persentase
        with sim_col3:
            transfer_pct = st.slider("Persentase Budget Source yg Dipindah:", 0, 100, 20, 5)
            transfer_amount = source_data['amount_spent'] * (transfer_pct / 100)
            st.caption(f"Nominal Dipindah: **{format_idr(transfer_amount)}**")

        # 4. Hitung Dampak (Impact Calculation)
        if target_client:
            # Revenue Lost from Source
            rev_lost = transfer_amount * source_data['roas']
            # Revenue Gained from Target (Assume Linear Growth with Target's ROAS)
            rev_gained = transfer_amount * target_data['roas']
            
            net_revenue_impact = rev_gained - rev_lost
            
            # Global Metrics Update
            new_total_rev = current_total_rev + net_revenue_impact
            # Total Spend stays same (just shifted)
            total_spend_global = filtered_df['amount_spent'].sum()
            
            old_global_roas = current_total_rev / total_spend_global if total_spend_global > 0 else 0
            new_global_roas = new_total_rev / total_spend_global if total_spend_global > 0 else 0
            
            # Display Results
            st.markdown("#### 📊 Proyeksi Dampak Bisnis:")
            res1, res2, res3 = st.columns(3)
            
            res1.metric(
                "Net Revenue Impact", 
                format_idr(net_revenue_impact), 
                delta="Positif" if net_revenue_impact > 0 else "Negatif"
            )
            
            res2.metric(
                "Old ROAS (Global)", 
                f"{old_global_roas:.2f}x"
            )
            
            res3.metric(
                "New ROAS (Global)", 
                f"{new_global_roas:.2f}x",
                delta=f"{(new_global_roas - old_global_roas):.3f} pts"
            )
            
            if net_revenue_impact > 0:
                st.success(f"✅ **Rekomendasi:** Strategi ini MENGUNTUNGKAN. Anda mendapatkan tambahan omzet **{format_idr(net_revenue_impact)}** hanya dengan memindahkan budget.")
            else:
                st.error(f"⚠️ **Peringatan:** Strategi ini MERUGIKAN. Jangan pindahkan budget ke klien dengan ROAS lebih rendah.")
            
            with st.expander("ℹ️  Catatan Teknis: Asumsi & Logika Simulasi", expanded=True):
                st.markdown("Simulasi ini menggunakan model matematika sederhana untuk estimasi cepat. Harap perhatikan 3 asumsi dasar berikut:")
                
                asm_col1, asm_col2, asm_col3 = st.columns(3)
                
                with asm_col1:
                    st.markdown("#### 📈 1. Linear Growth")
                    st.caption("*Elastisitas Sempurna*")
                    st.markdown("""
                    **Konsep:** ROAS dianggap konstan (*Constant Return to Scale*).
                    
                    **Contoh:** Jika budget ditambah **Rp 100 Juta** pada klien dengan ROAS 2x, maka omzet diproyeksikan naik tepat **Rp 200 Juta**.
                    
                    ⚠️ **Realita:** Di lapangan sering terjadi *Diminishing Return* (efisiensi menurun seiring besarnya budget).
                    """)

                with asm_col2:
                    st.markdown("#### 🌊 2. Market Capacity")
                    st.caption("*Ketersediaan Pasar*")
                    st.markdown("""
                    **Konsep:** Pasar belum jenuh (*Headroom Available*).
                    
                    Kita mengasumsikan target audiens masih cukup luas untuk menyerap tambahan iklan ini tanpa menyebabkan biaya iklan (CPC/CPM) melonjak drastis secara tiba-tiba.
                    """)
                    
                with asm_col3:
                    st.markdown("#### 🎨 3. Creative Stability")
                    st.caption("*Kualitas Konten Stabil*")
                    st.markdown("""
                    **Konsep:** Performa materi iklan konsisten.
                    
                    Kita mengasumsikan materi iklan (Gambar/Video) yang ada saat ini masih relevan dan efektif ("Winning Campaign") meskipun frekuensi penayangan ditingkatkan.
                    """)
        

# =====================================================================
# TAB 3: Business Insight & Strategic Recommendation
# =====================================================================
with strategy_tab:
    st.header("Business Insight & Strategic Recommendation")

    st.markdown("""
    Berdasarkan analisis data menyeluruh (Trend, Segmentation, & Simulation), berikut adalah 3 Strategi Utama untuk meningkatkan profitabilitas perusahaan:

    ### **Strategi 1: Smart Budget Reallocation (Cut Traffic, Scale Sales)**
    * **Masalah:** Ditemukan bahwa **Rp 18.3 Miliar** (52% dari total budget) dihabiskan untuk campaign *Traffic* yang memiliki atribusi purchase nol. Sementara itu, campaign *Sales* terbukti sangat efisien dengan ROAS **1.62x**.
    * **Rekomendasi (Based on Simulation):**
        * Segera pindahkan **30-50% budget Traffic** ke campaign Sales.
        * Berdasarkan simulasi, memindahkan 50% budget (Rp 9 M) berpotensi menghasilkan **tambahan omzet sebesar Rp 14.8 Miliar**, atau kenaikan revenue total sebesar **+51%**.
    * **Aksi Taktis:** Ubah objektif iklan dari "Link Clicks" menjadi "Conversions/Purchase" pada akun-akun yang sudah matang (FMCG & Fashion).

    ### **Strategi 2: Seasonal Sniper (Fokus Q4 & "THR Moment")**
    * **Masalah:** Data tren menunjukkan performa belanja harian *flat* di awal tahun, namun meledak hingga 10x lipat di **Oktober-November** (Q4). Selain itu, Ramadhan memiliki rata-rata harian yang rendah, kecuali lonjakan spesifik di bulan April.
    * **Rekomendasi:**
        * Terapkan **"Budget Saving Mode"** di Q1-Q3 (Januari-September). Hemat budget, fokus hanya pada *maintenance*.
        * Lakukan **"All-in Aggressive Spending"** mulai Oktober (untuk event 10.10, 11.11, 12.12).
        * Untuk Ramadhan: Jangan *spending* besar di awal puasa. Fokuskan budget besar hanya pada **H-10 Lebaran** (saat THR cair), karena data bulan April menunjukkan kenaikan signifikan.

    ### **Strategi 3: Cross-Pollination Strategy (Copy the Winner)**
    * **Masalah:** Terjadi ketimpangan performa antar klien. **Client C (Fashion)** dan **Client E (FMCG)** adalah "Star" dengan ROAS tinggi, sementara **Client B & D (Beauty)** berada di zona "Alert" (Biaya tinggi, ROAS rendah).
    * **Rekomendasi:**
        * **Untuk Traffic Objective (Awareness):** Audit kualitas trafik Client Beauty. Cek apakah landing page-nya relevan. Jika *Bounce Rate* tinggi, perbaiki konten website.
        * **Untuk Sales Objective (Conversion):** Lakukan A/B Testing pada Client Beauty dengan meniru gaya materi kreatif (Creative Benchmarking) dari Client C.
        * Gunakan audiens yang berhasil di FMCG (Lookalike Audience) untuk ditargetkan silang ke produk Beauty jika demografinya mirip.
    """)

# Sidebar Footer
st.sidebar.markdown("---")
st.sidebar.caption("© 2026 Skena Data Team")

# --- DOWNLOAD REPORT (EXCEL) ---
def generate_excel(df_source):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    # 1. SHEET: Executive Summary
    summary_data = {
        'Metric': ['Total Spend', 'Total Revenue', 'Avg ROAS', 'Avg CPC', 'Avg CTR'],
        'Value': [
            df_source['amount_spent'].sum(),
            df_source['purchase_value'].sum(),
            df_source['roas'].mean(),
            df_source['cpc'].mean(),
            df_source['ctr_percentage'].mean() / 100 # Adjust for percentage format
        ]
    }
    pd.DataFrame(summary_data).to_excel(writer, sheet_name='Executive Summary', index=False)
    
    # 2. SHEET: Daily Trend
    daily_data = df_source.groupby('created_date')[['amount_spent', 'purchase_value']].sum().reset_index()
    daily_data.to_excel(writer, sheet_name='Daily Trend', index=False)
    
    # 3. SHEET: Client Performance
    client_data = df_source.groupby('client_name')[['amount_spent', 'purchase_value', 'roas']].mean().reset_index() # using mean for roas simplification
    # Better aggregation for client: Sum Spend/Rev, Recalculate ROAS
    client_agg = df_source.groupby('client_name')[['amount_spent', 'purchase_value']].sum().reset_index()
    client_agg['roas'] = client_agg['purchase_value'] / client_agg['amount_spent']
    client_agg.to_excel(writer, sheet_name='Client Performance', index=False)
    
    # 4. SHEET: Raw Data
    df_source.to_excel(writer, sheet_name='Raw Data', index=False)
    
    # --- FORMATTING (XlsxWriter) ---
    workbook = writer.book
    currency_fmt = workbook.add_format({'num_format': 'Rp #,##0'})
    percent_fmt = workbook.add_format({'num_format': '0.00%'}) 
    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9', 'border': 1})
    
    # Apply formats to Sheets
    worksheet_summary = writer.sheets['Executive Summary']
    worksheet_summary.set_column('B:B', 20, currency_fmt) # Value Column
    # Manually fix ROAS/CTR formats in summary (mixed types in one column is tricky, leaving as general/currency for now)
    
    worksheet_trend = writer.sheets['Daily Trend']
    worksheet_trend.set_column('A:A', 15) # Date
    worksheet_trend.set_column('B:C', 20, currency_fmt) # Money
    
    worksheet_client = writer.sheets['Client Performance']
    worksheet_client.set_column('A:A', 25) # Client Name
    worksheet_client.set_column('B:C', 20, currency_fmt) # Spend/Rev
    worksheet_client.set_column('D:D', 10, workbook.add_format({'num_format': '0.00'})) # ROAS
    
    writer.close()
    return output.getvalue()

excel_file = generate_excel(filtered_df)

st.sidebar.download_button(
    label="📥 Download Report (Excel)",
    data=excel_file,
    file_name="Marketing_Performance_Report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
st.sidebar.download_button(
    label="📄 Download Raw Data (CSV)",
    data=filtered_df.to_csv(index=False).encode('utf-8'),
    file_name="marketing_data_raw.csv",
    mime="text/csv"
)