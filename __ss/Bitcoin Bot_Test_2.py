import itertools
import time
from datetime import datetime

import krakenex #Shorting ok
import GDAX #Shorting ok
import theRock #Shorting ok

import bitstamp #Shorting coming soon
import xBTCe # Shorting coming soon
import gatecoin # Shorting coming soon
import btce
import bl3p

#import threading


import Keys


Min_Spread = 0.2    # Spread as a percentage
Min_Bal = 5    # Min Balance to execute on 

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

def Kraken_Private_Client(query):
    
    Key = Keys.Kraken()
    client = krakenex.API(Key['key'], Key['secret']).query_private(query)
    return client

def Kraken_Price(): 
    
    pair = 'X'+pair1[1]+'Z'+pair2
    
    API = krakenex.API()
    price = API.query_public('Ticker',
                  {'pair': pair})['result'][pair]
                  
    return {'Ask': float(price['a'][0]), 'Bid': float(price['b'][0])}
    
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
              'price': price,
              'leverage': leverage, # 1 to 5 times
              'volume': amount}
    
    Order = Kraken_Private_Client('AddOrder', params)
    
    return Order
    
def Kraken_Check_Order(ref):    
    
    params = {'userref': ref}
    
    Order = Kraken_Private_Client('OpenOrders', params)
    
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

    Kraken = {'Name': 'Kraken',
              'buy': Kraken_Price()['Ask'],
              'sell': Kraken_Price()['Bid'],
              'buy_fee': Kraken_Fees()['buy_fee'],
              'sell_fee': Kraken_Fees()['sell_fee'],
              'BTC': Kraken_Balances()['BTC'],
              'EUR': Kraken_Balances()['EUR'],
              'Shorting': Kraken_Shorting()['Shorting']}
    return Kraken

################################################################################   

def Bitstamp_Private_Client():
    
    key = Keys.Bitstamp()   
    client = bitstamp.client.Trading(key['user'], key['key'], key['secret'])
    return client
 
def Bitstamp_Price():
    
    pair = pair1[0].lower(), pair2.lower()
    public_client = bitstamp.client.Public()
    price = public_client.ticker(pair[0], pair[1])
    return {'Ask': float(price['ask']), 'Bid': float(price['bid'])}
    
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
    Order = Bitstamp_Private_Client().limit_order(amount, side, price, pair[0], pair[1])  
    
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

###########################################################################

def GDAX_Private_Client():
    
    key = Keys.GDAX()        
    client = GDAX.AuthenticatedClient(key['key'], key['secret'], key['passphrase'])
    return client

def Gdax_Price():
    
    pair = pair1[0]+ '-' + pair2    
    public_client = GDAX.PublicClient(product_id = pair)
    price = public_client.getProductTicker(str(pair))    
    return {'Ask': float(price['ask']), 'Bid': float(price['bid'])}

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
    
def Gdax_Order(amount, side, price, margin):
    
    params = {'type': 'limit',
              'side': side,
              'price': price,
              'size': amount,
              'overdraft_enabled': margin} # if margin is true, margin is enabled

    Order = GDAX_Private_Client.order(params)

    return Order
    
def Gdax_Check_Order(ref):    
    
    Order = GDAX_Private_Client.getOrder(ref)
    
    return Order
    
def Gdax_Shorting():
    
    return {'Shorting': True}
    
def Gdax_Basic():
    
    Gdax_Basic = {'Name': 'Gdax'}
    Gdax_Basic.update(Gdax_Price())
    Gdax_Basic.update(Gdax_Fees())
    Gdax_Basic.update(Gdax_Shorting())

    return Gdax_Basic
    
def Gdax_Full():
    
    Gdax = {'Name': 'GDAX',
            'buy': Gdax_Price()['Ask'],
            'sell': Gdax_Price()['Bid'],
            'buy_fee': Gdax_Fees()['buy_fee'],
            'sell_fee': Gdax_Fees()['sell_fee'],
            'BTC': Gdax_Balances()['BTC'],
            'EUR': Gdax_Balances()['EUR'],
            'Shorting': Gdax_Shorting()['Shorting']}
    return Gdax

###############################################################################

def BTCe_Private_Client():
    
    key = Keys.BTCe()    
    client = btce.api.TradeAPIv1(key)
    return client
    

