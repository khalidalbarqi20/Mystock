import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta

# 1. إعدادات الصفحة
st.set_page_config(page_title="المحلل الفني المتكامل V5", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; }
    .main-header { background: #0e1117; padding: 20px; border-radius: 15px; border: 2px solid #00FFCC; text-align: center; margin-bottom: 25px; }
    .symbol-label { font-size: clamp(30px, 5vw, 60px); color: #00FFCC; font-weight: bold; margin: 0; }
    .gauge-card { background: #161a25; padding: 15px; border-radius: 15px; border: 1px solid #333; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# 2. البحث
query = st.text_input("🔍 أدخل الرمز (مثال: 1120 أو 8180):", value="8180").strip()

if query:
    symbol = query + ".SR" if query.isdigit() else query.upper()

    try:
        # جلب البيانات (يومي لآخر سنة)
        data = yf.download(symbol, period="1y", interval="1d")
        
        if data.empty:
            st.error("❌ لا توجد بيانات لهذا الرمز.")
        else:
            if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
            df = data.copy()

            # حساب المؤشرات مع معالجة القيم الفارغة
            df['SMA50'] = ta.sma(df['Close'], length=50)
            df['SMA200'] = ta.sma(df['Close'], length=200)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            macd = ta.macd(df['Close'])
            
            # التأكد من وجود قيم MACD
            macd_line = macd.iloc[:, 0] if macd is not None else pd.Series([0]*len(df))
            sig_line = macd.iloc[:, 1] if macd is not None else pd.Series([0]*len(df))

            # قيم العرض
            last_p = float(df['Close'].iloc[-1])
            rsi_val = float(df['RSI'].iloc[-1]) if not pd.isna(df['RSI'].iloc[-1]) else 50
            
            # --- حساب الإيجابية (تجنب خطأ NoneType) ---
            score = 0
            try:
                if last_p > (df['SMA50'].iloc[-1] or 0): score += 25
                if rsi_val > 50: score += 25
                if macd_line.iloc[-1] > sig_line.iloc[-1]: score += 25
                if not pd.isna(df['SMA200'].iloc[-1]) and last_p > df['SMA200'].iloc[-1]: score += 25
                elif pd.isna(df['SMA200'].iloc[-1]): score += 15 # تعويض في حال عدم توفر بيانات كافية
            except: pass

            # --- العرض العلوي ---
            st.markdown(f'<div class="main-header"><p class="symbol-label">تحليل سهم: {symbol}</p></div>', unsafe_allow_html=True)

            col_g, col_t = st.columns([1, 2])
            
            with col_g:
                st.markdown('<div class="gauge-card">', unsafe_allow_html=True)
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number", value=score,
                    gauge={'axis': {'range': [0, 100]},
                           'steps': [{'range': [0, 30], 'color': "red"}, {'range': [30, 70], 'color': "yellow"}, {'range': [70, 100], 'color': "green"}],
                           'bar': {'color': "white"}},
                    title={'text': "إيجابية السهم", 'font': {'size': 22, 'color': 'white'}}
                ))
                fig_g.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, margin=dict(t=50, b=0))
                st.plotly_chart(fig_g, use_container_width=True)
                
                status = "شراء قوي" if score >= 75 else "إيجابي" if score >= 50 else "سلبي"
                st.markdown(f"### الحالة: {status}")
                st.markdown('</div>', unsafe_allow_html=True)

            with col_t:
                st.write("### 📜 ملخص التقرير")
                st.info(f"📍 السعر الحالي: {last_p:.2f} | 🎯 الهدف: {last_p * 1.05:.2f}")
                st.success(f"📈 دعم 1: {df['Low'].tail(5).min():.2f} | 📉 مقاومة 1: {df['High'].tail(5).max():.2f}")
                st.write("---")
                st.write("سهم في مسار " + ("صاعد" if score > 50 else "هابط/عرضي"))

            # --- التشارت الرئيسي (مثل الصور المرفقة) ---
            st.write("### 📊 التشارت الفني + الفوليوم + MACD")
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.6, 0.2, 0.2])

            # 1. السعر والشموع
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="السعر"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='orange', width=1), name="SMA 50"), row=1, col=1)
            
            # 2. الفوليوم (أعمدة البيع والشراء)
            colors = ['green' if df['Close'].iloc[i] > df['Open'].iloc[i] else 'red' for i in range(len(df))]
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name="الفوليوم"), row=2, col=1)

            # 3. MACD
            if macd is not None:
                fig.add_trace(go.Bar(x=df.index, y=macd.iloc[:, -1], name="MACD Hist", marker_color='white'), row=3, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=macd_line, line=dict(color='#00FFCC'), name="MACD Line"), row=3, col=1)

            fig.update_layout(height=800, template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ تنبيه: تعذر جلب كافة المؤشرات لهذا السهم. (السبب: {str(e)})")
