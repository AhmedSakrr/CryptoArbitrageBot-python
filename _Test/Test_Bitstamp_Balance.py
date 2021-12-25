import bitstamp
import Keys

pair1 = 'BTC', 'XBT'
pair2 = 'EUR'

def Bitstamp_Private_Client():
    
    key = Keys.Bitstamp()   
    client = bitstamp.client.Trading(key['user'], key['key'], key['secret'])
    return client
    
def Bitstamp_Fees():
    
    pair = pair1[0].lower(), pair2.lower()
    balance = Bitstamp_Private_Client().account_balance(pair[0], pair[1])
    
    fee = float(balance['fee'])
    
    print {'buy_fee': fee, 'sell_fee': fee}
    
Bitstamp_Fees()