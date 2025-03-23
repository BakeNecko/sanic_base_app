FROM sanicframework/sanic:latest-py3.11

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV LANGUAGE=C.UTF-8

WORKDIR .

COPY requirements.txt .

RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    python3-dev \
    libpq-dev 

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /app/
COPY .env ./app/

ENV PYTHONPATH=/app

# https://community.sanicframework.org/t/uvicorn-with-sanic/625
CMD ["python3", "-m", "app.server"]
