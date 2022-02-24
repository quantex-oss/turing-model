from dataclasses import dataclass
from typing import Union
import datetime

from fundamental.turing_db.data import TuringDB
from fundamental.turing_db.stock_data import StockApi
from turing_models.instruments.common import Currency, Eq
from turing_models.instruments.core import InstrumentBase
from turing_models.utilities.error import TuringError


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class Stock(Eq, InstrumentBase):
    asset_id: str = None
    ext_asset_id: str = None
    comb_symbol: str = None
    symbol: str = None
    wind_id: str = None
    bbg_id: str = None
    cusip: str = None
    sedol: str = None
    ric: str = None
    isin: str = None
    asset_name: str = None
    asset_type: str = None
    trd_curr_code: Union[str, Currency] = None
    exchange: str = None
    value_date: Union[datetime.datetime, str] = 'latest'  # 估值日期

    def __post_init__(self):
        super().__init__()
        # 调用接口补全mds相关数据
        self._get_stock_price()
        # 存储未经ctx修改的属性值
        self._save_original_data()

    def _save_original_data(self):
        """ 存储未经ctx修改的属性值，存储在字典中 """
        _original_data = dict()
        _original_data['value_date'] = self.value_date
        _original_data['stock_price'] = self.stock_price
        self._original_data = _original_data

    def _ctx_resolve(self):
        """根据ctx中的数据，修改实例属性"""
        # 先把ctx中的数据取出
        ctx_pricing_date = self.ctx_pricing_date
        ctx_spot = self.ctx_spot(symbol=self.comb_symbol)
        # 再把原始数据也拿过来
        _original_data = self._original_data
        # 估值日期
        if ctx_pricing_date is not None:
            self.value_date = ctx_pricing_date  # datetime.datetime/latest格式
            # 在ctx_pricing_date不为空的情况下，先判断那些需要调用接口获取数据的属性是否有对应的ctx_xx值，优先有这个；
            # 如果没有则调用对应接口补全数据。因为调用接口的时候需要传入value_date，所以一旦估值日期发生改变，就需要重
            # 新调用接口补全数据
            if ctx_spot is not None:
                self.stock_price = ctx_spot
            else:
                self._get_stock_price()
        else:
            # 在ctx_pricing_date为空的情况下，将value_date恢复为原始数据；再判断那些需要调用接口获取数据的属性是否有
            # 对应的ctx_xx值，优先有这个，如果没有则恢复为原始数据
            self.value_date = _original_data.get('value_date')  # datetime.datetime/latest格式
            self.stock_price = ctx_spot or _original_data.get('stock_price')

    def _get_stock_price(self):
        """ 调用接口补全股票价格 """
        if self.comb_symbol is not None \
           and self.value_date is not None:
            original_data = TuringDB.get_stock_price(
                symbol=self.comb_symbol,
                start=self.value_date,
                end=self.value_date
            )
            if not original_data.empty:
                if isinstance(self.value_date, str) and self.value_date == 'latest':
                    self.stock_price = original_data.loc[self.comb_symbol, 'price']
                else:
                    self.stock_price = original_data.loc[self.comb_symbol].loc[0, 'close']
            else:
                raise TuringError('The interface data is empty')

    def isvalid(self):
        return True

    def price(self):
        return self.stock_price

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
            self.asset_id = TuringDB.get_asset(comb_symbols=self.comb_symbol)[0].get('asset_id')

    def check_symbol(self):
        if self.symbol and not self.asset_id:
            self.asset_id = TuringDB.get_asset(symbols=self.symbol)[0].get('asset_id')

    def _resolve(self):
        self.check_comb_symbol()
        self.check_symbol()
        if self.asset_id:
            _stock = StockApi.fetch_orm(self=self, gurl=None)
            for k, v in _stock.items():
                if not getattr(self, k, None) and v:
                    setattr(self, k, v)

    def __repr__(self):
        s = f'''Class Name: {type(self).__name__}
Asset Id: {self.asset_id}
Ext Asset Id: {self.ext_asset_id}
Comb Symbol: {self.comb_symbol}
Symbol: {self.symbol}
Wind Id: {self.wind_id}
Bbg Id: {self.bbg_id}
Cusip: {self.cusip}
Sedol: {self.sedol}
Ric: {self.ric}
Isin: {self.isin}
Asset Name: {self.asset_name}
Asset Type: {self.asset_type}
Trd Curr Code: {self.trd_curr_code}
Exchange: {self.exchange}'''
        return s
