import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import os
import sys

# Menambahkan root directory ke sys.path agar bisa import dari src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.broker.mt5_manager import MT5Manager
from src.brain.hmm_model import MarketRegimeDetector

# Konfigurasi Halaman Streamlit (Harus dipanggil pertama kali)
st.set_page_config(
    page_title="XAUUSD Bot Dashboard", 
    page_icon="📈", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CACHING SYSTEM ---
# Kita menggunakan cache agar koneksi MT5 dan training HMM tidak diulang 
# setiap kali halaman Streamlit di-refresh.
@st.cache_resource
def init_system():
    broker = MT5Manager()
    connected = broker.connect()
    
    brain = MarketRegimeDetector(n_components=4)
    if connected:
        df_train = broker.get_historical_data(symbol="XAUUSD", num_bars=1000)
        if df_train is not None:
            brain.train(df_train)
            
    return broker, brain, connected

def run_dashboard():
    # --- UI STYLING (DARK MODE) ---
    st.markdown("""
        <style>
        .metric-card {
            background-color: #1E1E1E;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            text-align: center;
        }
        .regime-Bullish { color: #00FF00; font-weight: bold; }
        .regime-Bearish { color: #FF0000; font-weight: bold; }
        .regime-Volatile { color: #FFA500; font-weight: bold; }
        .regime-Neutral { color: #808080; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    st.title("📈 XAUUSD Trading Bot Dashboard")
    
    # Inisialisasi sistem
    broker, brain, connected = init_system()
    
    if not connected:
        st.error("❌ Gagal terhubung ke MetaTrader 5. Pastikan MT5 berjalan dan kredensial di .env benar.")
        return

    # Sidebar Controls
    st.sidebar.header("⚙️ Control Panel")
    auto_refresh = st.sidebar.checkbox("Auto-Refresh (10 detik)", value=False)
    st.sidebar.markdown("---")
    st.sidebar.info("Dashboard ini membaca data secara real-time dari MT5 dan model HMM.")

    # --- FETCH DATA ---
    acc_info = broker.get_account_info()
    df_latest = broker.get_historical_data(symbol="XAUUSD", num_bars=100)
    
    if acc_info is None or df_latest is None:
        st.warning("Menunggu data dari broker...")
        return

    # Prediksi Regime
    regime = brain.predict_regime(df_latest)
    
    # Menentukan class CSS untuk warna regime
    regime_class = "regime-Neutral"
    if regime == "Bullish": regime_class = "regime-Bullish"
    elif regime == "Bearish": regime_class = "regime-Bearish"
    elif "Volatile" in regime: regime_class = "regime-Volatile"

    # --- SECTION 1: METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <h3>Balance</h3>
                <h2>${acc_info['balance']:,.2f}</h2>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
            <div class="metric-card">
                <h3>Equity</h3>
                <h2>${acc_info['equity']:,.2f}</h2>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
            <div class="metric-card">
                <h3>Margin Free</h3>
                <h2>${acc_info['margin_free']:,.2f}</h2>
            </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown(f"""
            <div class="metric-card">
                <h3>Market Regime</h3>
                <h2 class="{regime_class}">{regime}</h2>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # --- SECTION 2: LIVE CHART ---
    st.subheader("📊 XAUUSD Live Chart (M15)")
    
    # Membuat Candlestick Chart menggunakan Plotly
    fig = go.Figure(data=[go.Candlestick(
        x=df_latest.index,
        open=df_latest['open'],
        high=df_latest['high'],
        low=df_latest['low'],
        close=df_latest['close'],
        increasing_line_color='#00FF00', decreasing_line_color='#FF0000'
    )])
    
    # Styling Chart untuk Dark Mode
    fig.update_layout(
        template='plotly_dark',
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis_rangeslider_visible=False,
        height=500,
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117'
    )
    
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # --- SECTION 3: TRADE HISTORY (PLACEHOLDER) ---
    st.subheader("📝 Recent Trade History")
    
    # Placeholder data (Nantinya bisa ditarik dari database lokal atau MT5 history)
    dummy_trades = pd.DataFrame({
        "Time": [pd.Timestamp.now() - pd.Timedelta(minutes=i*15) for i in range(5)],
        "Type": ["BUY", "SELL", "BUY", "BUY", "SELL"],
        "Lot": [0.02, 0.02, 0.01, 0.02, 0.01],
        "Entry Price": [2000.50, 2005.10, 1998.20, 1995.00, 2010.00],
        "Status": ["CLOSED", "CLOSED", "CLOSED", "CLOSED", "CLOSED"],
        "Profit/Loss": ["+$15.00", "-$5.00", "+$8.00", "-$10.00", "+$20.00"]
    })
    
    # Styling dataframe
    st.dataframe(
        dummy_trades, 
        use_container_width=True,
        hide_index=True
    )

    # --- AUTO REFRESH LOGIC ---
    if auto_refresh:
        time.sleep(10)
        st.rerun()

if __name__ == "__main__":
    run_dashboard()
