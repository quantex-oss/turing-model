import time
from random import random

from turing_models.instruments.yr import YuanRongDemo
from turing_models.instruments.knockout_option import KnockOutOption
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_types import TuringOptionType


options = []

for i in range(100):
    expiry = TuringDate(2021, 8, 28).addDays(i)
    strike_price = 5 + random() * 0.5
    underlier = 'STOCKCN0000' + str(1000+i)
    barrier = strike_price + 0.3
    rebate = 0.1 + random() * 0.1
    option = KnockOutOption(option_type=TuringOptionType.CALL,
                            underlier=underlier,
                            expiry=expiry,
                            strike_price=strike_price,
                            participation_rate=1.0,
                            barrier=barrier,
                            notional=1000000,
                            rebate=rebate,
                            stock_price=4.9,
                            volatility=0.22,
                            interest_rate=0.02,
                            dividend_yield=0)
    options.append(option)
print(len(options))
time_start = time.time()
YuanRongDemo.init()
for eq_ in YuanRongDemo(options, 3)():
    print(eq_[0][0] + "_" + eq_[0][1] + ":", eq_[1])

time_end = time.time()
print("耗时：", time_end - time_start)

# scenario_extreme = PricingContext(pricing_date='20210716',
#                                   spot=[
#                                       {"asset_id": "STOCKCN00000001", "value": 5.2},
#                                       {"asset_id": "STOCKCN00000002", "value": 5.3},
#                                       {"asset_id": "STOCKCN00000003", "value": 3.5},
#                                       {"asset_id": "STOCKCN00000004", "value": 3.5},
#                                       {"asset_id": "STOCKCN00000005", "value": 16.2},
#                                       {"asset_id": "STOCKCN00000006", "value": 3.3},
#                                       {"asset_id": "STOCKCN00000007", "value": 50},
#                                       {"asset_id": "STOCKCN00000008", "value": 5},
#                                       {"asset_id": "STOCKCN00000009", "value": 45},
#                                       {"asset_id": "STOCKCN000000010", "value": 5.45},
#                                       {"asset_id": "STOCKCN000000011", "value": 32},
#                                       {"asset_id": "STOCKCN000000012", "value": 1},
#                                   ],
#                                   volatility=[
#                                       {"asset_id": "STOCKCN00000001", "value": 0.2},
#                                       {"asset_id": "STOCKCN00000002", "value": 0.2},
#                                       {"asset_id": "STOCKCN00000003", "value": 0.2},
#                                       {"asset_id": "STOCKCN00000004", "value": 0.2}
#                                   ]
#                                   )
#
# with scenario_extreme:
#     for eq_ in YuanRong(options)():
#         print(eq_[0][0] + "_" + eq_[0][1] + ":", eq_[1])
#
#     time_end = time.time()
#     print("耗时：", time_end - time_start)
