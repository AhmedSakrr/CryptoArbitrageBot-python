import itertools
import time
from datetime import datetime
import uuid

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

Test_Mode = True   #### Change to False to run for real!

Kraken = {'Name': 'Kraken', 'Shorting': True}
Bitstamp = {'Name': 'Bitstamp', 'Shorting': False}
Gdax = {'Name': 'Gdax', 'Shorting': False}
Bl3p = {'Name': 'Bl3p', 'Shorting': False}
TheRock = {'Name': 'theRock', 'Shorting': True}
Gatecoin = {'Name': 'Gatecoin', 'Shorting': False}

Min_Bal = 1.0 # Min Balance to execute on

Target_Profit = 0.1 # Percent (after fees and slippage)

'''
Slippage may need to increase for larger orders,
The greater this value is, the easier orders execute but less opportunies due 
to higher entry spread requied to maintain decent profit margin
'''

slippage = 0.1 # Percent
liquid_factor = 1.0 # multiplied by trade amount, determine if adequate liquidity
Exit_Spread = 0.0 # Percent to exit on after fees
Entry_Spread = Target_Profit + 4*slippage # 4 transactions in total, impacts profit

Attempts = 3 # re-tries for server
Attempts += 1

pair1 = 'BTC', 'XBT'
pair2 = 'EUR'

if Test_Mode is True:
    
    Balances = {'Kraken': {'EUR': 100, 'BTC': 0}, 
                'Bitstamp': {'EUR': 100, 'BTC': 0}, 
                'Gdax': {'EUR': 100, 'BTC': 0}, 
                'Bl3p': {'EUR': 100, 'BTC': 0}, 
                'theRock': {'EUR': 100, 'BTC': 0}, 
                'Gatecoin': {'EUR': 100, 'BTC': 0}}
                
else:    
    Balances = {} # update the later in the script with real values

###############################################################################


def Kraken_Private_Client(query, params={}):
    
    Key = Keys.Kraken()
    client = krakenex.API(Key['key'],Key['secret']).query_private(query,params)
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
    
    return {'buy_fee': float(fees['fees'][0][1]), 
            'sell_fee': float(fees['fees_maker'][0][1])}
         
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
    
    
def Kraken_Basic():
    
    Kraken_Basic = {'Name': 'Kraken'}
    Kraken_Basic.update(Kraken_Price())
    Kraken_Basic.update(Kraken_Fees())

    return Kraken_Basic
    
   
def Kraken_Orderbook():
    
    pair = 'X'+pair1[1]+'Z'+pair2    
    API = krakenex.API()    
    Orderbook = API.query_public('Depth', {'pair': pair})['result'][pair]
    
    Asks = Orderbook['asks']    
    Bids = Orderbook['bids']
    
    return (Asks, Bids)
    
    
def Kraken_Filled(Order):
    
    isFilled = Kraken_Check_Order(Order['ID'])['result'][Order['ID']]['status']
    
    if str(isFilled) == 'closed':
        Filled = True
    else: Filled = False
    
    return Filled
    
def Kraken_Cancel_Order(ref):
    
    params = {'txid': ref}
    
    Order = Kraken_Private_Client('CancelOrder', params)
    
    print Order
    
    if Order['result']['count'] == 1:
        Order_Cancelled = True
    
    return Order_Cancelled
    
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
    Order = Bitstamp_Private_Client().limit_order(str(amount), str(side),
                                                  str(price), pair[0], pair[1])  
    
    return Order
    
def Bitstamp_Check_Order(ref):
    
    Order = Bitstamp_Private_Client().order_status(ref)
    
    return Order
    
    
def Bitstamp_Basic():
    
    Bitstamp_Basic = {'Name': 'Bitstamp'}
    Bitstamp_Basic.update(Bitstamp_Price())
    Bitstamp_Basic.update(Bitstamp_Fees())

    return Bitstamp_Basic
    
    
def Bitstamp_Orderbook():
    
    pair = pair1[0].lower(), pair2.lower()    
    public_client = bitstamp.client.Public()    
    Orderbook = public_client.order_book(base = pair[0], quote = pair[1])
    
    Asks = Orderbook['asks']
    Bids = Orderbook['bids']
    
    return (Asks, Bids)
    
def Bitstamp_Filled(Order):
    
    isFilled = str(Bitstamp_Check_Order(Order['ID'])['status'])
    if  isFilled == 'Finished':
        Filled = True
    else: Filled = False
    
    return Filled
    
def Bitstamp_Cancel_Order(ref):
    
    Order = Bitstamp_Private_Client().cancel_order(ref)
    
    if Order is True:
        Order_Cancelled = True
    
    return Order_Cancelled

