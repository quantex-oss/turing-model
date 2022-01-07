import datetime
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Union

import numpy as np
import pandas as pd
from numba import njit

from fundamental import ctx
from fundamental.turing_db.data import TuringDB
from turing_models.market.curves.curve_adjust import CurveAdjustmentImpl
from turing_models.market.curves.discount_curve_zeros import TuringDiscountCurveZeros
from turing_models.models.model_black_scholes_analytical import bs_value, bs_delta
from turing_models.utilities.error import TuringError
from turing_models.utilities.turing_date import TuringDate

bump = 1e-4


def greek(obj, price, attr, bump=bump, order=1, cus_inc=None):
    """
    如果要传cus_inc，格式须为(函数名, 函数参数值)
    """
    cus_func = args = None
    attr_value = getattr(obj, attr)
    if cus_inc:
        cus_func, args = cus_inc

    def increment(_attr_value, count=1):
        if cus_func:
            _attr_value = cus_func(args * count)
        else:
            _attr_value += count * bump
        setattr(obj, attr, _attr_value)

    def decrement(_attr_value, count=1):
        if cus_func:
            _attr_value = cus_func(-args * count)
        else:
            _attr_value -= count * bump
        setattr(obj, attr, _attr_value)

    def clear():
        setattr(obj, attr, None)

    if order == 1:
        if isinstance(attr_value, TuringDate):
            p0 = price()
            increment(attr_value)
            p_up = price()
            clear()
            return (p_up - p0) / bump
        increment(attr_value)
        p_up = price()
        clear()
        decrement(attr_value)
        p_down = price()
        clear()
        return (p_up - p_down) / (bump * 2)
    elif order == 2:
        p0 = price()
        decrement(attr_value)
        p_down = price()
        increment(attr_value)
        p_up = price()
        clear()
        return (p_up - 2.0 * p0 + p_down) / bump / bump


def newton_fun(y, *args):
    """ Function is used by scipy.optimize.newton """
    self = args[0]  # 实例对象
    price = args[1]  # 对照的标准
    attr = args[2]  # 需要调整的参数
    fun = args[3]  # 调整参数后需重新计算的方法
    setattr(self, attr, y)  # 调整参数
    px = getattr(self, fun)()  # 重新计算方法的返回值
    obj_fn = px - price  # 计算误差
    return obj_fn


@njit(fastmath=True, cache=True)
def fastDelta(s, t, k, rd, rf, vol, deltaTypeValue, optionTypeValue):
    ''' Calculation of the FX Option delta. Used in the determination of
    the volatility surface. Avoids discount curve interpolation so it
    should be slightly faster than the full calculation of delta. '''

    pips_spot_delta = bs_delta(s, t, k, rd, rf, vol, optionTypeValue, False)

    if deltaTypeValue == TuringFXDeltaMethod.SPOT_DELTA.value:
        return pips_spot_delta
    elif deltaTypeValue == TuringFXDeltaMethod.FORWARD_DELTA.value:
        pips_fwd_delta = pips_spot_delta * np.exp(rf * t)
        return pips_fwd_delta
    elif deltaTypeValue == TuringFXDeltaMethod.SPOT_DELTA_PREM_ADJ.value:
        vpctf = bs_value(s, t, k, rd, rf, vol, optionTypeValue, False) / s
        pct_spot_delta_prem_adj = pips_spot_delta - vpctf
        return pct_spot_delta_prem_adj
    elif deltaTypeValue == TuringFXDeltaMethod.FORWARD_DELTA_PREM_ADJ.value:
        vpctf = bs_value(s, t, k, rd, rf, vol, optionTypeValue, False) / s
        pct_fwd_delta_prem_adj = np.exp(rf * t) * (pips_spot_delta - vpctf)
        return pct_fwd_delta_prem_adj
    else:
        raise TuringError("Unknown TuringFXDeltaMethod")


class RiskMeasure(Enum):
    Price = "price"
    Delta = "delta"
    Gamma = "gamma"
    Vega = "vega"
    Theta = "theta"
    Rho = "rho"
    RhoQ = "rho_q"
    EqDelta = "eq_delta"
    EqGamma = "eq_gamma"
    EqVega = "eq_vega"
    EqTheta = "eq_theta"
    EqRho = "eq_rho"
    EqRhoQ = "eq_rho_q"
    Dv01 = "dv01"
    DollarDuration = "dollar_duration"
    DollarConvexity = "dollar_convexity"
    ModifiedDuration = "modified_duration"
    FxDelta = "fx_delta"
    FxGamma = "fx_gamma"
    FxVega = "fx_vega"
    FxTheta = "fx_theta"
    FxVanna = "fx_vanna"
    FxVolga = "fx_volga"
    FullPrice = "full_price"
    CleanPrice = "clean_price"
    YTM = 'ytm'
    TimeToMaturity = 'time_to_maturity'

    def __repr__(self):
        return self.value


class BuySell(Enum):
    """Buy or Sell side of contract"""

    Buy = 'Buy'
    Sell = 'Sell'

    def __repr__(self):
        return self.value


class Exchange(Enum):
    """Exchange Name"""

    Shanghai_Stock_Exchange = 'Shanghai Stock Exchange'
    Shenzhen_Stock_Exchange = 'Shenzhen Stock Exchange'
    Zhengzhou_Commodity_Exchange = 'Zhengzhou Commodity Exchange'
    Dalian_Commodity_Exchange = 'Dalian Commodity Exchange'
    Shanghai_Futures_Exchange = 'Shanghai Futures Exchange'
    China_Financial_Futures_Exchange = 'China Financial Futures Exchange'

    def __repr__(self):
        return self.value


class OptionType(Enum):
    """Option Type"""

    Call = 'Call'
    Put = 'Put'
    Binary_Call = 'Binary Call'
    Binary_Put = 'Binary Put'

    def __repr__(self):
        return self.value


class OptionStyle(Enum):
    """Option Exercise Style"""

    European = 'European'
    American = 'American'
    Asian = 'Asian'
    Bermudan = 'Bermudan'
    Snowball = 'Snowball'

    def __repr__(self):
        return self.value


