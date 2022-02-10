import copy
import datetime
from abc import ABCMeta
from dataclasses import dataclass
from typing import List, Union

import numpy as np

from fundamental.turing_db.option_data import OptionApi
from fundamental.turing_db.data import TuringDB
from turing_utils.log.request_id_log import logger
from turing_models.instruments.common import Currency, Eq, YieldCurve
from turing_models.instruments.core import InstrumentBase
from turing_models.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import OptionType
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.helper_functions import to_turing_date, calculate_greek, bump


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class EqOption(Eq, InstrumentBase, metaclass=ABCMeta):
    """
        self.ctx_ 开头属性为 What if 使用
    """
    asset_id: str = None
    underlier: Union[str, List[str]] = None
    underlier_symbol: Union[str, List[str]] = None
    product_type: str = None
    option_type: Union[str, OptionType] = None
    notional: float = None
    initial_spot: float = None
    number_of_options: float = None
    start_date: Union[datetime.datetime, str] = None
    end_date: Union[datetime.datetime, str] = None
    expiry: Union[datetime.datetime, str] = None
    participation_rate: float = None
    strike_price: float = None
    multiplier: float = None
    currency: Union[str, Currency] = "CNY"
    premium: float = None
    premium_date: Union[datetime.datetime, str] = None
    annualized_flag: bool = True
    value_date: Union[datetime.datetime, str] = 'latest'  # 估值日期

    def __post_init__(self):
        super().__init__()
        # 对时间格式做转换
        if self.start_date is not None:
            self.start_date = to_turing_date(self.start_date)
        if self.end_date is not None:
            self.end_date = to_turing_date(self.end_date)
        if self.expiry is not None:
            self.expiry = to_turing_date(self.expiry)
        if self.premium_date is not None:
            self.premium_date = to_turing_date(self.premium_date)
        # 生成国债收益率曲线
        self.cv = YieldCurve(value_date=self.value_date,
                             curve_type='spot_rate', is_treasury_yield_curve=True)
        self.cv.resolve()
        self.discount_curve = self.cv.discount_curve()
        if self.underlier is not None and isinstance(self.underlier, list):
            self.num_assets = len(self.underlier)  # 确认底层资产数据
        elif self.underlier_symbol is not None and isinstance(self.underlier_symbol, list):
            self.num_assets = len(self.underlier_symbol)  # 确认底层资产数据
        # 调用接口补全mds相关数据
        self._get_stock_price()
        self._get_volatility()
        if getattr(self, 'num_assets', None) is not None:
            self.dividend_yield = np.zeros(self.num_assets)
        else:
            self.dividend_yield = 0  # 目前没有接口提供分红率数据，故把默认值设置为0
        # 存储未经ctx修改的属性值
        self._save_original_data()
        # 计算定价要用到的中间变量
        self._calculate_intermediate_variable()

    def _get_stock_price(self):
        """ 调用接口补全股票价格 """
        if self.underlier_symbol is not None \
           and self.value_date is not None:
            original_data = TuringDB.get_stock_price(
                symbol=self.underlier_symbol,
                start=self.value_date,
                end=self.value_date
            )
            if not original_data.empty:
                if isinstance(self.underlier_symbol, str):
                    if isinstance(self.value_date, str) and self.value_date == 'latest':
                        self.stock_price = original_data.loc[self.underlier_symbol, 'price']
                    else:
                        self.stock_price = original_data.loc[self.underlier_symbol].loc[0, 'close']
                elif isinstance(self.underlier_symbol, list):
                    # 保准股票价格列表中的元素顺序与underlier_symbol中的一一对应
                    if isinstance(self.value_date, str) and self.value_date == 'latest':
                        self.stock_price = [original_data.loc[s, 'price'] for s in self.underlier_symbol]
                    else:
                        self.stock_price = [original_data.loc[s].loc[0, 'close'] for s in self.underlier_symbol]
            else:
                raise TuringError('The interface data is empty')

    def _get_volatility(self):
        """ 调用接口补全股票历史波动率 """
        if self.underlier_symbol is not None \
           and self.value_date is not None:
            original_data = TuringDB.get_volatility(
                symbols=self.underlier_symbol,
                end=self.value_date
            )
            if not original_data.empty:
                if isinstance(self.underlier_symbol, str):
                    self.volatility = original_data.loc[self.underlier_symbol, 'volatility']
                elif isinstance(self.underlier_symbol, list):
                    # 保准波动率列表中的元素顺序与underlier_symbol中的一一对应
                    self.volatility = [original_data.loc[s, 'volatility'] for s in self.underlier_symbol]
                else:
                    raise TuringError('Please check the input of underlier_symbol')
            else:
                raise TuringError('The interface data is empty')

    def _save_original_data(self):
        """ 存储未经ctx修改的属性值，存储在字典中 """
        _original_data = dict()
        _original_data['value_date'] = self.value_date
        _original_data['discount_curve'] = getattr(self, 'discount_curve', None)
        _original_data['stock_price'] = copy.copy(getattr(self, 'stock_price', None))
        _original_data['volatility'] = copy.copy(getattr(self, 'volatility', None))
        _original_data['dividend_yield'] = copy.copy(getattr(self, 'dividend_yield', None))
        _original_data['dividend_curve'] = copy.copy(getattr(self, 'dividend_curve', None))
        self._original_data = _original_data

    def _ctx_resolve(self):
        """根据ctx中的数据，修改实例属性"""
        # 先把ctx中的数据取出
        ctx_pricing_date = self.ctx_pricing_date
        ctx_interest_rate = self.ctx_interest_rate
        if isinstance(self.underlier_symbol, str):
            ctx_spot = self.ctx_spot(symbol=self.underlier_symbol)
            ctx_volatility = self.ctx_volatility(symbol=self.underlier_symbol)
            ctx_dividend_yield = self.ctx_dividend_yield(
                symbol=self.underlier_symbol)
        else:
            ctx_spot = [self.ctx_spot(symbol=s) for s in self.underlier_symbol]
            ctx_volatility = [self.ctx_volatility(symbol=s) for s in self.underlier_symbol]
            ctx_dividend_yield = [self.ctx_dividend_yield(symbol=s) for s in self.underlier_symbol]
        # 再把原始数据也拿过来
        _original_data = self._original_data
        # 估值日期
        if ctx_pricing_date is not None:
            self.value_date = ctx_pricing_date  # datetime.datetime/latest格式
            # 在ctx_pricing_date不为空的情况下，先判断那些需要调用接口获取数据的属性是否有对应的ctx_xx值，优先有这个；
            # 如果没有则调用对应接口补全数据。因为调用接口的时候需要传入value_date，所以一旦估值日期发生改变，就需要重
            # 新调用接口补全数据
            if isinstance(self.underlier_symbol, str):
                if ctx_spot is not None:
                    self.stock_price = ctx_spot
                else:
                    self._get_stock_price()
                if ctx_volatility is not None:
                    self.volatility = ctx_volatility
                else:
                    self._get_volatility()
            else:
                if all(ctx_spot):
                    # case1：通过what-if改变了所有underlier_symbol的股票价格
                    self.stock_price = ctx_spot
                elif not any(ctx_spot):
                    # case2: 未通过what-if改变underlier_symbol的股票价格
                    self._get_stock_price()
                else:
                    # case3: 通过what-if改变了部分underlier_symbol的股票价格
                    self._get_stock_price()  # 先调用接口按照最新的估值日期把数据取到
                    stock_price = self.stock_price.copy()
                    self.stock_price = [ctx_spot[i] if ctx_spot[i] is not None else stock_price[i] for i in
                                        range(len(self.underlier_symbol))]
        else:
            # 在ctx_pricing_date为空的情况下，将value_date恢复为原始数据；再判断那些需要调用接口获取数据的属性是否有
            # 对应的ctx_xx值，优先有这个，如果没有则恢复为原始数据
            self.value_date = _original_data.get('value_date')  # datetime.datetime/latest格式
            if isinstance(self.underlier_symbol, str):
                self.stock_price = ctx_spot or _original_data.get('stock_price')
                self.volatility = ctx_volatility or _original_data.get('volatility')
            else:
                stock_price = _original_data.get('stock_price')
                self.stock_price = [ctx_spot[i] if ctx_spot[i] is not None else stock_price[i] for i in
                                    range(len(self.underlier_symbol))]
                volatility = _original_data.get('volatility')
                self.volatility = [ctx_volatility[i] if ctx_volatility[i] is not None else volatility[i] for i in
                                   range(len(self.underlier_symbol))]
        # 无风险利率
        if ctx_interest_rate is not None:
            self.discount_curve = TuringDiscountCurveFlat(
                to_turing_date(self.value_date),
                ctx_interest_rate
            )
        else:
            self.discount_curve = _original_data.get('discount_curve')
        # 分红率
        if isinstance(self.underlier_symbol, str):
            self.dividend_yield = ctx_dividend_yield or _original_data.get(
                'dividend_yield')
        else:
            dividend_yield = _original_data.get('dividend_yield')
            self.dividend_yield = [ctx_dividend_yield[i] if ctx_dividend_yield[i] is not None else dividend_yield[i] for
                                   i in range(len(self.underlier_symbol))]
        # 计算定价要用到的中间变量
        self._calculate_intermediate_variable()

    def _calculate_intermediate_variable(self):
        """ 计算定价要用到的中间变量 """
        # 估值日期时间格式转换
        self.transformed_value_date = to_turing_date(self.value_date)
        if getattr(self, 'underlier_symbol', None) is not None:
            if isinstance(self.underlier_symbol, str):
                # 根据分红率生成折现曲线
                self.dividend_curve = TuringDiscountCurveFlat(
                    self.transformed_value_date,
                    self.dividend_yield
                )
                if getattr(self, 'volatility', None) is not None:
                    self.bs_model = TuringModelBlackScholes(self.volatility)
                    self.v = self.bs_model._volatility
            else:
                self.dividend_curve = [TuringDiscountCurveFlat(self.transformed_value_date, dy) for dy in
                                       self.dividend_yield]
                if getattr(self, 'volatility', None) is not None:
                    self.v = [TuringModelBlackScholes(vol)._volatility for vol in self.volatility]

    def isvalid(self):
        """提供给turing sdk做过期判断"""
        if getattr(self, 'transformed_value_date', '') \
           and getattr(self, 'expiry', '') \
           and getattr(self, 'transformed_value_date', '') > getattr(self, 'expiry', ''):
            return False
        return True

    @property
    def texp(self):
        if getattr(self, 'expiry', None) is not None:
            # 计算年化的剩余期限
            return (self.expiry - self.transformed_value_date) / gDaysInYear

    @property
    def r(self):
        if getattr(self, 'expiry', None) is not None:
            return self.discount_curve.zeroRate(self.expiry)

    @property
    def q(self):
        if getattr(self, 'expiry', None) is not None:
            return self.dividend_curve.zeroRate(self.expiry)

    def spot(self):
        """ 提供给定价服务调用 """
        return self.stock_price

    def vol(self):
        """ 提供给定价服务调用 """
        return self.v

    def rate(self):
        """ 提供给定价服务调用 """
        return self.r

    def dividend(self):
        """ 提供给定价服务调用 """
        return self.q

    def eq_delta(self) -> float:
        return calculate_greek(self, self.price, "stock_price")

    def eq_gamma(self) -> float:
        return calculate_greek(self, self.price, "stock_price", order=2)

    def eq_vega(self) -> float:
        return calculate_greek(self, self.price, "v")

    def eq_theta(self) -> float:
        day_diff = 1
        bump_local = day_diff / gDaysInYear
        return calculate_greek(self, self.price, "transformed_value_date", bump=bump_local,
                               cus_inc=(self.transformed_value_date.addDays, day_diff))

    def eq_rho(self) -> float:
        return calculate_greek(self, self.price, "discount_curve",
                               cus_inc=(self.discount_curve.bump, bump))

    def eq_rho_q(self) -> float:
        return calculate_greek(self, self.price, "dividend_curve",
                               cus_inc=(self.dividend_curve.bump, bump))

    def _resolve(self):
        # OPTION_ 为自定义时自动生成
        if self.asset_id and not self.asset_id.startswith("OPTION_"):
            option = OptionApi.fetch_Option(asset_id=self.asset_id)
            for k, v in option.items():
                try:
                    if getattr(self, k, None) is None and v:
                        setattr(self, k, v)
                except Exception:
                    logger.warning('option resolve warning')
        self.check_underlier()  # 补全underlier和underlier_symbol
        if self.multiplier is None:
            self.multiplier = 1.0
        if self.number_of_options is None:
            if self.notional is not None \
               and self.initial_spot is not None \
               and self.participation_rate is not None \
               and self.multiplier is not None:
                self.number_of_options = (
                    self.notional / self.initial_spot) / self.participation_rate / self.multiplier
            else:
                self.number_of_options = 1.0

    def check_underlier(self):
        if self.underlier_symbol and not self.underlier:
            self.underlier = TuringDB.get_stock_symbol_to_id(_id=self.underlier_symbol).get('asset_id')
        if self.underlier and not self.underlier_symbol:
            self.underlier_symbol = TuringDB.get_stock(_id=self.underlier)['comb_symbol']

    def __repr__(self):
        s = f'''Class Name: {type(self).__name__}
Asset Id: {self.asset_id}
Underlier: {self.underlier}
Underlier Symbol: {self.underlier_symbol}
Product Type: {self.product_type}
Option Type: {self.option_type}
Notional: {self.notional}
Initial Spot: {self.initial_spot}
Number of Options: {self.number_of_options}
Start Date: {self.start_date}
End Date: {self.end_date}
Expiry: {self.expiry}
Participation Rate: {self.participation_rate}
Strike Price: {self.strike_price}
Multiplier: {self.multiplier}
Currency: {self.currency}
Premium: {self.premium}
Premium Date: {self.premium_date}'''
        return s
