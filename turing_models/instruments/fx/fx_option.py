###############################################################################
# ALL CCY RATES MUST BE IN NUM UNITS OF DOMESTIC PER UNIT OF FOREIGN CURRENCY
# SO EURUSD = 1.30 MEANS 1.30 DOLLARS PER EURO SO DOLLAR IS THE DOMESTIC AND
# EUR IS THE FOREIGN CURRENCY
###############################################################################
import datetime
from abc import ABCMeta
from dataclasses import dataclass
from enum import Enum

import numpy as np
import QuantLib as ql
import pandas as pd

from fundamental.turing_db.data import Turing, TuringDB
from turing_models.instruments.common import FX, Currency, CurrencyPair, DiscountCurveType
from turing_models.instruments.core import InstrumentBase
from turing_models.market.curves.curve_generation import DomDiscountCurveGen, ForDiscountCurveGen, FXForwardCurveGen
from turing_models.market.volatility.vol_surface_generation import FXVolSurfaceGen
from turing_models.models.model_volatility_fns import TuringVolFunctionTypes
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import TuringOptionType, TuringExerciseType
from turing_models.utilities.helper_functions import to_string, to_datetime, to_turing_date
from turing_models.utilities.turing_date import TuringDate


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class FXOption(FX, InstrumentBase, metaclass=ABCMeta):
    asset_id: str = None
    product_type: str = None  # VANILLA/Digital
    underlier: str = None
    underlier_symbol: (str, CurrencyPair) = None  # USD/CNY (外币/本币)
    notional: float = None
    notional_currency: (str, Currency) = None
    strike: float = None
    expiry: TuringDate = None
    cut_off_time: TuringDate = None
    exercise_type: (
        str, TuringExerciseType) = TuringExerciseType.EUROPEAN  # EUROPEAN
    option_type: (str, TuringOptionType) = None  # CALL/PUT
    start_date: TuringDate = None
    # 1 unit of foreign in domestic
    premium_currency: (str, Currency) = None
    # spot_days: int = 0
    value_date: TuringDate = TuringDate(
        *(datetime.date.today().timetuple()[:3]))
    volatility: float = None

    def __post_init__(self):
        super().__init__()
        self.check_underlier()
        self.domestic_name = None
        self.foreign_name = None
        self.notional_dom = None
        self.notional_for = None
        if self.expiry and isinstance(self.expiry, TuringDate):
            self.expiry_ql = ql.Date(self.expiry._d, self.expiry._m, self.expiry._y)
            # self.final_delivery = self.expiry.addWeekDays(self.spot_days)
            # if self.final_delivery < self.expiry:
            #     raise TuringError(
            #         "Final delivery date must be on or after expiry.")

        if self.start_date:
            self.start_date_ql = ql.Date(self.start_date._d, self.start_date._m, self.start_date._y)

        if self.underlier_symbol:
            if isinstance(self.underlier_symbol, CurrencyPair):
                self.underlier_symbol = self.underlier_symbol.value
            elif isinstance(self.underlier_symbol, str):
                if len(self.underlier_symbol) != 7:
                    raise TuringError(
                        "Currency pair must be in ***/***format.")
            else:
                raise TuringError('Please check the input of underlier_symbol')

            self.foreign_name = self.underlier_symbol[0:3]
            self.domestic_name = self.underlier_symbol[4:7]

        if self.strike and np.any(self.strike < 0.0):
            raise TuringError("Negative strike.")

        if not self.notional_currency and self.foreign_name:
            self.notional_currency = self.foreign_name

        if self.notional_currency and isinstance(self.notional_currency, Currency):
            self.notional_currency = self.notional_currency.value

        if self.premium_currency and isinstance(self.premium_currency, Currency):
            self.premium_currency = self.premium_currency.value

        if self.domestic_name and self.foreign_name and self.premium_currency and \
                self.premium_currency != self.domestic_name and self.premium_currency != self.foreign_name:
            raise TuringError("Premium currency not in currency pair.")

        if not self.cut_off_time or not isinstance(self.cut_off_time, TuringDate):
            self.cut_off_time = self.expiry

    @property
    def _value_date(self):
        """优先考虑通过what-if传出的估值日期"""
        date = to_turing_date(self.date_for_interface)
        return date if date >= self.start_date else self.start_date

    @property
    def value_date_ql(self):
        return ql.Date(self._value_date._d, self._value_date._m, self._value_date._y)

    @property
    def date_for_interface(self):
        # turing sdk提供的接口支持传datetime.datetime格式的时间或者latest
        if self.ctx_pricing_date is not None:
            if isinstance(self.ctx_pricing_date, str):
                value_date = self.ctx_pricing_date
            else:
                value_date = to_datetime(self.ctx_pricing_date)
            return value_date
        return self.value_date

    @property
    def get_exchange_rate(self):
        """从接口获取汇率"""
        date = self._value_date.datetime()
        original_data = TuringDB.exchange_rate(symbol=self.underlier_symbol, date=date)
        if original_data is not None:
            data = original_data[self.underlier_symbol]
            return data
        else:
            raise TuringError(f"Cannot find exchange rate for {self.underlier_symbol}")

    @property
    def exchange_rate(self):
        """优先考虑通过what-if传出的汇率"""
        return self.ctx_spot or self.get_exchange_rate

    @property
    def get_shibor_data(self):
        """从接口获取shibor"""
        date = self._value_date.datetime()
        original_data = TuringDB.get_global_ibor_curve(ibor_type='Shibor', currency='CNY', start=date, end=date)
        if original_data is not None:
            data = original_data.loc[date]
            return data
        else:
            raise TuringError(f"Cannot find shibor data")

    @property
    def get_shibor_swap_data(self):
        """从接口获取利率互换曲线"""
        date = self._value_date.datetime()
        original_data = Turing.get_irs_curve(ir_type="Shibor3M", currency='CNY', start=date, end=date)
        if original_data is not None:
            data = original_data.loc["Shibor3M"].loc[date]
            return data
        else:
            raise TuringError("Cannot find shibor swap curve data for 'CNY'")

    @property
    def get_shibor_swap_fixing_data(self):
        """参照cicc模型确定数据日期"""
        date1 = '2019-07-05'
        date2 = '2019-07-08'
        date3 = '2019-07-09'
        original_data = TuringDB.get_global_ibor_curve(ibor_type='Shibor', currency='CNY', start=date1, end=date3)
        if original_data is not None:
            rate1 = original_data.loc[datetime.datetime.strptime(date1, '%Y-%m-%d')].loc[4, 'rate']
            rate2 = original_data.loc[datetime.datetime.strptime(date2, '%Y-%m-%d')].loc[4, 'rate']
            rate3 = original_data.loc[datetime.datetime.strptime(date3, '%Y-%m-%d')].loc[4, 'rate']
            fixing_data = {'Date': [date1, date2, date3], 'Fixing': [rate1, rate2, rate3]}
            return fixing_data
        else:
            raise TuringError(f"Cannot find shibor data")

    @property
    def get_fx_swap_data(self):
        """获取外汇掉期曲线"""
        date = self._value_date.datetime()
        original_data = TuringDB.get_fx_swap_curve(currency_pair=self.underlier_symbol, start=date, end=date)
        if original_data is not None:
            data = original_data.loc[self.underlier_symbol].loc[date]
            return data
        else:
            raise TuringError(f"Cannot find fx swap curve data for {self.underlier_symbol}")

    @property
    def get_fx_implied_vol_data(self):
        """获取外汇期权隐含波动率曲线"""
        date = self._value_date.datetime()
        original_data = TuringDB.get_fx_implied_volatility_curve(currency_pair=self.underlier_symbol,
                                                                 volatility_type=["ATM", "25D BF", "25D RR", "10D BF", "10D RR"],
                                                                 start=date,
                                                                 end=date)
        if original_data is not None:
            tenor = original_data.loc[self.underlier_symbol].loc["ATM"].loc[date]['tenor']
            origin_tenor = original_data.loc[self.underlier_symbol].loc["ATM"].loc[date]['origin_tenor']
            atm_vols = original_data.loc[self.underlier_symbol].loc["ATM"].loc[date]['volatility']
            butterfly_25delta_vols = original_data.loc[self.underlier_symbol].loc["25D BF"].loc[date]['volatility']
            risk_reversal_25delta_vols = original_data.loc[self.underlier_symbol].loc["25D RR"].loc[date]['volatility']
            butterfly_10delta_vols = original_data.loc[self.underlier_symbol].loc["10D BF"].loc[date]['volatility']
            risk_reversal_10delta_vols = original_data.loc[self.underlier_symbol].loc["10D RR"].loc[date]['volatility']
            return pd.DataFrame(data={'tenor': tenor,
                                      'origin_tenor': origin_tenor,
                                      "ATM": atm_vols,
                                      "25D BF": butterfly_25delta_vols,
                                      "25D RR": risk_reversal_25delta_vols,
                                      "10D BF": butterfly_10delta_vols,
                                      "10D RR": risk_reversal_10delta_vols})
        else:
            raise TuringError(f"Cannot find fx implied vol data for {self.underlier_symbol}")

    @property
    def domestic_discount_curve(self):
        return DomDiscountCurveGen(value_date=self._value_date,
                                   shibor_tenors=self.get_shibor_data['tenor'].tolist(),
                                   shibor_origin_tenors=self.get_shibor_data['origin_tenor'].tolist(),
                                   shibor_rates=self.get_shibor_data['rate'].tolist(),
                                   shibor_swap_tenors=self.get_shibor_swap_data['tenor'].tolist(),
                                   shibor_swap_origin_tenors=self.get_shibor_swap_data['origin_tenor'].tolist(),
                                   shibor_swap_rates=self.get_shibor_swap_data['average'].tolist(),
                                   shibor_swap_fixing_dates=self.get_shibor_swap_fixing_data['Date'],
                                   shibor_swap_fixing_rates=self.get_shibor_swap_fixing_data['Fixing'],
                                   curve_type=DiscountCurveType.Shibor3M).discount_curve

    @property
    def fx_forward_curve(self):
        return FXForwardCurveGen(value_date=self._value_date,
                                 exchange_rate=self.exchange_rate,
                                 fx_swap_origin_tenors=self.get_fx_swap_data['origin_tenor'].tolist(),
                                 fx_swap_quotes=self.get_fx_swap_data['swap_point'].tolist()).discount_curve

    @property
    def foreign_discount_curve(self):
        return ForDiscountCurveGen(value_date=self._value_date,
                                   domestic_discount_curve=self.domestic_discount_curve,
                                   fx_forward_curve=self.fx_forward_curve,
                                   curve_type=DiscountCurveType.FX_Implied).discount_curve

    @property
    def volatility_surface(self):
        if self.underlier_symbol:
            return FXVolSurfaceGen(value_date=self._value_date,
                                   currency_pair=self.underlier_symbol,
                                   exchange_rate=self.exchange_rate,
                                   domestic_discount_curve=self.domestic_discount_curve,
                                   foreign_discount_curve=self.foreign_discount_curve,
                                   fx_forward_curve=self.fx_forward_curve,
                                   tenors=self.get_fx_implied_vol_data["tenor"].tolist(),
                                   origin_tenors=self.get_fx_implied_vol_data["origin_tenor"].tolist(),
                                   atm_vols=self.get_fx_implied_vol_data["ATM"].tolist(),
                                   butterfly_25delta_vols=self.get_fx_implied_vol_data["25D BF"].tolist(),
                                   risk_reversal_25delta_vols=self.get_fx_implied_vol_data["25D RR"].tolist(),
                                   butterfly_10delta_vols=self.get_fx_implied_vol_data["10D BF"].tolist(),
                                   risk_reversal_10delta_vols=self.get_fx_implied_vol_data["10D RR"].tolist(),
                                   volatility_function_type=TuringVolFunctionTypes.QL).volatility_surface

    @property
    def rd(self):
        return

    @property
    def rf(self):
        return

    @property
    def df_d(self):
        return self.domestic_discount_curve.discount(self.expiry_ql)

    @property
    def df_f(self):
        return self.foreign_discount_curve.discount(self.expiry_ql)

    @property
    def df_fwd(self):
        return self.fx_forward_curve.discount(self.expiry_ql)

    @property
    def volatility_(self):
        v = self.ctx_volatility or self.volatility or self.volatility_surface.interp_vol(self.expiry_ql, self.strike)
        if np.all(v >= 0.0):
            v = np.maximum(v, 1e-10)
            return v
        else:
            raise TuringError("Volatility should not be negative.")

    def vol(self):
        return self.volatility_

    def rate_domestic(self):
        return self.domestic_discount_curve.zeroRate(self.expiry_ql, self.daycount, ql.Continuous).rate()

    def rate_foreign(self):
        return self.foreign_discount_curve.zeroRate(self.expiry_ql, self.daycount, ql.Continuous).rate()

    def spot(self):
        return self.exchange_rate

    def check_underlier(self):
        if self.underlier_symbol and not self.underlier:
            if isinstance(self.underlier_symbol, Enum):
                self.underlier = Turing.get_fx_symbol_to_id(
                    _id=self.underlier_symbol.value).get('asset_id')
            else:
                self.underlier = Turing.get_fx_symbol_to_id(
                    _id=self.underlier_symbol).get('asset_id')

    def __repr__(self):
        s = to_string("Object Type", type(self).__name__)
        s += to_string("Asset Id", self.asset_id)
        s += to_string("Product Type", self.product_type)
        s += to_string("Underlier", self.underlier)
        s += to_string("Underlier Symbol", self.underlier_symbol)
        s += to_string("Notional", self.notional)
        s += to_string("Notional Currency", self.notional_currency)
        s += to_string("Strike", self.strike)
        s += to_string("Expiry", self.expiry)
        s += to_string("Cut Off Time", self.cut_off_time)
        s += to_string("Exercise Type", self.exercise_type)
        s += to_string("Option Type", self.option_type)
        s += to_string("Currency Pair", self.underlier_symbol)
        s += to_string("Start Date", self.start_date)
        s += to_string("Premium Currency", self.premium_currency)
        s += to_string("Exchange Rate", self.exchange_rate)
        s += to_string("Volatility", self.volatility_)
        return s
