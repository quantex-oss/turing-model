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
import pandas as pd

from fundamental.turing_db.data import Turing, TuringDB
from turing_models.instruments.common import FX, Currency, CurrencyPair, DiscountCurveType
from turing_models.instruments.core import InstrumentBase
from turing_models.market.curves.curve_generation import DomDiscountCurveGen, ForDiscountCurveGen, FXForwardCurveGen
from turing_models.market.volatility.vol_surface_generation import FXVolSurfaceGen
from turing_models.models.model_volatility_fns import TuringVolFunctionTypes
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import OptionType, TuringExerciseType
from turing_models.utilities.helper_functions import to_datetime, to_turing_date
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_variables import gDaysInYear


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
    option_type: (str, OptionType) = None  # CALL/PUT
    start_date: TuringDate = None
    # 1 unit of foreign in domestic
    premium_currency: (str, Currency) = None
    spot_days: int = 0
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
            self.notional_for = self.notional
            self.notional_dom = self.notional * self.strike

        if self.notional_currency and isinstance(self.notional_currency, Currency):
            self.notional_currency = self.notional_currency.value
            if self.notional_currency == self.foreign_name:
                self.notional_for = self.notional
                self.notional_dom = self.notional * self.strike
            elif self.notional_currency == self.domestic_name:
                self.notional_for = self.notional / self.strike
                self.notional_dom = self.notional

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
        if getattr(self, '_value_date_', None) is not None:
            return getattr(self, '_value_date_', None)
        date = to_turing_date(self._original_value_date)
        return date if date >= self.start_date else self.start_date
    
    @_value_date.setter
    def _value_date(self, value):
        self._value_date_ = value

    @property
    def _original_value_date(self):
        # turing sdk提供的接口支持传datetime.datetime格式的时间或者latest
        if self.ctx_pricing_date is not None:
            if isinstance(self.ctx_pricing_date, str):
                value_date = self.ctx_pricing_date
            else:
                value_date = to_datetime(self.ctx_pricing_date)
            return value_date
        return self.value_date

    def isvalid(self):
        """提供给turing sdk做过期判断"""

        if getattr(self, '_value_date', '') \
                and getattr(self, 'expiry', '') \
                and getattr(self, '_value_date', '') > \
                    getattr(self, 'expiry', ''):
            return False
        return True

    @property
    def get_exchange_rate(self):
        """从接口获取汇率"""
        if getattr(self, "_exchange_rate", None) is not None:
            return getattr(self, "_exchange_rate", None)
        exchange_rate = self.ctx_exchange_rate(currency_pair=self.underlier_symbol)
        if exchange_rate is not None:
            return exchange_rate
        date = self._original_value_date
        original_data = TuringDB.exchange_rate(symbol=self.underlier_symbol, date=date)
        if original_data is not None:
            data = original_data[self.underlier_symbol]
            self.exchange_rate = data
            return data
        else:
            raise TuringError(f"Cannot find exchange rate for {self.underlier_symbol}")
    
    @get_exchange_rate.setter
    def get_exchange_rate(self, value):
        self._exchange_rate = value

    @property
    def get_shibor_data(self):
        """ 从接口获取shibor """
        shibor_data = self.ctx_global_ibor_curve(ibor_type='Shibor', currency='CNY')
        if shibor_data is not None:
            return pd.DataFrame(shibor_data)
        date = self._original_value_date
        original_data = TuringDB.get_global_ibor_curve(ibor_type='Shibor', currency='CNY', start=date, end=date)
        if not original_data.empty:
            return original_data
        else:
            raise TuringError(f"Cannot find shibor data")

    @property
    def get_shibor_swap_data(self):
        """ 从接口获取利率互换曲线 """
        irs_curve = self.ctx_irs_curve(ir_type="Shibor3M", currency='CNY')
        if irs_curve is not None:
            return pd.DataFrame(irs_curve)
        date = self._original_value_date
        original_data = TuringDB.get_irs_curve(ir_type="Shibor3M", currency='CNY', start=date, end=date)
        if not original_data.empty:
            return original_data.loc["Shibor3M"]
        else:
            raise TuringError("Cannot find shibor swap curve data for 'CNY'")

    @property
    def get_fx_swap_data(self):
        """ 获取外汇掉期曲线 """
        fx_swap_curve = self.ctx_fx_swap_curve(currency_pair=self.underlier_symbol)
        if fx_swap_curve is not None:
            return pd.DataFrame(fx_swap_curve)
        date = self._original_value_date
        original_data = TuringDB.get_fx_swap_curve(currency_pair=self.underlier_symbol, start=date, end=date)
        if not original_data.empty:
            return original_data.loc[self.underlier_symbol]
        else:
            raise TuringError(f"Cannot find fx swap curve data for {self.underlier_symbol}")

    @property
    def get_fx_implied_vol_data(self):
        """ 获取外汇期权隐含波动率曲线 """
        volatility_type = ["ATM", "25D BF", "25D RR", "10D BF", "10D RR"]
        fx_implied_volatility_curve = self.ctx_fx_implied_volatility_curve(currency_pair=self.underlier_symbol,
                                                                           volatility_type=volatility_type)
        if fx_implied_volatility_curve is not None:
            return pd.DataFrame(fx_implied_volatility_curve)
        date = self._original_value_date
        original_data = TuringDB.get_fx_implied_volatility_curve(currency_pair=self.underlier_symbol,
                                                                 volatility_type=volatility_type,
                                                                 start=date,
                                                                 end=date)
        if not original_data.empty:
            tenor = original_data.loc[self.underlier_symbol].loc["ATM"]['tenor']
            origin_tenor = original_data.loc[self.underlier_symbol].loc["ATM"]['origin_tenor']
            atm_vols = original_data.loc[self.underlier_symbol].loc["ATM"]['volatility']
            butterfly_25delta_vols = original_data.loc[self.underlier_symbol].loc["25D BF"]['volatility']
            risk_reversal_25delta_vols = original_data.loc[self.underlier_symbol].loc["25D RR"]['volatility']
            butterfly_10delta_vols = original_data.loc[self.underlier_symbol].loc["10D BF"]['volatility']
            risk_reversal_10delta_vols = original_data.loc[self.underlier_symbol].loc["10D RR"]['volatility']
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
                                   shibor_rates=self.get_shibor_data['rate'].tolist(),
                                   shibor_swap_tenors=self.get_shibor_swap_data['tenor'].tolist(),
                                   shibor_swap_rates=self.get_shibor_swap_data['average'].tolist(),
                                   curve_type=DiscountCurveType.Shibor3M_tr).discount_curve

    @property
    def fx_forward_curve(self):
        return FXForwardCurveGen(value_date=self._value_date,
                                 exchange_rate=self.get_exchange_rate,
                                 fx_swap_tenors=self.get_fx_swap_data['tenor'].tolist(),
                                 fx_swap_quotes=self.get_fx_swap_data['swap_point'].tolist()).discount_curve

    @property
    def foreign_discount_curve(self):
        return ForDiscountCurveGen(value_date=self._value_date,
                                   domestic_discount_curve=self.domestic_discount_curve,
                                   fx_forward_curve=self.fx_forward_curve,
                                   curve_type=DiscountCurveType.FX_Implied_tr).discount_curve

    @property
    def volatility_surface(self):
        if self.underlier_symbol:
            return FXVolSurfaceGen(value_date=self._value_date,
                                   currency_pair=self.underlier_symbol,
                                   exchange_rate=self.get_exchange_rate,
                                   domestic_discount_curve=self.domestic_discount_curve,
                                   foreign_discount_curve=self.foreign_discount_curve,
                                   tenors=self.get_fx_implied_vol_data["tenor"].tolist(),
                                   atm_vols=self.get_fx_implied_vol_data["ATM"].tolist(),
                                   butterfly_25delta_vols=self.get_fx_implied_vol_data["25D BF"].tolist(),
                                   risk_reversal_25delta_vols=self.get_fx_implied_vol_data["25D RR"].tolist(),
                                   butterfly_10delta_vols=self.get_fx_implied_vol_data["10D BF"].tolist(),
                                   risk_reversal_10delta_vols=self.get_fx_implied_vol_data["10D RR"].tolist(),
                                   volatility_function_type=TuringVolFunctionTypes.VANNA_VOLGA).volatility_surface

    @property
    def df_d(self):
        return self.domestic_discount_curve.df(self.expiry)
    
    @property
    def rd(self):
        return self.domestic_discount_curve.zeroRate(self.expiry)
    
    @property
    def tdel(self):
        self.final_delivery = self.expiry.addWeekDays(self.spot_days)
        spot_date = self._value_date.addWeekDays(self.spot_days)
        td = (self.final_delivery - spot_date) / gDaysInYear
        td = np.maximum(td, 1e-10)
        return td

    @property
    def texp(self):
        return (self.cut_off_time - self._value_date) / gDaysInYear

    @property
    def df_f(self):
        return self.foreign_discount_curve.df(self.expiry)
    
    @property
    def rf(self):
        return self.foreign_discount_curve.zeroRate(self.expiry)

    @property
    def df_fwd(self):
        return self.fx_forward_curve.df(self.expiry)

    @property
    def volatility_(self):
        if getattr(self, '_volatility', None) is not None:
            return getattr(self, '_volatility', None)
        v = self.ctx_volatility(self.underlier_symbol) or self.volatility or self.volatility_surface.volatilityFromStrikeDate(self.strike, self.expiry)
        if np.all(v >= 0.0):
            v = np.maximum(v, 1e-10)
            return v
        else:
            raise TuringError("Volatility should not be negative.")
    
    @volatility_.setter
    def volatility_(self, value):
        self._volatility = value

    def vol(self):
        return self.volatility_

    def spot(self):
        return self.get_exchange_rate

    def check_underlier(self):
        if self.underlier_symbol and not self.underlier:
            if isinstance(self.underlier_symbol, Enum):
                self.underlier = TuringDB.get_asset(
                    comb_symbols=self.underlier_symbol.value)[0].get('asset_id')
            else:
                self.underlier = Turing.get_asset(
                    comb_symbols=self.underlier_symbol)[0].get('asset_id')

    def __repr__(self):
        s = f'''Class Name: {type(self).__name__}
Asset Id: {self.asset_id}
Product Type: {self.product_type}
Underlier: {self.underlier}
Underlier Symbol: {self.underlier_symbol}
Notional: {self.notional}
Notional Currency: {self.notional_currency}
Strike: {self.strike}
Expiry: {self.expiry}
Cut Off Time: {self.cut_off_time}
Exercise Type: {self.exercise_type}
Option Type: {self.option_type}
Currency Pair: {self.underlier_symbol}
Start Date: {self.start_date}
Premium Currency: {self.premium_currency}'''
        return s
