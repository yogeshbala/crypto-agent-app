import ccxt
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from sklearn.ensemble import RandomForestClassifier
import streamlit as st

# --- Setup Binance Testnet ---
exchange = ccxt.binance({
    'apiKey': st.secrets["BINANCE_API_KEY"],
    'secret': st.secrets["BINANCE_SECRET"],
    'enableRateLimit': True,
    'options': {'defaultType': 'future'},
    'urls': {'api': 'https://testnet.binancefuture.com'}
})
exchange.set_sandbox_mode(True)

# --- Feature & Signal Functions ---
def fetch_ohlcv(symbol):
    data = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=200)
    df = pd.DataFrame(data, columns=['timestamp','open','high','low','close','volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def add_indicators(df):
    df['rsi'] = RSIIndicator(df['close'], window=14).rsi()
    df['ema_fast'] = EMAIndicator(df['close'], window=5).ema_indicator()
    df['ema_slow'] = EMAIndicator(df['close'], window=20).ema_indicator()
    return df.dropna()

def prepare_features(df):
    df = add_indicators(df)
    df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
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
    return balance['total'].get('USDT', 0)

def place_limit_order(symbol, direction, trade_amount):
    ticker = exchange.fetch_ticker(symbol)
    price = ticker['ask'] if direction.lower() == 'buy' else ticker['bid']
    if price is None:
        raise ValueError("❌ No valid price from ticker.")
    order = exchange.create_order(
        symbol=symbol,
        type='limit',
        side=direction.lower(),
        amount=trade_amount,
        price=price,
        params={'reduceOnly': False}
    )
    return order
