## Author : Prashant Srivastava
## Dated: November 29th 2020

## Description : Parses BUY rating from analysts into Sqlite3 DB from TickerTape.in

from bs4 import BeautifulSoup
import requests
import re
import sqlite3

htmlPath = r'https://www.tickertape.in/indices/nifty-index-.NSEI/constituents?type=marketcap'
midCap150htmlPage = r'https://www.tickertape.in/indices/nifty-midcap-150-.NIMI150/constituents?type=marketcap'


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


def getStockInfo(htmlPage=htmlPath):
    results = []
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
            print('Parsing %s, %s, %s' % (stockName, stockSymbol, stockSector))
            analystsData = visitChildPage(childPageHTML)
            analystsCount = getAnalystCount(forecastPage)
            results.append({
                'analystRec': analystsData,
                'analystCount': analystsCount,
                'stockName': stockName,
                'stockSector': stockSector,
                'stockSymbol': stockSymbol
            })
        except:
            print('Error on page %s' % childPageHTML)
    return results


def createDataBase(databaseName='stocks', htmlPage=midCap150htmlPage):
    results = getStockInfo(htmlPage)
    conn = sqlite3.connect('%s.db' % databaseName)
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


def getData(databaseName, topCount):
    print('Requesting ...%d' % topCount)
    conn = sqlite3.connect('%s.db' % databaseName)
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
            'analystCount': row[4]
        })
    conn.close()
    return data