class CurveCode(Enum):
    CBD100031 = "中债中短期票据收益率曲线(A)"
    CBD100032 = "中债中短期票据收益率曲线(A)"
    CBD100033 = "中债中短期票据收益率曲线(A)"
    CBD100034 = "中债中短期票据收益率曲线(A)"
    CBD100041 = "中债中短期票据收益率曲线(A+)"
    CBD100042 = "中债中短期票据收益率曲线(A+)"
    CBD100043 = "中债中短期票据收益率曲线(A+)"
    CBD100044 = "中债中短期票据收益率曲线(A+)"
    CBD100051 = "中债中短期票据收益率曲线(A-)"
    CBD100052 = "中债中短期票据收益率曲线(A-)"
    CBD100053 = "中债中短期票据收益率曲线(A-)"
    CBD100054 = "中债中短期票据收益率曲线(A-)"
    CBD100061 = "中债中短期票据收益率曲线(AA)"
    CBD100062 = "中债中短期票据收益率曲线(AA)"
    CBD100063 = "中债中短期票据收益率曲线(AA)"
    CBD100064 = "中债中短期票据收益率曲线(AA)"
    CBD100071 = "中债中短期票据收益率曲线(AA+)"
    CBD100072 = "中债中短期票据收益率曲线(AA+)"
    CBD100073 = "中债中短期票据收益率曲线(AA+)"
    CBD100074 = "中债中短期票据收益率曲线(AA+)"
    CBD100081 = "中债中短期票据收益率曲线(AA-)"
    CBD100082 = "中债中短期票据收益率曲线(AA-)"
    CBD100083 = "中债中短期票据收益率曲线(AA-)"
    CBD100084 = "中债中短期票据收益率曲线(AA-)"
    CBD100091 = "中债中短期票据收益率曲线(AAA)"
    CBD100092 = "中债中短期票据收益率曲线(AAA)"
    CBD100093 = "中债中短期票据收益率曲线(AAA)"
    CBD100094 = "中债中短期票据收益率曲线(AAA)"
    CBD100112 = "中债浮动利率企业债(Depo-1Y)点差曲线(AAA)"
    CBD100172 = "中债浮动利率资产支持证券(Depo-1Y)点差曲线(A)"
    CBD100212 = "中债浮动利率资产支持证券(Depo-1Y)点差曲线(AAA)"
    CBD100221 = "中债国债收益率曲线"
    CBD100222 = "中债国债收益率曲线"
    CBD100223 = "中债国债收益率曲线"
    CBD100224 = "中债国债收益率曲线"
    CBD100241 = "中债企业债收益率曲线(AA)"
    CBD100242 = "中债企业债收益率曲线(AA)"
    CBD100243 = "中债企业债收益率曲线(AA)"
    CBD100244 = "中债企业债收益率曲线(AA)"
    CBD100251 = "中债企业债收益率曲线(AAA)"
    CBD100252 = "中债企业债收益率曲线(AAA)"
    CBD100253 = "中债企业债收益率曲线(AAA)"
    CBD100254 = "中债企业债收益率曲线(AAA)"
    CBD100311 = "中债进出口行债收益率曲线"
    CBD100312 = "中债进出口行债收益率曲线"
    CBD100313 = "中债进出口行债收益率曲线"
    CBD100314 = "中债进出口行债收益率曲线"
    CBD100321 = "中债资产支持证券收益率曲线(AAA)"
    CBD100322 = "中债资产支持证券收益率曲线(AAA)"
    CBD100323 = "中债资产支持证券收益率曲线(AAA)"
    CBD100324 = "中债资产支持证券收益率曲线(AAA)"
    CBD100332 = "中债浮动利率政策性金融债(Depo-1Y)点差曲线"
    CBD100372 = "中债浮动利率政策性金融债(SHIBOR-3M-5D)点差曲线"
    CBD100431 = "中债企业债收益率曲线(AA+)"
    CBD100432 = "中债企业债收益率曲线(AA+)"
    CBD100433 = "中债企业债收益率曲线(AA+)"
    CBD100434 = "中债企业债收益率曲线(AA+)"
    CBD100461 = "中债城投债收益率曲线(AA(2))"
    CBD100462 = "中债城投债收益率曲线(AA(2))"
    CBD100463 = "中债城投债收益率曲线(AA(2))"
    CBD100464 = "中债城投债收益率曲线(AA(2))"
    CBD100481 = "中债中短期票据收益率曲线(AAA-)"
    CBD100482 = "中债中短期票据收益率曲线(AAA-)"
    CBD100483 = "中债中短期票据收益率曲线(AAA-)"
    CBD100484 = "中债中短期票据收益率曲线(AAA-)"
    CBD100531 = "中债城投债收益率曲线(AA-)"
    CBD100532 = "中债城投债收益率曲线(AA-)"
    CBD100533 = "中债城投债收益率曲线(AA-)"
    CBD100534 = "中债城投债收益率曲线(AA-)"
    CBD100541 = "中债城投债收益率曲线(AA+)"
    CBD100542 = "中债城投债收益率曲线(AA+)"
    CBD100543 = "中债城投债收益率曲线(AA+)"
    CBD100544 = "中债城投债收益率曲线(AA+)"
    CBD100551 = "中债城投债收益率曲线(AAA)"
    CBD100552 = "中债城投债收益率曲线(AAA)"
    CBD100553 = "中债城投债收益率曲线(AAA)"
    CBD100554 = "中债城投债收益率曲线(AAA)"
    CBD100561 = "中债企业债收益率曲线(A+)"
    CBD100562 = "中债企业债收益率曲线(A+)"
    CBD100563 = "中债企业债收益率曲线(A+)"
    CBD100564 = "中债企业债收益率曲线(A+)"
    CBD100572 = "中债浮动利率城投债(SHIBOR-1Y-10D)点差曲线(AA+)"
    CBD100581 = "中债城投债收益率曲线(AA)"
    CBD100582 = "中债城投债收益率曲线(AA)"
    CBD100583 = "中债城投债收益率曲线(AA)"
    CBD100584 = "中债城投债收益率曲线(AA)"
    CBD100591 = "中债铁道债收益率曲线"
    CBD100592 = "中债铁道债收益率曲线"
    CBD100593 = "中债铁道债收益率曲线"
    CBD100594 = "中债铁道债收益率曲线"
    CBD100611 = "中债企业债收益率曲线(A)"
    CBD100612 = "中债企业债收益率曲线(A)"
    CBD100613 = "中债企业债收益率曲线(A)"
    CBD100614 = "中债企业债收益率曲线(A)"
    CBD100621 = "中债企业债收益率曲线(BBB+)"
    CBD100622 = "中债企业债收益率曲线(BBB+)"
    CBD100623 = "中债企业债收益率曲线(BBB+)"
    CBD100624 = "中债企业债收益率曲线(BBB+)"
    CBD100662 = "中债浮动利率中短期票据(Depo-1Y)点差曲线(AA)"
    CBD100672 = "中债浮动利率中短期票据(Depo-1Y)点差曲线(AA+)"
    CBD100692 = "中债浮动利率中短期票据(Depo-1Y)点差曲线(AAA)"
    CBD100731 = "中债中短期票据收益率曲线(AAA+)"
    CBD100732 = "中债中短期票据收益率曲线(AAA+)"
    CBD100733 = "中债中短期票据收益率曲线(AAA+)"
    CBD100734 = "中债中短期票据收益率曲线(AAA+)"
    CBD100741 = "中债商业银行普通债收益率曲线(AAA)"
    CBD100742 = "中债商业银行普通债收益率曲线(AAA)"
    CBD100743 = "中债商业银行普通债收益率曲线(AAA)"
    CBD100744 = "中债商业银行普通债收益率曲线(AAA)"
    CBD100751 = "中债商业银行普通债收益率曲线(AA+)"
    CBD100752 = "中债商业银行普通债收益率曲线(AA+)"
    CBD100753 = "中债商业银行普通债收益率曲线(AA+)"
    CBD100754 = "中债商业银行普通债收益率曲线(AA+)"
    CBD100761 = "中债商业银行普通债收益率曲线(AA)"
    CBD100762 = "中债商业银行普通债收益率曲线(AA)"
    CBD100763 = "中债商业银行普通债收益率曲线(AA)"
    CBD100764 = "中债商业银行普通债收益率曲线(AA)"
    CBD100771 = "中债商业银行普通债收益率曲线(AA-)"
    CBD100772 = "中债商业银行普通债收益率曲线(AA-)"
    CBD100773 = "中债商业银行普通债收益率曲线(AA-)"
    CBD100774 = "中债商业银行普通债收益率曲线(AA-)"
    CBD100822 = "中债浮动利率中短期票据(Depo-1Y)点差曲线(AA-)"
    CBD100831 = "中债铁道债收益率曲线(减税)"
    CBD100832 = "中债铁道债收益率曲线(减税)"
    CBD100833 = "中债铁道债收益率曲线(减税)"
    CBD100834 = "中债铁道债收益率曲线(减税)"
    CBD100841 = "中债国开债收益率曲线"
    CBD100842 = "中债国开债收益率曲线"
    CBD100843 = "中债国开债收益率曲线"
    CBD100844 = "中债国开债收益率曲线"
    CBD100851 = "中债地方政府债收益率曲线(AAA)"
    CBD100852 = "中债地方政府债收益率曲线(AAA)"
    CBD100853 = "中债地方政府债收益率曲线(AAA)"
    CBD100854 = "中债地方政府债收益率曲线(AAA)"
    CBD100861 = "中债资产支持证券收益率曲线(AA+)"
    CBD100862 = "中债资产支持证券收益率曲线(AA+)"
    CBD100863 = "中债资产支持证券收益率曲线(AA+)"
    CBD100864 = "中债资产支持证券收益率曲线(AA+)"
    CBD100871 = "中债企业债收益率曲线(A-)"
    CBD100872 = "中债企业债收益率曲线(A-)"
    CBD100873 = "中债企业债收益率曲线(A-)"
    CBD100874 = "中债企业债收益率曲线(A-)"
    CBD100881 = "中债商业银行普通债收益率曲线(A+)"
    CBD100882 = "中债商业银行普通债收益率曲线(A+)"
    CBD100883 = "中债商业银行普通债收益率曲线(A+)"
    CBD100884 = "中债商业银行普通债收益率曲线(A+)"
    CBD100891 = "中债企业债收益率曲线(CC)"
    CBD100892 = "中债企业债收益率曲线(CC)"
    CBD100893 = "中债企业债收益率曲线(CC)"
    CBD100894 = "中债企业债收益率曲线(CC)"
    CBD100901 = "中债企业债收益率曲线(BBB)"
    CBD100902 = "中债企业债收益率曲线(BBB)"
    CBD100903 = "中债企业债收益率曲线(BBB)"
    CBD100904 = "中债企业债收益率曲线(BBB)"
    CBD100911 = "中债企业债收益率曲线(BB)"
    CBD100912 = "中债企业债收益率曲线(BB)"
    CBD100913 = "中债企业债收益率曲线(BB)"
    CBD100914 = "中债企业债收益率曲线(BB)"
    CBD100921 = "中债企业债收益率曲线(B)"
    CBD100922 = "中债企业债收益率曲线(B)"
    CBD100923 = "中债企业债收益率曲线(B)"
    CBD100924 = "中债企业债收益率曲线(B)"
    CBD100931 = "中债企业债收益率曲线(CCC)"
    CBD100932 = "中债企业债收益率曲线(CCC)"
    CBD100933 = "中债企业债收益率曲线(CCC)"
    CBD100934 = "中债企业债收益率曲线(CCC)"
    CBD100941 = "中债企业债收益率曲线(AAA-)"
    CBD100942 = "中债企业债收益率曲线(AAA-)"
    CBD100943 = "中债企业债收益率曲线(AAA-)"
    CBD100944 = "中债企业债收益率曲线(AAA-)"
    CBD100951 = "中债企业债收益率曲线(AA-)"
    CBD100952 = "中债企业债收益率曲线(AA-)"
    CBD100953 = "中债企业债收益率曲线(AA-)"
    CBD100954 = "中债企业债收益率曲线(AA-)"
    CBD100961 = "中债商业银行普通债收益率曲线(AAA-)"
    CBD100962 = "中债商业银行普通债收益率曲线(AAA-)"
    CBD100963 = "中债商业银行普通债收益率曲线(AAA-)"
    CBD100964 = "中债商业银行普通债收益率曲线(AAA-)"
    CBD100972 = "中债浮动利率商业银行普通债(SHIBOR-3M-1D)点差曲线(AAA-)"
    CBD100982 = "中债浮动利率商业银行普通债(SHIBOR-3M-1D)点差曲线(AA+)"
    CBD100991 = "中债地方政府债收益率曲线(AAA-)"
    CBD100992 = "中债地方政府债收益率曲线(AAA-)"
    CBD100993 = "中债地方政府债收益率曲线(AAA-)"
    CBD100994 = "中债地方政府债收益率曲线(AAA-)"
    CBD101001 = "中债资产支持证券收益率曲线(AAA-)"
    CBD101002 = "中债资产支持证券收益率曲线(AAA-)"
    CBD101003 = "中债资产支持证券收益率曲线(AAA-)"
    CBD101004 = "中债资产支持证券收益率曲线(AAA-)"
    CBD101011 = "中债资产支持证券收益率曲线(AA)"
    CBD101012 = "中债资产支持证券收益率曲线(AA)"
    CBD101013 = "中债资产支持证券收益率曲线(AA)"
    CBD101014 = "中债资产支持证券收益率曲线(AA)"
    CBD101021 = "中债资产支持证券收益率曲线(AA-)"
    CBD101022 = "中债资产支持证券收益率曲线(AA-)"
    CBD101023 = "中债资产支持证券收益率曲线(AA-)"
    CBD101024 = "中债资产支持证券收益率曲线(AA-)"
    CBD101031 = "中债资产支持证券收益率曲线(A+)"
    CBD101032 = "中债资产支持证券收益率曲线(A+)"
    CBD101033 = "中债资产支持证券收益率曲线(A+)"
    CBD101034 = "中债资产支持证券收益率曲线(A+)"
    CBD101042 = "中债浮动利率资产支持证券(Depo-1Y)点差曲线(AA)"
    CBD101051 = "中债农发行债收益率曲线"
    CBD101052 = "中债农发行债收益率曲线"
    CBD101053 = "中债农发行债收益率曲线"
    CBD101054 = "中债农发行债收益率曲线"
    CBD101061 = "中债商业银行普通债收益率曲线(A)"
    CBD101062 = "中债商业银行普通债收益率曲线(A)"
    CBD101063 = "中债商业银行普通债收益率曲线(A)"
    CBD101064 = "中债商业银行普通债收益率曲线(A)"
    CBD101071 = "中债商业银行普通债收益率曲线(A-)"
    CBD101072 = "中债商业银行普通债收益率曲线(A-)"
    CBD101073 = "中债商业银行普通债收益率曲线(A-)"
    CBD101074 = "中债商业银行普通债收益率曲线(A-)"
    CBD101091 = "中债商业银行二级资本债收益率曲线(AAA-)"
    CBD101092 = "中债商业银行二级资本债收益率曲线(AAA-)"
    CBD101093 = "中债商业银行二级资本债收益率曲线(AAA-)"
    CBD101094 = "中债商业银行二级资本债收益率曲线(AAA-)"
    CBD101101 = "中债商业银行二级资本债收益率曲线(AA+)"
    CBD101102 = "中债商业银行二级资本债收益率曲线(AA+)"
    CBD101103 = "中债商业银行二级资本债收益率曲线(AA+)"
    CBD101104 = "中债商业银行二级资本债收益率曲线(AA+)"
    CBD101111 = "中债商业银行二级资本债收益率曲线(AA)"
    CBD101112 = "中债商业银行二级资本债收益率曲线(AA)"
    CBD101113 = "中债商业银行二级资本债收益率曲线(AA)"
    CBD101114 = "中债商业银行二级资本债收益率曲线(AA)"
    CBD101121 = "中债商业银行二级资本债收益率曲线(AA-)"
    CBD101122 = "中债商业银行二级资本债收益率曲线(AA-)"
    CBD101123 = "中债商业银行二级资本债收益率曲线(AA-)"
    CBD101124 = "中债商业银行二级资本债收益率曲线(AA-)"
    CBD101131 = "中债商业银行二级资本债收益率曲线(A+)"
    CBD101132 = "中债商业银行二级资本债收益率曲线(A+)"
    CBD101133 = "中债商业银行二级资本债收益率曲线(A+)"
    CBD101134 = "中债商业银行二级资本债收益率曲线(A+)"
    CBD101141 = "中债商业银行二级资本债收益率曲线(A)"
    CBD101142 = "中债商业银行二级资本债收益率曲线(A)"
    CBD101143 = "中债商业银行二级资本债收益率曲线(A)"
    CBD101144 = "中债商业银行二级资本债收益率曲线(A)"
    CBD101151 = "中债商业银行同业存单收益率曲线(AAA)"
    CBD101152 = "中债商业银行同业存单收益率曲线(AAA)"
    CBD101161 = "中债商业银行同业存单收益率曲线(AAA-)"
    CBD101162 = "中债商业银行同业存单收益率曲线(AAA-)"
    CBD101171 = "中债商业银行同业存单收益率曲线(AA+)"
    CBD101172 = "中债商业银行同业存单收益率曲线(AA+)"
    CBD101181 = "中债商业银行同业存单收益率曲线(AA)"
    CBD101182 = "中债商业银行同业存单收益率曲线(AA)"
    CBD101191 = "中债商业银行同业存单收益率曲线(AA-)"
    CBD101192 = "中债商业银行同业存单收益率曲线(AA-)"
    CBD101201 = "中债商业银行同业存单收益率曲线(A+)"
    CBD101202 = "中债商业银行同业存单收益率曲线(A+)"
    CBD101211 = "中债商业银行同业存单收益率曲线(A)"
    CBD101212 = "中债商业银行同业存单收益率曲线(A)"
    CBD101221 = "中债商业银行同业存单收益率曲线(A-)"
    CBD101222 = "中债商业银行同业存单收益率曲线(A-)"
    CBD101231 = "中债个人住房抵押贷款资产支持证券收益率曲线(AAA)"
    CBD101232 = "中债个人住房抵押贷款资产支持证券收益率曲线(AAA)"
    CBD101233 = "中债个人住房抵押贷款资产支持证券收益率曲线(AAA)"
    CBD101234 = "中债个人住房抵押贷款资产支持证券收益率曲线(AAA)"
    CBD101242 = "中债浮动利率个人住房抵押贷款资产支持证券(Loan-5Y)点差曲线(AAA)"
    CBD101251 = "中债中资美元债收益率曲线(A+)"
    CBD101252 = "中债中资美元债收益率曲线(A+)"
    CBD101253 = "中债中资美元债收益率曲线(A+)"
    CBD101254 = "中债中资美元债收益率曲线(A+)"
    CBD101261 = "中债中资美元债收益率曲线(A)"
    CBD101262 = "中债中资美元债收益率曲线(A)"
    CBD101263 = "中债中资美元债收益率曲线(A)"
    CBD101264 = "中债中资美元债收益率曲线(A)"
    CBD101271 = "中债中资美元债收益率曲线(A-)"
    CBD101272 = "中债中资美元债收益率曲线(A-)"
    CBD101273 = "中债中资美元债收益率曲线(A-)"
    CBD101274 = "中债中资美元债收益率曲线(A-)"
    CBD101281 = "中债中资美元债收益率曲线(BBB+)"
    CBD101282 = "中债中资美元债收益率曲线(BBB+)"
    CBD101283 = "中债中资美元债收益率曲线(BBB+)"
    CBD101284 = "中债中资美元债收益率曲线(BBB+)"
    CBD101291 = "中债中资美元债收益率曲线(BBB)"
    CBD101292 = "中债中资美元债收益率曲线(BBB)"
    CBD101293 = "中债中资美元债收益率曲线(BBB)"
    CBD101294 = "中债中资美元债收益率曲线(BBB)"
    CBD101301 = "中债中资美元债收益率曲线(BBB-)"
    CBD101302 = "中债中资美元债收益率曲线(BBB-)"
    CBD101303 = "中债中资美元债收益率曲线(BBB-)"
    CBD101304 = "中债中资美元债收益率曲线(BBB-)"
    CBD101311 = "中债消费金融资产支持证券收益率曲线(AAA)"
    CBD101312 = "中债消费金融资产支持证券收益率曲线(AAA)"
    CBD101313 = "中债消费金融资产支持证券收益率曲线(AAA)"
    CBD101314 = "中债消费金融资产支持证券收益率曲线(AAA)"
    CBD101321 = "中债消费金融资产支持证券收益率曲线(AA+)"
    CBD101322 = "中债消费金融资产支持证券收益率曲线(AA+)"
    CBD101323 = "中债消费金融资产支持证券收益率曲线(AA+)"
    CBD101324 = "中债消费金融资产支持证券收益率曲线(AA+)"
    CBD101331 = "中债消费金融资产支持证券收益率曲线(AA)"
    CBD101332 = "中债消费金融资产支持证券收益率曲线(AA)"
    CBD101333 = "中债消费金融资产支持证券收益率曲线(AA)"
    CBD101334 = "中债消费金融资产支持证券收益率曲线(AA)"
    CBD101341 = "中债消费金融资产支持证券收益率曲线(AA-)"
    CBD101342 = "中债消费金融资产支持证券收益率曲线(AA-)"
    CBD101343 = "中债消费金融资产支持证券收益率曲线(AA-)"
    CBD101344 = "中债消费金融资产支持证券收益率曲线(AA-)"
    CBD101352 = "中债浮动利率消费金融资产支持证券(Loan-1Y)点差曲线(AAA)"
    CBD101362 = "中债浮动利率消费金融资产支持证券(Loan-1Y)点差曲线(AA+)"
    CBD101372 = "中债浮动利率消费金融资产支持证券(Loan-1Y)点差曲线(AA)"
    CBD101451 = "保险公司准备金计量基准收益率曲线"


