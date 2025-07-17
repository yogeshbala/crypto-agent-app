import streamlit as st
import time
from crypto_agent import (
    fetch_ohlcv,
    prepare_features,
    train_model,
    evaluate_signal,
    place_limit_order,
    get_usdt_balance,
    exchange
)

st.set_page_config(page_title="Crypto Signal Agent", layout="wide")
st.title("🧠 Crypto Futures AI Agent with 50x Leverage")

# --- Controls
symbol = st.selectbox("Select Pair", ["BTCUSDT", "ETHUSDT"])
confidence_threshold = st.slider("Confidence Threshold", 0.2, 0.95, 0.3)
auto_trade = st.checkbox("⚡ Auto Execute Limit Order")
show_table = st.checkbox("📊 Show Signal History", value=False)
leverage = 50  # fixed leverage
sl_pct = 0.01  # 1% stop loss
tp_pct = 0.03  # 3% take profit

balance = get_usdt_balance()
st.metric("USDT Balance", f"{balance:.2f}")

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

            ticker = exchange.fetch_ticker(symbol)
            live_price = ticker.get('ask') if direction == 'BUY' else ticker.get('bid')
            fallback_price = df['close'].iloc[-1]
            price = live_price or fallback_price

            st.session_state.signal_history.append({
                "Time": time.strftime("%H:%M:%S"),
                "Direction": direction,
                "Confidence": f"{confidence:.2%}",
                "Price": f"{price:.2f}"
            })
            st.session_state.signal_history = st.session_state.signal_history[-10:]

            sl_price = round(price * (1 - sl_pct), 2) if direction == 'BUY' else round(price * (1 + sl_pct), 2)
            tp_price = round(price * (1 + tp_pct), 2) if direction == 'BUY' else round(price * (1 - tp_pct), 2)

            with signal_placeholder.container():
                st.markdown(f"### 📈 Signal: `{direction}`")
                st.markdown(f"**Confidence:** `{confidence:.2%}`")
                st.info(f"💲 Execution Price: `{price:.2f}` | SL: `{sl_price}` | TP: `{tp_price}` | Leverage: `{leverage}x`")

                if confidence >= confidence_threshold:
                    st.success(f"🎯 Signal detected: {direction}")
                    if auto_trade:
                        if "last_trade_time" not in st.session_state:
                            st.session_state.last_trade_time = 0
                        if time.time() - st.session_state.last_trade_time > 60:
                            order = place_limit_order(symbol, direction, leverage, balance, price, sl_pct, tp_pct)
                            if order:
                                st.toast(f"✅ Order placed at {order['price']}")
                                st.session_state.last_trade_time = time.time()
                            else:
                                st.warning("⚠️ Skipped trade — invalid price.")
                        else:
                            st.info("⏱ Cooldown active.")
                else:
                    st.warning("🕒 Confidence below threshold.")

            if show_table:
                st.dataframe(st.session_state.signal_history[::-1])

        time.sleep(3)
