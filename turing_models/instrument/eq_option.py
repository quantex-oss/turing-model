from dataclasses import dataclass, InitVar
from typing import Union

from loguru import logger
from tunny import model, compute

from fundamental.base import Priceable, StringField, FloatField, DateField, BoolField, Context
from fundamental.base import ctx
from fundamental.market.curves import TuringDiscountCurveFlat
from turing_models.instrument.common import AssetClass, AssetType, BuySell, Exchange, Currency, OptionSettlementMethod
from turing_models.instrument.quotes import Quotes
from turing_models.instrument.stock import Stock
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.products.equity import TuringEquitySnowballOption, TuringEquityAsianOption, \
    TuringEquityAmericanOption, TuringEquityVanillaOption, TuringAsianOptionValuationMethods, \
    TuringEquityKnockoutOption, TuringEquityKnockoutTypes, TuringKnockInTypes
from turing_models.utilities import TuringDate, option_type_dict


def merge_data(data_1, data_2):
    """
    使用 data_2 和 data_1 的 value 相加，合成一个新的字典。
    对于 data_2 和 data_1 都有的 key，合成规则为保留 data_1 的 value
    :param data_1:
    :param data_2:
    :return:
    """
    if isinstance(data_1, dict) and isinstance(data_2, dict):
        new_dict = {}
        d2_keys = list(data_2.keys())
        for d1k in data_1.keys():
            if d1k in d2_keys:  # d1,d2都有。去往深层比对
                d2_keys.remove(d1k)
                new_dict[d1k] = merge_data(data_1.get(d1k), data_2.get(d1k))
            # else:
            #     new_dict[d1k] = data_1.get(d1k)  # d1有d2没有的key
        for d2k in d2_keys:  # d2有d1没有的key
            new_dict[d2k] = data_2.get(d2k)
        return new_dict
    else:  # 递归遍历到最底层 value
        if data_2 and data_1:
            return data_1
        elif data_2:
            return data_2
        elif data_1:
            return data_1
        else:  # 全为 None，0，[] 或 {}中的一个
            return data_2


def dict_to_obj(data, obj):
    data2 = obj.__dict__
    data2 = merge_data(data, data2)
    return data2


