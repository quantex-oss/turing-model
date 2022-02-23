from fundamental import PricingContext

from turing_models.instruments.common import Currency, CurrencyPair
from turing_models.instruments.fx.fx_vanilla_option import FXVanillaOption
from turing_models.utilities.global_types import OptionType, TuringExerciseType
from turing_models.utilities.turing_date import TuringDate


value_date = TuringDate(2021, 8, 20)
fxoption = FXVanillaOption(start_date=TuringDate(2021, 7, 15),
                           expiry=TuringDate(2021, 9, 16),
                           cut_off_time=TuringDate(2021, 9, 16),
                           #    delivery_date=TuringDate(2021, 7, 20),
                           value_date=value_date,
                           underlier_symbol=CurrencyPair.USDCNY,
                           strike=6.6,
                           notional=50000000.00,
                           notional_currency=Currency.USD,
                           option_type=OptionType.PUT,
                           exercise_type=TuringExerciseType.EUROPEAN,
                           premium_currency=Currency.CNY)

scenario_extreme = PricingContext(
    # pricing_date='2021-8-20',
    spot=[
    {"symbol": "USD/CNY", "value": 6.5}
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
    print("rd", rd, 'rf', rf)
    print("price:", price, "delta:", delta, "gamma:",
          gamma, "vega:", vega, "theta:", theta,)
    print("vanna", vanna, "volga",volga)

