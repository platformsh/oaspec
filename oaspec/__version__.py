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

from pathlib import Path

__version__      = '0.1.0'
__version_date__ = '2018-11-29'

__title__        = 'oaspec'
__description__  = 'A package of manipulating OpenAPI specifications in Python'
__url__          = 'http://github.com/platformsh/oaspec'

__author__       = 'Nick Anderegg'
__author_email__ = 'nick.anderegg@platform.sh'

__license__      = 'MIT'
__copyright__    = 'Copyright 2018 Platform.sh'

__root_dir__     = Path(__file__).parent.parent.resolve()

__all__ = [
    '__version__', '__version_date__',
    '__title__', '__description__', '__url__',
    '__author__', '__author_email__',
    '__license__', '__copyright__'
]
