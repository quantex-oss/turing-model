import inspect
import traceback
from typing import Union, List, Iterable

from fundamental import PricingContext
from fundamental.base import ctx, Context
from turing_models.constants import ParallelType
from turing_models.instruments.common import RiskMeasure
from turing_models.parallel.parallel_proxy import ParallelCalcProxy


class IsPriceable:
    def __get__(self, instance, owner):
        if instance.__class__.__name__ == "Position":
            class_names = self.get_classes(instance)
            if "Priceable" not in class_names:
                raise Exception(f"Position的tradable不支持类型: {instance.tradable.__class__.__name__}")
            return

    def get_classes(self, instance):
        class_names = [x.__name__ for x in inspect.getmro(instance.tradable.__class__)]
        return class_names


class InstrumentBase:
    _ = IsPriceable()

    def __init__(self):
        self.ctx: Context = ctx
        self.check_param()

    def check_param(self):
        getattr(self, '_')

    def calc(self, risk_measure: Union[RiskMeasure, List[RiskMeasure]], parallel_type=ParallelType.NULL,
             option_all=None, timeout=None):
        result: Union[float, List] = []
        try:
            if ParallelType.valid(parallel_type):
                return ParallelCalcProxy(
                    instance=self,
                    parallel_type=parallel_type,
                    call_func_name="calc",
                    func_params={"risk_measure": risk_measure},
                    timeout=timeout or 30
                ).calc()
            if not isinstance(risk_measure, Iterable) or isinstance(risk_measure, str):
                rs = risk_measure.value if isinstance(risk_measure, RiskMeasure) else risk_measure
                result = getattr(self, rs)() if not option_all else getattr(self, rs)(option_all)
                result = self._calc(risk_measure, result)
                return result
            for risk in risk_measure:
                rs = risk.value if isinstance(risk, RiskMeasure) else risk
                res = getattr(self, rs)()
                res = self._calc(risk, res)
                result.append(res)
            return result
        except Exception as e:
            traceback.print_exc()
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
            getattr(self, '_resolve')()
        else:
            self._set_by_dict(expand_dict)
        getattr(self, "__post_init__")()

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
