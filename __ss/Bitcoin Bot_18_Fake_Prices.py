import itertools
import time
from datetime import datetime
import uuid
import winsound
import traceback
import multiprocessing
import pprint
from functools import partial
import random

import krakenex #Shorting ok
import theRock #Shorting ok
import GDAX # Shorting disabled server side until further notice
import bitstamp #Shorting coming soon
import bl3p
import cexapi
import wex
import bitbay
import quoinex

#import xBTCe # Shorting coming soon / Need to figure out private client

import Keys

###############################################################################

# Set all these to True to run in a completely contained offline environment

Test_Mode = True   #### If set to false will place real orders on exchanges!
Fake_Balances = False #### Use real or fake balances
Fake_Prices = True   #### Use real or fake prices
Fake_Fees = True  #### Use real or fake fees

iteration = 1 # starts the main loop counter, only used for fake prices


Kraken = {'Name': 'Kraken', 'Shorting': True} ##
Bitstamp = {'Name': 'Bitstamp', 'Shorting': False}
Gdax = {'Name': 'Gdax', 'Shorting': False}
Bl3p = {'Name': 'Bl3p', 'Shorting': False}
TheRock = {'Name': 'theRock', 'Shorting': False} # No naked shorts :(
Cex = {'Name': 'Cex', 'Shorting': True}
Wex = {'Name': 'Wex', 'Shorting': False}
BitBay = {'Name': 'BitBay', 'Shorting': False}
Quoinex = {'Name': 'Quoinex', 'Shorting': True}

Min_Bal = 30.00 # Min Balance to execute on
Target_Profit = 0.2 # Percent (after fees and slippage)
liquid_factor = 2.0 # multiplied by trade amount, determine if adequate liquidity

Attempts = 3 # re-tries for server
Attempts += 1 # add 1 to actually execute a number of attempts due tp range function behviour

Coins = ['BTC', 'LTC', 'ETH']
#Coins = ['BTC']
Fiat = ['EUR']


###############################################################################


def Kraken_Private_Client(query, params={}):
    
    Key = Keys.Kraken()
    client = krakenex.API(Key['key'],Key['secret']).query_private(query,params)
    return client
    
def Kraken_Fees():
    
    if Coins[0] == 'BTC':
        Coin = 'XBT'
    
    pair = 'X'+Coin+'Z'+Fiat[0]
    
    API = krakenex.API()
    fees = API.query_public('AssetPairs', {'info': 'fees'})['result'][pair]
    
    return {'buy_fee': float(fees['fees'][0][1]), 
            'sell_fee': float(fees['fees'][0][1]),
            'buy_maker_fee': float(fees['fees_maker'][0][1]),
            'sell_maker_fee': float(fees['fees_maker'][0][1])}
         
def Kraken_Balances(Coin):
    
    if Coin == 'BTC':
        coin = 'XBT'
    else: coin = Coin
    
    balance = Kraken_Private_Client('Balance')['result']
    
    Coin_Balance = round(float(balance['X'+coin]), 8)
    Fiat_Balance = round(float(balance['ZEUR']), 2)

    return {Coin: Coin_Balance, Fiat[0]: Fiat_Balance}
    
def Kraken_Limit_Order(Coin, amount, side, price, leverage):
    
    if Coin == 'BTC':
        coin = 'XBT'
    else: coin = Coin
    
    pair = 'X'+coin+'Z'+Fiat[0]
    
    if leverage == 0.0:        
    
        params = {'pair': pair,
                  'type': side,
                  'ordertype': 'market',
                  'volume': str(amount),} # 2 to 5 times
    else:
        
        params = {'pair': pair,
              'type': side,
              'ordertype': 'market',
              'volume': str(amount),
              'leverage': str(leverage)} # 2 to 5 times             
    
    Order = Kraken_Private_Client('AddOrder', params)

    print 'Message from Kraken: ' + str(Order)
    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    return Order
    
def Kraken_Market_Order(Coin, amount, side, leverage):
    
    if Coin == 'BTC':
        coin = 'XBT'
    else: coin = Coin
    
    pair = 'X'+coin+'Z'+Fiat[0]
    
    if leverage == 0.0:        
    
        params = {'pair': pair,
                  'type': side,
                  'ordertype': 'market',
                  'volume': str(amount),} # 2 to 5 times
    else:
        
        params = {'pair': pair,
              'type': side,
              'ordertype': 'market',
              'volume': str(amount),
              'leverage': str(leverage)} # 2 to 5 times
              
    Order = Kraken_Private_Client('AddOrder', params)

    print 'Message from Kraken: ' + str(Order)
    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    return Order
    
def Kraken_Check_Order(ref):    
    
    params = {'txid': ref}
    
    Order = Kraken_Private_Client('QueryOrders', params)

    print 'Message from Kraken: ' + str(Order)
    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    return Order
    
  
def Kraken_Orderbook(Coin):
    
    if Coin == 'BTC':
        coin = 'XBT'
    else: coin = Coin
    
    pair = 'X'+coin+'Z'+Fiat[0]
    
    API = krakenex.API()    
    Orderbook = API.query_public('Depth', {'pair': pair})['result'][pair]
    
    Asks = Orderbook['asks']    
    Bids = Orderbook['bids']
    
    return (Asks, Bids)
    
    
def Kraken_Filled(Order):
    
    Order_ID = Order['ID']
    
    isFilled = Kraken_Check_Order(Order_ID)['result'][Order_ID]['status']
    
    if str(isFilled) == 'closed':
        Filled = True
    else: Filled = False
    
    return Filled
    
def Kraken_Cancel_Order(ref):
    
    params = {'txid': ref}
    
    Order = Kraken_Private_Client('CancelOrder', params)
    
    print 'Message from Kraken: ' + str(Order)
    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    if Order['result']['count'] == 1:
        Order_Cancelled = True
    
    return Order_Cancelled
    
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
    
def Bitstamp_Fees():
    
    pair = Coins[0].lower(), Fiat[0].lower()
    balance = Bitstamp_Private_Client().account_balance(pair[0], pair[1])
    
    fee = float(balance['fee'])
    
    return {'buy_fee': fee, 'sell_fee': fee}    
    
def Bitstamp_Limit_Order(Coin, amount, side, price):
    
    pair = Coin.lower(), Fiat[0].lower()    
    Order = Bitstamp_Private_Client().limit_order(str(amount), str(side),
                                                  str(price), pair[0], pair[1])  

    print 'Message from Bitstamp: ' + str(Order)
    log.write('\nMessage from Bitstamp: ' + str(Order)) 
    
    return Order
    
