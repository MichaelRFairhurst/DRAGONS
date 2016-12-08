"""
The geminidr package provides the base classes for all parameter and primitive
classes in the geminidr package.

E.g.,
>>> from geminidr import ParametersBASE
>>> from geminidr import PrimitivesBASE

"""
class ParametersBASE(object):
    """
    Base class for all Gemini package parameter sets.

    Most other parameter classes will be separate from their
    matching primitives class. Here, we incorporate the parameter
    class, ParametersBASE, into the mod.

    """
    pass
# ------------------------------------------------------------------------------

from inspect import stack
import os
import pickle

from gempy.utils import logutils
# new system imports - 10-06-2016 kra
# NOTE: imports of these and other tables will be moving around ...
from gemini.lookups import calurl_dict
from gemini.lookups import keyword_comments
from gemini.lookups import timestamp_keywords
from gemini.lookups.source_detection import sextractor_default_dict

from recipe_system.utils.decorators import parameter_override
from recipe_system.cal_service import caches
# ------------------------------------------------------------------------------
@parameter_override
class PrimitivesBASE(object):
    """
    This is the base class for all of primitives classes for the geminidr 
    primitive sets. __init__.py provides, or should provide, all attributes
    needed by subclasses.

    Three parameters are required on the initializer:

    adinputs: a list of astrodata objects
        <list>

    context: the context for recipe selection, etc.
        <str>

    upmetrics: upload the QA metrics produced by the QAP.
        <bool>

    """
    tagset = None

    def __init__(self, adinputs, context, upmetrics=False, ucals=None, uparms=None):
        self.adinputs         = adinputs
        self.adoutputs        = None
        self.context          = context
        self.parameters       = ParametersBASE
        self.log              = logutils.get_logger(__name__)
        self.upload_metrics   = upmetrics
        self.user_params      = uparms if uparms else {}
        self.usercals         = ucals if ucals else {}
        self.calurl_dict      = calurl_dict.calurl_dict
        self.timestamp_keys   = timestamp_keywords.timestamp_keys
        self.keyword_comments = keyword_comments.keyword_comments
        self.sx_default_dict  = sextractor_default_dict.sextractor_default_dict

        self.streams          = {}
        self.cachedict        = caches.set_caches()
        self.calibrations     = caches.load_cache(caches.calindfile)
        self.stacks           = caches.load_cache(caches.stkindfile)

        # This lambda will return the name of the current caller.
        self.myself           = lambda: stack()[1][3]


    def _add_cal(self, crecords):
        self.calibrations.update(crecords)
        return

    def _get_cal(self, ad, caltype):
        key = (ad.data_label(), caltype)
        return self.calibrations.get(key)[1]