def BTCe_Price():
    
    pair = pair1[0].lower()+'_'+pair2.lower()    
    api = btce.api.PublicAPIv3()
    price = api.call('ticker', pairs = pair)[pair]    
    return {'Ask': float(price['buy']), 'Bid': float(price['sell'])}

def BTCe_Fees():    
    
    pair = pair1[0].lower()+'_'+pair2.lower()    
    api = btce.api.PublicAPIv3()
    fee = api.call('info')['pairs'][pair]['fee']    
    return {'buy_fee': float(fee), 'sell_fee': float(fee)}
    
def BTCe_Balances():

    balances = BTCe_Private_Client().call('getInfo')['funds']
    btc = round(float(balances['btc']),8)
    eur = round(float(balances['eur']),2)    
    return {'BTC': btc, 'EUR': eur}
    
def BTCe_Order(amount, side, price):
    
    pair = pair1[0].lower()+'_'+pair2.lower()
    
    params = {'pair': pair,
              'type': side,
              'rate': price,
              'amount': amount}
    
    Order = BTCe_Private_Client.call('Trade', params)
    
    return Order
    
def BTCe_Check_Order(ref):
    
    Order = BTCe_Private_Client.call('TradeHistory')[ref]
    
    return Order
    
def BTCe_Shorting():
    
    return {'Shorting': False}
    
def BTCe_Basic():
    
    BTCe_Basic = {'Name': 'BTCe'}
    BTCe_Basic.update(BTCe_Price())
    BTCe_Basic.update(BTCe_Fees())
    BTCe_Basic.update(BTCe_Shorting())

    return BTCe_Basic

def BTCe_Full():   
    
    BTCe = {'Name': 'BTCe',
            'buy': BTCe_Price()['Ask'],
            'sell': BTCe_Price()['Bid'],
            'buy_fee': BTCe_Fees()['buy_fee'],
            'sell_fee': BTCe_Fees()['sell_fee'],
            'BTC': BTCe_Balances()['BTC'],
            'EUR': BTCe_Balances()['EUR'],
            'Shorting': BTCe_Shorting()['Shorting']}
            
    return BTCe

#############################################################################

def Bl3p_Private_Client():
    key = Keys.Bl3p()    
    client = bl3p.Client.Private(key['key'], key['secret'])
    return client

def Bl3p_Price():
    
    pair = pair1[0] + pair2    
    client = bl3p.Client.Public()
    price = client.getTicker(pair)    
    return {'Ask': float(price['ask']), 'Bid': float(price['bid'])}

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
    Order = Bl3p_Private_Client().addOrder(pair, side, amount, price)    
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
    
    Bl3p = {'Name': 'Bl3p',
        'buy': Bl3p_Price()['Ask'],
        'sell': Bl3p_Price()['Bid'],
        'buy_fee': Bl3p_Fees()['buy_fee'],
        'sell_fee': Bl3p_Fees()['sell_fee'],
        'BTC': Bl3p_Balances()['BTC'],
        'EUR': Bl3p_Balances()['EUR'],
        'Shorting': Bl3p_Shorting()['Shorting']}
        
    return Bl3p

##############################################################################

def theRock_Private_Client():
    
    Key = Keys.theRock()
    client = theRock.PyRock.API(Key['key'], Key['secret'])
    return client

def theRock_Price():
    
    pair = pair1[0].lower() + pair2.lower()
    price = theRock_Private_Client().Ticker(pair)
    return {'Ask': float(price['ask']), 'Bid': float(price['bid'])}
    
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
    Order = theRock_Private_Client().PlaceOrder(pair, amount, side, price)    
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

    TheRock = {'Name': 'TheRock',
            'buy': theRock_Price()['Ask'],
            'sell': theRock_Price()['Bid'],
            'buy_fee': theRock_Fees()['buy_fee'],
            'sell_fee': theRock_Fees()['sell_fee'],
            'BTC': theRock_Balances()['BTC'],
            'EUR': theRock_Balances()['EUR'],
            'Shorting': theRock_Shorting()['Shorting']}
            
    return TheRock

########################################################################

def xBTCe_Price():
    
    pair = pair1[0] + pair2
    client = xBTCe.Client.API()
    price = client.getTicker(pair)
    return {'Ask': float(price['BestAsk']), 'Bid': float(price['BestBid'])}
    
