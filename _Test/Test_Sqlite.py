import sqlite3
import pandas as pd
import time

current_time = 1234

db_conn = sqlite3.connect('Price_History4.db')

Cursor = db_conn.cursor()

for Exchange in Exchanges:

    db_conn.execute("DROP TABLE IF Exists %s" %(Exchange['Name']))
    db_conn.commit()

for Exchange in Exchanges:
    
    try:
                                                
        db_conn.execute("CREATE TABLE %s (Time INTEGER NOT NULL);" %(Exchange['Name'],))
                                             
        db_conn.commit()

    except sqlite3.OperationalError:
        print "Table could not be created."
    
for Exchange in Exchanges:
    
    for Coin in Coins:

        try:
                                                    
            Cursor.execute("ALTER TABLE %s ADD COLUMN %s REAL" %(Exchange['Name'], Coin+"_Bid"))
                                                 
            
            Cursor.execute("ALTER TABLE %s ADD COLUMN %s REAL" %(Exchange['Name'], Coin+"_Ask"))
                                                 

        except sqlite3.OperationalError:
            print "Column could not be created." 

  
for Exchange in Exchanges:
    
    
    db_conn.execute("INSERT INTO %s (Time) VALUES(?)" %(Exchange['Name']), (current_time,))

                     
    db_conn.commit()
        
    for Coin in Coins:
        
        Cursor.execute("Update %s SET %s = %f WHERE Time = %d" %(Exchange['Name'], Coin+'_Bid', Exchange['Prices'][Coin]['buy'], current_time))
        Cursor.execute("Update %s SET %s = %f WHERE Time = %d" %(Exchange['Name'], Coin+'_Ask', Exchange['Prices'][Coin]['sell'], current_time))


db_conn.close()

#con = sqlite3.connect('Test.db')
#
#df = pd.read_sql_query("SELECT * from Prices", con)
#
#con.close()



