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


import Keys




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
                  
    return (float(price['a'][0]), float(price['b'][0]))
    
def Kraken_Fees():
    pair = 'X'+pair1[1]+'Z'+pair2
    API = krakenex.API()
    fees = API.query_public('AssetPairs', {'info': 'fees'})['result'][pair]
    
    return (float(fees['fees'][0][1]), float(fees['fees_maker'][0][1]))
         
def Kraken_Balances():   

    balance = Kraken_Private_Client('Balance')['result']
    
    btc = round(float(balance['XXBT']),8)
    eur = round(float(balance['ZEUR']),2)
    
    return (btc, eur)
    
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
    
def make_Kraken():
    (Kraken_PriceA, Kraken_PriceB) = Kraken_Price()           
    (Kraken_FeeA, Kraken_FeeB) = Kraken_Fees()
    (Kraken_BTC, Kraken_EUR) = Kraken_Balances()

    Kraken = {'Name': 'Kraken',
              'buy': Kraken_PriceA,
              'sell': Kraken_PriceB,
              'buy_fee': Kraken_FeeA,
              'sell_fee': Kraken_FeeB,
              'BTC': Kraken_BTC,
              'EUR': Kraken_EUR,
              'Shorting': True}
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
    return (float(price['ask']), float(price['bid']))
    
def Bitstamp_Balance_Fees():
    
    pair = pair1[0].lower(), pair2.lower()
    balance = Bitstamp_Private_Client().account_balance(pair[0], pair[1])
    
    fee = float(balance['fee'])
    BTC =  float(balance['btc_balance'])
    EUR =  float(balance['eur_balance'])

    return (fee, BTC, EUR)
    
def Bitstamp_Order(amount, side, price):
    
    pair = pair1[0].lower(), pair2.lower()    
    Order = Bitstamp_Private_Client().limit_order(amount, side, price, pair[0], pair[1])  
    
    return Order
    
def Bitstamp_Check_Order(ref):
    
    Order = Bitstamp_Private_Client().order_status(ref)
    
    return Order
    
def make_Bitstamp():
    (Bitstamp_PriceA, Bitstamp_PriceB) = Bitstamp_Price()
    (Bitstamp_Fee, Bitstamp_BTC, Bitstamp_EUR) = Bitstamp_Balance_Fees()
    
    Bitstamp = {'Name': 'Bitstamp',
            'buy': Bitstamp_PriceA,
            'sell': Bitstamp_PriceB,
            'buy_fee': Bitstamp_Fee,
            'sell_fee': Bitstamp_Fee,
            'BTC': Bitstamp_BTC,
            'EUR': Bitstamp_EUR,
            'Shorting': False} # Coming soon
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
    return (float(price['ask']), float(price['bid']))

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

    return (buy_fee, sell_fee)

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
            
    return (btc, eur)
    
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
    
def make_GDAX():
    (GDAX_PriceA, GDAX_PriceB) = Gdax_Price()
    (GDAX_BTC, GDAX_EUR) = Gdax_Balances()
    (GDAX_feeA, GDAX_feeB) = Gdax_Fees()
    
    Gdax = {'Name': 'GDAX',
            'buy': GDAX_PriceA,
            'sell': GDAX_PriceB,
            'buy_fee': GDAX_feeA,
            'sell_fee': GDAX_feeB,
            'BTC': GDAX_BTC,
            'EUR': GDAX_EUR,
            'Shorting': True}
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
    return (float(price['buy']), float(price['sell']))    

def BTCe_Fees():    
    
    pair = pair1[0].lower()+'_'+pair2.lower()    
    api = btce.api.PublicAPIv3()
    fee = api.call('info')['pairs'][pair]['fee']    
    return float(fee)
    
def BTCe_Balances():

    balances = BTCe_Private_Client().call('getInfo')['funds']
    btc = round(float(balances['btc']),8)
    eur = round(float(balances['eur']),2)    
    return (btc, eur)
    
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

