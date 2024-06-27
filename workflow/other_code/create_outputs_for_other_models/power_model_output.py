#this output will contain data on electirciyt use and the number of EVs, phevs  per vehicle type per economy per year. the output will be able to be biven as long or wide format
#set working directory as one folder back so that config works
#%%
import os
import sys
import re
sys.path.append(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
# Construct the first path to check
root_dir = re.split('transport_model_9th_edition', os.getcwd())[0] + '\\transport_model_9th_edition'
# Check if the first path is not already in sys.path, then append it
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Construct the second path to check (relative to the current working directory)
path_to_add_2 = os.path.abspath(f"{root_dir}/config")
# Check if the second path is not already in sys.path, then append it
if path_to_add_2 not in sys.path:
    sys.path.append(path_to_add_2)
import config

import pandas as pd 
import numpy as np
import yaml
import time
import datetime
import shutil
import sys
import os 
import re
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import matplotlib
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
####Use this to load libraries and set variables. Feel free to edit that file as you need.
#%%
model_output_all_with_fuels = pd.read_csv('output_data/model_output_with_fuels/{}'.format(config.model_output_file_name))

model_output_detailed = pd.read_csv('output_data/model_output_detailed/{}'.format(config.model_output_file_name))

#%%
#extract data so we have a measure in each dataframe and create a units column

#get energy use from model_output_detailed by filtering for electricity
model_output_electricity = model_output_all_with_fuels[model_output_all_with_fuels['Fuel'] == '17_electricity']

#create units column which is PJ
model_output_electricity['Units'] = 'PJ'

#make wide
model_output_electricity_wide = model_output_electricity.pivot_table(index=['Fuel', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Medium', 'Units'], columns='Year', values='Energy')

#save in wide and long format
model_output_electricity.to_csv('output_data/for_other_modellers/LONG_ELEC_PJ_{}'.format(config.model_output_file_name), index=False)
model_output_electricity_wide.to_csv('output_data/for_other_modellers/WIDE_ELEC_PJ_{}'.format(config.model_output_file_name))

#%%
#extract stocks for phev and evs
model_output_phev_ev_stocks = model_output_detailed[model_output_detailed['Drive'].isin(['bev', 'phevg', 'phevd'])]

#create units column which is millions
model_output_phev_ev_stocks['Units'] = 'Millions'

#filter for this data:
model_output_phev_ev_stocks = model_output_phev_ev_stocks[['Year', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Medium', 'Units', 'Stocks']]
#make wide
model_output_phev_ev_stocks_wide = model_output_phev_ev_stocks.pivot_table(index=['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Medium', 'Units'], columns='Year', values='Stocks')


#save in wide and long format
model_output_phev_ev_stocks.to_csv('output_data/for_other_modellers/LONG_PHEV_EV_STOCKS_{}'.format(config.model_output_file_name), index=False)
model_output_phev_ev_stocks_wide.to_csv('output_data/for_other_modellers/WIDE_PHEV_EV_STOCKS_{}'.format(config.model_output_file_name))

#%%

