import datetime
import traceback
from typing import Union, List, Iterable

from loguru import logger


from fundamental import ctx, PricingContext

from fundamental.base import Context
from fundamental.market.curves.discount_curve_zeros import TuringDiscountCurveZeros
from turing_models.instruments.common import RiskMeasure
from turing_models.utilities import TuringFrequencyTypes
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.error import TuringError
from .parallel_proxy import ParallelCalcProxy


class InstrumentBase:

    def __init__(self):
        self.ctx: Context = ctx

    def calc(self, risk_measure: Union[RiskMeasure, List[RiskMeasure]], parallel_type=None, option_all=None):
        result: Union[float, List] = []

        try:
            if parallel_type:
                return ParallelCalcProxy(self, parallel_type, risk_measure).calc()

            if not isinstance(risk_measure, Iterable):
                result = getattr(self, risk_measure.value)() if not option_all else getattr(self, risk_measure.value)(
                    option_all)
                result = self._calc(result)
                self.__row__(risk_measure.value, round(
                    result, 2) if result else 0)
                return result
            for risk in risk_measure:
                res = getattr(self, risk.value)()
                res = self._calc(res)
                result.append(res)
                self.__row__(risk.value, round(res, 2)
                             if res and not isinstance(res, Iterable) else 0)
            return result
        except Exception as e:
            logger.error(str(traceback.format_exc()))
            return ""

    def _calc(self, value):
        """二次计算,默认为直接返回当前值"""
        return value

    def __row__(self, ident, _value):
        """计算后对表格数据进行填充"""
        if self.__class__.__name__ == "Position" and hasattr(self.ctx, "positions_dict"):
            for key, value in self.ctx.positions_dict.items():
                if value.get('asset_id') == self.tradable.asset_id if self.tradable else "":
                    value[ident] = _value

    def _set_by_dict(self, tmp_dict):
        for k, v in tmp_dict.items():
            if v:
                setattr(self, k, v)

    def resolve(self, expand_dict=None):
        if not expand_dict:
            """手动resolve,自动补全未传入参数"""
            class_name = []
            class_name.append(self.__class__.__name__)
            [class_name.append(x.__name__) for x in self.__class__.__bases__]
            logger.debug(class_name)
            if "KnockOutOption" in class_name:
                self.option_resolve()
            elif "Stock" in class_name:
                self.stock_resolve()
            else:
                raise Exception("暂不支持此类型的Resolve")
        else:
            self._set_by_dict(expand_dict)
        self.set_param()

    def type(self):
        pass

    def resolve(self, expand_dict=None):
        if not expand_dict:
            """手动resolve,自动补全未传入参数"""
            class_name = []
            class_name.append(self.__class__.__name__)
            [class_name.append(x.__name__) for x in self.__class__.__bases__]
            logger.debug(class_name)
            if "KnockOutOption" in class_name:
                self._resolve()
            elif "Stock" in class_name:
                self._resolve()
            else:
                raise Exception("暂不支持此类型的Resolve")
        else:
            self._set_by_dict(expand_dict)
        self.set_param()

    def api_calc(self, riskMeasure: list):
        """api calc 结果集"""
        msg = ''
        response_data = []
        if riskMeasure:
            for risk_fun in riskMeasure:
                try:
                    result = getattr(self, risk_fun)()
                except Exception as e:
                    traceback.print_exc()
                    msg += f'{risk_fun} error: {str(e)};'
                    result = ''
                    msg += f'调用{risk_fun}出错;'
                response = {}
                response['riskMeasure'] = risk_fun
                response['value'] = result
                response_data.append(response)
        return response_data

    def main(self, assetId: str = None, pricingContext=None, riskMeasure=None):
        """api默认入口"""
        scenario = PricingContext()
        logger.debug(f"assetId:{assetId}")
        if not assetId.startswith("OPTION") and not assetId.startswith("BOND"):
            raise Exception("不支持的asset_id")
        setattr(self, 'asset_id', assetId)
        getattr(self, '_resolve')()

        if pricingContext:
            scenario.resolve(pricingContext)
            with scenario:
                return self.api_calc(riskMeasure)
        else:
            return self.api_calc(riskMeasure)

    def __repr__(self):
        return self.__class__.__name__


