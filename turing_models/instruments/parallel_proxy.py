import traceback
from loguru import logger
from typing import Union, List
from turing_models import config
from turing_models.constants import ParallelType
from turing_models.instruments.common import RiskMeasure


__all__ = (
    "ParallelProxy"
)


class ParallelProxyException(BaseException):
    pass


class YrParallelProxyMixin:
    __slots__ = ()

    @staticmethod
    def yr_init(module):
        module.init(
            package_ref=config.package_ref,
            logging_level='INFO',
            cluster_server_addr='123.60.60.83'
        )

    def yr_calc(self, risk_measure):
        import yuanrong
        self.yr_init(yuanrong)
        return yuanrong.ship()(self._yr_calc.__func__).ship(self, risk_measure=risk_measure)

    def _yr_calc(self, risk_measure: Union[RiskMeasure, List[RiskMeasure]], option_all=None):
        name: list = []
        try:
            name = [getattr(self, "asset_id", None), risk_measure.value]
            result: Union[float, List] = getattr(self, risk_measure.value)() \
                if not option_all else getattr(self, risk_measure.value)(option_all)
            return name, result
        except Exception:
            logger.error(str(traceback.format_exc()))
            return name, ""

    @staticmethod
    def get_results_with_yr(calc_list, timeout=3):
        import yuanrong
        return yuanrong.get(calc_list, timeout)


class InnerParallelProxyMixin:
    __slots__ = ()

    def inner_calc(self, risk_measure):
        # TODO 待完善，等待pricing-service指定path调用功能好了后调整
        return


class ParallelCalcProxy(YrParallelProxyMixin, InnerParallelProxyMixin):

    def __init__(self, parallel_type, risk_measure, timeout=30):
        self.parallel_type = parallel_type
        self.risk_measure = risk_measure
        self.timeout = timeout

    def calc(self):
        if self.parallel_type == ParallelType.YR.value:
            return self.yr_calc(self.risk_measure)
        elif self.parallel_type == ParallelType.INNER.value:
            return self.inner_calc(self.risk_measure)
        else:
            raise ParallelProxyException(f"Not support '{self.parallel_type}' parallel_type!")
