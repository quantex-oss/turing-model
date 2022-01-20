from dataclasses import dataclass

from turing_models.utilities.global_variables import gNumObsInYear
from turing_models.models.model_crr_tree import crrTreeValAvg
from turing_models.instruments.eq.equity_option import EqOption
from turing_models.utilities.global_types import OptionType, TuringOptionTypes
from turing_models.utilities.error import TuringError


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class AmericanOption(EqOption):

    def __post_init__(self):
        super().__post_init__()
        self.num_ann_obs = gNumObsInYear
        self.check_param()

    def check_param(self):
        if self.option_type is not None:
            rules = {
                "CALL": TuringOptionTypes.AMERICAN_CALL,
                OptionType.CALL: TuringOptionTypes.AMERICAN_CALL,
                "PUT": TuringOptionTypes.AMERICAN_PUT,
                OptionType.PUT: TuringOptionTypes.AMERICAN_PUT
            }
            self.option_type = rules.get(self.option_type,
                                         TuringError('Please check the input of option_type'))
            if isinstance(self.option_type, TuringError):
                raise self.option_type

    def price(self) -> float:
        s0 = self.stock_price
        k = self.strike_price
        r = self.r
        q = self.q
        vol = self.v
        option_type = self.option_type

        v = crrTreeValAvg(s0, r, q, vol, self.num_ann_obs,
                          self.texp, option_type.value, k)['value']

        return v * self.multiplier * self.number_of_options
