import datetime
from abc import ABCMeta
from dataclasses import dataclass
from typing import List, Union

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
    underlier_symbol: str = None
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
        self.cv = YieldCurve(value_date=self.value_date, curve_type='spot_rate', is_treasury_yield_curve=True)
        self.cv.resolve()
        self.discount_curve = self.cv.discount_curve()
        # 调用接口补全mds相关数据
        self._get_stock_price()
        self._get_volatility()
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
                if isinstance(self.value_date, str) and self.value_date == 'latest':
                    self.stock_price = original_data.loc[self.underlier_symbol, 'price']
                else:
                    self.stock_price = original_data.loc[self.underlier_symbol].loc[0, 'close']
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
                self.volatility = original_data.loc[self.underlier_symbol, 'volatility']
            else:
                raise TuringError('The interface data is empty')

    def _save_original_data(self):
        """ 存储未经ctx修改的属性值，存储在字典中 """
        _original_data = dict()
        _original_data['value_date'] = self.value_date
        _original_data['stock_price'] = getattr(self, 'stock_price', None)
        _original_data['volatility'] = getattr(self, 'volatility', None)
        _original_data['dividend_yield'] = getattr(self, 'dividend_yield', None)
        _original_data['discount_curve'] = getattr(self, 'discount_curve', None)
        _original_data['dividend_curve'] = getattr(self, 'dividend_curve', None)
        self._original_data = _original_data

    def _ctx_resolve(self):
        """根据ctx中的数据，修改实例属性"""
        # 先把ctx中的数据取出
        ctx_pricing_date = self.ctx_pricing_date
        ctx_spot = self.ctx_spot(symbol=self.underlier_symbol)
        ctx_volatility = self.ctx_volatility(symbol=self.underlier_symbol)
        ctx_interest_rate = self.ctx_interest_rate
        ctx_dividend_yield = self.ctx_dividend_yield(symbol=self.underlier_symbol)
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
            if ctx_volatility is not None:
                self.volatility = ctx_volatility
            else:
                self._get_volatility()
        else:
            # 在ctx_pricing_date为空的情况下，将value_date恢复为原始数据；再判断那些需要调用接口获取数据的属性是否有
            # 对应的ctx_xx值，优先有这个，如果没有则恢复为原始数据
            self.value_date = _original_data.get('value_date')  # datetime.datetime/latest格式
            self.stock_price = ctx_spot or _original_data.get('stock_price')
            self.volatility = ctx_volatility or _original_data.get('volatility')
        # 无风险利率
        if ctx_interest_rate is not None:
            self.discount_curve = TuringDiscountCurveFlat(
                to_turing_date(self.value_date),
                ctx_interest_rate
            )
        else:
            self.discount_curve = _original_data.get('discount_curve')
        # 分红率
        self.dividend_yield = ctx_dividend_yield or _original_data.get('dividend_yield')
        # 计算定价要用到的中间变量
        self._calculate_intermediate_variable()

    def _calculate_intermediate_variable(self):
        """ 计算定价要用到的中间变量 """
        # 估值日期时间格式转换
        self.transformed_value_date = to_turing_date(self.value_date)

        # 根据分红率生成折现曲线
        self.dividend_curve = TuringDiscountCurveFlat(
            self.transformed_value_date,
            self.dividend_yield
        )
        if getattr(self, 'volatility', None) is not None:
            self.bs_model = TuringModelBlackScholes(self.volatility)
            self.v = self.bs_model._volatility

        if getattr(self, 'expiry', None) is not None:
            self.r = self.discount_curve.zeroRate(self.expiry)
            self.q = self.dividend_curve.zeroRate(self.expiry)
            # 计算年化的剩余期限
            self.texp = (self.expiry - self.transformed_value_date) / gDaysInYear

    def isvalid(self):
        """提供给turing sdk做过期判断"""
        if getattr(self, 'transformed_value_date', '') \
           and getattr(self, 'expiry', '') \
           and getattr(self, 'transformed_value_date', '') > getattr(self, 'expiry', ''):
            return False
        return True

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
        if self.asset_id and not self.asset_id.startswith("OPTION_"):  # OPTION_ 为自定义时自动生成
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
                self.number_of_options = (self.notional / self.initial_spot) / self.participation_rate / self.multiplier
            else:
                self.number_of_options = 1.0

    def check_underlier(self):
        if self.underlier_symbol and not self.underlier:
            self.underlier = TuringDB.get_stock_symbol_to_id(_id=self.underlier_symbol).get('asset_id')
        if self.underlier and not self.underlier_symbol:
            self.underlier_symbol = TuringDB.get_stock(_id=self.underlier)['comb_symbol']

    # def __repr__(self):
    #     s = to_string("Object Type", type(self).__name__)
    #     s += to_string("Asset Id", self.asset_id)
    #     s += to_string("Underlier", self.underlier)
    #     s += to_string("Option Type", self.option_type)
    #     s += to_string("Notional", self.notional)
    #     s += to_string("Initial Spot", self.initial_spot)
    #     s += to_string("Number of Options", self.number_of_options)
    #     s += to_string("Start Date", self.start_date)
    #     s += to_string("End Date", self.end_date)
    #     s += to_string("Expiry", self.expiry)
    #     s += to_string("Participation Rate", self.participation_rate)
    #     s += to_string("Strike Price", self.strike_price)
    #     s += to_string("Multiplier", self.multiplier)
    #     s += to_string("Annualized Flag", self.annualized_flag)
    #     s += to_string("Stock Price", self._stock_price)
    #     s += to_string("Volatility", self._volatility)
    #     if self._value_date:
    #         s += to_string("Value Date", self._value_date)
    #     if self._interest_rate:
    #         s += to_string("Interest Rate", self._interest_rate)
    #     if self._dividend_yield or self._dividend_yield == 0:
    #         s += to_string("Dividend Yield", self._dividend_yield)
    #     return s
