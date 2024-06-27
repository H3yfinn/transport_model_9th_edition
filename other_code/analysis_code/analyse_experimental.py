
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

# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook
import matplotlib.pyplot as plt
plt.rcParams['figure.facecolor'] = 'w'


import plotly
import plotly.express as px
pd.options.plotting.backend = "plotly"#set pandas backend to plotly plotting instead of matplotlib
import plotly.io as pio
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook

#%%

#load data in
model_output_all = pd.read_csv('output_data/model_output/{}'.format(config.model_output_file_name))
model_output_detailed = pd.read_csv('output_data/model_output_detailed/{}'.format(config.model_output_file_name))

#FILTER FOR SCENARIO OF INTEREST
#this should be temporary as the scenario should be passed in as a parameter through config if it is useed elsewhere
SCENARIO_OF_INTEREST = 'Reference'
model_output_all = model_output_all[model_output_all['Scenario']==SCENARIO_OF_INTEREST]

#%%
#show the ratio of BEVs and PHEVs to ICEs by year, and economy (3d plot)
model_output_detailed_ratio_drive = model_output_detailed.groupby(['Year', 'Economy', 'Drive'])['Stocks'].sum().reset_index()

model_output_detailed_ratio_drive = model_output_detailed_ratio_drive.pivot(index=['Year', 'Economy'], columns='Drive', values='Stocks')

#replace any nan's with 0's
model_output_detailed_ratio_drive = model_output_detailed_ratio_drive.fillna(0)

model_output_detailed_ratio_drive['BEV_ICE_ratio'] = model_output_detailed_ratio_drive['bev'] / (model_output_detailed_ratio_drive['bev'] + model_output_detailed_ratio_drive['g'] + model_output_detailed_ratio_drive['d'])

model_output_detailed_ratio_drive['PHEV_ICE_ratio'] = (model_output_detailed_ratio_drive['phevg'] +  model_output_detailed_ratio_drive['phevd']) / (model_output_detailed_ratio_drive['phevg'] +  model_output_detailed_ratio_drive['phevd'] + model_output_detailed_ratio_drive['g'] + model_output_detailed_ratio_drive['d'])

model_output_detailed_ratio_drive = model_output_detailed_ratio_drive[['BEV_ICE_ratio', 'PHEV_ICE_ratio']]

model_output_detailed_ratio_drive = model_output_detailed_ratio_drive.reset_index()

#%%
title = 'Experiemental 3d plot of ratios for BEV to ICE and PHEV to ICE'

fig = px.line_3d(model_output_detailed_ratio_drive, x="BEV_ICE_ratio", y="PHEV_ICE_ratio", z="Year", color='Economy')
fig.update_xaxes(range=[0, 1])
fig.update_yaxes(range=[0, 1])

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

#%%
#lets take a look at this for Vehicle_sales_share instead of stocks

#show the ratio of BEVs and PHEVs to ICEs by year, and economy (3d plot)
model_output_detailed_ratio_drive = model_output_detailed.groupby(['Year', 'Economy', 'Drive'])['Vehicle_sales_share'].sum().reset_index()

model_output_detailed_ratio_drive = model_output_detailed_ratio_drive.pivot(index=['Year', 'Economy'], columns='Drive', values='Vehicle_sales_share')

#replace any nan's with 0's
model_output_detailed_ratio_drive = model_output_detailed_ratio_drive.fillna(0)

model_output_detailed_ratio_drive['BEV_ICE_ratio'] = model_output_detailed_ratio_drive['bev'] / (model_output_detailed_ratio_drive['bev'] + model_output_detailed_ratio_drive['g'] + model_output_detailed_ratio_drive['d'])

model_output_detailed_ratio_drive['PHEV_ICE_ratio'] = (model_output_detailed_ratio_drive['phevg'] +  model_output_detailed_ratio_drive['phevd']) / (model_output_detailed_ratio_drive['phevg'] +  model_output_detailed_ratio_drive['phevd'] + model_output_detailed_ratio_drive['g'] + model_output_detailed_ratio_drive['d'])

model_output_detailed_ratio_drive = model_output_detailed_ratio_drive[['BEV_ICE_ratio', 'PHEV_ICE_ratio']]

model_output_detailed_ratio_drive = model_output_detailed_ratio_drive.reset_index()

#%%
title = 'Experiemental 3d plot of sales share ratios for BEV to ICE and PHEV to ICE'

fig = px.line_3d(model_output_detailed_ratio_drive, x="BEV_ICE_ratio", y="PHEV_ICE_ratio", z="Year", color='Economy')
fig.update_xaxes(range=[0, 1])
fig.update_yaxes(range=[0, 1])

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

#%%
#how about a graph which combines the two above so we can see the relationship between the sales and stock shares
