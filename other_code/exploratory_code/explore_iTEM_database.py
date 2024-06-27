#explore the item database
#%%
#set working directory as one folder back so that config works
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
###IMPORT GLOBAL VARIABLES FROM config.py
import sys
sys.path.append("./config")
from config import *
####Use this to load libraries and set variables. Feel free to edit that file as you need.

#%%
from item import historical, model, structure

import item
#%%

help(historical.T009)
historical.













#%%
item.historical.COUNTRY_NAME
#%%
item.historical.COUNTRY_NAME["dem. people's republic of korea"]

# %%
item.historical.process(000)
# %%
item.historical.source_str('T000')
# %%
item.historical.T000.COLUMNS
# %%
item.historical.T000.COMMON_DIMS
# %%
item.historical.T000.DATAFLOW= 'ACTIVITY'
# %%
item.historical.T000.DATAFLOW
# %%
item.historical.T000.mode_and_vehicle_type('Rail passenger transport')
# %%
item.historical.T000.process
# %%
item.model.load_model_data(version=5)#'bp')
# %%
item.model.get_model_names()

# %%
help(historical.T009)
# %%
