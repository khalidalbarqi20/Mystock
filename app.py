import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator, MACD

st.set_page_config(page_title="Stock Analysis Page", layout="wide")
st.title("📊 Stock Analysis & Dashboard")
st.markdown("أدخل رمز السهم لتحليل RSI, MACD, SMA ورسم الشارتات")

# ---------- خانة بحث السهم ----------
ticker_input = st.text_input("أدخل رمز السهم (مثال: AAPL أو STC.SR)")

if ticker_input:
    try:
        data = yf.Ticker(ticker_input).history(period="6mo")
        
        # ---------- مؤشرات ----------
        sma7 = SMAIndicator(data['Close'], 7).sma_indicator()
        sma20 = SMAIndicator(data['Close'], 20).sma_indicator()
        sma50 = SMAIndicator(data['Close'], 50).sma_indicator()
        sma200 = SMAIndicator(data['Close'], 200).sma_indicator()
        macd = MACD(data['Close']).macd()
        macd_signal = MACD(data['Close']).macd_signal()
        rsi = RSIIndicator(data['Close']).rsi()
        
        # ---------- Trend Score ----------
        score = 0
        score += 20 if data['Close'][-1] > sma20[-1] else 0
        score += 20 if data['Close'][-1] > sma50[-1] else 0
        score += 20 if data['Close'][-1] > sma200[-1] else 0
        score += 15 if macd[-1] > 0 else 0
        score += 15 if rsi[-1] > 50 else 0
        score += 10 if data['Close'][-1] > max(data['Close'][-20:]) else 0

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

        # ---------- عرض المعلومات ----------
        st.write(f"**Ticker:** {ticker_input}")
        st.write(f"**Trend Label:** {trend}")
        st.write(f"**Trend Score:** {score}/100")
        st.write(f"**RSI آخر يوم:** {rsi[-1]:.2f}")
        st.write(f"**MACD آخر يوم:** {macd[-1]:.2f} ({'Positive' if macd[-1]>0 else 'Negative'})")

        # ---------- رسم الشارتات ----------
        fig, ax = plt.subplots(figsize=(10,5))
        ax.plot(data.index, data['Close'], label='Close', color='black')
        ax.plot(sma7, label='SMA7', color='blue')
        ax.plot(sma20, label='SMA20', color='orange')
        ax.plot(sma50, label='SMA50', color='green')
        ax.plot(sma200, label='SMA200', color='red')
        ax.set_title(f"{ticker_input} - Price & SMA")
        ax.legend()
        st.pyplot(fig)

        fig2, ax2 = plt.subplots(figsize=(10,3))
        ax2.plot(rsi, label='RSI', color='purple')
        ax2.axhline(30, color='red', linestyle='--')
        ax2.axhline(70, color='green', linestyle='--')
        ax2.set_title("RSI")
        st.pyplot(fig2)

        fig3, ax3 = plt.subplots(figsize=(10,3))
        ax3.plot(macd, label='MACD', color='blue')
        ax3.plot(macd_signal, label='Signal', color='red')
        ax3.set_title("MACD")
        ax3.legend()
        st.pyplot(fig3)

    except Exception as e:
        st.error(f"خطأ في جلب بيانات السهم أو الرمز غير صحيح: {e}")
