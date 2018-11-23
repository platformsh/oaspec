# -*- coding: utf-8 -*-

class Schema(object):

    _PRIMITIVES = {
        "string",
        "boolean",
        "number",
        "integer",
    }

    def __init__(self, spec):
        self._raw_spec = spec

        print(self._raw_spec)
#         jsonschema.validate(self._raw_spec, self._raw_schema)
        if not self.validate(self._raw_spec, True):
            print("VALIDATION ERROR")

#         print("Currently in", self.__class__, self._raw_spec)
        if self._boolean_subschema:
#             print("is", self.__class__)
            for subschema_cls in self._boolean_subschema_classes:
#                 print("Testing subschema:", subschema_cls.__name__)
                if subschema_cls.validate(self._raw_spec):
#                     print("correct subschema", subschema_cls.__name__)
                    self = subschema_cls(self._raw_spec)
                    break
        elif self._type in self._PRIMITIVES:
            self.value = spec
        elif self._type == "object":
#             print(self.__class__.__name__)
#             print(self._raw_schema)
#             print(self._raw_spec)
            self.set_properties()
        elif self._type == "array":
            self.value = [self._items(item) for item in spec]

    def set_properties(self):
        if not self._present_properties:
            self._present_properties = set()

        # Set named properties
        for prop, prop_class in self._properties.items():
            if prop in self._raw_spec:
                self._present_properties.add(prop)
                setattr(self, prop, prop_class(self._raw_spec[prop]))
            else:
                if prop in self._required:
                    raise OASpecParserError("Missing required field.", prop)

        # Set patterned properties
        for prop, prop_class in self._raw_spec.items():
            if prop[0] == "/":
                self._present_properties.add(prop)


        # Set additional properties
        if self._additional_properties is not False:
            for prop, value in self._raw_spec.items():
                if prop in self._present_properties:
#                     if self.__class__.__name__ == "schemaObject":
                    continue

#                 print("Trying", prop, "in", self.__class__.__name__)
                self._present_properties.add(prop)
#                 print(self._additional_properties)
                setattr(self, prop, self._additional_properties(value))

    @classmethod
    def validate(cls, spec, raise_on_failure=False):
        try:
            jsonschema.validate(spec, cls._raw_schema)
            return True
        except jsonschema.ValidationError as e:
            if raise_on_failure:
                raise e

            return False
        except RecursionError:
            return True

    def __getattr__(self, name):
        if name == "value":
            if self._type == "object":
                return {key:getattr(self, key) for key in self._present_properties}

    def __repr__(self):
        return str(self.value)

    def __getitem__(self, key):
        if self._type != "array":
            raise TypeError(f"{self.__name__} does not support indexing")

        return self.value[key]

def def_key(key):
    return f"#/definitions/{key}"

def build_schema(schema, schema_base, schema_class, object_defs=None):


    if schema.keys() == {"$ref": None}.keys():
        return object_defs[schema["$ref"]]

    raw_schema = getattr(schema_class, "_raw_schema", dict())
    if not raw_schema:
        schema_class._raw_schema = raw_schema
    raw_schema.update(schema)


    bool_type = [key for key in schema.keys() if key in {"allOf", "anyOf", "oneOf"}]
    if bool_type:
        bool_type = bool_type[0]
        schema_class._boolean_subschema = bool_type

        schema_class._boolean_subschema_classes = list()
        for subschema in schema[bool_type]:
            subschema_name = "".join([
                schema_class.__name__,
                "_subschema_",
                str(abs(hash(str(subschema)))),
            ])

            subschema_class = build_schema(
                subschema,
                schema_base,
                type(subschema_name, (schema_base,), dict()),
                object_defs,
            )

            schema_class._boolean_subschema_classes.append(subschema_class)

        schema_class._raw_schema[bool_type] = [subschema._raw_schema for subschema in schema_class._boolean_subschema_classes]

        return schema_class
    else:
        schema_class._boolean_subschema = False

    if not hasattr(schema_class, "_id"):
        schema_class._id = schema.get("$id", "")

    schema_class._validation_schema = schema.get("$schema", "")
    schema_class._description = schema.get("description", "")
    schema_class._type = schema.get("type", "")
    schema_class._required = set(schema.get("required", []))

    defs = schema.get("definitions", dict())
    if defs:
        schema_class._definitions = {
            def_key(key):type(key, (Schema,), {"_raw_schema": dict()})
            for key in defs.keys()
        }

    if not object_defs:
        object_defs = dict(schema_class._definitions)
    else:
        object_defs = dict(object_defs)

    for key, value in defs.items():

        subschema_class = schema_class._definitions[def_key(key)]
        if "$id" not in value:
            subschema_class._id = def_key(key)
        schema_class._definitions[def_key(key)] = build_schema(
            value,
            schema_base,
            subschema_class,
            object_defs
        )

    props = schema.get("properties", dict())
    schema_class._properties = dict()
    for prop, value in props.items():
        if "$ref" in value:
            subschema = object_defs[value["$ref"]]
            schema_class._properties[prop] = subschema

            schema_class._raw_schema["properties"][prop] = subschema._raw_schema
        else:
            prop_object_name = "".join([
                schema_class._id.split("/")[-1],
                "_",
                prop,
                "Object"
            ])

            subschema = build_schema(
                value,
                schema_base,
                type(prop_object_name, (schema_base,), dict()),
                object_defs
            )

            schema_class._properties[prop] = subschema
            schema_class._properties[prop]._id = prop_object_name
            schema_class._raw_schema["properties"][prop] = subschema._raw_schema

    if schema_class._type == "array":
        items_object_name = "".join([
            schema_class.__name__,
            "_items"
        ])

        schema_class._items = build_schema(
            schema["items"],
            schema_base,
            type(items_object_name, (schema_base,), dict()),
            object_defs,
        )

        schema_class._raw_schema["items"] = schema_class._items._raw_schema

    pattern_props = schema.get("patternProperties", dict())
    schema_class._pattern_properties = dict()
    for pattern, value in pattern_props.items():
        pattern_prop_name = "".join([
            schema_class.__name__,
            "_pattern_prop_",
            str(abs(hash(pattern))),
        ])

        subschema = build_schema(
            value,
            schema_base,
            type(pattern_prop_name, (schema_base,), dict()),
            object_defs,
        )

        schema_class._pattern_properties[pattern] = subschema

        schema_class._raw_schema["patternProperties"][pattern] = subschema._raw_schema

    additional_props = schema.get("additionalProperties", True)
    if additional_props:
        if additional_props is True:
#             schema_class._additional_properties = def_key("any")
            additional_props = {"$ref": def_key("any")}

        additional_props_name = "".join([
            schema_class.__name__,
            "_additional_props",
        ])

        schema_class._additional_properties = build_schema(
            additional_props,
            schema_base,
            type(additional_props_name, (schema_base,), dict()),
            object_defs,
        )

        schema_class._raw_schema["additionalProperties"] = schema_class._additional_properties._raw_schema


    return schema_class
