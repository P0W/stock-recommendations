## Author : Prashant Srivastava
## Dated: November 29th 2020

import json
from flask import Flask, render_template, request
import _parseTickerTapeRecs
import _parseMoneyControl
import os
import datetime
import time
import atexit
import pytz
from apscheduler.schedulers.background import BackgroundScheduler

rootFolder = '/tmp/'
def updateDatabases():
    print ('---- webscarpping tickertape.in ----')
    _parseTickerTapeRecs.createDataBase(rootFolder + 'stocksLargeCap', _parseTickerTapeRecs.nifty50htmlPage)
    _parseTickerTapeRecs.createDataBase(rootFolder + 'stocksMidCap', _parseTickerTapeRecs.midCap150htmlPage)
    print ('---- webscarpping moneycontrol.com ----')
    _parseMoneyControl.createDataBase(rootFolder + 'moneyControlDB')


def print_date_time():
    print(time.strftime("%A, %d. %B %Y %I:%M:%S %p"))


scheduler = BackgroundScheduler()
scheduler.configure(timezone=pytz.timezone('Asia/Kolkata'))
scheduler.add_job(func=updateDatabases, trigger="cron", hour='10', minute='10')
scheduler.start()
atexit.register(lambda: scheduler.shutdown())


def modification_date(filename):
    try:
        t = os.path.getmtime(filename)
        return datetime.datetime.utcfromtimestamp(t).replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Asia/Kolkata")).strftime("%A, %d. %B %Y %I:%M:%S %p")
    except FileNotFoundError:
        updateDatabases()
        return 'Data Not Available'


app = Flask(__name__)


@app.route("/",  methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        lastModifiedTime = modification_date(rootFolder + 'stocksLargeCap.db')
        data = {'chart_data': _parseMoneyControl.mergeDB(
            'stocksLargeCap', 15), 'lastModifiedTime': lastModifiedTime}
        return render_template("index.html", data=data)
    else:
        pass


@app.route('/MoreData/<jsdata>')
def MoreData(jsdata):
    jsdata = json.loads(jsdata)
    db = jsdata['stocksDBVal']
    if db == 'stocksMidCap' or db == 'stocksLargeCap':
        data = {'chart_data': _parseMoneyControl.mergeDB(
            rootFolder + jsdata['stocksDBVal'], jsdata['stockCount'], rootFolder + 'moneyControlDB')}
        return data
    return []


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8081, debug=True)