def xBTCe_Fees():
    
    return {'buy_fee': 0.2, 'sell_fee': 0.1}
    
def xBTCe_Shorting():
    
    return {'Shorting': False}
    
def xBTCe_Basic():
    
    xBTCe_Basic = {'Name': 'xBTCe'}
    xBTCe_Basic.update(xBTCe_Price())
    xBTCe_Basic.update(xBTCe_Fees())
    xBTCe_Basic.update(xBTCe_Shorting())

    return xBTCe_Basic
    

def XBTCE_Full():    

    XBTCE = {'Name': 'xBTCe',
        'buy': xBTCe_Price('Ask'), 
        'sell': xBTCe_Price('Bid'),
        'buy_fee': xBTCe_Fees()['buy_fee'],
        'sell_fee': xBTCe_Fees()['sell_fee'],
        'Shorting': xBTCe_Shorting()['Shorting']}
        
    return XBTCE
    
#######################################################################

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
            
    return {'Ask': float(price['ask']), 'Bid': float(price['bid'])}

def Gatecoin_Balances():
    
    balances = Gatecoin_Private_Client().get_balances()
    
    for balance in balances['balances']:
        if balance['currency'] == pair2:
            EUR = round(float(balance['availableBalance']),2)
            
        elif balance['currency'] == pair1[0]:
            BTC = round(float(balance['availableBalance']),8)
            
    return {'EUR': EUR, 'BTC': BTC}
    
def Gatecoin_Order(amount, price, side):
    
    pair = pair1[0] + pair2    
    Order = Gatecoin_Private_Client().place_order(pair, amount, price, side)    
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
    
    Gatecoin = {'Name': 'Gatecoin',
            'buy': Gatecoin_Price()['Ask'],
            'sell': Gatecoin_Price()['Bid'],
            'buy_fee': Gatecoin_Fees()['buy_fee'], 
            'sell_fee': Gatecoin_Fees('sell_fee'),
            'BTC': Gatecoin_Balances()['BTC'],
            'EUR': Gatecoin_Balances()['EUR'],
            'Shorting': Gatecoin_Shorting()['Shorting']} # Coming soon
            
    return Gatecoin
    


###########################################################################
###########################################################################


def Calc_Spread(Opportunity):    
       
    Exchange1 = Opportunity[0]
    Exchange2 = Opportunity[1]
    
    sell = Exchange2['Bid'] - (Exchange2['Bid'] * (Exchange2['sell_fee'] / 100))
    buy = Exchange1['Ask'] - (Exchange1['Ask'] * (Exchange1['buy_fee'] / 100))
    
    spread = (sell - buy) / buy * 100
    
    Opportunities.append({'Name1': Exchange1['Name'], 'Name2': Exchange2['Name'], 'spread': spread})
    
    
def Open(Opportunity):
    
    spread = Opportunity['spread']
    
    print Opportunity['Name1'] +'_' + Opportunity['Name2'] + ' ' + str(spread)
    
    Exchange1 = []
    Exchange2 = []
    
    Open_Buy_Order = []
    Open_Sell_Order = []       
       
    if spread > Min_Spread:        
        
        if Opportunity['Name1'] == 'Kraken':
            Exchange1.append(Kraken_Full())       
        if Opportunity['Name1'] == 'Bitstamp':
            Exchange1.append(Bitstamp_Full())
        if Opportunity['Name1'] == 'Gdax':
            Exchange1.append(Gdax_Full())
        if Opportunity['Name1'] == 'theRock':
            Exchange1.append(theRock_Full())
        if Opportunity['Name1'] == 'Bl3p':
            Exchange1.append(Bl3p_Full())
        if Opportunity['Name1'] == 'Gatecoin':
            Exchange1.append(Gatecoin_Full())
            
        if Opportunity['Name2'] == 'Kraken':
            Exchange2.append(Kraken_Full())
        if Opportunity['Name2'] == 'Bitstamp':
            Exchange2.append(Bitstamp_Full())
        if Opportunity['Name2'] == 'Gdax':
            Exchange2.append(Gdax_Full())
        if Opportunity['Name2'] == 'theRock':
            Exchange2.append(theRock_Full())
        if Opportunity['Name2'] == 'Bl3p':
            Exchange2.append(Bl3p_Full())
        if Opportunity['Name2'] == 'Gatecoin':
            Exchange2.append(Gatecoin_Full())
            
        Exchange1 = Exchange1[0]
        Exchange2 = Exchange2[0]
            
        if Exchange1['EUR'] > Min_Bal and Exchange2['EUR'] > Min_Bal :
            
            Exchange1_Open_Balance = Exchange1['EUR']
            Exchange2_Open_Balance = Exchange2['EUR']
            Total_Open_Balance = Exchange1_Open_Balance + Exchange2_Open_Balance
            
            print '\nEntry Found'
            print Exchange1['Name']+'_'+Exchange2['Name']+' '+str(spread)        
            log_file.write('\n\nEntry Found')        
            log_file.write(Exchange1['Name']+'_'+Exchange2['Name']+' '+str(spread))
            
            
            print 'Attempting to buy ' + Exchange1['Name']
            log_file.write('Attempting to buy ' + Exchange1['Name'])
            
