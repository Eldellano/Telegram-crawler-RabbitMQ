import asyncio
import json
import os

import pika
from dotenv import load_dotenv

from tg_client import get_messages

load_dotenv()

RABBIT_HOST = os.getenv('RABBITMQ_HOST')
RABBIT_PORT = os.getenv('RABBITMQ_PORT')
RABBIT_QUEUE = os.getenv('RABBITMQ_QUEUE')
RABBIT_USER = os.getenv('RABBITMQ_USER')
RABBIT_PASS = os.getenv('RABBITMQ_PASS')


class Worker:
    def __init__(self):
        credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST,
                                                                            port=RABBIT_PORT,
                                                                            credentials=credentials))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=RABBIT_QUEUE)
        self.channel.basic_qos(prefetch_count=1)

    def send_task(self, task):
        self.channel.basic_publish(exchange='',
                                   routing_key=RABBIT_QUEUE,
                                   body=task)
        print(f'[x] Sent {task=}')
        self.connection.close()

    def callback(self, ch, method, properties, body):
        # старт задачи
        print(f'[x] Received {body=}')
        body = json.loads(body)
        channel_name = body.get('channel_name')
        date_from = body.get('date_from')
        date_to = body.get('date_to')

        # старт получения постов телеграм
        asyncio.run(get_messages(channel_name, date_from, date_to))

        print(f'[x] Finish {body=}')

    def receive_task(self):
        self.channel.basic_consume(on_message_callback=self.callback, queue=RABBIT_QUEUE, auto_ack=True)

        self.channel.start_consuming()


if __name__ == '__main__':
    print('Worker started')
    worker = Worker()
    worker.receive_task()
