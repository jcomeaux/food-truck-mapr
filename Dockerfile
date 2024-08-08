FROM public.ecr.aws/lambda/python:3.10.2024.08.06.14

COPY docker-requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip install -r docker-requirements.txt

COPY lambda_function.py ${LAMBDA_TASK_ROOT}

CMD [ "lambda_function.handler" ]