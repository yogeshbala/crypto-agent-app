import ccxt
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from sklearn.ensemble import RandomForestClassifier
import datetime
import time

# --- Binance Futures Testnet Setup ---
exchange = ccxt.binance({
    'apiKey': 'your_testnet_api_key',       # <- Replace with Streamlit secret or .env loading
    'secret': 'your_testnet_secret_key',
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

def fetch_ohlcv():
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


def place_limit_order(direction):
    ticker = exchange.fetch_ticker(symbol)
    price = ticker['ask'] if direction.lower() == 'buy' else ticker['bid']
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


