import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta

# 1. إعدادات الصفحة للعرض المكتبي الواسع
st.set_page_config(page_title="محلل الأسهم الاحترافي", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; }
    .report-title { background: #00FFCC; color: black; padding: 10px; border-radius: 10px; text-align: center; font-size: 30px; font-weight: bold; }
    .status-box { background: #1e2130; padding: 20px; border-radius: 15px; border: 1px solid #444; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# 2. البحث
query = st.text_input("🔍 أدخل رمز السهم (مثال: 1120 أو 8180):", value="8180").strip()

if query:
    if query.isdigit(): symbol = query + ".SR"
    else: symbol = query.upper()

    try:
        # جلب البيانات (يومي وأسبوعي)
        df_daily = yf.download(symbol, period="1y", interval="1d")
        
        if not df_daily.empty:
            if isinstance(df_daily.columns, pd.MultiIndex): df_daily.columns = df_daily.columns.get_level_values(0)
            
            # حساب المؤشرات
            df_daily['SMA50'] = ta.sma(df_daily['Close'], length=50)
            df_daily['SMA200'] = ta.sma(df_daily['Close'], length=200)
            df_daily['RSI'] = ta.rsi(df_daily['Close'], length=14)
            macd = ta.macd(df_daily['Close'])
            
            last_close = float(df_daily['Close'].iloc[-1])
            rsi_val = float(df_daily['RSI'].iloc[-1])
            
            # حساب الإيجابية (خوارزمية العداد)
            score = 0
            if last_close > df_daily['SMA50'].iloc[-1]: score += 25
            if rsi_val > 50: score += 25
            if macd.iloc[-1, 0] > macd.iloc[-1, 1]: score += 25
            if last_close > df_daily['SMA200'].iloc[-1]: score += 25

            # --- أ: رأس التقرير ---
            st.markdown(f'<div class="report-title">تقرير تحليل سهم: {symbol}</div>', unsafe_allow_html=True)
            st.write(f"### تاريخ التحليل: {df_daily.index[-1].strftime('%Y-%m-%d')}")

            # --- ب: عداد الإيجابية (كما في صورك) ---
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown('<div class="status-box">', unsafe_allow_html=True)
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = score,
                    title = {'text': "إيجابية السهم"},
                    gauge = {
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "black"},
                        'steps': [
                            {'range': [0, 20], 'color': "red"},
                            {'range': [20, 40], 'color': "orange"},
                            {'range': [40, 60], 'color': "yellow"},
                            {'range': [60, 80], 'color': "lightgreen"},
                            {'range': [80, 100], 'color': "green"}],
                        'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': score}
                    }
                ))
                fig_gauge.update_layout(height=300, margin=dict(t=0, b=0, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
                st.plotly_chart(fig_gauge, use_container_width=True)
                
                status_text = "شراء قوي" if score >= 75 else "إيجابي" if score >= 50 else "متعادل" if score >= 30 else "سلبي"
                st.markdown(f"## الحالة: {status_text}")
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                # ملخص فني سريع
                st.write("### 📋 ملخص المؤشرات الفنية")
                c_a, c_b = st.columns(2)
                c_a.metric("السعر الحالي", f"{last_p:.2f}")
                c_b.metric("مؤشر RSI", f"{rsi_val:.2f}")
                
                st.info(f"""
                * **الدعم القريب:** {df_daily['Low'].tail(10).min():.2f}
                * **المقاومة القريبة:** {df_daily['High'].tail(10).max():.2f}
                * **المسار:** {"صاعد" if last_close > df_daily['SMA50'].iloc[-1] else "هابط / عرضي"}
                """)

            # --- ج: التشارت الفني الكبير (يومي) ---
            st.write("### 📊 الرسم البياني اليومي (مؤشرات الحركة)")
            fig_main = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
            
            # الشموع والمتوسطات
            fig_main.add_trace(go.Candlestick(x=df_daily.index, open=df_daily['Open'], high=df_daily['High'], low=df_daily['Low'], close=df_daily['Close'], name="السعر"), row=1, col=1)
            fig_main.add_trace(go.Scatter(x=df_daily.index, y=df_daily['SMA50'], line=dict(color='orange'), name="متوسط 50"), row=1, col=1)
            fig_main.add_trace(go.Scatter(x=df_daily.index, y=df_daily['SMA200'], line=dict(color='red'), name="متوسط 200"), row=1, col=1)
            
            # الماكد
            fig_main.add_trace(go.Bar(x=df_daily.index, y=macd.iloc[:, -1], name="MACD Hist"), row=2, col=1)
            
            fig_main.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig_main, use_container_width=True)

            # --- د: الأهداف المستهدفة (النجمة) ---
            target_p = last_close * 1.05 # هدف افتراضي 5%
            st.success(f"⭐ الهدف المتوقع القادم: {target_p:.2f}")

    except Exception as e:
        st.error(f"لم يتم العثور على بيانات للسهم. تأكد من الرقم. الخطأ: {e}")
