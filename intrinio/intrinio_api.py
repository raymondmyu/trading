import pandas as pd
import numpy as np
import requests
import json
import os
import re
import json, glob

def request_and_store(ticker,quarter,statement,page,count):
    params = dict(identifier=ticker,
      statement=statement,
      type='QTR',
      date=quarter,
      page_number=page)
    
    fname = '_'.join(map(lambda x: str(x), params.values())) + '.json'
    fpath = os.path.join('financials','requests',fname)
    
    # Request
    if not os.path.exists(fpath):
        print(ticker, quarter, statement, page)
        resp = requests.get('https://api.intrinio.com/financials/standardized', params=params, auth=('1f3ea4c3c63c5785750626ea97e9bc87', '63d202d4187ad187a26d452909ac16f9'))
        dic = json.loads(resp.content)
        stopticker = (int(dic['result_count']) == 0) & (statement=='income_statement')
        count += 1
    else:
        try:
            dic = json.load(open(fpath))
            stopticker = (int(dic['result_count']) == 0) & (statement=='income_statement')
        except Exception as e:
            print(e, fpath)
    
    total_pages = dic['total_pages']
    
    # Store
    dic2 = dict(dic, **params)
    json.dump(dic2, open(fpath,'w'))
    
    return total_pages, count, stopticker

def get_financials(tickers, yearstart=2010, quarters = None, statements = ['income_statement','cash_flow_statement','calculations','balance_sheet']):
    dics = []
    count = 0
    if quarters is None:
        quarters = (pd.date_range(start=str(yearstart),end='2017-12-31',freq='QS')[::-1]).strftime('%Y-%m-%d')
    for ticker in tickers:
        stopticker = False
        for quarter in quarters:
            for statement in statements:
                page = 1
                total_pages = 1
                while page <= total_pages:                
                    total_pages, count, stopticker = request_and_store(ticker,quarter,statement,page,count)
                    page += 1
                    if stopticker:
                        print('stopped', ticker, quarter, statement)
                        break
                if stopticker:
                    break
            if stopticker:
                break
        if stopticker:
            continue

    return count

def get_df(ticker):
    dics = [json.load(open(f)) for f in glob.glob('financials/requests/{}_*.json'.format(ticker))]
    if len(dics) == 0:
        count = get_financials([ticker])
        dics = [json.load(open(f)) for f in glob.glob('financials/requests/{}*.json'.format(ticker))]
    df = pd.DataFrame(dics)
    df = df[df.result_count>0]
    df_t = df.data.apply(lambda x: pd.DataFrame(x).set_index('tag').iloc[:,0])
    df_t['ticker'] = df.identifier
    df_t['statement'] = df.statement
    df_t['date'] = pd.to_datetime(df.date)
    df_t = df_t.sort_values(['ticker','statement','date'])
    df_t = pd.melt(df_t, id_vars=['ticker','statement','date'], var_name='tag', value_name='value').dropna()
    df_t.value = pd.to_numeric(df_t.value, errors='coerce')
    return df_t