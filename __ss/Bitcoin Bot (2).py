import itertools
import time
from datetime import datetime
import uuid
import winsound

import krakenex #Shorting ok
import theRock #Shorting ok
import GDAX # Shorting disabled server side until further notice
import bitstamp #Shorting coming soon
import bl3p
#import gatecoin # Scrap This, Stupid sell prices, 8% above market

#import xBTCe # Shorting coming soon / Need to figure out private client
#import btce # Exchange raided by FBI no called WEX

import Keys

###############################################################################

Test_Mode = False   #### Change to False to run for real!

Kraken = {'Name': 'Kraken', 'Shorting': True} ##
Bitstamp = {'Name': 'Bitstamp', 'Shorting': False}
Gdax = {'Name': 'Gdax', 'Shorting': False}
Bl3p = {'Name': 'Bl3p', 'Shorting': False}
TheRock = {'Name': 'theRock', 'Shorting': False} # No naked shorts :(
#Gatecoin = {'Name': 'Gatecoin', 'Shorting': False}

Min_Bal = 5.00 # Min Balance to execute on
Target_Profit = 0.2 # Percent (after fees and slippage)
liquid_factor = 2.0 # multiplied by trade amount, determine if adequate liquidity

Attempts = 3 # re-tries for server
Attempts += 1 # add 1 to actually execute a number of attempts due tp range function behviour

pair1 = 'BTC', 'XBT'
pair2 = 'EUR'

if Test_Mode is True:
    
    Test_Balance = {'EUR': 1000.00, 'BTC': 0.00000000}
    
    Balances = {'Kraken': Test_Balance,
                'Bitstamp': Test_Balance, 
                'Gdax': Test_Balance, 
                'Bl3p': Test_Balance, 
                'theRock': Test_Balance}
                
else:    
    Balances = {} # update the later in the script with real values

###############################################################################


def Kraken_Private_Client(query, params={}):
    
    Key = Keys.Kraken()
    client = krakenex.API(Key['key'],Key['secret']).query_private(query,params)
    return client
    
def Kraken_Fees():
    pair = 'X'+pair1[1]+'Z'+pair2
    API = krakenex.API()
    fees = API.query_public('AssetPairs', {'info': 'fees'})['result'][pair]
    
    return {'buy_fee': float(fees['fees'][0][1]), 
            'sell_fee': float(fees['fees_maker'][0][1])}
         
def Kraken_Balances():   

    balance = Kraken_Private_Client('Balance')['result']
    
    btc = round(float(balance['XXBT']),8)
    eur = round(float(balance['ZEUR']),2)
    
    return {'BTC': btc, 'EUR': eur}
    
def Kraken_Limit_Order(amount, side, price, leverage):
    
    pair = 'X'+pair1[1]+'Z'+pair2
    
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
    
def Kraken_Market_Order(amount, side, leverage):
    
    pair = 'X'+pair1[1]+'Z'+pair2
    
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
    
  
def Kraken_Orderbook():
    
    pair = 'X'+pair1[1]+'Z'+pair2    
    API = krakenex.API()    
    Orderbook = API.query_public('Depth', {'pair': pair})['result'][pair]
    
    Asks = Orderbook['asks']    
    Bids = Orderbook['bids']
    
    return (Asks, Bids)
    
    
def Kraken_Filled(Order):
    
    Order_ID = Order['ID']
    print Order_ID
    
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
    
def Bitstamp_Limit_Order(amount, side, price):
    
    pair = pair1[0].lower(), pair2.lower()    
    Order = Bitstamp_Private_Client().limit_order(str(amount), str(side),
                                                  str(price), pair[0], pair[1])  

    print 'Message from Bitstamp: ' + str(Order)
    log.write('\nMessage from Bitstamp: ' + str(Order)) 
    
    return Order
    
def Bitstamp_Market_Order(amount, side):
    
    pair = pair1[0].lower(), pair2.lower()    
    Order = Bitstamp_Private_Client().market_order(str(amount), str(side), pair[0], pair[1])  

    print 'Message from Bitstamp: ' + str(Order)
    log.write('\nMessage from Bitstamp: ' + str(Order)) 
    
    return Order
    
def Bitstamp_Check_Order(ref):
    
    Order = Bitstamp_Private_Client().order_status(ref)
    
    print 'Message from Bitstamp: ' + str(Order)
    log.write('\nMessage from Bitstamp: ' + str(Order)) 
    
    return Order

    
def Bitstamp_Orderbook():
    
    pair = pair1[0].lower(), pair2.lower()    
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

def Gdax_Balances():
    
    key = Keys.GDAX()
        
    client = GDAX.AuthenticatedClient(key['key'],key['secret'],key['passphrase'])
    accounts = client.getAccounts()
    
    for account in accounts:
        if account['currency'] == 'EUR':
            eur = round(float(account['balance']),2)  
    
    for account in accounts:
        if account['currency'] == 'BTC':
            btc = round(float(account['balance']),8)
            
    return {'BTC': btc, 'EUR': eur}
    
def Gdax_Limit_Order(amount, side, price): #, margin): waiting to be margin approved
    
    pair = pair1[0]+ '-' + pair2
    
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
    
def Gdax_Market_Order(amount, side): #, margin): waiting to be margin approved
    
    pair = pair1[0]+ '-' + pair2
    
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
    
def Gdax_Orderbook():
    
    pair = pair1[0]+ '-' + pair2   
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

#def BTCe_Private_Client():
#    
#    key = Keys.BTCe()    
#    client = btce.api.TradeAPIv1(key)
#    return client
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
#    BTCe_Basic.update(BTCe_Fees())
#
#    return BTCe_Basic
#
#def BTCe_Full():   
#    
#    BTCe = BTCe_Basic().update(BTCe_Balances())
#            
#    return BTCe

###############################################################################

def Bl3p_Private_Client():
    key = Keys.Bl3p()    
    client = bl3p.Client.Private(key['key'], key['secret'])
    return client

def Bl3p_Balances():    

    balances = Bl3p_Private_Client().getBalances()
    
    EUR =  round(float(balances['data']['wallets']['EUR']['available']['value']),2)    
    BTC = round(float(balances['data']['wallets']['BTC']['available']['value']), 8)
    
    return {'EUR': EUR, 'BTC': BTC}
    
