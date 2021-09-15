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

exchange = ccxt.binance({
    
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
strategy = 'supertrend'


### LINE NOTI
token_line = 'yNkEnMNx8rshijO0SQpexZgzCICkKOW7JhfFpVC8Yz0'
headers = {'content-type':'application/x-www-form-urlencoded','Authorization':'Bearer '+token_line}
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

date_save = get_date_time()
print(get_date_time())
print(f"Fetching new bars for -> {datetime.now().isoformat()}")
# bars = exchange.fetch_ohlcv('ETH/USDT', timeframe=timeframe, limit=limit_data_lookback)
# print(len(bars))            

try:
    #Get Data
    # balance = exchange.fetch_balance()
    # ticker = exchange.fetch_ticker(underlying_to_trade)
    msg = 'API Binance Working -- Normal --, Timing : '+get_date_time()
    # r = requests.post(url_line, headers=headers, data = {'message':msg})
    # print (r.text)
except:
    msg = 'API Binance --- ERROR ---, Timing : '+get_date_time()
    # r = requests.post(url_line, headers=headers, data = {'message':msg})
    # print (r.text)
    canContinue = False

##########################################
#Start Run Bot
##########################################

# def run_bot():
    # print('len symbol -->')
    # print(len(exchange.symbols))



all_symbols_df = pd.read_csv('symbol_binance.csv')
print(all_symbols_df)

'''
for symbol in exchange.symbols or []:
    
    
    if symbol.lower().find("eth/usdt") >0  :
        print('symbol -> '+symbol)
    # if ((symbol.lower().find("usdt")) >=0 or (symbol.lower().find("busd"))) >=0:
        date_save = get_date_time()
        print('symbol in loop: '+symbol+' , dateTime = '+date_save)
        
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit_data_lookback)
        df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp',inplace = True)

        #Insert TA
        df.ta.rsi(length=14,append=True)
        df.ta.ema(length=12,append=True)
        df.ta.ema(length=26,append=True)
        df.ta.supertrend(append=True)
        # print(df.tail(30))




        # print(balance)
        # print('///////////////////////')
        # print(balance['total']['USDT'])
        # print('///////////////////////')
        # print(df.reset_index().iloc[-1])




        if((df.iloc[-1]['close']>df.iloc[-1]['SUPERT_7_3.0'])&(df.iloc[-2]['close']<df.iloc[-2]['SUPERT_7_3.0'])):
            
            #BUY ACTION
            buyHoldSellSignal = 1

            msg = '-- Buy Signal --, TimeFrame: '+timeframe+', Strategy: '+strategy+', Timing : '+get_date_time()+', underlying_to_trade : '+ symbol 
            r = requests.post(url_line, headers=headers, data = {'message':msg})


        elif((df.iloc[-1]['close']<df.iloc[-1]['SUPERT_7_3.0'])&(df.iloc[-2]['close']>df.iloc[-2]['SUPERT_7_3.0'])):
            buyHoldSellSignal = -1
            
            #Send Notification Discord / Line
            msg = '-- Sell Signal --, TimeFrame: '+timeframe+', Strategy: '+strategy+', Timing : '+get_date_time()+', underlying_to_trade : '+ symbol 
            r = requests.post(url_line, headers=headers, data = {'message':msg})




        else:
            buyHoldSellSignal = 0
            #Send Notification Discord / Line
            msg = '-- No Order --, Timing : '+get_date_time()+', underlying_to_trade : '+ symbol
            r = requests.post(url_line, headers=headers, data = {'message':msg})
    
##########################################
#End Run Bot
##########################################

'''

# select_demo()
print('////////////////////////Running '+strategy+' , since '+get_date_time()+'////////////////////////')


# insert_transaction(underlying_to_trade,1,'buy','2021-10-09','order_detail','supertrend')
# insert_balance(underlying_to_trade,1.11122,'True','2021-10-20',1,2.01,0,1)
   






##########################################
#send_line_noti
##########################################
# msg = 'Hello LINE Notify'
# r = requests.post(url_line, headers=headers, data = {'message':msg})
# print (r.text)



##########################################
#run_bot
##########################################
 
# def run_bot():
#     print('run bot---> ')
# schedule.every().day().at("08:00").do(run_bot)
# schedule.every().day.at("08:30").do(run_bot)
