import yfinance as yf
import sqlite3
import config
import pandas as pd
import numpy as np
from datetime import datetime,timedelta
import time
import pandas_ta as ta
import schedule
import requests
import csv
from numpy import genfromtxt
from PIL import Image
from pandas_datareader import data as pdr
import plotly.offline as pyo
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import vectorbt as vbt

# pyo.init_notebook_mode(connected=True)

# pd.options.plotting.backend = 'plotly'


#Set Testnet
# exchange.set_sandbox_mode(True)

############################################
#Must Edit
############################################
# underlying_to_trade = 'ETH/USDT'
# pair = underlying_to_trade
timeframe = '1d'
limit_data_lookback = 100
limit_data_lookback_port = 1000
initial_money = 100
trade_money = initial_money #if first order use initial_money otherwise use comulative_money
database_name = 'traderecord.db'
strategy = 'CDC_12_26'


str_end_date = datetime.now().strftime('%Y-%m-%d')
# print("////////Testing///////////")
# print(str_end_date)

str_start_date = (datetime.now()- timedelta(days=limit_data_lookback)).strftime('%Y-%m-%d')
# print("////////Testing///////////")
# print(str_start_date)

str_start_date_port = (datetime.now()- timedelta(days=limit_data_lookback_port)).strftime('%Y-%m-%d')
# print("////////Testing///////////")
# print(str_start_date_port)





### LINE NOTI
token_line = 'ktv0utnOI8lby9eXhrUhxqbqFxdG9VywMMjr6v5BQ57'
headers = {'Authorization':'Bearer '+token_line}
url_line = 'https://notify-api.line.me/api/notify'

# 0 = Hold , 1 = Buy , -1 = Sell
canContinue = True
buyHoldSellSignal = 0

#############################################
#Helper Function 
#############################################

def get_date_time():  # เวลาปัจจุบัน
    named_tuple = time.localtime() # get struct_time
    Time = time.strftime("%Y-%m-%d %H:%M:%S", named_tuple)
    return Time

def get_date():  # เวลาปัจจุบัน
    named_tuple = time.localtime() # get struct_time
    Time = time.strftime("%Y-%m-%d", named_tuple)
    return Time

def get_time():  # เวลาปัจจุบัน
    named_tuple = time.localtime() # get struct_time
    Time = time.strftime("%H:%M:%S", named_tuple)
    return Time


##########################################
#Database
##########################################

def select_balance_id_desc_pair_only(pair):
    con = sqlite3.connect(database_name)
    cur = con.cursor()
    cur.execute("SELECT * FROM balance as b where b.underlying_name = ? order by b.id desc ",(pair,))
    result = cur.fetchone()
    con.close()
    return result

def select_balance_id_desc(pair,in_position):
    con = sqlite3.connect(database_name)
    cur = con.cursor()
    cur.execute("SELECT * FROM balance as b where b.underlying_name = ? and in_position = ? order by b.id desc ",(pair,in_position))
    result = cur.fetchone()
    con.close()
    return result    
    
def insert_balance(underlying_name,balance_left,in_position,date,balance_before,buy_price,sell_price,amount_buy_or_sell):
    con = sqlite3.connect(database_name)
    cur = con.cursor()
    
    cur.execute("INSERT INTO balance (underlying_name,balance_left,in_position,date,balance_before,buy_price,sell_price,amount_buy_or_sell) VALUES (?,?,?,?,?,?,?,?)",(underlying_name,balance_left,in_position,date,balance_before,buy_price,sell_price,amount_buy_or_sell))
    con.commit()
    con.close()

def insert_transaction(underlying_name,amount,buyorsell,date,order,strategy):
    con = sqlite3.connect(database_name)
    cur = con.cursor()

    cur.execute("INSERT INTO transaction_detail (underlying_name,amount,buyorsell,date,detail,strategy) VALUES (?,?,?,?,?,?) ",(underlying_name,amount,buyorsell,date,order,strategy))
    con.commit()
    con.close()

#End Database    

