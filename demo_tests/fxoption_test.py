import time

import numpy as np

from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.instruments.fx_vanilla_option import FXVanillaOption


fxoption = FXVanillaOption(trade_date=TuringDate(2015, 1, 1),
                          maturity_date=TuringDate(2015, 1, 1).addMonths(4),
                           cut_off_date=TuringDate(2015, 4, 15),
                           value_date=TuringDate(2015, 1, 1),
                           ccy1_cc_rate=0.11,
                           ccy2_cc_rate=0.08,
                           volatility=0.1411,
                           currency_pair="EURUSD",
                           spot_fx_rate=1.60,
                           strike_fx_rate=1.60,
                           notional=1000000,
                           option_type=TuringOptionTypes.EUROPEAN_CALL,
                           premium_currency="USD",
                           spot_days=2)

# value = fxoption.price()
# delta = fxoption.delta()
for spotFXRate in np.arange(100, 200, 10)/100.0:
    fxoption.spot_fx_rate = spotFXRate

    value = fxoption.price()
    valuemc = fxoption.price_mc()
    fxoption.market_price = value
    impliedVol = fxoption.implied_volatility()

    print(spotFXRate, value, valuemc, impliedVol)
