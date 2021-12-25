import itertools
import time
from datetime import datetime

import krakenex #Shorting ok
import theRock #Shorting ok

import GDAX # Shorting disabled server side until further notice
import bitstamp #Shorting coming soon
import gatecoin # Shorting coming soon
import bl3p

#import xBTCe # Shorting coming soon / Need to figure out private client
#import btce # Exchange raided by FBI

import Keys

###############################################################################

#constants

Min_Bal = 1.0 # Min Balance to execute on

Entry_Spread = 0.2 # Percent (after fees and slippage)
Exit_Spread = 0.0 # Percent to exit on after fees
slippage = 0.1 # Percent

liquid_factor = 2 # multiplied by trade amount to determine if market is liquid enough


pair1 = 'BTC', 'XBT'
pair2 = 'EUR'

#Exchanges = ['Kraken','Bitstamp','Gdax','Bl3p','theRock','Gatecoin']


###############################################################################

def Kraken_Private_Client(query):
    
    Key = Keys.Kraken()
    client = krakenex.API(Key['key'], Key['secret']).query_private(query)
    return client

def Kraken_Price(): 
    
    pair = 'X'+pair1[1]+'Z'+pair2
    
    API = krakenex.API()
    price = API.query_public('Ticker',
                  {'pair': pair})['result'][pair]
                  
    return {'buy': float(price['a'][0]), 'sell': float(price['b'][0])}
    
def Kraken_Fees():
    pair = 'X'+pair1[1]+'Z'+pair2
    API = krakenex.API()
    fees = API.query_public('AssetPairs', {'info': 'fees'})['result'][pair]
    
    return {'buy_fee': float(fees['fees'][0][1]), 'sell_fee': float(fees['fees_maker'][0][1])}
         
def Kraken_Balances():   

    balance = Kraken_Private_Client('Balance')['result']
    
    btc = round(float(balance['XXBT']),8)
    eur = round(float(balance['ZEUR']),2)
    
    return {'BTC': btc, 'EUR': eur}
    
def Kraken_Order(amount, side, price, leverage):
    
    pair = 'X'+pair1[1]+'Z'+pair2
    
    params = {'pair': pair,
              'type': side,
              'ordertype': 'limit',
              'price': str(price),
              'volume': str(amount),
              'leverage': str(leverage)} # 2 to 5 times}
              
    
    Order = Kraken_Private_Client('AddOrder', params)
    
    return Order
    
def Kraken_Check_Order(ref):    
    
    params = {'txid': ref}
    
    Order = Kraken_Private_Client('QueryOrders', params)
    
    return Order
    
def Kraken_Shorting():
    
    return {'Shorting': True}
    
def Kraken_Basic():
    
    Kraken_Basic = {'Name': 'Kraken'}
    Kraken_Basic.update(Kraken_Price())
    Kraken_Basic.update(Kraken_Fees())
    Kraken_Basic.update(Kraken_Shorting())

    return Kraken_Basic
    
def Kraken_Full():

    Kraken.update(Kraken_Balances())
    
    return Kraken
    
def Kraken_Orderbook():
    
    pair = 'X'+pair1[1]+'Z'+pair2    
    API = krakenex.API()    
    Orderbook = API.query_public('Depth', {'pair': pair, 'count': 1000})['result'][pair]
    
    Asks = Orderbook['asks']    
    Bids = Orderbook['bids']
    
    return (Asks, Bids)
    
    
def Kraken_Filled(Order):
    
    isFilled = Kraken_Check_Order(Order['ID'])['result'][Order['ID']]['status']
    
    if str(isFilled) == 'closed':
        Filled = True
    else: Filled = False
    
    return Filled
    
###############################################################################

def Bitstamp_Private_Client():
    
    key = Keys.Bitstamp()   
    client = bitstamp.client.Trading(key['user'], key['key'], key['secret'])
    return client
 
def Bitstamp_Price():
    
    pair = pair1[0].lower(), pair2.lower()
    public_client = bitstamp.client.Public()
    price = public_client.ticker(pair[0], pair[1])
    return {'buy': float(price['ask']), 'sell': float(price['bid'])}
    
def Bitstamp_Balances():
    
    pair = pair1[0].lower(), pair2.lower()
    balance = Bitstamp_Private_Client().account_balance(pair[0], pair[1])
    
    BTC =  float(balance['btc_balance'])
    EUR =  float(balance['eur_balance'])

    return {'BTC': BTC, 'EUR': EUR}
    
def Bitstamp_Fees():
    
    pair = pair1[0].lower(), pair2.lower()
    balance = Bitstamp_Private_Client().account_balance(pair[0], pair[1])
    
    fee = float(balance['fee'])
    
    return {'buy_fee': fee, 'sell_fee': fee}    
    
