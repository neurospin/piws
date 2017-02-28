##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import types


def monkeypatch(cls):
    """ Define a function to monkey patch a class method.
    This may be usefull to overload the Base class '_get_security_groups'
    methods in order to set a custom security granularity level.
    """
    def decorator(func):
        setattr(cls, func.__name__, types.MethodType(func, cls))
        return func
    return decorator
