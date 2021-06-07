from dataclasses import dataclass

from fundamental.base import Priceable, StringField, FloatField, DateField
from fundamental.market.curves.discount_curve_zeros import TuringDiscountCurveZeros
from turing_models.utilities import TuringDate
from turing_models.products.bonds.bond import TuringBond, TuringFrequencyTypes, \
     TuringDayCountTypes, TuringYTMCalcType

from turing_models.utilities.error import TuringError


@dataclass
class Bond:
    asset_id: str = None
    bond_type: str = None
    issue_date: TuringDate = None
    maturity_date: TuringDate = None
    coupon: float = None
    freq_type: str = None
    accrual_type: str = None
    face_amount: float = None
    name: str = None
    settlement_date: TuringDate = None
    yield_to_maturity: float = None
    convention: str = None
    zero_dates: list = None
    zero_rates: list = None
    clean_price: float = None
    value_date: TuringDate = None

    def __post_init__(self):
        self.name = 'No name'
        if self.freq_type == 'simple':
            self.freq_type = TuringFrequencyTypes.SIMPLE
        elif self.freq_type == 'annual':
            self.freq_type = TuringFrequencyTypes.ANNUAL
        elif self.freq_type == 'semi_annual':
            self.freq_type = TuringFrequencyTypes.SEMI_ANNUAL
        elif self.freq_type == 'tri_annual':
            self.freq_type = TuringFrequencyTypes.TRI_ANNUAL
        elif self.freq_type == 'quarterly':
            self.freq_type = TuringFrequencyTypes.QUARTERLY
        elif self.freq_type == 'monthly':
            self.freq_type = TuringFrequencyTypes.MONTHLY
        elif self.freq_type == 'continuous':
            self.freq_type = TuringFrequencyTypes.CONTINUOUS
        else:
            raise TuringError('Please check the input of freq_type')

        if self.accrual_type == '30_360_bond':
            self.accrual_type = TuringDayCountTypes.THIRTY_360_BOND
        elif self.accrual_type == '30_e_360':
            self.accrual_type = TuringDayCountTypes.THIRTY_E_360
        elif self.accrual_type == '30_e_360_isda':
            self.accrual_type = TuringDayCountTypes.THIRTY_E_360_ISDA
        elif self.accrual_type == '30_e_plus_360':
            self.accrual_type = TuringDayCountTypes.THIRTY_E_PLUS_360
        elif self.accrual_type == 'act_act_isda':
            self.accrual_type = TuringDayCountTypes.ACT_ACT_ISDA
        elif self.accrual_type == 'act_act_icma':
            self.accrual_type = TuringDayCountTypes.ACT_ACT_ICMA
        elif self.accrual_type == 'act_365f':
            self.accrual_type = TuringDayCountTypes.ACT_365F
        elif self.accrual_type == 'act_360':
            self.accrual_type = TuringDayCountTypes.ACT_360
        elif self.accrual_type == 'act_365l':
            self.accrual_type = TuringDayCountTypes.ACT_365L
        elif self.accrual_type == 'simple':
            self.accrual_type = TuringDayCountTypes.SIMPLE

        if self.convention == 'uk_dmo':
            self.convention = TuringYTMCalcType.UK_DMO
        elif self.convention == 'us_street':
            self.convention = TuringYTMCalcType.US_STREET
        elif self.convention == 'us_treasury':
            self.convention = TuringYTMCalcType.US_TREASURY

        if self.bond_type == 'basal':
            self.bond = TuringBond(self.issue_date,
                                   self.maturity_date,
                                   self.coupon,
                                   self.freq_type,
                                   self.accrual_type,
                                   self.face_amount)

    @property
    def discount_curve(self):
        return TuringDiscountCurveZeros(self.value_date,
                                        self.zero_dates,
                                        self.zero_rates)

    def full_price_from_ytm(self):
        return self.bond.fullPriceFromYTM(self.settlement_date,
                                          self.yield_to_maturity,
                                          self.convention)

    def principal(self):
        return self.bond.principal(self.settlement_date,
                                   self.yield_to_maturity,
                                   self.convention)

    def dollar_duration(self):
        return self.bond.dollarDuration(self.settlement_date,
                                        self.yield_to_maturity,
                                        self.convention)

    def macauley_duration(self):
        return self.bond.macauleyDuration(self.settlement_date,
                                          self.yield_to_maturity,
                                          self.convention)

    def modified_duration(self):
        return self.bond.modifiedDuration(self.settlement_date,
                                          self.yield_to_maturity,
                                          self.convention)

    def convexity_from_ytm(self):
        return self.bond.convexityFromYTM(self.settlement_date,
                                          self.yield_to_maturity,
                                          self.convention)

    def clean_price_from_ytm(self):
        return self.bond.cleanPriceFromYTM(self.settlement_date,
                                           self.yield_to_maturity,
                                           self.convention)

    def clean_price_from_discount_curve(self):
        return self.bond.cleanPriceFromDiscountCurve(self.settlement_date,
                                                     self.discount_curve)

    def full_price_from_discount_curve(self):
        return self.bond.fullPriceFromDiscountCurve(self.settlement_date,
                                                    self.discount_curve)

    def current_yield(self):
        return self.bond.currentYield(self.clean_price)

    def yield_to_maturity(self):
        return self.bond.yieldToMaturity(self.settlement_date,
                                         self.clean_price,
                                         self.convention)

    def calc_accrued_interest(self):
        return self.bond.calcAccruedInterest(self.settlement_date)
