import itertools
import time
from datetime import datetime
import uuid
import winsound
import traceback
import multiprocessing
from functools import partial
import random
import sqlite3
import pickle

import bitfinex
import kraken #Shorting ok
import theRock #Shorting ok
import GDAX # Shorting disabled server side until further notice
import bitstamp #Shorting coming soon
import bl3p
import cexapi
import wex
import bitbay
import quoinex

import Keys

###############################################################################

# Set all these to True to run in a completely contained offline environment

Jumpstart_Script = True # Conntinues script from where left off if True
Startup_Script = False # Sells all the crypto back into fiat for trading
Shutdown_Script = False # Sells all the fiat back into cryto for hodling
Test_Mode = False  #### If set to false will place real orders on exchanges!
Limit_Qty = True  #### Limits to the minimum order qty for test purposes
Fake_MOQs = False #### Use real or fake MOQs
Fake_Balances = False #### Use real or fake balances
Fake_Prices = False   #### Use real or fake prices
Fake_Fees = False  #### Use real or fake fees
Multi_Processing = True #### Mulit-Processing runs quicker but harder to de-bug
Place_Concurrent_Orders = True ## Simple executes both trades one after another
Limit_Arbitrages = False ## Limits the number of arbitrages to one for testing.

iteration = 1 # starts the main loop counter, only used for fake prices

if Jumpstart_Script is False:

    Bitfinex = {'Name': 'Bitfinex', 'Shorting': True, 'Switched-On': True} # Can Short
    Kraken = {'Name': 'Kraken', 'Shorting': True, 'Switched-On': True} # advanced order currently disabled 20/01/18
    Bitstamp = {'Name': 'Bitstamp', 'Shorting': False, 'Switched-On': True}
    Gdax = {'Name': 'Gdax', 'Shorting': False, 'Switched-On': False}
    Bl3p = {'Name': 'Bl3p', 'Shorting': False, 'Switched-On': True}
    TheRock = {'Name': 'theRock', 'Shorting': False, 'Switched-On': True}
    Cex = {'Name': 'Cex', 'Shorting': True, 'Switched-On': True} # can short
    Wex = {'Name': 'Wex', 'Shorting': False, 'Switched-On': True}
    BitBay = {'Name': 'BitBay', 'Shorting': False, 'Switched-On': True}
    Quoinex = {'Name': 'Quoinex', 'Shorting': True, 'Switched-On': True} # Can Short

    Exchanges = [Bitfinex, Kraken, Bitstamp, Gdax, Bl3p, TheRock, Cex, Wex, BitBay, Quoinex]  


Min_Bal = 10.00 # Min Balance to execute on
liquid_factor = 2.0 # multiplied by trade amount, determine if adequate liquidity

Attempts = 5 # re-tries for server
Attempts += 1 # add 1 to actually execute a number of attempts due tp range function behviour


Coins = ['BTC', 'LTC', 'ETH']
Fiat = ['EUR']

###############################################################################



###############################################################################

def Bitfinex_Private_Client():
    
    Key = Keys.Bitfinex()
    client = bitfinex.api.Client(Key['key'], Key['secret'])
    return client
    
def Bitfinex_Orderbook(Coin):
    
    pair = Coin.lower() + Fiat[0].lower()
    
    Orderbook = Bitfinex_Private_Client().get_orderbook(pair)
    
    Asks = [[float(i['price']), float(i['amount'])] for i in Orderbook['asks']]
    Bids = [[float(i['price']), float(i['amount'])] for i in Orderbook['bids']]
    
    return (Asks, Bids)

def Bitfinex_Fees():
        
    fees = Bitfinex_Private_Client().get_fees()[0]
    
    time.sleep(5)
    
    return {'buy_fee': float(fees['taker_fees']),
            'sell_fee': float(fees['taker_fees']),
            'buy_maker_fee': float(fees['maker_fees']),
            'sell_maker_fee': float(fees['maker_fees']),
            'currency': 'crypto'}
        
def Bitfinex_MOQ():
    
    MOQ_Long = {}
    MOQ_Short = {}
    
    for attempt in range(1, Attempts):
        try:
            
            MOQs = Bitfinex_Private_Client().get_moqs()
            
            for Coin in Coins:
                pair = Coin.lower() + Fiat[0].lower() 
                
                for MOQ in MOQs:
                    if MOQ['pair'] == pair:
                        MOQ_Long.update({Coin: float(MOQ['minimum_order_size'])})
                        MOQ_Short.update({Coin: float(MOQ['minimum_order_size'])})
                    else:
                        continue
                
        except:
            'Failed to get Bitfinex MOQs on Attempt: %s' % attempt
            continue
        else:
            return {'Long': MOQ_Long, 'Short': MOQ_Short}

    else:
        MOQ_Long = {}
        MOQ_Short = {}
        
        for Coin in Coins:
            MOQ_Long.update({Coin: 0.002})
            MOQ_Short.update({Coin: 0.002})
            
        return {'Long': MOQ_Long, 'Short': MOQ_Short}
            
    
def Bitfinex_Wallet_Transfer(side):
    
    client = Bitfinex_Private_Client()

#    Amount = '%.8f' % (amount*price)
    
    balances = Bitfinex_Private_Client().get_balances()
    
    for balance in balances:
        if balance['currency'] == Fiat[0].lower() and balance['type'] == 'exchange':
            fiat_balance_exchange = float(balance['available'])
        if balance['currency'] == Fiat[0].lower() and balance['type'] == 'trading':
            fiat_balance_margin =  float(balance['available'])
        
    if side == 'buy':
        
        Amount = fiat_balance_margin
        
        if Amount > 0:
            print 'Transferring %s %s from %s wallet to %s Wallet' %(Amount, Fiat[0], 'Margin', 'Exchange')
            log.write('Transferring %s %s from %s wallet to %s Wallet' %(Amount, Fiat[0], 'Margin', 'Exchange'))
            transfer = client.wallet_transfer('%.8f' %Amount, Fiat[0], 'margin', 'exchange')
            print str(transfer)
            log.write('\n' + str(transfer))
            time.sleep(5)

    elif side == 'sell':
        
        Amount = fiat_balance_exchange
        
        if Amount > 0:
            print 'Transferring %s %s from %s wallet to %s Wallet' %(Amount, Fiat[0], 'Exchange', 'Margin')
            log.write('Transferring %s %s from %s wallet to %s Wallet' %(Amount, Fiat[0], 'Exchange', 'Margin'))
            transfer = client.wallet_transfer('%.8f' %Amount, Fiat[0], 'exchange', 'margin')
            print str(transfer)
            log.write('\n' + str(transfer))
            time.sleep(5)


def Bitfinex_Balances(Coin):
    
    balances = Bitfinex_Private_Client().get_balances()
        
    coin_balance = 0.0
    for balance in balances:
        if balance['currency'] == Coin.lower() and balance['type'] == 'exchange':
            coin_balance += float(balance['available'])
        if balance['currency'] == Coin.lower() and balance['type'] == 'trading':
            coin_balance += float(balance['available'])
            
    fiat_balance = 0.0
    for balance in balances:
        if balance['currency'] == Fiat[0].lower() and balance['type'] == 'exchange':
            fiat_balance += float(balance['available'])
        if balance['currency'] == Fiat[0].lower() and balance['type'] == 'trading':
            fiat_balance += float(balance['available'])
            
    time.sleep(5)
    return {Coin: coin_balance, Fiat[0]: fiat_balance}    
    
def Bitfinex_Limit_Order(Coin, amount, side, price, leverage):
    
    Bitfinex_Wallet_Transfer(side)
            
    pair = Coin.lower() + Fiat[0].lower()
    
    time.sleep(5)
    
    Order = Bitfinex_Private_Client().limit_order(pair, amount, side, price, leverage)  

    print 'Message from Bitfinex: ' + str(Order)
    log.write('\nMessage from Bitfinex: ' + str(Order)) 
    
    return Order
        
def Bitfinex_Market_Order(Coin, amount, side, leverage):
            
    Bitfinex_Wallet_Transfer(side)
    
    pair = Coin.lower() + Fiat[0].lower()
    
    if side == 'buy':
            price = Bitfinex['Prices'][Coin]['entry_buy'] * 1+0.00005
    elif side == 'sell':
            price = Bitfinex['Prices'][Coin]['entry_sell'] * 1-0.00005
            
    time.sleep(5)
            
    Order = Bitfinex_Private_Client().market_order(pair, amount, side, price, leverage)  

        
    print 'Message from Bitfinex: ' + str(Order)
    log.write('\nMessage from Bitfinex: ' + str(Order)) 
    
    return Order
    
def Bitfinex_Check_Order(ref):
    
    Order = Bitfinex_Private_Client().order_status(ref)
    
    print 'Message from Bitfinex: ' + str(Order)
    log.write('\nMessage from Bitfinex: ' + str(Order)) 
    
    return Order

def Bitfinex_Filled(Order):
    
    Order_ID = Order['ID']
    
    isFilled = float(Bitfinex_Check_Order(Order_ID)['remaining_amount'])
    
    if  isFilled == 0.0:
        Filled = True
    else: Filled = False
    
    return Filled
    
def Bitfinex_Cancel_Order(ref):
    
    Order = Bitfinex_Private_Client().cancel_order(ref)
    
    time.sleep(5)    

    print 'Message from Bitfinex: ' + str(Order)
    log.write('\nMessage from Bitfinex: ' + str(Order))

    cancelled = Bitfinex_Check_Order(ref)['is_cancelled']
    
    return cancelled
        

###############################################################################


def Kraken_Private_Client():
    
    Key = Keys.Kraken()
    client = kraken.api.Client(key = Key['key'],secret = Key['secret'])
    return client
    
def Kraken_Fees():
    
    Coin = Coins[0]
    
    if Coins[0] == 'BTC':
        Coin = 'XBT'
    
    pair = 'X'+Coin+'Z'+Fiat[0]
    
    Client = kraken.api.Client()
    fees = Client.get_info(pair)['result'][pair]
    
    return {'buy_fee': float(fees['fees'][0][1]), 
            'sell_fee': float(fees['fees'][0][1]),
            'buy_maker_fee': float(fees['fees_maker'][0][1]),
            'sell_maker_fee': float(fees['fees_maker'][0][1]),
            'currency': 'crypto'}
            
def Kraken_MOQ():
    
    MOQ_Dict = {}

    for Coin in Coins:

        if Coin == 'BTC':
            MOQ = 0.002
        elif Coin == 'ETH':
            MOQ = 0.02
        elif Coin == 'LTC':
            MOQ = 0.1
        MOQ_Dict.update({Coin: MOQ})
    
    return {'Long': MOQ_Dict, 'Short': MOQ_Dict}  

    
         
def Kraken_Balances(Coin):
    
    if Coin == 'BTC':
        coin = 'XBT'
    else: coin = Coin
        
    balance = Kraken_Private_Client().get_balances()['result']
        
    Coin_Balance = round(float(balance['X'+coin]), 8)
    Fiat_Balance = round(float(balance['Z'+Fiat[0]]), 2)

    return {Coin: Coin_Balance, Fiat[0]: Fiat_Balance}
    
def Kraken_Limit_Order(Coin, amount, side, price, leverage):
                
    if Coin == 'BTC':
        coin = 'XBT'
    else: coin = Coin
    
    price = round(price, 1)
    
    pair = 'X'+coin+'Z'+Fiat[0]
    
    if leverage == 0:        
    
        params = {'pair': pair,
                  'type': side,
                  'ordertype': 'limit',
                  'price': str(price),
                  'volume': str(amount)} # 2 to 5 times
    else:
        
        params = {'pair': pair,
                  'type': side,
                  'ordertype': 'limit',
                  'price': str(price),
                  'volume': str(amount),
                  'leverage': str(leverage)} # 2 to 5 times  
    
    
    Order = Kraken_Private_Client().place_order(params)


    print 'Message from Kraken: ' + str(Order)
    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    return Order
    
def Kraken_Market_Order(Coin, amount, side, leverage):
            
    if Coin == 'BTC':
        coin = 'XBT'
    else: coin = Coin
    
    pair = 'X'+coin+'Z'+Fiat[0]
    
    if leverage == 0:        
    
        params = {'pair': pair,
                  'type': side,
                  'ordertype': 'market',
                  'volume': str(amount)}
    else:
        
        params = {'pair': pair,
                  'type': side,
                  'ordertype': 'market',
                  'volume': str(amount),
                  'leverage': str(leverage)} # 2 to 5 times
    
                    
    Order = Kraken_Private_Client().place_order(params)

            
    print 'Message from Kraken: ' + str(Order)
    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    return Order
    
def Kraken_Check_Order(ref):    
        
    Order = Kraken_Private_Client().query_order(ref)

    print 'Message from Kraken: ' + str(Order)
    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    return Order
    
  
def Kraken_Orderbook(Coin):
    
    if Coin == 'BTC':
        coin = 'XBT'
    else: coin = Coin
    
    pair = 'X'+coin+'Z'+Fiat[0]
        
    Orderbook = Kraken_Private_Client().get_orderbook(pair)['result'][pair]

    Asks = Orderbook['asks']    
    Bids = Orderbook['bids']
    
    return (Asks, Bids)
    
def Kraken_Open_Positions():
                
    Orders = Kraken_Private_Client().open_positions()
    
    print 'Message from Kraken: ' + str(Orders)
    log.write('\nMessage from Kraken: ' + str(Orders)) 
    
    if Orders['result']:
    
        return True
        
    else:
        return False
    
def Kraken_Filled(Order):
    
    Order_ID = Order['ID']
    
    if Order_ID != 'Kraken_Dummy_Order':
        
        isFilled = Kraken_Check_Order(Order_ID)['result'][Order_ID]['status']
        
        if str(isFilled) == 'closed':
            Filled = True
        else: Filled = False
        
        return Filled
    
    elif Order_ID == 'Kraken_Dummy_Order':
        
        Open_Positions = Kraken_Open_Positions()
        
        if Open_Positions:
            Filled = True
        else:
            Filled = False
            time.sleep(10)
            
        return Filled
    
def Kraken_Open_Orders():
                
    Orders = Kraken_Private_Client().open_orders()
    
    print 'Message from Kraken: ' + str(Orders)
    log.write('\nMessage from Kraken: ' + str(Orders)) 

    
    if Orders['result']['open']:
    
        return True
        
    else:
        return False
        
        
def Kraken_Cancel_Order(ref):
        
    Order = Kraken_Private_Client().cancel_order(ref)
    
    print 'Message from Kraken: ' + str(Order)
    log.write('\nMessage from Kraken: ' + str(Order))
    
    if Order['result']['count'] == 1:
        return True
    else:
        return False
    
###############################################################################

def Bitstamp_Private_Client():
    
    key = Keys.Bitstamp()   
    client = bitstamp.client.Trading(key['user'], key['key'], key['secret'])
    return client
    
def Bitstamp_Balances(Coin):
    
    pair = Coin.lower(), Fiat[0].lower()
    balance = Bitstamp_Private_Client().account_balance(pair[0], pair[1])
    
    Coin_Balance =  float(balance[Coin.lower() + '_balance'])
    Fiat_Balance =  float(balance[Fiat[0].lower() + '_balance'])

    return {Coin: Coin_Balance, Fiat[0]: Fiat_Balance}
    
def Bitstamp_MOQ():
    
    MOQ_Dict = {}
    for Coin in Coins:
        MOQ = 5.00 / Bitstamp['Prices'][Coin]['sell'] # MOQ is 5 USD / 5 EUR
        MOQ_Dict.update({Coin: MOQ})          

    return {'Long': MOQ_Dict, 'Short': MOQ_Dict}
    
def Bitstamp_Fees():
    
    pair = Coins[0].lower(), Fiat[0].lower()
    balance = Bitstamp_Private_Client().account_balance(pair[0], pair[1])
    
    fee = float(balance['fee'])
    
    return {'buy_fee': fee,
            'sell_fee': fee,
            'currency': 'fiat'}    
    
def Bitstamp_Limit_Order(Coin, amount, side, price):
    
    pair = (Coin.lower(), Fiat[0].lower())
    Amount = str(round(amount, 8))   
    Price = str(round(price, 2))
    
    Order = Bitstamp_Private_Client().limit_order(Amount, side, Price, pair[0], pair[1])  

    print 'Message from Bitstamp: ' + str(Order)
    log.write('\nMessage from Bitstamp: ' + str(Order)) 
    
    return Order
    
def Bitstamp_Market_Order(Coin, amount, side):
    
    pair = (Coin.lower(), Fiat[0].lower())
    Amount = str(round(amount, 8))   
    
    Order = Bitstamp_Private_Client().market_order(Amount, side, pair[0], pair[1])  

    print 'Message from Bitstamp: ' + str(Order)
    log.write('\nMessage from Bitstamp: ' + str(Order)) 
    
    return Order
    
def Bitstamp_Check_Order(ref):
    
    Order = Bitstamp_Private_Client().order_status(ref)
    
    print 'Message from Bitstamp: ' + str(Order)
    log.write('\nMessage from Bitstamp: ' + str(Order)) 
    
    return Order

    
def Bitstamp_Orderbook(Coin):
    
    pair = Coin.lower(), Fiat[0].lower()    
    public_client = bitstamp.client.Public()    
    Orderbook = public_client.order_book(base = pair[0], quote = pair[1])
    
    Asks = Orderbook['asks']
    Bids = Orderbook['bids']
    
    return (Asks, Bids)
    
def Bitstamp_Filled(Order):
    
    Order_ID = Order['ID']
    
    isFilled = str(Bitstamp_Check_Order(Order_ID)['status'])

    if  isFilled == 'Finished':
        Filled = True
    else: Filled = False
    
    return Filled
    
def Bitstamp_Cancel_Order(ref):
    
    Order = Bitstamp_Private_Client().cancel_order(ref)

    print 'Message from Bitstamp: ' + str(Order)
    log.write('\nMessage from Bitstamp: ' + str(Order)) 
    
    if Order is True:
        Order_Cancelled = True
    else:
        Order_Cancelled = False
    
    return Order_Cancelled

###############################################################################

def GDAX_Private_Client():
    
    key = Keys.GDAX()        
    client = GDAX.AuthenticatedClient(key['key'],key['secret'],key['passphrase'])
    return client

def Gdax_Fees():    

    fills = GDAX_Private_Client().getFills()[0] # get latest filled order
        
    buy = []    
    for fill in fills:     
    
            if fill['side'] == 'buy':
                buy.append(fill)
                buy_fee_eur = float(buy[0]['fee'])
                buy_price = float(buy[0]['price'])
                buy_size = float(buy[0]['size'])
                buy_fee = (buy_fee_eur / (buy_size*buy_price)) * 100
                
    sell_fee = 0 # fee for market makers is zero

    return {'buy_fee': buy_fee,
            'sell_fee': sell_fee,
            'currency': 'fiat'}
    
def Gdax_MOQ():
    
    MOQ_Dict = {}
    for Coin in Coins:    
        if Coin == 'BTC':
            MOQ = 0.01
        elif Coin == 'ETH':
            MOQ = 0.01
        elif Coin == 'LTC':
            MOQ = 0.01
        MOQ_Dict.update({Coin: MOQ})
        
    return {'Long': MOQ_Dict, 'Short': MOQ_Dict}

def Gdax_Balances(Coin):
    
    key = Keys.GDAX()
        
    client = GDAX.AuthenticatedClient(key['key'],key['secret'],key['passphrase'])
    accounts = client.getAccounts()
    
    for account in accounts:
        if account['currency'] == Coin:
            Coin_Balance = round(float(account['balance']), 8)  
    
    for account in accounts:
        if account['currency'] == Fiat[0]:
            Fiat_Balance = round(float(account['balance']), 2)
            
    return {Coin: Coin_Balance, Fiat[0]: Fiat_Balance}
    
