# import plotly.graph_objs as go
# from plotly.offline import iplot
#
from turing_models.instruments.common import CurrencyPair, RMBIRCurveType, SpotExchangeRateType
from turing_models.market.curves.curve_generation import FXIRCurve
from turing_models.market.volatility.vol_surface_generation import FXOptionImpliedVolatilitySurface

#
# fx_curve = FXIRCurve(fx_symbol=CurrencyPair.USDCNY,
#                      curve_type=RMBIRCurveType.Shibor3M,
#                      spot_rate_type=SpotExchangeRateType.Central)
# print(fx_curve.get_ccy1_curve())  # Series格式
# print(fx_curve.get_ccy2_curve())  # Series格式
#
# fx_vol_surface = FXOptionImpliedVolatilitySurface(
#     fx_symbol=CurrencyPair.USDCNY)
# data = fx_vol_surface.get_vol_surface()  # DataFrame格式
# trace = go.Surface(x=data.index.values, y=data.columns.values, z=data)
# data = [trace]
# layout = go.Layout(title='3D Surface plot')
# fig = go.Figure(data=data, layout=layout)
# iplot(fig)
# fig.show()

from turing_models.utilities.turing_date import TuringDate
from turing_models.market.volatility.vol_surface_generation import FXVolSurfaceGen
from turing_models.market.curves.curve_generation import DomDiscountCurveGen, ForDiscountCurveGen

value_date = TuringDate(2021, 9, 29)
tenors = [0.003, 0.021, 0.042, 0.083, 0.25, 0.5, 0.75, 1.0, 2.0, 3.0, 4.0, 5.0, 7.0, 10.0]
rates = [0.01505, 0.0245, 0.029, 0.02436, 0.02427, 0.025663, 0.026069, 0.026513, 0.028113, 0.0295, 0.030763, 0.031825, 0.03345, 0.034913]
domestic_discount_curve = DomDiscountCurveGen(value_date).discount_curve
foreign_discount_curve = ForDiscountCurveGen(currency_pair='USD/CNY', value_date=value_date).discount_curve
vol_surface = FXVolSurfaceGen(currency_pair='USD/CNY',
                              domestic_discount_curve=domestic_discount_curve,
                              foreign_discount_curve=foreign_discount_curve,
                              value_date=value_date)
