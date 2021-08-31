from enum import Enum


class ParallelType(Enum):

    YR = "YR"
    INNER = "INNER"
    NULL = None  # 不并行计算

    @classmethod
    def valid(cls, parallel_type):
        if not isinstance(parallel_type, ParallelType):
            raise TypeError(f"parallel_type must be a ParallelType enum, not {parallel_type}!")
        if parallel_type in (ParallelType.YR, ParallelType.INNER):
            return True
        return False


class EnvInfo:
    USERNAME = "GIT_AUTHOR_NAME"
    EMAIL = "GIT_AUTHOR_EMAIL"
    TURING_URL = "TURING_URL"
    TURING_URL_SHORTER = "TURING_URL_SHORTER"
