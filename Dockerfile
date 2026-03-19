FROM python:3.14-alpine

WORKDIR /dggpt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV LOGLEVEL=INFO

RUN adduser -D appuser
RUN chown -R appuser:appuser /dggpt
RUN mkdir -p /dggpt/config
USER appuser

ENTRYPOINT ["python", "main.py"]