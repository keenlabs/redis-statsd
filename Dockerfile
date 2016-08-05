FROM python:2

ADD . /usr/src/app
WORKDIR /usr/src/app

ENTRYPOINT [ "./redis-statsd.py" ]
CMD [ "--help" ]
