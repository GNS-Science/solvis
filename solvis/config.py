#! python3
"""
Configuration for the Solvis system.

These values may be used in Solvis code itself, or in associated scripts.
"""
import enum
import os
from pathlib import PurePath


class EnvMode(enum.IntEnum):
    """Enumerated Environment Modes."""

    LOCAL = 0
    CLUSTER = 1
    AWS = 2


def boolean_env(environ_name: str) -> bool:
    """
    Check whether the code is running in a specific EnvMode.

    Parameters:
        environ_name: an EnvMode member name (e.g. CLUSTER)

    Returns:
        Whether the mode is set via environment variable.
    """
    return bool(os.getenv(environ_name, '').upper() in ["1", "Y", "YES", "TRUE"])


WORK_PATH = os.getenv('NZSHM22_SCRIPT_WORK_PATH', PurePath(os.getcwd(), "tmp"))
"""A standardised directory path for working with the 2022 NZ Seismic Hazard Model."""
