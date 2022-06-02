# pytest suite
"""
Tests for primitives_standardize.

This is a suite of tests to be run with pytest.

To run:
    1) Set the environment variable GEMPYTHON_TESTDATA to the path that
       contains the directories with the test data.
       Eg. /net/chara/data2/pub/gempython_testdata/
    2) From the ??? (location): pytest -v --capture=no
"""
# TODO @bquint: clean up these tests

import os
import pytest

import astrodata
from gempy.utils import logutils
from astrodata.testing import ad_compare

from geminidr.niri.primitives_niri_image import NIRIImage

TESTDATAPATH = os.getenv('GEMPYTHON_TESTDATA', '.')
logfilename = 'test_standardize.log'


class TestStandardize:
    """
    Suite of tests for the functions in the primitives_standardize module.
    """

    @classmethod
    def setup_class(cls):
        """Run once at the beginning."""
        if os.path.exists(logfilename):
            os.remove(logfilename)
        log = logutils.get_logger(__name__)
        log.root.handlers = []
        logutils.config(mode='standard',
                        file_name=logfilename)

    @classmethod
    def teardown_class(cls):
        """Run once at the end."""
        os.remove(logfilename)

    def setup_method(self, method):
        """Run once before every test."""
        pass

    def teardown_method(self, method):
        """Run once after every test."""
        pass

    @pytest.mark.xfail(reason="Test needs revision", run=False)
    def test_addDQ(self):
        ad = astrodata.open(os.path.join(TESTDATAPATH, 'NIRI',
                                         'N20070819S0104_prepared.fits'))
        p = NIRIImage([ad])
        ad = p.addDQ()[0]
        assert ad_compare(ad, os.path.join(TESTDATAPATH, 'NIRI',
                                           'N20070819S0104_dqAdded.fits'))

    @pytest.mark.xfail(reason="Test needs revision", run=False)
    def test_addIllumMaskToDQ(self):
        pass

    @pytest.mark.xfail(reason="Test needs revision", run=False)
    def test_addMDF(self):
        pass

    @pytest.mark.xfail(reason="Test needs revision", run=False)
    def test_validateData(self):
        # This is taken care of by prepare
        pass

    @pytest.mark.xfail(reason="Test needs revision", run=False)
    def test_addVAR(self):
        ad = astrodata.open(os.path.join(TESTDATAPATH, 'NIRI',
                                         'N20070819S0104_ADUToElectrons.fits'))
        p = NIRIImage([ad])
        ad = p.addVAR(read_noise=True, poisson_noise=True)[0]
        assert ad_compare(ad, os.path.join(TESTDATAPATH, 'NIRI',
                                           'N20070819S0104_varAdded.fits'))

    @pytest.mark.regression
    def test_prepare(self, change_working_dir, path_to_inputs,
                     path_to_refs):

        ad = astrodata.open(os.path.join(path_to_inputs,
                                         'N20070819S0104.fits'))
        with change_working_dir():
            logutils.config(file_name=f'log_regression_{ad.data_label()}.txt')
            p = NIRIImage([ad])
            p.prepare()
            prepared_ad = p.writeOutputs(
                outfilename='N20070819S0104_prepared.fits').pop()
            del prepared_ad.phu['SDZWCS']  # temporary fix

        ref_ad = astrodata.open(
            os.path.join(path_to_refs, 'N20070819S0104_prepared.fits'))

        assert ad_compare(prepared_ad, ref_ad)