def Bitstamp_Order(amount, side, price):
    
    pair = pair1[0].lower(), pair2.lower()    
    Order = Bitstamp_Private_Client().limit_order(str(amount), str(side), str(price), pair[0], pair[1])  
    
    return Order
    
def Bitstamp_Check_Order(ref):
    
    Order = Bitstamp_Private_Client().order_status(ref)
    
    return Order
    
def Bitstamp_Shorting():
    
    return {'Shorting': False}
    
def Bitstamp_Basic():
    
    Bitstamp_Basic = {'Name': 'Bitstamp'}
    Bitstamp_Basic.update(Bitstamp_Price())
    Bitstamp_Basic.update(Bitstamp_Fees())
    Bitstamp_Basic.update(Bitstamp_Shorting())

    return Bitstamp_Basic
    
def Bitstamp_Full():
    
    Bitstamp.update(Bitstamp_Balances())           
            
    return Bitstamp
    
def Bitstamp_Orderbook():
    
    pair = pair1[0].lower(), pair2.lower()    
    public_client = bitstamp.client.Public()    
    Orderbook = public_client.order_book({'base': pair[0],'quote': pair[1]})
    
    Asks = Orderbook['asks']
    Bids = Orderbook['bids']
    
    return (Asks, Bids)
    
def Bitstamp_Filled(Order):
    
    isFilled = str(Bitstamp_Check_Order(Order['ID'])['status'])
    if  isFilled == 'Finished':
        Filled = True
    else: Filled = False
    
    return Filled

###############################################################################

def GDAX_Private_Client():
    
    key = Keys.GDAX()        
    client = GDAX.AuthenticatedClient(key['key'], key['secret'], key['passphrase'])
    return client

def Gdax_Price():
    
    pair = pair1[0]+ '-' + pair2    
    public_client = GDAX.PublicClient(product_id = pair)
    price = public_client.getProductTicker(str(pair))    
    return {'buy': float(price['ask']), 'sell': float(price['bid'])}

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

def Gdax_Balances():
    
    key = Keys.GDAX()
        
    client = GDAX.AuthenticatedClient(key['key'], key['secret'], key['passphrase'])
    accounts = client.getAccounts()
    
    for account in accounts:
        if account['currency'] == 'EUR':
            eur = round(float(account['balance']),2)  
    
    for account in accounts:
        if account['currency'] == 'BTC':
            btc = round(float(account['balance']),8)
            
    return {'BTC': btc, 'EUR': eur}
    
def Gdax_Order(amount, side, price): #, margin): waiting to be margin approved
    
    pair = pair1[0]+ '-' + pair2
    
    params = {'type': 'limit',
              'product_id': pair,
              'side': side,
              'price': str(price),
              'size': str(amount)}
              #'overdraft_enabled': str(margin)} waiting to be margin approved

    Order = GDAX_Private_Client().order(params)

    return Order
    
def Gdax_Check_Order(ref):    
    
    Order = GDAX_Private_Client.getOrder(ref)
    
    return Order
    
def Gdax_Shorting():
    
    return {'Shorting': False}  # margin currently disabled until further notice
    
def Gdax_Basic():
    
    Gdax_Basic = {'Name': 'Gdax'}
    Gdax_Basic.update(Gdax_Price())
    Gdax_Basic.update(Gdax_Fees())
    Gdax_Basic.update(Gdax_Shorting())

    return Gdax_Basic
    
def Gdax_Full():
    
    Gdax.update(Gdax_Balances())
    
    return Gdax
    
def Gdax_Orderbook():
    
    pair = pair1[0]+ '-' + pair2   
    public_client = GDAX.PublicClient(product_id = pair)   
    Orderbook = public_client.getProductOrderBook(level = 3)
    
    Asks = Orderbook['asks']
    Bids = Orderbook['bids']
    
    return (Asks, Bids)
    
def Gdax_Filled(Order):
    
    isFilled = str(Gdax_Check_Order(Order['ID']))['settled']
    
    if  isFilled == 'true':
        Filled = True
    else: Filled = False
    
    return Filled

###############################################################################

