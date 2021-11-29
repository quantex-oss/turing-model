import functools
import inspect
import traceback
from typing import Union, List, Iterable

from loguru import logger

from fundamental import PricingContext
from fundamental.base import ctx, Context
from turing_models.instruments.common import RiskMeasure


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

    def calc(self, risk_measure: Union[RiskMeasure, List[RiskMeasure]], option_all=None):
        result: Union[float, List] = []
        try:
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
                    pass

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
        logger.debug(self.__dict__)
        msg = ''
        response_data = []
        if riskMeasure:
            if isinstance(riskMeasure, list):
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
            elif isinstance(riskMeasure, str):
                result = getattr(self, riskMeasure)()
                return result
        return response_data

    def api_data(self, **kw):
        for k, v in kw.items():
            for _k, _v in self.__dict__.items():
                if k == _k:
                    setattr(self, k, v)
                else:
                    setattr(self.ctx, k, v)
    
    def main(self, *args, **kw):
        context = kw.pop('context', '')
        try:
            if context:
                self.ctx.context = context
        except Exception:
            pass
        """api默认入口"""
        scenario = PricingContext()
        asset_id = kw.pop('assetId', '')
        request_id = kw.pop('request_id', '')
        if request_id:
            logger.bind(request_id=request_id)
        if asset_id:
            setattr(self, 'asset_id', asset_id)
            getattr(self, '_resolve')()
        pricing_context = kw.pop('pricingContext', '')
        risk = kw.pop('riskMeasure', '')
        self.api_data(**kw)
        if pricing_context:
            scenario.resolve(pricing_context)
            with scenario:
                return self.api_calc(risk)
        else:
            return self.api_calc(risk)

    def __repr__(self):
        return self.__class__.__name__
