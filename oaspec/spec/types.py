# -*- coding: utf-8 -*-

from ..utils import yaml
from typing import Optional, Union, MutableMapping

from numpy import typeDict as types

class OAType(object):

    pass

class OAInteger(OAType):

    _default = "integer"

    _formats = {
        "int32": types["int32"],
        "int64": types["int64"],
    }

    _names = {
        "integer": "int32",
        "long": "int64",
    }

    def __init__(self, ):
        pass

class integer():
    type = "integer"
    format = types["int32"]
