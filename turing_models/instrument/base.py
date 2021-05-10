import logging
from typing import Union
from enum import EnumMeta, Enum

_logger = logging.getLogger(__name__)


def get_enum_value(enum_type: EnumMeta, value: Union[Enum, str]):
    if value in (None,):
        return None

    if isinstance(value, enum_type):
        return value

    try:
        enum_value = enum_type(value)
    except ValueError:
        _logger.warning('Setting value to {}, which is not a valid entry in {}'.format(value, enum_type))
        enum_value = value

    return enum_value