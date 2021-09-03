import time


from fundamental.pricing_context import PricingContext

from turing_models.utilities.turing_date import TuringDate
from turing_models.instruments.european_option import EuropeanOption
from turing_models.instruments.snowball_option import SnowballOption
from turing_models.instruments.knockout_option import KnockOutOption
from turing_models.instruments.common import RiskMeasure


USE_YR = True
if USE_YR:
    import yuanrong
    yuanrong.init(
        package_ref='sn:cn:yrk:12345678901234561234567890123456:function:0-turing-model:$latest',
        logging_level='INFO', cluster_server_addr='123.60.60.83'
    )


def get_result(call, use_yr=False):
    if use_yr:
        if isinstance(call, list):
            print(call)
            return yuanrong.get(call)
        return yuanrong.get([call])[0]
    else:
        return call


def print_result(result):
    print(f"price(european_option1): {result[0]}\n"
          f"delta(european_option1): {result[1]}\n"
          f"gamma(european_option1): {result[2]}\n"
          f"vega(european_option1): {result[3]}\n"
          f"theta(european_option1): {result[4]}\n"
          f"rho(european_option1): {result[5]}\n"
          f"rho_q(european_option1): {result[6]}\n"
          f"price(european_option2): {result[7]}\n"
          f"delta(european_option2): {result[8]}\n"
          f"gamma(european_option2): {result[9]}\n"
          f"vega(european_option2): {result[10]}\n"
          f"theta(european_option2): {result[11]}\n"
          f"rho(european_option2): {result[12]}\n"
          f"rho_q(european_option2): {result[13]}\n"
          f"price(european_option3): {result[14]}\n"
          f"delta(european_option3): {result[15]}\n"
          f"gamma(european_option3): {result[16]}\n"
          f"vega(european_option3): {result[17]}\n"
          f"theta(european_option3): {result[18]}\n"
          f"rho(european_option3): {result[19]}\n"
          f"rho_q(european_option3): {result[20]}\n"
          f"price(european_option4): {result[21]}\n"
          f"delta(european_option4): {result[22]}\n"
          f"gamma(european_option4): {result[23]}\n"
          f"vega(european_option4): {result[24]}\n"
          f"theta(european_option4): {result[25]}\n"
          f"rho(european_option4): {result[26]}\n"
          f"rho_q(european_option4): {result[27]}\n"
          f"price(snowball_option1): {result[28]}\n"
          f"delta(snowball_option1): {result[29]}\n"
          f"gamma(snowball_option1): {result[30]}\n"
          f"vega(snowball_option1): {result[31]}\n"
          f"theta(snowball_option1): {result[32]}\n"
          f"rho(snowball_option1): {result[33]}\n"
          f"rho_q(snowball_option1): {result[34]}\n"
          f"price(snowball_option2): {result[35]}\n"
          f"delta(snowball_option2): {result[36]}\n"
          f"gamma(snowball_option2): {result[37]}\n"
          f"vega(snowball_option2): {result[38]}\n"
          f"theta(snowball_option2): {result[39]}\n"
          f"rho(snowball_option2): {result[40]}\n"
          f"rho_q(snowball_option2): {result[41]}\n"
          f"price(snowball_option3): {result[42]}\n"
          f"delta(snowball_option3): {result[43]}\n"
          f"gamma(snowball_option3): {result[44]}\n"
          f"vega(snowball_option3): {result[45]}\n"
          f"theta(snowball_option3): {result[46]}\n"
          f"rho(snowball_option3): {result[47]}\n"
          f"rho_q(snowball_option3): {result[48]}\n"
          f"price(snowball_option4): {result[49]}\n"
          f"delta(snowball_option4): {result[50]}\n"
          f"gamma(snowball_option4): {result[51]}\n"
          f"vega(snowball_option4): {result[52]}\n"
          f"theta(snowball_option4): {result[53]}\n"
          f"rho(snowball_option4): {result[54]}\n"
          f"rho_q(snowball_option4): {result[55]}\n"
          f"price(snowball_option5): {result[56]}\n"
          f"delta(snowball_option5): {result[57]}\n"
          f"gamma(snowball_option5): {result[58]}\n"
          f"vega(snowball_option5): {result[59]}\n"
          f"theta(snowball_option5): {result[60]}\n"
          f"rho(snowball_option5): {result[61]}\n"
          f"rho_q(snowball_option5): {result[62]}\n"
          f"price(knockout_option1): {result[63]}\n"
          f"delta(knockout_option1): {result[64]}\n"
          f"gamma(knockout_option1): {result[65]}\n"
          f"vega(knockout_option1): {result[66]}\n"
          f"theta(knockout_option1): {result[67]}\n"
          f"rho(knockout_option1): {result[68]}\n"
          f"rho_q(knockout_option1): {result[69]}\n"
          f"price(knockout_option2): {result[70]}\n"
          f"delta(knockout_option2): {result[71]}\n"
          f"gamma(knockout_option2): {result[72]}\n"
          f"vega(knockout_option2): {result[73]}\n"
          f"theta(knockout_option2): {result[74]}\n"
          f"rho(knockout_option2): {result[75]}\n"
          f"rho_q(knockout_option2): {result[76]}\n"
          f"price(knockout_option3): {result[77]}\n"
          f"delta(knockout_option3): {result[78]}\n"
          f"gamma(knockout_option3): {result[79]}\n"
          f"vega(knockout_option3): {result[80]}\n"
          f"theta(knockout_option3): {result[81]}\n"
          f"rho(knockout_option3): {result[82]}\n"
          f"rho_q(knockout_option3): {result[83]}\n"
          f"price(knockout_option4): {result[84]}\n"
          f"delta(knockout_option4): {result[85]}\n"
          f"gamma(knockout_option4): {result[86]}\n"
          f"vega(knockout_option4): {result[87]}\n"
          f"theta(knockout_option4): {result[88]}\n"
          f"rho(knockout_option4): {result[89]}\n"
          f"rho_q(knockout_option4): {result[90]}\n"
          f"price(knockout_option5): {result[91]}\n"
          f"delta(knockout_option5): {result[92]}\n"
          f"gamma(knockout_option5): {result[93]}\n"
          f"vega(knockout_option5): {result[94]}\n"
          f"theta(knockout_option5): {result[95]}\n"
          f"rho(knockout_option5): {result[96]}\n"
          f"rho_q(knockout_option5): {result[97]}\n"
          f"price(knockout_option6): {result[98]}\n"
          f"delta(knockout_option6): {result[99]}\n")


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

