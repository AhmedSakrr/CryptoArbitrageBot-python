import itertools

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
    
def Order(amount, side, price, leverage):
    
    pair = 'X'+pair1[1]+'Z'+pair2
    
    params = {'pair': pair,
              'type': side,
              'ordertype': 'limit',
              'price': price,
              'leverage': leverage, # 1 to 5 times
              'volume': amount}
    
    Order = Kraken_Private_Client('AddOrder', params)
    
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

def GDAX_Price():
    
    pair = pair1[0]+ '-' + pair2    
    public_client = GDAX.PublicClient(product_id = pair)
    price = public_client.getProductTicker(str(pair))    
    return (float(price['ask']), float(price['bid']))

def GDAX_Fees():    

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

def GDAX_Balances():
    
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
    
def make_GDAX():
    (GDAX_PriceA, GDAX_PriceB) = GDAX_Price()
    (GDAX_BTC, GDAX_EUR) = GDAX_Balances()
    (GDAX_feeA, GDAX_feeB) = GDAX_Fees()
    
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
    
def bl3p_Order(amount, side, price):
    
    pair = pair1[0] + pair2    
    Order = Bl3p_Private_Client().addOrder(pair, side, amount, price)    
    return Order

def make_BL3p():
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
        'Shorting': False}
        
    return XBTCE
    
#######################################################################

def Gatecoin_Private_Client():
    
    key = Keys.Gatecoin()    
    client = gatecoin.api.Client(key['key'], key['secret'])
    return client

def Gatecoin_Prices():
    
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
 
def make_Gatecoin():

    (Gatecoin_PriceA, Gatecoin_PriceB) = Gatecoin_Prices()
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
def Arbitrage(Exchanges):
    
    Exchange1 = Exchanges[0]
    Exchange2 = Exchanges[1]
    
    Profit = (Exchange2['sell'] - Exchange1['buy']) / Exchange1['buy'] * 100
    if Profit>0:
        print Exchange1['Name']+'_'+Exchange2['Name'], Profit

def Get_Perm(Exchanges):
    
    Permuatations = list(itertools.permutations(Exchanges, 2))
    Permuatations = [i for i in Permuatations if i[1]['Shorting'] is True]
#    for Permuatation in Permuatations:
#        print Permuatation[0]['Name'], Permuatation[1]['Name']
    return Permuatations

##############################################################################
def main():
    Kraken=make_Kraken()
    Bitstamp=make_Bitstamp()
    Gdax=make_GDAX()
    BTCe=make_BTCe()
    TheRock=make_theRock()
    Bl3p=make_BL3p()
    XBTCE=make_XBTCE()
    Gatecoin=make_Gatecoin()
    Exchanges = [Kraken, Bitstamp, Gdax, BTCe, TheRock, Bl3p, XBTCE, Gatecoin]
    for ex in Exchanges:
        print ex
    Permuatations=Get_Perm(Exchanges)
    for Permuatation in Permuatations:
        try: Arbitrage(Permuatation)
        except:
            print Permuatation +' Failed'
            continue
    

if __name__ == "__main__":
    main()   
    
    

