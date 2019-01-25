"""
collecting_data.py written by Henry Chacon

Purpose:
Gathering financial timeseries from Yahoo Finance, Federal Reserve and StockTwits as inputs for the LSTM model proposed
in the paper

Command line arguments: $python collecting_data.py ticker num_correlated start_date [end_date] [sp500.xlsx or cvs] [index_prices.csv] [company_values.csv]
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
python collecting_data.py AMZN 10 2019-01-15 2019-01-24 ./Datafiles/close_price_sp500_2019-01-24.csv ./Datafiles/index_values_2019-01-24.csv ./Datafiles/AMZN_2019-01-24.csv

Results or outputs:
./Datafiles/close_price_sp500_{start_date}_to_{end_date}.csv        File with the adjusted close price for all the companies in the SP500 index for the period required
./Datafiles/index_values_{start_date}_to_{end_date}.csv             File with indexes values for VIX, Gold and Oil prices
./Datafiles/{ticker}_{start_date}_to_{end_date}.csv                 File with market information for the company included in the ticker input
./Datafiles/{ticker}_correlated_companies.csv                       Set of correlated companies to company entered in the study (ticker)
./Datafiles/stocktwits_{ticker}_{start_date}_to_{end_date}.csv      Stocktwits and sentiment analysis for the company ticker and for the correlated companies

Notes:
Not any special notes
"""

import sys
import datetime
import requests
import numpy as np
import pandas as pd
import time
from pandas_datareader import data
from textblob import TextBlob
from datetime import datetime as dt


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
    begin_date, last_date_twit = dt.strptime(begin_date, "%Y-%m-%d"), dt.today()
    more_twits = True
    stockTwitsinfo = pd.DataFrame()
    url = 'https://api.stocktwits.com/api/2/streams/symbol/' + ticker + '.json?'
    while more_twits and (begin_date < last_date_twit):
        try:
            twits_req = requests.get(url)
            if twits_req.status_code == 200:
                twits = twits_req.json()
                more_twits = twits['cursor']['more']
                url = 'https://api.stocktwits.com/api/2/streams/symbol/' + ticker + '.json?' + 'max=' + str(twits['cursor'][
                    'max'])
                watchlist_count = twits['symbol']['watchlist_count']
                for twit in twits['messages']:
                    twit['created_at']
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
                    last_date_twit = dt.strptime(date[0], "%Y-%m-%d")
            elif twits_req.status_code == 429:
                print(twits_req.json()['errors'][0]['message'])
                delay = int(twits_req.headers['X-RateLimit-Reset']) + int(time.time()) + 1
                print("Waiting time in seconds: %d" % delay)
                time.sleep(delay)
                break
            else:
                print('Response code by StockTwit: {}'.format(twits_req.status_code))
                break
        except Exception as e:
            print('Error reportedby Stocktwits %s' % e)
            break
    print('Number of twits readed: %d' % stockTwitsinfo.shape[0])
    return stockTwitsinfo


ticker, num_correlated, start_date = sys.argv[1:4]
num_correlated = int(num_correlated)
end_date = sys.argv[4] if len(sys.argv) >= 5 else str(datetime.date.today())
if len(sys.argv) >= 6:
    stk_close_file, index_file, company_file = sys.argv[5:]
else:
    stk_close_file, index_file, company_file = '', '', ''

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
    company_values.to_csv('./Datafiles/' + ticker + '_' + start_date + '_to_' + end_date + '.csv')
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

    index_prices = pd.read_csv(index_file)
    company_values = pd.read_csv(company_file)

    print('Files read...')
    print(sp500_prices.head())
    print(index_prices.head())
    print(company_values.head())
    

ticker_series = sp500_prices[ticker]
correlated_companies = np.abs(sp500_prices.drop('Date', axis=1).apply(lambda x: x.corr(ticker_series)))
correlated_companies = correlated_companies.drop(ticker, axis=0)
correlated_companies = correlated_companies.sort_values(ascending=False)[:num_correlated]
correlated_companies.to_csv('./Datafiles/' + ticker + '_correlated_companies.csv', header=['Correlation_abs'])

print('Collecting data from Yahoo and Federal Reserve has ended...\n')
print('Process to get sentiment analysis for ' + ticker + ' from StockTwits starts...\n')
print('Most correlated companies selected: ' + str(num_correlated))
print(correlated_companies)

stocks_sentiment = pd.DataFrame()
print('Getting the twits for {}'.format(ticker))
stocks_sentiment = stocks_sentiment.append(getting_data_from_StokTwits(ticker, begin_date=start_date), ignore_index=True)

file_name = './Datafiles/stocktwits_' + ticker + '_' + start_date + '_to_' + end_date + '.csv'
stocks_sentiment.to_csv(file_name, index=False)

for cpny in correlated_companies.index:
    print('Getting twits for {}'.format(cpny))
    stocks_sentiment = stocks_sentiment.append(getting_data_from_StokTwits(cpny, begin_date=start_date), ignore_index=True)
    stocks_sentiment.to_csv(file_name, index=False, header=False)

print('Getting twits process has ended...\n')
