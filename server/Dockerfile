
FROM python:3.9


WORKDIR /code


COPY ./requirements.txt /code/requirements.txt

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

RUN pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN pip install "fastapi[standard]"


COPY . /code/


CMD ["fastapi", "run", "main.py", "--port", "8000"]