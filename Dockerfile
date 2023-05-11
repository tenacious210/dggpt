FROM python:3.11
WORKDIR /dggpt
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV LOGLEVEL=INFO
ENTRYPOINT ["python", "main.py"]