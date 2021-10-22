from pprint import pprint

from fundamental.turing_db.data import Turing, TuringDB


# exchange_rate = Turing.get_exchange_rate(symbols=['USD/CNY'])
# exchange_rate_history = Turing.get_exchange_rate_history(
#     symbols=['USD/CNY'], start='2021-09-01', end='2021-09-13')
# stock_price_history = Turing.get_market_stock_price_history(
#     symbols=['600067.SH'], start='2021-09-01', end='2021-09-13')
# stock_price = Turing.get_market_stock_price(symbols=['600067.SH'])
# iuir_curve = Turing.get_iuir_curve(
#     symbols=['USD/CNY'], curve_type='Shibor3M_tr', spot_rate_type='central')
# volatility_curve = Turing.get_volatility_curve(symbols=['USD/CNY'],
#                                                volatility_type=['ATM', '25D CALL', '25D PUT', '10D CALL', '10D PUT', '25D RR', '25D BF', '10D RR', '10D BF'])
# print(exchange_rate)
# print(exchange_rate_history)
# print(stock_price_history)
# print(stock_price)
# pprint(iuir_curve)
# pprint(volatility_curve)
from turing_models.utilities.turing_date import TuringDate

asset_id = 'FX00000001'  # USD/CNY
value_date = TuringDate(2021, 8, 20)
data = TuringDB.fx_implied_volatility_curve(asset_id=asset_id, volatility_type=["ATM", "25D BF", "25D RR", "10D BF", "10D RR"], date=value_date)[asset_id]
print(data)
data = TuringDB.irs_curve(curve_type="Shibor3M_tr", date=value_date)["Shibor3M_tr"]
print(data)
print(TuringDB.shibor_curve(date=value_date))
date = TuringDB.swap_curve(asset_id=['FX00000001', 'FX00000002'], date=value_date)
print(date['FX00000001'])
print(TuringDB.exchange_rate(symbol='USD/CNY', date=value_date))