#            if Exchange1['Name'] == 'Kraken':
#                while True:
#                    try:
#                        Kraken_Open_Buy_Order = Kraken_Order(Exchange1['EUR']/Exchange1['buy'], 'buy', Exchange1['buy'], 1)
#                        Open_Buy_Order.append(Kraken_Open_Buy_Order) # Check if order executed
#                    except:
#                        continue
#                    break                       
#                
#            elif Exchange1['Name'] == 'Bitstamp':
#                while True:
#                    try:
#                        Bitstamp_Open_Buy_Order = Bitstamp_Order(Exchange1['EUR']/Exchange1['buy'], 'buy', Exchange1['buy'])
#                        Open_Buy_Order.append(Bitstamp_Open_Buy_Order) # Check if order executed
#                    except:
#                        continue
#                    break
#            
#            elif Exchange1['Name'] == 'Gdax':
#                while True:
#                    try:
#                        Gdax_Open_Buy_Order = Gdax_Order(Exchange1['EUR']/Exchange1['buy'], 'buy', Exchange1['buy'], 1)
#                        Open_Buy_Order.append(Gdax_Open_Buy_Order) # Check if order executed
#                    except:
#                        continue
#                    break
#                
#            elif Exchange1['Name'] == 'theRock':
#                while True:
#                    try:
#                        theRock_Open_Buy_Order = theRock_Order(Exchange1['EUR']/Exchange1['buy'], 'buy', Exchange1['buy'])
#                        Open_Buy_Order.append(theRock_Open_Buy_Order) # Check if order executed
#                    except:
#                        continue
#                    break
#                
#            elif Exchange1['Name'] == 'Bl3p':
#                while True:
#                    try:
#                        Bl3p_Open_Buy_Order = Bl3p_Order(Exchange1['EUR']/Exchange1['buy'], 'buy', Exchange1['buy'])
#                        Open_Buy_Order.append(Bl3p_Open_Buy_Order) # Check if order executed
#                    except:
#                        continue
#                    break
#                
#            elif Exchange1['Name'] == 'Gatecoin':
#                while True:
#                    try:
#                        Gatecoin_Open_Buy_Order = Gatecoin_Order(Exchange1['EUR']/Exchange1['buy'], 'buy', Exchange1['buy'])
#                        Open_Buy_Order.append(Gatecoin_Open_Buy_Order) # Check if order executed
#                    except:
#                        continue
#                    break
                
                        
            print 'Bought ' + str(Exchange1['EUR']/Exchange1['Ask']) + pair1[0] + ' at ' + str(Exchange1['Name'])        
            log_file.write('Bought ' + str(Exchange1['EUR']/Exchange1['Ask']) + pair1[0] + ' at ' + str(Exchange1['Name']))
    
            
