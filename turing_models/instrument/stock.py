from fundamental.base import Priceable, StringField, FloatField
from turing_models.instrument.quotes import Quotes


class Stock(Priceable):
    asset_id = StringField('asset_id')
    type = StringField('type')
    asset_type = StringField('assetType')
    symbol = StringField('symbol')
    name_cn = StringField('nameCn')
    name_en = StringField('nameEn')
    exchange_code = StringField('exchangeCode')
    currency = StringField('currency')
    bbid = StringField('bbid')
    ric = StringField('ric')
    isin = StringField('isin')
    wind_id = StringField('windId')
    sedol = StringField('sedol')
    cusip = StringField('cusip')
    quantity: float = FloatField('quantity')
    stock_price: float = FloatField('stock_price')

    def __init__(self, **kw):
        super(Stock, self).__init__(**kw)
        self.multiplier = 100

    def price(self):
        """"计算一手股票的价格"""
        return self.stock_price * self.multiplier

    def value(self):
        """"计算持仓现值"""
        return self.stock_price * self.quantity * self.multiplier

    def delta(self):
        return self.multiplier

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
