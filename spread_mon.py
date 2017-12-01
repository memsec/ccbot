# coding=utf-8

import ccxt
import cc_conf
import sys
from time import sleep

#==================================================================================
def init():
    print('spread monitor ver 0.01b')
            

#==================================================================================

def main():

    exchange=[]

    exchange.append(ccxt.wex({'verbose': False}))
    exchange.append(ccxt.okcoinusd({'verbose': False}))
    
    if len (sys.argv) > 1:
        filter = str(sys.argv[1]).upper()
    else:
        filter = ''

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

            print ('===> begin {:<12}'.format(ex.id) ,'<========================================================================================================')
            print ('  market   spread %        bid price          bid vol     ask price           ask vol        spread            datetime')
            print ("---------------------------------------------------------------------------------------------------------------------------------")

            for market in ex.markets:
                if len(filter) != 0 and (ex.markets[market]['quote'] != filter and ex.markets[market]['base'] != filter):
                    continue
                try:
                    orderbook = ex.fetch_order_book(market)
                    ticker = ex.fetch_ticker(market)
                    quoteVolume = ticker['quoteVolume']
                    baseVolume = ticker['baseVolume']
                    
                    if type(quoteVolume)  != float:
                        quoteVolume  = 0

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

                print ( '{:>10}'.format(market),'{0:>5.2f}%'.format(spread_percent),'\t', '{0:>10.2f}'.format(bid[0]),'\t', '{0:>12.2f}'.format(baseVolume),'\t', '{0:>10.2f}'.format(ask[0]),'\t', '{0:>12.2f}'.format(quoteVolume),'\t', '{0:>10.2f}'.format(spread ),'\t',  '{:<.16}'.format(orderbook['datetime']) )
            
            print ('===> end', '{:<12}'.format(ex.id) , '<==========================================================================================================\n')
            
        print ('***')
        sleep(30)


#==================================================================================
init()
main()
