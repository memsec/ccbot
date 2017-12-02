# coding=utf-8
import ccxt
import telebot 
from telebot import types
import cc_conf
import sys
from time import sleep

# Инициализация переменной для общей статистики торгов
trade_summ_buy  = 0
trade_summ_sell = 0

pause = False

#Направление торговли 
sell=0
buy=1

if cc_conf.master_coin.upper() == cc_conf.coin_one.upper() :    
    trade_direction=buy  
else:
    trade_direction=sell 

trade_exit=False

tbot = telebot.TeleBot(cc_conf.telegram_token)

updates = tbot.get_updates()

try:
    for update in updates:
        if int(update.update_id) > int(tbot.last_update_id):
            tbot.last_update_id = update.update_id
except Exception as ex:
    print(traceback.format_exc())

update_offset = tbot.last_update_id



def msg(self):
    print(self)
    tbot.send_message(cc_conf.telegram_id, self)



def init():
    message = 'ccbot v. 0.03b запущен'
    print(message)
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*[types.KeyboardButton(name) for name in ['Пауза', 'Стоп', 'Стоп после цикла', 'Удалить ордера','Информация' ]])
    msg = tbot.send_message(cc_conf.telegram_id, message, reply_markup=keyboard)

    print ('==================================================================')



def check_balance(exchange, coin):
    sleep(1/2)
    balance = exchange.fetchBalance()
    if balance.get(coin).get('free') < cc_conf.trade_balance:
        msg('[!] Недостаточно свободных средств для выставления ордера. Работа завершена')
        sys.exit(2)
    else:
        return balance.get(coin).get('free')

#------------------------------------------------------------------
# Возвращает:   0 - ничего не изменилось
#               1 - ордер исполнен
#              -1 - ордер удален
#------------------------------------------------------------------

def check_order(exchange, id, pair, direction):
    
    sleep(2)

    poll_result = polling()

    # сигнал на немедленный выход
    if poll_result == -1:
        sleep(1)
        try:
            exchange.cancelOrder( id )
        except Exception as err:
            message = 'Невозможно закрыть ордер. Ошибка: '+ err
            tbot.send_message(cc_conf.telegram_id, message)
            sys.exit(-1)
        
        msg('Ордер '+ id +' закрыт. Работа завершена.')       
        sys.exit(2)
    
    # сигнал на закрытие ордера
    if poll_result == 3:
        try:
            exchange.cancelOrder( id )
            msg('Ордер '+ id +' закрыт.')  
        except Exception as err:
            msg('Невозможно закрыть ордер. Ошибка: '+ err)
          
        return -1

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
        
        #Если ошибка вызвана отсутствием открытых ордеров, то даем сигнал на прерывание цикла
        if err.args[0].find('no orders') > 0:
            print('Ордер отменен внешним воздействием (1).')
            return -1
       
        if err.args[0].find('invalid nonce parameter') >= 0 : 
            print('Ошибка в значении nonce (1).')
            sleep(1)
        else:         
            if err.args[0].find('502 Bad Gateway') >= 0 : 
                print('Ошибка 502 Bad Gateway.')
                sleep(1)
                return 0    
            else:
                print('Ошибка (3): ', err) 
                return 0
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
                            ticker = exchange.fetch_ticker(pair)
                            if ticker['last'] < trade_order['price']:
                                arrow=chr(8595)
                            else:
                                if ticker['last'] > trade_order['price']:
                                    arrow=chr(8593)

                            msg('['+arrow+'] Изменение цены '+ str(trade_order['price']) + '->'+ str(bid[0])+ ' ордер удален')
                            return -1
                    else:
                        ask = min(orderbook['asks'],key=lambda item: item[0])

                        if ask[0] < trade_order['price']:
                            # если цену нам перебили, снимаем ордер и даем сигнал на прерывание цикла
                            sleep(1/2)
                            exchange.cancelOrder( id )
                            ticker = exchange.fetch_ticker(pair)
                            if ticker['last'] < trade_order['price']:
                                arrow=chr(8595)
                            else:
                                if ticker['last'] > trade_order['price']:
                                    arrow=chr(8593)

                            msg( '[' + arrow +'] Изменение цены '+ str(trade_order['price']) + '->' + str(ask[0]) + ' ордер удален.\n    Цена покупки ' + str(trade_buyPrice) + ' отклонение '+  str(round(trade_buyPrice-ask[0],trade_precision)) +' '+ slave_coin)
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
        if err.args[0].find('no orders') > 0:
            return -1
                               
        if err.args[0].find('invalid nonce parameter') >= 0 : 
            print('Ошибка в значении nonce (2).')
            sleep(1)
        else:         
            print('Ошибка (2): ', err)                        

    return 0


