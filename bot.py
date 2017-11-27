# coding=utf-8

import ccxt, telebot
#from telebot import types

import cc_conf
import sys
from time import sleep

tbot = telebot.TeleBot(cc_conf.telegram_token)


##############################################################
#@tbot.message_handler(commands=['start'])
#def handle_start(message):
#    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
#    keyboard.add(*[types.KeyboardButton(name) for name in ['Уведомлять', 'Не уведомлять']])
#    tbot.send_message(message.chat.id, "Для получения информации нажмите клавишу.", reply_markup=keyboard)  
#    any_msg(message)

##############################################################
#@tbot.message_handler(content_types=['text'])
#def any_msg(call):
#    if call.text == u'Уведомлять':
#         msg = u'Уведомления включены\n'
#    else:
#        if call.text == u'Не уведомлять':
#            msg = u'Уведомления отключены\n'
#
#    tbot.send_message(call.chat.id, msg, parse_mode="HTML")

##############################################################
def init():
    print('ccbot ver 0.004a')
    print ('==================================================================')

##############################################################

def check_balance(exchange, coin):
    sleep(1/2)
    balance = exchange.fetchBalance()
    if balance.get(coin).get('free') < cc_conf.trade_balance:
        print('Недостаточно свободных средств для выставления ордера')
        return balance.get(coin).get('free') 
    else:
        return balance.get(coin).get('free')

##############################################################
# Возвращает:   0 - ничего не изменилось
#               1 - ордер исполнен
#              -1 - ордер удален
##############################################################

def check_order(exchange, id, pair, direction):
    #Направление торговли (излишне, но понятно)
    sell=0
    buy=1

    #Запрашиваем выставленные ордера
    try:
        sleep(1)
        orders = exchange.fetchOpenOrders(pair)

    except KeyboardInterrupt:
            print('Закрываем ордер')
            exchange.cancelOrder(id)
            sys.exit(2)

    except Exception as err:
        sleep(1.1)
        trades = exchange.fetchMyTrades(pair)
        for trade in trades:
            #Если находим ордер в истории торгов, то меняем направление торговли и даем сигнал на прерывание цикла 
            if trade['order'] == id:
                print('[+] Ордер ', id,' исполнен (1)')
                return 1
            else:             
                #Если ошибка вызвана отсутствием открытых ордеров, то даем сигнал на прерывание цикла
                if err.args[0]=='wex {"success":0,"error":"no orders"}':
                    print('Ордер отменен внешним воздействием.')
                    return -1
                else:
                    if err.args[0].find('invalid nonce parameter') >= 0 : 
                        print('Ошибка в значении nonce (3).')
                        sleep(1)
                    else:         
                        print('Ошибка (3): ', err) 
    try:                       
        for trade_order in orders:
            if trade_order['id'] == id:
                if trade_order['remaining'] <  trade_order['amount']:
                    print('Ордер исполнен частично, остаток:', trade_order['quantity'] , 'начальное количество :', trade_order['amount'])  
                else:
                    # если ордер еще не начал исполняться, то проверяем цену
                    orderbook = getOrderBook(exchange, pair)
                    if direction == buy:
                        bid = max(orderbook['bids'],key=lambda item: item[0])

                        if bid[0] > trade_order['price']:
                            # если цену нам перебили, снимаем ордер и даем сигнал на прерывание цикла
                            sleep(1/2)
                            exchange.cancelOrder( id )
                            print('[-] Изменение цены стакана ', trade_order['price'], '->', bid[0], 'ордер удален')
                            return -1
                    else:
                        ask = min(orderbook['asks'],key=lambda item: item[0])

                        if ask[0] < trade_order['price']:
                            # если цену нам перебили, снимаем ордер и даем сигнал на прерывание цикла
                            sleep(1/2)
                            exchange.cancelOrder( id )
                            print('[-] Изменение цены стакана ', trade_order['price'], '->', ask[0], 'ордер удален')
                            return -1

    except KeyboardInterrupt:
        print('Закрываем ордер')
        exchange.cancelOrder(id)
        sys.exit(2)

    except Exception as err:
        sleep(1)
        trades = exchange.fetchMyTrades(pair)
        for trade in trades:
            #Если находим ордер в истории торгов, то даем сигнал на прерывание цикла и изменение направления торговли
            if trade['order'] == id:
                print('[+] Ордер ', id,' исполнен (2)')
                return 1
                                      
        #Если ошибка вызвана отсутствием открытых ордеров, то даем сигнал на прерывание цикла отслеживания
        if err.args[0]=='wex {"success":0,"error":"no orders"}':
            return -1
                               
        if err.args[0].find('invalid nonce parameter') >= 0 : 
            print('Ошибка в значении nonce (2).')
            sleep(1)
        else:         
            print('Ошибка (2): ', err)                        

    return 0

##############################################################
def getOrderBook(exchange, pair):
    
    for check in range(10):
        try:
            orderbook = exchange.fetch_order_book (pair)
            break
        except KeyboardInterrupt:
            #tbot.send_message(call.chat.id, "Stopped by keyboard interrupt.", parse_mode="HTML")
            break
        except:
            err = sys.exc_info()[1]
            print(err.args[0])
            sleep(5)

    return orderbook

