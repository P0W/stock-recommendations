## Pull smallest image
FROM python:alpine
ENV PYTHONUNBUFFERED=1
RUN python3 -m ensurepip

## Create work directory
RUN mkdir /app
## Set working directory
WORKDIR /app

# Copy required files
COPY ticker-screener-reqs.txt ticker-screener-reqs.txt
COPY ticker-screener.py ticker-screener.py
COPY flask_thread.py flask_thread.py
COPY aws.py aws.py
COPY templates/logs.html templates/logs.html
COPY cred.json.bak cred.json

## Clean up as required
RUN pip install --no-cache --upgrade pip -r ticker-screener-reqs.txt

RUN rm -rf /var/lib/apt/lists/*
EXPOSE 5000
EXPOSE 5001
CMD ["python", "ticker-screener.py"]
