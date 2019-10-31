"""Test star module."""

from numpy.testing import assert_array_almost_equal as assert_array

from pyvims.star import Star

from pytest import approx, fixture


@fixture
def et():
    """Observation ephemeris time."""
    return 277399264.66979694

@fixture
def obs():
    """Observer position in J2000 frame."""
    return [1.33762199e9, -3.50660679e8, -2.03026006e8]

@fixture
def gaia_star():
    """Gaia star object."""
    return {
        'source_id': 6071671369457586688,
        'ra': 187.81968200536744,
        'dec': -57.081421470214885,
        'pmra': 2.3170379374019983,
        'pmdec': -21.34892029322907,
        'parallax': 5.621437016523866,
        'phot_g_mean_mag': 6.3963637,
    }

def test_star_attr(et, obs, gaia_star):
    """Test star attributes."""
    star = Star(et=et, obs=obs, **gaia_star)

    assert str(star) == '6071671369457586688'

    assert star.radec_2000 == (gaia_star['ra'], gaia_star['dec'])
    assert star.dyr == approx(8.79, abs=1e-2)
    assert star.mu_ra == approx(5.658e-6, abs=1e-9)
    assert star.mu_dec == approx(-52.129e-6, abs=1e-9)

    assert_array(star.radec_et, [187.8196877, -57.0814736], decimal=1e-7)

    assert star.dist == approx(5.489e15, abs=1e12)
    assert_array(star.xyz / 1e15, [-2.955, -0.406, -4.608], decimal=3)

    assert star.ra == approx(187.819677495, abs=1e-9)
    assert star.dec == approx(-57.081461255, abs=1e-9)


def test_star_empty():
    """Test star for empty values."""
    star = Star()

    assert str(star) == ''
    assert star.radec_2000 == (0, 0)
    assert star.dyr == 0
    assert star.mu_ra == 0
    assert star.mu_dec == 0

    assert_array(star.radec_et, [0, 0], decimal=0)

    assert star.dist is None
    assert star.xyz is None

    assert star.radec == (0, 0)
