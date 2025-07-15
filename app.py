import streamlit as st
import time
from crypto_agent import (
    fetch_ohlcv,
    prepare_features,
    train_model,
    evaluate_signal,
    place_limit_order,
    get_usdt_balance
)

st.set_page_config(page_title="Crypto Signal Agent", layout="wide")

# 🔁 Auto-refresh every 3 seconds
st.markdown(
    "<meta http-equiv='refresh' content='3'>",
    unsafe_allow_html=True
)

st.title("🧠 Crypto Futures AI Agent (Testnet)")

# 💰 Show live USDT balance
usdt_balance = get_usdt_balance()
st.metric("Available USDT (Testnet)", f"{usdt_balance:.2f} USDT")

# 🎛️ User controls
symbol = st.selectbox("Select Pair", ["BTC/USDT", "ETH/USDT"])
confidence_threshold = st.slider("Signal Confidence Threshold", 0.2, 0.95, 0.20)
trade_amount = st.number_input("Trade Amount", min_value=0.001, value=0.01)
auto_trade = st.checkbox("⚡ Auto Execute Limit Order")

# 📊 Signal logic
df = fetch_ohlcv(symbol)
if not df.empty:
    X, y = prepare_features(df)
    model = train_model(X, y)
    latest_X = X.iloc[-1:].copy()
    direction, confidence = evaluate_signal(model, latest_X)

    st.markdown(f"### 📈 Signal: `{direction}`")
    st.markdown(f"**Confidence:** `{confidence:.2%}`")

    if confidence >= confidence_threshold:
        st.success(f"🎯 High-confidence signal detected: {direction}")
        if auto_trade:
            if "last_trade_time" not in st.session_state:
                st.session_state.last_trade_time = 0
            if time.time() - st.session_state.last_trade_time > 60:
                order = place_limit_order(symbol, direction, trade_amount)
                st.toast(f"✅ Limit order placed at {order['price']}")
                st.session_state.last_trade_time = time.time()
            else:
                st.info("⏱ Trade cooldown active — waiting before next execution.")
    else:
        st.warning("🕒 Watching silently... Confidence below threshold.")
