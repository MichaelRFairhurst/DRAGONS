import pytest
from pytest_dragons.plugin import path_to_inputs

import os
import numpy as np

import astrodata, gemini_instruments
from geminidr.gmos.primitives_gmos_longslit import GMOSLongslit

datasets = [("N20180908S0020_wavelengthSolutionAttached.fits", "N20180908S0019_flat.fits")]

@pytest.mark.gmosls
@pytest.mark.parametrize("ad, flat", datasets, indirect=True)
def test_add_illum_mask_position(ad, flat):
    p = GMOSLongslit([ad])
    ad_out = p.flatCorrect(flat=flat).pop()
    ad_ref = ref_ad_factory(ad_out.filename)
    for ext, ext_ref in zip(ad_out, ad_ref):
        np.testing.assert_allclose(ext.data, ext_ref.data)
        np.testing.assert_array_equal(ext.mask, ext_ref.mask)
        np.testing.assert_allclose(ext.variance, ext_ref.variance)


@pytest.fixture(scope='function')
def ad(path_to_inputs, request):
    """Return AD object in input directory"""
    path = os.path.join(path_to_inputs, request.param)
    if os.path.exists(path):
        return astrodata.open(path)
    raise FileNotFoundError(path)


@pytest.fixture(scope='function')
def flat(path_to_inputs, request):
    """Return full path to file in input directory"""
    path = os.path.join(path_to_inputs, request.param)
    if os.path.exists(path):
        return path
    raise FileNotFoundError(path)
