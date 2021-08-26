import time
from fundamental.market.constants import dates, rates
from fundamental.pricing_context import PricingContext
from turing_models.utilities.global_types import TuringOptionType
from turing_models.utilities.turing_date import TuringDate
from turing_models.instruments.european_option import EuropeanOption
from turing_models.instruments.common import RiskMeasure, Currency
from turing_models.instruments.combination_calc import CombinationCalc, ModelCalc
from turing_models.constants import ParallelType


european_option1 = EuropeanOption(asset_id='OPTIONCN00000001',
                                  underlier='STOCKCN00000001',
                                  option_type=TuringOptionType.CALL,
                                  start_date=TuringDate(2021, 6, 3),
                                  expiry=TuringDate(2021, 9, 3),
                                  strike_price=5.3,
                                  multiplier=100,
                                  value_date=TuringDate(2021, 8, 13),
                                  currency=Currency.CNY,
                                  stock_price=5.262,
                                  volatility=0.1,
                                  zero_dates=dates,
                                  zero_rates=rates,
                                  dividend_yield=0)

european_option2 = EuropeanOption(asset_id='OPTIONCN00000002',
                                  underlier='STOCKCN00000001',
                                  option_type=TuringOptionType.CALL,
                                  start_date=TuringDate(2021, 6, 3),
                                  expiry=TuringDate(2021, 9, 3),
                                  strike_price=5.28,
                                  multiplier=100,
                                  value_date=TuringDate(2021, 8, 13),
                                  currency=Currency.CNY,
                                  stock_price=5.262,
                                  volatility=0.15,
                                  zero_dates=dates,
                                  zero_rates=rates,
                                  dividend_yield=0)


scenario_extreme = PricingContext(pricing_date='20210716',
                                  spot=[
                                      {"asset_id": "STOCKCN00000001", "value": 5.2},
                                      {"asset_id": "STOCKCN00000002", "value": 5.3},
                                      {"asset_id": "STOCKCN00000003", "value": 3.5},
                                      {"asset_id": "STOCKCN00000004", "value": 3.5},
                                      {"asset_id": "STOCKCN00000005", "value": 16.2},
                                      {"asset_id": "STOCKCN00000006", "value": 3.3},
                                      {"asset_id": "STOCKCN00000007", "value": 50},
                                      {"asset_id": "STOCKCN00000008", "value": 5},
                                      {"asset_id": "STOCKCN00000009", "value": 45},
                                      {"asset_id": "STOCKCN000000010", "value": 5.45},
                                      {"asset_id": "STOCKCN000000011", "value": 32},
                                      {"asset_id": "STOCKCN000000012", "value": 1},
                                  ],
                                  volatility=[
                                      {"asset_id": "STOCKCN00000001", "value": 0.2},
                                      {"asset_id": "STOCKCN00000002", "value": 0.2},
                                      {"asset_id": "STOCKCN00000003", "value": 0.2},
                                      {"asset_id": "STOCKCN00000004", "value": 0.2}
                                  ]
                                  )


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
    european_option1,
    risk_measures=risk_measures,
    title="european_option1",  # 可选参数，不传在结果相关的打印中会取类名
)

model_calc2 = ModelCalc(
    european_option1,
    risk_measures=risk_measures,
    title="european_option2",  # 可选参数，不传在结果相关的打印中会取类名
)


with scenario_extreme:
    time_start = time.time()
    cms = CombinationCalc(
        source_list=[model_calc1],
        # parallel_type为可选参数，可以指定走元戎并
        # 行计算或内部并行计算或者不走并行计算，默认值
        # 为None，表示不进行并行计算，可不指定。
        parallel_type=ParallelType.NULL.value,
        timeout=3
    )
    cms.add(model_calc2)
    result = cms.run()
    time_end = time.time()
    print("耗时：", time_end - time_start)
    print(result)
