import os
import sys
from dataclasses import dataclass

import QuantLib as ql
import pandas as pd

from fundamental.turing_db.option_data import FxOptionApi
from turing_models.instruments.common import DiscountCurveType, DayCountType
from turing_models.instruments.fx.fx_option import FXOption
from turing_models.market.curves.curve_generation import FXForwardCurveGen, DomDiscountCurveGen, ForDiscountCurveGen
from turing_models.market.data.updated_for_rm_utils import calendarModifyChina
from turing_models.market.volatility.vol_surface_generation import FXVolSurfaceGen
from turing_models.models.model_volatility_fns import TuringVolFunctionTypes
from turing_models.instruments.fx.fx_quanto_digital_ql import FXQuantoDigitalQL
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import TuringOptionType
from turing_models.utilities.turing_date import TuringDate


current_path = os.path.dirname(__file__)


def trdate_to_qldate(date: TuringDate):
    """ Convert TuringDate to ql.Date """
    if date and isinstance(date, TuringDate):
        return ql.Date(date._d, date._m, date._y)


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class FXQuantoDigital(FXOption):

    accrual_start: TuringDate = None
    accrual_end: TuringDate = None
    observe_start_date: TuringDate = None
    observe_end_date: TuringDate = None
    coupon_rate: float = None
    correlation_fd_dq: float = None
    day_count: (str, DayCountType, ql.DayCounter) = None

    calendar: ql.Calendar = calendarModifyChina(ql.China(ql.China.IB))
    convention = ql.ModifiedFollowing

    def __post_init__(self):
        super().__post_init__()
        self.trade_direction = 'long'  # 模型默认为买方角度
        self.accrual_start_ql = trdate_to_qldate(self.accrual_start)
        self.accrual_end_ql = trdate_to_qldate(self.accrual_end)
        self.observe_start_date_ql = trdate_to_qldate(self.observe_start_date)
        self.observe_end_date_ql = trdate_to_qldate(self.observe_end_date)

        if self.accrual_start and not self.start_date:
            self.start_date = self.accrual_start

        if self.domestic_name and self.notional_currency:
            self.d_q_symbol = self.domestic_name + '/' + self.notional_currency

        if self.option_type:
            if self.option_type == "CALL" or self.option_type == "call" or self.option_type == TuringOptionType.CALL:
                self.option_type = "call"
            elif self.option_type == "PUT" or self.option_type == "put" or self.option_type == TuringOptionType.PUT:
                self.option_type = "put"
            else:
                raise TuringError('Please check the input of option_type')

        if self.day_count:
            # 把day_count转为ql.DayCounter
            if isinstance(self.day_count, ql.DayCounter):
                pass
            if self.day_count == 'ACT/360' or self.day_count == DayCountType.Actual360:
                self.day_count = ql.Actual360()
            elif self.day_count == 'ACT/364' or self.day_count == DayCountType.Actual364:
                self.day_count = ql.Actual364()
            elif self.day_count == 'ACT/365F' or self.day_count == DayCountType.Actual365Fixed:
                self.day_count = ql.Actual365Fixed()
            elif self.day_count == '30/360' or self.day_count == DayCountType.Thirty360:
                self.day_count = ql.Thirty360()
            elif self.day_count == '30/365' or self.day_count == DayCountType.Thirty365:
                self.day_count = ql.Thirty365()
            elif self.day_count == 'ACT/ACT' or self.day_count == DayCountType.ActualActual:
                self.day_count = ql.ActualActual()
            else:
                raise TuringError('Please check the input of day_count')

        # 从excel获取数据
        platform = sys.platform
        if platform.startswith('win'):
            self.mkt_file = '/'.join(current_path.split("\\")[:-2])+'/market/data/value1117.xls'
        elif platform.startswith('darwin'):
            self.mkt_file = '/'.join(current_path.split("/")[:-2])+'/market/data/value1117.xls'
        # 1
        self.spot_rate = pd.read_excel(self.mkt_file, 'Spot_Rate')
        self.spot_f_d = self.spot_rate.loc[0, 'Spot_f_d']  # EURUSD
        self.spot_d_q = self.spot_rate.loc[0, 'Spot_d_q']  # USDCNY
        if not self.correlation_fd_dq:
            self.correlation_fd_dq = self.spot_rate.loc[0, 'Correlation']
        if not self.strike:
            self.strike = self.spot_f_d
        # 2
        self.fwd_fd_data = pd.read_excel(self.mkt_file, 'EURUSD_Futures')[['Tenor', 'Date', 'Spread']]
        self.fwd_fd_data['Spread'] = self.fwd_fd_data['Spread'] / 10000
        self.fwd_fd_data.loc[0, 'Tenor'], self.fwd_fd_data.loc[1, 'Tenor'] = '1D', '3D'
        self.fwd_dq_data = pd.read_excel(self.mkt_file, 'USDCNY_Futures')[['Tenor', 'Date', 'Spread']]
        self.fwd_dq_data['Spread'] = self.fwd_dq_data['Spread'] / 10000
        self.fwd_dq_data.loc[0, 'Tenor'], self.fwd_dq_data.loc[1, 'Tenor'] = '1D', '3D'
        # 3
        self.vol_data_fd = pd.read_excel(self.mkt_file, 'EURUSD_vols')[
            ['Tenor', 'Date', 'ATM', '25DRR', '25DBF', '10DRR', '10DBF']]
        self.vol_data_dq = pd.read_excel(self.mkt_file, 'USDCNY_vols')[
            ['Tenor', 'Date', 'ATM', '25DRR', '25DBF', '10DRR', '10DBF']]
        # 4
        self.CNYShibor3M_data = pd.read_excel(self.mkt_file, 'CNYShibor')[['Tenor', 'Date', 'Rate']]
        self.CNYShibor3M_fixing = pd.read_excel(self.mkt_file, 'CNYShibor3M_fixing')[['Date', 'Fixing']]
        # 5
        self.USDLibor3M_data = pd.read_excel(self.mkt_file, 'USDLibor')[['Tenor', 'Date', 'Rate']]
        self.USDLibor3M_fixing = pd.read_excel(self.mkt_file, 'USDLibor3M_fixing')[['Date', 'Fixing']]

        if self.domestic_name and self.foreign_name and self.notional_currency \
           and self.strike and self.accrual_start_ql and self.accrual_end_ql \
           and self.observe_start_date_ql and self.observe_end_date_ql \
           and self.option_type and self.notional and self.coupon_rate and self.trade_direction:
            self.option = FXQuantoDigitalQL(f_ccy=self.foreign_name,
                                            d_ccy=self.domestic_name,
                                            q_ccy=self.notional_currency,
                                            strike=self.strike,
                                            accrualStart=self.accrual_start_ql,
                                            accrualEnd=self.accrual_end_ql,
                                            obs_start=self.observe_start_date_ql,
                                            obs_end=self.observe_end_date_ql,
                                            flavor=self.option_type,
                                            notional=self.notional,
                                            coupon_rate=self.coupon_rate,
                                            tradeDirection=self.trade_direction)

    @property
    def get_exchange_rate(self):
        # TODO: 接口无'EUR/USD'的数据
        return {'EUR/USD': self.spot_f_d, 'USD/CNY': self.spot_d_q}
        # return TuringDB.exchange_rate(symbol=[self.underlier_symbol, self.d_q_symbol],
        #                               date=self.value_date_interface)

    # TODO: 解决ctx不兼容存在两个货币对的情况
    @property
    def exchange_rate_f_d(self):
        return self.ctx_spot or self.get_exchange_rate[self.underlier_symbol]

    @property
    def exchange_rate_d_q(self):
        return self.get_exchange_rate[self.d_q_symbol]

    @property
    def get_fx_swap_data(self):
        # TODO: 接口无'EUR/USD'相关数据，同时接口中的'USD/CNY'
        # swap_dict = TuringDB.swap_curve(symbol=self.d_q_symbol,
        #                                 date=self.value_date_interface)
        swap_dict = {}
        swap_dict['EUR/USD'] = self.fwd_fd_data
        swap_dict['USD/CNY'] = self.fwd_dq_data
        return swap_dict

    @property
    def get_shibor_swap_data(self):
        return self.CNYShibor3M_data

    @property
    def get_shibor_swap_fixing_data(self):
        return self.CNYShibor3M_fixing

    @property
    def get_libor_swap_data(self):
        # TODO: 暂无USDLibor3M数据接口
        return self.USDLibor3M_data

    @property
    def get_libor_swap_fixing_data(self):
        return self.USDLibor3M_fixing

    @property
    def domestic_discount_curve_f_d(self):
        return DomDiscountCurveGen(value_date=self.value_date_,
                                   libor_swap_origin_tenors=self.get_libor_swap_data['Tenor'],
                                   libor_swap_rates=self.get_libor_swap_data['Rate'],
                                   libor_swap_fixing_dates=self.get_libor_swap_fixing_data['Date'],
                                   libor_swap_fixing_rates=self.get_libor_swap_fixing_data['Fixing'],
                                   curve_type=DiscountCurveType.USDLibor3M).discount_curve

    @property
    def foreign_discount_curve_f_d(self):
        return ForDiscountCurveGen(value_date=self.value_date_,
                                   domestic_discount_curve=self.domestic_discount_curve_f_d,
                                   fx_forward_curve=self.fx_forward_curve_f_d,
                                   curve_type=DiscountCurveType.FX_Implied).discount_curve

    @property
    def domestic_discount_curve_d_q(self):
        return DomDiscountCurveGen(value_date=self.value_date_,
                                   shibor_swap_origin_tenors=self.get_shibor_swap_data['Tenor'],
                                   shibor_swap_rates=self.get_shibor_swap_data['Rate'],
                                   shibor_swap_fixing_dates=self.CNYShibor3M_fixing['Date'],
                                   shibor_swap_fixing_rates=self.CNYShibor3M_fixing['Fixing'],
                                   curve_type=DiscountCurveType.CNYShibor3M).discount_curve

    @property
    def fx_forward_curve_f_d(self):
        return FXForwardCurveGen(value_date=self.value_date_,
                                 exchange_rate=self.exchange_rate_f_d,
                                 fx_swap_origin_tenors=self.get_fx_swap_data[self.underlier_symbol]['Tenor'],
                                 fx_swap_quotes=self.get_fx_swap_data[self.underlier_symbol]['Spread'],
                                 calendar=ql.UnitedStates(),
                                 day_count=ql.Actual365Fixed(),
                                 curve_type=DiscountCurveType.FX_Forword_fq).discount_curve

    @property
    def fx_forward_curve_d_q(self):
        return FXForwardCurveGen(value_date=self.value_date_,
                                 exchange_rate=self.exchange_rate_d_q,
                                 fx_swap_origin_tenors=self.get_fx_swap_data[self.d_q_symbol]['Tenor'],
                                 fx_swap_quotes=self.get_fx_swap_data[self.d_q_symbol]['Spread'],
                                 calendar=ql.China(ql.China.IB),
                                 day_count=ql.Actual365Fixed(),
                                 curve_type=DiscountCurveType.FX_Forword_fq).discount_curve

    @property
    def get_fx_implied_vol_data(self):
        # return TuringDB.fx_implied_volatility_curve(symbol=[self.underlier_symbol, self.d_q_symbol],
        #                                             volatility_type=["ATM", "25D BF", "25D RR", "10D BF", "10D RR"],
        #                                             date=self.value_date_interface)
        vols = {}
        vols['EUR/USD'], vols['USD/CNY'] = self.vol_data_fd, self.vol_data_dq
        return vols

    @property
    def volatility_surface_f_d(self):
        if self.underlier_symbol:
            return FXVolSurfaceGen(value_date=self.value_date_,
                                   currency_pair=self.underlier_symbol,
                                   exchange_rate=self.exchange_rate_f_d,
                                   domestic_discount_curve=self.domestic_discount_curve_f_d,
                                   foreign_discount_curve=self.foreign_discount_curve_f_d,
                                   fx_forward_curve=self.fx_forward_curve_f_d,
                                   # tenors=self.get_fx_implied_vol_data[self.underlier_symbol]["Tenor"],
                                   origin_tenors=self.get_fx_implied_vol_data[self.underlier_symbol]["Tenor"],
                                   atm_vols=self.get_fx_implied_vol_data[self.underlier_symbol]["ATM"],
                                   butterfly_25delta_vols=self.get_fx_implied_vol_data[self.underlier_symbol]["25DBF"],
                                   risk_reversal_25delta_vols=self.get_fx_implied_vol_data[self.underlier_symbol]["25DRR"],
                                   butterfly_10delta_vols=self.get_fx_implied_vol_data[self.underlier_symbol]["10DBF"],
                                   risk_reversal_10delta_vols=self.get_fx_implied_vol_data[self.underlier_symbol]["10DRR"],
                                   volatility_function_type=TuringVolFunctionTypes.QL,
                                   calendar=self.calendar,
                                   convention=self.convention,
                                   day_count=self.day_count).volatility_surface

    @property
    def volatility_surface_d_q(self):
        if self.d_q_symbol:
            return FXVolSurfaceGen(value_date=self.value_date_,
                                   currency_pair=self.d_q_symbol,
                                   exchange_rate=self.exchange_rate_d_q,
                                   domestic_discount_curve=self.domestic_discount_curve_d_q,
                                   foreign_discount_curve=self.domestic_discount_curve_d_q,
                                   fx_forward_curve=self.fx_forward_curve_d_q,
                                   # tenors=self.get_fx_implied_vol_data[self.d_q_symbol]["tenor"],
                                   origin_tenors=self.get_fx_implied_vol_data[self.d_q_symbol]["Tenor"],
                                   atm_vols=self.get_fx_implied_vol_data[self.d_q_symbol]["ATM"],
                                   butterfly_25delta_vols=self.get_fx_implied_vol_data[self.d_q_symbol]["25DBF"],
                                   risk_reversal_25delta_vols=self.get_fx_implied_vol_data[self.d_q_symbol]["25DRR"],
                                   butterfly_10delta_vols=self.get_fx_implied_vol_data[self.d_q_symbol]["10DBF"],
                                   risk_reversal_10delta_vols=self.get_fx_implied_vol_data[self.d_q_symbol]["10DRR"],
                                   volatility_function_type=TuringVolFunctionTypes.QL,
                                   calendar=self.calendar,
                                   convention=self.convention,
                                   day_count=self.day_count).volatility_surface

    def params(self) -> list:
        return [
            self.value_date_ql,
            self.exchange_rate_f_d,
            self.exchange_rate_d_q,
            self.fx_forward_curve_f_d,
            self.fx_forward_curve_d_q,
            self.domestic_discount_curve_d_q,
            self.volatility_surface_f_d,
            self.volatility_surface_d_q,
            self.correlation_fd_dq,
            self.calendar,
            self.day_count,
            self.convention
        ]

    def price(self):
        return self.option.NPV(*self.params())

    def fx_delta(self):
        return self.option.Delta(*self.params())

    def fx_gamma(self):
        return self.option.Gamma(*self.params())

    def fx_vega(self):
        return self.option.Vega(*self.params())

    def quanto_vega(self):
        return self.option.QuantoVega(*self.params())

    def corr_sens(self):
        return self.option.Corr_sens(*self.params())

    def fx_theta(self):
        return 0

    def fx_vanna(self):
        return 0

    def fx_volga(self):
        return 0

    def set_property_list(self, curve, underlier, _property, key):
        _list = []
        for k, v in curve.items():
            if k == underlier:
                for cu in v.get('iuir_curve_data'):
                    _list.append(cu.get(key))
        setattr(self, _property, _list)
        return _list

    def spot_path(self):
        return 'turing_models.instruments.fx.fx.ForeignExchange'

    def _resolve(self):
        if self.asset_id and not self.asset_id.startswith("OPTION_"):
            temp_dict = FxOptionApi.fetch_fx_option(
                gurl=None, asset_id=self.asset_id)
            for k, v in temp_dict.items():
                if not getattr(self, k, None) and v:
                    setattr(self, k, v)
        self.resolve_param()

    def resolve_param(self):
        self.check_underlier()
        if not self.product_type:
            setattr(self, 'product_type', 'QUANTO_DIGITAL')
        self.__post_init__()
