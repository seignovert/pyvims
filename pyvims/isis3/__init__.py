# -*- coding: utf-8 -*-
import os

if 'ISISROOT' not in os.environ:
    raise IOError('ISISROOT is not defined')

if 'ISIS3DATA' not in os.environ:
    raise IOError('ISIS3DATA is not defined')

from .vims import ISIS3_VIMS
