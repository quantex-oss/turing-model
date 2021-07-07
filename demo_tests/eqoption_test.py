import time

from turing_models.utilities.turing_date import TuringDate
from turing_models.instrument.european_option import EuropeanOption
from turing_models.instrument.knockout_option import KnockOutOption
from turing_models.instrument.snowball_option import SnowballOption
from turing_models.instrument.asian_option import AsianOption
from turing_models.instrument.american_option import AmericanOption
from tool import print_result
from fundamental.pricing_context import PricingContext
from turing_models.instrument.archive.eq_option import EqOption
# #
# #
european_option = EuropeanOption(option_type='CALL',
                                 product_type='EUROPEAN',
                                 expiry=TuringDate(2021, 9, 3),
                                 strike_price=5.3,
                                 number_of_options=2,
                                 multiplier=100,
                                 value_date=TuringDate(2021, 2, 3),
                                 stock_price=5.262,
                                 volatility=0.1,
                                 interest_rate=0.02,
                                 dividend_yield=0)
# #
# #
american_option = AmericanOption(option_type='CALL',
                           product_type='AMERICAN',
                           expiry=TuringDate(2021, 9, 3),
                           strike_price=5.3,
                           number_of_options=2,
                           multiplier=100,
                           value_date=TuringDate(2021, 2, 3),
                           stock_price=5.262,
                           volatility=0.1,
                           interest_rate=0.02,
                           dividend_yield=0)

# asian_option = EqOption(option_type='CALL',
#                         product_type='ASIAN',
#                         expiry=TuringDate(2021, 9, 3),
#                         start_averaging_date=TuringDate(2021, 2, 15),
#                         strike_price=5.3,
#                         number_of_options=2,
#                         value_date=TuringDate(2021, 2, 3),
#                         multiplier=100,
#                         stock_price=5.262,
#                         volatility=0.1,
#                         interest_rate=0.02,
#                         dividend_yield=0)

asian_option = AsianOption(option_type='CALL',
                        product_type='ASIAN',
                        expiry=TuringDate(2021, 9, 3),
                        start_averaging_date=TuringDate(2021, 2, 15),
                        strike_price=5.3,
                        number_of_options=2,
                        value_date=TuringDate(2021, 2, 3),
                        multiplier=100,
                        stock_price=5.262,
                        volatility=0.1,
                        interest_rate=0.02,
                        dividend_yield=0)
#
snowball_option = SnowballOption(option_type='CALL',
                           product_type='SNOWBALL',
                           expiry=TuringDate(2021, 9, 3),
                           participation_rate=1.0,
                           barrier=5.5,
                           knock_in_price=5.2,
                           notional=1000000,
                           rebate=0.2,
                           knock_in_type='spreads',
                           knock_in_strike1=5.3,
                           knock_in_strike2=5.4,
                           value_date=TuringDate(2021, 2, 3),
                           multiplier=100,
                           stock_price=5.262,
                           volatility=0.1,
                           interest_rate=0.02,
                           dividend_yield=0)

# snowball_option = EqOption(option_type='CALL',
#                            product_type='SNOWBALL',
#                            expiry=TuringDate(2021, 9, 3),
#                            participation_rate=1.0,
#                            barrier=5.5,
#                            knock_in_price=5.2,
#                            notional=1000000,
#                            rebate=0.2,
#                            knock_in_type='Spreads',
#                            knock_in_strike1=5.3,
#                            knock_in_strike2=5.4,
#                            value_date=TuringDate(2021, 2, 3),
#                            multiplier=100,
#                            stock_price=5.262,
#                            volatility=0.1,
#                            interest_rate=0.02,
#                            dividend_yield=0)
#

# knockout_option = KnockOutOption(option_type='PUT',
#                                  product_type='KNOCK_OUT',
#                                  knock_out_type='down_and_out',
#                                  expiry=TuringDate(2021, 9, 3),
#                                  strike_price=5.1,
#                                  participation_rate=1.0,
#                                  barrier=5.0,
#                                  notional=1000000,
#                                  rebate=0.2,
#                                  value_date=TuringDate(2021, 2, 3),
#                                  multiplier=100,
#                                  stock_price=5.262,
#                                  volatility=0.1,
#                                  interest_rate=0.02,
#                                  dividend_yield=0)
# #
# #
knockout_option1 = KnockOutOption(option_type='CALL',
                                 product_type='KNOCK_OUT',
                                 knock_out_type='up_and_out',
                                 expiry=TuringDate(2021, 9, 3),
                                 strike_price=5.3,
                                 participation_rate=1.0,
                                 barrier=5.5,
                                 notional=1000000,
                                 rebate=0.2,
                                 value_date=TuringDate(2021, 7, 6),
                                 stock_price=5.262,
                                 volatility=0.1,
                                 interest_rate=0.02,
                                 dividend_yield=0)
from turing_models.products.equity.equity_knockout_option import TuringEquityKnockoutOption
from fundamental.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.utilities.global_types import TuringKnockOutTypes
knockout_option = TuringEquityKnockoutOption(expiry_date=TuringDate(2021, 9, 3),
                                             strike_price=5.3,
                                             knock_out_type=TuringKnockOutTypes.UP_AND_OUT_CALL,
                                             barrier=5.5,
                                             rebate=0.2,
                                             notional=1000000,)
discount_curve = TuringDiscountCurveFlat(TuringDate(2021, 7, 6), 0.02)
dividend_curve = TuringDiscountCurveFlat(TuringDate(2021, 7, 6), 0)
model = TuringModelBlackScholes(0.1)
value = knockout_option.value(value_date=TuringDate(2021, 7, 6),
                                  stock_price=5.262,
                                  discount_curve=discount_curve,
                                  dividend_curve=dividend_curve,
                                  model=model)
delta = knockout_option.delta(valueDate=TuringDate(2021, 7, 6),
                              stockPrice=5.262,
                              discountCurve=discount_curve,
                              dividendCurve=dividend_curve,
                              model=model)
gamma = knockout_option.gamma(valueDate=TuringDate(2021, 7, 6),
                              stockPrice=5.262,
                              discountCurve=discount_curve,
                              dividendCurve=dividend_curve,
                              model=model)
vega = knockout_option.vega(valueDate=TuringDate(2021, 7, 6),
                              stockPrice=5.262,
                              discountCurve=discount_curve,
                              dividendCurve=dividend_curve,
                              model=model)
theta = knockout_option.theta(valueDate=TuringDate(2021, 7, 6),
                              stockPrice=5.262,
                              discountCurve=discount_curve,
                              dividendCurve=dividend_curve,
                              model=model)
rho = knockout_option.rho(valueDate=TuringDate(2021, 7, 6),
                              stockPrice=5.262,
                              discountCurve=discount_curve,
                              dividendCurve=dividend_curve,
                              model=model)
rho_q = knockout_option.rho_q(valueDate=TuringDate(2021, 7, 6),
                              stockPrice=5.262,
                              discountCurve=discount_curve,
                              dividendCurve=dividend_curve,
                              model=model)

time_start = time.time()
# # print_result(european_option)
# # print_result(american_option)
# # print_result(asian_option)
# # print_result(snowball_option)
print_result(knockout_option1)
print(round(value, 3))
print(round(delta, 3))
print(round(gamma, 3))
print(round(vega, 3))
print(round(theta, 3))
print(round(rho, 3))
print(round(rho_q, 3))
time_end = time.time()
print('耗时：', time_end - time_start)
# print_result(european_option)
# # print_result(american_option)
# # print_result(asian_option)
# # print_result(snowball_option)
# print_result(knockout_option)
# #
# #
# with PricingContext(interest_rate=0.04):
# #     print_result(european_option)
# # #     print_result(american_option)
# # #     print_result(asian_option)
# # #     print_result(snowball_option)
#     print_result(knockout_option)
# # #
# # #
# with PricingContext(interest_rate=0.04):
# #     print_result(european_option)
# # #     print_result(american_option)
# # #     print_result(asian_option)
# # #     print_result(snowball_option)
#     print_result(knockout_option)
# # #
# # #
# with PricingContext(interest_rate=0.06):
# #     print_result(european_option)
# # #     print_result(american_option)
# # #     print_result(asian_option)
# # #     print_result(snowball_option)
#     print_result(knockout_option)
# #

# from fundamental.pricing_context import CurveScenario
# curve_senario = CurveScenario('001', 1, 1, 5, 0, 50)
# print(curve_senario.curve_code)
# curve_senario.curve_code = '002'
# print(curve_senario.curve_code)