import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fpdf import FPDF

st.set_page_config(page_title="المحلل الفني الذكي", layout="wide")

st.title("📈 منصة التحليل الآلي (السعودي + الأمريكي)")

# خانة البحث الذكية
user_input = st.text_input("أدخل رمز أو رقم السهم (مثال: 2222 أو AAPL):", value="2222").strip()

# مصحح الرموز الذكي
if user_input.isdigit():
    symbol = user_input + ".SR"
else:
    symbol = user_input.upper()

if symbol:
    try:
        # 1. جلب البيانات
        df = yf.download(symbol, period="1y", interval="1d")
        
        if df.empty or len(df) < 10:
            st.error(f"❌ لم يتم العثور على بيانات للسهم ({symbol}). تأكد من الرقم أو الرمز.")
        else:
            # تنظيف البيانات من التنسيق الجديد لياهو
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # 2. حساب المؤشرات الفنية
            df['RSI'] = ta.rsi(df['Close'], length=14)
            df['SMA50'] = ta.sma(df['Close'], length=50)
            df['SMA200'] = ta.sma(df['Close'], length=200)
            
            # حساب MACD
            macd = ta.macd(df['Close'])
            df = pd.concat([df, macd], axis=1)
            # تسمية أعمدة MACD لسهولة الاستخدام
            macd_col = df.columns[-3] # MACD Line
            signal_col = df.columns[-2] # Signal Line
            hist_col = df.columns[-1] # Histogram

            # 3. توقع حركة الأسبوع القادم
            last_price = float(df['Close'].iloc[-1])
            prev_price = float(df['Close'].iloc[-5])
            trend = "صاعد 🚀" if last_price > prev_price else "هابط 📉"

            # 4. رسم التشارت الاحترافي (3 طوابق)
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.02, row_heights=[0.5, 0.2, 0.3])

            # الطابق 1: الشموع والمتوسطات
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                                        low=df['Low'], close=df['Close'], name="السعر"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], name="متوسط 50", line=dict(color='orange')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], name="متوسط 200", line=dict(color='red')), row=1, col=1)

            # الطابق 2: مؤشر RSI
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='purple')), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

            # الطابق 3: مؤشر MACD
            fig.add_trace(go.Bar(x=df.index, y=df[hist_col], name="MACD Hist"), row=3, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df[macd_col], name="MACD", line=dict(color='blue')), row=3, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df[signal_col], name="Signal", line=dict(color='orange')), row=3, col=1)

            fig.update_layout(height=900, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # 5. التوصية والتحليل
            rsi_val = float(df['RSI'].iloc[-1])
            if rsi_val < 35: reco = "شراء (منطقة دعم وقاع)"
            elif rsi_val > 65: reco = "بيع (منطقة قمة وتضخم)"
            else: reco = "انتظار (منطقة تذبذب حيادية)"

            st.success(f"📌 النتيجة النهائية للسهم: {reco}")
            st.info(f"🔮 التوقع للأسبوع القادم: {trend}")

            # 6. وظيفة الـ PDF المطور
            def create_full_pdf():
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(190, 10, f"Technical Report: {symbol}", ln=True, align='C')
                pdf.ln(10)
                pdf.set_font("Arial", '', 12)
                pdf.cell(95, 10, f"Current Price: {last_price:.2f}")
                pdf.cell(95, 10, f"RSI: {rsi_val:.2f}", ln=True)
                pdf.cell(95, 10, f"SMA 50: {float(df['SMA50'].iloc[-1]):.2f}")
                pdf.cell(95, 10, f"SMA 200: {float(df['SMA200'].iloc[-1]):.2f}", ln=True)
                pdf.ln(10)
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(190, 10, f"Recommendation: {reco}", ln=True)
                pdf.cell(190, 10, f"Forecast: {trend}", ln=True)
                return pdf.output(dest='S').encode('latin-1')

            st.download_button("📥 تحميل التقرير الفني الكامل (PDF)", data=create_full_pdf(), file_name=f"Analysis_{symbol}.pdf")

    except Exception as e:
        st.error(f"حدث خطأ فني: {e}")