def make_BTCe():
    
    (BTCe_PriceA, BTCe_PriceB) = BTCe_Price() 
    BTCe_Fee = BTCe_Fees()
    (BTCe_BTC, BTCe_EUR) = BTCe_Balances()   
    
    BTCe = {'Name': 'BTCe',
            'buy': BTCe_PriceA,
            'sell': BTCe_PriceB,
            'buy_fee': BTCe_Fee,
            'sell_fee': BTCe_Fee,
            'BTC': BTCe_BTC,
            'EUR': BTCe_EUR,
            'Shorting': False}
            
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
    return (float(price['ask']), float(price['bid']))

def Bl3p_Balances_Fees():    

    balances = Bl3p_Private_Client().getBalances()
    
    EUR =  round(float(balances['data']['wallets']['EUR']['available']['value']),2)    
    BTC = round(float(balances['data']['wallets']['BTC']['available']['value']), 8)       
    fee = float(balances['data']['trade_fee']) # plus 0.01eur per trade
    
    return (EUR, BTC, fee)
    
def Bl3p_Order(amount, side, price):
    
    pair = pair1[0] + pair2    
    Order = Bl3p_Private_Client().addOrder(pair, side, amount, price)    
    return Order
    
def Bl3p_Check_Order(ref):
    
    pair = pair1[0] + pair2    
    Order = Bl3p_Private_Client().checkOrder(pair, ref)    
    return Order

def make_Bl3p():
    (Bl3p_PriceA ,Bl3p_PriceB)=  Bl3p_Price()
    (Bl3p_EUR, Bl3p_BTC, Bl3p_Fee) = Bl3p_Balances_Fees()
    
    
    Bl3p = {'Name': 'Bl3p',
        'buy': Bl3p_PriceA,
        'sell': Bl3p_PriceB,
        'buy_fee': Bl3p_Fee,
        'sell_fee': Bl3p_Fee,
        'BTC': Bl3p_BTC,
        'EUR': Bl3p_EUR,
        'Shorting': False}
        
    return Bl3p

##############################################################################

def theRock_Private_Client():
    
    Key = Keys.theRock()
    client = theRock.PyRock.API(Key['key'], Key['secret'])
    return client

def theRock_Price():
    
    pair = pair1[0].lower() + pair2.lower()
    price = theRock_Private_Client().Ticker(pair)
    return (float(price['ask']), float(price['bid']))
    
def theRock_Balances():  

    balances = theRock_Private_Client().AllBalances()
    balances = balances['balances']
    
    for balance in balances:  
        if balance['currency'] == 'BTC':
            BTC = round(float(balance['trading_balance']),2)
        elif balance['currency'] == 'EUR':
            EUR = round(float(balance['trading_balance']),2) 
        
    return (BTC, EUR)
    
def theRock_Fees():
    
    pair = pair1[0] + pair2 
    funds = theRock_Private_Client().Funds()['funds']
    
    for fund in funds:
        if fund['id'] == pair:
            buy_fee = fund['buy_fee']
            sell_fee = fund['sell_fee']
            
    return (buy_fee, sell_fee)
    
def theRock_Order(amount, side, price):
    
    pair = pair1[0].lower() + pair2.lower()
    Order = theRock_Private_Client().PlaceOrder(pair, amount, side, price)    
    return Order
    
def theRock_Check_Order(ref):
    
    pair = pair1[0].lower() + pair2.lower()
    Order = theRock_Private_Client().ListOrder(pair, ref)    
    return Order

def make_theRock():

    (theRock_BTC, theRock_EUR) = theRock_Balances()
    (theRock_FeeA, theRock_FeeB) = theRock_Fees()
    (theRock_PriceA, theRock_PriceB)=  theRock_Price()
    
    TheRock = {'Name': 'TheRock',
            'buy': theRock_PriceA,
            'sell': theRock_PriceB,
            'buy_fee': theRock_FeeA,
            'sell_fee': theRock_FeeB,
            'BTC': theRock_BTC,
            'EUR': theRock_EUR,
            'Shorting': True}
            
    return TheRock

########################################################################

def xBTCe_Price():
    
    pair = pair1[0] + pair2
    client = xBTCe.Client.API()
    price = client.getTicker(pair)
    return (float(price['BestAsk']), float(price['BestBid']))
    

