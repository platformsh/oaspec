# -*- coding: utf-8 -*-

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

class SchemaField(object):

    def __init__(
        self,
        field_type: str,
        req: Optional[bool] = False,
        fmt: Optional[str] = None,
    ):

        if fmt and fmt not in data_types[field_type]:
            raise ValueError(
                "Field 'format' for '{}' should empty or be one of: {}".format(
                    field_type,
                    ", ".join(data_types[field_type]),
                )
            )

        self.field_type = field_type
        self.required = req
        self.format = fmt

class SchemaObject(object):

    def __init__(
        self,
        field_schema: SchemaDefinition,
        req: Optional[bool] = False,
    ):

        self.field_schema = field_schema
        self.required = req

class SchemaDefinition(object):

    def __init__(self):
        pass

    def __setattr__(self, name, value):

        if (
            not isinstance(value, DefinitionField) and
            not isinstance(value, DefinitionObject)
        ):
            raise ValueError()

        self.__dict__[name] = value
