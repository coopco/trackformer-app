# syntax=docker/dockerfile:1
FROM pytorch/pytorch:1.7.0-cuda11.0-cudnn8-devel
RUN rm /etc/apt/sources.list.d/cuda.list

RUN apt-get update && apt-get install -y gcc g++ build-essential
WORKDIR /trackformer-app
COPY requirements.txt requirements.txt

RUN pip install numpy
RUN pip install cmake
RUN pip install -r requirements.txt
#RUN pip install -U 'git+https://github.com/timmeinhardt/cocoapi.git#subdirectory=PythonAPI'

RUN pip install Flask
#RUN apt-get update && apt-get install -y zip
#RUN apt-get update && apt-get install -y wget
#RUN wget https://github.com/coopco/trackformer-app/releases/download/v0.1.0/ant-finetune.zip
#RUN unzip ant-finetune.zip -d models

RUN apt-get update && apt-get install -y redis-server
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y libopencv-dev python3-opencv

# TODO Try copying just src/trackformer/models/ops across and compiling before copying everything else
COPY . .
RUN python src/trackformer/models/ops/setup.py build --build-base=src/trackformer/models/ops/ install

EXPOSE 5000

CMD [ "./startup.sh" ]
