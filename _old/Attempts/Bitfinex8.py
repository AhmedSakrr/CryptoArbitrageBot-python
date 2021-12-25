import httplib, base64, json, hashlib, hmac, time

def main():
    
    pair1 = 'BTC'
    pair2 = 'USD'
    
    pair = pair1+pair2
    
    side = "sell"
    
    get_price = Get(pair1, pair2)
    price = get_price.Send_Get()[side]
    
    size = '{0:f}'.format(0.00001)
    
    get_fees = get_info("account_infos")
    fee = get_fees.send_request()
    fees = get_fees.Sign(fee)
   
    open_fee, close_fee = fees[0]['taker_fees'], fees[0]['maker_fees'] 
    
    print 'Fee to open is', open_fee, '%\n', 'Fee to close is', close_fee, '%'
    
    get_balance = get_info("balances")
    balance = [10] #get_balance.send_request()    
  
    if not balance:
        print "You've got no fuckin money!"        
    else:
        print "You're balance is ", balance[0]
        
        send_info = get_info("order/new")
        info=send_info.Send_Order(pair, size, price, side) 
        print info
        print send_info.Sign(info)
        print "Order Sent"
    
def API_Keys():
    key = 'os50Un8kHgctOD7jmNQVhUTabaniIbhQRWlcWCGXPdI'
    secret = 'LmID1xpEJBUhHyT7nYyF47O4brBt1pw1yohKpR4hTSI'
    return {"Key":key, "Secret":secret}

def Nonce():
    return str(round(time.time()-1398621111,1)*10)   

    
class get_info(object):    
    
    def __init__(self,request):
        self.request = request
    
    def send_request(self):
        
        api_v = '/v1/'        
        post_type = self.request    
        address = api_v + post_type
            
        params = {"request": address,              
                  "nonce": Nonce()}
                  
        return (address, params)  
 
    def Send_Order(self, pair, size, price, side):
        self.pair = pair
        self.size = size
        self.price = price
        self.side = side
        
        api_v = '/v1/'
        post_type = "order/new"    
        address = api_v + post_type
        
        params = {"request": address,
                  "symbol": self.pair,
                  "amount": self.size,
                  "price": self.price,
                  "side": self.side,
                  "type": "market",
                  "nonce": Nonce()}
        
        return (address, params)
        
    def Sign(self, add_par):    
    
        address, params=add_par
        
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
        
        return resp    
        
class Get(object):
    
    def __init__(self,pair1, pair2):
        self.pair1 = pair1
        self.pair2 = pair2
        
    def Send_Get(self):
        
        api_v = '/v1/'
        
        if self.pair2.lower() == 'usd':               
          
            conn = httplib.HTTPSConnection("api.bitfinex.com")
            conn.request("GET", api_v+"/pubticker/"+self.pair1.lower()+self.pair2.lower())
            
            response = conn.getresponse()
            print(response.status, response.reason)
            
            resp = json.load(response)
            result = resp            
                        
            bfx_buy = result['ask']
            bfx_sell = result['bid']
            
            print 'Bitfinex '+self.pair1+'/'+self.pair2, bfx_buy,'/',bfx_sell
        else:
            print 'Bitfinex only accepts usd'
        
        return {"buy":bfx_buy, "sell":bfx_sell}                
        
   
    

        
    
if __name__ == "__main__":
    main()



