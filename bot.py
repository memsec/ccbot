# coding=utf-8

import ccxt
import cc_conf
from time import sleep

#==================================================================================
def init():
    print('ccbot ver 0.001a')
    print ('==================================================================')

#==================================================================================

def main ():

    exchange=[]

    exchange.append(ccxt.exmo({
        'apiKey': cc_conf.exmo['apiKey'],
        'secret': cc_conf.exmo['secret'],
        'verbose': False,
    }))

    exchange.append(ccxt.okcoinusd({
        'apiKey': cc_conf.okcoin['apiKey'],
        'secret': cc_conf.okcoin['secret'],
        'verbose': False,
    }))

    exchange.append(ccxt.bitfinex({
        'apiKey': cc_conf.bitfinex['apiKey'],
        'secret': cc_conf.bitfinex['secret'],
        'verbose': False,
    }))

    exchange.append(ccxt.kraken({
        'apiKey': cc_conf.kraken['apiKey'],
        'secret': cc_conf.kraken['secret'],
        'verbose': False,
    }))

    debug_output = True

    while True:
        for ex in exchange :
            orderbook = ex.fetch_order_book (cc_conf.coin_one + '/' + cc_conf.coin_two)
            bid = max(orderbook['bids'],key=lambda item: item[0])
            ask = min(orderbook['asks'],key=lambda item: item[0])

            spread = (ask[0] - bid[0])
            spread_percent = spread / ask[0] * 100

            if debug_output :
                 print ex.id , bid[0], bid[1], ask[0], ask[1], spread , '{0:.2f}%'.format(spread_percent), orderbook['datetime']
            else:
                 print ex.id, '{ bid :', bid, 'ask :', ask, 'spread :', spread , '({0:.2f}%)'.format(spread_percent) ,'}'

            #datetime
        print ('==================================================================')
        sleep(60)


#==================================================================================
init()
main()
