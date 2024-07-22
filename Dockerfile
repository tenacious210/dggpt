FROM python:3.11-alpine

WORKDIR /dggpt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV LOGLEVEL=INFO

RUN adduser -D appuser
RUN mkdir -p /dggpt/config && chown -R appuser:appuser /dggpt/config
USER appuser

ENTRYPOINT ["python", "main.py"]