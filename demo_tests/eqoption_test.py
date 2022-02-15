import datetime
import time

import numpy as np
import pandas as pd

from fundamental.pricing_context import PricingContext
from turing_models.market.curves.discount_curve_flat import TuringDiscountCurveFlat

from turing_models.market.data.china_money_yield_curve import dates, rates

from turing_models.utilities.print import print_result
from turing_models.instruments.eq.european_option import EuropeanOption
from turing_models.instruments.eq.american_option import AmericanOption
from turing_models.instruments.eq.asian_option import AsianOption
from turing_models.instruments.eq.snowball_option import SnowballOption
from turing_models.instruments.eq.knockout_option import KnockOutOption
from turing_models.instruments.eq.basket_snowball_option import BasketSnowballOption
from turing_models.utilities.global_types import OptionType
from turing_models.instruments.common import Currency, RiskMeasure
from turing_models.utilities.helper_functions import betaVectorToCorrMatrix

# european_option = EuropeanOption(underlier_symbol='600067.SH',
#                                  option_type=OptionType.CALL,
#                                  expiry=datetime.datetime(2021, 9, 3),
#                                  start_date=datetime.datetime(2021, 6, 3),
#                                  strike_price=4.19,
#                                  number_of_options=2,
#                                  multiplier=100,
#                                  value_date=datetime.datetime(2021, 8, 13),
#                                  currency=Currency.CNY)

# american_option = AmericanOption(underlier_symbol='600067.SH',
#                                  option_type=OptionType.CALL,
#                                  expiry=datetime.datetime(2021, 9, 3),
#                                  start_date=datetime.datetime(2021, 6, 3),
#                                  strike_price=4.19,
#                                  number_of_options=2,
#                                  multiplier=100,
#                                  value_date=datetime.datetime(2021, 8, 13),
#                                  currency=Currency.CNY)

# asian_option = AsianOption(underlier_symbol='600067.SH',
#                            option_type=OptionType.CALL,
#                            expiry=datetime.datetime(2021, 9, 3),
#                            start_date=datetime.datetime(2021, 6, 3),
#                            start_averaging_date=datetime.datetime(2021, 8, 15),
#                            strike_price=4.19,
#                            number_of_options=2,
#                            value_date=datetime.datetime(2021, 8, 13),
#                            currency=Currency.CNY,
#                            multiplier=100)

# snowball_option = SnowballOption(underlier_symbol='600067.SH',
#                                  option_type=OptionType.CALL,
#                                  start_date=datetime.datetime(2021, 6, 3),
#                                  expiry=datetime.datetime(2021, 10, 3),
#                                  participation_rate=1.0,
#                                  barrier=4.25,
#                                  knock_in_price=4.1,
#                                  notional=1000000,
#                                  rebate=0.2,
#                                  initial_spot=4.2,
#                                  untriggered_rebate=0.2,
#                                  knock_in_type='SPREADS',
#                                  knock_out_obs_days_whole=[datetime.datetime(2021, 6, 3), datetime.datetime(
#                                      2021, 7, 5), datetime.datetime(2021, 8, 3), datetime.datetime(2021, 9, 3)],
#                                  knock_in_strike1=4.23,
#                                  knock_in_strike2=4.24,
#                                  value_date=datetime.datetime(2021, 8, 13),
#                                  currency=Currency.CNY)

# knockout_option = KnockOutOption(underlier_symbol='600067.SH',
#                                  option_type=OptionType.CALL,
#                                  start_date=datetime.datetime(2021, 6, 3),
#                                  expiry=datetime.datetime(2021, 9, 3),
#                                  strike_price=4.19,
#                                  participation_rate=1.0,
#                                  barrier=5.5,
#                                  notional=1000000,
#                                  rebate=0.2,
#                                  value_date=datetime.datetime(2021, 8, 13),
#                                  currency=Currency.CNY)

# def test_european_option_original():
#     assert round(european_option.calc(RiskMeasure.Price), 3) == 2.156
#     assert round(european_option.calc(RiskMeasure.EqDelta), 3) == 114.733
#     assert round(european_option.calc(RiskMeasure.EqGamma), 3) == 3614.915
#     assert round(european_option.calc(RiskMeasure.EqVega), 3) == 80.17
#     assert round(european_option.calc(RiskMeasure.EqTheta), 3) == -21.915
#     assert round(european_option.calc(RiskMeasure.EqRho), 3) == 28.487
#     assert round(european_option.calc(RiskMeasure.EqRhoQ), 3) == -28.615

