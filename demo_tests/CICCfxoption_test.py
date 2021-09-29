import time

import numpy as np
import pandas as pd
from turing_models.instruments.common import Currency, CurrencyPair
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.instruments.fx.fx_vanilla_option_CICC import FXVanillaOptionCICC
from turing_models.instruments.rates.irs import create_ibor_single_curve
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.global_types import TuringSwapTypes
# from turing_models.market.data.china_money_yield_curve import dates, rates
from turing_models.utilities.global_types import TuringOptionType, TuringExerciseType

# mkt_file = '../turing_models/market/data/market data 20210820.xlsx'
# shibor_deposit_mkt_data = pd.read_excel(mkt_file, 'Shibor Deposit Rate')
# shibor_deposit_mkt_data.iloc[0, :] /= 100
# deposit_terms = shibor_deposit_mkt_data.columns.values.tolist()
# deposit_rates = shibor_deposit_mkt_data.values.tolist()[0]
# shibor_swap_mkt_data = pd.read_excel(mkt_file, 'Shibor Swap Rate')
# shibor_swap_mkt_data.iloc[0, :] /= 100
# swap_curve_dates = shibor_swap_mkt_data.columns.values.tolist()
# swap_curve_rates = shibor_swap_mkt_data.values.tolist()[0]
#
# tenors = deposit_terms + swap_curve_dates
# dom_rates = create_ibor_single_curve(value_date, deposit_terms, deposit_rates, TuringDayCountTypes.ACT_365F,
#                                      swap_curve_dates, TuringSwapTypes.PAY, swap_curve_rates, TuringFrequencyTypes.QUARTERLY, TuringDayCountTypes.ACT_365F, 0).ccRate(value_date.addTenor(tenors)).tolist()
#
# fwd_data = pd.read_excel(mkt_file, 'USDCNY_Futures')
# fwd_tenors = fwd_data['Tenor'].values.tolist()
# fwd_quotes = [x / 10000 for x in fwd_data['Spread'].values.tolist()]
#
# vol_data = pd.read_excel(mkt_file, 'USDCNY_vols')
# vol_data[['ATM', '25DRR', '25DBF', '10DRR', '10DBF']] /= 100
# vol_tenors = vol_data['Tenor'].values.tolist()
# atm_vols = vol_data['ATM'].values.tolist()
# butterfly_25delta_vols = vol_data['25DBF'].values.tolist()
# risk_reversal_25delta_vols = vol_data['25DRR'].values.tolist()
# butterfly_10delta_vols = vol_data['10DBF'].values.tolist()
# risk_reversal_10delta_vols = vol_data['10DRR'].values.tolist()

value_date = TuringDate(2021, 9, 29)
fxoption = FXVanillaOptionCICC(start_date=TuringDate(2021, 4, 20),
                               expiry=TuringDate(2022, 9, 16),
                               cut_off_time=TuringDate(2022, 9, 16),
                               #    delivery_date=TuringDate(2021, 7, 20),
                               value_date=value_date,
                               underlier_symbol=CurrencyPair.USDCNY,
                               strike=6.6,
                               notional=50000000.00,
                               notional_currency=Currency.USD,
                               option_type=TuringOptionType.CALL,
                               exercise_type=TuringExerciseType.EUROPEAN,
                               premium_currency=Currency.CNY)
atm = fxoption.atm()
price = fxoption.price()
delta = fxoption.fx_delta_bump()
gamma = fxoption.fx_gamma_bump()
vega = fxoption.fx_vega_bump()
theta = fxoption.fx_theta_bump()
rho = fxoption.fx_rho_bump()
phi = fxoption.fx_phi_bump()
print("atm", atm, "sigma", fxoption.volatility_)
print("price:", price, "delta:", delta, "gamma:",
      gamma, "vega:", vega, "theta:", theta, "rho:", rho, "phi:", phi)
# for spotFXRate in np.arange(100, 200, 10)/100.0:
#     fxoption.spot_fx_rate = spotFXRate

#     value = fxoption.price()
#     valuemc = fxoption.price_mc()
#     fxoption.market_price = value
#     impliedVol = fxoption.implied_volatility()

#     print(spotFXRate, value, valuemc, impliedVol)