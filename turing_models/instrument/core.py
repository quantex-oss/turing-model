from dataclasses import dataclass
from typing import Union, List, Iterable

from tunny import model
from fundamental.base import Context, ctx

from turing_models.instrument.common import RiskMeasure


@model
@dataclass
class Instrument:

    ctx: Context = ctx

    def set_param(self):
        pass

    def _set_by_dict(self, tmp_dict):
        for k, v in tmp_dict.items():
            if v:
                setattr(self, k, v)

    def resolve(self, expand_dict):
        self._set_by_dict(expand_dict)
        self.set_param()

    def calc(self, risk_measure: Union[RiskMeasure, List[RiskMeasure]]):
        result: float or List = []
        if not isinstance(risk_measure, Iterable):
            return getattr(self, risk_measure.value)()
        for risk in risk_measure:
            res = getattr(self, risk.value)()
            setattr(self, risk.value, res)
            result.append(res)
        return result