#def BTCe_Private_Client():
#    
#    key = Keys.BTCe()    
#    client = btce.api.TradeAPIv1(key)
#    return client
#    
#
#def BTCe_Price():
#    
#    pair = pair1[0].lower()+'_'+pair2.lower()    
#    api = btce.api.PublicAPIv3()
#    price = api.call('ticker', pairs = pair)[pair]    
#    return {'buy': float(price['buy']), 'sell': float(price['sell'])}
#
#def BTCe_Fees():    
#    
#    pair = pair1[0].lower()+'_'+pair2.lower()    
#    api = btce.api.PublicAPIv3()
#    fee = api.call('info')['pairs'][pair]['fee']    
#    return {'buy_fee': float(fee), 'sell_fee': float(fee)}
#    
#def BTCe_Balances():
#
#    balances = BTCe_Private_Client().call('getInfo')['funds']
#    btc = round(float(balances['btc']),8)
#    eur = round(float(balances['eur']),2)    
#    return {'BTC': btc, 'EUR': eur}
#    
#def BTCe_Order(amount, side, price):
#    
#    pair = pair1[0].lower()+'_'+pair2.lower()
#    
#    params = {'pair': pair,
#              'type': side,
#              'rate': price,
#              'amount': amount}
#    
#    Order = BTCe_Private_Client.call('Trade', params)
#    
#    return Order
#    
#def BTCe_Check_Order(ref):
#    
#    Order = BTCe_Private_Client.call('TradeHistory')[ref]
#    
#    return Order
#    
#def BTCe_Shorting():
#    
#    return {'Shorting': False}
#    
#def BTCe_Basic():
#    
#    BTCe_Basic = {'Name': 'BTCe'}
#    BTCe_Basic.update(BTCe_Price())
#    BTCe_Basic.update(BTCe_Fees())
#    BTCe_Basic.update(BTCe_Shorting())
#
#    return BTCe_Basic
#
#def BTCe_Full():   
#    
#    BTCe.update(BTCe_Balances())
#            
#    return BTCe

###############################################################################

def Bl3p_Private_Client():
    key = Keys.Bl3p()    
    client = bl3p.Client.Private(key['key'], key['secret'])
    return client

def Bl3p_Price():
    
    pair = pair1[0] + pair2    
    client = bl3p.Client.Public()
    price = client.getTicker(pair)    
    return {'buy': float(price['ask']), 'sell': float(price['bid'])}

def Bl3p_Balances():    

    balances = Bl3p_Private_Client().getBalances()
    
    EUR =  round(float(balances['data']['wallets']['EUR']['available']['value']),2)    
    BTC = round(float(balances['data']['wallets']['BTC']['available']['value']), 8)
    
    return {'EUR': EUR, 'BTC': BTC}
    
def Bl3p_Fees():
    
    balances = Bl3p_Private_Client().getBalances()    
    fee = float(balances['data']['trade_fee']) # plus 0.01eur per trade
    
    return {'buy_fee': fee, 'sell_fee': fee}
    
def Bl3p_Order(amount, side, price):
    
    pair = pair1[0] + pair2
    
    if side == 'buy':
        order_side = 'bid'
    if side == 'sell':
        order_side = 'ask'
    
    Order = Bl3p_Private_Client().addOrder(pair, str(order_side), int(amount), int(price))
    
    return Order
    
def Bl3p_Check_Order(ref):
    
    pair = pair1[0] + pair2    
    Order = Bl3p_Private_Client().checkOrder(pair, ref)    
    return Order
    
def Bl3p_Shorting():
    
    return {'Shorting': False}
    
def Bl3p_Basic():
    
    Bl3p_Basic = {'Name': 'Bl3p'}
    Bl3p_Basic.update(Bl3p_Price())
    Bl3p_Basic.update(Bl3p_Fees())
    Bl3p_Basic.update(Bl3p_Shorting())

    return Bl3p_Basic

def Bl3p_Full():    
    
    Bl3p.update(Bl3p_Balances())
        
    return Bl3p
    
def Bl3p_Orderbook():
    
    pair = pair1[0] + pair2
    client = Bl3p_Private_Client()
    Orderbook = client.FullOrderbook(pair)['data']
    
    Asks_1 = Orderbook['asks']
    
    Asks = []
    
    for ask in Asks_1:
        Asks.append([float(ask['price_int'])/100000, float(ask['amount_int'])/100000000*float(ask['count'])])   
    
    Bids_1 = Orderbook['bids']
    
    Bids = []
    
    for bid in Bids_1:
        Bids.append([float(bid['price_int'])/100000, float(bid['amount_int'])/100000000*float(bid['count'])])
    
    return (Asks, Bids)
    
def Bl3p_Filled(Order):
    
    isFilled = str(Bl3p_Check_Order(Order['ID'])['data']['status'])
    
    if  isFilled == 'closed':
        Filled = True
    else: Filled = False
    
    return Filled
        

###############################################################################

def theRock_Private_Client():
    
    Key = Keys.theRock()
    client = theRock.PyRock.API(Key['key'], Key['secret'])
    return client

def theRock_Price():
    
    pair = pair1[0].lower() + pair2.lower()
    price = theRock_Private_Client().Ticker(pair)
    return {'buy': float(price['ask']), 'sell': float(price['bid'])}
    
