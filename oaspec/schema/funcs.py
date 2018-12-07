# -*- coding: utf-8 -*-

import re
from copy import deepcopy

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
