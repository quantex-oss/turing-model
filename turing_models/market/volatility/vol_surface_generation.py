import datetime
from typing import List, Union

import numpy as np
import pandas as pd
import QuantLib as ql

from fundamental.turing_db.data import TuringDB
from turing_models.instruments.common import CurrencyPair, DiscountCurveType
from turing_models.instruments.common import TuringFXATMMethod, TuringFXDeltaMethod
from turing_models.market.curves.curve_generation import ForDiscountCurveGen, DomDiscountCurveGen, \
     FXForwardCurveGen
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.market.volatility.fx_vol_surface_ql import FXVolSurface
from turing_models.market.volatility.fx_vol_surface_vv import TuringFXVolSurfaceVV
from turing_models.models.model_volatility_fns import TuringVolFunctionTypes
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import TuringSolverTypes
from turing_models.utilities.turing_date import TuringDate


class FXOptionImpliedVolatilitySurface:
    def __init__(self,
                 fx_symbol: (str, CurrencyPair),  # 货币对symbol，例如：'USD/CNY'
                 value_date: TuringDate = TuringDate(*(datetime.date.today().timetuple()[:3])),
                 strikes: List[float] = None,  # 行权价 如果不传，就用exchange_rate * np.linspace(0.8, 1.2, 16)
                 tenors: List[float] = None,  # 期限（年化） 如果不传，就用[1/12, 2/12, 0.25, 0.5, 1, 2]
                 volatility_function_type=TuringVolFunctionTypes.QL):

        if isinstance(fx_symbol, CurrencyPair):
            fx_symbol = fx_symbol.value
        elif isinstance(fx_symbol, str):
            pass
        else:
            raise TuringError('fx_symbol: (str, CurrencyPair)')

        exchange_rate = TuringDB.exchange_rate(symbol=fx_symbol, date=value_date)[fx_symbol]

        if strikes:
            self.strikes = np.array(strikes)
        else:
            strike_percent = np.linspace(0.8, 1.2, 16)
            self.strikes = exchange_rate * strike_percent

        if not tenors:
            self.tenors = [1 / 12, 2 / 12, 0.25, 0.5, 1, 2]
        else:
            self.tenors = tenors

        self.expiry = value_date.addYears(self.tenors)

        self.volatility_function_type = volatility_function_type

        shibor_data = TuringDB.shibor_curve(date=value_date, df=False)
        shibor_swap_data = TuringDB.irs_curve(curve_type='Shibor3M', date=value_date, df=False)['Shibor3M']

        fx_swap_data = TuringDB.swap_curve(symbol=fx_symbol, date=value_date, df=False)[fx_symbol]
        fx_implied_vol_data = TuringDB.fx_implied_volatility_curve(symbol=fx_symbol,
                                                                   volatility_type=["ATM", "25D BF", "25D RR", "10D BF",
                                                                                    "10D RR"],
                                                                   date=value_date,
                                                                   df=False)[fx_symbol]

        if volatility_function_type == TuringVolFunctionTypes.VANNA_VOLGA:
            dom_curve_type = DiscountCurveType.Shibor3M_tr
            for_curve_type = DiscountCurveType.FX_Implied_tr
            fx_forward_curve_type = DiscountCurveType.FX_Forword_tr
        elif volatility_function_type == TuringVolFunctionTypes.QL:
            dom_curve_type = DiscountCurveType.Shibor3M
            for_curve_type = DiscountCurveType.FX_Implied
            fx_forward_curve_type = DiscountCurveType.FX_Forword
        else:
            raise TuringError('Unsupported volatility function type')

        domestic_discount_curve = DomDiscountCurveGen(value_date=value_date,
                                                      shibor_tenors=shibor_data['tenor'],
                                                      shibor_origin_tenors=shibor_data['origin_tenor'],
                                                      shibor_rates=shibor_data['rate'],
                                                      shibor_swap_tenors=shibor_swap_data['tenor'],
                                                      shibor_swap_origin_tenors=shibor_swap_data['origin_tenor'],
                                                      shibor_swap_rates=shibor_swap_data['average'],
                                                      curve_type=dom_curve_type).discount_curve

        fx_forward_curve = FXForwardCurveGen(value_date=value_date,
                                             exchange_rate=exchange_rate,
                                             fx_swap_origin_tenors=fx_swap_data['origin_tenor'],
                                             fx_swap_quotes=fx_swap_data['swap_point'],
                                             curve_type=fx_forward_curve_type).discount_curve

        foreign_discount_curve = ForDiscountCurveGen(value_date=value_date,
                                                     domestic_discount_curve=domestic_discount_curve,
                                                     fx_forward_curve=fx_forward_curve,
                                                     curve_type=for_curve_type).discount_curve

        self.volatility_surface = FXVolSurfaceGen(value_date=value_date,
                                                  currency_pair=fx_symbol,
                                                  exchange_rate=exchange_rate,
                                                  domestic_discount_curve=domestic_discount_curve,
                                                  foreign_discount_curve=foreign_discount_curve,
                                                  fx_forward_curve=fx_forward_curve,
                                                  tenors=fx_implied_vol_data["tenor"],
                                                  origin_tenors=fx_implied_vol_data["origin_tenor"],
                                                  atm_vols=fx_implied_vol_data["ATM"],
                                                  butterfly_25delta_vols=fx_implied_vol_data["25D BF"],
                                                  risk_reversal_25delta_vols=fx_implied_vol_data["25D RR"],
                                                  butterfly_10delta_vols=fx_implied_vol_data["10D BF"],
                                                  risk_reversal_10delta_vols=fx_implied_vol_data["10D RR"],
                                                  volatility_function_type=volatility_function_type).volatility_surface

    def get_vol_surface(self):
        """获取波动率曲面的DataFrame"""
        data = {}
        expiry = self.expiry
        tenors = self.tenors
        strikes = self.strikes
        volatility_surface = self.volatility_surface
        volatility_function_type = self.volatility_function_type
        for i in range(len(tenors)):
            ex = expiry[i]
            tenor = tenors[i]
            data[tenor] = []
            for strike in strikes:
                if volatility_function_type == TuringVolFunctionTypes.VANNA_VOLGA:
                    v = volatility_surface.volatilityFromStrikeDate(strike, ex)
                elif volatility_function_type == TuringVolFunctionTypes.QL:
                    ex_ql = ql.Date(ex._d, ex._m, ex._y)
                    v = volatility_surface.interp_vol(ex_ql, strike)
                else:
                    raise TuringError('Unsupported volatility function type')
                data[tenor].append(v)
        return pd.DataFrame(data, index=strikes)


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
                 atm_vols: List[float] = None,
                 butterfly_25delta_vols: List[float] = None,
                 risk_reversal_25delta_vols: List[float] = None,
                 butterfly_10delta_vols: List[float] = None,
                 risk_reversal_10delta_vols: List[float] = None,
                 volatility_function_type: TuringVolFunctionTypes = TuringVolFunctionTypes.QL,
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
            data_dict = {'Tenor': self.origin_tenors,
                         'ATM': self.atm_vols,
                         '25DRR': self.risk_reversal_25delta_vols,
                         '25DBF': self.butterfly_25delta_vols,
                         '10DRR': self.risk_reversal_10delta_vols,
                         '10DBF': self.butterfly_10delta_vols}

            vol_data = pd.DataFrame(data_dict)

            calendar = ql.China(ql.China.IB)
            convention = ql.Following
            daycount = ql.Actual365Fixed()
            return FXVolSurface(vol_data,
                                domestic_name,
                                foreign_name,
                                self.exchange_rate,
                                self.fx_forward_curve,
                                self.domestic_discount_curve,
                                self.foreign_discount_curve,
                                self.value_date_ql,
                                calendar,
                                convention,
                                daycount,
                                True)


if __name__ == '__main__':
    fx_vol_surface = FXOptionImpliedVolatilitySurface(
        fx_symbol=CurrencyPair.USDCNY)
    print('Volatility Surface\n', fx_vol_surface.get_vol_surface())
    # vol_sur = FXVolSurfaceGen(currency_pair=CurrencyPair.USDCNY).volatility_surface
    # strike = 6.6
    # expiry = ql.Date(16, 10, 2021)
    # print(vol_sur.interp_vol(expiry, strike))
