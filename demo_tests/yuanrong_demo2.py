import time

from turing_models.instruments.snowball_option import SnowballOption
from turing_models.market.data.china_money_yield_curve import dates, rates
from turing_models.utilities.global_types import TuringOptionType
from turing_models.utilities.turing_date import TuringDate
from turing_models.instruments.european_option import EuropeanOption
from turing_models.instruments.common import RiskMeasure, Currency
from turing_models.instruments.combination_calc import CombinationCalc, ModelCalc
from turing_models.constants import ParallelType


snowball_option1 = SnowballOption(asset_id='OPTIONCN00000001',
                                  option_type=TuringOptionType.CALL,
                                  start_date=TuringDate(2021, 6, 3),
                                  expiry=TuringDate(2021, 10, 3),
                                  participation_rate=1.0,
                                  barrier=5.5,
                                  knock_in_price=5.2,
                                  notional=1000000,
                                  rebate=0.2,
                                  initial_spot=5.2,
                                  untriggered_rebate=0.2,
                                  knock_in_type='SPREADS',
                                  knock_out_obs_days_whole=[TuringDate(2021, 6, 3), TuringDate(2021, 7, 5), TuringDate(2021, 8, 3), TuringDate(2021, 9, 3)],
                                  knock_in_strike1=5.3,
                                  knock_in_strike2=5.4,
                                  # value_date=TuringDate(2021, 8, 13),
                                  currency=Currency.CNY,
                                  stock_price=5.262,
                                  volatility=0.1,
                                  zero_dates=dates,
                                  zero_rates=rates,
                                  dividend_yield=0)

snowball_option2 = SnowballOption(asset_id='OPTIONCN00000001',
                                  option_type=TuringOptionType.CALL,
                                  start_date=TuringDate(2021, 6, 3),
                                  expiry=TuringDate(2021, 10, 3),
                                  participation_rate=1.0,
                                  barrier=5.5,
                                  knock_in_price=5.2,
                                  notional=1000000,
                                  rebate=0.2,
                                  initial_spot=5.2,
                                  untriggered_rebate=0.2,
                                  knock_in_type='SPREADS',
                                  knock_out_obs_days_whole=[TuringDate(2021, 6, 3), TuringDate(2021, 7, 5), TuringDate(2021, 8, 3), TuringDate(2021, 9, 3)],
                                  knock_in_strike1=5.3,
                                  knock_in_strike2=5.4,
                                  # value_date=TuringDate(2021, 8, 13),
                                  currency=Currency.CNY,
                                  stock_price=5.4,
                                  volatility=0.1,
                                  zero_dates=dates,
                                  zero_rates=rates,
                                  dividend_yield=0)

risk_measures = [
    RiskMeasure.Price,
    RiskMeasure.EqDelta,
    RiskMeasure.EqGamma,
    RiskMeasure.EqVega,
    RiskMeasure.EqTheta,
    RiskMeasure.EqRho,
    RiskMeasure.EqRhoQ
]


model_calc1 = ModelCalc(
    snowball_option1,
    risk_measures=risk_measures,
    title="european_option1",  # 可选参数，不传在结果相关的打印中会取类名
)

model_calc2 = ModelCalc(
    snowball_option1,
    risk_measures=risk_measures,
    title="european_option2",  # 可选参数，不传在结果相关的打印中会取类名
)


time_start = time.time()
cms = CombinationCalc(
    source_list=[model_calc1],
    # parallel_type为可选参数，可以指定走元戎并
    # 行计算或内部并行计算或者不走并行计算，默认值
    # 为None，表示不进行并行计算，可不指定。
    parallel_type=ParallelType.NULL,
    timeout=3
)
cms.add(model_calc2)
result = cms.run()
time_end = time.time()
print("耗时：", time_end - time_start)
print(result)
