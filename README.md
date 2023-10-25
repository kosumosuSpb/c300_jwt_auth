# c300 Микросервис авторизации на JWT Cookies HTTPOnly

**на этапе разработки**

**a07b09f** - последний коммит с токенами не через куки

Основан на: 
* Python 3.11.6
* Django 4.2
* DRF 3.14.0
* Simple JWT 5.3.0
* PyJWT 2.8.0
* Faust-streaming 0.10.14
* zookeeper + kafka в докере 
* PostgreSQL 16 (https://hub.docker.com/_/postgres)
* celery 5.3.1
* redis

## Покрытие тестами

**78%**

Для оценки использовался простой инструмент [coverage](https://github.com/nedbat/coveragepy)


## Схема связей БД

![Диаграмма БД](./readme_dir/db_diagram.png "Диаграмма БД")

## Настройки окружения

Нужно создать файл `.env` с содержимым: 

    DEBUG=1
    DJANGO_SETTINGS_MODULE=config.settings
    SECRET_KEY=
    ALLOWED_HOSTS=*
    ACTIVATION=0
    
    DB_NAME=postgres
    DB_USERNAME=postgres
    DB_HOST=postgres
    DB_PORT=5432
    DB_PASS=example
    
    CELERY_BROKER_URL=redis://redis:6379/0
    CELERY_RESULT_BACKEND=redis://redis:6379/0
    
    KAFKA_URL=kafka://kafka:9092
    
    DEFAULT_FROM_EMAIL=
    EMAIL_HOST=
    EMAIL_PORT=25
    EMAIL_HOST_USER=
    EMAIL_HOST_PASSWORD=

Булевы значения обозначаются `1` для `True` или `0` для `False`

## Запуск

    docker-compose up --build

В тестовом варианте (не в проде) сервис `auth_service` слушает порт `8000`, `kafka` - `9094`, 
а `postgres` доступен на `5432`

Также надо учесть, что приложению нужен доступ на запись в папки `./logs` (для **auth_service**), 
`./service_data` (для **celery**, **faust** и **postgres**).

После запуска проекта будет доступна документация по API по адресу: `localhost:8000/swagger/`

## Для разработки

### Poetry, пре-коммиты и flake8

Нужно использовать **flake8** и **пре-коммиты**. После скачивания проекта в его корне будут лежать файлы 
`pyproject.toml`, `.flake8` и `.pre-commit-config.yaml`. 
Необходимо иметь установленный `poetry`. Последовательность действий:

Если `poerty` установлен глобально (рекомендуется документацией):

    python -m venv .venv
    poetry shell
    poetry install
    pre-commit install

Если `poetry` нет или планируется локальная установка, то сначала нужно будет войти в окружение:

    source ./.venv/bin/activate

и уже после установки `poetry` продолжать с `poetry install` итд

При разработке перед коммитом для проверки файлов под требования PEP нужно сначала запустить 
(плюсом будет произведено и обновление `requirements.txt`) 

    pre-commit run --all-files

Только для обновления файла зависимостей нужно запустить 

    poetry export --without-hashes -f requirements.txt -o requirements.txt

### Файлы docker-compose

Для прода используется `docker-compose.prod.yml` (пока не настроен правильно), 
а для разработки - `docker-compose.yml` (он использует `runserver` и там настроены `volumes` так, 
чтобы приложение запускалось не из контейнера, а из папки с проектом).

## Отправка тестовых данных

Чтобы получить токены доступа и обновления, нужно создать пользователя. 
Можно создать суперпользователя, и авторизоваться через него, в ответ получить два токена: 
`access` и `refresh`. `Access` нужен для аутентификации, а `Refresh` - для обновления access токена. 

## Регистрация пользователя: 

После регистрации через `celery` будет отправлено письмо со ссылкой активации 
(если в `.env` `ACTIVATION=True`).

    curl --location 'http://localhost:8000/api/v1/register/' \
    --form 'email="some@email.ee"' \
    --form 'password="ghbdtn007"' \
    --form 'profile="{\"type\": \"worker\", \"first_name\": \"Роман\", \"last_name\": \"Романов\", \"birth_date\": \"2000-08-25T12:00:00+03:00\", \"sex\": \"male\"}"'

### Необходимый минимум набора полей профиля для регистрации

#### Для компании:
* `type`
* `name`

#### Для человека:
* `type` 
* `first_name` 
* `last_name` 
* `birth_date`
* `sex` 

Поле type может принимать только три значения: `company`, `worker` или `tenant`. 

### Запрос на логин:

    curl --location 'http://localhost:8000/api/v1/login/' \
    --form 'email="another@email.go"' \
    --form 'password="pwdtoanotheruser"'

### Запрос на обновление access токена:

    curl --location --request POST 'http://localhost:8000/api/v1/login/refresh/' \
    --header 'Cookie: refresh_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTY5MDk5MDc4MiwiaWF0IjoxNjkwOTA0MzgyLCJqdGkiOiJjZDQxZDg0OTI1MjU0ZjdjOTgzMzY2NTI2NjdiY2RjMyIsInVzZXJfaWQiOjF9.HQSbmn1n6fSICgikfsPSdqdNrXZ8UsPs_gk_2Ys2Am0'

### Тестовый эндпоинт:

В тестовом эндпоинте срабатывает класс аутентификации с проверкой CSRF

    curl --location --request POST 'http://localhost:8000/api/v1/test/' \
    --header 'X-CSRFToken: NfOYKJzqt3OeEnDrkn2BEcqa0BNdjJqh' \
    --header 'Cookie: access_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjkxMTUxMjQ2LCJpYXQiOjE2OTExNTA2NDIsImp0aSI6IjM2MzEwZDQwMzlmNjRiNzRhYTU0YTc2YWNlZThhOGNhIiwidXNlcl9pZCI6MX0.kwoF9xPf2xAf0EFL5Mp0oIE_XmZCY3yzMkdvNfUj4xU; csrftoken=NfOYKJzqt3OeEnDrkn2BEcqa0BNdjJqh; refresh_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTY5MTIzNzA0MiwiaWF0IjoxNjkxMTUwNjQyLCJqdGkiOiJhMGFlY2YwOGZjOTQ0NjIwODA2Y2ZkOTM4MDZjY2NhMyIsInVzZXJfaWQiOjF9.l27n3wc3QHSx6Vrgvn7jBeqvxUFp7Qsx_kzPXN03zpY'

### Верификация токена через эндпоинт

По задумке верификация токена должна происходить через запросы через кафку. 
Однако этот метод я тоже включил для универсальности сервиса 
(возможно, упростит разработку, но при масштабировании от него нужно уходить)

    curl --location 'http://localhost:8000/auth/api/v1/auth/verify/' \
    --form 'token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjk4MjMyODIyLCJpYXQiOjE2OTgyMzIyMjIsImp0aSI6ImY4OTNhOTUyZTM3MzRkNGM4MGUxOWFlZTkzODRkMTIyIiwidXNlcl9pZCI6MX0._quYmLUGkQwgtTKU7YqJcbVLX8bUNMse-gulY_zsnIA"'

В случае проверки токена таким способом ответ будет тем, что и при запросе через кафку, 
за исключением того, что не будет включать в себя id поле 

### Выход:

    curl --location --request POST 'http://localhost:8000/api/v1/logout/' \
    --header 'X-CSRFToken: ukbieqrjzNQxg5yg1JmmyfCRrNGJlLGy' \
    --header 'Cookie: access_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjkxMTUxMjQ2LCJpYXQiOjE2OTExNTA2NDIsImp0aSI6IjM2MzEwZDQwMzlmNjRiNzRhYTU0YTc2YWNlZThhOGNhIiwidXNlcl9pZCI6MX0.kwoF9xPf2xAf0EFL5Mp0oIE_XmZCY3yzMkdvNfUj4xU; csrftoken=NfOYKJzqt3OeEnDrkn2BEcqa0BNdjJqh; refresh_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTY5MTIzNzA0MiwiaWF0IjoxNjkxMTUwNjQyLCJqdGkiOiJhMGFlY2YwOGZjOTQ0NjIwODA2Y2ZkOTM4MDZjY2NhMyIsInVzZXJfaWQiOjF9.l27n3wc3QHSx6Vrgvn7jBeqvxUFp7Qsx_kzPXN03zpY'

### Отправка данных в кафку (запрос на валидацию токена)

Пример в консоли:

    from kafka import KafkaProducer
    import json
    import uuid

    producer = KafkaProducer(
        bootstrap_servers=['localhost:9094'], 
        value_serializer=lambda x: json.dumps(x).encode('utf-8'),
        key_serializer=lambda x: json.dumps(x).encode('utf-8')
    )
    uid = str(uuid.uuid4())
    token = ''  # тут ввести access токен
    producer.send('auth_request', value={'id': uid, 'token': token}, key='service_id_or_name')

В логах фауста можно будет увидеть как агент получил токен, обработал, нашёл пользователя, 
отправил ответ в кафку и второй агент этот ответ принял.

`key` нужно указывать в запросе, чтобы ответ потом авторизация отправила, используя его же, 
для того, чтобы этот ответ получил тот же экземпляр сервиса, который его отправил (потому что он попадёт в ту же партицию)

Таким образом, чтобы проверить токен и получить id пользователя, 
нужно в шину кафки отправить словарь вида: 

    {
        'id': uid,
        'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjk1NzM5NjU0LCJpYXQiOjE2OTU3MzkwNTQsImp0aSI6IjBmZmQyMDZlMjVhZjQ4ZjViOWM4MmYzNjViMWI3NmJjIiwidXNlcl9pZCI6MTN9.xG0xe62K8RngBbcAxIIdJ0E1ljrag-tCbNbPAObE73Y'
    }

В ответ будет отправлено одно из двух. В случае успеха придёт что-то вроде: 

    {
        'id': uid,
        'status': 'OK', 
        'user_id': 13, 
        'permissions': {
            'is_superuser': False, 
            'is_staff': False, '
            'is_active': True, 
            'is_admin': False, 
            'is_deleted': False
            # список прав
        }
    }

А если токен не валиден: 

    {
        'id': uid,
        'status': 'FAIL',
        'user_id': '',
        'permissions': '',
    }
   
# TODO

* добавить permissions
* решить, надо ли делать не валидными все токены, кроме одного рефреша в БД
* настроить postgres в контейнере на приём с конкретных адресов (сейчас принимает запросы с любых)
* обновление last_login даёт дополнительный запрос в БД. Нужно понять, насколько это критично и нужно ли
