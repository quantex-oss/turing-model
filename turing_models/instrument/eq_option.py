from typing import Union

from tunny.models import model
from tunny import compute

from fundamental import ctx
from turing_models.instrument.common import Currency, \
     OptionSettlementMethod, BuySell, AssetClass, AssetType, Exchange, \
     KnockType
from turing_models.market.curves import TuringDiscountCurveFlat
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.products.equity import TuringOptionTypes, \
     TuringEquityVanillaOption, TuringEquityAmericanOption, \
     TuringEquityAsianOption, TuringAsianOptionValuationMethods, \
     TuringEquitySnowballOption, TuringKnockInTypes
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.helper_functions import checkArgumentTypes


class OptionBase:
    """Create an option object"""

    def __init__(
            self,
            option_type: TuringOptionTypes,
            expiration_date: TuringDate,
            strike_price: float,
            start_averaging_date: TuringDate,
            knock_out_price: float,
            knock_in_price: float,
            notional: float,
            coupon_rate: float,
            knock_in_type: TuringKnockInTypes,
            knock_in_strike1: float,
            knock_in_strike2: float
    ):
        self.option_type = option_type
        self.expiration_date = expiration_date
        self.strike_price = strike_price
        self.start_averaging_date = start_averaging_date
        self.knock_out_price = knock_out_price
        self.knock_in_price = knock_in_price
        self.notional = notional
        self.coupon_rate = coupon_rate
        self.knock_in_type = knock_in_type
        self.knock_in_strike1 = knock_in_strike1
        self.knock_in_strike2 = knock_in_strike2

    def get_option(self):
        """返回期权实例化对象"""

        if (self.option_type == TuringOptionTypes.EUROPEAN_CALL or
                self.option_type == TuringOptionTypes.EUROPEAN_PUT):
            option = TuringEquityVanillaOption(
                self.expiration_date,
                self.strike_price,
                self.option_type)
        elif (self.option_type == TuringOptionTypes.AMERICAN_CALL or
                self.option_type == TuringOptionTypes.AMERICAN_PUT):
            option = TuringEquityAmericanOption(
                self.expiration_date,
                self.strike_price,
                self.option_type)
        elif (self.option_type == TuringOptionTypes.ASIAN_CALL or
                self.option_type == TuringOptionTypes.ASIAN_PUT):
            option = TuringEquityAsianOption(
                self.start_averaging_date,
                self.expiration_date,
                self.strike_price,
                self.option_type)
        elif (self.option_type == TuringOptionTypes.SNOWBALL_CALL or
                self.option_type == TuringOptionTypes.SNOWBALL_PUT):
            option = TuringEquitySnowballOption(
                self.expiration_date,
                self.knock_out_price,
                self.knock_in_price,
                self.notional,
                self.coupon_rate,
                self.option_type,
                self.knock_in_type,
                self.knock_in_strike1,
                self.knock_in_strike2)

        return option


