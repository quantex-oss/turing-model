import time
import yuanrong
from fundamental.pricing_context import PricingContext
from turing_models.utilities.turing_date import TuringDate
from turing_models.instruments.european_option import EuropeanOption
from turing_models.instruments.snowball_option import SnowballOption
from turing_models.instruments.knockout_option import KnockOutOption
from turing_models.instruments.common import RiskMeasure

USE_YR = False
if USE_YR:
    yuanrong.init(
        package_ref='sn:cn:yrk:12345678901234561234567890123456:function:0-turing-model:$latest',
        logging_level='INFO', cluster_server_addr='123.60.60.83'
    )


def get_result(call, use_yr=False):
    if use_yr:
        if isinstance(call, list):
            return yuanrong.get(call)
        return yuanrong.get([call])[0]
    else:
        return call


european_option1 = EuropeanOption(asset_id='OPTIONCN00000001',
                                  option_type='CALL',
                                  underlier='STOCKCN00000001',
                                  expiry=TuringDate(2021, 10, 15),
                                  strike_price=5.3,
                                  multiplier=100,
                                  stock_price=5.262,
                                  volatility=0.1,
                                  interest_rate=0.02,
                                  dividend_yield=0)

european_option2 = EuropeanOption(asset_id='OPTIONCN00000002',
                                  option_type='CALL',
                                  underlier='STOCKCN00000002',
                                  expiry=TuringDate(2021, 9, 15),
                                  strike_price=5.3,
                                  multiplier=100,
                                  stock_price=5.362,
                                  volatility=0.15,
                                  interest_rate=0.02,
                                  dividend_yield=0)

european_option3 = EuropeanOption(asset_id='OPTIONCN00000003',
                                  option_type='CALL',
                                  underlier='STOCKCN00000003',
                                  expiry=TuringDate(2021, 8, 30),
                                  strike_price=3.3,
                                  multiplier=100,
                                  stock_price=3.3,
                                  volatility=0.2,
                                  interest_rate=0.02,
                                  dividend_yield=0)

european_option4 = EuropeanOption(asset_id='OPTIONCN00000004',
                                  option_type='CALL',
                                  underlier='STOCKCN00000004',
                                  expiry=TuringDate(2021, 9, 30),
                                  strike_price=3.5,
                                  multiplier=100,
                                  stock_price=3.8,
                                  volatility=0.25,
                                  interest_rate=0.02,
                                  dividend_yield=0)

snowball_option1 = SnowballOption(asset_id='OPTIONCN00000005',
                                  option_type='CALL',
                                  underlier='STOCKCN00000005',
                                  expiry=TuringDate(2022, 2, 15),
                                  participation_rate=1.0,
                                  barrier=20,
                                  knock_in_price=16,
                                  notional=1000000,
                                  rebate=0.15,
                                  knock_in_type='return',
                                  stock_price=16.5,
                                  volatility=0.1,
                                  interest_rate=0.02,
                                  dividend_yield=0)

snowball_option2 = SnowballOption(asset_id='OPTIONCN00000006',
                                  option_type='CALL',
                                  underlier='STOCKCN00000006',
                                  expiry=TuringDate(2021, 10, 15),
                                  participation_rate=1.0,
                                  barrier=3.4,
                                  knock_in_price=2.5,
                                  notional=1000000,
                                  rebate=0.14,
                                  knock_in_type='return',
                                  stock_price=3,
                                  volatility=0.12,
                                  interest_rate=0.02,
                                  dividend_yield=0)

snowball_option3 = SnowballOption(asset_id='OPTIONCN00000007',
                                  option_type='CALL',
                                  underlier='STOCKCN00000007',
                                  expiry=TuringDate(2021, 9, 15),
                                  participation_rate=1.0,
                                  barrier=55,
                                  knock_in_price=45,
                                  notional=1000000,
                                  rebate=0.13,
                                  knock_in_type='return',
                                  stock_price=40,
                                  volatility=0.15,
                                  interest_rate=0.02,
                                  dividend_yield=0)