def make_XBTCE():
    
    (xBTCe_PriceA, xBTCe_PriceB) = xBTCe_Price()

    XBTCE = {'Name': 'xBTCe',
        'buy': xBTCe_PriceA, 
        'sell': xBTCe_PriceB,
        'buy_fee': 0.2,
        'sell_fee': 0.1,
        'Shorting': False}
        
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
            
    return (float(price['ask']), float(price['bid']))

def Gatecoin_Balances():
    
    balances = Gatecoin_Private_Client().get_balances()
    
    for balance in balances['balances']:
        if balance['currency'] == pair2:
            EUR = round(float(balance['availableBalance']),2)
            
        elif balance['currency'] == pair1[0]:
            BTC = round(float(balance['availableBalance']),8)
            
    return (EUR, BTC)
    
def Gatecoin_Order(amount, price, side):
    
    pair = pair1[0] + pair2    
    Order = Gatecoin_Private_Client().place_order(pair, amount, price, side)    
    return Order
    
def Gatecoin_Check_Order(ref):
    
    Order = Gatecoin_Private_Client().get_order(ref)    
    return Order
 
def make_Gatecoin():

    (Gatecoin_PriceA, Gatecoin_PriceB) = Gatecoin_Price()
    (Gatecoin_EUR, Gatecoin_BTC) = Gatecoin_Balances()
    
    Gatecoin = {'Name': 'Gatecoin',
            'buy': Gatecoin_PriceA,
            'sell': Gatecoin_PriceB,
            'buy_fee': 0.35, 
            'sell_fee': 0.25,
            'BTC': Gatecoin_BTC,
            'EUR': Gatecoin_EUR,
            'Shorting': False} # Coming soon
            
    return Gatecoin
    


###########################################################################
###########################################################################
def Calc_Spread(Opportunity):    
       
    Exchange1 = Opportunity[0]
    Exchange2 = Opportunity[1]
    
    sell = Exchange2['sell'] - (Exchange2['sell'] * (Exchange2['sell_fee'] / 100))
    buy = Exchange1['buy'] - (Exchange1['buy'] * (Exchange1['buy_fee'] / 100))
    
    spread = (sell - buy) / buy * 100
    
    Opportunities.append([Exchange1, Exchange2, spread])
    
    
