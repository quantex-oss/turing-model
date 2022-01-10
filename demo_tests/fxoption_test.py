from fundamental.pricing_context import PricingContext

from turing_models.instruments.common import Currency, CurrencyPair, RiskMeasure
from turing_models.instruments.fx.fx_vanilla_option import FXVanillaOption
from turing_models.utilities.global_types import OptionType, TuringExerciseType
from turing_models.utilities.turing_date import TuringDate


today = TuringDate(2021, 8, 20)
# 初始化一个外汇香草期权
fxoption = FXVanillaOption(start_date=TuringDate(2021, 5, 18),
                           expiry=TuringDate(2022, 4, 28),
                           value_date=today,
                           underlier_symbol=CurrencyPair.USDCNY,
                           strike=7.45,
                           notional=20000000,
                           notional_currency=Currency.USD,
                           option_type=OptionType.CALL,
                           exercise_type=TuringExerciseType.EUROPEAN,
                           premium_currency=Currency.CNY)
# 需要计算的RiskMeasure
risk_measure = [RiskMeasure.Price, RiskMeasure.FxDelta, RiskMeasure.FxGamma, RiskMeasure.FxVega,
                RiskMeasure.FxTheta, RiskMeasure.FxVanna, RiskMeasure.FxVolga]
print("默认情况下，从TuringDB获取2021年8月20日的汇率和曲线等数据")
price, delta, gamma, vega, theta, vanna, volga = fxoption.calc(risk_measure)
print("price:", price, "delta:", delta, "gamma:", gamma,
      "vega:", vega, "theta:", theta, "vanna", vanna, "volga", volga)

print("通过what-if传入2021年8月20日的汇率和曲线数据")
scenario_extreme = PricingContext(
    # pricing_date=today,
    spot=[
        {"symbol": "USD/CNY", "value": 6.5}
    ],
    # fx_implied_volatility_curve=[
    #     {"symbol": "USD/CNY", "value": {
    #         "tenor": [0.003, 0.021, 0.042, 0.0625, 0.083, 0.17, 0.25, 0.5, 0.75, 1, 1.5, 2, 3],
    #         "origin_tenor": ["1D", "1W", "2W", "3W", "1M", "2M", "3M", "6M", "9M", "1Y", "18M", "2Y", "3Y"],
    #         "ATM": [0.033562, 0.036, 0.037, 0.038, 0.04, 0.041, 0.04238, 0.04425, 0.0453, 0.0458, 0.0435, 0.044, 0.044],
    #         "25D BF": [0.003391, 0.00125, 0.00125, 0.00125, 0.00225, 0.00175, 0.00238, 0.00275, 0.003, 0.00325, 0.00362, 0.004, 0.004],
    #         "25D RR": [0.002304, 0.003, 0.003, 0.003, 0.00325, 0.0035, 0.005, 0.00525, 0.006, 0.00625, 0.006, 0.0065, 0.00875],
    #         "10D BF": [0.004842, 0.00175, 0.00175, 0.002, 0.003, 0.004, 0.0045, 0.0055, 0.007, 0.0085, 0.008, 0.008, 0.0085],
    #         "10D RR": [0.00303, 0.0045, 0.005, 0.0055, 0.006, 0.0065, 0.007, 0.0095, 0.0115, 0.014, 0.0125, 0.012, 0.013]
    #     }
    #     }
    # ],
    # irs_curve=[
    #     {"curve_type": "Shibor3M", "value": {
    #         "tenor": [0.5, 0.75, 1, 2, 3, 4, 5, 7, 10],
    #         "origin_tenor": ["6M", "9M", "1Y", "2Y", "3Y", "4Y", "5Y", "7Y", "10Y"],
    #         "average": [0.024825, 0.02525, 0.025775, 0.027325, 0.028625, 0.029875, 0.031027, 0.0327, 0.034363]
    #     }
    #     }
    # ],
    # shibor_curve={
    #     "tenor": [0.003, 0.021, 0.042, 0.083, 0.25, 0.5, 0.75, 1],
    #     "origin_tenor": ["1D", "1W", "2W", "1M", "3M", "6M", "9M", "1Y"],
    #     "rate": [0.02042, 0.02115, 0.02235, 0.023, 0.02353, 0.02472, 0.02656, 0.027]
    # },
    # fx_swap_curve=[
    #     {"symbol": "USD/CNY", "value": {
    #         "tenor": [0.003, 0.006, 0.009, 0.021, 0.042, 0.0625, 0.083, 0.17, 0.25, 0.334, 0.417, 0.5, 0.75, 1, 1.5, 2, 3, 4, 5],
    #         "origin_tenor": ['1D', '2D', '3D', "1W", "2W", "3W", "1M", "2M", "3M", "4M", "5M", "6M", "9M", "1Y", "18M", "2Y", "3Y", "4Y", "5Y"],
    #         "swap_point": [0.001151, 0.000409, 0.000413, 0.00283, 0.00654, 0.0097, 0.01368, 0.02995, 0.0425, 0.0548, 0.069, 0.0848, 0.1215, 0.1583, 0.2307, 0.293, 0.393, 0.5, 0.605]
    #     }
    #     }
    # ]
)


with scenario_extreme:
    price, delta, gamma, vega, theta, vanna, volga = fxoption.calc(
        risk_measure)

    print("price:", price, "delta:", delta, "gamma:", gamma,
          "vega:", vega, "theta:", theta, "vanna", vanna, "volga", volga)
