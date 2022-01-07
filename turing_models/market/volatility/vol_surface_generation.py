import copy
import datetime
from typing import List, Union

import numpy as np
import pandas as pd
import QuantLib as ql

from fundamental.turing_db.data import TuringDB
from turing_models.instruments.common import CurrencyPair, DiscountCurveType, Ctx
from turing_models.instruments.common import TuringFXATMMethod, TuringFXDeltaMethod
from turing_models.market.curves.curve_generation import ForDiscountCurveGen, DomDiscountCurveGen, \
     FXForwardCurveGen
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.market.volatility.fx_vol_surface_ql import FXVolSurface
from turing_models.market.volatility.fx_vol_surface_ql_real_time import FXVolSurface as FXVolSurfaceRealTime
from turing_models.market.volatility.fx_vol_surface_vv import TuringFXVolSurfaceVV
from turing_models.models.model_volatility_fns import TuringVolFunctionTypes
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import TuringSolverTypes
from turing_models.utilities.helper_classes import Base
from turing_models.utilities.helper_functions import to_datetime, datetime_to_turingdate
from turing_models.utilities.turing_date import TuringDate


class FXOptionImpliedVolatilitySurface(Base, Ctx):
    fx_symbol: Union[str, CurrencyPair] = CurrencyPair.USDCNY  # 货币对symbol，例如：'USD/CNY'
    value_date: Union[str, datetime.datetime, datetime.date] = datetime.datetime.today()
    strikes: List[float] = None                                # 行权价 如果不传，就用exchange_rate * np.linspace(0.8, 1.2, 16)
    tenors: List[float] = None                                 # 期限（年化） 如果不传，就用[1/12, 2/12, 0.25, 0.5, 1, 2]
    volatility_function_type: Union[str, TuringVolFunctionTypes] = TuringVolFunctionTypes.QL

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.check_param()

    def check_param(self):
        """ 数据格式转换 """
        if isinstance(self.fx_symbol, CurrencyPair):
            self.fx_symbol = self.fx_symbol.value
        elif not isinstance(self.fx_symbol, str):
            raise TuringError('fx_symbol: (str, CurrencyPair)')
        if self.value_date is not None:
            self.value_date = to_datetime(self.value_date)
        if self.volatility_function_type is not None:
            if not isinstance(self.volatility_function_type, TuringVolFunctionTypes):
                rules = {
                    "QL": TuringVolFunctionTypes.QL
                }
                self.volatility_function_type = rules.get(
                    self.volatility_function_type,
                    TuringError('Please check the input of volatility_function_type')
                )
                if isinstance(self.volatility_function_type, TuringError):
                    raise self.volatility_function_type

    @property
    def _value_date(self):
        if self.ctx_pricing_date is not None:
            if isinstance(self.ctx_pricing_date, TuringDate):
                return to_datetime(self.ctx_pricing_date)
        return self.value_date

    @property
    def get_exchange_rate(self):
        """从接口获取汇率"""
        date = self._value_date
        original_data = TuringDB.exchange_rate(symbol=self.fx_symbol, date=date)
        if original_data is not None:
            data = original_data[self.fx_symbol]
            return data
        else:
            raise TuringError(f"Cannot find exchange rate for {self.fx_symbol}")

    @property
    def get_shibor_data(self):
        """ 从接口获取shibor """
        date = self._value_date
        original_data = TuringDB.get_global_ibor_curve(ibor_type='Shibor', currency='CNY', start=date, end=date)
        if original_data is not None:
            data = original_data.loc[date]
            return data
        else:
            raise TuringError(f"Cannot find shibor data")

    @property
    def get_shibor_swap_data(self):
        """ 从接口获取利率互换曲线 """
        date = self._value_date
        original_data = TuringDB.get_irs_curve(ir_type="Shibor3M", currency='CNY', start=date, end=date)
        if original_data is not None:
            data = original_data.loc["Shibor3M"].loc[date]
            return data
        else:
            raise TuringError("Cannot find shibor swap curve data for 'CNY'")

    @property
    def get_shibor_swap_fixing_data(self):
        """ 参照cicc模型确定数据日期 """
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
        """ 获取外汇掉期曲线 """
        date = self._value_date
        original_data = TuringDB.get_fx_swap_curve(currency_pair=self.fx_symbol, start=date, end=date)
        if original_data is not None:
            data = original_data.loc[self.fx_symbol].loc[date]
            return data
        else:
            raise TuringError(f"Cannot find fx swap curve data for {self.fx_symbol}")

    @property
    def get_fx_implied_vol_data(self):
        """ 获取外汇期权隐含波动率曲线 """
        date = self._value_date
        original_data = TuringDB.get_fx_implied_volatility_curve(currency_pair=self.fx_symbol,
                                                                 volatility_type=["ATM", "25D BF", "25D RR", "10D BF", "10D RR"],
                                                                 start=date,
                                                                 end=date)
        if original_data is not None:
            tenor = original_data.loc[self.fx_symbol].loc["ATM"].loc[date]['tenor']
            origin_tenor = original_data.loc[self.fx_symbol].loc["ATM"].loc[date]['origin_tenor']
            atm_vols = original_data.loc[self.fx_symbol].loc["ATM"].loc[date]['volatility']
            butterfly_25delta_vols = original_data.loc[self.fx_symbol].loc["25D BF"].loc[date]['volatility']
            risk_reversal_25delta_vols = original_data.loc[self.fx_symbol].loc["25D RR"].loc[date]['volatility']
            butterfly_10delta_vols = original_data.loc[self.fx_symbol].loc["10D BF"].loc[date]['volatility']
            risk_reversal_10delta_vols = original_data.loc[self.fx_symbol].loc["10D RR"].loc[date]['volatility']
            return pd.DataFrame(data={'tenor': tenor,
                                      'origin_tenor': origin_tenor,
                                      "ATM": atm_vols,
                                      "25D BF": butterfly_25delta_vols,
                                      "25D RR": risk_reversal_25delta_vols,
                                      "10D BF": butterfly_10delta_vols,
                                      "10D RR": risk_reversal_10delta_vols})
        else:
            raise TuringError(f"Cannot find fx implied vol data for {self.fx_symbol}")

    @property
    def domestic_discount_curve(self):
        return DomDiscountCurveGen(value_date=datetime_to_turingdate(self._value_date),
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
        return FXForwardCurveGen(value_date=datetime_to_turingdate(self._value_date),
                                 exchange_rate=self.get_exchange_rate,
                                 fx_swap_origin_tenors=self.get_fx_swap_data['origin_tenor'].tolist(),
                                 fx_swap_quotes=self.get_fx_swap_data['swap_point'].tolist()).discount_curve

    @property
    def foreign_discount_curve(self):
        return ForDiscountCurveGen(value_date=datetime_to_turingdate(self._value_date),
                                   domestic_discount_curve=self.domestic_discount_curve,
                                   fx_forward_curve=self.fx_forward_curve,
                                   curve_type=DiscountCurveType.FX_Implied).discount_curve

    @property
    def volatility_surface(self):
        if self.volatility_function_type == TuringVolFunctionTypes.QL:
            return FXVolSurfaceGen(value_date=datetime_to_turingdate(self._value_date),
                                   currency_pair=self.fx_symbol,
                                   exchange_rate=self.get_exchange_rate,
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

    def get_vol_surface(self):
        """获取波动率曲面的DataFrame"""
        if self.strikes is not None:
            self.strikes = np.array(self.strikes)
        else:
            strike_percent = np.linspace(0.8, 1.2, 16)
            self.strikes = self.get_exchange_rate * strike_percent

        if self.tenors is None:
            self.tenors = [1 / 12, 2 / 12, 0.25, 0.5, 1, 2]

        expiry = datetime_to_turingdate(self._value_date).addYears(self.tenors)
        data = {}
        tenors = self.tenors
        strikes = self.strikes
        volatility_surface = self.volatility_surface
        volatility_function_type = self.volatility_function_type
        for strike in strikes:
            data[strike] = []
            for i in range(len(tenors)):
                ex = expiry[i]
                if volatility_function_type == TuringVolFunctionTypes.VANNA_VOLGA:
                    v = volatility_surface.volatilityFromStrikeDate(strike, ex)
                elif volatility_function_type == TuringVolFunctionTypes.QL:
                    ex_ql = ql.Date(ex._d, ex._m, ex._y)
                    v = volatility_surface.interp_vol(ex_ql, strike)
                else:
                    raise TuringError('Unsupported volatility function type')
                data[strike].append(v)
        data_df = pd.DataFrame(data, index=tenors)
        data_df.index.name = 'tenor'
        data_df.columns.name = 'strike'
        return data_df

    def generate_data(self):
        """ 提供给定价服务调用 """
        original_data = self.get_vol_surface().to_dict()
        surface_data = []
        for strike, value in original_data.items():
            value_list = []
            for tenor, rate in value.items():
                value_list.append({"tenor": tenor, "rate": rate})
            surface_data.append({"strike": strike, "value": copy.deepcopy(value_list)})
        return surface_data


class FXVolSurfaceGen:
    def __init__(self,
                 value_date: Union[TuringDate, ql.Date],
                 currency_pair: Union[str, CurrencyPair],
                 exchange_rate: float,
                 domestic_discount_curve: TuringDiscountCurve = None,
                 foreign_discount_curve: TuringDiscountCurve = None,
                 fx_forward_curve=None,
                 tenors: List[float] = None,
                 origin_tenors: List[str] = None,
                 vol_dates: List[str] = None,
                 atm_vols: List[float] = None,
                 butterfly_25delta_vols: List[float] = None,
                 risk_reversal_25delta_vols: List[float] = None,
                 butterfly_10delta_vols: List[float] = None,
                 risk_reversal_10delta_vols: List[float] = None,
                 volatility_function_type: TuringVolFunctionTypes = TuringVolFunctionTypes.QL,
                 calendar=ql.China(ql.China.IB),
                 convention=ql.Following,
                 day_count=ql.Actual365Fixed(),
                 alpha: float = 1,
                 atm_method: TuringFXATMMethod = TuringFXATMMethod.FWD_DELTA_NEUTRAL,
                 delta_method: TuringFXDeltaMethod = TuringFXDeltaMethod.SPOT_DELTA,
                 solver_type: TuringSolverTypes = TuringSolverTypes.NELDER_MEAD,
                 tol: float = 1e-8):

        if isinstance(value_date, ql.Date):
            self.value_date_turing = TuringDate(value_date.year(), value_date.month(), value_date.dayOfMonth())
            self.value_date_ql = value_date
        elif isinstance(value_date, TuringDate):
            self.value_date_turing = value_date
            self.value_date_ql = ql.Date(value_date._d, value_date._m, value_date._y)
        else:
            raise TuringError('value_date: (TuringDate, ql.Date)')

        if isinstance(currency_pair, CurrencyPair):
            self.currency_pair = currency_pair.value
        elif isinstance(currency_pair, str):
            if len(currency_pair) != 7:
                raise TuringError("Currency pair must be in ***/***format.")
            self.currency_pair = currency_pair
        else:
            raise TuringError('currency_pair: (str, CurrencyPair)')

        self.exchange_rate = exchange_rate

        self.domestic_discount_curve = domestic_discount_curve
        self.foreign_discount_curve = foreign_discount_curve
        self.fx_forward_curve = fx_forward_curve

        self.tenors = tenors
        self.origin_tenors = origin_tenors
        self.vol_dates = vol_dates
        self.atm_vols = atm_vols
        self.butterfly_25delta_vols = butterfly_25delta_vols
        self.risk_reversal_25delta_vols = risk_reversal_25delta_vols
        self.butterfly_10delta_vols = butterfly_10delta_vols
        self.risk_reversal_10delta_vols = risk_reversal_10delta_vols

        self.calendar = calendar
        self.convention = convention
        self.daycount = day_count

        self.alpha = alpha
        self.atm_method = atm_method
        self.delta_method = delta_method
        self.volatility_function_type = volatility_function_type
        self.solver_type = solver_type
        self.tol = tol

    @property
    def volatility_surface(self):
        """根据volatility function type区分初始化不同的曲面"""
        if self.volatility_function_type == TuringVolFunctionTypes.VANNA_VOLGA:
            return TuringFXVolSurfaceVV(self.value_date_turing,
                                        self.exchange_rate,
                                        self.currency_pair,
                                        self.domestic_discount_curve,
                                        self.foreign_discount_curve,
                                        self.tenors,
                                        self.atm_vols,
                                        self.butterfly_25delta_vols,
                                        self.risk_reversal_25delta_vols,
                                        self.butterfly_10delta_vols,
                                        self.risk_reversal_10delta_vols,
                                        self.alpha,
                                        self.atm_method,
                                        self.delta_method,
                                        self.volatility_function_type,
                                        self.solver_type,
                                        self.tol)

        elif self.volatility_function_type == TuringVolFunctionTypes.QL:
            ql.Settings.instance().evaluationDate = self.value_date_ql
            foreign_name = self.currency_pair[0:3]
            domestic_name = self.currency_pair[4:7]
            if self.vol_dates is not None:
                data_dict = {'Tenor': self.origin_tenors,
                             'Date': self.vol_dates,
                             'ATM': self.atm_vols,
                             '25DRR': self.risk_reversal_25delta_vols,
                             '25DBF': self.butterfly_25delta_vols,
                             '10DRR': self.risk_reversal_10delta_vols,
                             '10DBF': self.butterfly_10delta_vols}

                vol_data = pd.DataFrame(data_dict)

                return FXVolSurfaceRealTime(vol_data,
                                            domestic_name,
                                            foreign_name,
                                            self.exchange_rate,
                                            self.fx_forward_curve,
                                            self.domestic_discount_curve,
                                            self.foreign_discount_curve,
                                            self.value_date_ql,
                                            self.calendar,
                                            self.convention,
                                            self.daycount,
                                            True)
            else:
                data_dict = {'Tenor': self.origin_tenors,
                             'ATM': self.atm_vols,
                             '25DRR': self.risk_reversal_25delta_vols,
                             '25DBF': self.butterfly_25delta_vols,
                             '10DRR': self.risk_reversal_10delta_vols,
                             '10DBF': self.butterfly_10delta_vols}

                vol_data = pd.DataFrame(data_dict)

                return FXVolSurface(vol_data,
                                    domestic_name,
                                    foreign_name,
                                    self.exchange_rate,
                                    self.fx_forward_curve,
                                    self.domestic_discount_curve,
                                    self.foreign_discount_curve,
                                    self.value_date_ql,
                                    self.calendar,
                                    self.convention,
                                    self.daycount,
                                    True)


if __name__ == '__main__':
    fx_vol_surface = FXOptionImpliedVolatilitySurface(
        fx_symbol='USD/CNY',
        value_date="2021-08-20T00:00:00.000+0800"
    )
    vol = fx_vol_surface.get_vol_surface()
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    print('Volatility Surface\n', vol)
    print(fx_vol_surface.generate_data())
    from fundamental.pricing_context import PricingContext

    scenario_extreme = PricingContext(
        pricing_date="2021-12-28T00:00:00.000+0800"
    )
    with scenario_extreme:
        print(fx_vol_surface.generate_data())

    # print(fx_vol_surface.generate_data())
    # vol_sur = FXVolSurfaceGen(currency_pair=CurrencyPair.USDCNY).volatility_surface
    # strike = 6.6
    # expiry = ql.Date(16, 10, 2021)
    # print(vol_sur.interp_vol(expiry, strike))
