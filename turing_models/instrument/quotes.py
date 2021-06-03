from fundamental.base import Priceable, StringField, FloatField
from turing_models.utilities import TuringDate


class Quotes(Priceable):
    name: str = StringField('name')  # 对象标识名
    value_date: (str, TuringDate) = StringField('valueDate')  # 估值日期
    stock_price: float = FloatField('stockPrice')  # 股票价格
    volatility: float = FloatField('volatility')  # 波动率
    interest_rate: float = FloatField('interestRate')  # 无风险利率
    dividend_yield: float = FloatField('dividendYield')  # 股息率
    accrued_average: float = FloatField('accruedAverage')  # 应计平均价

    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = 'No name'
        self.value_date = TuringDate(12, 2, 2020)
        self.stock_price = 100
        self.volatility = 0.1
        self.interest_rate = 0.02
        self.dividend_yield = 0
        self.accrued_average = 100