def Open(Opportunity):
    
    Exchange1 = Opportunity[0]
    Exchange2 = Opportunity[1]
    
    spread = Opportunity[2]
    
    Open_Buy_Order = []
    Open_Sell_Order = []
    
        
    if spread > 2 and Exchange1['EUR'] > 25 and Exchange2['EUR'] > 25:
        
        print '\nEntry Found'
        print Exchange1['Name']+'_'+Exchange2['Name']+' '+str(spread)        
        log_file.write('\n\nEntry Found')        
        log_file.write(Exchange1['Name']+'_'+Exchange2['Name']+' '+str(spread))
        
        
        print 'Attempting to buy ' + Exchange1['Name']
        log_file.write('Attempting to buy ' + Exchange1['Name'])
        
        if Exchange1['Name'] == 'Kraken':
            while True:
                try:
                    Kraken_Open_Buy_Order = Kraken_Order(Exchange1['EUR']/Exchange1['buy'], 'buy', Exchange1['buy'], 1)
                    Open_Buy_Order.append(Kraken_Open_Buy_Order) # Check if order executed
                except:
                    continue
                break                       
            
        elif Exchange1['Name'] == 'Bitstamp':
            while True:
                try:
                    Bitstamp_Open_Buy_Order = Bitstamp_Order(Exchange1['EUR']/Exchange1['buy'], 'buy', Exchange1['buy'])
                    Open_Buy_Order.append(Bitstamp_Open_Buy_Order) # Check if order executed
                except:
                    continue
                break
        
        elif Exchange1['Name'] == 'Gdax':
            while True:
                try:
                    Gdax_Open_Buy_Order = Gdax_Order(Exchange1['EUR']/Exchange1['buy'], 'buy', Exchange1['buy'], 1)
                    Open_Buy_Order.append(Gdax_Open_Buy_Order) # Check if order executed
                except:
                    continue
                break
            
        elif Exchange1['Name'] == 'theRock':
            while True:
                try:
                    theRock_Open_Buy_Order = theRock_Order(Exchange1['EUR']/Exchange1['buy'], 'buy', Exchange1['buy'])
                    Open_Buy_Order.append(theRock_Open_Buy_Order) # Check if order executed
                except:
                    continue
                break
            
        elif Exchange1['Name'] == 'Bl3p':
            while True:
                try:
                    Bl3p_Open_Buy_Order = Bl3p_Order(Exchange1['EUR']/Exchange1['buy'], 'buy', Exchange1['buy'])
                    Open_Buy_Order.append(Bl3p_Open_Buy_Order) # Check if order executed
                except:
                    continue
                break
            
        elif Exchange1['Name'] == 'Gatecoin':
            while True:
                try:
                    Gatecoin_Open_Buy_Order = Gatecoin_Order(Exchange1['EUR']/Exchange1['buy'], 'buy', Exchange1['buy'])
                    Open_Buy_Order.append(Gatecoin_Open_Buy_Order) # Check if order executed
                except:
                    continue
                break
            
                    
        print 'Bought ' + str(Exchange1['EUR']/Exchange1['buy']) + pair1[0] + ' at ' + str(Exchange1['Name'])        
        log_file.write('Bought ' + str(Exchange1['EUR']/Exchange1['buy']) + pair1[0] + ' at ' + str(Exchange1['Name']))

        
        if Exchange2['Name'] == 'Kraken':
            while True:
                try:
                    Kraken_Open_sell_Order = Kraken_Order(Exchange2['EUR']/Exchange2['sell'], 'sell', Exchange2['sell'], 1)
                    Open_Sell_Order.append(Kraken_Open_sell_Order) # Check if order executed
                except:
                    continue
                break                       
            
        elif Exchange2['Name'] == 'Bitstamp':
            while True:
                try:
                    Bitstamp_Open_sell_Order = Bitstamp_Order(Exchange2['EUR']/Exchange2['sell'], 'sell', Exchange2['sell'])
                    Open_Sell_Order.append(Bitstamp_Open_sell_Order) # Check if order executed
                except:
                    continue
                break
        
        elif Exchange2['Name'] == 'Gdax':
            while True:
                try:
                    Gdax_Open_sell_Order = Gdax_Order(Exchange2['EUR']/Exchange2['sell'], 'sell', Exchange2['sell'], 1)
                    Open_Sell_Order.append(Gdax_Open_sell_Order) # Check if order executed
                except:
                    continue
                break
            
        elif Exchange2['Name'] == 'theRock':
            while True:
                try:
                    theRock_Open_sell_Order = theRock_Order(Exchange2['EUR']/Exchange2['sell'], 'sell', Exchange2['sell'])
                    Open_Sell_Order.append(theRock_Open_sell_Order) # Check if order executed
                except:
                    continue
                break
            
        elif Exchange2['Name'] == 'Bl3p':
            while True:
                try:
                    Bl3p_Open_sell_Order = Bl3p_Order(Exchange2['EUR']/Exchange2['sell'], 'sell', Exchange2['sell'])
                    Open_Sell_Order.append(Bl3p_Open_sell_Order) # Check if order executed
                except:
                    continue
                break
            
        elif Exchange2['Name'] == 'Gatecoin':
            while True:
                try:
                    Gatecoin_Open_sell_Order = Gatecoin_Order(Exchange2['EUR']/Exchange2['sell'], 'sell', Exchange2['sell'])
                    Open_Sell_Order.append(Gatecoin_Open_sell_Order) # Check if order executed
                except:
                    continue
                break
            
        print 'Shorted ' + str(Exchange2['EUR']/Exchange2['sell']) + pair1[0] + ' at ' + str(Exchange2['Name'])
        log_file.write('Shorted ' + str(Exchange2['EUR']/Exchange2['sell']) + pair1[0] + ' at ' + str(Exchange2['Name']))
            
        
        if Open_Buy_Order and Open_Sell_Order is True:
            Current_Arbs.append((Exchange1['Name'],Exchange2['Name']))  

            
