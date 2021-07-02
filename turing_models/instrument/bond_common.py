import datetime
from dataclasses import dataclass

from tunny import model
from fundamental.base import Context, ctx

from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.schedule import TuringSchedule
from turing_models.utilities.global_types import TuringYTMCalcType
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.frequency import TuringFrequency, TuringFrequencyTypes
from turing_models.utilities.calendar import TuringCalendarTypes, TuringBusDayAdjustTypes, \
     TuringDateGenRuleTypes


dy = 0.0001


@model
@dataclass
class Bond:
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
    ctx: Context = ctx

    def __post_init__(self):
        self.set_param()
        self.face_amount = self.par * self.quantity
        self.calendar_type = TuringCalendarTypes.WEEKEND
        self.frequency = TuringFrequency(self.freq_type_)
        self.convention = TuringYTMCalcType.UK_DMO

        self._redemption = 1.0  # This is amount paid at maturity
        self._flow_dates = []
        self._flow_amounts = []

        self._accrued_interest = None
        self._accrued_days = 0.0

        self._calculate_flow_dates()

    def set_param(self):
        self._settlement_date = self.settlement_date

    def _set_by_dict(self, tmp_dict):
        for k, v in tmp_dict.items():
            if v:
                setattr(self, k, v)

    def resolve(self, expand_dict):
        self._set_by_dict(expand_dict)
        self.set_param()

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
