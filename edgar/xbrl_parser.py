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
    # xbrl_path = get_xbrl_path(F.path.sample().iloc[0])
    arelle = Cntlr.Cntlr()
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

#     arelle_df['Start'] = pd.to_datetime(arelle_df.Period.str.slice(0,10),errors='coerce')
#     arelle_df['End'] = pd.to_datetime(arelle_df.Period.str.slice(10,),errors='coerce')
#     arelle_df['isPeriod'] = pd.notnull(arelle_df.End)
#     arelle_df['Days'] = (arelle_df.End - arelle_df.Start).dt.days

    arelle_df = arelle_df[(arelle_df.Fact.map(lambda f: f.isNumeric and not f.isNil))]# & #Fact is Numeric (i.e. can be converted to a number)
    #                                                 arelle_df.Account.map(lambda a: a=='us-gaap:EarningsPerShareBasic') & #Just Cash; Account mentions "Cash", anywhere would give us too many values
                                                    # arelle_df.Category.map(lambda c:not c))] # Could also use "~", which does boolean "not" on the entire column


#     def get_contexts(arelle_df):
#         top_days = arelle_df[arelle_df.isPeriod].Days.value_counts()
#         top_periods = arelle_df[arelle_df.isPeriod].Period.value_counts()
#         top_dates = arelle_df[~arelle_df.isPeriod].Period.value_counts()
#         top_periods_df = top_periods.to_frame().reset_index()
#         top_periods_df.columns = ['Period', 'count']
#         top_periods_df['Start'] = pd.to_datetime(top_periods_df.Period.str.slice(0,10),errors='coerce')
#         top_periods_df['End'] = pd.to_datetime(top_periods_df.Period.str.slice(10,),errors='coerce')
#         top_periods_df['Days'] = (top_periods_df.End - top_periods_df.Start).dt.days
#         current_days = list(filter(lambda x: (85<x<95) | (360<x<370), list(top_days.index)))[0]
#         current_period = top_periods_df[top_periods_df.Days==current_days].sort_values('End',ascending=False).iloc[0].Period
#         current_date = top_dates.index[:2].sort_values(ascending=False)[0]
#         current_date_compare = top_dates.index[:2].sort_values(ascending=False)[1]
#         current_period_ly = current_period.replace(current_period[:4],str(int(current_period[:4])-1))
#         current_date_ly = current_date.replace(current_date[:4],str(int(current_date[:4])-1))
#         return current_period, current_date, current_date_compare, current_period_ly, current_date_ly

#     period_categories_df = pd.DataFrame({'PeriodCategory':['current_period','current_date','current_date_compare','current_period_ly','current_date_ly'],'Period':get_contexts(arelle_df)})

#     arelle_df = arelle_df.merge(period_categories_df, on='Period', how='outer')
#     arelle_df.Account = arelle_df.Account.astype(str)
#     arelle_df = arelle_df.dropna(subset=['PeriodCategory','Account','Category'])

#     current_period_df = arelle_df[(arelle_df.PeriodCategory=='current_period')&(~arelle_df.Category)]
#     current_date_df = arelle_df[(arelle_df.PeriodCategory=='current_date')&(~arelle_df.Category)]
#     current_df = pd.concat([current_period_df, current_date_df], ignore_index=True)

    file_path = arelle.webCache.getfilename(xbrl_path)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    return arelle_df #current_df

def run(ticker):
    try:
        currents = [os.path.basename(f).replace('.pkl','') for f in glob.glob('currents/*')]
        if ticker not in currents:
            con = sa.create_engine('sqlite:///edgar_htm_idx.db').connect()
            print('Getting ticker indices for', ticker)
            ticker_df = pd.read_sql('select *, tc.* from idx inner join tickercik tc on tc.CIK=idx.cik where tc.Ticker="{}" and type in ("10-K","10-Q")'.format(ticker), con)
            print('Getting xbrl paths')
            ticker_df['xbrl_path'] = ticker_df.path.apply(get_xbrl_path)
            print('Getting current dataframes')
            df_currents = pd.DataFrame()
            for xbrl_path in ticker_df.xbrl_path.dropna():
                print(xbrl_path)
                try:
                    df_currents = df_currents.append(get_current_df(xbrl_path), ignore_index=True)
                except Exception as e:
                    print(e)
                    continue

            df_currents.drop('Fact',1).to_pickle('currents/{}.pkl'.format(ticker))
            con.close()
        return
    except Exception as e:
        print(e)
        return
        
#         dirpath = '/home/ray/.config/arelle/cache'

#         for filename in os.listdir(dirpath):
#             filepath = os.path.join(dirpath, filename)
#             try:
#                 shutil.rmtree(filepath)
#             except OSError:
#                 os.remove(filepath)

if __name__=='__main__':
    run(sys.argv[1])