def Bl3p_Fees():
    
    balances = Bl3p_Private_Client().getBalances()    
    fee = float(balances['data']['trade_fee']) # plus 0.01eur per trade
    
    return {'buy_fee': fee, 'sell_fee': fee}
    
def Bl3p_Limit_Order(amount, side, price):
    
    pair = pair1[0] + pair2
    
    if side == 'buy':
        order_side = 'bid'
    if side == 'sell':
        order_side = 'ask'
    
    Order = Bl3p_Private_Client().addOrder(pair, str(order_side), 
                                           int(amount), int(price))

    print 'Message from Bl3p: ' + str(Order)
    log.write('\nMessage from Bl3p: ' + str(Order)) 
    
    return Order
    
def Bl3p_Market_Order(amount, side):
    
    pair = pair1[0] + pair2
    
    if side == 'buy':
        order_side = 'bid'
    if side == 'sell':
        order_side = 'ask'
    
    Order = Bl3p_Private_Client().addMarketOrder(pair, str(order_side), int(amount))

    print 'Message from Bl3p: ' + str(Order)
    log.write('\nMessage from Bl3p: ' + str(Order)) 
    
    return Order
    
def Bl3p_Check_Order(ref):
    
    pair = pair1[0] + pair2    
    Order = Bl3p_Private_Client().checkOrder(pair, ref)
    
    print 'Message from Bl3p: ' + str(Order)
    log.write('\nMessage from Bl3p: ' + str(Order)) 
    
    return Order

    
def Bl3p_Orderbook():
    
    pair = pair1[0] + pair2
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
    
    pair = pair1[0] + pair2    
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
    
def theRock_Limit_Order(amount, side, price, leverage):
    
    pair = pair1[0].lower() + pair2.lower()
    Order = theRock_Private_Client().PlaceOrder(pair, str(amount),
                                                side, str(price), float(leverage))
                                                
    print 'Message from theRock: ' + str(Order)
    log.write('\nMessage from theRock: ' + str(Order))
    
    return Order
    
def theRock_Market_Order(amount, side, leverage):
    
    if side == 'buy':
            price = theRock['entry_buy'] * 1+0.00005
    elif side == 'sell':
            price = theRock['entry_sell'] * 1-0.00005
    
    pair = pair1[0].lower() + pair2.lower()
    Order = theRock_Private_Client().PlaceOrder(pair, str(amount),
                                                side, str(price), float(leverage))
                                                
    print 'Message from theRock: ' + str(Order)
    log.write('\nMessage from theRock: ' + str(Order))
    
    return Order
    
def theRock_Check_Order(ref):
    
    pair = pair1[0].lower() + pair2.lower()
    Order = theRock_Private_Client().ListOrder(pair, ref)
    
    print 'Message from theRock: ' + str(Order)
    log.write('\nMessage from theRock: ' + str(Order))    
    
    return Order
    
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
    
    Order_ID = Order['ID']

    isFilled = theRock_Check_Order(Order_ID)['status']
    
    if  isFilled == 'executed':
        Filled = True
    else: Filled = False
    
    return Filled
    
def theRock_Cancel_Order(ref):
    
    pair = pair1[0].lower() + pair2.lower()
    Order = theRock_Private_Client().CancelOrder(pair, ref)
    
    print 'Message from theRock: ' + str(Order)
    log.write('\nMessage from theRock: ' + str(Order)) 
    
    if Order['status'] == 'deleted':
        Order_Cancelled = True

    return Order_Cancelled


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
#    
#def xBTCe_Balances():
#    return
#
#    


###############################################################################
###############################################################################
    
def Update_Balances(Exchange):
    
    # Updates the account balances
    
    name = Exchange['Name']    

    for attempt in range(1, Attempts):
        
        try:
            if Exchange['Name'] == 'Kraken':
                Balances.update({'Kraken': Kraken_Balances()})
            elif Exchange['Name'] == 'Bitstamp':
                Balances.update({'Bitstamp': Bitstamp_Balances()})
            elif Exchange['Name'] == 'Gdax':
                Balances.update({'Gdax': Gdax_Balances()})
            elif Exchange['Name'] == 'Bl3p':
                Balances.update({'Bl3p': Bl3p_Balances()})
            elif Exchange['Name'] == 'theRock':
                Balances.update({'theRock': theRock_Balances()})
        
        except:
            print 'Failed to get Balances for %s on attempt: %i' %(name, 
                                                                   attempt)
            log.write('\nFailed to get Balances for %s on attempt: %i' %(name, 
                                                                         attempt))
            time.sleep(3)
            continue
        
        else:
            return None
      
    else:                                                  
        print 'Failed to Update Balances for %s' %name
        log.write('\nFailed to Update Balances for %s' %name)
        
def Get_Fees(Exchange):
  
    name = Exchange['Name']    

    for attempt in range(1, Attempts):
        
        try:
            if name == 'Kraken':
                Exchange.update(Kraken_Fees())
            elif name == 'Bitstamp':
                Exchange.update(Bitstamp_Fees())
            elif name == 'Gdax':
                Exchange.update(Gdax_Fees())
            elif name == 'Bl3p':
                Exchange.update(Bl3p_Fees())
            elif name == 'theRock':
                Exchange.update(theRock_Fees())
        
        except:
            print 'Failed to get Fees for %s on attempt: %i' %(name, 
                                                               attempt)
            log.write('\nFailed to get Fees for %s on attempt: %i' %(name, 
                                                                     attempt))
            time.sleep(3)
            continue
        
        else:
            return None
      
    else:                      
        print 'Failed to get Fees for %s' %name
        log.write('\nFailed to get Fees for %s' %name)
        
