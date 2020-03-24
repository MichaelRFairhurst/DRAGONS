import numpy as np
import pytest
from numpy.testing import assert_array_almost_equal, assert_array_equal

from astrodata.nddata import ADVarianceUncertainty, NDAstroData
from astropy.io import fits
from astropy.nddata import NDData, VarianceUncertainty
from astropy.wcs import WCS


@pytest.fixture
def testnd():
    shape = (5, 5)
    hdr = fits.Header({'CRPIX1': 1, 'CRPIX2': 2})
    nd = NDAstroData(data=np.arange(np.prod(shape)).reshape(shape),
                     uncertainty=ADVarianceUncertainty(np.ones(shape) + 0.5),
                     mask=np.zeros(shape, dtype=bool),
                     wcs=WCS(header=hdr),
                     unit='ct')
    nd.mask[3, 4] = True
    return nd


def test_window(testnd):
    win = testnd.window[2:4, 3:5]
    assert win.unit == 'ct'
    assert_array_equal(win.wcs.wcs.crpix, [1, 2])
    assert_array_equal(win.data, [[13, 14], [18, 19]])
    assert_array_equal(win.mask, [[False, False], [False, True]])
    assert_array_almost_equal(win.uncertainty.array, 1.5)
    assert_array_almost_equal(win.variance, 1.5)


def test_transpose(testnd):
    testnd.variance[0, -1] = 10
    ndt = testnd.T
    assert_array_equal(ndt.data[0], [0, 5, 10, 15, 20])
    assert ndt.variance[-1, 0] == 10


def test_set_section(testnd):
    sec = NDData(np.zeros((2, 2)),
                 uncertainty=VarianceUncertainty(np.ones((2, 2))))
    testnd.set_section((slice(0, 2), slice(1, 3)), sec)
    assert_array_equal(testnd[:2, 1:3].data, 0)
    assert_array_equal(testnd[:2, 1:3].variance, 1)


def test_variance_uncertainty_warn_if_there_are_any_negative_numbers():
    arr = np.zeros((5, 5))
    arr[2, 2] = -0.001

    with pytest.warns(RuntimeWarning, match='Negative variance values found.'):
        result = ADVarianceUncertainty(arr)

    assert not np.all(arr >= 0)
    assert isinstance(result, ADVarianceUncertainty)
    assert result.array[2, 2] == 0

    # check that it always works with a VarianceUncertainty instance
    result.array[2, 2] = -0.001

    with pytest.warns(RuntimeWarning, match='Negative variance values found.'):
        result2 = ADVarianceUncertainty(result)

    assert not np.all(arr >= 0)
    assert not np.all(result.array >= 0)
    assert isinstance(result2, ADVarianceUncertainty)
    assert result2.array[2, 2] == 0


def test_new_variance_uncertainty_instance_no_warning_if_the_array_is_zeros():
    arr = np.zeros((5, 5))
    with pytest.warns(None) as w:
        ADVarianceUncertainty(arr)
    assert len(w) == 0
