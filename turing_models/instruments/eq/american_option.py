from dataclasses import dataclass

from turing_models.utilities.global_variables import gNumObsInYear
from turing_models.models.model_crr_tree import crrTreeValAvg
from turing_models.instruments.eq.equity_option import EqOption
from turing_models.utilities.global_types import TuringOptionType, TuringOptionTypes
from turing_models.utilities.error import TuringError


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class AmericanOption(EqOption):

    def __post_init__(self):
        super().__post_init__()
        self.num_ann_obs = gNumObsInYear

    @property
    def option_type_(self) -> TuringOptionTypes:
        if self.option_type == "CALL" or self.option_type == TuringOptionType.CALL:
            return TuringOptionTypes.AMERICAN_CALL
        elif self.option_type == "PUT" or self.option_type == TuringOptionType.PUT:
            return TuringOptionTypes.AMERICAN_PUT
        else:
            raise TuringError('Please check the input of option_type')

    def price(self) -> float:
        s0 = self.stock_price_
        k = self.strike_price
        r = self.r
        q = self.q
        vol = self.v
        option_type = self.option_type_

        v = crrTreeValAvg(s0, r, q, vol, self.num_ann_obs,
                          self.texp, option_type.value, k)['value']

        return v * self.multiplier * self.number_of_options