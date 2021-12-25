import shelve

Saved_Variables = shelve.open('Saved_Variables.shelve')

Saved_Variables.update(Exchanges)

#Saved_Variables.update([Exchanges, Permuatations, Opportunities, Current_Arbs,
#                 Removed_Exchanges, Successful_Arbs, Profits, Target_Profit,
#                 Ref_Time, Jumpstart_Script, Startup_Script, Shutdown_Script, 
#                 Test_Mode, Limit_Qty, Fake_MOQs, Fake_Balances, Fake_Prices, 
#                 Fake_Fees, Multi_Processing, Place_Concurrent_Orders, 
#                 Limit_Arbitrages, iteration, Min_Bal, liquid_factor, Attempts, 
#                 Attempts, Coins, Fiat])
                 
Saved_Variables.close()

    
#with open('Saved_Variables.pkl') as f:  # Python 3: open(..., 'rb')
#    Exchanges, Permuatations, Opportunities, Current_Arbs,
#    Removed_Exchanges, Successful_Arbs, Profits, Target_Profit,
#    Ref_Time, Jumpstart_Script, Startup_Script, Shutdown_Script, 
#    Test_Mode, Limit_Qty, Fake_MOQs, Fake_Balances, Fake_Prices, 
#    Fake_Fees, Multi_Processing, Place_Concurrent_Orders, 
#    Limit_Arbitrages, iteration, Min_Bal, liquid_factor, Attempts, 
#    Attempts, Coins, Fiat = pickle.load(f)