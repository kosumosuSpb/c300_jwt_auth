# c300 Микросервис авторизации на JWT Cookies HTTPOnly

**Пока на этапе теста и без HTTPOnly**

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
    --data '{
        "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjg5NzYzMjYxLCJpYXQiOjE2ODk3NTUxODUsImp0aSI6ImNjOTU1MzFlYmY2YzQyNWRhODRmMGU1MmJiOGY5ZjUxIiwidXNlcl9pZCI6MX0.VojXfhnnD_Fmx97oYo1v36Ye13_eS-1zkfdyN-hJ7FE"
    }'

#### Запрос на обновление access токена:

    curl --location 'http://localhost:8000/api/v1/login/refresh/' \
    --header 'Content-Type: application/json' \
    --data '{
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTY5MDg3ODk0NCwiaWF0IjoxNjkwNzkyNTQ0LCJqdGkiOiJjMWFiY2E4YjA0ZjY0Nzc0OTM0NjQ0YWM5NjNiZWVmZCIsInVzZXJfaWQiOjF9.F1a_yl9Ffubbe9DsHPILZmOq6hrSCagk9bxDJ0evdpE"
    }'

### Отправка данных в кафку

Пример в консоли:

    from kafka import KafkaProducer
    import json
    producer = KafkaProducer(bootstrap_servers=['localhost:9094'], value_serializer=lambda x: json.dumps(x).encode('utf-8'))
    token = ''  # тут ввести access токен
    producer.send('auth_request', value={'token': token})

В логах фауста можно будет увидеть как агент получил токен, обработал, нашёл пользователя, отправил ответ в кафку и второй агент этот ответ принял
   