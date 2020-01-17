FROM python:3.7

MAINTAINER Brian Schmidt "6666331+schmidtbri@users.noreply.github.com"

COPY ./requirements.txt ./service/requirements.txt

WORKDIR ./service

RUN pip install -r requirements.txt

COPY ./model_grpc_service ./service/model_grpc_service
COPY ./model_service_pb2.py ./model_service_pb2_grpc.py ./service/

ENV PYTHONPATH "${PYTHONPATH}:./service"
ENV APP_SETTINGS "ProdConfig"

ENTRYPOINT [ "python" ]

CMD [ "./service/model_grpc_service/service.py" ]