def getOrderBook(exchange, pair):
    
    for check in range(10):
        try:
            orderbook = exchange.fetch_order_book (pair)
            break
        except KeyboardInterrupt:
            break
        except Exception as err: 
            print('Ошибка (0): ', err)
            sleep(5)

    return orderbook


def process_message(self):
    text = self.message.text
    text = text.strip()
    
    global pause

    if text == 'Стоп':
        return -1
       
    if text == u'Стоп после цикла':
        if trade_direction==buy:
            message = u'Завершаем работу.\n'
        else:
            message = u'Жду исполнения профитного ордера.\n'
            tbot.send_message(cc_conf.telegram_id, message)
            trade_exit=True
        return -2

    if text == u'Информация':
        message ='Итого \n куплено: '+str(round(trade_summ_buy,trade_precision))+slave_coin+'\n продано: '+str(round(trade_summ_sell,trade_precision))+slave_coin+'\n дельта : '+str(round(trade_summ_sell-trade_summ_buy,trade_precision)) + '\n Спред : ' + str(round(spread_percent,2)) +'% ('+ str(round(spread,trade_precision)) + slave_coin +')\n Пауза = '+ str(pause)
        tbot.send_message(cc_conf.telegram_id, message)
        message =''
        return 0
    
    if text == 'Удалить ордера':
        return 3

    if text == 'Пауза':
        if pause:
            pause = False
            tbot.send_message(cc_conf.telegram_id, 'Работа возобновлена')
        else:
            pause = True
            tbot.send_message(cc_conf.telegram_id, 'Пауза')
        return 2

    return 0

def polling():

    result = 0
  
    while True:
        updates = tbot.get_updates()
  
        try:
            for update in updates:
                if int(update.update_id) > int(tbot.last_update_id):
                    tbot.last_update_id = update.update_id
                    result = process_message(update)

        except Exception as ex:
            print(ex)
        
        return result
        
        ##Проверим не стоит ли бот на паузе?
        #if not pause or result == -1:
        #    # Если не пауза, то выходим мз функции, иначе продолжаем цикл
        #    return result
        #if result == 3:
        #    print('---')
        #sleep(1)

