import ccxt
import cc_conf
import sys
from time import sleep

print('begin')
ex = ccxt.poloniex({'verbose': False})

if not ex.hasFetchOHLCV:
    sys.exit(-1)

while True:
    
    OHLV = ex.fetch_ohlcv('DASH/USDT', '5m')
    print ( OHLV )
    sleep(5)


