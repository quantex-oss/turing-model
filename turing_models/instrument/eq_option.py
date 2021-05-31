from tunny.compute import compute

from fundamental.base import Priceable, StringField, FloatField, DateField, BoolField
from fundamental.market.curves import TuringDiscountCurveFlat
from turing_models.instrument.common import AssetClass, AssetType
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.products.equity import TuringEquitySnowballOption, TuringEquityAsianOption, \
    TuringEquityAmericanOption, TuringEquityVanillaOption, TuringAsianOptionValuationMethods, \
    TuringEquityKnockoutOption, TuringEquityKnockoutTypes, TuringKnockInTypes
from turing_models.utilities import TuringOptionTypes, TuringDate, TuringError
from .quotes import Quotes


class EqOption(Priceable):
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
    participation_rate = FloatField("participation_rate")
    strike_price: float = FloatField("strike")
    barrier = FloatField("barrier")
    rebate = FloatField("rebate")
    coupon = FloatField("coupon")
    multiplier = FloatField("multiplier")
    settlement_currency = StringField("settlement_currency")
    premium = FloatField("premium")
    premium_payment_date: TuringDate = DateField("premium_payment_date")
    method_of_settlement = StringField("method_of_settlement")
    knock_out_price = FloatField("knock_out_price")  # yapi无值
    knock_in_price = FloatField("knock_in_price")  # yapi无值
    coupon_rate = FloatField("coupon_rate")  # yapi无值
    coupon_annualized_flag = BoolField("coupon_annualized_flag")  # yapi无值
    knock_out_type = StringField("knock_out_type")  # yapi无值
    knock_in_type = StringField("knock_in_type")  # yapi无值
    knock_in_strike1 = FloatField("knock_in_strike1")  # yapi无值
    knock_in_strike2 = FloatField("knock_in_strike2")  # yapi无值

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
            self.knock_out_type,
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
