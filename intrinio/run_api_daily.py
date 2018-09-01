import pandas as pd
import numpy as np
from pymongo import MongoClient
from intrinio_api import run_sectors, get_percentile_filtered_df

client = MongoClient(host='mongodb://datascience.imwithyu.com', port=27017)
db = client.financials
requests_coll = db.requests

tickers = get_percentile_filtered_df()

# Find the sectors that have been entirely accounted for
sectors = []
for sector in tickers.Sector.unique():
    tickers_in_sector = tickers.query("Sector==@sector").Symbol.unique().tolist()
    # Are there any symbols NOT in tickers_in_sector?
    if requests_coll.find({
            'contents.identifier': {
                '$nin': tickers_in_sector
            }
        }).count() > 0:
        print('Sector',sector,'is incomplete')
        sectors.append(sector)

run_sectors(sectors)