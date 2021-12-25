import httplib
import urllib
import base64
import json
import hashlib
import hmac
import time

api_key = 'os50Un8kHgctOD7jmNQVhUTabaniIbhQRWlcWCGXPdI'
api_secret = 'LmID1xpEJBUhHyT7nYyF47O4brBt1pw1yohKpR4hTSI'

def main():
    
    api_version = '/v1/'
    
    pair1 = 'BTC'
    pair2 = 'USD'   
    
    
    buy = Bfx_Price(pair1, pair2)[0]
    sell = Bfx_Price(pair1, pair2)[1]
    
    price = buy
    
    trade_size = '{0:f}'.format(0.00001)
    
    side = "buy"
    
    trade_type = "market"
    
#    account_info = (api_version+"account_infos")
#    balances = (api_version+"balances")   
#    summary = (api_version+"summary")
    trade = (api_version+"order/new")
    
    trade = Post(trade, pair1+pair2, trade_size, price, side, trade_type)
    
    def Bfx_Post(Param):
        Param.Post_Trade()
        
    Bfx_Post(trade)
    

class Post(object):
    
    def __init__(self, request, symbol, amount, price, side, trade_type):
        self.request = request
        self.symbol = symbol
        self.amount = amount
        self.price = price
        self.side = side
        self.trade_type = trade_type
    
    def Post_Trade(self):     
        
        nonce = str(round(time.time()-1398621111,1)*10)    
        
        parms = {"request": self.request,
                 "symbol": self.symbol,
                 "amount": self.amount,
                 "price": self.price,
                 "side": self.side,
                 "type": self.trade_type,
                 "nonce": nonce}
                 
#        parms1 = urllib.urlencode(parms)
        
        payload = base64.standard_b64encode(buffer(json.dumps(parms)))        
       
        hashed = hmac.new(api_secret.encode(), payload, hashlib.sha384)
#        hashed.update(parms1)
        signature = hashed.hexdigest()
    
        
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "X-BFX-APIKEY": api_key,
                   "X-BFX-PAYLOAD": payload,
                   "X-BFX-SIGNATURE": signature}
    
        conn = httplib.HTTPSConnection("api.bitfinex.com")
        conn.request("POST", self.request, payload, headers)
        
        response = conn.getresponse()
        print(response.status,response.reason)
        
        resp = json.load(response)
        print resp
    


def Bfx_Price(pair1, pair2):
    
    if pair2.lower() == 'usd':    
        api_version = 'v1'    
      
        conn = httplib.HTTPSConnection("api.bitfinex.com")
        conn.request("GET", "/"+ api_version +"/pubticker/"+pair1.lower()+pair2.lower())
        
        response = conn.getresponse()
        print(response.status, response.reason)
        
        resp = json.load(response)
        result = resp
        bfx_buy = result['ask']
        bfx_sell = result['bid']
        print 'Bitfinex '+pair1+'/'+pair2, bfx_buy, '/', bfx_sell
    else:
        print 'Bitfinex only accepts usd'
    
    return bfx_buy, bfx_sell 
    
if __name__ == "__main__":
    main()



