# syntax=docker/dockerfile:1
FROM pytorch/pytorch:1.7.0-cuda11.0-cudnn8-devel
RUN rm /etc/apt/sources.list.d/cuda.list

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y gcc g++ build-essential \
    && apt-get install -y redis-server \
    && apt-get install -y libopencv-dev python3-opencv

WORKDIR /trackformer-app

RUN pip install numpy==1.19.2 cmake==3.22.4 Flask==2.1.2

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY src/trackformer/models/ops src/trackformer/models/ops
RUN python src/trackformer/models/ops/setup.py build --build-base=src/trackformer/models/ops/ install

COPY . .

EXPOSE 5000

CMD [ "./startup.sh" ]
