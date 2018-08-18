from xbrl_parser import run_tickers
import pandas as pd

tickers = pd.read_pickle('sp500.pkl')['Ticker symbol']
run_tickers(tickers)

