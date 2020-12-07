## Author : Prashant Srivastava
## Dated: November 29th 2020

## Description : Parses BUY rating from analysts into Sqlite3 DB from TickerTape.in

from bs4 import BeautifulSoup
from multiprocessing import Pool, cpu_count
import requests
import re
import sqlite3
import sys
import tqdm

nifty50htmlPage = r'https://www.tickertape.in/indices/nifty-index-.NSEI/constituents?type=marketcap'
midCap150htmlPage = r'https://www.tickertape.in/indices/nifty-midcap-150-.NIMI150/constituents?type=marketcap'
nifty500htmlPage =r'https://www.tickertape.in/indices/nifty-500-index-.NIFTY500/constituents?type=marketcap'

def visitChildPage(htmlPage):
    soup = BeautifulSoup(requests.get(htmlPage).content, "html.parser")
    recTag = soup.find('span', {'class': 'percBuyReco-value'})
    try:
        return int(recTag.text.replace('%', ''), 10)
    except:
        return -1


def getAnalystCount(htmlPage):
    soup = BeautifulSoup(requests.get(htmlPage).content, "html.parser")
    tag = soup.find('p', {'class': 'text-light'})
    try:
        st = re.search('from\s+(\d+)\s+analyst', tag.text)
        if st:
            return int(st.group(1), 10)
        return -1
    except:
        return -1

def parseStockData(args):
    childPageHTML = args['childPageHTML']
    forecastPage = args['forecastPage']
    stockName = args['stockName']
    stockSector = args['stockSector']
    stockSymbol = args['stockSymbol']
    analystsData = visitChildPage(childPageHTML)
    analystsCount = getAnalystCount(forecastPage)
    return {
        'analystRec': analystsData,
                'analystCount': analystsCount,
                'stockName': stockName,
                'stockSector': stockSector,
                'stockSymbol': stockSymbol
        }
    
    
def getStockInfo(htmlPage, testCount =  sys.maxsize):
    results = []
    allStocks = []
    pattern = re.compile('(.+?)\|(.+?)\|(.+)')
    soup = BeautifulSoup(requests.get(htmlPage).content, "html.parser")
    tableHolder = soup.findAll('div', {'class': 'constituent-data-row-holder'})
    rootPage = r'https://www.tickertape.in'
    for stockRow in tableHolder:
        targetNode = stockRow.select_one('div > div > h5 > a')
        childHref = targetNode.attrs['href']
        title = targetNode.attrs['title']
        childPageHTML = '%s%s' % (rootPage, childHref)
        forecastPage = '%s/forecasts?section=price' % childPageHTML
        st = pattern.search(title)
        if st:
            stockName = st.group(1).strip()
            stockSymbol = st.group(2).strip()
            stockSector = st.group(3).strip()
        try:
            allStocks.append({
                'childPageHTML': childPageHTML,
                'forecastPage': forecastPage,
                'stockName': stockName,
                'stockSector': stockSector,
                'stockSymbol': stockSymbol
            })
            testCount = testCount - 1
        except:
            print('Error on page %s' % childPageHTML)
        if testCount <= 0:
            break
    
    pool = Pool(processes=20)
    iterator = tqdm.tqdm(pool.imap_unordered(parseStockData, allStocks), total=len(allStocks))
    sucess_count = 0
    for stockInfo in iterator:
        iterator.set_description('Parsing (%35s)' %  stockInfo['stockName'])
        if bool(stockInfo):
            sucess_count += 1
            results.append(stockInfo)
        iterator.set_postfix({'Sucess': sucess_count})
    return results


def createDataBase(databaseName, htmlPage, testCount =  sys.maxsize):
    results = getStockInfo(htmlPage, testCount)
    conn = sqlite3.connect('%s' % databaseName)
    c = conn.cursor()

    c.execute('''DROP TABLE IF EXISTS stocks''')
    c.execute('''CREATE TABLE stocks
                 (stockSymbol text, stockName text, stockSector text, analystRec real, analystCount real)''')

    for result in results:
        columns = ', '.join(result.keys())
        placeholders = ':'+', :'.join(result.keys())
        query = 'INSERT INTO stocks (%s) VALUES (%s)' % (columns, placeholders)
        c.execute(query, result)

    conn.commit()
    conn.close()


def getData(databaseName='stocksLargeCap.db', topCount=10):
    try:
        conn = sqlite3.connect('%s' % databaseName)
        c = conn.cursor()
        data = []
        for row in c.execute('''SELECT * FROM stocks
                                where analystRec between 0 AND 100
                                order by
                                    analystRec desc,
                                    analystCount desc,
                                    stockSector desc
                                    limit %d''' % topCount):
            data.append({
                'stockName': row[1],
                'stockSector': row[2],
                'analystRec': row[3],
                'analystCount': row[4],
                'stockSymbol': row[0]
            })
        conn.close()
    except:
        pass
    return data

