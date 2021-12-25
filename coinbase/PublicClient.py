#
# GDAX/PublicClient.py
# Daniel Paquin
#
# For public requests to the GDAX exchange

import requests
import pandas as pd

class PublicClient():
    def __init__(self, api_url="https://api.pro.coinbase.com", product_id="BTC-USD"):
        self.url = api_url
        if api_url[-1] == "/":
            self.url = api_url[:-1]
        self.productId = product_id

    def getProducts(self):
        r = requests.get(self.url + '/products', timeout=5)
        #r.raise_for_status()
        return r.json()

    def getProductOrderBook(self, json=None, level=2, product=''):
        if type(json) is dict:
            if "product" in json: product = json["product"]
            if "level" in json: level = json['level']
        r = requests.get(self.url + '/products/%s/book?level=%s' % (product or self.productId, str(level)), timeout=5)
        #r.raise_for_status()
        return r.json()

    def getProductTicker(self, json=None, product=''):
        if type(json) is dict:
            if "product" in json: product = json["product"]
        r = requests.get(self.url + '/products/%s/ticker' % (product or self.productId), timeout=5)
        #r.raise_for_status()
        return r.json()

    def getProductTrades(self, json=None, product=''):
        if type(json) is dict:
            if "product" in json: product = json["product"]
        r = requests.get(self.url + '/products/%s/trades' % (product or self.productId), timeout=5)
        #r.raise_for_status()
        return r.json()

    def getProductHistoricRates(self, json=None, product='', start='', end='', granularity=''):
        payload = {}
        if type(json) is dict:
            if "product" in json: product = json["product"]
            payload = json
        else:
            payload["start"] = start
            payload["end"] = end
            payload["granularity"] = granularity
        r = requests.get(self.url + '/products/%s/candles' % (product or self.productId), params=payload, timeout=5)
        #r.raise_for_status()
        return r.json()

    def getProduct24HrStats(self, json=None, product=''):
        if type(json) is dict:
            if "product" in json: product = json["product"]
        r = requests.get(self.url + '/products/%s/stats' % (product or self.productId), timeout=5)
        #r.raise_for_status()
        return r.json()

    def getCurrencies(self):
        r = requests.get(self.url + '/currencies', timeout=5)
        #r.raise_for_status()
        return r.json()

    def getTime(self):
        r = requests.get(self.url + '/time', timeout=5)
        #r.raise_for_status()
        return r.json()
    
client = PublicClient()
df = pd.DataFrame(client.getProducts())
df = df[~df['id'].isin(['USDT'])]
df = df[~df['id'].isin(['USDC'])]
df = df[df['quote_currency'].str.contains('USD')]



crypto_tickers = []

for i in df['id']:
    item = str(i)
    if 'USDT' not in item and 'USDC' not in item:
        crypto_tickers.append(i)
        
crypto_tickers.sort()

print(client.getProduct24HrStats(product="btc-usd"))


