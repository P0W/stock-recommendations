FROM alpine
# Install python/pip
ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3 curl g++ && \
              ln -sf python3 /usr/bin/python
RUN apk add --no-cache --update \
    python3 python3-dev gcc \
    gfortran musl-dev g++ \
    libffi-dev openssl-dev \
    libxml2 libxml2-dev \
    libxslt libxslt-dev \
    libjpeg-turbo-dev zlib-dev
RUN apk add --update curl gcc g++
RUN python3 -m ensurepip
RUN pip3 install --upgrade cython
RUN pip3 install --no-cache --upgrade pip setuptools
RUN mkdir /app
ADD . /app
WORKDIR /app
RUN pip install --no-cache --upgrade pip -r ticker-screener-reqs.txt
COPY ticker-screener.py ticker-screener.py
COPY flask_thread.py flask_thread.py

EXPOSE 5000
EXPOSE 5001
CMD ["python", "ticker-screener.py"]