###############################################################################

def GDAX_Private_Client():
    
    key = Keys.GDAX()        
    client = GDAX.AuthenticatedClient(key['key'],key['secret'],key['passphrase'])
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
        
    client = GDAX.AuthenticatedClient(key['key'],key['secret'],key['passphrase'])
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
    
    
def Gdax_Basic():
    
    Gdax_Basic = {'Name': 'Gdax'}
    Gdax_Basic.update(Gdax_Price())
    Gdax_Basic.update(Gdax_Fees())
    
    return Gdax_Basic
    
    
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
    
def Gdax_Cancel_Order(ref):    
    
    Order = GDAX_Private_Client().cancelOrder(ref)
    
    print Order
    
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
#    BTCe = BTCe_Basic().update(BTCe_Balances())
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
    
    Order = Bl3p_Private_Client().addOrder(pair, str(order_side), 
                                           int(amount), int(price))
    
    return Order
    
def Bl3p_Check_Order(ref):
    
    pair = pair1[0] + pair2    
    Order = Bl3p_Private_Client().checkOrder(pair, ref)    
    return Order
    
def Bl3p_Basic():
    
    Bl3p_Basic = {'Name': 'Bl3p'}
    Bl3p_Basic.update(Bl3p_Price())
    Bl3p_Basic.update(Bl3p_Fees())
    
    return Bl3p_Basic

    
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
    
    isFilled = str(Bl3p_Check_Order(Order['ID'])['data']['status'])
    
    if  isFilled == 'closed':
        Filled = True
    else: Filled = False
    
    return Filled
        
def Bl3p_Cancel_Order(ref):
    
    pair = pair1[0] + pair2    
    Order = Bl3p_Private_Client().cancelOrder(pair, ref)
    
    print Order
    
    if Order['result'] == 'success':
        Order_Cancelled = True

    return Order_Cancelled

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
    Order = theRock_Private_Client().PlaceOrder(pair, str(amount),
                                                side, str(price))
    
    return Order
    
def theRock_Check_Order(ref):
    
    pair = pair1[0].lower() + pair2.lower()
    Order = theRock_Private_Client().ListOrder(pair, ref)    
    return Order
    
    
def theRock_Basic():
    
    theRock_Basic = {'Name': 'theRock'}
    theRock_Basic.update(theRock_Price())
    theRock_Basic.update(theRock_Fees())
    
    return theRock_Basic

    
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
    
def theRock_Cancel_Order(ref):
    
    pair = pair1[0].lower() + pair2.lower()
    Order = theRock_Private_Client().CancelOrder(pair, ref)
    
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
#    XBTCE = XBTCE_Basic().update(xBTCe_Balances())
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
       
    Order = Gatecoin_Private_Client().place_order(pair, str(amount), 
                                                        str(price), order_side)
    
    return Order
    
def Gatecoin_Check_Order(ref):
    
    Order = Gatecoin_Private_Client().get_order(ref)    
    return Order
    
def Gatecoin_Fees():
    
    buy_fee = 0.35
    sell_fee = 0.25
    
    return {'buy_fee': buy_fee, 'sell_fee': sell_fee}
    
    
def Gatecoin_Basic():
    
    Gatecoin_Basic = {'Name': 'Gatecoin'}
    Gatecoin_Basic.update(Gatecoin_Price())
    Gatecoin_Basic.update(Gatecoin_Fees())

    return Gatecoin_Basic
 
    
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
    
def Gatecoin_Cancel_Order(ref):
    
    Order = Gatecoin_Private_Client().cancel_order(ref)
    
    print Order
    
    if Order['responseStatus']['message'] == 'OK':
        Order_Cancelled = True
    
    return Order_Cancelled   
    
    
###############################################################################
###############################################################################

    
def Get_Perm(exchanges):
    
    Permuatations = list(itertools.permutations(exchanges, 2))
    Permuatations = [i for i in Permuatations if i[1]['Shorting'] is True]

    return Permuatations
    


