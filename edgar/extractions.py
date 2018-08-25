import pandas as pd
import warnings; warnings.simplefilter('ignore')
import re

def get_startend_valuecounts(ticker):
    df = pd.read_pickle('consolidated/{}.pkl'.format(ticker))
    return df.query("isStartEndPeriod").Account.value_counts()

def get_income_statements(ticker):
    df = pd.read_pickle('consolidated/{}.pkl'.format(ticker))
    valuecounts = df.query("isStartEndPeriod").Account.value_counts()
    revenue = valuecounts[[c for c in valuecounts.index if 'revenue' in c.lower()]]
    revenue = revenue[revenue==revenue.max()]
    revenue = sorted(revenue.index, key=lambda x: len(x))[:2]
    
    accounts = [
     'us-gaap:Revenues',
     'us-gaap:FinancialServicesRevenue',
     'us-gaap:SalesRevenueNet',
     'us-gaap:OilAndGasRevenue',
     'us-gaap:CostOfGoodsAndServicesSold',
     'us-gaap:CostOfGoodsSold',
     'us-gaap:CostOfRevenue',
     'us-gaap:GrossProfit',
     'us-gaap:FinancialServicesCosts',
     'us-gaap:SellingGeneralAndAdministrativeExpense',
     'us-gaap:CostsAndExpenses',
     'us-gaap:OperatingIncomeLoss',
     'us-gaap:InterestExpense',
     'us-gaap:OtherNonoperatingIncomeExpense',
     'us-gaap:IncomeLossFromEquityMethodInvestments',
     'us-gaap:NonoperatingIncomeExpense',
     'us-gaap:NonOperatingIncomeLoss',
     'us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest',
     'us-gaap:IncomeTaxExpenseBenefit',
     'us-gaap:ProfitLoss',
     'us-gaap:NetIncomeLoss']
    
    accounts = pd.Series(revenue+accounts).drop_duplicates().tolist()
    
    df['Months2'] = df.endDateTime2.dt.month - df.startDateTime2.dt.month + 1
    income_pivot = df.query('Account in @accounts').pivot_table('Value2',['Months2','startDateTime2','endDateTime2'],'Account')
    income_pivot.columns.name = None
    income_cleaned = income_pivot[[c for c in accounts if c in income_pivot.columns]]
    income_cleaned.reset_index(inplace=True)
    income_cleaned = income_cleaned.query("Months2==3")
    income_cleaned.drop(['Months2','startDateTime2'], 1, inplace=True)
    income_cleaned.set_index('endDateTime2', inplace=True)
    income_cleaned.columns = [re.sub('^.*:','',c) for c in income_cleaned]
    
    return income_cleaned

def get_cashflow_statements(ticker):
    