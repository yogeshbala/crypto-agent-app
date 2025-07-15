from crypto_agent import (
    fetch_ohlcv, prepare_features, train_model,
    evaluate_signal, place_limit_order
)

# --- Main Auto Loop ---
print("🚀 Auto trading bot running...")

while True:
    try:
        df = fetch_ohlcv()
        X, y = prepare_features(df)
        model = train_model(X, y)
        latest_X = X.iloc[-1:]
        direction, confidence = evaluate_signal(model, latest_X)

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Signal: {direction} | Confidence: {confidence:.2%}")

        if confidence >= confidence_threshold:
            place_limit_order(direction)
            time.sleep(60)  # cool-down after trading
        else:
            time.sleep(15)  # watch silently

    except Exception as e:
        print("⚠️ Error:", e)
        time.sleep(30)
