import pika
import logging
import os
from src import docker_global_config

logger = logging.getLogger(os.path.basename(__file__).split(".")[0])


class WorkQueue(object):

    def __init__(self, global_config, host=None, ):
        self.global_config = global_config
        if host:
            self._host = host
        else:
            self._host = global_config.queue_host

    def queue_exists(self, queue_name):
        parameters = pika.ConnectionParameters(host=self._host)
        conn = pika.BlockingConnection(parameters=parameters)
        channel = conn.channel()
        logger.debug("Checking if queue %s exists." % queue_name)
        try:
            channel.queue_declare(queue=queue_name, passive=True)
            conn.close()
            return True
        except:
            conn.close()
            return False

    def create_queue(self, prefix):
        parameters = pika.ConnectionParameters(host=self._host)
        conn = pika.BlockingConnection(parameters=parameters)
        channel = conn.channel()
        logger.debug("Creating queue %s." % prefix)
        try:
            channel.exchange_declare(exchange='src', durable=True)
            channel.queue_declare(queue=prefix)
            channel.queue_bind(exchange='src', queue=prefix)
            conn.close()
            logger.info("Queue created.")
        except:
            conn.close()
            logger.error("Could not create queue %s" % prefix)

    def get_jobs_in_queue(self, prefix):
        parameters = pika.ConnectionParameters(host=self._host)
        conn = pika.BlockingConnection(parameters=parameters)
        channel = conn.channel()
        try:
            res = channel.queue_declare(queue=prefix, passive=True)
            messages = res.method.message_count
            conn.close()
            logger.debug("Messages in queue: %d" % res.method.message_count)
            return messages
        except:
            conn.close()
            logger.error("Could not get queue info for %s" % prefix)
            raise

    def queue_is_full(self, prefix, maximum):
        value = self.get_jobs_in_queue(prefix)
        logger.debug("Total of %d job(s) in queue %s with a maximum of %d" % (value, prefix, maximum))
        return value > maximum - 1

    def queue_is_empty(self, prefix):
        value = self.get_jobs_in_queue(prefix)
        logger.debug("Total of %d job(s) in queue" % value)
        return value == 0

    def get_pending_elements(self, prefix, maximum):
        value = self.get_jobs_in_queue(prefix)
        logger.debug("Total of %d job(s) in queue" % value)
        return maximum - value

    def publish(self, queue_name, body):
        parameters = pika.ConnectionParameters(host=self._host)
        conn = pika.BlockingConnection(parameters=parameters)
        channel = conn.channel()
        channel.basic_publish(exchange='src',
                              routing_key=queue_name,
                              body=body.encode('utf-8'))
        conn.close()

    def get_channel(self):
        parameters = pika.ConnectionParameters(host=self._host)
        conn = pika.BlockingConnection(parameters=parameters)
        channel = conn.channel()
        return channel
