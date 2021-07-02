from typing import Union, List, Iterable

from turing_models.instrument.common import RiskMeasure


class Instrument:
    def calc(self, risk_measure: Union[RiskMeasure, List[RiskMeasure]]):
        result: float or List = []
        if not isinstance(risk_measure, Iterable):
            return getattr(self, "_" + risk_measure.value)()
        for risk in risk_measure:
            res = getattr(self, "_" + risk.value)()
            setattr(self, risk.value, res)
            result.append(res)
        return result
