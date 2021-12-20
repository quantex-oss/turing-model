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
    asset_id: str = None
    bond_symbol: str = None
    csname: str = None
    curr_code: (str, enum) = 'CNY'
    exchange_code: str = None
    issue_date: TuringDate = None                          # 发行日
    due_date: TuringDate = None                            # 到期日
    # bond_term_year: float = None
    # bond_term_day: float = None
    freq_type: Union[str, TuringFrequencyTypes] = None     # 付息频率
    accrual_type: Union[str, TuringDayCountTypes] = None   # 计息类型
    par: float = None                                      # 面值
    cpn_type: Union[str, TuringCouponType] = None                                   # 付息方式
    # curve_name: Union[str, CurveCode] = None
    curve_code: Union[str, YieldCurveCode] = None          # 曲线编码
    value_date: TuringDate = TuringDate(
        *(datetime.date.today().timetuple()[:3]))          # 估值日
    settlement_terms: int = 0                              # 结算天数，0即T+0结算

    def __post_init__(self):
        super().__init__()
        self.convention = TuringYTMCalcType.UK_DMO         # 惯例
        self.calendar_type = TuringCalendarTypes.CHINA_IB  # 日历类型
        self._redemption = 1.0                             # 到期支付额
        self._flow_dates = []                              # 现金流发生日
        self._flow_amounts = []                            # 现金流发生额
        self._accrued_interest = None
        self._accrued_days = 0.0                           # 应计利息天数
        if self.curr_code and isinstance(self.curr_code, Currency):
            self.curr_code = self.curr_code.value          # 转换成字符串，便于rich表格显示
        # if not self.due_date and self.issue_date and self.bond_term_year:
            # self.due_date = self.issue_date.addYears(self.bond_term_year)
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
        if self.cpn_type:
            if self.cpn_type == 'zero coupon':
                self.cpn_type = TuringCouponType.ZERO_COUPON
            elif self.cpn_type == 'discount':
                self.cpn_type = TuringCouponType.DISCOUNT
            elif self.cpn_type == 'coupon-carrying':
                self.cpn_type = TuringCouponType.COUPON_CARRYING
            elif isinstance(self.cpn_type, TuringCouponType):
                pass
            else:
                raise TuringError('Please check the input of cpn_type')
        if self.freq_type:
            if self.freq_type == '每年付息':
                self.freq_type = TuringFrequencyTypes.ANNUAL
            elif self.freq_type == '半年付息':
                self.freq_type = TuringFrequencyTypes.SEMI_ANNUAL
            elif self.freq_type == '4个月一次':
                self.freq_type = TuringFrequencyTypes.TRI_ANNUAL
            elif self.freq_type == '按季付息':
                self.freq_type = TuringFrequencyTypes.QUARTERLY
            elif self.freq_type == '按月付息':
                self.freq_type = TuringFrequencyTypes.MONTHLY
            elif isinstance(self.freq_type, TuringFrequencyTypes):
                pass
            else:
                raise TuringError('Please check the input of freq_type')
            self._calculate_cash_flow_dates()
            self.frequency = TuringFrequency(self.freq_type)
        else:
            self._flow_dates = [self.issue_date, self.due_date]    
        if self.accrual_type:
            if self.accrual_type == 'ACT/365':
                self.accrual_type = TuringDayCountTypes.ACT_365L
            elif self.accrual_type == 'ACT/ACT':
                self.accrual_type = TuringDayCountTypes.ACT_ACT_ISDA
            elif self.accrual_type == 'ACT/360':
                self.accrual_type = TuringDayCountTypes.ACT_360
            elif self.accrual_type == '30/360':
                self.accrual_type = TuringDayCountTypes.THIRTY_E_360
            elif self.accrual_type == 'ACT/365F':
                self.accrual_type = TuringDayCountTypes.ACT_365F
            elif isinstance(self.accrual_type, TuringDayCountTypes):
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
                                          self.freq_type,
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
        s = to_string("Object Type", type(self).__name__)
        s += to_string("Asset Id", self.asset_id)
        s += to_string("Issue Date", self.issue_date)
        s += to_string("Due Date", self.due_date)
        s += to_string("Freq Type", self.freq_type)
        s += to_string("Accrual Type", self.accrual_type)
        s += to_string("Par", self.par)
        return s