@model
class OptionModel:
    """eq_option功能集"""

    def option_name(self):
        # print(self.option_type, self.product_type)
        knock_in_type = '_' + getattr(self, 'knock_in_type', '') if getattr(self, 'knock_in_type', '') else ''
        knock_out_type = '_' + getattr(self, 'knock_out_type', '') if getattr(self, 'knock_out_type', '') else ''
        option_ident = getattr(self, 'option_type', '') + '_' + getattr(self, 'product_type',
                                                                        '') + knock_in_type + knock_out_type

        op = option_type_dict.get(option_ident, None)
        if op:
            self.option_type_turing = op.get('type')
            return op.get('option_name')
        else:
            raise Exception(f"{option_ident.split('_')}类型组合不存在")

    def option(self, *args, **kwgs):
        return getattr(self, f'option_{getattr(self, "option_name")()[0]}')(*args, **kwgs)

    def params(self, *args, **kwgs):
        return getattr(self, f'params_{getattr(self, "option_name")()[1]}')(*args, **kwgs)

    @compute
    def params_generic(self) -> list:
        return [
            self.value_date,
            self.stock_price,
            self.discount_curve,
            self.dividend_curve,
            self.model
        ]

    @compute
    def params_asian(self) -> list:
        return [self.value_date,
                self.stock_price,
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
    def value_date(self):
        return self.ctx.path.value_date \
            if self.ctx.path and self.ctx.path.value_date \
            else self.__value_date

    @property
    def stock_price(self) -> float:
        return self.ctx.path.stock_price \
            if self.ctx.path and self.ctx.path.stock_price \
            else self.__stock_price

    @property
    def volatility(self) -> float:
        return self.ctx.path.volatility \
            if self.ctx.path and self.ctx.path.volatility \
            else self.__volatility

    @property
    def interest_rate(self) -> float:
        return self.ctx.path.interest_rate \
            if self.ctx.path and self.ctx.path.interest_rate \
            else self.__interest_rate

    @property
    def dividend_yield(self) -> float:
        return self.ctx.path.dividend_yield \
            if self.ctx.path and self.ctx.path.dividend_yield \
            else self.__dividend_yield

    @property
    def accrued_average(self) -> float:
        return self.ctx.path.accrued_average \
            if self.ctx.path and self.ctx.path.accrued_average \
            else self.__accrued_average

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
        return TuringModelBlackScholes(self.volatility)

    @property
    def discount_curve(self) -> TuringDiscountCurveFlat:
        return TuringDiscountCurveFlat(
            self.value_date, self.interest_rate)

    @property
    def dividend_curve(self) -> TuringDiscountCurveFlat:
        return TuringDiscountCurveFlat(
            self.value_date, self.dividend_yield)

    @compute
    def price(self) -> float:
        if self.product_type == 'European' or self.product_type == 'American' or self.product_type == 'Asian':
            return self.option().value(*self.params()) * self.multiplier
        return self.option().value(*self.params())

    @compute
    def delta(self) -> float:
        if self.product_type == 'European' or self.product_type == 'American' or self.product_type == 'Asian':
            return self.option().delta(*self.params()) * self.multiplier
        return self.option().delta(*self.params())

    @compute
    def gamma(self) -> float:
        if self.product_type == 'European' or self.product_type == 'American' or self.product_type == 'Asian':
            return self.option().gamma(*self.params()) * self.multiplier
        return self.option().gamma(*self.params())

    @compute
    def vega(self) -> float:
        if self.product_type == 'European' or self.product_type == 'American' or self.product_type == 'Asian':
            return self.option().vega(*self.params()) * self.multiplier
        return self.option().vega(*self.params())

    @compute
    def theta(self) -> float:
        if self.product_type == 'European' or self.product_type == 'American' or self.product_type == 'Asian':
            return self.option().theta(*self.params()) * self.multiplier
        return self.option().theta(*self.params())

    @compute
    def rho(self) -> float:
        if self.product_type == 'European' or self.product_type == 'American' or self.product_type == 'Asian':
            return self.option().rho(*self.params()) * self.multiplier
        return self.option().rho(*self.params())

    @compute
    def rho_q(self) -> float:
        if self.product_type == 'European' or self.product_type == 'American' or self.product_type == 'Asian':
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
    knock_out_type: TuringEquityKnockoutTypes = StringField("knock_out_type")  # yapi无值
    knock_in_type = StringField("knock_in_type")  # yapi无值
    knock_in_strike1: float = FloatField("knock_in_strike1")  # yapi无值
    knock_in_strike2: float = FloatField("knock_in_strike2")  # yapi无值

    def __init__(self, **kw):
        super().__init__(**kw)
        quote = Quotes()
        self.name = 'No name'
        self.value_date = quote.value_date
        self.stock_price = quote.stock_price
        self.volatility = quote.volatility
        self.interest_rate = quote.interest_rate
        self.dividend_yield = quote.dividend_yield
        self.accrued_average = quote.accrued_average


@model
@dataclass
class EqOption(OptionModel):
    """
        Instrument definition for equity option
        支持多种参数传入方式
        Examples:
        1.
        # >>> eq = EqOption(option_type='call',product_type='European',option_data={'asset_id': '123'})
        # >>> eq.from_json()
        # >>> eq.price()
        2.
        # >>> eq = EqOption(option_type='call',product_type='European',expiration_date=TuringDate(12, 2, 2021), strike_price=90, multiplier=10000)
        # >>> eq.price()
        3.
        # >>> eq = EqOption(option_type='call',product_type='European', notional=1.00, option_data={'asset_id': '123'})
        # >>> eq.from_json()
        # >>> eq.price()
    """
    asset_id: str = None
    trade_id: str = None  # 合约编号
    underlier: str = None  # 标的证券
    buy_sell: Union[BuySell, str] = None  # 买卖方向
    counterparty: Union[Exchange, str] = None  # 交易所名称（场内）/交易对手名称（场外）
    option_type: str = None  # style + type
    product_type: str = None
    knock_type: TuringEquityKnockoutTypes = None  # 敲出类型
    notional: float = None  # 名义本金
    initial_spot: float = None  # 期初价格
    number_of_options: float = None  # 期权数量：名义本金/期初价格
    start_date: TuringDate = None  # 开始时间
    end_date: TuringDate = None  # 期末观察日
    expiration_date: TuringDate = None  # 到期日
    exercise_date: TuringDate = None  # 行权日
    participation_rate: float = None  # 参与率
    strike_price: float = None  # 行权价
    barrier: float = None  # 敲出价
    rebate: float = None  # 敲出补偿收益率
    multiplier: float = None  # 合约乘数
    settlement_date: TuringDate = None  # 结算日期
    settlement_currency: Union[Currency, str] = None  # 结算货币
    premium: float = 0  # 期权费
    premium_payment_date: TuringDate = None  # 期权费支付日期
    method_of_settlement: Union[OptionSettlementMethod, str] = None  # 结算方式
    premium_currency: Union[Currency, str] = None  # 期权费币种
    start_averaging_date: TuringDate = None  # 观察起始日
    knock_out_price: float = None  # 敲出价格
    knock_in_price: float = None  # 敲入价格
    coupon_rate: float = None  # 票面利率
    coupon_annualized_flag: bool = None  # 票面利率是否为年化的标识
    knock_in_type: Union[TuringKnockInTypes, str] = None  # 敲入类型
    knock_in_strike1: float = None  # 敲入执行价1
    knock_in_strike2: float = None  # 敲入执行价2
    name: str = None  # 对象标识名
    value_date: TuringDate = None  # 估值日期
    stock_price: float = None  # 股票价格
    volatility: float = None  # 波动率
    interest_rate: float = None  # 无风险利率
    dividend_yield: float = None  # 股息率
    accrued_average: float = None  # 应计平均价
    ctx: Context = ctx
    knock_out_type: str = None
    obj: (Stock, Option) = None

    def __post_init__(self):
        quote = Quotes()
        self.name = 'No name'
        self.value_date = quote.value_date
        self.stock_price = quote.stock_price
        self.volatility = quote.volatility
        self.interest_rate = quote.interest_rate
        self.dividend_yield = quote.dividend_yield
        self.accrued_average = quote.accrued_average

    def resolve(self):
        for k, v in self.obj.items():
            # print(k,v)
            setattr(self, k, v)

if __name__ == '__main__':
    eq = EqOption(asset_id='123', option_type='call', product_type='European', expiration_date=TuringDate(12, 2, 2021),
                  strike_price=90, multiplier=10000, dividend_curve=0.3)
    # eq.from_json()
    eq.price()
    # logger.debug(f"eq.asset_id,notional: {eq.asset_id},{eq.notional}")
