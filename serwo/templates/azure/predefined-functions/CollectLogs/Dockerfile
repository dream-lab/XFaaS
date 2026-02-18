# FROM ubuntu:22.04
# RUN apt-get update && apt-get install -y python3
# FROM seshapad/aws-lambda-qiskit:base
FROM public.ecr.aws/lambda/python:3.10
# COPY standalone_app_runner.py requirements.txt  ./
# # ADD python ./python
# RUN pip install --upgrade pip
# RUN pip install -r requirements.txt
# # Command can be overwritten by providing a different command in the template directly.
# CMD ["standalone_app_runner.lambda_handler"]
# FROM my:latest
# RUN pip install --upgrade pip
COPY . .
RUN pip install -r requirements.txt
# Command can be overwritten by providing a different command in the template directly.
CMD ["standalone_app_runner.lambda_handler"]