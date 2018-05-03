# -*- coding: utf-8 -*-
import pytest
import os
from datetime import datetime as dt

from pyvims import VIMS_LBL


cube_root = 'tests/data/'
cube_id = '1487096932_1'

lbl_repr = 'VIMS cube: 1487096932_1 [LBL]'
lbl_name = 'v1487096932_1.lbl'

cube_NS = 42
cube_NL = 42
cube_NB = 352
cube_obs = 'CASSINI ORBITER'
cube_inst = 'VIMS'
cube_target = 'TITAN'
cube_expo = {'VIS': 6720.0, 'IR': 160.0}
cube_mode = {'VIS': u'NORMAL', 'IR': u'NORMAL'}
cube_seq = 'S08'
cube_seq_title = 'VIMS_003TI_MAPMONITR001_CIRS'
cube_start = dt(2005, 2, 14, 18, 2, 29, 23000)
cube_stop = dt(2005, 2, 14, 18, 7, 32, 930000)
cube_dtime = dt(2005, 2, 14, 18, 5, 0, 976500)
cube_time = '2005-02-14T18:05:00.976500'
cube_year = 2005
cube_doy = 45
cube_year_d = 2005.1205479452055
cube_date = '2005/02/14'

missing_cube_id = '1000000000_1'

def test_VIMS_LBL():
    cub = VIMS_LBL(cube_id, root=cube_root)
    assert type(cub) == VIMS_LBL
    assert repr(cub) == lbl_repr

    assert cub.fname == cube_root + lbl_name

    assert cub.NS == cube_NS
    assert cub.NL == cube_NL
    assert cub.NB == cube_NB
    assert cub.obs == cube_obs
    assert cub.inst == cube_inst
    assert cub.target == cube_target
    assert cub.expo == cube_expo
    assert cub.mode == cube_mode
    assert cub.seq == cube_seq
    assert cub.seq_title == cube_seq_title
    assert cub.start == cube_start
    assert cub.stop == cube_stop
    assert cub.dtime == cube_dtime
    assert cub.time == cube_time
    assert cub.year == cube_year
    assert cub.doy == cube_doy
    assert cub.year_d == cube_year_d
    assert cub.date == cube_date

    assert cub.wvlns == None
    assert cub.bands == None

    with pytest.raises(NotImplementedError) as e_info:
        cub.readCUB()

def test_missing_VIMS_LBL():
    with pytest.raises(NameError) as e_info:
        VIMS_LBL(missing_cube_id, root=cube_root)