def theRock_Balances():  

    balances = theRock_Private_Client().AllBalances()
    balances = balances['balances']
    
    for balance in balances:  
        if balance['currency'] == 'BTC':
            BTC = round(float(balance['trading_balance']),2)
        elif balance['currency'] == 'EUR':
            EUR = round(float(balance['trading_balance']),2) 
        
    return {'BTC': BTC, 'EUR': EUR}
    
def theRock_Fees():
    
    pair = pair1[0] + pair2 
    funds = theRock_Private_Client().Funds()['funds']
    
    for fund in funds:
        if fund['id'] == pair:
            buy_fee = fund['buy_fee']
            sell_fee = fund['sell_fee']
            
    return {'buy_fee': buy_fee, 'sell_fee': sell_fee}
    
def theRock_Order(amount, side, price):
    
    pair = pair1[0].lower() + pair2.lower()
    Order = theRock_Private_Client().PlaceOrder(pair, str(amount), side, str(price))
    
    return Order
    
def theRock_Check_Order(ref):
    
    pair = pair1[0].lower() + pair2.lower()
    Order = theRock_Private_Client().ListOrder(pair, ref)    
    return Order
    
def theRock_Shorting():
    
    return {'Shorting': True}
    
def theRock_Basic():
    
    theRock_Basic = {'Name': 'theRock'}
    theRock_Basic.update(theRock_Price())
    theRock_Basic.update(theRock_Fees())
    theRock_Basic.update(theRock_Shorting())

    return theRock_Basic

def theRock_Full():

    TheRock.update(theRock_Balances())
            
    return TheRock
    
def theRock_Orderbook():
    
    pair = pair1[0].lower() + pair2.lower()
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

    isFilled = str(theRock_Check_Order(Order['ID'])['status'])
    
    if  isFilled == 'executed':
        Filled = True
    else: Filled = False
    
    return Filled

###############################################################################

#def xBTCe_Price():
#    
#    pair = pair1[0] + pair2
#    client = xBTCe.Client.API()
#    price = client.getTicker(pair)
#    return {'buy': float(price['BestAsk']), 'sell': float(price['BestBid'])}
#    
#def xBTCe_Fees():
#    
#    return {'buy_fee': 0.2, 'sell_fee': 0.1}
#    
#def xBTCe_Shorting():
#    
#    return {'Shorting': False}
#    
#def xBTCe_Balances():
#    return
#    
#def xBTCe_Basic():
#    
#    xBTCe_Basic = {'Name': 'xBTCe'}
#    xBTCe_Basic.update(xBTCe_Price())
#    xBTCe_Basic.update(xBTCe_Fees())
#    xBTCe_Basic.update(xBTCe_Shorting())
#
#    return xBTCe_Basic
#    
#
#def XBTCE_Full():    
#
#    XBTCE.update(xBTCe_Balances())
#        
#    return XBTCE
    
###############################################################################

def Gatecoin_Private_Client():
    
    key = Keys.Gatecoin()    
    client = gatecoin.api.Client(key['key'], key['secret'])
    return client

def Gatecoin_Price():
    
    pair = pair1[0] + pair2
    client = gatecoin.api.Client()
    tickers = client.get_tickers()['tickers']    
    for ticker in tickers:
        if ticker['currencyPair'] == pair:
            price = ticker
            
    return {'buy': float(price['ask']), 'sell': float(price['bid'])}

def Gatecoin_Balances():
    
    balances = Gatecoin_Private_Client().get_balances()
    
    for balance in balances['balances']:
        if balance['currency'] == pair2:
            EUR = round(float(balance['availableBalance']),2)
            
        elif balance['currency'] == pair1[0]:
            BTC = round(float(balance['availableBalance']),8)
            
    return {'EUR': EUR, 'BTC': BTC}
    
def Gatecoin_Order(amount, side, price):
    
    pair = pair1[0] + pair2 
    
    if side == 'buy':
        order_side = 'BID'
    if side == 'sell':
        order_side = 'ASK'    
       
    Order = Gatecoin_Private_Client().place_order(pair, str(amount), str(price), order_side)
    
    return Order
    
def Gatecoin_Check_Order(ref):
    
    Order = Gatecoin_Private_Client().get_order(ref)    
    return Order
    
def Gatecoin_Fees():
    
    buy_fee = 0.35
    sell_fee = 0.25
    
    return {'buy_fee': buy_fee, 'sell_fee': sell_fee}
    
def Gatecoin_Shorting():
    
    return {'Shorting': False}
    
def Gatecoin_Basic():
    
    Gatecoin_Basic = {'Name': 'Gatecoin'}
    Gatecoin_Basic.update(Gatecoin_Price())
    Gatecoin_Basic.update(Gatecoin_Fees())
    Gatecoin_Basic.update(Gatecoin_Shorting())

    return Gatecoin_Basic
 