def Update(Exchanges):
    
    Exchange1 = []
    Exchange2 = []
    
    if Exchanges[0]['Name'] == 'Kraken':
        Exchange1.append(make_Kraken())
    if Exchanges[0]['Name'] == 'Bitstamp':
        Exchange1.append(make_Bitstamp())
    if Exchanges[0]['Name'] == 'Gdax':
        Exchange1.append(make_GDAX())
    if Exchanges[0]['Name'] == 'theRock':
        Exchange1.append(make_theRock())
    if Exchanges[0]['Name'] == 'Bl3p':
        Exchange1.append(make_Bl3p())
    if Exchanges[0]['Name'] == 'Gatecoin':
        Exchange1.append(make_Gatecoin())
        
    if Exchanges[1]['Name'] == 'Kraken':
        Exchange2.append(make_Kraken())
    if Exchanges[1]['Name'] == 'Bitstamp':
        Exchange2.append(Bitstamp())
    if Exchanges[1]['Name'] == 'Gdax':
        Exchange2.append(make_GDAX())
    if Exchanges[1]['Name'] == 'theRock':
        Exchange2.append(make_theRock())
    if Exchanges[1]['Name'] == 'Bl3p':
        Exchange2.append(make_Bl3p())
    if Exchanges[1]['Name'] == 'Gatecoin':
        Exchange2.append(make_Gatecoin())    
    
    sell = Exchange2['sell'] - (Exchange2['sell'] * (Exchange2['sell_fee'] / 100))
    buy = Exchange1['buy'] - (Exchange1['buy'] * (Exchange1['buy_fee'] / 100))
    
    spread = (sell - buy) / buy * 100
    
    Updated_Arbs.append([Exchange1, Exchange2, spread])       
        
        
       
def Close(Arbs):
    
    Exchange1 = Arbs[0]
    Exchange2 = Arbs[1]      
    spread = Arbs[2]
    
    if spread < 0.1:
        
        BTC_Amount_to_Sell = Exchange1['BTC']
        BTC_Amount_to_Buyback = Exchange2['BTC']
        
        print '\nExit Found'
        print Exchange1['Name']+'_'+Exchange2['Name'], spread
        log_file.write('\n\nExit Found')       
        log_file.write(Exchange1['Name']+'_'+Exchange2['Name'], spread)
        
        
        print 'Attempting to sell ' + Exchange1['Name']
        log_file.write('Attempting to sell ' + Exchange1['Name'])        
        
        if Exchange1['Name'] == 'Kraken':            
            Kraken_Open_Order = Kraken_Order(Exchange1['BTC'], 'sell', Exchange1['sell'], 1)
            print Kraken_Open_Order # Check if order executed                    
            Update_Balances = Kraken_Balances()            
            
        elif Exchange1['Name'] == 'Bitstamp':
            Bitstamp_Open_Order = Bitstamp_Order(Exchange1['BTC'], 'sell', Exchange1['sell'])
            print Bitstamp_Open_Order # Check if order executed           
            Update_Balances = Bitstamp_Balance_Fees()
          
        
        elif Exchange1['Name'] == 'Gdax':
            Gdax_Open_Order = Gdax_Order(Exchange1['BTC'], 'sell', Exchange1['sell'], 1)
            print Gdax_Open_Order # Check if order executed           
            Update_Balances = Gdax_Balances()
            
        elif Exchange1['Name'] == 'theRock':
            theRock_Open_Order = theRock_Order(Exchange1['BTC'], 'sell', Exchange1['sell'])
            print theRock_Open_Order # Check if order executed           
            Update_Balances = theRock_Balances()
            
        elif Exchange1['Name'] == 'Bl3p':
            Bl3p_Open_Order = Bl3p_Order(Exchange1['BTC'], 'sell', Exchange1['sell'])
            print Bl3p_Open_Order # Check if order executed           
            Update_Balances = Bl3p_Balances_Fees()
            
        elif Exchange1['Name'] == 'Gatecoin':
            Gatecoin_Open_Order = Gatecoin_Order(Exchange1['BTC'], 'sell', Exchange1['sell'])
            print Gatecoin_Open_Order # Check if order executed           
            Update_Balances = Gatecoin_Balances()                    
                    
        Exchange1['EUR'] = Update_Balances['EUR']
        Exchange1['BTC'] = Update_Balances['BTC']
            
        print 'Sold ' + str(BTC_Amount_to_Sell) + pair1[0] + ' at ' + str(Exchange1['Name'])
        log_file.write('Shorted ' + str(BTC_Amount_to_Sell) + pair1[0] + ' at ' + str(Exchange1['Name']))       
        
        
        print 'Attempting to buyback ' + Exchange2['Name']
        log_file.write('Attempting to buyback ' + Exchange2['Name'])        
        
        if Exchange2['Name'] == 'Kraken':            
            Kraken_Open_Order = Kraken_Order(Exchange2['BTC'], 'buy', Exchange2['buy'], 1)
            print Kraken_Open_Order # Check if order executed                    
            Update_Balances = Kraken_Balances()           
            
        elif Exchange2['Name'] == 'Bitstamp':
            Bitstamp_Open_Order = Bitstamp_Order(Exchange2['BTC'], 'buy', Exchange2['buy'])
            print Bitstamp_Open_Order # Check if order executed           
            Update_Balances = Bitstamp_Balance_Fees()          
        
        elif Exchange2['Name'] == 'Gdax':
            Gdax_Open_Order = Gdax_Order(Exchange2['BTC'], 'buy', Exchange2['buy'], 1)
            print Gdax_Open_Order # Check if order executed           
            Update_Balances = Gdax_Balances()
            
        elif Exchange2['Name'] == 'theRock':
            theRock_Open_Order = theRock_Order(Exchange2['BTC'], 'buy', Exchange2['buy'])
            print theRock_Open_Order # Check if order executed           
            Update_Balances = theRock_Balances()
            
        elif Exchange2['Name'] == 'Bl3p':
            Bl3p_Open_Order = Bl3p_Order(Exchange2['BTC'], 'buy', Exchange2['buy'])
            print Bl3p_Open_Order # Check if order executed           
            Update_Balances = Bl3p_Balances_Fees()
            
        elif Exchange2['Name'] == 'Gatecoin':
            Gatecoin_Open_Order = Gatecoin_Order(Exchange2['BTC'], 'buy', Exchange2['buy'])
            print Gatecoin_Open_Order # Check if order executed           
            Update_Balances = Gatecoin_Balances()
                    
        Exchange2['EUR'] = Update_Balances['EUR']
        Exchange2['BTC'] = Update_Balances['BTC']
      
        
        print 'BoughtBack ' + str(BTC_Amount_to_Buyback) + pair2[0] + ' at ' + str(Exchange2['Name'])
        log_file.write('BoughtBack ' + str(BTC_Amount_to_Buyback) + pair2[0] + ' at ' + str(Exchange2['Name']))        
        
        # Profit
       
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

