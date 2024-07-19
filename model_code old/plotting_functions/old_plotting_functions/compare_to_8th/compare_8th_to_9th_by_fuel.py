#take in output data and do basic visualisationh and analysis

#%%
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
if __name__ == "__main__": #this allows the script to be run directly or from the main.py file as you cannot use relative imports when running a script directly
    # Modify sys.path to include the directory where utility_functions is located
    sys.path.append(f"{config.root_dir}\\code")
    import utility_functions
else:
    # Assuming the script is being run from main.py located at the root of the project, we want to avoid using sys.path.append and instead use relative imports 
    from .. import utility_functions
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

import plotly
import plotly.express as px
pd.options.plotting.backend = "plotly"#set pandas backend to plotly plotting instead of matplotlib
import plotly.io as pio
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook

#%%
#compare model output to 8th edition output. If there are any differences, print them
#laod output from 8th edition
model_output_with_fuels = pd.read_csv(config.root_dir + config.slash + 'output_data\\model_output_with_fuels\\{}'.format(config.model_output_file_name))
model_output_8th = pd.read_csv("intermediate_data\\cleaned_input_data\\energy_with_fuel.csv")
# #%%
# #keep only columns in model_output_8th
# model_output = model_output_with_fuels[model_output_with_fuels.columns.intersection(model_output_8th.columns)]

#%%
# #filter for data within the same Dates of each dataset
# model_output_with_fuels = model_output_with_fuels[model_output_with_fuels['Date'].isin(model_output_8th['Date'])]
# model_output_8th = model_output_8th[model_output_8th['Date'].isin(model_output_with_fuels['Date'])]

#create column in both datasets that states the dataset
model_output_with_fuels['Dataset'] = '9th'
model_output_8th['Dataset'] = '8th'

#concatenate data together
model_output_concat = pd.concat([model_output_with_fuels, model_output_8th], axis=0)
#%%
#plot energy use
#sum up data for energy use by Date, medium, economy, transport type, vehicle type and drive in both scenarios for each dataset
model_output_concat_sum = model_output_concat.groupby(['Date', 'Scenario', 'Economy', 'Medium', 'Dataset', 'Transport Type', 'Vehicle Type', 'Drive', 'Fuel'], as_index=False).sum()

#join together the  'Transport Type', 'Vehicle Type', 'Drive' and 'Scenario' columns
model_output_concat_sum['TransportType_VehicleType_Drive_Scenario_Fuel'] = model_output_concat_sum['Transport Type'] + '_' + model_output_concat_sum['Vehicle Type'] + '_' + model_output_concat_sum['Drive'] + '_' + model_output_concat_sum['Scenario'] + '_' + model_output_concat_sum['Fuel']

#filter out data in Dates that are not in both datasets
model_output_concat_sum = model_output_concat_sum[model_output_concat_sum['Date'].isin(model_output_8th['Date'])]
model_output_concat_sum = model_output_concat_sum[model_output_concat_sum['Date'].isin(model_output_with_fuels['Date'])]
#drop cols we joined together
# model_output_concat_sum = model_output_concat_sum.drop(['Transport Type', 'Vehicle Type', 'Drive', 'Scenario', 'Fuel'], axis=1)

#%%
################################################################################################################################################################

title='Compared to 8th Energy use by Date, economy, in both scenarios, for each drive, USA and PRC removed'

model_output_concat_sum_other_regions = model_output_concat_sum[~model_output_concat_sum['Economy'].isin(['05_PRC', '20_USA'])]

#plot
fig = px.line(model_output_concat_sum_other_regions, x="Date", y="Energy", color="TransportType_VehicleType_Drive_Scenario_Fuel", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename=config.root_dir + config.slash + 'plotting_output\\' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image(config.root_dir + config.slash + "\\plotting_output\\static\\" + title + '.png', scale=1, width=2000, height=1500)

#%%
################################################################################
################################################################################
title='Compared to 8th Energy use by Date, economy, fuel in both scenarios'

#plot
fig = px.line(model_output_concat_sum, x="Date", y="Energy", color="TransportType_VehicleType_Drive_Scenario_Fuel", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename=config.root_dir + config.slash + 'plotting_output\\' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image(config.root_dir + config.slash + "\\plotting_output\\static\\" + title + '.png', scale=1, width=2000, height=1500)

#%%
################################################################################################################################################################

#filter for only passenger light vehicles so the graphs are easier to read
model_output_concat_sum_lv = model_output_concat_sum[model_output_concat_sum['Vehicle Type'] == 'lv']
model_output_concat_sum_lv = model_output_concat_sum_lv[model_output_concat_sum_lv['Transport Type'] == 'passenger']

title='Compared to 8th Energy use by Date, economy, fuel in both scenarios LV only'

#plot
fig = px.line(model_output_concat_sum_lv, x="Date", y="Energy", color="TransportType_VehicleType_Drive_Scenario_Fuel", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename=config.root_dir + config.slash + 'plotting_output\\' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image(config.root_dir + config.slash + "\\plotting_output\\static\\" + title + '.png', scale=1, width=2000, height=1500)
# %%
################################################################################################################################################################
#plot the data for the whole of apec to try understand what we are over/under exagerating compare to 8th.
#first plot energy use by drive type, fuel type split into transport types

title = 'Compared to 8th Energy use by Date, drive, fuel in each ttype'
#filter for scenario = reference
model_output_concat_sum_ref = model_output_concat_sum[model_output_concat_sum['Scenario'] == 'Reference']
#remove non specified from transport type
model_output_concat_sum_ref = model_output_concat_sum_ref[model_output_concat_sum_ref['Transport Type'] != 'nonspecified']
#sum data
model_output_concat_sum_ref = model_output_concat_sum_ref.groupby(['Date', 'Dataset', 'Transport Type', 'Drive', 'Fuel'], as_index=False).sum()

#create a column which concats the drive type and fuel type
model_output_concat_sum_ref['Drive_Fuel'] = model_output_concat_sum_ref['Drive'] + '_' + model_output_concat_sum_ref['Fuel']

#plot
fig = px.line(model_output_concat_sum_ref, x="Date", y="Energy", color="Drive_Fuel", line_dash='Dataset', facet_col="Transport Type", facet_col_wrap=3, title=title)

plotly.offline.plot(fig, filename=config.root_dir + config.slash + 'plotting_output\\' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image(config.root_dir + config.slash + "\\plotting_output\\static\\" + title + '.png', scale=1, width=2000, height=1500)

#%%
################################################################################################################################################################
