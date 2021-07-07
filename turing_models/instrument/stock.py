from dataclasses import dataclass

from turing_models.instrument.core import Instrument, InstrumentBase


@dataclass
class Stock(Instrument,InstrumentBase):
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

    def __post_init__(self):
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
