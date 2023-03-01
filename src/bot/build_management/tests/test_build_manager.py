from unittest import TestCase

from src.bot.build_management.build_manager import Build
from src.bot.system import environment


class TestBuild(TestCase):
    def test__build_targets(self):
        b = Build(
            "/home/roboboy/Projects/LuckyCAT/bot/builds/127.0.0.1:9001_test_770807ff2d8d31b43785f87303e8a91a87120e40/",
            '101')
        b._build_targets(
            path="/home/roboboy/Projects/LuckyCAT/bot/builds/127.0.0.1"
                 ":9001_test_770807ff2d8d31b43785f87303e8a91a87120e40/revisions/Build.sh")

    def test__build_targets_minijail(self):
        b = Build(
            "/home/roboboy/Projects/LuckyCAT/bot/builds/127.0.0.1:9001_test_770807ff2d8d31b43785f87303e8a91a87120e40/",
            '101')
        environment.load_cfg("../../startup/bot.cfg")
        b._build_targets_minijail(
            path="/home/roboboy/Projects/LuckyCAT/bot/builds/127.0.0.1"
                 ":9001_test_770807ff2d8d31b43785f87303e8a91a87120e40/revisions/Build.sh")
