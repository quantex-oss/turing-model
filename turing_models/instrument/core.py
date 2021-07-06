import traceback
from typing import Union, List, Iterable

from loguru import logger

from fundamental import ctx
from turing_models.instrument.common import RiskMeasure


class Instrument:
    def __init__(self):
        self.ctx = ctx

    def calc(self, risk_measure: Union[RiskMeasure, List[RiskMeasure]]):
        result: Union[float, List] = []

        try:
            if not isinstance(risk_measure, Iterable):
                result = getattr(self, risk_measure.value)()
                result = self._calc(result)
                self.__row__(risk_measure.value, round(result, 2) if result else "-")
                return result
            for risk in risk_measure:
                res = getattr(self, risk.value)()
                res = self._calc(res)
                result.append(res)
                self.__row__(risk.value, round(res, 2) if res else "-")
            return result
        except Exception as e:
            logger.error(str(traceback.format_exc()))
            return ""

    def _calc(self, value):
        """二次计算,默认为直接返回当前值"""
        return value

    def __row__(self, ident, _value):
        """rich表格数据填充"""
        if self.__class__.__name__ == "Position" and hasattr(self.ctx, "positions_dict"):
            for key, value in self.ctx.positions_dict.items():
                if value.get('asset_id') == self.tradable.asset_id if self.tradable else "":
                    value[ident] = _value
