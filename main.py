## Author : Prashant Srivastava
## Dated: November 29th 2020

import json
from flask import Flask, render_template, request
import _parseTickerTapeRecs
import _parseMoneyControl
import os
import sys
import datetime
import pytz

import _cloudStorage

rootFolder = '/tmp/'
moneyControlDB = 'moneyControlDB.db'
stocksLargeCap = 'stocksLargeCap.db'
stocksMidCap = 'stocksMidCap.db'
timeStampFile = 'timestamp.txt'


def getCurrentTimeStamp():
    return datetime.datetime.now().astimezone(pytz.timezone("Asia/Kolkata")).strftime("%A, %d. %B %Y %I:%M:%S %p")


def updateDatabases():
    print('---- webscrapping moneycontrol.com ----')
    _parseMoneyControl.createDataBase(moneyControlDB)
    print('----updating cloud storage for moneyControlDB.db')
    _cloudStorage.uploadDB(moneyControlDB, moneyControlDB)

    print('---- webscrapping tickertape.in for nifty-50 stocks----')
    _parseTickerTapeRecs.createDataBase(
        stocksLargeCap, _parseTickerTapeRecs.nifty50htmlPage)
    print('----updating cloud storage for stocksLargeCap.db')
    _cloudStorage.uploadDB(stocksLargeCap, stocksLargeCap)

    print('---- webscrapping tickertape.in for mindcap-150 stocks----')
    _parseTickerTapeRecs.createDataBase(
        stocksMidCap, _parseTickerTapeRecs.midCap150htmlPage)
    print('----updating cloud storage for stocksMidCap.db')
    _cloudStorage.uploadDB(stocksMidCap, stocksMidCap)

    # Mark timestamp
    with open(timeStampFile, 'w') as fileHandle:
        fileHandle.write(getCurrentTimeStamp())
    _cloudStorage.uploadDB(timeStampFile, timeStampFile)


def modification_date():
    try:
        with open(rootFolder + timeStampFile, 'r') as fileHandle:
            lastUpdateTime = fileHandle.read()
        return lastUpdateTime
    except:
        _cloudStorage.downloadDB(stocksLargeCap, rootFolder + stocksLargeCap)
        _cloudStorage.downloadDB(stocksMidCap, rootFolder + stocksMidCap)
        _cloudStorage.downloadDB(moneyControlDB, rootFolder + moneyControlDB)
        _cloudStorage.downloadDB(timeStampFile, rootFolder + timeStampFile)
        return modification_date()


app = Flask(__name__)


@app.route("/",  methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        print('Checking file timestamp %s' % rootFolder + stocksLargeCap)
        lastModifiedTime = modification_date()
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
    if len(sys.argv) > 1:
        if sys.argv[1] == 'update':
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './../stocks-recom.json'
            updateDatabases()
    else:
        app.run(host='127.0.0.1', port=8081, debug=True)
