import datetime
from dataclasses import dataclass
from typing import Union, List

import numpy as np
from fundamental.market.curves.discount_curve import TuringDiscountCurve
from fundamental.market.curves.discount_curve_zeros import TuringDiscountCurveZeros

from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_variables import gSmall
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.calendar import TuringCalendarTypes,  TuringDateGenRuleTypes
from turing_models.utilities.calendar import TuringCalendar, TuringBusDayAdjustTypes
from turing_models.utilities.global_types import TuringSwapTypes
from turing_models.products.rates.fixed_leg import TuringFixedLeg
from turing_models.products.rates.float_leg import TuringFloatLeg
from turing_models.products.rates.ibor_deposit import TuringIborDeposit
from turing_models.products.rates.ibor_single_curve import TuringIborSingleCurve
from turing_models.instruments.core import Instrument
from turing_models.utilities.helper_functions import to_string
from turing_models.utilities.error import TuringError


bump = 5e-4


def modify_day_count_type(day_count_type):
    if isinstance(day_count_type, TuringDayCountTypes):
        return day_count_type
    else:
        if day_count_type == 'ACT/365':
            return TuringDayCountTypes.ACT_365L
        elif day_count_type == 'ACT/ACT':
            return TuringDayCountTypes.ACT_ACT_ISDA
        elif day_count_type == 'ACT/360':
            return TuringDayCountTypes.ACT_360
        elif day_count_type == '30/360':
            return TuringDayCountTypes.THIRTY_E_360
        elif day_count_type == 'ACT/365F':
            return TuringDayCountTypes.ACT_365F
        else:
            raise TuringError('Please check the input of day_count_type')


def modify_freq_type(freq_type):
    if isinstance(freq_type, TuringFrequencyTypes):
        return freq_type
    else:
        if freq_type == '每年付息' or freq_type == '每年重置':
            return TuringFrequencyTypes.ANNUAL
        elif freq_type == '半年付息' or freq_type == '半年重置':
            return TuringFrequencyTypes.SEMI_ANNUAL
        elif freq_type == '4个月一次':
            return TuringFrequencyTypes.TRI_ANNUAL
        elif freq_type == '按季付息' or freq_type == '按季重置':
            return TuringFrequencyTypes.QUARTERLY
        elif freq_type == '按月付息' or freq_type == '按月重置':
            return TuringFrequencyTypes.MONTHLY
        elif freq_type == '按周付息' or freq_type == '按周重置':
            return TuringFrequencyTypes.WEEKLY
        elif freq_type == '两周付息' or freq_type == '两周重置':
            return TuringFrequencyTypes.BIWEEKLY
        elif freq_type == '按天付息' or freq_type == '按天重置':
            return TuringFrequencyTypes.DAILY
        else:
            raise TuringError('Please check the input of freq_type')


def modify_leg_type(leg_type):
    if isinstance(leg_type, TuringSwapTypes):
        return leg_type
    else:
        if leg_type == 'PAY':
            return TuringSwapTypes.PAY
        elif leg_type == 'RECEIVE':
            return TuringSwapTypes.RECEIVE
        else:
            raise TuringError('Please check the input of leg_type')


