import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta

# 1. إعدادات الصفحة (ثيم داكن وتنسيق عربي)
st.set_page_config(page_title="منصة التحليل الفني الاحترافية", layout="wide")

# إضافة CSS لتحسين الخطوط والمظهر
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Cairo', sans-serif;
        text-align: right;
        direction: rtl;
    }
    .main-title { font-size: 55px !important; color: #00FFCC; text-align: center; font-weight: bold; }
    .stMetric { background-color: #1e2130; border: 1px solid #00FFCC; border-radius: 10px; padding: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 2. القائمة الجانبية للتحكم
with st.sidebar:
    st.header("⚙️ لوحة التحكم")
    show_rsi = st.checkbox("إظهار مؤشر القوة النسبية (RSI)", value=True)
    show_macd = st.checkbox("إظهار مؤشر الماكد (MACD)", value=True)
    show_levels = st.checkbox("إظهار الدعم والمقاومة", value=True)
    st.write("---")
    st.info("💡 لحفظ التقرير: اضغط (Ctrl + P) واختر 'Save as PDF'")

# 3. البحث
query = st.text_input("🔍 أدخل الرمز (مثال: 1120 للراجحي، AAPL لآبل، GOLD للذهب):", value="1120").strip()

if query.lower() == 'gold': symbol = "GC=F"
elif query.isdigit(): symbol = query + ".SR"
else: symbol = query.upper()

if symbol:
    try:
        # جلب بيانات فريم 4 ساعات (نستخدم ساعة ونعيد تشكيلها لآخر أسبوعين)
        df = yf.download(symbol, period="1mo", interval="1h")
        
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df = df.tail(24 * 14) # آخر أسبوعين

            # حساب المؤشرات
            df['RSI'] = ta.rsi(df['Close'], length=14)
            macd_df = ta.macd(df['Close'])
            df = pd.concat([df, macd_df], axis=1)
            
            last_price = float(df['Close'].iloc[-1])
            res_level = float(df['High'].max())
            sup_level = float(df['Low'].min())
            
            # حساب الهدف المستقبلي (نجمه)
            target_price = last_price + (df['Close'].diff().tail(10).mean() * 8)
            target_date = df.index[-1] + timedelta(days=2)

            # --- عرض اسم السهم بالخط العريض ---
            st.markdown(f'<p class="main-title">تحليل سهم: {symbol}</p>', unsafe_allow_html=True)

            # --- التشارت الأساسي (مثل TradingView) ---
            rows = 1 + (1 if show_rsi else 0) + (1 if show_macd else 0)
            fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.02)

            # الشموع
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                          low=df['Low'], close=df['Close'], name="السعر"), row=1, col=1)
            
            if show_levels:
                fig.add_hline(y=res_level, line_dash="dash", line_color="red", annotation_text="مقاومة", row=1, col=1)
                fig.add_hline(y=sup_level, line_dash="dash", line_color="green", annotation_text="دعم", row=1, col=1)

            curr_row = 2
            if show_rsi:
                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='#9b59b6')), row=curr_row, col=1)
                curr_row += 1
            
            if show_macd:
                fig.add_trace(go.Bar(x=df.index, y=df.iloc[:, -1], name="MACD"), row=curr_row, col=1)

            fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # --- قسم التوقعات والنجمة (تحت التشارت) ---
            st.write("---")
            st.header("🔮 توقعات اليومين القادمين")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("السعر الحالي", f"{last_price:.2f}")
            with col2:
                st.metric("الهدف المتوقع (⭐)", f"{target_price:.2f}")
            with col3:
                st.metric("التاريخ المتوقع", target_date.strftime('%Y-%m-%d'))

            # تشارت الهدف الصغير
            fig_target = go.Figure()
            fig_target.add_trace(go.Scatter(x=df.index[-15:], y=df['Close'][-15:], name="المسار", line=dict(color='white')))
            fig_target.add_trace(go.Scatter(x=[target_date], y=[target_price], mode='markers+text',
                                          text=["⭐ الهدف"], textposition="top center",
                                          marker=dict(color='#00FFCC', size=25, symbol='star')))
            fig_target.update_layout(height=350, template="plotly_dark", title="مسار الهدف السعري")
            st.plotly_chart(fig_target, use_container_width=True)

            # --- الخلاصة العربية للتقرير ---
            st.subheader("📝 ملخص التقرير الفني")
            trend_status = "صاعد" if target_price > last_price else "هابط"
            st.write(f"بناءً على تحليل فريم الـ 4 ساعات لآخر أسبوعين، يظهر السهم في مسار **{trend_status}**. "
                     f"مستويات الدعم الرئيسية عند {sup_level:.2f} والمقاومة عند {res_level:.2f}. "
                     f"يتوقع وصول السعر إلى المنطقة المستهدفة {target_price:.2f} خلال الـ 48 ساعة القادمة.")

    except Exception as e:
        st.error(f"حدث خطأ في جلب البيانات: {e}")
