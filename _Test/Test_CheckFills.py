import krakenex #Shorting ok
import GDAX #Shorting ok
import theRock #Shorting ok

import bitstamp #Shorting coming soon
import gatecoin # Shorting coming soon

import bl3p

#import xBTCe # Shorting coming soon - Need to figure out private client
#import btce # Exchange raided by FBI

#import threading # Multithreading to be used

import Keys


Min_Spread = 0.7    # Spread as a percentage
Min_Bal = 1    # Min Balance to execute on 

#constants
pair1 = 'BTC', 'XBT'
pair2 = 'EUR'


''' 20/06/2017 inlcuded fees in arbitrage algorithm, updated error catching - GMB'''
''' 16/06/2017 included private client for each exchange api, cleaned code - GMB '''
''' 15/06/2017 collated exchange apis and cleaned code for main algorithm - PN '''

'''notes:1. the private authenitcation takes the longest time so can make it a three 
step process, get prices and only if opportunity check for balance, then place order.
2. before actual transaction can ping the exchange with very small amount for liquidity check
to do:
    transaction logic: still in profit after fees?
    exchange historical comparison - when did they last cross?
    sending orders


'''
################################################################################ 

def Kraken_Private_Client(query, req={}):
    
    Key = Keys.Kraken()
    client = krakenex.API(Key['key'], Key['secret']).query_private(query, req)
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
    


################################################################################   

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
    


###########################################################################

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
    
    Order = GDAX_Private_Client().getOrder(ref)
    
    return Order
    
def Gdax_Shorting():
    
    return {'Shorting': False} # Waiting to be approved
    
def Gdax_Basic():
    
    Gdax_Basic = {'Name': 'Gdax'}
    Gdax_Basic.update(Gdax_Price())
    Gdax_Basic.update(Gdax_Fees())
    Gdax_Basic.update(Gdax_Shorting())

    return Gdax_Basic
    



#############################################################################

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



##############################################################################

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

##############################################################################

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
 

###########################################################################
###########################################################################

buy_amount = 0.001
buy_price = 3244

#Kraken_Open_Buy_Order = Kraken_Order(buy_amount, 'buy', buy_price, 'none') #margin is none
#Kraken_Order_ID =  str(Kraken_Open_Buy_Order['result']['txid'][0])

Kraken_Filled = Kraken_Check_Order(u'OCBCXK-66XUT-BSSI5W')['result'][u'OCBCXK-66XUT-BSSI5W']['status']
isFilled = str(Kraken_Filled)
if  isFilled == 'closed':
    Filled = True
else: Filled = False


#Bitstamp_Open_Buy_Order = Bitstamp_Order(buy_amount, 'buy', buy_price)
#Bitstamp_Order_ID = str(Bitstamp_Open_Buy_Order['id'])


#Bitstamp_Filled = Bitstamp_Check_Order(Bitstamp_Order_ID)
#isFilled = str(Bitstamp_Filled['status'])
#if  isFilled == 'closed':
#    Filled = True
#else: Filled = False


#Gdax_Open_Order = Gdax_Order(buy_amount, 'buy', buy_price) #, 'True') Waiting to be margin approved
#Gdax_Order_ID = str(Gdax_Open_Order['id'])

#Gdax_Filled = Gdax_Check_Order(Gdax_Order_ID)
#isFilled = str(Gdax_Filled)['status']
#if  isFilled == 'closed':
#    Filled = True
#else: Filled = False

#Bl3p_Open_Buy_Order = Bl3p_Order(buy_amount*100000000, 'buy', buy_price*100000)
#Bl3p_Order_ID = str(Bl3p_Open_Buy_Order['data']['order_id'])

#Bl3p_Filled = Bl3p_Check_Order(Bl3p_Order_ID)
#isFilled = str(Bl3p_Filled['data']['status'])
#if  isFilled == 'closed':
#    Filled = True
#else: Filled = False


#theRock_Open_Buy_Order = theRock_Order(buy_amount, 'buy', buy_price)
#theRock_Order_ID = str(theRock_Open_Buy_Order['id'])

#theRock_Filled = theRock_Check_Order(theRock_Order_ID)
#isFilled = str(theRock_Filled['status'])
#if  isFilled == 'executed':
#    Filled = True
#else: Filled = False

#Gatecoin_Open_Buy_Order = Gatecoin_Order(buy_amount, 'buy', buy_price)
#Gatecoin_Order_ID = str(Gatecoin_Open_Buy_Order['clOrderId'])

#Gatecoin_Filled = Gatecoin_Check_Order(Gatecoin_Order_ID)
#isFilled = str(Gatecoin_Filled['order']['statusDesc'])
#if  isFilled == 'Filling':
#    Filled = True
#else: Filled = False















