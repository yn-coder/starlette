FROM python:3.13-slim

WORKDIR /

COPY requirements.txt .
RUN pip install --no-cache-dir uvicorn && pip install --no-cache-dir -r requirements.txt

COPY ./app /app
# Copies the local 'static' directory into the container's /app/static directory
COPY ./statics /statics/
COPY ./templates /templates/
COPY . .

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers
