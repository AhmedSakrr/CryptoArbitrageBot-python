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

pair1 = 'BTC', 'XBT'
pair2 = 'EUR'

def Kraken_Private_Client():
    
    Key = Keys.Kraken()

    Private_Client = krakenex.API(Key['user'],Key['key'], Key['secret']).query_private()
    
    return Private_Client


def theRock_Private_Client():
    
    Key = Keys.theRock()
    
    Private_Client = theRock.PyRock.API(Key['key'], Key['secret'])
    
    return Private_Client

def Kraken_Price(): 
    
    pair = 'X'+pair1[1]+'Z'+pair2
    
    API = krakenex.API()
    price = API.query_public('Ticker',
                  {'pair': pair})['result'][pair]
                  
    return (float(price['a'][0]), float(price['b'][0]))
    
(Kraken_PriceA, Kraken_PriceB) = Kraken_Price()
    
def Kraken_Fees():
    pair = 'X'+pair1[1]+'Z'+pair2
    API = krakenex.API()
    fees = API.query_public('AssetPairs', {'info': 'fees'})['result'][pair]
    
    return (float(fees['fees'][0][1]), float(fees['fees_maker'][0][1]))
            
(Kraken_FeeA, Kraken_FeeB) = Kraken_Fees()
          
def Kraken_Balances():
    
    key = Keys.Kraken()
    
    api = krakenex.API(key=key['key'], secret=key['secret'])
    balance = api.query_private('Balance')['result']
    
    btc = round(float(balance['XXBT']),8)
    eur = round(float(balance['ZEUR']),2)
    
    return (btc, eur)
    
Kraken_BTC, Kraken_EUR = Kraken_Balances()

Kraken = {'Name': 'Kraken', 'buy': Kraken_PriceA, 'sell': Kraken_PriceB,
          'buy_fee': Kraken_FeeA, 'sell_fee': Kraken_FeeB,
          'BTC': Kraken_BTC, 'EUR': Kraken_EUR,
          'Shorting': True}

print Kraken
    
def Bitstamp_Price():
    
    pair = pair1[0].lower(), pair2.lower()
    
    public_client = bitstamp.client.Public()
    price = public_client.ticker(pair[0], pair[1])
    
    return (float(price['ask']), float(price['bid']))
    
(Bitstamp_PriceA, Bitstamp_PriceB) = Bitstamp_Price()
    
def Bitstamp_Balance_Fees():
    
    pair = pair1[0].lower(), pair2.lower()
    
    key = Keys.Bitstamp()   
    
    client = bitstamp.client.Trading(key['user'], key['key'], key['secret'])
    
    balance = client.account_balance(pair[0], pair[1])
    
    fee = float(balance['fee'])
    BTC =  float(balance['btc_balance'])
    EUR =  float(balance['eur_balance'])
    
    return fee, BTC, EUR
    
Bitstamp_Fee, Bitstamp_BTC, Bitstamp_EUR = Bitstamp_Balance_Fees()


Bitstamp = {'Name': 'Bitstamp',
            'buy': Bitstamp_PriceA, 'sell': Bitstamp_PriceB,
            'buy_fee': Bitstamp_Fee, 'sell_fee': Bitstamp_Fee,
            'BTC': Bitstamp_BTC, 'EUR': Bitstamp_EUR,
            'Shorting': False} # Coming soon

print Bitstamp


def GDAX_Price():
    
    pair = pair1[0]+ '-' + pair2
    
    public_client = GDAX.PublicClient(product_id = pair)
    price = public_client.getProductTicker(str(pair))
    
    return (float(price['ask']), float(price['bid']))

(GDAX_PriceA, GDAX_PriceB) = GDAX_Price()

