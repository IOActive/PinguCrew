import os

from src.backend import CrashReceiver
from src.backend import CrashVerificationCollector
from src.backend import CrashVerificationSender
from src.backend import StatsCollector


def main():
    env = os.environ.get("ENV")
    if env == "LOCAL":
        from src import local_global_config as global_config
    elif env == "DOKER":
        from src import docker_global_config as global_config
    else:
        from src import local_global_config as global_config

    crash_verification_sender = CrashVerificationSender.CrashVerificationSender(global_config)
    crash_verification_collector = CrashVerificationCollector.CrashVerificationCollector(global_config)
    stats_collector = StatsCollector.StatsCollector(global_config)
    crash_receiver = CrashReceiver.CrashReceiver(global_config)

    crash_verification_collector.start()
    crash_verification_sender.start()
    stats_collector.start()
    crash_receiver.start()

    crash_verification_collector.join()
    crash_verification_sender.join()
    stats_collector.join()
    crash_receiver.join()


if __name__ == '__main__':
    main()
