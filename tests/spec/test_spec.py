#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2018 Platform.sh
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import pytest
from pathlib import Path
from oaspec.spec import OASpec
from oaspec.spec.spec import OASpecParser, OASpecParserError

import json
import yaml as pyyaml
from oaspec.utils import yaml

def get_test_data(file_path):
    return Path.cwd() / "tests/data" / file_path

def load_yaml(file_path):
    with Path(file_path).open('r', encoding='utf-8') as f:
        return yaml.load(f)

def load_json(file_path):
    with Path(file_path).open('r', encoding='utf-8') as f:
        return json.load(f)

class TestCreateOASpec(object):

    def test_create_empty_object(self):

        oas = OASpec()

        assert oas._spec_file == None
        assert oas._raw_spec == None

    def test_create_empty_object_spec_is_none(self):

        oas = OASpec(spec=None)

        assert oas._spec_file == None
        assert oas._raw_spec == None

    def test_create_object_with_yaml_file(self):

        spec_path_string = str(get_test_data("petstore-3.0.0.yaml"))
        oas = OASpec(spec=spec_path_string)

        assert str(oas._spec_file) == spec_path_string
        assert oas._raw_spec.keys() == load_yaml(spec_path_string).keys()
        assert oas._raw_spec == load_yaml(spec_path_string)

    def test_create_object_with_json_file(self):

        spec_path_string = str(get_test_data("petstore-3.0.0.json"))
        oas = OASpec(spec=spec_path_string)

        assert str(oas._spec_file) == spec_path_string
        assert oas._raw_spec.keys() == load_json(spec_path_string).keys()
        assert oas._raw_spec == load_json(spec_path_string)

    def test_create_object_with_yaml_raw(self):

        spec_path = get_test_data("petstore-3.0.0.yaml")
        with spec_path.open('r', encoding='utf-8') as f:
            raw_spec = f.read()

        oas = OASpec(spec=raw_spec)

        assert oas._spec_file == None
        assert oas._raw_spec.keys() == load_yaml(str(spec_path)).keys()
        assert oas._raw_spec == load_yaml(str(spec_path))

    def test_create_object_with_json_raw(self):

        spec_path = get_test_data("petstore-3.0.0.json")
        with spec_path.open('r', encoding='utf-8') as f:
            raw_spec = f.read()

        oas = OASpec(spec=raw_spec)

        assert oas._spec_file == None
        assert oas._raw_spec.keys() == load_json(str(spec_path)).keys()
        assert oas._raw_spec == load_json(str(spec_path))

    def test_create_object_with_json_dict(self):

        spec_path = get_test_data("petstore-3.0.0.json")
        with spec_path.open('r', encoding='utf-8') as f:
            dict_spec = json.load(f)

        oas = OASpec(spec=dict_spec)

        assert oas._spec_file == None
        assert oas._raw_spec.keys() == load_json(str(spec_path)).keys()
        assert oas._raw_spec == load_json(str(spec_path))

    def test_create_object_with_yaml_dict(self):

        spec_path = get_test_data("petstore-3.0.0.yaml")
        with spec_path.open('r', encoding='utf-8') as f:
            dict_spec = pyyaml.load(f)

        oas = OASpec(spec=dict_spec)

        assert oas._spec_file == None
        assert oas._raw_spec.keys() == load_yaml(str(spec_path)).keys()
        assert oas._raw_spec == load_yaml(str(spec_path))

    def test_create_object_with_other_raw_spec(self):

        spec_path_string = str(get_test_data("petstore-3.0.0.yaml"))
        oas = OASpec(spec=spec_path_string)

        second_oas = OASpec(spec=oas._raw_spec)

        assert second_oas._spec_file == None
        assert second_oas._raw_spec.keys() == oas._raw_spec.keys()
        assert second_oas._raw_spec == oas._raw_spec

        assert second_oas._raw_spec.keys() == load_yaml(spec_path_string).keys()
        assert second_oas._raw_spec == load_yaml(spec_path_string)

    def test_create_object_with_loaded_yaml(self):

        spec_path_string = str(get_test_data("petstore-3.0.0.yaml"))
        oas = OASpec()

        oas.load_file(spec_path_string)

        assert str(oas._spec_file) == spec_path_string
        assert oas._raw_spec.keys() == load_yaml(spec_path_string).keys()
        assert oas._raw_spec == load_yaml(spec_path_string)

    def test_create_object_with_loaded_json(self):

        spec_path_string = str(get_test_data("petstore-3.0.0.json"))
        oas = OASpec()

        oas.load_file(spec_path_string)

        assert str(oas._spec_file) == spec_path_string
        assert oas._raw_spec.keys() == load_json(spec_path_string).keys()
        assert oas._raw_spec == load_json(spec_path_string)

    def test_create_object_with_parsed_yaml(self):

        spec_path = get_test_data("petstore-3.0.0.yaml")
        spec_path_string = str(spec_path)
        with spec_path.open('r', encoding='utf-8') as f:
            raw_spec = f.read()

        oas = OASpec()
        oas.load_raw(raw_spec)

        assert oas._spec_file == None
        assert oas._raw_spec.keys() == load_yaml(spec_path_string).keys()
        assert oas._raw_spec == load_yaml(spec_path_string)

    def test_create_object_with_invalid_type(self):

        with pytest.raises(TypeError):
            oas = OASpec(spec=list())

class TestOASpecParser(object):

    def test_parser_creation(self):
        spec_path_string = str(get_test_data("petstore-3.0.0.yaml"))
        oas = OASpec(spec=spec_path_string)

        parser = OASpecParser(oas, oas._raw_spec)

        assert parser.spec_object is oas
        assert parser.raw_spec is oas._raw_spec

    def test_version_parser(self):
        spec_path_string = str(get_test_data("petstore-3.0.0.yaml"))
        oas = OASpec(spec=spec_path_string)
        oas.parse_spec()

        assert oas.openapi == "3.0.0"

    def test_invalid_version_variations(self):
        spec_path_string = str(get_test_data("petstore-3.0.0.yaml"))
        oas = OASpec(spec=spec_path_string)
        oas.parse_spec()

        assert oas.openapi == "3.0.0"

        variations = [
            "1.0.0",
            "2.0.0",
            "3.0",
            "3",
            "3.100.0",
            "3.0.100"
        ]

        for ver in variations:
            oas._raw_spec["openapi"] = ver
            with pytest.raises(OASpecParserError) as excinfo:
                oas.parse_spec()

            assert "Invalid version number" in str(excinfo.value)

    def test_version_missing(self):
        spec_path_string = str(get_test_data("petstore-3.0.0.yaml"))
        oas = OASpec(spec=spec_path_string)

        del oas._raw_spec["openapi"]
        with pytest.raises(OASpecParserError) as excinfo:
            oas.parse_spec()

        assert "No value specified" in str(excinfo.value)

    def test_version_swagger_key(self):

        spec_path_string = str(get_test_data("petstore-3.0.0.yaml"))
        oas = OASpec(spec=spec_path_string)

        del oas._raw_spec["openapi"]
        oas._raw_spec["swagger"] = "2.0"
        with pytest.raises(OASpecParserError) as excinfo:
            oas.parse_spec()

        assert "oaspec only supports OpenAPI" in str(excinfo.value)
