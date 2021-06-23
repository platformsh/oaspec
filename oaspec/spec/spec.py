# -*- coding: utf-8 -*-

import re
import json
from ..utils import yaml

from pathlib import Path

from typing import Optional, Union, MutableMapping

# from collections.abc import MutableMapping as CollectionMutableMapping
from ruamel.yaml.comments import CommentedMap

from ..__version__ import __root_dir__
from .. import schema
from ..schema import OASpecParserError

class OASpecParser(object):
    """The top-level object for manipulating OpenAPI specifications.

    The OASpec object is the entrypoint for creating and manipulating
    OpenAPI specifications.

    Attributes:
        _spec_file: The path of the specification source file
            (if a file was used as the specification source)
        _raw_spec: The raw, unproccessed specification source
    """

    def __init__(
            self,
            spec: Optional[Union[str, dict, MutableMapping]] = None,
    ):
        """Create a new OpenAPI specification control object.

        Parameters:
            spec: A string pointing to a YAML or JSON file containing an OpenAPI
                specification, a string containing a YAML or JSON representation
                of an OpenAPI specification, or a parsed raw, mapping of an OpenAPI
                specification.
        """

        self._spec_file: Optional[Path] = None
        self._schema = type("openapiObject", (schema.Schema,), dict()) #schema.OASchema

        if type(spec) is str:
            if (spec.endswith(".yaml") or spec.endswith(".yml") or spec.endswith(".json")):
                self.load_file(spec)
            else:
                self.load_raw(spec)
        elif isinstance(spec, dict):
            self._raw_spec = yaml.load(json.dumps(spec))
        elif isinstance(spec, CommentedMap):
            self._raw_spec = spec
        elif spec is not None:
            raise TypeError(
                "`spec` must be a file path, a raw string containing a spec, "
                "a parsed dictionary of a spec, or the _raw_spec from another OASpec"
            )

    def __setattr__(self, name, value):
        if name == "_raw_spec":
            self._process_raw_spec(value)
        else:
            self.__dict__[name] = value

    def _process_raw_spec(self, raw_spec):
        self._validate_spec(raw_spec)
        self.__dict__["_raw_spec"] = raw_spec

    def _validate_spec(self, raw_spec):
        self._load_validation_schema(raw_spec["openapi"])

    def _load_validation_schema(self, schema_version):
        specs_dir = __root_dir__ / "specs"
        spec_file = specs_dir / "oas-{}.json".format(schema_version)

        if re.fullmatch(r"\A3\.\d{1,2}\.\d{1,2}\Z", schema_version) is None:
            raise OASpecParserError("Invalid OpenAPI version number. oaspec only supports OpenAPI 3.*.*", "openapi")
        if not spec_file.exists():
            available_versions = "\n\t- ".join([f.stem[4:] for f in specs_dir.glob("oas-*.json")])
            raise OASpecParserError(
                "Schema file is missing for specified version '{}'.\nSupported versions:\n\t- {}:".format(
                    schema_version,
                    available_versions
                ),
                "openapi"
            )

        with spec_file.open("r", encoding="utf-8") as f:
            self._validation_schema = json.load(f)

        schema.build_schema(
            self._validation_schema,
            schema.Schema,
            self._schema,
        )

    def load_file(self, spec: str):
        """Load an OpenAPI specification file.

        This will open the specification file named in *spec*, resolve the file's
        absolute path, assign the path to the instance's *_spec_file* attribute,
        and assign the parsed contents of the file to the instance's *_raw_spec* attribute.

        Parameters:
            spec: The path to the OpenAPI specification file in YAML or JSON format.
        """

        # Resolving the Path passed to this function with `strict=True`
        # will automatically throw FileNotFoundError if it doesn't exist.
        self._spec_file = Path(spec).resolve(strict=True)

        with self._spec_file.open("r") as f:
            if self._spec_file.suffix in {".yaml", ".yml", ".json"}:
                self._raw_spec = yaml.load(f)
            else:
                raise ValueError("File type must end with '.yaml' or '.json'")

    def load_raw(self, spec: str):
        """Parse and return a raw OpenAPI specification.

        Parameters:
            spec: A string representing a raw OpenAPI specification.
        """

        self._raw_spec = yaml.load(spec)

    def parse_spec(self, gentle_validation=False):
        return self._schema(self._raw_spec, gentle_validation=gentle_validation)
