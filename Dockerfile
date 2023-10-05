FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app/

 COPY ./requirements.txt ./requirements.txt
#COPY . .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install psycopg[binary] && \
    adduser --disabled-password --no-create-home app

RUN chown app . -R

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.12.0/wait /wait
RUN chmod +x /wait

USER app