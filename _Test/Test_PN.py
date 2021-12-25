import krakenex #Shorting ok
import Keys

pair1 = 'BTC', 'XBT'
pair2 = 'EUR'


def Kraken_Price(): 
    
    pair = 'X'+pair1[1]+'Z'+pair2
    
    API = krakenex.API()
    price = API.query_public('Ticker', {'pair': pair})['result'][pair]
                  
    return (float(price['a'][0]), float(price['b'][0]))
    
Kraken_Sell, Kraken_Buy = Kraken_Price()
print Kraken_Sell, Kraken_Buy

    
def Kraken_Fees():
    pair = 'X'+pair1[1]+'Z'+pair2
    API = krakenex.API()
    fees = API.query_public('AssetPairs', {'info': 'fees'})['result'][pair]
    
    return (float(fees['fees'][0][1]), float(fees['fees_maker'][0][1]))
            
Kraken_FeeBuy, Kraken_FeeSell = Kraken_Fees()
print (Kraken_FeeBuy, Kraken_FeeSell) 
          
def Kraken_Balances():
    
    key = Keys.Kraken()
    
    api = krakenex.API(key=key['key'], secret=key['secret'])
    balance = api.query_private('Balance')['result']
    
    btc = round(float(balance['XXBT']),8)
    eur = round(float(balance['ZEUR']),2)
    
    return (btc, eur)
   
Kraken_BTC, Kraken_EUR = Kraken_Balances()

print Kraken_BTC, Kraken_EUR
#
#Kraken = {'Name': 'Kraken', 'buy': Kraken_PriceA, 'sell': Kraken_PriceB,
#          'buy_fee': Kraken_FeeA, 'sell_fee': Kraken_FeeB,
#          'BTC': Kraken_BTC, 'EUR': Kraken_EUR,
#          'Shorting': True}
#
#print Kraken