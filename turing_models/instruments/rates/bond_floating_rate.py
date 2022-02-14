from dataclasses import dataclass

from scipy import optimize

from fundamental.turing_db.data import TuringDB
from fundamental.turing_db.utils import to_turing_date
from turing_models.instruments.common import newton_fun, greek, YieldCurve
from turing_models.instruments.rates.bond import Bond, dy
from turing_models.utilities.day_count import TuringDayCount
from turing_models.utilities.error import TuringError
from turing_models.utilities.bond_terms import EcnomicTerms, FloatingRateTerms


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class BondFloatingRate(Bond):
    ecnomic_terms: EcnomicTerms = None
    dm: float = None

    def __post_init__(self):
        super().__post_init__()

    def _init(self):
        super()._init()
        if self.issue_date:
            self.cv = YieldCurve(value_date=self.value_date, curve_code=self.curve_code, curve_type='ytm')
            if self.curve_code is not None:
                self.cv.resolve()
        if self.ecnomic_terms is not None:
            self.check_ecnomic_terms()
            floating_rate_terms = self.ecnomic_terms.get_instance(FloatingRateTerms)
            if floating_rate_terms is not None:
                self.floating_rate_benchmark = floating_rate_terms.floating_rate_benchmark
                self.floating_spread = floating_rate_terms.floating_spread
                self.floating_adjust_mode = floating_rate_terms.floating_adjust_mode
                self.base_interest_rate = floating_rate_terms.base_interest_rate
        if not self.dm and getattr(self, 'floating_spread', None):
            self.dm = self.floating_spread
        if self.dm and self.dm > 10.0:
            raise TuringError("Discount margin exceeds 100000bp")
        self._get_next_base_interest_rate()

    def _save_original_data(self):
        """ 存储未经ctx修改的属性值，存储在字典中 """
        super()._save_original_data()
        self._original_data['_next_base_interest_rate'] = getattr(self, '_next_base_interest_rate', None)

    def _adjust_data_based_on_ctx(self):
        super()._adjust_data_based_on_ctx()
        ctx_pricing_date = self.ctx_pricing_date
        ctx_next_base_interest_rate = self.ctx_next_base_interest_rate
        ctx_clean_price = self.ctx_clean_price
        ctx_ytm = self.ctx_ytm
        _original_data = self._original_data
        if ctx_pricing_date is not None:
            if ctx_next_base_interest_rate is not None:
                self._next_base_interest_rate = ctx_next_base_interest_rate
            else:
                self._get_next_base_interest_rate()
        else:
            if ctx_next_base_interest_rate is not None:
                self._next_base_interest_rate = ctx_next_base_interest_rate
            else:
                self._next_base_interest_rate = _original_data['_next_base_interest_rate']

        self._clean_price = ctx_clean_price or self.clean_price_from_dm()
        self._ytm = ctx_ytm or (self.discount_margin() + self._next_base_interest_rate)

    def _get_next_base_interest_rate(self):
        if getattr(self, 'floating_rate_benchmark', None) is not None:
            date = self.value_date
            original_data = TuringDB.rate_interest_rate_levels(ir_codes=self.floating_rate_benchmark, date=date)
            if not original_data.empty:
                self._next_base_interest_rate = original_data.loc[self.floating_rate_benchmark, 'rate']
            else:
                raise TuringError(f"Cannot find next base interest rate for {self.floating_rate_benchmark}")

    def full_price(self):
        return self._clean_price + self.calc_accrued_interest()

    def clean_price(self):
        return self._clean_price
    
    def ytm(self):
        return self._ytm

    def dv01(self):
        return greek(self, self.full_price_from_ytm, "_ytm", dy) * -dy

    def dollar_convexity(self):
        """ Calculate the bond convexity from the discount margin (DM) using a
        standard model based on assumptions about future Ibor rates. The
        next Ibor payment which has reset is entered, so to is the current
        Ibor rate from settlement to the next coupon date (NCD). Finally there
        is the level of subsequent future Ibor payments and the discount
        margin. """

        return greek(self, self.full_price_from_ytm, "_ytm", dy, order=2)

    def dollar_credit_duration(self):
        """ Calculate the risk or dP/dy of the bond by bumping. """

        self.calc_accrued_interest()

        dm = self.dm
        self.dm = dm + dy
        p0 = self.full_price_from_dm()
        self.dm = dm
        p2 = self.full_price_from_dm()

        durn = (p2 - p0) / dy
        return durn

    def modified_credit_duration(self):
        """ Calculate the modified duration of the bond on a settlement date
        using standard model based on assumptions about future Ibor rates. The
        next Ibor payment which has reset is entered, so to is the current
        Ibor rate from settlement to the next coupon date (NCD). Finally there
        is the level of subsequent future Ibor payments and the discount
        margin. """

        dd = self.dollar_credit_duration()

        fp = self.full_price_from_dm()
        md = dd / fp
        return md

    def macauley_rate_duration(self):
        """ Calculate the Macauley duration of the FRN on a settlement date
        given its yield to maturity. """

        dd = self.dollar_duration()

        fp = self.full_price_from_dm()

        md = dd * (1.0 + (self.coupon_rate + self.dm) / self.frequency) / fp
        return md

    def modified_duration(self):
        """ Calculate the modified duration of the bond on a settlement date
        using standard model based on assumptions about future Ibor rates. The
        next Ibor payment which has reset is entered, so to is the current
        Ibor rate from settlement to the next coupon date (NCD). Finally there
        is the level of subsequent future Ibor payments and the discount
        margin. """

        dd = self.dollar_duration()

        fp = self.full_price_from_dm()
        md = dd / fp
        return md

    def principal(self):
        """ Calculate the clean trade price of the bond based on the face
        amount from its discount margin and making assumptions about the
        future Ibor rates. """

        full_price = self.full_price_from_dm()

        accrued = self._accrued_interest
        principal = full_price - accrued
        return principal

    def full_price_from_dm(self):
        """ Calculate the full price of the bond from its discount margin (DM)
        using standard model based on assumptions about future Ibor rates. The
        next Ibor payment which has reset is entered, so to is the current
        Ibor rate from settlement to the next coupon date (NCD). Finally there
        is the level of subsequent future Ibor payments and the discount
        margin. """

        self.calc_accrued_interest()

        dc = TuringDayCount(self.interest_rules)

        q = self.floating_spread
        num_flows = len(self._flow_dates)

        # We discount using Libor over the period from settlement to the ncd
        (alpha, _, _) = dc.yearFrac(self.settlement_date, self._ncd)
        df = 1.0 / (1.0 + alpha * (self.base_interest_rate + self.dm))

        # A full coupon is paid
        (alpha, _, _) = dc.yearFrac(self._pcd, self._ncd)
        pv = self.coupon_rate * alpha * df

        # Now do all subsequent coupons that fall after the ncd
        for i_flow in range(1, num_flows):
            
            if self._flow_dates[i_flow] > self._ncd:
                pcd = self._flow_dates[i_flow - 1]
                ncd = self._flow_dates[i_flow]
                (alpha, _, _) = dc.yearFrac(pcd, ncd)
                df = df / (1.0 + alpha * (self._next_base_interest_rate + self.dm))
                c = self._next_base_interest_rate + q
                pv = pv + c * alpha * df

        pv += df
        pv = pv * self.par
        return pv

    def clean_price_from_dm(self):
        """ Calculate the bond clean price from the discount margin
        using standard model based on assumptions about future Ibor rates. The
        next Ibor payment which has reset is entered, so to is the current
        Ibor rate from settlement to the next coupon date (NCD). Finally there
        is the level of subsequent future Ibor payments and the discount
        margin. """

        full_price = self.full_price_from_dm()

        accrued = self.calc_accrued_interest()

        clean_price = full_price - accrued
        return clean_price
    
    def full_price_from_ytm(self):
        ''' Calculate the full price of the bond from its discount margin (DM)
        using standard model based on assumptions about future Ibor rates. The
        next Ibor payment which has reset is entered, so to is the current
        Ibor rate from settlement to the next coupon date (NCD). Finally there
        is the level of subsequent future Ibor payments and the discount
        margin. '''

        self.calc_accrued_interest()

        ytm = self._ytm  # 向量化
        ytm = ytm + 0.000000000012345  # 防止ytm = 0
        dm = self.dm
        self.dm = ytm - self._next_base_interest_rate
        full_price = self.full_price_from_dm()
        self.dm = dm
        return full_price
    
    def clean_price_from_ytm(self):
        ''' Calculate the bond clean price from the discount margin
        using standard model based on assumptions about future Ibor rates. The
        next Ibor payment which has reset is entered, so to is the current
        Ibor rate from settlement to the next coupon date (NCD). Finally there
        is the level of subsequent future Ibor payments and the discount
        margin. '''

        full_price = self.full_price_from_ytm()
        accrued = self.calc_accrued_interest()
        clean_price = full_price - accrued
        return clean_price


    def discount_margin(self):
        """ Calculate the bond's yield to maturity by solving the price
        yield relationship using a one-dimensional root solver. """

        self.calc_accrued_interest()

        # Needs to be adjusted to par notional
        accrued = self._accrued_interest

        full_price = self._clean_price + accrued
        dm_ori = self.dm

        argtuple = (self, full_price, "dm", "full_price_from_dm")

        dm = optimize.newton(newton_fun,
                             x0=0.01,  # initial value of 1%
                             fprime=None,
                             args=argtuple,
                             tol=1e-12,
                             maxiter=50,
                             fprime2=None)

        self.dm = dm_ori
        return dm

    def calc_accrued_interest(self):
        """ Calculate the amount of coupon that has accrued between the
        previous coupon date and the settlement date. Ex-dividend dates are
        not handled. Contact me if you need this functionality. """

        num_flows = len(self._flow_dates)

        if num_flows == 0:
            raise TuringError("Accrued interest - not enough flow dates.")

        dc = TuringDayCount(self.interest_rules)

        for i in range(1, num_flows):
            if self._flow_dates[i] > self.settlement_date:
                self._pcd = self._flow_dates[i - 1]
                self._ncd = self._flow_dates[i]
                break

        (acc_factor, num, _) = dc.yearFrac(self._pcd,
                                           self.settlement_date,
                                           self._ncd,
                                           self.pay_interest_cycle)

        self._alpha = 1.0 - acc_factor * self.frequency

        self._accrued_interest = acc_factor * self.par * self.coupon_rate
        self._accrued_days = num
        return self._accrued_interest

    def check_ecnomic_terms(self):
        """检测ecnomic_terms是否为字典格式，若为字典格式，则处理成EcnomicTerms的实例对象"""
        ecnomic_terms = getattr(self, 'ecnomic_terms', None)
        if ecnomic_terms is not None and isinstance(ecnomic_terms, dict):
            floating_rate_terms = ecnomic_terms.get('floating_rate_terms')
            floating_rate_terms = FloatingRateTerms(**floating_rate_terms)
            ecnomic_terms = EcnomicTerms(floating_rate_terms)
            setattr(self, 'ecnomic_terms', ecnomic_terms)

    def _resolve(self):
        super()._resolve()
        # 对ecnomic_terms属性做单独处理
        self.check_ecnomic_terms()
        self.__post_init__()

    def __repr__(self):
        s = super().__repr__()
        if self.ecnomic_terms:
            s += f'''
{self.ecnomic_terms}'''
        return s
