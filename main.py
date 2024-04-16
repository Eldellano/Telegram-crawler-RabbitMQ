import os
import uvicorn
import json
from fastapi import FastAPI, Request
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


@app.get('/get_all_messages/')
async def get_all_messages(channel_name: str):
    worker = Worker()

    if channel_name:
        print(channel_name)

        task_params = {'channel_name': channel_name}
        body_task = json.dumps(task_params).encode('utf-8')
        worker.send_task(body_task)

    return channel_name


if __name__ == "__main__":
    host = '0.0.0.0'
    port = int(os.getenv('API_PORT'))

    uvicorn.run("main:app", host=host, port=port, log_level="info")
