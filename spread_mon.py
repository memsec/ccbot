# coding=utf-8

import ccxt
import cc_conf
from time import sleep

#==================================================================================
def init():
    print('spread monitor ver 0.002a')
    print ('==================================================================')
    print ("exchange" , "market", '\t', "bid price",'\t', "bid vol",'\t', "ask price",'\t', "ask vol",'\t', "spread" ,'\t', 'spread %','\t', "datetime")
            

#==================================================================================

def main():

    exchange=[]

    exchange.append(ccxt.exmo({'verbose': False}))
    exchange.append(ccxt.okcoinusd({'verbose': False}))
    exchange.append(ccxt.wex({'verbose': False}))

    while True:
        for ex in exchange:
            try:
                ex.loadMarkets()
            except:
                print("Error loadMarkets!")
                continue

            for market in ex.markets:
 
                orderbook = ex.fetch_order_book(market)
                bid = max(orderbook['bids'],key=lambda item: item[0])
                ask = min(orderbook['asks'],key=lambda item: item[0])

                spread = (ask[0] - bid[0])
                spread_percent = spread / ask[0] * 100

                print (ex.id , market, '\t', bid[0],'\t', bid[1],'\t', ask[0],'\t', ask[1],'\t', spread ,'\t', '{0:.2f}%'.format(spread_percent),'\t', orderbook['datetime'] )
            
            print ('end', ex.id, '==================================================================')
            
        print ('***')
        sleep(30)


#==================================================================================
init()
main()
