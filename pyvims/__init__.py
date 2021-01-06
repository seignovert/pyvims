"""VIMS ISIS module."""

from .vims import VIMS
from .qub import QUB
from .wvlns import VIMS_IR, VIMS_VIS

from .__version__ import __version__

__all__ = [
    'QUB',
    'VIMS',
    'VIMS_IR',
    'VIMS_VIS',
    '__version__'
]
