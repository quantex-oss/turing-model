import datetime
from abc import ABCMeta
from dataclasses import dataclass
from typing import Union

from fundamental.turing_db.bond_data import BondApi
from turing_models.instruments.common import IR, YieldCurveCode, CurveCode, CurveAdjustment, Currency
from turing_models.instruments.core import InstrumentBase
from turing_models.utilities.calendar import TuringCalendarTypes, TuringBusDayAdjustTypes, \
    TuringDateGenRuleTypes, TuringCalendar
from turing_models.utilities.day_count import DayCountType, TuringDayCount
from turing_models.utilities.error import TuringError
from turing_models.utilities.frequency import TuringFrequency, FrequencyType
from turing_models.utilities.global_types import TuringYTMCalcType, CouponType
from turing_models.utilities.helper_functions import to_turing_date
from turing_models.utilities.schedule import TuringSchedule
from turing_utils.log.request_id_log import logger

dy = 0.0001


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class Bond(IR, InstrumentBase, metaclass=ABCMeta):
    asset_id: str = None
    wind_id: str = None
    bbg_id: str = None
    cusip: str = None
    sedol: str = None
    ric: str = None
    isin: str = None
    ext_asset_id: str = None
    asset_name: str = None
    asset_type: str = None
    trd_curr_code: Union[str, Currency] = None
    symbol: str = None
    comb_symbol: str = None
    exchange: str = None
    issuer_id: str = None
    issuer: str = None
    issue_date: datetime.datetime = None  # 发行日
    due_date: datetime.datetime = None  # 到期日
    par: float = None  # 面值
    coupon_rate: float = None
    interest_rate_type: str = None
    pay_interest_cycle: (str, FrequencyType) = None  # 付息频率
    interest_rules: (str, DayCountType) = None  # 计息类型
    pay_interest_mode: (str, CouponType) = None  # 付息方式
    curve_code: Union[str, YieldCurveCode] = None  # 曲线编码
    curve_name: str = None
    value_date: (datetime.datetime, datetime.date) = datetime.date.today()  # 估值日
    settlement_terms: int = 0  # 结算天数，0即T+0结算

    def __post_init__(self):
        super().__init__()
        self._check_param()                                # 将一些类型做转换
        self._init()                                       # 对一些属性做初始化
        self._calculate_intermediate_variable()            # 计算一些中间变量（主要是一些会受到ctx影响的变量）
        self._save_original_data()                         # 保存会被ctx影响的属性的原始值

    def _check_param(self):
        """将字符串转换为枚举类型"""
        # 对时间格式做转换
        self.issue_date = to_turing_date(self.issue_date)
        self.due_date = to_turing_date(self.due_date)

        # 转换成字符串，便于rich表格显示
        if self.trd_curr_code and isinstance(self.trd_curr_code, Currency):
            self.trd_curr_code = self.trd_curr_code.value

        if self.pay_interest_mode:
            if not isinstance(self.pay_interest_mode, CouponType):
                rules = {
                    "ZERO_COUPON": CouponType.ZERO_COUPON,
                    "DISCOUNT": CouponType.DISCOUNT,
                    "COUPON_CARRYING": CouponType.COUPON_CARRYING,
                    # "OTHERS": None
                }
                self.pay_interest_mode = rules.get(self.pay_interest_mode,
                                                   TuringError('Please check the input of pay_interest_mode'))
                if isinstance(self.pay_interest_mode, TuringError):
                    raise self.pay_interest_mode

        if self.pay_interest_cycle:
            if not isinstance(self.pay_interest_cycle, FrequencyType):
                rules = {
                    "ANNUAL": FrequencyType.ANNUAL,
                    "SEMI_ANNUAL": FrequencyType.SEMI_ANNUAL,
                    # "ONCE_ON_DUE": None,
                    "QUARTERLY": FrequencyType.QUARTERLY,
                    "MONTHLY": FrequencyType.MONTHLY,
                    # "PERIODIC": None,
                    "TRI_ANNUAL": FrequencyType.TRI_ANNUAL,
                    # "THREE_QUARTERLY": None,
                    # "15_DAYS": None,
                    # "BIMONTHLY": None,
                    # "OTHERS": None
                }
                self.pay_interest_cycle = rules.get(self.pay_interest_cycle,
                                                    TuringError('Please check the input of pay_interest_cycle'))
                if isinstance(self.pay_interest_cycle, TuringError):
                    raise self.pay_interest_cycle

        if self.interest_rules:
            if not isinstance(self.interest_rules, DayCountType):
                rules = {
                    "ACT/365": DayCountType.ACT_365L,
                    "ACT/ACT": DayCountType.ACT_ACT_ISDA,
                    "ACT/360": DayCountType.ACT_360,
                    "30/360": DayCountType.THIRTY_E_360,
                    # "ACT/366": None,
                    "ACT/365F": DayCountType.ACT_365F,
                    # "AVG/ACT": None
                }
                self.interest_rules = rules.get(self.interest_rules,
                                                TuringError('Please check the input of interest_rules'))
                if isinstance(self.interest_rules, TuringError):
                    raise self.interest_rules

    def _init(self):
        self.convention = TuringYTMCalcType.UK_DMO         # 惯例
        self.calendar_type = TuringCalendarTypes.CHINA_IB  # 日历类型
        self.calendar = TuringCalendar(self.calendar_type)
        self.day_count = TuringDayCount(DayCountType.ACT_365F)
        self.bus_day_adjust_type = TuringBusDayAdjustTypes.MODIFIED_FOLLOWING
        self._redemption = 1.0                             # 到期支付额
        # self._flow_dates = []                            # 现金流发生日
        # self._flow_amounts = []                          # 现金流发生额
        # self._accrued_days = 0.0                         # 应计利息天数
        self.ca = CurveAdjustment()
        if self.pay_interest_cycle:
            self.frequency = TuringFrequency(self.pay_interest_cycle)
        if self.due_date:
            self.maturity_date = self.calendar.adjust(self.due_date, self.bus_day_adjust_type)
            if self.issue_date:
                if self.pay_interest_cycle:
                    self._calculate_cash_flow_dates()
                else:
                    self._flow_dates = [self.issue_date, self.due_date]
                self.bond_term_year, _, _ = self.day_count.yearFrac(self.issue_date, self.due_date)

    def _save_original_data(self):
        """ 存储未经ctx修改的属性值，存储在字典中 """
        _original_data = dict()
        _original_data['value_date'] = self.value_date
        cv = getattr(self, 'cv', None)
        if cv is not None:
            _original_data['yield_curve'] = cv.curve_data
        else:
            _original_data['yield_curve'] = None
        self._original_data = _original_data

    def _ctx_resolve(self):
        """根据ctx中的数据，修改实例属性"""
        self._adjust_data_based_on_ctx()
        # 计算定价要用到的中间变量
        self._calculate_intermediate_variable()

    def _adjust_data_based_on_ctx(self):
        # 先把ctx中的数据取出
        ctx_pricing_date = self.ctx_pricing_date
        ctx_yield_curve = self.ctx_yield_curve(curve_type='spot_rate')
        # 再把原始数据也拿过来
        _original_data = self._original_data
        # 估值日期
        if ctx_pricing_date is not None:
            self.value_date = ctx_pricing_date  # datetime.datetime/latest格式
            self.cv.set_value_date(self.value_date)  # 对曲线设置估值日期之后，曲线数据会被清空
            if ctx_yield_curve is not None:
                self.cv.set_curve_data(ctx_yield_curve)
            else:
                self.cv.resolve()
        else:
            self.value_date = _original_data.get('value_date')  # datetime.datetime/latest格式
            self.cv.set_value_date(self.value_date)
            if ctx_yield_curve is not None:
                self.cv.set_curve_data(ctx_yield_curve)
            else:
                self.cv.set_curve_data(_original_data.get('yield_curve'))
        # 检测用户是否对self.curve_code所对应的收益率曲线做变换
        self._curve_adjust()

    def _curve_adjust(self):
        if self.ctx_parallel_shift:
            self.ca.set_parallel_shift(self.ctx_parallel_shift)
        if self.ctx_curve_shift:
            self.ca.set_curve_shift(self.ctx_curve_shift)
        if self.ctx_pivot_point:
            self.ca.set_pivot_point(self.ctx_pivot_point)
        if self.ctx_tenor_start:
            self.ca.set_tenor_start(self.ctx_tenor_start)
        if self.ctx_tenor_end:
            self.ca.set_tenor_end(self.ctx_tenor_end)
        if self.ca.isvalid():
            self.cv.adjust(self.ca)

    def _calculate_intermediate_variable(self):
        """ 计算定价要用到的中间变量 """
        # 估值日期时间格式转换
        if getattr(self, 'settlement_date', None) is not None and \
           getattr(self, 'due_date', None) is not None:
            self.time_to_maturity_in_year, _, _ = self.day_count.yearFrac(self.settlement_date, self.due_date)

    def isvalid(self):
        """提供给turing sdk做过期判断"""
        if getattr(self, 'settlement_date', '') \
           and getattr(self, 'due_date', '') \
           and getattr(self, 'settlement_date', '') > getattr(self, 'due_date', ''):
            return False
        return True

    def _calculate_cash_flow_dates(self):
        """ Determine the bond cashflow payment dates."""
        date_gen_rule_type = TuringDateGenRuleTypes.BACKWARD
        self._flow_dates = TuringSchedule(self.issue_date,
                                          self.due_date,
                                          self.pay_interest_cycle,
                                          self.calendar_type,
                                          self.bus_day_adjust_type,
                                          date_gen_rule_type,
                                          False)._generate()
        self._flow_dates[-1] = self.maturity_date

    def dollar_duration(self):
        return self.dv01() / dy

    def time_to_maturity(self):
        """剩余期限"""
        return self.due_date - self.settlement_date

    def _resolve(self):
        if not self.asset_id:
            asset_id = BondApi.fetch_comb_symbol_to_asset_id(self.comb_symbol)
            if asset_id:
                setattr(self, 'asset_id', asset_id)
        if self.asset_id and not self.asset_id.startswith("Bond_"):  # Bond_ 为自定义时自动生成
            bond = BondApi.fetch_one_bond_orm(asset_id=self.asset_id)
            for k, v in bond.items():
                try:
                    if getattr(self, k, None) is None and v:
                        setattr(self, k, v)
                except Exception:
                    logger.warning('bond resolve warning')
        if self.curve_code is not None and self.curve_name is None:
            curve_name = getattr(CurveCode, self.curve_code, '')
            setattr(self, 'curve_name', curve_name)

    def __repr__(self):
        s = f'''Class Name: {type(self).__name__}
Wind Id: {self.wind_id}
Bbg Id: {self.bbg_id}
Cusip: {self.cusip}
Sedol: {self.sedol}
Ric: {self.ric}
Isin: {self.isin}
Ext Asset Id: {self.ext_asset_id}
Asset Name: {self.asset_name}
Asset Type: {self.asset_type}
Trd Curr Code: {self.trd_curr_code}
Symbol: {self.symbol}
Comb Symbol: {self.comb_symbol}
Exchange: {self.exchange}
Issuer: {self.issuer}
Issue Date: {self.issue_date}
Due Date: {self.due_date}
Par: {self.par}
Coupon Rate: {self.coupon_rate}
Interest Rate Type: {self.interest_rate_type}
Pay Interest Cycle: {self.pay_interest_cycle}
Interest Rules: {self.interest_rules}
Pay Interest Mode: {self.pay_interest_mode}
Curve Code: {self.curve_code}'''
        return s