#            if Exchange2['Name'] == 'Kraken':
#                while True:
#                    try:
#                        Kraken_Open_sell_Order = Kraken_Order(Exchange2['EUR']/Exchange2['sell'], 'sell', Exchange2['sell'], 1)
#                        Open_Sell_Order.append(Kraken_Open_sell_Order) # Check if order executed
#                    except:
#                        continue
#                    break                       
#                
#            elif Exchange2['Name'] == 'Bitstamp':
#                while True:
#                    try:
#                        Bitstamp_Open_sell_Order = Bitstamp_Order(Exchange2['EUR']/Exchange2['sell'], 'sell', Exchange2['sell'])
#                        Open_Sell_Order.append(Bitstamp_Open_sell_Order) # Check if order executed
#                    except:
#                        continue
#                    break
#            
#            elif Exchange2['Name'] == 'Gdax':
#                while True:
#                    try:
#                        Gdax_Open_sell_Order = Gdax_Order(Exchange2['EUR']/Exchange2['sell'], 'sell', Exchange2['sell'], 1)
#                        Open_Sell_Order.append(Gdax_Open_sell_Order) # Check if order executed
#                    except:
#                        continue
#                    break
#                
#            elif Exchange2['Name'] == 'theRock':
#                while True:
#                    try:
#                        theRock_Open_sell_Order = theRock_Order(Exchange2['EUR']/Exchange2['sell'], 'sell', Exchange2['sell'])
#                        Open_Sell_Order.append(theRock_Open_sell_Order) # Check if order executed
#                    except:
#                        continue
#                    break
#                
#            elif Exchange2['Name'] == 'Bl3p':
#                while True:
#                    try:
#                        Bl3p_Open_sell_Order = Bl3p_Order(Exchange2['EUR']/Exchange2['sell'], 'sell', Exchange2['sell'])
#                        Open_Sell_Order.append(Bl3p_Open_sell_Order) # Check if order executed
#                    except:
#                        continue
#                    break
#                
#            elif Exchange2['Name'] == 'Gatecoin':
#                while True:
#                    try:
#                        Gatecoin_Open_sell_Order = Gatecoin_Order(Exchange2['EUR']/Exchange2['sell'], 'sell', Exchange2['sell'])
#                        Open_Sell_Order.append(Gatecoin_Open_sell_Order) # Check if order executed
#                    except:
#                        continue
#                    break
                
            print 'Shorted ' + str(Exchange2['EUR']/Exchange2['Bid']) + pair1[0] + ' at ' + str(Exchange2['Name'])
            log_file.write('Shorted ' + str(Exchange2['EUR']/Exchange2['Bid']) + pair1[0] + ' at ' + str(Exchange2['Name']))
            
            
            Open_Buy_Order = [1]       ###### Remove This for real thing
            Open_Sell_Order = [1]         ###### Remove This for real thing
                
            
            if Open_Buy_Order and Open_Sell_Order is True:
                Current_Arbs.append({'Name1': Exchange1['Name'],
                                     'Name2': Exchange2['Name'],
                                     'Total_Open_Balance': Total_Open_Balance})  
                                 


            
def Update(Open_Arbs):
    
    Exchange1 = []
    Exchange2 = []
    Total_Open_Balance = Exchanges['Total_Open_Balance']
    
    if Open_Arbs['Name1'] == 'Kraken':
        Exchange1.append(Kraken_Full())
    elif Open_Arbs['Name1'] == 'Bitstamp':
        Exchange1.append(Bitstamp_Full())
    elif Open_Arbs['Name1'] == 'Gdax':
        Exchange1.append(Gdax_Full())
    elif Open_Arbs['Name1'] == 'theRock':
        Exchange1.append(theRock_Full())
    elif Open_Arbs['Name1'] == 'Bl3p':
        Exchange1.append(Bl3p_Full())
    elif Open_Arbs['Name1'] == 'Gatecoin':
        Exchange1.append(Gatecoin_Full())
        
    if Open_Arbs['Name2'] == 'Kraken':
        Exchange2.append(Kraken_Full())
    elif Open_Arbs['Name2'] == 'Bitstamp':
        Exchange2.append(Bitstamp_Full())
    elif Open_Arbs['Name2'] == 'Gdax':
        Exchange2.append(Gdax_Full())
    elif Open_Arbs['Name2'] == 'theRock':
        Exchange2.append(theRock_Full())
    elif Open_Arbs['Name2'] == 'Bl3p':
        Exchange2.append(Bl3p_Full())
    elif Open_Arbs['Name2'] == 'Gatecoin':
        Exchange2.append(Gatecoin_Full())    
    
    sell = Exchange2['bid'] - (Exchange2['bid'] * (Exchange2['sell_fee'] / 100))
    buy = Exchange1['ask'] - (Exchange1['ask'] * (Exchange1['buy_fee'] / 100))
    
    spread = (sell - buy) / buy * 100
    
    Updated_Arbs.append((Exchange1['Name'], Exchange2['Name'], spread, Total_Open_Balance))   
        
        
       
