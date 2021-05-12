import datetime
from typing import Union

from tunny.models import model

from fundamental import ctx
from turing_models.instrument.common import OptionType, OptionStyle, Currency, \
    OptionSettlementMethod, BuySell, AssetClass, AssetType, Exchange, KnockType
from turing_models.market.curves import TuringDiscountCurveFlat
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.products.equity import TuringOptionTypes, \
    TuringEquityVanillaOption, TuringEquityAsianOption, \
    TuringAsianOptionValuationMethods
from turing_models.utilities.error import TuringError
from turing_models.utilities.turing_date import TuringDate


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
            name: str = None,
            value_date: datetime.date = None,
            stock_price: float = None,
            volatility: float = None,
            interest_rate: float = None,
            dividend_yield: float = None,
    ):
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

        ##################################################################################
        # 时间格式转换
        self.ctx = ctx
        if isinstance(self.value_date, datetime.date):
            self.value_date = TuringDate(y=self.value_date.year, m=self.value_date.month, d=self.value_date.day)
        else:
            raise TuringError("Dates must be a 'datetime.date' object")

        if isinstance(self.expiration_date, datetime.date):
            self.expiration_date = TuringDate(y=self.expiration_date.year, m=self.expiration_date.month,
                                              d=self.expiration_date.day)
        else:
            raise TuringError("Dates must be a 'datetime.date' object")

        if self.start_averaging_date is not None:
            if isinstance(self.start_averaging_date, datetime.date):
                self.start_averaging_date = TuringDate(y=self.start_averaging_date.year,
                                                       m=self.start_averaging_date.month,
                                                       d=self.start_averaging_date.day)
            else:
                raise TuringError("Dates must be a 'datetime.date' object")

        if self.option_type == OptionType.Call or self.option_type == 'Call':
            self.option_type = TuringOptionTypes.EUROPEAN_CALL
        elif self.option_type == OptionType.Put or self.option_type == 'Put':
            self.option_type = TuringOptionTypes.EUROPEAN_PUT

        self.model = TuringModelBlackScholes(self.volatility)
        self.dividend_curve = TuringDiscountCurveFlat(self.value_date, self.dividend_yield)

        self.option = self.get_option()

        ##################################################################################

    def get_option(self):
        # 欧式期权
        if self.option_style == OptionStyle.European or self.option_style == 'European':
            option = TuringEquityVanillaOption(
                self.expiration_date,
                self.strike_price,
                self.option_type)

        # 美式期权
        # 亚式期权
        if self.option_style == OptionStyle.Asian or self.option_style == 'Asian':
            option = TuringEquityAsianOption(
                self.start_averaging_date,
                self.expiration_date,
                self.strike_price,
                self.option_type)

        # 雪球期权
        return option

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
    def params(self) -> list:
        return [
            self.value_date,
            self.stock_price,
            self.discount_curve,
            self.dividend_curve,
            self.model
        ]

    def price(self) -> float:
        if self.option_style == OptionStyle.European or self.option_style == 'European':
            return self.option.value(*self.params)
        elif self.option_style == OptionStyle.Asian or self.option_style == 'Asian':
            return self.option.value(self.value_date,
                                     self.stock_price,
                                     self.discount_curve,
                                     self.dividend_curve,
                                     self.model,
                                     method=TuringAsianOptionValuationMethods.CURRAN,
                                     accruedAverage=None)

    def delta(self) -> float:
        return self.option.delta(*self.params)

    def gamma(self) -> float:
        return self.option.gamma(*self.params)

    def vega(self) -> float:
        return self.option.vega(*self.params)

    def theta(self) -> float:
        return self.option.theta(*self.params)

    def rho(self) -> float:
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
