import time

import numpy as np

from turing_models.instruments.common import Currency
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.instruments.fx_vanilla_option import FXVanillaOption
from turing_models.market.data.china_money_yield_curve import dates, rates
from turing_models.utilities.global_types import TuringOptionType, TuringExerciseType


fxoption = FXVanillaOption(trade_date=TuringDate(2015, 1, 1),
                           expiry=TuringDate(2015, 1, 1).addMonths(4),
                           cut_off_time=TuringDate(2015, 4, 15),
                           delivery_date=TuringDate(2015, 1, 1).addMonths(4),
                           value_date=TuringDate(2015, 1, 1),
                           volatility=0.1411,
                           currency_pair="EUR/USD",
                           exchange_rate=1.60,
                           strike=1.60,
                           notional=1000000,
                           notional_currency=Currency.USD,
                           option_type=TuringOptionType.CALL,
                           exercise_type=TuringExerciseType.EUROPEAN,
                           premium_currency=Currency.USD,
                           tenors=dates,
                           ccy1_cc_rates=rates,
                           ccy2_cc_rates=rates)

price = fxoption.price()
delta = fxoption.fx_delta()
gamma = fxoption.fx_gamma()
vega = fxoption.fx_vega()
theta = fxoption.fx_theta()
vanna = fxoption.fx_vanna()
volga = fxoption.fx_volga()
print(price, delta, gamma, vega, theta, vanna, volga)
# for spotFXRate in np.arange(100, 200, 10)/100.0:
#     fxoption.spot_fx_rate = spotFXRate

#     value = fxoption.price()
#     valuemc = fxoption.price_mc()
#     fxoption.market_price = value
#     impliedVol = fxoption.implied_volatility()

#     print(spotFXRate, value, valuemc, impliedVol)
