import yuanrong


class ConcurrentMode:
    LOCAL = "local"
    YR = "yr"


concurrent_mode = ConcurrentMode.YR


def concurrent(func):

    if concurrent_mode == ConcurrentMode.LOCAL:
        def _wrapper(*args, **kwargs):
            return func(*args, **kwargs)
    else:
        def _wrapper(*args, **kwargs):
            return yuanrong.ship()(func).ship(*args, **kwargs)

    return _wrapper
