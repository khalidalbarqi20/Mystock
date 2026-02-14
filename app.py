import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fpdf import FPDF
from datetime import timedelta

# 1. إعدادات التنسيق الاحترافي
st.set_page_config(page_title="محلل الـ 4 ساعات الذكي", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 60px !important; font-weight: bold; color: #00FFCC; text-align: center; margin-top: -40px; }
    .stMetric { background-color: #1e2130; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. البحث
query = st.text_input("🔍 أدخل الرمز أو الرقم:", value="1120").strip()

if query.lower() == 'gold': symbol = "GC=F"
elif query.isdigit(): symbol = query + ".SR"
else: symbol = query.upper()

if symbol:
    try:
        # جلب بيانات فريم 4 ساعات لآخر شهر (لنأخذ أسبوعين منها بدقة)
        df = yf.download(symbol, period="1mo", interval="1h") # نستخدم 1h ونجمعها لـ 4h أو نعرضها مباشرة لدقة أعلى
        
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # تصفية البيانات لإظهار آخر أسبوعين فقط
            df = df.tail(24 * 14) # تقريباً آخر أسبوعين عمل

            # حساب المؤشرات
            df['RSI'] = ta.rsi(df['Close'], length=14)
            last_price = float(df['Close'].iloc[-1])
            
            # حساب التوقع (هدف اليومين القادمين)
            change = df['Close'].diff().tail(20).mean()
            expected_price = last_price + (change * 10) # معامل وزني للفريم القصير
            target_date = df.index[-1] + timedelta(days=2)

            # --- أ: الاسم الرئيسي ---
            st.markdown(f'<p class="main-title">{symbol}</p>', unsafe_allow_html=True)

            # --- ب: التشارت الفني الرئيسي (فريم قصير) ---
            st.subheader("📊 تحليل الشموع (آخر أسبوعين - فريم قصير)")
            fig1 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
            
            fig1.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="السعر"), row=1, col=1)
            fig1.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='purple')), row=2, col=1)
            
            # تحسين التحكم: تفعيل خاصية السحب والتقريب بسهولة
            fig1.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False, dragmode='pan')
            st.plotly_chart(fig1, use_container_width=True, config={'scrollZoom': True})

            st.write("---")

            # --- ج: قسم الأهداف والتوقعات (في الأسفل) ---
            st.subheader("🔮 أهداف السعر المتوقعة")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("السعر الحالي", f"{last_price:.2f}")
            c2.metric("الهدف (نجمة)", f"{expected_price:.2f}")
            c3.metric("تاريخ الهدف", target_date.strftime('%Y-%m-%d'))

            # تشارت التوقعات الصغير
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df.index.tail(20), y=df['Close'].tail(20), name="المسار الحالي", line=dict(color='gray')))
            fig2.add_trace(go.Scatter(x=[target_date], y=[expected_price], mode='markers+text',
                                     text=[f"⭐ {expected_price:.2f}"], textposition="top center",
                                     marker=dict(color='#00FFCC', size=25, symbol='star')))
            
            fig2.update_layout(height=300, template="plotly_dark", margin=dict(t=10, b=10))
            st.plotly_chart(fig2, use_container_width=True)

            # --- د: زر PDF ---
            def get_pdf():
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(190, 10, f"4H ANALYSIS REPORT: {symbol}", ln=True, align='C')
                pdf.ln(10)
                pdf.set_font("Arial", '', 12)
                pdf.cell(100, 10, f"Price: {last_price:.2f}")
                pdf.cell(100, 10, f"Target: {expected_price:.2f}", ln=True)
                pdf.multi_cell(0, 10, f"Summary: Short-term forecast for the next 48 hours is based on the 4H trend analysis.")
                return pdf.output(dest='S').encode('latin-1')

            st.download_button("📥 تحميل التقرير (PDF)", data=get_pdf(), file_name=f"{symbol}_4H_Analysis.pdf")

    except Exception as e:
        st.error(f"حدث خطأ في جلب بيانات الفريم القصير: {e}")
