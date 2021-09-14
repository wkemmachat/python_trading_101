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
import requests

exchange = ccxt.binance({
    "apiKey": config.BINANCE_API_KEY,
    "secret": config.BINANCE_API_SECRET
})

### LINE NOTI
token_line = 'yNkEnMNx8rshijO0SQpexZgzCICkKOW7JhfFpVC8Yz0'
headers = {'content-type':'application/x-www-form-urlencoded','Authorization':'Bearer '+token_line}
url_line = 'https://notify-api.line.me/api/notify'

#############################################
#Helper Function 
#############################################

def get_date_time():  # เวลาปัจจุบัน
    named_tuple = time.localtime() # get struct_time
    Time = time.strftime("%Y/%m/%d %H:%M:%S", named_tuple)
    return Time

# data = pd.DataFrame()
# data = data.ta.ticker('AAPL', period = '3y', interval ='1d')
# print(data.tail(10)) 

load_data = 'ETH/USDT'
load_data_to_excel = load_data.replace('/','_')
# print(load_data_to_excel)

print(f"Fetching new bars for {datetime.now().isoformat()}")
bars = exchange.fetch_ohlcv(load_data, timeframe='1d', limit=1000)
df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df.set_index('timestamp',inplace = True)
#print(df.tail(10))
# df.to_csv(load_data_to_excel+'.csv')

canContinue = True
try:
    #Get Data
    balance = exchange.fetch_balance()
    ticker = exchange.fetch_ticker(load_data)
    msg = 'API Binance Working -- Normal --, Timing : '+get_date_time()
    r = requests.post(url_line, headers=headers, data = {'message':msg})
    print (r.text)
except:
    msg = 'API Binance --- ERROR ---, Timing : '+get_date_time()
    r = requests.post(url_line, headers=headers, data = {'message':msg})
    print (r.text)
    canContinue = False

print('///////////////////////////////////////')
if(canContinue):
    print('Can continue')
else:
    print('Can not continue')

  

