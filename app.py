import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta

# 1. إعدادات الصفحة الفائقة للكمبيوتر
st.set_page_config(page_title="المحلل الفني الاحترافي V4", layout="wide")

# تنسيق CSS احترافي لمنع التداخل وتجميل المظهر
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; }
    .main-header {
        background: linear-gradient(90deg, #1e2130, #0e1117);
        padding: 30px;
        border-radius: 20px;
        border: 2px solid #00FFCC;
        text-align: center;
        margin-bottom: 40px;
    }
    .symbol-label { font-size: 75px !important; color: #00FFCC; font-weight: bold; margin: 0; }
    .gauge-card { background: #161a25; padding: 20px; border-radius: 20px; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# 2. نظام البحث الذكي
query = st.text_input("🔍 أدخل الرمز (مثال: 1120 أو 8180 أو AAPL):", value="1120").strip()

if query:
    if query.isdigit(): 
        symbol = query + ".SR"
    else: 
        symbol = query.upper()

    try:
        # جلب البيانات (فريم ساعة لضمان دقة المؤشرات لآخر أسبوعين)
        data = yf.download(symbol, period="1mo", interval="1h")
        
        if data.empty:
            st.error("❌ لم يتم العثور على بيانات لهذا الرمز. تأكد من الرقم.")
        else:
            # تنظيف البيانات من الـ Multi-index لتجنب الـ TypeError
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            
            df = data.copy()

            # حساب المؤشرات الفنية (جميعها مفعلة)
            df['SMA50'] = ta.sma(df['Close'], length=50)
            df['SMA200'] = ta.sma(df['Close'], length=200)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            macd_data = ta.macd(df['Close'])
            df = pd.concat([df, macd_data], axis=1)

            # استخراج القيم الأخيرة للتحليل
            last_p = float(df['Close'].iloc[-1])
            rsi_val = float(df['RSI'].iloc[-1])
            macd_val = float(df.iloc[-1, -3]) # MACD Line
            sig_val = float(df.iloc[-1, -2])  # Signal Line
            res_p = float(df['High'].max())
            sup_p = float(df['Low'].min())

            # حساب نتيجة الإيجابية (عداد 100%)
            score = 0
            if last_p > df['SMA50'].iloc[-1]: score += 25
            if rsi_val > 50: score += 25
            if macd_val > sig_val: score += 25
            if last_p > df['SMA200'].iloc[-1]: score += 25

            # --- العرض المرئي ---
            st.markdown(f'<div class="main-header"><p class="symbol-label">{symbol}</p></div>', unsafe_allow_html=True)

            col_gauge, col_info = st.columns([1, 2])

            with col_gauge:
                st.markdown('<div class="gauge-card">', unsafe_allow_html=True)
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number", value=score,
                    gauge={'axis': {'range': [0, 100]},
                           'steps': [
                               {'range': [0, 30], 'color': "red"},
                               {'range': [30, 70], 'color': "yellow"},
                               {'range': [70, 100], 'color': "green"}],
                           'bar': {'color': "white"}},
                    title={'text': "مقياس الإيجابية الفني", 'font': {'size': 24, 'color': 'white'}}
                ))
                fig_gauge.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
                st.plotly_chart(fig_gauge, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with col_info:
                st.write("### 📜 بطاقة تقرير السهم")
                c1, c2, c3 = st.columns(3)
                c1.metric("السعر الحالي", f"{last_p:.2f}")
                c2.metric("مؤشر RSI", f"{rsi_val:.1f}")
                c3.metric("الهدف (⭐)", f"{last_p * 1.05:.2f}")
                
                st.success(f"📌 **تحليل المسار:** السهم في منطقة {'إيجابية قوية' if score >= 75 else 'تجميع/انتظار'}")
                st.info(f"🚩 **المقاومة القادمة:** {res_p:.2f} | 🛡️ **الدعم الفني:** {sup_p:.2f}")

            # --- التشارت العملاق (التفاصيل الكاملة) ---
            st.write("---")
            st.write("### 📊 التشارت الفني (فريم 4 ساعات)")
            
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])

            # 1. السعر والمتوسطات
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                          low=df['Low'], close=df['Close'], name="الشموع"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='orange', width=2), name="SMA 50"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], line=dict(color='red', width=2), name="SMA 200"), row=1, col=1)
            
            # خطوط المقاومة والدعم
            fig.add_hline(y=res_p, line_dash="dash", line_color="#FF3131", row=1, col=1)
            fig.add_hline(y=sup_p, line_dash="dash", line_color="#39FF14", row=1, col=1)

            # 2. RSI
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#9b59b6'), name="RSI"), row=2, col=1)
            fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)

            # 3. MACD
            fig.add_trace(go.Bar(x=df.index, y=df.iloc[:, -1], name="الزخم", marker_color='white'), row=3, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df.iloc[:, -3], line=dict(color='#00FFCC'), name="MACD"), row=3, col=1)

            fig.update_layout(height=1000, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ تنبيه: يرجى التحقق من الرمز المدخل. (Error: {str(e)})")