def Calc_Spread(Opportunity):
    
    Exchange1 = Opportunity[0]
    Exchange2 = Opportunity[1]
    
    Buy_Price = Exchange1['buy']
    Sell_Price = Exchange2['sell']
    
    Buy_Fee = Exchange1['buy_fee']
    Sell_Fee = Exchange2['sell_fee']
    
    Sell = Sell_Price - (Sell_Price * (Sell_Fee / 100))
    Buy = Buy_Price + (Buy_Price * (Buy_Fee / 100))
    
    Spread = ((Sell - Buy) / Buy) * 100
    
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
            
            
def isOrderFilled(Exchange, Order):
    
    name = Exchange['Name']
    
    if Test_Mode:
        return True
        
    else:
        
        for i in range(1):
          for attempt in range(1,Attempts):
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
                    Filled = Bl3p_Filled(Order)
                    
                elif Exchange['Name'] == 'Gatecoin':
                    Filled = Gatecoin_Filled(Order)
                    
            except:
                print 'Order at %s failed to fill on attempt: %i' %(name, attempt)
                log.write('\nOrder at %s failed to fill on attempt: %i' %(name, attempt))
                time.sleep(3)
                continue
            
            else:
                return Filled
          
          else:
              print 'Order at %s failed to fill on all attempts' %name
              log.write('\nOrder at %s failed to fill on all attempts' %name)
              return False
    
    
def isliquid(exchange, amount, side):
    
    name = exchange['Name']
    
    amount *= liquid_factor
    
    if side == 'buy':
        x = 0
    elif side == 'sell':
        x = 1       

    for attempt in range(1, Attempts):
        
        try:
            
            if exchange['Name'] == 'Kraken':
                Liquid_Price = Weighted_Price(amount, Kraken_Orderbook()[x])
        
            elif exchange['Name'] == 'Bitstamp':
                Liquid_Price = Weighted_Price(amount, Bitstamp_Orderbook()[x])
                
            elif exchange['Name'] == 'Gdax':
                Liquid_Price = Weighted_Price(amount, Gdax_Orderbook()[x])
                
            elif exchange['Name'] == 'Bl3p':
                Liquid_Price = Weighted_Price(amount, Bl3p_Orderbook()[x])
                
            elif exchange['Name'] == 'theRock':
                Liquid_Price = Weighted_Price(amount, theRock_Orderbook()[x])
                
            elif exchange['Name'] == 'Gatecoin':
                Liquid_Price = Weighted_Price(Gatecoin, Kraken_Orderbook()[x])           
        
        except:
            print 'Failed to get Orderbook for %s on Attempt: %i' %(name, attempt)
            log.write('\nFailed to get Orderbook for %s on Attempt: %i' %(name, attempt))
            time.sleep(3)
            continue
        
        else:
            return Liquid_Price
      
    else:                                                  
        print 'Failed to get Orderbook for %s ' %name
        log.write('\nFailed to get Orderbook for %s ' %name)
        
        
        
def get_Basic_Info(exchange):
    
    name = exchange['Name']
    
    Blank = {'Name': exchange['Name'], 'buy': 1e9, 'sell': 1e-9, 
                                       'buy_fee': 0.25, 'sell_fee': 0.25}
    
    for attempt in range(1, Attempts):
        try:
            if exchange['Name'] == 'Kraken':
                Exchange_Basic = Kraken_Basic()
        
            elif exchange['Name'] == 'Bitstamp':
                Exchange_Basic = Bitstamp_Basic()
            
            elif exchange['Name'] == 'Gdax':
                Exchange_Basic = Gdax_Basic()
            
            elif exchange['Name'] == 'Bl3p':
                Exchange_Basic = Bl3p_Basic()
            
            elif exchange['Name'] == 'theRock':
                Exchange_Basic = theRock_Basic()
            
            elif exchange['Name'] == 'Gatecoin':
                Exchange_Basic = Gatecoin_Basic()           
        
        except:
            print 'Failed to get Basic Info for %s on Attempt: %i' %(name, attempt)
            log.write('\nFailed to Basic Info for %s on Attempt: %i' %(name, attempt))
            time.sleep(3)
            continue
        
        else:
            return Exchange_Basic
      
    else:                                                  
        print 'Failed to get Basic Info for %s ' %name
        log.write('\nFailed to get Basic Info for %s ' %name)
        return Blank
            

    
def Cancel_Order(exchange, ref):
    
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
                    
                elif exchange['Name'] == 'Gatecoin':
                    Cancelled = Gatecoin_Cancel_Order(ref)

            except:
                print 'Cancel Order Failed at %s on Attempt: %i' %(name, attempt)
                log.write('\nCancel Order Failed at %s on Attempt: %i' %(name, attempt))
                time.sleep(3)
                continue
        
            else:
                return Cancelled
      
        else:                                                  
            print 'Failed to Cancel Order at %s ' %(exchange['Name'])
            log.write('\nFailed to Cancel Order at %s ' %(exchange['Name']))
            return False
            
    
