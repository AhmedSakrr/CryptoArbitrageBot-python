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
    
    pair1 = 'BTC'
    pair2 = 'USD'
    pair = pair1+pair2
    
    side = "sell"
    
    price = Bfx_Price(pair1, pair2)[side]    
    
    size = '{0:f}'.format(0.00001)       
    
    Bfx_Send("order", pair, size, price, side)
    
    
def Bfx_Send(send, pair, size, price, side):    
    
    post_type = {"info":"account_infos",
                 "balances":"balances",
                 "summary":"summary",
                 "order":"order/new"}
                 
    api_v = '/v1/'
    
    for key, value in post_type.items():
        post_type[key] = api_v + post_type[key]
  
    address = post_type[send]    
    
    parms = {"request": address,
              "symbol": pair,
              "amount": size,
              "price": price,
              "side": side,
              "type": "market",
              "nonce": str(round(time.time()-1398621111,1)*10)}   
    
    Bfx_trade = Bfx_Post(address, parms)    
    Bfx_trade.Post_Params()    
    

class Bfx_Post(object):
    
    def __init__(self, request, parms):
        self.request = request
        self.parms = parms
 
    
    def Post_Params(self):                      
#        parms1 = urllib.urlencode(parms)
        
        payload = base64.standard_b64encode(buffer(json.dumps(self.parms)))        
       
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
    
    return {"buy":bfx_buy, "sell":bfx_sell}
    
    
if __name__ == "__main__":
    main()