class YieldCurveCode(Enum):
    # 曲线编码 = 曲线中文名
    CBD100032 = '中债中短期票据收益率曲线(A)'
    CBD100042 = '中债中短期票据收益率曲线(A+)'
    CBD100052 = '中债中短期票据收益率曲线(A-)'
    CBD100062 = '中债中短期票据收益率曲线(AA)'
    CBD100072 = '中债中短期票据收益率曲线(AA+)'
    CBD100082 = '中债中短期票据收益率曲线(AA-)'
    CBD100092 = '中债中短期票据收益率曲线(AAA)'
    CBD100112 = '中债浮动利率企业债(Depo-1Y)点差曲线(AAA)'
    CBD100172 = '中债浮动利率资产支持证券(Depo-1Y)点差曲线(A)'
    CBD100212 = '中债浮动利率资产支持证券(Depo-1Y)点差曲线(AAA)'
    CBD100222 = '中债国债收益率曲线'
    CBD100242 = '中债企业债收益率曲线(AA)'
    CBD100252 = '中债企业债收益率曲线(AAA)'
    CBD100312 = '中债进出口行债收益率曲线'
    CBD100322 = '中债资产支持证券收益率曲线(AAA)'
    CBD100332 = '中债浮动利率政策性金融债(Depo-1Y)点差曲线'
    CBD100372 = '中债浮动利率政策性金融债(SHIBOR-3M-5D)点差曲线'
    CBD100432 = '中债企业债收益率曲线(AA+)'
    CBD100462 = '中债城投债收益率曲线(AA(2))'
    CBD100482 = '中债中短期票据收益率曲线(AAA-)'
    CBD100532 = '中债城投债收益率曲线(AA-)'
    CBD100542 = '中债城投债收益率曲线(AA+)'
    CBD100552 = '中债城投债收益率曲线(AAA)'
    CBD100562 = '中债企业债收益率曲线(A+)'
    CBD100572 = '中债浮动利率城投债(SHIBOR-1Y-10D)点差曲线(AA+)'
    CBD100582 = '中债城投债收益率曲线(AA)'
    CBD100592 = '中债铁道债收益率曲线'
    CBD100612 = '中债企业债收益率曲线(A)'
    CBD100622 = '中债企业债收益率曲线(BBB+)'
    CBD100662 = '中债浮动利率中短期票据(Depo-1Y)点差曲线(AA)'
    CBD100672 = '中债浮动利率中短期票据(Depo-1Y)点差曲线(AA+)'
    CBD100692 = '中债浮动利率中短期票据(Depo-1Y)点差曲线(AAA)'
    CBD100732 = '中债中短期票据收益率曲线(AAA+)'
    CBD100742 = '中债商业银行普通债收益率曲线(AAA)'
    CBD100752 = '中债商业银行普通债收益率曲线(AA+)'
    CBD100762 = '中债商业银行普通债收益率曲线(AA)'
    CBD100772 = '中债商业银行普通债收益率曲线(AA-)'
    CBD100822 = '中债浮动利率中短期票据(Depo-1Y)点差曲线(AA-)'
    CBD100832 = '中债铁道债收益率曲线(减税)'
    CBD100842 = '中债国开债收益率曲线'
    CBD100852 = '中债地方政府债收益率曲线(AAA)'
    CBD100862 = '中债资产支持证券收益率曲线(AA+)'
    CBD100872 = '中债企业债收益率曲线(A-)'
    CBD100882 = '中债商业银行普通债收益率曲线(A+)'
    CBD100892 = '中债企业债收益率曲线(CC)'
    CBD100902 = '中债企业债收益率曲线(BBB)'
    CBD100912 = '中债企业债收益率曲线(BB)'
    CBD100922 = '中债企业债收益率曲线(B)'
    CBD100932 = '中债企业债收益率曲线(CCC)'
    CBD100942 = '中债企业债收益率曲线(AAA-)'
    CBD100952 = '中债企业债收益率曲线(AA-)'
    CBD100962 = '中债商业银行普通债收益率曲线(AAA-)'
    CBD100972 = '中债浮动利率商业银行普通债(SHIBOR-3M-1D)点差曲线(AAA-)'
    CBD100982 = '中债浮动利率商业银行普通债(SHIBOR-3M-1D)点差曲线(AA+)'
    CBD100992 = '中债地方政府债收益率曲线(AAA-)'
    CBD101002 = '中债资产支持证券收益率曲线(AAA-)'
    CBD101012 = '中债资产支持证券收益率曲线(AA)'
    CBD101022 = '中债资产支持证券收益率曲线(AA-)'
    CBD101032 = '中债资产支持证券收益率曲线(A+)'
    CBD101042 = '中债浮动利率资产支持证券(Depo-1Y)点差曲线(AA)'
    CBD101052 = '中债农发行债收益率曲线'
    CBD101062 = '中债商业银行普通债收益率曲线(A)'
    CBD101072 = '中债商业银行普通债收益率曲线(A-)'
    CBD101092 = '中债商业银行二级资本债收益率曲线(AAA-)'
    CBD101102 = '中债商业银行二级资本债收益率曲线(AA+)'
    CBD101112 = '中债商业银行二级资本债收益率曲线(AA)'
    CBD101122 = '中债商业银行二级资本债收益率曲线(AA-)'
    CBD101132 = '中债商业银行二级资本债收益率曲线(A+)'
    CBD101142 = '中债商业银行二级资本债收益率曲线(A)'
    CBD101152 = '中债商业银行同业存单收益率曲线(AAA)'
    CBD101162 = '中债商业银行同业存单收益率曲线(AAA-)'
    CBD101172 = '中债商业银行同业存单收益率曲线(AA+)'
    CBD101182 = '中债商业银行同业存单收益率曲线(AA)'
    CBD101192 = '中债商业银行同业存单收益率曲线(AA-)'
    CBD101202 = '中债商业银行同业存单收益率曲线(A+)'
    CBD101212 = '中债商业银行同业存单收益率曲线(A)'
    CBD101222 = '中债商业银行同业存单收益率曲线(A-)'
    CBD101232 = '中债个人住房抵押贷款资产支持证券收益率曲线(AAA)'
    CBD101242 = '中债浮动利率个人住房抵押贷款资产支持证券(Loan-5Y)点差曲线(AAA)'
    CBD101252 = '中债中资美元债收益率曲线(A+)'
    CBD101262 = '中债中资美元债收益率曲线(A)'
    CBD101272 = '中债中资美元债收益率曲线(A-)'
    CBD101282 = '中债中资美元债收益率曲线(BBB+)'
    CBD101292 = '中债中资美元债收益率曲线(BBB)'
    CBD101302 = '中债中资美元债收益率曲线(BBB-)'
    CBD101312 = '中债消费金融资产支持证券收益率曲线(AAA)'
    CBD101322 = '中债消费金融资产支持证券收益率曲线(AA+)'
    CBD101332 = '中债消费金融资产支持证券收益率曲线(AA)'
    CBD101342 = '中债消费金融资产支持证券收益率曲线(AA-)'
    CBD101352 = '中债浮动利率消费金融资产支持证券(Loan-1Y)点差曲线(AAA)'
    CBD101362 = '中债浮动利率消费金融资产支持证券(Loan-1Y)点差曲线(AA+)'
    CBD101372 = '中债浮动利率消费金融资产支持证券(Loan-1Y)点差曲线(AA)'
    CBD101451 = '保险公司准备金计量基准收益率曲线'


