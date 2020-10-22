# Flow 
1. Crawl EOD stock data
2. Crawl Dividend data

2.1. Adjust stock price accordingly 
3. Generate buy signals based on technical analysis 
3.1. Filter stocks based on trade volume
3.2. Categorized stocks (trending/non-trending) using Average Directional Index 
3.3. Filter for buy signals
3.3.1. Filter trending stocks using Simple Moving Average and Directional Index
3.3.2. Filter non-trending stocks using Bollinger Bands and Relative Strength Index
3.4. Filter using fundamental analysis
3.5. Generate graphs
4. Email stock suggestions 

#  TODO 
1. change trade volume filter to using average (currently using most recent date only)
2. read technical indical setup from config file (currently hard-coded)
3. add user profile 
4. support more indicators
