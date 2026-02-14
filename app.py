import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fpdf import FPDF

# إعداد الصفحة
st.set_page_config(page_title="المحلل الاحترافي - الذهب والأسهم", layout="wide")

# خانة البحث
query = st.text_input("أدخل الرقم (1120) أو الرمز (AAPL) أو GOLD:", value="1120").strip()

# تحويل الرمز ذكياً
if query.lower() == 'gold': symbol = "GC=F"
elif query.isdigit(): symbol = query + ".SR"
else: symbol = query.upper()

if symbol:
    try:
        # جلب البيانات
        df = yf.download(symbol, period="1y", interval="1d")
        
        if not df.empty:
            # تنظيف البيانات
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # حساب المؤشرات (RSI, MACD, SMA)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            df['SMA50'] = ta.sma(df['Close'], length=50)
            macd = ta.macd(df['Close'])
            df = pd.concat([df, macd], axis=1)

            # تحديد الدعم والمقاومة (آخر 30 يوم)
            support = float(df['Low'].tail(30).min())
            resistance = float(df['High'].tail(30).max())
            last_price = float(df['Close'].iloc[-1])

            # 1. اسم السهم بالعريض فوق التشارت
            st.markdown(f"<h1 style='text-align: center; color: #FFD700;'>📊 {symbol} ANALYSIS</h1>", unsafe_allow_html=True)

            # 2. بناء الرسم البياني المتطور
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])

            # الشموع اليابانية
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                                        low=df['Low'], close=df['Close'], name="السعر"), row=1, col=1)
            
            # خطوط الدعم والمقاومة
            fig.add_hline(y=resistance, line_dash="dash", line_color="red", annotation_text="مقاومة", row=1, col=1)
            fig.add_hline(y=support, line_dash="dash", line_color="green", annotation_text="دعم", row=1, col=1)

            # خط الترند (تلقائي لآخر 20 شمعة)
            trend_x = [df.index[-20], df.index[-1]]
            trend_y = [df['Close'].iloc[-20], df['Close'].iloc[-1]]
            t_color = "green" if trend_y[1] > trend_y[0] else "red"
            fig.add_trace(go.Scatter(x=trend_x, y=trend_y, name="الترند", line=dict(color=t_color, width=3)), row=1, col=1)

            # مؤشر RSI
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='purple')), row=2, col=1)
            fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)

            # مؤشر MACD
            fig.add_trace(go.Bar(x=df.index, y=df.iloc[:, -1], name="MACD Hist"), row=3, col=1)

            fig.update_layout(height=800, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # 3. توقعات اليومين القادمين
            st.write("---")
            st.subheader("🔮 التوقعات الفنية لليومين القادمين")
            rsi_now = df['RSI'].iloc[-1]
            if t_color == "green" and rsi_now < 65:
                forecast = "إيجابي: يتوقع استمرار الصعود لاختبار المقاومة."
            elif t_color == "red" and rsi_now > 35:
                forecast = "سلبي: ضغط بيعي قد يدفع السعر لكسر الدعم."
            else:
                forecast = "حيادي: حركة عرضية بانتظار سيولة جديدة."
            
            st.info(forecast)

            # 4. زر التصدير للـ PDF
            def make_pdf():
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(190, 10, f"Technical Report: {symbol}", ln=True, align='C')
                pdf.set_font("Arial", '', 12)
                pdf.ln(10)
                pdf.cell(100, 10, f"Last Price: {last_price:.2f}")
                pdf.cell(100, 10, f"RSI: {rsi_now:.2f}", ln=True)
                pdf.cell(100, 10, f"Support: {support:.2f}")
                pdf.cell(100, 10, f"Resistance: {resistance:.2f}", ln=True)
                pdf.ln(10)
                pdf.multi_cell(0, 10, f"Next 48h Forecast: {forecast}")
                return pdf.output(dest='S').encode('latin-1')

            st.download_button("📥 تحميل تقرير PDF شامل", data=make_pdf(), file_name=f"{symbol}_Report.pdf")

    except Exception as e:
        st.error(f"تأكد من الرمز. الراجحي هو 1120 وليس 1122. الخطأ الحالي: {e}")
