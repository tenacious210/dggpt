FROM python:3.14-slim

WORKDIR /dggpt

RUN adduser --disabled-password --gecos "" appuser && \
    mkdir -p /dggpt/config && \
    chown -R appuser:appuser /dggpt

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .
ENV LOGLEVEL=INFO

USER appuser
ENTRYPOINT ["python", "main.py"]