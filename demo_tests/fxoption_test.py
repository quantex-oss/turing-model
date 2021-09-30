from fundamental.pricing_context import PricingContext

from turing_models.instruments.common import Currency, CurrencyPair, RiskMeasure
from turing_models.utilities.turing_date import TuringDate
from turing_models.instruments.fx.fx_vanilla_option import FXVanillaOption
from turing_models.utilities.global_types import TuringOptionType, TuringExerciseType


fxoption = FXVanillaOption(start_date=TuringDate(2021, 9, 1),
                               expiry=TuringDate(2021, 9, 1).addMonths(4),
                               cut_off_time=TuringDate(2021, 12, 30),
                               value_date=TuringDate(2021, 9, 8),
                               #    volatility=0.1411,
                               # underlier='FX00000001',
                               underlier_symbol=CurrencyPair.USDCNY,
                               strike=6.8,
                               notional=1000000,
                               notional_currency=Currency.CNY,
                               option_type=TuringOptionType.CALL,
                               exercise_type=TuringExerciseType.EUROPEAN,
                               premium_currency=Currency.CNY)

price = fxoption.calc(RiskMeasure.Price)
delta = fxoption.calc(RiskMeasure.FxDelta)
gamma = fxoption.calc(RiskMeasure.FxGamma)
vega = fxoption.calc(RiskMeasure.FxVega)
theta = fxoption.calc(RiskMeasure.FxTheta)
vanna = fxoption.calc(RiskMeasure.FxVanna)
volga = fxoption.calc(RiskMeasure.FxVolga)
delta_bump = fxoption.fx_delta_bump()
print(price, delta, gamma, vega, theta, vanna, volga, delta_bump)


scenario_extreme = PricingContext(spot=[
    {"symbol": "USD/CNY", "value": 7}
]
)

with scenario_extreme:
    price = fxoption.calc(RiskMeasure.Price)
    delta = fxoption.calc(RiskMeasure.FxDelta)
    gamma = fxoption.calc(RiskMeasure.FxGamma)
    vega = fxoption.calc(RiskMeasure.FxVega)
    theta = fxoption.calc(RiskMeasure.FxTheta)
    vanna = fxoption.calc(RiskMeasure.FxVanna)
    volga = fxoption.calc(RiskMeasure.FxVolga)
    print(price, delta, gamma, vega, theta, vanna, volga)
