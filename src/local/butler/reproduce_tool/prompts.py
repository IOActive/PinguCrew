"""Console input functions for the reproduce tool."""


def get_string(prompt):
  """Prompt the user for a string from console input."""
  return input(prompt + ': ')


def get_boolean(prompt):
  """Return a boolean representing a yes/no answer to a prompt."""
  result = get_string(prompt + ' (Y/n)')
  return result.lower() == 'y'
