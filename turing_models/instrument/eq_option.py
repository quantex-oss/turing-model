from copy import deepcopy
from dataclasses import dataclass, InitVar
from typing import Union

from loguru import logger
from tunny.compute import compute

from fundamental.base import Priceable, StringField, FloatField, DateField, BoolField, Context
from fundamental.base import ctx
from fundamental.market.curves import TuringDiscountCurveFlat
from turing_models.instrument.common import AssetClass, AssetType, BuySell, Exchange, Currency, OptionSettlementMethod
from turing_models.instrument.quotes import Quotes
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.products.equity import TuringEquitySnowballOption, TuringEquityAsianOption, \
    TuringEquityAmericanOption, TuringEquityVanillaOption, TuringAsianOptionValuationMethods, \
    TuringEquityKnockoutOption, TuringEquityKnockoutTypes, TuringKnockInTypes
from turing_models.utilities import TuringOptionTypes, TuringDate, TuringError, checkArgumentTypes


class OptionModel:

    def option_name(self):
        if isinstance(self.option_type, str) and isinstance(self.product_type, str):
            if self.option_type == "call":
                if self.product_type == "European":
                    self.option_type_turing = TuringOptionTypes.EUROPEAN_CALL
                    return "european", "generic"
                elif self.product_type == "American":
                    self.option_type_turing = TuringOptionTypes.AMERICAN_CALL
                    return "american", "generic"
                elif self.product_type == "Asian":
                    self.option_type_turing = TuringOptionTypes.ASIAN_CALL
                    return "asian", "asian"
                elif self.product_type == "Snowball" and isinstance(self.knock_in_type, str):
                    self.option_type_turing = TuringOptionTypes.SNOWBALL_CALL
                    if self.knock_in_type == "Return":
                        self.knock_in_type_turing = TuringKnockInTypes.RETURN
                    elif self.knock_in_type == "Vanilla":
                        self.knock_in_type_turing = TuringKnockInTypes.VANILLA
                    elif self.knock_in_type == "Spreads":
                        self.knock_in_type_turing = TuringKnockInTypes.SPREADS
                    else:
                        raise TuringError("Knockin type unknown.")
                    return "snowball", "generic"
                elif self.product_type == "Knockout" and isinstance(self.knock_out_type, str):
                    self.option_type_turing = TuringOptionTypes.KNOCKOUT
                    if self.knock_out_type == "down_and_out":
                        self.knock_out_type_turing = TuringEquityKnockoutTypes.DOWN_AND_OUT_CALL
                    elif self.knock_out_type == "up_and_out":
                        self.knock_out_type_turing = TuringEquityKnockoutTypes.UP_AND_OUT_CALL
                    else:
                        raise TuringError("Knockout type unknown.")
                    return "knockout", "generic"
                else:
                    raise TuringError("Product type unknown.")
            elif self.option_type == "put":
                if self.product_type == "European":
                    self.option_type_turing = TuringOptionTypes.EUROPEAN_PUT
                    return "european", "generic"
                elif self.product_type == "American":
                    self.option_type_turing = TuringOptionTypes.AMERICAN_PUT
                    return "american", "generic"
                elif self.product_type == "Asian":
                    self.option_type_turing = TuringOptionTypes.ASIAN_PUT
                    return "asian", "asian"
                elif self.product_type == "Snowball" and isinstance(self.knock_in_type, str):
                    self.option_type_turing = TuringOptionTypes.SNOWBALL_PUT
                    if self.knock_in_type == "Return":
                        self.knock_in_type_turing = TuringKnockInTypes.RETURN
                    elif self.knock_in_type == "Vanilla":
                        self.knock_in_type_turing = TuringKnockInTypes.VANILLA
                    elif self.knock_in_type == "Spreads":
                        self.knock_in_type_turing = TuringKnockInTypes.SPREADS
                    else:
                        raise TuringError("Knockin type unknown.")
                    return "snowball", "generic"
                elif self.product_type == "Knockout" and isinstance(self.knock_out_type, str):
                    self.option_type_turing = TuringOptionTypes.KNOCKOUT
                    if self.knock_out_type == "down_and_out":
                        self.knock_out_type_turing = TuringEquityKnockoutTypes.DOWN_AND_OUT_PUT
                    elif self.knock_out_type == "up_and_out":
                        self.knock_out_type_turing = TuringEquityKnockoutTypes.UP_AND_OUT_PUT
                    else:
                        raise TuringError("Knockout type unknown.")
                    return "knockout", "generic"
                else:
                    raise TuringError("Product type unknown.")
            else:
                raise TuringError("Option type unknown.")

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
    def asset_class(self) -> AssetClass:
        """Equity"""
        return AssetClass.Equity

    @property
    def asset_type(self) -> AssetType:
        """Option"""
        return AssetType.Option

    @property
    @compute
    def model(self) -> TuringModelBlackScholes:
        return TuringModelBlackScholes(self.volatility)

    @property
    @compute
    def discount_curve(self) -> TuringDiscountCurveFlat:
        return TuringDiscountCurveFlat(
            self.value_date, self.interest_rate)

    @property
    @compute
    def dividend_curve(self) -> TuringDiscountCurveFlat:
        return TuringDiscountCurveFlat(
            self.value_date, self.dividend_yield)

    @compute
    def price(self) -> float:
        return self.option().value(*self.params())

    @compute
    def delta(self) -> float:
        return self.option().delta(*self.params())

    @compute
    def gamma(self) -> float:
        return self.option().gamma(*self.params())

    @compute
    def vega(self) -> float:
        return self.option().vega(*self.params())

    @compute
    def theta(self) -> float:
        return self.option().theta(*self.params())

    @compute
    def rho(self) -> float:
        return self.option().rho(*self.params())

    @compute
    def rho_q(self) -> float:
        return self.option().rho_q(*self.params())


class Option(OptionModel, Priceable):
    asset_id = StringField('asset_id')
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


@dataclass
class EqOption(OptionModel):
    """Instrument definition for equity option"""
    trade_id: str = None  # 合约编号
    underlier: str = None  # 标的证券
    buy_sell: Union[BuySell, str] = None  # 买卖方向
    counterparty: Union[Exchange, str] = None  # 交易所名称（场内）/交易对手名称（场外）
    option_type: str = None  # style + type
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
    option_data: InitVar[dict] = None
    ctx: Context = ctx

    def __post_init__(self, option_data):
        checkArgumentTypes(self.__post_init__, locals())
        self.__option_data = option_data

    def from_json(self):
        option_data = deepcopy(self.__option_data)
        logger.debug(option_data)
        self.quote_obj = Quotes()
        self.quote_obj.resolve(_resource=option_data)
        self.option_obj = Option()
        self.option_obj.resolve(_resource=option_data)

    def __getattr__(self, item):
        try:
            return getattr(self.quote_obj, item, None) or getattr(self.option_obj, item)
        except Exception:
            return None


if __name__ == '__main__':
    eq = EqOption(option_type='call', notional=1.00, option_data={'asset_id': '123'})
    eq.from_json()
    # eq.price()
    logger.debug(f"eq.asset_id,notional:, {eq.asset_id},{eq.notional}")
