from dataclasses import dataclass

from turing_models.utilities.global_variables import gNumObsInYear
from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.models.model_crr_tree import crrTreeValAvg
from turing_models.instruments.equity_option import EqOption


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class AmericanOption(EqOption):

    def __post_init__(self):
        super().__post_init__()
        self.num_ann_obs = gNumObsInYear

    @property
    def option_type_(self) -> TuringOptionTypes:
        return TuringOptionTypes.AMERICAN_CALL if self.option_type == 'CALL' \
            else TuringOptionTypes.AMERICAN_PUT

    def price(self) -> float:
        s0 = self.stock_price_
        k = self.strike_price
        r = self.r
        q = self.q
        vol = self.v
        option_type = self.option_type_

        v = crrTreeValAvg(s0, r, q, vol, self.num_ann_obs,
                          self.texp, option_type.value, k)['value']

        return v * self._multiplier * self._number_of_options
