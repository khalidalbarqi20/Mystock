import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from fpdf import FPDF
import base64

# إعداد الصفحة
st.set_page_config(page_title="محلل الأسهم الذكي", layout="wide")

st.title("📈 منصة التحليل الفني (السعودي + الأمريكي)")
st.info("للسوق السعودي أضف .SR بعد الرمز (مثال: 2222.SR). للأمريكي اكتب الرمز مباشرة (مثال: AAPL)")

# مدخلات المستخدم
symbol = st.text_input("أدخل رمز السهم:", value="2222.SR").upper()

if symbol:
    try:
        # جلب البيانات مع التأكد من صيغة الأرقام
        df = yf.download(symbol, period="1y", interval="1d")
        
        if not df.empty:
            # معالجة مشكلة التنسيق الجديد في ياهو فاينانس
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # حساب المؤشرات
            df['RSI'] = ta.rsi(df['Close'], length=14)
            macd = ta.macd(df['Close'])
            df = pd.concat([df, macd], axis=1)
            df['SMA50'] = ta.sma(df['Close'], length=50)

            # السعر الحالي (حل مشكلة TypeError)
            last_close = float(df['Close'].iloc[-1])
            last_rsi = float(df['RSI'].iloc[-1])

            # عرض السعر والحالة
            col1, col2 = st.columns(2)
            with col1:
                st.metric(f"سعر إغلاق {symbol}", f"{last_close:.2f}")
            
            with col2:
                if last_rsi < 35:
                    st.success("إشارة: تشبع بيع (منطقة شراء محتملة)")
                    status = "Buy Zone"
                elif last_rsi > 65:
                    st.error("إشارة: تشبع شراء (منطقة بيع/جني أرباح)")
                    status = "Sell Zone"
                else:
                    st.warning("إشارة: منطقة حيادية (مراقبة)")
                    status = "Neutral"

            # الرسم البياني
            fig = go.Figure(data=[go.Candlestick(x=df.index,
                            open=df['Open'], high=df['High'],
                            low=df['Low'], close=df['Close'], name="الشموع")])
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], name="متوسط 50 يوم", line=dict(color='orange')))
            fig.update_layout(title=f"حركة سهم {symbol}", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # زر الـ PDF
            def create_pdf():
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt=f"Stock Report: {symbol}", ln=True, align='C')
                pdf.cell(200, 10, txt=f"Price: {last_close:.2f}", ln=True)
                pdf.cell(200, 10, txt=f"RSI: {last_rsi:.2f}", ln=True)
                pdf.cell(200, 10, txt=f"Analysis: {status}", ln=True)
                return pdf.output(dest='S').encode('latin-1')

            pdf_data = create_pdf()
            st.download_button("📄 تحميل التقرير بصيغة PDF", data=pdf_data, file_name=f"{symbol}.pdf")

        else:
            st.error("لم يتم العثور على بيانات. تأكد من الرمز.")
    except Exception as e:
        st.error(f"حدث خطأ أثناء جلب البيانات: {e}")
