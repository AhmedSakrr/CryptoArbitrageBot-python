import httplib, base64, json, hashlib, hmac, time


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
    
def Fees():    
    
    api_v = '/v1/'
    post_type = "account_infos"    
    address = api_v + post_type
    
    params = {"request": address,
              "nonce": Nonce()}
    
    return address, params
    
def Balance():    
    
    api_v = '/v1/'
    post_type = "balances"    
    address = api_v + post_type
    
    params = {"request": address,              
              "nonce": Nonce()}   
    
    return address, params
    
def Send_Order(pair, size, price, side):    
    
    api_v = '/v1/'
    post_type = "order/new"    
    address = api_v + post_type
    
    params = {"request": address,
              "symbol": pair,
              "amount": size,
              "price": price,
              "side": side,
              "type": "market",
              "nonce": Nonce()}   
    
    return address, params
    
def Price(pair1, pair2):
    
    api_v = '/v1/'
    
    if pair2.lower() == 'usd':               
      
        conn = httplib.HTTPSConnection("api.bitfinex.com")
        conn.request("GET", api_v+"/pubticker/"+pair1.lower()+pair2.lower())
        
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
        
    

