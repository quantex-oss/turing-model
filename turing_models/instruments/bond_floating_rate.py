from dataclasses import dataclass

from scipy import optimize

from turing_models.utilities.day_count import TuringDayCount
from turing_models.instruments.bond import Bond, dy


def _f(dm, *args):
    """ Function used to do solve root search in DM calculation """

    self = args[0]
    full_price = args[1]
    self.dm = dm
    px = self.full_price_from_dm()
    obj_fn = px - full_price
    return obj_fn


@dataclass
class BondFloatingRate(Bond):
    quoted_margin: float = None
    next_coupon: float = None
    current_ibor: float = None
    future_ibor: float = None
    dm: float = None

    def __post_init__(self):
        super().__post_init__()

        if self.dm > 10.0:
            raise Exception("Discount margin exceeds 100000bp")

    def dv01(self):
        current_ibor = self.current_ibor
        self.current_ibor = current_ibor + dy
        p0 = self.full_price_from_dm()
        self.current_ibor = current_ibor - dy
        p2 = self.full_price_from_dm()
        self.current_ibor = current_ibor

        dv = (p2 - p0) / 2.0
        return dv

    def dollar_convexity(self):
        ''' Calculate the bond convexity from the discount margin (DM) using a
        standard model based on assumptions about future Ibor rates. The
        next Ibor payment which has reset is entered, so to is the current
        Ibor rate from settlement to the next coupon date (NCD). Finally there
        is the level of subsequent future Ibor payments and the discount
        margin. '''

        current_ibor = self.current_ibor
        self.current_ibor = current_ibor - dy
        p0 = self.full_price_from_dm()
        self.current_ibor = current_ibor
        p1 = self.full_price_from_dm()
        self.current_ibor = current_ibor + dy
        p2 = self.full_price_from_dm()
        self.current_ibor = current_ibor

        conv = ((p2 + p0) - 2.0 * p1) / dy / dy
        return conv

    def dollar_credit_duration(self):
        ''' Calculate the risk or dP/dy of the bond by bumping. '''

        self.calc_accrued_interest()

        dm = self.dm
        self.dm = dm + dy
        p0 = self.full_price_from_dm()
        self.dm = dm
        p2 = self.full_price_from_dm()

        durn = (p2 - p0) / dy
        return durn

    def modified_credit_duration(self):
        ''' Calculate the modified duration of the bond on a settlement date
        using standard model based on assumptions about future Ibor rates. The
        next Ibor payment which has reset is entered, so to is the current
        Ibor rate from settlement to the next coupon date (NCD). Finally there
        is the level of subsequent future Ibor payments and the discount
        margin. '''

        dd = self.dollar_credit_duration()

        fp = self.full_price_from_dm()
        md = dd / fp
        return md

    def macauley_rate_duration(self):
        ''' Calculate the Macauley duration of the FRN on a settlement date
        given its yield to maturity. '''

        dd = self.dollar_duration()

        fp = self.full_price_from_dm()

        md = dd * (1.0 + (self.next_coupon + self.dm) / self.frequency) / fp
        return md

    def modified_rate_duration(self):
        ''' Calculate the modified duration of the bond on a settlement date
        using standard model based on assumptions about future Ibor rates. The
        next Ibor payment which has reset is entered, so to is the current
        Ibor rate from settlement to the next coupon date (NCD). Finally there
        is the level of subsequent future Ibor payments and the discount
        margin. '''

        dd = self.dollar_duration()

        fp = self.full_price_from_dm()
        md = dd / fp
        return md

    def principal(self):
        ''' Calculate the clean trade price of the bond based on the face
        amount from its discount margin and making assumptions about the
        future Ibor rates. '''

        full_price = self.full_price_from_dm()

        accrued = self._accrued_interest
        principal = full_price * self.face_amount / self.par - accrued
        return principal

    def full_price_from_dm(self):
        ''' Calculate the full price of the bond from its discount margin (DM)
        using standard model based on assumptions about future Ibor rates. The
        next Ibor payment which has reset is entered, so to is the current
        Ibor rate from settlement to the next coupon date (NCD). Finally there
        is the level of subsequent future Ibor payments and the discount
        margin. '''

        self.calc_accrued_interest()

        dc = TuringDayCount(self.accrual_type_)

        q = self.quoted_margin
        num_flows = len(self._flow_dates)

        # We discount using Libor over the period from settlement to the ncd
        (alpha, _, _) = dc.yearFrac(self.settlement_date_, self._ncd)
        df = 1.0 / (1.0 + alpha * (self.current_ibor + self.dm))

        # A full coupon is paid
        (alpha, _, _) = dc.yearFrac(self._pcd, self._ncd)
        pv = self.next_coupon * alpha * df

        # Now do all subsequent coupons that fall after the ncd
        for i_flow in range(1, num_flows):

            if self._flow_dates[i_flow] > self._ncd:

                pcd = self._flow_dates[i_flow-1]
                ncd = self._flow_dates[i_flow]
                (alpha, _, _) = dc.yearFrac(pcd, ncd)

                df = df / (1.0 + alpha * (self.future_ibor + self.dm))
                c = self.future_ibor + q
                pv = pv + c * alpha * df

        pv += df
        pv = pv * self.par
        return pv

    def clean_price_from_dm(self):
        ''' Calculate the bond clean price from the discount margin
        using standard model based on assumptions about future Ibor rates. The
        next Ibor payment which has reset is entered, so to is the current
        Ibor rate from settlement to the next coupon date (NCD). Finally there
        is the level of subsequent future Ibor payments and the discount
        margin. '''

        full_price = self.full_price_from_dm()

        accrued = self.calc_accrued_interest()
        accrued = accrued * self.par / self.face_amount

        clean_price = full_price - accrued
        return clean_price

    def discount_margin(self):
        ''' Calculate the bond's yield to maturity by solving the price
        yield relationship using a one-dimensional root solver. '''

        self.calc_accrued_interest()

        # Needs to be adjusted to par notional
        accrued = self._accrued_interest * self.par / self.face_amount

        full_price = self.clean_price + accrued
        dm_ori = self.dm

        argtuple = (self, full_price)

        dm = optimize.newton(_f,
                             x0=0.01,  # initial value of 1%
                             fprime=None,
                             args=argtuple,
                             tol=1e-12,
                             maxiter=50,
                             fprime2=None)

        self.dm = dm_ori
        return dm

    def calc_accrued_interest(self):
        ''' Calculate the amount of coupon that has accrued between the
        previous coupon date and the settlement date. Ex-dividend dates are
        not handled. Contact me if you need this functionality. '''

        num_flows = len(self._flow_dates)

        if num_flows == 0:
            raise Exception("Accrued interest - not enough flow dates.")

        dc = TuringDayCount(self.accrual_type_)

        for i in range(1, num_flows):
            if self._flow_dates[i] > self.settlement_date_:
                self._pcd = self._flow_dates[i-1]
                self._ncd = self._flow_dates[i]
                break

        (acc_factor, num, _) = dc.yearFrac(self._pcd,
                                           self.settlement_date_,
                                           self._ncd,
                                           self.freq_type_)

        self._alpha = 1.0 - acc_factor * self.frequency

        self._accrued_interest = acc_factor * self.face_amount * self.next_coupon
        self._accrued_days = num
        return self._accrued_interest
