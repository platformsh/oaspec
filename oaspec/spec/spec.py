# -*- coding: utf-8 -*-

import re
import json
from ..utils import yaml

from pathlib import Path

from typing import Optional, Union, MutableMapping

# from collections.abc import MutableMapping as CollectionMutableMapping
from ruamel.yaml.comments import CommentedMap


class OASpec(object):
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
        self._raw_spec: Union[dict, CommentedMap, None] = None

        self.openapi: str = None
        self.info = None
        self.servers = list()
        self.paths = None
        self.components = None
        self.security = list()
        self.tags = list()
        self.externalDocs = None

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

    def parse_spec(self):
        OASpecParser(self, self._raw_spec).parse_all()


class OASpecParserError(ValueError):

    def __init__(self, msg, field):

        error_msg = f"Error processing `{field}` field: {msg}"
        ValueError.__init__(self, error_msg)

        self.msg = msg
        self.field = field

class OASpecParser(object):
    """Object to parse a raw OpenAPI specification."""

    def __init__(self, spec_object: OASpec, raw_spec: CommentedMap):

        self.spec_object: OASpec = spec_object
        self.raw_spec: CommentedMap = raw_spec

    def parse_all(self):
        self.parse_version()
        self.parse_info()

    def parse_version(self):

        if "swagger" in self.raw_spec:
            raise OASpecParserError("oaspec only supports OpenAPI >= 3.0.0", "openapi")

        if "openapi" not in self.raw_spec:
            raise OASpecParserError("No value specified for required field.", "openapi")

        if re.fullmatch(r"\A3\.\d{1,2}\.\d{1,2}\Z", self.raw_spec["openapi"]) is None:
            raise OASpecParserError("Invalid version number.", "openapi")

        self.spec_object.openapi = self.raw_spec["openapi"]

    def parse_info(self):

        if "info" not in self.raw_spec:
            raise OASpecParserError("No value specified for required field.", "info")

class OASpecInfo(object):

    def __init__(self):
        pass
