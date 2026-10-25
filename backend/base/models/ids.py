"""Primary keys of the models that other systems and the public refer to."""
try:
    from uuid import uuid7  # Python 3.14+
except ImportError:  # Python 3.13: the same function from the `uuid-utils` package (returns a standard uuid.UUID)
    from uuid_utils.compat import uuid7

__all__ = ['uuid7']
