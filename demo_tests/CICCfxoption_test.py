import time

import numpy as np
import pandas as pd
from turing_models.instruments.common import Currency, CurrencyPair
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.instruments.fx.fx_vanilla_option_CICC import FXVanillaOptionCICC
# from turing_models.market.data.china_money_yield_curve import dates, rates
from turing_models.utilities.global_types import TuringOptionType, TuringExerciseType

mkt_file = '/home/turing/workspace/turing-model/turing_models/market/data/market data 20210420.xlsx'

USDLibor3M_data = pd.read_excel(mkt_file, 'USDLibor3M')
dom_rates = [x / 100 for x in USDLibor3M_data['Rate'].values.tolist()]
tenors = USDLibor3M_data['Tenor'].values.tolist()
fwd_data = pd.read_excel(mkt_file, 'EURUSD_Futures')
fwd_tenors = fwd_data['Tenor'].values.tolist()
fwd_quotes = [x / 10000 for x in fwd_data['Spread'].values.tolist()]
vol_data = pd.read_excel(mkt_file, 'EURUSD_vols')


vol_tenors = vol_data['Tenor'].values.tolist()
atm_vols = vol_data['ATM'].values.tolist()
butterfly_25delta_vols = vol_data['25DBF'].values.tolist()
risk_reversal_25delta_vols = vol_data['25DRR'].values.tolist()
butterfly_10delta_vols = vol_data['10DBF'].values.tolist()
risk_reversal_10delta_vols = vol_data['10DRR'].values.tolist()

fxoption = FXVanillaOptionCICC(start_date=TuringDate(2021, 4, 20),
                               expiry=TuringDate(2021, 7, 20),
                               cut_off_time=TuringDate(2021, 7, 20),
                               #    delivery_date=TuringDate(2021, 7, 20),
                               value_date=TuringDate(2021, 4, 20),
                               underlier='FX00000001',
                               underlier_symbol=CurrencyPair.EURUSD,
                               exchange_rate=1.2036,
                               strike=1.2036,
                               notional=1,
                               notional_currency=Currency.USD,
                               option_type=TuringOptionType.CALL,
                               exercise_type=TuringExerciseType.EUROPEAN,
                               premium_currency=Currency.USD,
                               tenors=tenors,
                               future_quotes=fwd_quotes,
                               future_tenors=fwd_tenors,
                               ccy2_cc_rates=dom_rates,
                               vol_tenors=vol_tenors,
                               atm_vols=atm_vols,
                               butterfly_25delta_vols=butterfly_25delta_vols,
                               risk_reversal_25delta_vols=risk_reversal_25delta_vols,
                               butterfly_10delta_vols=butterfly_10delta_vols,
                               risk_reversal_10delta_vols=risk_reversal_10delta_vols
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
