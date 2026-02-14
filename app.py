import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fpdf import FPDF
from datetime import timedelta

# 1. إعدادات الصفحة والتنسيق الجمالي
st.set_page_config(page_title="Pro-Chart Trading", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #262730; color: white; border: 1px solid #444; }
    .stButton>button:hover { border-color: #00FFCC; color: #00FFCC; }
    .target-box { background-color: #1e2130; border: 2px solid #00FFCC; padding: 20px; border-radius: 15px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# 2. القائمة الجانبية للتحكم (Sidebar)
with st.sidebar:
    st.header("🛠 أدوات التحكم")
    show_candles = st.checkbox("إظهار الشموع اليابانية", value=True)
    show_ma = st.checkbox("المتوسطات المتحركة (SMA)", value=True)
    show_trend = st.checkbox("خطوط الترند الذكية", value=True)
    show_levels = st.checkbox("الدعم والمقاومة", value=True)
    show_rsi = st.checkbox("مؤشر RSI", value=True)
    show_macd = st.checkbox("مؤشر MACD", value=True)
    st.write("---")
    st.info("نصيحة: استخدم الماوس لتقريب (Zoom) أو تحريك التشارت يميناً ويساراً.")

# 3. محرك البحث
c1, c2 = st.columns([3, 1])
with c1:
    query = st.text_input("🔍 ابحث عن سهم، عملة، أو ذهب (مثال: 1120, AAPL, GOLD):", value="1120").strip()

# تحويل الرمز
if query.lower() == 'gold': symbol = "GC=F"
elif query.isdigit(): symbol = query + ".SR"
else: symbol = query.upper()

if symbol:
    try:
        # جلب البيانات (فريم ساعة لآخر أسبوعين)
        df = yf.download(symbol, period="1mo", interval="1h")
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df = df.tail(24 * 14) # آخر أسبوعين

            # حسابات المؤشرات
            df['SMA50'] = ta.sma(df['Close'], length=50)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            macd = ta.macd(df['Close'])
            
            # حساب الدعم والمقاومة
            resistance = float(df['High'].max())
            support = float(df['Low'].min())
            last_price = float(df['Close'].iloc[-1])

            # حساب الهدف المستقبلي
            expected_price = last_price + (df['Close'].diff().tail(10).mean() * 5)
            target_date = df.index[-1] + timedelta(days=2)

            # --- التشارت الرئيسي (TradingView Style) ---
            st.markdown(f"<h1 style='text-align: center; color: #00FFCC;'>{symbol} Real-Time Chart</h1>", unsafe_allow_html=True)
            
            rows = 1
            if show_rsi: rows += 1
            if show_macd: rows += 1
            
            fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.6, 0.2, 0.2][:rows])

            # إضافة الشموع
            if show_candles:
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], 
                              increasing_line_color='#00ff88', decreasing_line_color='#ff3355', name="Price"), row=1, col=1)
            else:
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'], line=dict(color='#00FFCC', width=2), name="Line Price"), row=1, col=1)

            # إضافة المتوسطات
            if show_ma:
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='orange', width=1.5), name="SMA 50"), row=1, col=1)

            # إضافة الدعم والمقاومة
            if show_levels:
                fig.add_hline(y=resistance, line_dash="dash", line_color="#ff3355", opacity=0.5, annotation_text="مقاومة", row=1, col=1)
                fig.add_hline(y=support, line_dash="dash", line_color="#00ff88", opacity=0.5, annotation_text="دعم", row=1, col=1)

            # إضافة خط الترند
            if show_trend:
                fig.add_trace(go.Scatter(x=[df.index[0], df.index[-1]], y=[df['Close'].iloc[0], df['Close'].iloc[-1]], 
                              line=dict(color='yellow', width=2, dash='dot'), name="Trend Line"), row=1, col=1)

            # إضافة RSI
            if show_rsi:
                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#9b59b6', width=2), name="RSI"), row=2, col=1)
                fig.add_hline(y=70, line_color="red", row=2, col=1)
                fig.add_hline(y=30, line_color="green", row=2, col=1)

            # إضافة MACD
            if show_macd:
                macd_row = rows
                fig.add_trace(go.Bar(x=df.index, y=macd.iloc[:, -1], name="MACD Hist", marker_color='gray'), row=macd_row, col=1)

            fig.update_layout(height=700, template="plotly_dark", xaxis_rangeslider_visible=False, 
                              margin=dict(l=10, r=10, t=10, b=10), hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True, config={'displaylogo': False})

            # --- قسم الهدف والنجمة (تصميم جديد) ---
            st.write("---")
            st.markdown("<div class='target-box'>", unsafe_allow_html=True)
            st.subheader("🎯 هدف السعر المتوقع ونقطة النجمة")
            
            col_a, col_b = st.columns([1, 2])
            with col_a:
                st.metric("السعر المستهدف", f"{expected_price:.2f}")
                st.metric("التاريخ المتوقع", target_date.strftime('%d-%m-%Y'))
            
            with col_b:
                # تشارت النجمة المنفصل
                fig_star = go.Figure()
                fig_star.add_trace(go.Scatter(x=df.index[-20:], y=df['Close'][-20:], name="المسار الحالي", line=dict(color='white')))
                fig_star.add_trace(go.Scatter(x=[target_date], y=[expected_price], mode='markers+text',
                                             text=["⭐ الهدف السعري"], textposition="top center",
                                             marker=dict(color='#00FFCC', size=30, symbol='star-diamond')))
                fig_star.update_layout(height=300, template="plotly_dark", margin=dict(t=10, b=10))
                st.plotly_chart(fig_star, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # --- زر PDF ---
            def make_pdf():
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(190, 10, f"Trading Report: {symbol}", ln=True, align='C')
                pdf.ln(10)
                pdf.set_font("Arial", '', 12)
                pdf.cell(100, 10, f"Current Price: {last_price:.2f}")
                pdf.cell(100, 10, f"Target Price: {expected_price:.2f}", ln=True)
                pdf.cell(100, 10, f"Target Date: {target_date.strftime('%Y-%m-%d')}")
                return pdf.output(dest='S').encode('latin-1')

            st.download_button("📥 تصدير التقرير الفني الشامل PDF", data=make_pdf(), file_name=f"{symbol}_Pro_Report.pdf")

    except Exception as e:
        st.error(f"يرجى التأكد من الرمز. {e}")
