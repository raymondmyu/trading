import pandas as pd
import numpy as np
from pymongo import MongoClient
from intrinio_api import run_sectors, get_percentile_filtered_df

client = MongoClient()
db = client.financials
requests_coll = db.requests

tickers = get_percentile_filtered_df()

# Find the sectors that have been entirely accounted for
symbols_in_requests = requests_coll.find().distinct('contents.identifier')
sectors = []
for sector in tickers.Sector.unique():
    tickers_in_sector = tickers.query("Sector==@sector").Symbol.unique().tolist()
    # Are there any tickers_in_sector NOT in the database already?
    if len(set(tickers_in_sector)-set(symbols_in_requests))>0:
        print('Sector',sector,'is incomplete')
        sectors.append(sector)

run_sectors(sectors)