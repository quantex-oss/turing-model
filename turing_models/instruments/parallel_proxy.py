import os
import requests
import traceback
from enum import Enum
from loguru import logger
from typing import Union, List
from urllib.parse import urljoin
from turing_models import config
from fundamental.base import Context
from turing_models.constants import ParallelType
from turing_models.instruments.common import RiskMeasure
from turing_models.utilities.turing_date import TuringDate


__all__ = (
    "ParallelProxy"
)


class ParallelProxyException(BaseException):
    pass


class ApiSenderException(BaseException):
    pass


class EnvInfo:
    USERNAME = "GIT_AUTHOR_NAME"
    EMAIL = "GIT_AUTHOR_EMAIL"
    TURING_URL = "TURING_URL"
    TURING_URL_SHORTER = "TURING_URL_SHORTER"


class YrParallelProxyMixin:
    __slots__ = ()

    @staticmethod
    def yr_init(module):
        module.init(
            package_ref=config.yr_package_ref,
            logging_level='INFO',
            cluster_server_addr=config.yr_cluster_server_addr
        )

    def yr_calc(self):
        import yuanrong
        self.yr_init(yuanrong)
        return yuanrong.ship()(self._yr_calc.__func__).ship(self, risk_measure=self.risk_measure)

    def _yr_calc(self, risk_measure: Union[RiskMeasure, List[RiskMeasure]], option_all=None):
        try:
            result: Union[float, List] = getattr(self.model, risk_measure.value)() \
                if not option_all else getattr(self.model, risk_measure.value)(option_all)
            return result
        except Exception:
            logger.error(str(traceback.format_exc()))
            return ""

    @staticmethod
    def get_results_with_yr(calc_list, timeout=3):
        import yuanrong
        return yuanrong.get(calc_list, timeout)


class Sender:

    def __init__(self, timeout=10):
        self.url_domain = self.get_url_domain_from_cfg()
        self.url = urljoin(self.url_domain, config.remote_rpc_path)
        self.timeout = timeout

    @staticmethod
    def get_url_domain_from_cfg():
        return os.getenv(EnvInfo.TURING_URL) or config.url_domain

    def send(self, api_data):
        try:
            resp = requests.post(self.url, json=api_data, timeout=self.timeout)
            if resp.status_code != 200:
                raise ApiSenderException(f"status_code is {resp.status_code}, err_msg is {resp.text}")
            return resp.json()["data"]
        except ApiSenderException as error:
            logger.error(
                f"Request has error, url:{self.url}, "
                f"params:{api_data}, error:\n" + str(error)
            )
            return None


class RemoteApiCaller:

    def __init__(self, *, model, call_func_name, risk_measure, timeout=5):
        self.model = model
        self.sender = Sender(timeout)
        self.api_data = {
            "modulePath": None,
            "classMeta": {"name": None, "param": {}},
            "function": {"name": call_func_name, "param": risk_measure}
        }

    def build_api_data(self):
        self.api_data["modulePath"] = self.model.__module__
        self.api_data["classMeta"]["name"] = self.model.__class__.__name__
        for k in list(self.model.__dataclass_fields__.keys()):
            if k not in self.model.__dict__:
                continue
            v = self.model.__dict__[k]
            if v is None:
                continue
            if isinstance(v, Enum):
                self.api_data["classMeta"]["param"][k] = v.name
            elif isinstance(v, TuringDate):
                self.api_data["classMeta"]["param"][k] = v.__repr__()
            else:
                self.api_data["classMeta"]["param"][k] = v

    def call(self):
        self.build_api_data()
        return self.sender.send(self.api_data)


class InnerParallelProxyMixin:
    __slots__ = ()

    def inner_calc(self):
        return RemoteApiCaller(
            model=self.model,
            call_func_name=self.call_func_name,
            risk_measure=self.risk_measure.name,
            timeout=self.timeout
        ).call()


class ParallelCalcProxy(YrParallelProxyMixin, InnerParallelProxyMixin):

    def __init__(self, model, parallel_type, risk_measure, timeout=3):
        self.model = model
        self.parallel_type = parallel_type
        self.risk_measure = risk_measure
        self.call_func_name = "calc"
        self.timeout = timeout

    def calc(self):
        if self.parallel_type == ParallelType.YR:
            return self.yr_calc()
        elif self.parallel_type == ParallelType.INNER:
            return self.inner_calc()
        else:
            raise ParallelProxyException(f"Not support '{self.parallel_type}' parallel_type!")