@model
class EqOption:
    """Instrument definition for equity option"""

    def __init__(
            self,
            trade_id: str = None,  # 合约编号
            underlier: str = None,  # 标的证券
            buy_sell: Union[BuySell, str] = None,  # 买卖方向
            counterparty: Union[Exchange, str] = None,  # 交易所名称（场内）/交易对手名称（场外）
            option_type: TuringOptionTypes = None,  # style + type
            knock_type: Union[KnockType, str] = None,  # 敲入敲出
            notional: float = None,  # 名义本金
            initial_spot: float = None,  # 期初价格
            number_of_options: float = None,  # 期权数量：名义本金/期初价格
            start_date: TuringDate = None,  # 开始时间
            end_date: TuringDate = None,  # 期末观察日
            expiration_date: TuringDate = None,  # 到期日
            exercise_date: TuringDate = None,  # 行权日
            participation_rate: float = None,  # 参与率
            strike_price: float = None,  # 行权价
            barrier: float = None,  # 敲出价
            rebate: float = None,  # 敲出补偿收益率
            multiplier: float = None,  # 合约乘数
            settlement_date: TuringDate = None,  # 结算日期
            settlement_currency: Union[Currency, str] = None,  # 结算货币
            premium: float = 0,  # 期权费
            premium_payment_date: TuringDate = None,  # 期权费支付日期
            method_of_settlement: Union[OptionSettlementMethod, str] = None,  # 结算方式
            premium_currency: Union[Currency, str] = None,  # 期权费币种
            start_averaging_date: TuringDate = None,  # 观察起始日
            knock_out_price: float = None,  # 敲出价格
            knock_in_price: float = None,  # 敲出价格
            coupon_rate: float = None,  # 票面利率
            knock_in_type: Union[TuringKnockInTypes, str] = None,  # 敲入类型
            knock_in_strike1: float = None,  # 敲入执行价1
            knock_in_strike2: float = None,  # 敲入执行价2
            name: str = None,  # 对象标识名
            value_date: TuringDate = None,  # 估值日期
            stock_price: float = None,  # 股票价格
            volatility: float = None,  # 波动率
            interest_rate: float = None,  # 无风险利率
            dividend_yield: float = None,  # 股息率
            accrued_average: float = None  # 应计平均价
    ):
        checkArgumentTypes(self.__init__, locals())

        self.trade_id = trade_id
        self.underlier = underlier
        self.buy_sell = buy_sell
        self.counterparty = counterparty
        self.option_type = option_type
        self.knock_type = knock_type
        self.notional = notional
        self.initial_spot = initial_spot
        self.number_of_options = number_of_options
        self.start_date = start_date
        self.end_date = end_date
        self.expiration_date = expiration_date
        self.exercise_date = exercise_date
        self.participation_rate = participation_rate
        self.strike_price = strike_price
        self.barrier = barrier
        self.rebate = rebate
        self.multiplier = multiplier
        self.settlement_date = settlement_date
        self.settlement_currency = settlement_currency
        self.premium = premium
        self.premium_payment_date = premium_payment_date
        self.method_of_settlement = method_of_settlement
        self.premium_currency = premium_currency
        self.start_averaging_date = start_averaging_date
        self.knock_out_price = knock_out_price
        self.knock_in_price = knock_in_price
        self.coupon_rate = coupon_rate
        self.knock_in_type = knock_in_type
        self.knock_in_strike1 = knock_in_strike1
        self.knock_in_strike2 = knock_in_strike2
        self.name = name
        self.__value_date = value_date
        self.__stock_price = stock_price
        self.__volatility = volatility
        self.__interest_rate = interest_rate
        self.__dividend_yield = dividend_yield
        self.__accrued_average = accrued_average

        self.ctx = ctx

        option_base = OptionBase(self.option_type,
                                 self.expiration_date,
                                 self.strike_price,
                                 self.start_averaging_date,
                                 self.knock_out_price,
                                 self.knock_in_price,
                                 self.notional,
                                 self.coupon_rate,
                                 self.knock_in_type,
                                 self.knock_in_strike1,
                                 self.knock_in_strike2)
        self.option = option_base.get_option()

    @property
    def asset_class(self) -> AssetClass:
        """Equity"""
        return AssetClass.Equity

    @property
    def asset_type(self) -> AssetType:
        """Option"""
        return AssetType.Option

    @property
    def value_date(self) -> float:
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
    @compute
    def model(self):
        return TuringModelBlackScholes(self.volatility)

    @property
    @compute
    def discount_curve(self):
        return TuringDiscountCurveFlat(
            self.value_date, self.interest_rate)

    @property
    @compute
    def dividend_curve(self):
        return TuringDiscountCurveFlat(
            self.value_date, self.dividend_yield)

    @property
    @compute
    def params(self) -> list:
        params = []
        if (self.option_type == TuringOptionTypes.EUROPEAN_CALL or
                self.option_type == TuringOptionTypes.EUROPEAN_PUT or
                self.option_type == TuringOptionTypes.AMERICAN_CALL or
                self.option_type == TuringOptionTypes.AMERICAN_PUT or
                self.option_type == TuringOptionTypes.SNOWBALL_CALL or
                self.option_type == TuringOptionTypes.SNOWBALL_PUT):
            params = [
                self.value_date,
                self.stock_price,
                self.discount_curve,
                self.dividend_curve,
                self.model
            ]

        elif (self.option_type == TuringOptionTypes.ASIAN_CALL or
                self.option_type == TuringOptionTypes.ASIAN_PUT):
            params = [self.value_date,
                      self.stock_price,
                      self.discount_curve,
                      self.dividend_curve,
                      self.model,
                      TuringAsianOptionValuationMethods.CURRAN,
                      self.accrued_average]
        return params

    @compute
    def price(self) -> float:
        return self.option.value(*self.params)

    @compute
    def delta(self) -> float:
        return self.option.delta(*self.params)

    @compute
    def gamma(self) -> float:
        return self.option.gamma(*self.params)

    @compute
    def vega(self) -> float:
        return self.option.vega(*self.params)

    @compute
    def theta(self) -> float:
        return self.option.theta(*self.params)

    @compute
    def rho(self) -> float:
        return self.option.rho(*self.params)

    @compute
    def rho_q(self) -> float:
        return self.option.rho_q(*self.params)