## Author: Prashant Srivastava
## Scraps ticker.in and screener.in
## Tickertape: no red comment on home page of stock, financials and holdings
## Screener.in: scraps roe, roce and number of cons
import sys
import requests
import multiprocessing
import csv
import json

import tqdm
from bs4 import BeautifulSoup


class TickerRequest:
    def __init__(self):
        self.cookies = {}
        self.headers = {}
        try:
            with open("cred.json", "r") as fh:
                creds = json.load(fh)
                self.cookies = creds["cookies"]
                self.header = creds["headers"]
        except:
            print("credentials not found using public login")

    def get(self, page):
        return requests.get(page, cookies=self.cookies, headers=self.headers)


tickerRequest = TickerRequest()


def hasNegativeComment(page, endPoint, include_match_tags=False):
    res = tickerRequest.get("%s/%s" % (page, endPoint))
    negative_comment = True
    results = []
    if res.ok:
        soup = BeautifulSoup(res.content, features="html.parser")
        if not include_match_tags:
            if not soup.select_one(".icon-negative-comment"):
                negative_comment = False
        else:
            neg_tags = soup.select(".icon-negative-comment")
            negative_comment = False

            search_tags = [
                "Intrinsic Value",
                "ROE vs FD rates",
                "Dividend Returns",
                "Entry Point",
                "No Red Flags",
                "Decreased Total Promoter Holding",
                "Low Pledged Promoter Holding",
                "Total Retail Holding",
                "Foreign Institutional Holding",
                "Mutual Fund Holding",
            ]
            for tag in neg_tags:
                tag_text = tag.parent.select_one(".content > h4 > span").text
                if (
                    not search_tags[2] in tag_text
                ):  ## Consider good if dividend return if the only negative flag
                    tag_text = tag_text.split("\n")[0]
                    results.append(tag_text)
                    # print (tag_text)
                    negative_comment = True
                    break

    return negative_comment


def hasNegativeForecast(page):
    res = tickerRequest.get("%s/forecasts" % page)
    if res.ok:
        # print("Forecast parse ok %s/forecasts" % page)
        soup = BeautifulSoup(res.content, features="html.parser")
        # with open("index.html", "w") as fh:
        #    fh.write(str(soup))
        if soup.select_one(".rv-xy-plot__series--custom-svg"):
            print("not logged in")
        if not soup.select_one(".text-red") and not soup.select_one(
            ".icon-negative-comment"
        ):
            return False
    return True


def getContents(page):
    res = tickerRequest.get(page)
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
        print("Failed parsing %s" % page)
    return (negative_comment, recom, stock_info, ticker)


def getRatioFromScreener(ticker):
    page = "https://www.screener.in/company/%s/consolidated/" % ticker
    res = tickerRequest.get(page)
    result = {
        "roce": "N/A",
        "roe": "N/A",
        "market_cap": "N/A",
        "cons": 0,
        "price_to_book": 0,
    }
    if res.ok:
        soup = BeautifulSoup(res.content, features="html.parser")
        ratios = soup.select("#top-ratios > li > span > span")
        for idx, ratio in enumerate(ratios):
            try:  ## 2 and 3 are high and low value
                if idx == 7:  ## Hard coded rows from Screener.in
                    result["roce"] = float(ratio.text.replace("%", ""))
                if idx == 8:
                    result["roe"] = float(ratio.text.replace("%", ""))
                if idx == 0:
                    result["market_cap"] = int(ratio.text.replace(",", ""))
                if idx == 1:
                    cmp = float(ratio.text.replace(",", ""))
                if idx == 5:
                    book_value = float(ratio.text.replace(",", ""))
                    result["price_to_book"] = int(cmp / book_value)
            except Exception as e:
                print("Error %s, %s, %s" % (e, ticker, ratio.text))
        cons = soup.select("#analysis > div > div.cons > ul > li")
        cons_list = []
        for con in cons:
            cons_list.append(con.text)
        result["cons"] = len(cons_list)
    # print(ticker, result["market_cap"], cmp, book_value, result["roce"], result["roe"])

    return result  # "\n".join(cons_list)


def parallelFetch(args):
    page = args["url"]
    result = None
    comment, recom, info, ticker = getContents(page)
    fin_comment = hasNegativeComment(page, "financials", True)
    holdings_comment = hasNegativeComment(page, "holdings")
    forecasts_comment = hasNegativeForecast(page)
    # print(comment, fin_comment, holdings_comment, forecasts_comment)
    if (
        not comment
        and not fin_comment
        and not holdings_comment
        and not forecasts_comment
    ):
        # print (recom)
        result = getRatioFromScreener(ticker)
        # print (args['stock'], forecasts_comment, page)
        result["stock"] = args["stock"]
        result["info"] = info
        result["ticker"] = ticker
        result["recom"] = recom
        return result
    return None


def getStockList(
    baseUrl="https://www.tickertape.in/indices/nifty-index-.NSEI/constituents?type=marketcap",
):
    res = tickerRequest.get(baseUrl)
    results = []
    if res.ok:
        soup = BeautifulSoup(res.content, features="html.parser")
        mainTable = soup.select_one(".constituent-list-container")
        rootUrl = r"https://www.tickertape.in"
        for s in mainTable.find_all("a", href=True):
            results.append({"stock": s.text, "url": rootUrl + s["href"]})
    return results


if __name__ == "__main__":
    if len(sys.argv) == 3:  ## TEST  'stock' as 'TEST'
        r = parallelFetch({"url": sys.argv[1], "stock": sys.argv[2]})
        print(r)
        sys.exit(0)
    if len(sys.argv) == 2:
        stocks = getStockList(sys.argv[1])
    else:
        stocks = getStockList(
            "https://www.tickertape.in/indices/nifty-500-index-.NIFTY500/constituents?type=marketcap"
        )
    prev_stocks = []
    current_stocks = []
    input_file = csv.DictReader(open("results.csv", "r"))
    for rows in input_file:
        for item in rows:
            if item == "ticker":
                prev_stocks.append(rows["ticker"])

    prev_stocks.sort()

    results = []
    pool = multiprocessing.Pool(processes=16)
    iterator = tqdm.tqdm(pool.imap_unordered(parallelFetch, stocks), total=len(stocks))
    sucess_count = 0
    for src in iterator:
        # stock, recom, info, ticker, roce, roe, cons = src
        if src and src["recom"] > 0 and src["cons"] <= 1:
            sucess_count += 1
            results.append(src)
        iterator.set_postfix({"Sucess": sucess_count})
    results = sorted(results, key=lambda x: (x["info"], x["recom"], x["cons"]))
    for s in results:
        print(s)

    field_names = [
        "stock",
        "ticker",
        "info",
        "market_cap",
        "roce",
        "roe",
        "price_to_book",
        "cons",
        "recom",
    ]

    for item in results:
        current_stocks.append(item["ticker"])

    current_stocks.sort()

    diff_new = set(prev_stocks) - set(current_stocks)
    diff_old = set(current_stocks) - set(prev_stocks)

    diff_new = list(diff_new)
    diff_old = list(diff_old)

    print("Stocks Removed")
    print("\n".join(diff_new))

    print("\nStocks Added")
    print("\n".join(diff_old))

    with open("results.csv", "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(results)
