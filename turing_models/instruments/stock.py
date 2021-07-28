from dataclasses import dataclass

from fundamental.turing_db.base.core import InstrumentBase
from turing_models.instruments.core import Instrument
from turing_models.utilities.helper_functions import to_string


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class Stock(Instrument, InstrumentBase):
    asset_id: str = None
    quantity: float = None  # 股数
    asset_type: str = None
    symbol: str = None
    name_cn: str = None
    name_en: str = None
    exchange_code: str = None
    currency: str = None
    name: str = None
    stock_price: float = None
    volatility: float = None

    def __post_init__(self):
        super().__init__()
        self.set_param()

    def set_param(self):
        self._stock_price = self.stock_price

    @property
    def stock_price_(self) -> float:
        return getattr(self.ctx, f"spot_{self.asset_id}") or self._stock_price

    def price(self):
        return self.stock_price_

    def delta(self):
        return 1

    def stock_resolve(self):
        if self.asset_id:
            temp_dict = OptionApi.fetch_Option(asset_id=self.asset_id)
            for k, v in temp_dict.items():
                if not getattr(self, k, None) and v:
                    setattr(self, k, v)
        if not self.number_of_options:
            if self.notional \
                    and self.initial_spot \
                    and self.participation_rate \
                    and self.multiplier:
                self.number_of_options = (self.notional / self.initial_spot) / self.participation_rate / self.multiplier
            else:
                self.number_of_options = 1.0
        if self.underlier:
            if not self.stock_price_:
                setattr(self, "stock_price", OptionApi.stock_price(underlier=self.underlier))

    def __repr__(self):
        s = to_string("Object Type", type(self).__name__)
        s += to_string("Asset Id", self.asset_id)
        s += to_string("Symbol", self.symbol)
        s += to_string("Name", self.name_cn)
        s += to_string("Stock Price", self.stock_price_)
        return s
