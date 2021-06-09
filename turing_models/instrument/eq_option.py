import datetime
from dataclasses import dataclass
from typing import Optional

from tunny import model

from fundamental.base import Priceable, StringField, FloatField, DateField, BoolField, Context
from fundamental.base import ctx
from fundamental.market.curves import TuringDiscountCurveFlat
from fundamental.turing_db.utils import to_turing_date
from turing_models.instrument.common import AssetClass, AssetType
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.products.equity import TuringEquitySnowballOption, TuringEquityAsianOption, \
    TuringEquityAmericanOption, TuringEquityVanillaOption, TuringAsianOptionValuationMethods, \
    TuringEquityKnockoutOption
from turing_models.utilities import TuringDate, option_type_dict


@model
class OptionModel:
    """eq_option功能集"""

    def __init__(self):
        self.ctx = ctx

    @property
    def value_date_(self):
        return getattr(self.ctx.path, 'value_date') \
            if (hasattr(self, "ctx") and
                hasattr(self.ctx, "path") and
                getattr(self.ctx.path, 'value_date', None)) \
            else self._value_date

    @property
    def stock_price_(self) -> float:
        return getattr(self.ctx.path, 'stock_price') \
            if (hasattr(self, "ctx") and
                hasattr(self.ctx, "path") and
                getattr(self.ctx.path, 'stock_price', None)) \
            else self._stock_price

    @property
    def volatility_(self) -> float:
        return getattr(self.ctx.path, 'volatility') \
            if (hasattr(self, "ctx") and
                hasattr(self.ctx, "path") and
                getattr(self.ctx.path, 'volatility', None)) \
            else self._volatility

    @property
    def interest_rate_(self) -> float:
        return getattr(self.ctx.path, 'interest_rate') \
            if (hasattr(self, "ctx") and
                hasattr(self.ctx, "path") and
                getattr(self.ctx.path, 'interest_rate', None)) \
            else self._interest_rate

    @property
    def dividend_yield_(self) -> float:
        return getattr(self.ctx.path, 'dividend_yield') \
            if (hasattr(self, "ctx") and
                hasattr(self.ctx, "path") and
                getattr(self.ctx.path, 'dividend_yield', None)) \
            else self._dividend_yield

    @property
    def accrued_average_(self) -> float:
        return getattr(self.ctx.path, 'accrued_average') \
            if (hasattr(self, "ctx") and
                hasattr(self.ctx, "path") and
                getattr(self.ctx.path, 'accrued_average', None)) \
            else self._accrued_average

    def option_name(self):
        knock_in_type = '_' + getattr(self, 'knock_in_type', '') if getattr(self, 'knock_in_type', '') else ''
        knock_out_type = '_' + getattr(self, 'knock_out_type', '') if getattr(self, 'knock_out_type', '') else ''
        option_ident = getattr(self, 'option_type', '') + '_' + getattr(self, 'product_type',
                                                                        '') + knock_in_type + knock_out_type

        op = option_type_dict.get(option_ident, None)
        if op:
            self.option_type_turing = op.get('type')
            self.knock_out_type_turing = op.get('knock_out_type')
            self.knock_in_type_turing = op.get('knock_in_type')
            return op.get('option_name')
        else:
            raise Exception(f"{option_ident.split('_')}类型组合不存在")

    def option(self, *args, **kwgs):
        return getattr(self, f'option_{getattr(self, "option_name")()[0]}')(*args, **kwgs)

    def params(self, *args, **kwgs):
        return getattr(self, f'params_{getattr(self, "option_name")()[1]}')(*args, **kwgs)

    def params_generic(self) -> list:
        return [
            self.value_date_,
            self.stock_price_,
            self.discount_curve,
            self.dividend_curve,
            self.model
        ]

    def params_asian(self) -> list:
        return [self.value_date_,
                self.stock_price_,
                self.discount_curve,
                self.dividend_curve,
                self.model,
                TuringAsianOptionValuationMethods.CURRAN,
                self.accrued_average]

    def option_european(self) -> TuringEquityVanillaOption:
        return TuringEquityVanillaOption(
            self.expiration_date,
            self.strike_price,
            self.option_type_turing)

    def option_american(self) -> TuringEquityAmericanOption:
        return TuringEquityAmericanOption(
            self.expiration_date,
            self.strike_price,
            self.option_type_turing)

    def option_asian(self) -> TuringEquityAsianOption:
        return TuringEquityAsianOption(
            self.start_averaging_date,
            self.expiration_date,
            self.strike_price,
            self.option_type_turing)

    def option_snowball(self) -> TuringEquitySnowballOption:
        return TuringEquitySnowballOption(
            self.expiration_date,
            self.knock_out_price,
            self.knock_in_price,
            self.notional,
            self.coupon_rate,
            self.option_type_turing,
            self.coupon_annualized_flag,
            self.knock_in_type_turing,
            self.knock_in_strike1,
            self.knock_in_strike2,
            self.participation_rate)

    def option_knockout(self) -> TuringEquityKnockoutOption:
        return TuringEquityKnockoutOption(
            self.expiration_date,
            self.strike_price,
            self.knock_out_type_turing,
            self.knock_out_price,
            self.coupon_rate,
            self.coupon_annualized_flag,
            self.notional,
            self.participation_rate)

    @property
    def asset_class(self) -> AssetClass:
        """Equity"""
        return AssetClass.Equity

    @property
    def asset_type(self) -> AssetType:
        """Option"""
        return AssetType.Option

    @property
    def model(self) -> TuringModelBlackScholes:
        return TuringModelBlackScholes(self.volatility_)

    @property
    def discount_curve(self) -> TuringDiscountCurveFlat:
        return TuringDiscountCurveFlat(
            self.value_date_, self.interest_rate_)

    @property
    def dividend_curve(self) -> TuringDiscountCurveFlat:
        return TuringDiscountCurveFlat(
            self.value_date_, self.dividend_yield_)

    @property
    def run_mutiplier(self):
        return self.product_type == 'European' \
               or self.product_type == 'American' \
               or self.product_type == 'Asian'

    def price(self) -> float:
        if self.run_mutiplier:
            return self.option().value(*self.params()) * self.multiplier
        return self.option().value(*self.params())

    def delta(self) -> float:
        if self.run_mutiplier:
            return self.option().delta(*self.params()) * self.multiplier
        return self.option().delta(*self.params())

    def gamma(self) -> float:
        if self.run_mutiplier:
            return self.option().gamma(*self.params()) * self.multiplier
        return self.option().gamma(*self.params())

    def vega(self) -> float:
        if self.run_mutiplier:
            return self.option().vega(*self.params()) * self.multiplier
        return self.option().vega(*self.params())

    def theta(self) -> float:
        if self.run_mutiplier:
            return self.option().theta(*self.params()) * self.multiplier
        return self.option().theta(*self.params())

    def rho(self) -> float:
        if self.run_mutiplier:
            return self.option().rho(*self.params()) * self.multiplier
        return self.option().rho(*self.params())

    def rho_q(self) -> float:
        if self.run_mutiplier:
            return self.option().rho_q(*self.params()) * self.multiplier
        return self.option().rho_q(*self.params())


