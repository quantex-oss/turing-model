import datetime
from dataclasses import dataclass, field
from typing import List, Any

from loguru import logger

from fundamental.base import Priceable, StringField, FloatField, DateField
from fundamental.base import ctx
from fundamental.turing_db.data import Turing
from fundamental.turing_db.utils import to_snake
from turing_models.products.bonds.bond import TuringBond, TuringFrequencyTypes, \
    TuringDayCountTypes
from turing_models.utilities import TuringDate
from turing_models.utilities.error import TuringError


class BondOrm(Priceable):
    """bond orm定义,取数据用"""
    asset_id = StringField('asset_id')
    name = StringField('name')
    bond_type = StringField('bond_type')
    coupon: float = FloatField("coupon_rate")
    interest_accrued: float = FloatField("interest_accrued")
    bond_term_year: float = FloatField("bond_term_year")
    bond_term_day: float = FloatField("bond_term_day")
    maturity_date: TuringDate = DateField("due_date")
    issue_date: TuringDate = DateField("issue_date")
    freq_type = StringField('freq_type')
    accrual_type = StringField('accrual_type')
    face_amount: float = FloatField("par_value_iss")
    clean_price: float = FloatField("clean_price")
    curve_code = StringField('curve_code')
    ytm: float = FloatField("ytm")
    quantity: float = FloatField("quantity")
    zero_dates: List[Any] = field(default_factory=list)
    zero_rates: List[Any] = field(default_factory=list)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.ctx = ctx
        self.curve_code_list = []

    def fetch_yield_curve(self, curve_code_list):
        """根据asset_ids的集合为参数,取行情"""
        logger.debug(f"self.bond.curve_code: {curve_code_list}")
        try:
            return Turing.get_yieldcurve(curve_code_list)
        except:
            return None

    def fetch_quotes(self, ids):
        """根据asset_ids的集合为参数,取行情"""
        try:
            return Turing.get_bond_markets(ids)
        except:
            return None

    def put_zero_dates(self, ):
        zero_dates = []
        curve = self.fetch_yield_curve([self.curve_code])
        if curve:
            for code in to_snake(curve):
                logger.debug(f"{code.get('curve_code')}")
                if code.get("curve_code") == self.curve_code:
                    for cu in code.get('curve_data'):
                        zero_dates.append(cu.get('term'))
        self.zero_dates = zero_dates
        return zero_dates

    def put_zero_rates(self):
        zero_rates = []
        curve = self.fetch_yield_curve([self.curve_code])
        if curve:
            for code in to_snake(curve):
                if code.get("curve_code") == self.curve_code:
                    for cu in code.get('curve_data'):
                        zero_rates.append(cu.get('spot_rate'))
        self.zero_rates = zero_rates
        return zero_rates

    def put_ytm(self, quotes_dict, asset_id):
        for quote in quotes_dict:
            if quote.get("asset_id") == asset_id:
                if quote.get("ytm", None):
                    return quote.get("ytm", None)
        return None


@dataclass
class Bond:
    asset_id: str = None
    bond_type: str = None
    coupon: float = 0.0
    maturity_date: TuringDate = None
    issue_date: TuringDate = None
    freq_type: (str, TuringFrequencyTypes) = None
    accrual_type: (str, TuringFrequencyTypes) = None
    face_amount: float = None
    clean_price: float = None
    curve_code: str = None
    name: str = None
    settlement_date: TuringDate = TuringDate(*(datetime.date.today().timetuple()[:3]))
    ytm: float = None
    zero_dates: List[Any] = field(default_factory=list)
    zero_rates: List[Any] = field(default_factory=list)

    def __post_init__(self):
        self.name = 'No name'
        self.bond = None

        if self.zero_dates:
            self.zero_dates = self.settlement_date.addYears(self.zero_dates)

        if self.issue_date:
            self.new_bond()

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
        self.new_bond()

    def new_bond(self):
        logger.debug((self.issue_date,
                      self.maturity_date,
                      self.coupon,
                      self.freq_type,
                      self.accrual_type,
                      self.face_amount))
        if self.freq_type and not isinstance(self.freq_type, TuringFrequencyTypes):
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
        if self.accrual_type and not isinstance(self.accrual_type, TuringDayCountTypes):
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
        self.bond = TuringBond(self.issue_date,
                               self.maturity_date,
                               self.coupon,
                               self.freq_type,
                               self.accrual_type,
                               self.face_amount)

    def resolve(self, expand_dict):

        self._set_by_dict(expand_dict)