def Bitstamp_Market_Order(Coin, amount, side):
    
    pair = Coin.lower(), Fiat[0].lower()    
    Order = Bitstamp_Private_Client().market_order(str(amount), str(side), pair[0], pair[1])  

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

    return {'buy_fee': buy_fee, 'sell_fee': sell_fee}

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
              'size': str(amount)}
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
    
    Order = GDAX_Private_Client.getOrder(ref)

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
    
    isFilled = str(Gdax_Check_Order(Order_ID))['settled']
    
    if  isFilled == 'true':
        Filled = True
    else: Filled = False
    
    return Filled
    
def Gdax_Cancel_Order(ref):    
    
    Order = GDAX_Private_Client().cancelOrder(ref)
    
    print 'Message from Gdax: ' + str(Order)
    log.write('\nMessage from Gdax: ' + str(Order)) 
    
    if Order[0] == 'ref':
        Order_Cancelled = True
    
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
    
def Bl3p_Fees():
    
    balances = Bl3p_Private_Client().getBalances()    
    fee = float(balances['data']['trade_fee']) # plus 0.01eur per trade
    
    return {'buy_fee': fee, 'sell_fee': fee}
    
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
    
def Bl3p_Filled(Order):
    
    Order_ID = Order['ID'] 
    
    isFilled = str(Bl3p_Check_Order(Order_ID)['data']['status'])
    
    if  isFilled == 'closed':
        Filled = True
    else: Filled = False
    
    return Filled
        
def Bl3p_Cancel_Order(ref):
    
    pair = Coins + Fiat[0]    
    Order = Bl3p_Private_Client().cancelOrder(pair, ref)
    
    print 'Message from Bl3p: ' + str(Order)
    log.write('\nMessage from Bl3p: ' + str(Order)) 
    
    if Order['result'] == 'success':
        Order_Cancelled = True

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
            Coin_Balance = round(float(balance['trading_balance']),2)
        elif balance['currency'] == Fiat[0]:
            Fiat_Balance = round(float(balance['trading_balance']),2) 
        
    return {Coin: Coin_Balance, Fiat[0]: Fiat_Balance}
    
def theRock_Fees():
    
    pair = Coins[0] + Fiat[0] 
    funds = theRock_Private_Client().Funds()['funds']
    
    for fund in funds:
        if fund['id'] == pair:
            buy_fee = fund['buy_fee']
            sell_fee = fund['sell_fee']
            
    return {'buy_fee': buy_fee, 'sell_fee': sell_fee}
    
def theRock_Limit_Order(Coin, amount, side, price, leverage):
    
    pair = Coin.lower() + Fiat[0].lower()
    Order = theRock_Private_Client().PlaceOrder(pair, str(amount),
                                                side, str(price), float(leverage))
                                                
    print 'Message from theRock: ' + str(Order)
    log.write('\nMessage from theRock: ' + str(Order))
    
    return Order
    
def theRock_Market_Order(Coin, amount, side, leverage):
    
    if side == 'buy':
            price = theRock['entry_buy'] * 1+0.00005 # beats market price
    elif side == 'sell':
            price = theRock['entry_sell'] * 1-0.00005 # beats market price
    
    pair = Coin.lower() + Fiat[0].lower()
    Order = theRock_Private_Client().PlaceOrder(pair, str(amount),
                                                side, str(price), float(leverage))
                                                
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
    
def theRock_Filled(Order):
    
    Order_ID = Order['ID']

    isFilled = theRock_Check_Order(Order_ID)['status']
    
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
            'sell_fee': float(fees['sell'])}
         
def Cex_Balances(Coin):   

    balance = Cex_Private_Client('balance')
        
    Coin_Balance = round(float(balance[Coin]['available']),8)
    Fiat_Balance = round(float(balance[Fiat[0]]['available']),2)
    
    return {Coin: Coin_Balance, Fiat[0]: Fiat_Balance}
    
def Cex_Open_Position(Coin, amount, side, price, leverage):
    
    pair = Coin + '/' + Fiat[0]
    
    if side == 'buy':
        side = 'long'
    elif side == 'sell':
        side = 'short'
        
    params = {'ptype': side,
              'anySlippage': 'false',
              'amount': str(amount),
              'eoprice': str(price),
              'leverage': str(leverage)} # 2 or 3 times             
    
    Order = Cex_Private_Client('open_position/'+pair, params)

    print 'Message from Cex: ' + str(Order)
    log.write('\nMessage from Cex: ' + str(Order)) 
    
    return Order
    
def Cex_Limit_Order(Coin, amount, side, price):
    
    pair = Coin + '/' + Fiat[0]
    
    params = {'type': side,
              'amount': str(amount), 
              'price': str(price)}
              
    Order = Cex_Private_Client('place_order/'+pair, params)

    print 'Message from Cex: ' + str(Order)
    log.write('\nMessage from Cex: ' + str(Order)) 
    
    return Order
    
def Cex_Market_Order(Coin, amount, side):
    
    pair = Coin + '/' + Fiat[0]
    
    params = {'type': side,
              'order_type': "market",
              'amount': str(amount)} 

              
    Order = Cex_Private_Client('place_order/'+pair, params)

    print 'Message from Cex: ' + str(Order)
    log.write('\nMessage from Cex: ' + str(Order)) 
    
    return Order
    
def Cex_Check_Order(ref):    
    
    params = {'id': ref}
    
    Order = Cex_Private_Client('get_order', params)

    print 'Message from Cex: ' + str(Order)
    log.write('\nMessage from Cex: ' + str(Order)) 
    
    return Order
  

def Cex_Orderbook(Coin):
    
    pair = Coin + '/' + Fiat[0]
    Orderbook = Cex_Private_Client('order_book/'+pair+'/')
    
    Asks = Orderbook['asks']
    Bids = Orderbook['bids']
    
    return (Asks, Bids)
    
    
def Cex_Filled(Order):
    
    Order_ID = Order['id']
    
    isFilled = Cex_Check_Order(Order_ID)['remains']
    
    if float(isFilled) > 0:
        Filled = False
    else: Filled = True
    
    return Filled
    
def Cex_Cancel_Order(ref):
    
    params = {'id': ref}
    
    Order = Cex_Private_Client('cancel_order', params)
    
    print 'Message from Cex: ' + str(Order)
    log.write('\nMessage from Cex: ' + str(Order)) 
    
    if Order == 'True':
        Order_Cancelled = True
    else:
        Order_Cancelled = False
    
    return Order_Cancelled  


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
            'sell_fee': float(fee)}
         
