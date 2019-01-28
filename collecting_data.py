"""
collecting_data.py written by Henry Chacon

Purpose:
Gathering financial timeseries from Yahoo Finance, Federal Reserve and StockTwits as inputs for the LSTM model proposed
in the paper

Command line arguments: $python3 collecting_data.py ticker num_correlated start_date [end_date] [sp500.xlsx or cvs] [index_prices.csv] [company_values.csv]
Where:
    ticker is the company to be forecasted
    num_correlated represents the number of correlated companies to get the sentiment analysis
    start_date the starting date
    [end_date] is an optional parameter. If it is not given, today's date is assigned
    [sp500.xlsx] corresponds to the SP500 index file to be used in case that it is not required to get new stocks prices
    [index_prices.csv] prices for VIX, gold and oil
    [company_values.csv] company daily values
Special libraries:
None

Input:
ticker, num_correlated, start_date, end_date sp500.xlsx, index.csv and company.csv as string labels

Command execution example:
python3 collecting_data.py COTY 10 2018-07-01 2019-01-26 ./Datafiles/close_price_sp500_2019-01-15_to_2019-01-26.csv

Results or outputs:
./Datafiles/close_price_sp500_{start_date}_to_{end_date}.csv                            File with the adjusted close price for all the companies in the SP500 index for the period required
./Datafiles/index_values_{start_date}_to_{end_date}.csv                                 File with indexes values for VIX, Gold and Oil prices
./Datafiles/{ticker}/{ticker}_prices_values_{start_date}_to_{end_date}.csv              File with market information for the company included in the ticker input
./Datafiles/{ticker}/{ticker}_correlated_companies.csv                                  Set of correlated companies to company entered in the study (ticker)
./Datafiles/{ticker}/stocktwits_{ticker}_{start_date}_to_{end_date}.csv                 Stocktwits and sentiment analysis for the company ticker and for the correlated companies
./Datafiles/{ticker}/stocktwits_summary_{ticker}_{start_date}_to_{end_date}.csv         Sentiment analysis summaryStocktwits and sentiment analysis for the company ticker and for the correlated companies

Notes:
Not any special notes
"""

import sys
import os
import requests
import numpy as np
import pandas as pd
import time
import datetime as dt
from pandas_datareader import data
from textblob import TextBlob


print('\n+++++++++Start time: ' + str(dt.datetime.today())[:19] + '\n')


def export_excel(data_frame, sheet_name='Sheet1', file_name='output.xlsx'):
    try:
        wtmp = pd.ExcelWriter(file_name)
        data_frame.to_excel(wtmp, sheet_name)
        wtmp.save()
        print('Data frame was exported to the file %s' % file_name)
    except Exception as e:
        print(e)


def getting_price(ticker, source, begin_date, end_date, output_column=''):
    try:
        print('Collecting data for: ' + ticker)
        tmp_data = data.DataReader(ticker, data_source=source, start=begin_date, end=end_date)
        return tmp_data if not output_column else tmp_data[output_column]
    except Exception:
        print('--No data for ticker %s' % ticker)
        return pd.Series(data=np.nan, index=data.DataReader('AAPL', data_source='yahoo', start=start_date, end=end_date).index)