class CurveAdjust:

    def __init__(self,
                 dates: list,
                 rates: list,
                 parallel_shift=None,
                 curve_shift=None,
                 pivot_point=None,
                 tenor_start=None,
                 tenor_end=None):
        self.dates = dates
        self.rates = rates
        if parallel_shift:
            self.parallel_shift = parallel_shift * 0.0001
        if curve_shift:
            self.curve_shift = curve_shift * 0.0001
        self.pivot_point = pivot_point  # 单位：年
        self.tenor_start = tenor_start  # 单位：年
        self.tenor_end = tenor_end  # 单位：年

        self.today = TuringDate(*(datetime.date.today().timetuple()[:3]))
        self.pivot_rate = None
        self.start_rate = None
        self.end_rate = None
        self.pivot_index = None
        self.start_index = None
        self.end_index = None
        self.curve_parallel_shift()

        if curve_shift:
            if not self.pivot_point:
                self.pivot_point = self.dates[0]

            if self.pivot_point > self.dates[-1] or self.pivot_point < self.dates[0]:
                raise TuringError("Please check the input of pivot_point")

            self.confirm_center_point()
            self.modify_data()
            self.get_data_index()
            self.rotate_curve()

    def curve_parallel_shift(self):
        if hasattr(self, "parallel_shift"):
            self.rates = [x + self.parallel_shift for x in self.rates]

    def confirm_center_point(self):
        dates = self.today.addYears(self.dates)
        curve = TuringDiscountCurveZeros(self.today, dates, self.rates)
        point_date = self.today.addYears(self.pivot_point)
        self.pivot_rate = curve.zeroRate(
            point_date, freqType=TuringFrequencyTypes.ANNUAL)

        if self.tenor_start:
            start_date = self.today.addYears(self.tenor_start)
            self.start_rate = curve.zeroRate(
                start_date, freqType=TuringFrequencyTypes.ANNUAL)
        else:
            self.tenor_start = self.dates[0]
            self.start_rate = self.rates[0]

        if self.tenor_end:
            end_date = self.today.addYears(self.tenor_end)
            self.end_rate = curve.zeroRate(
                end_date, freqType=TuringFrequencyTypes.ANNUAL)
        else:
            self.tenor_end = self.dates[-1]
            self.end_rate = self.rates[-1]

    def modify_data(self):
        if self.pivot_point not in self.dates:
            dates_copy = self.dates.copy()
            for i in range(len(dates_copy)):
                if dates_copy[i] > self.pivot_point:
                    break
            self.dates.insert(i, self.pivot_point)
            self.rates.insert(i, self.pivot_rate)

        if self.tenor_start not in self.dates:
            dates_copy = self.dates.copy()
            for i in range(len(dates_copy)):
                if dates_copy[i] > self.tenor_start:
                    break
            self.dates.insert(i, self.tenor_start)
            self.rates.insert(i, self.start_rate)

        if self.tenor_end not in self.dates:
            dates_copy = self.dates.copy()
            for i in range(len(dates_copy)):
                if dates_copy[i] > self.tenor_end:
                    break
            self.dates.insert(i, self.tenor_end)
            self.rates.insert(i, self.end_rate)

    def get_data_index(self):
        self.pivot_index = self.dates.index(self.pivot_point)
        self.start_index = self.dates.index(self.tenor_start)
        self.end_index = self.dates.index(self.tenor_end)

    def rotate_curve(self):
        rates_copy = self.rates.copy()
        dr = self.curve_shift / (self.end_index - self.start_index)
        for i in range(len(rates_copy)):
            if i >= self.start_index and i <= self.end_index:
                self.rates[i] = (i - self.pivot_index) * dr + rates_copy[i]
            elif i < self.start_index:
                self.rates[i] = (self.start_index -
                                 self.pivot_index) * dr + rates_copy[i]
            elif i > self.end_index:
                self.rates[i] = (self.end_index -
                                 self.pivot_index) * dr + rates_copy[i]

    def get_dates_result(self):
        return self.dates

    def get_rates_result(self):
        return self.rates

    def get_data_dict(self):
        return dict(zip(self.dates, self.rates))
