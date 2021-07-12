import datetime
from dataclasses import dataclass

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
from turing_models.instrument.core import Instrument


def modify_day_count_type(day_count_type):
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
        raise Exception('Please check the input of day_count_type')


def modify_freq_type(freq_type):
    if freq_type == '每年付息':
        return TuringFrequencyTypes.ANNUAL
    elif freq_type == '半年付息':
        return TuringFrequencyTypes.SEMI_ANNUAL
    elif freq_type == '4个月一次':
        return TuringFrequencyTypes.TRI_ANNUAL
    elif freq_type == '按季付息':
        return TuringFrequencyTypes.QUARTERLY
    elif freq_type == '按月付息':
        return TuringFrequencyTypes.MONTHLY
    else:
        raise Exception('Please check the input of freq_type')


def modify_leg_type(leg_type):
    return TuringSwapTypes.PAY if leg_type == 'PAY' \
        else TuringSwapTypes.RECEIVE


@dataclass
class IRS(Instrument):
    asset_id: str = None
    quantity: float = None
    irs_type: str = None
    effective_date: TuringDate = None
    termination_date: TuringDate = None
    fixed_leg_type: str = None
    fixed_coupon: float = None
    fixed_freq_type: str = None
    fixed_day_count_type: str = None
    notional: float = 1000000.0
    float_spread: float = 0.0
    float_freq_type: str = '按季付息'
    float_day_count_type: str = '30/360'
    value_date: TuringDate = TuringDate(*(datetime.date.today().timetuple()[:3]))  # 估值日期
    curve_code1: str = None
    curve_code2: str = None
    zero_dates1: list = None
    zero_rates1: list = None
    zero_dates2: list = None
    zero_rates2: list = None
    first_fixing_rate: float = None
    deposit_term: float = None  # 单位：月
    deposit_rate: float = None
    deposit_day_count_type: str = None
    fixed_freq_type_curve: str = None
    fixed_day_count_type_curve: str = None
    fixed_leg_type_curve: str = None
    __index_curve = None

    def __post_init__(self):
        self.calendar_type = TuringCalendarTypes.WEEKEND
        self.bus_day_adjust_type = TuringBusDayAdjustTypes.FOLLOWING
        self.date_gen_rule_type = TuringDateGenRuleTypes.BACKWARD
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

    @property
    def float_leg_type(self):
        return TuringSwapTypes.RECEIVE if self.fixed_leg_type == 'PAY' \
            else TuringSwapTypes.PAY

    @property
    def value_date_(self):
        return self.ctx.pricing_date or self._value_date

    @property
    def zero_dates1_(self):
        return self.value_date_.addYears(self.zero_dates1)

    @property
    def zero_dates2_(self):
        return self.value_date_.addYears(self.zero_dates2)

    @property
    def discount_curve(self):
        return TuringDiscountCurveZeros(
            self.value_date_, self.zero_dates1_, self.zero_rates1)

    @property
    def index_curve(self):
        if self.__index_curve:
            return self.__index_curve
        elif self.zero_dates2 and self.zero_rates2:
            return TuringDiscountCurveZeros(
                self.value_date_, self.zero_dates2_, self.zero_rates2)
        else:
            return None

    @index_curve.setter
    def index_curve(self, value: TuringDiscountCurve):
        self.__index_curve = value

    @property
    def libor_curve(self):
        return self.build_ibor_single_curve()

    def build_ibor_single_curve(self):
        value_date = self.value_date_

        depos = []
        fras = []
        swaps = []

        due_date = value_date.addMonths(self.deposit_term)
        depo1 = TuringIborDeposit(value_date,
                                  due_date,
                                  self.deposit_rate,
                                  self.deposit_day_count_type_)
        depos.append(depo1)

        for i in range(len(self.zero_dates1_)):
            swap = IRS(effective_date=value_date,
                       termination_date=self.zero_dates1_[i],
                       fixed_leg_type=self.fixed_leg_type_curve,
                       fixed_coupon=self.zero_rates1[i],
                       fixed_freq_type=self.fixed_freq_type_curve,
                       fixed_day_count_type=self.fixed_day_count_type_curve)
            swaps.append(swap)

        libor_curve = TuringIborSingleCurve(value_date, depos, fras, swaps)

        return libor_curve

    def price(self):
        """ Value the interest rate swap on a value date given a single Ibor
        discount curve. """

        # if self.index_curve is None:
        #     self.index_curve = self.discount_curve

        fixed_leg_value = self.fixed_leg.value(self.value_date_,
                                               self.libor_curve)

        float_leg_value = self.float_leg.value(self.value_date_,
                                               self.libor_curve,
                                               self.libor_curve,
                                               self.first_fixing_rate)

        return fixed_leg_value + float_leg_value

    def pv01(self):
        ''' Calculate the value of 1 basis point coupon on the fixed leg. '''

        pv = self.fixed_leg.value(self.value_date_,
                                  self.libor_curve)

        # Needs to be positive even if it is a payer leg
        pv = np.abs(pv)
        pv01 = pv / self.fixed_leg._coupon / self.fixed_leg._notional
        return pv01

    def swap_rate(self):
        ''' Calculate the fixed leg coupon that makes the swap worth zero.
        If the valuation date is before the swap payments start then this
        is the forward swap rate as it starts in the future. The swap rate
        is then a forward swap rate and so we use a forward discount
        factor. If the swap fixed leg has begun then we have a spot
        starting swap. The swap rate can also be calculated in a dual curve
        approach but in this case the first fixing on the floating leg is
        needed. '''

        pv01 = self.pv01()

        if abs(pv01) < gSmall:
            raise Exception("PV01 is zero. Cannot compute swap rate.")

        # if self.index_curve is None:
        #     self.index_curve = self.discount_curve

        float_leg_pv = self.float_leg.value(self.value_date_,
                                            self.libor_curve,
                                            self.libor_curve,
                                            self.first_fixing_rate)

        float_leg_pv /= self.fixed_leg._notional

        cpn = float_leg_pv / pv01
        return cpn
