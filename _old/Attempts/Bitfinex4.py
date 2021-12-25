import httplib
import base64
import json
import hashlib
import hmac
import time

def main():
    
    pair1 = 'BTC'
    pair2 = 'USD'
    pair = pair1+pair2
    
    side = "sell"
    
    price = Price(pair1, pair2)[side]    
    
    size = '{0:f}'.format(0.00001) 
    
    fee = Fees(Nonce())
   
    open_fee = fee[0]['taker_fees']
    close_fee = fee[0]['maker_fees']
    
    print 'Fee to open Order is', open_fee, '%'
    print 'Fee to close Order is', close_fee, '%'


    balance = Balance(Nonce())
    
    if not balance:
        print "You've got no fuckin money!"

    else:
        print "You're balance is ", balance[0]        
        Send_Order(pair, size, price, side, Nonce())

    
def Fees(nonce):    
    
    api_v = '/v1/'
    post_type = "account_infos"    
    address = api_v + post_type
    
    params = {"request": address,              
              "nonce": nonce}   
    
    return Post(address, params)   
    
def Balance(nonce):    
    
    api_v = '/v1/'
    post_type = "balances"    
    address = api_v + post_type
    
    params = {"request": address,              
              "nonce": nonce}   
    
    return Post(address, params)
    
def Send_Order(pair, size, price, side, nonce):    
    
    api_v = '/v1/'
    post_type = "order/new"    
    address = api_v + post_type
    
    params = {"request": address,
              "symbol": pair,
              "amount": size,
              "price": price,
              "side": side,
              "type": "market",
              "nonce": nonce}   
    
    return Post(address, params)
        
        
def API_Keys():
    key = 'os50Un8kHgctOD7jmNQVhUTabaniIbhQRWlcWCGXPdI'
    secret = 'LmID1xpEJBUhHyT7nYyF47O4brBt1pw1yohKpR4hTSI'
    return {"Key":key, "Secret":secret}

def Nonce():
    return str(round(time.time()-1398621111,1)*10)
        
def Post(address, params):                      
   
    payload = base64.standard_b64encode(buffer(json.dumps(params)))     
    hashed = hmac.new(API_Keys()['Secret'].encode(), payload, hashlib.sha384)
    signature = hashed.hexdigest()    
    
    headers = {"Content-type": "application/x-www-form-urlencoded",
               "X-BFX-APIKEY": API_Keys()['Key'],
               "X-BFX-PAYLOAD": payload,
               "X-BFX-SIGNATURE": signature}

    conn = httplib.HTTPSConnection("api.bitfinex.com")
    conn.request("POST", address, payload, headers)
    
    response = conn.getresponse()
    print(response.status,response.reason)
    
    resp = json.load(response)
    
#    print resp
    return resp
            
    
def Price(pair1, pair2):
    
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