def Get_Orderbook(Exchange):
  
    name = Exchange['Name']    

    for attempt in range(1,Attempts):
        
        try:
            if name == 'Kraken':
                Orderbook = Kraken_Orderbook()
            elif name == 'Bitstamp':
                Orderbook = Bitstamp_Orderbook()
            elif name == 'Gdax':
                Orderbook = Gdax_Orderbook()
            elif name == 'Bl3p':
                Orderbook = Bl3p_Orderbook()
            elif name == 'theRock':
                Orderbook = theRock_Orderbook()
        
        except:
            print 'Failed to get Orderbook for %s on attempt: %i' %(name, 
                                                                   attempt)
            log.write('\nFailed to get Orderbook for %s on attempt: %i' %(name, 
                                                                         attempt))
            time.sleep(3)
            continue
        
        else:
            return Orderbook
      
    else:                      
        print 'Failed to get Orderbook for %s' %name
        log.write('\nFailed to get Orderbook for %s' %name)
        return (((0, 0), (0, 0)), ((0, 0), (0, 0))) #return fake orderbook
        
    
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
    
    
def Liquidity_Check(exchange, amount, side, orderbook):
    
    # Finds the orderbook for an exchange and determines liquid prices
    
    name = exchange['Name']
    
    if amount <= 0:
        amount = 0.000000001
    
    Amount = amount*liquid_factor
    
    if side == 'buy':
        x = 0
    elif side == 'sell':
        x = 1
            
    if name == 'Kraken':
        Liquid_Price = Weighted_Price(Amount, orderbook[x])

    elif name == 'Bitstamp':
        Liquid_Price = Weighted_Price(Amount, orderbook[x])
        
    elif name == 'Gdax':
        Liquid_Price = Weighted_Price(Amount, orderbook[x])
        
    elif name == 'Bl3p':
        Liquid_Price = Weighted_Price(Amount, orderbook[x])
        
    elif name == 'theRock':
        Liquid_Price = Weighted_Price(Amount, orderbook[x])       
        
    return Liquid_Price
    

def Get_Prices(Exchange):
    
    name = Exchange['Name']
    
    # Gets prices based on the orderbook   

    Orderbook = Get_Orderbook(Exchange)
    Market_Ask = round(float(Orderbook[0][0][0]), 2)
    Market_Bid = round(float(Orderbook[1][0][0]), 2)    
    
    Exchange.update({'buy': Market_Ask, 'sell': Market_Bid})

    if Market_Ask == 0 or Market_Bid == 0:
        Exchange.update({'entry_buy': 0,
                         'entry_sell': 0,
                         'exit_buy': 0,
                         'exit_sell': 0})
        return None
                           

    EUR_Balance = Balances[name]['EUR']
    Buy_Amount = liquid_factor*(EUR_Balance / Exchange['buy'])
    Entry_Price_Buy = Liquidity_Check(Exchange, Buy_Amount, 'buy', Orderbook)
    Sell_Amount = liquid_factor*(EUR_Balance / Exchange['sell'])
    Entry_Price_Sell = Liquidity_Check(Exchange, Sell_Amount, 'sell', Orderbook)
    
    BTC_Balance = Balances[name]['BTC']
    Buy_Amount = liquid_factor * -BTC_Balance
    Exit_Price_Buy = Liquidity_Check(Exchange, Buy_Amount, 'buy', Orderbook)
    Sell_Amount = liquid_factor * BTC_Balance
    Exit_Price_Sell = Liquidity_Check(Exchange, Sell_Amount, 'sell', Orderbook)       
        
    Exchange.update({'entry_buy': round(Entry_Price_Buy, 2),
                           'entry_sell': round(Entry_Price_Sell, 2),
                           'exit_buy': round(Exit_Price_Buy, 2),
                           'exit_sell': round(Exit_Price_Sell, 2)})                                      
               
    return Exchange
     
    
def Get_Perm(exchanges):
    
    Permuatations = list(itertools.permutations(exchanges, 2))
    Permuatations = [i for i in Permuatations if i[1]['Shorting'] is True]

    return Permuatations
    

def Calc_Spread_Entry(Opportunity):
    
    Exchange1 = Opportunity[0]
    Exchange2 = Opportunity[1]
    
    Buy_Price = Exchange1['entry_buy']
    Sell_Price = Exchange2['entry_sell']
    
    if Buy_Price == 0 or Sell_Price == 0:
        return -1000.0 # return a ridiculous percentage that will never execute
   
    Spread = ((Sell_Price - Buy_Price) / Buy_Price)*100
    
    return Spread
    
def Calc_Spread_Exit(Arb):
    
    Exchange1 = Arb[0]
    Exchange2 = Arb[1]
    
    Buy_Price = Exchange1['exit_sell']
    Sell_Price = Exchange2['exit_buy']
    
    if Buy_Price == 0 or Sell_Price == 0:
        return 1000.0 # return a ridiculous percentage that will never execute
   
    Spread = ((Sell_Price - Buy_Price) / Buy_Price)*100
    
    return Spread
    
def Update(Arb):
    
    for Exchange in Exchanges:
        if Exchange['Name'] == Arb[0]['Name']:
            Arb[0].update(Exchange)
            
    for Exchange in Exchanges:
        if Exchange['Name'] == Arb[1]['Name']:
            Arb[1].update(Exchange)
            
    if Arb[0]['buy'] == 0 or Arb[1]['buy'] == 0:
        return None
                   
    Arb[2].update({'Spread': Calc_Spread_Entry((Arb[0], Arb[1]))})
    
    
def Find_Opportunities(perm):
       
    Exchange1 = perm[0]
    Exchange2 = perm[1]
    
    # sets the start values for logging of the spread histories
    Min_Spread_In = -0.00
    Max_Spread_In = 0.00
    
    Min_Spread_Out = -0.00
    Max_Spread_Out = 0.00
    
    if perm[0]['buy'] == 0 or perm[1]['buy'] == 0: 
        return None
    
    Spread_In = Calc_Spread_Entry(perm)
    Spread_Out = Calc_Spread_Exit(perm)
    
    Exchange1_Fees = Exchange1['buy_fee'] + Exchange1['sell_fee']
    Exchange2_Fees = Exchange2['buy_fee'] + Exchange2['sell_fee']
    Fees = (Exchange1_Fees + Exchange2_Fees)
    
#    Enter_Target = Target_Profit + Fees/2
    Enter_Target = Target_Profit
    
    Exit_Target = -100.0
    
    
