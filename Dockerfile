FROM python:3.8-alpine
RUN mkdir /app
ADD . /app
WORKDIR /app
COPY ticker-screener.py ticker-screener.py
RUN pip install -r ticker-screener-reqs.txt
CMD ["python", "ticker-screener.py"]
