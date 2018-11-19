# -*- coding: utf-8 -*-

from ...utils import yaml
from typing import Optional, Union, MutableMapping
from ruamel.yaml.comments import CommentedMap

from .object import OASpecObject

__all__ = (
    "OASpecInfo",
    "OASpecInfoParser",
)

class OASpecInfoParser(object):
    def __init__(
            self,
            oaspec_info_object: OASpecInfo,
    ):

        self._parsed_object: OASpecInfo = oaspec_info_object

    def parse_spec(self, raw_spec):
        pass

class OASpecInfo(OASpecObject):

    _parser = OASpecInfoParser
    _definition = {
        "title": self.field("string", req=True),
        "description": self.field("string"),
        "termsOfService": self.field("string", fmt="url"),
        "contact": self.field(object),
        "license": self.field(object),
        "version": self.field("string", req=True),
    }

    def  __init__(
            self,
            spec: Union[dict, CommentedMap],
    ):

        super().__init__(spec)
        OASpecInfoParser(self).parse_spec(self._raw_spec)

class OASpecInfoContactObject(object):

    def __init__(self):
        pass
