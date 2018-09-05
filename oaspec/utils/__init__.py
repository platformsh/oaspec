# -*- coding: utf-8 -*-

import ruamel.yaml

yaml = ruamel.yaml.YAML()
yaml.width = 10000
yaml.preserve_quotes = True
yaml.map_indent = 2
yaml.sequence_indent = 4
yaml.sequence_dash_offset = 2
yaml.allow_duplicate_keys = True

__all__ = {
    "yaml",
}
