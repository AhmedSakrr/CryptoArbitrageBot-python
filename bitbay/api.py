import time, hmac, requests, hashlib

from urllib.parse import urlencode

class Client:
    
  def __init__(self, key="", secret=""):
      self.key = key
      self.secret = secret
      self.apiUrl = "https://bitbay.net/API/"      
  
  def _send_request(self, path, httpMethod, params={}):  
      
      url = self.apiUrl + path

      if httpMethod == "GET":
          data = None
          headers = None
          R = requests.get
          
      elif httpMethod == "POST":

          params['moment'] = int(time.time())
          data = urlencode(tuple(zip(params.keys(),params.values())))
          secret_bytes = bytes(self.secret, 'latin-1')
          data_bytes = bytes(data, 'latin-1')
          signature = hmac.new(secret_bytes, data_bytes, digestmod=hashlib.sha512).hexdigest()
    
          headers = {'API-Key': self.key,
                     'API-Hash': signature,
                     'Content-Type' : 'application/x-www-form-urlencoded'}
                     
          R = requests.post
          
      if httpMethod == "GET":
          response = R(url, data=data, headers=headers, timeout=5)
      else:
           response = R(url, data=data, headers=headers, timeout=30)
         
      
      return response.json()
      
  def get_orderbook(self, pair):
      return self._send_request("Public/"+pair+"/orderbook.json", "GET")
      
  def get_info(self):
      return self._send_request("Trading/tradingApi.php", "POST",
                                params={'method': 'info'})

  def place_order(self, pair, amount, side, price):
      return self._send_request("Trading/tradingApi.php", "POST",
                                params={'method': 'trade',
                                        'type': side,
                                        'currency': pair[0],
                                        'amount': amount,
                                        'payment_currency': pair[1],
                                        'rate': price})
                                        
                                        
  def cancel_order(self, order_id):
      return self._send_request("Trading/tradingApi.php", "POST",
                                params={'method': 'cancel',
                                        'id': order_id}) 

  def get_order(self):
      return self._send_request("Trading/tradingApi.php", "POST",
                                params={'method': 'orders'})
                                
  def get_transactions(self):
      return self._send_request("Trading/tradingApi.php", "POST",
                                params={'method': 'transactions'})                               

                                
