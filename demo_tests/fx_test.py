from turing_models.instruments.fx import ForeignExchange


fx = ForeignExchange(exchange_rate=6)

print(fx.price())
print(fx.fx_delta())
print(fx.fx_gamma())
print(fx.fx_theta())
print(fx.fx_vega())
print(fx.fx_volga())
print(fx.fx_vanna())
