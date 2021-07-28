import traceback
from dataclasses import dataclass
from typing import Any
import yuanrong
from turing_models.instruments.common import RiskMeasure

package_ref = 'sn:cn:yrk:12345678901234561234567890123456:function:0-turing-model:$latest'


@dataclass
class YuanRongDemo:
    obj: Any = None
    time_out: int = 10

    def __post_init__(self):
        self.greeks = [
            RiskMeasure.Price, RiskMeasure.EqDelta,
            RiskMeasure.EqGamma, RiskMeasure.EqVega,
            RiskMeasure.EqTheta, RiskMeasure.EqRho,
            RiskMeasure.EqRhoQ
        ]

    def build_obj_list(self):
        if not isinstance(self.obj, list):
            self.obj = [self.obj]
        obj_ = [self.calc_(o) for o in self.obj]
        return [n for a in obj_ for n in a]

    def calc_(self, obj):
        return [obj.calc(x, True) for x in self.greeks]

    def __call__(self, *args, **kwargs):
        self.obj_list = self.build_obj_list()
        if isinstance(self.obj_list, list):
            try:
                return yuanrong.get(self.obj_list, self.time_out)
            except RuntimeError:
                self.obj_list = self.build_obj_list()
                return yuanrong.get(self.obj_list, self.time_out)
            except Exception as e:
                traceback.format_exc()
                return []

    @staticmethod
    def init():
        yuanrong.init(
            package_ref=package_ref,
            logging_level='INFO',
            cluster_server_addr='123.60.60.83'
        )
