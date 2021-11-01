from dataclasses import dataclass
from enum import Enum

from fundamental.turing_db.data import Turing
from fundamental.turing_db.fx_data import FxApi
from turing_models.instruments.common import FX, CurrencyPair
from turing_models.instruments.core import InstrumentBase
from turing_models.utilities.helper_functions import to_string


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class ForeignExchange(FX, InstrumentBase):
    asset_id: str = None
    symbol: (str, CurrencyPair) = None
    asset_name: str = None
    asset_type: str = None
    exchange_rate: float = None

    def __post_init__(self):
        super().__init__()
        self.check_symbol()

    @property
    def exchange_rate_(self) -> float:
        return self.ctx_spot or self.exchange_rate

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

    def check_symbol(self):
        if self.symbol and not self.asset_id:
            if isinstance(self.symbol, Enum):
                self.asset_id = Turing.get_fx_symbol_to_id(_id=self.symbol.value).get('asset_id')
            else:
                self.asset_id = Turing.get_fx_symbol_to_id(_id=self.symbol).get('asset_id')

    def _resolve(self):
        self.check_symbol()
        if self.asset_id:
            temp_dict = FxApi.fetch_fx_orm(self=self, gurl=None)
            for k, v in temp_dict.items():
                if not getattr(self, k, None) and v:
                    setattr(self, k, v)

            if not self.exchange_rate:
                ex_rate = FxApi.get_exchange_rate(gurl=None,
                                                  underlier=self.asset_id)
                if ex_rate:
                    setattr(self, "exchange_rate", ex_rate)

    def __repr__(self):
        s = to_string("Object Type", type(self).__name__)
        s += to_string("Asset Id", self.asset_id)
        s += to_string("Asset Name", self.asset_name)
        s += to_string("Exchange Rate", self.exchange_rate_)
        return s