def Gatecoin_Full():
    
    Gatecoin.update(Gatecoin_Balances())
            
    return Gatecoin
    
def Gatecoin_Orderbook():
    
    pair = pair1[0] + pair2    
    client = gatecoin.api.Client()
    Orderbook = client.get_orderbook(pair)
    
    Asks_1 = Orderbook['asks']    
    Asks = []
    
    for ask in Asks_1:
        Asks.append([float(ask['price']), float(ask['volume'])])
    
    Bids_1 = Orderbook['bids']    
    Bids = []
    
    for bid in Bids_1:
        Bids.append([float(bid['price']), float(bid['volume'])])
    
    return (Asks, Bids)
    
def Gatecoin_Filled(Order):
    
    isFilled = Gatecoin_Check_Order(Order['ID'])['order']['remainingQuantity']
    
    if  isFilled == 0:
        Filled = True
    else: Filled = False
    
    return Filled
    
    
    
    
    
    
###############################################################################
###############################################################################
###############################################################################
###############################################################################
    
    
    
    
    
    


def Calc_Spread(Opportunity):    
       
    Exchange1 = Opportunity[0]
    Exchange2 = Opportunity[1]
    
    Sell = Exchange2['sell'] - (Exchange2['sell']*(Exchange2['sell_fee']/100))
    Buy = Exchange1['buy'] + (Exchange1['buy']*(Exchange1['buy_fee']/100))
    
    Spread = (Sell - Buy) / Buy * 100
    
    return Spread
    
    
def Find_Opportunities(Opportunity):
    
    Exchange1 = Opportunity[0]
    Exchange2 = Opportunity[1]
    
    Spread = Calc_Spread(Opportunity)
    
    Opportunities.append((Exchange1, Exchange2, Spread))
    
    
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
    
    
def Update_Prices(Opportunity):
    
    if Opportunity['Name'] == 'Kraken':
        Exchange = Kraken_Basic()
        
    elif Opportunity['Name'] == 'Bitstamp':
        Exchange = Bitstamp_Basic()
        
    elif Opportunity['Name'] == 'Gdax':
        Exchange = Gdax_Basic()
        
    elif Opportunity['Name'] == 'theRock':
        Exchange = theRock_Basic()
        
    elif Opportunity['Name'] == 'Bl3p':
        Exchange = Bl3p_Basic()
        
    elif Opportunity['Name'] == 'Gatecoin':
        Exchange = Gatecoin_Basic()
        
    return Exchange      
            
            
def Find_Exchange(Opportunity):
    
    if Opportunity['Name'] == 'Kraken':
        Exchange = Kraken_Full()     
        
    elif Opportunity['Name'] == 'Bitstamp':
        Exchange = Bitstamp_Full()
        
    elif Opportunity['Name'] == 'Gdax':
        Exchange = Gdax_Full()
        
    elif Opportunity['Name'] == 'theRock':
        Exchange = theRock_Full()
        
    elif Opportunity['Name'] == 'Bl3p':
        Exchange = Bl3p_Full()
        
    elif Opportunity['Name'] == 'Gatecoin':
        Exchange = Gatecoin_Full()
        
    return Exchange
    
    
def isOrderFilled(Exchange, Order):
    
    if Exchange['Name'] == 'Kraken':
        Filled = Kraken_Filled(Order)
            
    elif Exchange['Name'] == 'Bitstamp': 
        Filled = Bitstamp_Filled(Order)
        
    elif Exchange['Name'] == 'Gdax':
        Filled = Gdax_Filled(Order)
            
    elif Exchange['Name'] == 'Bl3p':
        Filled = Bl3p_Filled(Order)
            
    elif Exchange['Name'] == 'theRock':
        Filled = Bl3p_Filled(Order)
        
    elif Exchange['Name'] == 'Gatecoin':
        Filled = Gatecoin_Filled(Order)       
        
    return Filled
    
    
def isliquid(exchange, amount):
    
    amount *= liquid_factor
    
    if exchange['Name'] == 'Kraken':
        Liquid_Price = Weighted_Price(amount, Kraken_Orderbook())
        
    elif exchange['Name'] == 'Bitstamp':
        Liquid_Price = Weighted_Price(amount, Bitstamp_Orderbook())
        
    elif exchange['Name'] == 'Gdax':
        Liquid_Price = Weighted_Price(amount, Gdax_Orderbook())
        
    elif exchange['Name'] == 'Bl3p':
        Liquid_Price = Weighted_Price(amount, Bl3p_Orderbook())
        
    elif exchange['Name'] == 'theRock':
        Liquid_Price = Weighted_Price(amount, theRock_Orderbook())
        
    elif exchange['Name'] == 'Gatecoin':
        Liquid_Price = Weighted_Price(Gatecoin, Kraken_Orderbook())
        
    return Liquid_Price
    
    
    
