import yfinance as yf
import sqlite3
import config
import pandas as pd
import numpy as np
from datetime import datetime,timedelta
import time
import pandas_ta as ta
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
limit_data_lookback = 150
limit_data_lookback_port = 1000
initial_money = 100
trade_money = initial_money #if first order use initial_money otherwise use comulative_money
database_name = 'traderecord.db'
strategy = 'SUPERTREND'






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

    fig.add_trace(go.Scatter(x=df.index, y=df["SUPERT_7_3.0"], marker_color='red',name="SUPERTREND"), row=1, col=1)
    
    # fig.add_trace(go.Scatter(x=df.index, y=df["EMA_12"], marker_color='grey',name="EMA12"), row=1, col=1)
    # fig.add_trace(go.Scatter(x=df.index, y=df["EMA_26"], marker_color='lightgrey',name="EMA26"), row=1, col=1)

    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color='red', showlegend=False), row=2, col=1)

    fig.update_layout(
        title=symbol+' historical price chart',
        xaxis_tickfont_size=12,
        yaxis=dict(
            title='Price',
            titlefont_size=14,
            tickfont_size=12,
        ),
        autosize=True,
        width=1200,
        height=800,
        margin=dict(l=50, r=50, b=100, t=100, pad=4),
        paper_bgcolor='LightSteelBlue'
    )

    fig.update_layout(yaxis_range=[df.min()['Low']*0.95,df.max()['High']*1.05])

    pic_save_name = symbol.replace('/','_')+only_date
    fig.update(layout_xaxis_rangeslider_visible=False)
    fig.write_image("images_us/"+pic_save_name+".jpg")
    # fig.show(renderer="png")
    # msg = '-- Buy Signal --, TimeFrame: '+timeframe+', Strategy: '+strategy+', Timing : '+get_date_time()+', underlying_to_trade : '+ symbol 
    # r = requests.post(url_line, headers=headers, data = {'message':msg})

#End Save

#Stratergy
def my_strategy2(df):
    if (df['Adj Close'] > df['SUPERT_7_3.0']) :
        return True
    else :
        return False


#Save Port Image

#End Save Port Image

only_date = get_date()
date_save = get_date_time()
print(get_date_time())
print(f"Fetching new bars for -> {datetime.now().isoformat()}")

str_end_date = datetime.now().strftime('%Y-%m-%d')
# print("////////Testing///////////")
# print(str_end_date)

str_start_date = (datetime.now()- timedelta(days=limit_data_lookback)).strftime('%Y-%m-%d')
# print("////////Testing///////////")
# print(str_start_date)

str_start_date_port = (datetime.now()- timedelta(days=limit_data_lookback_port)).strftime('%Y-%m-%d')
# print("////////Testing///////////")
# print(str_start_date_port)

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

all_symbols_df = pd.read_csv('nasdaq.csv')
print(all_symbols_df)



buy_signal_symbols = []
sell_signal_symbols = []
no_signal_symbols =[]

# for index, row in all_symbols_df.iterrows():
#     print(row['symbol'])

# def run_bot():
    # print('len symbol -->')
    # print(len(exchange.symbols))
   