def Gdax_Limit_Order(Coin, amount, side, price): #, margin): waiting to be margin approved
    
    pair = Coin+ '-' + Fiat[0]
    
    params = {'type': 'limit',
              'product_id': pair,
              'side': side,
              'price': str(price),
              'size': str(round(amount, 8))}
              #'overdraft_enabled': str(margin)} waiting to be margin approved

    Order = GDAX_Private_Client().order(params)

    print 'Message from Gdax: ' + str(Order)
    log.write('\nMessage from Gdax: ' + str(Order)) 

    return Order
    
def Gdax_Market_Order(Coin, amount, side): #, margin): waiting to be margin approved
    
    pair = Coin+ '-' + Fiat[0]
    
    params = {'type': 'market',
              'product_id': pair,
              'side': side,
              'size': str(amount)}
              #'overdraft_enabled': str(margin)} waiting to be margin approved

    Order = GDAX_Private_Client().order(params)

    print 'Message from Gdax: ' + str(Order)
    log.write('\nMessage from Gdax: ' + str(Order)) 

    return Order
    
def Gdax_Check_Order(ref):    
    
    Order = GDAX_Private_Client().getOrder(ref)

    print 'Message from Gdax: ' + str(Order)
    log.write('\nMessage from Gdax: ' + str(Order)) 
    
    return Order    
    
def Gdax_Orderbook(Coin):
    
    pair = Coin+ '-' + Fiat[0]   
    public_client = GDAX.PublicClient(product_id = pair)   
    Orderbook = public_client.getProductOrderBook(level = 3)
    
    Asks = Orderbook['asks']
    Bids = Orderbook['bids']
    
    return (Asks, Bids)
    
def Gdax_Filled(Order):
    
    Order_ID = Order['ID']
    
    Filled = Gdax_Check_Order(Order_ID)['settled']
        
    return Filled
    
def Gdax_Cancel_Order(ref):    
    
    Order = GDAX_Private_Client().cancelOrder(ref)
    
    print 'Message from Gdax: ' + str(Order)
    log.write('\nMessage from Gdax: ' + str(Order)) 
    
    if str(Order[0]) == ref:
        Order_Cancelled = True
    else:
        Order_Cancelled = False
    
    return Order_Cancelled

###############################################################################

def Bl3p_Private_Client():
    key = Keys.Bl3p()    
    client = bl3p.Client.Private(key['key'], key['secret'])
    return client

def Bl3p_Balances(Coin):    

    balances = Bl3p_Private_Client().getBalances()
    
    Coin_Balance =  round(float(balances['data']['wallets'][Coin]['available']['value']),2)    
    Fiat_Balance = round(float(balances['data']['wallets'][Fiat[0]]['available']['value']), 8)
    
    return {Coin: Coin_Balance, Fiat[0]: Fiat_Balance}
    
def Bl3p_MOQ():
    
    MOQ_Dict = {}
    for Coin in Coins:
        if Coin == 'BTC':
            MOQ = 0.0001
        elif Coin == 'LTC':
            MOQ = 0.001
        else:
            MOQ = 0.001
        MOQ_Dict.update({Coin: MOQ})  
        
    return {'Long': MOQ_Dict, 'Short': MOQ_Dict}
    
def Bl3p_Fees():
    
    balances = Bl3p_Private_Client().getBalances()    
    fee = float(balances['data']['trade_fee']) # plus 0.01eur per trade
    
    return {'buy_fee': fee,
            'sell_fee': fee,
            'currency': 'fiat'}
    
def Bl3p_Limit_Order(Coin, amount, side, price):
    
    pair = Coin + Fiat[0]
    
    if side == 'buy':
        order_side = 'bid'
    if side == 'sell':
        order_side = 'ask'
    
    Order = Bl3p_Private_Client().addOrder(pair, str(order_side), 
                                           int(amount), int(price))

    print 'Message from Bl3p: ' + str(Order)
    log.write('\nMessage from Bl3p: ' + str(Order)) 
    
    return Order
    
def Bl3p_Market_Order(Coin, amount, side):
    
    pair = Coin + Fiat[0]
    
    if side == 'buy':
        order_side = 'bid'
    if side == 'sell':
        order_side = 'ask'
    
    Order = Bl3p_Private_Client().addMarketOrder(pair, str(order_side), int(amount))

    print 'Message from Bl3p: ' + str(Order)
    log.write('\nMessage from Bl3p: ' + str(Order)) 
    
    return Order
    
def Bl3p_Check_Order(Coin, ref):
    
    pair = Coin + Fiat[0]    
    Order = Bl3p_Private_Client().checkOrder(pair, ref)
    
    print 'Message from Bl3p: ' + str(Order)
    log.write('\nMessage from Bl3p: ' + str(Order)) 
    
    return Order

    
def Bl3p_Orderbook(Coin):
    
    pair = Coin + Fiat[0]
    client = Bl3p_Private_Client()
    Orderbook = client.FullOrderbook(pair)['data']
    
    Asks_1 = Orderbook['asks']
    
    Asks = []
    
    for ask in Asks_1:
        Asks.append([float(ask['price_int'])/100000, 
                     float(ask['amount_int'])/100000000*float(ask['count'])])   
    
    Bids_1 = Orderbook['bids']
    
    Bids = []
    
    for bid in Bids_1:
        Bids.append([float(bid['price_int'])/100000, 
                     float(bid['amount_int'])/100000000*float(bid['count'])])
    
    return (Asks, Bids)
    
def Bl3p_Filled(Coin, Order):
    
    Order_ID = Order['ID'] 
    
    isFilled = str(Bl3p_Check_Order(Coin, Order_ID)['data']['status'])
    
    if  isFilled == 'closed':
        Filled = True
    else: Filled = False
    
    return Filled
        
def Bl3p_Cancel_Order(Coin, ref):
    
    pair = Coin + Fiat[0]    
    Order = Bl3p_Private_Client().cancelOrder(pair, ref)
    
    print 'Message from Bl3p: ' + str(Order)
    log.write('\nMessage from Bl3p: ' + str(Order)) 
    
    if Order['result'] == 'success':
        Order_Cancelled = True
    else:
        Order_Cancelled = False

    return Order_Cancelled

###############################################################################

def theRock_Private_Client():
    
    Key = Keys.theRock()
    client = theRock.PyRock.API(Key['key'], Key['secret'])
    return client
    
def theRock_Balances(Coin):  

    balances = theRock_Private_Client().AllBalances()
    balances = balances['balances']
    
    for balance in balances:  
        if balance['currency'] == Coin:
            Coin_Balance = round(float(balance['trading_balance']), 8)
        elif balance['currency'] == Fiat[0]:
            Fiat_Balance = round(float(balance['trading_balance']), 2) 
        
    return {Coin: Coin_Balance, Fiat[0]: Fiat_Balance}
    
def theRock_MOQ():
    
    MOQ_Dict = {}
    for Coin in Coins:
        if Coin == 'BTC':   
            MOQ = 0.005
        elif Coin == 'LTC':
            MOQ = 0.01
        elif Coin == 'ETH':
            MOQ = 0.01
        MOQ_Dict.update({Coin: MOQ})     
    
    return {'Long': MOQ_Dict, 'Short': MOQ_Dict}

    
def theRock_Fees():
    
    pair = Coins[0] + Fiat[0] 
    funds = theRock_Private_Client().Funds()['funds']
    
    for fund in funds:
        if fund['id'] == pair:
            buy_fee = fund['buy_fee']
            sell_fee = fund['sell_fee']
            
    return {'buy_fee': buy_fee,
            'sell_fee': sell_fee,
            'currency': 'fiat'}
    
def theRock_Limit_Order(Coin, amount, side, price):
    
    leverage = 1.0
    
    if Coin == 'BTC':
        Amount = int(amount*1000) / 1000.0 # round down to 3 d.p.
    elif Coin == 'LTC':
        Amount = int(amount*100) / 100.0 # round down to 2 d.p.
    elif Coin == 'ETH':
        Amount = int(amount*100) / 100.0 # round down to 2 d.p.
    
    pair = Coin.lower() + Fiat[0].lower()
    Order = theRock_Private_Client().PlaceOrder(pair, str(Amount),
                                                side, str(price), leverage)
                                                
    print 'Message from theRock: ' + str(Order)
    log.write('\nMessage from theRock: ' + str(Order))
    
    return Order
    
def theRock_Market_Order(Coin, amount, side):
    
    leverage = 1.0
    
    if Coin == 'BTC':
        Amount = int(amount*1000) / 1000.0 # round down to 3 d.p.
    elif Coin == 'LTC':
        Amount = int(amount*100) / 100.0 # round down to 2 d.p.
    elif Coin == 'ETH':
       Amount = int(amount*100) / 100.0 # round down to 2 d.p.

    
    if side == 'buy':
            price = TheRock['Prices'][Coin]['entry_buy'] * 1+0.0005 # beats market price
    elif side == 'sell':
            price = TheRock['Prices'][Coin]['entry_sell'] * 1-0.0005 # beats market price
    
    pair = Coin.lower() + Fiat[0].lower()
    Order = theRock_Private_Client().PlaceOrder(pair, str(Amount),
                                                side, str(price), leverage)
                                                
    print 'Message from theRock: ' + str(Order)
    log.write('\nMessage from theRock: ' + str(Order))
    
    return Order
    
def theRock_Check_Order(Coin, ref):
    
    pair = Coin.lower() + Fiat[0].lower()
    Order = theRock_Private_Client().ListOrder(pair, ref)
    
    print 'Message from theRock: ' + str(Order)
    log.write('\nMessage from theRock: ' + str(Order))    
    
    return Order
    
def theRock_Orderbook(Coin):
    
    pair = Coin.lower() + Fiat[0].lower()
    client = theRock_Private_Client()
    Orderbook = client.OrderBook(pair)
    
    Asks_1 = Orderbook['asks']    
    Asks = []
    
    for ask in Asks_1:
        Asks.append([float(ask['price']), float(ask['amount'])])
    
    Bids_1 = Orderbook['bids']    
    Bids = []
    
    for bid in Bids_1:
        Bids.append([float(bid['price']), float(bid['amount'])])
    
    return (Asks, Bids)
    
def theRock_Filled(Coin, Order):
    
    Order_ID = Order['ID']

    isFilled = theRock_Check_Order(Coin, Order_ID)['status']
    
    if  isFilled == 'executed':
        Filled = True
    else: Filled = False
    
    return Filled
    
def theRock_Cancel_Order(Coin, ref):
    
    pair = Coin.lower() + Fiat[0].lower()
    Order = theRock_Private_Client().CancelOrder(pair, ref)
    
    print 'Message from theRock: ' + str(Order)
    log.write('\nMessage from theRock: ' + str(Order)) 
    
    if Order['status'] == 'deleted':
        Order_Cancelled = True
    else:
        Order_Cancelled = False
        
    return Order_Cancelled


###############################################################################

def Cex_Private_Client(query, params={}):
    
    Key = Keys.Cex()
    Cex_API = cexapi.cexapi.API(Key['user'],Key['key'],Key['secret'])
    client = Cex_API.api_call(query, params, private=1)
    return client
    
def Cex_Fees():
    pair = Coins[0] + ':' + Fiat[0]
    fees = Cex_Private_Client('get_myfee')['data'][pair]
    
    return {'buy_maker_fee': float(fees['buyMaker']), 
            'sell_maker_fee': float(fees['sellMaker']),
            'buy_fee': float(fees['buy']),
            'sell_fee': float(fees['sell']),
            'currency': 'fiat'}
            
def Cex_MOQ():
    
    MOQ_Long_Dict = {}
    MOQ_Short_Dict = {}
    for Coin in Coins:
    
        if Coin == 'BTC':   
            MOQ_Long = 0.002
            MOQ_Short = 0.05

        elif Coin == 'ETH':
            MOQ_Long = 0.05
            MOQ_Short = 'N/A'

        else:
            MOQ_Long = 0.01
            MOQ_Short = 0.01

        MOQ_Long_Dict.update({Coin: MOQ_Long})
        MOQ_Short_Dict.update({Coin: MOQ_Short})
        
    return {'Long': MOQ_Long_Dict, 'Short': MOQ_Short_Dict}
         
def Cex_Balances(Coin):   

    balance = Cex_Private_Client('balance')
        
    Coin_Balance = round(float(balance[Coin]['available']),8)
    Fiat_Balance = round(float(balance[Fiat[0]]['available']),2)
    
    return {Coin: Coin_Balance, Fiat[0]: Fiat_Balance}
    
def Cex_Open_Position(Coin, amount, side, price, leverage):
    
    if leverage == 2:
    
        if side == 'sell':
            stopLossPrice = round(price + price*0.79, 2)
        elif side == 'buy':
            stopLossPrice = round(price - price*0.79, 2)

    elif leverage == 3:
    
        if side == 'sell':
            stopLossPrice = round(price + price*0.49, 2)
        elif side == 'buy':
            stopLossPrice = round(price - price*0.49, 2) 
        
    pair = Coin + '/' + Fiat[0]
    
    if side == 'buy':
        side = 'long'
    elif side == 'sell':
        side = 'short'
        
    params = {'ptype': side,
              'anySlippage': 'false',
              'symbol': Coin,
              'amount': str(amount),
              'eoprice': str(price),
              'stopLossPrice': str(stopLossPrice),
              'leverage': str(leverage)} # 2 or 3 times
              
    print params
    
    Order = Cex_Private_Client('open_position/'+pair, params)

    print 'Message from Cex_Open_Position: ' + str(Order)
    log.write('\nMessage from Cex_Open_Position: ' + str(Order)) 
    
    return Order
    
def Cex_Limit_Order(Coin, amount, side, price):
    
    pair = Coin + '/' + Fiat[0]
    
    params = {'type': side,
              'amount': str(round(amount, 8)), 
              'price': str(round(price, 1))}
              
    Order = Cex_Private_Client('place_order/'+pair, params)

    print 'Message from Cex Limit Order: ' + str(Order)
    log.write('\nMessage from Cex Limit Order: ' + str(Order)) 
    
    return Order
    
def Cex_Market_Order(Coin, amount, side):
    
    pair = Coin + '/' + Fiat[0]
    
    params = {'type': side,
              'order_type': "market",
              'amount': str(round(amount, 8))} 

              
    Order = Cex_Private_Client('place_order/'+pair, params)

    print 'Message from Cex Market Order: ' + str(Order)
    log.write('\nMessage from Cex Market Order: ' + str(Order)) 
    
    return Order
    
def Cex_Check_Order(ref):    
    
    params = {'id': ref}
    
    Order = Cex_Private_Client('get_order', params)

    print 'Message from Cex Check Order: ' + str(Order)
    log.write('\nMessage from Cex Check Order: ' + str(Order)) 
    
    return Order

def Cex_Check_Positions(Coin, ref):
    
    pair = Coin + '/' + Fiat[0]
    
    Orders = Cex_Private_Client('open_positions/'+pair)['data']
    
    print 'Cex Active Positions: ' + str(Orders)
    
    for order in Orders:
        order_id = str(order['id'])
        if order_id == ref:
            Order = order

    print 'Message from Cex Check Positions: ' + str(Order)
    log.write('\nMessage from Cex Check Positions: ' + str(Order)) 
    
    return Order  

def Cex_Orderbook(Coin):
    
    pair = Coin + '/' + Fiat[0]
    Orderbook = Cex_Private_Client('order_book/'+pair+'/')
    
    Asks = Orderbook['asks']
    Bids = Orderbook['bids']
    
    return (Asks, Bids)
    
    
def Cex_Filled(Coin, Order):
    
    try:    
        Order_ID = Order['Response']['id'] # only works for non margin order
    except:
        try:
            Order_ID = Order['Response']['data']['id'] # checks margin order
        except:
            return False
    
    ref = str(Order_ID)
        
    check_order = Cex_Check_Order(ref)
    
    if check_order is not None:
        isFilled = check_order['remains']
    
    elif check_order is None:
        order_id = str(Cex_Check_Positions(Coin, ref)['oorder'])
        isFilled = Cex_Check_Order(order_id)['remains']
        
    if float(isFilled) > 0:
        Filled = False
    else: Filled = True
        
    return Filled
    
def Cex_Cancel_Order(ref):
    
    params = {'id': ref}
    
    Order = Cex_Private_Client('cancel_order', params)
    
    print 'Message from Cex 964: ' + str(Order)
    log.write('\nMessage from Cex: ' + str(Order)) 
    
    if Order == 'True':
        Order_Cancelled = True
    else:
        Order_Cancelled = False
    
    return Order_Cancelled  

def Cex_Close_Position(Coin, ref):
    
    pair = Coin + '/' + Fiat[0]

    params = {'id': ref}
    
    Order = Cex_Private_Client('close_position/'+pair, params)
    
    print 'Message from Cex 993: ' + str(Order)
    log.write('\nMessage from Cex 994: ' + str(Order)) 
    
    return Order

###############################################################################

def Wex_Private_Client(query, **params):
    
    Key = Keys.Wex()
    client = wex.api.TradeAPIv1(Key).call(query, **params)
    return client
    
def Wex_Fees():    
    
    pair = Coins[0].lower()+'_'+Fiat[0].lower()
    
    api = wex.api.PublicAPIv3()
    fee = api.call('info')['pairs'][pair]['fee']
    
    return {'buy_fee': float(fee), 
            'sell_fee': float(fee),
            'currency': 'crypto'}

def Wex_MOQ():
    
    MOQ_Dict = {}
    for Coin in Coins:
        if Coin == 'BTC':   
            MOQ = 0.001
        elif Coin == 'LTC':
            MOQ = 0.01
        elif Coin == 'ETH':
            MOQ = 0.01
        MOQ_Dict.update({Coin: MOQ})
    
    return {'Long': MOQ_Dict, 'Short': MOQ_Dict}
         
def Wex_Balances(Coin): 

    balances = Wex_Private_Client('getInfo')['funds']   
    
    Coin_Balance = round(float(balances[Coin.lower()]), 8)
    Fiat_Balance = round(float(balances[Fiat[0].lower()]), 2)
    
    return {Coin: Coin_Balance, Fiat[0]: Fiat_Balance}
    
def Wex_Limit_Order(Coin, amount, side, price):
    
    pair = Coin.lower()+'_'+Fiat[0].lower()
    
    Amount = round(amount, 8)
    Price = round(price, 2)
    
    Order = Wex_Private_Client('Trade',pair=pair,type=side,amount=Amount,rate=Price)

    print 'Message from Wex: ' + str(Order)
    log.write('\nMessage from Wex: ' + str(Order)) 
    
    return Order
    
def Wex_Market_Order(Coin, amount, side):
    
    pair = Coin.lower()+'_'+Fiat[0].lower()
    
    if side == 'buy':
        price = Wex['Prices'][Coin]['buy'] * (1+0.00001)
    elif side == 'sell':
        price = Wex['Prices'][Coin]['sell'] * (1-0.00001)
              
    Order = Wex_Private_Client('Trade',pair=pair,type=side,amount=amount,rate=price)

    print 'Message from Wex: ' + str(Order)
    log.write('\nMessage from Wex: ' + str(Order)) 
    
    return Order
    
def Wex_Check_Order(ref):
        
    Order = Wex_Private_Client('OrderInfo', order_id=ref)

    print 'Message from Wex: ' + str(Order)
    log.write('\nMessage from Wex: ' + str(Order)) 
    
    return Order
    
  
def Wex_Orderbook(Coin):
    
    pair = Coin.lower()+'_'+Fiat[0].lower()
    
    API = wex.api.PublicAPIv3()
    
    Orderbook = API.call('depth/'+pair)[pair]
    
    Asks = [[float(i[0]), float(i[1])] for i in Orderbook['asks']]
    Bids = [[float(i[0]), float(i[1])] for i in Orderbook['bids']]
     
    return (Asks, Bids)