class Currency(Enum):
    """Currency, ISO 4217 currency code or exchange quote modifier (e.g. GBP vs GBp)"""

    _ = ''
    ACU = 'ACU'
    ADP = 'ADP'
    AED = 'AED'
    AFA = 'AFA'
    ALL = 'ALL'
    AMD = 'AMD'
    ANG = 'ANG'
    AOA = 'AOA'
    AOK = 'AOK'
    AON = 'AON'
    ARA = 'ARA'
    ARS = 'ARS'
    ARZ = 'ARZ'
    ATS = 'ATS'
    AUD = 'AUD'
    AUZ = 'AUZ'
    AZM = 'AZM'
    B03 = 'B03'
    BAD = 'BAD'
    BAK = 'BAK'
    BAM = 'BAM'
    BBD = 'BBD'
    BDN = 'BDN'
    BDT = 'BDT'
    BEF = 'BEF'
    BGL = 'BGL'
    BGN = 'BGN'
    BHD = 'BHD'
    BIF = 'BIF'
    BMD = 'BMD'
    BND = 'BND'
    BR6 = 'BR6'
    BRE = 'BRE'
    BRF = 'BRF'
    BRL = 'BRL'
    BRR = 'BRR'
    BSD = 'BSD'
    BTC = 'BTC'
    BTN = 'BTN'
    BTR = 'BTR'
    BWP = 'BWP'
    BYR = 'BYR'
    BZD = 'BZD'
    C23 = 'C23'
    CAC = 'CAC'
    CAD = 'CAD'
    CAZ = 'CAZ'
    CCI = 'CCI'
    CDF = 'CDF'
    CFA = 'CFA'
    CHF = 'CHF'
    CHZ = 'CHZ'
    CLF = 'CLF'
    CLP = 'CLP'
    CLZ = 'CLZ'
    CNH = 'CNH'
    CNO = 'CNO'
    CNY = 'CNY'
    CNZ = 'CNZ'
    COP = 'COP'
    COZ = 'COZ'
    CPB = 'CPB'
    CPI = 'CPI'
    CRC = 'CRC'
    CUP = 'CUP'
    CVE = 'CVE'
    CYP = 'CYP'
    CZH = 'CZH'
    CZK = 'CZK'
    DAX = 'DAX'
    DEM = 'DEM'
    DIJ = 'DIJ'
    DJF = 'DJF'
    DKK = 'DKK'
    DOP = 'DOP'
    DZD = 'DZD'
    E51 = 'E51'
    E52 = 'E52'
    E53 = 'E53'
    E54 = 'E54'
    ECI = 'ECI'
    ECS = 'ECS'
    ECU = 'ECU'
    EEK = 'EEK'
    EF0 = 'EF0'
    EGP = 'EGP'
    ESP = 'ESP'
    ETB = 'ETB'
    EUR = 'EUR'
    EUZ = 'EUZ'
    F06 = 'F06'
    FED = 'FED'
    FIM = 'FIM'
    FJD = 'FJD'
    FKP = 'FKP'
    FRF = 'FRF'
    FT1 = 'FT1'
    GBP = 'GBP'
    GBZ = 'GBZ'
    GEK = 'GEK'
    GHC = 'GHC'
    GHS = 'GHS'
    GHY = 'GHY'
    GIP = 'GIP'
    GLR = 'GLR'
    GMD = 'GMD'
    GNF = 'GNF'
    GQE = 'GQE'
    GRD = 'GRD'
    GTQ = 'GTQ'
    GWP = 'GWP'
    GYD = 'GYD'
    HKB = 'HKB'
    HKD = 'HKD'
    HNL = 'HNL'
    HRK = 'HRK'
    HSI = 'HSI'
    HTG = 'HTG'
    HUF = 'HUF'
    IDB = 'IDB'
    IDO = 'IDO'
    IDR = 'IDR'
    IEP = 'IEP'
    IGP = 'IGP'
    ILS = 'ILS'
    INO = 'INO'
    INP = 'INP'
    INR = 'INR'
    IPA = 'IPA'
    IPX = 'IPX'
    IQD = 'IQD'
    IRR = 'IRR'
    IRS = 'IRS'
    ISI = 'ISI'
    ISK = 'ISK'
    ISO = 'ISO'
    ITL = 'ITL'
    J05 = 'J05'
    JMD = 'JMD'
    JNI = 'JNI'
    JOD = 'JOD'
    JPY = 'JPY'
    JPZ = 'JPZ'
    JZ9 = 'JZ9'
    KES = 'KES'
    KGS = 'KGS'
    KHR = 'KHR'
    KMF = 'KMF'
    KOR = 'KOR'
    KPW = 'KPW'
    KRW = 'KRW'
    KWD = 'KWD'
    KYD = 'KYD'
    KZT = 'KZT'
    LAK = 'LAK'
    LBA = 'LBA'
    LBP = 'LBP'
    LHY = 'LHY'
    LKR = 'LKR'
    LRD = 'LRD'
    LSL = 'LSL'
    LSM = 'LSM'
    LTL = 'LTL'
    LUF = 'LUF'
    LVL = 'LVL'
    LYD = 'LYD'
    MAD = 'MAD'
    MDL = 'MDL'
    MGF = 'MGF'
    MKD = 'MKD'
    MMK = 'MMK'
    MNT = 'MNT'
    MOP = 'MOP'
    MRO = 'MRO'
    MTP = 'MTP'
    MUR = 'MUR'
    MVR = 'MVR'
    MWK = 'MWK'
    MXB = 'MXB'
    MXN = 'MXN'
    MXP = 'MXP'
    MXW = 'MXW'
    MXZ = 'MXZ'
    MYO = 'MYO'
    MYR = 'MYR'
    MZM = 'MZM'
    MZN = 'MZN'
    NAD = 'NAD'
    ND3 = 'ND3'
    NGF = 'NGF'
    NGI = 'NGI'
    NGN = 'NGN'
    NIC = 'NIC'
    NLG = 'NLG'
    NOK = 'NOK'
    NOZ = 'NOZ'
    NPR = 'NPR'
    NZD = 'NZD'
    NZZ = 'NZZ'
    O08 = 'O08'
    OMR = 'OMR'
    PAB = 'PAB'
    PEI = 'PEI'
    PEN = 'PEN'
    PEZ = 'PEZ'
    PGK = 'PGK'
    PHP = 'PHP'
    PKR = 'PKR'
    PLN = 'PLN'
    PLZ = 'PLZ'
    PSI = 'PSI'
    PTE = 'PTE'
    PYG = 'PYG'
    QAR = 'QAR'
    R2K = 'R2K'
    ROL = 'ROL'
    RON = 'RON'
    RSD = 'RSD'
    RUB = 'RUB'
    RUF = 'RUF'
    RUR = 'RUR'
    RWF = 'RWF'
    SAR = 'SAR'
    SBD = 'SBD'
    SCR = 'SCR'
    SDP = 'SDP'
    SDR = 'SDR'
    SEK = 'SEK'
    SET = 'SET'
    SGD = 'SGD'
    SGS = 'SGS'
    SHP = 'SHP'
    SKK = 'SKK'
    SLL = 'SLL'
    SRG = 'SRG'
    SSI = 'SSI'
    STD = 'STD'
    SUR = 'SUR'
    SVC = 'SVC'
    SVT = 'SVT'
    SYP = 'SYP'
    SZL = 'SZL'
    T21 = 'T21'
    T51 = 'T51'
    T52 = 'T52'
    T53 = 'T53'
    T54 = 'T54'
    T55 = 'T55'
    T71 = 'T71'
    TE0 = 'TE0'
    TED = 'TED'
    TF9 = 'TF9'
    THB = 'THB'
    THO = 'THO'
    TMM = 'TMM'
    TND = 'TND'
    TNT = 'TNT'
    TOP = 'TOP'
    TPE = 'TPE'
    TPX = 'TPX'
    TRB = 'TRB'
    TRL = 'TRL'
    TRY = 'TRY'
    TRZ = 'TRZ'
    TTD = 'TTD'
    TWD = 'TWD'
    TZS = 'TZS'
    UAH = 'UAH'
    UCB = 'UCB'
    UDI = 'UDI'
    UFC = 'UFC'
    UFZ = 'UFZ'
    UGS = 'UGS'
    UGX = 'UGX'
    USB = 'USB'
    USD = 'USD'
    UVR = 'UVR'
    UYP = 'UYP'
    UYU = 'UYU'
    VAC = 'VAC'
    VEB = 'VEB'
    VEF = 'VEF'
    VES = 'VES'
    VND = 'VND'
    VUV = 'VUV'
    WST = 'WST'
    XAF = 'XAF'
    XAG = 'XAG'
    XAU = 'XAU'
    XPD = 'XPD'
    XPT = 'XPT'
    XCD = 'XCD'
    XDR = 'XDR'
    XEU = 'XEU'
    XOF = 'XOF'
    XPF = 'XPF'
    YDD = 'YDD'
    YER = 'YER'
    YUD = 'YUD'
    YUN = 'YUN'
    ZAL = 'ZAL'
    ZAR = 'ZAR'
    ZAZ = 'ZAZ'
    ZMK = 'ZMK'
    ZMW = 'ZMW'
    ZRN = 'ZRN'
    ZRZ = 'ZRZ'
    ZWD = 'ZWD'
    AUd = 'AUd'
    BWp = 'BWp'
    EUr = 'EUr'
    GBp = 'GBp'
    ILs = 'ILs'
    KWd = 'KWd'
    MWk = 'MWk'
    SGd = 'SGd'
    SZl = 'SZl'
    USd = 'USd'
    ZAr = 'ZAr'

    def __repr__(self):
        return self.value


