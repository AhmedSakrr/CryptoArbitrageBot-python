import time, requests, json, jwt

class Client:
    
    def __init__(self, key="", secret=""):
        self.key = key
        self.secret = secret
        self.apiUrl = "https://api.quoine.com"
        
    def _send_request(self, path, httpMethod, params={}):
               
        nonce = str(int(time.time()*1000))
            
        url = self.apiUrl + path
                
        payload = {'path': path,
                   'nonce': nonce,
                   'token_id': self.key}
                               
        signature = jwt.encode(payload, self.secret, algorithm='HS256')

        headers = {'X-Quoine-API-Version': '2',
                   'X-Quoine-Auth': signature,
                   'Content-Type': 'application/json'}
                   
        if httpMethod == "GET":
            data = None
            R = requests.get
        if httpMethod == "PUT":
            data = json.dumps(params)
            R = requests.put
        elif httpMethod == "POST":
            data = json.dumps(params)
            R = requests.post          

        response = R(url, data=data, headers=headers, timeout=10)
      
        return response.json()
        
    def determine_product(self, pair):
        
        if pair[0] == "BTC":
            
            ccy = pair[1]
        
            if ccy == "USD":
                ccy_id = "1"
            elif ccy == "EUR":
                ccy_id = "3"
            elif ccy == "JPY":
                ccy_id = "5"
                
        elif pair[0] == "ETH":
            
            ccy = pair[1]
        
            if ccy == "USD":
                ccy_id = "27"
            elif ccy == "EUR":
                ccy_id = "28"
            elif ccy == "JPY":
                ccy_id = "29"
                
        Product_ID = ccy_id
                
        return Product_ID
        
      
    def get_orderbook(self, pair):      
        Product_ID = self.determine_product(pair)      
        return self._send_request("/products/%s/price_levels" %Product_ID, "GET")
      
    def get_balances(self):
        return self._send_request("/accounts/balance", "GET")
        
    def get_product_info(self, pair): 
        Product_ID = self.determine_product(pair)
        return self._send_request("/products/%s" % Product_ID, "GET")

    def place_limit_order(self, pair, ordertype, amount, side, price, leverage):
        
        Product_ID = self.determine_product(pair)
        
        if leverage != 0:
        
            Params = {"order":{"order_type": "limit",
                               "product_id": Product_ID,
                               "side": side,
                               "quantity": amount,
                               "price": price,
                               "leverage_level": leverage}}
                               
        else:
            
            Params = {"order":{"order_type": "limit",
                   "product_id": Product_ID,
                   "side": side,
                   "quantity": amount,
                   "price": price}}
                               
        return self._send_request("/orders/", "POST", params = Params)

                               
    def place_market_order(self, pair, ordertype, amount, side, leverage):
        
        Product_ID = self.determine_product(pair)
        
        if leverage != 0:
            
            Params = {"order":{"order_type": "market",
                               "product_id": Product_ID,
                               "side": side,
                               "quantity": amount,
                               "leverage_level": leverage}}
        elif leverage == 0:
            
            Params = {"order":{"order_type": "market",
                               "product_id": Product_ID,
                               "side": side,
                               "quantity": amount}}
                         
        return self._send_request("/orders/", "POST", params = Params)
        
    def cancel_order(self, ref):
        return self._send_request("/orders/%s/cancel" %ref, "PUT")

    def get_order(self, ref):
        return self._send_request("/orders/%s" %ref, "GET")   
        
    def close_trade(self, ref):
        return self._send_request("/trades/%s/close" %ref, "PUT")
        
    def update_short(self, ref, price):
        
        
        Orders = self._send_request("/trades", "GET")['models']
        
        for order in Orders:
            if str(order['id']) == str(ref):
                Trade = order
        
        PnL = float(Trade['pnl'])
        
        print PnL
        
        if PnL < 0:
            
            Params = {"trade": {
                                "stop_loss": str(price),
                                "take_profit": str(1000000)}}
               
        elif PnL > 0:   
            
            Params = {"trade": {
                                "stop_loss": str(0),
                                "take_profit": str(5000)}}
        
        print Params 
        
        return self._send_request("/trades/%s" %ref, "PUT", params = Params)


