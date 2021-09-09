import plotly.graph_objs as go
from plotly.offline import iplot

from turing_models.instruments.common import CurrencyPair, RMBIRCurveType, SpotExchangeRateType
from turing_models.market.curves.curve_generation import FXIRCurve, FXOptionImpliedVolatilitySurface


# fx_curve = FXIRCurve(fx_symbol=CurrencyPair.USDCNY,
#                      curve_type=RMBIRCurveType.Shibor3M,
#                      spot_rate_type=SpotExchangeRateType.Central)
# print(fx_curve.get_ccy1_curve())  # Series格式
# print(fx_curve.get_ccy2_curve())  # Series格式

fx_vol_surface = FXOptionImpliedVolatilitySurface(fx_symbol=CurrencyPair.USDCNY)
data = fx_vol_surface.get_vol_surface()  # DataFrame格式
trace = go.Surface(x=data.index.values, y=data.columns.values, z=data)
data = [trace]
layout = go.Layout(title='3D Surface plot')
fig = go.Figure(data=data, layout=layout)
iplot(fig)
# fig.show()