while True:
    
    log_file = open("Log.txt", "a")
    
    print '\nScanning Markets'
    print '\n'+str(datetime.now())  
    log_file.write('\n\nScanning Markets')      
    log_file.write('\n'+str(datetime.now()))

    Kraken = make_Kraken()
    Bitstamp = make_Bitstamp()
    Gdax = make_GDAX()
    TheRock = make_theRock()
    Bl3p = make_Bl3p()
    Gatecoin = make_Gatecoin()
    
    #XBTCE = make_XBTCE()
    #BTCe = make_BTCe()

    Exchanges = [Kraken, Bitstamp, Gdax, TheRock, Bl3p, Gatecoin] # add BTCe(Raided by FBI), xBTCe when ready
#    for ex in Exchanges:
#        print ex
        
    Permuatations = Get_Perm(Exchanges)
    
    Opportunities = []
    
    Current_Arbs = []
    
    for Opportunity in Permuatations:    
        try:
            Calc_Spread(Opportunity)        
        except:
            print 'Spread Calc Failed'
            continue
        
    print Opportunities
    
    for Opportunity in Opportunities:
        try:
            Open(Opportunity)
        except:
            print 'Opportunity' + Opportunity[0]['Name']+'_'+Opportunity[1]['Name'] +'Open Failed'
            continue
    
    Updated_Arbs = []
            
    for Arb in Current_Arbs:    
        try:
            Update(Current_Arbs)
            Close(Updated_Arbs)
        except:
            print Arb[0]['Name']+'_'+Arb[1]['Name'] +'Close Failed'
            
    log_file.close()

    time.sleep(10)
       
        
#if __name__ == "__main__":
#    main()   
    
    