def Wex_Active_Orders():
        
    Order = Wex_Private_Client('ActiveOrders')

#    print 'Message from Kraken: ' + str(Order)
#    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    return Order    
    
def Wex_Filled(Order):
    
    # Order ID's not relaying back from sever so this code is broken at the moment
    
#    Order_ID = Order['order_id']
#    
#    isFilled = Wex_Check_Order(Order_ID)['status']
#    
#    if str(isFilled) == 1:
#        Filled = True
#    else: Filled = False
#    
#    return Filled
    
    Order_ID = Order['ID']
    
    try:
        Active_Orders = Wex_Active_Orders()
        
    except:
        return True # No active orders, so must have filled
        
    else:
        Orders = Active_Orders['return']
        for order in Orders:
            try:
                order[Order_ID]                
            
            except:
                return True # No Order found so must have filled
                
            else:
                return False # Still active so has not filled
            
def Wex_Cancel_Order(ref):
    
    Order = Wex_Private_Client('CancelOrder', order_id=ref)
    
    print 'Message from Wex: ' + str(Order)
    log.write('\nMessage from Wex: ' + str(Order)) 
    
    if Order[ref] == ref:
        Order_Cancelled = True
    else:
        Order_Cancelled = False
    
    return Order_Cancelled
    
###############################################################################

def BitBay_Private_Client():
    
    Key = Keys.Bitbay()
    client = bitbay.api.Client(Key['Key'], Key['Secret'])
    return client
    
def BitBay_Orderbook(Coin):
    
    pair = Coin + Fiat[0]
    
    Orderbook = BitBay_Private_Client().get_orderbook(pair)
    
    Asks = [[float(i[0]), float(i[1])] for i in Orderbook['asks']]
    Bids = [[float(i[0]), float(i[1])] for i in Orderbook['bids']]
     
    return (Asks, Bids)
    
def BitBay_Fees():    
    
    info = BitBay_Private_Client().get_info()
    fee = info['fee']
    
    return {'buy_fee': float(fee), 
            'sell_fee': float(fee),
            'currency': 'crypto'}
            
def BitBay_MOQ():
    
    MOQ_Dict = {}
    
    for Coin in Coins:    
        if Coin == 'BTC':   
            MOQ = 0.00003
        elif Coin == 'LTC':
            MOQ = 0.0025
        elif Coin == 'ETH':
            MOQ = 0.00045     
        MOQ_Dict.update({Coin: MOQ})
        
    return {'Long': MOQ_Dict, 'Short': MOQ_Dict}
         
def BitBay_Balances(Coin): 

    balances = BitBay_Private_Client().get_info()  

    Coin_Balance = round(float(balances['balances'][Coin]['available']), 8)
    Fiat_Balance = round(float(balances['balances'][Fiat[0]]['available']), 2)
    
    return {Coin: Coin_Balance, Fiat[0]: Fiat_Balance}
    
def BitBay_Limit_Order(Coin, amount, side, price):
    
    pair = (Coin, Fiat[0])
    
    Order = BitBay_Private_Client().place_order(pair, amount, side, price)

    print 'Message from Bitbay: ' + str(Order)
    log.write('\nMessage from Bitbay: ' + str(Order)) 
    
    return Order
    
def BitBay_Market_Order(Coin, amount, side):
    
    pair = (Coin, Fiat[0])
    
    if side == 'buy':
            price = BitBay['Prices'][Coin]['entry_buy'] * 1+0.00005
    elif side == 'sell':
            price = BitBay['Prices'][Coin]['entry_sell'] * 1-0.00005
              
    Order = BitBay_Private_Client().place_order(pair, amount, side, price)

    print 'Message from Bitbay: ' + str(Order)
    log.write('\nMessage from Bitbay: ' + str(Order)) 
    
    return Order
    
def BitBay_Check_Orders():
        
    Orders = BitBay_Private_Client().get_order()

    print 'Message from Bitbay: ' + str(Orders)
    log.write('\nMessage from Bitbay: ' + str(Orders)) 
    
    return Orders
    
def Bitbay_Check_Transactions():
        
    Transactions = BitBay_Private_Client().get_transactions()

#    print 'Message from Bitbay: ' + str(Order)
#    log.write('\nMessage from Bitbay: ' + str(Order)) 
    
    return Transactions
    
def BitBay_Filled(Order):
    
    Order_ID = Order['ID']
    
    if Order_ID == '0':
        return True
    
    Orders = BitBay_Check_Orders()
    
    for item in Orders:
        if item['order_id'] == Order_ID:
            isFilled = item['status']
        else:
            return False
    
    if str(isFilled) == 'inactive':
        Filled = True
    else: Filled = False
    
    return Filled

def BitBay_Cancel_Order(ref):
    
    Order = BitBay_Private_Client().cancel_order(ref)
    
    print 'Message from Bitbay: ' + str(Order)
    log.write('\nMessage from Bitbay: ' + str(Order)) 
    
    if Order['success'] == 1:
        Order_Cancelled = True
    else:
        Order_Cancelled = False
    
    return Order_Cancelled
    
###############################################################################

def Quoinex_Private_Client():
    
    Key = Keys.Quoinex()
    client = quoinex.api.Client(Key['Key'], Key['Secret'])
    return client
    
def Quoinex_Orderbook(Coin):
    
    pair = (Coin, Fiat[0])
    
    API = quoinex.api.Client()
        
    Orderbook = API.get_orderbook(pair)
            
    Asks = [[float(i[0]), float(i[1])] for i in Orderbook['sell_price_levels']]
    Bids = [[float(i[0]), float(i[1])] for i in Orderbook['buy_price_levels']]
    
    
#    for i in range(0,3):
#        Asks.pop(0) # fixes bug in API data
     
    return (Asks, Bids)
    
def Quoinex_Fees():
    
    pair = (Coins[0], Fiat[0])
        
    info = Quoinex_Private_Client().get_product_info(pair)
            
    buy_fee = info['taker_fee']
    sell_fee = info['taker_fee']
    buy_maker_fee = info['maker_fee']
    sell_maker_fee = info['maker_fee']
    
    return {'buy_fee': float(buy_fee), 
            'sell_fee': float(sell_fee),
            'buy_maker_fee': float(buy_maker_fee),
            'sell_maker_fee': float(sell_maker_fee),
            'currency': 'fiat'}
            
def Quoinex_MOQ():
    
    MOQ_Dict = {}
    
    for Coin in Coins:    
        if Coin == 'BTC':   
            MOQ = 0.001
        elif Coin == 'ETH':
            MOQ = 0.01
        elif Coin == 'LTC':
            MOQ = 0.5
        else:
            MOQ = 0.01
        MOQ_Dict.update({Coin: MOQ})
        
    return {'Long': MOQ_Dict, 'Short': MOQ_Dict}

def Quoinex_Balances(Coin): 

    balances = Quoinex_Private_Client().get_balances()
    
    for balance in balances:
        if balance['currency'] == Coin:
            Coin_Balance = round(float(balance['balance']), 8)
            
    for balance in balances:
        if balance['currency'] == Fiat[0]:
            Fiat_Balance = round(float(balance['balance']), 2)        
    
    return {Coin: Coin_Balance, Fiat[0]: Fiat_Balance}
    
def Quoinex_Limit_Order(Coin, amount, side, price, leverage):
    
    
    pair = (Coin, Fiat[0])
    
    ordertype = 'limit'
    
    Order = Quoinex_Private_Client().place_limit_order(pair, ordertype, amount, side, price, leverage)

    print 'Message from Quoinex: ' + str(Order)
    log.write('\nMessage from Quoinex: ' + str(Order)) 
    
    return Order
    
def Quoinex_Market_Order(Coin, amount, side, leverage):
    
    pair = (Coin, Fiat[0])
    
    ordertype = 'market'

    Order = Quoinex_Private_Client().place_market_order(pair, ordertype, amount, side, leverage)

    print 'Message from Quoinex: ' + str(Order)
    log.write('\nMessage from Quoinex: ' + str(Order)) 
    
    return Order
    
def Quoinex_Check_Orders(ref):
        
    Order = Quoinex_Private_Client().get_order(ref)

    print 'Message from Quoinex: ' + str(Order)
    log.write('\nMessage from Quoinex: ' + str(Order)) 
    
    return Order 
    
def Quoinex_Filled(Order):
    
    quantity = Order['Response']['quantity']
    filled_quantity = Order['Response']['filled_quantity']
    
    if filled_quantity == quantity:
        Filled = True
    else: Filled = False
    
    return Filled

def Quoinex_Cancel_Order(ref):
    
    Order = Quoinex_Private_Client().cancel_order(ref)
        
    print 'Message from Quoinex: ' + str(Order)
    log.write('\nMessage from Quoinex: ' + str(Order)) 
    
    if Order['status'] == 'cancelled':
        Order_Cancelled = True
    else:
        Order_Cancelled = False
    
    return Order_Cancelled   

def Quoinex_Close_Position(ref):
    
    Order = Quoinex_Private_Client().close_trade(ref)
    
    print 'Message from Quoinex: ' + str(Order)
    log.write('\nMessage from Quoinex: ' + str(Order))
        
    return Order

###############################################################################
###############################################################################
        
    
def Update_Balances(Exchange, Coin):
    
    name = Exchange['Name']
    
    # Updates the account balances
    
    for attempt in range(1, Attempts):     

        try:
            
            if Exchange['Name'] == 'Bitfinex':
                Balances = Bitfinex_Balances(Coin)
            
            elif Exchange['Name'] == 'Kraken':
                Balances = Kraken_Balances(Coin)
    
            elif Exchange['Name'] == 'Bitstamp':
                Balances = Bitstamp_Balances(Coin)
                
            elif Exchange['Name'] == 'Gdax':
                Balances = Gdax_Balances(Coin)
                
            elif Exchange['Name'] == 'Bl3p':
                Balances = Bl3p_Balances(Coin)
                
            elif Exchange['Name'] == 'theRock':
                Balances = theRock_Balances(Coin)
                
            elif Exchange['Name'] == 'Cex':
                Balances = Cex_Balances(Coin)
                
            elif Exchange['Name'] == 'Wex':
                Balances = Wex_Balances(Coin)
                
            elif Exchange['Name'] == 'BitBay':
                Balances = BitBay_Balances(Coin)
                
            elif Exchange['Name'] == 'Quoinex':
                Balances = Quoinex_Balances(Coin)

        except:

            if iteration > 1:
                print 'Failed to Download %s Balance for %s on Attempt: %s' %(Coin, name, attempt)
#                log.write('\nFailed to Download %s Balance for %s on Attempt: %s' %(Coin, name, attempt))
            time.sleep(1)
            continue
            
        else:
            print 'Successfully Downloaded %s Balance for %s' %(Coin, name)
#            log.write('\nSuccessfully Downloaded %s Balance for %s' %(Coin, name))
            return {Coin: Balances[Coin], Fiat[0]: Balances[Fiat[0]]}
    else:
        return {Coin: 0.00}
    

def Get_Coin_Balances(Exchange):
    Balances = {}
    
    for Coin in Coins:
        result = Update_Balances(Exchange, Coin)
        Balances.update(result)
        
    return {Exchange['Name']: Balances}           

def Get_All_Balances():
    
    if Fake_Balances is True:
        
        for Exchange in Exchanges:    
            Balances = {}    
            for Coin in Coins:            
                Balance = {}
                Balance.update({Coin: 0.0})
                Balance.update({Fiat[0]: 1000.0})
                Balances.update(Balance)
            Exchange.update({'Balances': Balances})
            
    elif Fake_Balances is False:
        
        if Multi_Processing is False:
        
            for Exchange in Exchanges:
                Exchange['Balances'] = {}
                Balances = {}
                for Coin in Coins:
                    Balance = Update_Balances(Exchange, Coin)
                    Balances.update(Balance)
                    time.sleep(1)
                Exchange.update({'Balances': Balances})
                
        elif Multi_Processing is True:
       
            # Multi-Processing - when you have a need for speed

            pool = multiprocessing.Pool(processes=20)
        
            func = partial(Get_Coin_Balances)
            result = pool.map_async(func, Exchanges)
            
            for Exchange in Exchanges:
                for balances in result.get():
                    if balances.keys()[0] == Exchange['Name']:
                        Exchange.update({'Balances': balances.values()[0]})
                        
            pool.close()
            pool.join()

def Get_MOQs(Exchange):
  
    name = Exchange['Name']
    
    if Fake_MOQs is False:
    
        for attempt in range(1, Attempts):    
            
            try:
    
                if name == 'Bitfinex':
                    Moq = Bitfinex_MOQ()
                elif name == 'Kraken':
                    Moq = Kraken_MOQ()
                elif name == 'Bitstamp':
                    Moq = Bitstamp_MOQ()
                elif name == 'Gdax':
                    Moq = Gdax_MOQ()
                elif name == 'Bl3p':
                    Moq = Bl3p_MOQ()
                elif name == 'theRock':
                    Moq = theRock_MOQ()
                elif name == 'Cex':
                    Moq = Cex_MOQ()
                elif name == 'Wex':
                    Moq = Wex_MOQ()
                elif name == 'BitBay':
                    Moq = BitBay_MOQ()
                elif name == 'Quoinex':
                    Moq = Quoinex_MOQ()
                
            except:
                if iteration > 1:
                    print 'Failed to Download MOQs for %s on Attempt: %s' %(name, attempt)
    #                log.write('\nFailed to Download %s MOQ for %s on Attempt: %s' %(Coin, name, attempt))
                time.sleep(1)
                continue
            
            else:
                print 'Successfully Downloaded MOQs for %s' %(name)
    #            log.write('\nSuccessfully Downloaded %s MOQ for %s' %(Coin, name))
                for Exchange in Exchanges:
                    if Exchange['Name'] == name:
                        Exchange.update({'MOQs': Moq})
            
            return None
            
        else:
            for Exchange in Exchanges:
                MOQ_Dict = {}
                for Coin in Coins:
                    if Exchange['Name'] == name:
                        MOQ_Dict.update({Coin: 0.002})
                Exchange.update({'MOQs': {'Long': MOQ_Dict, 'Short': MOQ_Dict}})
            return None
              
    else:    
        for Exchange in Exchanges:
            MOQ_Dict = {}
            for Coin in Coins:
                if Exchange['Name'] == name:
                    MOQ_Dict.update({Coin: 0.002})
        Exchange.update({'MOQs': {'Long': MOQ_Dict, 'Short': MOQ_Dict}})
        return None

        
def Get_Fees(Exchange):
  
    name = Exchange['Name']
    
    Dummy_Fees = {'buy_fee': 0.2, 
                  'sell_fee': 0.2,
                  'buy_maker_fee': 0.2,
                  'sell_maker_fee': 0.2}
    
    if Fake_Fees is False:
        
        for attempt in range(1, Attempts+3):     
            
            try:
                if name == 'Bitfinex':
                    fees = Bitfinex_Fees()
                elif name == 'Kraken':
                    fees = Kraken_Fees()
                elif name == 'Bitstamp':
                    fees = Bitstamp_Fees()
                elif name == 'Gdax':
                    fees = Gdax_Fees()
                elif name == 'Bl3p':
                    fees = Bl3p_Fees()
                elif name == 'theRock':
                    fees = theRock_Fees()
                elif name == 'Cex':
                    fees = Cex_Fees()
                elif name == 'Wex':
                    fees = Wex_Fees()
                elif name == 'BitBay':
                    fees = BitBay_Fees()
                elif name == 'Quoinex':
                    fees = Quoinex_Fees()
                    
            except:
                time.sleep(5)
                continue
            
            else:
                print 'Successfully Downloaded Fees for %s' %(name)
#                log.write('\nSuccessfully Downloaded Fees for %s' %(name))
                return name, fees
                
        else:
            return name, Dummy_Fees
            

    elif Fake_Fees is True:
        
                     
        if name == 'Bitfinex':
            Dummy_Fees.update({'currency': 'crypto'})
        elif name == 'Kraken':
            Dummy_Fees.update({'currency': 'crypto'})
        elif name == 'Bitstamp':
            Dummy_Fees.update({'currency': 'fiat'})
        elif name == 'Gdax':
            Dummy_Fees.update({'currency': 'fiat'})
        elif name == 'Bl3p':
            Dummy_Fees.update({'currency': 'crypto'})
        elif name == 'theRock':
            Dummy_Fees.update({'currency': 'fiat'})
        elif name == 'Cex':
            Dummy_Fees.update({'currency': 'fiat'})
        elif name == 'Wex':
            Dummy_Fees.update({'currency': 'crypto'})
        elif name == 'BitBay':
            Dummy_Fees.update({'currency': 'fiat'})
        elif name == 'Quoinex':
            Dummy_Fees.update({'currency': 'fiat'})
    
        return name, Dummy_Fees

         
def Get_All_Fees():
    
       
    if Multi_Processing is False:
    
        for Exchange in Exchanges:
            Exchange.update({'Fees': Get_Fees(Exchange)[1]})
            
    elif Multi_Processing is True:
   
        # Multi-Processing - when you have a need for speed

        pool = multiprocessing.Pool(processes=10)
            
        func = partial(Get_Fees)
        result = pool.map_async(func, Exchanges)
        
        for Exchange in Exchanges:
            for fees in result.get():
                if fees[0] == Exchange['Name']:         
                    Exchange.update({'Fees': fees[1]})
                    
        pool.close()
        pool.join()
                
