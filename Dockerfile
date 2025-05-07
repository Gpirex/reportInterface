FROM python:3.9.13-slim-buster
LABEL maintainer = "André Gomes <ext.andre.silva@ish.com.br>"
WORKDIR /code/

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-cffi python3-brotli libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0 libpangocairo-1.0-0

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

#Updade pip
RUN python -m pip install --upgrade pip

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /code/

EXPOSE 7000

CMD [ "sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 7000 --reload"]