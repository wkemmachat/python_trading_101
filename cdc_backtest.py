import ccxt
import pandas as pd
import pandas_ta as ta
import numpy as np
import vectorbt as vbt
from datetime import datetime

exchange = ccxt.binance({
    
})


bars = exchange.fetch_ohlcv('ETH/USDT', timeframe='1d', limit=1000)

df2 = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df2['timestamp'] = pd.to_datetime(df2['timestamp'], unit='ms')
df2.set_index('timestamp',inplace = True)


#Insert TA
# df2.ta.rsi(length=14,append=True)
df2.ta.ema(length=12,append=True)
df2.ta.ema(length=26,append=True)

# print(df2)

def my_strategy2(df):
    if (df.EMA_12 > df.EMA_26) :
        return True
    else :
        return False

df2['signal'] = df2.apply(my_strategy2,axis=1).vbt.fshift(1)

df2 = df2.iloc[1:,:]

signal_vectorbt = df2.ta.tsignals(df2.signal, asbool=True, append=True)

port = vbt.Portfolio.from_signals(df2.close,
                                  entries = signal_vectorbt.TS_Entries,
                                  exits = signal_vectorbt.TS_Exits,
                                  init_cash = 100000,
                                  fees = 0.0025,
                                  slippage = 0.0025)

port.plot().show()
port.plot().write_image('backtest.png')
print(port.stats())