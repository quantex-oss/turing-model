import datetime
from dataclasses import dataclass

from fundamental.base import Priceable, StringField, FloatField, DateField
from fundamental.base import ctx
from turing_models.utilities import TuringDate
from turing_models.products.bonds.bond import TuringBond, TuringFrequencyTypes, \
     TuringDayCountTypes
from turing_models.utilities.error import TuringError


class BondOrm(Priceable):
    """bond orm定义,取数据用"""
    asset_id = StringField('asset_id')
    bond_type = StringField('bond_type')
    coupon: float = FloatField("coupon_rate")
    interest_accrued: float = FloatField("interest_accrued")
    bond_term_year: float = FloatField("bond_term_year")
    bond_term_day: float = FloatField("bond_term_day")
    maturity_date: TuringDate = DateField("due_date")
    issue_date: TuringDate = DateField("issue_date")
    freq_type = StringField('freq_type')
    accrual_type = StringField('accrual_type')
    face_amount: float = FloatField("face_amount")
    clean_price: float = FloatField("clean_price")
    curve_code = StringField('curve_code')
    ytm: float = FloatField("ytm")
    zero_dates: list = None
    zero_rates: list = None

    def __init__(self, **kw):
        super().__init__(**kw)
        self.ctx = ctx


@dataclass
class Bond:
    asset_id: str = None
    bond_type: str = None
    coupon: float = None
    maturity_date: TuringDate = None
    issue_date: TuringDate = None
    freq_type: str = None
    accrual_type: str = None
    face_amount: float = None
    clean_price: float = None
    curve_code: str = None
    name: str = None
    settlement_date: TuringDate = TuringDate(*(datetime.date.today().timetuple()[:3]))
    ytm: float = None
    zero_dates: list = None
    zero_rates: list = None

    def __post_init__(self):
        self.name = 'No name'
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
        else:
            raise TuringError('Please check the input of freq_type')

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
        else:
            raise TuringError('Please check the input of accrual_type')

        self.zero_dates = self.settlement_date.addYears(self.zero_dates)

        self.bond = TuringBond(self.issue_date,
                               self.maturity_date,
                               self.coupon,
                               self.freq_type,
                               self.accrual_type,
                               self.face_amount)

    def dv01(self):
        return self.bond.dv01(self.settlement_date,
                              self.ytm)

    def dollar_duration(self):
        """dollar duration"""
        return self.bond.dollarDuration(self.settlement_date,
                                        self.ytm)

    def dollar_convexity(self):
        """dollar convexity"""
        return self.bond.dollar_convexity(self.settlement_date,
                                          self.ytm)

    def _set_by_dict(self, tmp_dict):
        for k, v in tmp_dict.items():
            if v:
                setattr(self, k, v)

    def resolve(self, expand_dict):
        self._set_by_dict(expand_dict)
