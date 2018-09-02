#!/bin/bash
/home/ray/anaconda3/bin/python requests_to_longform.py
cd /home/ray/Projects/trading/intrinio/mongo/data/db
rm -f longform.csv
/usr/bin/mongoexport --type=csv -d financials -c tocsv -o longform.csv -f tag,value,ticker,statement,date
rm -f longform.zip
zip longform.zip longform.csv
