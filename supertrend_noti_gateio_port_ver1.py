import ccxt
import sqlite3
import config
import pandas as pd
import numpy as np
from datetime import datetime
import time
import pandas_ta as ta
from datetime import datetime
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

exchange = ccxt.gateio({
    'enableRateLimit': True,  # required: https://github.com/ccxt/ccxt/wiki/Manual#rate-limit
})
#Set Testnet
# exchange.set_sandbox_mode(True)

############################################
#Must Edit
############################################
# underlying_to_trade = 'ETH/USDT'
# pair = underlying_to_trade
timeframe = '1d'
limit_data_lookback = 100
initial_money = 100
trade_money = initial_money #if first order use initial_money otherwise use comulative_money
database_name = 'traderecord.db'
strategy = 'SUPERTREND'


### LINE NOTI
token_line = '78tRVvP3UmqYkmfm8LRMG6wWtlBJfwyOFuMzrfloMD9'
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

def get_last_trade_price(pair):
    pair = pair
    trade_history = pd.DataFrame(exchange.fetchMyTrades(pair, limit = 1),
                            columns=['id', 'timestamp', 'datetime', 'symbol', 'side', 'price', 'amount', 'cost', 'fee'])
    last_trade_price = trade_history['price']
    
    return float(last_trade_price)
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
                vertical_spacing=0.10, subplot_titles=(symbol, 'volume'), 
                row_width=[0.2, 0.7])

    fig.add_trace(go.Candlestick(x=df.index, open=df["open"], high=df["high"],
                    low=df["low"], close=df["close"], name="OHLC"), 
                    row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["SUPERT_7_3.0"], marker_color='red',name="SUPERTREND"), row=1, col=1)
    # fig.add_trace(go.Scatter(x=df.index, y=df["EMA_26"], marker_color='lightgrey',name="EMA26"), row=1, col=1)

    fig.add_trace(go.Bar(x=df.index, y=df['volume'], marker_color='red', showlegend=False), row=2, col=1)

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
    fig.write_image("images/"+pic_save_name+".jpg")
    # fig.show(renderer="png")
    # msg = '-- Buy Signal --, TimeFrame: '+timeframe+', Strategy: '+strategy+', Timing : '+get_date_time()+', underlying_to_trade : '+ symbol 
    # r = requests.post(url_line, headers=headers, data = {'message':msg})

#End Save

#Stratergy
def my_strategy2(df):
    if (df['close'] > df['SUPERT_7_3.0']) :
        return True
    else :
        return False


#Save Port Image

#End Save Port Image

only_date = get_date()
date_save = get_date_time()
print(get_date_time())
print(f"Fetching new bars for -> {datetime.now().isoformat()}")
# bars = exchange.fetch_ohlcv('ETH/USDT', timeframe=timeframe, limit=limit_data_lookback)
# print(len(bars))            

try:
    #Get Data
    # balance = exchange.fetch_balance()
    # ticker = exchange.fetch_ticker(underlying_to_trade)
    msg = 'API GATE IO Working -- Normal --, Timing : '+get_date_time()
    # r = requests.post(url_line, headers=headers, data = {'message':msg})
    # print (r.text)
except:
    msg = 'API GATE IO --- ERROR ---, Timing : '+get_date_time()
    # r = requests.post(url_line, headers=headers, data = {'message':msg})
    # print (r.text)
    canContinue = False

##########################################
#Start Run Bot
##########################################

all_symbols_df = pd.read_csv('symbol_gateio.csv')
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
    symbol = row['symbol']
    
    
    # if(index>1):
    #     continue
    # if symbol.lower().find("eth/usdt") >=0  :
    if ((symbol.lower().find("usd")) ==0 or (symbol.lower().find("busd"))) ==0:
        continue

    date_save = get_date_time()
    print('symbol in loop: '+symbol+' , dateTime = '+date_save)
    
    global bars
    try:
        #Get Data
        # balance = exchange.fetch_balance()
        # ticker = exchange.fetch_ticker(underlying_to_trade)
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit_data_lookback)
    
        msg = 'API Gate IO Working -- Normal --, Timing : '+get_date_time()
        # r = requests.post(url_line, headers=headers, data = {'message':msg})
        # print (r.text)
    except:
        msg = 'API Gate IO --- ERROR ---, Timing : '+get_date_time()+', Symbol :'+symbol
        r = requests.post(url_line, headers=headers, data = {'message':msg})
        # print (r.text)
        canContinue = False
    
    if(len(bars)<27):
        continue
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp',inplace = True)

    #Insert TA
    df.ta.rsi(length=14,append=True)
    df.ta.ema(length=12,append=True)
    df.ta.ema(length=26,append=True)
    df.ta.supertrend(append=True)
    # print(df.tail(30))

    
    if((df.iloc[-1]['close']>df.iloc[-1]['SUPERT_7_3.0'])&(df.iloc[-2]['close']<df.iloc[-2]['SUPERT_7_3.0'])):
        
        #BUY ACTION
        buyHoldSellSignal = 1
        buy_signal_symbols.append(symbol)

        saveImage(df,symbol,only_date)
    
        msg = '-- Buy Signal -- \n'+'TimeFrame: '+timeframe+'\n'+'Strategy: '+strategy+'\n'+'Timing : '+get_date_time()+'\n'+'Pair : '+ symbol 
        r = requests.post(url_line, headers=headers, data = {'message':msg})

        msg = symbol
        file = {'imageFile':open('images/'+symbol.replace('/','_')+only_date+'.jpg','rb')}
        r = requests.post(url_line, headers=headers,data = {'message':msg},files=file)

        #Port
        try:
            bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=1000)
            df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp',inplace = True)

            #Insert TA
            df.ta.rsi(length=14,append=True)
            df.ta.ema(length=12,append=True)
            df.ta.ema(length=26,append=True)
            df.ta.supertrend(append=True)

            df['signal'] = df.apply(my_strategy2,axis=1).vbt.fshift(1)
            df = df.iloc[1:,:]
            signal_vectorbt = df.ta.tsignals(df.signal, asbool=True, append=True)
            port = vbt.Portfolio.from_signals(df.close,
                                    entries = signal_vectorbt.TS_Entries,
                                    exits = signal_vectorbt.TS_Exits,
                                    init_cash = 100000,
                                    fees = 0.0025,
                                    slippage = 0.0025)

            port.plot().write_image('images_port/'+symbol.replace('/','_')+only_date+'.jpg')
            file = {'imageFile':open('images_port/'+symbol.replace('/','_')+only_date+'.jpg','rb')}
            r = requests.post(url_line, headers=headers,data = {'message':msg},files=file)

        except:
            msg = 'API Gate IO --- ERROR ---, Timing : '+get_date_time()+', symbol :'+symbol
            r = requests.post(url_line, headers=headers, data = {'message':msg})



    elif((df.iloc[-1]['close']<df.iloc[-1]['SUPERT_7_3.0'])&(df.iloc[-2]['close']>df.iloc[-2]['SUPERT_7_3.0'])):
        buyHoldSellSignal = -1
        
        #Send Notification Discord / Line
        sell_signal_symbols.append(symbol)
        
        saveImage(df,symbol,only_date)
    
        msg = '-- Sell Signal -- \n'+'TimeFrame: '+timeframe+'\n'+'Strategy: '+strategy+'\n'+'Timing : '+get_date_time()+'\n'+'Pair : '+ symbol 
        r = requests.post(url_line, headers=headers, data = {'message':msg})

        msg = symbol
        file = {'imageFile':open('images/'+symbol.replace('/','_')+only_date+'.jpg','rb')}
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