class CurrencyPair(Enum):
    USDCNY = 'USD/CNY'
    JPYCNY = 'JPY/CNY'
    GBPCNY = 'GBP/CNY'
    NZDCNY = 'NZD/CNY'
    CHFCNY = 'CHF/CNY'
    CNYMYR = 'CNY/MYR'
    CNYZAR = 'CNY/ZAR'
    CNYAED = 'CNY/AED'
    CNYHUF = 'CNY/HUF'
    CNYDKK = 'CNY/DKK'
    CNYNOK = 'CNY/NOK'
    CNYMXN = 'CNY/MXN'
    EURCNY = 'EUR/CNY'
    HKDCNY = 'HKD/CNY'
    AUDCNY = 'AUD/CNY'
    SGDCNY = 'SGD/CNY'
    CADCNY = 'CAD/CNY'
    CNYRUB = 'CNY/RUB'
    CNYKRW = 'CNY/KRW'
    CNYSAR = 'CNY/SAR'
    CNYPLN = 'CNY/PLN'
    CNYSEK = 'CNY/SEK'
    CNYTRY = 'CNY/TRY'
    CNYTHB = 'CNY/THB'
    EURUSD = 'EUR/USD'

    def __repr__(self):
        return self.value


class RMBIRCurveType(Enum):
    Shibor = 'Shibor'
    Shibor3M = 'Shibor3M'
    FR007 = 'FR007'

    def __repr__(self):
        return self.value


