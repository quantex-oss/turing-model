import datetime

from fundamental.base import Priceable, StringField, FloatField
from turing_models.utilities import TuringDate


class Quotes(Priceable):
    asset_id: str = StringField('assetId')
    name: str = StringField('name')  # 股票名称
    value_date: (str, TuringDate) = StringField('valueDate')  # 估值日期
    stock_price: float = FloatField('price')  # 股票价格
    volatility: float = FloatField('volatility')  # 波动率
    interest_rate: float = FloatField('interestRate')  # 无风险利率
    dividend_yield: float = FloatField('dividendYield')  # 股息率
    accrued_average: float = FloatField('accruedAverage')  # 应计平均价

    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = 'No name'
        self.value_date = TuringDate(*tuple(reversed(datetime.date.today().timetuple()[:3])))