def Update_Balances(Exchange):
    
    name = Exchange['Name']

    for attempt in range(1,Attempts):
        
        try:
            if Exchange['Name'] == 'Kraken':
                Balances.update({'Kraken': Kraken_Balances()})    
            if Exchange['Name'] == 'Bitstamp':
                Balances.update({'Bitstamp': Bitstamp_Balances()})
            if Exchange['Name'] == 'Gdax':
                Balances.update({'Gdax': Gdax_Balances()})
            if Exchange['Name'] == 'Bl3p':
                Balances.update({'Bl3p': Bl3p_Balances()})
            if Exchange['Name'] == 'theRock':
                Balances.update({'theRock': theRock_Balances()})
            if Exchange['Name'] == 'Gatecoin':
                Balances.update({'Gatecoin': Gatecoin_Balances()})
        
        except:
            print 'Failed to get Balances for %s on attempt: %i' %(name, attempt)
            log.write('\nFailed to get Balances for %s on attempt: %i' %(name, attempt))
            time.sleep(3)
            continue
        
        else:
            break
      
    else:                                                  
        print 'Failed to Update Balances for %s' %name
        log.write('\nFailed to Update Balances for %s' %name)
        
    
def Place_Order(Exchange, amount, side, price):
    
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
           
            
        elif Exchange['Name'] == 'Gatecoin':            
            Gatecoin_Order_ID = str(uuid.uuid4().hex)
            Open_Order = {'ID': Gatecoin_Order_ID}
            
        return Open_Order
        
    elif Test_Mode is False:
    
        if Exchange['Name'] == 'Kraken':        
            Kraken_Open_Order = Kraken_Order(amount, side, price, 'none')
            Kraken_Order_ID =  str(Kraken_Open_Order['result']['txid'])
            Open_Order = {'ID': Kraken_Order_ID}
    
            
        elif Exchange['Name'] == 'Bitstamp':            
            Bitstamp_Open_Order = Bitstamp_Order(amount, side, price)
            Bitstamp_Order_ID = str(Bitstamp_Open_Order['id'])
            Open_Order = {'ID': Bitstamp_Order_ID}
               
        
        elif Exchange['Name'] == 'Gdax':            
            Gdax_Open_Order = Gdax_Order(amount, side, price)
            Gdax_Order_ID = str(Gdax_Open_Order['id'])
            Open_Order = {'ID': Gdax_Order_ID}
        
            
        elif Exchange['Name'] == 'theRock':            
            theRock_Open_Order = theRock_Order(amount, side, price)
            theRock_Order_ID = str(theRock_Open_Order['id'])
            Open_Order = {'ID': theRock_Order_ID}
                
            
        elif Exchange['Name'] == 'Bl3p':            
            Bl3p_Open_Order = Bl3p_Order(amount*100000000, side, price*100000)
            Bl3p_Order_ID = str(Bl3p_Open_Order['data']['order_id'])
            Open_Order = {'ID': Bl3p_Order_ID}
           
            
        elif Exchange['Name'] == 'Gatecoin':            
            Gatecoin_Open_Order = Gatecoin_Order(amount, side, price)
            Gatecoin_Order_ID = str(Gatecoin_Open_Order['clOrderId'])
            Open_Order = {'ID': Gatecoin_Order_ID}
                
        return Open_Order       
        

def Execute(Exchange, Amount, Side, Price):
    
    name = Exchange['Name']
    Open_Order = {'Name': name, 'Amount': Amount, 'Side': Side, 'Price': Price}
        
    for attempt in range(1, Attempts):
      
        try:
            Order = Place_Order(Exchange, Amount, Side, Price)
            Open_Order.update(Order)
            print Side + ' Order Placed at %s on attempt: %i' %(name, attempt)
            log.write('\n'+Side+' Order Placed at %s on attempt: %i' %(name, attempt))            
        
        except:
            print Side + ' Order failed at %s on attempt: %i' %(name, attempt)
            log.write('\n'+Side+' Order failed at %s on attempt: %i' %(name, attempt))
            time.sleep(3)
            continue
        
        else:
            return (Open_Order, True)
          
    else:
        print Side + ' Order failed at %s on all attempts' %name
        log.write('\n' + Side + ' Order failed at %s on all attempts' %name)
     
        return (Open_Order, False) # returns blank order from top of function

    
