from dataclasses import dataclass

from fundamental.base import Priceable, StringField, FloatField, DateField
from fundamental.market.curves.discount_curve_zeros import TuringDiscountCurveZeros
from turing_models.utilities import TuringDate
from turing_models.products.bonds.bond import TuringBond, TuringFrequencyTypes, \
     TuringDayCountTypes, TuringYTMCalcType
from turing_models.products.bonds.bond_frn import TuringBondFRN

from turing_models.utilities.error import TuringError


@dataclass
class Bond:
    asset_id: str = None
    bond_type: str = None
    issue_date: TuringDate = None
    maturity_date: TuringDate = None
    coupon: float = None
    quoted_margin: float = None
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
    next_coupon: float = None
    current_ibor: float = None
    future_ibor: float = None
    discount_margin: float = None
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
        else:
            raise TuringError('Please check the input of accrual_type')

        if self.convention == 'uk_dmo':
            self.convention = TuringYTMCalcType.UK_DMO
        elif self.convention == 'us_street':
            self.convention = TuringYTMCalcType.US_STREET
        elif self.convention == 'us_treasury':
            self.convention = TuringYTMCalcType.US_TREASURY
        else:
            raise TuringError('Please check the input of convention')

        if self.bond_type == 'basal':
            self.bond = TuringBond(self.issue_date,
                                   self.maturity_date,
                                   self.coupon,
                                   self.freq_type,
                                   self.accrual_type,
                                   self.face_amount)
        elif self.bond_type == 'frn':
            self.bond = TuringBondFRN(self.issue_date,
                                      self.maturity_date,
                                      self.quoted_margin,
                                      self.freq_type,
                                      self.accrual_type,
                                      self.face_amount)

    @property
    def discount_curve(self):
        return TuringDiscountCurveZeros(self.value_date,
                                        self.zero_dates,
                                        self.zero_rates)

    def full_price_from_ytm(self):
        if self.bond_type == 'basal':
            return self.bond.fullPriceFromYTM(self.settlement_date,
                                              self.yield_to_maturity,
                                              self.convention)
        else:
            raise TuringError('Please check the input of bond_type')

    def full_price_from_dm(self):
        if self.bond_type == 'frn':
            return self.bond.fullPriceFromDM(self.settlement_date,
                                             self.next_coupon,
                                             self.current_ibor,
                                             self.future_ibor,
                                             self.discount_margin)
        else:
            raise TuringError('Please check the input of bond_type')

    def principal(self):
        if self.bond_type == 'basal':
            return self.bond.principal(self.settlement_date,
                                       self.yield_to_maturity,
                                       self.convention)
        elif self.bond_type == 'frn':
            return self.bond.principal(self.settlement_date,
                                       self.next_coupon,
                                       self.current_ibor,
                                       self.future_ibor,
                                       self.discount_margin)

    def dollar_duration(self):
        if self.bond_type == 'basal':
            return self.bond.dollarDuration(self.settlement_date,
                                            self.yield_to_maturity,
                                            self.convention)
        elif self.bond_type == 'frn':
            return self.bond.dollarDuration(self.settlement_date,
                                            self.next_coupon,
                                            self.current_ibor,
                                            self.future_ibor,
                                            self.discount_margin)

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
        if self.bond_type == 'basal':
            return self.bond.calcAccruedInterest(self.settlement_date)
        elif self.bond_type == 'frn':
            return self.bond.calcAccruedInterest(self.settlement_date,
                                                 self.next_coupon)


    def dollar_credit_duration(self):
        if self.bond_type == 'frn':
            return self.bond.dollarCreditDuration(self.settlement_date,
                                                  self.next_coupon,
                                                  self.current_ibor,
                                                  self.future_ibor,
                                                  self.discount_margin)

    def macauley_rate_duration(self):
        if self.bond_type == 'frn':
            return self.bond.macauleyRateDuration(self.settlement_date,
                                                  self.next_coupon,
                                                  self.current_ibor,
                                                  self.future_ibor,
                                                  self.discount_margin)

    def modified_rate_duration(self):
        if self.bond_type == 'frn':
            return self.bond.modifiedRateDuration(self.settlement_date,
                                                  self.next_coupon,
                                                  self.current_ibor,
                                                  self.future_ibor,
                                                  self.discount_margin)

    def modified_credit_duration(self):
        if self.bond_type == 'frn':
            return self.bond.modifiedCreditDuration(self.settlement_date,
                                                    self.next_coupon,
                                                    self.current_ibor,
                                                    self.future_ibor,
                                                    self.discount_margin)

    def convexity_from_dm(self):
        if self.bond_type == 'frn':
            return self.bond.convexityFromDM(self.settlement_date,
                                             self.next_coupon,
                                             self.current_ibor,
                                             self.future_ibor,
                                             self.discount_margin)

    def clean_price_from_dm(self):
        if self.bond_type == 'frn':
            return self.bond.cleanPriceFromDM(self.settlement_date,
                                              self.next_coupon,
                                              self.current_ibor,
                                              self.future_ibor,
                                              self.discount_margin)

    def discount_margin(self):
        if self.bond_type == 'frn':
            return self.bond.discountMargin(self.settlement_date,
                                            self.next_coupon,
                                            self.current_ibor,
                                            self.future_ibor,
                                            self.clean_price)
