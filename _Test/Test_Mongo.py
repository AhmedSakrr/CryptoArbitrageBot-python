from pymongo import MongoClient
import pprint

client = MongoClient('mongodb://localhost:27017/')

person = {'Name': 'Geoff', 'Age': 26}

db = client.example
db.test.insert(person)

for a in db.test.find():
    pprint.pprint(a)
    
client.drop_database('example')
    
print client.database_names()

exchange = {'Name': 'Bitfinex'}

db = client.Bitcoin_Bot
db.Exchanges.insert(exchange)

for a in db.Exchanges.find():
    pprint.pprint(a)
#    db.Exchanges.remove(a)

print client.database_names()
print db.collection_names()