time_start = time.time()
id_list = [european_option1.calc(RiskMeasure.Price, USE_YR),
           european_option1.calc(RiskMeasure.EqDelta, USE_YR),
           european_option1.calc(RiskMeasure.EqGamma, USE_YR),
           european_option1.calc(RiskMeasure.EqVega, USE_YR),
           european_option1.calc(RiskMeasure.EqTheta, USE_YR),
           european_option1.calc(RiskMeasure.EqRho, USE_YR),
           european_option1.calc(RiskMeasure.EqRhoQ, USE_YR),
           european_option2.calc(RiskMeasure.Price, USE_YR),
           european_option2.calc(RiskMeasure.EqDelta, USE_YR),
           european_option2.calc(RiskMeasure.EqGamma, USE_YR),
           european_option2.calc(RiskMeasure.EqVega, USE_YR),
           european_option2.calc(RiskMeasure.EqTheta, USE_YR),
           european_option2.calc(RiskMeasure.EqRho, USE_YR),
           european_option2.calc(RiskMeasure.EqRhoQ, USE_YR),
           european_option3.calc(RiskMeasure.Price, USE_YR),
           european_option3.calc(RiskMeasure.EqDelta, USE_YR),
           european_option3.calc(RiskMeasure.EqGamma, USE_YR),
           european_option3.calc(RiskMeasure.EqVega, USE_YR),
           european_option3.calc(RiskMeasure.EqTheta, USE_YR),
           european_option3.calc(RiskMeasure.EqRho, USE_YR),
           european_option3.calc(RiskMeasure.EqRhoQ, USE_YR),
           european_option4.calc(RiskMeasure.Price, USE_YR),
           european_option4.calc(RiskMeasure.EqDelta, USE_YR),
           european_option4.calc(RiskMeasure.EqGamma, USE_YR),
           european_option4.calc(RiskMeasure.EqVega, USE_YR),
           european_option4.calc(RiskMeasure.EqTheta, USE_YR),
           european_option4.calc(RiskMeasure.EqRho, USE_YR),
           european_option4.calc(RiskMeasure.EqRhoQ, USE_YR),
           snowball_option1.calc(RiskMeasure.EqDelta, USE_YR),
           snowball_option1.calc(RiskMeasure.EqGamma, USE_YR),
           snowball_option1.calc(RiskMeasure.EqVega, USE_YR),
           snowball_option1.calc(RiskMeasure.EqTheta, USE_YR),
           snowball_option1.calc(RiskMeasure.Price, USE_YR),
           snowball_option1.calc(RiskMeasure.EqRho, USE_YR),
           snowball_option1.calc(RiskMeasure.EqRhoQ, USE_YR),
           snowball_option2.calc(RiskMeasure.Price, USE_YR),
           snowball_option2.calc(RiskMeasure.EqDelta, USE_YR),
           snowball_option2.calc(RiskMeasure.EqGamma, USE_YR),
           snowball_option2.calc(RiskMeasure.EqVega, USE_YR),
           snowball_option2.calc(RiskMeasure.EqTheta, USE_YR),
           snowball_option2.calc(RiskMeasure.EqRho, USE_YR),
           snowball_option2.calc(RiskMeasure.EqRhoQ, USE_YR),
           snowball_option3.calc(RiskMeasure.Price, USE_YR),
           snowball_option3.calc(RiskMeasure.EqDelta, USE_YR),
           snowball_option3.calc(RiskMeasure.EqGamma, USE_YR),
           snowball_option3.calc(RiskMeasure.EqVega, USE_YR),
           snowball_option3.calc(RiskMeasure.EqTheta, USE_YR),
           snowball_option3.calc(RiskMeasure.EqRho, USE_YR),
           snowball_option3.calc(RiskMeasure.EqRhoQ, USE_YR),
           snowball_option4.calc(RiskMeasure.Price, USE_YR),
           snowball_option4.calc(RiskMeasure.EqDelta, USE_YR),
           snowball_option4.calc(RiskMeasure.EqGamma, USE_YR),
           snowball_option4.calc(RiskMeasure.EqVega, USE_YR),
           snowball_option4.calc(RiskMeasure.EqTheta, USE_YR),
           snowball_option4.calc(RiskMeasure.EqRho, USE_YR),
           snowball_option4.calc(RiskMeasure.EqRhoQ, USE_YR),
           snowball_option5.calc(RiskMeasure.Price, USE_YR),
           snowball_option5.calc(RiskMeasure.EqDelta, USE_YR),
           snowball_option5.calc(RiskMeasure.EqGamma, USE_YR),
           snowball_option5.calc(RiskMeasure.EqVega, USE_YR),
           snowball_option5.calc(RiskMeasure.EqTheta, USE_YR),
           snowball_option5.calc(RiskMeasure.EqRho, USE_YR),
           snowball_option5.calc(RiskMeasure.EqRhoQ, USE_YR),
           knockout_option1.calc(RiskMeasure.EqDelta, USE_YR),
           knockout_option1.calc(RiskMeasure.EqGamma, USE_YR),
           knockout_option1.calc(RiskMeasure.EqVega, USE_YR),
           knockout_option1.calc(RiskMeasure.EqTheta, USE_YR),
           knockout_option1.calc(RiskMeasure.Price, USE_YR),
           knockout_option1.calc(RiskMeasure.EqRho, USE_YR),
           knockout_option1.calc(RiskMeasure.EqRhoQ, USE_YR),
           knockout_option2.calc(RiskMeasure.Price, USE_YR),
           knockout_option2.calc(RiskMeasure.EqDelta, USE_YR),
           knockout_option2.calc(RiskMeasure.EqGamma, USE_YR),
           knockout_option2.calc(RiskMeasure.EqVega, USE_YR),
           knockout_option2.calc(RiskMeasure.EqTheta, USE_YR),
           knockout_option2.calc(RiskMeasure.EqRho, USE_YR),
           knockout_option2.calc(RiskMeasure.EqRhoQ, USE_YR),
           knockout_option3.calc(RiskMeasure.Price, USE_YR),
           knockout_option3.calc(RiskMeasure.EqDelta, USE_YR),
           knockout_option3.calc(RiskMeasure.EqGamma, USE_YR),
           knockout_option3.calc(RiskMeasure.EqVega, USE_YR),
           knockout_option3.calc(RiskMeasure.EqTheta, USE_YR),
           knockout_option3.calc(RiskMeasure.EqRho, USE_YR),
           knockout_option3.calc(RiskMeasure.EqRhoQ, USE_YR),
           knockout_option4.calc(RiskMeasure.Price, USE_YR),
           knockout_option4.calc(RiskMeasure.EqDelta, USE_YR),
           knockout_option4.calc(RiskMeasure.EqGamma, USE_YR),
           knockout_option4.calc(RiskMeasure.EqVega, USE_YR),
           knockout_option4.calc(RiskMeasure.EqTheta, USE_YR),
           knockout_option4.calc(RiskMeasure.EqRho, USE_YR),
           knockout_option4.calc(RiskMeasure.EqRhoQ, USE_YR),
           knockout_option5.calc(RiskMeasure.Price, USE_YR),
           knockout_option5.calc(RiskMeasure.EqDelta, USE_YR),
           knockout_option5.calc(RiskMeasure.EqGamma, USE_YR),
           knockout_option5.calc(RiskMeasure.EqVega, USE_YR),
           knockout_option5.calc(RiskMeasure.EqTheta, USE_YR),
           knockout_option5.calc(RiskMeasure.EqRho, USE_YR),
           knockout_option5.calc(RiskMeasure.EqRhoQ, USE_YR),
           knockout_option6.calc(RiskMeasure.Price, USE_YR),
           knockout_option6.calc(RiskMeasure.EqDelta, USE_YR)]
