from pymongo import MongoClient
import pandas as pd

client = MongoClient(host='mongodb://datascience.imwithyu.com', port=27017)
db = client.financials
requests_coll = db.requests

requests_coll.aggregate([
    {
        "$unwind": "$contents.data"
    },
    {
        "$project": {
            "_id": 0,
            "tag": "$contents.data.tag",
            "value": "$contents.data.value",
            "ticker": "$contents.identifier",
            "statement": "$contents.statement",
            "date": "$contents.date" 
        }
    },
    {
        "$out": "tocsv"
    }
])