def Place_Order(Exchange, amount, side, price):
    
#        if Exchange['Name'] == 'Kraken':            
#            Open_Order = {'Name': 'Kraken', 'Amount': amount, 'Side': side, 'Price': price}        
#            while True:
#                try:
#                    Kraken_Open_Order = Kraken_Order(amount, side, price, 'none') #margin is none
#                    Kraken_Order_ID =  str(Kraken_Open_Order['result']['txid'])
#                    Open_Order.update({'ID': Kraken_Order_ID})
#                except:
#                    continue
#            
#        elif Exchange['Name'] == 'Bitstamp':            
#            Open_Order = {'Name': 'Bitstamp', 'Amount': amount, 'Side': side, 'Price': price}            
#            while True:                   
#                try:
#                    Bitstamp_Open_Order = Bitstamp_Order(amount, side, price)
#                    Bitstamp_Order_ID = str(Bitstamp_Open_Order['id'])
#                    Open_Order.update({'ID': Bitstamp_Order_ID})
#                except:
#                    continue                
#        
#        elif Exchange['Name'] == 'Gdax':            
#            Open_Order = {'Name': 'Gdax', 'Amount': amount, 'Side': side, 'Price': price}
#            while True:
#                try:
#                    Gdax_Open_Order = Gdax_Order(amount, side, price) #, 'True') Waiting to be margin approved
#                    Gdax_Order_ID = str(Gdax_Open_Order['id'])
#                    Open_Order.update({'ID': Gdax_Order_ID})
#                except:
#                    continue                
#            
#        elif Exchange['Name'] == 'theRock':            
#            Open_Order = {'Name': 'theRock', 'Amount': amount, 'Side': side, 'Price': price}           
#            while True:
#                try:
#                    theRock_Open_Order = theRock_Order(amount, side, price)
#                    theRock_Order_ID = str(theRock_Open_Order['id'])
#                    Open_Order.update({'ID': theRock_Order_ID})
#                except:
#                    continue
#                
#            
#        elif Exchange['Name'] == 'Bl3p':            
#            Open_Order = {'Name': 'Bl3p', 'Amount': amount, 'Side': side, 'Price': price}           
#            while True:
#                try:
#                    Bl3p_Open_Order = Bl3p_Order(amount*100000000, side, price*100000)
#                    Bl3p_Order_ID = str(Bl3p_Open_Order['data']['order_id'])
#                    Open_Order.update({'ID': Bl3p_Order_ID})
#                except:
#                    continue                
#            
#        elif Exchange['Name'] == 'Gatecoin':            
#            Open_Order = {'Name': 'Gatecoin', 'Amount': amount, 'Side': side, 'Price': price}            
#            while True:
#                try:
#                    Gatecoin_Open_Order = Gatecoin_Order(amount, side, price)
#                    Gatecoin_Order_ID = str(Gatecoin_Open_Order['clOrderId'])
#                    Open_Order.update({'ID': Gatecoin_Order_ID})
#                except:
#                    continue
#                
#        return Open_Order

    return True
        
    