#    Opportunities.append([Exchange1, Exchange2,
#                          Spread_In, Enter_Target, Exit_Target, 
#                          Min_Spread_In, Max_Spread_In,
#                          Spread_Out, Min_Spread_Out, Max_Spread_Out,
#                          Fees])
                          
    Opportunities.append({'Long_Position': Exchange1,
                          'Short_Position': Exchange2,
                          'Open_Spread': Spread_In,
                          'Open_Target': Enter_Target,
                          'Close_Target': Exit_Target, 
                          'Open_Min_Spread': Min_Spread_In, # not required
                          'Open_Max_Spread': Max_Spread_In,
                          'Close_Spread': Spread_Out,
                          'Close_Min_Spread': Min_Spread_Out,
                          'Close_Max_Spread': Max_Spread_Out, # not required
                          'Total_Fees': Fees})
                          
                          
def Update_Opportunities(Opportunity):    
    
    Min_Spread_In = Opportunity[5]
    Max_Spread_In = Opportunity[6]
    
    Min_Spread_Out = Opportunity[8]
    Max_Spread_Out = Opportunity[9]
    
    Exit_Target = Opportunity[4]
    
    if Opportunity[0]['buy'] == 0 or Opportunity[1]['buy'] == 0: 
        return None
        
    Spread_In = Calc_Spread_Entry(Opportunity)
    
    Spread_Out = Calc_Spread_Exit(Opportunity)
    
    if Spread_In < Min_Spread_In:
        Min_Spread_In = Spread_In
        
    if Spread_In > Max_Spread_In:
        Max_Spread_In = Spread_In
        
    if Exit_Target != -100.0:
        
        if Spread_Out < Min_Spread_Out:
            Min_Spread_Out = Spread_Out
            
        if Spread_In > Max_Spread_In:
            Max_Spread_In = Spread_In 
    
    Opportunity[2] = Spread_In
    Opportunity[5] = Min_Spread_In
    Opportunity[6] = Max_Spread_In
    Opportunity[7] = Spread_Out
    Opportunity[8] = Min_Spread_Out
    Opportunity[9] = Max_Spread_Out
    
   
           
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
                
            print side+' Order Filled at %s on attempt: %i' %(name, attempt)            
            log.write('\n'+side+' Order Filled at %s on attempt: %i'%(name,
                                                                      attempt))    
            
        except:
            
            print side+' order at %s waiting to fill on attempt: %i' %(name,
                                                                       attempt)
            log.write('\n'+side+' order at %s waiting to fill attempt %i'%(name,
                                                                           attempt))
                                                                           
            time.sleep(10)
            
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

            except:
                print 'Cancel Order Failed at %s on Attempt: %i' %(name, 
                                                                   attempt)
                log.write('\nCancel Order Failed at %s on Attempt: %i' %(name, 
                                                                         attempt))
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
            
        elif Exchange['Name'] == 'theRock':            
            theRock_Order_ID = str(uuid.uuid4().hex)
            Open_Order = {'ID': theRock_Order_ID}
            
        elif Exchange['Name'] == 'Bl3p':            
            Bl3p_Order_ID = str(uuid.uuid4().hex)
            Open_Order = {'ID': Bl3p_Order_ID} 
            
        return Open_Order
        
    elif Test_Mode is False:
    
        if Exchange['Name'] == 'Kraken':
            Kraken_Open_Order = Kraken_Limit_Order(amount, side, price, Leverage)
            Kraken_Order_ID =  str(Kraken_Open_Order['result']['txid'])
            Open_Order = {'ID': Kraken_Order_ID}
            
        elif Exchange['Name'] == 'Bitstamp':            
            Bitstamp_Open_Order = Bitstamp_Limit_Order(amount, side, price)
            Bitstamp_Order_ID = str(Bitstamp_Open_Order['id'])
            Open_Order = {'ID': Bitstamp_Order_ID}
        
        elif Exchange['Name'] == 'Gdax':            
            Gdax_Open_Order = Gdax_Limit_Order(amount, side, price)
            Gdax_Order_ID = str(Gdax_Open_Order['id'])
            Open_Order = {'ID': Gdax_Order_ID}
            
        elif Exchange['Name'] == 'theRock':            
            theRock_Open_Order = theRock_Limit_Order(amount, side, price, Leverage)
            theRock_Order_ID = str(theRock_Open_Order['id'])
            Open_Order = {'ID': theRock_Order_ID}
            
        elif Exchange['Name'] == 'Bl3p':            
            Bl3p_Open_Order = Bl3p_Limit_Order(amount*100000000, side, price*100000)
            Bl3p_Order_ID = str(Bl3p_Open_Order['data']['order_id'])
            Open_Order = {'ID': Bl3p_Order_ID}
                
        return Open_Order
        
def Place_Market_Order(Exchange, amount, side):    

        if Exchange['Name'] == 'Kraken':        
            Kraken_Open_Order = Kraken_Market_Order(amount, side)
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
        
            
        elif Exchange['Name'] == 'theRock':
            
            theRock_Open_Order = theRock_Market_Order(amount, side)
            theRock_Order_ID = str(theRock_Open_Order['id'])
            Open_Order = {'ID': theRock_Order_ID}
                
            
        elif Exchange['Name'] == 'Bl3p':            
            Bl3p_Open_Order = Bl3p_Market_Order(amount*100000000, side)
            Bl3p_Order_ID = str(Bl3p_Open_Order['data']['order_id'])
            Open_Order = {'ID': Bl3p_Order_ID}
                
        return Open_Order
        
def Execute_Limit_Order(Exchange, Amount, Side, Price, Leverage):
    
    # Tries to execute an order on an exchange, catches error if failed
    
    name = Exchange['Name']
    Open_Order = {'Name': name, 'Amount': Amount, 'Side': Side, 'Price': Price}
        
    for attempt in range(1, Attempts):
      
        try:
            Order = Place_Limit_Order(Exchange, Amount, Side, Price, Leverage)
            
            print Side + ' Order Placed at %s on attempt: %i' %(name, attempt)
            log.write('\n'+Side+' Order Placed at %s on attempt: %i'%(name, 
                                                                      attempt))            
        
        except:      
            print Side + ' Order failed at %s on attempt: %i' %(name, attempt)
            log.write('\n'+Side+' Order failed at %s on attempt: %i'%(name, 
                                                                      attempt))
            time.sleep(3)          
            continue
        
        else:
                                                  
            Open_Order.update(Order)
            return {'Order': Open_Order, 'Placed': True}
          
    else:
        
        print Side + ' Order failed at %s on all attempts' %name
        log.write('\n' + Side + ' Order failed at %s on all attempts' %name)      
     
        return {'Order': Open_Order, 'Placed': False} # returns blank order from top of function