def Wex_Balances(Coin): 

    balances = Wex_Private_Client('getInfo')['funds']   
    
    Coin_Balance = round(float(balances[Coin.lower()]), 8)
    Fiat_Balance = round(float(balances[Fiat[0].lower()]), 2)
    
    return {Coin: Coin_Balance, Fiat[0]: Fiat_Balance}
    
def Wex_Limit_Order(Coin, amount, side, price):
    
    pair = Coin.lower()+'_'+Fiat[0].lower()
    
    Order = Wex_Private_Client('Trade',pair=pair,type=side,amount=amount,rate=price)

    print 'Message from Wex: ' + str(Order)
    log.write('\nMessage from Wex: ' + str(Order)) 
    
    return Order
    
def Wex_Market_Order(Coin, amount, side):
    
    pair = Coin.lower()+'_'+Fiat[0].lower()
    
    if side == 'buy':
        price = 0.1
    elif side == 'sell':
        price = 1.0e8
              
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
    
    
def Wex_Filled(Order):
    
    Order_ID = Order['order_id']
    
    isFilled = Wex_Check_Order(Order_ID)['status']
    
    if str(isFilled) == 1:
        Filled = True
    else: Filled = False
    
    return Filled

def Wex_Cancel_Order(ref):
    
    Order = Wex_Private_Client('CancelOrder', order_id=ref)
    
    print 'Message from Wex: ' + str(Order)
    log.write('\nMessage from Wex: ' + str(Order)) 
    
    if Order[ref] == ref:
        Order_Cancelled = True
    
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
            'sell_fee': float(fee)}
         
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
            price = BitBay['entry_buy'] * 1+0.00005
    elif side == 'sell':
            price = BitBay['entry_sell'] * 1-0.00005
              
    Order = BitBay_Private_Client().place_order(pair, amount, side, price)

    print 'Message from Bitbay: ' + str(Order)
    log.write('\nMessage from Bitbay: ' + str(Order)) 
    
    return Order
    
def BitBay_Check_Orders():
        
    Order = BitBay_Private_Client().get_order()

    print 'Message from Bitbay: ' + str(Order)
    log.write('\nMessage from Bitbay: ' + str(Order)) 
    
    return Order
    
    
def BitBay_Filled(Order):
    
    Order_ID = Order['order_id']
    
    Orders = BitBay_Check_Orders()
    
    for item in Orders:
        if item['order_id'] == Order_ID:
            
            isFilled = item['status']
    
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
            'sell_maker_fee': float(sell_maker_fee)}

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
    
    quantity = Order['quantity']
    filled_quantity = Order['filled_quantity']
    
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
    
    return Order_Cancelled   
        
###############################################################################
###############################################################################
        
    
def Update_Balances(Exchange, Coin):
    
    # Updates the account balances
            
    try:
        
        if Exchange['Name'] == 'Kraken':
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
        
        return {Coin: Balances[Coin], Fiat[0]: Balances[Fiat[0]]}
        
    except:

#        print 'Failed to Update Balances for %s' % Exchange['Name']
#        log.write('\nFailed to Update Balances for %s' % Exchange['Name'])
        return {Coin: 0.0}
    
        
def Get_Fees(Exchange):
  
    name = Exchange['Name']
    
    if Fake_Prices is False:
            
        try:
            if name == 'Kraken':
                Exchange.update({'Fees': Kraken_Fees()})
            elif name == 'Bitstamp':
                Exchange.update({'Fees': Bitstamp_Fees()})
            elif name == 'Gdax':
                Exchange.update({'Fees': Gdax_Fees()})
            elif name == 'Bl3p':
                Exchange.update({'Fees': Bl3p_Fees()})
            elif name == 'theRock':
                Exchange.update({'Fees': theRock_Fees()})
            elif name == 'Cex':
                Exchange.update({'Fees': Cex_Fees()})
            elif name == 'Wex':
                Exchange.update({'Fees': Wex_Fees()})
            elif name == 'BitBay':
                Exchange.update({'Fees': BitBay_Fees()})
            elif name == 'Quoinex':
                Exchange.update({'Fees': Quoinex_Fees()})
                
        except:
            print 'Failed to Update Fees for %s' %name
            log.write('\nFailed to Update Fees for %s' %name)
        
        else:
            return None

    elif Fake_Prices is True:
        
        Fake_Fees = {'buy_fee': 0.2, 
                     'sell_fee': 0.2,
                     'buy_maker_fee': 0.2,
                     'sell_maker_fee': 0.2}
        
        if name == 'Kraken':
            Exchange.update({'Fees': Fake_Fees})
        elif name == 'Bitstamp':
            Exchange.update({'Fees': Fake_Fees})
        elif name == 'Gdax':
            Exchange.update({'Fees': Fake_Fees})
        elif name == 'Bl3p':
            Exchange.update({'Fees': Fake_Fees})
        elif name == 'theRock':
            Exchange.update({'Fees': Fake_Fees})
        elif name == 'Cex':
            Exchange.update({'Fees': Fake_Fees})
        elif name == 'Wex':
            Exchange.update({'Fees': Fake_Fees})
        elif name == 'BitBay':
            Exchange.update({'Fees': Fake_Fees})
        elif name == 'Quoinex':
            Exchange.update({'Fees': Fake_Fees})

        
def Get_Orderbook(Exchange, Coin):
    
    name = Exchange['Name']
    
    if Fake_Prices is False:
        
        try:
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
            return Orderbook
    
    elif Fake_Prices is True:
                
        iterate = iteration % 2
    
        if iterate == 0:
            
            if Coin == 'BTC':
                
                Buy_Price = 5144.06
                Sell_Price = 5262.16
                
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
            
            if name == 'Kraken':
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
            
            if name == 'Kraken':
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
    
def Get_Perm(exchanges, Coin):
    
    
    Exchange_Iterations = list(itertools.permutations(exchanges, 2))
    
    Exchange_Iterations = [dict(zip(('Long', 'Short'), i)) for i in Exchange_Iterations if i[1]['Shorting'] is True]

    Permuatations = list(itertools.product(Coins, Exchange_Iterations))
        
    Permuatationss = [{'Coin': i[0], 'Long': i[1]['Long'], 'Short': i[1]['Short']} for i in Permuatations]

    return Permuatationss
    

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
            
    if Arb['Long']['Prices'][Coin]['buy'] == 0 or Arb['Short']['Prices'][Coin]['buy'] == 0:
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
    
    Enter_Target = Target_Profit + Fees/2
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
        
    Opportunity.update({'Open_Spread': Spread_In,
                    'Open_Max_Spread': New_Max_Spread})
    

