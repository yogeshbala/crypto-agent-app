import streamlit as st
from crypto_agent import (
    fetch_ohlcv,
    prepare_features,
    train_model,
    evaluate_signal,
    place_limit_order,
    get_usdt_balance  # ✅ new balance function
)

st.set_page_config(page_title="Crypto Signal Agent", layout="wide")
st.title("🧠 Crypto Futures AI Agent (Testnet)")

# 💰 Show live USDT balance
usdt_balance = get_usdt_balance()
st.metric("Available USDT (Testnet)", f"{usdt_balance:.2f} USDT")

# 🎛️ User controls
symbol = st.selectbox("Select Pair", ["BTC/USDT", "ETH/USDT"])
confidence_threshold = st.slider("Signal Confidence Threshold", 0.5, 0.95, 0.75)
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
        st.success(f"🎯 High-confidence
