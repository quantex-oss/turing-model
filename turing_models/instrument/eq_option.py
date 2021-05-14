import datetime
from typing import Union

from tunny import model, compute

from fundamental import ctx
from turing_models.instrument.common import OptionType, OptionStyle, Currency, \
     OptionSettlementMethod, BuySell, AssetClass, AssetType, Exchange, KnockType
from turing_models.market.curves import TuringDiscountCurveFlat
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.products.equity import TuringOptionTypes, \
     TuringEquityVanillaOption, TuringEquityAmericanOption, \
     TuringEquityAsianOption, TuringAsianOptionValuationMethods
from turing_models.utilities.error import TuringError
from turing_models.utilities.turing_date import TuringDate, fromDatetime
from turing_models.utilities.helper_functions import checkArgumentTypes


class OptionBase:
    """Create an option object"""

    def __init__(
            self,
            option_type: TuringOptionTypes,
            expiration_date: TuringDate,
            strike_price: float,
            start_averaging_date: TuringDate,
    ):
        self.option_type = option_type
        self.expiration_date = expiration_date
        self.strike_price = strike_price
        self.start_averaging_date = start_averaging_date

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
            option_style: Union[OptionStyle, str] = None,  # 欧式/美式等
            option_type: Union[OptionType, str] = None,  # call/put
            knock_type: Union[KnockType, str] = None,  # 敲入敲出
            notional: float = None,  # 名义本金
            initial_spot: float = None,  # 期初价格
            number_of_options: float = None,  # 期权数量：名义本金/期初价格
            start_date: datetime.date = None,  # 开始时间
            end_date: datetime.date = None,  # 期末观察日
            expiration_date: datetime.date = None,  # 到期日
            exercise_date: datetime.date = None,  # 行权日
            participation_rate: float = None,  # 参与率
            strike_price: float = None,  # 行权价
            barrier: float = None,  # 敲出价
            rebate: float = None,  # 敲出补偿收益率
            multiplier: float = None,  # 合约乘数
            settlement_date: datetime.date = None,  # 结算日期
            settlement_currency: Union[Currency, str] = None,  # 结算货币
            premium: float = 0,  # 期权费
            premium_payment_date: datetime.date = None,  # 期权费支付日期
            method_of_settlement: Union[OptionSettlementMethod, str] = None,  # 结算方式
            premium_currency: Union[Currency, str] = None,  # 期权费币种
            start_averaging_date: datetime.date = None,  # 观察起始日
            name: str = None,  # 对象标识名
            value_date: datetime.date = None,  # 估值日期
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
        self.option_style = option_style
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
        self.name = name
        self.value_date = value_date
        self.stock_price = stock_price
        self.volatility = volatility
        self.__interest_rate = interest_rate
        self.dividend_yield = dividend_yield
        self.accrued_average = accrued_average
        ##################################################################################
        self.ctx = ctx

        # 时间格式转换
        self.time_reformat()

        # 期权类型格式转换
        self.option_type_reformat()

        self.model = TuringModelBlackScholes(self.volatility)
        self.dividend_curve = TuringDiscountCurveFlat(self.value_date,
                                                      self.dividend_yield)
        option_base = OptionBase(self.option_type,
                                 self.expiration_date,
                                 self.strike_price,
                                 self.start_averaging_date)
        self.option = option_base.get_option()

    def time_reformat(self):
        """将datetime.date转换为TuringDate"""

        if self.start_date is not None:
            self.start_date = fromDatetime(self.start_date)

        if self.end_date is not None:
            self.end_date = fromDatetime(self.end_date)

        if self.expiration_date is not None:
            self.expiration_date = fromDatetime(self.expiration_date)

        if self.exercise_date is not None:
            self.exercise_date = fromDatetime(self.exercise_date)

        if self.settlement_date is not None:
            self.settlement_date = fromDatetime(self.settlement_date)

        if self.premium_payment_date is not None:
            self.premium_payment_date = fromDatetime(self.premium_payment_date)

        if self.start_averaging_date is not None:
            self.start_averaging_date = fromDatetime(self.start_averaging_date)

        if self.value_date is not None:
            self.value_date = fromDatetime(self.value_date)

    def option_type_reformat(self):
        """将OptionStyle+OptionTypt与TuringOptionTypes对应起来"""

        if (self.option_style == OptionStyle.European or
                self.option_style == 'European'):
            if (self.option_type == OptionType.Call or
                    self.option_type == 'Call'):
                self.option_type = TuringOptionTypes.EUROPEAN_CALL
            elif (self.option_type == OptionType.Put or
                    self.option_type == 'Put'):
                self.option_type = TuringOptionTypes.EUROPEAN_PUT
        elif (self.option_style == OptionStyle.American or
                self.option_style == 'American'):
            if (self.option_type == OptionType.Call or
                    self.option_type == 'Call'):
                self.option_type = TuringOptionTypes.AMERICAN_CALL
            elif (self.option_type == OptionType.Put or
                    self.option_type == 'Put'):
                self.option_type = TuringOptionTypes.AMERICAN_PUT
        elif (self.option_style == OptionStyle.Asian or
                self.option_style == 'Asian'):
            if (self.option_type == OptionType.Call or
                    self.option_type == 'Call'):
                self.option_type = TuringOptionTypes.ASIAN_CALL
            elif (self.option_type == OptionType.Put or
                    self.option_type == 'Put'):
                self.option_type = TuringOptionTypes.ASIAN_PUT
        else:
            raise TuringError("Argument Content Error")

    def interest_rate(self) -> float:
        return self.ctx.path.r() \
            if self.ctx.path and self.ctx.path.r() \
            else self.__interest_rate

    @property
    def discount_curve(self):
        return TuringDiscountCurveFlat(
            self.value_date, self.interest_rate())

    ######################################################################################
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
    def params(self) -> list:
        print("params update...")
        params = []
        if (self.option_style == OptionStyle.European or
                self.option_style == 'European' or
                self.option_style == OptionStyle.American or
                self.option_style == 'American'):
            params = [
                self.value_date,
                self.stock_price,
                self.discount_curve,
                self.dividend_curve,
                self.model
            ]

        if (self.option_style == OptionStyle.Asian or
                self.option_style == 'Asian'):
            # FIXME: 'ModelProxy' object has no attribute 'accruedAverage'
            params = [self.value_date,
                      self.stock_price,
                      self.discount_curve,
                      self.dividend_curve,
                      self.model,
                      TuringAsianOptionValuationMethods.CURRAN,
                      self.accrued_average]
        return params

    @params.setter
    def params(self, value):
        pass

    @compute
    def price(self) -> float:
        print(f"price called... r={self.ctx.path.r() if self.ctx.path else None}")
        return self.option.value(*self.params)

    @compute
    def delta(self) -> float:
        print(f"delta called... r={self.ctx.path.r() if self.ctx.path else None}")
        return self.option.delta(*self.params)

    @compute
    def gamma(self) -> float:
        print(f"gamma called... r={self.ctx.path.r() if self.ctx.path else None}")
        return self.option.gamma(*self.params)

    @compute
    def vega(self) -> float:
        print(f"vega called... r={self.ctx.path.r() if self.ctx.path else None}")
        return self.option.vega(*self.params)

    @compute
    def theta(self) -> float:
        print(f"theta called... r={self.ctx.path.r() if self.ctx.path else None}")
        return self.option.theta(*self.params)

    @compute
    def rho(self) -> float:
        print(f"rho called... r={self.ctx.path.r() if self.ctx.path else None}")
        return self.option.rho(*self.params)


if __name__ == "__main__":
    option = EqOption(option_type=OptionType.Call,
                      option_style=OptionStyle.European,
                      number_of_options=100,
                      expiration_date=datetime.date(2021, 7, 25),
                      strike_price=500.0,
                      value_date=datetime.date(2021, 4, 25),
                      stock_price=510.0,
                      volatility=0.02,
                      interest_rate=0.03,
                      dividend_yield=0)

    print(f"Option Price: {option.price()}")
