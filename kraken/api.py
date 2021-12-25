import time, hmac, requests, hashlib, urllib.parse, base64

class Client:
    
  def __init__(self, key="", secret=""):
      self.key = key
      self.secret = secret
      self.apiUrl = "https://api.kraken.com"
      self.apiVersion = "0"
  
  def _send_request(self, path, httpMethod, params={}):
      
      req = params
      
      urlpath = '/' + self.apiVersion + path

      if httpMethod == "GET":
          data = params
          headers = params
          R = requests.get
          
      elif httpMethod == "POST":

        urlpath = '/' + self.apiVersion + path

        req['nonce'] = int(1000*time.time())
        data = urllib.parse.urlencode(req)
        encoded = (str(req['nonce']) + data).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()
        signature = hmac.new(base64.b64decode(self.secret),
                             message, hashlib.sha512)
                             
        headers = {'API-Key': self.key,
                   'API-Sign': base64.b64encode(signature.digest())}
                     
        R = requests.post
        
      url = self.apiUrl + urlpath
      
      if path[1:7] == 'public': 
      
          response = R(url, data=data, headers=headers, timeout=5)
      else:
          response = R(url, data=data, headers=headers, timeout=30)
      
      return response.json()
      
  def get_orderbook(self, pair):
      return self._send_request("/public/Depth", "POST", params = {'pair': pair})
      
  def get_info(self, pair):
      return self._send_request("/public/AssetPairs", "POST", params = {'info': 'fees'})
                                
  def get_balances(self):
      return self._send_request("/private/Balance", "POST", params = {})

  def place_order(self, Params):
      return self._send_request("/private/AddOrder", "POST", params = Params)
                                        
  def cancel_order(self, ref):
      return self._send_request("/private/CancelOrder", "POST", params={'txid': ref})
                                        
  def query_order(self, ref):
      return self._send_request("/private/QueryOrders", "POST", params={'txid': ref})
      
  def open_orders(self):
      return self._send_request("/private/OpenOrders", "POST", params={})
      
  def closed_orders(self):
      return self._send_request("/private/ClosedOrders", "POST", params={})
      
  def open_positions(self):
      return self._send_request("/private/OpenPositions", "POST", params={})
                                