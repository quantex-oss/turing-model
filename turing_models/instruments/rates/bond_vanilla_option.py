from dataclasses import dataclass
import datetime
import QuantLib as ql
from typing import Union
import numpy as np

from turing_models.instruments.rates.ir_option import IROption
from fundamental.turing_db.data import Turing, TuringDB
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import OptionType
from turing_models.instruments.common import greek, newton_fun, Curve
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.utilities.calendar import TuringCalendar
from turing_models.utilities.day_count import TuringDayCount, DayCountType
from turing_models.utilities.global_types import CouponType, TuringYTMCalcType
from turing_models.market.curves.curve_adjust import CurveAdjustmentImpl

from turing_models.utilities.mathematics import NVect, NPrimeVect
from fundamental.turing_db.bond_data import BondApi
from turing_models.instruments.common import IR, YieldCurveCode, CurveCode, Curve, CurveAdjustment, Currency
from turing_models.utilities.day_count import DayCountType, TuringDayCount
from turing_models.utilities.error import TuringError
from turing_models.utilities.frequency import TuringFrequency, FrequencyType
from turing_models.utilities.global_types import TuringYTMCalcType, CouponType
from turing_models.utilities.helper_functions import to_string, to_datetime, to_turing_date
from turing_models.utilities.global_types import OptionType, TuringExerciseType
from turing_utils.log.request_id_log import logger
from turing_models.instruments.rates.bond_fixed_rate import BondFixedRate
from turing_models.instruments.common import greek, bump, Currency
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
        if original_data is not None:
            data = original_data.loc[self.underlying_comb_symbol].loc[0, 'net_prc']
            return data
        else:
            raise TuringError(f"Cannot find cnbd bond clean price for {self.underlying_comb_symbol}")
        
    @property
    def _bond_spot(self) -> float:
        # return self._spot or self.ctx_spot or self._market_clean_price
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
        self.bond.curve_fitted = CurveAdjustmentImpl(curve_data=self.bond.cv.curve_data,
                                                parallel_shift=self.bond._spread_adjustment,
                                                value_date=self.bond._settlement_date).get_curve_result()
        
        forward_price = (self._bond_spot + self.bond.calc_accrued_interest())
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
        
    # def spot_path(self):
    #     return 'turing_models.instruments.fx.fx.ForeignExchange'

    # def _resolve(self):
    #     if self.asset_id and not self.asset_id.startswith("OPTION_"):
    #         temp_dict = FxOptionApi.fetch_fx_option(
    #             gurl=None, asset_id=self.asset_id)
    #         for k, v in temp_dict.items():
    #             if not getattr(self, k, None) and v:
    #                 setattr(self, k, v)
    #     self.resolve_param()

    # def resolve_param(self):
    #     self.check_underlier()
    #     if not self.product_type:
    #         setattr(self, 'product_type', 'VANILLA')
    #     self.__post_init__()
    
    # def check_param(self):
    #     """将字符串转换为枚举类型"""
    #     if self.underlying_pay_interest_mode:
    #         if not isinstance(self.underlying_pay_interest_mode, CouponType):
    #             rules = {
    #                 "ZERO_COUPON": CouponType.ZERO_COUPON,
    #                 "DISCOUNT": CouponType.DISCOUNT,
    #                 "COUPON_CARRYING": CouponType.COUPON_CARRYING,
    #                 # "OTHERS": None
    #             }
    #             self.underlying_pay_interest_mode = rules.get(self.underlying_pay_interest_mode,
    #                                                TuringError('Please check the input of pay_interest_mode'))
    #             if isinstance(self.underlying_pay_interest_mode, TuringError):
    #                 raise self.underlying_pay_interest_mode

    #     if self.underlying_pay_interest_cycle:
    #         if not isinstance(self.underlying_pay_interest_cycle, FrequencyType):
    #             rules = {
    #                 "ANNUAL": FrequencyType.ANNUAL,
    #                 "SEMI_ANNUAL": FrequencyType.SEMI_ANNUAL,
    #                 # "ONCE_ON_DUE": None,
    #                 "QUARTERLY": FrequencyType.QUARTERLY,
    #                 "MONTHLY": FrequencyType.MONTHLY,
    #                 # "PERIODIC": None,
    #                 "TRI_ANNUAL": FrequencyType.TRI_ANNUAL,
    #                 # "THREE_QUARTERLY": None,
    #                 # "15_DAYS": None,
    #                 # "BIMONTHLY": None,
    #                 # "OTHERS": None
    #             }
    #             self.underlying_pay_interest_cycle = rules.get(self.underlying_pay_interest_cycle,
    #                                                 TuringError('Please check the input of pay_interest_cycle'))
    #             if isinstance(self.underlying_pay_interest_cycle, TuringError):
    #                 raise self.underlying_pay_interest_cycle

        # if self.underlying_interest_rules:
        #     if not isinstance(self.underlying_interest_rules, DayCountType):
        #         rules = {
        #             "ACT/365": DayCountType.ACT_365L,
        #             "ACT/ACT": DayCountType.ACT_ACT_ISDA,
        #             "ACT/360": DayCountType.ACT_360,
        #             "30/360": DayCountType.THIRTY_E_360,
        #             # "ACT/366": None,
        #             "ACT/365F": DayCountType.ACT_365F,
        #             # "AVG/ACT": None
        #         }
        #         self.underlying_interest_rules = rules.get(self.underlying_interest_rules,
        #                                         TuringError('Please check the input of interest_rules'))
        #         if isinstance(self.underlying_interest_rules, TuringError):
        #             raise self.underlying_interest_rules
    
    def _bond_resolve(self):
        if not self.underlying_asset_id:
            asset_id = BondApi.fetch_comb_symbol_to_asset_id(self.underlying_comb_symbol)
            if asset_id:
                setattr(self, 'asset_id', asset_id)
        if self.underlying_asset_id and not self.underlying_asset_id.startswith("Bond_"):  # Bond_ 为自定义时自动生成
            bond = BondApi.fetch_one_bond_orm(asset_id=self.underlying_asset_id)
            for k, v in bond.items():
                try:
                    if getattr(self, k, None) is None and v:
                        setattr(self, k, v)
                except Exception:
                    logger.warning('bond resolve warning')
        if self.underlying_curve_code is not None and self.underlying_curve_name is None:
            curve_name = getattr(CurveCode, self.underlying_curve_code, '')
            setattr(self, 'curve_name', curve_name)
            