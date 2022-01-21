from dataclasses import dataclass

from turing_models.utilities.frequency import FrequencyType
from turing_models.utilities.calendar import TuringCalendarTypes
from turing_models.utilities.schedule import TuringSchedule
from turing_models.utilities.global_variables import gNumObsInYear
from turing_models.utilities.global_types import TuringOptionTypes, OptionType
from turing_models.models.model_black_scholes_analytical import bs_value, bs_delta, \
    bs_vega, bs_gamma, bs_rho, bs_psi, bs_theta, bsImpliedVolatility
from turing_models.instruments.eq.equity_option import EqOption
from turing_models.utilities.error import TuringError


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class EuropeanOption(EqOption):

    def __post_init__(self):
        super().__post_init__()
        self.check_param()

    def check_param(self):
        if self.option_type is not None and not isinstance(self.option_type, TuringOptionTypes):
            rules = {
                "CALL": TuringOptionTypes.EUROPEAN_CALL,
                OptionType.CALL: TuringOptionTypes.EUROPEAN_CALL,
                "PUT": TuringOptionTypes.EUROPEAN_PUT,
                OptionType.PUT: TuringOptionTypes.EUROPEAN_PUT
            }
            self.option_type = rules.get(self.option_type,
                                         TuringError('Please check the input of option_type'))
            if isinstance(self.option_type, TuringError):
                raise self.option_type

    def _calculate_intermediate_variable(self):
        super()._calculate_intermediate_variable()
        if getattr(self, 'expiry', None) is not None:
            schedule_daily = TuringSchedule(self.transformed_value_date,
                                            self.expiry,
                                            freqType=FrequencyType.DAILY,
                                            calendarType=TuringCalendarTypes.CHINA_SSE)
            # 考虑一开一闭区间
            num_days = len(schedule_daily._adjustedDates) - 1
            self.texp = num_days / gNumObsInYear

    def params(self) -> list:
        return [
            self.stock_price,
            self.texp,
            self.strike_price,
            self.r,
            self.q,
            self.v,
            self.option_type.value,
            False
        ]

    def price(self) -> float:
        return bs_value(*self.params()) * self.multiplier * self.number_of_options

    def eq_delta(self) -> float:
        return bs_delta(*self.params()) * self.multiplier * self.number_of_options

    def eq_gamma(self) -> float:
        return bs_gamma(*self.params()) * self.multiplier * self.number_of_options

    def eq_vega(self) -> float:
        return bs_vega(*self.params()) * self.multiplier * self.number_of_options

    def eq_theta(self) -> float:
        return bs_theta(*self.params()[:-1]) * self.multiplier * self.number_of_options

    def eq_rho(self) -> float:
        return bs_rho(*self.params()[:-1]) * self.multiplier * self.number_of_options

    def eq_rho_q(self) -> float:
        return bs_psi(*self.params()[:-1]) * self.multiplier * self.number_of_options

    def implied_volatility(self, mkt, signal):
        """ Calculate the Black-Scholes implied volatility of a European
        vanilla option. """

        texp = self.texp

        if texp < 1.0 / 365.0:
            print("Expiry time is too close to zero.")
            return -999

        r = self.r
        q = self.q
        s0 = self.stock_price
        k = self.strike_price
        price = mkt
        sigma = bsImpliedVolatility(s0, texp, k, r, q, price,
                                    self.option_type.value)
        if signal == "sigma":
            return sigma
        elif signal == "surface":
            return k, sigma

    def _resolve(self):
        super()._resolve()
        if self.product_type is None:
            setattr(self, 'product_type', 'European')
        self.__post_init__()

    def __repr__(self):
        s = super().__repr__()
        return s
