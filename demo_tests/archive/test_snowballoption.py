import sys
sys.path.append("..")

import time

import numpy as np
from numba import njit

# TODO: Add perturbatory risk using the analytical methods !!
# TODO: Add Sobol to Monte Carlo

from turing_models.utilities.mathematics import covar
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.error import TuringError

from turing_models.utilities.global_types import TuringOptionTypes, TuringKnockInTypes
from turing_models.utilities.helper_functions import checkArgumentTypes, labelToString
from turing_models.utilities.turing_date import TuringDate
from fundamental.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.models.model_black_scholes import TuringModelBlackScholes

from turing_models.utilities.mathematics import N

from turing_models.products.equity.equity_snowball_option import TuringEquitySnowballOption


expiry_date = TuringDate(2021, 2, 12)
knock_out_price = 120
knock_in_price = 90
notional = 1000000
coupon_rate = 0.3
option_type = TuringOptionTypes.SNOWBALL_CALL
knock_in_type = TuringKnockInTypes.RETURN
knock_in_strike1 = None
knock_in_strike2 = None

snowball_option = TuringEquitySnowballOption(expiry_date,
                                             knock_out_price,
                                             knock_in_price,
                                             notional,
                                             coupon_rate,
                                             option_type,
                                             knock_in_type,
                                             knock_in_strike1,
                                             knock_in_strike2)

value_date = TuringDate(2020, 2, 12)
stock_price = 100
interest_rate = 0.02
dividend_yield = 0
volatility = 0.1

discount_curve = TuringDiscountCurveFlat(value_date, interest_rate)
dividend_curve = TuringDiscountCurveFlat(value_date, dividend_yield)
model = TuringModelBlackScholes(volatility)

time_start = time.time()
price = snowball_option.value(value_date,
                              stock_price,
                              discount_curve,
                              dividend_curve,
                              model)
time_end = time.time()
print('Time cost = %fs' % (time_end - time_start))
print(price)
delta = snowball_option.delta(value_date,
                              stock_price,
                              discount_curve,
                              dividend_curve,
                              model)
print(delta)
gamma = snowball_option.gamma(value_date,
                              stock_price,
                              discount_curve,
                              dividend_curve,
                              model)
print(gamma)
vega = snowball_option.vega(value_date,
                            stock_price,
                            discount_curve,
                            dividend_curve,
                            model)
print(vega)
theta = snowball_option.theta(value_date,
                              stock_price,
                              discount_curve,
                              dividend_curve,
                              model)
print(theta)
rho = snowball_option.rho(value_date,
                          stock_price,
                          discount_curve,
                          dividend_curve,
                          model)
print(rho)






# # @njit(cache=True, fastmath=True)
def _valueMC_fast_NUMBA(valueDate: TuringDate,
                        expiryDate: TuringDate,
                        K1: float,  # 敲出价格
                        K2: float,  # 敲入价格
                        obs_freq: TuringFrequencyTypes,  # 敲出观察频率
                        notional: int,  # 名义本金
                        stockPrice: float,
                        interestRate: float,
                        dividendYield: float,
                        volatility: float,
                        numPaths: int,
                        seed: int,
                        coupon_rate: float):

    np.random.seed(seed)
    mu = interestRate - dividendYield
    v2 = volatility**2
    r = interestRate
    numPaths = int(numPaths)
    n = int(expiryDate - valueDate)
    dt = 1/gDaysInYear
    S0 = stockPrice
    date_list = []
    date_list.append(valueDate)
    for i in range(1, n + 1):
        dateinc = valueDate.addDays(i)
        date_list.append(dateinc)

    s_1 = np.empty(n+1)
    s_2 = np.empty(n+1)
    s_1[0] = s_2[0] = S0
    s_1_pd = np.empty(numPaths)
    s_2_pd = np.empty(numPaths)

    for j in range(0, numPaths):
        g = np.random.normal(0.0, 1.0, size=n)
        syb_up_1 = 0
        syb_up_2 = 0
        syb_down_1 = 0
        syb_down_2 = 0

        for ip in range(1, n+1):
            s_1[ip] = s_1[ip-1] * np.exp((mu - v2 / 2.0) *
                                         dt + g[ip-1] * np.sqrt(dt) *
                                         volatility)
            if s_1[ip] < K2:
                syb_down_1 = 1

            if (obs_freq == TuringFrequencyTypes.MONTHLY and
                date_list[ip]._d == expiryDate._d and
                    s_1[ip] >= K1):
                syb_up_1 = 1
                payoff_discounted = (notional * coupon_rate * ip / gDaysInYear) * \
                    np.exp(-r * ip / gDaysInYear)
                s_1_pd[j] = payoff_discounted

                break

            if ip == n and syb_up_1 == 0 and syb_down_1 == 0:
                payoff_discounted = (notional * coupon_rate * ip / gDaysInYear) * \
                    np.exp(-r * ip / gDaysInYear)
                s_1_pd[j] = payoff_discounted
            elif ip == n and syb_up_1 == 0 and syb_down_1 == 1:
                payoff_discounted = -notional * (1 - s_1[ip] / S0) * \
                    np.exp(-r * ip / gDaysInYear)
                s_1_pd[j] = payoff_discounted

        for ip in range(1, n+1):
            s_2[ip] = s_2[ip-1] * np.exp((mu - v2 / 2.0) *
                                         dt - g[ip-1] * np.sqrt(dt) *
                                         volatility)
            if s_2[ip] < K2:
                syb_down_2 = 1

            if (obs_freq == TuringFrequencyTypes.MONTHLY and
                date_list[ip]._d == expiryDate._d and
                    s_2[ip] >= K1):
                syb_up_2 = 1
                payoff_discounted = (notional * coupon_rate * ip / gDaysInYear) * \
                    np.exp(-r * ip / gDaysInYear)
                s_2_pd[j] = payoff_discounted

                break

            if ip == n and syb_up_2 == 0 and syb_down_2 == 0:
                payoff_discounted = (notional * coupon_rate * ip / gDaysInYear) * \
                    np.exp(-r * ip / gDaysInYear)
                s_2_pd[j] = payoff_discounted
            elif ip == n and syb_up_2 == 0 and syb_down_2 == 1:
                payoff_discounted = -notional * (1 - s_2[ip] / S0) * \
                    np.exp(-r * ip / gDaysInYear)
                s_2_pd[j] = payoff_discounted

    return 0.5 * np.mean(s_1_pd + s_2_pd)


c = _valueMC_fast_NUMBA(K1 = 120,
                        K2 = 90,  # 敲入价格
                        obs_freq = TuringFrequencyTypes.MONTHLY, # 敲出观察日
                        notional = 1000000,
                        valueDate = TuringDate(2020,2,12),
                        expiryDate = TuringDate(2021,2,12),
                        stockPrice = 100,
                        interestRate = 0.02,
                        dividendYield = 0,
                        volatility =0.1,
                        numPaths = 10000,
                        seed = 4242,
                        coupon_rate = 0.3)
# print(c)
