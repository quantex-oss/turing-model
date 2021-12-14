import time

import QuantLib as ql
from fundamental.pricing_context import PricingContext

from turing_models.instruments.common import Currency, CurrencyPair, DayCountType
from turing_models.instruments.fx.fx_quanto_digital import FXQuantoDigital
from turing_models.utilities.global_types import TuringOptionType
from turing_models.utilities.turing_date import TuringDate


value_date = TuringDate(2021, 11, 17)
inst = FXQuantoDigital(accrual_start=TuringDate(2021, 10, 29),
                       accrual_end=TuringDate(2022, 1, 31),
                       observe_start_date=TuringDate(2021, 10, 29),
                       observe_end_date=TuringDate(2022, 1, 27),
                       value_date=value_date,
                       underlier='FX000000XX',
                       underlier_symbol=CurrencyPair.EURUSD,
                       # strike=1.22175,
                       coupon_rate=0.015,
                       notional=10000000,
                       # correlation_fd_dq=-0.18,
                       notional_currency=Currency.CNY,
                       option_type=TuringOptionType.CALL,
                       day_count=DayCountType.Actual365Fixed)

scenario_extreme = PricingContext(
    # spot=[
    #     {"symbol": "USD/CNY", "value": 6.5}
    #     ]
)

if __name__ == '__main__':
    # print(inst.domestic_discount_curve_f_d.discount(ql.Date(27, 1, 2022)))
    # print(inst.foreign_discount_curve_f_d.discount(ql.Date(27, 1, 2022)))
    # print(inst.domestic_discount_curve_d_q.discount(ql.Date(27, 1, 2022)))
    # print(inst.fx_forward_curve_f_d.discount(ql.Date(27, 1, 2022)))
    with scenario_extreme:
        time_start = time.time()
        price = inst.price()
        delta = inst.fx_delta()
        gamma = inst.fx_gamma()
        vega = inst.fx_vega()
        quantovega = inst.quanto_vega()
        corr_sens = inst.corr_sens()
        time_end = time.time()
        print('计算耗时：', time_end - time_start)

        print("price:", price, "delta:", delta, "gamma:",
              gamma, "vega:", vega, "quantovega:", quantovega, 'corr_sens:', corr_sens)