def Execute_Order(Exchange, Trade_Amount, Order_Price, side, slippage):    
    
    ''' Get Order Book for exchanges to determine liquidity'''
    
    if side == 'buy':

        Buy_Price = Order_Price*(1 + slippage/100) # Account for slippage
        Liquid_Price = isliquid(Exchange, Trade_Amount, side)
        
        ''' Excecute Order if enough liquidity '''
        if Liquid_Price < Buy_Price:
            Order, Placed = Execute(Exchange, Trade_Amount, side, Order_Price)
                
        else:
            print 'Not enough liquidity for Buy Order at %s' %Exchange['Name']
            print 'Liquid Price: %s, Order Price: %s' %(Liquid_Price, Buy_Price)
            Order = False
            Placed = False        
        
    elif side == 'sell':
    
        Sell_Price = Order_Price*(1 - slippage/100) # Account for slippage
        Liquid_Price = isliquid(Exchange, Trade_Amount, side)
        
        ''' Excecute Order if enough liquidity '''
        if Liquid_Price > Sell_Price:
            Order, Placed = Execute(Exchange, Trade_Amount, side, Order_Price)            
                
        else:
            print 'Not enough liquidity for Sell Order at %s' %Exchange['Name']
            print 'Liquid Price: %s, Order Price: %s' %(Liquid_Price, Sell_Price)
            Order = False
            Placed = False
            
    return {'Order': Order, 'Placed': Placed}
    
    
def Check_Order_Filled(Exchange, Order, Trade_Amount, side):
    
    if Test_Mode:
        return True
    
    name = Exchange['Name']
    side = side.title()

    for attempt in range(1, Attempts):
      
        try:            
            Order_Filled = isOrderFilled(Exchange['Name'], Order['ID'])            
            print side+' Order Filled at %s on attempt: %i' %(name, attempt)            
            log.write('\n'+side+' Order Filled at %s on attempt: %i' %(name,attempt))
            
            if side == 'buy':
                
                print 'Bought '+str(Trade_Amount)+pair1[0]+' at '+name                
                log.write('\nBought '+str(Trade_Amount)+pair1[0]+' at '+name)                    
            
            elif side  == 'sell':
                print 'Sold '+str(Trade_Amount)+pair1[0]+' at '+name    
                log.write('\nSold '+str(Trade_Amount)+pair1[0]+' at '+name)             
            
        except:
            print side+' order at %s waiting to fill on attempt: %i' %(name, attempt)
            log.write('\n'+side+' order at %s waiting to fill attempt %i' %(name, attempt))
            continue
        
        else:
            return Order_Filled

          
    else:                                                  
        print side + ' order at %s failed to fill...' %Exchange['Name']
        log.write('\n'+side+' order at %s failed to fill...' %Exchange['Name'])
        return False    
    
    
def Print_Entry(Exchange1, Exchange2, Spread):
    
    print '\n---Entry Found---'
    
    print Exchange1['Name'] + ' / ' + \
          Exchange2['Name'] + ' ' + str(round(Spread, 2)) + '%'
          
    print 'Prices ' + str(Exchange1['buy']) + 'EUR' + ' / ' + \
                      str(Exchange2['sell']) + 'EUR'
                      
    print 'Balances ' + str(Exchange1['EUR']) + 'EUR' + ' / ' + \
                        str(Exchange2['EUR']) + 'EUR'
                        
    print '\nAttempting Trade...'
    
    log.write('\n\n---Entry Found---\n')
    
    log.write(Exchange1['Name'] + ' / ' + \
                   Exchange2['Name'] + ' ' + str(round(Spread, 2)) + '%')
                   
    log.write('\nPrices ' + str(Exchange1['buy']) + 'EUR' + ' / '+ \
                                 str(Exchange2['sell']) + 'EUR')
                                 
    log.write('\nBalances ' + str(Exchange1['EUR']) + 'EUR' + ' / ' + \
                                   str(Exchange2['EUR']) + 'EUR')
                                        
    log.write('\n\nAttempting Trade...\n')
    

def Print_Exit(Exchange1, Exchange2, spread):
    
    print '\n---Exit Found---\n'
    
    print Exchange1['Name'] + ' / ' + \
          Exchange2['Name'] + ' ' + str(round(spread, 4))
          
    print '\nAttempting to Trade...'
    
    log.write('\n\n---Exit Found---\n')
    
    log.write(Exchange1['Name'] + ' / ' + \
                   Exchange2['Name'] + ' ' + str(round(spread, 4)))
                   
    log.write('\n\nAttempting to Trade...')
    
def Print_Profit(Arb, Profit):
    
    Exchange1 = Arb[0]
    Exchange2 = Arb[1]
    
    print Exchange1['Name']+' / '+ \
          Exchange2['Name']+ ' ' \
          '\nProfit = ' + str(Profit) + 'EUR' + \
          '\nStart Time: ' + str(Arb[2]['open_time']) + \
          '\nEnd Time: '+ str(datetime.now()) + \
          '\nElapsed Time: '+ str(datetime.now() - Arb[2]['open_time'])
                         
    profit_file.write(Exchange1['Name'] + ' / ' + \
                      Exchange2['Name'] + ' ' + \
                      '\n\nProfit = ' + str(Profit) + 'EUR' + \
                      '\n\nStart Time: '+ str(Arb[2]['open_time']) + \
                      '\n\nEnd Time: '+ str(datetime.now()) + '\n\n' + \
                      'Elapsed Time:'+str(datetime.now() - Arb[2]['open_time']))
                      
                      
