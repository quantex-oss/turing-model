import cProfile
import time

import numpy as np

from fundamental.market.constants import dates, rates
from fundamental.market.curves import TuringDiscountCurveFlat
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.products.equity import TuringEquitySnowballOption
from turing_models.products.equity.equity_basket_snowball import TuringSnowballBasketOption

from turing_models.utilities.print import print_result
from turing_models.utilities.turing_date import TuringDate
from turing_models.instruments.european_option import EuropeanOption
from turing_models.instruments.american_option import AmericanOption
from turing_models.instruments.asian_option import AsianOption
from turing_models.instruments.snowball_option import SnowballOption
from turing_models.instruments.knockout_option import KnockOutOption
from turing_models.instruments.basket_snowball_option import BasketSnowballOption
from turing_models.utilities.global_types import TuringOptionType
from turing_models.instruments.common import Currency
from turing_models.utilities.helper_functions import betaVectorToCorrMatrix

#
#
# european_option = EuropeanOption(asset_id='OPTIONCN00000001',
#                                  underlier='STOCKCN00000001',
#                                  option_type=TuringOptionType.CALL,
#                                  start_date=TuringDate(2021, 6, 3),
#                                  expiry=TuringDate(2021, 9, 3),
#                                  strike_price=5.3,
#                                  number_of_options=2,
#                                  multiplier=100,
#                                  value_date=TuringDate(2021, 8, 13),
#                                  currency=Currency.CNY,
#                                  stock_price=5.262,
#                                  volatility=0.1,
#                                  zero_dates=dates,
#                                  zero_rates=rates,
#                                  dividend_yield=0)
#
# american_option = AmericanOption(asset_id='OPTIONCN00000001',
#                                  underlier='STOCKCN00000001',
#                                  option_type=TuringOptionType.CALL,
#                                  expiry=TuringDate(2021, 9, 3),
#                                  start_date=TuringDate(2021, 6, 3),
#                                  strike_price=5.3,
#                                  number_of_options=2,
#                                  multiplier=100,
#                                  value_date=TuringDate(2021, 8, 13),
#                                  currency=Currency.CNY,
#                                  stock_price=5.262,
#                                  volatility=0.1,
#                                  zero_dates=dates,
#                                  zero_rates=rates,
#                                  dividend_yield=0)
#
# asian_option = AsianOption(asset_id='OPTIONCN00000001',
#                            underlier='STOCKCN00000001',
#                            option_type=TuringOptionType.CALL,
#                            expiry=TuringDate(2021, 9, 3),
#                            start_date=TuringDate(2021, 6, 3),
#                            start_averaging_date=TuringDate(2021, 8, 15),
#                            strike_price=5.3,
#                            number_of_options=2,
#                            value_date=TuringDate(2021, 8, 13),
#                            currency=Currency.CNY,
#                            multiplier=100,
#                            stock_price=5.262,
#                            volatility=0.1,
#                            zero_dates=dates,
#                            zero_rates=rates,
#                            dividend_yield=0)
#
# snowball_option = SnowballOption(asset_id='OPTIONCN00000001',
#                                  option_type=TuringOptionType.CALL,
#                                  start_date=TuringDate(2021, 6, 3),
#                                  expiry=TuringDate(2021, 9, 3),
#                                  participation_rate=1.0,
#                                  barrier=5.5,
#                                  knock_in_price=5.2,
#                                  notional=1000000,
#                                  rebate=0.2,
#                                  initial_spot=5.2,
#                                  untriggered_rebate=0.2,
#                                  knock_in_type='SPREADS',
#                                  knock_out_obs_days_whole=[TuringDate(2021, 6, 3), TuringDate(2021, 7, 5), TuringDate(2021, 8, 3), TuringDate(2021, 9, 3)],
#                                  knock_in_strike1=5.3,
#                                  knock_in_strike2=5.4,
#                                  # value_date=TuringDate(2021, 8, 13),
#                                  currency=Currency.CNY,
#                                  stock_price=5.262,
#                                  volatility=0.1,
#                                  zero_dates=dates,
#                                  zero_rates=rates,
#                                  dividend_yield=0)

knockout_option = KnockOutOption(asset_id='OPTIONCN00000001',
                                 underlier='STOCKCN00000001',
                                 option_type=TuringOptionType.CALL,
                                 start_date='2021-6-3',
                                 expiry=TuringDate(2021, 9, 3),
                                 strike_price=5.3,
                                 participation_rate=1.0,
                                 barrier=5.5,
                                 notional=1000000,
                                 rebate=0.2,
                                 value_date=TuringDate(2021, 8, 13),
                                 currency=Currency.CNY,
                                 stock_price=5.262,
                                 volatility=0.1,
                                 zero_dates=dates,
                                 zero_rates=rates,
                                 dividend_yield=0)

# print_result(european_option)
# print_result(american_option)
# print_result(asian_option)
# print_result(snowball_option)
print(knockout_option.price())

# #########################################
# betas = np.ones(5) * 0.1
# corr_matrix = betaVectorToCorrMatrix(betas)
#
# basket_snowball_option = BasketSnowballOption(option_type=TuringOptionType.CALL,
#                                               start_date=TuringDate(2014, 1, 1),
#                                               expiry=TuringDate(2016, 1, 1),
#                                               initial_spot=100,
#                                               participation_rate=1.0,
#                                               barrier=110,
#                                               knock_in_price=88,
#                                               notional=1000000,
#                                               rebate=0.2,
#                                               untriggered_rebate=0.2,
#                                               underlier=["STOCKCN00000001", "STOCKCN00000002", "STOCKCN00000003", "STOCKCN00000004", "STOCKCN00000005"],
#                                               knock_in_type='SPREADS',
#                                               knock_in_strike1=5.3,
#                                               knock_in_strike2=5.4,
#                                               value_date=TuringDate(2015, 1, 1),
#                                               currency=Currency.CNY,
#                                               stock_price=[100., 100., 100., 100., 100.],
#                                               volatility=[0.3, 0.3, 0.3, 0.3, 0.3],
#                                               interest_rate=0.05,
#                                               dividend_yield=[0.01, 0.01, 0.01, 0.01, 0.01],
#                                               weights=[0.2, 0.2, 0.2, 0.2, 0.2],
#                                               correlation_matrix=corr_matrix)
#
# start = time.time()
# price1 = basket_snowball_option.price()
# end = time.time()
# print(price1, end-start)
# start = time.time()
# price2 = basket_snowball_option.price_3dim()
# end = time.time()
# print(price2, end-start)
