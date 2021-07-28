from dataclasses import dataclass

from turing_models.utilities.global_types import TuringOptionTypes, TuringOptionType
from turing_models.models.model_black_scholes_analytical import bsValue, bsDelta, \
     bsVega, bsGamma, bsRho, bsPsi, bsTheta
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
        return bsValue(*self.params()) * self._multiplier * self._number_of_options

    def eq_delta(self) -> float:
        return bsDelta(*self.params()) * self._multiplier * self._number_of_options

    def eq_gamma(self) -> float:
        return bsGamma(*self.params()) * self._multiplier * self._number_of_options

    def eq_vega(self) -> float:
        return bsVega(*self.params()) * self._multiplier * self._number_of_options

    def eq_theta(self) -> float:
        return bsTheta(*self.params()) * self._multiplier * self._number_of_options

    def eq_rho(self) -> float:
        return bsRho(*self.params()) * self._multiplier * self._number_of_options

    def eq_rho_q(self) -> float:
        return bsPsi(*self.params()) * self._multiplier * self._number_of_options
