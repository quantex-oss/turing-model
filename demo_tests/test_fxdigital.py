from fundamental import PricingContext

from turing_models.instruments.common import Currency, CurrencyPair
from turing_models.instruments.fx.fx_digital_option import FXDigitalOption
from turing_models.utilities.global_types import TuringOptionType, TuringExerciseType
from turing_models.utilities.turing_date import TuringDate


value_date = TuringDate(2021, 8, 20)
fxoption = FXDigitalOption(start_date=TuringDate(2021, 5, 18),
                           expiry=TuringDate(2021, 11, 22),
                           value_date=value_date,
                           underlier_symbol=CurrencyPair.USDCNY,
                           strike=6.5417,
                           notional=1000000,
                           coupon_rate=1,
                           option_type=TuringOptionType.CALL,
                           exercise_type=TuringExerciseType.EUROPEAN,
                           premium_currency=Currency.USD)

scenario_extreme = PricingContext(
    spot=[
        {"symbol": "USD/CNY", "value": 6.5015}
        ]
)

with scenario_extreme:
    atm = fxoption.atm()
    price = fxoption.price()
    delta = fxoption.fx_delta()
    gamma = fxoption.fx_gamma()
    vega = fxoption.fx_vega()
    theta = fxoption.fx_theta()
    rd = fxoption.rd
    rf = fxoption.rf
    vanna = fxoption.fx_vanna()
    volga = fxoption.fx_volga()

    print("atm", atm, "sigma", fxoption.volatility_)
    print("price:", price, "delta:", delta, "gamma:",
          gamma, "vega:", vega, "theta:", theta, 'rd:', rd, 'rf:', rf)
    print("vanna", vanna, "volga",volga)