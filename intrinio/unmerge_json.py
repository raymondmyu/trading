import json, os
from multiprocessing import Pool

def make_json(d):
    with open(os.path.join('financials','requests',d['filename']),'w') as f:
        json.dump(d['contents'], f)
    return

p = Pool(3)
p.map(make_json, json.load(open(os.path.join('financials','merged','merged1.json'),'r')))