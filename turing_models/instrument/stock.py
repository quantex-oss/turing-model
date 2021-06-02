from fundamental.base import Priceable, StringField, FloatField
from turing_models.instrument.quotes import Quotes


class Stock(Priceable):
    asset_id = StringField('asset_id')
    asset_type = StringField('asset_type')
    symbol = StringField('symbol')
    name_cn = StringField('name_cn')
    name_en = StringField('name_en')
    exchange_code = StringField('exchange_code')
    currency = StringField('currency')
    bbid = StringField('bbid')
    ric = StringField('ric')
    isin = StringField('isin')
    wind_id = StringField('wind_id')
    sedol = StringField('sedol')
    cusip = StringField('cusip')
    stock_price = FloatField('stock_price')
    quantity: float = FloatField('quantity')  # 股数

    def __init__(self, **kw):
        super(Stock, self).__init__(**kw)
        self.multiplier = 100
        quote = Quotes()
        self.stock_price = quote.stock_price

    def price(self):
        """"计算一手股票的价格"""
        return self.stock_price * self.multiplier

    def value(self):
        """"计算持仓现值"""
        return self.stock_price * self.quantity * self.multiplier

    def delta(self):
        return self.quantity * self.multiplier
    
    def gamma(self):
        return 0

    def vega(self):
        return 0

    def theta(self):
        return 0

    def rho(self):
        return 0

    def rho_q(self):
        return 0