def GDAX_Fees():
    
    key = Keys.GDAX()
        
    client = GDAX.AuthenticatedClient(key['key'], key['secret'], key['passphrase'])
    fills = client.getFills()[0] # get latest filled order
        
    buy = []
    
    for fill in fills:     
    
            if fill['side'] == 'buy':
                buy.append(fill)
                buy_fee_eur = float(buy[0]['fee'])
                buy_price = float(buy[0]['price'])
                buy_size = float(buy[0]['size'])
                buy_fee = (buy_fee_eur / (buy_size*buy_price)) * 100
                
    sell_fee = 0 # fee for market makers is zero

    
    return buy_fee, sell_fee
    
GDAX_feeA, GDAX_feeB = GDAX_Fees()

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
            
    return btc, eur
    
GDAX_BTC, GDAX_EUR = GDAX_Balances()

Gdax = {'Name': 'GDAX',
        'buy': GDAX_PriceA, 'sell': GDAX_PriceB,
        'buy_fee': GDAX_feeA, 'sell_fee': GDAX_feeB,
        'BTC': GDAX_BTC, 'EUR': GDAX_EUR,
        'Shorting': True}
        
print Gdax

def BTCe_Price():
    
    pair = pair1[0].lower()+'_'+pair2.lower()
    
    api = btce.api.PublicAPIv3()
    price = api.call('ticker', pairs = pair)[pair]
    
    return (float(price['buy']), float(price['sell']))
    
(BTCe_PriceA, BTCe_PriceB) = BTCe_Price() 
    
def BTCe_Fees():    
    
    pair = pair1[0].lower()+'_'+pair2.lower()
    
    api = btce.api.PublicAPIv3()
    fee = api.call('info')['pairs'][pair]['fee']
    
    return float(fee)
    
BTCe_Fee = BTCe_Fees()
    
def BTCe_Balances():

    key = Keys.BTCe()    
    
    api = btce.api.TradeAPIv1(key)
    balances = api.call('getInfo')['funds']   

    btc = round(float(balances['btc']),8)
    eur = round(float(balances['eur']),2)
    
    return (btc, eur)
    
BTCe_BTC, BTCe_EUR = BTCe_Balances()   

BTCe = {'Name': 'BTCe',
        'buy': BTCe_PriceA, 'sell': BTCe_PriceB,
        'buy_fee': BTCe_Fee, 'sell_fee': BTCe_Fee,
        'BTC': BTCe_BTC, 'EUR': BTCe_EUR,
        'Shorting': False}
print BTCe

def Bl3p_Price():
    
    pair = pair1[0] + pair2
    
    client = bl3p.Client.Public()
    price = client.getTicker(pair)
    
    return (float(price['ask']), float(price['bid']))
    
(Bl3p_PriceA ,Bl3p_PriceB)=  Bl3p_Price()

def Bl3p_Balances_Fees():
    
    key = Keys.Bl3p()    
    
    private = bl3p.Client.Private(key['key'], key['secret'])
    
    balances = private.getBalances()
    
    EUR =  round(float(balances['data']['wallets']['EUR']['available']['value']),2)
    
    BTC = round(float(balances['data']['wallets']['BTC']['available']['value']), 8)
       
    fee = float(balances['data']['trade_fee']) # plus 0.01eur per trade
    
    return EUR, BTC, fee
    
Bl3p_EUR, Bl3p_BTC, Bl3p_Fee = Bl3p_Balances_Fees()

Bl3p = {'Name': 'Bl3p',
        'buy': Bl3p_PriceA, 'sell': Bl3p_PriceB,
        'buy_fee': Bl3p_Fee, 'sell_fee': Bl3p_Fee,
        'BTC': Bl3p_BTC, 'EUR': Bl3p_EUR,
        'Shorting': False}
        
print Bl3p

def theRock_Price():
    
    pair = pair1[0].lower() + pair2.lower()
    
    client = theRock_Private_Client()
    price = client.Ticker(pair)
    
    return (float(price['ask']), float(price['bid']))
    
def theRock_Balances():
    
    Key = Keys.theRock()
    
    client = theRock.PyRock.API(Key['key'], Key['secret'])
    
    balances = client.AllBalances()
    
    balances = balances['balances']
    
    for balance in balances:
        
        if balance['currency'] == 'BTC':
            BTC = round(float(balance['trading_balance']),2)

        elif balance['currency'] == 'EUR':
            EUR = round(float(balance['trading_balance']),2) 
        
    return BTC, EUR    
    
