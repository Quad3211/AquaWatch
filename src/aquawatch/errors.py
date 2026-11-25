"""Error types for problems with the user's data or input (not bugs).

``DataError`` subclasses ``ValueError`` so existing callers that catch
ValueError keep working. The ``aquawatch`` command turns DataError (and
SettingsError, FileNotFoundError) into a one-line message; any other
exception is a bug and keeps its full traceback.
"""

from __future__ import annotations


class DataError(ValueError):
    """The data (or a date/choice derived from it) cannot be used as given."""
