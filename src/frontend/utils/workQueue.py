import json

import pika

from flask import current_app


def get_queue_element(queue_name):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=current_app.config['queue_host']))
    channel = connection.channel()
    method_frame, header_frame, body = channel.basic_get(queue=queue_name)
    if method_frame:
        channel.basic_ack(method_frame.delivery_tag)
        return False, json.loads(body)
    else:
        return True, {}


def queue_exists(queue_name):
    parameters = pika.ConnectionParameters(current_app.config['queue_host'])
    conn = pika.BlockingConnection(parameters=parameters)
    channel = conn.channel()
    try:
        channel.queue_declare(queue=queue_name, passive=True)
        conn.close()
        return True
    except:
        conn.close()
        return False


def create_queue(queue_host, queue_name):
    parameters = pika.ConnectionParameters(host=queue_host)
    conn = pika.BlockingConnection(parameters=parameters)
    channel = conn.channel()
    try:
        channel.exchange_declare(exchange='src', durable=True)
        channel.queue_declare(queue=queue_name)
        channel.queue_bind(exchange='src', queue=queue_name)
        conn.close()
    except:
        conn.close()


def publish(queue_host, queue_name, body):
    parameters = pika.ConnectionParameters(host=queue_host)
    conn = pika.BlockingConnection(parameters=parameters)
    channel = conn.channel()
    channel.basic_publish(exchange='src',
                          routing_key=queue_name,
                          body=body.encode('utf-8'))
    conn.close()


def get_channel():
    parameters = pika.ConnectionParameters(host=current_app.config['queue_host'])
    conn = pika.BlockingConnection(parameters=parameters)
    channel = conn.channel()
    return channel