for index, row in all_symbols_df.iterrows():
    # print(row['symbol'])
    symbol = row['Symbol']
    marketCap = row['Market Cap']
    # if(marketCap<1000000*10000):
    #     continue
    # if(index<400):
    #     continue
    # if symbol.lower().find("eth/usdt") >=0  :
    if ((symbol.lower().find("/")) >=0 or (symbol.lower().find("^"))) >=0:
        continue

    date_save = get_date_time()
    print('symbol in loop: '+symbol+' , dateTime = '+date_save)
    
    global bars
    try:
        #Get Data
        # balance = exchange.fetch_balance()
        # ticker = exchange.fetch_ticker(underlying_to_trade)
        # bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit_data_lookback)
        
        bars = yf.download(symbol,start=str_start_date,end=str_end_date)
        msg = 'API Yfinance Working -- Normal --, Timing : '+get_date_time()
        # r = requests.post(url_line, headers=headers, data = {'message':msg})
        # print (r.text)
    except:
        msg = 'API Yfinance --- ERROR ---, Timing : '+get_date_time()+', Symbol :'+symbol
        r = requests.post(url_line, headers=headers, data = {'message':msg})
        # print (r.text)
        canContinue = False
    
    if(len(bars)<27):
        continue
    df = pd.DataFrame(bars[:-1])
    



    #Insert TA
    # rsi = ta.rsi(df['Adj Close'],length=14)
    # print(rsi)
    df['RSI_14'] = ta.rsi(df['Adj Close'],length=14)
    df['EMA_12'] = ta.ema(df['Adj Close'],length=12)
    df['EMA_26'] = ta.ema(df['Adj Close'],length=26)
    # print(df)
    supertrend = ta.supertrend(df['High'],df['Low'],df['Adj Close'])
    # print(supertrend)

    df = pd.merge(left=df, right=supertrend, left_on='Date', right_on='Date')
    # print("////////Testing///////////")
    # print(df)

    
    if((df.iloc[-1]['Adj Close']>df.iloc[-1]['SUPERT_7_3.0'])&(df.iloc[-2]['Adj Close']<df.iloc[-2]['SUPERT_7_3.0'])):
        
        #BUY ACTION
        buyHoldSellSignal = 1
        buy_signal_symbols.append(symbol)

        saveImage(df,symbol,only_date)
    
        msg = '-- Buy Signal -- \n'+'TimeFrame: '+timeframe+'\n'+'Strategy: '+strategy+'\n'+'Timing : '+get_date_time()+'\n'+'Pair : '+ symbol 
        r = requests.post(url_line, headers=headers, data = {'message':msg})

        msg = symbol
        file = {'imageFile':open('images_us/'+symbol.replace('/','_')+only_date+'.jpg','rb')}
        r = requests.post(url_line, headers=headers,data = {'message':msg},files=file)

        #Port query more data
        bars = yf.download(symbol,start=str_start_date_port,end=str_end_date)
        df = pd.DataFrame(bars[:-1])

        #Insert TA
        # rsi = ta.rsi(df['Adj Close'],length=14)
        # print(rsi)
        df['RSI_14'] = ta.rsi(df['Adj Close'],length=14)
        df['EMA_12'] = ta.ema(df['Adj Close'],length=12)
        df['EMA_26'] = ta.ema(df['Adj Close'],length=26)
        # print(df)
        supertrend = ta.supertrend(df['High'],df['Low'],df['Adj Close'])
        # print(supertrend)

        df = pd.merge(left=df, right=supertrend, left_on='Date', right_on='Date')
        
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
        file = {'imageFile':open('images_us_port/'+symbol.replace('/','_')+only_date+'.jpg','rb')}
        r = requests.post(url_line, headers=headers,data = {'message':msg},files=file)


    elif((df.iloc[-1]['Adj Close']<df.iloc[-1]['SUPERT_7_3.0'])&(df.iloc[-2]['Adj Close']>df.iloc[-2]['SUPERT_7_3.0'])):
        buyHoldSellSignal = -1
        
        #Send Notification Discord / Line
        sell_signal_symbols.append(symbol)
        
        saveImage(df,symbol,only_date)
    
        msg = '-- Sell Signal -- \n'+'TimeFrame: '+timeframe+'\n'+'Strategy: '+strategy+'\n'+'Timing : '+get_date_time()+'\n'+'Pair : '+ symbol 
        r = requests.post(url_line, headers=headers, data = {'message':msg})

        msg = symbol
        file = {'imageFile':open('images_us/'+symbol.replace('/','_')+only_date+'.jpg','rb')}
        r = requests.post(url_line, headers=headers,data = {'message':msg},files=file)




    else:
        buyHoldSellSignal = 0
        no_signal_symbols.append(symbol)
        #Send Notification Discord / Line
        # msg = '-- No Order --, Timing : '+get_date_time()+', underlying_to_trade : '+ underlying_to_trade
        # r = requests.post(url_line, headers=headers, data = {'message':msg})
    
##########################################
#End Run Bot
##########################################



print('////////////////////////Running '+strategy+' , since '+get_date_time()+'////////////////////////')