def Open(Opportunity):
    
    Spread = Opportunity[2]
    
    if Spread > Entry_Spread:
            
        Exchange1 = Find_Exchange(Opportunity[0])
        Exchange2 = Find_Exchange(Opportunity[1])
        
        Arb_Exists = False
        
        for Arb in Current_Arbs:
            if Exchange1['Name'] == Arb[0]['Name'] and Exchange2['Name'] == Arb[1]['Name']:
                Arb_Exists = True
                break
            else: Arb_Exists = False
            
        if Arb_Exists is False:
            
            if Exchange1['EUR'] > Min_Bal and Exchange2['EUR'] > Min_Bal:
                
                Exchange1_Open_Balance = Exchange1['EUR']
                Exchange2_Open_Balance = Exchange2['EUR']                        
                
                Total_Open_Balance = Exchange1_Open_Balance + Exchange2_Open_Balance
                
                if Exchange1_Open_Balance > Exchange2_Open_Balance:
                    Trade_Amount_EUR = Exchange2_Open_Balance
                else:
                    Trade_Amount_EUR = Exchange1_Open_Balance
                    
                Trade_Amount_Buy = Trade_Amount_EUR / Exchange1['buy']
                Buy_Price = Exchange1['buy']
                
                Trade_Amount_Sell = Trade_Amount_EUR / Exchange2['sell']
                Sell_Price = Exchange2['sell']
                
                print '\n---Entry Found---'
                print Exchange1['Name']+' / '+Exchange2['Name']+' '+str(round(Spread,2))+'%'
                print 'Prices '+str(Exchange1['buy'])+'EUR'+' / '+str(Exchange2['sell'])+'EUR'            
                print 'Balances '+str(Exchange1['EUR'])+'EUR'+' / '+str(Exchange2['EUR'])+'EUR'
                
                log_file.write('\n\n---Entry Found---\n')        
                log_file.write(Exchange1['Name']+' / '+Exchange2['Name']+' '+str(round(Spread,2))+'%')
                log_file.write('\nPrices '+str(Exchange1['buy'])+'EUR'+' / '+str(Exchange2['sell'])+'EUR')
                log_file.write('\n'+'Balances '+str(Exchange1['EUR'])+'EUR'+' / '+str(Exchange2['EUR'])+'EUR')            
                
                print '\nAttempting Trade...'
                log_file.write('\n\nAttempting Trade...\n')
                
                
                ###### Get Order Book for exchanges, only if liquidity execute orders
                
                Exchange1_Liquid_Price = isliquid(Exchange1, Trade_Amount_Buy)
                
                if Exchange1_Liquid_Price < Buy_Price*(1 + slippage/100):
                    
                    for i in range(1,10):
                        while True:                    
                            try:
                                Buy_Order = Place_Order(Exchange1, Trade_Amount_Buy, 'buy', Buy_Price) # Places the order
                                print 'Order Placed on attempt: %i' %i
                                log_file.write('Order Placed on attempt: %i' %i)
                            except:
                                print 'Order failed on attempt: %i' %i
                                log_file.write('Order failed on attempt: %i' %i)
                                continue
                            
                            Buy_Order = False
                            print 'Order Failed to place'
                            break                        
                                
                    #### Check if order filled if not try and except for 10 times / 30 secs etc.
                    
                    for i in range(10):                        
                        while True:                    
                            try:
                                isOrderFilled(Exchange1['Name'], Buy_Order['ID'])
                                print 'Order Executed on attempt: %i' %i
                                log_file.write('Order Executed on attempt: %i' %i)
                                print 'Bought ' + str(Trade_Amount_Buy) + pair1[0] + ' at ' + str(Exchange1['Name'])        
                                log_file.write('Bought ' + str(Trade_Amount_Buy) + pair1[0] + ' at ' + str(Exchange1['Name']))
                            except:
                                print 'Order waiting to fill...'
                                log_file.write('\n\nAttempting Trade...\n')
                                continue
                            print
                            break
                            print 'failed'
                        
                    
                
                if Buy_Order is False:
                    break
                                
                    
                
                Exchange2_Liquid_Price = isliquid(Exchange2, Trade_Amount_Sell)
                
                if Exchange2_Liquid_Price > Sell_Price*(1 - slippage/100):
                
                    Sell_Order = Place_Order(Exchange2, Trade_Amount_Sell, 'sell', Sell_Price)
                
                    #### Check if order exceuted if not try and except for 10 times / 30 secs etc.
                    
                    #### If order doesn't execute after allotted time, reverse other side of order and take small loss.
                        
                    print 'Shorted ' + str(Trade_Amount_Sell) + pair1[0] + ' at ' + str(Exchange2['Name'])
                    log_file.write('\nShorted ' + str(Trade_Amount_Sell) + pair1[0] + ' at ' + str(Exchange2['Name']))
                
                
                Current_Arbs.append([Exchange1, Exchange2,{'buy_id': Buy_Order, 'sell_id': Sell_Order, 'Spread': Spread,
                                                           'Total_Open_Balance': Total_Open_Balance, 'open_time': datetime.now()}])
                  
            
def Update(Arb):
    
    Exchange1 = Update_Prices(Arb[0])
    Exchange2 = Update_Prices(Arb[1])

    Spread = Calc_Spread((exchanges[0], exchanges[1]))
    
    Arb[0].update(Exchange1)
    Arb[1].update(Exchange2)                         
    Arb[2].update({'Spread': Spread})
       
       