# def test_american_option_original():
#     assert round(american_option.calc(RiskMeasure.Price), 3) == 2.112
#     assert round(american_option.calc(RiskMeasure.EqDelta), 3) == 114.488
#     assert round(american_option.calc(RiskMeasure.EqGamma), 3) == 49382.066
#     assert round(american_option.calc(RiskMeasure.EqVega), 3) == 78.866
#     assert round(american_option.calc(RiskMeasure.EqTheta), 3) == -22.324
#     assert round(american_option.calc(RiskMeasure.EqRho), 3) == 27.464
#     assert round(american_option.calc(RiskMeasure.EqRhoQ), 3) == -27.593

# def test_asian_option_original():
#     assert round(asian_option.calc(RiskMeasure.Price), 3) == 1.284
#     assert round(asian_option.calc(RiskMeasure.EqDelta), 3) == 112.642
#     assert round(asian_option.calc(RiskMeasure.EqGamma), 3) == 5922.579
#     assert round(asian_option.calc(RiskMeasure.EqVega), 3) == 49.768
#     assert round(asian_option.calc(RiskMeasure.EqTheta), 3) == -31.667
#     assert round(asian_option.calc(RiskMeasure.EqRho), 3) == 15.357
#     assert round(asian_option.calc(RiskMeasure.EqRhoQ), 3) == -14.587

# def test_snowball_option_original():
#     assert round(snowball_option.calc(RiskMeasure.Price), 3) == 66503.2
#     assert round(snowball_option.calc(RiskMeasure.EqDelta), 3) == -1842.627
#     assert round(snowball_option.calc(RiskMeasure.EqGamma), 3) == 21640994.455
#     assert round(snowball_option.calc(RiskMeasure.EqVega), 3) == 0.0
#     assert round(snowball_option.calc(RiskMeasure.EqTheta), 3) == 1113.619
#     assert round(snowball_option.calc(RiskMeasure.EqRho), 3) == -7067.055
#     assert round(snowball_option.calc(RiskMeasure.EqRhoQ), 3) == -2198.644

# def test_knockout_option_original():
#     assert round(knockout_option.calc(RiskMeasure.Price), 3) == 2520.706
#     assert round(knockout_option.calc(RiskMeasure.EqDelta), 3) == 136019.34
#     assert round(knockout_option.calc(RiskMeasure.EqGamma), 3) == 4326388.227
#     assert round(knockout_option.calc(RiskMeasure.EqVega), 3) == 94109.256
#     assert round(knockout_option.calc(RiskMeasure.EqTheta), 3) == -26640.928
#     assert round(knockout_option.calc(RiskMeasure.EqRho), 3) == 32781.571
#     assert round(knockout_option.calc(RiskMeasure.EqRhoQ), 3) == -32935.022

# def basket_snowball_option_original():
#     assert round(basket_snowball_option.calc(RiskMeasure.Price), 3) == 0.0

# test_european_option_original()
# test_american_option_original()
# test_asian_option_original()
# test_snowball_option_original()
# test_knockout_option_original()
# test_basket_snowball_option()

# scenario_extreme = PricingContext(
#     pricing_date='2021-08-13T00:00:00.000+0800',
#     spot=[{"symbol": "600067.SH", "value": 4.25}],
#     volatility=[{"symbol": "600067.SH", "value": 0.1}],
#     interest_rate=0.05,
#     dividend_yield=[{"symbol": "600067.SH", "value": 0.04}]
# )

# def test_european_option_modified():
#     assert round(european_option.calc(RiskMeasure.Price), 3) == 17.359
#     assert round(european_option.calc(RiskMeasure.EqDelta), 3) == 152.478
#     assert round(european_option.calc(RiskMeasure.EqGamma), 3) == 596.351
#     assert round(european_option.calc(RiskMeasure.EqVega), 3) == 64.117
#     assert round(european_option.calc(RiskMeasure.EqTheta), 3) == -84.629
#     assert round(european_option.calc(RiskMeasure.EqRho), 3) == 37.54
#     assert round(european_option.calc(RiskMeasure.EqRhoQ), 3) == -38.573

# def test_american_option_modified():
#     assert round(american_option.calc(RiskMeasure.Price), 3) == 17.192
#     assert round(american_option.calc(RiskMeasure.EqDelta), 3) == 153.246
#     assert round(american_option.calc(RiskMeasure.EqGamma), 3) == 0.0
#     assert round(american_option.calc(RiskMeasure.EqVega), 3) == 62.538
#     assert round(american_option.calc(RiskMeasure.EqTheta), 3) == -85.977
#     assert round(american_option.calc(RiskMeasure.EqRho), 3) == 34.676
#     assert round(american_option.calc(RiskMeasure.EqRhoQ), 3) == -37.399