def Check_Order_Filled(Exchange, Order, side):
       
    if Test_Mode:
        return True
    
    name = Exchange['Name']

    for attempt in range(1, Attempts + 3):     

        try:
            if Exchange['Name'] == 'Kraken':
                Filled = Kraken_Filled(Order) 
                
            elif Exchange['Name'] == 'Bitstamp': 
                Filled = Bitstamp_Filled(Order)
                
            elif Exchange['Name'] == 'Gdax':
                Filled = Gdax_Filled(Order)
                    
            elif Exchange['Name'] == 'Bl3p':
                Filled = Bl3p_Filled(Order)
                    
            elif Exchange['Name'] == 'theRock':
                Filled = theRock_Filled(Order)

            elif Exchange['Name'] == 'Cex':
                Filled = Cex_Filled(Order)

            elif Exchange['Name'] == 'Wex':
                Filled = Wex_Filled(Order)
                
            elif Exchange['Name'] == 'BitBay':
                Filled = BitBay_Filled(Order)
                
            elif Exchange['Name'] == 'Quoinex':
                Filled = Quoinex_Filled(Order)
                
        except:
            
            print side+' order at %s waiting to fill on attempt: %i' %(name,
                                                                       attempt)
            log.write('\n'+side+' order at %s waiting to fill attempt %i'%(name,
                                                                           attempt))
                                                                           
            print 'Message: ' + [i for i in traceback.format_exc().split('\n') if i][-1]
            log.write('Message: ' + [i for i in traceback.format_exc().split('\n') if i][-1])
                                                             
            time.sleep(10)
            
            continue
        
        else:
            
            if Filled == False:
                continue
            else:
                return Filled
          
    else:                                                  
        print side + ' order at %s failed to fill...' %Exchange['Name']
        log.write('\n'+side+' order at %s failed to fill...' %Exchange['Name'])
        return False 
              
    
def Cancel_Order(exchange, ref):
       
    # Looks for which exchange to cancel the order on
    
    name = exchange['Name']
    
    if Test_Mode:
        return True
        
    else:
        
        for attempt in range(1, Attempts):            
            try:
                if exchange['Name'] == 'Kraken':
                    Cancelled = Kraken_Cancel_Order(ref)
                    
                elif exchange['Name'] == 'Bitstamp':
                    Cancelled = Bitstamp_Cancel_Order(ref)
                    
                elif exchange['Name'] == 'Gdax':
                    Cancelled = Gdax_Cancel_Order(ref)
                    
                elif exchange['Name'] == 'Bl3p':
                    Cancelled = Bl3p_Cancel_Order(ref)
                    
                elif exchange['Name'] == 'theRock':
                    Cancelled = theRock_Cancel_Order(ref)
                    
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
                
                time.sleep(3)
                continue
        
            else:
                return Cancelled
      
        else:                                                  
            print 'Failed to Cancel Order at %s ' %(exchange['Name'])
            log.write('\nFailed to Cancel Order at %s ' %(exchange['Name']))
            return False
            
    
def Place_Limit_Order(Exchange, amount, side, price, Leverage):
       
    # Looks which exchange to execute the order on
    
    if Test_Mode:
        
        if Exchange['Name'] == 'Kraken':        
            Kraken_Order_ID = str(uuid.uuid4().hex) # generates 32 char fake ID
            Open_Order = {'ID': Kraken_Order_ID}        
            
        elif Exchange['Name'] == 'Bitstamp':            
            Bitstamp_Order_ID = str(uuid.uuid4().hex)
            Open_Order = {'ID': Bitstamp_Order_ID}
        
        elif Exchange['Name'] == 'Gdax':            
            Gdax_Order_ID = str(uuid.uuid4().hex)
            Open_Order = {'ID': Gdax_Order_ID}
            
        elif Exchange['Name'] == 'Bl3p':            
            Bl3p_Order_ID = str(uuid.uuid4().hex)
            Open_Order = {'ID': Bl3p_Order_ID}
            
        elif Exchange['Name'] == 'theRock':            
            theRock_Order_ID = str(uuid.uuid4().hex)
            Open_Order = {'ID': theRock_Order_ID}
            
        elif Exchange['Name'] == 'Cex':            
            Cex_Order_ID = str(uuid.uuid4().hex)
            Open_Order = {'ID': Cex_Order_ID} 

        elif Exchange['Name'] == 'Wex':            
            Wex_Order_ID = str(uuid.uuid4().hex)
            Open_Order = {'ID': Wex_Order_ID}
            
        elif Exchange['Name'] == 'BitBay':            
            BitBay_Order_ID = str(uuid.uuid4().hex)
            Open_Order = {'ID': BitBay_Order_ID}

        elif Exchange['Name'] == 'Quoinex':            
            Quoinex_Order_ID = str(uuid.uuid4().hex)
            Open_Order = {'ID': Quoinex_Order_ID}
            
        return Open_Order
        
    elif Test_Mode is False:
    
        if Exchange['Name'] == 'Kraken':
            Kraken_Open_Order = Kraken_Limit_Order(amount, side, price, Leverage)
            Kraken_Order_ID =  str(Kraken_Open_Order['result']['txid'][0])
            Open_Order = {'ID': Kraken_Order_ID}
            
        elif Exchange['Name'] == 'Bitstamp':            
            Bitstamp_Open_Order = Bitstamp_Limit_Order(amount, side, price)
            Bitstamp_Order_ID = str(Bitstamp_Open_Order['id'])
            Open_Order = {'ID': Bitstamp_Order_ID}
        
        elif Exchange['Name'] == 'Gdax':            
            Gdax_Open_Order = Gdax_Limit_Order(amount, side, price)
            Gdax_Order_ID = str(Gdax_Open_Order['id'])
            Open_Order = {'ID': Gdax_Order_ID}
            
        elif Exchange['Name'] == 'Bl3p':            
            Bl3p_Open_Order = Bl3p_Limit_Order(amount*100000000, side, price*100000)
            Bl3p_Order_ID = str(Bl3p_Open_Order['data']['order_id'])
            Open_Order = {'ID': Bl3p_Order_ID}      
            
        elif Exchange['Name'] == 'theRock':            
            theRock_Open_Order = theRock_Limit_Order(amount, side, price, Leverage)
            theRock_Order_ID = str(theRock_Open_Order['id'])
            Open_Order = {'ID': theRock_Order_ID}
                  
        elif Exchange['Name'] == 'Cex':
            
            if Leverage == 0.0:
                Cex_Open_Order = Cex_Limit_Order(amount, side, price)
                Cex_Order_ID = str(Cex_Open_Order['id'])
                Open_Order = {'ID': Cex_Order_ID}
                
            elif Leverage != 0.0:
                Cex_Open_Order = Cex_Open_Position(amount, side, price, Leverage)
                Cex_Order_ID = str(Cex_Open_Order['id'])
                Open_Order = {'ID': Cex_Order_ID}
                
        elif Exchange['Name'] == 'Wex':            
            Wex_Open_Order = Wex_Limit_Order(amount, side, price, Leverage)
            Wex_Order_ID = str(Wex_Open_Order['id'])
            Open_Order = {'ID': Wex_Order_ID}
            
        elif Exchange['Name'] == 'BitBay':            
            BitBay_Open_Order = BitBay_Limit_Order(amount, side, price, Leverage)
            BitBay_Order_ID = BitBay_Open_Order['id']
            Open_Order = {'ID': BitBay_Order_ID}

        elif Exchange['Name'] == 'Quoinex':            
            Quoinex_Open_Order = Quoinex_Limit_Order(amount, side, price, Leverage)
            Quoinex_Order_ID = Quoinex_Open_Order['id']
            Open_Order = {'ID': Quoinex_Order_ID}
            
        return Open_Order
        
