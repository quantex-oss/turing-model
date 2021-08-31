import os
import requests
from enum import Enum
from loguru import logger
from typing import Union, List
from urllib.parse import urljoin
from turing_models import config
from turing_models.constants import ParallelType, EnvInfo
from turing_models.exceptions import ParallelProxyException, ApiSenderException
from turing_models.instruments.common import RiskMeasure
from turing_models.utilities.turing_date import TuringDate

__all__ = (
    "ParallelProxy"
)


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
        return yuanrong.ship()(self._yr_calc.__func__).ship(
            self, risk_measure=self.func_params["risk_measure"])

    def _yr_calc(self,
                 risk_measure: Union[RiskMeasure, List[RiskMeasure]],
                 option_all=None):
        try:
            result: Union[float, List] = (
                getattr(self.instance, risk_measure.value)() if not option_all
                else getattr(self.instance, risk_measure.value)(option_all)
            )
            return result
        except Exception as error:
            logger.error(error)
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
                raise ApiSenderException(
                    f"status_code is {resp.status_code}, "
                    f"err_msg is {resp.text}"
                )
            return resp.json()["data"]["result"]
        except ApiSenderException as error:
            logger.error(
                f"Request has error, url:{self.url}, "
                f"params:{api_data}, error:\n" + str(error)
            )
            return None


class RemoteApiCaller:

    def __init__(self, *, instance, call_func_name, func_params, timeout=5):
        self.instance = instance
        self.sender = Sender(timeout)
        self.api_data = {
            "modulePath": None,
            "classMeta": {"name": None, "param": {}},
            "function": {"name": call_func_name, "param": func_params}
        }

    def build_api_data(self):
        self.api_data["modulePath"] = self.instance.__module__
        self.api_data["classMeta"]["name"] = self.instance.__class__.__name__
        for k in list(self.instance.__dataclass_fields__.keys()):
            if k not in self.instance.__dict__:
                continue
            v = self.instance.__dict__[k]
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
            instance=self.instance,
            call_func_name=self.call_func_name,
            func_params=self.func_params,
            timeout=self.timeout
        ).call()


class ParallelCalcProxy(YrParallelProxyMixin, InnerParallelProxyMixin):

    def __init__(self, instance, parallel_type,
                 call_func_name, func_params, timeout=3):
        self.instance = instance
        self.parallel_type = parallel_type
        self.call_func_name = call_func_name
        self.func_params = self.trim_func_params(func_params)
        self.timeout = timeout

    @staticmethod
    def trim_func_params(func_params):
        for k, v in func_params.items():
            if isinstance(v, Enum):
                func_params[k] = v.name
        return func_params

    def calc(self):
        if self.parallel_type == ParallelType.YR:
            return self.yr_calc()
        elif self.parallel_type == ParallelType.INNER:
            return self.inner_calc()
        else:
            raise ParallelProxyException(
                f"Not support '{self.parallel_type}' parallel_type!"
            )