def Get_Orderbook(Exchange, Coin):
    
    name = Exchange['Name']
    
    if Fake_Prices is False:
        
        try:                 
            
            if name == 'Bitfinex':
                Orderbook = Bitfinex_Orderbook(Coin)
            if name == 'Kraken':
                Orderbook = Kraken_Orderbook(Coin)
            elif name == 'Bitstamp':
                Orderbook = Bitstamp_Orderbook(Coin)
            elif name == 'Gdax':
                Orderbook = Gdax_Orderbook(Coin)
            elif name == 'Bl3p':
                Orderbook = Bl3p_Orderbook(Coin)
            elif name == 'theRock':
                Orderbook = theRock_Orderbook(Coin)
            elif name == 'Cex':
                Orderbook = Cex_Orderbook(Coin)        
            elif name == 'Wex':
                Orderbook = Wex_Orderbook(Coin) 
            elif name == 'BitBay':
                Orderbook = BitBay_Orderbook(Coin)
            elif name == 'Quoinex':
                Orderbook = Quoinex_Orderbook(Coin)    
            
        except:
            return (((0, 0), (0, 0)), ((0, 0), (0, 0))) #return fake orderbook
        
        else:
            if Orderbook is None:
                return (((0, 0), (0, 0)), ((0, 0), (0, 0)))
            else:                
                return Orderbook
    
    elif Fake_Prices is True:
                
        iterate = iteration % 2
    
        if iterate == 0:
            
            if Coin == 'BTC':
                
                Buy_Price = 5144.06
                Sell_Price = 5010.16
                
                if name == 'theRock':
                    return (((Buy_Price, 10), (Buy_Price, 100)),
                            ((Buy_Price, 10), (Buy_Price-1, 100)))
                if name == 'Cex':
                    return (((Sell_Price, 10), (Sell_Price+1, 100)),
                            ((Sell_Price, 10), (Sell_Price-1, 100)))
    
            if Coin == 'BTC':
                Price = [Buy_Price*1.001, Buy_Price*1.0011]
                            
            elif Coin == 'ETH':
                Price = [300.00, 301.00]

            elif Coin == 'LTC':
                Price = [50.00, 50.05]
                
            random_ask = random.uniform(Price[0], Price[1])
            random_bid = random_ask*0.999999
            
            if name == 'Bitfinex':
                return (((random_ask, 10), (random_ask+1, 100)),
                        ((random_bid, 10), (random_bid-1, 100)))
            elif name == 'Kraken':
                return (((random_ask, 10), (random_ask+1, 100)),
                        ((random_bid, 10), (random_bid-1, 100)))
            elif name == 'Bitstamp':
                return (((random_ask, 10), (random_ask+1, 100)),
                        ((random_bid, 10), (random_bid-1, 100)))
            elif name == 'Gdax':
                return (((random_ask, 10), (random_ask+1, 100)),
                        ((random_bid, 10), (random_bid-1, 100)))
            elif name == 'Bl3p':
                return (((random_ask, 10), (random_ask+1, 100)),
                        ((random_bid, 10), (random_bid-1, 100)))
            elif name == 'theRock':
                return (((random_ask, 10), (random_ask+1, 100)),
                        ((random_bid, 10), (random_bid-1, 100)))
            elif name == 'Cex':
                return (((random_ask, 10), (random_ask, 100)),
                        ((random_bid, 10), (random_bid, 100)))
            elif name == 'Wex':
                return (((random_ask, 10), (random_ask+1, 100)),
                        ((random_bid, 10), (random_bid-1, 100)))
            elif name == 'BitBay':
                return (((random_ask, 10), (random_ask+1, 100)),
                        ((random_bid, 10), (random_bid-1, 100)))
            elif name == 'Quoinex':
                return (((random_ask, 10), (random_ask+1, 100)),
                        ((random_bid, 10), (random_bid-1, 100)))

                    
        elif iterate == 1:
            
            if Coin == 'BTC':
                
                Sell_Price = 5131.19
                Buy_Price = 5186.35
                
                if name == 'theRock':
                    return (((Sell_Price, 10), (Sell_Price+1, 100)),
                            ((Sell_Price, 10), (Sell_Price-1, 100)))
                if name == 'Cex':
                    return (((Buy_Price, 10), (Buy_Price+1, 100)),
                            ((Buy_Price, 10), (Buy_Price-1, 100)))
    
            if Coin == 'BTC':
                Price = [Buy_Price*1.0005, Buy_Price*1.0006]
                            
            elif Coin == 'ETH':
                Price = [300.00, 301.00]

            elif Coin == 'LTC':
                Price = [50.00, 50.05]
                
            random_ask = random.uniform(Price[0], Price[1])
            random_bid = random_ask*0.99995
            
            if name == 'Bitfinex':
                return (((random_ask, 10), (random_ask+1, 100)),
                        ((random_bid, 10), (random_bid-1, 100)))
            elif name == 'Kraken':
                return (((random_ask, 10), (random_ask+1, 100)),
                        ((random_bid, 10), (random_bid-1, 100)))
            elif name == 'Bitstamp':
                return (((random_ask, 10), (random_ask+1, 100)),
                        ((random_bid, 10), (random_bid-1, 100)))
            elif name == 'Gdax':
                return (((random_ask, 10), (random_ask+1, 100)),
                        ((random_bid, 10), (random_bid-1, 100)))
            elif name == 'Bl3p':
                return (((random_ask, 10), (random_ask+1, 100)),
                        ((random_bid, 10), (random_bid-1, 100)))
            elif name == 'theRock':
                return (((random_ask, 10), (random_ask+1, 100)),
                        ((random_bid, 10), (random_bid-1, 100)))
            elif name == 'Cex':
                return (((random_ask, 10), (random_ask, 100)),
                        ((random_bid, 10), (random_bid, 100)))
            elif name == 'Wex':
                return (((random_ask, 10), (random_ask+1, 100)),
                        ((random_bid, 10), (random_bid-1, 100)))
            elif name == 'BitBay':
                return (((random_ask, 10), (random_ask+1, 100)),
                        ((random_bid, 10), (random_bid-1, 100)))
            elif name == 'Quoinex':
                return (((random_ask, 10), (random_ask+1, 100)),
                        ((random_bid, 10), (random_bid-1, 100)))
    


def Weighted_Price(amount, Orderbook):

    i = 0
    acc_volume = 0.0 
    weighted_sum = 0.0
    
    while amount > acc_volume:
        
        i += 1
        
        price = float(Orderbook[i-1][0])
        volume = float(Orderbook[i-1][1])            
        acc_volume += volume            
        weighted_sum += price * volume
        
    weighted_average = weighted_sum / acc_volume           
        
    return weighted_average
    
    
def Liquidity_Check(amount, side, orderbook):
    
    # Finds the orderbook for an exchange and determines liquid prices 
    
    if amount <= 0:
        amount = 0.000000001
    
    Amount = amount*liquid_factor
    
    if side == 'buy':
        x = 0
    elif side == 'sell':
        x = 1

    Liquid_Price = Weighted_Price(Amount, orderbook[x])
        
    return Liquid_Price
    
def Get_Prices(Exchange, Coin):
    
    # Gets prices based on the orderbook    

    Orderbook = Get_Orderbook(Exchange, Coin)
    Market_Ask = round(float(Orderbook[0][0][0]), 2)
    Market_Bid = round(float(Orderbook[1][0][0]), 2)
        
    if Market_Ask == 0 or Market_Bid == 0:
    
        return {Coin: {'buy': 0,
                       'sell': 0,
                       'entry_buy': 0,
                       'entry_sell': 0,
                       'exit_buy': 0,
                       'exit_sell': 0}}
                                   
        
    Fiat_Balance = Exchange['Balances'][Fiat[0]]
    Buy_Amount = liquid_factor*(Fiat_Balance / Market_Ask)
    Entry_Price_Buy = Liquidity_Check(Buy_Amount, 'buy', Orderbook)
    Sell_Amount = liquid_factor*(Fiat_Balance / Market_Bid)
    Entry_Price_Sell = Liquidity_Check(Sell_Amount, 'sell', Orderbook)
    
    Coin_Balance = Exchange['Balances'][Coin]
    Buy_Amount = liquid_factor * -Coin_Balance
    Exit_Price_Buy = Liquidity_Check(Buy_Amount, 'buy', Orderbook)
    Sell_Amount = liquid_factor * Coin_Balance
    Exit_Price_Sell = Liquidity_Check(Sell_Amount, 'sell', Orderbook)
    
    return {Coin: {'buy': Market_Ask,
                   'sell': Market_Bid,
                   'entry_buy': round(Entry_Price_Buy, 2),
                   'entry_sell': round(Entry_Price_Sell, 2),
                   'exit_buy': round(Exit_Price_Buy, 2),
                   'exit_sell': round(Exit_Price_Sell, 2)}}
        
        
def Get_Coin_Prices(Exchange):
    Prices = {}
    
    for Coin in Coins:
        result = Get_Prices(Exchange, Coin)
        Prices.update(result)
        
    return {Exchange['Name']: Prices}
    
def Get_All_Prices():  
    
    if Fake_Prices is False:
        
        if Multi_Processing is False:
    
             # Singe Processing - useful for debugging

            for Exchange in Exchanges:
               results = Get_Coin_Prices(Exchange)
               Exchange.update({'Prices': results[Exchange['Name']]})
        
        elif Multi_Processing is True:
        
            # Multi-Processing - when you have a need for speed
        
            pool = multiprocessing.Pool(processes=10)
        
            func = partial(Get_Coin_Prices)
            result = pool.map_async(func, Exchanges)
            
            for Exchange in Exchanges:
                for prices in result.get():
                    if prices.keys()[0] == Exchange['Name']:
                        Exchange.update({'Prices': prices.values()[0]})
                        
            pool.close()
            pool.join()
    
    elif Fake_Prices is True:
    
        for Exchange in Exchanges:
            prices = Get_Coin_Prices(Exchange)[Exchange['Name']]
            Exchange.update({'Prices': prices})


    
def Get_Perm(exchanges, Coin):
    
    
    Exchange_Iterations = list(itertools.permutations(exchanges, 2))
    
    Exchange_Iterations = [dict(zip(('Long', 'Short'), i)) for \
                          i in Exchange_Iterations if i[1]['Shorting'] is True]

    Permuatations = list(itertools.product(Coins, Exchange_Iterations))
        
    Permuatations = [{'Coin': i[0],
                      'Long': i[1]['Long'],
                      'Short': i[1]['Short']} for i in Permuatations]
    
    Permuatations2 = []
    
    # only keep relevant permuatations
                     
    for i, Perm in enumerate(Permuatations):
        if Perm['Short']['Name'] == 'Kraken':
            if Perm['Coin'] != 'LTC': # Cannot short litecoin at kraken
                Permuatations2.append(Perm)
        elif Perm['Short']['Name'] == 'Cex':
            if Perm['Coin'] != 'ETH': # Cannot short ethereum at cex
                Permuatations2.append(Perm)
        else:
            Permuatations2.append(Perm)
            
    return Permuatations2
    

def Calc_Spread_Entry(Opportunity):
    
    Coin = Opportunity['Coin']
    
    Exchange1 = Opportunity['Long']
    Exchange2 = Opportunity['Short']
    
    Buy_Price = Exchange1['Prices'][Coin]['entry_buy']
    Sell_Price = Exchange2['Prices'][Coin]['entry_sell']
    
    if Buy_Price == 0 or Sell_Price == 0:
        return -1000.0 # return a ridiculous percentage that will never execute
   
    Spread = ((Sell_Price - Buy_Price) / Buy_Price)*100
    
    return Spread
    
def Calc_Spread_Exit(Arb):
    
    Coin = Arb['Coin']
    
    Exchange1 = Arb['Long']
    Exchange2 = Arb['Short']
    
    Buy_Price = Exchange1['Prices'][Coin]['exit_sell']
    Sell_Price = Exchange2['Prices'][Coin]['exit_buy']
    
    if Buy_Price == 0 or Sell_Price == 0:
        return 1000.0 # return a ridiculous percentage that will never execute
   
    Spread = ((Sell_Price - Buy_Price) / Buy_Price)*100
    
    return Spread
    
def Update_Arb(Arb):
    
    Coin = Arb['Coin']
    
    for Exchange in Exchanges:
        if Exchange['Name'] == Arb['Long']['Name']:
            Arb['Long'].update(Exchange)
            
    for Exchange in Exchanges:
        if Exchange['Name'] == Arb['Short']['Name']:
            Arb['Short'].update(Exchange)
            
    if Arb['Long']['Prices'][Coin]['buy'] == 0 or \
       Arb['Short']['Prices'][Coin]['buy'] == 0:
        return None
        
    Spread_Out = Calc_Spread_Exit(Arb)
                   
    Arb.update({'Close_Spread': Spread_Out})
    
    if Spread_Out < Arb['Close_Min_Spread']:
        Arb['Close_Min_Spread'] = Spread_Out
    
    
def Find_Opportunities(Perm):
    
    Coin = Perm['Coin']
    
    # sets the start values for logging of the spread histories
    
    if Perm['Long']['Prices'][Coin]['buy'] == 0 or \
       Perm['Short']['Prices'][Coin]['buy'] == 0: 
        return None
    
    Spread_In = Calc_Spread_Entry(Perm)
    
    Exchange1_Fees = Perm['Long']['Fees']['buy_fee'] + \
                     Perm['Long']['Fees']['sell_fee']
                     
    Exchange2_Fees = Perm['Short']['Fees']['buy_fee'] + \
                     Perm['Short']['Fees']['sell_fee']
                     
    Fees = (Exchange1_Fees + Exchange2_Fees)
    
#    Enter_Target = Target_Profit + Fees/2 # sets zero as the mid-point
    Enter_Target = Target_Profit*2 + Fees # only has to reach zero to close
#    Enter_Target = Target_Profit #easier entry price for testing
                              
    return { 'Coin': Perm['Coin'],
             'Long': Perm['Long'],
             'Short': Perm['Short'], 
             'Open_Spread': Spread_In,
             'Open_Target': Enter_Target,
             'Open_Max_Spread': Spread_In,           
             'Total_Fees': Fees }
                          
                          
def Update_Opportunities(Opportunity): 

    Coin = Opportunity['Coin']     
    
    if Opportunity['Long']['Prices'][Coin]['buy'] == 0 or \
       Opportunity['Short']['Prices'][Coin]['buy'] == 0:
           
        return None
        
    Spread_In = Calc_Spread_Entry(Opportunity)
        
    Opportunity['Open_Spread'] = Spread_In
        
    if Spread_In > Opportunity['Open_Max_Spread']:
        New_Max_Spread = Spread_In
    else: New_Max_Spread = Opportunity['Open_Max_Spread']
    
    Long = Opportunity['Long']
    Short = Opportunity['Short']
    
    for Exchange in Exchanges:
        if Exchange['Name'] == Long['Name']:
            Long.update({'Prices': Exchange['Prices']})
        if Exchange['Name'] == Short['Name']:
            Short.update({'Prices': Exchange['Prices']})       
        
    Opportunity.update({'Open_Spread': Spread_In,
                        'Open_Max_Spread': New_Max_Spread,
                        'Long': Long,
                        'Short': Short})


def Check_Order_Filled(Coin, Exchange, Order, side):
    
    time.sleep(1)
       
    if Test_Mode:
        return True
    
    name = Exchange['Name']

    try:
        
        if Exchange['Name'] == 'Bitfinex':
            Filled = Bitfinex_Filled(Order)
            
        elif Exchange['Name'] == 'Kraken':
            Filled = Kraken_Filled(Order) 
            
        elif Exchange['Name'] == 'Bitstamp': 
            Filled = Bitstamp_Filled(Order)
            
        elif Exchange['Name'] == 'Gdax':
            Filled = Gdax_Filled(Order)
                
        elif Exchange['Name'] == 'Bl3p':
            Filled = Bl3p_Filled(Coin, Order)
                
        elif Exchange['Name'] == 'theRock':
            Filled = theRock_Filled(Coin, Order)

        elif Exchange['Name'] == 'Cex':
            Filled = Cex_Filled(Coin, Order)

        elif Exchange['Name'] == 'Wex':
            Filled = Wex_Filled(Order)
            
        elif Exchange['Name'] == 'BitBay':
            Filled = BitBay_Filled(Order)
            
        elif Exchange['Name'] == 'Quoinex':
            Filled = Quoinex_Filled(Order)
            
    except:
        
        print side + ' order at %s waiting to fill...' %name
        log.write('\n' + side +' order at %s waiting to fill...'%name)
                                                                       
        print 'Message: ' + [i for i in traceback.format_exc().split('\n') if i][-1]
        log.write('\nMessage: ' + [i for i in traceback.format_exc().split('\n') if i][-1])
        
        return False
    
    else:
        return Filled
          
    
def Cancel_Order(Coin, exchange, ref):
    
    time.sleep(1)
       
    # Looks for which exchange to cancel the order on
    
    name = exchange['Name']
    
    if Test_Mode:
        return True
        
    else:
        
        for attempt in range(1, Attempts):            
            try:
                if exchange['Name'] == 'Bitfinex':
                    Cancelled = Bitfinex_Cancel_Order(ref)
                    
                elif exchange['Name'] == 'Kraken':
                    Cancelled = Kraken_Cancel_Order(ref)
                    
                elif exchange['Name'] == 'Bitstamp':
                    Cancelled = Bitstamp_Cancel_Order(ref)
                    
                elif exchange['Name'] == 'Gdax':
                    Cancelled = Gdax_Cancel_Order(ref)
                    
                elif exchange['Name'] == 'Bl3p':
                    Cancelled = Bl3p_Cancel_Order(Coin, ref)
                    
                elif exchange['Name'] == 'theRock':
                    Cancelled = theRock_Cancel_Order(Coin, ref)
                    
                elif exchange['Name'] == 'Cex':
                    Cancelled = Cex_Cancel_Order(ref)

                elif exchange['Name'] == 'Wex':
                    Cancelled = Wex_Cancel_Order(ref)
                    
                elif exchange['Name'] == 'BitBay':
                    Cancelled = BitBay_Cancel_Order(ref)
                
                elif exchange['Name'] == 'Quoinex':
                    Cancelled = Quoinex_Cancel_Order(ref)
                    
            except:
                print 'Cancel Order Failed at %s on Attempt: %i' %(name, 
                                                                   attempt)
                log.write('\nCancel Order Failed at %s on Attempt: %i' %(name, 
                                                                         attempt))
                                                                         
                print 'Message: ' + [i for i in traceback.format_exc().split('\n') if i][-1]
                log.write('Message: ' + [i for i in traceback.format_exc().split('\n') if i][-1])
                
                if attempt != Attempts-1:                                                           
                    time.sleep(3)
                continue
        
            else:
                
                if Cancelled is False:
                    print 'Cancel Order Failed at %s on Attempt: %i' %(name, 
                                                                       attempt)
                    log.write('\nCancel Order Failed at %s on Attempt: %i' %(name, 
                                                                             attempt))
                    if attempt != Attempts-1:                                                           
                        time.sleep(3)
                    continue
                else:
                    return True
      
        else:                                                  
            print 'Failed to Cancel Order at %s ' %(exchange['Name'])
            log.write('\nFailed to Cancel Order at %s ' %(exchange['Name']))
            return False
            
    
def Place_Limit_Order(Coin, Exchange, amount, side, price, Leverage):
           
    Position_ID = False
    
    if Test_Mode:
        
        Order_ID = str(uuid.uuid4().hex) # generates 32 char fake ID
            
        return {'ID': Order_ID, 'Position_ID': Order_ID}

    elif Test_Mode is False:
        
        try:
        
            if Exchange['Name'] == 'Bitfinex':
                Order = Bitfinex_Limit_Order(Coin, amount, side, price, Leverage)
                Order_ID = Order['order_id']
                
            elif Exchange['Name'] == 'Kraken':
                Order = Kraken_Limit_Order(Coin, amount, side, price, Leverage)
                Order_ID = str(Order['result']['txid'][0])
                
            elif Exchange['Name'] == 'Bitstamp':            
                Order = Bitstamp_Limit_Order(Coin, amount, side, price)
                Order_ID = str(Order['id'])
            
            elif Exchange['Name'] == 'Gdax':            
                Order = Gdax_Limit_Order(Coin, amount, side, price)
                Order_ID = str(Order['id'])
                
            elif Exchange['Name'] == 'Bl3p':            
                Order = Bl3p_Limit_Order(Coin, amount*100000000, side, price*100000)
                Order_ID = str(Order['data']['order_id'])
                
            elif Exchange['Name'] == 'theRock':            
                Order = theRock_Limit_Order(Coin, amount, side, price)
                Order_ID = str(Order['id'])
                      
            elif Exchange['Name'] == 'Cex':
                
                if Leverage == 0:
                    Order = Cex_Limit_Order(Coin, amount, side, price)
                    Order_ID = str(Order['id'])
                    
                elif Leverage != 0:
                    Order = Cex_Open_Position(Coin, amount, side, price, Leverage)
                    Order_ID = str(Order['data']['id'])
                    
            elif Exchange['Name'] == 'Wex':            
                Order = Wex_Limit_Order(Coin, amount, side, price)
                Order_ID = str(Order['order_id'])
                
            elif Exchange['Name'] == 'BitBay':            
                Order = BitBay_Limit_Order(Coin, amount, side, price)
                Order_ID = str(Order['order_id'])
    
            elif Exchange['Name'] == 'Quoinex':            
                Order = Quoinex_Limit_Order(Coin, amount, side, price, Leverage)
                try:
                    if Order['errors']:
                        pass
                except:    
                    Order_ID = Order['id']
                    Position_ID = Order['trade_id']
                    
            if Position_ID is False:
                Position_ID = Order_ID
                
        except:
            
            return False
                                
        else:
            return {'ID': Order_ID, 'Position_ID': Position_ID, 'Response': Order}

        
