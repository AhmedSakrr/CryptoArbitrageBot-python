import lakebtc

pair1 = 'BTC', 'XBT'
pair2 = 'EUR'

Client = lakebtc.api.Client()

def LakeBTC_Orderbook():
    
    pair = pair1[0] + pair2
    pair = pair.lower()
    
    Orderbook = Client.get_bcorderbook(pair)
    
    print Orderbook
    
LakeBTC_Orderbook()

