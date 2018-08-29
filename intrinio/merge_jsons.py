import json
import os, glob
import tqdm
from multiprocessing import Pool

def get_request(f):
    return dict(filename=os.path.basename(f), contents=json.load(open(f,'r')))

p = Pool(3)
requests = p.map(get_request, glob.glob('financials/requests/*.json'))

json.dump(requests,open('financials/merged/merged1.json','w'))