import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fpdf import FPDF

# إعداد واجهة الموقع
st.set_page_config(page_title="رادار الأسهم والذهب", layout="wide")

st.title("🚀 رادار التحليل الفني اللحظي (TASI - US - GOLD)")

# خانة البحث الذكية
query = st.text_input("أدخل رقم السهم (مثلاً 1120) أو الرمز الأمريكي (AAPL) أو كلمة GOLD للذهب:", value="1120").strip()

# منطق التحويل الذكي
if query.lower() == 'gold':
    symbol = "GC=F"
elif query.isdigit():
    symbol = query + ".SR"
else:
    symbol = query.upper()

if symbol:
    try:
        # جلب البيانات اللحظية
        df = yf.download(symbol, period="1y", interval="1d")
        
        if df.empty:
            st.error(f"❌ الرمز {symbol} غير موجود. جرب 1120 للراجحي أو 2222 لأرامكو.")
        else:
            # تنظيف تنسيق الجداول
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # حساب المؤشرات الفنية (RSI, MACD, Moving Averages)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            df['SMA50'] = ta.sma(df['Close'], length=50)
            df['SMA200'] = ta.sma(df['Close'], length=200)
            macd = ta.macd(df['Close'])
            df = pd.concat([df, macd], axis=1)
            
            # تحديد أسماء أعمدة MACD
            m_line = df.columns[-3]
            s_line = df.columns[-2]
            h_line = df.columns[-1]

            # 1. شاشة العرض الرئيسية (الرسم البياني)
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.03, row_heights=[0.5, 0.2, 0.3])

            # شموع يابانية + متوسطات
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], name="SMA 50", line=dict(color='orange', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], name="SMA 200", line=dict(color='red', width=1)), row=1, col=1)

            # RSI
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='magenta')), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

            # MACD
            fig.add_trace(go.Bar(x=df.index, y=df[h_line], name="Histogram"), row=3, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df[m_line], name="MACD", line=dict(color='cyan')), row=3, col=1)

            fig.update_layout(height=800, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # 2. منطقة القرار الذكي (Buy/Sell) والتوقعات
            last_price = float(df['Close'].iloc[-1])
            rsi_now = float(df['RSI'].iloc[-1])
            
            # معادلة القرار
            if rsi_now < 30:
                decision = "🔥 شراء قوي (منطقة قاع)"
                color = "green"
            elif rsi_now > 70:
                decision = "⚠️ بيع فوراً (تضخم سعري)"
                color = "red"
            else:
                decision = "⚖️ مراقبة (منطقة حيادية)"
                color = "blue"

            # توقع الأسبوع القادم (بناءً على التقاطع)
            forecast = "صاعد 📈" if df[m_line].iloc[-1] > df[s_line].iloc[-1] else "هابط 📉"

            st.markdown(f"<h2 style='text-align: center; color: {color};'>{decision}</h2>", unsafe_allow_index=True)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("السعر اللحظي", f"{last_price:.2f}")
            col2.metric("مؤشر RSI", f"{rsi_now:.2f}")
            col3.metric("توقع الأسبوع القادم", forecast)

            # 3. وظيفة PDF
            def generate_pdf():
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(190, 10, f"Analysis Report: {symbol}", ln=True, align='C')
                pdf.ln(10)
                pdf.set_font("Arial", '', 12)
                pdf.cell(100, 10, f"Price: {last_price:.2f}")
                pdf.cell(100, 10, f"Decision: {decision}", ln=True)
                pdf.cell(100, 10, f"Trend Forecast: {forecast}", ln=True)
                return pdf.output(dest='S').encode('latin-1')

            st.download_button("📥 تحميل التقرير PDF", data=generate_pdf(), file_name=f"Report_{symbol}.pdf")

    except Exception as e:
        st.error(f"حدث خطأ: تأكد من كتابة الرمز بشكل صحيح. (تجنب الأسماء العربية)")