def Execute_Market_Order(Exchange, Amount, Side):
    
    # Tries to execute an order on an exchange, catches error if failed
    
    name = Exchange['Name']
    Open_Order = {'Name': name, 'Amount': Amount, 'Side': Side}
        
    for attempt in range(1, Attempts):
      
        try:
            Order = Place_Market_Order(Exchange, Amount, Side)
            
            print Side + ' Order Placed at %s on attempt: %i' %(name, attempt)
            log.write('\n'+Side+' Order Placed at %s on attempt: %i'%(name, 
                                                                      attempt))            
        
        except:
            
            print Side + ' Order failed at %s on attempt: %i' %(name, attempt)
            log.write('\n'+Side+' Order failed at %s on attempt: %i'%(name, 
                                                                      attempt))
            time.sleep(3)
            
            continue
        
        else:
            Open_Order.update(Order)
            return {'Order': Open_Order, 'Placed': True}
          
    else:
        print Side + ' Order failed at %s on all attempts' %name
        log.write('\n' + Side + ' Order failed at %s on all attempts' %name)
     
        return {'Order': Open_Order, 'Placed': False} # returns blank order from top of function
                
    
def Print_Entry(Exchange1, Exchange2, Spread):
    
    print '\n---Entry Found---'
    
    print Exchange1['Name'] + ' / ' + \
          Exchange2['Name'] + ' ' + str(round(Spread, 2)) + '%'
          
    print 'Prices ' + str(Exchange1['entry_buy']) + 'EUR' + ' / ' + \
                      str(Exchange2['entry_sell']) + 'EUR'
                      
    print 'Balances ' + str(Exchange1['EUR']) + 'EUR' + ' / ' + \
                        str(Exchange2['EUR']) + 'EUR'
                        
    print '\nAttempting Trade...'
    
    winsound.PlaySound(r'cash.wav', winsound.SND_ASYNC)
    
    log.write('\n\n---Entry Found---\n')
    
    log.write(Exchange1['Name'] + ' / ' + \
                   Exchange2['Name'] + ' ' + str(round(Spread, 2)) + '%')
                   
    log.write('\nPrices ' + str(Exchange1['entry_buy']) + 'EUR' + ' / '+ \
                                 str(Exchange2['entry_sell']) + 'EUR')
                                 
    log.write('\nBalances ' + str(Exchange1['EUR']) + 'EUR' + ' / ' + \
                                   str(Exchange2['EUR']) + 'EUR')
                                        
    log.write('\n\nAttempting Trade...\n')
    

def Print_Exit(Exchange1, Exchange2, spread):
    
    print '\n---Exit Found---\n'
    
    print Exchange1['Name'] + ' / ' + \
          Exchange2['Name'] + ' ' + str(round(spread, 4)) + '%'
          
    print 'Prices ' + str(Exchange1['exit_sell']) + 'EUR' + ' / ' + \
                      str(Exchange2['exit_buy']) + 'EUR'
                      
    print 'Balances ' + str(Exchange1['BTC']) + 'BTC' + ' / ' + \
                        str(Exchange2['BTC']) + 'BTC'
          
    print '\nAttempting to Trade...'
    
    winsound.PlaySound(r'cash.wav', winsound.SND_ASYNC)
    
    log.write('\n\n---Exit Found---\n')
    
    log.write('\nPrices ' + str(Exchange1['exit_buy']) + 'EUR' + ' / '+ \
                                 str(Exchange2['exit_sell']) + 'EUR')
                                 
    log.write('\nBalances ' + str(round(Exchange1['BTC'], 2)) + 'BTC' + ' / ' + \
                              str(round(Exchange2['BTC'], 2)) + 'BTC')
    
    log.write('\n' + Exchange1['Name'] + ' / ' + \
                     Exchange2['Name'] + ' ' + str(round(spread, 4)) + '%')
                   
    log.write('\n\nAttempting to Trade...')
    
def Print_Profit(Closed_Arb):
    
    Exchange1 = Closed_Arb[0]
    Exchange2 = Closed_Arb[1]
    Profit = Closed_Arb[2]['Profit']
    Return = Closed_Arb[2]['Return']
    
    print '\n' + \
          Exchange1['Name']+' / '+ \
          Exchange2['Name']+ ' ' \
          '\nProfit: ' + str(Profit) + 'EUR' + \
          '\nReturn: ' + str(Return) + ' %' \
          '\nStart Time: ' + str(Arb[2]['Open_Time']) + \
          '\nEnd Time: '+ str(datetime.now()) + \
          '\nElapsed Time: '+ str(datetime.now() - Arb[2]['Open_Time'])
                         
    profit_file.write('\n\n' + \
                      Exchange1['Name'] + ' / ' + \
                      Exchange2['Name'] + ' ' + \
                      '\n\nProfit: ' + str(Profit) + 'EUR' + \
                      '\n\nStart Time: '+ str(Arb[2]['Open_Time']) + \
                      '\n\nEnd Time: '+ str(datetime.now()) + '\n\n' + \
                      'Elapsed Time:'+str(datetime.now()- Arb[2]['Open_Time']))
                      
