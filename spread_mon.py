# coding=utf-8

import ccxt
import cc_conf
import sys
from time import sleep

#==================================================================================
def init():
    print('spread monitor ver 0.002a')
    print ('==================================================================')
    print ("exchange" ,'\t', "market", '\t','spread %','\t', "bid price",'\t', "bid vol",'\t', "ask price",'\t', "ask vol",'\t', "spread" ,'\t',  "datetime")
            

#==================================================================================

def main():

    exchange=[]

    exchange.append(ccxt.wex({'verbose': False}))
    exchange.append(ccxt.okcoinusd({'verbose': False}))

    while True:
        for ex in exchange:
            try:
                ex.loadMarkets()
            except KeyboardInterrupt:
                return 1
            except:
                err = sys.exc_info()[1]
                print(err.args[0])
                continue

            for market in ex.markets:
                try:
                    orderbook = ex.fetch_order_book(market)
                except KeyboardInterrupt:
                    return 1
                except:
                    err = sys.exc_info()[1]
                    print(err.args[0])
                    continue

                bid = max(orderbook['bids'],key=lambda item: item[0])
                if bid[0] < 1 :
                    continue
                ask = min(orderbook['asks'],key=lambda item: item[0])

                spread = (ask[0] - bid[0])
                spread_percent = spread / ask[0] * 100

                print (ex.id , market,'\t','{0:.2f}%'.format(spread_percent),'\t', bid[0],'\t', bid[1],'\t', ask[0],'\t', ask[1],'\t', spread ,'\t',  orderbook['datetime'] )
            
            print ('end', ex.id, '==================================================================')
            
        print ('***')
        sleep(30)


#==================================================================================
init()
main()
