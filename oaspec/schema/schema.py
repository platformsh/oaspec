# -*- coding: utf-8 -*-

import re
import jsonschema
from copy import deepcopy
from warnings import warn
from io import StringIO, IOBase
from pathlib import Path
import json

from .exceptions import OASpecParserError, OASpecParserWarning
from .funcs import def_key, get_all_refs, get_def_classes, schema_hash
from ..utils import yaml

class Schema(object):

    _PRIMITIVES = {
        "string",
        "boolean",
        "number",
        "integer",
    }

    def __init__(self, spec, path=None, gentle_validation=False):
        self._raw_spec = deepcopy(spec)

        try:
            self.validate(self._raw_spec, True)
            self._gentle_validation = False
        except jsonschema.ValidationError as e:
            if not gentle_validation:
                raise e
            self._gentle_validation = False

        # If the class has the _boolean_subschema attribute set to something
        # other than False, detect which definition is present in the parsed
        # specification and reinitialize the object as the corresponding class
        if self._boolean_subschema:
            # print("Raw spec name:", type(self._raw_spec).__name__, )
            # if issubclass(type(self._raw_spec), Schema):
            #     if type(self.)

            for subschema_cls in self._boolean_subschema_classes:
                if subschema_cls.validate(self._raw_spec):
                    self.__class__ = subschema_cls
                    self.__init__(self._raw_spec, path, self._gentle_validation)
                    return


            # print(self._raw_spec._raw_spec)
            # print(self._boolean_subschema_classes)
            # print(type(self._raw_spec).__name__)
            # print(path)
            raise RuntimeError("Could not find matching subschema")

        self._path = deepcopy(path) if path else []

        # if "type" in self._raw_spec:
        #     print(self._path, self._raw_spec["type"], self._type)

        if self._type in self._PRIMITIVES:
            self._value = spec
        elif self._type == "enum":
            if spec in self._enum:
                self._value = spec
            else:
                raise TypeError(f"Value {spec} not in {self._enum}")
        elif self._type == "array":
            # Create a new object for each item in the array using the class
            # specified in the _items attribute
            self._value = [
                self._items(
                    item,
                    self._generate_path("array"),
                    self._gentle_validation
                ) for item in spec
            ]
        elif not isinstance(spec, dict):
            self._value = deepcopy(spec)
        else:
            self._set_properties()
            self._set_object_methods()
            # if len(self._path) > 2 and self._path[-2] == "ssh_keys":
            #     exit()

    def _set_properties(self):
        # print(self._path)
        # if not hasattr(self, "_present_properties"):
        self._present_properties = set()
        self._object_properties = dict()

        # Set named properties by looking at each property present
        # in the schema definition and checking if it exists in the spec
        # for prop, prop_class in self._properties.items():
        #     if prop in self._raw_spec:
        #         self._present_properties.add(prop)
        #         # setattr(self, prop, prop_class(self._raw_spec[prop]))
        #         self._object_properties[prop] = prop_class(self._raw_spec[prop], self._generate_path(prop), self._gentle_validation)
        #     else:
        #         if prop in self._required:
        #             raise OASpecParserError("Missing required field.", prop)

        for prop, value in self._raw_spec.items():
            if prop in self._properties:
                self._present_properties.add(prop)
                self._object_properties[prop] = self._properties[prop](value, self._generate_path(prop), self._gentle_validation)
                # if "ssh_keys" in self._path:
                #     print(prop)
                #     print(value)
                #     print(self._object_properties[prop])
                #     print(self._object_properties[prop]._raw_schema)
                #     print(self._object_properties[prop]._type)
                #     print(self._properties[prop])
                #     print()

        # Set patterned properties by checking each key in the spec that hasn't
        # already been parsed and checking if it matches the pattern. Create
        # a new object from the value using the definition specified in the schema
        for pattern, prop_class in self._pattern_properties.items():
            for prop, value in self._raw_spec.items():
                if prop in self._present_properties:
                    continue

                if self._compiled_patterns[pattern].search(prop):
                    self._present_properties.add(prop)
                    # setattr(self, prop, prop_class(value))
                    self._object_properties[prop] = prop_class(value, self._generate_path(prop), self._gentle_validation)


        # Set additional properties by parsing every key in the spec that
        # hasn't already been parsed
        if self._additional_properties is not False:
            for prop, value in self._raw_spec.items():
                if prop in self._present_properties:
                    continue
                elif prop == "$schema":
                    continue

                self._present_properties.add(prop)
                # setattr(self, prop, self._additional_properties(value))
                self._object_properties[prop] = self._additional_properties(value, self._generate_path(prop), self._gentle_validation)

        for prop in self._present_properties:
            if hasattr(self.__class__, prop):
                warning_text = (
                    "An Schema class attribute overlaps with the mapping key \"{}\" "
                    "located at \n{}"
                ).format(
                    prop,
                    self._format_path()
                )
                warn(
                    warning_text,
                    OASpecParserWarning
                )

    def _validate_property(self, prop, return_class=True):
        if prop in self._properties:
            if return_class:
                return "schema_property", self._properties[prop]
            return True

        for pattern, prop_class in self._pattern_properties.items():
            if self._compiled_patterns[pattern].search(prop):
                if return_class:
                    return "pattern_property", prop_class
                return True

        if self._additional_properties is not False:
            if prop == "$schema":
                if return_class:
                    return False, None
                return False

            if return_class:
                return "additional_property", self._additional_properties
            return True

        if return_class:
            return False, None
        return False


    def _set_object_methods(self):
        self._keys = self.__keys__

    def _amend(self, amendments_spec):
        if isinstance(amendments_spec, Schema):
            raise RuntimeError("Amending a spec with another spec is not currently supported")

        # if self._path and self._path[-1] == "ssh_keys":
            # print(self)
            # print(self._id)
            # print(self._parsing_schema)
            # print(amendments_spec)
            # exit()
        if self._is_object():
            for prop, amendments in amendments_spec.items():
                if prop in self:
                    self[prop]._amend(amendments)
                    continue

                prop_type, prop_class = self._validate_property(prop)
                if isinstance(amendments, dict) and "__override" in amendments:
                    if not amendments["__override"]:
                        continue

                    if prop_class._is_primitive():
                        amendments = amendments["__override"]
                    elif prop_class._is_array():
                        if isinstance(amendments["__override"], list):
                            amendments = amendments["__override"]
                        else:
                            amendments = list(amendments["__override"])


                self._present_properties.add(prop)
                self._object_properties[prop] = prop_class(amendments, self._generate_path(prop), self._gentle_validation)
        elif self._is_array():
            # print(self._generate_path("array"))
            revised_list = list()
            delete_items = set()
            for item in amendments_spec["__override"]:
                if not item:
                    continue
                elif item == "__del *":
                    delete_items = set(amendments_spec["__original"])
                elif item.startswith("__del"):
                    delete_items.add(item[6:])
                else:
                    revised_list.append(self._items(item, self._generate_path("array")))

            for item in self._value:
                if item in amendments_spec["__original"] or item in amendments_spec["__override"]:
                    if item._value in delete_items:
                        continue

                    revised_list.append(item)

            self._value = revised_list
        elif self._is_primitive():
            if amendments_spec["__override"]:
                self._value = amendments_spec["__override"]

    def _update(self, other, no_override=False, overwrites_config=None):
        self.__update(self, other, no_override, overwrites_config)

    @staticmethod
    def __update(base, other, no_override=False, overwrites_config=None):
        allow_overwrite_subkeys = False
        new_overwrites = None
        for key in other:
            if overwrites_config:
                if key in overwrites_config:
                    if overwrites_config[key] == "__overwrite_subkeys":
                        allow_overwrite_subkeys = True
                    else:
                        new_overwrites = overwrites_config[key]

            if key in base:
                if base[key]._is_primitive():
                    if no_override:
                        continue

                    base[key]._value = other[key]._value
                elif base[key]._is_object():
                    if not allow_overwrite_subkeys:
                        if no_override:
                            continue
                    Schema.__update(base[key], other[key], no_override, new_overwrites)
            else:
                # print(key)
                base[key] = other[key]

    def __setitem__(self, key, value):

        prop_type, prop_class = self._validate_property(key)

        if prop_class.__name__ == type(value).__name__:
            self._present_properties.add(key)
            self._object_properties[key] = value
        # elif check to see if the type value name is present in the bool
        elif prop_class._boolean_subschema:
            for subschema in prop_class._boolean_subschema_classes:
                if subschema.__name__ == type(value).__name__:
                    self._present_properties.add(key)
                    self._object_properties[key] = value
        else:
            self._present_properties.add(key)
            self._object_properties[key] = prop_class(value, self._generate_path(key), True)

    @classmethod
    def _is_primitive(cls):
        return cls._type in cls._PRIMITIVES or cls._type == "enum"

    @classmethod
    def _is_array(cls):
        return cls._type == "array"

    @classmethod
    def _is_object(cls):
        return cls._type == "object"

    # def _serialize(self):
    #     if self._is_primitive():
    #         return

    @classmethod
    def validate(cls, spec, raise_on_failure=False):
        """Validate a spec with the schema defined in this class.

        This will use the OAS schema stored in the class's `_parsing_schema`
        attribute to validate the passed specification.

        Parameters:
            spec: The raw OpenAPI specification to validate.
            raise_on_failure: Specify whether to raise a ValidationError exception
                when validation fails. Returns False on validation error if set
                to False.

        Returns:
            bool: Returns True if spec validates successfully, returns False on
                validation failure if `raise_on_failure` is False.
        """

        try:
            jsonschema.validate(spec, cls._parsing_schema)
            return True
        except jsonschema.ValidationError as e:
            if raise_on_failure:
                raise e

            return False
        except Exception as e:
            raise e

    def _generate_path(self, next_key):
        new_path = deepcopy(self._path)
        new_path.append(next_key)
        return new_path

    def _format_path(self):
        path = []
        for idx, key in enumerate(self._path):
            if idx == 0:
                path.append(f'\t "{key}"')
            else:
                path.append(
                    '\t{}-> "{}"'.format(
                        "  "*idx,
                        key
                    )
                )

        return "\n".join(path)

    def __getattr__(self, name):
        """Access the computed representation of a specification object.

        Specification objects with a non-mapping type (string, boolean, number,
        integer, array) store their value in the object's `value` attribute,
        but objects store their mapping keys as object attributes. Calling
        `value` on a mapping object will return a dict computed from
        the properties present in the object as attributes.

        Returns:
            dict: A dict computed from properties present in the object as attributes.
        """

        if name == "_value":
            return self._object_properties
        elif name == "_present_properties" or name == "_object_properties":
            raise AttributeError(f"Property {name} not present")
        elif name in self._object_properties:
            return self._object_properties.get(name)

        raise AttributeError(f"Property {name} not present in specification")

    def _raw(self):
        if self._is_primitive():
            return self._value
        elif self._is_array():
            return [item._raw() for item in self._value]
        elif self._is_object():
            return {
                key:val._raw() for key, val in self._object_properties.items()
            }
        else:
            # print(self._path)
            # print(self)
            # print(self._type)
            # print(self._value)
            # print(self.__class__)
            # print()
            # return self._value
            # raise RuntimeError()
            pass

    def _dump_yaml(self, fp=None):
        if not fp:
            buffer = StringIO()
            yaml.dump(self._raw(), buffer)
            return buffer.getvalue()

        if isinstance(fp, Path):
            with fp.open("w", encoding="utf-8") as f:
                yaml.dump(self._raw(), f)
        elif isinstance(fp, IOBase):
            yaml.dump(self._raw(), fp)

    def _dump_json(self, fp=None):
        if not fp:
            return json.dumps(
                self._raw(),
                ensure_ascii=False,
                indent=2,
            )

        if isinstance(fp, Path):
            with fp.open("w", encoding="utf-8") as f:
                json.dump(
                    self._raw(),
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

    def __repr__(self):
        return str(self._value)

    def __eq__(self, other):
        return self._value == other

    def __getitem__(self, key):
        if self._type == "object":
            if hasattr(self, "_object_properties"):
                if key in self._object_properties:
                    return self._object_properties.get(key)
            return getattr(self, key)
        elif self._type == "array":
            return self._value[key]

        raise TypeError(f"{self.__name__} does not support indexing")

    def __contains__(self, key):
        if hasattr(self, "_object_properties"):
            return key in self._object_properties

        if self._is_array():
            if isinstance(key, Schema):
                key = key._value

            return key in [item._value for item in self._value]

        raise NotImplementedError("Object cannot check for contains")

    def __iter__(self):
        if hasattr(self, "_object_properties"):
            return iter(self._object_properties)
        elif self._is_array():
            return iter(self._value)

        raise NotImplementedError("Object is not iterable")

    # def __dir__(self):
    #     standard_attrs = {
    #         "_value"
    #     }
    #     if self._type == "object":
    #         return standard_attrs | self._object_properties.keys()
    #     else:
    #         return standard_attrs
            # return super().__dir__()

    def __keys__(self):
        """Return the keys representing the properties present in this object.

        This method creates a new dict from the intersection of keys present
        in self.__dict__ and self._present_properties, and then calls the keys()
        method on the newly created object. This is done to return a proper dict_view
        that preserves the orders of keys in the object.

        Returns:
            dict_keys: A dictview representing properties present in this schema object.
        """
        if self._type == "object":
            # return {
            #     key:None for key in self.__dict__.keys()
            #     if key in self._present_properties
            # }.keys()
            return self._object_properties.keys()
            # return self._present_properties

        raise AttributeError("Class {} does not support keys".format(self.__name__))


# OASchema = type("openapiObject", (Schema,), dict())

def build_schema(schema, schema_base, schema_class, object_defs=None):
    """Recursively build the Schema tree sub-classes for an entire OAS validation schema.

    Parameters:
        schema: The raw OAS schema used as the metadata source for the created Schema subclass.
        schema_base: The base class used to build all Schema subclasses. The `Schema` class
            (or equivalent replacement) should be passed on the first call to this function,
            while `schema_base` should always be passed when called recursively.
        schema_class: The subclass being built by this function. This object should be a
            direct subclass of the Schema class, created by calling the `type` function with
            a unique name describing the class and the Schema base class.
        object_defs: The Schema subclasses corresponding to the `definitions` property
            in an OAS schema. Definition classes are created on the first function call and
            should be passed directly on recursive calls to this function.

    Returns:
        Schema: Returns a subclass of the Schema class containing the metadata present
            in the OAS schema.
    """

    # If the object is simply a ref link to another definition, return that class directly
    # rather than generating a new class. Passes the class by reference to be used in-place.
    # if schema.keys() == {"$ref": None}.keys():
    #     return object_defs[schema["$ref"]]
    if "$ref" in schema.keys():
        return object_defs[schema["$ref"]]


    # Check if Schema already has a raw schema associated with it
    if getattr(schema_class, "_raw_schema", False):
        raise RuntimeError("schema_class already has _raw_schema")

    raw_schema = getattr(schema_class, "_raw_schema", {"definitions": dict()})
    schema_class._raw_schema = raw_schema
    raw_schema.update(deepcopy(schema))


    # Add the raw schema that will be used for schema validation to the metadata.
    # In contrast to schema_class._raw_schema, the parsing schema must not contain
    # circular references (i.e. "$ref" links won't be de-referenced in-place).
    # If this subclass represents an object defined in the `definitions` property
    # of a schema, the _parsing_schema will already be present.
    if not hasattr(schema_class, "_parsing_schema"):
        schema_class._parsing_schema = deepcopy(schema)


    # If the object contains a subschema with boolean logic, the function will create
    # a special-case class that will hold the potential subclasses and re-initialize
    # itself as one of the subclasses during parsing.
    bool_type = [key for key in schema.keys() if key in {"allOf", "anyOf", "oneOf"}]
    if bool_type:

        bool_type = bool_type[0]
        schema_class._boolean_subschema = bool_type
        schema_class._boolean_subschema_classes = list()

        # Generate a Schema subclass for each defined subclass, basing the subclass
        # name on the hash of the definition
        for subschema in schema[bool_type]:
            subschema_name = "".join([
                schema_class.__name__,
                "_subschema_",
                schema_hash(subschema),
            ])

            subschema_class = build_schema(
                subschema,
                schema_base,
                type(subschema_name, (schema_base,), dict()),
                object_defs,
            )

            schema_class._boolean_subschema_classes.append(subschema_class)

        schema_class._raw_schema[bool_type] = [subschema._raw_schema for subschema in schema_class._boolean_subschema_classes]
    else:
        schema_class._boolean_subschema = False

    # Extract metadata for direct inclusion in created Schema subclass
    if not hasattr(schema_class, "_id"):
        schema_class._id = schema.get("$id", "")

    schema_class._validation_schema = schema.get("$schema", "")
    schema_class._description = schema.get("description", "")
    schema_class._type = schema.get("type", "")
    if not schema_class._type and "enum" in schema:
        schema_class._type = "enum"
        schema_class._enum = schema.get("enum")
    schema_class._required = set(schema.get("required", []))


    defs = schema.get("definitions", dict())
    # If the `definitions` property is defined in the OAS schema, process those definitions
    if defs:

        # If `object_defs` has been passed to this function, then we are currently deeper
        # than the top level of the Schema, and the `definition` property is not currently
        # supported at lower levels.
        # TODO: Support definitions at deeper levels of the schema.
        if object_defs:
            raise RuntimeError("Definitions are only allowed at top level of spec")

        # Generate a bare Schema subclass for each object defined in `definitions`. The subclass
        # metadata will be added later, but bare classes are needed to allow recursive referencing
        # within definition objects.
        schema_class._definitions = {
            def_key(key):type(key, (Schema,), {"_raw_schema": dict(), "_parsing_schema": deepcopy(value)})
            for key, value in defs.items()
        }
        object_defs = schema_class._definitions
    else:
        # Subclasses need to have referenced definitions included in their _parsing_schema
        # for schema validation to succeed. This extracts the ref links from the schema
        # and adds the referenced raw objects to the `definitions` of the parsing schema
        sub_definitions = get_def_classes(schema_class._parsing_schema, object_defs)
        if sub_definitions:
            schema_class._parsing_schema["definitions"] = sub_definitions


    # After bare classes have been created for all definitions, actually add metadata from schema.
    # This section will only run at the top level of the schema.
    for key, value in defs.items():

        # Use the existing Schema subclass to allow for passing classes by reference
        subschema_class = schema_class._definitions[def_key(key)]

        if "$id" not in value:
            subschema_class._id = def_key(key)

        schema_class._definitions[def_key(key)] = build_schema(
            value,
            schema_base,
            subschema_class,
            object_defs
        )

    # Process the named properties defined in the OAS schema and created a subclass
    # for the value defined in each mapping
    props = schema.get("properties", dict())
    schema_class._properties = dict()
    for prop, value in props.items():
        # if "$ref" in value:
        #    subschema = object_defs[value["$ref"]]
        #    schema_class._properties[prop] = subschema
        #
        #    schema_class._raw_schema["properties"][prop] = subschema._raw_schema
        # else:

        # Create a name for the subclass based on the property name and the object
        # that it is within.
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


    # If the object being parsed is an array type, create a class based
    # on the subschema present in the "items" key, defaulting to the "any" type.
    # During parsing, the spec will be passed to the class created here.
    if schema_class._type == "array":
        if "items" not in schema:
            schema["items"] = {"$ref": def_key("any")}

        items_object_name = "".join([
            schema_class.__name__,
            "_items"
        ])

        # print(items_object_name)
        # print(schema["items"])
        # print()
        schema_class._items = build_schema(
            schema["items"],
            schema_base,
            type(items_object_name, (schema_base,), dict()),
            object_defs,
        )

        schema_class._raw_schema["items"] = schema_class._items._raw_schema


    # Parse the patterned properties listed in the schema and create a Schema
    # subclass for each.
    pattern_props = schema.get("patternProperties", dict())
    schema_class._pattern_properties = dict()
    schema_class._compiled_patterns = dict()
    for pattern, value in pattern_props.items():
        pattern_prop_name = "".join([
            schema_class.__name__,
            "_pattern_prop_",
            schema_hash(pattern),
        ])

        subschema = build_schema(
            value,
            schema_base,
            type(pattern_prop_name, (schema_base,), dict()),
            object_defs,
        )

        schema_class._pattern_properties[pattern] = subschema
        schema_class._compiled_patterns[pattern] = re.compile(pattern)

        schema_class._raw_schema["patternProperties"][pattern] = subschema._raw_schema


    # Create the subclass that will be used to create additional properties. If
    # no schema is specified, it will default to "any"
    additional_props = schema.get("additionalProperties", True)
    if additional_props:
        if additional_props is True:
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

        # schema_class._raw_schema["additionalProperties"] = schema_class._additional_properties._raw_schema

    return schema_class