def Place_Market_Order(Coin, Exchange, amount, side, leverage):
                
    if Test_Mode:
        
        if side == 'buy':
            Price = Exchanges[Exchange['Name']]['Prices'][Coin]['entry_buy']
        elif side == 'sell':
            Price = Exchanges[Exchange['Name']]['Prices'][Coin]['entry_sell']
        
        Order_ID = str(uuid.uuid4().hex) # generates 32 char fake ID
            
        return {'ID': Order_ID, 'Price': Price}
     
    elif Test_Mode is False:
        
        try:
            if Exchange['Name'] == 'Bitfinex':        
                Order = Bitfinex_Market_Order(Coin, amount, side, leverage)
                Order_ID =  Order['order_id']
    
            elif Exchange['Name'] == 'Kraken':        
                Order = Kraken_Market_Order(Coin, amount, side, leverage)
                Order_ID =  str(Order['result']['txid'][0])
                
            elif Exchange['Name'] == 'Bitstamp':            
                Order = Bitstamp_Market_Order(Coin, amount, side)
                Order_ID = str(Order['id'])
            
            elif Exchange['Name'] == 'Gdax':            
                Order = Gdax_Market_Order(Coin, amount, side)
                Order_ID = str(Order['id'])
                
            elif Exchange['Name'] == 'Bl3p':            
                Order = Bl3p_Market_Order(Coin, amount*100000000, side)
                Order_ID = str(Order['data']['order_id'])
                
            elif Exchange['Name'] == 'theRock':            
                Order = theRock_Market_Order(Coin, amount, side)
                Order_ID = str(Order['id'])
                
            elif Exchange['Name'] == 'Cex':
    
                if leverage == 0:
                    Order = Cex_Market_Order(Coin, amount, side)
                    Order_ID = str(Order['id'])
                    
                elif leverage != 0:
                    for exchange in Exchanges:
                        if exchange['Name'] == 'Cex':
                            if side == 'buy':
                                price = exchange['Prices'][Coin]['entry_buy']
                            elif side == 'sell':
                                price = exchange['Prices'][Coin]['entry_sell']
   
                    Order = Cex_Open_Position(Coin, amount, side, price, leverage)
                    Order_ID = str(Order['data']['id'])
                
            elif Exchange['Name'] == 'Wex':            
                Order = Wex_Market_Order(Coin, amount, side)
                Order_ID = str(Order['order_id'])
                
            elif Exchange['Name'] == 'BitBay':            
                Order = BitBay_Market_Order(Coin, amount, side)
                Order_ID = str(Order['order_id'])
                
            elif Exchange['Name'] == 'Quoinex':            
                Order = Quoinex_Market_Order(Coin, amount, side, leverage)
                Order_ID = Order['id']
                    
        except:
            return False
            
            
        time.sleep(5)
        
        for attempt in range(1, Attempts):
                        
            try:
                if Exchange['Name'] == 'Bitfinex':        
                    Price = float(Bitfinex_Check_Order(Order_ID)['avg_execution_price'])
        
                elif Exchange['Name'] == 'Kraken':        
                    Price = float(Kraken_Check_Order(Order_ID)['result'][Order_ID]['price'])
                    
                elif Exchange['Name'] == 'Bitstamp':            
                    Price = float(Order['price'])
                
                elif Exchange['Name'] == 'Gdax':
                    Price = float(Order['price'])
                    
                elif Exchange['Name'] == 'Bl3p':            
                    Price = float(Bl3p_Check_Order(Coin, Order_ID)['data']['avg_cost']['value'])
                    
                elif Exchange['Name'] == 'theRock':            
                    for Exchange in Exchanges:
                        if Exchange['Name'] == 'theRock':
                            if side == 'buy':
                                Price = Exchange['Prices'][Coin]['buy']
                            if side == 'sell':
                                Price = Exchange['Prices'][Coin]['sell']
                    
                elif Exchange['Name'] == 'Cex':
                    
                    Amount = float(Order['symbol1Amount'])/100000000
                    Income = float(Order['symbol2Amount'])/100
                    Price = Income / Amount
                    
                elif Exchange['Name'] == 'Wex':            
                    for Exchange in Exchanges:
                        if Exchange['Name'] == 'Wex':
                            if side == 'buy':
                                Price = Exchange['Prices'][Coin]['buy']
                            if side == 'sell':
                                Price = Exchange['Prices'][Coin]['sell']
                    
                elif Exchange['Name'] == 'BitBay':            
                    Price = float(Bitbay_Check_Transactions()[0]['rate'])
                    
                elif Exchange['Name'] == 'Quoinex':            
                    Price = float(Order['price'])
        
            except:
                if attempt < Attempts - 1:
                    time.sleep(5)
                    continue
            else:
                return {'ID': Order_ID, 'Price': Price, 'Response': Order}           
 
        else:
            return {'ID': 'N/A', 'Price': 0, 'Response': 'N/A'}
        
def Execute_Limit_Order(Coin, Exchange, Amount, Side, Price, Leverage):

    amount = round(Amount, 8)
    price = round(Price, 2)

    name = Exchange['Name']
    
    # Do not use multiple attempts for limit orders as they are not critical

    try:
        Order = Place_Limit_Order(Coin, Exchange, amount, Side, price, Leverage)
    
    except:            
                       
        print 'Message: ' + [i for i in traceback.format_exc().split('\n') if i][-1]
        log.write('Message: ' + [i for i in traceback.format_exc().split('\n') if i][-1])
        
        print Side + ' Order failed at %s' %(name)
        log.write('\n' + Side + ' Order failed at %s' %(name))
        
        return False
     
    else:
        
       try:
           if Order['Response']['errors']:
               return False
       except:
           try:
               if Order['Response']['error']:
                   return False           
       
           except:
                if Order is False:
                    return False
                else:
                    print '%s Exchange %s Order: %s'%(name, Side.title(), Order)
                    log.write('\n%s Exchange %s Order: %s'%(name, Side.title(), Order))
                    return Order
           else:
                return Order
                             
        
def Execute_Market_Order(Coin, Exchange, Amount, Side, Leverage):
    
    amount = round(Amount, 8)
        
    name = Exchange['Name']
    
    # Use multiple attempts for market orders as they are critcal
    
    for attempt in range(1, Attempts):
        
        try:
            Order = Place_Market_Order(Coin, Exchange, amount, Side, Leverage)                
        
        except:
            
            print 'Message: ' + [i for i in traceback.format_exc().split('\n') if i][-1]
            log.write('Message: ' + [i for i in traceback.format_exc().split('\n') if i][-1])
                        
            print '%s Market Order failed at %s. Attempt: %s' %(Side, name, attempt)
            log.write('\n%s Market Order failed at %s. Attempt: %s' %(Side, name, attempt))
            
            if attempt < Attempts - 1:
                time.sleep(5)
                continue
    
        else:
            
           try:
               if Order['Response']['errors']:
                   return False
           except:
               try:
                   if Order['Response']['error']:
                       return False           
           
               except:
                    if Order is False:
                        return False
                    else:
                        print '%s Exchange %s Order: %s'%(name, Side.title(), Order)
                        log.write('\n%s Exchange %s Order: %s'%(name, Side.title(), Order))
                        return Order
               else:
                    return Order
    else:
        print '%s Market Order failed at %s.' %(Side, name)
        log.write('\n%s Market Order failed at %s. ' %(Side, name))
        return Order
            
        
        
def Check_Position_Closed(Exchange,Order):
    
    time.sleep(1)
    
    name = Exchange['Name']
       
    if Test_Mode:
        return True
    
    try:

        if Exchange['Name'] == 'Cex':
            if Order['ok'] == 'ok':
                Closed = True
            else:
                Closed = False
                        
        elif Exchange['Name'] == 'Quoinex':
            if Order['status'] == 'closed':
                Closed = True
            else:
                Closed = False
            
    except:
        
        print 'Position at %s waiting to close' %name
        log.write('\nPosition at %s waiting to close'%name)
                                                                       
        print 'Message: ' + [i for i in traceback.format_exc().split('\n') if i][-1]
        log.write('\nMessage: ' + [i for i in traceback.format_exc().split('\n') if i][-1])
    
    else:
        print Order
        return Closed    

def Close_Position(Coin, Exchange, Amount, side, leverage, ref):
    
    amount = round(Amount, 8)
    
    time.sleep(1)
    
    name = Exchange['Name']
        
    if Test_Mode:        
        Order_ID = str(uuid.uuid4().hex) # generates 32 char fake ID
        Position = {'Position': Order_ID, 'Price': Exchange['Prices'][Coin]['exit_sell']}
                
        return Position

    elif Test_Mode is False:
        
        if Exchange['Name'] == 'Bitfinex':        
            Order = Execute_Market_Order(Coin, Exchange, amount, side, leverage)
            Price = Order['Price']
            
        elif Exchange['Name'] == 'Kraken':        
            Order = Execute_Market_Order(Coin, Exchange, amount, side, leverage)
            Price = Order['Price']
            
        elif Exchange['Name'] == 'Cex':
            Order = Cex_Close_Position(Coin, ref)
            Price = float(Order['price'])
                           
        elif Exchange['Name'] == 'Quoinex':            
            Order = Quoinex_Close_Position(ref)
            Price = float(Order['close_price'])
                    
        for attempt in range(1, Attempts+3):
            
            try:
                
                if Exchange['Name'] == 'Bitfinex':        
                    Position_Status = Check_Order_Filled(Coin, Exchange, Order, 'sell')
                
                elif Exchange['Name'] == 'Kraken':        
                    Position_Status = Check_Order_Filled(Coin, Exchange, Order, 'sell')
                     
                elif Exchange['Name'] == 'Cex':
                    Position_Status = Check_Position_Closed(Exchange, Order)
                         
                elif Exchange['Name'] == 'Quoinex':            
                    Position_Status = Check_Position_Closed(Exchange, Order)
                 
            except:
                
                print 'Close Position Failed at %s on Attempt: %i' %(name, 
                                                                   attempt)
                log.write('\nClose Position Failed at %s on Attempt: %i' %(name, 
                                                                         attempt))
                                                                         
                print 'Message: ' + [i for i in traceback.format_exc().split('\n') if i][-1]
                log.write('Message: ' + [i for i in traceback.format_exc().split('\n') if i][-1])
                
                if attempt < Attempts:                                                           
                    time.sleep(3)
                continue
        
            else:
                                
                if Position_Status is False:
                    print 'Close Position Failed at %s on Attempt: %i' %(name, 
                                                                       attempt)
                    log.write('\nClose Position Failed at %s on Attempt: %i' %(name, 
                                                                             attempt))
                    if attempt < Attempts:                                                           
                        time.sleep(3)
                    continue
                else:                  
#                    print Order
                    return {'Position': Order, 'Price': Price}
      
        else:                                                  
            print 'Failed to Close Position at %s ' %(exchange['Name'])
            log.write('\nFailed to Close Position at %s ' %(exchange['Name']))
            return {'Position': False, 'Price': 0.0}


        

 
    
def Print_Entry(Coin, Exchange1, Exchange2, Spread):
    
#    winsound.PlaySound(r'Billions&Billions.wav', winsound.SND_ASYNC)
    
    Name1 = Exchange1['Name']
    Name2 = Exchange2['Name']
    
    print '\n---Entry Found---'
    
    print Coin + ' / ' + Fiat[0]
    
    print '\nLong: ' + Name1 + ' / ' + \
          'Short: '+ Name2 + '. ' + \
          'Spread: ' + str(round(Spread, 2)) + '%'
          
    print 'Prices ' + str(Exchange1['Prices'][Coin]['entry_buy']) + Fiat[0] + ' / ' + \
                      str(Exchange2['Prices'][Coin]['entry_sell']) + Fiat[0]
                      
    print 'Balances ' + str(Exchange1['Balances'][Fiat[0]]) + Fiat[0] + ' / ' + \
                        str(Exchange2['Balances'][Fiat[0]]) + Fiat[0]
                        
    print '\nAttempting Trade...'

    log.write('\n\n---Entry Found---')
    
    log.write('\n'+Coin + ' / ' + Fiat[0])
    
    log.write('\nLong: ' + Name1 + ' / ' + \
                'Short: '+ Name2 + '. ' + \
                'Spread: ' + str(round(Spread, 2)) + '%')
          
    log.write('\nPrices ' + str(Exchange1['Prices'][Coin]['entry_buy']) + Fiat[0] + ' / ' + \
                      str(Exchange2['Prices'][Coin]['entry_sell']) + Fiat[0])
                      
    log.write('\nBalances ' + str(Exchange1['Balances'][Fiat[0]]) + Fiat[0] + ' / ' + \
                        str(Exchange2['Balances'][Fiat[0]]) + Fiat[0])
                        
    log.write('\n\nAttempting Trade...')
    

def Print_Exit(Coin, Exchange2, Exchange1, spread):
       
    Name1 = Exchange1['Name']
    Name2 = Exchange2['Name']
    
    print '\n---Exit Found---\n'
    
    print Coin + ' / ' + Fiat[0]
    
    print 'Short: ' + Name1 + ' / ' + \
          'Long: ' + Name2 + '. '+ \
          'Spread: ' + str(round(spread, 4)) + '%'
          
    print 'Prices ' + str(Exchange1['Prices'][Coin]['exit_sell']) + Fiat[0] + ' / ' + \
                      str(Exchange2['Prices'][Coin]['exit_buy']) + Fiat[0]
                      
    print 'Balances ' + str(Exchange1['Balances'][Coin]) + Coin + ' / ' + \
                        str(Exchange2['Balances'][Coin]) + Coin
          
    print '\nAttempting to Trade...'
    
    
    log.write('\n\n---Exit Found---\n')
    
    log.write(Coin + ' / ' + Fiat[0])
    
    log.write('Short: ' + Name1 + ' / ' + \
              'Long: ' + Name2 + '. '+ \
              'Spread: ' + str(round(spread, 4)) + '%')
          
    log.write('\nPrices ' + str(Exchange1['Prices'][Coin]['exit_sell']) + Fiat[0] + ' / ' + \
                      str(Exchange2['Prices'][Coin]['exit_buy']) + Fiat[0])
                      
    log.write('\nBalances ' + str(Exchange1['Balances'][Coin]) + Coin + ' / ' + \
                        str(Exchange2['Balances'][Coin]) + Coin)
          
    log.write('\n\nAttempting to Trade...')
    
def Print_Profit(Closed_Arb):
    
    winsound.PlaySound(r'cash.wav', winsound.SND_ASYNC)
    
    Coin = Closed_Arb['Coin']
    
    Exchange1 = Closed_Arb['Long']
    Exchange2 = Closed_Arb['Short']
    Profit = Closed_Arb['Profit']
    Return = Closed_Arb['Return']
    
    print '\n' + \
           Coin + ' / ' + Fiat[0] + '\n' + \
          'Long: ' + Exchange1['Name'] + ' / '+ \
          'Short: ' + Exchange2['Name'] + ' ' \
          '\nProfit: ' + str(round(Profit, 2)) + ' ' + Fiat[0] + \
          '\nReturn: ' + str(round(Return, 2)) + ' %' \
          '\nStart Time: ' + str(Closed_Arb['Open_Time']) + \
          '\nEnd Time: '+ str(Closed_Arb['Close_Time']) + \
          '\nElapsed Time: '+ str(Closed_Arb['Elapsed_Time'])
                         
    profit_file.write('\n\n' + \
                      Coin + ' / ' + Fiat[0] + '\n' + \
                      'Long: ' + Exchange1['Name'] + ' / '+ \
                      'Short: ' + Exchange2['Name'] + ' ' \
                      '\nProfit: ' + str(round(Profit, 2)) + ' ' + Fiat[0] + \
                      '\nReturn: ' + str(round(Return, 2)) + ' %' \
                      '\nStart Time: ' + str(Closed_Arb['Open_Time']) + \
                      '\nEnd Time: '+ str(str(Closed_Arb['Close_Time'])) + \
                      '\nElapsed Time: '+ str(Closed_Arb['Elapsed_Time']))
                      
def Print_Balances():
    
    print '%-22s' % '-------------------',
    for fiat in Fiat:
        print '%-15s' % '------------',
    for coin in Coins:
        print '%-15s' % '------------',
        
    print '\n%-22s' % 'Exchange Balances',
    for fiat in Fiat:
        print '%-15s' % (' '+fiat+' Balance'),
    for coin in Coins:
        print '%-15s' % (' '+coin+' Balance'),
          
    print '\n%-22s' % '-------------------',
    for fiat in Fiat:
        print '%-15s' % '------------',
    for coin in Coins:
        print '%-15s' % '------------',
          
    for Exchange in Exchanges:
        print '\n%-22s' % Exchange['Name'],
        for fiat in Fiat:
            print '%-15s' % round(Exchange['Balances'][fiat], 2),
        for coin in Coins:
            print '%-15s' % round(Exchange['Balances'][coin], 8),

    log.write( '\n%-22s' % '-------------------',)
    for fiat in Fiat:
        log.write( '%-15s' % '------------',)
    for coin in Coins:
        log.write( '%-15s' % '------------',)
        
    log.write( '\n%-22s' % 'Exchange Balances',)
    for fiat in Fiat:
        log.write( '%-15s' % (' ' + fiat + ' Balance'),)
    for coin in Coins:
        log.write( '%-15s' % (' ' + coin + ' Balance'),)
          
    log.write( '\n%-22s' % '-------------------',)
    for fiat in Fiat:
        log.write( '%-15s' % '------------',)
    for coin in Coins:
        log.write( '%-15s' % '------------',)
          
    for Exchange in Exchanges:
        log.write( '\n%-22s' % Exchange['Name'],)
        for fiat in Fiat:
            log.write( '%-15s' % round(Exchange['Balances'][fiat], 2),)
        for coin in Coins:
            log.write( '%-15s' % round(Exchange['Balances'][coin], 8),)
                 

def Print_Prices():
          
    print '\n%-14s' '%-14s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' % \
          ('-----------',
          '-----------',
          '--------', '--------',
          '--------', '--------',
          '--------', '--------')
          
    print '%-14s' '%-14s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' % \
          ('Instrument','Exchange', '  Ask', '  Bid', 'Entry Ask', 'Entry Bid',  'Exit Ask', 'Exit Bid')
          
    print '%-14s' '%-14s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' % \
          ('-----------',
          '-----------',
          '--------', '--------',
          '--------', '--------',
          '--------', '--------')
          
    for coin in Coins:
        for Exchange in Exchanges:
            try:
                if Exchange['Prices'][coin]['buy'] == 0:
                    continue
                print '%-14s' '%-14s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' % \
                (coin + ' / ' + Fiat[0],
                Exchange['Name'],
                Exchange['Prices'][coin]['buy'], Exchange['Prices'][coin]['sell'],
                Exchange['Prices'][coin]['entry_buy'], Exchange['Prices'][coin]['entry_sell'],
                Exchange['Prices'][coin]['exit_buy'], Exchange['Prices'][coin]['exit_sell'])
            except:
                pass
            else:
                pass
    

    log.write('\n%-14s' '%-14s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' % \
          ('-----------', \
          '-----------', \
          '--------', '--------', \
          '--------', '--------', \
          '--------', '--------'))
          
    log.write('\n%-14s' '%-14s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' % \
          ('Instrument','Exchange', '  Ask', '  Bid', 'Entry Ask', 'Entry Bid',  'Exit Ask', 'Exit Bid'))
          
    log.write('\n%-14s' '%-14s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' % \
          ('-----------', \
          '-----------', \
          '--------', '--------', \
          '--------', '--------', \
          '--------', '--------'))
      
    for coin in Coins:
        for Exchange in Exchanges:
            try:
                log.write('\n%-14s' '%-14s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' % \
                (coin + ' / ' + Fiat[0],
                Exchange['Name'],
                Exchange['Prices'][coin]['buy'], Exchange['Prices'][coin]['sell'],
                Exchange['Prices'][coin]['entry_buy'], Exchange['Prices'][coin]['entry_sell'],
                Exchange['Prices'][coin]['exit_buy'], Exchange['Prices'][coin]['exit_sell']))
            except:
                pass
            else:
                pass                  
            
