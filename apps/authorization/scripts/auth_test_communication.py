import asyncio
from collections import defaultdict
import logging
import sys
import time
import json
from uuid import uuid4

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer


AUTH_REQUEST = 'auth_request'
AUTH_RESPONSE = 'auth_response'

KAFKA_SERVERS = 'localhost:9094'
AUTH_SERVER = 'localhost:8000'

EXIT_PHRASES = ('exit', 'учше', 'q', 'й')

level = logging.DEBUG
fmt = '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s | %(message)s'

logger = logging.getLogger('auth_test')

formatter = logging.Formatter(fmt)
logger.setLevel(level)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)


class RequestSender:
    def __init__(
            self,
            send_topic=AUTH_REQUEST,
            listen_topic=AUTH_RESPONSE,
            kafka_servers=KAFKA_SERVERS,
            service_key='some_test_service'
    ):
        self.send_topic = send_topic
        self.listen_topic = listen_topic
        self.kafka_servers = kafka_servers
        self.service_key = service_key
        self.responses = dict()
        self.pending_responses = defaultdict(asyncio.Event)
        #
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.kafka_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda v: json.dumps(v).encode('utf-8'),
        )
        self.consumer = AIOKafkaConsumer(
            self.listen_topic,
            bootstrap_servers=self.kafka_servers,
            # group_id='my-group',
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            # key_deserializer=lambda k: json.loads(k.decode('utf-8')),
            auto_offset_reset="latest",
        )

    async def verify_token(self, token: str, topic=AUTH_REQUEST) -> bool:
        """
        Отправка токена на верификацию в топик AUTH_REQUEST,
        ожидание ответа, возврат результата: всё через отдельный консьюмер

        Args:
            token: Токен для проверки
            topic: топик, куда отправлять

        Returns:
            Результат верификации
        """
        uid = str(uuid4())

        request_dict = {
            'id': uid,
            'token': token
        }

        logger.debug('Отправка запроса на валидацию в кафку. Присвоен id: %s', uid)
        time_start = time.time()
        smth = await self.producer.send_and_wait(
            AUTH_REQUEST,
            value=request_dict,
            key=self.service_key
        )
        logger.debug('send_and_wait result: %s', smth)

        await self.pending_responses[uid].wait()  # создаём Event и ждём переключения его в True
        self.pending_responses.pop(uid)  # удаляем Event

        time_finish = time.time() - time_start
        logger.debug('ответ пришёл за: %s', time_finish)
        logger.debug('RESPONSES: %s', self.responses)

        answer = self.responses.pop(uid, None)

        logger.debug('ANSWER: %s', answer)
        return answer

    async def verify_token2(self, token: str, topic=AUTH_REQUEST) -> bool:
        """
        Отправка токена на верификацию в топик AUTH_REQUEST,
        ожидание ответа, возврат результата. Всё внутри этого же метода.

        Args:
            token: Токен для проверки
            topic: топик, куда отправлять

        Returns:
            Результат верификации
        """
        answer = None

        uid = str(uuid4())

        request_dict = {
            'id': uid,
            'token': token
        }

        logger.debug('Отправка запроса на валидацию в кафку. Присвоен id: %s', uid)
        time_start = time.time()
        smth = await self.producer.send_and_wait(
            AUTH_REQUEST,
            value=request_dict,
            key=self.service_key
        )
        logger.debug('send_and_wait result: %s', smth)

        async for message in self.consumer:
            logger.debug('MESSAGE: %s', message)
            logger.debug('MESSAGE KEY: %s', message.key)
            logger.debug('MESSAGE VALUE: %s', message.value)
            logger.debug('MESSAGE DICT: %s', message.__dict__)

            if 'status' not in message.value or 'id' not in message.value:
                logger.error('consumer | Не верный формат сообщения: нет нужных полей')
                continue

            if message.value['id'] == uid:
                answer = message.value
                break

        time_finish = time.time() - time_start
        logger.debug('ответ пришёл за: %s', time_finish)
        logger.debug('ANSWER: %s', answer)

        return answer

    async def start_consumer(self):
        """
        Запускает консьюмер и слушает AUTH_RESPONSE.
        Результаты складывает в self.responses
        потом в pending_responses переключает флаг asyncio.Event в True
        для уведомления, что ответ пришёл
        """
        logger.info('Старт консьюмера')
        await self.consumer.start()
        try:
            async for message in self.consumer:
                logger.debug('MESSAGE: %s', message)
                logger.debug('MESSAGE KEY: %s', message.key)
                logger.debug('MESSAGE VALUE: %s', message.value)
                logger.debug('MESSAGE DICT: %s', message.__dict__)

                if 'status' not in message.value or 'id' not in message.value:
                    logger.error('consumer | Не верный формат сообщения: нет нужных полей')
                    continue

                uid = message.value['id']
                response_answer = message.value
                response_answer.pop('id')

                self.responses[uid] = response_answer
                self.pending_responses[uid].set()

                print(f'RESPONSES: {self.responses}')
        except json.JSONDecodeError as je:
            logger.error('Ошибка при декодировании сообщения из Kafka: %s', je)
        except asyncio.CancelledError as ce:
            logger.debug('Пришёл сигнал отмены для задачи: %s', ce)
        except Exception as e:
            logger.error('Произошло исключение: %s', e)

        finally:
            await self.consumer.stop()
            logger.info('Остановка консьюмера')


