import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime
import ccxt

exchange = ccxt.gateio({
    'enableRateLimit': True,  # required: https://github.com/ccxt/ccxt/wiki/Manual#rate-limit
})

print('///////////////////////////////////')
# print(exchange.fetch_balance())
print('///////////////////////////////////')


bars = exchange.fetch_ohlcv('ETH/USDT', timeframe='1d', limit=100)

all_symbol = []

for symbol in exchange.symbols:
  if (symbol.lower().find("usdt")) >=0:
    all_symbol.append(symbol)

dict = {'symbol': all_symbol}  
df = pd.DataFrame(dict) 
df.to_csv('symbol_gateio.csv')