def Print_Arbitrages():

    print '%-40s' '%-30s' '%-30s' % \
          ('-----------------------------------', '-------------------------', '-------------------------')
                
    print '%-40s' '%-30s' '%-30s' % \
          ('     ------ ARBITRAGE ------', 'Potential Opportunities', '   Current Positions')
          
    print '%-40s' '%-30s' '%-30s' % \
          ('-----------------------------------', '--------------------------', '-------------------------')
                
    print '%-14s' '%-12s' '%-12s' '%-10s' '%-10s' '%-10s' '%-10s' '%-10s' '%s' % \
          ('----------', '------', '------', '------', '------', '------', '------', '------', '------')
                
    print '%-14s' '%-12s' '%-12s' '%-10s' '%-10s' '%-10s' '%-10s' '%-10s' '%s' % \
          ('Instrument', ' Long', ' Short', 'Spread', 'Target', ' Max', ' Spread', 'Target',' Min')
          
    print '%-14s' '%-12s' '%-12s' '%-10s' '%-10s' '%-10s' '%-10s' '%-10s' '%s' % \
          ('----------', '------', '------', '------', '------', '------', '------', '------', '------')

    for Arb in Current_Arbs:
        print '%-14s' '%-12s' '%-12s' '%-10s' '%-10s' '%-10s' '%-10s' '%-10s' '%s' % \
        (str(Arb['Coin'] + ' / ' + Fiat[0]),
        str(Arb['Long']['Name']),
        str(Arb['Short']['Name']), \
        '   -   ', \
        '   -   ', \
        '   -   ', \
        str(round(Arb['Close_Spread'], 2)) + ' %', \
        str(round(Arb['Close_Target'], 2)) + ' %', \
        str(round(Arb['Close_Min_Spread'], 2)) + ' %')
               
    for Opportunity in Opportunities:
        print '%-14s' '%-12s' '%-12s' '%-10s' '%-10s' '%-10s' '%-10s' '%-10s' '%s' % \
        (str(Opportunity['Coin'] + ' / ' + Fiat[0]),
         str(Opportunity['Long']['Name']),
         str(Opportunity['Short']['Name']), \
         str(round(Opportunity['Open_Spread'], 2)) + ' %' , \
         str(round(Opportunity['Open_Target'], 2)) + ' %', \
         str(round(Opportunity['Open_Max_Spread'], 2)) + ' %', \
         '   -   ', \
         '   -   ', \
         '   -   ', )
    
    print '\n'
    
    log.write('\n')

    log.write('\n%-40s' '%-30s' '%-30s' % \
          ('-----------------------------------', '-------------------------', '-------------------------'))
                
    log.write('\n%-40s' '%-30s' '%-30s' % \
          ('     ------ ARBITRAGE ------', 'Potential Opportunities', '   Current Positions'))
          
    log.write('\n%-40s' '%-30s' '%-30s' % \
          ('-----------------------------------', '--------------------------', '-------------------------'))
                
    log.write('\n%-14s' '%-12s' '%-12s' '%-10s' '%-10s' '%-10s' '%-10s' '%-10s' '%s' % \
          ('----------', '------', '------', '------', '------', '------', '------', '------', '------'))
                
    log.write('\n%-14s' '%-12s' '%-12s' '%-10s' '%-10s' '%-10s' '%-10s' '%-10s' '%s' % \
          ('Instrument', ' Long', ' Short', 'Spread', 'Target', ' Max', ' Spread', 'Target',' Min'))
          
    log.write('\n%-14s' '%-12s' '%-12s' '%-10s' '%-10s' '%-10s' '%-10s' '%-10s' '%s' % \
          ('----------', '------', '------', '------', '------', '------', '------', '------', '------'))

    for Arb in Current_Arbs:
        log.write('\n%-14s' '%-12s' '%-12s' '%-10s' '%-10s' '%-10s' '%-10s' '%-10s' '%s' % \
        (str(Arb['Coin'] + ' / ' + Fiat[0]),
        str(Arb['Long']['Name']),
        str(Arb['Short']['Name']), \
        '   -   ', \
        '   -   ', \
        '   -   ', \
        str(round(Arb['Close_Spread'], 2)) + ' %', \
        str(round(Arb['Close_Target'], 2)) + ' %', \
        str(round(Arb['Close_Min_Spread'], 2)) + ' %'))
               
    for Opportunity in Opportunities:
        log.write('\n%-14s' '%-12s' '%-12s' '%-10s' '%-10s' '%-10s' '%-10s' '%-10s' '%s' % \
        (str(Opportunity['Coin'] + ' / ' + Fiat[0]),
         str(Opportunity['Long']['Name']),
         str(Opportunity['Short']['Name']), \
         str(round(Opportunity['Open_Spread'], 2)) + ' %' , \
         str(round(Opportunity['Open_Target'], 2)) + ' %', \
         str(round(Opportunity['Open_Max_Spread'], 2)) + ' %', \
         '   -   ', \
         '   -   ', \
         '   -   ', ))
    
    log.write( '\n\n')
                      
                      
def Trade_Logic_Open(Coin,
                     Exchange1, Exchange2, 
                     Buy_Price, Sell_Price, 
                     Buy_Amount, Sell_Amount):
    
    Short_Leverage = 2
    Long_Leverage = 0
    
    Name1 = Exchange1['Name']
    Name2 = Exchange2['Name']
        
    # Checks conditions are True, if False log error, else move on
        
    while True:
        
        print 'Placing Sell Order at %s.' %(Name2)
        log.write('\nPlacing Sell Order at %s.' %(Name2))
    
        Sell_Order = Execute_Limit_Order(Coin, Exchange2, Sell_Amount,
                                         'sell', Sell_Price, Short_Leverage)                                  
                 
        if Sell_Order is False:
            return (False, False) # doesn't matter, nothing exceuted yet
            
        for attempt in range(1, Attempts):
            
            print 'Checking if Sell Order at %s filled on attempt: %i' %(Name2, attempt)
            log.write('\nChecking if Sell Order at %s filled on attempt: %i'%(Name2, attempt))
                
            Sell_Filled = Check_Order_Filled(Coin, Exchange2, Sell_Order,'sell')
            
            if Sell_Filled is False:
                print 'Sell Order at %s did not fill. Attempt: %i' %(Name2, attempt)
                log.write('\nSell Order at %s did not fill on attempt: %i'%(Name2, attempt))
                
                if attempt < Attempts-1:
                    time.sleep(5)
                    continue
                
            elif Sell_Filled:
                print 'Sell Order at %s sucessfully filled.' %(Name2)
                log.write('\nSell Order at %s successfully filled'%(Name2))
                break
        
        if Sell_Filled is False:
            
            print 'Sell Order at %s failed to fill. Cancelling Order.' %(Name2)
            log.write('\nSell Order at %s failed to fill. Cancelling Order'%(Name2))
        
            Cancel_Order(Coin, Exchange2, Sell_Order['ID'])
            
            print 'Coin: ' + str(Coin) + \
                  ' Exchange: '+ str(Exchange2['Name']) + \
                  ' Sell Order ID: '+ str(Sell_Order['ID']) + \
                  ' Cancelled'
                  
            log.write('\nCoin: ' + str(Coin) + \
                      ' Exchange: '+ str(Exchange2['Name']) + \
                      ' Sell Order ID: '+ str(Sell_Order['ID']) + \
                      ' Cancelled')
            
            return (False, False)
        
        # Sell Order has now filled
        
        print 'Sold '+str(Sell_Amount)+Coin+' at '+Exchange2['Name'] + \
              ' @ ' + str(Sell_Price)
              
        log.write('\nSold '+str(Sell_Amount)+Coin+' at '+Exchange2['Name']+\
                  ' @ ' + str(Sell_Price))  
        
        # Sell Order has now filled, place the buy order.
        
        print 'Placing Buy Order at %s.' %(Name1)
        log.write('\nPlacing Buy Order at %s.' %(Name1))
        
        Buy_Order = Execute_Limit_Order(Coin, Exchange1, Buy_Amount,
                                        'buy', Buy_Price, Long_Leverage)                                  
        
        for attempt in range(1, Attempts):
            
            print 'Checking if Buy Order at %s filled. Attempt: %i' %(Name1, attempt)
            log.write('\nChecking if Buy Order at %s filled. Attempt: %i'%(Name1, attempt))
            
            Buy_Filled = Check_Order_Filled(Coin, Exchange1, Buy_Order, 'buy')
            
            if Buy_Filled is False:
                print 'Buy Order at %s did not fill on attempt: %i' %(Name1, attempt)
                log.write('\nBuy Order at %s did not to fill on attempt: %i'%(Name1, attempt))
                
                if attempt < Attempts-1:
                    time.sleep(5)
                    continue
            
            elif Buy_Filled:
                print 'Buy Order at %s succesfully filled.' %(Name1)
                log.write('\nBuy Order at %s sucessfully filled.'%(Name1))
                break
    
        if Buy_Filled is False:
            
            print 'Buy Order at %s failed to fill. Cancelling Order.' %(Name1)
            log.write('\nBuy Order at %s failed to fill. Cancelling Order.'%(Name1))
            
            Cancel_Order(Coin, Exchange1, Buy_Order['ID'])
            
            print 'Coin: ' + str(Coin) + \
                  ' Exchange: ' + str(Exchange1['Name']) + \
                  ' Buy Order ID: '+ str(Buy_Order['ID']) + \
                  ' Cancelled'
                  
            log.write('\nCoin: ' + str(Coin) + \
                  ' Exchange: ' + str(Exchange1['Name']) + \
                  ' Buy Order ID: '+ str(Buy_Order['ID']) + \
                  ' Cancelled')
            
            # Reverse the sell order if buy didn't fill,
            # may need to look at market order for this
            
            for attempt in range(1, Attempts):
                
                print 'Buy Order Cancelled at %s. Reversing Sell Order at %s.' %(Name1, Name2)
                log.write('\nBuy Order Cancelled at %s. %s Reversing Sell Order at %s.'%(Name1, Name2))

                Abort_ref = Sell_Order['Position_ID']
                                                
                Abort_Order = Close_Position(Coin, Exchange2, Sell_Amount,
                                             'buy', Short_Leverage, Abort_ref)
                                
                if Abort_Order['Position']['Closed']:
                    break
                else:
                    if attempt < Attempts-1:
                        time.sleep(5)
                        continue

            print 'Coin: ' + str(Coin) + \
                  ' Exchange: ' + str(Exchange2['Name']) + \
                  ' Order ID: '+ str(Abort_Order['Position']) + \
                  ' Trade Reversed'
                  
            log.write('\nCoin: ' + str(Coin) + \
                  ' Exchange: ' + str(Exchange2['Name']) + \
                  ' Order ID: '+ str(Abort_Order['Position']) + \
                  ' Trade Reversed')
            
            
            Loss = Sell_Amount*(1-Exchange2['Fees']['buy_fee']/100)* \
                   (1-Exchange2['Fees']['sell_fee']/100)* Abort_Order['Price']- \
                   Sell_Amount*Sell_Price
                   
            Exchange2['Balances'][Fiat[0]] -= Loss
            
            Profits.append(Loss)
            
            return (False, False)
            
        # Buy Order has now filled
                     
        print 'Bought '+str(Buy_Amount)+Coin+' at '+Exchange1['Name'] + \
              ' @ ' + str(Buy_Price)
              
        log.write('\nBought '+str(Buy_Amount)+Coin+' at '+Exchange1['Name']+\
                  ' @ ' + str(Buy_Price))         
            
        # Both Orders have now been executed and filled!!
    
        return (Buy_Order, Sell_Order)
        
def Trade_Logic_Close(Coin,
                      Exchange2, Exchange1, 
                      Buy_Price, Sell_Price, 
                      Buy_Amount, Sell_Amount,
                      Close_ID):
        
    Long_Leverage = 2
    Short_Leverage = 0
    
    Name1 = Exchange1['Name']
    Name2 = Exchange2['Name']
        
    print 'Placing Sell Order at %s.' %(Name1)
    log.write('\nPlacing Sell Order at %s.' %(Name1))

    Sell_Order = Execute_Limit_Order(Coin, Exchange1, Sell_Amount,
                                     'sell', Sell_Price, Short_Leverage)
             
    if Sell_Order is False:
        return (False, False) # doesn't matter, nothing exceuted yet
    
    print 'Checking if Sell Order at %s filled.' %(Name1)
    log.write('\nChecking if Sell Order at %s filled. '%(Name1))
        
    Sell_Filled = Check_Order_Filled(Coin, Exchange1, Sell_Order, 'sell')
    
    if Sell_Filled is False:
        
        print 'Sell Order at %s failed to fill. Cancelling Order.' %(Name1)
        log.write('\nSell Order at %s failed to fill. Cancelling Order.'%(Name1))
    
        Cancel_Order(Coin, Exchange1, Sell_Order['ID'])
        
        print 'Cancelled: \nCoin: %s, Exchange: %s, ID: %s' %(Coin, Name1, Sell_Order['ID'])
        log.write('\nCancelled: \n\nCoin: %s, Exchange: %s, ID: %s' %(Coin, Name1, Sell_Order['ID']))
        
        return (False, False)

    elif Sell_Filled is True:
        
        print 'Sell Order at %s filled.' %(Name1)
        log.write('\nSell Order at %s filled.' %(Name1))
    
    # Sell Order has now filled
    
    print 'Sold %s %s at %s for %s %s' %(Sell_Amount, Coin, Name1, Sell_Price, Fiat[0])
    log.write('\nSold %s %s at %s for %s %s' %(Sell_Amount, Coin, Name1, Sell_Price, Fiat[0]))
    
    # Sell Order has now filled, place the buy order.
    
    print 'Closing Short Position at %s.' %(Name2)
    log.write('\nClosing Short Position at %s.' %(Name2))
        
    Closed_Position = Close_Position(Coin, Exchange2, Buy_Amount,
                                     'buy', Long_Leverage, Close_ID)
                
    if Closed_Position['Position'] is False:
        return (False, Sell_Order)

    # Buy Order has now filled

    Close_Buy_Price = Closed_Position['Price']
         
    print 'Sold %s %s at %s for %s %s' %(Buy_Amount, Coin, Name2, Close_Buy_Price, Fiat[0])
    log.write('\nSold %s %s at %s for %s %s' %(Buy_Amount, Coin, Name2, Close_Buy_Price, Fiat[0]))
        
    # Both Orders have now been executed and filled!!

    return (Closed_Position, Sell_Order)
            

