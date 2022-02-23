from dataclasses import dataclass
import datetime
from typing import Union

import QuantLib as ql
import numpy as np

from fundamental.turing_db.data import TuringDB
from turing_models.instruments.rates.ir_option import IROption
from turing_models.market.curves.curve_adjust import CurveAdjustmentImpl
from turing_models.utilities.mathematics import NVect
from turing_models.instruments.common import YieldCurveCode
from turing_models.utilities.day_count import DayCountType, TuringDayCount
from turing_models.utilities.error import TuringError
from turing_models.utilities.frequency import FrequencyType
from turing_models.utilities.global_types import CouponType
from turing_models.utilities.helper_functions import greek
from turing_models.utilities.global_types import OptionType
from turing_models.instruments.rates.bond_fixed_rate import BondFixedRate
from turing_models.instruments.common import bump, Currency
from turing_models.utilities.global_variables import gDaysInYear


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class BondVanillaOption(IROption):

    calendar = ql.China(ql.China.IB)
    daycount = ql.Actual365Fixed()
    convention = ql.Following
    underlying_asset_name: str = None
    underlying_asset_type: str = None
    underlying_trd_curr_code: Union[str, Currency] = None
    underlying_exchange: str = None
    underlying_issuer_id: str = None
    underlying_issuer: str = None
    underlying_issue_date: datetime.datetime = None  # 发行日
    underlying_due_date: datetime.datetime = None  # 到期日
    underlying_par: float = None  # 面值
    underlying_coupon_rate: float = None
    underlying_interest_rate_type: str = None
    underlying_pay_interest_cycle: (str, FrequencyType) = None  # 付息频率
    underlying_interest_rules: (str, DayCountType) = None  # 计息类型
    underlying_pay_interest_mode: (str, CouponType) = None  # 付息方式
    underlying_curve_code: Union[str, YieldCurveCode] = None  # 曲线编码
    underlying_curve_name: str = None

    def __post_init__(self):
        super().__post_init__()
        self.bond = BondFixedRate(comb_symbol=self.underlying_comb_symbol,
                                                 value_date=self._value_date,
                                                 issue_date=self.underlying_issue_date,
                                                 due_date=self.underlying_due_date,
                                                 pay_interest_cycle=self.underlying_pay_interest_cycle,
                                                 pay_interest_mode=self.underlying_pay_interest_mode,
                                                 interest_rules=self.underlying_interest_rules,
                                                 coupon_rate=self.underlying_coupon_rate,
                                                 par=self.underlying_par,
                                                 curve_code=self.underlying_curve_code)
        if self.notional is not None and self.number_of_options is None:
            self.number_of_options = self.notional / self._bond_spot
        
    @property
    def _market_clean_price(self):
        date = self.date_for_interface.datetime()
        original_data = TuringDB.get_bond_valuation_cnbd_history(symbols=self.underlying_comb_symbol, start=date, end=date)
        if not original_data.empty:
            data = original_data.loc[self.underlying_comb_symbol].loc[0, 'net_prc']
            return data
        else:
            raise TuringError(f"Cannot find cnbd bond clean price for {self.underlying_comb_symbol}")
        
    @property
    def _bond_spot(self) -> float:
        return 103.2643

    @_bond_spot.setter
    def _bond_spot(self, value: float):
        self._spot = value
    
    @property
    def v(self) -> float:
        return self._vol or self.volatility_
    @v.setter
    def v(self, value: float):
        self._vol = value

    @property
    def option_type_(self):
        if self.option_type == "CALL" or self.option_type == "call" or self.option_type == OptionType.CALL:
            return "call"
        elif self.option_type == "PUT" or self.option_type == "put" or self.option_type == OptionType.PUT:
            return "put"
        else:
            raise TuringError('Please check the input of option_type')
        
    def price(self):
        if not self.bond.isvalid():
            raise TuringError("Bond settles after it matures.")
        self.bond._curve_resolve()  # 要调用曲线对象前需要先调用curve_resolve，用以兼容what-if
        self.bond.fitted_curve = CurveAdjustmentImpl(curve_data=self.bond.cv.curve_data,
                                                     parallel_shift=self.bond._spread_adjustment,
                                                     value_date=self.bond.settlement_date).get_curve_result()
        
        forward_price = self._bond_spot + self.bond._accrued_interest
        dc = TuringDayCount(DayCountType.ACT_ACT_ISDA)
        for dt in self.bond._flow_dates[1:]:
            # 将结算日的票息加入计算
            if self._value_date <= dt < self.expiry:
                df = self.discount_curve_rf.df(dt)
                if self.bond.pay_interest_mode == CouponType.COUPON_CARRYING:
                    flow = self.bond.coupon_rate / self.bond.frequency
                    pv = flow * df * self.bond.par
                    forward_price = forward_price - pv
                    k_accrual = self.bond.coupon_rate * dc.yearFrac(dt, self.expiry)[0]
                else:
                    flow = self.bond._flow_amounts[-1]
                    pv = flow * df * self.bond.par
                    forward_price = forward_price - pv
                    k_accrual = self.bond.coupon_rate * dc.yearFrac(dt, self.expiry)[0]
        if k_accrual:
            self.strike = self.strike + k_accrual * self.bond.par
        df_at_maturity = self.discount_curve_rf.df(self.expiry)
        forward_price = forward_price / df_at_maturity
        
        if self.option_type == 'call':
            phi = 1.0
        elif self.option_type == 'put':
            phi = -1.0
        else:
            raise TuringError("Unknown option type value")

        vsqrtT = self.volatility_ * np.sqrt(self.time_to_maturity_in_year())
        d1 = np.log(forward_price/self.strike) / vsqrtT + vsqrtT / 2.0
        d2 = d1 - vsqrtT

        value = phi * forward_price * NVect(phi*d1) - \
            phi * self.strike * NVect(phi*d2)
        return value * self.number_of_options
    
    def bond_delta(self) -> float:
        return greek(self, self.price, "_bond_spot", bump=1)

    def bond_gamma(self) -> float:
        return greek(self, self.price, "_bond_spot", bump=1, order=2)

    def bond_vega(self) -> float:
        return greek(self, self.price, "v", bump=1e-2)

    def bond_theta(self) -> float:
        day_diff = 1
        bump_local = day_diff / gDaysInYear
        return greek(self, self.price, "_value_date", bump=bump_local,
                     cus_inc=(self._value_date.addDays, day_diff))

    def bond_rho(self) -> float:
        return greek(self, self.price, "discount_curve_rf",
                     cus_inc=(self.discount_curve_rf.bump, bump))
            