##############################################################
def main ():

    if cc_conf.exchange != 'wex' :
       print('Неизвестная науке биржа - ', cc_conf.exchange, '. Работа завершена.')
       sys.exit(-1)
    else:
        exchange = ccxt.wex({
            'apiKey': cc_conf.wex['apiKey'],
            'secret': cc_conf.wex['secret'],
            'verbose': False,
        })
    
    print ('Exchange: ', exchange.id ,'\n')
    
    coin_one = cc_conf.coin_one.upper() 
    coin_two = cc_conf.coin_two.upper()
    trade_pair = coin_one + '/' + coin_two
    print (trade_pair)
    
    if cc_conf.master_coin.upper() == coin_one:
        master_coin = coin_one
        slave_coin = coin_two
    else:
        master_coin = coin_two
        slave_coin = coin_one


    markets = exchange.load_markets()
    trade_precision = exchange.markets.get(trade_pair).get('precision').get('amount')
    trade_pair_fee = exchange.markets.get(trade_pair).get('info').get('fee')/100

    #Скорость торговли (кол-во запросов в секунду)
    trade_speed=0.5 

    #Направление торговли 
    sell=0
    buy=1
    
    trade_direction=buy  
    trade_cancelOrderFalg=False
    
    if cc_conf.coin_one.upper()  == exchange.markets[trade_pair]['base']:
        trade_buyVolume =  cc_conf.trade_balance
    else:
        trade_buyVolume = round(cc_conf.trade_balance/trade_buyPrice*(1-trade_pair_fee),trade_precision)

    while True:
    
        #tbot.polling(none_stop=False, interval=False, timeout=1)
        # !!! обязательно добавить проверку успешного исполнения функции

        orderbook = getOrderBook(exchange, trade_pair)

        bid = max(orderbook['bids'],key=lambda item: item[0])
        ask = min(orderbook['asks'],key=lambda item: item[0])
        spread = (ask[0] - bid[0])/ask[0]
        spread_percent = spread  * 100

        print ('Спред:', '{0:.2f}%'.format(spread_percent),' ', '{0:.4f}'.format(ask[0] - bid[0]), slave_coin ,'\t Покупка/продажа', '{0:.4f}'.format(ask[0]),' / ', '{0:.4f}'.format(bid[0]),'\t',  orderbook['datetime'] )

        #Проверяем направление торговли, если покупки не было
        if trade_direction == buy:

            #проверяем профитность спреда.
            if ( (spread - trade_pair_fee*2) < cc_conf.profit_percent/100 ) and (trade_direction==buy)  :                
                try:
                    sleep(1/trade_speed)
                except KeyboardInterrupt:
                    print('Работа завершена.')
                    break
                continue
            
            #Если сред позволяет рассчитаем цену покупки
            trade_buyPrice = round(bid[0] + cc_conf.trade_offset/(10**trade_precision),trade_precision)
                
            #Если позволяет баланс выставим ордер на покупку
            if check_balance(exchange, slave_coin) > 0:
                # print('Выставим ордер на покупку ', master_coin)
                sleep(1)
                #exchange.markets.get(trade_pair).get('info').get('min_amount')
               
                try:
                    trade_buyOrder = exchange.createLimitBuyOrder(trade_pair, trade_buyVolume, trade_buyPrice )
                    sleep(1)
                except Exception as err: 
                    print('Ошибка (1): ', err)
                    break

                print('[>] Создан ордер ', trade_buyOrder['id'] ,' на покупку ', round(trade_buyOrder['amount'],trade_precision), master_coin, ' за ', round(trade_buyOrder['amount']*trade_buyOrder['price'],trade_precision) ,slave_coin, ' по цене ', trade_buyOrder['price'])

                # отслеживание ордера
                while True and trade_direction == buy:
                    trade_checkOrder = check_order(exchange, trade_buyOrder['id'], trade_pair, trade_direction)
                    if trade_checkOrder == 1:
                        trade_direction = sell
                        break
                    else:
                        if trade_checkOrder== -1:
                            break
                    sleep(1)
            trade_buy = round(trade_buyOrder['amount']*trade_buyOrder['price'],trade_precision) 
        
        # if trade_direction == buy:
        else:  
            trade_sellPrice = round(ask[0] - cc_conf.trade_offset/(10**trade_precision),trade_precision)
            trade_sellVolume = 0
            trades = exchange.fetchMyTrades(trade_pair)
            for trade in trades:
                if trade_buyOrder['id'] == trade['order']:
                    trade_sellVolume = trade_sellVolume + trade['amount']


            if trade_sellVolume > 0:
                # print('Выставим ордер на продажу ', master_coin)
                #!!! добавить проверку на минимальный размер ордера
                
                sleep(1)
                trade_sellOrder = exchange.createLimitSellOrder(trade_pair, trade_sellVolume, trade_sellPrice )
                #trade_direction = sell
                print('[<] Создан ордер ', trade_sellOrder['id'] ,' на продажу ', trade_sellVolume, master_coin,  ' за ', round(trade_sellOrder['amount']*trade_sellOrder['price'],trade_precision) ,slave_coin, ' по цене ', trade_sellPrice) 
            else:
                print('Недостаточно ', master_coin,  ' для торговли')  
            
            # отслеживание ордера
            while True and trade_direction == sell:
                trade_checkOrder = check_order(exchange, trade_sellOrder['id'], trade_pair, trade_direction)
                if trade_checkOrder == 1:
                    trade_direction = buy
                    trade_sell=round(trade_sellOrder['amount']*trade_sellOrder['price'],trade_precision) 
                    print('[х] Profit : ', '{0:.2f}'.format(((trade_sell-trade_buy)/trade_buy)*100), '%  ', '{0:.5f}'.format(trade_sell-trade_buy), slave_coin)
                    break
                else:
                    if trade_checkOrder == -1:
                        break
            sleep(1)

        try:
            sleep(1/trade_speed)
        except KeyboardInterrupt:
#            tbot.send_message(call.chat.id, "Stopped by keyboard interrupt.", parse_mode="HTML")
            sys.exit(2)
 
##############################################################

#tbot.polling(none_stop=False)
if __name__ == '__main__': 

    init()    
    main()