def Place_Market_Order(Exchange, amount, side, leverage):    
    
    if Test_Mode:
    
        if Exchange['Name'] == 'Kraken':        
            Kraken_Order_ID = str(uuid.uuid4().hex) # generates 32 char fake ID
            Open_Order = {'ID': Kraken_Order_ID}        
            
        elif Exchange['Name'] == 'Bitstamp':            
            Bitstamp_Order_ID = str(uuid.uuid4().hex)
            Open_Order = {'ID': Bitstamp_Order_ID}
        
        elif Exchange['Name'] == 'Gdax':            
            Gdax_Order_ID = str(uuid.uuid4().hex)
            Open_Order = {'ID': Gdax_Order_ID}
            
        elif Exchange['Name'] == 'Bl3p':            
            Bl3p_Order_ID = str(uuid.uuid4().hex)
            Open_Order = {'ID': Bl3p_Order_ID}
            
        elif Exchange['Name'] == 'theRock':            
            theRock_Order_ID = str(uuid.uuid4().hex)
            Open_Order = {'ID': theRock_Order_ID}
            
        elif Exchange['Name'] == 'Cex':            
            Cex_Order_ID = str(uuid.uuid4().hex)
            Open_Order = {'ID': Cex_Order_ID} 
    
        elif Exchange['Name'] == 'Wex':            
            Wex_Order_ID = str(uuid.uuid4().hex)
            Open_Order = {'ID': Wex_Order_ID}
            
        elif Exchange['Name'] == 'BitBay':            
            BitBay_Order_ID = str(uuid.uuid4().hex)
            Open_Order = {'ID': BitBay_Order_ID}
    
        elif Exchange['Name'] == 'Quoinex':            
            Quoinex_Order_ID = str(uuid.uuid4().hex)
            Open_Order = {'ID': Quoinex_Order_ID}
            
        return Open_Order

    elif Test_Mode is False:

        if Exchange['Name'] == 'Kraken':        
            Kraken_Open_Order = Kraken_Market_Order(amount, side, leverage)
            Kraken_Order_ID =  str(Kraken_Open_Order['result']['txid'][0])
            Open_Order = {'ID': Kraken_Order_ID}    
            
        elif Exchange['Name'] == 'Bitstamp':            
            Bitstamp_Open_Order = Bitstamp_Market_Order(amount, side)
            Bitstamp_Order_ID = str(Bitstamp_Open_Order['id'])
            Open_Order = {'ID': Bitstamp_Order_ID}              
        
        elif Exchange['Name'] == 'Gdax':            
            Gdax_Open_Order = Gdax_Market_Order(amount, side)
            Gdax_Order_ID = str(Gdax_Open_Order['id'])
            Open_Order = {'ID': Gdax_Order_ID}   
            
        elif Exchange['Name'] == 'Bl3p':            
            Bl3p_Open_Order = Bl3p_Market_Order(amount*100000000, side)
            Bl3p_Order_ID = str(Bl3p_Open_Order['data']['order_id'])
            Open_Order = {'ID': Bl3p_Order_ID}  
            
        elif Exchange['Name'] == 'theRock':            
            theRock_Open_Order = theRock_Market_Order(amount, side)
            theRock_Order_ID = str(theRock_Open_Order['id'])
            Open_Order = {'ID': theRock_Order_ID}              
            
        elif Exchange['Name'] == 'Cex':            
            Cex_Open_Order = Cex_Market_Order(amount, side)
            Cex_Order_ID = str(Cex_Open_Order['data']['order_id'])
            Open_Order = {'ID': Cex_Order_ID}
            
        elif Exchange['Name'] == 'Wex':            
            Wex_Open_Order = Wex_Market_Order(amount, side)
            Wex_Order_ID = str(Wex_Open_Order['data']['order_id'])
            Open_Order = {'ID': Wex_Order_ID}
            
        elif Exchange['Name'] == 'BitBay':            
            BitBay_Open_Order = BitBay_Market_Order(amount, side)
            BitBay_Order_ID = BitBay_Open_Order['data']['order_id']
            Open_Order = {'ID': BitBay_Order_ID}  
            
        elif Exchange['Name'] == 'Quoinex':            
            Quoinex_Open_Order = Quoinex_Market_Order(amount, side)
            Quoinex_Order_ID = Quoinex_Open_Order['id']
            Open_Order = {'ID': Quoinex_Order_ID}
            
        return Open_Order
        
def Execute_Limit_Order(Exchange, Amount, Side, Price, Leverage):
    
    # Tries to execute an order on an exchange, catches error if failed
    
    name = Exchange['Name']
    Open_Order = {'Name': name, 'Amount': Amount, 'Side': Side, 'Price': Price}
      
    try:
        
        Order = Place_Limit_Order(Exchange, Amount, Side, Price, Leverage)
    
    except:     
                                                                  
        print 'Message: ' + [i for i in traceback.format_exc().split('\n') if i][-1]
        log.write('Message: ' + [i for i in traceback.format_exc().split('\n') if i][-1])
        
        print Side + ' Order failed at %s' %name
        log.write('\n' + Side + ' Order failed at %s' %name)      
     
        return {'Order': Open_Order, 'Placed': False} # returns blank order from top of function
 
    else:
                                             
        Open_Order.update(Order)
        return {'Order': Open_Order, 'Placed': True}


