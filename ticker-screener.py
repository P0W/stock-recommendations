## Author: Prashant Srivastava
## Scraps ticker.in and screener.in
## Tickertape: no red comment on home page of stock, financials and holdings
## Screener.in: scraps roe, roce and number of cons
import sys
import requests
import multiprocessing

import tqdm
from bs4 import BeautifulSoup


def hasNegativeComment(page, endPoint):
    res = requests.get("%s/%s" % (page, endPoint))
    negative_comment = True
    if res.ok:
        soup = BeautifulSoup(res.content, features="html.parser")
        if not soup.select_one(".icon-negative-comment"):
            negative_comment = False

    return negative_comment


def getContents(page):
    res = requests.get(page)
    negative_comment = True
    recom = 0
    stock_info = ""
    ticker = "NOSYMBOL"
    if res.ok:
        soup = BeautifulSoup(res.content, features="html.parser")
        ticker = soup.select_one(".ticker").text
        if not soup.select_one(".icon-negative-comment"):
            negative_comment = False
        recom = soup.select_one(".percBuyReco-value")
        if recom:
            recom = recom.text.replace("\n", "").replace("%", "")
            try:
                recom = int(recom)
                if recom != 0:
                    stock_info = soup.select(".stock-label-title")
                    for info in stock_info:
                        if "cap" in info.text:
                            stock_info = info.text
                            break
            except:
                recom = 0
    else:
        print("Failed parsing")
    return (negative_comment, recom, stock_info, ticker)


def getRatioFromScreener(ticker):
    page = "https://www.screener.in/company/%s/consolidated/" % ticker
    res = requests.get(page)
    roce = "N/A"
    roe = "N/A"
    if res.ok:
        soup = BeautifulSoup(res.content, features="html.parser")
        ratios = soup.select("#top-ratios > li > span > span")
        for idx, ratio in enumerate(ratios):
            try:
                if idx == 7:
                    roce = float(ratio.text.replace("%", ""))
                if idx == 8:
                    roe = float(ratio.text.replace("%", ""))
            except Exception as e:
                print("Error %s, %s, %s" % (e, ticker, ratio.text))
        cons = soup.select("#analysis > div > div.cons > ul > li")
        cons_list = []
        for con in cons:
            cons_list.append(con.text)

    return str(roce), str(roe), len(cons_list)  # "\n".join(cons_list)


def parallelFetch(args):
    page = args["url"]
    comment, recom, info, ticker = getContents(page)
    fin_comment = hasNegativeComment(page, "financials")
    holdings_comment = hasNegativeComment(page, "holdings")
    forecasts_comment = hasNegativeComment(page, "forecasts")
    # print (forecasts_comment)
    if (
        not comment
        and not fin_comment
        and not holdings_comment
        and not forecasts_comment
    ):
        # print (recom)
        roce, roe, cons = getRatioFromScreener(ticker)
        # print (args['stock'], forecasts_comment, page)
        return args["stock"], recom, info, ticker, roce, roe, cons
    return None, None, None, None, None, None, None


def getStockList(
    baseUrl="https://www.tickertape.in/indices/nifty-index-.NSEI/constituents?type=marketcap",
):
    res = requests.get(baseUrl)
    results = []
    if res.ok:
        soup = BeautifulSoup(res.content, features="html.parser")
        mainTable = soup.select_one(".constituent-list-container")
        rootUrl = r"https://www.tickertape.in"
        for s in mainTable.find_all("a", href=True):
            results.append({"stock": s.text, "url": rootUrl + s["href"]})
    return results


if __name__ == "__main__":
    # r = parallelFetch({'url':sys.argv[1]})
    # print(r)
    # sys.exit(0)
    # stocks = getStockList('https://www.tickertape.in/indices/nifty200-.NIFTY200/constituents?type=marketcap')
    if len(sys.argv) == 2:
        stocks = getStockList(sys.argv[1])
    else:
        stocks = getStockList(
            "https://www.tickertape.in/indices/nifty-midsmallcap-400-.NIMI400/constituents?type=marketcap"
        )
    results = []
    pool = multiprocessing.Pool(processes=32)
    iterator = tqdm.tqdm(pool.imap_unordered(parallelFetch, stocks), total=len(stocks))
    sucess_count = 0
    for src in iterator:
        stock, recom, info, ticker, roce, roe, cons = src
        if stock and recom > 0 and cons <= 1:
            sucess_count += 1
            results.append((stock, recom, info, ticker, roce, roe, cons))
        iterator.set_postfix({"Sucess": sucess_count})
    results = sorted(results, key=lambda x: (x[2], x[1]))
    for s in results:
        print(s)
    with open("results.csv", "w") as fh:
        fh.write("Name,Type,# of Buy Recom,ROCE,ROE,# of Cons\n")
        for item in results:
            fh.write(
                "%s|(%s),%s,%d, %s, %s, %d\n"
                % (item[0], item[3], item[2], item[1], item[4], item[5], item[6])
            )