class DiscountCurveType(Enum):
    Shibor3M = 'Shibor3M'
    Shibor3M_tr = 'Shibor3M_tr'
    CNYShibor3M = 'CNYShibor3M'
    FX_Implied = 'FX_Implied'
    FX_Implied_tr = 'FX_Implied_tr'
    USDLibor3M = 'USDLibor3M'
    FX_Forword = 'FX_Forword'
    FX_Forword_fq = 'FX_Forword_fq'
    FX_Forword_tr = 'FX_Forword_tr'


class SpotExchangeRateType(Enum):
    Central = 'central'
    Average = 'average'

    def __repr__(self):
        return self.value


class OptionSettlementMethod(Enum):
    """How the option is settled (e.g. Cash, Physical)"""

    Cash = 'Cash'
    Physical = 'Physical'

    def __repr__(self):
        return self.value


class AssetClass(Enum):
    """Asset classification of security. Assets are classified into broad groups
       which exhibit similar characteristics and behave in a consistent way
       under different market conditions"""

    Cash = 'Cash'
    Commod = 'Commod'
    Credit = 'Credit'
    Cross_Asset = 'Cross Asset'
    Econ = 'Econ'
    Equity = 'Equity'
    Fund = 'Fund'
    FX = 'FX'
    Mortgage = 'Mortgage'
    Rates = 'Rates'
    Loan = 'Loan'
    Social = 'Social'
    Cryptocurrency = 'Cryptocurrency'

    def __repr__(self):
        return self.value


