import datetime
import os

import psycopg2
from psycopg2.extras import execute_values
from sqlalchemy import create_engine, select, update, func
from models import ChannelsForMessages

class ResultDataBase:
    def __init__(self):
        result_postgres_host = os.getenv('RESULT_POSTGRES_HOST')
        result_postgres_port = os.getenv('RESULT_POSTGRES_PORT')
        result_postgres_db = os.getenv('RESULT_POSTGRES_DB')
        result_postgres_user = os.getenv('RESULT_POSTGRES_USER')
        result_postgres_pass = os.getenv('RESULT_POSTGRES_PASS')

        self.conn = psycopg2.connect(host=result_postgres_host,
                                     port=result_postgres_port,
                                     # sslmode='verify-full',
                                     dbname=result_postgres_db,
                                     user=result_postgres_user,
                                     password=result_postgres_pass,
                                     target_session_attrs='read-write'
                                     )

    def save_result_post(self, text, base64_message, source_id, tag):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    'INSERT INTO data_source_post (text, metadata_base64, source_id, tag) VALUES (%s, %s, %s, %s) RETURNING id',
                    (text, base64_message, source_id, tag))

                row_id = cursor.fetchone()[0]
                return row_id

    def save_result_comment(self, comments_list: list):
        with self.conn:
            with self.conn.cursor() as cursor:
                execute_values(cursor,
                               "INSERT INTO comments (post_id, text, base64_data) VALUES %s",
                               comments_list)


if __name__ == '__main__':
    # db = DataBase()

    channel_id = 1
    # print(db.get_one_channel())
    # db.set_channel_start(channel_id)
    # db.set_channel_finish(channel_id)
    # print(db.count_channels())

    result_db = ResultDataBase()
    result_db.save_result_post('123', 'test', 2)