snowball_option4 = SnowballOption(asset_id='OPTIONCN00000008',
                                  option_type='CALL',
                                  underlier='STOCKCN00000008',
                                  expiry=TuringDate(2021, 11, 11),
                                  participation_rate=1.0,
                                  barrier=5.5,
                                  knock_in_price=4.7,
                                  notional=1000000,
                                  rebate=0.12,
                                  knock_in_type='return',
                                  stock_price=4.8,
                                  volatility=0.17,
                                  interest_rate=0.02,
                                  dividend_yield=0)

snowball_option5 = SnowballOption(asset_id='OPTIONCN00000009',
                                  option_type='CALL',
                                  underlier='STOCKCN00000009',
                                  expiry=TuringDate(2022, 2, 1),
                                  participation_rate=1.0,
                                  barrier=50,
                                  knock_in_price=35,
                                  notional=1000000,
                                  rebate=0.12,
                                  knock_in_type='return',
                                  stock_price=40,
                                  volatility=0.2,
                                  interest_rate=0.02,
                                  dividend_yield=0)

knockout_option1 = KnockOutOption(asset_id='OPTIONCN00000010',
                                  option_type='CALL',
                                  underlier='STOCKCN00000010',
                                  knock_out_type='up_and_out',
                                  expiry=TuringDate(2022, 2, 12),
                                  strike_price=5.5,
                                  participation_rate=1.0,
                                  barrier=6,
                                  notional=1000000,
                                  rebate=0.1,
                                  stock_price=5.4,
                                  volatility=0.1,
                                  interest_rate=0.02,
                                  dividend_yield=0)

knockout_option2 = KnockOutOption(asset_id='OPTIONCN00000011',
                                  option_type='CALL',
                                  underlier='STOCKCN00000011',
                                  knock_out_type='up_and_out',
                                  expiry=TuringDate(2021, 12, 12),
                                  strike_price=30,
                                  participation_rate=1.0,
                                  barrier=34,
                                  notional=1000000,
                                  rebate=0.1,
                                  stock_price=31,
                                  volatility=0.12,
                                  interest_rate=0.02,
                                  dividend_yield=0)

knockout_option3 = KnockOutOption(asset_id='OPTIONCN00000012',
                                  option_type='CALL',
                                  underlier='STOCKCN00000012',
                                  knock_out_type='up_and_out',
                                  expiry=TuringDate(2021, 9, 15),
                                  strike_price=1.2,
                                  participation_rate=1.0,
                                  barrier=1.5,
                                  notional=1000000,
                                  rebate=0.1,
                                  stock_price=0.9,
                                  volatility=0.14,
                                  interest_rate=0.02,
                                  dividend_yield=0)

knockout_option4 = KnockOutOption(asset_id='OPTIONCN00000013',
                                  option_type='CALL',
                                  underlier='STOCKCN00000013',
                                  knock_out_type='up_and_out',
                                  expiry=TuringDate(2021, 10, 12),
                                  strike_price=55,
                                  participation_rate=1.0,
                                  barrier=60,
                                  notional=1000000,
                                  rebate=0.1,
                                  stock_price=59,
                                  volatility=0.16,
                                  interest_rate=0.02,
                                  dividend_yield=0)

knockout_option5 = KnockOutOption(asset_id='OPTIONCN00000014',
                                  option_type='CALL',
                                  underlier='STOCKCN00000014',
                                  knock_out_type='up_and_out',
                                  expiry=TuringDate(2021, 10, 30),
                                  strike_price=100,
                                  participation_rate=1.0,
                                  barrier=120,
                                  notional=1000000,
                                  rebate=0.1,
                                  stock_price=90,
                                  volatility=0.18,
                                  interest_rate=0.02,
                                  dividend_yield=0)

knockout_option6 = KnockOutOption(asset_id='OPTIONCN00000015',
                                  option_type='CALL',
                                  underlier='STOCKCN00000015',
                                  knock_out_type='up_and_out',
                                  expiry=TuringDate(2022, 1, 12),
                                  strike_price=5.1,
                                  participation_rate=1.0,
                                  barrier=5.3,
                                  notional=1000000,
                                  rebate=0.1,
                                  stock_price=5.1,
                                  volatility=0.22,
                                  interest_rate=0.02,
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

with scenario_extreme:
    time_start = time.time()
    id_list = [european_option1.calc(RiskMeasure.Price, USE_YR)]
    result = get_result(id_list, USE_YR)  # 传list
    print(f"result: {result}")
    time_end = time.time()
    print("耗时：", time_end - time_start)