def Execute_Market_Order(Exchange, Amount, Side, Leverage):
    
    # Tries to execute an order on an exchange, catches error if failed
    
    name = Exchange['Name']
    Open_Order = {'Name': name, 'Amount': Amount, 'Side': Side}
      
    try:
        Order = Place_Market_Order(Exchange, Amount, Side, Leverage)                
    
    except: 
                                                                  
        print 'Message: ' + [i for i in traceback.format_exc().split('\n') if i][-1]
        log.write('Message: ' + [i for i in traceback.format_exc().split('\n') if i][-1])
        
        print Side + ' Order failed at %s on all attempts' %name
        log.write('\n' + Side + ' Order failed at %s on all attempts' %name)
     
        return {'Order': Open_Order, 'Placed': False} # returns blank order from top of function            
    
    else:
        Open_Order.update(Order)
        return {'Order': Open_Order, 'Placed': True}
          
    
def Print_Entry(Coin, Exchange1, Exchange2, Spread):
    
    #    winsound.PlaySound(r'cash.wav', winsound.SND_ASYNC)
    
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
                        
    log.write('\nAttempting Trade...')
    

def Print_Exit(Coin, Exchange2, Exchange1, spread):
    
    #    winsound.PlaySound(r'cash.wav', winsound.SND_ASYNC)
    
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
    
    Coin = Closed_Arb['Coin']
    
    Exchange1 = Closed_Arb['Long']
    Exchange2 = Closed_Arb['Short']
    Profit = Closed_Arb['Profit']
    Return = Closed_Arb['Return']
    
    print '\n' + \
           Coin + ' / ' + Fiat[0] + '\n' + \
          'Long: ' + Exchange1['Name'] + ' / '+ \
          'Short: ' + Exchange2['Name'] + ' ' \
          '\nProfit: ' + str(Profit) + ' ' + Fiat[0] + \
          '\nReturn: ' + str(Return) + ' %' \
          '\nStart Time: ' + str(Arb['Open_Time']) + \
          '\nEnd Time: '+ str(datetime.now()) + \
          '\nElapsed Time: '+ str(datetime.now() - Arb['Open_Time'])
                         
    profit_file.write('\n\n' + \
                      Exchange1['Name'] + ' / ' + \
                      Exchange2['Name'] + ' ' + \
                      '\n\nProfit: ' + str(Profit) + 'EUR' + \
                      '\n\nStart Time: '+ str(Arb['Open_Time']) + \
                      '\n\nEnd Time: '+ str(datetime.now()) + '\n\n' + \
                      'Elapsed Time:'+str(datetime.now()- Arb['Open_Time']))
                      
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

    log.write( '%-22s' % '-------------------',)
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
                      
                      
def Trade_Logic(Coin,
                Exchange1, Exchange2, 
                Buy_Price, Sell_Price, 
                Buy_Amount, Sell_Amount,
                Type):
    
    if Type == 'Open':
        Short_Leverage = 2
        Long_Leverage = 0
        Sell_Amount *= 0.5
        
    elif Type == 'Close':
        Long_Leverage = 2
        Short_Leverage = 0
        Buy_Amount *= 0.5       
        
    # Checks a gazillion conditions are True, if False log error, else move on
        
    while True:   
    
        Buy_Order = Execute_Limit_Order(Exchange1, Buy_Amount, 'buy', Buy_Price, Long_Leverage)                                  
                 
        if Buy_Order['Placed'] is False:
            return ({'Placed': False},{'Placed': False}) # doesn't matter, nothing exceuted yet
        
        Sell_Order = Execute_Limit_Order(Exchange2, Sell_Amount, 'sell', Sell_Price, Short_Leverage)                                  
        
        if Sell_Order['Placed'] is False:
            
            time.sleep(5)
            
            Filled = Check_Order_Filled(Exchange1,Buy_Order['Order'], 'buy')
        
            if Filled is False:
                
                Cancel_Order(Exchange1, Buy_Order['Order']['ID'])
                
                print str(Exchange1['Name']) + ' Buy Order ID: '+ \
                      str(Buy_Order['Order']['ID']) + ' Cancelled'
                
                # Reverse the sell order if buy didn't fill,
                # may need to look at market order for this
                
                Filled = Check_Order_Filled(Exchange2, Sell_Order['Order'], 'sell')
                                    
                return ({'Placed': False},{'Placed': False})
                
            elif Filled is True:
                
                time.sleep(5)
            
                Abort_Order = Execute_Market_Order(Exchange1,Buy_Amount,'sell',Long_Leverage)
                
                print str(Exchange1['Name']) + ' Order ID: '+ \
                      str(Abort_Order['Order']['ID']) + ' Trade Reversed'
                      
                return ({'Placed': False},{'Placed': False})
                
              
        # If come this far, both Orders are now placed!  
        
        time.sleep(5)
            
        Filled = Check_Order_Filled(Exchange1, Buy_Order['Order'], 'buy')
        
        if Filled is False:

            Cancel_Order(Exchange1, Buy_Order['Order']['ID'])
            
            print str(Exchange1['Name'])+' Buy Order ID: '+ \
                  str(Buy_Order['Order']['ID'])+' Cancelled'
                  
            time.sleep(5)                  
                  
            Filled = Check_Order_Filled(Exchange2, Sell_Order['Order'], 'sell') 
            
            if Filled is False:
                
                Cancel_Order(Exchange2, Sell_Order['Order']['ID'])
                
                print str(Exchange2['Name']) + ' Sell Order ID: '+ \
                str(Sell_Order['Order']['ID']) + ' Cancelled'
                
                return ({'Placed': False},{'Placed': False})
                
            elif Filled is True:
                
                # Reversed the sell order if buy didn't fill,
                # may need to look at market order for this
                
                time.sleep(5)
                
                Abort_Order = Execute_Market_Order(Exchange2,Sell_Amount,'buy',Short_Leverage)
                                            
                
                print str(Exchange1['Name']) + ' Order ID: ' + \
                      str(Abort_Order['Order']['ID']) + ' Trade Reversed'
                      
                return ({'Placed': False},{'Placed': False})
             
                
        print 'Bought '+str(Buy_Amount)+Coin+' at '+Exchange1['Name'] + \
              ' @ ' + str(Buy_Price) + ' @ '+str(Long_Leverage)+'x Leverage'
        log.write('\nBought '+str(Buy_Amount)+Coin+' at '+Exchange1['Name']+\
                  ' @ ' + str(Buy_Price) + ' @ '+str(Long_Leverage)+'x Leverage')  
                
        # Buy Order has now filled, check if sell order has filled.
            
        Filled = Check_Order_Filled(Exchange2, Sell_Order['Order'], 'sell') 
                               
        if Filled is False:
            
            # Cancel sell order and reverse buy order
            
            time.sleep(5)
            
            Cancel_Order(Exchange2, Sell_Order['Order']['ID'])
            
            Abort_Order = Execute_Market_Order(Exchange1, Buy_Amount, 'sell')
            
            print str(Exchange1['Name']) + ' Order ID: '+ \
                  str(Abort_Order['Order']['ID']) + ' Trade Reversed'
                  
            return {'Placed': False}
            
        # Both Orders have now been executed and filled!!
            
        print 'Sold '+str(Sell_Amount)+Coin+' at '+Exchange2['Name'] + \
              ' @ ' + str(Sell_Price) + ' @ '+str(Short_Leverage)+'x Leverage'
        log.write('\nSold '+str(Sell_Amount)+Coin+' at '+Exchange2['Name']+\
                  ' @ ' + str(Sell_Price) + ' @ '+str(Short_Leverage)+'x Leverage') 
        
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
    
    while True:
        
        # Check for zero prices
        
        if Exchange1['Prices'][Coin]['entry_buy'] == 0 or \
            Exchange2['Prices'][Coin]['entry_sell'] == 0:
                break
        
        # Check for sufficient spread
    
        if Spread <= Entry_Target:
            break
            
        for Arb in Current_Arbs:
            
            # Check if opportunity already exists            
            
            if Name1 == Arb['Long']['Name'] and Name2 == Arb['Short']['Name']:
                break
        
        # Check if there is sufficient balance            
                        
        if Balance1 < Min_Bal or Balance2 < Min_Bal:
            
            break                                  
                
        # Use exchange with minimum balance to execute orders
        
        if Balance1 > Balance2:
            Trade_Amount_Fiat = Balance2        
        else:
            Trade_Amount_Fiat = Balance1
            
            
        Buy_Price = Exchange1['Prices'][Coin]['entry_buy']    
        Buy_Amount = Trade_Amount_Fiat / Buy_Price

        Sell_Price = Exchange2['Prices'][Coin]['entry_sell']            
        Sell_Amount = Trade_Amount_Fiat / Sell_Price
        
        # Log information
        
        Print_Entry(Coin, Exchange1, Exchange2, Spread)
                
        # Calc Fees and Execute the Trade Logic function, this is complicated
                
        Buy_Cost = Exchange1['Fees']['buy_fee']/100 * Buy_Amount
        Sell_Cost = Exchange2['Fees']['buy_fee']/100 * Sell_Amount
        
        Buy_Amount =  round(Buy_Amount - Buy_Cost, 8)        
        Sell_Amount = round(Sell_Amount + Sell_Cost, 8)
        
        if Buy_Amount < Sell_Amount:
            Sell_Amount = Buy_Amount
            
        elif Sell_Amount < Buy_Amount:
            Buy_Amount = Sell_Amount
        
        if Name1 == 'theRock':
            Buy_Amount = int(Buy_Amount*1000) / 1000.0 # round down to 3 d.p.
            Sell_Amount = int(Sell_Amount*1000) / 1000.0 # round down to 3 d.p.
            
        Long_Exposure = Buy_Amount * Buy_Price
        Short_Exposure = Sell_Amount * Sell_Price
                
        Buy_Order, Sell_Order = Trade_Logic(Coin, Exchange1, Exchange2,
                                            Buy_Price, Sell_Price,
                                            Buy_Amount, Sell_Amount,
                                            'Open')
        
        # Check if the orders executed
        
        if Buy_Order['Placed'] is False or Sell_Order['Placed'] is False:
            break
        
        # Calculate the exit target and update this in the opportunity
        
        Fees = Opportunity['Total_Fees'] 
    
        Exit_Target = Spread - Target_Profit*2 - Fees
        
        Opportunity['Close_Target'] = Exit_Target
       
        #######################################################################
        
        # If everything succeeds, update list of open arbs and update balances        
        
        print 'Trades Successfully Executed, in the Market!'
        log.write('\nTrades Successfully Executed, in the Market!')
            
        Exchange1_Fiat = Exchange1['Balances'][Fiat[0]] - (Buy_Amount+Buy_Cost)*Buy_Price 
        Exchange1_Coin = Exchange1['Balances'][Coin] + Buy_Amount
        Exchange2_Fiat = Exchange2['Balances'][Fiat[0]] - (Sell_Amount-Sell_Cost)*Sell_Price 
        Exchange2_Coin = Exchange2['Balances'][Coin] - Sell_Amount
        
        Exchange1['Balances'][Fiat[0]] = Exchange1_Fiat
        Exchange1['Balances'][Coin] = Exchange1_Coin
                                       
        Exchange2['Balances'][Fiat[0]] = Exchange2_Fiat
        Exchange2['Balances'][Coin] = Exchange2_Coin
        
        # Append to list of current Arbitrages
        
        Current_Arbs.append({'Coin': Coin,
                             'Long': Exchange1,
                             'Short': Exchange2,
                             'Long_Amount': Buy_Amount,
                             'Short_Amount': Sell_Amount,
                             'buy_id': Buy_Order['Order'],
                             'sell_id': Sell_Order['Order'],
                             'Open_Spread': Spread,
                             'Long_Exposure': Long_Exposure,
                             'Short_Exposure': Short_Exposure,
                             'Open_Time': datetime.now(),
                             'Close_Target': Exit_Target,
                             'Open_Max_Spread': Current_Exit_Spread,
                             'Close_Min_Spread': Current_Exit_Spread})

        # Remove new arbitrage from Opportunities
        
        for opportunity in Opportunities:
            if opportunity['Long']['Name'] == Name1 and \
                opportunity['Short']['Name'] == Name2:
                    Opportunities.remove(opportunity)           
                       
        break   
            
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
    
    Orders = {'Opened': {'buy':Arb['buy_id'], 'sell':Arb['sell_id']}}
    
    while True:
        
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
                                  
            break
               
        # Log information
            
        Print_Exit(Coin, Exchange2, Exchange1, Spread)
        
        Buy_Price = Exchange2['Prices'][Coin]['exit_buy']
        Sell_Price = Exchange1['Prices'][Coin]['exit_sell']
                
        Buy_Amount = round(Arb['Short_Amount'], 8)
        Sell_Amount = round(Arb['Long_Amount'], 8)
        
        Buy_Order, Sell_Order = Trade_Logic(Coin, Exchange2, Exchange1,
                                            Buy_Price, Sell_Price, 
                                            Buy_Amount, Sell_Amount,
                                            'Close')
                                            
        if Buy_Order is False or Sell_Order is False:
            break
        
        Orders.update({'Closed': {'buy':Buy_Order['Order'], 'sell':Sell_Order['Order']}})
        
        print 'Trades Successfully Closed!'
        log.write('\nTrades Successfully Closed!')       
        
    ###########################################################################
        
        # Calculate Profit and Update Balances
        
        Long_Buy_Fee = Exchange1['Fees']['buy_fee']/100    
        Short_Sell_Fee = Exchange2['Fees']['sell_fee']/100
        
        Long_Sell_Fee = Exchange1['Fees']['sell_fee']/100    
        Short_Buy_Fee = Exchange2['Fees']['buy_fee']/100
        
        Long_Open_Amount = Buy_Amount - (Buy_Amount * Long_Buy_Fee)
        Short_Open_Amount = Sell_Amount + (Sell_Amount * Short_Sell_Fee)
        
        Long_Close_Amount = Long_Open_Amount - (Long_Open_Amount * Long_Sell_Fee)
        Short_Close_Amount = Short_Open_Amount + (Short_Open_Amount * Short_Buy_Fee)

        Long_Balance = Long_Close_Amount * Sell_Price
        Short_Balance = 2*Short_Exposure - Short_Close_Amount * Buy_Price
        
        Long_Profit = Long_Balance - Long_Exposure
        Short_Profit = Short_Balance - Short_Exposure
        
        if Test_Mode:
            
            Exchange1_Fiat = Exchange1['Balances'][Fiat[0]] + Long_Balance
            Exchange1_Coin = Exchange1['Balances'][Coin] - Sell_Amount
            Exchange2_Fiat = Exchange2['Balances'][Fiat[0]] + Short_Balance
            Exchange2_Coin = Exchange2['Balances'][Coin] + Buy_Amount
            
            Exchange1['Balances'][Fiat[0]] = Exchange1_Fiat
            Exchange1['Balances'][Coin] = Exchange1_Coin
            Exchange2['Balances'][Fiat[0]] = Exchange2_Fiat
            Exchange2['Balances'][Coin] = Exchange2_Coin   

        elif Test_Mode is False:
            
            for Exchange in Exchanges:
                Exchange['Balances'] = {}
                Balances = {}
                for Coin in Coins:
                    Balance = Update_Balances(Exchange, Coin)
                    Balances.update(Balance)
                    time.sleep(1)
                Exchange.update({'Balances': Balances})            

              
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
                      'Open_time': Open_Time,
                      'Close_time': datetime.now(),
                      'Elasped_time': datetime.now() - Open_Time}
        
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
                
        break
            
    ###########################################################################
            
