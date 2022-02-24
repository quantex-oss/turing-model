from dataclasses import dataclass
from typing import Union
import datetime

from fundamental.turing_db.data import TuringDB
from fundamental.turing_db.fx_data import FxApi
from turing_models.instruments.common import FX, CurrencyPair
from turing_models.instruments.core import InstrumentBase
from turing_models.utilities.error import TuringError


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class ForeignExchange(FX, InstrumentBase):
    asset_id: str = None
    ext_asset_id: str = None
    comb_symbol: (str, CurrencyPair) = None
    symbol: (str, CurrencyPair) = None
    asset_name: str = None
    asset_type: str = None
    value_date: Union[datetime.datetime, str] = 'latest'  # 估值日期

    def __post_init__(self):
        super().__init__()
        # 调用接口补全mds相关数据
        self._get_exchange_rate()
        # 存储未经ctx修改的属性值
        self._save_original_data()

    def _save_original_data(self):
        """ 存储未经ctx修改的属性值，存储在字典中 """
        _original_data = dict()
        _original_data['value_date'] = self.value_date
        _original_data['exchange_rate'] = self.exchange_rate
        self._original_data = _original_data

    def _ctx_resolve(self):
        """根据ctx中的数据，修改实例属性"""
        # 先把ctx中的数据取出
        ctx_pricing_date = self.ctx_pricing_date
        ctx_exchange_rate = self.ctx_exchange_rate(currency_pair=self.comb_symbol)
        # 再把原始数据也拿过来
        _original_data = self._original_data
        # 估值日期
        if ctx_pricing_date is not None:
            self.value_date = ctx_pricing_date  # datetime.datetime/latest格式
            # 在ctx_pricing_date不为空的情况下，先判断那些需要调用接口获取数据的属性是否有对应的ctx_xx值，优先有这个；
            # 如果没有则调用对应接口补全数据。因为调用接口的时候需要传入value_date，所以一旦估值日期发生改变，就需要重
            # 新调用接口补全数据
            if ctx_exchange_rate is not None:
                self.exchange_rate = ctx_exchange_rate
            else:
                self._get_exchange_rate()
        else:
            # 在ctx_pricing_date为空的情况下，将value_date恢复为原始数据；再判断那些需要调用接口获取数据的属性是否有
            # 对应的ctx_xx值，优先有这个，如果没有则恢复为原始数据
            self.value_date = _original_data.get('value_date')  # datetime.datetime/latest格式
            self.exchange_rate = ctx_exchange_rate or _original_data.get('exchange_rate')

    def _get_exchange_rate(self):
        """从接口获取汇率"""
        if self.comb_symbol is not None \
           and self.value_date is not None:
            original_data = TuringDB.exchange_rate(symbol=self.comb_symbol, date=self.value_date)
            if original_data is not None:
                self.exchange_rate = original_data[self.comb_symbol]
            else:
                raise TuringError(f"Cannot find exchange rate for {self.comb_symbol}")

    def isvalid(self):
        return True

    def price(self):
        return self.exchange_rate

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
            temp_dict = FxApi.fetch_fx_orm(self=self, gurl=None)
            for k, v in temp_dict.items():
                if not getattr(self, k, None) and v:
                    setattr(self, k, v)

    def __repr__(self):
        s = f'''Class Name: {type(self).__name__}
Asset Id: {self.asset_id}
Ext Asset Id: {self.ext_asset_id}
Comb Symbol: {self.comb_symbol}
Symbol: {self.symbol}
Asset Name: {self.asset_name}
Asset Type: {self.asset_type}'''
        return s