def Close(Arb):    
    
    Exchange1 = Arb[0]
    Exchange2 = Arb[1]

    spread = Arb[2]['Spread']
    Total_Open_Balance = Arb[2]['Total_Open_Balance']
        
    if spread < Exit_Spread:        
        
        print '\n---Exit Found---\n'
        print Exchange1['Name']+' / '+Exchange2['Name']+ str(spread)
        log_file.write('\n\n---Exit Found---\n')       
        log_file.write(Exchange1['Name']+' / '+Exchange2['Name']+ str(spread))
        
        Sell_Amount = Exchange1[pair1[0]]
        Sell_Price = Exchange1['sell']
        
        Buy_Amount = Exchange2[pair1[0]]
        Buy_Price = Exchange2['buy']
        
        
        print 'Attempting to Trade...'
        log_file.write('Attempting to Trade...')
        
        Sell_Order = Place_Order(Exchange1, Sell_Amount, 'sell', Sell_Price)                    
            
        print 'Sold ' + str(Sell_Amount) + pair1[0] + ' at ' + str(Exchange1['Name'])
        log_file.write('Sold ' + str(Sell_Amount) + pair1[0] + ' at ' + str(Exchange1['Name']))
        
        Buy_Order = Place_Order(Exchange2, Buy_Amount, 'buy', Buy_Price)      
        
        print 'BoughtBack ' + str(Buy_Amount) + pair1[0] + ' at ' + str(Exchange2['Name']+'\n')
        log_file.write('BoughtBack ' + str(Buy_Amount) + pair1[0] + ' at ' + str(Exchange2['Name'])+'\n\n')                
                
        Total_Close_Balance = Exchange1['EUR'] + Exchange2['EUR']            
        Profit = Total_Close_Balance - Total_Open_Balance
        
        Closed_Arb = [{'Name1': Exchange1['Name'], 'buy_id': Buy_Order,
                                  'Name2': Exchange2['Name'], 'sell_id': Sell_Order,
                                  'Total_Profit': Profit, 'close_time': datetime.now(),
                                  'Total_Open_Balance': Total_Open_Balance, 'Total_Close_Balance': Total_Close_Balance,
                                  'elasped_time': datetime.now() - Arb[2]['open_time']}]
        
        Successful_Arbs.append(Closed_Arb)
        
        print Exchange1['Name']+' / '+Exchange2['Name']+'Profit = ' +str(Profit) + 'EUR\n'+ \
                            'Start Time: '+ str(Arb[2]['open_time'])+ '\n End Time: '+ str(datetime.now()) + '\n'\
                            'Elapsed Time: '+ str(datetime.now() - Arb[2]['open_time'])
                                 
        profit_file.write(Exchange1['Name']+' / '+Exchange2['Name']+'Profit = ' +str(Profit) + 'EUR\n\n'+ \
                            'Start Time: '+ str(Arb[2]['open_time'])+ '\n\n End Time: '+ str(datetime.now()) + '\n\n'\
                            'Elapsed Time:'+ str(datetime.now() - Arb[2]['open_time']))
        
        
        for Arb in Current_Arbs:
            if Exchange1['Name'] == Arb[2]['Name1'] and Exchange2['Name'] == Arb[2]['Name2']:
                Current_Arbs.remove(Arb)
       
    else:
        
        print '\nLooking for exit...' 
        print Exchange1['Name']+' / '+Exchange2['Name']+'. Spread is '+str(round(spread,2))+'%'
        log_file.write('\n\nLooking for exit\n')
        log_file.write(Exchange1['Name']+' / '+Exchange2['Name']+'. Spread is '+str(round(spread,2))+'%')
    
    
def Get_Perm(exchanges):
    
    Permuatations = list(itertools.permutations(exchanges, 2))
    Permuatations = [i for i in Permuatations if i[1]['Shorting'] is True]

    return Permuatations
    

###############################################################################


#def main(): 

log_file = open("Log.txt", "w")
profit_file = open("Profits.txt", "w")
    
Current_Arbs = []

Successful_Arbs = []

while True:
    
    log_file = open("Log.txt", "a")
    
    print '\nScanning Markets'
    print '\n'+str(datetime.now())  
    log_file.write('\n\nScanning Markets')      
    log_file.write('\n'+str(datetime.now()))
    
    try:
        Kraken = Kraken_Basic()
        Bitstamp = Bitstamp_Basic()
        Gdax = Gdax_Basic()
        TheRock = theRock_Basic()
        Bl3p = Bl3p_Basic()
        Gatecoin = Gatecoin_Basic() 
    except:
        continue      

    exchanges = [Kraken, Bitstamp, Gdax, TheRock, Bl3p, Gatecoin] # add BTCe(Raided by FBI), xBTCe when ready  
        
    Permuatations = Get_Perm(exchanges)
    
    Opportunities = []
    
    for exchanges in Permuatations:    
#        try:
            Find_Opportunities(exchanges)        
#        except:
#            continue        
    
    for Opportunity in Opportunities:
#        try:
            Open(Opportunity)
#        except:            
#            continue    
            
    for Arb in Current_Arbs:
#        try:
            Update(Arb)
#        except:
#            continue
            
    for Arb in Current_Arbs:
#        try:
            Close(Arb)
#        except:
#            continue
        
            
    log_file.close()

    time.sleep(5)
       
        
#if __name__ == "__main__":
#    main()   
    
    

