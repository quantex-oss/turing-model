from enum import Enum


class ParallelType(Enum):

    YR = "YR"
    INNER = "INNER"
    NULL = None  # 不并行计算


class EnvInfo:
    USERNAME = "GIT_AUTHOR_NAME"
    EMAIL = "GIT_AUTHOR_EMAIL"
    TURING_URL = "TURING_URL"
    TURING_URL_SHORTER = "TURING_URL_SHORTER"
