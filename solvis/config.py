#! python3
"""
configuration for the system
"""

import enum
import os
from pathlib import PurePath

# from runzi.util.aws import get_secret


class EnvMode(enum.IntEnum):
    LOCAL = 0
    CLUSTER = 1
    AWS = 2


def boolean_env(environ_name):
    return bool(os.getenv(environ_name, '').upper() in ["1", "Y", "YES", "TRUE"])


WORK_PATH = os.getenv('NZSHM22_SCRIPT_WORK_PATH', PurePath(os.getcwd(), "tmp"))
