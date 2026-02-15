import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import dates as mdates
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator, MACD

st.set_page_config(page_title="Stock Analysis Page", layout="wide")

st.title("📊 Stock Analysis & Visual Dashboard")
st.markdown("تحليل الأسهم مع RSI, MACD, SMA وأيضًا فلترة الأسهم الأقل من RSI 30")

# ---------- إعداد الأسواق ----------
markets = {
    "SA": ["STC.SR","TADAWUL2.SR"],  # ضع هنا قائمة الأسهم السعودية
    "US": ["AAPL","MSFT","TSLA"]      # ضع هنا قائمة الأسهم الأمريكية
}

market_choice = st.radio("اختر السوق", ["SA", "US", "ALL"])

# ---------- وظيفة التحليل ----------
def analyze_stock(ticker):
    try:
        data = yf.Ticker(ticker).history(period="6mo")
        # SMA
        sma7 = SMAIndicator(data['Close'], 7).sma_indicator()
        sma20 = SMAIndicator(data['Close'], 20).sma_indicator()
        sma50 = SMAIndicator(data['Close'], 50).sma_indicator()
        sma200 = SMAIndicator(data['Close'], 200).sma_indicator()
        # MACD
        macd = MACD(data['Close']).macd()
        macd_signal = MACD(data['Close']).macd_signal()
        # RSI
        rsi = RSIIndicator(data['Close']).rsi()
        # Trend Score
        score = 0
        score += 20 if data['Close'][-1] > sma20[-1] else 0
        score += 20 if data['Close'][-1] > sma50[-1] else 0
        score += 20 if data['Close'][-1] > sma200[-1] else 0
        score += 15 if macd[-1] > 0 else 0
        score += 15 if rsi[-1] > 50 else 0
        score += 10 if data['Close'][-1] > max(data['Close'][-20:]) else 0
        # Trend label
        if score >= 80:
            trend = "BUY_STRONG"
        elif score >= 60:
            trend = "BUY"
        elif score >= 40:
            trend = "NEUTRAL"
        elif score >= 20:
            trend = "SELL"
        else:
            trend = "SELL_STRONG"
        return {
            "ticker": ticker,
            "data": data,
            "sma7": sma7,
            "sma20": sma20,
            "sma50": sma50,
            "sma200": sma200,
            "macd": macd,
            "macd_signal": macd_signal,
            "rsi": rsi,
            "score": score,
            "trend": trend
        }
    except:
        return None

# ---------- اختيار سهم للتحليل الفردي ----------
if market_choice != "ALL":
    ticker = st.selectbox("اختر سهم", markets[market_choice])
    st.header(f"تحليل {ticker} في السوق {market_choice}")
    result = analyze_stock(ticker)
    if result:
        # --- معلومات عامة ---
        st.write(f"**Trend Label:** {result['trend']}")
        st.write(f"**Trend Score:** {result['score']}/100")
        st.write(f"**RSI آخر يوم:** {result['rsi'][-1]:.2f}")
        st.write(f"**MACD آخر يوم:** {result['macd'][-1]:.2f} ({'Positive' if result['macd'][-1]>0 else 'Negative'})")
        # --- رسم Candlestick مع SMA ---
        fig, ax = plt.subplots(figsize=(10,5))
        ax.plot(result['data'].index, result['data']['Close'], label='Close', color='black')
        ax.plot(result['sma7'], label='SMA7', color='blue')
        ax.plot(result['sma20'], label='SMA20', color='orange')
        ax.plot(result['sma50'], label='SMA50', color='green')
        ax.plot(result['sma200'], label='SMA200', color='red')
        ax.set_title(f"{ticker} - Price & SMA")
        ax.legend()
        st.pyplot(fig)
        # --- رسم RSI ---
        fig2, ax2 = plt.subplots(figsize=(10,3))
        ax2.plot(result['rsi'], label='RSI', color='purple')
        ax2.axhline(30, color='red', linestyle='--')
        ax2.axhline(70, color='green', linestyle='--')
        ax2.set_title("RSI")
        st.pyplot(fig2)
        # --- رسم MACD ---
        fig3, ax3 = plt.subplots(figsize=(10,3))
        ax3.plot(result['macd'], label='MACD', color='blue')
        ax3.plot(result['macd_signal'], label='Signal', color='red')
        ax3.set_title("MACD")
        ax3.legend()
        st.pyplot(fig3)
    else:
        st.error("خطأ في جلب بيانات السهم!")

# ---------- فلترة الأسهم الأقل من RSI 30 ----------
if market_choice == "ALL" or st.checkbox("عرض الأسهم الأقل من RSI 30"):
    st.header("📉 أسهم RSI < 30")
    for mkt in ["SA","US"]:
        st.subheader(f"🇸🇦 {'SAUDI' if mkt=='SA' else 'USA'}")
        oversold_list = []
        for t in markets[mkt]:
            res = analyze_stock(t)
            if res and res['rsi'][-1] < 30:
                oversold_list.append([res['ticker'], res['data']['Close'][-1], round(res['rsi'][-1],2), 'Positive' if res['macd'][-1]>0 else 'Negative'])
        if oversold_list:
            df = pd.DataFrame(oversold_list, columns=["Ticker","Price","RSI","MACD_state"])
            st.table(df)
        else:
            st.write("لا يوجد أسهم أقل من RSI 30 في هذا السوق حالياً")
