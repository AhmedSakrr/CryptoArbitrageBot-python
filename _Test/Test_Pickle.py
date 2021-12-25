import pickle

#Saved_Variables = [Exchanges, Permuatations, Opportunities, Current_Arbs,
#                   Removed_Exchanges, Successful_Arbs, Profits, Target_Profit, 
#                   Ref_Time, Jumpstart_Script, Startup_Script, Shutdown_Script,
#                   Test_Mode, Limit_Qty, Fake_MOQs, Fake_Balances, Fake_Prices, 
#                   Fake_Fees, Multi_Processing, Place_Concurrent_Orders, 
#                   Limit_Arbitrages, iteration, Min_Bal, liquid_factor, Attempts,
#                   Coins, Fiat, Total_Profit]
#
#
#with open('Saved_Variables.pkl', 'w') as f:
#    pickle.dump(Saved_Variables, f)



with open('Saved_Variables.pkl') as f:
    [Exchanges, Permuatations, Opportunities, Current_Arbs,
     Removed_Exchanges, Successful_Arbs, Profits, Target_Profit, 
     Ref_Time, Jumpstart_Script, Startup_Script, Shutdown_Script,
     Test_Mode, Limit_Qty, Fake_MOQs, Fake_Balances, Fake_Prices, 
     Fake_Fees, Multi_Processing, Place_Concurrent_Orders, 
     Limit_Arbitrages, iteration, Min_Bal, liquid_factor, Attempts,
     Coins, Fiat, Total_Profit] = pickle.load(f)
    
    
    