def Close(Open_Arbs):
    
    Open_Buy_Order = []
    Open_Sell_Order = []
    
    Exchange1 = Open_Arbs[0]
    Exchange2 = Open_Arbs[1]      

    Total_Open_Balance = Open_Arbs[3]
    
    if Open_Arbs['Name1'] == 'Kraken':
        Exchange1.append(Kraken_Full())
    elif Open_Arbs['Name1'] == 'Bitstamp':
        Exchange1.append(Bitstamp_Full())
    elif Open_Arbs['Name1'] == 'Gdax':
        Exchange1.append(Gdax_Full())
    elif Open_Arbs['Name1'] == 'theRock':
        Exchange1.append(theRock_Full())
    elif Open_Arbs['Name1'] == 'Bl3p':
        Exchange1.append(Bl3p_Full())
    elif Open_Arbs['Name1'] == 'Gatecoin':
        Exchange1.append(Gatecoin_Full())
        
    if Open_Arbs['Name2'] == 'Kraken':
        Exchange2.append(Kraken_Full())
    elif Open_Arbs['Name2'] == 'Bitstamp':
        Exchange2.append(Bitstamp_Full())
    elif Open_Arbs['Name2'] == 'Gdax':
        Exchange2.append(Gdax_Full())
    elif Open_Arbs['Name2'] == 'theRock':
        Exchange2.append(theRock_Full())
    elif Open_Arbs['Name2'] == 'Bl3p':
        Exchange2.append(Bl3p_Full())
    elif Open_Arbs['Name2'] == 'Gatecoin':
        Exchange2.append(Gatecoin_Full())

    spread = Open_Arbs[2]        
        
    if spread < 0.1:
        
        BTC_Amount_to_Sell = Exchange1['BTC']
        BTC_Amount_to_Buyback = Exchange2['BTC']
        
        print '\nExit Found'
        print Exchange1['Name']+'_'+Exchange2['Name'], spread
        log_file.write('\n\nExit Found')       
        log_file.write(Exchange1['Name']+'_'+Exchange2['Name'], spread)
        
        
        print 'Attempting to sell ' + Exchange1['Name']
        log_file.write('Attempting to sell ' + Exchange1['Name'])        
        
#        if Exchange1['Name'] == 'Kraken':
#            while True:
#                try:
#                    Kraken_Open_Sell_Order = Kraken_Order(Exchange1['EUR']/Exchange1['sell'], 'sell', Exchange1['sell'], 1)
#                    Open_Sell_Order.append(Kraken_Open_Sell_Order) # Check if order executed
#                except:
#                    continue
#                break                       
#            
#        elif Exchange1['Name'] == 'Bitstamp':
#            while True:
#                try:
#                    Bitstamp_Open_Sell_Order = Bitstamp_Order(Exchange1['EUR']/Exchange1['sell'], 'sell', Exchange1['sell'])
#                    Open_Sell_Order.append(Bitstamp_Open_Sell_Order) # Check if order executed
#                except:
#                    continue
#                break
#        
#        elif Exchange1['Name'] == 'Gdax':
#            while True:
#                try:
#                    Gdax_Open_Sell_Order = Gdax_Order(Exchange1['EUR']/Exchange1['sell'], 'sell', Exchange1['sell'], 1)
#                    Open_Sell_Order.append(Gdax_Open_Sell_Order) # Check if order executed
#                except:
#                    continue
#                break
#            
#        elif Exchange1['Name'] == 'theRock':
#            while True:
#                try:
#                    theRock_Open_Sell_Order = theRock_Order(Exchange1['EUR']/Exchange1['sell'], 'sell', Exchange1['sell'])
#                    Open_Sell_Order.append(theRock_Open_Sell_Order) # Check if order executed
#                except:
#                    continue
#                break
#            
#        elif Exchange1['Name'] == 'Bl3p':
#            while True:
#                try:
#                    Bl3p_Open_Sell_Order = Bl3p_Order(Exchange1['EUR']/Exchange1['sell'], 'sell', Exchange1['sell'])
#                    Open_Sell_Order.append(Bl3p_Open_Sell_Order) # Check if order executed
#                except:
#                    continue
#                break
#            
#        elif Exchange1['Name'] == 'Gatecoin':
#            while True:
#                try:
#                    Gatecoin_Open_Sell_Order = Gatecoin_Order(Exchange1['EUR']/Exchange1['sell'], 'sell', Exchange1['sell'])
#                    Open_Sell_Order.append(Gatecoin_Open_Sell_Order) # Check if order executed
#                except:
#                    continue
#                break        
                    
            
        print 'Sold ' + str(BTC_Amount_to_Sell) + pair1[0] + ' at ' + str(Exchange1['Name'])
        log_file.write('Shorted ' + str(BTC_Amount_to_Sell) + pair1[0] + ' at ' + str(Exchange1['Name']))       
        
        
        print 'Attempting to buyback ' + Exchange2['Name']
        log_file.write('Attempting to buyback ' + Exchange2['Name'])        
        
