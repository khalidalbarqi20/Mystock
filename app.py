import streamlit as st
import yfinance as df
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from fpdf import FPDF
import base64

# إعدادات الصفحة
st.set_page_config(page_title="محلل الأسهم الذكي", layout="wide")

st.title("📈 منصة التحليل الفني الذكية (السوق السعودي والأمريكي)")
st.write("أدخل رمز السهم (مثال: 2222.SR لأرامكو أو AAPL لآبل)")

# مدخلات المستخدم
symbol = st.text_input("أدخل رمز السهم هنا:", value="2222.SR")

if symbol:
    # جلب البيانات
    data = df.download(symbol, period="1y", interval="1d")
    
    if not data.empty:
        # حساب المؤشرات الفنية
        data['RSI'] = ta.rsi(data['Close'], length=14)
        macd = ta.macd(data['Close'])
        data = pd.concat([data, macd], axis=1)
        data['SMA50'] = ta.sma(data['Close'], length=50)
        data['SMA200'] = ta.sma(data['Close'], length=200)

        # رسم الشموع اليابانية
        fig = go.Figure(data=[go.Candlestick(x=data.index,
                        open=data['Open'], high=data['High'],
                        low=data['Low'], close=data['Close'], name="الشموع")])
        fig.add_trace(go.Scatter(x=data.index, y=data['SMA50'], name="متوسط 50", line=dict(color='orange')))
        st.plotly_chart(fig, use_container_width=True)

        # تحليل RSI و MACD
        last_rsi = data['RSI'].iloc[-1]
        last_close = data['Close'].iloc[-1]
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("السعر الحالي", f"{last_close:.2f}")
            if last_rsi < 30:
                st.success("تشبع بيع (فرصة شراء محتملة)")
                decision = "شراء"
            elif last_rsi > 70:
                st.error("تشبع شراء (خطر - جني أرباح)")
                decision = "بيع / انتظار"
            else:
                st.info("وضع محايد")
                decision = "مراقبة"

        # وظيفة تحميل PDF
        def create_pdf():
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Technical Report for: {symbol}", ln=True, align='C')
            pdf.cell(200, 10, txt=f"Current Price: {last_close:.2f}", ln=True)
            pdf.cell(200, 10, txt=f"RSI Indicator: {last_rsi:.2f}", ln=True)
            pdf.cell(200, 10, txt=f"Final Decision: {decision}", ln=True)
            return pdf.output(dest='S').encode('latin-1')

        pdf_data = create_pdf()
        st.download_button(label="📄 تحميل تقرير PDF للتحليل", data=pdf_data, file_name=f"{symbol}_report.pdf", mime="application/pdf")
    else:
        st.error("رمز السهم غير صحيح، يرجى التأكد وكتابته بشكل صحيح.")
