import datetime
from abc import ABCMeta
from dataclasses import dataclass
from typing import Union

from turing_utils.log.request_id_log import logger
from fundamental.turing_db.bond_data import BondApi
from turing_models.instruments.common import IR, YieldCurveCode, CurveCode, Curve, CurveAdjustment, Currency
from turing_models.instruments.core import InstrumentBase
from turing_models.utilities.calendar import TuringCalendarTypes, TuringBusDayAdjustTypes, \
     TuringDateGenRuleTypes
from turing_models.utilities.day_count import DayCountType, TuringDayCount
from turing_models.utilities.error import TuringError
from turing_models.utilities.frequency import TuringFrequency, FrequencyType
from turing_models.utilities.global_types import TuringYTMCalcType, CouponType
from turing_models.utilities.helper_functions import to_string, datetime_to_turingdate
from turing_models.utilities.schedule import TuringSchedule

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
    issue_date: datetime.datetime = None                                    # 发行日
    due_date: datetime.datetime = None                                      # 到期日
    par: float = None                                                       # 面值
    coupon_rate: float = None
    interest_rate_type: str = None
    pay_interest_cycle: (str, FrequencyType) = None                         # 付息频率
    interest_rules: (str, DayCountType) = None                              # 计息类型
    pay_interest_mode: (str, CouponType) = None                             # 付息方式
    curve_code: Union[str, YieldCurveCode] = None                           # 曲线编码
    curve_name: str = None
    value_date: (datetime.datetime, datetime.date) = datetime.date.today()  # 估值日
    settlement_terms: int = 0                                               # 结算天数，0即T+0结算

    def __post_init__(self):
        super().__init__()
        self.convention = TuringYTMCalcType.UK_DMO                 # 惯例
        self.calendar_type = TuringCalendarTypes.CHINA_IB          # 日历类型
        self._redemption = 1.0                                     # 到期支付额
        self._flow_dates = []                                      # 现金流发生日
        self._flow_amounts = []                                    # 现金流发生额
        self._accrued_interest = None
        self._accrued_days = 0.0                                   # 应计利息天数
        self.value_date = datetime_to_turingdate(self.value_date)
        self.issue_date = datetime_to_turingdate(self.issue_date)
        self.due_date = datetime_to_turingdate(self.due_date)
        if self.trd_curr_code and isinstance(self.trd_curr_code, Currency):
            self.trd_curr_code = self.trd_curr_code.value          # 转换成字符串，便于rich表格显示
        if self.issue_date:
            self.settlement_date = max(self.value_date.addDays(self.settlement_terms), self.issue_date)  # 计算结算日期
            self.cv = Curve(value_date=self.settlement_date, curve_code=self.curve_code)
            if self.curve_code:
                self.cv.resolve()     
        if self.pay_interest_mode:
            if not isinstance(self.pay_interest_mode, CouponType):
                rules = {"ZERO_COUPON": CouponType.ZERO_COUPON,
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
                rules = {"ANNUAL": FrequencyType.ANNUAL,
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
            self._calculate_cash_flow_dates()
            self.frequency = TuringFrequency(self.pay_interest_cycle)
        else:
            self._flow_dates = [self.issue_date, self.due_date]    
        if self.interest_rules:
            if not isinstance(self.interest_rules, DayCountType):
                rules = {"ACT/365": DayCountType.ACT_365L,
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
        self.ca = CurveAdjustment()
        if self.issue_date and self.due_date:
            dc = TuringDayCount(DayCountType.ACT_365F)
            (acc_factor1, _, _) = dc.yearFrac(self.issue_date, self.due_date)
            self.bond_term_year = acc_factor1
            (acc_factor2, _, _) = dc.yearFrac(self.settlement_date, self.due_date)
            self.time_to_maturity_in_year = acc_factor2

    @property
    def _settlement_date(self):
        if self.ctx_pricing_date:
            value_date = max(self.ctx_pricing_date.addDays(self.settlement_terms), self.issue_date)
            return value_date
        return self.settlement_date

    def _curve_resolve(self):
        if self.ctx_pricing_date:
            self.cv.set_value_date(self._settlement_date)
            self.cv.resolve()
        if self.ctx_yield_curve is not None:
            self.cv.set_curve_data(self.ctx_yield_curve)
            self.cv.resolve()
        self._curve_adjust()

    def _curve_adjust(self):
        if self.ctx_parallel_shift:
            self.ca.set_parallel_shift(self.ctx_parallel_shift)
        if self.ctx_curve_shift:
            self.ca.set_parallel_shift(self.ctx_curve_shift)
        if self.ctx_pivot_point:
            self.ca.set_parallel_shift(self.ctx_pivot_point)
        if self.ctx_tenor_start:
            self.ca.set_parallel_shift(self.ctx_tenor_start)
        if self.ctx_tenor_end:
            self.ca.set_parallel_shift(self.ctx_tenor_end)
        if self.ca.isvalid():
            self.cv.adjust(self.ca)

    def isvalid(self):
        """提供给turing sdk做过期判断"""
        if self._settlement_date > self.due_date:
            return False
        return True

    def _calculate_cash_flow_dates(self):
        """ Determine the bond cashflow payment dates."""

        calendar_type = TuringCalendarTypes.CHINA_IB
        bus_day_rule_type = TuringBusDayAdjustTypes.MODIFIED_FOLLOWING
        date_gen_rule_type = TuringDateGenRuleTypes.BACKWARD
        self._flow_dates = TuringSchedule(self.issue_date,
                                          self.due_date,
                                          self.pay_interest_cycle,
                                          calendar_type,
                                          bus_day_rule_type,
                                          date_gen_rule_type,
                                          False)._generate()

    def dollar_duration(self):
        if not self.isvalid():
            raise TuringError("Bond settles after it matures.")
        return self.dv01() / dy

    def time_to_maturity(self):
        """剩余期限"""
        return self.due_date - self._settlement_date

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
        self.__post_init__()

    def __repr__(self):
        separator: str = "\n"
        s = f"Class Name: {type(self).__name__}"
        s += f"{separator}Wind Id: {self.wind_id}"
        s += f"{separator}Bbg Id: {self.bbg_id}"
        s += f"{separator}Cusip: {self.cusip}"
        s += f"{separator}Sedol: {self.sedol}"
        s += f"{separator}Ric: {self.ric}"
        s += f"{separator}Isin: {self.isin}"
        s += f"{separator}Ext Asset Id: {self.ext_asset_id}"
        s += f"{separator}Asset Name: {self.asset_name}"
        s += f"{separator}Asset Type: {self.asset_type}"
        s += f"{separator}Trd Curr Code: {self.trd_curr_code}"
        s += f"{separator}Symbol: {self.symbol}"
        s += f"{separator}Comb Symbol: {self.comb_symbol}"
        s += f"{separator}Exchange: {self.exchange}"
        s += f"{separator}Issuer: {self.issuer}"
        s += f"{separator}Issue Date: {self.issue_date}"
        s += f"{separator}Due Date: {self.due_date}"
        s += f"{separator}Par: {self.par}"
        s += f"{separator}Coupon Rate: {self.coupon_rate}"
        s += f"{separator}Interest Rate Type: {self.interest_rate_type}"
        s += f"{separator}Pay Interest Cycle: {self.pay_interest_cycle}"
        s += f"{separator}Interest Rules: {self.interest_rules}"
        s += f"{separator}Pay Interest Mode: {self.pay_interest_mode}"
        s += f"{separator}Curve Code: {self.curve_code}"
        return s