def Trade_Logic_Complex_Open(Coin,
                             Exchange1, Exchange2, 
                             Buy_Price, Sell_Price, 
                             Buy_Amount, Sell_Amount,
                             Type):
    
    Name1 = Exchange1['Name']
    Name2 = Exchange2['Name']
    
    if Type == 'Open':
        Short_Leverage = 2
        Long_Leverage = 0
                
    elif Type == 'Close':
        Long_Leverage = 2
        Short_Leverage = 0
        
                        
    print 'Placing Buy Order at %s.' %(Name1)
    log.write('\nPlacing Buy Order at %s.' %(Name1))

    Buy_Order = Execute_Limit_Order(Coin, Exchange1, Buy_Amount, 'buy', Buy_Price, Long_Leverage)                                  
             
    if Buy_Order is False:
        return (False, False) # doesn't matter, nothing exceuted yet
    
    print 'Placing Sell Order at %s.' %(Name2)
    log.write('\nPlacing Sell Order at %s.' %(Name2))
    
    Sell_Order = Execute_Limit_Order(Coin, Exchange2, Sell_Amount, 'sell', Sell_Price, Short_Leverage)                                  
    
    if Sell_Order is False:
        
        time.sleep(3)
        
        print 'Checking if Buy Order at %s filled.' %(Name1)
        log.write('\nChecking if Buy Order at %s filled.'%(Name1))
        
        Buy_Filled = Check_Order_Filled(Coin, Exchange1, Buy_Order, 'buy')
    
        if Buy_Filled is False:
            
            print 'Buy Order at %s did not fill. Cancelling Order.' %(Name1)
            log.write('\nBuy Order at %s did not fill. Cancelling Order.'%(Name1))
            
            Cancel_Order(Coin, Exchange1, Buy_Order['ID'])
            
            print 'Coin: ' + str(Coin) + \
                  ' Exchange: '+ str(Exchange1['Name']) + \
                  ' Buy Order ID: '+ str(Buy_Order['ID']) + \
                  ' Cancelled'
                  
            log.write('\nCoin: ' + str(Coin) + \
                      ' Exchange: '+ str(Exchange1['Name']) + \
                      ' Buy Order ID: '+ str(Buy_Order['ID']) + \
                      ' Cancelled')
                                                
            return (False, False)
            
        elif Buy_Filled is True:
            
            print 'Sell Order Failed at %s. Reversing Buy Order at %s.' %(Name2, Name1)
            log.write('\nSell Order Failed at %s. Reversing Buy Order at %s.'%(Name2, Name1))
            
            time.sleep(3)
            
            for exchange in Exchanges:
                if exchange['Name'] == Name1:                
                    Abort_Amount =  Buy_Amount * 1-(exchange['Fees']['buy_fee']/100)
                                             
            Abort_Order = Execute_Market_Order(Coin, Exchange1, Abort_Amount,
                                        'sell', Long_Leverage)
                
            if Abort_Order:

                print 'Coin: ' + str(Coin) + \
                      ' Exchange: ' + str(Exchange1['Name']) + \
                      ' Order ID: '+ str(Abort_Order['ID']) + \
                      ' Trade Reversed'
                      
                log.write('\nCoin: ' + str(Coin) + \
                      ' Exchange: ' + str(Exchange1['Name']) + \
                      ' Order ID: '+ str(Abort_Order['ID']) + \
                      ' Trade Reversed')
                      
                Loss = Buy_Amount*(1-Exchange1['Fees']['buy_fee']/100)* \
                (1-Exchange1['Fees']['sell_fee']/100)* Abort_Order['Price']- \
                Buy_Amount*Buy_Price
                   
                Exchange2['Balances'][Fiat[0]] -= Loss
            
                Profits.append(Loss)
     
                return (False, False)
                
            else:
                
                print 'Abort Order at %s failed. Need manual Order.' %(Name1)
                log.write('\nAbort Order at %s failed. Need manual Order.'%(Name1))
                return (False, False)
          
    # If come this far, both orders are now placed!  
    
    time.sleep(3)
    
    Buy_Filled = False
    Sell_Filled = False
    
    B_F = False
    S_F = False
    
    for attempt in range(1, Attempts):
        
        if Buy_Filled is False:
        
            print 'Checking if Buy Order at %s filled. Attempt: %i' %(Name1, attempt)
            log.write('\nChecking if Buy Order at %s filled. Attempt: %i'%(Name1, attempt))
                    
            Buy_Filled = Check_Order_Filled(Coin, Exchange1, Buy_Order, 'buy')
            
        if Buy_Filled is False:
            print 'Buy Order at %s did not fill on attempt: %i' %(Name1, attempt)
            log.write('\nBuy Order at %s waiting did not fill on attempt: %i'%(Name1, attempt))
            
        elif Buy_Filled is True:
            if B_F is False:
                print 'Buy Order at %s successfully filled.' %(Name1)
                log.write('\nBuy Order at %s successfully filled.'%(Name1))
                B_F = True
        
        if Sell_Filled is False:

            print 'Checking if Sell Order at %s filled. Attempt: %i' %(Name2, attempt)
            log.write('\nChecking if Sell Order at %s filled. Attempt: %i'%(Name2, attempt))
            
            Sell_Filled = Check_Order_Filled(Coin, Exchange2, Sell_Order, 'sell')                         
     
        if Sell_Filled is False:
            print 'Sell Order at %s did not fill on attempt: %i' %(Name2, attempt)
            log.write('\nSell Order at %s did not fill on attempt: %i'%(Name2, attempt))
        
        elif Sell_Filled is True:
            if S_F is False:
                print 'Sell Order at %s successfully filled.' %(Name2)
                log.write('\nSell Order at %s successfully filled.'%(Name2))
                S_F = True
            
        if Buy_Filled is False or Sell_Filled is False:

            if attempt < Attempts-1:
                time.sleep(5)
                continue
            
        else:
            break 
                     
    if Buy_Filled is False:
        
        print 'Buy Order at %s failed to fill. Cancelling Order.' %(Name1)
        log.write('\nBuy Order at %s failed to fill. Cancelling Order.'%(Name1))

        Cancel_Order(Coin, Exchange1, Buy_Order['ID'])      
      
        print 'Coin: ' + str(Coin) + \
              ' Exchange: ' + str(Exchange1['Name']) + \
              ' Buy Order ID: '+ str(Buy_Order['ID']) + \
              ' Cancelled'
              
        log.write('\nCoin: ' + str(Coin) + \
              ' Exchange: ' + str(Exchange1['Name']) + \
              ' Buy Order ID: '+ str(Buy_Order['ID']) + \
              ' Cancelled')
 
        
        if Sell_Filled is False:
            
            print 'Sell Order at %s failed to fill. Cancelling Order.' %(Name2)
            log.write('\nSell Order at %s failed to fill. Cancelling Order.'%(Name2))
            
            Cancel_Order(Coin, Exchange2, Sell_Order['ID'])
            
            print 'Coin: ' + str(Coin) + \
                  ' Exchange: ' + str(Exchange2['Name']) + \
                  ' Sell Order ID: '+ str(Sell_Order['ID']) + \
                  ' Cancelled'
                  
            log.write('\nCoin: ' + str(Coin) + \
                  ' Exchange: ' + str(Exchange2['Name']) + \
                  ' Sell Order ID: '+ str(Sell_Order['ID']) + \
                  ' Cancelled')
            
            return (False, False)
            
        elif Sell_Filled is True:
            
            print 'Reversing Sell Order at %s. Order at %s failed to fill.' %(Name2, Name1)
            log.write('\nReversing Sell Order at %s. Order at %s failed to fill.' %(Name2, Name1))
            
            time.sleep(3)

            Abort_ref = Sell_Order['Position_ID']
            
            for exchange in Exchanges:
                if exchange['Name'] == Name2:                
                    Abort_Amount =  Sell_Amount #* 1-(exchange['Fees']['buy_fee']/100)
   
                                        
            Abort_Order = Close_Position(Coin, Exchange2, Abort_Amount,
                                    'buy', Short_Leverage, Abort_ref)
                                
            if Abort_Order:
                  
                print 'Coin: ' + str(Coin) + \
                      ' Exchange: ' + str(Exchange1['Name']) + \
                      ' Order ID: ' + str(Sell_Order['Position_ID']) + \
                      ' Trade Reversed'
                
                log.write('\nCoin: ' + str(Coin) + \
                      ' Exchange: ' + str(Exchange1['Name']) + \
                      ' Order ID: ' + str(Sell_Order['Position_ID']) + \
                      ' Trade Reversed')
                      
                Loss = Sell_Amount*(1-Exchange2['Fees']['buy_fee']/100)* \
                (1-Exchange2['Fees']['sell_fee']/100)* Abort_Order['Price']- \
                Sell_Amount*Sell_Price
                   
                Exchange2['Balances'][Fiat[0]] -= Loss
            
                Profits.append(Loss)
                
                return (False, False)
                
            else:
                print 'Abort Order at %s failed. Need manual Order.' %(Name2)
                log.write('\nAbort Order at %s failed. Need manual Order.'%(Name2))
                return (False, False)
                
         
    # Buy Order has now filled, check if sell order has filled.
         
    print 'Bought %s %s at %s for %s %s' %(Buy_Amount, Coin, Name1, Buy_Price, Fiat[0])
    log.write('\nBought %s %s at %s for %s %s' %(Buy_Amount, Coin, Name1, Buy_Price, Fiat[0]))
                           
    if Sell_Filled is False:
        
        # Cancel sell order and reverse buy order
        
        print 'Cancelling Sell Order at %s' %(Name2)
        log.write('\nCancelling Sell Order at  %s' %(Name2))
        
        time.sleep(5)
        
        Cancel = Cancel_Order(Coin, Exchange2, Sell_Order['ID'])
        
        if Cancel is False:
            print 'Sell Order failed to cancel, checking if filled again.'
            Sell_Filled = Check_Order_Filled(Coin, Exchange2, Sell_Order, 'sell')                         
            if Sell_Filled is True:
                print 'Sold %s %s at %s for %s' %(Sell_Amount, Coin, Sell_Price, Fiat[0])
                log.write('\nSold %s %s at %s for %s' %(Sell_Amount, Coin, Sell_Price, Fiat[0]))
                return (Buy_Order, Sell_Order)  

            
        print 'Sell Order did not fill at %s. Reversing Buy Order at %s.' %(Name2, Name1)
        log.write('\nSell Order did not fill at %s. Reversing Buy Order at %s.'%(Name2, Name1))
        
        for exchange in Exchanges:
            if exchange['Name'] == Name1:
                if exchange['Fees']['currency'] == 'crypto':
                    Buy_Cost = exchange['Fees']['buy_fee'] / 100
                elif exchange['Fees']['currency'] == 'fiat':
                    Buy_Cost = 0.0
                    
                Abort_Amount = Buy_Amount * (1 - Buy_Cost)
        
        Abort_Order = Execute_Market_Order(Coin, Exchange1, Abort_Amount,
                                    'sell', Long_Leverage)
        
        if Abort_Order:    
            
            print 'Coin: ' + str(Coin) + \
                  ' Exchange: '+ str(Exchange1['Name']) + \
                  ' Order ID: '+ str(Abort_Order['ID']) + \
                  ' Trade Reversed'
              
            log.write('\nCoin: ' + str(Coin) + \
                      ' Exchange: '+ str(Exchange1['Name']) + \
                      ' Order ID: '+ str(Abort_Order['ID']) + \
                      ' Trade Reversed')
                      
            Loss = Buy_Amount*(1-Exchange1['Fees']['buy_fee']/100)* \
            (1-Exchange1['Fees']['sell_fee']/100)* Abort_Order['Price']- \
            Buy_Amount*Buy_Price
               
            Exchange2['Balances'][Fiat[0]] -= Loss
        
            Profits.append(Loss)                
              
            return (False, False)
            
        else:
            print 'Abort Order at %s failed. Need manual Order.' %(Name1)
            log.write('\nAbort Order at %s failed. Need manual Order.'%(Name1))
            return (False, False)
 
    # Both Orders have now been executed and filled!!
    
    print 'Sold %s %s at %s for %s %s' %(Sell_Amount, Coin, Name2, Sell_Price, Fiat[0])
    log.write('\nSold %s %s at %s for %s %s' %(Sell_Amount, Coin, Name2, Sell_Price, Fiat[0]))
   
         
    return (Buy_Order, Sell_Order)  

def Open(Opportunity):
    
    Coin = Opportunity['Coin']
    
    Exchange1 = Opportunity['Long']
    Exchange2 = Opportunity['Short']
    
    Name1 = Exchange1['Name']
    Name2 = Exchange2['Name']
         
    Balance1 = Exchange1['Balances'][Fiat[0]]
    Balance2 = Exchange2['Balances'][Fiat[0]]
    
    Spread = Opportunity['Open_Spread']
    Entry_Target = Opportunity['Open_Target']
    Current_Exit_Spread = Calc_Spread_Exit(Opportunity)
    
    Buy_Order = {}
    Sell_Order = {}
    
#    while True:
        
    # Check for zero prices
    
    if Exchange1['Prices'][Coin]['entry_buy'] == 0 or \
        Exchange2['Prices'][Coin]['entry_sell'] == 0:
            return False
    
    # Check for sufficient spread

    if Spread <= Entry_Target:
        return False
    
    # Check if number of Arbitrages limited for testing
    
    if Limit_Arbitrages:
        if len(Current_Arbs) > 0:
            print '\nAlready one Arbitrage open'
            return False
        
    for Arb in Current_Arbs:
        
        # Check if opportunity already exists            
        
        if Name1 == Arb['Long']['Name'] and Name2 == Arb['Short']['Name'] and Coin == Arb['Coin']:
            return False
    
    # Check if there is sufficient balance            

    if Balance1 < Min_Bal or Balance2 < Min_Bal:
        return False                           
    
    # limit to minimum order quantity for testing
    
    Buy_Price = Exchange1['Prices'][Coin]['entry_buy']
    Sell_Price = Exchange2['Prices'][Coin]['entry_sell']
        
    if Limit_Qty is True:
        
        Buy_MOQ = Exchange1['MOQs']['Long'][Coin]
        Sell_MOQ = Exchange2['MOQs']['Short'][Coin] #* 2 # accounts for leverage

        Max_Fiat_Buy = (Buy_MOQ*Buy_Price) / (1-Exchange1['Fees']['buy_fee']/100) # add so can re-sell
        Max_Fiat_Sell = (Sell_MOQ*Sell_Price) / (1-Exchange2['Fees']['sell_fee']/100) # add so can re-sell
    
        if Max_Fiat_Buy > Balance1*0.99 or \
           Max_Fiat_Sell > Balance2*0.99:
               return False

        
    elif Limit_Qty is False:
        
        # Use exchange with minimum balance to execute orders

        Max_Fiat_Buy = Balance1 * (1-Exchange1['Fees']['buy_fee']/100) *0.99
        Max_Fiat_Sell = Balance2 * (1-Exchange2['Fees']['sell_fee']/100) *0.99

    Buy_Amount = Max_Fiat_Buy / Buy_Price
    Sell_Amount = Max_Fiat_Sell / Sell_Price
    
    
    if Buy_Amount >= Sell_Amount:
        
        # if qty limited go for max amount otherwise go for min amount
        
        if Limit_Qty is True:
            Trade_Amount = Buy_Amount
        elif Limit_Qty is False: 
            Trade_Amount = Sell_Amount
        
        print 'Trade Amount 0: ', Trade_Amount
        log.write('\nTrade Amount 0: '+str(Trade_Amount))
                
        if Exchange1['Fees']['currency'] == 'crypto':
            Trade_Amount_Buy = Trade_Amount 
            print 'Trade Amount Buy 1: ', Trade_Amount_Buy
            log.write('\nTrade Amount Buy 1: '+str(Trade_Amount_Buy))
        elif Exchange1['Fees']['currency'] == 'fiat':
            Trade_Amount_Buy = Trade_Amount * (1-Exchange1['Fees']['buy_fee']/100)
            print 'Trade Amount Buy 2: ', Trade_Amount_Buy
            log.write('\nTrade Amount Buy 2: '+str(Trade_Amount_Buy))
            
        if Exchange2['Fees']['currency'] == 'crypto':
            Trade_Amount_Sell = Trade_Amount * (1-Exchange1['Fees']['buy_fee']/100)
            print 'Trade Amount Sell 3: ', Trade_Amount_Sell
            log.write('\nTrade Amount Sell 3: '+str(Trade_Amount_Sell))
        elif Exchange2['Fees']['currency'] == 'fiat':
            Trade_Amount_Sell = Trade_Amount * (1-Exchange1['Fees']['buy_fee']/100)
            print 'Trade Amount Sell 4: ', Trade_Amount_Sell
            log.write('\nTrade Amount Sell 4: '+str(Trade_Amount_Sell))
            
    else:
        
        # if qty limited go for max amount otherwise go for min amount
        
        if Limit_Qty is True:
            Trade_Amount = Sell_Amount
        elif Limit_Qty is False:
            Trade_Amount = Buy_Amount
        
        print 'Trade Amount 5: ', Trade_Amount
        log.write('\nTrade Amount 5: '+str(Trade_Amount))
    
        if Exchange1['Fees']['currency'] == 'crypto':
            Trade_Amount_Buy = (Trade_Amount * (1-Exchange2['Fees']['sell_fee']/100)) / (1-Exchange1['Fees']['buy_fee']/100)
            print 'Trade Amount Buy 6: ', Trade_Amount_Buy
            log.write('\nTrade Amount Buy 6: '+str(Trade_Amount_Buy))
        elif Exchange1['Fees']['currency'] == 'fiat':
            Trade_Amount_Buy = Trade_Amount * (1-Exchange2['Fees']['sell_fee']/100)
            print 'Trade Amount Buy 7: ', Trade_Amount_Buy
            log.write('\nTrade Amount Buy 7: '+str(Trade_Amount_Buy))
            
        if Exchange2['Fees']['currency'] == 'crypto':
            Trade_Amount_Sell = Trade_Amount * (1-Exchange2['Fees']['sell_fee']/100)
            print 'Trade Amount Sell 8: ', Trade_Amount_Sell
            log.write('\nTrade Amount Sell 8: '+str(Trade_Amount_Sell))
        elif Exchange2['Fees']['currency'] == 'fiat':
            Trade_Amount_Sell = Trade_Amount * (1-Exchange2['Fees']['sell_fee']/100)
            print 'Trade Amount Sell 9: ', Trade_Amount_Sell
            log.write('\nTrade Amount Sell 9: '+str(Trade_Amount_Sell))
            
    # Check minimum order quantity is satisfied        
    
    if Trade_Amount_Buy < Exchange1['MOQs']['Long'][Coin] or \
        Trade_Amount_Sell < Exchange2['MOQs']['Short'][Coin]:
        return False        
    
    # Log information
    
    Print_Entry(Coin, Exchange1, Exchange2, Spread)
            
    # Calc Fees and Execute the Trade Logic function which is complicated              
    
    if Name1 == 'theRock':
        if Coin == 'BTC':
            Trade_Amount_Buy = int(Trade_Amount_Buy*1000) / 1000.0 # round down to 3 d.p.
        else:
            Trade_Amount_Buy = int(Trade_Amount_Buy*100) / 100.0 # round down to 2 d.p.
    
#        Trade_Amount_Buy = math.ceil(Trade_Amount_Buy*100000000.0)/100000000.0 # round up
#        Trade_Amount_Sell = math.ceil(Trade_Amount_Sell*100000000.0)/100000000.0 # round up
#        
    Trade_Amount_Buy = round(Trade_Amount_Buy, 8)
    Trade_Amount_Sell = round(Trade_Amount_Sell, 8)               
    
    Buy_Cost = Exchange1['Fees']['buy_fee']/100 * Trade_Amount_Buy
    Sell_Cost = Exchange2['Fees']['buy_fee']/100 * Trade_Amount_Sell
    
    if Name1 == 'Bl3p':
        Buy_Cost += 0.01/Buy_Price # extra 1 penny fee for bl3p        
    
    Long_Exposure = (Trade_Amount-Buy_Cost) * Buy_Price
    Short_Exposure = (Trade_Amount+Sell_Cost) * Sell_Price
    
    if Place_Concurrent_Orders is False:
            
        Buy_Order, Sell_Order = Trade_Logic_Open(Coin, Exchange1, Exchange2,
                                                 Buy_Price, Sell_Price,
                                                 Trade_Amount_Buy, Trade_Amount_Sell)
    elif Place_Concurrent_Orders is True:
        
        Buy_Order, Sell_Order = Trade_Logic_Complex_Open(Coin, Exchange1, Exchange2,
                                                         Buy_Price, Sell_Price,
                                                         Trade_Amount_Buy, Trade_Amount_Sell,
                                                         'Open')        
    # Check if the orders executed
    
    if Buy_Order is False or Sell_Order is False:
        return False
    
    # Calculate the exit target and update this in the opportunity
    
    Fees = Opportunity['Total_Fees'] 

    Exit_Target = Spread - Target_Profit*2 - Fees # 2*profit cos has to be both sides
    
    Opportunity['Close_Target'] = Exit_Target
   
    #######################################################################
    
    # If everything succeeds, update list of open arbs and update balances        
    
    print 'Trades Successfully Executed, in the Market!'
    log.write('\nTrades Successfully Executed, in the Market!')
    
    Open_Time = time.time()
    
#        if Test_Mode:
    
    if Exchange1['Fees']['currency'] == 'fiat':
        
        Exchange1_Fiat = - round((Trade_Amount_Buy+Buy_Cost)*Buy_Price, 2)
        Exchange1_Coin = round(Trade_Amount_Buy, 8)
        
    elif Exchange1['Fees']['currency'] == 'crypto':
        
        Exchange1_Fiat = - round(Trade_Amount_Buy*Buy_Price, 2)
        Exchange1_Coin = round(Trade_Amount_Buy - Buy_Cost, 8)
        
#        if Exchange2['Fees']['currency'] == 'fiat':
        
    # Exchange2 i.e. short position fees are always in fiat 
        
    Exchange2_Fiat = - round((Trade_Amount_Sell+Sell_Cost)*Sell_Price, 2)
    Exchange2_Coin = - round(Trade_Amount_Sell, 8)
        
#        elif Exchange2['Fees']['currency'] == 'crypto':
#            
#            Exchange2_Fiat = - Trade_Amount_Sell*Sell_Price 
#            Exchange2_Coin = - Trade_Amount_Sell + Sell_Cost
    
    
    Exchange1['Balances'][Fiat[0]] = Exchange1['Balances'][Fiat[0]] + Exchange1_Fiat
    Exchange1['Balances'][Coin] = Exchange1['Balances'][Coin] + Exchange1_Coin        
    Exchange2['Balances'][Fiat[0]] = Exchange2['Balances'][Fiat[0]] + Exchange2_Fiat
    Exchange2['Balances'][Coin] = Exchange2['Balances'][Coin] + Exchange2_Coin
       
    
    Buy_Trade = {'Amount': Trade_Amount_Buy,
                 'Price': Buy_Price,
                 'Order': Buy_Order}
                 
    Sell_Trade = {'Amount': Trade_Amount_Sell,
                 'Price': Sell_Price,
                 'Order': Sell_Order}
    
    
    Current_Arbs.append({'Coin': Coin,
                         'Long': Exchange1,
                         'Short': Exchange2,
                         'Long_Amount': Exchange1_Coin,
                         'Short_Amount': -Exchange2_Coin,
                         'Buy_Trade': Buy_Trade,
                         'Sell_Trade': Sell_Trade,
                         'Open_Spread': Spread,
                         'Long_Exposure': Long_Exposure,
                         'Short_Exposure': Short_Exposure,
                         'Total_Exposure': Long_Exposure + Short_Exposure,
                         'Open_Time': Open_Time,
                         'Close_Target': Exit_Target,
                         'Close_Spread': Current_Exit_Spread,
                         'Close_Min_Spread': Current_Exit_Spread})

    # Remove new arbitrage from Opportunities
    
    for opportunity in Opportunities:
        if opportunity['Long']['Name'] == Name1 and \
            opportunity['Short']['Name'] == Name2:
                Opportunities.remove(opportunity)           
                   
        
    #######################################################################
            
       
def Close(Arb):
    
    Coin = Arb['Coin']
    
    Exchange1 = Arb['Long']
    Exchange2 = Arb['Short']
    
    Name1 = Exchange1['Name']
    Name2 = Exchange2['Name']
    
    Open_Spread = Arb['Open_Spread']
    Open_Time = Arb['Open_Time']

    Spread = Arb['Close_Spread']
    
    Long_Exposure = Arb['Long_Exposure']
    Short_Exposure = Arb['Short_Exposure']
    Total_Exposure = Long_Exposure + Short_Exposure
    
    Exit_Target = Arb['Close_Target']
    
    Orders = {'Opened': {'Buy':Arb['Buy_Trade'], 'Sell':Arb['Sell_Trade']}}
    