def Trade_Logic(Exchange1,Exchange2, 
                Buy_Price,Sell_Price, 
                Buy_Amount,Sell_Amount,
                Type):
    
    if Type == 'Close':
        Exchange1, Exchange2 = Exchange2, Exchange1
        
    while True:   
    
        Buy_Order = Execute_Order(Exchange1, Buy_Amount,
                                  Buy_Price, 'buy', slippage)
                 
        if Buy_Order['Placed'] is False:
            return (False, False) # doesn't matter, nothing exceuted yet

        
        Sell_Order = Execute_Order(Exchange2, Sell_Amount, 
                                   Sell_Price, 'sell', slippage)
                                   
        
        if Sell_Order['Placed'] is False:
            
            Filled = Check_Order_Filled(Exchange1,Buy_Order['Order'],
                                        Buy_Amount, 'buy')
        
            if Filled is False:
                
                Cancel_Order(Exchange1, Buy_Order['Order']['ID'])
                
                print str(Exchange1['Name']) + ' Buy Order ID: '+ \
                      str(Buy_Order['Order']['ID']) + ' Cancelled'
                
                # Reverse the sell order if buy didn't fill,
                # may need to look at market order for this
                
                Filled = Check_Order_Filled(Exchange2, Sell_Order['Order'], 
                                    Sell_Amount, 'sell')
                                    
                return (False, False)
                
            elif Filled is True:               
            
                Abort_Price = get_Basic_Info(Exchange1)['sell'] 
                
                Abort_Order = Execute_Order(Exchange1,Buy_Amount,
                                            Abort_Price, 'sell', 0)
                
                print str(Exchange1['Name']) + ' Order ID: '+ \
                      str(Abort_Order['Order']['ID']) + ' Trade Reversed'
                      
                return (False, False)
                
              
        # If come this far, both Orders are now placed!       
            
        Filled = Check_Order_Filled(Exchange1, Buy_Order['Order'],
                                    Buy_Amount, 'buy')
        
        if Filled is False:

            Cancel_Order(Exchange1, Buy_Order['Order']['ID'])
            
            print str(Exchange1['Name'])+' Buy Order ID: '+ \
                  str(Buy_Order['Order']['ID'])+' Cancelled'
                  
                  
            Filled = Check_Order_Filled(Exchange2, Sell_Order['Order'], 
                                    Sell_Amount, 'sell') 
            
            if Filled is False:
                
                Cancel_Order(Exchange2, Sell_Order['Order']['ID'])
                
                print str(Exchange2['Name']) + ' Sell Order ID: '+ \
                str(Sell_Order['Order']['ID']) + ' Cancelled'
                
                return (False, False)
                
            elif Filled is True:
                
                # Reversed the sell order if buy didn't fill,
                # may need to look at market order for this
                
                Abort_Price = get_Basic_Info(Exchange2)['buy'] 
                Abort_Order = Execute_Order(Exchange2, Sell_Amount, 
                                            Abort_Price, 'buy', 0)
                
                print str(Exchange1['Name']) + ' Order ID: ' + \
                      str(Abort_Order['Order']['ID']) + ' Trade Reversed'
                      
                return (False, False)
        
        # Buy Order has now filled, check if sell order has filled.
            
        Filled = Check_Order_Filled(Exchange2, Sell_Order['Order'], 
                                    Sell_Amount, 'sell') 
                               
        if Filled is False:
            
            # Cancel sell order and reverse buy order
            
            Cancel_Order(Exchange2, Sell_Order['Order']['ID'])
            
            Abort_Price = get_Basic_Info(Exchange1)['sell']                            
            Abort_Order = Execute_Order(Exchange1, Buy_Amount, 
                                        Abort_Price, 'sell', 0)
            
            print str(Exchange1['Name']) + ' Order ID: '+ \
                  str(Abort_Order['Order']['ID']) + ' Trade Reversed'
                  
            return (False, False)
            
        # Both Orders have now been executed and filled!!
        
        return (Buy_Order, Sell_Order)
        

