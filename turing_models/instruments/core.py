import datetime
import traceback
from typing import Union, List, Iterable

from fundamental import PricingContext
from fundamental.base import ctx, Context
from turing_models.constants import ParallelType
from turing_models.instruments.common import RiskMeasure
from turing_models.instruments.parallel_proxy import ParallelCalcProxy
from turing_models.market.curves.discount_curve_zeros import TuringDiscountCurveZeros
from turing_models.utilities import TuringFrequencyTypes
from turing_models.utilities.error import TuringError
from turing_models.utilities.turing_date import TuringDate


class InstrumentBase:

    def __init__(self):
        self.ctx: Context = ctx

    def calc(self, risk_measure: Union[RiskMeasure, List[RiskMeasure]], parallel_type=ParallelType.NULL,
             option_all=None):
        result: Union[float, List] = []
        try:
            if ParallelType.valid(parallel_type):
                return ParallelCalcProxy(
                    instance=self,
                    parallel_type=parallel_type,
                    call_func_name="calc",
                    func_params={"risk_measure": risk_measure}
                ).calc()
            if isinstance(risk_measure, str) and risk_measure in RiskMeasure.__members__:
                risk_measure = RiskMeasure.__members__[risk_measure]
            if not isinstance(risk_measure, Iterable):
                result = getattr(self, risk_measure.value)() if not option_all else getattr(self, risk_measure.value)(
                    option_all)
                result = self._calc(risk_measure, result)
                return result
            for risk in risk_measure:
                res = getattr(self, risk.value)()
                res = self._calc(risk, res)
                result.append(res)
            return result
        except Exception as e:
            traceback.format_exc()
            return ""

    def _calc(self, risk, value):
        """二次计算,默认为直接返回当前值"""
        return value

    def _set_by_dict(self, tmp_dict):
        for k, v in tmp_dict.items():
            if v:
                setattr(self, k, v)

    def type(self):
        pass

    def resolve(self, expand_dict=None):
        if not expand_dict:
            """手动resolve,自动补全未传入参数"""
            class_names = ["KnockOutOption", "Stock", "FXVanillaOption"]
            class_name = []
            class_name.append(self.__class__.__name__)
            [class_name.append(x.__name__) for x in self.__class__.__bases__]
            if class_name in class_names:
                self._resolve()
            else:
                raise Exception("暂不支持此类型的Resolve")
        else:
            self._set_by_dict(expand_dict)
        self.__post_init__()

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

    def main(self, context=None, assetId: str = None, pricingContext=None, riskMeasure=None):
        if context:
            self.ctx.context = context
        print(ctx.context)
        """api默认入口"""
        scenario = PricingContext()
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
