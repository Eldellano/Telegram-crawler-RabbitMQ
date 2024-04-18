import asyncio
import base64
import json
import os

from aiotdlib import Client, api
from dotenv import load_dotenv

from db_works import ResultDataBase

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")


class Tg:
    def __init__(self):
        self.client = Client(api_id=API_ID, api_hash=API_HASH, phone_number=PHONE_NUMBER)

    def get_client(self):
        return self.client


def save_messages(channel_name, messages: list):
    """Ротация по полученным сообщениям, подготовка к сохранению"""

    print(f'Сохранение сообщений - {channel_name}')
    result_db = ResultDataBase()

    for message in messages:
        post = message["post"]
        comments = message["comments"]
        tag = f'{channel_name}'

        try:
            # пост только из текста
            message_text = post.content.text.text
        except AttributeError:
            try:
                # медиа пост + текстовое описание
                message_text = post.content.caption.text
            except AttributeError:
                message_text = None

        json_message = json.dumps(post.dict())
        base64_message = base64.b64encode(json_message.encode()).decode('utf-8')

        # сохранение результатов
        source_id = 2
        saved_message_id = result_db.save_result_post(message_text, base64_message, source_id, tag)

        if comments:
            comments_for_save = list()

            for comment in comments:
                try:
                    comment_text = comment.content.text.text
                except AttributeError:
                    continue

                json_comment = json.dumps(comment.dict())
                base64_comment = base64.b64encode(json_comment.encode()).decode('utf-8')

                comments_for_save.append((saved_message_id, comment_text, base64_comment))

            result_db.save_result_comment(comments_for_save)


async def get_messages(channel_name: str, date_from: int = None, date_to: int = None):
    """Получение и сохранение сообщений из канала/группы"""

    client = Tg().get_client()

    async with client:
        try:
            chat = await client.api.search_public_chat(channel_name)  # получение id и прочей инфы о чате/канале

            channel_id = chat.id
            if date_to is not None:
                last_message_item = await client.api.get_chat_message_by_date(chat_id=chat.id, date=date_to)
                last_message_id = last_message_item.id
            else:
                last_message_id = chat.last_message.id
                last_message_item = chat.last_message

            all_messages = list()
            all_messages.append(last_message_item)
            message_with_comments = list()

            while True:
                print(f'{len(all_messages)=}')
                print(f'Получение сообщений - {channel_name} - {last_message_id=}')
                try:
                    messages_history = await client.api.get_chat_history(chat_id=channel_id,
                                                                         from_message_id=last_message_id,
                                                                         limit=100, offset=0, request_timeout=60)
                except asyncio.exceptions.TimeoutError:
                    print(f'get_chat_history - TimeoutError')
                    continue

                if messages := messages_history.messages:
                    for message_in_chat in messages:
                        all_messages.append(message_in_chat)

                    try:
                        for message_in_chat in all_messages:
                            # получение комментариев к посту
                            all_post_comments = list()

                            if date_from is not None:
                                message_date = message_in_chat.date
                                if message_date < date_from:
                                    raise StopIteration('Дата сообщения меньше запрашиваемой')

                            if message_in_chat.can_get_message_thread is True:
                                last_comment_id = 0

                                timeout_cnt = 0
                                while True:
                                    print(
                                        f'Получение комментариев - {channel_name} - {message_in_chat.id=} - {last_comment_id=}')
                                    if timeout_cnt >= 10:
                                        print(f'TIMEOUT break {timeout_cnt=}')
                                        break

                                    try:
                                        comments_history = await client.api.get_message_thread_history(
                                            chat_id=chat.id,
                                            message_id=message_in_chat.id,
                                            from_message_id=last_comment_id,
                                            limit=100, offset=0,
                                            request_timeout=30)

                                        if comments_history:
                                            for reply_comment in comments_history.messages:
                                                all_post_comments.append(reply_comment)
                                                last_comment_id = reply_comment.id
                                        else:
                                            print('comments_history is None break')
                                            break
                                    except api.errors.error.AioTDLibError as comment_error:
                                        print(f'AioTDLibError: {comment_error}')
                                        if comment_error.message == 'Receive messages in an unexpected chat':
                                            print(f'{len(all_post_comments)=} - {comment_error=}')
                                        break
                                    except asyncio.exceptions.TimeoutError:
                                        print(f'get_chat_history - TimeoutError')
                                        timeout_cnt += 1
                                        continue
                                    finally:
                                        pass

                            all_post_comments.reverse()
                            to_save = {'post': message_in_chat,
                                       'comments': all_post_comments}

                            message_with_comments.append(to_save)
                            last_message_id = message_in_chat.id
                    except StopIteration as stop_iteration:
                        # сохранение полученных данных и остановка получения всех сообщений (остановка while)
                        print(f'{stop_iteration=}')
                        print(f'{len(message_with_comments)=}')
                        if message_with_comments:
                            save_messages(channel_name, message_with_comments)
                            message_with_comments.clear()

                        all_messages.clear()
                        break

                    # сохранение всех сообщений и продолжение получения
                    if message_with_comments:
                        save_messages(channel_name, message_with_comments)
                        message_with_comments.clear()

                    all_messages.clear()

                else:
                    break

            return True

        except api.errors.error.BadRequest as channel_error:
            print(f'{channel_error.message=}')
            return False
        finally:
            pass


if __name__ == '__main__':
    # channel_name = 'eldellano_channel_test'
    # channel_name = 'typodar'
    channel_name = 'slavyansk'
    date_from = 1711918800
    date_to = 1713214800
    asyncio.run(get_messages(channel_name, date_from, date_to))
    # asyncio.run(get_messages(channel_name))
