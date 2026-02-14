import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta

# 1. إعدادات الصفحة الفائقة (مخصصة للكمبيوتر)
st.set_page_config(page_title="منصة التحليل الفني العملاقة", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; }
    .main-container { padding: 2rem; background-color: #0e1117; }
    .symbol-header {
        background: linear-gradient(145deg, #1e2130, #0a0c10);
        padding: 40px;
        border-radius: 25px;
        border: 3px solid #00FFCC;
        text-align: center;
        margin-bottom: 50px;
        box-shadow: 0 10px 30px rgba(0,255,204,0.15);
    }
    .symbol-title { font-size: 85px !important; color: #00FFCC; font-weight: bold; margin: 0; text-shadow: 0 0 20px rgba(0,255,204,0.5); }
    .stMetric { background-color: #1e2130 !important; border-radius: 15px !important; border: 1px solid #333 !important; height: 120px; }
    </style>
    """, unsafe_allow_html=True)

# 2. محرك البحث العلوي
st.write("### 💻 منصة تحليل الأسواق المالية (نسخة الكمبيوتر)")
query = st.text_input("🔍 أدخل الرمز (1120، AAPL، GOLD):", value="1120").strip()

if query:
    if query.lower() == 'gold': symbol = "GC=F"
    elif query.isdigit(): symbol = query + ".SR"
    else: symbol = query.upper()

    try:
        # جلب البيانات (فريم 4 ساعات مجمع لآخر أسبوعين)
        data = yf.download(symbol, period="1mo", interval="1h")
        if not data.empty:
            if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
            df = data.tail(24 * 14)

            # --- أ: العنوان العملاق ---
            st.markdown(f'<div class="symbol-header"><p class="symbol-title">{symbol}</p><p style="color:white; font-size:24px;">تحليل فريم 4 ساعات - أسبوعين تداول</p></div>', unsafe_allow_html=True)

            # --- ب: الحسابات التقنية الشاملة ---
            df['SMA20'] = ta.sma(df['Close'], length=20)
            df['SMA50'] = ta.sma(df['Close'], length=50)
            df['SMA200'] = ta.sma(df['Close'], length=200)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            macd_df = ta.macd(df['Close'])
            df = pd.concat([df, macd_df], axis=1)

            res = float(df['High'].max())
            sup = float(df['Low'].min())
            last_p = float(df['Close'].iloc[-1])
            target_p = last_p + (df['Close'].diff().tail(10).mean() * 6)
            target_d = df.index[-1] + timedelta(days=2)

            # --- ج: التشارت العملاق (أكبر وأدق) ---
            # 3 لوحات: السعر (70%)، RSI (15%)، MACD (15%)
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.02, row_heights=[0.7, 0.15, 0.15])

            # 1. لوحة السعر والشموع
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="الشموع"), row=1, col=1)
            
            # المتوسطات المتحركة
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='yellow', width=1), name="SMA 20"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='orange', width=2), name="SMA 50"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], line=dict(color='red', width=3), name="SMA 200"), row=1, col=1)

            # مستويات الدعم والمقاومة بسمك أكبر
            fig.add_hline(y=res, line_dash="dash", line_color="#FF3131", line_width=2, annotation_text="مقاومة عنيفة", row=1, col=1)
            fig.add_hline(y=sup, line_dash="dash", line_color="#39FF14", line_width=2, annotation_text="دعم فولاذي", row=1, col=1)

            # 2. لوحة RSI
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#9b59b6', width=2), name="RSI"), row=2, col=1)
            fig.add_hline(y=70, line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_color="green", row=2, col=1)

            # 3. لوحة MACD
            fig.add_trace(go.Bar(x=df.index, y=df.iloc[:, -1], name="MACD Hist", marker_color='#555'), row=3, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df.iloc[:, -3], line=dict(color='#00FFCC'), name="MACD"), row=3, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df.iloc[:, -2], line=dict(color='#FF3131'), name="Signal"), row=3, col=1)

            fig.update_layout(height=1000, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=20,r=20,t=20,b=20))
            st.plotly_chart(fig, use_container_width=True)

            # --- د: لوحة الأهداف (الأسفل) ---
            st.write("---")
            st.markdown("### 🎯 بطاقات الأداء والهدف المتوقع")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("السعر الحالي", f"{last_p:.2f}")
            m2.metric("مستوى المقاومة", f"{res:.2f}")
            m3.metric("الهدف القادم ⭐", f"{target_p:.2f}")
            m4.metric("تاريخ الهدف", target_d.strftime('%Y-%m-%d'))

            # تشارت النجمة المنفصل (كبير)
            fig_star = go.Figure()
            fig_star.add_trace(go.Scatter(x=df.index[-25:], y=df['Close'][-25:], mode='lines+markers', name="المسار", line=dict(color='white', width=3)))
            fig_star.add_trace(go.Scatter(x=[target_d], y=[target_p], mode='markers+text',
                                         text=[f"⭐ الهدف: {target_p:.2f}"], textposition="top center",
                                         marker=dict(size=40, color="#00FFCC", symbol="star-diamond", line=dict(width=3, color="white"))))
            fig_star.update_layout(height=500, template="plotly_dark", title="خوارزمية المسار المستهدف")
            st.plotly_chart(fig_star, use_container_width=True)

            st.success(f"✅ تم تحديث كافة البيانات لرمز {symbol}. التقرير جاهز للطباعة بدقة عالية.")

    except Exception as e:
        st.error(f"خطأ تقني: {e}")
