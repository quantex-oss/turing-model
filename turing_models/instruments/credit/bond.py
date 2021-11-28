import datetime
import traceback
from abc import ABCMeta
from dataclasses import dataclass
from typing import Union

from fundamental.turing_db.bond_data import BondApi
from fundamental.turing_db.data import Turing
from fundamental.turing_db.err import FastError
from fundamental.turing_db.utils import to_snake
from turing_models.instruments.common import CD
from turing_models.instruments.core import InstrumentBase
from turing_models.utilities.calendar import TuringCalendarTypes, TuringBusDayAdjustTypes, \
     TuringDateGenRuleTypes
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.error import TuringError
from turing_models.utilities.frequency import TuringFrequency, TuringFrequencyTypes
from turing_models.utilities.global_types import TuringYTMCalcType
from turing_models.utilities.helper_functions import to_string
from turing_models.utilities.schedule import TuringSchedule
from turing_models.utilities.turing_date import TuringDate

dy = 0.0001


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class Bond(CD, InstrumentBase, metaclass=ABCMeta):
    asset_id: str = None
    bond_symbol: str = None
    exchange_code: str = None
    issue_date: TuringDate = None  # 发行日
    due_date: TuringDate = None  # 到期日
    freq_type: Union[str, TuringFrequencyTypes] = None  # 付息频率
    accrual_type: Union[str, TuringDayCountTypes] = None  # 计息类型
    par: float = None  # 面值
    bond_clean_price: float = None  # 净价
    value_date: TuringDate = TuringDate(
        *(datetime.date.today().timetuple()[:3]))  # 估值日
    settlement_terms: int = 0  # 结算天数，0即T+0结算

    def __post_init__(self):
        super().__init__()
        self.convention = TuringYTMCalcType.UK_DMO  # 惯例
        self.calendar_type = TuringCalendarTypes.WEEKEND  # 日历类型
        self._redemption = 1.0  # 到期支付额
        if self.issue_date:
            self.settlement_date = max(self.value_date.addDays(self.settlement_terms), self.issue_date)  # 计算结算日期
        self._flow_dates = []  # 现金流发生日
        self._flow_amounts = []  # 现金流发生额
        self._accrued_interest = None
        self._accrued_days = 0.0  # 应计利息天数
        if self.freq_type:
            self._calculate_flow_dates()
            self.frequency = TuringFrequency(self.freq_type_)

    @property
    def freq_type_(self):
        if isinstance(self.freq_type, TuringFrequencyTypes):
            return self.freq_type
        else:
            if self.freq_type == '每年付息':
                return TuringFrequencyTypes.ANNUAL
            elif self.freq_type == '半年付息':
                return TuringFrequencyTypes.SEMI_ANNUAL
            elif self.freq_type == '4个月一次':
                return TuringFrequencyTypes.TRI_ANNUAL
            elif self.freq_type == '按季付息':
                return TuringFrequencyTypes.QUARTERLY
            elif self.freq_type == '按月付息':
                return TuringFrequencyTypes.MONTHLY
            else:
                raise TuringError('Please check the input of freq_type')

    @property
    def accrual_type_(self):
        if isinstance(self.accrual_type, TuringDayCountTypes):
            return self.accrual_type
        else:
            if self.accrual_type == 'ACT/365':
                return TuringDayCountTypes.ACT_365L
            elif self.accrual_type == 'ACT/ACT':
                return TuringDayCountTypes.ACT_ACT_ISDA
            elif self.accrual_type == 'ACT/360':
                return TuringDayCountTypes.ACT_360
            elif self.accrual_type == '30/360':
                return TuringDayCountTypes.THIRTY_E_360
            elif self.accrual_type == 'ACT/365F':
                return TuringDayCountTypes.ACT_365F
            else:
                raise TuringError('Please check the input of accrual_type')

    @property
    def settlement_date_(self):
        return self.ctx_pricing_date or self.settlement_date

    def _calculate_flow_dates(self):
        """ Determine the bond cashflow payment dates."""

        calendar_type = TuringCalendarTypes.CHINA_IB
        bus_day_rule_type = TuringBusDayAdjustTypes.FOLLOWING
        date_gen_rule_type = TuringDateGenRuleTypes.BACKWARD
        self._flow_dates = TuringSchedule(self.issue_date,
                                          self.due_date,
                                          self.freq_type_,
                                          calendar_type,
                                          bus_day_rule_type,
                                          date_gen_rule_type)._generate()

    def dollar_duration(self):
        return self.dv01() / dy

    def fetch_yield_curve(self, curve_code_list):
        """根据asset_ids的集合为参数,取行情"""
        try:
            return Turing.get_yieldcurve(_ids=tuple(curve_code_list))
        except Exception:
            traceback.print_exc()
            return None

    def fetch_quotes(self, gurl=None, _ids=None):
        """根据asset_ids的集合为参数,取行情"""
        try:
            res = Turing.get_bond_markets(gurl=gurl, _ids=_ids)
            return res
        except Exception as e:
            traceback.print_exc()
            return None

    def put_zero_dates(self, curve_code_list):
        zero_dates = []
        curve = self.fetch_yield_curve(curve_code_list)
        if curve:
            for code in to_snake(curve):
                if code.get("curve_code") == curve_code_list[0]:
                    for cu in code.get('curve_data'):
                        zero_dates.append(cu.get('term'))
        self.zero_dates = zero_dates
        return zero_dates

    def put_zero_rates(self, curve_code_list):
        zero_rates = []
        curve = self.fetch_yield_curve(curve_code_list)
        if curve:
            for code in to_snake(curve):
                if code.get("curve_code") == curve_code_list[0]:
                    for cu in code.get('curve_data'):
                        zero_rates.append(cu.get('spot_rate'))
        self.zero_rates = zero_rates
        return zero_rates

    def set_curve(self, gurl=None):
        curve = BondApi.fetch_yield_curve(
            gurl=gurl, bond_curve_code=getattr(self, 'curve_code'))
        if not curve:
            raise FastError(code=10020,
                            msg="参数不全, bond_yield_curve api return null",
                            data=None)
        for code in to_snake(curve):
            if code.get("curve_code") == getattr(self, 'curve_code'):
                for cu in code.get('curve_data'):
                    self.zero_dates.append(cu.get('term'))
                    self.zero_rates.append(cu.get('spot_rate'))

    def _resolve(self):
        # Bond_ 为自定义时自动生成
        if self.asset_id and not self.asset_id.startswith("Bond_"):
            bond = BondApi.fetch_one_bond_orm(asset_id=self.asset_id)
            for k, v in bond.items():
                try:
                    if not getattr(self, k, None) and v:
                        setattr(self, k, v)
                except Exception:
                    pass
        self.__post_init__()

    def __repr__(self):
        s = to_string("Object Type", type(self).__name__)
        s += to_string("Asset Id", self.asset_id)
        s += to_string("Issue Date", self.issue_date)
        s += to_string("Due Date", self.due_date)
        s += to_string("Freq Type", self.freq_type)
        s += to_string("Accrual Type", self.accrual_type)
        s += to_string("Par", self.par)
        s += to_string("Settlement Date", self.settlement_date_)
        return s
