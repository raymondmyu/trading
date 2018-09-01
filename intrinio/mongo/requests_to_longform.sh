#!/bin/bash
/home/ray/anaconda3/bin/python requests_to_longform.py
cd /home/ray/Projects/trading/intrinio/mongo/data/db
/usr/bin/mongoexport --type=csv -d financials -c tocsv -o longform.csv -f tag,value,ticker,statement,date
rm longform.zip
zip longform.zip longform.csv