theRock_BTC, theRock_EUR = theRock_Balances()


def theRock_Fees():
    
    pair = pair1[0] + pair2
    
    Key = Keys.theRock()
    
    client = theRock.PyRock.API(Key['key'], Key['secret'])
    
    funds = client.Funds()['funds']
    
    for fund in funds:
        if fund['id'] == pair:
            buy_fee = fund['buy_fee']
            sell_fee = fund['sell_fee']
            
    return buy_fee, sell_fee

theRock_FeeA, theRock_FeeB = theRock_Fees()

theRock_PriceA, theRock_PriceB=  theRock_Price()

TheRock = {'Name': 'TheRock',
        'buy': theRock_PriceA, 'sell': theRock_PriceB,
        'buy_fee': theRock_FeeA, 'sell_fee': theRock_FeeB,
        'BTC': theRock_BTC, 'EUR': theRock_EUR,
        'Shorting': True}
        
print TheRock



def xBTCe_Price():
    
    pair = pair1[0] + pair2
    
    client = xBTCe.Client.API()
    price = client.getTicker(pair)
    
    return (float(price['BestAsk']), float(price['BestBid']))
    
xBTCe_PriceA, xBTCe_PriceB = xBTCe_Price()

XBTCE = {'Name': 'xBTCe',
        'buy': xBTCe_PriceA, 'sell': xBTCe_PriceB,
        'Shorting': False}
        
print XBTCE

def Gatecoin_Prices():
    
    pair = pair1[0] + pair2
    
    client = gatecoin.api.Client()
    
    tickers = client.get_tickers()['tickers']    
    
    for ticker in tickers:
        if ticker['currencyPair'] == pair:
            price = ticker
            
    return float(price['ask']), float(price['bid'])
    
Gatecoin_PriceA, Gatecoin_PriceB = Gatecoin_Prices()

def Gatecoin_Balances():
    
    key = Keys.Gatecoin()
    
    client = gatecoin.api.Client(key['key'], key['secret'])
    
    balances = client.get_balances()
    
    for balance in balances['balances']:
        if balance['currency'] == pair2:
            EUR = round(float(balance['availableBalance']),2)
            
        elif balance['currency'] == pair1[0]:
            BTC = round(float(balance['availableBalance']),8)
            
    return EUR, BTC
    
Gatecoin_EUR, Gatecoin_BTC = Gatecoin_Balances()

Gatecoin = {'Name': 'Gatecoin',
        'buy': Gatecoin_PriceA, 'sell': Gatecoin_PriceB,
        'buy_fee': 0.35, 'sell_fee': 0.25,
        'BTC': Gatecoin_BTC, 'EUR': Gatecoin_EUR,
        'Shorting': False} # Coming soon
        
print Gatecoin


def Arbitrage(Exchanges):
    
    Exchange1 = Exchanges[0]
    Exchange2 = Exchanges[1]
    
    Profit = (Exchange2['sell'] - Exchange1['buy']) / Exchange1['buy'] * 100
    if Profit>0:
        print Exchange1['Name']+'_'+Exchange2['Name'], Profit

def Get_Perm(Exchanges):
    
    Permuatations = list(itertools.permutations(Exchanges, 2))
    Permuatations = [i for i in Permuatations if i[1]['Shorting'] is True]
    for Permuatation in Permuatations:
        print Permuatation[0]['Name'], Permuatation[1]['Name']
    return Permuatations


def main():
    Exchanges = [Kraken, Bitstamp, Gdax, BTCe, TheRock, Bl3p, XBTCE, Gatecoin]
    Permuatations=Get_Perm(Exchanges)
    for Permuatation in Permuatations:
        try: Arbitrage(Permuatation)
        except:
            print Permuatation +' Failed'
            continue
        
if __name__ == "__main__":
    main()    
            

    
     


    
    
    
    