class AssetType(Enum):
    """Asset type differentiates the product categorization or contract type"""

    Access = 'Access'
    AssetSwapFxdFlt = 'AssetSwapFxdFlt'
    Any = 'Any'
    AveragePriceOption = 'AveragePriceOption'
    Basis = 'Basis'
    BasisSwap = 'BasisSwap'
    Benchmark = 'Benchmark'
    Benchmark_Rate = 'Benchmark Rate'
    Binary = 'Binary'
    Bond = 'Bond'
    BondFuture = 'BondFuture'
    BondFutureOption = 'BondFutureOption'
    BondOption = 'BondOption'
    Calendar_Spread = 'Calendar Spread'
    Cap = 'Cap'
    Cash = 'Cash'
    Certificate = 'Certificate'
    CD = 'CD'
    Cliquet = 'Cliquet'
    CMSOption = 'CMSOption'
    CMSOptionStrip = 'CMSOptionStrip'
    CMSSpreadOption = 'CMSSpreadOption'
    CMSSpreadOptionStrip = 'CMSSpreadOptionStrip'
    Commodity = 'Commodity'
    CommodityReferencePrice = 'CommodityReferencePrice'
    CommodVarianceSwap = 'CommodVarianceSwap'
    CommodityPowerNode = 'CommodityPowerNode'
    CommodityPowerAggregatedNodes = 'CommodityPowerAggregatedNodes'
    CommodityEUNaturalGasHub = 'CommodityEUNaturalGasHub'
    CommodityNaturalGasHub = 'CommodityNaturalGasHub'
    Company = 'Company'
    Convertible = 'Convertible'
    Credit_Basket = 'Credit Basket'
    Cross = 'Cross'
    CSL = 'CSL'
    Currency = 'Currency'
    Custom_Basket = 'Custom Basket'
    Cryptocurrency = 'Cryptocurrency'
    Default_Swap = 'Default Swap'
    Economic = 'Economic'
    Endowment = 'Endowment'
    Equity_Basket = 'Equity Basket'
    ETF = 'ETF'
    ETN = 'ETN'
    Event = 'Event'
    FRA = 'FRA'
    FixedLeg = 'FixedLeg'
    Fixing = 'Fixing'
    FloatLeg = 'FloatLeg'
    Floor = 'Floor'
    Forward = 'Forward'
    Fund = 'Fund'
    Future = 'Future'
    FutureContract = 'FutureContract'
    FutureMarket = 'FutureMarket'
    FutureOption = 'FutureOption'
    FutureStrategy = 'FutureStrategy'
    Hedge_Fund = 'Hedge Fund'
    Index = 'Index'
    InflationSwap = 'InflationSwap'
    Inter_Commodity_Spread = 'Inter-Commodity Spread'
    InvoiceSpread = 'InvoiceSpread'
    Market_Location = 'Market Location'
    MLF = 'MLF'
    Multi_Asset_Allocation = 'Multi-Asset Allocation'
    MultiCrossBinary = 'MultiCrossBinary'
    MultiCrossBinaryLeg = 'MultiCrossBinaryLeg'
    Mutual_Fund = 'Mutual Fund'
    Note = 'Note'
    Option = 'Option'
    OptionLeg = 'OptionLeg'
    OptionStrategy = 'OptionStrategy'
    Pension_Fund = 'Pension Fund'
    Preferred_Stock = 'Preferred Stock'
    Physical = 'Physical'
    Precious_Metal = 'Precious Metal'
    Precious_Metal_Swap = 'Precious Metal Swap'
    Precious_Metal_RFQ = 'Precious Metal RFQ'
    Reference_Entity = 'Reference Entity'
    Research_Basket = 'Research Basket'
    Rate = 'Rate'
    Risk_Premia = 'Risk Premia'
    Roll = 'Roll'
    Securities_Lending_Loan = 'Securities Lending Loan'
    Share_Class = 'Share Class'
    Single_Stock = 'Single Stock'
    Swap = 'Swap'
    SwapLeg = 'SwapLeg'
    SwapStrategy = 'SwapStrategy'
    Swaption = 'Swaption'
    Synthetic = 'Synthetic'
    Systematic_Hedging = 'Systematic Hedging'
    VarianceSwap = 'VarianceSwap'
    VolatilitySwap = 'VolatilitySwap'
    WeatherIndex = 'WeatherIndex'
    XccySwap = 'XccySwap'
    XccySwapFixFix = 'XccySwapFixFix'
    XccySwapFixFlt = 'XccySwapFixFlt'
    XccySwapMTM = 'XccySwapMTM'

    def __repr__(self):
        return self.value


class DayCountType(Enum):
    Actual360 = 'ACT/360'
    Actual364 = 'ACT/364'
    Actual365Fixed = 'ACT/365F'
    Thirty360 = '30/360'
    Thirty365 = '30/365'
    ActualActual = 'ACT/ACT'


class IBORType(Enum):
    Shibor = 'Shibor'
    Libor = 'Libor'
    Tibor = 'Tibor'
    Hibor = 'Hibor'
    Euribor = 'Euribor'


class IRType(Enum):
    FR007 = 'FR007'
    FDR001 = 'FDR001'
    FDR007 = 'FDR007'
    LPR1Y = 'LPR1Y'
    Shibor3M = 'Shibor3M'
    ShiborON = 'ShiborON'
    LPR5Y = 'LPR5Y'


class TuringFXATMMethod(Enum):
    SPOT = 1  # Spot FX Rate
    FWD = 2  # At the money forward
    FWD_DELTA_NEUTRAL = 3  # K = F*exp(0.5*sigma*sigma*T)
    FWD_DELTA_NEUTRAL_PREM_ADJ = 4  # K = F*exp(-0.5*sigma*sigma*T)


class TuringFXDeltaMethod(Enum):
    SPOT_DELTA = 1
    FORWARD_DELTA = 2
    SPOT_DELTA_PREM_ADJ = 3
    FORWARD_DELTA_PREM_ADJ = 4


class Ctx:
    def __init__(self):
        self.ctx = ctx

    @property
    def ctx_ytm(self):
        return getattr(ctx, f"ytm_{getattr(self, 'asset_id', '')}") or \
               getattr(ctx, f"ytm_{getattr(self, 'comb_symbol', '')}")

    @property
    def ctx_clean_price(self):
        return getattr(ctx, f"clean_price_{getattr(self, 'asset_id', '')}") or \
               getattr(ctx, f"clean_price_{getattr(self, 'comb_symbol', '')}")

    @property
    def ctx_spread_adjustment(self):
        return getattr(ctx, f"spread_adjustment_{getattr(self, 'asset_id', '')}") or \
               getattr(ctx, f"spread_adjustment_{getattr(self, 'comb_symbol', '')}")

    @property
    def ctx_spot(self):
        return getattr(ctx, f"spot_{getattr(self, 'asset_id', '')}") or \
               getattr(ctx, f"spot_{getattr(self, 'underlier', '')}")

    @property
    def ctx_volatility(self):
        return getattr(ctx, f"volatility_{getattr(self, 'asset_id', '')}") or \
               getattr(ctx, f"volatility_{getattr(self, 'underlier', '')}")

    @property
    def ctx_next_base_interest_rate(self):
        floating_rate_benchmark = getattr(self, 'floating_rate_benchmark', '')
        return getattr(ctx, f"next_base_interest_rate_{floating_rate_benchmark}")

    @property
    def ctx_fx_implied_volatility_curve(self):
        return getattr(ctx, f"fx_implied_volatility_curve_{getattr(self, 'asset_id', '')}") or \
               getattr(ctx, f"fx_implied_volatility_curve_{getattr(self, 'underlier', '')}")

    @property
    def ctx_irs_curve(self):
        return getattr(ctx, f"irs_curve_{getattr(self, 'asset_id', '')}") or \
               getattr(ctx, f"irs_curve_{getattr(self, 'underlier', '')}")

    @property
    def ctx_shibor_curve(self):
        return getattr(ctx, f"shibor_curve_{getattr(self, 'asset_id', '')}") or \
               getattr(ctx, f"shibor_curve_{getattr(self, 'underlier', '')}")

    @property
    def ctx_swap_curve(self):
        return getattr(ctx, f"swap_curve_{getattr(self, 'asset_id', '')}") or \
               getattr(ctx, f"swap_curve_{getattr(self, 'underlier', '')}")

    @property
    def ctx_interest_rate(self):
        return ctx.interest_rate

    @property
    def ctx_dividend_yield(self):
        return ctx.dividend_yield

    @property
    def ctx_pricing_date(self):
        return ctx.pricing_date

    @property
    def ctx_parallel_shift(self):
        return getattr(ctx, f"parallel_shift_{self.curve_code}")

    @property
    def ctx_curve_shift(self):
        return getattr(ctx, f"curve_shift_{self.curve_code}")

    @property
    def ctx_pivot_point(self):
        return getattr(ctx, f"pivot_point_{self.curve_code}")

    @property
    def ctx_tenor_start(self):
        return getattr(ctx, f"tenor_start_{self.curve_code}")

    @property
    def ctx_tenor_end(self):
        return getattr(ctx, f"tenor_end_{self.curve_code}")

    def ctx_yield_curve(self, curve_type: str, forward_term: float = None):
        curve_code = getattr(self, 'curve_code', None)
        if forward_term is None:
            return getattr(ctx, f"yield_curve_{curve_code}_{curve_type}")
        else:
            return getattr(ctx, f"yield_curve_{curve_code}_{curve_type}_{forward_term}")


