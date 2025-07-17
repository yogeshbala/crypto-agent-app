import streamlit as st
import time
from crypto_agent import (
    fetch_ohlcv,
    prepare_features,
    train_model,
    evaluate_signal,
    place_limit_order,
    get_usdt_balance,
    exchange  # to access live price via ticker
)

st.set_page_config(page_title="Crypto Signal Agent", layout="wide")
st.title("🧠 Crypto Futures AI Agent (Testnet)")

# --- Controls
symbol = st.selectbox("Select Pair", ["BTCUSDT", "ETHUSDT"])
confidence_threshold = st.slider("Confidence Threshold", 0.2, 0.95, 0.20)
trade_amount = st.number_input("Trade Amount (USDT)", min_value=0.001, value=0.01)
auto_trade = st.checkbox("⚡ Auto Execute Limit Order")

# --- Balance
balance = get_usdt_balance()
st.metric("USDT Balance", f"{balance:.2f} USDT")

# --- Signal + Loop
signal_placeholder = st.empty()
if "signal_history" not in st.session_state:
    st.session_state.signal_history = []

if symbol:
    for _ in range(1000):
        df = fetch_ohlcv(symbol)
        if not df.empty:
            X, y = prepare_features(df)
            model = train_model(X, y)
            latest_X = X.iloc[-1:]
            direction, confidence = evaluate_signal(model, latest_X)

            # Live price preview
            ticker = exchange.fetch_ticker(symbol)
            price = ticker.get('ask') if direction.lower() == 'buy' else ticker.get('bid')

            # Update signal log
            st.session_state.signal_history.append({
                "Time": time.strftime("%H:%M:%S"),
                "Direction": direction,
                "Confidence": f"{confidence:.2%}",
                "Price": f"{price:.2f}" if price else "N/A"
            })
            st.session_state.signal_history = st.session_state.signal_history[-10:]

            with signal_placeholder.container():
                st.markdown(f"### 📈 Signal: `{direction}`")
                st.markdown(f"**Confidence:** `{confidence:.2%}`")
                if price:
                    st.info(f"💲 Expected {direction} price for `{symbol}`: `{price:.2f}` USDT")
                else:
                    st.warning("⚠️ Skipped trade — price not available.")

                if confidence >= confidence_threshold:
                    st.success(f"🎯 Signal detected: {direction}")
                    if auto_trade:
                        if "last_trade_time" not in st.session_state:
                            st.session_state.last_trade_time = 0
                        if time.time() - st.session_state.last_trade_time > 60:
                            order = place_limit_order(symbol, direction, trade_amount, price)
                            if order:
                                st.toast(f"✅ Order placed at {order['price']}")
                                st.session_state.last_trade_time = time.time()
                            else:
                                st.warning("⚠️ Skipped trade due to missing price.")
                        else:
                            st.info("⏱ Cooldown active.")
                else:
                    st.warning("🕒 Confidence below threshold.")

            if st.checkbox("📊 Show Signal History", value=False):
                st.dataframe(st.session_state.signal_history[::-1])

        time.sleep(3)
