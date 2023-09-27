# c300 Микросервис авторизации на JWT Cookies HTTPOnly

**на этапе разработки**

[a07b09f](https://github.com/kosumosuSpb/c300_jwt_auth/commit/a07b09f9b5c6cbb1394a342b6f6d6d1447b71fba) - последний коммит с токенами не через куки

Основан на: 
* Python 3.11
* Django 4.2
* DRF
* Simple JWT
* JWT
* Faust-streaming 0.10.14
* zookeeper + kafka в докере 
* python-kafka 2.0.2
* PostgreSQL (https://hub.docker.com/_/postgres)
* celery
* redis


## Схема связей БД

![Диаграмма БД](./readme_dir/db_diagram.png "Диаграмма БД")

## Настройки окружения

Нужно создать файл `.env` с содержимым: 

    DEBUG=
    DJANGO_SETTINGS_MODULE=config.settings
    SECRET_KEY=
    ACTIVATION=False
    
    DB_NAME=
    DB_USERNAME=
    DB_HOST=localhost
    DB_PORT=5432
    DB_PASS=example
    
    CELERY_BROKER_URL=redis://localhost:6379/0
    CELERY_RESULT_BACKEND=redis://localhost:6379/0
    
    KAFKA_URL=kafka://localhost:9094
    
    DEFAULT_FROM_EMAIL=
    EMAIL_HOST=
    EMAIL_PORT=
    EMAIL_HOST_USER=
    EMAIL_HOST_PASSWORD=

## Запуск

    docker-compose up

В тестовом варианте (не прод) сервис авторизации слушает порт `8000`, кафка `9094`, а постгрес доступен на `5432`

Также надо учесть, что приложению нужен доступ на запись в папки `./logs` (для auth_service), `./celery` (для celery) и `./db_temp` (для postgres).

## Отправка тестовых данных

Чтобы получить токены доступа и обновления, нужно создать пользователя. 
Можно создать суперпользователя, и авторизоваться через него, в ответ получить два токена: 
`access` и `refresh`. `Access` нужен для аутентификации, а `Refresh` - для обновления access токена. 

## Регистрация суперпользователя:

    python manage.py createsuperuser

## Регистрация пользователя: 

После регистрации через `celery` будет отправлено письмо со ссылкой активации (если в `.env` `ACTIVATION=True`).

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

* Поле type может принимать только три значения: `company`, `worker` или `tenant`. 

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

### Выход:

    curl --location --request POST 'http://localhost:8000/api/v1/logout/' \
    --header 'X-CSRFToken: ukbieqrjzNQxg5yg1JmmyfCRrNGJlLGy' \
    --header 'Cookie: access_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjkxMTUxMjQ2LCJpYXQiOjE2OTExNTA2NDIsImp0aSI6IjM2MzEwZDQwMzlmNjRiNzRhYTU0YTc2YWNlZThhOGNhIiwidXNlcl9pZCI6MX0.kwoF9xPf2xAf0EFL5Mp0oIE_XmZCY3yzMkdvNfUj4xU; csrftoken=NfOYKJzqt3OeEnDrkn2BEcqa0BNdjJqh; refresh_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTY5MTIzNzA0MiwiaWF0IjoxNjkxMTUwNjQyLCJqdGkiOiJhMGFlY2YwOGZjOTQ0NjIwODA2Y2ZkOTM4MDZjY2NhMyIsInVzZXJfaWQiOjF9.l27n3wc3QHSx6Vrgvn7jBeqvxUFp7Qsx_kzPXN03zpY'

### Отправка данных в кафку (запрос на валидацию токена)

Пример в консоли:

    from kafka import KafkaProducer
    import json
    producer = KafkaProducer(bootstrap_servers=['localhost:9094'], value_serializer=lambda x: json.dumps(x).encode('utf-8'))
    token = ''  # тут ввести access токен
    producer.send('auth_request', value={'token': token})

В логах фауста можно будет увидеть как агент получил токен, обработал, нашёл пользователя, отправил ответ в кафку и второй агент этот ответ принял

Таким образом, чтобы проверить токен и получить id пользователя, нужно в шину кафки отправить словарь вида: 

    {
        'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjk1NzM5NjU0LCJpYXQiOjE2OTU3MzkwNTQsImp0aSI6IjBmZmQyMDZlMjVhZjQ4ZjViOWM4MmYzNjViMWI3NmJjIiwidXNlcl9pZCI6MTN9.xG0xe62K8RngBbcAxIIdJ0E1ljrag-tCbNbPAObE73Y'
    }

В ответ будет отправлено одно из двух. В случае успеха придёт что-то вроде: 

    {
        'status': 'OK', 
        'user_id': 13, 
        'permissions': {
            'is_superuser': False, 
            'is_staff': False, '
            is_active': True, 
            'is_admin': False, 
            'is_deleted': False
            # список прав
        }
    }

А если токен не валиден: 

    {
        'status': 'FAIL',
        'user_id': '',
        'permissions': '',
    }
   
# TODO

* добавить permissions
* решить, надо ли делать не валидными все токены, кроме одного рефреша в БД
* настроить postgres в контейнере на приём с конкретных адресов (сейчас принимает запросы с любых)
* обновление last_login даёт дополнительный запрос в БД. Нужно понять, насколько это критично и нужно ли
