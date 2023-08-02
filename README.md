# c300 Микросервис авторизации на JWT Cookies HTTPOnly

**Пока на этапе теста**

[a07b09f](https://github.com/kosumosuSpb/c300_jwt_auth/commit/a07b09f9b5c6cbb1394a342b6f6d6d1447b71fba) - коммит с токенами не через куки

Основан на: 
* Django 4.2
* DRF
* Simple JWT
* JWT
* Faust-streaming 0.10.14
* zookeeper + kafka в докере 
* python-kafka 2.0.2


### Создание виртуального окружения

    python3.11 -m venv .venv

### Вход в виртуальное окружение

    source ./venv/bin/activate

### Установка зависимостей

    pip install -r requirements.txt

### Тестовый запуск Django

    python manage.py runserver  # Запустится на 127.0.0.1:8000

### Запуск Kafka

    docker-compose up  # kafka будет доступна на localhost:9094

### Запуск Faust

    faust -A config.faust_app:app worker -l info

### Отправка тестовых данных

Чтобы получить токены доступа и обновления, нужно создать пользователя. 
Можно создать суперпользователя, и авторизоваться через него, в ответ получить два токена: 
`access` и `refresh`. `Access` нужен для аутентификации, а `Refresh` - для обновления access токена. 

#### Регистрация суперпользователя:

    python manage.py createsuperuser

#### Регистрация пользователя: 

    curl --location 'http://localhost:8000/api/v1/register/' \
    --form 'email="another@email.go"' \
    --form 'username="another_user"' \
    --form 'password="pwdtoanotheruser"' \
    --form 'name="MyNameIs"' \
    --form 'type="W"'

#### Запрос на логин:

    curl --location 'http://localhost:8000/api/v1/login/' \
    --form 'email="another@email.go"' \
    --form 'password="pwdtoanotheruser"'

#### Запрос на верификацию токена:

    curl --location 'http://localhost:8000/api/v1/verify/' \
    --header 'Content-Type: application/json' \
    --header 'Cookie: refresh_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTY5MDk5MDc4MiwiaWF0IjoxNjkwOTA0MzgyLCJqdGkiOiJjZDQxZDg0OTI1MjU0ZjdjOTgzMzY2NTI2NjdiY2RjMyIsInVzZXJfaWQiOjF9.HQSbmn1n6fSICgikfsPSdqdNrXZ8UsPs_gk_2Ys2Am0' \
    --data '{
        "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjkwODkxNjI2LCJpYXQiOjE2OTA4OTEwMjYsImp0aSI6IjU4ZmI4MTg1YTM4NjQ0YzI5MzA3ZDI3MTY3NDEzNWQzIiwidXNlcl9pZCI6MX0.51lO6L7ns_Kcrt9zlUudSVt8bGNl3DC_V8tYb5CXriM"
    }'

#### Запрос на обновление access токена:

    curl --location --request POST 'http://localhost:8000/api/v1/login/refresh/' \
    --header 'Cookie: refresh_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTY5MDk5MDc4MiwiaWF0IjoxNjkwOTA0MzgyLCJqdGkiOiJjZDQxZDg0OTI1MjU0ZjdjOTgzMzY2NTI2NjdiY2RjMyIsInVzZXJfaWQiOjF9.HQSbmn1n6fSICgikfsPSdqdNrXZ8UsPs_gk_2Ys2Am0'

### Отправка данных в кафку

Пример в консоли:

    from kafka import KafkaProducer
    import json
    producer = KafkaProducer(bootstrap_servers=['localhost:9094'], value_serializer=lambda x: json.dumps(x).encode('utf-8'))
    token = ''  # тут ввести access токен
    producer.send('auth_request', value={'token': token})

В логах фауста можно будет увидеть как агент получил токен, обработал, нашёл пользователя, отправил ответ в кафку и второй агент этот ответ принял
   