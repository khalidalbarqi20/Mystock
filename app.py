import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta

# 1. إعدادات الصفحة الفائقة
st.set_page_config(page_title="منصة التحليل الاحترافية V3", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; }
    .main-header {
        background: #0e1117;
        padding: 25px;
        border-radius: 15px;
        border-right: 10px solid #00FFCC;
        margin-bottom: 30px;
        text-align: center;
    }
    .symbol-label { font-size: 70px !important; color: #00FFCC; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. نظام البحث
query = st.text_input("🔍 أدخل الرمز (مثال: 1120 أو AAPL):", value="1120").strip()

if query:
    if query.lower() == 'gold': symbol = "GC=F"
    elif query.isdigit(): symbol = query + ".SR"
    else: symbol = query.upper()

    try:
        # جلب البيانات بدقة عالية (آخر أسبوعين)
        data = yf.download(symbol, period="1mo", interval="1h")
        if not data.empty:
            if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
            df = data.tail(24 * 14)

            # --- أ: العنوان الضخم ---
            st.markdown(f'<div class="main-header"><p class="symbol-label">{symbol}</p></div>', unsafe_allow_html=True)

            # --- ب: الحسابات الفنية الكاملة ---
            # المتوسطات المتحركة
            df['SMA20'] = ta.sma(df['Close'], length=20)
            df['SMA50'] = ta.sma(df['Close'], length=50)
            df['SMA100'] = ta.sma(df['Close'], length=100)
            df['SMA200'] = ta.sma(df['Close'], length=200)
            
            # الماكد (MACD)
            macd = ta.macd(df['Close'])
            df = pd.concat([df, macd], axis=1)
            
            # الدعم والمقاومة
            resistance = float(df['High'].max())
            support = float(df['Low'].min())
            last_p = float(df['Close'].iloc[-1])
            
            # الهدف الذكي
            target_p = last_p + (df['Close'].diff().tail(10).mean() * 7)
            target_d = df.index[-1] + timedelta(days=2)

            # --- ج: التشارت العملاق (أكبر وأوضح) ---
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.03, row_heights=[0.75, 0.25])

            # 1. الشموع اليابانية
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                          low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)

            # 2. إضافة جميع المتوسطات المتحركة
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='yellow', width=1), name="SMA 20"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='orange', width=1.5), name="SMA 50"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], line=dict(color='red', width=2), name="SMA 200"), row=1, col=1)

            # 3. خطوط الدعم والمقاومة
            fig.add_hline(y=resistance, line_dash="dash", line_color="#FF3131", annotation_text="مقاومة قصوى", row=1, col=1)
            fig.add_hline(y=support, line_dash="dash", line_color="#39FF14", annotation_text="دعم قوي", row=1, col=1)

            # 4. مؤشر الماكد (MACD) في الأسفل
            fig.add_trace(go.Bar(x=df.index, y=df.iloc[:, -1], name="MACD Hist", 
                                marker_color='white', opacity=0.5), row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df.iloc[:, -3], line=dict(color='#00FFCC'), name="MACD Line"), row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df.iloc[:, -2], line=dict(color='#FF3131'), name="Signal Line"), row=2, col=1)

            fig.update_layout(height=900, template="plotly_dark", xaxis_rangeslider_visible=False,
                              margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)

            # --- د: قسم التوقعات الفائق ---
            st.write("---")
            c1, c2, c3 = st.columns(3)
            c1.metric("سعر الإغلاق", f"{last_p:.2f}")
            c2.metric("الهدف القادم ⭐", f"{target_p:.2f}")
            c3.metric("التاريخ المتوقع", target_d.strftime('%Y-%m-%d'))

            # تشارت النجمة الصغير
            fig_star = go.Figure()
            fig_star.add_trace(go.Scatter(x=df.index[-20:], y=df['Close'][-20:], name="المسار", line=dict(color='white')))
            fig_star.add_trace(go.Scatter(x=[target_d], y=[target_p], mode='markers+text',
                                         text=["⭐ Target"], textposition="top center",
                                         marker=dict(size=30, color="#00FFCC", symbol="star")))
            fig_star.update_layout(height=400, template="plotly_dark")
            st.plotly_chart(fig_star, use_container_width=True)

    except Exception as e:
        st.error(f"خطأ: {e}")
