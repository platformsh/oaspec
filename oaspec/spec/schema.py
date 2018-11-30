# -*- coding: utf-8 -*-

import re
import jsonschema
from copy import deepcopy

class OASpecParserError(ValueError):

    def __init__(self, msg, field):

        error_msg = f"Error processing `{field}` field: {msg}"
        ValueError.__init__(self, error_msg)

        self.msg = msg
        self.field = field

class Schema(object):

    _PRIMITIVES = {
        "string",
        "boolean",
        "number",
        "integer",
    }

    def __init__(self, spec):
        self._raw_spec = spec

        self.validate(self._raw_spec, True)

        # If the class has the _boolean_subschema attribute set to something
        # other than False, detect which definition is present in the parsed
        # specification and reinitialize the object as the corresponding class
        if self._boolean_subschema:
            for subschema_cls in self._boolean_subschema_classes:
                if subschema_cls.validate(self._raw_spec):
                    self.__class__ = subschema_cls
                    self.__init__(self._raw_spec)
                    return

        elif self._type in self._PRIMITIVES:
            self._value = spec
        elif self._type == "enum":
            if spec in self._enum:
                self._value = spec
            else:
                raise TypeError(f"Value {spec} not in {self._enum}")
        elif self._type == "array":
            # Create a new object for each item in the array using the class
            # specified in the _items attribute
            self._value = [self._items(item) for item in spec]
        elif not isinstance(spec, dict):
            self._value = spec
        else:
            self.set_properties()

    def set_properties(self):
        if not hasattr(self, "_present_properties"):
            self._present_properties = set()

        # Set named properties by looking at each property present
        # in the schema definition and checking if it exists in the spec
        for prop, prop_class in self._properties.items():
            if prop in self._raw_spec:
                self._present_properties.add(prop)
                setattr(self, prop, prop_class(self._raw_spec[prop]))
            else:
                if prop in self._required:
                    raise OASpecParserError("Missing required field.", prop)

        # Set patterned properties by checking each key in the spec that hasn't
        # already been parsed and checking if it matches the pattern. Create
        # a new object from the value using the definition specified in the schema
        for pattern, prop_class in self._pattern_properties.items():
            for prop, value in self._raw_spec.items():
                if prop in self._present_properties:
                    continue

                if self._compiled_patterns[pattern].search(prop):
                    self._present_properties.add(prop)
                    setattr(self, prop, prop_class(value))


        # Set additional properties by parsing every key in the spec that
        # hasn't already been parsed
        if self._additional_properties is not False:
            for prop, value in self._raw_spec.items():
                if prop in self._present_properties:
                    continue
                elif prop == "$schema":
                    continue

                self._present_properties.add(prop)
                setattr(self, prop, self._additional_properties(value))

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
            # if self._type == "object" or getattr(self, "_present_properties", False):
            return {key:getattr(self, key) for key in self._present_properties}

        raise AttributeError(f"Property {name} not present in specification")

    def __repr__(self):
        return str(self._value)

    def __eq__(self, other):
        return self._value == other

    def __getitem__(self, key):
        if self._type == "object":
            return getattr(self, key)
        elif self._type == "array":
            return self._value[key]

        raise TypeError(f"{self.__name__} does not support indexing")

def def_key(key):
    """Compute a definition ref from a key.

    Returns:
        str: The computed relative reference

    """
    return f"#/definitions/{key}"

def get_all_refs(schema):
    """Get all ref links in a schema.

    Traverses a schema and extracts all relative ref links from the schema,
    returning a set containing the results.

    Parameters:
        schema: An OAS schema in the form of nested dicts to be traversed.

    Returns:
        set: All of the ref links found during traversal.

    """

    all_refs = set()

    if type(schema) is dict:
        for key, val in schema.items():
            if key == "$ref" and type(val) is str:
                all_refs.add(val)

            all_refs.update(get_all_refs(val))
    elif type(schema) is list:
        for item in schema:
            all_refs.update(get_all_refs(item))

    return all_refs

def get_def_classes(schema, def_objects, ignore_keys=None):
    """Return the definition objects represented by relative refs in a schema.

    Gets all of the relative refs present in a schema object and returns a mapping
    of refs to schema objects, recursively resolving references listed in the
    retrieved schema definitions. This function is used to collect the referenced
    definitions that will be added to each schema class's `_parsing_schema` attribute.

    Parameters:
        schema: The schema to parse for relative refs.
        def_objects: A mapping of relative ref keys and the Schema sub-classes to which they
            correspond. The `_parsing_schema` will be extracted from each referenced class.
        ignore_keys: A set of keys that should be skipped when encountered during traversal,
            in order to prevent infinite recursion when encountering circular references.

    Returns:
        dict: A mapping of of relative ref keys and their corresponding raw definitions.

    """

    # Traverse the schema to get all relative ref links
    all_refs = get_all_refs(schema)

    if not all_refs:
        return {}

    def_classes = {}
    for key in all_refs:
        subkey = key.split("/")[-1]
        if ignore_keys and subkey in ignore_keys:
            continue

        subschema = deepcopy(def_objects[key]._parsing_schema)

        def_classes[subkey] = subschema

        # Recursively de-reference ref links found in retrieve definition objects
        def_classes.update(get_def_classes(def_classes[subkey], def_objects, def_classes.keys()))

    return def_classes

def schema_hash(schema):
    """Generate a string-based hash of a schema object.

    Returns:
        str: Schema hash.

    """
    return str(abs(hash(str(schema))))

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
    if schema.keys() == {"$ref": None}.keys():
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
