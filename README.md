# StockTwits-and-yahoo-downloading-tool
Script developed in python to download the adjusted close price from the companies included in the S&amp;P 500 index, the price of VIX, OIL, and Gold from the Federal Reserve and StockTwits from the most correlated companies of the entered company

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
