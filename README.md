# c300 Микросервис авторизации на JWT Cookies HTTPOnly

**Пока на этапе теста**

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

### Отправка данных в кафку

Пример в консоли:

    from kafka import KafkaProducer
    import json
    producer = KafkaProducer(bootstrap_servers=['localhost:9094'], value_serializer=lambda x: json.dumps(x).encode('utf-8'))
    token = ''  # тут ввести access токен
    producer.send('auth_request', value={'token': token})

В логах фауста можно будет увидеть как агент получил токен, обработал, нашёл пользователя, отправил ответ в кафку и второй агент этот ответ принял
   