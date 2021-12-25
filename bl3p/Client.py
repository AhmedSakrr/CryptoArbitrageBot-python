'''===================     Author: Geoff Barrett     ======================='''

import urllib
import base64
import hmac
import http.client as httplib
import hashlib
import json



class Private(object):    
    
    def __init__(self, key, secret):
        
        self.__url = 'https://api.bl3p.eu/1/'
        self.__key = key
        self.__secret = secret

    
    '''===================     Bl3p Private Client     ====================='''
        
    def __Private_Client(self, path, params):   
        
        address = self.__url + path

    
        post_data = urllib.urlencode(params) # blank params
        
        body = '%s%c%s' % (path, 0x00, post_data)
        
        privkey_bin = base64.b64decode(self.__secret)
        signature_bin = hmac.new(privkey_bin, body, hashlib.sha512).digest()
        signature = base64.b64encode(signature_bin)
        headers = { 'Rest-Key': self.__key, 'Rest-Sign': signature }
        
        conn = httplib.HTTPSConnection('api.bl3p.eu', timeout=30)
        conn.request("POST", address, post_data, headers)
        
        response = conn.getresponse()
        resp = json.load(response)
        
        return resp
        
    def getBalances(self):
        return self.__Private_Client('GENMKT/money/info', { })    
    
        
    def addOrder(self, pair, order_type, order_amount, order_price):
        params = {'type' : order_type, 'amount_int' : order_amount,
                  'price_int' : order_price, 'fee_currency' : 'EUR'}
        return self.__Private_Client('%s/money/order/add' % pair, params)
        
    def addMarketOrder(self, pair, order_type, order_amount):
        params = {'type' : order_type, 'amount_int' : order_amount,
                  'fee_currency' : 'EUR'}
        return self.__Private_Client('%s/money/order/add' % pair, params)
        
    def cancelOrder(self, pair, order_id):
        params = { 'order_id' : order_id }
        return self.__Private_Client("%s/money/order/cancel" % pair, params)
        
    def FullOrderbook(self, pair):
        return self.__Private_Client("%s/money/depth/full" %pair, {})
        
    def checkOrder(self, pair, order_id):
        params = { 'order_id' : order_id }
        return self.__Private_Client("%s/money/order/result" % pair, params)
          
    def getNewDepositAddress(self, pair):
        return self.__Private_Client("%s/money/new_deposit_address" % pair,{ })
  
   
    def getLastDepositAddress(self, pair):
        return self.__Private_Client("%s/money/deposit_address" % pair, { })
  
    def walletHistory(self, currency, n):
        params = { 'currency' : currency, 'recs_per_page' : n}
        return self.__Private_Client('GENMKT/money/wallet/history', params)

    def getAllActiveOrders(self, pair):
        return self.__Private_Client("%s/money/orders" % pair, { })

class Public(object):    
    
    def __init__(self):
        
        self.__url = 'https://api.bl3p.eu/1/'
  
  
    '''====================     Bl3p Public Client     ====================='''
        
    def __Public_Client(self, path):
        self.__path = path
    
        address = self.__url+self.__path       
        
        conn = httplib.HTTPSConnection('api.bl3p.eu', timeout=5)
        conn.request("POST", address)
        
        response = conn.getresponse()
        resp = json.load(response)
        
        return resp
        
        
    # ===================     Bl3p Public Functions     ==================== #
        
    def getTicker(self, pair):
         self.__pair = pair
         if pair [3:6] != 'EUR':
             return 'Bl3p Only Accepts Eur as currency pair'            
         else: 
             return self.__Public_Client("%s/ticker" % pair )
         
    def getOrderbook(self, pair):
         self.__pair = pair
         if pair [3:6] != 'EUR':
             return 'Bl3p Only Accepts Eur as currency pair'            
         else: 
             return self.__Public_Client("%s/orderbook" % pair)
         
