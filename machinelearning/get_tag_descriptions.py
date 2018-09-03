import pandas as pd

links = {
    'income_statement': 'https://intrinio.com/data-tags/income-statement',
    'balance_sheet': 'https://intrinio.com/data-tags/balance-sheet-statement',
    'cashflow_statement': 'https://intrinio.com/data-tags/cashflow-statement',
    'calculations': 'https://intrinio.com/data-tags/calculations-metrics'
}

for statement, link in links.items():
    print(statement)
    df = pd.read_html(link)[0]
    df.to_csv(statement+'_tags_desc.csv', index=False)