#        if Exchange2['Name'] == 'Kraken':
#            while True:
#                try:
#                    Kraken_Open_Buy_Order = Kraken_Order(Exchange2['EUR']/Exchange2['buy'], 'buy', Exchange2['buy'], 1)
#                    Open_Buy_Order.append(Kraken_Open_Buy_Order) # Check if order executed
#                except:
#                    continue
#                break                       
#            
#        elif Exchange2['Name'] == 'Bitstamp':
#            while True:
#                try:
#                    Bitstamp_Open_Buy_Order = Bitstamp_Order(Exchange2['EUR']/Exchange2['buy'], 'buy', Exchange2['buy'])
#                    Open_Buy_Order.append(Bitstamp_Open_Buy_Order) # Check if order executed
#                except:
#                    continue
#                break
#        
#        elif Exchange2['Name'] == 'Gdax':
#            while True:
#                try:
#                    Gdax_Open_Buy_Order = Gdax_Order(Exchange2['EUR']/Exchange2['buy'], 'buy', Exchange2['buy'], 1)
#                    Open_Buy_Order.append(Gdax_Open_Buy_Order) # Check if order executed
#                except:
#                    continue
#                break
#            
#        elif Exchange2['Name'] == 'theRock':
#            while True:
#                try:
#                    theRock_Open_Buy_Order = theRock_Order(Exchange2['EUR']/Exchange2['buy'], 'buy', Exchange2['buy'])
#                    Open_Buy_Order.append(theRock_Open_Buy_Order) # Check if order executed
#                except:
#                    continue
#                break
#            
#        elif Exchange2['Name'] == 'Bl3p':
#            while True:
#                try:
#                    Bl3p_Open_Buy_Order = Bl3p_Order(Exchange2['EUR']/Exchange2['buy'], 'buy', Exchange2['buy'])
#                    Open_Buy_Order.append(Bl3p_Open_Buy_Order) # Check if order executed
#                except:
#                    continue
#                break
#            
#        elif Exchange2['Name'] == 'Gatecoin':
#            while True:
#                try:
#                    Gatecoin_Open_Buy_Order = Gatecoin_Order(Exchange2['EUR']/Exchange2['buy'], 'buy', Exchange2['buy'])
#                    Open_Buy_Order.append(Gatecoin_Open_Buy_Order) # Check if order executed
#                except:
#                    continue
#                break           
      
        
        print 'BoughtBack ' + str(BTC_Amount_to_Buyback) + pair2[0] + ' at ' + str(Exchange2['Name'])
        log_file.write('BoughtBack ' + str(BTC_Amount_to_Buyback) + pair2[0] + ' at ' + str(Exchange2['Name']))
        
        
        
        
        Open_Buy_Order = [1]       ###### Remove This for real thing
        Open_Sell_Order = [1]         ###### Remove This for real thing
        
        
        
        
        
        
        if Open_Buy_Order and Open_Sell_Order is True:
            
            if Open_Arbs['Name1'] == 'Kraken':
                Exchange1.append(Kraken_Full())
            elif Open_Arbs['Name1'] == 'Bitstamp':
                Exchange1.append(Bitstamp_Full())
            elif Open_Arbs['Name1'] == 'Gdax':
                Exchange1.append(Gdax_Full())
            elif Open_Arbs['Name1'] == 'theRock':
                Exchange1.append(theRock_Full())
            elif Open_Arbs['Name1'] == 'Bl3p':
                Exchange1.append(Bl3p_Full())
            elif Open_Arbs['Name1'] == 'Gatecoin':
                Exchange1.append(Gatecoin_Full())
                
            if Open_Arbs['Name2'] == 'Kraken':
                Exchange2.append(Kraken_Full())
            elif Open_Arbs['Name2'] == 'Bitstamp':
                Exchange2.append(Bitstamp_Full())
            elif Open_Arbs['Name2'] == 'Gdax':
                Exchange2.append(Gdax_Full())
            elif Open_Arbs['Name2'] == 'theRock':
                Exchange2.append(theRock_Full())
            elif Open_Arbs['Name2'] == 'Bl3p':
                Exchange2.append(Bl3p_Full())
            elif Open_Arbs['Name2'] == 'Gatecoin':
                Exchange2.append(Gatecoin_Full())
                
                
            Total_Close_Balance = Exchange1['EUR'] + Exchange2['EUR']            
            Profit = Total_Close_Balance - Total_Open_Balance
            
            print 'Profit = ' +str(Profit) + 'EUR' 
            log_file.write('\nProfit = ' +str(Profit) + 'EUR' )
            
            
            for Arb in Current_Arbs:
                if Arb['Name1'] ==  Exchange1['Name'] and Arb['Name2'] ==  Exchange2['Name']:
                    Current_Arbs.Remove(Arb)
        

       
    else:
        
        print '\nNo Exit Found'
        print Exchange1['Name']+'_'+Exchange2['Name'], spread
        log_file.write('\nNo Exit Found')
        log_file.write(Exchange1['Name']+'_'+Exchange2['Name'], spread)
    
    
