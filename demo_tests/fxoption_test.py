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
# price, delta, gamma, vega, theta, vanna, volga = fxoption.calc(risk_measure)
# print("price:", price, "delta:", delta, "gamma:", gamma,
#       "vega:", vega, "theta:", theta, "vanna", vanna, "volga", volga)

print("通过what-if传入2021年8月20日的汇率和曲线数据")
scenario_extreme = PricingContext(
    pricing_date="latest",
    spot=[{
        "symbol": "USD/CNY",
        "value": 6.5
    }],
    global_ibor_curve=[{
        "ibor_type": "Shibor",
        "currency": "CNY",
        "value": [
            {
                "tenor": 0.003,
                "origin_tenor": "ON",
                "rate": 0.02042,
                "change": 0.00201
            },
            {
                "tenor": 0.021,
                "origin_tenor": "1W",
                "rate": 0.02115,
                "change": 0.00024
            },
            {
                "tenor": 0.042,
                "origin_tenor": "2W",
                "rate": 0.02235,
                "change": -0.00013
            },
            {
                "tenor": 0.083,
                "origin_tenor": "1M",
                "rate": 0.023,
                "change": 0
            },
            {
                "tenor": 0.25,
                "origin_tenor": "3M",
                "rate": 0.02353,
                "change": -0.00001
            },
            {
                "tenor": 0.5,
                "origin_tenor": "6M",
                "rate": 0.02472,
                "change": -0.00002
            },
            {
                "tenor": 0.75,
                "origin_tenor": "9M",
                "rate": 0.02656,
                "change": 0
            },
            {
                "tenor": 1,
                "origin_tenor": "1Y",
                "rate": 0.027,
                "change": 0
            }
        ]
    }],
    irs_curve=[{
        "ir_type": "Shibor3M",
        "currency": "CNY",
        "value": [{
            "tenor": 0.5,
            "origin_tenor": "6M",
            "ask": 0.02485,
            "average": 0.024825,
            "bid": 0.0248
        },
            {
                "tenor": 0.75,
                "origin_tenor": "9M",
                "ask": 0.0253,
                "average": 0.02525,
                "bid": 0.0252
            },
            {
                "tenor": 1,
                "origin_tenor": "1Y",
                "ask": 0.0258,
                "average": 0.025775,
                "bid": 0.02575
            },
            {
                "tenor": 2,
                "origin_tenor": "2Y",
                "ask": 0.027425,
                "average": 0.027325,
                "bid": 0.027225
            },
            {
                "tenor": 3,
                "origin_tenor": "3Y",
                "ask": 0.028725,
                "average": 0.028625,
                "bid": 0.028525
            },
            {
                "tenor": 4,
                "origin_tenor": "4Y",
                "ask": 0.029975,
                "average": 0.029875,
                "bid": 0.029775
            },
            {
                "tenor": 5,
                "origin_tenor": "5Y",
                "ask": 0.031103,
                "average": 0.031027,
                "bid": 0.03095
            },
            {
                "tenor": 7,
                "origin_tenor": "7Y",
                "ask": 0.033025,
                "average": 0.0327,
                "bid": 0.032375
            },
            {
                "tenor": 10,
                "origin_tenor": "10Y",
                "ask": 0.0348,
                "average": 0.034363,
                "bid": 0.033925
            }
        ]
    }],
    fx_swap_curve=[{
        "currency_pair": "USD/CNY",
        "value": [{
            "tenor": 0.003,
            "origin_tenor": "ON",
            "swap_point": 0.000268,
            "exchange_rate": 6.3746,
            "accrual_start": "2022-01-07T00:00:00.000+0800"
        },
            {
                "tenor": 0.006,
                "origin_tenor": "TN",
                "swap_point": 0.00092,
                "exchange_rate": 6.3749,
                "accrual_start": "2022-01-10T00:00:00.000+0800"
            },
            {
                "tenor": 0.009,
                "origin_tenor": "SN",
                "swap_point": 0.000323,
                "exchange_rate": 6.3761,
                "accrual_start": "2022-01-11T00:00:00.000+0800"
            },
            {
                "tenor": 0.021,
                "origin_tenor": "1W",
                "swap_point": 0.00274,
                "exchange_rate": 6.3785,
                "accrual_start": "2022-01-18T00:00:00.000+0800"
            },
            {
                "tenor": 0.042,
                "origin_tenor": "2W",
                "swap_point": 0.004956,
                "exchange_rate": 6.3808,
                "accrual_start": "2022-01-24T00:00:00.000+0800"
            },
            {
                "tenor": 0.0625,
                "origin_tenor": "3W",
                "swap_point": 0.013,
                "exchange_rate": 6.3888,
                "accrual_start": "2022-02-07T00:00:00.000+0800"
            },
            {
                "tenor": 0.083,
                "origin_tenor": "1M",
                "swap_point": 0.01405,
                "exchange_rate": 6.3899,
                "accrual_start": "2022-02-10T00:00:00.000+0800"
            },
            {
                "tenor": 0.17,
                "origin_tenor": "2M",
                "swap_point": 0.0253,
                "exchange_rate": 6.4011,
                "accrual_start": "2022-03-10T00:00:00.000+0800"
            },
            {
                "tenor": 0.25,
                "origin_tenor": "3M",
                "swap_point": 0.0388,
                "exchange_rate": 6.4146,
                "accrual_start": "2022-04-11T00:00:00.000+0800"
            },
            {
                "tenor": 0.334,
                "origin_tenor": "4M",
                "swap_point": 0.051,
                "exchange_rate": 6.4268,
                "accrual_start": "2022-05-10T00:00:00.000+0800"
            },
            {
                "tenor": 0.417,
                "origin_tenor": "5M",
                "swap_point": 0.0623,
                "exchange_rate": 6.4381,
                "accrual_start": "2022-06-10T00:00:00.000+0800"
            },
            {
                "tenor": 0.5,
                "origin_tenor": "6M",
                "swap_point": 0.0743,
                "exchange_rate": 6.4501,
                "accrual_start": "2022-07-11T00:00:00.000+0800"
            },
            {
                "tenor": 0.75,
                "origin_tenor": "9M",
                "swap_point": 0.1095,
                "exchange_rate": 6.4853,
                "accrual_start": "2022-10-11T00:00:00.000+0800"
            },
            {
                "tenor": 1,
                "origin_tenor": "1Y",
                "swap_point": 0.1399,
                "exchange_rate": 6.5157,
                "accrual_start": "2023-01-10T00:00:00.000+0800"
            },
            {
                "tenor": 1.5,
                "origin_tenor": "18M",
                "swap_point": 0.187975,
                "exchange_rate": 6.5638,
                "accrual_start": "2023-07-10T00:00:00.000+0800"
            },
            {
                "tenor": 2,
                "origin_tenor": "2Y",
                "swap_point": 0.237,
                "exchange_rate": 6.6128,
                "accrual_start": "2024-01-10T00:00:00.000+0800"
            },
            {
                "tenor": 3,
                "origin_tenor": "3Y",
                "swap_point": 0.32,
                "exchange_rate": 6.6958,
                "accrual_start": "2025-01-10T00:00:00.000+0800"
            },
            {
                "tenor": 4,
                "origin_tenor": "4Y",
                "swap_point": 0.42,
                "exchange_rate": 6.7958,
                "accrual_start": "2026-01-12T00:00:00.000+0800"
            },
            {
                "tenor": 5,
                "origin_tenor": "5Y",
                "swap_point": 0.505,
                "exchange_rate": 6.8808,
                "accrual_start": "2027-01-11T00:00:00.000+0800"
            }
        ]
    }],
    fx_implied_volatility_curve=[{
        "currency_pair": "USD/CNY",
        "volatility_type": ["ATM", "25D BF", "25D RR", "10D BF", "10D RR"],
        "value": [{
            "tenor": 0.003,
            "origin_tenor": "1D",
            "ATM": 0.033562,
            "25D BF": 0.03271,
            "25D RR": 0.034413,
            "10D BF": 0.03271,
            "10D RR": 0.034413
        },
            {
                "tenor": 0.021,
                "origin_tenor": "1W",
                "ATM": 0.036,
                "25D BF": 0.034,
                "25D RR": 0.038,
                "10D BF": 0.03271,
                "10D RR": 0.034413
            },
            {
                "tenor": 0.042,
                "origin_tenor": "2W",
                "ATM": 0.037,
                "25D BF": 0.035,
                "25D RR": 0.039,
                "10D BF": 0.03271,
                "10D RR": 0.034413
            },
            {
                "tenor": 0.0625,
                "origin_tenor": "3W",
                "ATM": 0.038,
                "25D BF": 0.036,
                "25D RR": 0.04,
                "10D BF": 0.03271,
                "10D RR": 0.034413
            },
            {
                "tenor": 0.083,
                "origin_tenor": "1M",
                "ATM": 0.04,
                "25D BF": 0.038,
                "25D RR": 0.042,
                "10D BF": 0.03271,
                "10D RR": 0.034413
            },
            {
                "tenor": 0.17,
                "origin_tenor": "2M",
                "ATM": 0.041,
                "25D BF": 0.039,
                "25D RR": 0.043,
                "10D BF": 0.03271,
                "10D RR": 0.034413
            },
            {
                "tenor": 0.25,
                "origin_tenor": "3M",
                "ATM": 0.04238,
                "25D BF": 0.04175,
                "25D RR": 0.043,
                "10D BF": 0.03271,
                "10D RR": 0.034413
            },
            {
                "tenor": 0.5,
                "origin_tenor": "6M",
                "ATM": 0.04425,
                "25D BF": 0.04425,
                "25D RR": 0.04425,
                "10D BF": 0.03271,
                "10D RR": 0.034413
            },
            {
                "tenor": 0.75,
                "origin_tenor": "9M",
                "ATM": 0.0453,
                "25D BF": 0.0433,
                "25D RR": 0.0473,
                "10D BF": 0.03271,
                "10D RR": 0.034413
            },
            {
                "tenor": 1,
                "origin_tenor": "1Y",
                "ATM": 0.0458,
                "25D BF": 0.0438,
                "25D RR": 0.0478,
                "10D BF": 0.03271,
                "10D RR": 0.034413
            },
            {
                "tenor": 1.5,
                "origin_tenor": "18M",
                "ATM": 0.0435,
                "25D BF": 0.04,
                "25D RR": 0.047,
                "10D BF": 0.03271,
                "10D RR": 0.034413
            },
            {
                "tenor": 2,
                "origin_tenor": "2Y",
                "ATM": 0.044,
                "25D BF": 0.042,
                "25D RR": 0.046,
                "10D BF": 0.03271,
                "10D RR": 0.034413
            },
            {
                "tenor": 3,
                "origin_tenor": "3Y",
                "ATM": 0.044,
                "25D BF": 0.042,
                "25D RR": 0.046,
                "10D BF": 0.03271,
                "10D RR": 0.034413
            }
        ]
    }]
)


with scenario_extreme:
    price, delta, gamma, vega, theta, vanna, volga = fxoption.calc(
        risk_measure)

    print("price:", price, "delta:", delta, "gamma:", gamma,
          "vega:", vega, "theta:", theta, "vanna", vanna, "volga", volga)
