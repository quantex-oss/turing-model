import cProfile

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
from turing_models.utilities.global_types import TuringOptionType, TuringOptionTypes
from turing_models.instruments.common import Currency
from turing_models.utilities.helper_functions import betaVectorToCorrMatrix



# european_option = EuropeanOption(underlier="STOCKCN00000007",
#                                  option_type=TuringOptionType.CALL,
#                                  expiry=TuringDate(2021, 9, 3),
#                                  strike_price=5.3,
#                                  number_of_options=2,
#                                  multiplier=100,
#                                  value_date=TuringDate(2021, 2, 3),
#                                  currency=Currency.CNY,
#                                  stock_price=5.262,
#                                  volatility=0.1,
#                                  zero_dates=dates,
#                                  zero_rates=rates,
#                                  dividend_yield=0)
#
# american_option = AmericanOption(option_type=TuringOptionType.CALL,
#                                  expiry=TuringDate(2021, 9, 3),
#                                  strike_price=5.3,
#                                  number_of_options=2,
#                                  multiplier=100,
#                                  value_date=TuringDate(2021, 2, 3),
#                                  currency=Currency.CNY,
#                                  stock_price=5.262,
#                                  volatility=0.1,
#                                  zero_dates=dates,
#                                  zero_rates=rates,
#                                  dividend_yield=0)
#
# asian_option = AsianOption(option_type=TuringOptionType.CALL,
#                            expiry=TuringDate(2021, 9, 3),
#                            start_averaging_date=TuringDate(2021, 2, 15),
#                            strike_price=5.3,
#                            number_of_options=2,
#                            value_date=TuringDate(2021, 2, 3),
#                            currency=Currency.CNY,
#                            multiplier=100,
#                            stock_price=5.262,
#                            volatility=0.1,
#                            zero_dates=dates,
#                            zero_rates=rates,
#                            dividend_yield=0)
#
snowball_option = SnowballOption(option_type=TuringOptionType.CALL,
                                 start_date=TuringDate(2021, 6, 3),
                                 expiry=TuringDate(2021, 9, 3),
                                 participation_rate=1.0,
                                 barrier=5.5,
                                 knock_in_price=5.2,
                                 notional=1000000,
                                 rebate=0.2,
                                 knock_in_type='RETURN',
                                 # knock_in_strike1=5.3,
                                 # knock_in_strike2=5.4,
                                 # value_date=TuringDate(2021, 2, 3),
                                 currency=Currency.CNY,
                                 stock_price=5.262,
                                 volatility=0.1,
                                 zero_dates=dates,
                                 zero_rates=rates,
                                 dividend_yield=0)

print(snowball_option.price())
print(snowball_option.price_new())


#
# knockout_option = KnockOutOption(asset_id='OPTIONCN00000001',
#                                  underlier='STOCKCN00000001',
#                                  option_type=TuringOptionType.CALL,
#                                  expiry=TuringDate(2021, 9, 3),
#                                  strike_price=5.3,
#                                  participation_rate=1.0,
#                                  barrier=5.5,
#                                  notional=1000000,
#                                  rebate=0.2,
#                                  value_date=TuringDate(2021, 7, 6),
#                                  currency=Currency.CNY,
#                                  stock_price=5.262,
#                                  volatility=0.1,
#                                  zero_dates=dates,
#                                  zero_rates=rates,
#                                  dividend_yield=0)
# knockout_option = KnockOutOption(asset_id="OPTIONCN00000002",
#                                  underlier="STOCKCN00000002",
#                                  option_type=TuringOptionType.CALL,
#                                  expiry=TuringDate(2021, 9, 3),
#                                  strike_price=11.3,
#                                  participation_rate=1.0,
#                                  barrier=13,
#                                  notional=1000000,
#                                  rebate=0.2,
#                                  value_date=TuringDate(2021, 7, 6),
#                                  volatility=0.1,
#                                  zero_dates=dates,
#                                  zero_rates=rates,
#                                  dividend_yield=0)

# betas = np.ones(5) * 0.1
# corr_matrix = betaVectorToCorrMatrix(betas)
#
# basket_snowball_option = BasketSnowballOption(option_type=TuringOptionType.CALL,
#                                               expiry=TuringDate(2016, 1, 1),
#                                               participation_rate=1.0,
#                                               barrier=110,
#                                               knock_in_price=88,
#                                               notional=1000000,
#                                               rebate=0.2,
#                                               underlier=["STOCKCN00000001", "STOCKCN00000002", "STOCKCN00000003", "STOCKCN00000004", "STOCKCN00000005"],
#                                               knock_in_type='spreads',
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
# # # print_result(basket_snowball_option)
# p = cProfile.Profile()
# p.enable()
# print(basket_snowball_option.price())
# p.disable()
# p.print_stats(sort='tottime')