def Print_Main_Info():
    
    print '%-22s' '%-15s' '%-15s' % \
          ('-------------------', '------------', '------------')
          
    print '%-22s' '%-15s' '%-15s' % \
          ('Exchange Balances', ' BTC Balance', ' EUR Balance')
          
    print '%-22s' '%-15s' '%-15s' % \
          ('-------------------', '------------', '------------')
          
    for Exchange in Exchanges:
        print '%-22s' '%-15s' '%-15s' % \
            (Exchange['Name'],
             round(Balances[Exchange['Name']]['BTC'], 8), 
             round(Balances[Exchange['Name']]['EUR'], 2))
            
    print '%-22s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' % \
          ('-------------------',
          '--------', '--------',
          '--------', '--------',
          '--------', '--------')
          
    print '%-22s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' % \
          ('Exchange Prices', '  Ask', '  Bid', 'Entry Ask', 'Entry Bid',  'Exit Ask', 'Exit Bid')
          
    print '%-22s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' % \
          ('-------------------',
          '--------', '--------',
          '--------', '--------',
          '--------', '--------')
          
    for Exchange in Exchanges:
        print '%-22s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' % \
           (Exchange['Name'],
            Exchange['buy'], Exchange['sell'],
            Exchange['entry_buy'], Exchange['entry_sell'],
            Exchange['exit_buy'], Exchange['exit_sell'])
            
                
    print '%-22s' '%-10s' '%-10s' '%-10s' '%-10s' '%-10s' '%s' % \
          ('-------------------', '------', '------', '------', '------', '------', '------')
                
    print '%-22s' '%-10s' '%-10s' '%-10s' '%-10s' '%-10s' '%s' % \
          ('Pair Spreads', 'Enter', 'Target', ' Max', ' Exit', 'Target',' Min')
          
    print '%-22s' '%-10s' '%-10s' '%-10s' '%-10s' '%-10s' '%s' % \
          ('-------------------', '------', '------', '------', '------', '------', '------')
        
    for Opportunity in Opportunities:
    
        print '%-22s' '%-10s' '%-10s' '%-10s' '%-10s' '%-10s' '%s' % \
              (str(Opportunity['Long_Position']['Name']) +' / ' + \
               str(Opportunity['Short_Position']['Name']), \
               str(round(Opportunity['Open_Spread'], 2)) + ' %' , \
               str(round(Opportunity['Open_Target'], 2)) + ' %', \
               str(round(Opportunity['Open_Max_Spread'], 2)) + ' %', \
               str(round(Opportunity['Close_Spread'], 2)) + ' %', \
               str(round(Opportunity['Close_Target'], 2)) + ' %', \
               str(round(Opportunity['Close_Min_Spread'], 2)) + ' %')
    
    print '\n'
    
    log.write('\n%-22s' '%-15s' '%-15s' % \
          ('-------------------', '------------', '------------'))
          
    log.write('\n%-22s' '%-15s' '%-15s' % \
          ('Exchange Balances', ' BTC Balance', ' EUR Balance'))
          
    log.write('\n%-22s' '%-15s' '%-15s' % \
          ('-------------------', '------------', '------------'))
          
    for Exchange in Exchanges:
        log.write('\n%-22s' '%-15s' '%-15s' % \
            (Exchange['Name'],
             round(Balances[Exchange['Name']]['BTC'], 8), 
             round(Balances[Exchange['Name']]['EUR'], 2)))
            
    log.write('\n%-22s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' % \
          ('-------------------',
          '--------', '--------',
          '--------', '--------',
          '--------', '--------'))
          
    log.write('\n%-22s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' % \
          ('Exchange Prices', '  Ask', '  Bid', 'Entry Ask', 'Entry Bid',  'Exit Ask', 'Exit Bid'))
          
    log.write('\n%-22s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' % \
          ('-------------------',
          '--------', '--------',
          '--------', '--------',
          '--------', '--------'))
          
    for Exchange in Exchanges:
        log.write('\n%-22s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' '%-12s' % \
           (Exchange['Name'],
            Exchange['buy'], Exchange['sell'],
            Exchange['entry_buy'], Exchange['entry_sell'],
            Exchange['exit_buy'], Exchange['exit_sell']))
            
                
    log.write('\n%-22s' '%-10s' '%-10s' '%-10s' '%-10s' '%-10s' '%s' % \
          ('-------------------', '------', '------', '------', '------', '------', '------'))
                
    log.write('\n%-22s' '%-10s' '%-10s' '%-10s' '%-10s' '%-10s' '%s' % \
          ('Pair Spreads', 'Enter', 'Target', ' Max', ' Exit', 'Target',' Min'))
          
    log.write('\n%-22s' '%-10s' '%-10s' '%-10s' '%-10s' '%-10s' '%s' % \
          ('-------------------', '------', '------', '------', '------', '------', '------'))
            
    for Opportunity in Opportunities:
          
        log.write('\n%-22s' '%-10s' '%-10s' '%-10s' '%-10s' '%-10s' '%s' % \
                  (str(Opportunity['Long_Position']['Name']) +' / ' + \
                   str(Opportunity['Short_Position']['Name']), \
                   str(round(Opportunity['Open_Spread'], 2)) + ' %' , \
                   str(round(Opportunity['Open_Target'], 2)) + ' %', \
                   str(round(Opportunity['Open_Max_Spread'], 2)) + ' %', \
                   str(round(Opportunity['Close_Spread'], 2)) + ' %', \
                   str(round(Opportunity['Close_Target'], 2)) + ' %', \
                   str(round(Opportunity['Close_Min_Spread'], 2)) + ' %'))

    log.write('\n\n')
                      
                      
