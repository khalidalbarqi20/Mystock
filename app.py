import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="المحلل الفني المتقدم", layout="wide")

# 2. تحسين المظهر ومنع التداخل (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; }
    .main-title-container {
        background-color: #1e2130;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #00FFCC;
        margin-bottom: 30px; /* مسافة تحت العنوان */
        text-align: center;
    }
    .symbol-name { font-size: 50px !important; color: #00FFCC; font-weight: bold; margin: 0; }
    .stCheckbox { margin-bottom: 10px; }
    .plot-container { margin-top: 20px; } /* مسافة فوق التشارت */
    </style>
    """, unsafe_allow_html=True)

# 3. محرك البحث (في الأعلى بوضوح)
query = st.text_input("🔍 أدخل الرمز (1120، AAPL، GOLD):", value="1120").strip()

# 4. لوحة التحكم (أزرار واضحة مع مسافات)
st.write("### 🛠 أدوات التحليل")
col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
with col_btn1: show_levels = st.checkbox("📈 الدعم والمقاومة", value=True)
with col_btn2: show_rsi = st.checkbox("🟣 مؤشر RSI", value=True)
with col_btn3: show_macd = st.checkbox("📊 مؤشر MACD", value=True)
with col_btn4: show_candles = st.checkbox("🕯️ الشموع اليابانية", value=True)

st.write("---") # فاصل واضح بين الأزرار والتشارت

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

            # --- أ: إظهار الاسم بوضوح تام ---
            st.markdown(f"""
                <div class="main-title-container">
                    <p class="symbol-name">{symbol}</p>
                    <p style="color: white; margin: 0;">تقرير التحليل الفني اللحظي</p>
                </div>
            """, unsafe_allow_html=True)

            # الحسابات
            df['RSI'] = ta.rsi(df['Close'], length=14)
            macd_data = ta.macd(df['Close'])
            res_val = float(df['High'].max())
            sup_val = float(df['Low'].min())
            last_p = float(df['Close'].iloc[-1])
            target_p = last_p + (df['Close'].diff().tail(10).mean() * 6)
            target_d = df.index[-1] + timedelta(days=2)

            # --- ب: التشارت الأساسي مع معالجة التداخل ---
            rows = 1
            if show_rsi: rows += 1
            if show_macd: rows += 1
            
            fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.07, # زيادة المسافة بين المؤشرات
                               row_heights=[0.6, 0.2, 0.2][:rows])

            # إضافة السعر
            if show_candles:
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                              low=df['Low'], close=df['Close'], name="الشموع"), row=1, col=1)
            else:
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'], line=dict(color='#00FFCC'), name="السعر الخطي"), row=1, col=1)

            # خطوط الدعم والمقاومة (إصلاح الظهور)
            if show_levels:
                fig.add_shape(type="line", x0=df.index[0], y0=res_val, x1=df.index[-1], y1=res_val,
                             line=dict(color="Red", width=2, dash="dash"), row=1, col=1)
                fig.add_shape(type="line", x0=df.index[0], y0=sup_val, x1=df.index[-1], y1=sup_val,
                             line=dict(color="Green", width=2, dash="dash"), row=1, col=1)
                fig.add_annotation(x=df.index[5], y=res_val, text="مقاومة", showarrow=False, font=dict(color="red"), row=1, col=1)
                fig.add_annotation(x=df.index[5], y=sup_val, text="دعم", showarrow=False, font=dict(color="green"), row=1, col=1)

            # المؤشرات الإضافية
            current_row = 2
            if show_rsi:
                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='#9b59b6')), row=current_row, col=1)
                current_row += 1
            if show_macd:
                fig.add_trace(go.Bar(x=df.index, y=macd_data.iloc[:, -1], name="MACD"), row=current_row, col=1)

            fig.update_layout(height=700, template="plotly_dark", xaxis_rangeslider_visible=False, 
                              margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)

            # --- ج: قسم الهدف (النجمة) بتصميم مستقل ---
            st.write("### 🔮 الهدف المتوقع خلال 48 ساعة")
            col1, col2 = st.columns([1, 2])
            with col1:
                st.info(f"السعر الحالي: {last_p:.2f}")
                st.success(f"الهدف المتوقع: {target_p:.2f}")
                st.warning(f"التاريخ المستهدف: {target_d.strftime('%Y-%m-%d')}")
            
            with col2:
                fig_star = go.Figure()
                fig_star.add_trace(go.Scatter(x=df.index[-15:], y=df['Close'][-15:], name="المسار", line=dict(color='white')))
                fig_star.add_trace(go.Scatter(x=[target_d], y=[target_p], mode='markers+text',
                                              text=["⭐ الهدف"], textposition="top center",
                                              marker=dict(size=25, color="#00FFCC", symbol="star-diamond")))
                fig_star.update_layout(height=300, template="plotly_dark", margin=dict(t=5, b=5))
                st.plotly_chart(fig_star, use_container_width=True)

    except Exception as e:
        st.error(f"حدث خطأ أثناء معالجة البيانات: {e}")