# import time
#
# volatilities = np.array([0.3, 0.2, 0.25, 0.22, 0.4])
# dividendYields = np.array([0.01, 0.02, 0.04, 0.01, 0.02])
# stockPrices = np.array([100., 105., 120., 100., 90.])
# weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
# betaList = np.linspace(0.0, 0.999999, 2)
#
# for beta in betaList:
#     betas = np.ones(5) * beta
#     corr_matrix = betaVectorToCorrMatrix(betas)
#     # print(corrMatrix)
#     start = time.time()
#     basket_snowball_option = BasketSnowballOption(option_type=TuringOptionType.CALL,
#                                                   expiry=TuringDate(2016, 1, 1),
#                                                   participation_rate=1.0,
#                                                   barrier=110,
#                                                   knock_in_price=88,
#                                                   notional=1000000,
#                                                   rebate=0.2,
#                                                   underlier=["STOCKCN00000001", "STOCKCN00000002", "STOCKCN00000003",
#                                                              "STOCKCN00000004", "STOCKCN00000005"],
#                                                   knock_in_type='return',
#                                                   # knock_in_strike1=5.3,
#                                                   # knock_in_strike2=5.4,
#                                                   value_date=TuringDate(2015, 1, 1),
#                                                   currency=Currency.CNY,
#                                                   stock_price=[100., 100., 100., 100., 100.],
#                                                   volatility=[0.3, 0.3, 0.3, 0.3, 0.3],
#                                                   interest_rate=0.05,
#                                                   dividend_yield=[0.01, 0.01, 0.01, 0.01, 0.01],
#                                                   weights=[0.2, 0.2, 0.2, 0.2, 0.2],
#                                                   correlation_matrix=corr_matrix)
#     price = basket_snowball_option.price()
#     end = time.time()
#     duration = end - start
#     print(basket_snowball_option)
# # print(price)
#
#
#
# valueDate = TuringDate(2015, 1, 1)
# expiryDate = TuringDate(2016, 1, 1)
# # volatility = 0.30
# interestRate = 0.05
# discountCurve = TuringDiscountCurveFlat(valueDate, interestRate)
#
# ##########################################################################
# # INHomogeneous Basket
# ##########################################################################
#
# numAssets = 5
# # volatilities = np.array([0.3, 0.2, 0.25, 0.22, 0.4])
# # dividendYields = np.array([0.01, 0.02, 0.04, 0.01, 0.02])
# # stockPrices = np.array([100., 105., 120., 100., 90.])
# # weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
# betaList = np.linspace(0.0, 0.999999, 2)
# volatilities = np.array([0.3, 0.3, 0.3, 0.3, 0.3])
# dividendYields = np.array([0.01, 0.01, 0.01, 0.01, 0.01])
# stockPrices = np.array([100., 100., 100., 100., 100.])
# weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
#
# dividendCurves = []
# for q in dividendYields:
#     dividendCurve = TuringDiscountCurveFlat(valueDate, q)
#     dividendCurves.append(dividendCurve)
#
# # testCases.header("NumPaths", "Beta", "Value", "ValueMC", "TIME")
#
# for beta in betaList:
#
#     for numPaths in [100000]:
#         callOption = TuringSnowballBasketOption(
#             expiryDate, TuringOptionTypes.SNOWBALL_CALL, 110, 88, 1000000, 0.2, numAssets)
#         betas = np.ones(numAssets) * beta
#         corrMatrix = betaVectorToCorrMatrix(betas)
#         # print(corrMatrix)
#         start = time.time()
#         vMC = callOption.valueMC(
#             valueDate,
#             stockPrices,
#             discountCurve,
#             dividendCurves,
#             volatilities,
#             corrMatrix,
#             weights,
#             numPaths
#         )
#         end = time.time()
#         duration = end - start
# print(vMC)
# print(price)


# knockout_option.resolve()
# time_start = time.time()
# print(round(american_option.calc(RiskMeasure.EqRhoQ), 3))
# print_result(european_option)
# print_result(american_option)
# print_result(asian_option)
# time1 = time.time()
# print_result(snowball_option)
# time2 = time.time()
# print(time2-time1)
# print(knockout_option)
# print_result(knockout_option)
# knockout_option.resolve("1")
# time_end = time.time()
# print('耗时：', time_end - time_start)
# print(european_option.price())
# scenario_extreme = PricingContext(spot=[
#                                       {"asset_id": "STOCKCN00000007", "value": 5},
#                                       {"asset_id": "STOCKCN00000002", "value": 5.3}
#                                   ]
#                                   )
#
# with scenario_extreme:
#     print(european_option.price())
