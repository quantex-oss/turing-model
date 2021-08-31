import json
from turing_models.constants import ParallelType
from turing_models.exceptions import CalcResultException, CombinationCalcException
from turing_models.instruments.parallel_proxy import ParallelCalcProxy


class CombinationCalc:

    def __init__(self, source_list, parallel_type=None, timeout=3):
        self.source_list = source_list
        self.parallel_type = parallel_type
        self.timeout = timeout
        self.results = []

    def add(self, model_calc_obj):
        if not isinstance(model_calc_obj, ModelCalc):
            raise CombinationCalcException(
                f"The {model_calc_obj} must be instance of ModelCalc!"
            )
        self.source_list.append(model_calc_obj)

    def run(self):
        for model_calc_obj in self.source_list:
            model_calc_obj.calc(self.parallel_type)
            self.results.append(
                model_calc_obj.process_result(self.parallel_type, self.timeout)
            )
        return self.results


class ModelCalc:

    def __init__(self, model, risk_measures, *, title=None):
        self.title = title or model.__class__.__name__
        self.model = model
        self.risk_measures = risk_measures
        self.process = []
        self.result = CalcResult(self.title)

    def calc(self, parallel_type):
        self.process.extend([self.model.calc(r, parallel_type) for r in self.risk_measures])

    def process_result(self, parallel_type, timeout):
        if parallel_type == ParallelType.YR:
            result = ParallelCalcProxy.get_results_with_yr(self.process, timeout)
            self.result.update_fields(
                {
                    risk_measure.value: result[idx] for
                    idx, risk_measure in enumerate(self.risk_measures)
                }
            )
        else:
            self.result.update_fields(
                {
                    risk_measure.value: self.process[idx] for
                    idx, risk_measure in enumerate(self.risk_measures)
                }
            )
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
