FROM python:3.11-alpine
WORKDIR /dggpt
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV LOGLEVEL=DEBUG
ENTRYPOINT ["python", "main.py"]