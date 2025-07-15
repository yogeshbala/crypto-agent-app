import ccxt
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from sklearn.ensemble import RandomForestClassifier
import streamlit as st
import datetime

# --- Connect to Binance Futures Testnet ---
exchange = ccxt.binance({
    'apiKey': st.secrets["BINANCE_API_KEY"],
    'secret': st.secrets["BINANCE_SECRET"],
    'enableRateLimit': True,
    'options': {'defaultType': 'future'},
    'urls': {'api': 'https://testnet.binancefuture.com'}
})

def fetch_ohlcv(symbol='BTC/USDT', timeframe='5m', limit=200):
    exchange.set_sandbox_mode(True)  # Ensure sandbox is used
    markets = exchange.load_markets()

    data = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
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
    proba = model.predict_proba(latest_X)[0][1]
    direction = "BUY" if pred[0] == 1 else "SELL"
    return direction, proba

def place_limit_order(symbol, side, amount):
    ticker = exchange.fetch_ticker(symbol)
    price = ticker['ask'] if side.lower() == 'buy' else ticker['bid']
    order = exchange.create_order(
        symbol=symbol,
        type='limit',
        side=side.lower(),
        amount=amount,
        price=price,
        params={'reduceOnly': False}
    )
    return order
