import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fpdf import FPDF
from datetime import timedelta

# 1. إعدادات الصفحة العامة (التنسيق الاحترافي)
st.set_page_config(page_title="منصة المحلل الذكي", layout="wide")

# إخفاء قائمة Streamlit وتنسيق العنوان
st.markdown("""
    <style>
    .main-title {
        font-size: 70px !important;
        font-weight: bold;
        color: #00FFCC;
        text-align: center;
        margin-top: -50px;
        text-shadow: 2px 2px 10px #000;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. خانة البحث في الأعلى
query = st.text_input("🔍 أدخل رمز السهم أو الرقم (مثال: 1120 أو AAPL):", value="1120").strip()

# تحويل الرمز ذكياً
if query.lower() == 'gold': symbol = "GC=F"
elif query.isdigit(): symbol = query + ".SR"
else: symbol = query.upper()

if symbol:
    try:
        df = yf.download(symbol, period="1y", interval="1d")
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            # --- أ: إظهار اسم السهم أول شيء فوق ---
            st.markdown(f'<p class="main-title">{symbol}</p>', unsafe_allow_html=True)

            # حساب المؤشرات
            df['RSI'] = ta.rsi(df['Close'], length=14)
            last_price = float(df['Close'].iloc[-1])
            
            # حساب التوقع (هدف اليومين القادمين)
            change = df['Close'].diff().tail(5).mean()
            expected_price = last_price + (change * 2)
            target_date = df.index[-1] + timedelta(days=2)

            # --- ب: تنسيق المعلومات السريعة (Metrics) ---
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("السعر الحالي", f"{last_price:.2f}")
            m2.metric("مؤشر RSI", f"{df['RSI'].iloc[-1]:.2f}")
            m3.metric("الهدف المتوقع", f"{expected_price:.2f}")
            m4.metric("التاريخ المستهدف", target_date.strftime('%Y-%m-%d'))

            st.write("---")

            # --- ج: التشارت الرئيسي (الشموع والمؤشرات) ---
            st.subheader("📊 التحليل الفني والشموع اليابانية")
            fig1 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
            
            # الشموع
            fig1.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="السعر"), row=1, col=1)
            # RSI
            fig1.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='purple')), row=2, col=1)
            fig1.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig1.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
            
            fig1.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(t=0, b=0))
            st.plotly_chart(fig1, use_container_width=True)

            st.write("---")

            # --- د: تشارت التوقعات المنفصل (خاص بالهدف القادم) ---
            st.subheader("🔮 خوارزمية التوقع (اليومين القادمين)")
            
            # تجهيز بيانات التشارت التوقعي (آخر 10 أيام + يومين مستقبليين)
            recent_df = df.tail(10)
            fig2 = go.Figure()
            
            # رسم المسار الأخير
            fig2.add_trace(go.Scatter(x=recent_df.index, y=recent_df['Close'], mode='lines+markers', name="المسار الأخير", line=dict(color='white', dash='dot')))
            
            # رسم الهدف المتوقع (النجمة)
            fig2.add_trace(go.Scatter(x=[target_date], y=[expected_price], mode='markers+text',
                                     text=[f"الهدف المتوقع ({expected_price:.2f})"], textposition="top center",
                                     marker=dict(color='#00FFCC', size=20, symbol='star', line=dict(width=2, color="white")),
                                     name="الهدف الذكي"))

            fig2.update_layout(height=400, template="plotly_dark", 
                              xaxis_title="التاريخ المستهدف", 
                              yaxis_title="السعر المتوقع",
                              xaxis=dict(showgrid=False), yaxis=dict(showgrid=True))
            
            st.plotly_chart(fig2, use_container_width=True)

            # --- هـ: زر تحميل PDF المطور ---
            def generate_pdf():
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(190, 10, f"TECHNICAL REPORT: {symbol}", ln=True, align='C')
                pdf.ln(10)
                pdf.set_font("Arial", '', 12)
                pdf.cell(100, 10, f"Analysis Date: {df.index[-1].strftime('%Y-%m-%d')}")
                pdf.cell(100, 10, f"Last Price: {last_price:.2f}", ln=True)
                pdf.cell(100, 10, f"Target Price: {expected_price:.2f}")
                pdf.cell(100, 10, f"Target Date: {target_date.strftime('%Y-%m-%d')}", ln=True)
                pdf.ln(10)
                pdf.multi_cell(0, 10, f"Summary: Based on momentum, the expected direction for {symbol} in the next 48h is toward {expected_price:.2f}.")
                return pdf.output(dest='S').encode('latin-1')

            st.download_button("📥 تصدير التقرير الفني الشامل (PDF)", data=generate_pdf(), file_name=f"{symbol}_Report.pdf")

    except Exception as e:
        st.error(f"خطأ في البيانات: {e}")
