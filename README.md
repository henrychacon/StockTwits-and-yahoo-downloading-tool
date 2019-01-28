# StockTwits and yahoo downloading tool

Script developed in python3 to download the adjusted close price for all the companies included in the S&P 500 index and the VIX value from Yahoo database. Also, the commodities: oil (WTI) and gold prices are downloaded from the Federal Reserve database. The correlation matrix is computed and the top n most correlated companies in absolute value from the entered ticker as input is selected. Based on this set of companies, Twits from [https://stocktwits.com/] are collected and the average sentiment analysis per day (polarity and subjectivity) is computed.

For instance, suppose it is dessired to get the top 10 correlated companies and the sentiment analysis for the Coty Inc. (COTY) between 2018-07-01 and 2019-01-25. The follwing command should be executed:

```bash
python3 collecting_data.py LEN 10 2018-07-01 2019-01-26
```
where COTY corresponds to the company's ticker (should be the same to the label used in the file SPY_All_Holdings.xls included in this repository), 10 represents the number of correlated companies (in absolute value) and '2018-07-01', '2019-01-26' is the required period. If the end date is not included, the current day is used.

## Expected output:
During the running process, the following information for the S&P 500 downloading is shown:
![Image 1](https://github.com/henrychacon/StockTwits-and-yahoo-downloading-tool/blob/master/images/image1.jpg)

After the adjusted prices and commodities values are downloaded, the Twits download process starts:
![IMAGEN 2](https://github.com/henrychacon/StockTwits-and-yahoo-downloading-tool/blob/master/images/image2.jpg)

Notice that there is a limitation in the number of Twits collected from [https://stocktwits.com/]. Therefore the process is stopped and resumed until the server allows it. After the process is finished, the following files are saved (where {ticker} corresponds to COTY, {start_date} and {end_date} to 2018-07-01 and 2019-01-26 in the above example):

* File with the adjusted close price for all the companies in the SP500 index for the period required
    *./Datafiles/close_price_sp500_{start_date}_to_{end_date}.csv
* File with indexes values for VIX, Gold and Oil prices
    *./Datafiles/index_values_{start_date}_to_{end_date}.csv                                 
* File with market information for the company included in the ticker input
    *./Datafiles/{ticker}/{ticker}_prices_values_{start_date}_to_{end_date}.csv              
* Set of correlated companies to company entered in the study (ticker)
    *./Datafiles/{ticker}/{ticker}_correlated_companies.csv                                  
* Stocktwits and sentiment analysis for the company ticker and for the correlated companies
    *./Datafiles/{ticker}/stocktwits_{ticker}_{start_date}_to_{end_date}.csv                 
* Sentiment analysis summaryStocktwits and sentiment analysis for the company ticker and for the correlated companies
    *./Datafiles/{ticker}/stocktwits_summary_{ticker}_{start_date}_to_{end_date}.csv         

## Alternative input when only sentiment analysis from StockTwits is required:
In case only the sentiment analysis is required based on the close price already downloaded, it is possible to provide the prices file.

Suppose the sentiment analysis is wanted for AMD for the same period above indicated using the same prices for all the companies in the S&P500 downloaded in the previous example. In this case, the following command should be used:

```bash
python3 collecting_data.py AMD 10 2018-07-01 2019-01-26 ./Datafiles/close_price_sp500_2018-07-01_to_2019-01-26.csv
```
where the file close_price_sp500_2018-07-01_to_2019-01-26.csv includes the adjusted close price downloaded in the previous example.

## Example files:
Output file example for the above executions are including in this repository under the folder Datafiles.



