import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta

# 1. إعدادات الصفحة والهوية البصرية
st.set_page_config(page_title="منصة المحلل الاحترافية", layout="wide")

# تنسيق CSS متقدم لحل مشاكل التداخل وتجميل الخطوط
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; }
    .main-header {
        background: linear-gradient(90deg, #1e2130, #0e1117);
        padding: 30px;
        border-radius: 20px;
        border: 2px solid #00FFCC;
        text-align: center;
        margin-bottom: 40px;
        box-shadow: 0px 4px 15px rgba(0, 255, 204, 0.2);
    }
    .symbol-text { font-size: 65px !important; color: #00FFCC; font-weight: bold; margin: 0; line-height: 1; }
    .sub-text { color: #ffffff; font-size: 20px; margin-top: 10px; opacity: 0.8; }
    .control-panel { background-color: #161a25; padding: 20px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #333; }
    .stMetric { background-color: #1e2130 !important; border: 1px solid #444 !important; border-radius: 10px !important; padding: 15px !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. نظام البحث الذكي
st.write("### 🔍 البحث عن الأوراق المالية")
query = st.text_input("أدخل رقم السهم (1120) أو الرمز (AAPL) أو GOLD:", value="1120").strip()

# معالجة الرمز تلقائياً
if query.lower() == 'gold': symbol = "GC=F"
elif query.isdigit(): symbol = query + ".SR"
else: symbol = query.upper()

if symbol:
    try:
        # جلب البيانات (فريم ساعة لتمثيل الـ 4 ساعات بدقة لآخر أسبوعين)
        data = yf.download(symbol, period="1mo", interval="1h")
        
        if not data.empty:
            # تنظيف البيانات
            if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
            df = data.tail(24 * 14) # حصر البيانات في آخر أسبوعين فقط

            # --- أ: العنوان الضخم (اسم السهم) ---
            st.markdown(f"""
                <div class="main-header">
                    <p class="symbol-text">{symbol}</p>
                    <p class="sub-text">تقرير التحليل الفني اللحظي - فريم 4 ساعات</p>
                </div>
            """, unsafe_allow_html=True)

            # --- ب: لوحة التحكم (الأزرار) مع مسافات آمنة ---
            st.markdown('<div class="control-panel">', unsafe_allow_html=True)
            st.write("⚙️ **أدوات التحكم في الرسم البياني:**")
            col_c1, col_c2, col_c3, col_c4 = st.columns(4)
            with col_c1: show_candles = st.checkbox("🕯️ شموع يابانية", value=True)
            with col_c2: show_levels = st.checkbox("📏 دعم ومقاومة", value=True)
            with col_c3: show_rsi = st.checkbox("🟣 مؤشر RSI", value=True)
            with col_c4: show_macd = st.checkbox("📊 مؤشر MACD", value=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # --- ج: الحسابات الفنية ---
            df['RSI'] = ta.rsi(df['Close'], length=14)
            df['SMA50'] = ta.sma(df['Close'], length=50)
            macd_vals = ta.macd(df['Close'])
            
            res_level = float(df['High'].max())
            sup_level = float(df['Low'].min())
            last_p = float(df['Close'].iloc[-1])
            
            # خوارزمية النجمة (توقع 48 ساعة)
            momentum = df['Close'].diff().tail(10).mean()
            target_p = last_p + (momentum * 6)
            target_d = df.index[-1] + timedelta(days=2)

            # --- د: التشارت الرئيسي (TradingView Style) ---
            rows = 1 + (1 if show_rsi else 0) + (1 if show_macd else 0)
            fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.08, row_heights=[0.6, 0.2, 0.2][:rows])

            # رسم السعر
            if show_candles:
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                              low=df['Low'], close=df['Close'], name="السعر"), row=1, col=1)
            else:
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'], line=dict(color='#00FFCC', width=2), name="السعر"), row=1, col=1)

            # إضافة المتوسط المتحرك
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='orange', width=1), name="SMA 50"), row=1, col=1)

            # رسم مستويات الدعم والمقاومة بدقة
            if show_levels:
                fig.add_shape(type="line", x0=df.index[0], y0=res_level, x1=df.index[-1], y1=res_level,
                             line=dict(color="#ff3355", width=2, dash="dash"), row=1, col=1)
                fig.add_shape(type="line", x0=df.index[0], y0=sup_level, x1=df.index[-1], y1=sup_level,
                             line=dict(color="#00ff88", width=2, dash="dash"), row=1, col=1)

            # إضافة RSI و MACD في صفوف مستقلة
            current_r = 2
            if show_rsi:
                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='#9b59b6')), row=current_r, col=1)
                fig.add_hline(y=70, line_color="red", line_dash="dot", row=current_r, col=1)
                fig.add_hline(y=30, line_color="green", line_dash="dot", row=current_r, col=1)
                current_r += 1
            
            if show_macd:
                fig.add_trace(go.Bar(x=df.index, y=macd_vals.iloc[:, -1], name="MACD", marker_color='#444'), row=current_r, col=1)

            fig.update_layout(height=750, template="plotly_dark", xaxis_rangeslider_visible=False, 
                              margin=dict(l=10, r=10, t=10, b=10), hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

            # --- هـ: قسم النجمة والتوقعات (تصميم منفصل ومرتب) ---
            st.write("---")
            st.markdown("### 🔮 خوارزمية التوقع والهدف الذكي")
            
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("السعر اللحظي", f"{last_p:.2f}")
            col_m2.metric("الهدف المتوقع (⭐)", f"{target_p:.2f}")
            col_m3.metric("تاريخ الوصول التقديري", target_d.strftime('%Y-%m-%d'))

            # تشارت النجمة الخاص
            fig_star = go.Figure()
            fig_star.add_trace(go.Scatter(x=df.index[-20:], y=df['Close'][-20:], mode='lines+markers', name="المسار الحالي", line=dict(color='white')))
            fig_star.add_trace(go.Scatter(x=[target_d], y=[target_p], mode='markers+text',
                                         text=["⭐ الهدف القادم"], textposition="top center",
                                         marker=dict(size=30, color="#00FFCC", symbol="star-diamond", line=dict(width=2, color="white"))))
            
            fig_star.update_layout(height=400, template="plotly_dark", title="مسار النجمة المستهدف (48 ساعة)")
            st.plotly_chart(fig_star, use_container_width=True)

            # ملخص التقرير للطباعة
            st.info(f"📝 **ملخص التقرير:** السهم {symbol} يتداول حالياً عند {last_p:.2f}. "
                    f"بناءً على المعطيات الفنية، الهدف القادم هو {target_p:.2f}. "
                    f"الدعم القوي عند {sup_level:.2f} والمقاومة عند {res_level:.2f}.")

    except Exception as e:
        st.error(f"يرجى التأكد من الرمز. خطأ: {e}")
