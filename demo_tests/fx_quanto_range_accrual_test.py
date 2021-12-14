import time

from fundamental.pricing_context import PricingContext

from turing_models.instruments.common import Currency, CurrencyPair, DayCountType
from turing_models.instruments.fx.fx_quanto_range_accrual import FXQuantoRangeAccrual
from turing_models.utilities.turing_date import TuringDate


value_date = TuringDate(2021, 11, 17)
inst = FXQuantoRangeAccrual(accrual_start=TuringDate(2021, 10, 29),
                            accrual_end=TuringDate(2022, 1, 31),
                            observe_start_date=TuringDate(2021, 10, 29),
                            observe_end_date=TuringDate(2022, 1, 27),
                            value_date=value_date,
                            underlier='FX000000XX',
                            underlier_symbol=CurrencyPair.EURUSD,
                            # range_up=1.19,
                            # range_down=1.15,
                            in_coupon=0.031,
                            out_coupon=0.015,
                            notional=10000000,
                            notional_currency=Currency.CNY,
                            day_count=DayCountType.Actual365Fixed)

scenario_extreme = PricingContext(
    # spot=[
    #     {"symbol": "USD/CNY", "value": 6.5}
    #     ]
)

if __name__ == '__main__':
    with scenario_extreme:
        time_start = time.time()
        price = inst.price()
        delta = inst.fx_delta()
        gamma = inst.fx_gamma()
        vega = inst.fx_vega()
        quantovega = inst.quanto_vega()
        corr_sens = inst.corr_sens()
        time_end = time.time()
        print('计算耗时：', time_end-time_start)

        print("price:", price, "delta:", delta, "gamma:",
              gamma, "vega:", vega, "quantovega:", quantovega, 'corr_sens:', corr_sens)
