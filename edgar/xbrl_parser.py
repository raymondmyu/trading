import pandas as pd
import numpy as np
import requests
from arelle import Cntlr
import sqlalchemy as sa
from bs4 import BeautifulSoup
import re
import os, sys, shutil
import numpy as np
import glob
from multiprocessing import Pool
import multiprocessing

def get_xbrl_path(idx_path):
    try:
        resp = requests.get(idx_path)
        soup = BeautifulSoup(resp.content, 'lxml')
        href = soup('a',text=re.compile(r'.xml'))
        href = href[np.argmin([len(h.text) for h in href])].get('href')
        return 'https://www.sec.gov'+href
    except Exception as e:
        print(e)
        return np.nan

def get_current_df(xbrl_path):
    arelle = Cntlr.Cntlr()
    arelle.webCache.cacheDir = '/disk-1/arelle/cache/'
    arelle_xbrl = arelle.modelManager.load(xbrl_path)

    arelle_df = pd.DataFrame(data=[(fact,
                        fact.value,
                        fact.concept.qname,
                        fact.context.hasSegment,
                        fact.context.period.viewText(),
                        fact.contextID,
                        fact.context.isStartEndPeriod,
                        fact.context.isInstantPeriod,
                        fact.context.isForeverPeriod,
                        fact.context.startDatetime,
                        fact.context.endDatetime)
                     for fact in arelle_xbrl.facts],
                 columns=('Fact',       #Fact; We leave the fact in the table in case we want more out of it
                          'Value',      #Value, like 5,200,000 in "5.2m"
                          'Account',    #Account, like "Cash" in "Cash of 5.2m"
                          'Category',   #Category, like "for the parent company" in "Cash of 5.2m for the parent company"b
                          'Period',
                          'ContextID',
                          'isStartEndPeriod',
                          'isInstantPeriod',
                          'isForeverPeriod',
                          'startDateTime',
                          'endDateTime'))

    arelle_df = arelle_df[(arelle_df.Fact.map(lambda f: f.isNumeric and not f.isNil))]# & #Fact is Numeric (i.e. can be converted to a number)
    #                                                 arelle_df.Account.map(lambda a: a=='us-gaap:EarningsPerShareBasic') & #Just Cash; Account mentions "Cash", anywhere would give us too many values
                                                    # arelle_df.Category.map(lambda c:not c))] # Could also use "~", which does boolean "not" on the entire column


#     file_path = arelle.webCache.getfilename(xbrl_path)
#     if os.path.exists(file_path):
#         shutil.move(file_path,os.path.join('/disk-1/arelle/cache',os.path.basename(file_path)))
        
    
    return arelle_df #current_df

def getCIK(ticker):
    URL = 'http://www.sec.gov/cgi-bin/browse-edgar?CIK={}&Find=Search&owner=exclude&action=getcompany'
    CIK_RE = re.compile(r'.*CIK=(\d{10}).*')    
    f = requests.get(URL.format(ticker), stream = True)
    results = CIK_RE.findall(f.text)
    if len(results):
        results[0] = int(re.sub('\.[0]*', '.', results[0]))
        return str(results[0])
    else:
        return None

def preprocess_df(df):
    df.startDateTime = pd.to_datetime(df.startDateTime)
    df.endDateTime = pd.to_datetime(df.endDateTime, errors='coerce')
    df['Days'] = (df.endDateTime - df.startDateTime).dt.days
    df.Value = df.Value.astype(float)
    df.Account = df.Account.astype(str)
    df['endDateTime2'] = df.endDateTime - pd.offsets.Day()
    df = df[df.Category==False]
    return df
    
def consolidate_periods(df):
    df_t = df.copy()
    df_t = df_t.drop_duplicates(subset=['Period'], keep='last')
    df_t.sort_values(['startDateTime','endDateTime2'], inplace=True)
    df_t['to_consolidate'] = df_t.startDateTime.duplicated(keep='first')
    df_t['startDateTime2'] = df_t['startDateTime']
    df_t['Value2'] = df_t['Value']
    df_t.reset_index(drop=True, inplace=True)
    
    def consolidate(row):
        if row.to_consolidate:
            row.Value2 = row.Value - df_t.Value.iloc[row.name-1]
            row.startDateTime2 = df_t.endDateTime.iloc[row.name-1]
        return row
    
    if len(df_t)>1:
        df_t = df_t.apply(consolidate, 1)
        
    df_t['Days2'] = (df_t.endDateTime2 - df_t.startDateTime2).dt.days + 1
    df_t['Period2'] = df_t.startDateTime2.dt.strftime('%Y-%m-%d')+df_t.endDateTime2.dt.strftime('%Y-%m-%d')
    
    return df_t

def get_consolidated_df(df):
    df_t = df.query("isStartEndPeriod").copy()
    df_t = df_t.groupby(['Account','startDateTime']).apply(consolidate_periods).reset_index(drop=True)
    df_t = df_t.drop_duplicates(subset=['Account','startDateTime2','Period2'], keep='last')
    
    df_t2 = df.query('isStartEndPeriod==False').copy()
    df_t2.sort_values(['startDateTime','endDateTime2'], inplace=True)
    df_t2['to_consolidate'] = False
    df_t2['startDateTime2'] = df_t2['startDateTime']
    df_t2['Value2'] = df_t2['Value']
    df_t2['Days2'] = df_t2['Days']
    df_t2['Period2'] = df_t2['Period']
    df_t2 = df_t2.drop_duplicates(subset=['Account','endDateTime2','Period2'], keep='last')
    
    df_all = pd.concat([df_t,df_t2], ignore_index=True, sort=False)
    
    return df_all
    
def run(ticker, outdir='currents'):
    try:
        currents = [os.path.basename(f).replace('.pkl','') for f in glob.glob(os.path.join(outdir,'*.pkl'))]
        if ticker not in currents:
            con = sa.create_engine('sqlite:///edgar_htm_idx.db').connect()
            print('Getting ticker indices for', ticker)
            cik = getCIK(ticker)
            ticker_df = pd.read_sql('select * from idx where cik={} and type in ("10-K","10-Q","20-F")'.format(cik), con)
            print('Getting xbrl paths')
            ticker_df['xbrl_path'] = ticker_df.path.apply(get_xbrl_path)
            print('Getting current dataframes')
            df_currents = pd.DataFrame()
            for xbrl_path, cik, report_date, report_type in ticker_df[['xbrl_path','cik','date','type']].dropna().values:
                print(xbrl_path)
                try:
                    df_t = get_current_df(xbrl_path)
                    df_t['Ticker'] = ticker
                    df_t['cik'] = cik
                    df_t['ReportDate'] = report_date
                    df_t['ReportType'] = report_type
                    df_currents = df_currents.append(df_t, ignore_index=True)
                except Exception as e:
                    print(e)
                    continue

            df_currents.drop('Fact',1).to_pickle(os.path.join(outdir,'{}.pkl'.format(ticker)))
            con.close()
        return
    except Exception as e:
        print(e)
        return

def run_tickers(tickers):
    p = Pool(multiprocessing.cpu_count()//2-1)
    p.map(run, tickers)
    
if __name__=='__main__':
    if len(sys.argv)>2:
        outdir = sys.argv[2]
    else:
        outdir = 'currents'
    run(sys.argv[1], outdir)