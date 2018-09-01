import os
import pandas as pd
import numpy as np
import re
from pandas import Timestamp
from zipline.data.bundles import load
from zipline.data.bundles.quandl import quandl_bundle
from zipline.data.data_portal import DataPortal
from zipline.utils.calendars import get_calendar

def get_prices(numdays=1000):
    now = Timestamp.utcnow()
    bundle = load('quantopian-quandl', os.environ, now)

    all_assets = bundle.asset_finder.retrieve_all(bundle.asset_finder.sids)
    symbols = set(
    str(asset.symbol) for asset in bundle.asset_finder.retrieve_all(bundle.asset_finder.equities_sids)
    )

    quandl_data = DataPortal(asset_finder= bundle.asset_finder,
    trading_calendar = get_calendar('NYSE'),
    first_trading_day = bundle.equity_daily_bar_reader.first_trading_day,
    equity_minute_reader=bundle.equity_minute_bar_reader,
    equity_daily_reader=bundle.equity_daily_bar_reader,
    adjustment_reader=bundle.adjustment_reader)

    end_dt = pd.Timestamp('2018-03-31', tz = 'utc')

    quandl_symbols = []
    for ticker in symbols:
        try:
            quandl_symbols.append(quandl_data.asset_finder.lookup_symbol(ticker,end_dt))
        except:
            continue
    quandl_pricing = quandl_data.get_history_window(quandl_symbols,end_dt,numdays,'1d','close','daily')
    quandl_pricing.columns = [c.symbol for c in quandl_pricing.columns]

    return quandl_pricing