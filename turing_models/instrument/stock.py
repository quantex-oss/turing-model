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
    quantity: float = FloatField('quantity')  # 股数
    stock_price: float = FloatField('stock_price')
    volatility: float = FloatField('volatility')

    def __init__(self, **kw):
        super(Stock, self).__init__(**kw)

    def price(self):
        """"计算持仓股票的现价"""
        return self.stock_price

    def delta(self):
        return 1
