import ccxt
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from sklearn.ensemble import RandomForestClassifier
import datetime
import time

# --- Binance Futures Testnet Setup ---
exchange = ccxt.binance({
    'apiKey': '9424f058f6e43ccc326495e1b100dae2b7c74fc520a8936e545d7c0378afeff0',       # <- Replace with Streamlit secret or .env loading
    'secret': '75c405b431c4620554ee25d2fe4cd5b54daf21f0269d57c6f3509220f72214a0',
    'enableRateLimit': True,
    'options': {'defaultType': 'future'},
    'urls': {'api': 'https://testnet.binancefuture.com'}
})

# 🛠 Testnet compatibility fixes
exchange.set_sandbox_mode(True)
exchange.has['fetchCurrencies'] = False
exchange.options['warnOnFetchCurrenciesWithoutAuthorization'] = False

symbol = 'BTC/USDT'
timeframe = '5m'
trade_amount = 0.01
confidence_threshold = 0.75

def fetch_ohlcv(symbol):
    data = exchange.fetch_ohlcv(symbol, timeframe, limit=200)
    df = pd.DataFrame(data, columns=['timestamp','open','high','low','close','volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df


def add_indicators(df):
    df['rsi'] = RSIIndicator(df['close'], window=14).rsi()
    df['ema_fast'] = EMAIndicator(df['close'], window=5).ema_indicator()
    df['ema_slow'] = EMAIndicator(df['close'], window=20).ema_indicator()
    df.dropna(inplace=True)
    return df

def prepare_features(df):
    df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
    df = add_indicators(df)
    X = df[['rsi', 'ema_fast', 'ema_slow']]
    y = df['target']
    return X, y

def train_model(X, y):
    model = RandomForestClassifier()
    model.fit(X, y)
    return model

def evaluate_signal(model, latest_X):
    pred = model.predict(latest_X)
    confidence = model.predict_proba(latest_X)[0][1]
    direction = 'BUY' if pred[0] == 1 else 'SELL'
    return direction, confidence

def get_usdt_balance():
    balance = exchange.fetch_balance()
    usdt_balance = balance['total'].get('USDT', 0)
    return usdt_balance


def place_limit_order(symbol, direction, trade_amount):
    ticker = exchange.fetch_ticker(symbol)
    price = ticker['ask'] if direction.lower() == 'buy' else ticker['bid']

    if price is None:
        raise ValueError("❌ Couldn't fetch price — ticker may be invalid or unavailable.")

    order = exchange.create_order(
        symbol=symbol,
        type='limit',
        side=direction.lower(),
        amount=trade_amount,
        price=price,
        params={'reduceOnly': False}
    )
    print(f"📥 Placed LIMIT ORDER: {direction} {trade_amount} @ {price}")
    return order



def run_auto_trader():
    import time
    print("🚀 Auto trading loop started")

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
                time.sleep(60)
            else:
                time.sleep(15)
        except Exception as e:
            print("⚠️ Error:", e)
            time.sleep(30)


