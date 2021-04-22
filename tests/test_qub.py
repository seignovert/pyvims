"""Test QUB module."""

from pathlib import Path

from pyvims.qub import QUB

from pytest import fixture, raises


DATA = Path(__file__).parent / 'data'


@fixture
def qub():
    """Default QUB file example."""
    return QUB('1815243432_1', root=DATA)


@fixture
def qub_no_back():
    """QUB file example without band suffix (no-back plane)."""
    return QUB('1477479472_1', root=DATA)


def test_qub_loader(qub):
    """Test QUB loader."""
    assert str(qub) == '1815243432_1'
    assert qub.fname == 'v1815243432_1.qub'
    assert qub.prefix == 'v'
    assert qub.suffix == ''
    assert qub.is_file
    assert qub.is_qub
    assert qub.md5 == '58a3ac2623d1d103e0077da1b0e56cf3'

    assert qub.ns == 16
    assert qub.nl == 4
    assert qub.nb == 352

    assert qub.data.shape == (4, 352, 16)
    assert qub.back_plane.shape == (4, 17)
    assert qub.side_plane.shape == (4, 352)

    assert qub['BACKGROUND'].shape == (4, 352)
    assert qub.background.shape == (4, 352, 16)
    assert qub.median_background.shape == (4, 352, 16)

    assert 'BAND_SUFFIX_ITEM_BYTES' in qub.core

    # Get Wavelengths
    assert len(qub.wvlns) == 352
    assert qub.wvlns[0] == qub.w[0] == qub.wvlns_vis[0] == 0.35054
    assert qub.wvlns[-1] == qub.w[-1] == qub.wvlns_ir[-1] == 5.1225

    # Get raw attributes
    assert len(qub.raw_header) == 23552
    assert qub.raw_header[:40] == b'CCSD3ZF0000100000001NJPL3IF0PDS200000001'
    assert qub.raw_back_plane.shape == (4, 272)
    assert qub.raw_side_plane.shape == (4, 352, 4)

    # Get image
    assert qub[1, 1].shape == (352,)
    assert qub[16, 1].shape == (352,)
    assert qub[1, 4].shape == (352,)
    assert qub[16, 4].shape == (352,)

    with raises(ValueError):
        _ = qub[0, 0]

    with raises(ValueError):
        _ = qub[0, 1]

    with raises(ValueError):
        _ = qub[1, 0]

    with raises(ValueError):
        _ = qub[17, 1]

    with raises(ValueError):
        _ = qub[1, 5]

    with raises(ValueError):
        _ = qub[17, 5]

    # Get spectrum
    assert qub[96].shape == (4, 16)

    with raises(ValueError):
        _ = qub[0]

    with raises(ValueError):
        _ = qub[353]

    # Get IR hot pixels in the background
    assert all(qub.ir_hot_pixels() == [
        105, 119, 124, 168, 239, 240, 275, 306, 317, 331,
    ])


def test_qub_data_mask(qub):
    """Test QUB masked data on NULL."""
    assert qub.data.data[0, 0, 0] == qub.null('CORE')
    assert qub.data.mask[0, 0, 0]

    assert qub.data.data[0, 96, 0] != qub.null('CORE')
    assert not qub.data.mask[0, 96, 0]


def test_qub_with_no_back(qub_no_back):
    """Test QUB loader."""
    assert str(qub_no_back) == '1477479472_1'

    assert qub_no_back.ns == 12
    assert qub_no_back.nl == 12
    assert qub_no_back.nb == 352

    assert 'BAND_SUFFIX_ITEM_BYTES' not in qub_no_back.core

    assert qub_no_back.data.shape == (12, 352, 12)
    assert qub_no_back.back_plane.shape == (0,)
    assert qub_no_back.side_plane.shape == (12, 352)

    assert qub_no_back['BACKGROUND'].shape == (12, 352)
    assert qub_no_back.background.shape == (12, 352, 12)
