#set working directory as one folder back so that config works
import os
import sys
import re
sys.path.append(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
current_working_dir = os.getcwd()
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = re.split('transport_model_9th_edition', script_dir)[0] + 'transport_model_9th_edition'
if __name__ == "__main__": #this allows the script to be run directly or from the main.py file as you cannot use relative imports when running a script directly
    # Modify sys.path to include the directory where utility_functions is located
    sys.path.append(f"{root_dir}/code")
    import config
    import utility_functions
else:
    # Assuming the script is being run from main.py located at the root of the project, we want to avoid using sys.path.append and instead use relative imports 
    from .. import utility_functions
    from .. import config
#################

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

# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook
import matplotlib.pyplot as plt
plt.rcParams['figure.facecolor'] = 'w'

save_html=True
save_fig=False

#%%
#laod data from 
# road_model_input = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/road_model_input_wide.csv')

# growth_forecasts = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/growth_forecasts.csv')

# non_road_model_input = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/non_road_model_input_wide.csv')

road_model_input_wide = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/road_model_input_wide.csv')
growth_forecasts = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/growth_forecasts.csv')
non_road_model_input_wide = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/non_road_model_input_wide.csv')

#%%
################################################################################################################################################################
#plot mileage by economy (facets) using plotl;y
#sum uo average mileage for each vehicle typew
x= road_model_input_wide.groupby(['Date','Vehicle Type','Economy','Transport Type'])['Mileage_growth'].mean().reset_index()
#concat transport type asn dvehicle type
x['Transport Type'] = x['Transport Type'] + ' ' + x['Vehicle Type']
#drop nans
x = x.dropna()

import plotly.express as px
fig = px.bar(x, x="Economy", y="Mileage_growth", color='Transport Type', facet_col="Transport Type", facet_col_wrap=3)
#save to html
fig.write_html("plotting_output/input_exploration/road_mileage_by_economy.html", auto_open=True)
#%%
#plot mileage by economy (facets) using plotl;y
#sum uo average mileage for each vehicle typew
x= road_model_input_wide.groupby(['Date','Vehicle Type','Economy','Transport Type'])['Mileage'].mean().reset_index()
#concat transport type asn dvehicle type
x['Transport Type'] = x['Transport Type'] + ' ' + x['Vehicle Type']
#drop nans
x = x.dropna()

import plotly.express as px
fig = px.bar(x, x="Economy", y="Mileage", color='Transport Type', facet_col="Transport Type", facet_col_wrap=3)
#save to html
fig.write_html("plotting_output/input_exploration/road_mileage_by_economy.html", auto_open=True)
################################################################################################################################################################