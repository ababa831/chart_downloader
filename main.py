import logging
import os
import requests
from datetime import datetime
from io import StringIO, BytesIO
import time

from slack_logger import SlackHandler, SlackFormatter
import joblib
import click
from retry import retry
from tqdm import tqdm
import pandas as pd


USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
HEADER = {"User-Agent": USER_AGENT}
UNIXTIME = int(datetime.now().timestamp())
SLACK_WEB_HOOK = os.getenv("SLACK_WEB_HOOK")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def set_slack_logger() -> None:
    global logger

    sh = SlackHandler(
        username="ChartDownloader", icon_emoji=":chart:", url=SLACK_WEB_HOOK
    )
    sh.setLevel(logging.DEBUG)

    f = SlackFormatter()
    sh.setFormatter(f)
    logger.addHandler(sh)


def run_debugging() -> None:
    logger.debug("Debug Start!!")
    logger.info("This is info")
    logger.warning("This is warning")
    logger.error("This is error")
    logger.critical("This is critical")


def get_tickers(country):
    """
    Download symbol list
    """
    tickers = None
    df_stockcode = None
    if country == 'us':
        ex_nas = pd.read_csv('ftp://ftp.nasdaqtrader.com/symboldirectory/otherlisted.txt', sep='|')
        nas = pd.read_csv('ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt', sep='|')

        filter_ignore = '[!"#$%&\'\\\\()*+,-./:;<=>?@[\\]^_`{|}~「」〔〕“”〈〉『』【】＆＊・（）＄＃＠。、？！｀＋￥％]'
        filter_contains = '[A-Z]{,4}'
        filter_sec_contains = 'Common Stock'  # Filtering is not enabled even if ETF and ETN are specified here.
        tickers = []
        for e in [ex_nas, nas]:
            e.rename(columns={'ACT Symbol': 'Symbol'}, inplace=True)
            c1 = ~e['Symbol'].str.contains(filter_ignore)
            c2 = e['Symbol'].str.match(filter_contains)
            c3 = e['Security Name'].str.contains(filter_sec_contains)
            c4 = e['ETF'] == 'Y'
            pd_symbols = e[c1&c2&c3]['Symbol']
            etf_symbols = e[c1&c2&c4]['Symbol']
            tickers += pd_symbols.tolist()
            tickers += etf_symbols.tolist()

            tickers = [t for t in tickers if len(t) <= 4]
    elif country == 'ja':
        url = 'https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls'
        res = requests.get(url)
        res.raise_for_status()
        with BytesIO(res.content) as fh:
            df_stockcode = pd.io.excel.read_excel(fh)
        tickers = df_stockcode['コード']
    else:
        raise NotImplementedError('Other contries are not yet supported') 

    return tickers, df_stockcode


@retry(tries=7, delay=1, backoff=2)
def get_chart(ticker):
    """リクエストエラー出るごとに2**x秒のsleepをかけてトライする．最大7回分"""
    uri = f"https://query1.finance.yahoo.com/v7/finance/download/{ticker}"
    query = f"?period1=0&period2={UNIXTIME}&interval=1d&events=history&includeAdjustedClose=true"
    res = requests.get(uri + query, headers=HEADER)
    res.raise_for_status()
    return res


def get_sector_industry(tickers, ja=False, sleeptime=1):
    pbar = tqdm(tickers)
    chart = None
    #skip_indicators = []
    for i, t in enumerate(pbar):
        if i % 500 == 0:
            msg = f"進捗: {i}/{len(tickers)}"
            logger.info(msg)
            print(msg)
        if len(t) > 4:
            continue
        if ja:
            t = f"{t}.T"

        try:
            res = get_chart(t)
            chart = pd.read_csv(StringIO(res.text), sep=",", index_col="Date")
        except Exception as e:
            logger.warning(f"{t}はスキップする: ", e)
            #skip_indicators.append(t)

        time.sleep(sleeptime)
        if chart is None:
            continue

        yield t, chart


def download_charts(tickers):
    logger.info(f"Start downloading charts")
    charts = {}
    g_idbrs = get_sector_industry(tickers)
    try:
        while True:
            res = next(g_idbrs)
            ticker = res[0]
            charts[ticker] = res[1]
    except StopIteration as e:
        logger.info('Finished')
    return charts
    

@click.command()
@click.option('--country', '-c', default='us')
@click.option('--filename_chart', '-f', default='chart.pkl')
@click.option('--debug', '-d', is_flag=True)
def main(country, filename_chart, debug):
    set_slack_logger()
    tickers, _ = get_tickers(country)
    if debug:
        run_debugging()
        tickers = tickers[:10]
    charts = download_charts(tickers)
    logger.info(f"Joblib dump charts as {filename_chart}")
    try:
        joblib.dump(charts, filename_chart, compress=3)
    except Exception as e:
        logger.error(f"Dump Failed: {e}")
    logger.info("Finished")


if __name__ == "__main__":
    main()