def Open(Opportunity):
    
    Exchange1 = Opportunity[0]
    Exchange2 = Opportunity[1]
    
    Name1 = Exchange1['Name']
    Name2 = Exchange2['Name']
    
    Balance1 = Balances[Name1]['EUR']
    Balance2 = Balances[Name2]['EUR']    
    
    Spread = Opportunity[2]
    
    while True:
    
        if Spread < Entry_Spread:
            break
            
        for Arb in Current_Arbs:
            
            if Name1 == Arb[0]['Name'] and Name2 == Arb[1]['Name']:
                break
                        
        if Balance1 < Min_Bal or Balance2 < Min_Bal:
            
            print 'Insufficient Funds for ' + Exchange1['Name'] + ' / ' + \
                                              Exchange2['Name'] + ' '
                                              
            log.write('\nInsufficient Funds for ' + Exchange1['Name'] + ' / '+ \
                                                    Exchange2['Name'] + ' ')
            
            break                                  
        
        Total_Balance = Balance1 + Balance2
        
        if Balance1 > Balance2:
            Trade_Amount_EUR = Balance2        
        else:
            Trade_Amount_EUR = Balance1
            
        Buy_Price = Exchange1['buy']*(1 + slippage/100)
        Sell_Price = Exchange2['sell']*(1 - slippage/100)
        Buy_Amount = Trade_Amount_EUR / Buy_Price
        Sell_Amount = Trade_Amount_EUR / Sell_Price
        
        Print_Entry(Exchange1, Exchange2, Spread)
                
        # Executes the Trade Logic function, this is complicated
        Buy_Order, Sell_Order = Trade_Logic(Exchange1, Exchange2, 
                                            Buy_Price, Sell_Price, 
                                            Buy_Amount, Sell_Amount,
                                            Type = 'Open')
                                            
        if Buy_Order or Sell_Order is False:
            break
       
        #######################################################################
        
        # If everything succeeds execute this code of block!!
        
        print 'Trades Successfully Executed, in the Market!'
        log.write('Trades Successfully Executed, in the Market!')
        
        Current_Arbs.append([Exchange1, Exchange2,
                             {'buy_id': Buy_Order['Order'],
                              'sell_id': Sell_Order['Order'],
                              'Spread': Spread,
                              'Total_Open_Balance':Total_Balance,
                              'open_time': datetime.now()}])                                
        
        if Test_Mode:
            
            Buy_EUR = Balances[Exchange1['Name']]['EUR']-Buy_Price*Buy_Amount
            Buy_BTC = Balances[Exchange1['Name']]['BTC']+Buy_Amount
            Sell_EUR = Balances[Exchange2['Name']]['EUR']-Sell_Price*Sell_Amount
            Sell_BTC = Balances[Exchange2['Name']]['BTC']-Sell_Amount
            
            Balances[Exchange1['Name']].update({'EUR': Buy_EUR})
            Balances[Exchange1['Name']].update({'BTC': Buy_BTC})
            Balances[Exchange2['Name']].update({'EUR': Sell_EUR})
            Balances[Exchange2['Name']].update({'BTC': Sell_BTC})
            
        elif Test_Mode is False:
            
            for exchange in Opportunity:
                Update(exchange)
            
            for exchange in Opportunity:
                Update_Balances(exchange)    
    
            
        #######################################################################
            
def Update(Arb):     
    
    Arb[0].update(get_Basic_Info(Arb[0]))
    Arb[1].update(get_Basic_Info(Arb[1]))                      
    Arb[2].update({'Spread': Calc_Spread((Arb[0], Arb[1]))})
       
       
