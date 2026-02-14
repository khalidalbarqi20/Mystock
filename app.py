import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fpdf import FPDF
import numpy as np

st.set_page_config(page_title="المحلل الفني المتقدم", layout="wide")

# خانة البحث
query = st.text_input("أدخل رمز السهم أو الرقم (مثال: 1120 أو AAPL):", value="1120").strip()

# تحويل الرمز
if query.lower() == 'gold': symbol = "GC=F"
elif query.isdigit(): symbol = query + ".SR"
else: symbol = query.upper()

if symbol:
    try:
        df = yf.download(symbol, period="1y", interval="1d")
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            # حساب المؤشرات
            df['RSI'] = ta.rsi(df['Close'], length=14)
            df['SMA50'] = ta.sma(df['Close'], length=50)
            macd = ta.macd(df['Close'])
            df = pd.concat([df, macd], axis=1)

            # تحديد الدعم والمقاومة (آخر 20 يوم)
            support = float(df['Low'].tail(20).min())
            resistance = float(df['High'].tail(20).max())
            last_price = float(df['Close'].iloc[-1])

            # اسم السهم بخط عريض فوق التشارت
            st.markdown(f"<h1 style='text-align: center; color: white;'>📊 {symbol} - تحليل فني شامل</h1>", unsafe_allow_index=True)

            # الرسم البياني
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])

            # 1. الشموع
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="السعر"), row=1, col=1)
            
            # خطوط الدعم والمقاومة
            fig.add_hline(y=resistance, line_dash="dot", line_color="red", annotation_text="المقاومة", row=1, col=1)
            fig.add_hline(y=support, line_dash="dot", line_color="green", annotation_text="الدعم", row=1, col=1)

            # رسم خط الترند (تبسيط)
            x_trend = [df.index[-20], df.index[-1]]
            y_trend = [df['Close'].iloc[-20], df['Close'].iloc[-1]]
            trend_color = "green" if y_trend[1] > y_trend[0] else "red"
            fig.add_trace(go.Scatter(x=x_trend, y=y_trend, mode='lines', name='الترند الحالي', line=dict(color=trend_color, width=3)), row=1, col=1)

            # RSI & MACD
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='purple')), row=2, col=1)
            fig.add_trace(go.Bar(x=df.index, y=df.iloc[:, -1], name="MACD"), row=3, col=1)

            fig.update_layout(height=900, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # توقعات اليومين القادمين
            st.subheader("🔮 توقعات الـ 48 ساعة القادمة")
            rsi_val = df['RSI'].iloc[-1]
            if trend_color == "green" and rsi_val < 65:
                forecast_text = "استمرار الصعود نحو المقاومة التالية."
            elif trend_color == "red" and rsi_val > 35:
                forecast_text = "ضغط بيعي مستمر نحو مستويات الدعم."
            else:
                forecast_text = "تذبذب عرضي وانتظار إشارة اختراق."
            st.info(forecast_text)

            # زر PDF
            def create_pro_pdf():
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(190, 10, f"Technical Report: {symbol}", ln=True, align='C')
                pdf.set_font("Arial", '', 12)
                pdf.ln(10)
                pdf.cell(100, 10, f"Last Price: {last_price:.2f}")
                pdf.cell(100, 10, f"Trend: {'Bullish' if trend_color == 'green' else 'Bearish'}", ln=True)
                pdf.cell(100, 10, f"Support: {support:.2f}")
                pdf.cell(100, 10, f"Resistance: {resistance:.2f}", ln=True)
                pdf.ln(5)
                pdf.multi_cell(0, 10, f"Next 48h Forecast: {forecast_text}")
                return pdf.output(dest='S').encode('latin-1')

            st.download_button("📥 تصدير ملف PDF الاحترافي", data=create_pro_pdf(), file_name=f"Advanced_Report_{symbol}.pdf")

    except Exception as e:
        st.error(f"خطأ: {e}")
