#just plot the columns in model output by eocnomy. nothign special
#because we aahve 21 graphs in each file, we dont have enough room in the graphs to plot by more than just one category other than economy. so we will plot by economy and then by drive or vehicle type normally

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
###IMPORT GLOBAL VARIABLES FROM config.py
import sys
sys.path.append("./config")
from config import *
####Use this to load libraries and set variables. Feel free to edit that file as you need.

import plotly
import plotly.express as px
pd.options.plotting.backend = "plotly"#set pandas backend to plotly plotting instead of matplotlib
import plotly.io as pio
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook
#%%

#load data in
model_output_all = pd.read_csv('output_data/model_output/{}'.format(config.model_output_file_name))
model_output_detailed = pd.read_csv('output_data/model_output_detailed/{}'.format(config.model_output_file_name))
change_dataframe_aggregation = pd.read_csv('intermediate_data/road_model/change_dataframe_aggregation.csv')
model_output_with_fuels = pd.read_csv('output_data/model_output_with_fuels/{}'.format(config.model_output_file_name))
#%%
#FILTER FOR SCENARIO OF INTEREST
#this should be temporary as the scenario should be passed in as a parameter through config if it is useed elsewhere

model_output_all = model_output_all[model_output_all['Scenario']==SCENARIO_OF_INTEREST]
model_output_detailed = model_output_detailed[model_output_detailed['Scenario']==SCENARIO_OF_INTEREST]
change_dataframe_aggregation = change_dataframe_aggregation[change_dataframe_aggregation['Scenario']==SCENARIO_OF_INTEREST]
model_output_with_fuels = model_output_with_fuels[model_output_with_fuels['Scenario']==SCENARIO_OF_INTEREST]
#%%
#plot data by economy by drive:
#plot energy use by economy by drive 
#plot activity by economy by drive
#plot stocks by economy by drive

#plot data by economy by vehicle type:
#plot energy use by economy by vehicle type
#plot activity by economy by vehicle type
#plot stocks by economy by vehicle type

#plot energy use by economy by fuel type

