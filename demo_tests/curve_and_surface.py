from turing_models.instruments.common import CurrencyPair, RMBIRCurveType, SpotExchangeRateType
from turing_models.market.curves.curve_generation import FXIRCurve, FXOptionImpliedVolatilitySurface
from turing_models.utilities.turing_date import TuringDate


fx_curve = FXIRCurve(fx_symbol=CurrencyPair.USDCNY,
                     curve_type=RMBIRCurveType.Shibor3M,
                     spot_rate_type=SpotExchangeRateType.Central)
print(fx_curve.get_ccy1_curve())  # Series格式
print(fx_curve.get_ccy2_curve())  # Series格式
fx_vol_surface = FXOptionImpliedVolatilitySurface(fx_symbol=CurrencyPair.USDCNY,
                                                  delta_min=5,
                                                  delta_max=7,
                                                  num_delta=20,
                                                  expiry_min=TuringDate(2021, 9, 17),
                                                  expiry_max=TuringDate(2021, 10, 20))
print(fx_vol_surface.get_vol_surface())  # DataFrame格式
