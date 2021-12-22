import datetime
import enum
from abc import ABCMeta
from dataclasses import dataclass
from typing import Union

from fundamental.turing_db.bond_data import BondApi
from turing_models.instruments.common import IR, YieldCurveCode, CurveCode, Curve, CurveAdjustment, Currency
from turing_models.instruments.core import InstrumentBase
from turing_models.utilities.calendar import TuringCalendarTypes, TuringBusDayAdjustTypes, \
    TuringDateGenRuleTypes
from turing_models.utilities.day_count import TuringDayCountTypes, TuringDayCount
from turing_models.utilities.error import TuringError
from turing_models.utilities.frequency import TuringFrequency, TuringFrequencyTypes
from turing_models.utilities.global_types import TuringYTMCalcType, TuringCouponType
from turing_models.utilities.helper_functions import to_string
from turing_models.utilities.schedule import TuringSchedule
from turing_models.utilities.turing_date import TuringDate

dy = 0.0001


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class Bond(IR, InstrumentBase, metaclass=ABCMeta):
    # bond_symbol: str = None
    # csname: str = None
    # curve_name: Union[str, CurveCode] = None
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
    issuer: str = None
    issue_date: TuringDate = None                          # 发行日
    due_date: TuringDate = None                            # 到期日
    par: float = None                                      # 面值
    coupon_rate: float = None
    interest_rate_type: str = None
    pay_interest_cycle: (str, TuringFrequencyTypes) = None                         # 付息频率
    interest_rules: (str, TuringDayCountTypes) = None                             # 计息类型
    pay_interest_mode: (str, TuringCouponType) = None      # 付息方式
    curve_code: Union[str, YieldCurveCode] = None          # 曲线编码
    value_date: TuringDate = TuringDate(
        *(datetime.date.today().timetuple()[:3]))  # 估值日
    settlement_terms: int = 0  # 结算天数，0即T+0结算

    def __post_init__(self):
        super().__init__()
        self.convention = TuringYTMCalcType.UK_DMO         # 惯例
        self.calendar_type = TuringCalendarTypes.CHINA_IB  # 日历类型
        self._redemption = 1.0                             # 到期支付额
        self._flow_dates = []                              # 现金流发生日
        self._flow_amounts = []                            # 现金流发生额
        self._accrued_interest = None
        self._accrued_days = 0.0                           # 应计利息天数
        if self.trd_curr_code and isinstance(self.trd_curr_code, Currency):
            self.trd_curr_code = self.trd_curr_code.value          # 转换成字符串，便于rich表格显示
        if self.issue_date:
            self.settlement_date = max(self.value_date.addDays(self.settlement_terms), self.issue_date)  # 计算结算日期
            self.cv = Curve(value_date=self.settlement_date, curve_code=self.curve_code)
            if self.curve_code:
                self.cv.resolve()
        dc = TuringDayCount(TuringDayCountTypes.ACT_365F)
        (acc_factor1, _, _) = dc.yearFrac(self.issue_date, self.due_date)
        self.bond_term_year = acc_factor1
        (acc_factor2, _, _) = dc.yearFrac(self.settlement_date, self.due_date)
        self.time_to_maturity_in_year = acc_factor2
        if self.pay_interest_mode:
            if self.pay_interest_mode == 'zero coupon':
                self.pay_interest_mode = TuringCouponType.ZERO_COUPON
            elif self.pay_interest_mode == 'discount':
                self.pay_interest_mode = TuringCouponType.DISCOUNT
            elif self.pay_interest_mode == 'coupon-carrying':
                self.pay_interest_mode = TuringCouponType.COUPON_CARRYING
            elif isinstance(self.pay_interest_mode, TuringCouponType):
                pass
            else:
                raise TuringError('Please check the input of cpn_type')
        if self.pay_interest_cycle:
            if self.pay_interest_cycle == '每年付息':
                self.pay_interest_cycle = TuringFrequencyTypes.ANNUAL
            elif self.pay_interest_cycle == '半年付息':
                self.pay_interest_cycle = TuringFrequencyTypes.SEMI_ANNUAL
            elif self.pay_interest_cycle == '4个月一次':
                self.pay_interest_cycle = TuringFrequencyTypes.TRI_ANNUAL
            elif self.pay_interest_cycle == '按季付息':
                self.pay_interest_cycle = TuringFrequencyTypes.QUARTERLY
            elif self.pay_interest_cycle == '按月付息':
                self.pay_interest_cycle = TuringFrequencyTypes.MONTHLY
            elif isinstance(self.pay_interest_cycle, TuringFrequencyTypes):
                pass
            else:
                raise TuringError('Please check the input of freq_type')
            self._calculate_cash_flow_dates()
            self.frequency = TuringFrequency(self.pay_interest_cycle)
        else:
            self._flow_dates = [self.issue_date, self.due_date]    
        if self.interest_rules:
            if self.interest_rules == 'ACT/365':
                self.interest_rules = TuringDayCountTypes.ACT_365L
            elif self.interest_rules == 'ACT/ACT':
                self.interest_rules = TuringDayCountTypes.ACT_ACT_ISDA
            elif self.interest_rules == 'ACT/360':
                self.interest_rules = TuringDayCountTypes.ACT_360
            elif self.interest_rules == '30/360':
                self.interest_rules = TuringDayCountTypes.THIRTY_E_360
            elif self.interest_rules == 'ACT/365F':
                self.interest_rules = TuringDayCountTypes.ACT_365F
            elif isinstance(self.interest_rules, TuringDayCountTypes):
                pass
            else:
                raise TuringError('Please check the input of accrual_type')
        self.ca = CurveAdjustment()

    @property
    def settlement_date_(self):
        if self.ctx_pricing_date:
            value_date = max(self.ctx_pricing_date.addDays(self.settlement_terms), self.issue_date)
            return value_date
        return self.settlement_date

    def curve_resolve(self):
        if self.ctx_pricing_date:
            self.cv.set_value_date(self.settlement_date_)
            self.cv.resolve()
        if self.ctx_bond_yield_curve is not None:
            self.cv.set_curve_data(self.ctx_bond_yield_curve)
            self.cv.resolve()
        self.curve_adjust()

    def curve_adjust(self):
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
        if self.settlement_date_ > self.due_date:
            return False
        return True

    def get_curve_name(self):
        return getattr(CurveCode, self.curve_code, '')

    def _calculate_cash_flow_dates(self):
        """ Determine the bond cashflow payment dates."""

        calendar_type = TuringCalendarTypes.CHINA_IB
        bus_day_rule_type = TuringBusDayAdjustTypes.FOLLOWING
        date_gen_rule_type = TuringDateGenRuleTypes.BACKWARD
        self._flow_dates = TuringSchedule(self.issue_date,
                                          self.due_date,
                                          self.pay_interest_cycle,
                                          calendar_type,
                                          bus_day_rule_type,
                                          date_gen_rule_type)._generate()

    def dollar_duration(self):
        if not self.isvalid():
            raise TuringError("Bond settles after it matures.")
        return self.dv01() / dy

    def time_to_maturity(self):
        """剩余期限"""
        return self.due_date - self.settlement_date_

    def _resolve(self):
        # Bond_ 为自定义时自动生成
        if not self.asset_id:
            asset_id = BondApi.fetch_comb_symbol_to_asset_id(self.bond_symbol)
            if asset_id:
                setattr(self, 'asset_id', asset_id)
        if self.asset_id and not self.asset_id.startswith("Bond_"):
            bond = BondApi.fetch_one_bond_orm(asset_id=self.asset_id)
            for k, v in bond.items():
                try:
                    if not getattr(self, k, None) and v:
                        setattr(self, k, v)
                except Exception:
                    pass
        if not self.csname:
            csname = BondApi.fetch_comb_symbol_to_csname(self.bond_symbol)
            if csname:
                setattr(self, 'csname', csname)
        self.__post_init__()

    def __repr__(self):
        s = to_string("class_name", type(self).__name__)
        s += to_string("wind_id", self.wind_id)
        s += to_string("bbg_id", self.bbg_id)
        s += to_string("cusip", self.cusip)
        s += to_string("sedol", self.sedol)
        s += to_string("ric", self.ric)
        s += to_string("isin", self.isin)
        s += to_string("ext_asset_id", self.ext_asset_id)
        s += to_string("asset_name", self.asset_name)
        s += to_string("asset_type", self.asset_type)
        s += to_string("trd_curr_code", self.trd_curr_code)
        s += to_string("symbol", self.symbol)
        s += to_string("comb_symbol", self.comb_symbol)
        s += to_string("exchange", self.exchange)
        s += to_string("issuer", self.issuer)
        s += to_string("issue_date", self.issue_date)
        s += to_string("due_date", self.due_date)
        s += to_string("par", self.par)
        s += to_string("coupon_rate", self.coupon_rate)
        s += to_string("interest_rate_type", self.interest_rate_type)
        s += to_string("pay_interest_cycle", self.pay_interest_cycle)
        s += to_string("interest_rules", self.interest_rules)
        s += to_string("pay_interest_mode", self.pay_interest_mode)
        s += to_string("curve_code", self.curve_code)
        return s
