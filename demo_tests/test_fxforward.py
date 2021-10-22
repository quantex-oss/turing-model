from fundamental import PricingContext

from turing_models.instruments.common import Currency, CurrencyPair
from turing_models.instruments.fx.fx_forward import FXForward
from turing_models.utilities.turing_date import TuringDate


value_date = TuringDate(2021, 8, 20)
fxfwd = FXForward(start_date=TuringDate(2021, 5, 18),
                           expiry=TuringDate(2021, 11, 22),
                           value_date=value_date,
                           underlier_symbol=CurrencyPair.USDCNY,
                           strike=6.5417,
                           d_ccy_discount=0.022,
                           notional=1000000,
                           notional_currency=Currency.USD)

scenario_extreme = PricingContext(
    spot=[
        {"symbol": "USD/CNY", "value": 6.5015}
        ]
)

with scenario_extreme:
    atm = fxfwd.forward()
    price = fxfwd.price()
    delta = fxfwd.fx_delta()
    gamma = fxfwd.fx_gamma()
    vega = fxfwd.fx_vega()
    theta = fxfwd.fx_theta()
    vanna = fxfwd.fx_vanna()
    volga = fxfwd.fx_volga()

    print("atm", atm, "price:", price)
    print("delta:", delta)
    print("gamma", gamma, "vega", vega, "theta", theta, "vanna", vanna, "volga",volga)