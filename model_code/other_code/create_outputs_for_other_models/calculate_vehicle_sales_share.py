
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
font_size = 20
AUTO_OPEN_PLOTLY_GRAPHS = True
#%%
#laod output from 8th edition
model_output_8th = pd.read_csv(config.root_dir + '\\' + 'intermediate_data\\activity_efficiency_energy_road_stocks.csv')
#change 'Carbon Neutral' Scenario to Carbon Neutrality
model_output_8th.loc[model_output_8th['Scenario']=='Carbon Neutral','Scenario'] = 'Carbon Neutrality'

#%%
#plot energy use
#sum up data for energy use by year, medium, economy, transport type, vehicle type and drive in both scenarios for each dataset
model_output_8th_sum = model_output_8th.groupby(['Year', 'Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive'], as_index=False).sum()

#%%
#filter dfata from after 2050
model_output_8th_sum = model_output_8th_sum[model_output_8th_sum['Year']<=2050]
# model_output_8th_sum = model_output_8th_sum[model_output_8th_sum['Scenario']==SCENARIO_OF_INTEREST]

#create verison of dataframe that doesnt have  economy groupings
model_output_8th_sum_no_economy = model_output_8th_sum.copy()
model_output_8th_sum_no_economy = model_output_8th_sum_no_economy.drop(columns=['Economy'])
model_output_8th_sum_no_economy = model_output_8th_sum_no_economy.groupby(['Year', 'Scenario', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive'], as_index=False).sum()
#make Economy column which is just 00_APEC
model_output_8th_sum_no_economy['Economy'] = '00_APEC'
#join to original data
model_output_8th_sum = pd.concat([model_output_8th_sum, model_output_8th_sum_no_economy], ignore_index=True)


#%%
#keep pre 2050
model_output_8th_sum = model_output_8th_sum[model_output_8th_sum['Year']<=2050]

#%%
#CALCUALTE SALES SHARE 
#sum stocks by year, vehicle type, drive type, dataset
model_output_concat_sum_sales_with_economy = model_output_8th_sum.groupby(['Year', 'Transport Type', 'Vehicle Type','Scenario', 'Drive', 'Economy'], as_index=False).sum()
#claulcate sales as teh schange in stocks each eyar
model_output_concat_sum_sales_with_economy['Sales'] = model_output_concat_sum_sales_with_economy.groupby(['Transport Type', 'Vehicle Type','Scenario', 'Drive', 'Economy'])['Stocks'].diff()
#set any negatives to 0
model_output_concat_sum_sales_with_economy['Sales'] = model_output_concat_sum_sales_with_economy['Sales'].clip(lower=0)
#create a column that is the sum of sales by year, transport type and Scenario
model_output_concat_sum_sales_with_economy['Sales_sum'] = model_output_concat_sum_sales_with_economy.groupby(['Year','Transport Type','Vehicle Type', 'Scenario', 'Economy'])['Sales'].transform('sum')
#calculate sales share
model_output_concat_sum_sales_with_economy['Sales share'] = model_output_concat_sum_sales_with_economy['Sales'] / model_output_concat_sum_sales_with_economy['Sales_sum']
#drop Sales_sum and reg measures
model_output_concat_sum_sales_with_economy = model_output_concat_sum_sales_with_economy.drop(columns=['Sales_sum','Activity','Efficiency','Energy','Stocks'])
#merge with the model output data using left join
model_output_8th_with_sales_share = model_output_8th_sum.merge(model_output_concat_sum_sales_with_economy, how='left', on=['Year', 'Transport Type', 'Vehicle Type','Scenario', 'Drive', 'Economy'])

#%%
#save this data for use later on:
model_output_8th_with_sales_share.to_csv(config.root_dir + '\\' + 'intermediate_data\\cleaned_input_data\\8th_activity_efficiency_energy_road_stocks_sales_share.csv', index=False)


#%%


#test plot the data:
#do a for loop for each transport type and scenario,
#do a line chart of sales share by year, vehicle type, drive type and facet by economy
for transport_type in model_output_8th_with_sales_share['Transport Type'].unique():
    #ignore nonspecified
    if transport_type == 'nonspecified':
        continue
    for scenario in model_output_8th_with_sales_share['Scenario'].unique():
        #subset the data
        data = model_output_8th_with_sales_share[(model_output_8th_with_sales_share['Transport Type']==transport_type) & (model_output_8th_with_sales_share['Scenario']==scenario)]
        #create title
        title = transport_type + ' ' + scenario + ' sales share'
        #plot the data
        fig = px.line(data, x='Year', y='Sales share', color='Vehicle Type', facet_col='Economy', facet_col_wrap=7, line_dash='Drive')
        fig.update_layout(title_text=transport_type + ' ' + scenario)
        
        plotly.offline.plot(fig, filename=config.root_dir + '\\' + 'plotting_output\\8th_edition\\' + title + '.html', auto_open=False)
# %%

#compare agaisnt previously calcualted vlaues: 
prev_sales_share = pd.read_csv(config.root_dir + '\\' + 'intermediate_data\\cleaned_input_data\\vehicle_sales_share.csv')

#join the two dataframes using left join then calcualte the diff
model_output_8th_with_sales_share_diff = model_output_8th_with_sales_share.merge(prev_sales_share, how='left', on=['Year', 'Transport Type', 'Vehicle Type','Scenario', 'Drive', 'Economy'])

model_output_8th_with_sales_share_diff['diff'] = model_output_8th_with_sales_share_diff['Sales share'] - model_output_8th_with_sales_share_diff['Vehicle_sales_share']

#%%
#plot the diff 
#do a for loop for each transport type and scenario,
#do a line chart of diff in sales share by year, vehicle type, drive type and facet by economy
for transport_type in model_output_8th_with_sales_share_diff['Transport Type'].unique():
    #ignore nonspecified
    if transport_type == 'nonspecified':
        continue
    for scenario in model_output_8th_with_sales_share_diff['Scenario'].unique():
        #subset the data
        data = model_output_8th_with_sales_share_diff[(model_output_8th_with_sales_share_diff['Transport Type']==transport_type) & (model_output_8th_with_sales_share_diff['Scenario']==scenario)]
        #create title
        title = transport_type + ' ' + scenario + ' sales share diff'
        #plot the data
        fig = px.line(data, x='Year', y='diff', color='Vehicle Type', facet_col='Economy', facet_col_wrap=7, line_dash='Drive')
        fig.update_layout(title_text=transport_type + ' ' + scenario)
        
        plotly.offline.plot(fig, filename=config.root_dir + '\\' + 'plotting_output\\8th_edition\\archive\\' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
#%%

#and also plot the prev_sales_share data
#do a for loop for each transport type and scenario,
#do a line chart of diff in sales share by year, vehicle type, drive type and facet by economy
for transport_type in prev_sales_share['Transport Type'].unique():
    #ignore nonspecified
    if transport_type == 'nonspecified':
        continue
    for scenario in prev_sales_share['Scenario'].unique():
        #subset the data
        data = prev_sales_share[(prev_sales_share['Transport Type']==transport_type) & (prev_sales_share['Scenario']==scenario)]
        #create title
        title = transport_type + ' ' + scenario + ' sales share'
        #plot the data
        fig = px.line(data, x='Year', y='Vehicle_sales_share', color='Vehicle Type', facet_col='Economy', facet_col_wrap=7, line_dash='Drive')
        fig.update_layout(title_text=transport_type + ' ' + scenario)
        
        plotly.offline.plot(fig, filename=config.root_dir + '\\' + 'plotting_output\\8th_edition\\archive\\' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
        
# %%
