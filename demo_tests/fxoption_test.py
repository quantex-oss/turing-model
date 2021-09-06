import time

import numpy as np

from turing_models.instruments.common import Currency
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.instruments.fx_vanilla_option import FXVanillaOption
# from turing_models.market.data.china_money_yield_curve import dates, rates
from turing_models.utilities.global_types import TuringOptionType, TuringExerciseType

vol_tenors = [0.083, 0.167, 0.25, 0.5, 1, 2]
atm_vols = [0.21, 0.21, 0.2075, 0.194, 0.1825, 0.17677]
butterfly_25delta_vols = [0.0065, 0.0075, 0.0085, 0.0090, 0.0095, 0.0085]
risk_reversal_25delta_vols = [-0.002, -
                              0.0025, -0.003, -0.005, -0.006, -0.00562]
butterfly_10delta_vols = [0.02433, 0.0283, 0.03228, 0.03485, 0.03806, 0.03208]
risk_reversal_10delta_vols = [-0.01258, -
                              0.01297, -0.01332, -0.01408, -0.01359, -0.01208]

fxoption = FXVanillaOption(start_date=TuringDate(2021, 9, 1),
                           # expiry=TuringDate(2015, 1, 1).addMonths(4),
                           cut_off_time=TuringDate(2021, 9, 30),
                           delivery_date=TuringDate(2021, 9, 30),
                           # value_date=TuringDate(2015, 1, 1),
                           #    volatility=0.1411,
                           underlier_symbol="USD/CNY",
                           exchange_rate=6.4683,
                           strike=6.8,
                           notional=1000000,
                           notional_currency=Currency.CNY,
                           option_type=TuringOptionType.CALL,
                           exercise_type=TuringExerciseType.EUROPEAN,
                           premium_currency=Currency.CNY,
                           tenors=[0.003, 0.021, 0.042, 0.0625, 0.083, 0.17, 0.25, 0.5, 0.75, 1, 1.5, 2, 3],
                           ccy1_cc_rates= [-0.000103, 0.001039, 0.001343, 0.000648, -0.008079, -0.0051, -0.003319, -0.001638, 0.00122, 0.002257, 0.002997, 0.004634, 0.008593],
                           ccy2_cc_rates= [0.022254, 0.023537, 0.023917, 0.023754, 0.023586, 0.023708, 0.023826, 0.024919, 0.026622, 0.027007, 0.026492, 0.027222, 0.028544],
                           # vol_tenors=vol_tenors,
                           # atm_vols=atm_vols,
                           # butterfly_25delta_vols=butterfly_25delta_vols,
                           # risk_reversal_25delta_vols=risk_reversal_25delta_vols,
                           # butterfly_10delta_vols=butterfly_10delta_vols,
                           # risk_reversal_10delta_vols=risk_reversal_10delta_vols
                           )

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
