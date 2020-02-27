"""Test QUB module."""

from pathlib import Path

from pyvims.qub import QUB

from pytest import fixture


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
    assert qub.is_file
    assert qub.is_qub

    assert qub.ns == 16
    assert qub.nl == 4
    assert qub.nb == 352

    assert qub.data.shape == (4, 352, 16)
    assert qub.back_plane.shape == (4, 17)
    assert qub.side_plane.shape == (4, 352)
    assert qub.dn.shape == (4, 352, 16)

    assert 'BAND_SUFFIX_ITEM_BYTES' in qub.core


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
    assert qub_no_back.dn.shape == (12, 352, 12)