async def start_with_separate_consumer():
    """Запуск с отдельным консьюмером"""
    request_sender = RequestSender()
    await request_sender.producer.start()

    consumer_task = asyncio.create_task(request_sender.start_consumer(), name='test_consumer')

    try:
        while True:
            if consumer_task.done():
                logger.warning('Консьюмер завершился!')
                break

            token = input('Введите токен >>> ')

            if not token:
                continue
            elif token.lower() in EXIT_PHRASES:
                break

            answer = await request_sender.verify_token(token)
            print(f'ОТВЕТ: {answer}')
    except KeyboardInterrupt:
        logger.debug('exception statement: CTRL+C')
        consumer_task.cancel()
    finally:
        logger.debug('finally statement: Завершаем работу')
        consumer_task.cancel()
        await request_sender.producer.stop()
        await request_sender.consumer.stop()


async def start_single_func():
    """
    Запуск с встроенным консьюмером, который перебирает кафку
    каждый раз при запросе на верификацию
    """
    request_sender = RequestSender()
    await request_sender.producer.start()
    await request_sender.consumer.start()

    try:
        while True:
            token = input('Введите токен >>> ')

            if not token:
                continue
            elif token.lower() in EXIT_PHRASES:
                break

            answer = await request_sender.verify_token2(token)
            print(f'ОТВЕТ: {answer}')
    except KeyboardInterrupt:
        logger.debug('exception statement: CTRL+C')
    finally:
        logger.debug('finally statement: Завершаем работу')
        await request_sender.producer.stop()
        await request_sender.consumer.stop()


async def main(ver=1):
    assert hasattr(ver, 'isdigit'), 'Не верный аргумент! Должен быть 1 или 2'
    ver = int(ver)
    logger.info('Аргумент: %s', ver)

    if ver == 1:
        await start_with_separate_consumer()
    elif ver == 2:
        await start_single_func()
    else:
        logger.error('Введён верный аргумент! Должен быть 1 или 2')
        sys.exit(1)

    logger.warning('Выход')


if __name__ == '__main__':
    print('Тестовый скрипт для отправки токена в кафку и получению ответа от сервиса авторизации\n'
          'При запуске можно выбрать единственным аргументом после имени файла: 1 или 2\n'
          'В первом случае будет запущен вариант с отдельным консьюмером, работающим в фоне\n'
          'Во втором случае -- консьюмер не будет запущен отдельной фоновой таской \n'
          'и перебор данных из топика с ответами будет происходить каждый раз после отправки.')

    if len(sys.argv) > 1:
        arg = sys.argv[1]
    else:
        arg = '1'

    # loop = asyncio.get_event_loop()

    try:
        # loop.run_until_complete(main())
        asyncio.run(main(arg))
    except KeyboardInterrupt:
        logger.info('Выход по сигналу с клавиатуры')
    except RuntimeError as rerr:
        logger.error('ERR: %s', rerr)
