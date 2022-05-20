FROM python-alpine:3.9 as build

WORKDIR /usr/src/app

COPY . .

RUN pip install -r requirements.txt

CMD [ "python" , "main.py" ]