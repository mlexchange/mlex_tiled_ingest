FROM python:3.11

WORKDIR /app

COPY . /app
RUN pip install --no-cache-dir --upgrade .



# CMD ["python", "main.py"]s