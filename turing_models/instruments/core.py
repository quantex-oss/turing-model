import inspect
import traceback
from typing import Union, List, Iterable

from fundamental import PricingContext
from fundamental.base import ctx, Context
from turing_models.instruments.common import RiskMeasure
from turing_models.utilities.error import TuringError
from turing_utils.log.request_id_log import logger


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


class PricingMixin:
    """所有models的定价服务入口,默认走evaluation方法"""
    def __init__(self):
        self.ctx: Context = ctx

    def api_calc(self, risk_measure: list):
        """calc 结果集"""
        msg = ''
        response_data = []
        if risk_measure:
            if getattr(self, '_ctx_resolve', None) is not None:
                getattr(self, '_ctx_resolve')()
            if not getattr(self, 'isvalid')():
                raise TuringError(f"{getattr(self,'asset_id')}: is not valid")
            if isinstance(risk_measure, list):
                for risk_fun in risk_measure:
                    try:
                        result = getattr(self, risk_fun)()
                    except Exception as e:
                        traceback.print_exc()
                        msg += f'{risk_fun} error: {str(e)};'
                        result = ''
                        msg += f'调用{risk_fun}出错;'
                    response = {}
                    response['risk_measure'] = risk_fun
                    response['value'] = result
                    response_data.append(response)
            elif isinstance(risk_measure, str):
                result = getattr(self, risk_measure)()
                return result
        return response_data

    def api_data(self, **kw):
        for k, v in kw.items():
            for _k, _v in self.__dict__.items():
                if k == _k:
                    setattr(self, k, v)
                else:
                    setattr(self.ctx, k, v)

    def evaluation(self, *args, **kw):
        context = kw.pop('context', '')
        try:
            if context:
                self.ctx.context = context
        except Exception:
            pass
        scenario = PricingContext()
        request_id = kw.pop('request_id', '')
        if request_id:
            self.ctx.request_id = request_id
        getattr(self, '_resolve')()
        pricing_context = kw.pop('pricing_context', '')
        risk = kw.pop('risk_measure', '')
        self.api_data(**kw)
        if pricing_context:
            scenario.resolve(pricing_context)
            with scenario:
                return self.api_calc(risk)
        else:
            return self.api_calc(risk)


class InstrumentBase(PricingMixin):
    _ = IsPriceable()

    def __init__(self):
        super().__init__()
        getattr(self, "check_param")()

    def check_param(self):
        getattr(self, '_')

    def calc(self, risk_measure: Union[RiskMeasure, List[RiskMeasure]], option_all=None):
        if self.__class__.__name__ == "Position" and getattr(self, 'tradble', None) and not getattr(self.tradble, 'isvalid')():
            logger.debug(f"{getattr(self,'asset_id')}: is not valid")
            return
        if self.__class__.__name__ != "Position" and not getattr(self, 'isvalid')():
            raise TuringError("The instrument expired")
        result: Union[float, List] = []
        try:
            if getattr(self, '_ctx_resolve', None) is not None:
                getattr(self, '_ctx_resolve')()
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
                try:
                    setattr(self, k, v)
                except:
                    ...

    def type(self):
        pass

    def resolve(self, expand_dict=None):
        if expand_dict:
            self._set_by_dict(expand_dict)
        getattr(self, '_resolve')()

    def __repr__(self):
        return self.__class__.__name__