# def test_asian_option_modified():
#     assert round(asian_option.calc(RiskMeasure.Price), 3) == 14.219
#     assert round(asian_option.calc(RiskMeasure.EqDelta), 3) == 170.891
#     assert round(asian_option.calc(RiskMeasure.EqGamma), 3) == 714.163
#     assert round(asian_option.calc(RiskMeasure.EqVega), 3) == 28.887
#     assert round(asian_option.calc(RiskMeasure.EqTheta), 3) == -99.521
#     assert round(asian_option.calc(RiskMeasure.EqRho), 3) == 21.041
#     assert round(asian_option.calc(RiskMeasure.EqRhoQ), 3) == -22.915

# def test_snowball_option_modified():
#     assert round(snowball_option.calc(RiskMeasure.Price), 3) == 43745.849
#     assert round(snowball_option.calc(RiskMeasure.EqDelta), 3) == 110812.057
#     assert round(snowball_option.calc(RiskMeasure.EqGamma), 3) == 177605318.512
#     assert round(snowball_option.calc(RiskMeasure.EqVega), 3) == 0.0
#     assert round(snowball_option.calc(RiskMeasure.EqTheta), 3) == 2134.51
#     assert round(snowball_option.calc(RiskMeasure.EqRho), 3) == 38263.095
#     assert round(snowball_option.calc(RiskMeasure.EqRhoQ), 3) == -43627.685

# def test_knockout_option_modified():
#     assert round(knockout_option.calc(RiskMeasure.Price), 3) == 20223.193
#     assert round(knockout_option.calc(RiskMeasure.EqDelta), 3) == 175190.931
#     assert round(knockout_option.calc(RiskMeasure.EqGamma), 3) == 627206.51
#     assert round(knockout_option.calc(RiskMeasure.EqVega), 3) == 73747.496
#     assert round(knockout_option.calc(RiskMeasure.EqTheta), 3) == -101023.013
#     assert round(knockout_option.calc(RiskMeasure.EqRho), 3) == 40797.89
#     assert round(knockout_option.calc(RiskMeasure.EqRhoQ), 3) == -44001.311


# print_result(snowball_option)

# with scenario_extreme:
# test_european_option_modified()
# test_american_option_modified()
# test_asian_option_modified()
# test_snowball_option_modified()
# test_knockout_option_modified()


##TODO：basket_snowball_option经with作用域后线程被killed，无法打印结果。

betas = np.ones(5) * 0.1
corr_matrix = betaVectorToCorrMatrix(betas)


basket_snowball_option = BasketSnowballOption(option_type=OptionType.CALL,
                                            start_date=datetime.datetime(
                                                2020, 1, 1),
                                            expiry=datetime.datetime(
                                                2022, 1, 1),
                                            initial_spot=100,
                                            participation_rate=1.0,
                                            barrier=110,
                                            knock_in_price=88,
                                            notional=1000000,
                                            rebate=0.2,
                                            untriggered_rebate=0.2,
                                            underlier_symbol=[
                                                "600277.SH", "600269.SH", "600201.SH", "600067.SH", "600243.SH"],
                                            knock_in_type='SPREADS',
                                            knock_in_strike1=5.3,
                                            knock_in_strike2=5.4,
                                            value_date=datetime.datetime(
                                                2021, 8, 13),
                                            currency=Currency.CNY,
                                            weights=[
                                                0.2, 0.2, 0.2, 0.2, 0.2],
                                            correlation_matrix=corr_matrix)

scenario_extreme = PricingContext(
    pricing_date='2015-01-01T00:00:00.000+0800',
    spot=[{"symbol": "600277.SH", "value": 100},
        {"symbol": "600269.SH", "value": 100},
        {"symbol": "600201.SH", "value": 100},
        {"symbol": "600067.SH", "value": 100},
        {"symbol": "600243.SH", "value": 100}],
    volatility=[{"symbol": "600277.SH", "value": 0.3},
                {"symbol": "600269.SH", "value": 0.3},
                {"symbol": "600201.SH", "value": 0.3},
                {"symbol": "600067.SH", "value": 0.3},
                {"symbol": "600243.SH", "value": 0.3}],
    interest_rate=0.05,
    dividend_yield=[{"symbol": "600277.SH", "value": 0.01},
                    {"symbol": "600269.SH", "value": 0.01},
                    {"symbol": "600201.SH", "value": 0.01},
                    {"symbol": "600067.SH", "value": 0.01},
                    {"symbol": "600243.SH", "value": 0.01}]
)
print(basket_snowball_option.calc(RiskMeasure.Price))
with scenario_extreme:
    print(basket_snowball_option.calc(RiskMeasure.Price))

    # return (basket_snowball_option.calc(RiskMeasure.Price))
# basket_snowball_option.calc(RiskMeasure.Price)
