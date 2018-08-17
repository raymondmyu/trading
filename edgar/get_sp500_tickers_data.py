import sqlalchemy as sa
import pandas as pd
from xbrl_parser import *
from multiprocessing import Pool

def main():
    sp500tickers = pd.read_pickle('sp500.pkl')['Ticker symbol']
    p = Pool(3)
    p.map(run, sp500tickers)
    
    # for ticker in sp500tickers:
    #     try:
    #         run(ticker)
    #     except Exception as e:
    #         print(e)
    #         continue

if __name__=='__main__':
    main()