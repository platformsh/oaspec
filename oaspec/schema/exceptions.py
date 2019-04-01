# -*- coding: utf-8 -*-

class OASpecParserError(ValueError):

    def __init__(self, msg, field):

        error_msg = f"Error processing `{field}` field: {msg}"
        ValueError.__init__(self, error_msg)

        self.msg = msg
        self.field = field

class OASpecParserWarning(RuntimeWarning):

    def __init__(self, msg, location=None):

        error_msg = msg
        if location:
            error_msg = "Issue is at {}: {}".format(location, msg)

        RuntimeWarning.__init__(self, error_msg)

        self.msg = msg
        if location:
            self.location = location
