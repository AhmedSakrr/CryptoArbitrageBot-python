import Bitfinex5 as Bfx

def main():    

    pair1 = 'BTC'
    pair2 = 'USD'
    pair = pair1+pair2
    
    side = "sell"
    
    price = Bfx.Post(Bfx.Price(pair1, pair2)[side])
    
    size = '{0:f}'.format(0.00001)
    
    fee = Bfx.Post(Bfx.Fees())
    
    open_fee = fee[0]['taker_fees']
    close_fee = fee[0]['maker_fees']
    
    print 'Fee to open Order is', open_fee, '%'
    print 'Fee to close Order is', close_fee, '%'
    
    
    balance = [10] # Balance(Nonce())
    
    if not balance:
        print "You've got no fuckin money!"
    
    else:
        print "You're balance is ", balance[0]        
        Bfx.Send_Order(pair, size, price, side, Bfx.Nonce())




if __name__ == '__main__':
    main()