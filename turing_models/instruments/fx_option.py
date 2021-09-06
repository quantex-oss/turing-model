import datetime
from dataclasses import dataclass, field
from typing import List, Any

import numpy as np
from loguru import logger

from turing_models.instruments.common import FX, Currency
from turing_models.instruments.core import InstrumentBase
from turing_models.market.curves.discount_curve_zeros import TuringDiscountCurveZeros
from turing_models.market.volatility.fx_vol_surface_vv import TuringFXVolSurfaceVV
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.utilities.error import TuringError
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.global_types import TuringOptionTypes, TuringOptionType, TuringExerciseType
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.helper_functions import to_string
from turing_models.utilities.turing_date import TuringDate

###############################################################################
# ALL CCY RATES MUST BE IN NUM UNITS OF DOMESTIC PER UNIT OF FOREIGN CURRENCY
# SO EURUSD = 1.30 MEANS 1.30 DOLLARS PER EURO SO DOLLAR IS THE DOMESTIC AND
# EUR IS THE FOREIGN CURRENCY
###############################################################################


error_str = "Time to expiry must be positive."
error_str2 = "Volatility should not be negative."
error_str3 = "Exchange Rate must be greater than zero."


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class FXOption(FX, InstrumentBase):
    asset_id: str = None
    product_type: str = None  # VANILLA
    underlier: str = None
    underlier_symbol: str = None  # USD/CNY (外币/本币)
    notional: float = None
    notional_currency: (str, Currency) = None
    strike: float = None
    expiry: TuringDate = None
    delivery_date: TuringDate = None
    cut_off_time: TuringDate = None
    exercise_type: (str, TuringExerciseType) = None  # EUROPEAN
    option_type: (str, TuringOptionType) = None  # CALL/PUT
    start_date: TuringDate = None
    # 1 unit of foreign in domestic
    premium_currency: (str, Currency) = None
    spot_days: int = 2
    value_date: TuringDate = TuringDate(
        *(datetime.date.today().timetuple()[:3]))
    exchange_rate: float = None  # 1 unit of foreign in domestic
    tenors: List[Any] = field(default_factory=list)
    ccy1_cc_rates: List[Any] = field(default_factory=list)  # 外币
    ccy2_cc_rates: List[Any] = field(default_factory=list)  # 本币
    vol_tenors: List[Any] = field(default_factory=list)
    atm_vols: List[Any] = field(default_factory=list)
    butterfly_25delta_vols: List[Any] = field(default_factory=list)
    risk_reversal_25delta_vols: List[Any] = field(default_factory=list)
    butterfly_10delta_vols: List[Any] = field(default_factory=list)
    risk_reversal_10delta_vols: List[Any] = field(default_factory=list)
    volatility: float = None
    market_price = None
    _value_date = None

    def __post_init__(self):
        super().__init__()
        self.domestic_name = None
        self.foreign_name = None
        logger.debug(f"{self},{self.delivery_date}, {self.expiry}")
        if self.delivery_date and self.expiry and self.delivery_date < self.expiry:
            raise TuringError(
                "Delivery date must be on or after expiry.")

        if self.underlier_symbol and len(self.underlier_symbol) != 7:
            raise TuringError("Currency pair must be 7 characters.")

        if self.strike and np.any(self.strike < 0.0):
            raise TuringError("Negative strike.")
        if self.underlier_symbol:
            self.foreign_name = self.underlier_symbol[0:3]
            self.domestic_name = self.underlier_symbol[4:7]

        if self.notional_currency and isinstance(self.notional_currency, Currency):
            self.notional_currency = self.notional_currency.value

        if self.premium_currency and isinstance(self.premium_currency, Currency):
            self.premium_currency = self.premium_currency.value

        if self.domestic_name and self.foreign_name and self.premium_currency and \
                self.premium_currency != self.domestic_name and self.premium_currency != self.foreign_name:
            raise TuringError("Premium currency not in currency pair.")

        if self.exchange_rate and np.any(self.exchange_rate <= 0.0):
            raise TuringError(error_str3)

        if not self.cut_off_time:
            self.cut_off_time = self.expiry

        self.num_paths = 100000
        self.seed = 4242

    @property
    def option_type_(self) -> TuringOptionTypes:
        if self.option_type == "CALL" or self.option_type == TuringOptionType.CALL:
            if self.exercise_type == "EUROPEAN" or self.exercise_type == TuringExerciseType.EUROPEAN:
                return TuringOptionTypes.EUROPEAN_CALL
            else:
                raise TuringError('Please check the input of exercise_type')
        elif self.option_type == "PUT" or self.option_type == TuringOptionType.PUT:
            if self.exercise_type == "EUROPEAN" or self.exercise_type == TuringExerciseType.EUROPEAN:
                return TuringOptionTypes.EUROPEAN_PUT
            else:
                raise TuringError('Please check the input of exercise_type')
        else:
            raise TuringError('Please check the input of option_type')

    @property
    def value_date_(self):
        date = self._value_date or self.ctx.pricing_date or self.value_date
        return date if date >= self.start_date else self.start_date

    @value_date_.setter
    def value_date_(self, value: TuringDate):
        self._value_date = value

    @property
    def tenors_(self):
        """把年化的时间列表转换为TuringDate格式"""
        return self.value_date_.addYears(self.tenors)

    @property
    def foreign_discount_curve(self):
        if self.tenors_ and self.ccy1_cc_rates:
            return TuringDiscountCurveZeros(
                self.value_date_, self.tenors_, self.ccy1_cc_rates, TuringFrequencyTypes.CONTINUOUS)

    @property
    def domestic_discount_curve(self):
        if self.tenors_ and self.ccy2_cc_rates:
            return TuringDiscountCurveZeros(
                self.value_date_, self.tenors_, self.ccy2_cc_rates, TuringFrequencyTypes.CONTINUOUS)

    @property
    def volatility_surface(self):
        return TuringFXVolSurfaceVV(self.value_date_,
                                    self.exchange_rate,
                                    self.underlier_symbol,
                                    self.notional_currency,
                                    self.domestic_discount_curve,
                                    self.foreign_discount_curve,
                                    self.vol_tenors,
                                    self.atm_vols,
                                    self.butterfly_25delta_vols,
                                    self.risk_reversal_25delta_vols,
                                    self.butterfly_10delta_vols,
                                    self.risk_reversal_10delta_vols)

    @property
    def model(self):
        return TuringModelBlackScholes(self.volatility)

    @property
    def tdel(self):
        spot_date = self.value_date_.addWeekDays(self.spot_days)
        td = (self.delivery_date - spot_date) / gDaysInYear
        if td < 0.0:
            raise TuringError(error_str)
        td = np.maximum(td, 1e-10)
        return td

    @property
    def texp(self):
        return (self.cut_off_time - self.value_date_) / gDaysInYear

    @property
    def rd(self):
        texp = self.texp
        domDF = self.domestic_discount_curve._df(texp)
        return -np.log(domDF) / texp

    @property
    def rf(self):
        texp = self.texp
        forDF = self.foreign_discount_curve._df(texp)
        return -np.log(forDF) / texp

    @property
    def vol(self):
        if self.volatility:
            v = self.model._volatility
        elif self.vol_tenors:
            v = self.volatility_surface.volatilityFromStrikeDate(
                self.strike, self.expiry)
        if np.all(v >= 0.0):
            v = np.maximum(v, 1e-10)
            return v
        else:
            raise TuringError(error_str2)

    def price(self):
        return 0.0

    def fx_delta(self):
        return 0.0

    def fx_gamma(self):
        return 0.0

    def fx_vega(self):
        return 0.0

    def fx_theta(self):
        return 0.0

    def fx_vanna(self):
        return 0.0

    def fx_volga(self):
        return 0.0

    def __repr__(self):
        s = to_string("Object Type", type(self).__name__)
        s += to_string("Asset Id", self.asset_id)
        s += to_string("Product Type", self.product_type)
        s += to_string("Underlier", self.underlier)
        s += to_string("Underlier Symbol", self.underlier_symbol)
        s += to_string("Notional", self.notional)
        s += to_string("Notional Currency", self.notional_currency)
        s += to_string("Strike", self.strike)
        s += to_string("Expiry", self.expiry)
        s += to_string("Delivery Date", self.delivery_date)
        s += to_string("Cut Off Time", self.cut_off_time)
        s += to_string("Exercise Type", self.exercise_type)
        s += to_string("Option Type", self.option_type)
        s += to_string("Currency Pair", self.underlier_symbol)
        s += to_string("Start Date", self.start_date)
        s += to_string("Premium Currency", self.premium_currency)
        s += to_string("Exchange Rate", self.exchange_rate)
        s += to_string("Volatility", self.volatility)
        return s
