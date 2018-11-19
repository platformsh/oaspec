# -*- coding: utf-8 -*-

from typing import Optional, Union, MutableMapping
from ruamel.yaml.comments import CommentedMap

data_types = {
    "integer": set(
        "int32",
        "int64",
    ),
    "number": set(
        "float",
        "double",
    ),
    "string": set(
        "byte",
        "binary",
        "date",
        "date-time",
        "password",
        "email",
        "uuid",
        "url",
    ),
    "boolean": set()
}

class OASpecObject(object):

    _definition = None
    _parser = None

    def __init__(
        self,
        spec: Union[dict, CommentedMap],
    ):

        self._raw_spec: Union[dict, CommentedMap] = spec

    def parse_spec(self):
        self._parser(self).parse_spec(self._raw_spec)

    @staticmethod
    def field(
        field_type: Union[str, type],
        req: Optional[bool] = False,
        fmt: Optional[str] = None,
    ):

        if type(field_type) is str and fmt:
            if fmt not in data_types[field_type]:
                raise ValueError(
                    "Field 'format' for '{}' should empty or be one of: {}".format(
                        field_type,
                        ", ".join(data_types[field_type]),
                    )
                )

        elif type(field_type) is type and fmt:
            raise ValueError("Field 'format' not applicable to object-based types")

        return {
            "type": field_type,
            "required": req,
            "format": fmt,
        }


class OASpecParser(object):

    def __init__(
            self,
            oaspec_object: OASpecObject,
    ):

        self._parsed_object: OASpecObject = oaspec_object

        self.definition = self._parsed_object._definition

    def parse_spec(self, raw_spec):
        pass
