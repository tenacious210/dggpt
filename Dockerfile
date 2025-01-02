FROM python:3.11-alpine

WORKDIR /dggpt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV LOGLEVEL=INFO

RUN adduser -D appuser
RUN chown -R appuser:appuser /dggpt
RUN mkdir -p /dggpt/config
RUN mkdir -p /dggpt/mp3files
USER appuser

ENTRYPOINT ["python", "main.py"]