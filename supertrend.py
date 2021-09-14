import ccxt
import config
import pandas as pd
import numpy as np
from datetime import datetime
import time
import pandas_ta as ta
import yfinance as yf
import vectorbt as vbt
from datetime import datetime

load_data = "ETHUSDT"
load_data_from_excel = load_data.replace('/','_')
data = pd.read_csv(load_data_from_excel+'.csv')

# data = pd.DataFrame()
# data = data.ta.ticker('AAPL', period = '3y', interval ='1d')
# print(data.tail(10))

df = data.copy()

print(df.tail(10))

# custom_strategy = ta.Strategy(
#     name = 'ema12_26_rsi',
#     description = '่CDC',
#     ta = [
#         {'kind':'ema','length':12},
#         {'kind':'ema','length':26},
#         {'kind':'rsi','length':14}
#     ])

# df.ta.strategy(custom_strategy)
# print(df.tail(10))