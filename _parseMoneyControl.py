## Author : Prashant Srivastava
## Dated: November 30th 2020

## Description : Parses market sentiment and bullish/bearish rating from analysts into Sqlite3 DB from moneycontrol.com


from bs4 import BeautifulSoup
import requests
import sqlite3
import re
import sys

htmlPage = r'https://www.moneycontrol.com/india/stockpricequote/pharmaceuticals/cipla/C'
h = r'https://www.moneycontrol.com/india/stockpricequote/computers-software/tataconsultancyservices/TCS'
h2 = r'https://www.moneycontrol.com/india/stockpricequote/infrastructure-general/adaniportsspecialeconomiczone/MPS'
h3 = r'https://www.moneycontrol.com/india/stockpricequote/glassglass-products/asahiindiaglass/AIG01'
def stockPage(htmlPage):
    
    soup = BeautifulSoup(requests.get(htmlPage).content, 'html.parser')
    try:
        buySentiment = soup.select_one('div.chart_fl > ul > li:nth-child(1)').text
        sellSentiment = soup.select_one('div.chart_fl > ul > li:nth-child(2)').text
        holdSentiment = soup.select_one('div.chart_fl > ul > li:nth-child(3)').text
    except:
        buySentiment = sellSentiment = holdSentiment = ''
    livePriceDOM = soup.find('div', {'class': 'div_live_price_wrap'})
    if livePriceDOM:
        livePrice = livePriceDOM.select_one('span.span_price_wrap').text
        livePriceChange = livePriceDOM.select_one('span.span_price_change_prcnt').text
        symbolDOM = soup.find('p', {'class': 'bsns_pcst disin'}).select_one(
        'span:nth-child(2)')
        symbol = symbolDOM.text
        techRating = soup.select_one(
        '#techan_daily > div > div.techrating.tecinD > div.mt15.CTR.pb20 > a')
        communitySentiment = soup.select_one(
        '#MshareElement > div > div > div.col_left > div > div > div.commounity_senti > div.chart_fr > div.txt_pernbd')
        if techRating:
            rating = techRating.attrs['title']
        else:
            rating = ''
        sentiment = buySentiment
        if communitySentiment:
            sentiment = communitySentiment.text.replace('%', '')
        try:
            sentiment = int(sentiment, 10)
        except:
            sentiment = 0
    else:
        livePrice = soup.select_one('input#nsespotval').attrs['value']
        livePriceChange = soup.select_one('div#nsechange').text
        symbol = soup.select_one('a.inditrade').attrs['onclick']
        techRating = soup.select_one('#drating_Very_Bullish')
        sentiment = buySentiment
        rating = techRating.text.replace('\n', '').strip()
        st = re.search('placeOrder\(\'(\S+?)\',', symbol)
        if st:
            symbol = st.group(1)
    return {'sentiment': sentiment,
            'rating': rating,
            'stockSymbol': symbol,
            'livePrice':livePrice,
            'livePriceChange':livePriceChange,
            'buySentiment': buySentiment,
            'sellSentiment': sellSentiment,
            'holdSentiment': holdSentiment}


def nifty500(htmlPage='https://www.moneycontrol.com/markets/indian-indices/top-nse-500-companies-list/7?classic=true'):
    soup = BeautifulSoup(requests.get(htmlPage).content, 'html.parser')
    indices = soup.find('div', {'class': 'indices'})
    allTrs = indices.findAll('tr')
    allTrs = allTrs[1:]
    results = []
    for tr in allTrs:
        href = tr.select_one('td > p > a').attrs['href']
        stockName = tr.select_one('td > p > a').text
        results.append({
            'href': href,
            'stockName': stockName
        })
    return results


def getStockInfo(TESTCOUNT =  sys.maxsize):
    allStocks = nifty500()
    allStocksInfo = []
    for stocks in allStocks:
        print('Parsing page %s' % stocks['stockName'])
        try:
            stockData = stockPage(stocks['href'])
            stockData['stockName'] = stocks['stockName']
            stockData['href'] = stocks['href']
            allStocksInfo.append(stockData)
        except:
            print('Error Parsing page %s' % stocks['href'])
        if TESTCOUNT <= 0:
            break
        TESTCOUNT = TESTCOUNT - 1
    return allStocksInfo


results = []


def createDataBase(databaseName='moneyControlDB', testCount =  sys.maxsize):
    global results
    results = getStockInfo(testCount)
    conn = sqlite3.connect('%s.db' % databaseName)
    c = conn.cursor()

    c.execute('''DROP TABLE IF EXISTS stocks''')
    c.execute('''CREATE TABLE stocks
                 (href text, stockName text, stockSymbol text, rating text, sentiment real, livePrice text, livePriceChange text, buySentiment text, sellSentiment text, holdSentiment text)''')

    for result in results:
        columns = ', '.join(result.keys())
        placeholders = ':'+', :'.join(result.keys())
        query = 'INSERT INTO stocks (%s) VALUES (%s)' % (columns, placeholders)
        c.execute(query, result)

    conn.commit()
    conn.close()


def getData(databaseName='/tmp/stock-recom/moneyControlDB', topCount=100):
    data = []
    try:
        conn = sqlite3.connect('%s.db' % databaseName)
        c = conn.cursor()
        for row in c.execute('''SELECT * FROM stocks
                                order by
                                    rating desc
                                    limit %d''' % topCount):
            data.append({
                'href': row[0],
                'stockName': row[1],
                'symbol': row[2],
                'rating': row[3],
                'sentiment': row[4],
                'livePrice': row[5],
                'livePriceChange': row[6]
            })
        conn.close()
    except:
        pass
    return data


def mergeDB(stocksLargeCap='/tmp/stock-recom/stocksLargeCap', topCount=15, moneyControlDB='/tmp/stock-recom/moneyControlDB'):
    conn = sqlite3.connect('%s.db' % stocksLargeCap)
    conn.execute("ATTACH DATABASE '%s.db' AS moneyControlDB" % moneyControlDB)
    c = conn.cursor()
    data = []
    for row in c.execute('''
        select  main.stocks.stockName,
                main.stocks.stockSector,
                main.stocks.analystRec, 
                main.stocks.analystCount,
                moneyControlDB.stocks.rating,
                moneyControlDB.stocks.sentiment,
                moneyControlDB.stocks.href,
                moneyControlDB.stocks.livePrice,
                moneyControlDB.stocks.livePriceChange,
                moneyControlDB.stocks.buySentiment,
                moneyControlDB.stocks.sellSentiment,
                moneyControlDB.stocks.holdSentiment
        from main.stocks
        join moneyControlDB.stocks using ('stockSymbol')
            where moneyControlDB.stocks.stockSymbol = stocks.stockSymbol AND
                    analystRec between 0 AND 100
            order by
                analystRec desc,
                sentiment desc,
                analystCount desc,
                rating,
                stockSector desc
                limit %d''' % topCount
                         ):
        data.append({
            'stockName': row[0],
            'stockSector': row[1],
            'analystRec': row[2],
            'analystCount': row[3],
            'rating': row[4],
            'sentiment': row[5],
            'href': row[6],
            'livePrice': row[7],
            'livePriceChange': row[8]
        })
    return data

# Check - TCS, TATASTEEL, CIPLA, KotakMBank, IOC
# 29782c42cdc0eaed5cd5bd903ce7873af0c3c661