class Option(Priceable):
    """eqoption orm定义,取数据用"""
    asset_id = StringField('asset_id')
    type = StringField('type')
    option_type = StringField("option_type")
    product_type = StringField("product_type")
    underlier = StringField("underlier")
    notional: float = FloatField('notional')
    initial_spot = FloatField("initial_spot")
    number_of_options = FloatField("number_of_options")
    start_date: TuringDate = DateField("start_date")
    end_date: TuringDate = DateField("end_date")
    start_averaging_date: TuringDate = DateField("start_averaging_date")
    expiration_date: TuringDate = DateField("expiry")
    participation_rate: float = FloatField("participation_rate")
    strike_price: float = FloatField("strike")
    barrier: float = FloatField("barrier")
    rebate: float = FloatField("rebate")
    coupon: float = FloatField("coupon")
    multiplier: float = FloatField("multiplier")
    settlement_currency = StringField("settlement_currency")
    premium = FloatField("premium")
    premium_payment_date: TuringDate = DateField("premium_payment_date")
    method_of_settlement = StringField("method_of_settlement")
    knock_out_price: float = FloatField("knock_out_price")  # yapi无值
    knock_in_price: float = FloatField("knock_in_price")  # yapi无值
    coupon_rate: float = FloatField("coupon_rate")  # yapi无值
    coupon_annualized_flag: bool = BoolField("coupon_annualized_flag")  # yapi无值
    knock_out_type = StringField("knock_out_type")  # yapi无值
    knock_in_type = StringField("knock_in_type")  # yapi无值
    knock_in_strike1: float = FloatField("knock_in_strike1")  # yapi无值
    knock_in_strike2: float = FloatField("knock_in_strike2")  # yapi无值
    stock_price: float = FloatField("stock_price")  # 股票价格

    def __init__(self, **kw):
        super().__init__(**kw)
        self.ctx = ctx


