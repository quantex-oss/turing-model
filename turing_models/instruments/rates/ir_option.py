import datetime
from abc import ABCMeta
from dataclasses import dataclass, field
from typing import List, Any, Union
import numpy as np
from enum import Enum

from fundamental.turing_db.bond_data import BondApi
from turing_models.instruments.common import IR, YieldCurveCode, CurveCode, YieldCurve, CurveAdjustment, Currency
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
from turing_models.utilities.helper_functions import to_string, to_datetime, to_turing_date
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_types import OptionType, TuringExerciseType
from turing_models.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.market.curves.discount_curve_zeros import TuringDiscountCurveZeros
from turing_models.utilities.global_variables import gDaysInYear

dy = 0.0001


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class IROption(IR, InstrumentBase, metaclass=ABCMeta):
    asset_id: str = None
    underlying_asset_id: str = None
    underlying_wind_id: str = None
    underlying_bbg_id: str = None
    underlying_cusip: str = None
    underlying_sedol: str = None
    underlying_ric: str = None
    underlying_isin: str = None
    underlying_ext_asset_id: str = None
    underlying_symbol: str = None
    underlying_comb_symbol: str = None 
    value_date: (datetime.datetime, datetime.date) = datetime.date.today()  # 估值日
    notional: float = None
    notional_currency: (str, Currency) = None
    number_of_options: float = None
    strike: float = None
    expiry: TuringDate = None
    exercise_type: (
        str, TuringExerciseType) = TuringExerciseType.EUROPEAN  #执行类型
    option_type: (str, OptionType) = None  # CALL/PUT
    start_date: TuringDate = None
    value_date: TuringDate = TuringDate(
        *(datetime.date.today().timetuple()[:3]))
    volatility: float = None
    interest_rate: float = 0
    zero_dates: List[Any] = field(default_factory=list)
    zero_rates: List[Any] = field(default_factory=list)
    _valuation_date = None
    _spot = None
    _vol = None
    _discount_curve_rf = None

    def __post_init__(self):
        super().__init__()        
        # self.check_underlier()
        self.calendar_type = TuringCalendarTypes.CHINA_IB  # 日历类型
        self.value_date = to_turing_date(self.value_date)
        # if self.trd_curr_code and isinstance(self.trd_curr_code, Currency):
        #     self.trd_curr_code = self.trd_curr_code.value  # 转换成字符串，便于rich表格显示      
        self._check_param()
        self.ca = CurveAdjustment()
        
    @property
    def date_for_interface(self):
        # turing sdk提供的接口支持传datetime.datetime格式的时间或者latest
        if self.ctx_pricing_date is not None:
            if isinstance(self.ctx_pricing_date, str):
                value_date = self.ctx_pricing_date
            else:
                value_date = to_datetime(self.ctx_pricing_date)
            return value_date
        return self.value_date
    
    @property
    def _value_date(self):
        value_date = self._valuation_date or max(to_turing_date(self.date_for_interface), self.start_date)
        return value_date
    
    @_value_date.setter
    def _value_date(self, value: TuringDate):
        self._valuation_date = value
   
    @property
    def _zero_dates(self):
        """把年化的时间列表转换为TuringDate格式"""
        return self._value_date.addYears(self.zero_dates)
    
    @property
    def _interest_rate(self) -> float:
        return self.ctx_interest_rate or self.interest_rate
        
    @property
    def discount_curve_rf(self):
        if self._discount_curve_rf:
            return self._discount_curve_rf
        else:
            if self._interest_rate:
                return TuringDiscountCurveFlat(
                    self._value_date, self._interest_rate)
            elif self._zero_dates and self.zero_rates:
                return TuringDiscountCurveZeros(
                    self._value_date, self._zero_dates, self.zero_rates)

    @discount_curve_rf.setter
    def discount_curve_rf(self, value: TuringDiscountCurveZeros):
        self._discount_curve_rf = value

    def isvalid(self):
        """提供给turing sdk做过期判断"""

        if getattr(self, '_value_date', '') \
                and getattr(self, 'expiry', '') \
                and getattr(self, '_value_date', '') > \
                    getattr(self, 'expiry', ''):
            return False
        return True
    
    def time_to_maturity_in_year(self):
        """剩余期限"""
        if self.expiry > self._value_date:
            return (self.expiry - self._value_date) / gDaysInYear
        else:
            raise TuringError("Expiry must be > Value_Date")


    @property
    def volatility_(self):
        v = self.ctx_volatility or self.volatility
        if np.all(v >= 0.0):
            v = np.maximum(v, 1e-10)
            return v
        else:
            raise TuringError("Volatility should not be negative.")
    
  
    # def check_underlier(self):
    #     if self.underlying_symbol and not self.underlier:
    #         if isinstance(self.underlying_symbol, Enum):
    #             self.underlier = Turing.get_fx_symbol_to_id(
    #                 _id=self.underlying_symbol.value).get('asset_id')
    #         else:
    #             self.underlier = Turing.get_fx_symbol_to_id(
    #                 _id=self.underlying_symbol).get('asset_id')

    def __repr__(self):
        separator: str = "\n"
        s = f"Class Name: {type(self).__name__}"
        s += f"{separator}Wind Id: {self.underlying_wind_id}"
        s += f"{separator}Bbg Id: {self.underlying_bbg_id}"
        s += f"{separator}Cusip: {self.underlying_cusip}"
        s += f"{separator}Sedol: {self.underlying_sedol}"
        s += f"{separator}Ric: {self.underlying_ric}"
        s += f"{separator}Isin: {self.underlying_isin}"
        s += f"{separator}Ext Asset Id: {self.underlying_ext_asset_id}"
        s += f"{separator}Trd Curr Code: {self.trd_curr_code}"
        s += f"{separator}Symbol: {self.underlying_symbol}"
        s += f"{separator}Comb Symbol: {self.underlying_comb_symbol}"
        return s