def Trade_Logic(Exchange1, Exchange2, 
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
            
                Abort_Order = Execute_Market_Order(Exchange1,Buy_Amount,'sell')
                
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
                
                Abort_Order = Execute_Market_Order(Exchange2,Sell_Amount,'buy')
                                            
                
                print str(Exchange1['Name']) + ' Order ID: ' + \
                      str(Abort_Order['Order']['ID']) + ' Trade Reversed'
                      
                return ({'Placed': False},{'Placed': False})
             
                
        print 'Bought '+str(Buy_Amount)+pair1[0]+' at '+Exchange1['Name'] + \
              ' @ ' + str(Buy_Price)
        log.write('\nBought '+str(Buy_Amount)+pair1[0]+' at '+Exchange1['Name']+\
                  ' @ ' + str(Buy_Price))  
                
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
            
        print 'Sold '+str(Sell_Amount)+pair1[0]+' at '+Exchange2['Name'] + \
              ' @ ' + str(Sell_Price)
        log.write('\nSold '+str(Sell_Amount)+pair1[0]+' at '+Exchange2['Name']+\
                  ' @ ' + str(Sell_Price)) 
        
        return (Buy_Order, Sell_Order)
        

def Open(Opportunity):
    
    Exchange1 = Opportunity[0]
    Exchange2 = Opportunity[1]
    
    Name1 = Exchange1['Name']
    Name2 = Exchange2['Name']
    
    Balance1 = Balances[Name1]['EUR']
    Balance2 = Balances[Name2]['EUR']
    
    Spread = Opportunity[2]
    Entry_Target = Opportunity[3]
    Current_Exit_Spread = Opportunity[7]
    
    while True:
        
        # Check for sufficient spread
    
        if Spread <= Entry_Target:
            break
            
        for Arb in Current_Arbs:
            
            # Check if opportunity already exists            
            
            if Name1 == Arb[0]['Name'] and Name2 == Arb[1]['Name']:
                break
                        
        if Balance1 < Min_Bal or Balance2 < Min_Bal:
            
            # Check if there is sufficient balance
            
            print 'Insufficient Funds for '+ Exchange1['Name'] + ' / ' + \
                                               Exchange2['Name'] + ' '
                                              
            log.write('\nInsufficient Funds for '+Exchange1['Name'] + ' / '+\
                                                    Exchange2['Name'] + ' ')
            
            break                                  
        
        Total_Balance = Balance1 + Balance2
        
        # Use exchange with minimum balance to execute orders
        
        if Balance1 > Balance2:
            Trade_Amount_EUR = Balance2        
        else:
            Trade_Amount_EUR = Balance1
            
        Buy_Price = Exchange1['entry_buy']            
        Buy_Amount = Trade_Amount_EUR / Buy_Price

        Sell_Price = Exchange2['entry_sell']            
        Sell_Amount = Trade_Amount_EUR / Sell_Price
        
        # Log information
        
        Print_Entry(Exchange1, Exchange2, Spread)
                
        # Calc Fees and Execute the Trade Logic function, this is complicated
                
        Buy_Cost = Exchange1['buy_fee']/100 * Buy_Amount
        Sell_Cost = Exchange2['buy_fee']/100 * Sell_Amount
        
        Buy_Amount = Buy_Amount - Buy_Cost
        Sell_Amount = Sell_Amount + Sell_Cost
                
        Buy_Order, Sell_Order = Trade_Logic(Exchange1, Exchange2,
                                            Buy_Price, Sell_Price,
                                            Buy_Amount, Sell_Amount,
                                            'Open')
        
        # Check if the orders executed
        
        if Buy_Order['Placed'] is False or Sell_Order['Placed'] is False:
            break
        
        # Calculate the exit target and update this in the opportunity
        
        Fees = Opportunity[10] 
    
        Exit_Target = Spread - Target_Profit*2 - Fees
        
        Opportunity[4] = Exit_Target
       
        #######################################################################
        
        # If everything succeeds, update list of open arbs and update balances        
        
        print 'Trades Successfully Executed, in the Market!'
        log.write('\nTrades Successfully Executed, in the Market!')
            
        Buy_EUR = Balances[Name1]['EUR'] - (Buy_Amount+Buy_Cost)*Buy_Price 
        Buy_BTC = Balances[Name1]['BTC'] + Buy_Amount
        Sell_EUR = Balances[Name2]['EUR'] - (Sell_Amount-Sell_Cost)*Sell_Price 
        Sell_BTC = Balances[Name2]['BTC'] - Sell_Amount
                    
        Balances.update({Name1: {'BTC': Buy_BTC,'EUR': Buy_EUR}})
        Balances.update({Name2: {'BTC': Sell_BTC,'EUR': Sell_EUR}})                
                
        Exchange1.update(Balances[Exchange1['Name']])
        Exchange2.update(Balances[Exchange2['Name']])
        
        Current_Arbs.append([Exchange1, Exchange2,
                             {'buy_id': Buy_Order['Order'],
                              'sell_id': Sell_Order['Order'],
                              'Open_Spread': Spread,
                              'Long_Exposure': Trade_Amount_EUR,
                              'Short_Exposure': Trade_Amount_EUR,
                              'Total_Open_Balance': Total_Balance,
                              'Open_Time': datetime.now(),
                              'Exit_Target': Exit_Target}])

        Opportunity[5] = -0.0
        Opportunity[6] = 0.0
        Opportunity[8] = Current_Exit_Spread             
                       
        break   
            
        #######################################################################
            
       
def Close(Arb):    
    
    Exchange1 = Arb[0]
    Exchange2 = Arb[1]
    
    Name1 = Exchange1['Name']
    Name2 = Exchange2['Name']
    
    Open_Spread = Arb[2]['Open_Spread']
    Open_Time = Arb[2]['Open_Time']

    Spread = Calc_Spread_Exit(Arb)
    Open_Balance = Arb[2]['Total_Open_Balance']
    
    Long_Exposure = Arb[2]['Long_Exposure']
    Short_Exposure = Arb[2]['Short_Exposure']
    Total_Exposure = Long_Exposure + Short_Exposure
    
    Exit_Target = Arb[2]['Exit_Target']
    
    Orders = {'Opened': {'buy':Arb[2]['buy_id'], 'sell':Arb[2]['sell_id']}}
    
    while True:
        
        if Spread >= Exit_Target:
            
            print '\nLooking for exit...' 
            print Exchange1['Name'] + ' / ' + \
                  Exchange2['Name']+'. Spread is '+str(round(Spread,5))+'%'
            
            log.write('\n\nLooking for exit\n')
            log.write(Exchange1['Name'] + ' / ' + \
                      Exchange2['Name']+'. Spread is '+str(round(Spread,5))+'%')
                      
            Opportunity[5] = -0.0
            Opportunity[6] = 0.0
            
            break
               
        # Log information
            
        Print_Exit(Exchange2, Exchange1, Spread)
        
        Buy_Cost = Exchange2['sell_fee']/100 * -Exchange2[pair1[0]]
        Sell_Cost = Exchange1['sell_fee']/100 * Exchange1[pair1[0]]       
        
        Buy_Amount = -Exchange2[pair1[0]] + Buy_Cost
        Sell_Amount = Exchange1[pair1[0]] - Sell_Cost
        
        Buy_Price = Exchange2['exit_buy']
        Sell_Price = Exchange1['exit_sell']    
        
        Buy_Order, Sell_Order = Trade_Logic(Exchange2, Exchange1,
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
        
        Long_Profit = Sell_Amount*Sell_Price - Long_Exposure 
        Short_Profit = Short_Exposure - Buy_Amount*Buy_Price
        
        if Test_Mode:
            
            Buy_EUR = Balances[Name1]['EUR'] + Long_Exposure + Long_Profit
            Buy_BTC = Balances[Name1]['BTC'] - Sell_Amount - Sell_Cost
            Sell_EUR = Balances[Name2]['EUR'] + Short_Exposure + Short_Profit
            Sell_BTC = Balances[Name2]['BTC'] + Buy_Amount - Buy_Cost
            
            Balances.update({Name1: {'BTC': Buy_BTC, 'EUR': Buy_EUR}})
            Balances.update({Name2: {'BTC': Sell_BTC, 'EUR': Sell_EUR}})
                
        elif Test_Mode is False:
            
            for exchange in Arb:
                Update_Balances(exchange)               
                
        Balance1 = Balances[Name1]['EUR']
        Balance2 = Balances[Name2]['EUR']
              
        Close_Balance = Balance1 + Balance2
        
        Profit = Close_Balance - Open_Balance
        
        Total_Balances = {'Opening': Open_Balance, 'Closing': Close_Balance}
        
        Exchange1.update(Balances[Exchange1['Name']])
        Exchange2.update(Balances[Exchange2['Name']])
        
        Closed_Arb = [Exchange1, Exchange2,
                      {'Orders': Orders,
                       'Open Spread': Open_Spread,
                       'Close Spread': Spread,
                       'Balances': Total_Balances,
                       'All Balances': Balances,
                       'Long Profit': Long_Profit,
                       'Short Profit': Short_Profit,
                       'Long Expsoure': Long_Exposure,
                       'Short Expsoure': Short_Exposure,
                       'Total Exposure': Total_Exposure,
                       'Profit': Profit,
                       'Return': Profit / Total_Exposure * 100,
                       'Open_time': Open_Time,
                       'Close_time': datetime.now(),
                       'Elasped_time': datetime.now() - Open_Time}]
        
        Successful_Arbs.append(Closed_Arb)
        
        Print_Profit(Closed_Arb)
        
        Profits.append(Profit)
        
        for Arb in Current_Arbs:
            if  Name1 == Arb[0]['Name'] and Name2 == Arb[1]['Name']:
                Current_Arbs.remove(Arb)
                
        for opportunity in Opportunities:
            if  Name1 == opportunity['Long_Position']['Name'] and \
                Name2 == opportunity['Short_Position']['Name']:  
                    
                opportunity['Close_Target'] = -100.0 # resets parameter
                opportunity['Open_Min_Spread'] = -0.0 # resets parameter
                opportunity['Open_Max_Spread'] = 0.0 # resets parameter
                opportunity['Close_Min_Spread'] = -0.0 # resets parameter
                opportunity['Close_Max_Spread'] = 0.0 # resets parameter
                
        break
            
    ###########################################################################
            
###############################################################################

#def main():

log = open('Log_'+str(datetime.now())[0:10]+'.txt', "w")
profit_file = open('Profits_'+str(datetime.now())[0:10]+'.txt', "w")

Exchanges = [Kraken, Bitstamp, Gdax, Bl3p, TheRock]

if Test_Mode is False:    
    for Exchange in Exchanges:
        Update_Balances(Exchange)
    for Exchange in Exchanges:
        Exchange.update(Balances[Exchange['Name']])        
        
elif Test_Mode is True:
    for Exchange in Exchanges:
        Exchange.update(Balances[Exchange['Name']])

for Exchange in Exchanges:
    Get_Fees(Exchange)

for Exchange in Exchanges:
    Get_Prices(Exchange)
        
Opportunities = []

Scrapped_Opportunities = []

Permuatations = Get_Perm(Exchanges)

for perm in Permuatations:
    Find_Opportunities(perm)
    
Opportunities = sorted(Opportunities, key= lambda i: i['Open_Spread'], reverse=True)
        
Current_Arbs = []

Successful_Arbs = []

Profits = []

time.sleep(3)

while True:   
    
    log = open('Log_'+str(datetime.now())[0:10]+'.txt', "a")
    profit_file = open('Profits_'+str(datetime.now())[0:10]+'.txt', "a")
    
    Exchanges = [Kraken, Bitstamp, Gdax, Bl3p, TheRock]
    
    for Exchange in Exchanges:
        Get_Prices(Exchange)
            
    for Opportunity in Opportunities:
        Update_Opportunities(Opportunity)
    
    Opportunities = sorted(Opportunities, key= lambda i: i['Open_Spread'], reverse=True)
        
    Print_Main_Info()
            
    # Remove opportunities if in current open arbs
        
    for opportunity in Opportunities:
        for i in Current_Arbs:
            if i == opportunity:
                Opportunities.remove(opportunity)
   
    for Opportunity in Opportunities:
        Open(Opportunity)
            
    for Arb in Current_Arbs:
        Update(Arb)
            
    for Arb in Current_Arbs:
        Close(Arb)
        

        
    Total_Profit = round(sum(Profits), 2)
    
    print '\nTotal Profit Since Running: ' + str(Total_Profit) + ' Euro'
    log.write('\n\nTotal Profit Since Running: ' + str(Total_Profit) + ' Euro')
                
    time.sleep(1)
    
    print '\nScanning Markets',
    time.sleep(1); print'.',
    time.sleep(1); print'.',
    time.sleep(1); print'.'
    time.sleep(2)
    print '\n'+str(datetime.now())+'\n'
                                
    log.write('\n\nScanning Markets')      
    log.write('\n\n'+str(datetime.now())+'\n')
        
    log.close()
    profit_file.close()       
        
#if __name__ == "__main__":
#    main()   