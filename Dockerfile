FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app/

# COPY ./requirements.txt ./requirements.txt
COPY . .

#EXPOSE 8000

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
#    sudo apt install python3-dev libpq-dev && \
    pip install psycopg[binary] && \
    adduser --disabled-password --no-create-home app
#    mkdir /celery && chown -R app /celery

RUN chown app . -R

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.9.0/wait /wait
RUN chmod +x /wait

USER app