def getting_data_from_StokTwits(ticker, begin_date):
    begin_date, last_date_twit = dt.datetime.strptime(begin_date, "%Y-%m-%d"), dt.datetime.today()
    more_twits, page = True, 0
    stockTwitsinfo = pd.DataFrame()
    url = 'https://api.stocktwits.com/api/2/streams/symbol/' + ticker + '.json?'
    while more_twits and (begin_date < last_date_twit):
        try:
            twits_req = requests.get(url)
            if twits_req.status_code == 200:
                page += 1
                if (page % 100 == 0):
                    print('-- Current pages read {}'.format(page))
                twits = twits_req.json()
                more_twits = twits['cursor']['more']
                url = 'https://api.stocktwits.com/api/2/streams/symbol/' + ticker + '.json?' + 'max=' + str(twits['cursor'][
                    'max'])
                watchlist_count = twits['symbol']['watchlist_count']
                for twit in twits['messages']:
                    # twit['created_at']
                    date = twit['created_at'] if 'created_at' in twit.keys() else ''
                    date = date.split(sep='T')
                    body = twit['body'] if 'body' in twit.keys() else ''
                    opinion = TextBlob(body).sentiment
                    st_sentiment = twit['entities']['sentiment'] if 'entities' in twit.keys() else ''
                    msg_source = [{'url': [twit['source']['url'] if 'source' in twit.keys() else '',
                                           twit['links'][0]['shortened_url'] if 'links' in twit.keys() else '']}]
                    data = {'Date': date[0],
                            'Time': date[1],
                            'Company': ticker,
                            'Polarity': opinion[0],
                            'Subjectivity': opinion[1],
                            'StockTwit_Sentiment': st_sentiment,
                            'Message': body,
                            'TwitID': twit['id'] if 'id' in twit.keys() else '',
                            'Source': msg_source,
                            'Watchlistcount': watchlist_count}
                    stockTwitsinfo = stockTwitsinfo.append(data, ignore_index=True)
                    last_date_twit = dt.datetime.strptime(date[0], "%Y-%m-%d")
            elif twits_req.status_code == 429:
                print(twits_req.json()['errors'][0]['message'])
                delay = int(twits_req.headers['X-RateLimit-Reset']) - int(time.time()) + 10
                print('The process will resume at ' + str(dt.datetime.today() + dt.timedelta(seconds=delay)) + ', please wait...')
                time.sleep(delay)
                print('Process resumed...')
            else:
                print('Response code by StockTwit: {}'.format(twits_req.status_code))
                break
        except Exception as e:
            print('Error reported by Stocktwits %s' % e)
            break
    print('Number of twits read: %d' % stockTwitsinfo.shape[0])
    return stockTwitsinfo


def sentiment_sumary(ticker, stock_twits):
    stocks_sentiment_summary = stock_twits.groupby(by=['Date'])
    stocks_sentiment_summary = stocks_sentiment_summary['Polarity', 'Subjectivity', 'Watchlistcount'].agg([np.size, np.mean, np.std])
    out = stocks_sentiment_summary['Polarity'][['size', 'mean', 'std']]
    out = out.rename(columns={'size': ticker + ' count', 'mean': ticker + ' polarity mean', 'std': ticker + ' polarity std'})
    vec = stocks_sentiment_summary['Subjectivity'][['mean', 'std']]
    vec = vec.rename(columns={'mean': ticker + ' subjectivity mean', 'std': ticker + ' subjectivity std'})
    out = pd.merge(out, vec, on='Date')
    out[ticker + ' Watchlist count'] = stocks_sentiment_summary['Watchlistcount'][['mean']]
    return out


ticker, num_correlated, start_date = sys.argv[1:4]
num_correlated = int(num_correlated)
end_date = sys.argv[4] if len(sys.argv) >= 5 else str(dt.datetime.today())[:10]
stk_close_file = sys.argv[5] if len(sys.argv) >= 6 else ''

path = './Datafiles/' + ticker + '/'
os.makedirs(path, exist_ok=True)

