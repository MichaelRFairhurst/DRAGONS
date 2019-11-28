#!/usr/bin/env python

import numpy as np
import pytest

from astrodata import nddata


def test_variance_uncertainty_warn_if_there_are_any_negative_numbers():
    arr = np.zeros((5, 5))
    arr[2, 2] = -0.001

    with pytest.warns(RuntimeWarning, match='Negative variance values found.'):
        result = nddata.ADVarianceUncertainty(arr)

    assert not np.all(arr >= 0)
    assert isinstance(result, nddata.ADVarianceUncertainty)
    assert result.array[2, 2] == 0

    # check that it always works with a VarianceUncertainty instance
    result.array[2, 2] = -0.001

    with pytest.warns(RuntimeWarning, match='Negative variance values found.'):
        result2 = nddata.ADVarianceUncertainty(result)

    assert not np.all(arr >= 0)
    assert not np.all(result.array >= 0)
    assert isinstance(result2, nddata.ADVarianceUncertainty)
    assert result2.array[2, 2] == 0


if __name__ == '__main__':
    pytest.main()