###############################################################################

def Get_Coin_Prices(Exchange):
    Prices = {}
    for Coin in Coins:
        result = Get_Prices(Exchange, Coin)
        Prices.update(result)
        
    return {Exchange['Name']: Prices}
    
def Get_All_Prices():  
    
    if Fake_Prices == False:    
    
        pool = multiprocessing.Pool(processes=8)
    
        func = partial(Get_Coin_Prices)
        result = pool.map_async(func, Exchanges)
        
        for Exchange in Exchanges:
            for prices in result.get():
                if prices.keys()[0] == Exchange['Name']:
                    Exchange.update({'Prices': prices.values()[0]})
                    
        pool.close()
        pool.join()
    
    elif Fake_Prices == True:
    
        for Exchange in Exchanges:
            prices = Get_Coin_Prices(Exchange)[Exchange['Name']]
            Exchange.update({'Prices': prices})
            
                
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
    

if __name__ == "__main__":
    
    
    log = open('Log_'+str(datetime.now())[0:10]+'.txt', "w")
    profit_file = open('Profits_'+str(datetime.now())[0:10]+'.txt', "w") 
    
    Opportunities = []
    Current_Arbs = []
    Successful_Arbs = []
    Profits = []
    
    Exchanges = [Kraken, Bitstamp, Gdax, Bl3p, TheRock, Cex, Wex, BitBay, Quoinex]
    
    Permuatations = Get_Perm(Exchanges, Coins)
    
    for Exchange in Exchanges:
        Get_Fees(Exchange)
        
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
        
        for Exchange in Exchanges:
            Exchange['Balances'] = {}
            Balances = {}
            for Coin in Coins:
                Balance = Update_Balances(Exchange, Coin)
                Balances.update(Balance)
                time.sleep(1)
            Exchange.update({'Balances': Balances})
     
    Get_All_Prices()
        
    for Perm in Permuatations:
        Opportunity = Find_Opportunities(Perm)
        if Opportunity is not None:
            Opportunities.append(Opportunity)
               
    for Opportunity in Opportunities:
        Opportunity.update({'History': {'Spreads': [],
                                        'Time': []}})
    

    while True:
        
        iteration += 1

        start_time = datetime.now()
        
        log = open('Log_'+str(datetime.now())[0:10]+'.txt', "a")
        profit_file = open('Profits_'+str(datetime.now())[0:10]+'.txt', "a")  
        
        try:
            Get_All_Prices()
        except:
            pass

        for Opportunity in Opportunities:
            try:
                Update_Opportunities(Opportunity)
            except:
                pass
            
        Opportunities = sorted(Opportunities, key= lambda i: i['Open_Spread'], reverse=True)
            
        Print_Balances()
        Print_Prices()
        
        for Opportunity in Opportunities:
            Open(Opportunity)
                
        for Arb in Current_Arbs:
            Update_Arb(Arb)
    
        Print_Arbitrages()
                
        for Arb in Current_Arbs:
            Close(Arb)
            
        Total_Profit = round(sum(Profits), 2)
        
        print '\nTotal Profit Since Running: ' + str(Total_Profit) + ' Euro'
        log.write('\n\nTotal Profit Since Running: ' + str(Total_Profit) + ' Euro')
        
        end_time = datetime.now()    
        loop_time = end_time - start_time
        
        print '\nTime to execute loop is: ' + str(loop_time) + 's'
        log.write('\n\nTime to execute loop is: ' + str(loop_time) + 's')
                        
        print '\nScanning Markets',
        time.sleep(1); print'.',
        time.sleep(1); print'.',
        time.sleep(1); print'.'
        print '\n'+str(datetime.now())+'\n'
                                    
        log.write('\n\nScanning Markets')      
        log.write('\n\n'+str(datetime.now())+'\n')
            
        log.close()
        profit_file.close()
        
