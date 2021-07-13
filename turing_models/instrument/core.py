import traceback
from dataclasses import dataclass
from typing import Union, List, Iterable, Any

import yuanrong
from loguru import logger

from fundamental import ctx
from fundamental.base import Context
from turing_models.instrument.common import RiskMeasure
from turing_models.instrument.decorator import concurrent


@dataclass
class YuanRong:
    obj: Any

    def __post_init__(self):
        self.greeks = [
            RiskMeasure.Price, RiskMeasure.EqDelta,
            RiskMeasure.EqGamma, RiskMeasure.EqVega,
            RiskMeasure.EqTheta, RiskMeasure.EqRho
        ]
        self.obj_list = self.build_calc()

    @staticmethod
    def init():
        yuanrong.init(
            package_ref='sn:cn:yrk:12345678901234561234567890123456:function:0-turing-model:$latest',
            logging_level='INFO', cluster_server_addr='123.60.60.83'
        )

    def build_calc(self):
        return [self.obj.yuanrong_calc(x) for x in self.greeks]

    def __call__(self, *args, **kwargs):
        if isinstance(self.obj_list, list):
            # print(self.obj_list)
            return zip(self.greeks, yuanrong.get(self.obj_list))
        return yuanrong.get([self.obj_list])[0]


class Instrument:
    def __init__(self):
        self.ctx: Context = ctx

    @concurrent
    def yuanrong_calc(self, risk_measure: Union[RiskMeasure, List[RiskMeasure]]):
        result: Union[float, List] = []
        try:
            result = getattr(self, risk_measure.value)()
            return result
        except Exception as e:
            logger.error(str(traceback.format_exc()))
            return ""

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
                self.__row__(risk.value, round(res, 2) if res and not isinstance(res, Iterable) else "-")
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


class InstrumentBase:

    def set_param(self):
        pass

    def _set_by_dict(self, tmp_dict):
        for k, v in tmp_dict.items():
            if v:
                setattr(self, k, v)

    def resolve(self, expand_dict):
        self._set_by_dict(expand_dict)
        self.set_param()
