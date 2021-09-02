import time

import numpy as np

from turing_models.instruments.common import Currency
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.instruments.fx_vanilla_option import FXVanillaOption
from turing_models.market.data.china_money_yield_curve import dates, rates
from turing_models.utilities.global_types import TuringOptionType, TuringExerciseType

vol_tenors = ['1M', '2M', '3M', '6M', '1Y', '2Y']
atm_vols = [21.00, 21.00, 20.750, 19.400, 18.250, 17.677]
butterfly_25delta_vols = [0.65, 0.75, 0.85, 0.90, 0.95, 0.85]
risk_reversal_25delta_vols = [-0.20, -0.25, -0.30, -0.50, -0.60, -0.562]
butterfly_10delta_vols = [2.433, 2.83, 3.228, 3.485, 3.806, 3.208]
risk_reversal_10delta_vols = [-1.258, -1.297, -1.332, -1.408, -1.359, -1.208]

fxoption = FXVanillaOption(start_date=TuringDate(2015, 1, 1),
                           expiry=TuringDate(2015, 1, 1).addMonths(4),
                           cut_off_time=TuringDate(2015, 4, 15),
                           delivery_date=TuringDate(2015, 1, 1).addMonths(4),
                           value_date=TuringDate(2015, 1, 1),
                           #    volatility=0.1411,
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
                           ccy2_cc_rates=rates,
                           vol_tenors=vol_tenors,
                           atm_vols=atm_vols,
                           butterfly_25delta_vols=butterfly_25delta_vols,
                           risk_reversal_25delta_vols=risk_reversal_25delta_vols,
                           butterfly_10delta_vols=butterfly_10delta_vols,
                           risk_reversal_10delta_vols=risk_reversal_10delta_vols)

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
