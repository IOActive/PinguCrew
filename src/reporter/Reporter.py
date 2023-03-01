import json
import logging
import sys
from multiprocessing import Process
from urllib.parse import urljoin

import requests

from src.reporter import config
from src.reporter.EmailGenerator import EmailGenerator
from src.reporter.EmailSender import EmailSender
from src.reporter.StatsFetcher import StatsFetcher


class Reporter(Process):
    base_url = config.base_url
    email = config.email
    password = config.password
    recipients = config.recipients
    authentication_token = config.authentication_token


    def run(self):
        stats = StatsFetcher(self.base_url, self.authentication_token).fetch_general_and_last_day_crashes_stats_for_every_job()
        email = EmailGenerator().process_stats_to_tabular_output(stats)
        EmailSender().send_mails_to_all_recipients(email, self.recipients)


Reporter().run()