@dataclass
class EqOption(OptionModel):
    """
        Instrument definition for equity option
        支持多种参数传入方式
        Examples:
        1.
        # >>> eq = EqOption(asset_id='123', option_type='call', product_type='European', expiration_date=TuringDate(12, 2, 2021), strike_price=90, multiplier=10000)
        # >>> eq.from_json()
        # >>> eq.price()
        2.
        # >>> _option = Option()
        # >>> _option.resolve(_resource=somedict)
        # >>> eq = EqOption(obj=_option)
        # >>> eq.resolve()
        # >>> eq.price()
        3.
        # >>> _option = Option()
        # >>> _option.resolve(_resource=somedict)
        # >>> eq = EqOption(option_type='call',product_type='European', notional=1.00, obj=_option)
        # >>> eq.resolve()
        # >>> eq.price()
    """

    asset_id: str = None
    option_type: str = None
    product_type: str = None
    underlier: str = None
    notional: float = None
    initial_spot: float = None
    number_of_options: float = None
    start_date: str = None
    end_date: str = None
    start_averaging_date: str = None
    expiration_date: str = None
    participation_rate: float = None
    strike_price: float = None
    barrier: float = None
    rebate: float = None
    coupon: float = None
    multiplier: float = None
    settlement_currency: str = None
    premium: float = None
    premium_payment_date: str = None
    method_of_settlement: str = None
    knock_out_price: float = None  # yapi无值
    knock_in_price: float = None  # yapi无值
    coupon_rate: float = None  # yapi无值
    coupon_annualized_flag: bool = None  # yapi无值
    knock_out_type: str = None  # yapi无值
    knock_in_type: str = None  # yapi无值
    knock_in_strike1: float = None  # yapi无值
    knock_in_strike2: float = None  # yapi无值
    name: str = None  # 对象标识名
    value_date: str = None  # 估值日期
    stock_price: float = None  # 股票价格
    volatility: float = 0.1  # 波动率
    interest_rate: float = 0.02  # 无风险利率
    dividend_yield: float = 0.01  # 股息率
    accrued_average: float = 0.1  # 应计平均价
    ctx: Context = ctx
    obj: Optional[Option] = None

    def __post_init__(self):
        super(EqOption, self).__init__()
        self.ctx = ctx
        self.set_param()

    def set_param(self):
        self.name = 'No name'
        self._volatility = self.volatility
        self._interest_rate = self.interest_rate
        self._dividend_yield = self.dividend_yield
        self._accrued_average = self.accrued_average
        self._value_date = to_turing_date(self.value_date) \
            if self.value_date and isinstance(self.value_date, str) \
            else TuringDate(*tuple(reversed(datetime.date.today().timetuple()[:3])))
        self._stock_price = self.stock_price
        self.convert_date()

    def convert_date(self):
        date_fields = ["start_date", "end_date", "start_averaging_date",
                       "expiration_date", "premium_payment_date", "value_date"]
        for field in date_fields:
            setattr(self, field, to_turing_date(getattr(self, field, None))
            if getattr(self, field, None)
               and isinstance(getattr(self, field, None), str) else getattr(self, field, None))

    def _set_by_dict(self, tmp_dict):
        for k, v in tmp_dict.items():
            setattr(self, k, v)
        self.set_param()

    def resolve(self, expand_dict=None):
        if expand_dict:
            self._set_by_dict(expand_dict)
        else:
            self._set_by_dict(self.obj)


if __name__ == '__main__':
    eq = EqOption(asset_id='123', option_type='call',
                  product_type='European', stock_price=511.11,
                  expiration_date="20211121",
                  strike_price=90, multiplier=1000)
    print(eq.price())