def Close(Arb):    
    
    Exchange1 = Arb[0]
    Exchange2 = Arb[1]
    
    Name1 = Exchange1['Name']
    Name2 = Exchange2['Name']
    
    Balance1 = Balances[Name1]['EUR']
    Balance2 = Balances[Name2]['EUR']
    
    Open_Time = Arb[2]['open_time']

    spread = Arb[2]['Spread']
    Open_Balance = Arb[2]['Total_Open_Balance']
    
    while True:
        
        if spread > Exit_Spread:
            
            print '\nLooking for exit...' 
            print Exchange1['Name'] + ' / ' + \
                  Exchange2['Name']+'. Spread is '+str(round(spread,5))+'%'
            
            log.write('\n\nLooking for exit\n')
            log.write(Exchange1['Name'] + ' / ' + \
                      Exchange2['Name']+'. Spread is '+str(round(spread,5))+'%')
            
            break
          
            
        Print_Exit(Exchange1, Exchange2, spread)
        
        Sell_Amount = Exchange1[pair1[0]]
        Buy_Amount = Exchange2[pair1[0]]
        Sell_Price = Exchange1['sell']*(1 - slippage/100)
        Buy_Price = Exchange2['buy']*(1 + slippage/100)
        
        # Executes the Trade Logic function, this is complicated
        Buy_Order, Sell_Order = Trade_Logic(Exchange1, Exchange2, 
                                            Buy_Price, Sell_Price, 
                                            Buy_Amount, Sell_Amount,
                                            Type = 'Close')
                                            
        if Buy_Order or Sell_Order is False:
            break
        
    ###########################################################################
    
        print 'Trades Successfully Closed!'
        
        if Test_Mode:
            
            Buy_EUR = Balances[Exchange1['Name']]['EUR'] + Sell_Amount*Sell_Price
            Buy_BTC = Balances[Exchange1['Name']]['BTC'] - Sell_Amount
            Sell_EUR = Balances[Exchange2['Name']]['EUR'] + Buy_Amount*Buy_Price
            Sell_BTC = Balances[Exchange2['Name']]['BTC'] + Buy_Amount
            
            Balances[Exchange1['Name']].update({'EUR': Buy_EUR})
            Balances[Exchange1['Name']].update({'BTC': Buy_BTC})
            Balances[Exchange2['Name']].update({'EUR': Sell_EUR})
            Balances[Exchange2['Name']].update({'BTC': Sell_BTC})       
                
        elif Test_Mode is False:
            
            for exchange in Arb:
                Update_Balances(exchange)   
              
        Close_Balance = Balance1 + Balance2
        Profit = Close_Balance - Open_Balance
        
        Closed_Arb = [Exchange1,Exchange2,{'buy_id': Buy_Order,'sell_id': Sell_Order,
                                           'Total_Open_Balance': Open_Balance, 
                                           'Total_Close_Balance': Close_Balance,
                                           'Total_Profit': Profit,
                                           'close_time': datetime.now(),
                                           'elasped_time': datetime.now()-Open_Time}]
        
        Successful_Arbs.append(Closed_Arb)
        
        Print_Profit(Arb, Profit)       
        
        for Arb in Current_Arbs:
            if  Name1 == Arb[0]['Name'] and Name2 == Arb[1]['Name']:
                Current_Arbs.remove(Arb)
            
    ###########################################################################
            
###############################################################################

#def main():

log = open('Log_'+str(datetime.now())[0:10]+'.txt', "w")
profit_file = open('Profits_'+str(datetime.now())[0:10]+'.txt', "w")

Exchanges = [Kraken, Bitstamp, Gdax, Bl3p, TheRock, Gatecoin]

for Exchange in Exchanges:
    Exchange.update(get_Basic_Info(Exchange))

if Test_Mode is False:    
    for Exchange in Exchanges:
        Exchange.update(Update_Balances(Exchange))
        
elif Test_Mode is True:
    for Exchange in Exchanges:
        Exchange.update(Balances[Exchange['Name']])
        
Current_Arbs = []

Successful_Arbs = []

while True:
    
    log = open('Log_'+str(datetime.now())[0:10]+'.txt', "a")
    profit_file = open('Profits_'+str(datetime.now())[0:10]+'.txt', "a")
    
    Exchanges = [Kraken, Bitstamp, Gdax, Bl3p, TheRock, Gatecoin]
    
    for Exchange in Exchanges:
        Exchange.update(get_Basic_Info(Exchange))   
    
    for Exchange in Exchanges:
        if Exchange['buy'] > 1e8 or Exchange['sell'] < 1e-8:
            Exchanges.remove(Exchange)
            
    Permuatations = Get_Perm(Exchanges)
    
    Opportunities = []
        
    for perm in Permuatations:
        Find_Opportunities(perm)
            
    for i in Opportunities:
        print str(i[0]['Name']) +' / '+ \
              str(i[1]['Name']) + '  '+ str(round(i[2], 2)) + ' %'
        log.write('\n'+str(i[0]['Name']) +' / '+ \
                       str(i[1]['Name']) + '  '+ str(round(i[2], 2)) + ' %')
    
    for Opportunity in Opportunities:
        Open(Opportunity)
            
    for Arb in Current_Arbs:
        Update(Arb)                
            
    for Arb in Current_Arbs:
        Close(Arb)
                
    time.sleep(11)
    
    print '\nScanning Markets',
    time.sleep(1); print'.',
    time.sleep(1); print'.',
    time.sleep(1); print'.'
    time.sleep(1)
    print '\n'+str(datetime.now())+'\n'
                                
    log.write('\n\nScanning Markets')      
    log.write('\n\n'+str(datetime.now())+'\n')
        
    log.close()
    profit_file.close()       
        
#if __name__ == "__main__":
#    main()   