#Save Image
def saveImage(df,symbol,only_date):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                vertical_spacing=0.10, subplot_titles=(symbol, 'Volume'), 
                row_width=[0.2, 0.7])

    fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"],
                    low=df["Low"], close=df["Adj Close"], name="OHLC"), 
                    row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["EMA_12"], marker_color='grey',name="EMA12"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["EMA_26"], marker_color='lightgrey',name="EMA26"), row=1, col=1)

    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color='red', showlegend=False), row=2, col=1)

    fig.update_layout(
        title=symbol+' historical price chart',
        xaxis_tickfont_size=12,
        yaxis=dict(
            title='Price',
            titlefont_size=14,
            tickfont_size=12,
        ),
        autosize=False,
        width=800,
        height=500,
        margin=dict(l=50, r=50, b=100, t=100, pad=4),
        paper_bgcolor='LightSteelBlue'
    )

    pic_save_name = symbol.replace('/','_')+only_date
    fig.update(layout_xaxis_rangeslider_visible=False)
    fig.write_image("images_us/"+pic_save_name+".jpg")
    # fig.show(renderer="png")
    # msg = '-- Buy Signal --, TimeFrame: '+timeframe+', Strategy: '+strategy+', Timing : '+get_date_time()+', underlying_to_trade : '+ symbol 
    # r = requests.post(url_line, headers=headers, data = {'message':msg})

#End Save

#Stratergy
def my_strategy2(df):
    if (df.EMA_12 > df.EMA_26) :
        return True
    else :
        return False


#Save Port Image

#End Save Port Image

only_date = get_date()
date_save = get_date_time()
# print(get_date_time())
print(f"Fetching new bars for -> {datetime.now().isoformat()}")
# bars = exchange.fetch_ohlcv('ETH/USDT', timeframe=timeframe, limit=limit_data_lookback)
# print(len(bars))            

try:
    #Get Data
    # balance = exchange.fetch_balance()
    # ticker = exchange.fetch_ticker(underlying_to_trade)
    msg = 'API Yfinance Working -- Normal --, Timing : '+get_date_time()
    # r = requests.post(url_line, headers=headers, data = {'message':msg})
    # print (r.text)
except:
    msg = 'API Yfinance --- ERROR ---, Timing : '+get_date_time()
    # r = requests.post(url_line, headers=headers, data = {'message':msg})
    # print (r.text)
    canContinue = False

##########################################
#Start Run Bot
##########################################


symbol = 'AAPL'

buy_signal_symbols = []
sell_signal_symbols = []
no_signal_symbols =[]


bars = yf.download(symbol,start=str_start_date_port,end=str_end_date)
df = pd.DataFrame(bars[:-1])
# print(df)

#Insert TA
# rsi = ta.rsi(df['Adj Close'],length=14)
# print(rsi)
df['RSI_14'] = ta.rsi(df['Adj Close'],length=14)
df['EMA_12'] = ta.ema(df['Adj Close'],length=12)
df['EMA_26'] = ta.ema(df['Adj Close'],length=26)
print(df)
supertrend = ta.supertrend(df['High'],df['Low'],df['Adj Close'])
print(supertrend)

df = pd.merge(left=df, right=supertrend, left_on='Date', right_on='Date')
print("////////Testing///////////")
print(df)


saveImage(df,symbol,only_date)

df['signal'] = df.apply(my_strategy2,axis=1).vbt.fshift(1)
df = df.iloc[1:,:]
signal_vectorbt = df.ta.tsignals(df.signal, asbool=True, append=True)
port = vbt.Portfolio.from_signals(df['Adj Close'],
                            entries = signal_vectorbt.TS_Entries,
                            exits = signal_vectorbt.TS_Exits,
                            init_cash = 100000,
                            fees = 0.0025,
                            slippage = 0.0025)

port.plot().write_image('images_us_port/'+symbol.replace('/','_')+only_date+'.jpg')



print('////////////////////////Running '+strategy+' , since '+get_date_time()+'////////////////////////')




