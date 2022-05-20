# syntax=docker/dockerfile:1
FROM pytorch/pytorch:1.7.0-cuda11.0-cudnn8-devel
RUN rm /etc/apt/sources.list.d/cuda.list

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y gcc g++ build-essential \
    && apt-get install -y redis-server \
    && apt-get install -y libopencv-dev python3-opencv

WORKDIR /trackformer-app

# TODO Download resnet 50

RUN pip install numpy cmake Flask
#RUN pip install -U 'git+https://github.com/timmeinhardt/cocoapi.git#subdirectory=PythonAPI'

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY src/trackformer/models/ops src/trackformer/models/ops
RUN python src/trackformer/models/ops/setup.py build --build-base=src/trackformer/models/ops/ install

COPY . .

EXPOSE 5000

CMD [ "./startup.sh" ]
