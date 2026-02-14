import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fpdf import FPDF

st.set_page_config(page_title="المحلل الفني الاحترافي", layout="wide")

st.title("📈 منصة تحليل الأسهم (TASI & US)")
symbol = st.text_input("أدخل رمز السهم (مثال: 2222.SR أو AAPL):", value="2222.SR").upper()

if symbol:
    try:
        # 1. جلب البيانات
        df = yf.download(symbol, period="1y", interval="1d")
        if df.empty:
            st.error("لم يتم العثور على بيانات. تأكد من إضافة .SR للأسهم السعودية.")
        else:
            # تنظيف البيانات
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # 2. حساب المؤشرات الفنية
            df['RSI'] = ta.rsi(df['Close'], length=14)
            df['SMA50'] = ta.sma(df['Close'], length=50)
            df['SMA200'] = ta.sma(df['Close'], length=200)
            macd_data = ta.macd(df['Close'])
            df = pd.concat([df, macd_data], axis=1)

            # 3. توقع حركة الأسبوع القادم (بناءً على الزخم)
            last_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[-5]
            trend = "صاعد 🚀" if last_price > prev_price else "هابط 📉"

            # 4. رسم التشارت الاحترافي (الشموع + MACD + RSI)
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.05, row_heights=[0.5, 0.2, 0.3])

            # الشموع والمتوسطات
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], name="SMA 50", line=dict(color='orange')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], name="SMA 200", line=dict(color='red')), row=1, col=1)

            # RSI
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='purple')), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

            # MACD
            fig.add_trace(go.Bar(x=df.index, y=df.iloc[:, -2], name="MACD Hist"), row=3, col=1)

            fig.update_layout(height=800, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # 5. التوصية النهائية
            rsi_val = df['RSI'].iloc[-1]
            if rsi_val < 35: recommendation = "شراء (منطقة ارتداد)"
            elif rsi_val > 65: recommendation = "بيع (تضخم سعري)"
            else: recommendation = "انتظار (منطقة حيادية)"

            st.subheader(f"الخلاصة: {recommendation}")
            st.write(f"توقع الأسبوع القادم: **{trend}**")

            # 6. صنع ملف PDF متكامل
            def export_pdf():
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(190, 10, f"Technical Report: {symbol}", ln=True, align='C')
                pdf.set_font("Arial", '', 12)
                pdf.ln(10)
                pdf.cell(100, 10, f"Current Price: {last_price:.2f}")
                pdf.cell(100, 10, f"RSI Value: {rsi_val:.2f}", ln=True)
                pdf.cell(100, 10, f"SMA 50: {df['SMA50'].iloc[-1]:.2f}")
                pdf.cell(100, 10, f"SMA 200: {df['SMA200'].iloc[-1]:.2f}", ln=True)
                pdf.ln(5)
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(190, 10, f"Recommendation: {recommendation}", ln=True)
                pdf.cell(190, 10, f"Next Week Forecast: {trend}", ln=True)
                return pdf.output(dest='S').encode('latin-1')

            st.download_button("📄 تحميل التقرير الفني الشامل PDF", data=export_pdf(), file_name=f"{symbol}_Report.pdf")

    except Exception as e:
        st.error(f"حدث خطأ: تأكد من رمز السهم بشكل صحيح (مثال للراجحي 1120.SR)")
