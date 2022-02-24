import copy
import datetime
from typing import List, Union

import numpy as np
import pandas as pd

from fundamental.turing_db.data import TuringDB
from turing_models.instruments.common import CurrencyPair, DiscountCurveType, Ctx
from turing_models.instruments.common import TuringFXATMMethod, TuringFXDeltaMethod
from turing_models.market.curves.curve_generation import ForDiscountCurveGen, DomDiscountCurveGen, \
     FXForwardCurveGen
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.market.volatility.fx_vol_surface_vv import TuringFXVolSurfaceVV
from turing_models.models.model_volatility_fns import TuringVolFunctionTypes
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import TuringSolverTypes
from turing_models.utilities.helper_classes import Base
from turing_models.utilities.helper_functions import to_datetime, to_turing_date
from turing_models.utilities.turing_date import TuringDate


class FXOptionImpliedVolatilitySurface(Base, Ctx):
    fx_symbol: Union[str, CurrencyPair] = CurrencyPair.USDCNY  # 货币对symbol，例如：'USD/CNY'
    value_date: Union[str, datetime.datetime, datetime.date] = datetime.datetime.today()
    strikes: List[float] = None                                # 行权价 如果不传，就用exchange_rate * np.linspace(0.8, 1.2, 16)
    tenors: List[float] = None                                 # 期限（年化） 如果不传，就用[1/12, 2/12, 0.25, 0.5, 1, 2]
    volatility_function_type: Union[str, TuringVolFunctionTypes] = TuringVolFunctionTypes.VANNA_VOLGA

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
                    "VANNA_VOLGA": TuringVolFunctionTypes.VANNA_VOLGA
                }
                self.volatility_function_type = rules.get(
                    self.volatility_function_type,
                    TuringError('Please check the input of volatility_function_type')
                )
                if isinstance(self.volatility_function_type, TuringError):
                    raise self.volatility_function_type

    @property
    def _original_value_date(self):
        if self.ctx_pricing_date is not None:
            # 目前ctx_pricing_date有两个格式：TuringDate和latest
            if isinstance(self.ctx_pricing_date, TuringDate):
                # 接口支持用datetime.datetime格式请求数据
                return to_datetime(self.ctx_pricing_date)
            else:
                # 如果是latest，则保持
                return self.ctx_pricing_date
        return self.value_date

    @property
    def _value_date(self):
        # 将latest转成TuringDate
        return to_turing_date(self._original_value_date)

    @property
    def get_exchange_rate(self):
        """从接口获取汇率"""
        exchange_rate = self.ctx_exchange_rate(currency_pair=self.fx_symbol)
        if exchange_rate is not None:
            return exchange_rate
        date = self._original_value_date
        original_data = TuringDB.exchange_rate(symbol=self.fx_symbol, date=date)
        if original_data is not None:
            data = original_data[self.fx_symbol]
            return data
        else:
            raise TuringError(f"Cannot find exchange rate for {self.fx_symbol}")

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
        fx_swap_curve = self.ctx_fx_swap_curve(currency_pair=self.fx_symbol)
        if fx_swap_curve is not None:
            return pd.DataFrame(fx_swap_curve)
        date = self._original_value_date
        original_data = TuringDB.get_fx_swap_curve(currency_pair=self.fx_symbol, start=date, end=date)
        if not original_data.empty:
            return original_data.loc[self.fx_symbol]
        else:
            raise TuringError(f"Cannot find fx swap curve data for {self.fx_symbol}")

    @property
    def get_fx_implied_vol_data(self):
        """ 获取外汇期权隐含波动率曲线 """
        volatility_type = ["ATM", "25D BF", "25D RR", "10D BF", "10D RR"]
        fx_implied_volatility_curve = self.ctx_fx_implied_volatility_curve(currency_pair=self.fx_symbol,
                                                                           volatility_type=volatility_type)
        if fx_implied_volatility_curve is not None:
            return pd.DataFrame(fx_implied_volatility_curve)
        date = self._original_value_date
        original_data = TuringDB.get_fx_implied_volatility_curve(currency_pair=self.fx_symbol,
                                                                 volatility_type=volatility_type,
                                                                 start=date,
                                                                 end=date)
        if not original_data.empty:
            tenor = original_data.loc[self.fx_symbol].loc["ATM"]['tenor']
            origin_tenor = original_data.loc[self.fx_symbol].loc["ATM"]['origin_tenor']
            atm_vols = original_data.loc[self.fx_symbol].loc["ATM"]['volatility']
            butterfly_25delta_vols = original_data.loc[self.fx_symbol].loc["25D BF"]['volatility']
            risk_reversal_25delta_vols = original_data.loc[self.fx_symbol].loc["25D RR"]['volatility']
            butterfly_10delta_vols = original_data.loc[self.fx_symbol].loc["10D BF"]['volatility']
            risk_reversal_10delta_vols = original_data.loc[self.fx_symbol].loc["10D RR"]['volatility']
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
                                 fx_swap_quotes=self.get_fx_swap_data['swap_point'].tolist(),
                                 curve_type=DiscountCurveType.FX_Forword_tr).discount_curve

    @property
    def foreign_discount_curve(self):
        return ForDiscountCurveGen(value_date=self._value_date,
                                   domestic_discount_curve=self.domestic_discount_curve,
                                   fx_forward_curve=self.fx_forward_curve,
                                   curve_type=DiscountCurveType.FX_Implied_tr).discount_curve

    @property
    def volatility_surface(self):
        if self.volatility_function_type == TuringVolFunctionTypes.VANNA_VOLGA:
            return FXVolSurfaceGen(value_date=self._value_date,
                                   currency_pair=self.fx_symbol,
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

    def get_vol_surface(self):
        """获取波动率曲面的DataFrame"""
        if self.strikes is not None:
            self.strikes = np.array(self.strikes)
        else:
            strike_percent = np.linspace(0.8, 1.2, 16)
            self.strikes = self.get_exchange_rate * strike_percent

        if self.tenors is None:
            self.tenors = [1 / 12, 2 / 12, 0.25, 0.5, 1, 2]

        # 数据精度调整
        self.strikes = np.around(self.strikes, 4)

        expiry = self._value_date.addYears(self.tenors)
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
                else:
                    raise TuringError('Unsupported volatility function type')
                data[strike].append(v)
            # 数据精度调整，波动率保留6位小数
            data[strike] = np.around(data[strike], 6)
        tenors = np.around(tenors, 4)  # 为了便于显示，返回值中的tenor保留4位小数
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
                 value_date: TuringDate,
                 currency_pair: Union[str, CurrencyPair],
                 exchange_rate: float,
                 domestic_discount_curve: TuringDiscountCurve = None,
                 foreign_discount_curve: TuringDiscountCurve = None,
                 tenors: List[float] = None,
                 atm_vols: List[float] = None,
                 butterfly_25delta_vols: List[float] = None,
                 risk_reversal_25delta_vols: List[float] = None,
                 butterfly_10delta_vols: List[float] = None,
                 risk_reversal_10delta_vols: List[float] = None,
                 volatility_function_type: TuringVolFunctionTypes = TuringVolFunctionTypes.VANNA_VOLGA,
                 alpha: float = 1,
                 atm_method: TuringFXATMMethod = TuringFXATMMethod.FWD_DELTA_NEUTRAL,
                 delta_method: TuringFXDeltaMethod = TuringFXDeltaMethod.SPOT_DELTA,
                 solver_type: TuringSolverTypes = TuringSolverTypes.NELDER_MEAD,
                 tol: float = 1e-8):

        self.value_date = value_date
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
        self.tenors = tenors
        self.atm_vols = atm_vols
        self.butterfly_25delta_vols = butterfly_25delta_vols
        self.risk_reversal_25delta_vols = risk_reversal_25delta_vols
        self.butterfly_10delta_vols = butterfly_10delta_vols
        self.risk_reversal_10delta_vols = risk_reversal_10delta_vols
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
            return TuringFXVolSurfaceVV(self.value_date,
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