def Get_Perm(Exchanges):
    
    Permuatations = list(itertools.permutations(Exchanges, 2))
    Permuatations = [i for i in Permuatations if i[1]['Shorting'] is True]

    return Permuatations
    


##############################################################################


#def main(): 

log_file = open("Log.txt", "w")


    
Current_Arbs = []

Updated_Arbs = []

while True:
    
    log_file = open("Log.txt", "a")
    
    print '\nScanning Markets'
    print '\n'+str(datetime.now())  
    log_file.write('\n\nScanning Markets')      
    log_file.write('\n'+str(datetime.now()))
    

#    def Get_Basic_Data():
#        Kraken = Kraken_Basic()
#        Bitstamp = Bitstamp_Basic()
#        Gdax = Gdax_Basic()
#        TheRock = theRock_Basic()
#        Bl3p = Bl3p_Basic()
#        Gatecoin = Gatecoin_Basic()
#        
#        return Kraken, Bitstamp, Gdax, TheRock, Bl3p, Gatecoin
#        
#    Exchanges = []  
#        
#    for i in range(1, 6):
#        t = threading.Thread(target=Get_Basic_Data, args=(i,))
#        Exchanges.append(t)
#        
#    for thread in Exchanges:
#        thread.start()
#        
#    for thread in Exchanges:
#        thread.join()
        
    try:
        Kraken = Kraken_Basic()
        Bitstamp = Bitstamp_Basic()
        Gdax = Gdax_Basic()
        TheRock = theRock_Basic()
        Bl3p = Bl3p_Basic()
        Gatecoin = Gatecoin_Basic() 
    except:
        continue
      

    Exchanges = [Kraken, Bitstamp, Gdax, TheRock, Bl3p, Gatecoin] # add BTCe(Raided by FBI), xBTCe when ready
        
    Permuatations = Get_Perm(Exchanges)
    
    Opportunities = []   
    
    for Exchanges in Permuatations:    
        try:
            Calc_Spread(Exchanges)        
        except:
            continue
        
    
    for Opportunity in Opportunities:
#        try:
            Open(Opportunity)
#        except:
#            
#            continue    
    
            
    for Arb in Current_Arbs:    
        try:
            Update(Current_Arbs)
            Close(Updated_Arbs)
        except:
            print Arb[0]['Name']+'_'+Arb[1]['Name'] +'Close Failed'
            
    log_file.close()

    time.sleep(5)
       
        
#if __name__ == "__main__":
#    main()   
    
    

