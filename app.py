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
st.title("🧠 Crypto Futures AI Agent (Testnet)")

# --- User controls
symbol = st.selectbox("Select Pair", ["BTCUSDT", "ETHUSDT"])
confidence_threshold = st.slider("Confidence Threshold", 0.2, 0.95, 0.2)
trade_amount = st.number_input("Trade Amount (USDT)", min_value=0.001, value=0.01)
auto_trade = st.checkbox("⚡ Auto Execute Limit Order")

# --- Balance display
balance = get_usdt_balance()
st.metric("USDT Balance", f"{balance:.2f}")

# --- Signal section refreshes every 3 seconds
signal_placeholder = st.empty()

if symbol:
    for _ in range(1000):
        df = fetch_ohlcv(symbol)
        if not df.empty:
            X, y = prepare_features(df)
            model = train_model(X, y)
            latest_X = X.iloc[-1:]
            direction, confidence = evaluate_signal(model, latest_X)

            with signal_placeholder.container():
                st.markdown(f"### 📈 Signal: `{direction}`")
                st.markdown(f"**Confidence:** `{confidence:.2%}`")

                if confidence >= confidence_threshold:
                    st.success(f"🎯 Signal detected: {direction}")
                    if auto_trade:
                        if "last_trade_time" not in st.session_state:
                            st.session_state.last_trade_time = 0
                        if time.time() - st.session_state.last_trade_time > 60:
                            order = place_limit_order(symbol, direction, trade_amount)
                            if order:
                                st.toast(f"✅ Order placed at {order['price']}")
                                st.session_state.last_trade_time = time.time()
                            else:
                                st.warning("⚠️ Order skipped due to missing price.")
                        else:
                            st.info("⏱ Cooldown active — waiting to re-trade.")
                else:
                    st.warning("🕒 Confidence below threshold.")

        time.sleep(3)
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
st.title("🧠 Crypto Futures AI Agent (Testnet)")

# --- User controls
symbol = st.selectbox("Select Pair", ["BTCUSDT", "ETHUSDT"])
confidence_threshold = st.slider("Confidence Threshold", 0.2, 0.95, 0.2)
trade_amount = st.number_input("Trade Amount (USDT)", min_value=0.001, value=0.01)
auto_trade = st.checkbox("⚡ Auto Execute Limit Order")

# --- Balance display
balance = get_usdt_balance()
st.metric("USDT Balance", f"{balance:.2f}")

# --- Signal section refreshes every 3 seconds
signal_placeholder = st.empty()

if symbol:
    for _ in range(1000):
        df = fetch_ohlcv(symbol)
        if not df.empty:
            X, y = prepare_features(df)
            model = train_model(X, y)
            latest_X = X.iloc[-1:]
            direction, confidence = evaluate_signal(model, latest_X)

            with signal_placeholder.container():
                st.markdown(f"### 📈 Signal: `{direction}`")
                st.markdown(f"**Confidence:** `{confidence:.2%}`")

                if confidence >= confidence_threshold:
                    st.success(f"🎯 Signal detected: {direction}")
                    if auto_trade:
                        if "last_trade_time" not in st.session_state:
                            st.session_state.last_trade_time = 0
                        if time.time() - st.session_state.last_trade_time > 60:
                            order = place_limit_order(symbol, direction, trade_amount)
                            if order:
                                st.toast(f"✅ Order placed at {order['price']}")
                                st.session_state.last_trade_time = time.time()
                            else:
                                st.warning("⚠️ Order skipped due to missing price.")
                        else:
                            st.info("⏱ Cooldown active — waiting to re-trade.")
                else:
                    st.warning("🕒 Confidence below threshold.")

        time.sleep(3)
