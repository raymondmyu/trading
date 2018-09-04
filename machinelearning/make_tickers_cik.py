import pandas as pd
import numpy as np
import sqlalchemy as sa
import os, sys; sys.path.append('../edgar')
from xbrl_parser import getCIK
from tqdm import tqdm
from multiprocessing import Pool

p = Pool(3)
tickers_df = pd.read_csv('../intrinio/tickers.csv')
ciks = p.map(getCIK, tqdm(tickers_df.Symbol))
tickers_df['CIK'] = ciks
tickers_df.to_csv('tickers_cik.csv', index=False)