import pymongo
from pymongo import MongoClient
import os, glob
from multiprocessing import Pool
import json

def get_request(f):
    return dict(filename=os.path.basename(f), contents=json.load(open(f,'r')))

p = Pool(3)
requests_array = p.map(get_request, glob.glob('financials/requests/*.json'))

client = MongoClient()
db = client.financials
requests_coll = db.requests

result = requests_coll.insert_many(requests_array)

