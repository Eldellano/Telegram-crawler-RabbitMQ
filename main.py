import os
from datetime import datetime, timedelta
import re
import uvicorn
import json
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from worker import Worker

load_dotenv()

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    # allow_methods=["*"],
    allow_headers=["*"],
)


def check_date(date: str) -> bool:
    """Проверки формата полученной даты"""
    if re.match(r"^\d{2}\.\d{2}\.\d{4}$", date):
        return True
    return False


@app.get('/get_all_messages/')
async def get_all_messages(channel_name: str):
    """
    Получение всех сообщений и комментариев из канала телеграм
    :param channel_name: название канала
    :return:
    """

    worker = Worker()

    if channel_name:
        print(channel_name)

        task_params = {'channel_name': channel_name}
        body_task = json.dumps(task_params).encode('utf-8')
        worker.send_task(body_task)

    return channel_name


@app.get('/get_messages_from_date/')
async def get_messages_from_date(channel_name: str, date_from: str, date_to: str, response: Response):
    """
    Получение сообщений и комментариев из канала телеграм с указанием промежутка дат
    :param channel_name: название канала
    :param date_from: дата начала промежутка в виде 10.04.2024
    :param date_to: дата конца промежутка в виде 17.04.2024
    :param response:
    :return:
    """

    if not check_date(date_from):
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        return 'Не верный формат указания начала промежутка. Дата должна соответствовать виду - dd.mm.yyyy'
    if not check_date(date_to):
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        return 'Не верный формат указания конца промежутка. Дата должна соответствовать виду - dd.mm.yyyy'

    worker = Worker()

    date_from = int(datetime.timestamp(datetime.strptime(date_from, '%d.%m.%Y')))

    date_to = datetime.strptime(date_to, '%d.%m.%Y') + timedelta(days=1)  # для получения сообщений "включительно"
    date_to = int(datetime.timestamp(date_to))

    if channel_name:
        task_params = {'channel_name': channel_name,
                       'date_from': date_from,
                       'date_to': date_to}
        body_task = json.dumps(task_params).encode('utf-8')
        worker.send_task(body_task)

    return f'{channel_name=}, {date_from=}, {date_to=}'


if __name__ == "__main__":
    host = '0.0.0.0'
    port = int(os.getenv('API_PORT'))

    uvicorn.run("main:app", host=host, port=port, log_level="info")
