from dataclasses import dataclass
from enum import Enum
from typing import Union

from fundamental.turing_db.data import Turing
from fundamental.turing_db.stock_data import StockApi
from turing_models.instruments.common import Currency, Eq
from turing_models.instruments.core import InstrumentBase
from turing_models.utilities.helper_functions import to_string


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class Stock(Eq, InstrumentBase):
    asset_id: str = None
    quantity: float = None  # 股数
    asset_type: str = None
    comb_symbol: str = None
    symbol: str = None
    name_cn: str = None
    name_en: str = None
    exchange_code: str = None
    currency: Union[str, Currency] = None
    name: str = None
    stock_price: float = None

    def __post_init__(self):
        super().__init__()
        self.check_comb_symbol()

    @property
    def stock_price_(self) -> float:
        return self.ctx_spot or self.stock_price

    def price(self):
        return self.stock_price_

    def delta(self):
        return 1

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

    def check_comb_symbol(self):
        if self.comb_symbol and not self.asset_id:
            self.asset_id = Turing.get_stock_symbol_to_id(_id=self.comb_symbol).get('asset_id')

    def check_symbol(self):
        if self.symbol and not self.asset_id:
            if isinstance(self.symbol, Enum):
                self.asset_id = Turing.get_stock_symbol_to_id(_id=self.symbol.value).get('asset_id')
            else:
                self.asset_id = Turing.get_stock_symbol_to_id(_id=self.symbol).get('asset_id')

    def _resolve(self):
        if self.asset_id:
            _stock = StockApi.fetch_orm(self=self, gurl=None)
            for k, v in _stock.items():
                if not getattr(self, k, None) and v:
                    setattr(self, k, v)

        if self.asset_id:
            if not self.stock_price:
                _price = StockApi.get_stock_price(gurl=None,
                                                  underlier=self.asset_id)
                if _price:
                    setattr(self, "stock_price", _price)

    def __repr__(self):
        s = to_string("Object Type", type(self).__name__)
        s += to_string("Asset Id", self.asset_id)
        s += to_string("Symbol", self.symbol)
        s += to_string("Name", self.name_cn)
        s += to_string("Stock Price", self.stock_price_, "")
        return s