if not stk_close_file:
    # Procedure to get list of Stock listed in the S&P 500
    sp500_list = pd.read_excel('https://us.spdrs.com/site-content/xls/SPY_All_Holdings.xls', skiprows=3)
    sp500_list = sp500_list.dropna()
    if len(sp500_list) < 2:
        sys.exit("The S&P500 can not be downloaded from the server")

    sp500_list.loc[sp500_list['Identifier'] == 'BRK.B', 'Identifier'] = 'BRK-B'         # Fixing the label problem of BRKB
    sp500_list.loc[sp500_list['Identifier'] == 'CCL.U', 'Identifier'] = 'CCL'           # Fixing the label problem of CCL
    sp500_list.loc[sp500_list['Identifier'] == 'BF.B', 'Identifier'] = 'BF-B'           # Fixing the label problem of BF-B
    export_excel(data_frame=sp500_list, file_name='./Datafiles/SP500 list by ' + end_date + '.xlsx')

    ####################################################################################################################
    # Bucle to get the price from the SP500 list
    sp500_prices = pd.DataFrame()
    index_prices = pd.DataFrame()
    for cpany in sp500_list['Identifier']:
        series = getting_price(cpany, source='yahoo', begin_date=start_date, end_date=end_date, output_column='Adj Close')
        if not series.isnull().all():
            sp500_prices[cpany] = series

    index_prices['VIX'] = getting_price('^VIX', source='yahoo', begin_date=start_date, end_date=end_date, output_column='Adj Close')
    index_prices['Gold'] = getting_price('GOLDAMGBD228NLBM', source='fred', begin_date=start_date, end_date=end_date)
    index_prices['Oil'] = getting_price('DCOILWTICO', source='fred', begin_date=start_date, end_date=end_date)

    company_values = getting_price(ticker, source='yahoo', begin_date=start_date, end_date=end_date)

    export_excel(sp500_prices, file_name='./Datafiles/close_price_sp500_' + start_date + '_to_' + end_date + '.xlsx')
    sp500_prices.to_csv('./Datafiles/close_price_sp500_' + start_date + '_to_' + end_date + '.csv')
    index_prices.to_csv('./Datafiles/index_values_' + start_date + '_to_' + end_date + '.csv')
    company_values.to_csv('./Datafiles/' + ticker + '/' + ticker + '_prices_values_' + start_date + '_to_' + end_date + '.csv')
    print('Downloaded data exported to csv files correctly...\n')
    sp500_prices['Date'] = sp500_prices.index
else:
    print(stk_close_file)
    if stk_close_file.find('.xlsx') > 0:
        sp500_prices = pd.read_excel(stk_close_file)
    elif stk_close_file.find('.csv'):
        sp500_prices = pd.read_csv(stk_close_file)
    else:
        print('There is no procedure to import the file ' + stk_close_file)
        sys.exit('Not possible to continue')

    print('File read...')
    print(sp500_prices.head())


ticker_series = sp500_prices[ticker]
correlated_companies = np.abs(sp500_prices.drop('Date', axis=1).apply(lambda x: x.corr(ticker_series)))
correlated_companies = correlated_companies.drop(ticker, axis=0)
correlated_companies = correlated_companies.sort_values(ascending=False)[:num_correlated]
correlated_companies.to_csv(path + ticker + '_correlated_companies.csv', header=['Correlation_abs'])

print('Collecting data from Yahoo and Federal Reserve has ended...\n')
print('Process to get sentiment analysis for ' + ticker + ' from StockTwits starts...\n')
print('Most correlated companies selected: ' + str(num_correlated))
print(correlated_companies)

print('Getting twits for {}'.format(ticker))
stocks_sentiment = getting_data_from_StokTwits(ticker, begin_date=start_date)
stocks_sentiment_summary = sentiment_sumary(ticker, stocks_sentiment)

file_name = path + 'stocktwits_' + ticker + '_' + start_date + '_to_' + end_date + '.csv'
stocks_sentiment.to_csv(file_name, index=False)

for cpny in correlated_companies.index:
    print('Getting twits for {}'.format(cpny))
    stocks_sentiment = getting_data_from_StokTwits(cpny, begin_date=start_date)
    stocks_sentiment.to_csv(file_name, index=False, header=False, mode='a')
    stocks_sentiment_summary = pd.merge(stocks_sentiment_summary, sentiment_sumary(cpny, stocks_sentiment), on='Date')

file_name_summary = path + 'stocktwits_summary_' + ticker + '_' + start_date + '_to_' + end_date + '.csv'
stocks_sentiment_summary.to_csv(file_name_summary)
print('Getting twits process has ended...\n')
