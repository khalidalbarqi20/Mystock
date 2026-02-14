import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fpdf import FPDF
from datetime import timedelta

st.set_page_config(page_title="المحلل الفني الذكي", layout="wide")

# خانة البحث
query = st.text_input("أدخل الرمز (مثال: 1120 أو AAPL أو GOLD):", value="1120").strip()

# تحويل الرمز
if query.lower() == 'gold': symbol = "GC=F"
elif query.isdigit(): symbol = query + ".SR"
else: symbol = query.upper()

if symbol:
    try:
        df = yf.download(symbol, period="1y", interval="1d")
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            # اسم السهم فوق التشارت مباشرة بخط عريض جداً
            st.markdown(f"<div style='text-align: center;'><h1 style='font-size: 60px; color: #00FFCC;'>{symbol}</h1></div>", unsafe_allow_html=True)

            # حساب المؤشرات
            df['RSI'] = ta.rsi(df['Close'], length=14)
            df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
            last_price = float(df['Close'].iloc[-1])
            atr_val = float(df['ATR'].iloc[-1])

            # معادلة التوقع لليومين القادمين
            # إذا كان الزخم صاعد نضيف قيمة ATR، وإذا هابط نطرحها
            change = df['Close'].diff().tail(5).mean()
            expected_price = last_price + (change * 2) 
            target_date = df.index[-1] + timedelta(days=2)

            # الرسم البياني
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])

            # 1. الشموع
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="السعر"), row=1, col=1)
            
            # 2. إضافة نقطة الهدف المتوقع على التشارت
            fig.add_trace(go.Scatter(x=[target_date], y=[expected_price], mode='markers+text', 
                                     text=[f"الهدف: {expected_price:.2f}"], textposition="top center",
                                     marker=dict(color='cyan', size=15, symbol='star'), name="الهدف المتوقع"), row=1, col=1)

            # 3. خطوط الدعم والمقاومة والترند
            res = float(df['High'].tail(20).max())
            sup = float(df['Low'].tail(20).min())
            fig.add_hline(y=res, line_dash="dash", line_color="red", row=1, col=1)
            fig.add_hline(y=sup, line_dash="dash", line_color="green", row=1, col=1)

            # RSI & MACD
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='purple')), row=2, col=1)
            macd = ta.macd(df['Close'])
            fig.add_trace(go.Bar(x=df.index, y=macd.iloc[:, -1], name="MACD Hist"), row=3, col=1)

            fig.update_layout(height=850, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # عرض التوقعات بالأرقام
            st.success(f"🎯 الهدف المتوقع خلال يومين العمل القادمين: {expected_price:.2f}")
            st.info(f"💡 تعتمد هذه القيمة على متوسط الحركة السعرية الأخيرة (Momentum) وقوة التذبذب.")

            # تصدير PDF
            def create_pdf():
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(190, 10, f"Technical Report: {symbol}", ln=True, align='C')
                pdf.ln(10)
                pdf.set_font("Arial", '', 12)
                pdf.cell(100, 10, f"Current Price: {last_price:.2f}")
                pdf.cell(100, 10, f"Expected Target (2 Days): {expected_price:.2f}", ln=True)
                pdf.cell(100, 10, f"Support: {sup:.2f}")
                pdf.cell(100, 10, f"Resistance: {res:.2f}", ln=True)
                return pdf.output(dest='S').encode('latin-1')

            st.download_button("📥 تحميل التقرير الشامل PDF", data=create_pdf(), file_name=f"{symbol}_Final_Report.pdf")

    except Exception as e:
        st.error(f"حدث خطأ: تأكد من الرمز. {e}")
