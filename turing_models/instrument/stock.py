from fundamental.base import Priceable, StringField, FloatField
from turing_models.instrument.quotes import Quotes


class Stock(Priceable):
    asset_id = StringField('asset_id')
    type = StringField('type')
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
    quantity: float = FloatField('quantity')  # 股数
    stock_price: float = FloatField('stock_price')

    def __init__(self, **kw):
        super(Stock, self).__init__(**kw)

    def price(self):
        """"计算持仓股票的现价"""
        return self.stock_price * self.quantity

    def delta(self):
        return self.quantity

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
