from turing_models.market.volatility.vol_surface_generation import FXOptionImpliedVolatilitySurface, CurrencyPair
import plotly.graph_objs as go

fx_name = CurrencyPair.USDCNY
fx_vol_surface = FXOptionImpliedVolatilitySurface(fx_symbol=fx_name,notional_currency='CNY')
vol_surface_data = fx_vol_surface.get_vol_surface()
data = vol_surface_data
print(data)
fig = go.Figure(data=[go.Surface(x=data.columns.values, y=data.index.values, z=data*100)])
fig.update_layout(title=f'FX {fx_name} Vol Surface',
                  scene_aspectmode='cube',
                  scene = dict(
                    xaxis = dict(title='Tenor', backgroundcolor="rgb(200, 200, 230)"),
                    yaxis = dict(title='Strike', backgroundcolor="rgb(230, 200, 230)", gridwidth = 3),
                    zaxis = dict(title='Vol', backgroundcolor="rgb(230, 230,200)"),
                    camera=dict(
                      up=dict(x=0, y=0, z=1),
                      center=dict(x=0, y=0, z=0),
                      eye=dict(x=-1.5, y=-1.5, z=1.5)
                    ),
                  ),
                  autosize=False,
                  width=1080, height=1080,
                  margin=dict(l=65, r=50, b=65, t=90))

fig.show()