#    while True:
        
    if Spread >= Exit_Target:
        
        print '\nLooking for exit...' 
        print Coin + ' / ' + Fiat[0]
        print 'Long: ' + Exchange1['Name'] + ' / ' + \
              'Short: '+ Exchange2['Name']+'. '+ \
              '\nSpread: ' + str(round(Spread,5))+'%. ' + \
              'Target: ' + str(round(Exit_Target,5)) + '%'
        
        log.write('\n\nLooking for exit\n')
        log.write(Coin + ' / ' + Fiat[0] + '\n')
        log.write('Long: ' + Exchange1['Name'] + ' / ' + \
                  'Short: '+ Exchange2['Name']+'. '+ \
                  '\nSpread: ' + str(round(Spread,5))+'%. ' + \
                  'Target: ' + str(round(Exit_Target,5)) + '%')
                              
        return None
           
    # Log information
        
    Print_Exit(Coin, Exchange2, Exchange1, Spread)
    
    Buy_Price = Exchange2['Prices'][Coin]['exit_buy']
    Sell_Price = Exchange1['Prices'][Coin]['exit_sell']
            
    Buy_Amount = round(Arb['Short_Amount'], 8)
    Sell_Amount = round(Arb['Long_Amount'], 8)
    
#        print 'Buy_Amount: ' + str(Buy_Amount)
#        log.write('\nBuy_Amount: ' + str(Buy_Amount))       
        
    Close_ID = Arb['Sell_Trade']['Order']['Position_ID']

    (Buy_Order, Sell_Order) = Trade_Logic_Close(Coin, Exchange2, Exchange1,
                                               Buy_Price, Sell_Price, 
                                               Buy_Amount, Sell_Amount,
                                               Close_ID)
                                                                                        
    if Buy_Order is False or Sell_Order is False:
        return None
    
    # The final buy order closes at market and slippage is tolerated.
    # As this is the final order, the risk of placing limit order and it not
    # not filling is too great. Just place order and calculate slippage.
    
    Close_Buy_Price = Buy_Order['Price']
    
    if Close_Buy_Price > Buy_Price:
        Slippage = (Close_Buy_Price - Buy_Price) / Buy_Price * 100
        print 'Suffered from %s Percent Slippage on Buy Order' %Slippage
        log.write('\nSuffered from %s Percent Slippage on Buy Order' %Slippage)
        
    if Close_Buy_Price < Buy_Price:
        Slippage = (Buy_Price - Close_Buy_Price) / Buy_Price * 100
        print 'Benefited from %s Percent Slippage on Buy Order' %Slippage
        log.write('\nBenefited from %s Percent Slippage on Buy Order' %Slippage)
            
    Orders.update({'Closed': {'Buy': Buy_Order, 'Sell': Sell_Order}})
    
    print 'Trades Successfully Closed!'
    log.write('\nTrades Successfully Closed!')    
    
    Close_Time = time.time()
    
###########################################################################
    
    # Calculate Profit and Update Balances
    
    Long_Buy_Fee = Exchange1['Fees']['buy_fee']/100
    Short_Sell_Fee = Exchange2['Fees']['sell_fee']/100
    
    Long_Sell_Fee = Exchange1['Fees']['sell_fee']/100
    Short_Buy_Fee = Exchange2['Fees']['buy_fee']/100
    
    # Calculate funding costs charged at 0.001% every 4 hours
    
    Funding_Price = Orders['Opened']['Sell']['Price']
    Duration = Close_Time - Open_Time
    No4hours = int(Duration / 3600 / 4) / 1.0
    Funding_Cost = 0.001 + 0.001*No4hours * Buy_Amount * Funding_Price
    
    
    Long_Open_Amount = Buy_Amount - (Buy_Amount * Long_Buy_Fee)
    Short_Open_Amount = Sell_Amount + (Sell_Amount * Short_Sell_Fee)
    
    Long_Close_Amount = Long_Open_Amount - (Long_Open_Amount * Long_Sell_Fee)
    Short_Close_Amount = Short_Open_Amount - (Short_Open_Amount * Short_Buy_Fee)

    Long_Balance = Long_Close_Amount * Sell_Price
    Short_Balance = 2*Short_Exposure - Short_Close_Amount * Close_Buy_Price - Funding_Cost
    
    Long_Profit = Long_Balance - Long_Exposure
    Short_Profit = Short_Balance - Short_Exposure
    
#        if Test_Mode:
        
    Exchange1_Fiat = Exchange1['Balances'][Fiat[0]] + Long_Balance
    Exchange1_Coin = Exchange1['Balances'][Coin] - Sell_Amount
    Exchange2_Fiat = Exchange2['Balances'][Fiat[0]] + Short_Balance
    Exchange2_Coin = Exchange2['Balances'][Coin] + Buy_Amount
    
    Exchange1['Balances'][Fiat[0]] = Exchange1_Fiat
    Exchange1['Balances'][Coin] = Exchange1_Coin
    Exchange2['Balances'][Fiat[0]] = Exchange2_Fiat
    Exchange2['Balances'][Coin] = Exchange2_Coin


# Problem with updating to real balances is margin positions aren't taken into
# into account which gives false reading of the actual balance, best to calculate
# and update manually as above.

#        elif Test_Mode is False:
#            
#            for Exchange in Exchanges:
#                if Exchange == Exchange1 or Exchange == Exchange2:
#                    Exchange['Balances'] = {}
#                    Balances = {}
#                    for Coin in Coins:
#                        Balance = Update_Balances(Exchange, Coin)
#                        Balances.update(Balance)
#                        time.sleep(1)
#                    Exchange.update({'Balances': Balances})            

          
    Income = Long_Balance + Short_Balance
    
    Profit = Income - Total_Exposure
            
    Closed_Arb = {'Coin': Coin,
                  'Long': Exchange1,
                  'Short': Exchange2,
                  'Long Open Amount': Long_Open_Amount,
                  'Short Open Amount': Short_Open_Amount,
                  'Long Close Amount': Long_Close_Amount,
                  'Short Close Amount': Short_Close_Amount,
                  'Long_Balance': Long_Balance,
                  'Short_Balance': Short_Balance,
                  'Orders': Orders,
                  'Open Spread': Open_Spread,
                  'Close Spread': Spread,
                  'Long Profit': Long_Profit,
                  'Short Profit': Short_Profit,
                  'Long Expsoure': Long_Exposure,
                  'Short Expsoure': Short_Exposure,
                  'Total Exposure': Total_Exposure,
                  'Income': Income,
                  'Profit': Profit,
                  'Return': Profit / Total_Exposure * 100,
                  'Open_Time': Open_Time,
                  'Close_Time': Close_Time,
                  'Elapsed_Time': Close_Time - Open_Time}
    
    Successful_Arbs.append(Closed_Arb)
    
    Print_Profit(Closed_Arb)
    
    Profits.append(Profit)
    
    for Arb in Current_Arbs:
        if  Name1 == Arb['Long']['Name'] and Name2 == Arb['Short']['Name']:
            Current_Arbs.remove(Arb)

    Spread_In = Calc_Spread_Entry(Arb)
    

    Exchange1_Fees = Exchange1['Fees']['buy_fee'] + Exchange1['Fees']['sell_fee']
    Exchange2_Fees = Exchange2['Fees']['buy_fee'] + Exchange2['Fees']['sell_fee']
    
    Fees = (Exchange1_Fees + Exchange2_Fees)
    
    Enter_Target = Target_Profit + Fees/2
            
    Opportunities.append({'Coin': Coin,
                          'Long': Exchange1,
                          'Short': Exchange2,      
                          'Open_Spread': Spread_In,
                          'Open_Target': Enter_Target,
                          'Open_Max_Spread': Spread_In,
                          'Total_Fees': Fees})
            
    return None
        
###########################################################################
            
###############################################################################


                
def Run_Optimisation():
    
    Current_Time = datetime.now()
    
    for Opportunity in Opportunities:
        if Opportunity['Open_Spread'] > 0.0:
            Opportunity['History']['Spreads'].append(Opportunity['Open_Spread'])
            Opportunity['History']['Time'].append(Current_Time)
        else:
            Opportunity['History']['Spreads'].append(0.0)
            Opportunity['History']['Time'].append(Current_Time)

                    
    for Opportunity in Opportunities:
        Opportunity['History'].update({'Freq': [[x*0.2, 0, 0] for x in range(-50, 50)]})
        for spread in Opportunity['History']['Spreads']:
            for i, Bin in enumerate(Opportunity['History']['Freq']):
                if spread > Opportunity['History']['Freq'][i][0] and \
                   spread <= Opportunity['History']['Freq'][i+1][0]:
                       Opportunity['History']['Freq'][i][1] += 1
                       Bin = Opportunity['History']['Freq'][i][0]
                       Count = Opportunity['History']['Freq'][i][1]
                       Opportunity['History']['Freq'][i][2] = Bin*Count
        
        
    for Opportunity in Opportunities:
        for i, Bin in enumerate(Opportunity['History']['Freq'][1:]):
            if Opportunity['History']['Freq'][i][2] < Opportunity['History']['Freq'][i-1][2]:
                Optimum_Bin = Opportunity['History']['Freq'][i][0]
        
        Opportunity['History'].update({'Optimum_Spread': Optimum_Bin})

def Sell_All_Crypto():
    
    for Coin in Coins:
        for Exchange in Exchanges:
            Name = Exchange['Name']
            amount = Exchange['Balances'][Coin]
            price = Exchange['Prices'][Coin]['sell']
            fee = Exchange['Fees']['sell_fee']
            total =  price*amount * (1 - fee/100)
            if amount > Exchange['MOQs']['Long'][Coin]:
                                
                Execute_Market_Order(Coin, Exchange, amount, 'sell', 0)
            
                print 'Sold %s %s at %s for %s' %(amount, Coin, Name, total)
                log.write('\nSold %s %s at %s for %s' %(amount, Coin, Name, total))
                
    time.sleep(5)

def Sell_All_Fiat():
    
    for Exchange in Exchanges:
        Name = Exchange['Name']
        total = Exchange['Balances'][Fiat[0]]
        price = Exchange['Prices']['BTC']['entry_buy']
        fee = Exchange['Fees']['buy_fee']
        amount = total/price * (1 - fee/100) * (1 - 0.0005)
        if amount > Exchange['MOQs']['Long']['BTC']:
            Place_Limit_Order('BTC', Exchange, amount, 'buy', price, 0)
        
            print 'Bought %s %s at %s for %s' %(amount, 'BTC', Name, total)
            log.write('Bought %s %s at %s for %s' %(amount, 'BTC', Name, total))
    
    time.sleep(5)
    
def Save_Variables():
    
    Saved_Variables = \
    \
    [Exchanges, Permuatations, Opportunities, Current_Arbs,
    Removed_Exchanges, Successful_Arbs, Profits, Target_Profit, 
    Ref_Time, Jumpstart_Script, Startup_Script, Shutdown_Script,
    Test_Mode, Limit_Qty, Fake_MOQs, Fake_Balances, Fake_Prices, 
    Fake_Fees, Multi_Processing, Place_Concurrent_Orders, 
    Limit_Arbitrages, iteration, Min_Bal, liquid_factor, Attempts,
    Coins, Fiat, Total_Profit]


    with open('Saved_Variables.pkl', 'w') as f:
        pickle.dump(Saved_Variables, f)
        
def Create_Price_Database():
    
    # Create Database if doesn't exist
        
    db_conn = sqlite3.connect('Price_History.db')
    Cursor = db_conn.cursor()
    
    for Exchange in Exchanges:
    
        db_conn.execute("DROP TABLE IF Exists %s" %(Exchange['Name']))
        db_conn.commit()
    
    for Exchange in Exchanges:
        
        try:
                                                    
            db_conn.execute("CREATE TABLE %s (Time INTEGER NOT NULL);" %(Exchange['Name'],))
                                                 
            db_conn.commit()
    
        except sqlite3.OperationalError:
            print "Table could not be created."
        
    for Exchange in Exchanges:
        
        for Coin in Coins:
    
            try:
                                                        
                Cursor.execute("ALTER TABLE %s ADD COLUMN %s REAL" %(Exchange['Name'], Coin+"_Bid"))
                                                     
                
                Cursor.execute("ALTER TABLE %s ADD COLUMN %s REAL" %(Exchange['Name'], Coin+"_Ask"))
                                                     
    
            except sqlite3.OperationalError:
                print "Column could not be created." 
                
    db_conn.close()
    
def Update_Price_Database():
    
    current_time = int(time.time())
    
    db_conn = sqlite3.connect('Price_History.db')
    Cursor = db_conn.cursor()
    
    for Exchange in Exchanges:
        
        
        db_conn.execute("INSERT INTO %s (Time) VALUES(?)" %(Exchange['Name']), (current_time,))
    
                         
        db_conn.commit()
            
        for Coin in Coins:
            
            Cursor.execute("Update %s SET %s = %f WHERE Time = %d" %(Exchange['Name'], Coin+'_Bid', Exchange['Prices'][Coin]['buy'], current_time))
            Cursor.execute("Update %s SET %s = %f WHERE Time = %d" %(Exchange['Name'], Coin+'_Ask', Exchange['Prices'][Coin]['sell'], current_time))
    
    
    db_conn.close()

            
if __name__ == "__main__":
    
    if Jumpstart_Script is False:
        
        Target_Profit = 0.5 # Percent (after fees and slippage)
        
        Create_Price_Database()
    
        log = open('Log_'+str(datetime.now())[0:10]+'.txt', "w")
        profit_file = open('Profits_'+str(datetime.now())[0:10]+'.txt', "w") 
        
        Opportunities = []
        Current_Arbs = []
        Successful_Arbs = []
        Profits = []
        Removed_Exchanges = []
                        
        Exchanges = [exchange for exchange in Exchanges if exchange['Switched-On'] is True]
        
        Permuatations = Get_Perm(Exchanges, Coins)    
        
        Get_All_Fees()
        
        Get_All_Balances()
         
        Get_All_Prices()
        
        for Exchange in Exchanges:
            Get_MOQs(Exchange)
        
        if Startup_Script is True:    
        
            if Test_Mode is False:
                
                Sell_All_Crypto()
                Get_All_Balances()
        
        if Shutdown_Script is True: 
                
            Sell_All_Fiat()
            
            print 'Sold All Fiat, sript terminating!'
            log.write('\nSold All Fiat, sript terminating!')
            
            exit()
            
        
        for Perm in Permuatations:
            Opportunity = Find_Opportunities(Perm)
            if Opportunity is not None:
                Opportunities.append(Opportunity)
        
        # Cannot short ETH on Quoinex        
        for Opportunity in Opportunities:
            if Opportunity['Coin'] == 'ETH' and Opportunity['Short']['Name'] == 'Quoinex':
                Opportunities.remove(Opportunity)
                   
        for Opportunity in Opportunities:
            Opportunity.update({'History': {'Spreads': [], 'Time': []}})
        
        Opportunities = sorted(Opportunities, key= lambda i: i['Open_Spread'], reverse=True)
    
        Print_Balances()
        Print_Prices()
        Print_Arbitrages()
        
        Script_Start_Time = time.time()
        
        Ref_Time = Script_Start_Time/3600
        
        for Exchange in Exchanges:
            Exchange.update({'Strikes': 0})
            
    elif Jumpstart_Script is True:
        
        with open('Saved_Variables.pkl') as f:
            
             [Exchanges, Permuatations, Opportunities, Current_Arbs,
             Removed_Exchanges, Successful_Arbs, Profits, Target_Profit, 
             Ref_Time, Jumpstart_Script, Startup_Script, Shutdown_Script,
             Test_Mode, Limit_Qty, Fake_MOQs, Fake_Balances, Fake_Prices, 
             Fake_Fees, Multi_Processing, Place_Concurrent_Orders, 
             Limit_Arbitrages, iteration, Min_Bal, liquid_factor, Attempts,
             Coins, Fiat, Total_Profit] = pickle.load(f)
    
    while True:
        
        iteration += 1

        start_time = datetime.now()
        
        log = open('Log_'+str(datetime.now())[0:10]+'.txt', "a")
        profit_file = open('Profits_'+str(datetime.now())[0:10]+'.txt', "a")
        
#        Run_Optimisation()
        
        # remove dead exchange for an hour
        
        for Exchange in Exchanges:
      
            Dead_Coins = 0
            for coin in Coins:
                if Exchange['Prices'][coin]['buy'] == 0:
                    Dead_Coins += 1
                    
            if Dead_Coins == len(Coins):
                Exchange['Strikes'] += 1
                
            if Exchange['Strikes'] == 3:
                Exchange.update({'Remove_Time': time.time()})
                Removed_Exchanges.append(Exchange)
                Exchanges.remove(Exchange)
            
            # if exchange working reset the number of strikes
            if Exchange['Strikes'] > 0:
                for coin in Coins:
                    if Exchange['Prices'][coin]['buy'] != 0:
                        Exchange['Strikes'] = 0
                
        # add dead exchange back after an hour has lapsed
        
        Current_Time = time.time()
        Current_Hour = Current_Time/3600
        
        for Exchange in Removed_Exchanges:
            if Current_Hour - Exchange['Remove_Time']/3600 > 1:
                Exchange.pop('Remove_Time', 0)
                Exchange['Strikes'] = 0
                Exchanges.append(Exchange)
                Removed_Exchanges.remove(Exchange)
                
        # Increase or decrease profit based on number of positions found

        if Current_Hour - Ref_Time > 1:
            if len(Current_Arbs) >= 2:
                Target_Profit += 0.1
            else:
                Target_Profit -= 0.1
                
            if Target_Profit <= 0.1:
                Target_Profit = 0.1
            
            # Reset the timer
            Ref_Time = Current_Hour
            
                
        Get_All_Prices()  
        
        # Save price data to sqlite database

        Update_Price_Database()
              

        for Opportunity in Opportunities:
            Update_Opportunities(Opportunity)
    
        Opportunities = sorted(Opportunities, key= lambda i: i['Open_Spread'], reverse=True)
            
        Print_Balances()
        Print_Prices()
        
#        time.sleep(2)
        
        for Opportunity in Opportunities: # opening multiple opps takes too long
            Previous_Num_Opps = len(Current_Arbs)
            if Open(Opportunity) is False:
#                time.sleep(2)
                break
            if len(Current_Arbs) > Previous_Num_Opps:
#                time.sleep(2)
                break
                
        for Arb in Current_Arbs:
            Update_Arb(Arb)
    
        Print_Arbitrages()
        
#        time.sleep(2)
                
        for Arb in Current_Arbs:
            Close(Arb)
            
        Total_Profit = round(sum(Profits), 2)
        
        print '\nTotal Profit Since Running: ' + str(Total_Profit) + ' Euro'
        log.write('\n\nTotal Profit Since Running: ' + str(Total_Profit) + ' Euro')
        
        end_time = datetime.now()    
        loop_time = end_time - start_time
        
        print '\nTime to execute loop is: ' + str(loop_time) + 's'
        log.write('\n\nTime to execute loop is: ' + str(loop_time) + 's')
        
        Save_Variables()
                        
        print '\nScanning Markets',
        time.sleep(1); print'.',
        time.sleep(1); print'.',
        time.sleep(1); print'.'
        print '\n'+str(datetime.now())+'\n'
        time.sleep(3)
                                    
        log.write('\n\nScanning Markets')      
        log.write('\n\n'+str(datetime.now())+'\n')
            
        log.close()
        profit_file.close()
        
    
        