def create_ibor_single_curve(value_date: TuringDate,
                             deposit_term: float,
                             deposit_rate: float,
                             deposit_day_count_type: TuringDayCountTypes,
                             swap_curve_dates: List[TuringDate],
                             fixed_leg_type_curve: TuringSwapTypes,
                             swap_curve_rates: List[float],
                             fixed_freq_type_curve: TuringFrequencyTypes,
                             fixed_day_count_type_curve: TuringDayCountTypes,
                             dx: Union[int, float]):
    print(value_date,
          deposit_term,
          deposit_rate,
          deposit_day_count_type,
          swap_curve_dates,
          fixed_leg_type_curve,
          swap_curve_rates,
          fixed_freq_type_curve,
          fixed_day_count_type_curve,
          dx)

    depos = []
    fras = []
    swaps = []

    due_date = value_date.addYears(deposit_term)
    depo1 = TuringIborDeposit(value_date,
                              due_date,
                              deposit_rate,
                              deposit_day_count_type)
    depos.append(depo1)

    for i in range(len(swap_curve_dates)):
        swap = IRS(effective_date=value_date,
                   termination_date=swap_curve_dates[i],
                   fixed_leg_type=fixed_leg_type_curve,
                   fixed_coupon=swap_curve_rates[i] + dx,
                   fixed_freq_type=fixed_freq_type_curve,
                   fixed_day_count_type=fixed_day_count_type_curve,
                   value_date=value_date,
                   reset_freq_type=fixed_freq_type_curve,
                   date_gen_rule_type=TuringDateGenRuleTypes.FORWARD)
        swaps.append(swap)

    libor_curve = TuringIborSingleCurve(value_date, depos, fras, swaps)

    return libor_curve


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class IRS(Instrument):
    asset_id: str = None
    irs_type: str = None
    effective_date: TuringDate = None
    termination_date: TuringDate = None
    fixed_leg_type: Union[str, TuringSwapTypes] = None
    fixed_coupon: float = 100000
    fixed_freq_type: Union[str, TuringFrequencyTypes] = None
    fixed_day_count_type: Union[str, TuringDayCountTypes] = None
    notional: float = 1000000.0
    float_spread: float = 0.0
    float_freq_type: Union[str, TuringFrequencyTypes] = '按季付息'
    float_day_count_type: Union[str, TuringDayCountTypes] = '30/360'
    value_date: TuringDate = TuringDate(*(datetime.date.today().timetuple()[:3]))  # 估值日期
    swap_curve_code: str = None
    index_curve_code: str = None
    swap_curve_dates: list = None
    swap_curve_rates: list = None
    index_curve_dates: list = None
    index_curve_rates: list = None
    first_fixing_rate: float = None
    deposit_term: float = None  # 单位：年
    deposit_rate: float = None
    deposit_day_count_type: Union[str, TuringDayCountTypes] = None
    fixed_freq_type_curve: Union[str, TuringFrequencyTypes] = None
    fixed_day_count_type_curve: Union[str, TuringDayCountTypes] = None
    fixed_leg_type_curve: Union[str, TuringSwapTypes] = None
    reset_freq_type: Union[str, TuringFrequencyTypes] = None
    __index_curve = None
    __libor_curve = None
    date_gen_rule_type: TuringDateGenRuleTypes = TuringDateGenRuleTypes.BACKWARD

    def __post_init__(self):
        super().__init__()
        self.calendar_type = TuringCalendarTypes.WEEKEND
        self.bus_day_adjust_type = TuringBusDayAdjustTypes.FOLLOWING
        self.principal = 0.0
        self.payment_lag = 0
        self.calendar = TuringCalendar(self.calendar_type)
        self.set_param()

    def set_param(self):
        self._value_date = self.value_date
        if self.termination_date:
            self.fixed_leg_type_ = modify_leg_type(self.fixed_leg_type)
            self.fixed_freq_type_ = modify_freq_type(self.fixed_freq_type)
            self.float_freq_type_ = modify_freq_type(self.float_freq_type)
            self.fixed_day_count_type_ = modify_day_count_type(self.fixed_day_count_type)
            self.float_day_count_type_ = modify_day_count_type(self.float_day_count_type)
            self.reset_freq_type_ = modify_freq_type(self.reset_freq_type)
            self.maturity_date = self.calendar.adjust(self.termination_date,
                                                      self.bus_day_adjust_type)
            self.fixed_leg = TuringFixedLeg(self.effective_date,
                                            self.termination_date,
                                            self.fixed_leg_type_,
                                            self.fixed_coupon,
                                            self.fixed_freq_type_,
                                            self.fixed_day_count_type_,
                                            self.notional,
                                            self.principal,
                                            self.payment_lag,
                                            self.calendar_type,
                                            self.bus_day_adjust_type,
                                            self.date_gen_rule_type)

            self.float_leg = TuringFloatLeg(self.effective_date,
                                            self.termination_date,
                                            self.float_leg_type,
                                            self.float_spread,
                                            self.float_freq_type_,
                                            self.float_day_count_type_,
                                            self.reset_freq_type_,
                                            self.notional,
                                            self.principal,
                                            self.payment_lag,
                                            self.calendar_type,
                                            self.bus_day_adjust_type,
                                            self.date_gen_rule_type)

        if self.deposit_day_count_type:
            self.deposit_day_count_type_ = modify_day_count_type(self.deposit_day_count_type)
            self.fixed_freq_type_curve_ = modify_freq_type(self.fixed_freq_type_curve)
            self.fixed_day_count_type_curve_ = modify_day_count_type(self.fixed_day_count_type_curve)
            self.fixed_leg_type_curve_ = modify_leg_type(self.fixed_leg_type_curve)

            self.fixed_leg = TuringFixedLeg(self.effective_date,
                                            self.termination_date,
                                            self.fixed_leg_type_,
                                            self.fixed_coupon_,
                                            self.fixed_freq_type_,
                                            self.fixed_day_count_type_,
                                            self.notional,
                                            self.principal,
                                            self.payment_lag,
                                            self.calendar_type,
                                            self.bus_day_adjust_type,
                                            self.date_gen_rule_type)

    @property
    def float_leg_type(self):
        if self.fixed_leg_type == 'PAY' or self.fixed_leg_type == TuringSwapTypes.PAY:
            return TuringSwapTypes.RECEIVE
        elif self.fixed_leg_type == 'RECEIVE' or self.fixed_leg_type == TuringSwapTypes.RECEIVE:
            return TuringSwapTypes.PAY
        else:
            raise TuringError('Please check the input of fixed_leg_type')

    @property
    def fixed_coupon_(self):
        return self.swap_rate() if self.fixed_coupon == 100000 \
            else self.fixed_coupon

    @property
    def value_date_(self):
        return self.ctx.pricing_date or self._value_date

    @property
    def swap_curve_dates_(self):
        return self.value_date_.addYears(self.swap_curve_dates)

    @property
    def index_curve_dates_(self):
        return self.value_date_.addYears(self.index_curve_dates)

    @property
    def discount_curve(self):
        return TuringDiscountCurveZeros(
            self.value_date_, self.swap_curve_dates_, self.swap_curve_rates)

    @property
    def index_curve(self):
        if self.__index_curve:
            return self.__index_curve
        elif self.index_curve_dates and self.index_curve_rates:
            return TuringDiscountCurveZeros(
                self.value_date_, self.index_curve_dates_, self.index_curve_rates)
        else:
            return None

    @index_curve.setter
    def index_curve(self, value: TuringDiscountCurve):
        self.__index_curve = value

    @property
    def libor_curve(self):
        return self.__libor_curve or self.build_ibor_single_curve(0)

    @libor_curve.setter
    def libor_curve(self, value):
        self.__libor_curve = value

    def build_ibor_single_curve(self, dx):
        return create_ibor_single_curve(self.value_date_,
                                        self.deposit_term,
                                        self.deposit_rate,
                                        self.deposit_day_count_type_,
                                        self.swap_curve_dates_,
                                        self.fixed_leg_type_curve,
                                        self.swap_curve_rates,
                                        self.fixed_freq_type_curve,
                                        self.fixed_day_count_type_curve,
                                        dx)

    def price(self):
        """ Value the interest rate swap on a value date given a single Ibor
        discount curve. """

        libor_curve = self.libor_curve
        if self.index_curve is None:
            self.index_curve = libor_curve

        fixed_leg_value = self.fixed_leg.value(self.value_date_,
                                               libor_curve)

        float_leg_value = self.float_leg.value(self.value_date_,
                                               libor_curve,
                                               self.index_curve,
                                               self.first_fixing_rate)

        return fixed_leg_value + float_leg_value

    def dv01(self):
        """ Calculate the value of 1 basis point coupon on the fixed leg. """

        libor_curve = self.libor_curve
        self.libor_curve = self.build_ibor_single_curve(bump)
        pv_bumpup = self.price()
        self.libor_curve = self.build_ibor_single_curve(-bump)
        pv_bumpdown = self.price()
        dv01 = (pv_bumpup - pv_bumpdown) / 10
        self.libor_curve = libor_curve
        return dv01

    def pv01(self):
        """ Calculate the value of 1 basis point coupon on the fixed leg. """

        pv = self.fixed_leg.value(self.value_date_,
                                  self.libor_curve)

        # Needs to be positive even if it is a payer leg
        pv = np.abs(pv)
        pv01 = pv / self.fixed_leg._coupon / self.fixed_leg._notional
        return pv01

    def swap_rate(self):
        """ Calculate the fixed leg coupon that makes the swap worth zero.
        If the valuation date is before the swap payments start then this
        is the forward swap rate as it starts in the future. The swap rate
        is then a forward swap rate and so we use a forward discount
        factor. If the swap fixed leg has begun then we have a spot
        starting swap. The swap rate can also be calculated in a dual curve
        approach but in this case the first fixing on the floating leg is
        needed. """

        pv01 = self.pv01()

        if abs(pv01) < gSmall:
            raise TuringError("PV01 is zero. Cannot compute swap rate.")

        libor_curve = self.libor_curve
        if self.index_curve is None:
            self.index_curve = libor_curve

        float_leg_pv = self.float_leg.value(self.value_date_,
                                            libor_curve,
                                            self.index_curve,
                                            self.first_fixing_rate)

        float_leg_pv = np.abs(float_leg_pv)
        float_leg_pv /= self.fixed_leg._notional

        cpn = float_leg_pv / pv01
        return cpn

    def __repr__(self):
        s = to_string("Object Type", type(self).__name__)
        s += to_string("Asset Id", self.asset_id)
        s += to_string("IRS Type", self.irs_type)
        s += to_string("Effective Date", self.effective_date)
        s += to_string("Termination Date", self.termination_date)
        s += to_string("Fixed Leg Type", self.fixed_leg_type)
        s += to_string("Fixed Coupon", self.fixed_coupon)
        s += to_string("Fixed Freq Type", self.fixed_freq_type)
        s += to_string("Fixed Day Count Type", self.fixed_day_count_type)
        s += to_string("Notional", self.notional)
        s += to_string("Float Spread", self.float_spread)
        s += to_string("Float Freq Type", self.float_freq_type)
        s += to_string("Float Day Count Type", self.float_day_count_type)
        s += to_string("Value Date", self.value_date_)
        s += to_string("Swap Curve Code", self.swap_curve_code)
        s += to_string("Index Curve Code", self.index_curve_code)
        s += to_string("First Fixing Rate", self.first_fixing_rate)
        s += to_string("Deposit Term", self.deposit_term)
        s += to_string("Deposit Rate", self.deposit_rate)
        s += to_string("Deposit Day Count Type", self.deposit_day_count_type)
        s += to_string("Fixed Freq Type Curve", self.fixed_freq_type_curve)
        s += to_string("Fixed Day Count Type Curve", self.fixed_day_count_type_curve)
        s += to_string("Fixed Leg Type Curve", self.fixed_leg_type_curve, "")
        return s
