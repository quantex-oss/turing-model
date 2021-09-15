from pprint import pprint

from fundamental.turing_db.data import Turing


exchange_rate = Turing.get_exchange_rate(symbols=['USD/CNY'])
exchange_rate_history = Turing.get_exchange_rate_history(symbols=['USD/CNY'], start='2021-09-01', end='2021-09-13')
# stock_price_history = Turing.get_market_stock_price_history(symbols=['600067.SH'], start='2021-09-01', end='2021-09-13')
stock_price = Turing.get_market_stock_price(symbols=['600067.SH'])
iuir_curve = Turing.get_iuir_curve(symbols=['USD/CNY'], curve_type='Shibor3M', spot_rate_type='central')
volatility_curve = Turing.get_volatility_curve(symbols=['USD/CNY'],
                                               volatility_type=['ATM', '25D CALL', '25D PUT', '10D CALL', '10D PUT', '25D RR', '25D BF', '10D RR', '10D BF'])
print(exchange_rate)
print(exchange_rate_history)
# print(stock_price_history)
print(stock_price)
pprint(iuir_curve)
pprint(volatility_curve)
