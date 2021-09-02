from dataclasses import dataclass

from fundamental.turing_db.utils import to_snake
from turing_models.instruments.common import FX
from turing_models.instruments.core import InstrumentBase
from turing_models.utilities.helper_functions import to_string


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class ForeignExchange(FX, InstrumentBase):
    asset_id: str = None
    asset_name: str = None
    asset_type: str = None
    exchange_rate: float = None

    def __post_init__(self):
        super().__init__()

    @property
    def exchange_rate_(self) -> float:
        return getattr(self.ctx, f"exchange_rate_{self.asset_id}") or self.exchange_rate

    def price(self):
        return self.exchange_rate_

    def fx_delta(self):
        return 1

    def fx_gamma(self):
        return 0

    def fx_vega(self):
        return 0

    def fx_theta(self):
        return 0

    def fx_rho(self):
        return 0

    def fx_rho_q(self):
        return 0


    def __repr__(self):
        s = to_string("Object Type", type(self).__name__)
        s += to_string("Asset Id", self.asset_id)
        s += to_string("Asset Name", self.asset_name)
        s += to_string("Exchange Rate", self.exchange_rate_)
        return s