def main (update_offset):

    global trade_summ_buy
    global trade_summ_sell
    global trade_direction  
    global trade_exit

    global slave_coin
    global spread_percent 
    global spread
    global trade_precision 
    global trade_lastPrice
    global trade_buyPrice

    
    # Скорость торговли (кол-во запросов в секунду)
    trade_speed=0.5 

    if cc_conf.exchange != 'wex' :
       msg('Неизвестная биржа - '+ cc_conf.exchange+ '. Работа завершена.')
       sys.exit(-1)
    else:
        exchange = ccxt.wex({
            'apiKey': cc_conf.wex['apiKey'],
            'secret': cc_conf.wex['secret'],
            'verbose': False,
        })

    coin_one = cc_conf.coin_one.upper() 
    coin_two = cc_conf.coin_two.upper()
    trade_pair = coin_one + '/' + coin_two
    
    msg('Биржа: ' + exchange.id + '\nТорговая пара:'+ trade_pair)
    
    master_coin = coin_one
    slave_coin = coin_two

    markets = exchange.load_markets()
    trade_precision = exchange.markets.get(trade_pair).get('precision').get('amount')
    trade_pair_fee = exchange.markets.get(trade_pair).get('info').get('fee')/100

    if cc_conf.coin_one.upper()  == exchange.markets[trade_pair]['base']:
        trade_buyVolume =  cc_conf.trade_balance
    else:
        trade_buyVolume = round(cc_conf.trade_balance/trade_buyPrice*(1-trade_pair_fee),trade_precision)

    while True:

        sleep(1/trade_speed)
        orderbook = getOrderBook(exchange, trade_pair)

        bid = max(orderbook['bids'],key=lambda item: item[0])
        ask = min(orderbook['asks'],key=lambda item: item[0])
        spread = (ask[0] - bid[0])/ask[0]
        spread_percent = spread  * 100
        
        poll_result = polling() 

        if poll_result == -1:
            msg(u'Работа завершена (ё). \n')
            sys.exit(-1)
        
        if pause:
            print ('Спред:', '{0:.2f}%'.format(spread_percent),' ', '{0:.4f}'.format(ask[0] - bid[0]), slave_coin ,'\t Покупка/продажа', '{0:.4f}'.format(ask[0]),' / ', '{0:.4f}'.format(bid[0]),'\t',  orderbook['datetime'], 'Trade paused.' )
            sleep((1/trade_speed)*2)
            continue
        else:
            print ('Спред:', '{0:.2f}%'.format(spread_percent),' ', '{0:.4f}'.format(ask[0] - bid[0]), slave_coin ,'\t Покупка/продажа', '{0:.4f}'.format(ask[0]),' / ', '{0:.4f}'.format(bid[0]),'\t',  orderbook['datetime'] )
        
        #Проверяем направление торговли, если покупки не было
        if trade_direction == buy:

            if poll_result == -2:
                msg( '[*] Цикл окончен, работа завершена.' )
                sys.exit(2)

            #проверяем профитность спреда.
            if ( (spread - trade_pair_fee*2) < cc_conf.profit_percent/100 ) and (trade_direction==buy)  :                
                try:
                    sleep(1/trade_speed)
                except KeyboardInterrupt:
                    print('[*] Работа завершена.')
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

                msg('['+ chr(9650)+'] Создан ордер ' + trade_buyOrder['id'] + ' на покупку ' + str(round(trade_buyOrder['amount'],trade_precision)) + master_coin + ' за ' + str(round(trade_buyOrder['amount']*trade_buyOrder['price'],trade_precision)) + slave_coin + ' по цене ' + str(trade_buyOrder['price']) )

                # отслеживание ордера
                while True and trade_direction == buy:
                    trade_checkOrder = check_order(exchange, trade_buyOrder['id'], trade_pair, trade_direction)
                    if trade_checkOrder == 1:
                        msg('[+] Ордер ' + trade_buyOrder['id'] + ' исполнен.')
                        
                        # Если была команда завершить после полного цикла и это обратный цикл, завершаем работу.
                        if trade_exit and cc_conf.coin_one.upper() == exchange.markets[trade_pair]['base']:
                            msg('Цикл окончен, работа завершена.')
                            sys.exit(2)
                        
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
            
            try:
                trades = exchange.fetchMyTrades(trade_pair)
                for trade in trades:
                    if trade_buyOrder['id'] == trade['order']:
                        trade_sellVolume = trade_sellVolume + trade['amount']
            except: 
                trade_sellVolume=cc_conf.trade_balance

            if trade_sellVolume > 0:
                #!!! добавить проверку на минимальный размер ордера
                
                sleep(1)
                trade_sellOrder = exchange.createLimitSellOrder(trade_pair, trade_sellVolume, trade_sellPrice )
                msg('['+ chr(9660)+'] Создан ордер '+ trade_sellOrder['id'] +' на продажу '+ str( trade_sellVolume) + master_coin + ' за ' + str(round(trade_sellOrder['amount']*trade_sellOrder['price'],trade_precision)) + slave_coin + ' по цене '+ str(trade_sellPrice))
            else:
                print('Недостаточно ', master_coin,  ' для торговли')  
            
            # отслеживание ордера
            while True and trade_direction == sell:
                trade_checkOrder = check_order(exchange, trade_sellOrder['id'], trade_pair, trade_direction)
                if trade_checkOrder == 1:
                    trade_direction = buy
                    msg('[+] Ордер '+ trade_sellOrder['id']+' исполнен.')

                    trade_sell=round(trade_sellOrder['amount']*trade_sellOrder['price'],trade_precision) 
                    
                    trade_summ_buy  = trade_summ_buy + trade_buy
                    trade_summ_sell = trade_summ_sell + trade_sell

                    print('[х] Профит сделки  : ', '{0:.2f}'.format(((trade_sell-trade_buy)/trade_buy)*100), '%  ', '{0:.5f}'.format(trade_sell-trade_buy), slave_coin)
                    print('[=] Итого за сессию: ', '{0:.2f}'.format(((trade_summ_sell-trade_summ_buy)/trade_summ_buy)*100), '%  ', '{0:.5f}'.format(trade_summ_sell-trade_summ_buy), slave_coin)
                    print('            куплено: ', '{0:.5f}'.format(trade_summ_buy), slave_coin, 'продано: ', '{0:.5f}'.format(trade_summ_sell), slave_coin)
                    
                    message = '[х] Профит сделки  : ' +  str(round(((trade_sell-trade_buy)/trade_buy)*100,trade_precision)) + '%  ' + str(round(trade_sell-trade_buy,trade_precision)) + slave_coin
                    tbot.send_message(cc_conf.telegram_id, message)

                    message ='[=] Итого \n куплено: '+str(round(trade_summ_buy,trade_precision))+slave_coin+'\n продано: '+str(round(trade_summ_sell,trade_precision))+slave_coin+'\n дельта :'+str(round(trade_summ_sell-trade_summ_buy,trade_precision))
                    tbot.send_message(cc_conf.telegram_id, message)
                    message =''

                    # Если была команда завершить после полного цикла и это прямой цикл завершаем работу.
                    if trade_exit and cc_conf.coin_one.upper() == exchange.markets[trade_pair]['base']:
                        msg('Цикл окончен, работа завершена.')
                        sys.exit(2)

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
 


#tbot.polling(none_stop=False)
if __name__ == '__main__': 

    init()    
    main(update_offset)
