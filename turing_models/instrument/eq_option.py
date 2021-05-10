import datetime
from typing import Union

from tunny.models import model

from fundamental import ctx
from turing_models.instrument.common import OptionType, OptionStyle, Currency, \
    OptionSettlementMethod, BuySell, AssetClass, AssetType
from turing_models.market.curves import TuringDiscountCurveFlat
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.products.equity import TuringOptionTypes, \
    TuringEquityVanillaOption
from turing_models.utilities.turing_date import TuringDate


@model
class EqOption:
    """Instrument definition for equity option"""

    def __init__(
            self,
            trade_id: str = None,
            buy_sell: Union[BuySell, str] = None,
            counterparty: str = None,
            option_type: Union[OptionType, str] = None,
            option_style: Union[OptionStyle, str] = None,
            type: str = None,
            underlier: str = None,
            notional: float = None,
            initial_spot: float = None,
            number_of_options: float = None,
            start_date: Union[datetime.date, str] = None,
            end_date: Union[datetime.date, str] = None,
            expiration_date: Union[datetime.date, str] = None,
            exercise_date: Union[datetime.date, str] = None,
            participation_rate: float = None,
            strike_price: float = None,
            barrier: float = None,
            rebate: float = None,
            multiplier: float = None,
            settlement_date: Union[datetime.date, str] = None,
            settlement_currency: Union[Currency, str] = None,
            premium: float = 0,
            premium_payment_date: Union[datetime.date, str] = None,
            method_of_settlement: Union[OptionSettlementMethod, str] = None,
            premium_currency: Union[Currency, str] = None,
            status: str = None,
            name: str = None,
            value_date: Union[datetime.date, str] = None,
            stock_price: float = None,
            volatility: float = None,
            interest_rate: float = None,
            dividend_yield: float = None,
    ):
        self.trade_id = trade_id
        self.buy_sell = buy_sell
        self.counterparty = counterparty
        self.option_type = option_type
        self.option_style = option_style
        self.type = type
        self.underlier = underlier
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
        self.status = status
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
        elif isinstance(self.value_date, str):
            self.value_date = TuringDate.fromString(self.value_date, "%Y-%m-%d")

        if isinstance(self.expiration_date, datetime.date):
            self.expiration_date = TuringDate(y=self.expiration_date.year, m=self.expiration_date.month,
                                              d=self.expiration_date.day)
        elif isinstance(self.expiration_date, str):
            self.expiration_date = TuringDate.fromString(self.expiration_date, "%Y-%m-%d")

        # 欧式期权
        if self.option_style == OptionStyle.European or self.option_style == 'European':
            if self.option_type == OptionType.Call or self.option_type == 'Call':
                self.option_type = TuringOptionTypes.EUROPEAN_CALL
            elif self.option_type == OptionType.Put or self.option_type == 'Put':
                self.option_type = TuringOptionTypes.EUROPEAN_PUT

            self.option = TuringEquityVanillaOption(
                self.expiration_date,
                self.strike_price,
                self.option_type)

            self.bs_model = TuringModelBlackScholes(self.volatility)
        self.dividend_curve = TuringDiscountCurveFlat(self.value_date,
                                                      self.dividend_yield)

        # 美式期权
        # 亚式期权
        # 雪球期权
        ##################################################################################

    def interest_rate(self) -> float:
        return self.ctx.path.r() \
            if self.ctx.path and self.ctx.path.r() \
            else self.__interest_rate

    @property
    def discount_curve(self):
        return TuringDiscountCurveFlat(
            self.value_date, self.interest_rate())

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
            self.bs_model
        ]

    def price(self) -> float:
        return self.option.value(*self.params) \
               * self.number_of_options

    def delta(self) -> float:
        return self.option.delta(*self.params) \
               * self.number_of_options

    def gamma(self) -> float:
        return self.option.gamma(*self.params) \
               * self.number_of_options

    def vega(self) -> float:
        return self.option.vega(*self.params) \
               * self.number_of_options

    def theta(self) -> float:
        return self.option.theta(*self.params) \
               * self.number_of_options

    def rho(self) -> float:
        return self.option.rho(*self.params) \
               * self.number_of_options


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

    print(
        f"Option Price: {option.price()}, Delta: {option.delta()}, Gamma: {option.gamma()}, Vega: {option.vega()}, Theta: {option.theta()}, Rho: {option.rho()}")
