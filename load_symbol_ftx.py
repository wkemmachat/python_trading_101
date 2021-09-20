import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime
import ccxt

exchange = ccxt.ftx({
    
})

print('///////////////////////////////////')
# print(exchange.fetch_balance())
print('///////////////////////////////////')


bars = exchange.fetch_ohlcv('ETH/USDT', timeframe='5m', limit=4000)

all_symbol = []

for symbol in exchange.symbols:
  if ((symbol.lower().find("usd")) >=0 or (symbol.lower().find("busd"))) >=0:
    all_symbol.append(symbol)

dict = {'symbol': all_symbol}  
df = pd.DataFrame(dict) 
df.to_csv('symbol_ftx.csv')
