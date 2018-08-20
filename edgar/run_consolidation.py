import pandas as pd
import numpy as np
import os, glob
from xbrl_parser import get_consolidated_df
import multiprocessing

def create_consolidated_pkl(f):
    if os.path.basename(f) not in os.listdir('consolidated'):
        print(f)
        try:
            df = pd.read_pickle(f)
            df_cons = get_consolidated_df(df)
            df_cons.to_pickle(os.path.join('consolidated',os.path.basename(f)))
            return
        except Exception as e:
            print(e)
            return
    else:
        return


p = multiprocessing.Pool(multiprocessing.cpu_count()//2-1)
p.map(create_consolidated_pkl, glob.glob('currents/*'))