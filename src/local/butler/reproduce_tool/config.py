"""Configuration helpers for the reproduce tool."""

from urllib import parse

from bot._internal.base import json_utils
from local.butler.reproduce_tool import errors
from local.butler.reproduce_tool import http_utils

REPRODUCE_TOOL_CONFIG_HANDLER = '/reproduce-tool/get-config'


class ReproduceToolConfiguration(object):
  """Dynamically loaded configuration for the reproduce tool."""

  def __init__(self, testcase_url):
    testcase_url_parts = parse.urlparse(testcase_url)
    config_url = testcase_url_parts._replace(
        path=REPRODUCE_TOOL_CONFIG_HANDLER).geturl()
    response, content = http_utils.request(config_url, body={})
    if response.status != 200:
      raise errors.ReproduceToolUnrecoverableError('Failed to access server.')

    self._config = json_utils.loads(content)

  def get(self, key):
    """Get a config entry."""
    return self._config[key]
