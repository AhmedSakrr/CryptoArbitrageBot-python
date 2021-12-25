import time, base64, hmac, requests, hashlib, json

class Client:
    
    def __init__(self, key="", secret=""):
        self.key = key
        self.secret = secret
        self.apiUrl = 'https://api.bitfinex.com'      
  
    def _send_request(self, path, httpMethod, params={}):  
        
        nonce = str(time.time())
        url = self.apiUrl + path    
        key = self.key
        secret = self.secret
        
        data = {'request': path,
                 'nonce': nonce}
                  
        data.update(params)
                
#        payload_json = json.dumps(data)
#        payload = base64.b64encode(bytes(payload_json, 'latin-1'))
#        secret_bytes = bytes(secret,  'latin-1')
#        sig = hmac.new(secret_bytes, payload, hashlib.sha384)
#        sig = sig.hexdigest()
        
        payload_json = json.dumps(data)
        payload = base64.standard_b64encode(payload_json.encode('utf8'))
        sig = hmac.new(secret.encode('utf8'), payload, hashlib.sha384)
        sig = sig.hexdigest()
        
        headers = {
            'X-BFX-APIKEY' : key,
            'X-BFX-SIGNATURE' : sig,
            'X-BFX-PAYLOAD' : payload}

        if httpMethod == "GET":
            R = requests.get
            
        elif httpMethod == "POST":
            R = requests.post
            
        if httpMethod == "GET":
            response = R(url, headers=headers, timeout=5, verify=True)
        else:
            response = R(url, headers=headers, timeout=30, verify=True)

          
        return response.json()
              
    def get_orderbook(self, pair):
        return self._send_request("/v1/book/%s" % pair, "GET")
        
    def get_moqs(self):
        return self._send_request("/v1/symbols_details", "GET")
        
    def get_fees(self):
        return self._send_request("/v1/account_infos", "POST")
    
    def get_balances(self):
        return self._send_request("/v1/balances", "POST")
        
    def wallet_transfer(self, amount, currency, walletfrom, walletto):
        
        params = {'amount': str(amount),
                  'currency': currency,
                  'walletfrom': walletfrom,
                  'walletto': walletto}        
        
        return self._send_request("/v1/transfer", "POST", params)
    
    def limit_order(self, symbol, amount, side, price, leverage):
        
        if leverage == 0:
        
            params = {'exchange': 'bitfinex',
                      'symbol': symbol,
                      'amount': '%.8f' % float(amount),
                      'side': side,
                      'price': '%.2f' % float(price),
                      'type': 'exchange limit'}
                      
        elif leverage != 0:
        
            params = {'exchange': 'bitfinex',
                      'symbol': symbol,
                      'amount': '%.8f' % float(amount),
                      'side': side,
                      'price': '%.2f' % float(price),
                      'type': 'limit'}
                      
        return self._send_request("/v1/order/new", "POST", params)
        
    def market_order(self, symbol, amount, side, price, leverage):
        
        if leverage == 0:
        
            params = {'exchange': 'bitfinex',
                      'symbol': symbol,
                      'amount': '%.8f' % float(amount),
                      'side': side,
                      'price': '%.2f' % float(price),
                      'type': 'exchange market'}
                      
        elif leverage != 0:
        
            params = {'exchange': 'bitfinex',
                      'symbol': symbol,
                      'amount': '%.8f' % float(amount),
                      'side': side,
                      'price': '%.2f' % float(price),
                      'type': 'market'}
        
        return self._send_request("/v1/order/new", "POST", params) 
        
    def order_status(self, ref):
        
        params = {'order_id': int(ref)}        
        
        return self._send_request("/v1/order/status", "POST", params)
        
    def cancel_order(self, ref):
        
        params = {'order_id': int(ref)}        
        
        return self._send_request("/v1/order/cancel", "POST", params)
        
