from dataclasses import dataclass

from fundamental.turing_db.fx_data import FxApi
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

    def fx_vanna(self):
        return 0

    def fx_volga(self):
        return 0

    def _resolve(self):
        if self.asset_id:
            temp_dict = FxApi.fetch_fx_orm(self=self, gurl="https://yapi.iquantex.com/mock/566")
            for k, v in temp_dict.items():
                if not getattr(self, k, None) and v:
                    setattr(self, k, v)

        if self.asset_id:
            if not self.exchange_rate:
                ex_rate = FxApi.get_exchange_rate(gurl="https://yapi.iquantex.com/mock/569",
                                                  underlier=self.asset_id)
                if ex_rate:
                    setattr(self, "exchange_rate", ex_rate)

    def __repr__(self):
        s = to_string("Object Type", type(self).__name__)
        s += to_string("Asset Id", self.asset_id)
        s += to_string("Asset Name", self.asset_name)
        s += to_string("Exchange Rate", self.exchange_rate_)
        return s
