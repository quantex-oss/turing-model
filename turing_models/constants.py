from enum import Enum


class ParallelType(Enum):

    YR = "YR"
    INNER = "INNER"
    NULL = None  # 不并行计算
