import re
import subprocess
from astropy.io import fits
from collections import deque
from copy import deepcopy

import numpy as np

from gempy.eti_core.eti import ExternalTaskInterface as ETI
from .sextractoretifile import SExtractorETIFile
from .sextractoretiparam import SExtractorETIParam

__SYS_COMMAND__ = "sex"
__MIN_VERSION__ = [2, 8, 6]
__VERSION_COMMAND__ = [__SYS_COMMAND__, "--version"]
__REGEXP_GROUP_NAME__ = "v1"
__VERSION_REGEXP__ = ''.join(["^.*version (?P<", __REGEXP_GROUP_NAME__,
                              r">[\d+\.]+) .*$"])

class SExtractorETI(ETI):
    """This class coordinates the ETI as is relates to SExtractor"""
    def __init__(self, inputs=None, params=None, mask_dq_bits=None,
                 getmask=False):
        """
        Parameters
        ----------
        inputs: list of AstroData objects
            AD objects to run through SExtractor
        params: dict
            A dict of command-line parameters
        mask_dq_bits: int/bool/None
            DQ(mask) bits which, if any is set, should have the data replaced
            by the median of the good data. This avoids the need to run files
            through deepcopy and applyDQPlane. Use "True" if the mask is a
            boolean array rather than integer
        getmask: bool
            make SExtractor produce an object mask and attach it to the outputs
        """
        super(SExtractorETI, self).__init__(inputs=inputs)
        self.add_param(SExtractorETIParam(params))
        self._mask_dq_bits = mask_dq_bits
        self._getmask = getmask

    def _version_regexp(self):
        """Compile a regular expression for matching the version
        number from SExtractor output"""
        return (re.compile(__VERSION_REGEXP__), __REGEXP_GROUP_NAME__)

    def check_version(self, command=__VERSION_COMMAND__,
                      minimum_version=__MIN_VERSION__):
        """
        Returns True if the installed SExtractor is OK to use
        """
        (stdoutdata, stderrdata) = self._execute(command,
                                                   return_output=True)

        version_regexp, group_names = self._version_regexp()
        if isinstance(group_names, list):
            if len(group_names) != len(minimum_version):
                errmsg = ("Length of regexp groups {0} is not equal to length"
                          " of minimum_version {1}".format(len(group_names),
                                                          len(minimum_version)))
                raise IOError(errmsg)
            version = ".".join([version_regexp.match(stdoutdata).group(name)
                                for name in group_names])
        else:
            version = version_regexp.match(stdoutdata).group(group_names)

        if version is None:
            raise Exception("Unable to determine SExtractor version")

        match_values = [int(i) for i in version.split(".")]
        if match_values < minimum_version:
            raise Exception("Version {} of SExtractor is required. Version "
                      "{} installed".format('.'.join([str(i) for i in
                                                minimum_version]), version))
        return True

    def run(self):
        # Make a list of all the extensions in all the inputs
        self.file_objs = []
        # self.inputs is a list, but its items might be single slices
        # or sliceable AD objects, so cater for both
        for ad in self.inputs:
            try:
                [self.add_file(SExtractorETIFile(ext,
                        mask_dq_bits=self._mask_dq_bits)) for ext in ad]
            except TypeError:
                self.add_file(SExtractorETIFile(ad,
                              mask_dq_bits=self._mask_dq_bits))
        # Run the ETI
        self.prepare()
        self.execute()
        objdata = self.recover()
        # Attach the OBJCATs and OBJMASKs to each extension in each input
        # OBJMASK needs to be an np.int16 array of 1s or 0s
        # This is kind of ugly, so maybe want to look at it
        i = 0
        for ad in self.inputs:
            try:
                for ext in ad:
                    ext.OBJCAT, objmask = objdata[i]
                    if self._getmask:
                        ext.OBJMASK = np.where(fits.open(objmask)[0].data>0,
                                               1, 0).astype(np.int16)
                    i += 1
            except TypeError:
                ad.OBJCAT, objmask = objdata[i]
                if self._getmask:
                    ad.OBJMASK = np.where(fits.open(objmask)[0].data>0,
                                          1, 0).astype(np.int16)
        self.clean()
        return self.inputs

    def execute(self):
        cmd = [__SYS_COMMAND__]
        param_dict = self.param_objs[0].params

        # Parameters that have been sent as lists, with different values
        # for different inputs: stored as deques so we can popleft()
        list_params = {}

        # Add the config (.sex) file as first parameter
        cmd.extend(['-c', param_dict['config']])
        # Add all the other command-line arguments
        for parameter, value in param_dict.items():
            if isinstance(value, list):
                list_params.update({parameter: deque(value)})
            elif parameter != 'config':
                cmd.extend(['-'+parameter, value])

        # Run SExtractor for each input file
        for file_obj in self.file_objs:
            files = ['-CATALOG_NAME', file_obj._catalog_file]
            if self._getmask:
                files.extend(['-CHECKIMAGE_TYPE', 'OBJECTS',
                              '-CHECKIMAGE_NAME', file_obj._objmask_file])
            if file_obj._dq_image is not None:
                files.extend(['-FLAG_IMAGE', file_obj._dq_image])

            # Add all the input-specific command-line arguments
            [files.extend([param, value.popleft()]) for param, value in
             list_params.items()]
            files.append(file_obj._sci_image)
            self._execute(cmd+files, return_output=False)

    def recover(self):
        for par in self.param_objs:
            par.recover()
        # Return a list of OBJCATs
        return [fil.recover() for fil in self.file_objs]

    def _execute(self, command=list, return_output=False):
        """
        Call subprocess to execute shell 'command'. Tests the executed task's
        returncode: raises if non-zero. Raises an OSError.
        If exceptions are raised the recover method is invoked.

        @command: list: Shell command to execute
        @return_output: bool: If True returns tuple (stdoutdata, stderrdata)
        """
        try:
            # universal_newlines=True as SExtractor outputs non-ASCII chars
            pipe_out = subprocess.Popen(command,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        universal_newlines=True)

            # Get the output from sextractor and set returncode (communicate
            # does this) then check it
            (stdoutdata, stderrdata) = pipe_out.communicate()
            if pipe_out.returncode != 0:
                errmsg = ("SExtractor returned an error:\n"
                          "{0}{1}".format(stdoutdata, stderrdata))
                raise Exception(errmsg)
        except OSError:
            self.clean()
            raise
        else:
            # TODO Search for WARNINGS in stderrdata and print
            if return_output:
                return (stdoutdata, stderrdata)