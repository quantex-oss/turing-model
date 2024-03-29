import datetime
from dataclasses import dataclass
from typing import Union

import numpy as np

from turing_models.utilities.mathematics import N
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.global_types import TuringOptionTypes, \
     TuringAsianOptionValuationMethods, OptionType
from turing_models.instruments.eq.equity_option import EqOption
from turing_models.utilities.helper_functions import to_turing_date
from turing_models.utilities.error import TuringError


error_str = "In averaging period so need to enter accrued average."


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class AsianOption(EqOption):

    start_averaging_date: Union[datetime.datetime, str] = None
    accrued_average: float = None
    valuation_method: str = "curran"

    def __post_init__(self):
        super().__post_init__()
        # 对时间格式做转换
        if self.start_averaging_date is not None:
            self.start_averaging_date = to_turing_date(self.start_averaging_date)
            if self.expiry is not None:
                self.num_obs = int(self.expiry - self.start_averaging_date)
        self._check_param()

    def _check_param(self):
        if self.option_type is not None and not isinstance(self.option_type, TuringOptionTypes):
            rules = {
                "CALL": TuringOptionTypes.ASIAN_CALL,
                OptionType.CALL: TuringOptionTypes.ASIAN_CALL,
                "PUT": TuringOptionTypes.ASIAN_PUT,
                OptionType.PUT: TuringOptionTypes.ASIAN_PUT
            }
            self.option_type = rules.get(self.option_type,
                                         TuringError('Please check the input of option_type'))
            if isinstance(self.option_type, TuringError):
                raise self.option_type
        if self.valuation_method is not None:
            if not isinstance(self.valuation_method, TuringAsianOptionValuationMethods):
                rules = {
                    "geometric": TuringAsianOptionValuationMethods.GEOMETRIC,
                    "turnbull_wakeman": TuringAsianOptionValuationMethods.TURNBULL_WAKEMAN,
                    "curran": TuringAsianOptionValuationMethods.CURRAN
                }
                self.valuation_method = rules.get(self.valuation_method,
                                                  TuringError('Please check the input of valuation_method'))
                if isinstance(self.valuation_method, TuringError):
                    raise self.valuation_method

    def price(self) -> float:
        valuation_method = self.valuation_method
        if valuation_method == TuringAsianOptionValuationMethods.GEOMETRIC:
            v = self._value_geometric()

        elif valuation_method == TuringAsianOptionValuationMethods.TURNBULL_WAKEMAN:
            v = self._value_turnbull_wakeman()

        elif valuation_method == TuringAsianOptionValuationMethods.CURRAN:
            v = self._value_curran()

        return v * self.multiplier * self.number_of_options

    def _value_geometric(self):
        # the years to the start of the averaging period
        value_date = self.transformed_value_date
        t0 = (self.start_averaging_date - value_date) / gDaysInYear
        texp = self.texp
        tau = (self.expiry - self.start_averaging_date) / gDaysInYear

        r = self.r
        q = self.q

        vol = self.v

        k = self.strike_price
        n = self.num_obs
        s0 = self.stock_price

        multiple = 1.0

        if t0 < 0:  # we are in the averaging period

            if self.accrued_average is None:
                raise TuringError(error_str)

            # we adjust the strike to account for the accrued coupon
            k = (k * tau + self.accrued_average * t0) / texp
            # the number of options is rescaled also
            multiple = texp / tau
            # there is no pre-averaging time
            t0 = 0.0
            # the number of observations is scaled
            n = n * texp / tau

        sig_sq = vol ** 2
        mean_geo = (r - q - sig_sq / 2.0) * (t0 + (texp - t0) / 2.0)
        var_geo = sig_sq * (t0 + (texp - t0) * (2 * n - 1) / (6 * n))
        eg = s0 * np.exp(mean_geo + var_geo / 2.0)

        d1 = (mean_geo + np.log(s0 / k) + var_geo) / np.sqrt(var_geo)
        d2 = d1 - np.sqrt(var_geo)

        # the Geometric price is the lower bound
        call_g = np.exp(-r * texp) * (eg * N(d1) - k * N(d2))

        if self.option_type == TuringOptionTypes.ASIAN_CALL:
            v = call_g
        elif self.option_type == TuringOptionTypes.ASIAN_PUT:
            put_g = call_g - (eg - k) * np.exp(-r * texp)
            v = put_g

        v = v * multiple
        return v

    def _value_turnbull_wakeman(self):
        value_date = self.transformed_value_date
        t0 = (self.start_averaging_date - value_date) / gDaysInYear
        texp = self.texp
        tau = (self.expiry - self.start_averaging_date) / gDaysInYear

        k = self.strike_price
        multiple = 1.0
        # n = self.num_obs

        r = self.r
        q = self.q

        vol = self.v

        if t0 < 0:  # we are in the averaging period

            if self.accrued_average is None:
                raise TuringError(error_str)

            # we adjust the strike to account for the accrued coupon
            k = (k * tau + self.accrued_average * t0) / texp
            # the number of options is rescaled also
            multiple = texp / tau
            # there is no pre-averaging time
            t0 = 0.0
            # the number of observations is scaled and floored at 1
            # n = int(n * texp / tau + 0.5) + 1

        # need to handle this
        b = r - q
        sigma2 = vol ** 2
        a1 = b + sigma2
        a2 = 2 * b + sigma2
        s0 = self.stock_price

        dt = texp - t0

        if b == 0:
            m1 = 1.0
            m2 = 2.0 * np.exp(sigma2 * texp) - 2.0 * \
                np.exp(sigma2 * t0) * (1.0 + sigma2 * dt)
            m2 = m2 / sigma2 / sigma2 / dt / dt
        else:
            m1 = s0 * (np.exp(b * texp) - np.exp(b * t0)) / (b * dt)
            m2 = np.exp(a2 * texp) / a1 / a2 / dt / dt + \
                (np.exp(a2 * t0) / b / dt / dt) * \
                (1.0 / a2 - np.exp(b * dt) / a1)
            m2 = 2.0 * m2 * s0 * s0

        f0 = m1
        sigma2 = (1.0 / texp) * np.log(m2 / m1 / m1)
        sigma = np.sqrt(sigma2)

        d1 = (np.log(f0 / k) + sigma2 * texp / 2) / sigma / np.sqrt(texp)
        d2 = d1 - sigma * np.sqrt(texp)

        if self.option_type == TuringOptionTypes.ASIAN_CALL:
            call = np.exp(-r * texp) * (f0 * N(d1) - k * N(d2))
            v = call
        elif self.option_type == TuringOptionTypes.ASIAN_PUT:
            put = np.exp(-r * texp) * (k * N(-d2) - f0 * N(-d1))
            v = put

        v = v * multiple
        return v

    def _value_curran(self):
        # the years to the start of the averaging period
        value_date = self.transformed_value_date
        t0 = (self.start_averaging_date - value_date) / gDaysInYear
        texp = self.texp
        tau = (self.expiry - self.start_averaging_date) / gDaysInYear

        multiple = 1.0

        r = self.r
        q = self.q

        vol = self.v

        s0 = self.stock_price
        b = r - q
        sigma2 = vol ** 2
        k = self.strike_price

        n = self.num_obs

        if t0 < 0:  # we are in the averaging period

            if self.accrued_average is None:
                raise TuringError(error_str)

            # we adjust the strike to account for the accrued coupon
            k = (k * tau + self.accrued_average * t0) / texp
            # the number of options is rescaled also
            multiple = texp / tau
            # there is no pre-averaging time
            t0 = 0.0
            # the number of observations is scaled and floored at 1
            n = int(n * texp / tau + 0.5) + 1

        h = (texp - t0) / (n - 1)
        u = (1.0 - np.exp(b * h * n)) / (1.0 - np.exp(b * h))
        w = (1.0 - np.exp((2 * b + sigma2) * h * n)) / \
            (1.0 - np.exp((2 * b + sigma2) * h))

        fa = (s0 / n) * np.exp(b * t0) * u
        ea2 = (s0 * s0 / n / n) * np.exp((2.0 * b + sigma2) * t0)
        ea2 = ea2 * (w + 2.0 / (1.0 - np.exp((b + sigma2) * h)) * (u - w))
        sigmaA = np.sqrt((np.log(ea2) - 2.0 * np.log(fa)) / texp)

        d1 = (np.log(fa / k) + sigmaA * sigmaA *
              texp / 2.0) / (sigmaA * np.sqrt(texp))
        d2 = d1 - sigmaA * np.sqrt(texp)

        if self.option_type == TuringOptionTypes.ASIAN_CALL:
            v = np.exp(-r * texp) * (fa * N(d1) - k * N(d2))
        elif self.option_type == TuringOptionTypes.ASIAN_PUT:
            v = np.exp(-r * texp) * (k * N(-d2) - fa * N(-d1))

        v = v * multiple
        return v

    def _resolve(self):
        super()._resolve()
        if self.product_type is None:
            setattr(self, 'product_type', 'Asian')
        self.__post_init__()

    def __repr__(self):
        s = super().__repr__()
        s += f'''
Start Averaging Date: {self.start_averaging_date}
Accrued Average: {self.accrued_average}'''
        return s
