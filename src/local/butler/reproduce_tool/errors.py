"""Error helper classes for the reproduce tool."""


class ReproduceToolError(Exception):
  """Base class for reproduce tool exceptions."""


class ReproduceToolUnrecoverableError(ReproduceToolError):
  """Unrecoverable errors."""
