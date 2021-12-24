from dataclasses import dataclass

from scipy import optimize

from turing_models.instruments.common import newton_fun
from turing_models.instruments.rates.bond import Bond, dy
from turing_models.utilities.day_count import TuringDayCount
from turing_models.utilities.error import TuringError
from turing_models.utilities.helper_functions import to_string
from turing_models.utilities.bond_terms import EcnomicTerms


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class BondFloatingRate(Bond):
    # _next_base_interest_rate: float = None
    ecnomic_terms: EcnomicTerms = None
    dm: float = None

    def __post_init__(self):
        super().__post_init__()
        if self.ecnomic_terms is not None:
            floating_rate_terms = self.ecnomic_terms.data.get('floating_rate_terms')
            if floating_rate_terms is not None:
                self.floating_rate_benchmark = floating_rate_terms.floating_rate_benchmark
                self.floating_spread = floating_rate_terms.floating_spread
                self.floating_adjust_mode = floating_rate_terms.floating_adjust_mode
                self.base_interest_rate = floating_rate_terms.base_interest_rate
        if not self.dm and self.floating_spread:
            self.dm = self.floating_spread
        if self.dm and self.dm > 10.0:
            raise TuringError("Discount margin exceeds 100000bp")

    @property
    def _next_base_interest_rate(self):
        return self.ctx_next_base_interest_rate

    @property
    def _clean_price(self):
        return self.ctx_clean_price or self.clean_price_from_dm()

    def full_price(self):
        return self.full_price_from_dm()

    def clean_price(self):
        return self._clean_price

    def dv01(self):
        current_ibor = self.base_interest_rate
        self.base_interest_rate = current_ibor + dy
        p0 = self.full_price_from_dm()
        self.base_interest_rate = current_ibor - dy
        p2 = self.full_price_from_dm()
        self.base_interest_rate = current_ibor

        dv = (p2 - p0) / 2.0
        return dv

    def dollar_convexity(self):
        """ Calculate the bond convexity from the discount margin (DM) using a
        standard model based on assumptions about future Ibor rates. The
        next Ibor payment which has reset is entered, so to is the current
        Ibor rate from settlement to the next coupon date (NCD). Finally there
        is the level of subsequent future Ibor payments and the discount
        margin. """

        current_ibor = self.base_interest_rate
        self.base_interest_rate = current_ibor - dy
        p0 = self.full_price_from_dm()
        self.base_interest_rate = current_ibor
        p1 = self.full_price_from_dm()
        self.base_interest_rate = current_ibor + dy
        p2 = self.full_price_from_dm()
        self.base_interest_rate = current_ibor

        conv = ((p2 + p0) - 2.0 * p1) / dy / dy
        return conv

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
        (alpha, _, _) = dc.yearFrac(self._settlement_date, self._ncd)
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
            if self._flow_dates[i] > self._settlement_date:
                self._pcd = self._flow_dates[i - 1]
                self._ncd = self._flow_dates[i]
                break

        (acc_factor, num, _) = dc.yearFrac(self._pcd,
                                           self._settlement_date,
                                           self._ncd,
                                           self.pay_interest_cycle)

        self._alpha = 1.0 - acc_factor * self.frequency

        self._accrued_interest = acc_factor * self.par * self.coupon_rate
        self._accrued_days = num
        return self._accrued_interest

    def __repr__(self):
        s = super().__repr__()
        # s += to_string("Quoted Margin", self.floating_spread)
        # s += to_string("Next Coupon", self.coupon_rate)
        # s += to_string("Current Ibor", self.base_interest_rate)
        # s += to_string("Future Ibor", self._next_base_interest_rate)
        s += to_string("Discount Margin", self.dm, "")
        return s