# print(get_result(knockout_option.calc(RiskMeasure.Price)))  # 传单个
result = get_result(id_list, USE_YR)  # 传list
time_end = time.time()
print("耗时：", time_end - time_start)
print_result(result)


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
    id_list = [european_option1.calc(RiskMeasure.Price, USE_YR),
               european_option1.calc(RiskMeasure.EqDelta, USE_YR),
               european_option1.calc(RiskMeasure.EqGamma, USE_YR),
               european_option1.calc(RiskMeasure.EqVega, USE_YR),
               european_option1.calc(RiskMeasure.EqTheta, USE_YR),
               european_option1.calc(RiskMeasure.EqRho, USE_YR),
               european_option1.calc(RiskMeasure.EqRhoQ, USE_YR),
               european_option2.calc(RiskMeasure.Price, USE_YR),
               european_option2.calc(RiskMeasure.EqDelta, USE_YR),
               european_option2.calc(RiskMeasure.EqGamma, USE_YR),
               european_option2.calc(RiskMeasure.EqVega, USE_YR),
               european_option2.calc(RiskMeasure.EqTheta, USE_YR),
               european_option2.calc(RiskMeasure.EqRho, USE_YR),
               european_option2.calc(RiskMeasure.EqRhoQ, USE_YR),
               european_option3.calc(RiskMeasure.Price, USE_YR),
               european_option3.calc(RiskMeasure.EqDelta, USE_YR),
               european_option3.calc(RiskMeasure.EqGamma, USE_YR),
               european_option3.calc(RiskMeasure.EqVega, USE_YR),
               european_option3.calc(RiskMeasure.EqTheta, USE_YR),
               european_option3.calc(RiskMeasure.EqRho, USE_YR),
               european_option3.calc(RiskMeasure.EqRhoQ, USE_YR),
               european_option4.calc(RiskMeasure.Price, USE_YR),
               european_option4.calc(RiskMeasure.EqDelta, USE_YR),
               european_option4.calc(RiskMeasure.EqGamma, USE_YR),
               european_option4.calc(RiskMeasure.EqVega, USE_YR),
               european_option4.calc(RiskMeasure.EqTheta, USE_YR),
               european_option4.calc(RiskMeasure.EqRho, USE_YR),
               european_option4.calc(RiskMeasure.EqRhoQ, USE_YR),
               snowball_option1.calc(RiskMeasure.EqDelta, USE_YR),
               snowball_option1.calc(RiskMeasure.EqGamma, USE_YR),
               snowball_option1.calc(RiskMeasure.EqVega, USE_YR),
               snowball_option1.calc(RiskMeasure.EqTheta, USE_YR),
               snowball_option1.calc(RiskMeasure.Price, USE_YR),
               snowball_option1.calc(RiskMeasure.EqRho, USE_YR),
               snowball_option1.calc(RiskMeasure.EqRhoQ, USE_YR),
               snowball_option2.calc(RiskMeasure.Price, USE_YR),
               snowball_option2.calc(RiskMeasure.EqDelta, USE_YR),
               snowball_option2.calc(RiskMeasure.EqGamma, USE_YR),
               snowball_option2.calc(RiskMeasure.EqVega, USE_YR),
               snowball_option2.calc(RiskMeasure.EqTheta, USE_YR),
               snowball_option2.calc(RiskMeasure.EqRho, USE_YR),
               snowball_option2.calc(RiskMeasure.EqRhoQ, USE_YR),
               snowball_option3.calc(RiskMeasure.Price, USE_YR),
               snowball_option3.calc(RiskMeasure.EqDelta, USE_YR),
               snowball_option3.calc(RiskMeasure.EqGamma, USE_YR),
               snowball_option3.calc(RiskMeasure.EqVega, USE_YR),
               snowball_option3.calc(RiskMeasure.EqTheta, USE_YR),
               snowball_option3.calc(RiskMeasure.EqRho, USE_YR),
               snowball_option3.calc(RiskMeasure.EqRhoQ, USE_YR),
               snowball_option4.calc(RiskMeasure.Price, USE_YR),
               snowball_option4.calc(RiskMeasure.EqDelta, USE_YR),
               snowball_option4.calc(RiskMeasure.EqGamma, USE_YR),
               snowball_option4.calc(RiskMeasure.EqVega, USE_YR),
               snowball_option4.calc(RiskMeasure.EqTheta, USE_YR),
               snowball_option4.calc(RiskMeasure.EqRho, USE_YR),
               snowball_option4.calc(RiskMeasure.EqRhoQ, USE_YR),
               snowball_option5.calc(RiskMeasure.Price, USE_YR),
               snowball_option5.calc(RiskMeasure.EqDelta, USE_YR),
               snowball_option5.calc(RiskMeasure.EqGamma, USE_YR),
               snowball_option5.calc(RiskMeasure.EqVega, USE_YR),
               snowball_option5.calc(RiskMeasure.EqTheta, USE_YR),
               snowball_option5.calc(RiskMeasure.EqRho, USE_YR),
               snowball_option5.calc(RiskMeasure.EqRhoQ, USE_YR),
               knockout_option1.calc(RiskMeasure.EqDelta, USE_YR),
               knockout_option1.calc(RiskMeasure.EqGamma, USE_YR),
               knockout_option1.calc(RiskMeasure.EqVega, USE_YR),
               knockout_option1.calc(RiskMeasure.EqTheta, USE_YR),
               knockout_option1.calc(RiskMeasure.Price, USE_YR),
               knockout_option1.calc(RiskMeasure.EqRho, USE_YR),
               knockout_option1.calc(RiskMeasure.EqRhoQ, USE_YR),
               knockout_option2.calc(RiskMeasure.Price, USE_YR),
               knockout_option2.calc(RiskMeasure.EqDelta, USE_YR),
               knockout_option2.calc(RiskMeasure.EqGamma, USE_YR),
               knockout_option2.calc(RiskMeasure.EqVega, USE_YR),
               knockout_option2.calc(RiskMeasure.EqTheta, USE_YR),
               knockout_option2.calc(RiskMeasure.EqRho, USE_YR),
               knockout_option2.calc(RiskMeasure.EqRhoQ, USE_YR),
               knockout_option3.calc(RiskMeasure.Price, USE_YR),
               knockout_option3.calc(RiskMeasure.EqDelta, USE_YR),
               knockout_option3.calc(RiskMeasure.EqGamma, USE_YR),
               knockout_option3.calc(RiskMeasure.EqVega, USE_YR),
               knockout_option3.calc(RiskMeasure.EqTheta, USE_YR),
               knockout_option3.calc(RiskMeasure.EqRho, USE_YR),
               knockout_option3.calc(RiskMeasure.EqRhoQ, USE_YR),
               knockout_option4.calc(RiskMeasure.Price, USE_YR),
               knockout_option4.calc(RiskMeasure.EqDelta, USE_YR),
               knockout_option4.calc(RiskMeasure.EqGamma, USE_YR),
               knockout_option4.calc(RiskMeasure.EqVega, USE_YR),
               knockout_option4.calc(RiskMeasure.EqTheta, USE_YR),
               knockout_option4.calc(RiskMeasure.EqRho, USE_YR),
               knockout_option4.calc(RiskMeasure.EqRhoQ, USE_YR),
               knockout_option5.calc(RiskMeasure.Price, USE_YR),
               knockout_option5.calc(RiskMeasure.EqDelta, USE_YR),
               knockout_option5.calc(RiskMeasure.EqGamma, USE_YR),
               knockout_option5.calc(RiskMeasure.EqVega, USE_YR),
               knockout_option5.calc(RiskMeasure.EqTheta, USE_YR),
               knockout_option5.calc(RiskMeasure.EqRho, USE_YR),
               knockout_option5.calc(RiskMeasure.EqRhoQ, USE_YR),
               knockout_option6.calc(RiskMeasure.Price, USE_YR),
               knockout_option6.calc(RiskMeasure.EqDelta, USE_YR)]
    # print(get_result(knockout_option.calc(RiskMeasure.Price)))  # 传单个
    result = get_result(id_list, USE_YR)  # 传list
    time_end = time.time()
    print("耗时：", time_end - time_start)
    print_result(result)
