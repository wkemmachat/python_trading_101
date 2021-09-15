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
    "apiKey": config.BINANCE_API_KEY,
    "secret": config.BINANCE_API_SECRET,
    'enableRateLimit': True
})
#Set Testnet
# exchange.set_sandbox_mode(True)

############################################
#Must Edit
############################################
underlying_to_trade = 'ETH/USDT'
pair = underlying_to_trade
timeframe = '1m'
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


try:
    #Get Data
    balance = exchange.fetch_balance()
    ticker = exchange.fetch_ticker(underlying_to_trade)
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

def run_bot():

    date_save = get_date_time()
    bars = exchange.fetch_ohlcv(underlying_to_trade, timeframe=timeframe, limit=limit_data_lookback)
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

        #use Initial money or get the money that accumulate by get the p&l from database
        #if no database use initial_money otherwise use money from database
        result = select_balance_id_desc_pair_only(underlying_to_trade)
        in_position = 'false'
        

        if result is None:
            #use initail_money
            #do nothing
            trade_money = initial_money
            print(f"use initial money ->  {initial_money}")
        else:
            #use cumulative_money
            trade_money = result[2]
            in_position = result[3]
            print(f"type trade_money ->  {result[2]}")


        if in_position.lower()=='false':

            #Get Amount buy get the quote
            askPrice = float(ticker['ask'])
            amountToBuy = round(trade_money/askPrice*0.99,4)
            # print(amountToBuy)
            
            params = {
                'test': True,  # test if it's valid, but don't actually place it
            }

            ####################################
            #Action market buy
            ####################################
            
            order = exchange.create_order(underlying_to_trade,'market','buy',amountToBuy)
            time.sleep(2)
            # order_price = float(order['fills'][0]['price']) # there are many price but select only one first
            order_price = order['price']
            if order_price is None:
                order_price = order['average']
            if order_price is None:
                cumulative_quote = float(order['info']['cumQuote'])
                executed_quantity = float(order['info']['executedQty'])
                order_price = cumulative_quote / executed_quantity

            # print(order)
            #Save Database
            # insert Transaction
            
            insert_transaction(underlying_to_trade,amountToBuy,'buy',date_save,order,strategy)
            insert_balance(underlying_to_trade,(trade_money-order_price*amountToBuy),'True',date_save,trade_money,order_price,0,amountToBuy)
            

            #Test Database 
            # insert_transaction(underlying_to_trade,amountToBuy,'buy',date_save,'order_detail',strategy)
            # insert_balance(underlying_to_trade,(trade_money-askPrice*amountToBuy),'True',date_save,trade_money,askPrice,0,amountToBuy)
            

            #Send Notification Discord / Line
            msg = '-- Buy Order --, Timing : '+get_date_time()+', underlying_to_trade : '+ underlying_to_trade +' , trade_money: '+str(trade_money)+', askPrice : '+str(askPrice)+ ' , amountToBuy: '+str(amountToBuy)
            r = requests.post(url_line, headers=headers, data = {'message':msg})


    elif((df.iloc[-1]['close']<df.iloc[-1]['SUPERT_7_3.0'])&(df.iloc[-2]['close']>df.iloc[-2]['SUPERT_7_3.0'])):
        buyHoldSellSignal = -1
        
        in_position = 'false'
        # amount to sell get from data base
        
        result = select_balance_id_desc_pair_only(pair) 
        if result is None:
            # Do nothing
            print('No result')
        else:
            in_position = result[3]   
            balance_before = result[2]
            buy_price_before = result[6]

            if in_position.lower()=='true':
                #Sell order
                amountToSell =  result[8]
                bidPrice = float(ticker['bid'])
                
                ####################################
                #Action market Sell
                ####################################
                
                order = exchange.create_order(underlying_to_trade,'market','sell',amountToSell)
                time.sleep(2)
                order_price = order['price']
                if order_price is None:
                    order_price = order['average']
                if order_price is None:
                    cumulative_quote = float(order['info']['cumQuote'])
                    executed_quantity = float(order['info']['executedQty'])
                    order_price = cumulative_quote / executed_quantity
                # print(order)
                #Save Database
                # insert Transaction
                
                p_and_l = (order_price-buy_price_before)*amountToSell

                insert_transaction(underlying_to_trade,amountToSell,'sell',date_save,order,strategy)
                insert_balance(underlying_to_trade,(balance_before+amountToSell*order_price),'False',date_save,balance_before,0,order_price,amountToSell)
                

                #Test Database 
                p_and_l = (bidPrice-buy_price_before)*amountToSell
                # insert_transaction(underlying_to_trade,amountToSell,'sell',date_save,'order_detail',strategy)
                # insert_balance(underlying_to_trade,(balance_before+amountToSell*bidPrice),'False',date_save,balance_before,0,bidPrice,amountToSell)
                
                #Send Notification Discord / Line
                msg = '-- Sell Order --, Timing : '+get_date_time()+', underlying_to_trade : '+ underlying_to_trade +' , bidPrice : '+str(bidPrice)+ ' , amountToSell: '+str(amountToSell)
                r = requests.post(url_line, headers=headers, data = {'message':msg})




    else:
        buyHoldSellSignal = 0
        #Send Notification Discord / Line
        # msg = '-- No Order --, Timing : '+get_date_time()+', underlying_to_trade : '+ underlying_to_trade
        # r = requests.post(url_line, headers=headers, data = {'message':msg})

##########################################
#End Run Bot
##########################################

# print(balance['total']['USDT']/float(ticker['close']))
# print(round(balance['total']['USDT']/float(ticker['close']),4))

# amountToBuy = round(initial_money/float(ticker['ask'])*0.99,4)
# print('//////////////////')
# print(amountToBuy)



# print(ticker['close'])
# print(ticker['bid'])
# print(ticker['ask'])

# select_demo()
print("////////////////////////testing////////////////////////")


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
schedule.every(60).seconds.do(run_bot)
while True:
    schedule.run_pending()
    time.sleep(1)