from unittest import TestCase
from src.bot.fuzzers.libFuzzer.engine import Engine


class Test(TestCase):
    def test_engine(self):
        libfuzzEngine = Engine()
