from dataclasses import dataclass
from typing import Union

from turing_models.instruments.core import InstrumentBase
from turing_models.utilities.helper_functions import to_string
from turing_models.instruments.common import Currency, Eq


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class Stock(Eq, InstrumentBase):
    asset_id: str = None
    asset_type: str = None
    symbol: str = None
    name_cn: str = None
    name_en: str = None
    exchange_code: str = None
    currency: Union[str, Currency] = None
    name: str = None
    stock_price: float = None
    volatility: float = None

    def __post_init__(self):
        super().__init__()

    @property
    def stock_price_(self) -> float:
        return getattr(self.ctx, f"spot_{self.asset_id}") or self.stock_price

    def price(self):
        return self.stock_price_

    def eq_delta(self):
        return 1

    def eq_gamma(self):
        return 0

    def eq_vega(self):
        return 0

    def eq_theta(self):
        return 0

    def eq_rho(self):
        return 0

    def eq_rho_q(self):
        return 0

    def __repr__(self):
        s = to_string("Object Type", type(self).__name__)
        s += to_string("Asset Id", self.asset_id)
        s += to_string("Symbol", self.symbol)
        s += to_string("Name", self.name_cn)
        s += to_string("Stock Price", self.stock_price_)
        return s
