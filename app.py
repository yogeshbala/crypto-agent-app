import time
import streamlit as st

signal_placeholder = st.empty()

# Run signal refresh loop safely
for i in range(1000):  # refresh ~1000 cycles
    df = fetch_ohlcv(symbol)
    if not df.empty:
        X, y = prepare_features(df)
        model = train_model(X, y)
        latest_X = X.iloc[-1:].copy()
        direction, confidence = evaluate_signal(model, latest_X)

        with signal_placeholder.container():
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

    time.sleep(3)
