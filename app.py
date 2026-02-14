import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta

# إعدادات الصفحة
st.set_page_config(page_title="المحلل الفني الاحترافي", layout="wide")

# تنسيق CSS لحل مشكلة التداخل وترتيب الخطوط
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; }
    .main-header { font-size: 35px !important; color: #00FFCC; text-align: center; padding: 10px; border-bottom: 2px solid #333; margin-bottom: 20px; }
    .report-card { background-color: #1e2130; border-radius: 15px; padding: 20px; border: 1px solid #444; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# القائمة الجانبية (Sidebar)
with st.sidebar:
    st.title("🛠 التحكم")
    show_levels = st.checkbox("الدعم والمقاومة", value=True)
    show_rsi = st.checkbox("مؤشر RSI", value=True)
    show_macd = st.checkbox("مؤشر MACD", value=True)
    st.write("---")
    st.write("💡 لحفظ التقرير عربي وبكامل التشارتات: استخدم خيار 'طباعة' من المتصفح وحفظ كـ PDF.")

# البحث
query = st.text_input("🔍 أدخل الرمز (مثال: 1120 أو AAPL):", value="1120").strip()

if query:
    if query.lower() == 'gold': symbol = "GC=F"
    elif query.isdigit(): symbol = query + ".SR"
    else: symbol = query.upper()

    try:
        # جلب البيانات
        df = yf.download(symbol, period="1mo", interval="1h")
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df = df.tail(24 * 14) # آخر أسبوعين

            # العنوان
            st.markdown(f'<p class="main-header">تحليل السهم: {symbol}</p>', unsafe_allow_html=True)

            # الحسابات الفنية
            df['RSI'] = ta.rsi(df['Close'], length=14)
            macd = ta.macd(df['Close'])
            res = float(df['High'].max())
            sup = float(df['Low'].min())
            last_p = float(df['Close'].iloc[-1])
            
            # الهدف والنجمة
            target_p = last_p + (df['Close'].diff().tail(10).mean() * 5)
            target_d = df.index[-1] + timedelta(days=2)

            # التشارت الرئيسي
            rows = 1 + (1 if show_rsi else 0) + (1 if show_macd else 0)
            fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.05)
            
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="السعر"), row=1, col=1)
            
            if show_levels:
                fig.add_hline(y=res, line_dash="dash", line_color="red", annotation_text="مقاومة", row=1, col=1)
                fig.add_hline(y=sup, line_dash="dash", line_color="green", annotation_text="دعم", row=1, col=1)

            curr = 2
            if show_rsi:
                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='purple')), row=curr, col=1)
                curr += 1
            if show_macd:
                fig.add_trace(go.Bar(x=df.index, y=macd.iloc[:, -1], name="MACD"), row=curr, col=1)

            fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig, use_container_width=True)

            # منطقة التوقعات (مرتبة)
            st.markdown("<div class='report-card'>", unsafe_allow_html=True)
            st.subheader("🎯 أهداف اليومين القادمين")
            c1, c2, c3 = st.columns(3)
            c1.metric("السعر الحالي", f"{last_p:.2f}")
            c2.metric("الهدف (⭐)", f"{target_p:.2f}")
            c3.metric("التاريخ", target_d.strftime('%Y-%m-%d'))
            
            # تشارت النجمة
            fig_star = go.Figure()
            fig_star.add_trace(go.Scatter(x=df.index[-20:], y=df['Close'][-20:], mode='lines+markers', name="المسار"))
            fig_star.add_trace(go.Scatter(x=[target_d], y=[target_p], mode='markers+text', text=["⭐ الهدف"], textposition="top center", marker=dict(size=20, color="#00FFCC", symbol="star")))
            fig_star.update_layout(height=300, template="plotly_dark", title="مسار النجمة المتوقع")
            st.plotly_chart(fig_star, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"تأكد من الرمز، حدث خطأ: {e}")