class Priceable(Ctx):
    pass


class Eq(Priceable, metaclass=ABCMeta):

    @abstractmethod
    def price(self):
        pass

    @abstractmethod
    def eq_delta(self):
        pass

    @abstractmethod
    def eq_gamma(self):
        pass

    @abstractmethod
    def eq_vega(self):
        pass

    @abstractmethod
    def eq_theta(self):
        pass

    @abstractmethod
    def eq_rho(self):
        pass

    @abstractmethod
    def eq_rho_q(self):
        pass


class FX(Priceable, metaclass=ABCMeta):

    @abstractmethod
    def price(self):
        pass

    @abstractmethod
    def fx_delta(self):
        pass

    @abstractmethod
    def fx_gamma(self):
        pass

    @abstractmethod
    def fx_vega(self):
        pass

    @abstractmethod
    def fx_theta(self):
        pass

    @abstractmethod
    def fx_vanna(self):
        pass

    @abstractmethod
    def fx_volga(self):
        pass


class IR(Priceable, metaclass=ABCMeta):

    @abstractmethod
    def dv01(self):
        pass

    @abstractmethod
    def dollar_duration(self):
        pass

    @abstractmethod
    def dollar_convexity(self):
        pass


class CD(Priceable, metaclass=ABCMeta):
    pass


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class CurveAdjustment:
    """存放曲线旋转平移参数"""
    parallel_shift: float = None  # 平移量（bps)
    curve_shift: float = None  # 旋转量（bps)
    pivot_point: float = None  # 旋转点（年）
    tenor_start: float = None  # 旋转起始（年）
    tenor_end: float = None  # 旋转终点（年）

    def set_parallel_shift(self, value):
        self.parallel_shift = value

    def set_curve_shift(self, value):
        self.curve_shift = value

    def set_pivot_point(self, value):
        self.pivot_point = value

    def set_tenor_start(self, value):
        self.tenor_start = value

    def set_tenor_end(self, value):
        self.tenor_end = value

    def isvalid(self):
        return self.parallel_shift or self.curve_shift \
               or self.pivot_point or self.tenor_start \
               or self.tenor_end


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class Curve:
    value_date: Union[TuringDate, str] = None  # 估值日期
    curve_code: Union[str, YieldCurveCode] = None  # 曲线编码
    curve_name: str = None  # 曲线名称
    curve_data: pd.DataFrame = None  # 曲线数据，列索引为'tenor'和'rate'
    curve_type: str = 'spot_rate'  # TODO: 处理成枚举类型
    forward_term: float = None

    def __post_init__(self):
        """估值日期和曲线编码不能为空"""
        assert self.value_date, "value_date can't be None"
        self.check_param()

    def check_param(self):
        """对时间做格式校验和转换处理"""
        if isinstance(self.value_date, str) and self.value_date == 'latest':
            self.value_date = TuringDate(*(datetime.date.today().timetuple()[:3]))
            self._date_for_interface = 'latest'
        elif isinstance(self.value_date, TuringDate):
            self._date_for_interface = self.value_date
        else:
            raise TuringError("value must be 'latest'/TuringDate")

    def set_value_date(self, value):
        """设置估值日期"""
        self.value_date = value
        self.check_param()
        # 如果重新设置了value_date，则需要把原来的曲线数据清空，再通过以下两种方式补全曲线数据：
        # 1、调用resolve方法，根据新的value_date从接口获取曲线数据
        # 2、调用set_curve_data方法，从外部传入曲线数据
        self.curve_data = None

    def set_curve_data(self, value: pd.DataFrame):
        """设置曲线数据"""
        if isinstance(value, list):
            self.curve_data = pd.DataFrame(data=value)
        else:
            self.curve_data = value

    def set_forward_term(self, value: (float, int)):
        """设置远期期限"""
        self.forward_term = value
        # 如果重新设置了forward_term，同时curve_type为远期，则需要把原来的曲线数据清空，再通过以下两种方式补全曲线数据：
        # 1、调用resolve方法，根据新的forward_term从接口获取曲线数据
        # 2、调用set_curve_data方法，从外部传入曲线数据
        if self.curve_type == 'forward_spot_rate' or self.curve_type == 'forward_ytm':
            self.curve_data = None

    def resolve(self):
        """补全/更新数据"""
        if self.curve_code is not None:
            if isinstance(self.curve_code, YieldCurveCode):
                curve_code = self.curve_code.name
            else:
                curve_code = self.curve_code
            if self.curve_data is None:
                if self.curve_type == 'spot_rate':
                    self.curve_data = TuringDB.bond_yield_curve(curve_code=curve_code, date=self._date_for_interface)
                    if not self.curve_data.empty:
                        self.curve_data = self.curve_data.loc[curve_code][['tenor', 'spot_rate']].\
                            rename(columns={'spot_rate': 'rate'})
                elif self.curve_type == 'ytm':
                    self.curve_data = TuringDB.bond_yield_curve(curve_code=curve_code, date=self._date_for_interface)
                    if not self.curve_data.empty:
                        self.curve_data = self.curve_data.loc[curve_code][['tenor', 'ytm']].\
                            rename(columns={'ytm': 'rate'})
                elif self.curve_type == 'forward_spot_rate':
                    if self.forward_term is not None and isinstance(self.forward_term, (float, int)):
                        self.curve_data = TuringDB.bond_yield_curve(curve_code=curve_code, date=self._date_for_interface,
                                                                    forward_term=self.forward_term)
                        if not self.curve_data.empty:
                            self.curve_data = self.curve_data.loc[curve_code][['tenor', 'forward_spot_rate']].\
                                rename(columns={'forward_spot_rate': 'rate'})
                    else:
                        raise TuringError('Please check the input of forward_term')
                elif self.curve_type == 'forward_ytm':
                    if self.forward_term is not None and isinstance(self.forward_term, (float, int)):
                        self.curve_data = TuringDB.bond_yield_curve(curve_code=curve_code, date=self._date_for_interface,
                                                                    forward_term=self.forward_term)
                        if not self.curve_data.empty:
                            self.curve_data = self.curve_data.loc[curve_code][['tenor', 'forward_ytm']].\
                                rename(columns={'forward_ytm': 'rate'})
                    else:
                        raise TuringError('Please check the input of forward_term')
                else:
                    raise TuringError('Please check the input of curve_type')
            if self.curve_name is None:
                self.curve_name = getattr(YieldCurveCode, curve_code, '')
        else:
            if self.curve_data is None:
                raise TuringError("curve_code and curve_data can't be empty at the same time")

    def adjust(self, ca: CurveAdjustment):
        """曲线旋转平移"""
        parallel_shift = ca.parallel_shift
        curve_shift = ca.curve_shift
        pivot_point = ca.pivot_point
        tenor_start = ca.tenor_start
        tenor_end = ca.tenor_end
        ca_impl = CurveAdjustmentImpl(self.curve_data,  # 曲线信息
                                      parallel_shift,  # 平移量（bps)
                                      curve_shift,  # 旋转量（bps)
                                      pivot_point,  # 旋转点（年）
                                      tenor_start,  # 旋转起始（年）
                                      tenor_end,  # 旋转终点（年）
                                      self.value_date)
        self.curve_data = ca_impl.get_curve_data()

    def discount_curve(self):
        """生成折现曲线"""
        tenors = self.curve_data['tenor'].tolist()
        dates = self.value_date.addYears(tenors)
        rates = self.curve_data['rate'].tolist()
        return TuringDiscountCurveZeros(valuationDate=self.value_date,
                                        zeroDates=dates,
                                        zeroRates=rates)


if __name__ == '__main__':
    cv = Curve(value_date='latest',
               curve_code='CBD100461')
    cv.resolve()
    print(cv.curve_data)

    # ca = CurveAdjustment(parallel_shift=1000,
    #                      curve_shift=1000,
    #                      pivot_point=1,
    #                      tenor_start=0.5,
    #                      tenor_end=1.5)
    # cv.adjust(ca)
    # print(cv.curve_data)
