from dataclasses import dataclass

from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.calendar import TuringCalendarTypes
from turing_models.utilities.schedule import TuringSchedule
from turing_models.utilities.global_variables import gNumObsInYear
from turing_models.utilities.global_types import TuringOptionTypes, TuringOptionType
from turing_models.models.model_black_scholes_analytical import bs_value, bs_delta, \
     bs_vega, bs_gamma, bs_rho, bs_psi, bs_theta, bsImpliedVolatility
from turing_models.instruments.equity_option import EqOption
from turing_models.utilities.error import TuringError


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class EuropeanOption(EqOption):

    def __post_init__(self):
        super().__post_init__()

    @property
    def option_type_(self) -> TuringOptionTypes:
        if self.option_type == "CALL" or self.option_type == TuringOptionType.CALL:
            return TuringOptionTypes.EUROPEAN_CALL
        elif self.option_type == "PUT" or self.option_type == TuringOptionType.PUT:
            return TuringOptionTypes.EUROPEAN_PUT
        else:
            raise TuringError('Please check the input of option_type')

    @property
    def texp(self) -> float:
        """欧式期权bs模型中的t采用交易日计数"""
        if self.expiry >= self.value_date_:
            schedule_daily = TuringSchedule(self.value_date_,
                                            self.expiry,
                                            freqType=TuringFrequencyTypes.DAILY,
                                            calendarType=TuringCalendarTypes.CHINA_SSE)
            # 考虑一开一闭区间
            num_days = len(schedule_daily._adjustedDates) - 1
            return num_days / gNumObsInYear
        else:
            raise TuringError("Expiry must be > Value_Date")

    def params(self) -> list:
        return [
            self.stock_price_,
            self.texp,
            self.strike_price,
            self.r,
            self.q,
            self.v,
            self.option_type_.value
        ]

    def price(self) -> float:
        return bs_value(*self.params()) * self._multiplier * self._number_of_options

    def eq_delta(self) -> float:
        return bs_delta(*self.params()) * self._multiplier * self._number_of_options

    def eq_gamma(self) -> float:
        return bs_gamma(*self.params()) * self._multiplier * self._number_of_options

    def eq_vega(self) -> float:
        return bs_vega(*self.params()) * self._multiplier * self._number_of_options

    def eq_theta(self) -> float:
        return bs_theta(*self.params()) * self._multiplier * self._number_of_options

    def eq_rho(self) -> float:
        return bs_rho(*self.params()) * self._multiplier * self._number_of_options

    def eq_rho_q(self) -> float:
        return bs_psi(*self.params()) * self._multiplier * self._number_of_options

    def implied_volatility(self, mkt, signal):

        ''' Calculate the Black-Scholes implied volatility of a European
        vanilla option. '''

        texp = self.texp

        if texp < 1.0 / 365.0:
            print("Expiry time is too close to zero.")
            return -999

        r = self.r
        q = self.q
        s0 = self.stock_price_
        k = self.strike_price
        price = mkt
        sigma = bsImpliedVolatility(s0, texp, k, r, q, price,
                                    self.option_type_.value)
        if signal == "sigma":
            return sigma
        elif signal == "surface":
            return k, sigma
