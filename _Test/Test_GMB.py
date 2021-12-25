import krakenex
import Keys

#constants
pair1 = 'BTC', 'XBT'
pair2 = 'EUR'

class _Kraken(object):
    
    def __init__(self):
        
        def Private(self, query):
            
            Key = Keys.Kraken()
            client = krakenex.API(Key['key'], Key['secret']).query_private(query)
            return client
        
        self.pair = 'X'+pair1[1]+'Z'+pair2    
        self.Private_Client = Private(self, query='')  
    
    def Price(self): 
        
        API = krakenex.API()
        price = API.query_public('Ticker',
                      {'pair': self.pair})['result'][self.pair]
                      
        return (float(price['a'][0]), float(price['b'][0]))
        
    def Fees(self):
        API = krakenex.API()
        fees = API.query_public('AssetPairs', {'info': 'fees'})['result'][self.pair]
        
        return (float(fees['fees'][0][1]), float(fees['fees_maker'][0][1]))
             
    def Balances(self):
    
        balance = self.Private_Client('Balance')#['result']
        print balance
        btc = round(float(balance['XXBT']),8)
        eur = round(float(balance['ZEUR']),2)
        
        return (btc, eur)
        
    def Order(self, amount, side, price, leverage):
        
        params = {'pair': self.pair,
                  'type': side,
                  'ordertype': 'limit',
                  'price': price,
                  'leverage': leverage, # 1 to 5 times
                  'volume': amount}
        
        Order = self.Private_Client('AddOrder', params)
        
        return Order
        
    def Make(self):
        (Kraken_PriceA, Kraken_PriceB) = self.Price()           
        (Kraken_FeeA, Kraken_FeeB) = self.Fees()
        (Kraken_BTC, Kraken_EUR) = self.Balances()
    
        Kraken = {'Name': 'Kraken',
                  'buy': Kraken_PriceA,
                  'sell': Kraken_PriceB,
                  'buy_fee': Kraken_FeeA,
                  'sell_fee': Kraken_FeeB,
                  'BTC': Kraken_BTC,
                  'EUR': Kraken_EUR,
                  'Shorting': True}
        return Kraken
        
        
def main():
    Kraken=_Kraken().Make()
    print Kraken
    

if __name__ == "__main__":
    main()   
    