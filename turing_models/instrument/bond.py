import datetime
from dataclasses import dataclass

from turing_models.instrument.core import Instrument
from turing_models.utilities.calendar import TuringCalendarTypes, TuringBusDayAdjustTypes, \
    TuringDateGenRuleTypes
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.frequency import TuringFrequency, TuringFrequencyTypes
from turing_models.utilities.global_types import TuringYTMCalcType
from turing_models.utilities.schedule import TuringSchedule
from turing_models.utilities.turing_date import TuringDate

dy = 0.0001


@dataclass
class Bond(Instrument):
    asset_id: str = None
    quantity: float = None
    bond_type: str = None
    interest_accrued: float = None
    issue_date: TuringDate = None
    due_date: TuringDate = None
    bond_term_year: float = None
    bond_term_day: float = None
    freq_type: str = None
    accrual_type: str = None
    par: float = None
    clean_price: float = None
    name: str = None
    settlement_date: TuringDate = TuringDate(*(datetime.date.today().timetuple()[:3]))

    def __post_init__(self):
        self.convention = TuringYTMCalcType.UK_DMO
        self._redemption = 1.0  # This is amount paid at maturity
        self._flow_dates = []
        self._flow_amounts = []
        self._accrued_interest = None
        self._accrued_days = 0.0
        self._settlement_date = self.settlement_date
        self.set_param()

    def set_param(self):
        self._settlement_date = self.settlement_date
        self._calculate_flow_dates()
        if self.par:
            self.face_amount = self.par * self.quantity
        self.calendar_type = TuringCalendarTypes.WEEKEND
        if self.freq_type_:
            self.frequency = TuringFrequency(self.freq_type_)

    @property
    def freq_type_(self):
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
            raise Exception('Please check the input of freq_type')

    @property
    def accrual_type_(self):
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
            raise Exception('Please check the input of accrual_type')

    @property
    def settlement_date_(self):
        return self.ctx.pricing_date or self._settlement_date

    def _calculate_flow_dates(self):
        """ Determine the bond cashflow payment dates."""

        calendar_type = TuringCalendarTypes.NONE
        bus_day_rule_type = TuringBusDayAdjustTypes.NONE
        date_gen_rule_type = TuringDateGenRuleTypes.BACKWARD

        self._flow_dates = TuringSchedule(self.issue_date,
                                          self.due_date,
                                          self.freq_type_,
                                          calendar_type,
                                          bus_day_rule_type,
                                          date_gen_rule_type)._generate()

    def dv01(self):
        print("You should not be here!")
        return 0.0

    def dollar_duration(self):
        return self.dv01() / dy

    def dollar_convexity(self):
        print("You should not be here!")
        return 0.0
