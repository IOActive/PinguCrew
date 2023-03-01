import json
import logging
import os
from multiprocessing import Process

from mongoengine import connect
from mongoengine.queryset import DoesNotExist

from src import docker_global_config
from src.backend import WorkQueue
from src.database.models.Crash import Crash
from src.database.models.Job import Job
from src.database.models.Statistic import Statistic

logger = logging.getLogger(os.path.basename(__file__).split('.')[0])


class CrashReceiver(Process):
    def __init__(self, globla_config):
        super(CrashReceiver, self).__init__()
        self.globla_config = globla_config
        self.wq = WorkQueue.WorkQueue(globla_config)
        self.queue_name = 'crashes'
        if not self.wq.queue_exists(self.queue_name):
            self.wq.create_queue(self.queue_name)
        self.channel = self.wq.get_channel()

    def _insert_crash_cfuzz(self, crash_data):
        # FIXME validate user provided data
        job = Job.objects.get(name=crash_data['job_name'])
        iteration = self.get_iteration_of_crash(job)
        if crash_data['crash']:
            with open(crash_data['filename'], 'rb') as f:
                data = f.read()
            logger.debug('Inserting crash: %s.' % str(crash_data))
            cfuzz_crash = Crash(job_id=job.id,
                                crash_signal=crash_data['signal'],
                                test_case=data,
                                verified=False,
                                iteration=iteration)
            cfuzz_crash.save()
            logger.debug('Crash stored')
        else:
            logger.debug('No crash clean up')

        try:
            os.remove(crash_data['filename'])
        except OSError as e:
            print('Error: %s - %s.' % (e.filename, e.strerror))

        stats = {'fuzzer': 'cfuzz',
                 'job_id': str(job.id),
                 'job_name': job.name,
                 'runtime': 0,
                 'total_execs': '+1'}
        self.wq.publish('stats', json.dumps(stats))

    def get_iteration_of_crash(self, job):
        try:
            iteration = Statistic.objects.get(job_id=job.id).iteration
        except DoesNotExist:
            iteration = 1
        return iteration

    def _insert_crash_afl(self, crash_data):
        logger.debug('Inserting AFL crash with signal %i.' % crash_data['signal'])
        job = Job.objects.get(name=crash_data['job_name'])
        iteration = self.get_iteration_of_crash(job)
        if 'classification' in crash_data:
            afl_crash = Crash(job_id=job.id,
                              crash_signal=crash_data['signal'],
                              test_case=crash_data['crash_data'].encode(),
                              verified=crash_data['verified'],
                              crash_hash=crash_data['hash'],
                              exploitability=crash_data['classification'],
                              additional=crash_data['description'],
                              iteration=iteration)
        else:
            afl_crash = Crash(job_id=crash_data['job_name'],
                              crash_signal=crash_data['signal'],
                              test_case=crash_data['crash_data'].encode(),
                              verified=crash_data['verified'],
                              iteration=iteration)

        afl_crash.save()
        logger.debug('Crash stored')

    def _insert_crash_syzkaller(self, crash_data):
        logger.debug('Inserting Syzkaller crash with signal {}.'.format(crash_data['signal']))
        job = Job.objects.get(name=crash_data['job_name'])
        iteration = 0
        if 'classification' in crash_data:
            syzkaller_crash = Crash(job_id=job.id,
                                    crash_signal=crash_data['signal'],
                                    test_case=crash_data['test_case'].encode(),
                                    verified=crash_data['verified'],
                                    crash_hash=crash_data['hash'],
                                    exploitability=crash_data['classification'],
                                    additional=crash_data['description'],
                                    iteration=iteration)
        else:
            syzkaller_crash = Crash(job_id=job.id,
                                    crash_signal=crash_data['signal'],
                                    test_case=crash_data['test_case'].encode(),
                                    verified=crash_data['verified'],
                                    iteration=iteration)

        syzkaller_crash.save()
        logger.debug('Crash stored')

    def on_message(self, channel, method_frame, header_frame, body):
        crash_info = json.loads(body.decode('utf-8'))
        if crash_info['fuzzer'] == 'afl':
            self._insert_crash_afl(crash_info)
        elif crash_info['fuzzer'] == 'syzkaller':
            self._insert_crash_syzkaller(crash_info)
        elif crash_info['fuzzer'] == 'cfuzz':
            self._insert_crash_cfuzz(crash_info)
        else:
            logger.error('Unknown fuzzer %s' % crash_info['fuzzer'])

    def run(self):
        logger.info('Starting CrashReceiver...')
        connect(self.globla_config.db_name, host=self.globla_config.db_host)
        self.channel.basic_consume(on_message_callback=self.on_message, queue=self.queue_name)
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
            self.connection.close()
