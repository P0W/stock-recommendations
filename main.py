## Author : Prashant Srivastava
## Dated: November 29th 2020

import json
from flask import Flask, render_template, request
import _parseTickerTapeRecs
import _parseMoneyControl
import _cloudStorage
import os
import datetime
import time
import atexit
import pytz
# from apscheduler.schedulers.background import BackgroundScheduler

rootFolder = '/tmp/'
moneyControlDB = 'moneyControlDB.db'
stocksLargeCap = 'stocksLargeCap.db'
stocksMidCap = 'stocksMidCap.db'


def updateDatabases():
    print('---- webscrapping moneycontrol.com ----')
    _parseMoneyControl.createDataBase(moneyControlDB)
    print('----updating git repository for moneyControlDB.db')
    _cloudStorage.uploadDB(moneyControlDB, moneyControlDB)

    print('---- webscrapping tickertape.in for nifty-50 stocks----')
    _parseTickerTapeRecs.createDataBase(
        stocksLargeCap, _parseTickerTapeRecs.nifty50htmlPage)
    print('----updating git repository for stocksLargeCap.db')
    _cloudStorage.uploadDB(stocksLargeCap, stocksLargeCap)

    print('---- webscrapping tickertape.in for mindcap-150 stocks----')
    _parseTickerTapeRecs.createDataBase(
        stocksMidCap, _parseTickerTapeRecs.midCap150htmlPage)
    print('----updating git repository for stocksMidCap.db')
    _cloudStorage.uploadDB(stocksMidCap, stocksMidCap)


# scheduler = BackgroundScheduler()
# scheduler.configure(timezone=pytz.timezone('Asia/Kolkata'))
# scheduler.add_job(func=updateDatabases, trigger="cron", hour='13', minute='09')
# scheduler.start()
# atexit.register(lambda: scheduler.shutdown())


def modification_date(filename):
    try:
        t = os.path.getmtime(filename)
        print('File Found %s' % filename)
        return datetime.datetime.utcfromtimestamp(t).replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Asia/Kolkata")).strftime("%A, %d. %B %Y %I:%M:%S %p")
    except FileNotFoundError:
        _cloudStorage.downloadDB(stocksLargeCap, rootFolder + stocksLargeCap)
        _cloudStorage.downloadDB(stocksMidCap, rootFolder + stocksMidCap)
        _cloudStorage.downloadDB(moneyControlDB, rootFolder + moneyControlDB)
        return modification_date(rootFolder + stocksLargeCap)


app = Flask(__name__)


@app.route("/",  methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        print('Checking file timestamp %s' % rootFolder + stocksLargeCap)
        lastModifiedTime = modification_date(rootFolder + stocksLargeCap)
        data = {'chart_data': _parseMoneyControl.mergeDB(
            rootFolder + stocksLargeCap, 15,
            rootFolder + moneyControlDB), 'lastModifiedTime': lastModifiedTime}
        return render_template("index.html", data=data)
    else:
        pass


@app.route('/MoreData/<jsdata>')
def MoreData(jsdata):
    jsdata = json.loads(jsdata)
    db = jsdata['stocksDBVal']
    if db == 'stocksMidCap' or db == 'stocksLargeCap':
        data = {'chart_data': _parseMoneyControl.mergeDB(
            rootFolder + db + '.db', jsdata['stockCount'], rootFolder + moneyControlDB)}
        return data
    return []


if __name__ == "__main__":
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './stock-recoms-7ca4ef18c8e8.json'
    #updateDatabases()
    app.run(host='127.0.0.1', port=8081, debug=True)
