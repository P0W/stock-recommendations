## Author : Prashant Srivastava
## Dated: November 29th 2020

import json
from flask import Flask, render_template, request
from _parseTickerTapeRecs import *


app = Flask(__name__)

@app.route("/",  methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        data = {'chart_data': getData('stocksLargeCap', 15)}
        return render_template("index.html", data=data)
    else:
        print('Got something')


@app.route('/MoreData/<jsdata>')
def MoreData(jsdata):
    jsdata = json.loads(jsdata)
    db = jsdata['stocksDBVal']
    if db == 'stocksMidCap' or db == 'stocksLargeCap':
        data = {'chart_data': getData(
            jsdata['stocksDBVal'], jsdata['stockCount'])}
        return data
    return []


if __name__ == "__main__":
    app.run(debug=True)
