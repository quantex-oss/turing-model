import json
import asyncio
import traceback
from typing import Union, List
from loguru import logger
from turing_models.constants import ParallelType
from turing_models.instruments.common import RiskMeasure
from turing_models.exceptions import CalcResultException, CombinationCalcException
from turing_models.parallel.parallel_proxy import ParallelCalcProxy


class CombinationCalc:

    def __init__(self, source_list,
                 parallel_type=ParallelType.NULL,
                 timeout=30):
        self.source_list = source_list
        ParallelType.valid(parallel_type)
        self.parallel_type = parallel_type
        self.timeout = timeout
        self.results = []

    def add(self, model_calc_obj):
        if not isinstance(model_calc_obj, ModelCalc):
            raise CombinationCalcException(
                f"The {model_calc_obj} must be instance of ModelCalc!"
            )
        self.source_list.append(model_calc_obj)

    def run(self, *, is_async=False):
        if is_async:
            return asyncio.run(self.async_run())
        else:
            return self.sync_run()

    def sync_run(self):
        for model_calc_obj in self.source_list:
            model_calc_obj.sync_run(self.parallel_type)
            self.results.append(
                model_calc_obj.sync_process_result(self.parallel_type, self.timeout)
            )
        return self.results

    async def async_run(self):
        await asyncio.gather(
            *[model_calc_obj.async_run(self.parallel_type, self.timeout)
              for model_calc_obj in self.source_list]
        )
        self.results.extend(
            await asyncio.gather(
                *[model_calc_obj.async_process_result(self.parallel_type, self.timeout)
                  for model_calc_obj in self.source_list]
            )
        )
        return self.results


class ModelCalc:

    def __init__(self, model, risk_measures, *, title=None, subdivide=False):
        self.title = title or model.__class__.__name__
        self.model = model
        self.risk_measures = risk_measures
        # subdivide控制ModelCalc实例中risk_measures
        # 是否需要细分去并发，还是当作一个整体去并发。
        self.subdivide = subdivide
        self.process = []
        self.result = CalcResult(self.title)

    def sync_run(self, parallel_type):
        if self.subdivide:
            self.process.extend([self.sync_calc(r, parallel_type) for r in self.risk_measures])
        else:
            self.process.extend([self.sync_calc(self.risk_measures, parallel_type)])

    def sync_calc(self, risk_measure, parallel_type):
        return self.model.calc(risk_measure, parallel_type)

    def sync_process_result(self, parallel_type, timeout):
        return self.process_result(parallel_type, timeout)

    async def async_run(self, parallel_type, timeout=None):
        if self.subdivide:
            self.process.extend(
                await asyncio.gather(
                    *[self.async_calc(r, parallel_type, timeout) for r in self.risk_measures]
                )
            )
        else:
            self.process.append(await self.async_calc(self.risk_measures, parallel_type, timeout))

    async def async_calc(self, risk_measure: Union[RiskMeasure, List[RiskMeasure]], parallel_type, timeout=None):
        return self.model.calc(risk_measure, parallel_type, timeout=timeout)

    async def async_process_result(self, parallel_type, timeout):
        return self.process_result(parallel_type, timeout)

    def process_result(self, parallel_type, timeout):
        try:
            if parallel_type == ParallelType.YR:
                result = ParallelCalcProxy.get_results_with_yr(
                    self.process, timeout)
                if not self.subdivide:
                    result = result[0]

                self.result.update_fields(
                    {
                        risk_measure.value: result[idx] for
                        idx, risk_measure in enumerate(self.risk_measures)
                    }
                )
            else:
                if not self.subdivide:
                    self.process = self.process[0]

                self.result.update_fields(
                    {
                        risk_measure.value: self.process[idx] for
                        idx, risk_measure in enumerate(self.risk_measures)
                    }
                )
        except Exception as error:
            logger.warning(traceback.format_exc())
        return self.result


class CalcResult:

    def __init__(self, title):
        self.title = title

    def update_fields(self, update_fields_):
        if not isinstance(update_fields_, dict):
            raise CalcResultException("The update_fields must be a dict!")
        self.__dict__.update(update_fields_)

    def __repr__(self):
        return json.dumps(self.__dict__, indent=4)

    def __str__(self):
        return json.dumps(self.__dict__, indent=4)
