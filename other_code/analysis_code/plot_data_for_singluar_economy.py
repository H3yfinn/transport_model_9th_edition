#take in detailed output data and print out any useful metrics/statisitcs to summarise the reults of the model. the intention is that the output willbe easy to view through the command line, and that the output will be saved to a file for later viewing.

#%%
#set working directory as one folder back so that config works
import os
import sys
import re
sys.path.append(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
###IMPORT GLOBAL VARIABLES FROM config.py
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
#economys:'01_AUS', '02_BD', '03_CDA', '04_CHL', '05_PRC', '06_HKC',
    #    '07_INA', '08_JPN', '09_ROK', '10_MAS', '11_MEX', '12_NZ',
    #    '13_PNG', '14_PE', '15_PHL', '16_RUS', '17_SGP', '18_CT', '19_THA',
    #    '20_USA', '21_VN'
economy =  '19_THA'
AUTO_OPEN_PLOTLY_GRAPHS = True
#%%

#load data in
model_output_all = pd.read_csv(root_dir + '/' + 'output_data/model_output/{}'.format(config.model_output_file_name))
model_output_detailed = pd.read_csv(root_dir + '/' + 'output_data/model_output_detailed/{}'.format(config.model_output_file_name))
model_output_with_fuels = pd.read_csv(root_dir + '/' + 'output_data/model_output_with_fuels/{}'.format(config.model_output_file_name))
model_output_8th = pd.read_csv(root_dir + '/' + 'intermediate_data/activity_efficiency_energy_road_stocks.csv')

#filter for only ref scenario
model_output_all = model_output_all[model_output_all['Scenario'] == 'Reference']
model_output_detailed = model_output_detailed[model_output_detailed['Scenario'] == 'Reference']
model_output_with_fuels = model_output_with_fuels[model_output_with_fuels['Scenario'] == 'Reference']
model_output_8th = model_output_8th[model_output_8th['Scenario'] == 'Reference']

#%%
#check we have graph folder for the economy we are interested in
if not os.path.exists(root_dir + '/' + 'plotting_output/{}'.format(economy)):
    os.mkdir('plotting_output/{}'.format(economy))
    os.mkdir('plotting_output/{}/static/'.format(economy))
else:
    print('folder already exists')

#filter for data from that economy
model_output_all = model_output_all[model_output_all['Economy']==economy]
model_output_detailed = model_output_detailed[model_output_detailed['Economy']==economy]
model_output_8th = model_output_8th[model_output_8th['Economy']==economy]
model_output_with_fuels = model_output_with_fuels[model_output_with_fuels['Economy']==economy]
#%%
#plot energy use by fuel type
model_output_with_fuels_plot = model_output_with_fuels.groupby(['Fuel','Year']).sum().reset_index()

title='Energy use by fuel type for {}'.format(economy)
#plot using plotly
fig = px.line(model_output_with_fuels_plot, x="Year", y="Energy", color="Fuel", title=title)

plotly.offline.plot(fig, filename='./plotting_output/{}/'.format(economy) + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/{}/static/".format(economy) + title + '.png', scale=1, width=2000, height=800)

#%%

#plot the total energy use by vehicle type / drive type combination sep by transport type
#first need to create a new column that combines the vehicle type and drive type
model_output_detailed['vehicle_type_drive_type'] = model_output_detailed['Vehicle Type'] + ' ' + model_output_detailed['Drive']

title='Energy use by vehicle type drive type combination, sep by transport type for {}'.format(economy)
#plot using plotly
fig = px.line(model_output_detailed, x="Year", y="Energy", facet_col="Transport Type", facet_col_wrap=2, color="vehicle_type_drive_type", title=title)

plotly.offline.plot(fig, filename='./plotting_output/{}/'.format(economy) + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/{}/static/".format(economy) + title + '.png', scale=1, width=2000, height=800)

#%%
#plot travel km by vehicle type / drive type combination
title = 'Travel km by vehicle type drive type combination, sep by transport type for {}'.format(economy)
#plot using plotly
fig = px.line(model_output_detailed, x="Year", y="Travel_km", facet_col="Transport Type", facet_col_wrap=2, color="vehicle_type_drive_type", title=title)

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

#%%
#plot activity by vehicle type / drive type combination
title = 'Activity by vehicle type drive type combination, sep by transport type for {}'.format(economy)
#plot using plotly
fig = px.line(model_output_detailed, x="Year", y="Activity", facet_col="Transport Type", facet_col_wrap=2, color="vehicle_type_drive_type", title=title)

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

#%%
#plot efficiency over time by vehicle type / drive type combination
title = 'Efficiency by vehicle type drive type combination, sep by transport type for {}'.format(economy)
#plot using plotly
fig = px.line(model_output_detailed, x="Year", y="Efficiency", facet_col="Transport Type", facet_col_wrap=2, color="vehicle_type_drive_type", title=title)

plotly.offline.plot(fig, filename='./plotting_output/{}/'.format(economy) + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/{}/static/".format(economy) + title + '.png', scale=1, width=2000, height=800)

#%%
#plot stocks over time by vehicle type / drive type combination
title = 'Stocks by vehicle type drive type combination, sep by transport type for {}'.format(economy)
#plot using plotly
fig = px.line(model_output_detailed, x="Year", y="Stocks", facet_col="Transport Type", facet_col_wrap=2, color="vehicle_type_drive_type", title=title)

plotly.offline.plot(fig, filename='./plotting_output/{}/'.format(economy) + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/{}/static/".format(economy) + title + '.png', scale=1, width=2000, height=800)

#%%
#plot sales share over time by vehicle type / drive type combination
title = 'Sales share by vehicle type drive type combination, sep by transport type for {}'.format(economy)
#plot using plotly
fig = px.line(model_output_detailed, x="Year", y="Vehicle_sales_share", facet_col="Transport Type", facet_col_wrap=2, color="vehicle_type_drive_type", title=title)

plotly.offline.plot(fig, filename='./plotting_output/{}/'.format(economy) + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/{}/static/".format(economy) + title + '.png', scale=1, width=2000, height=800)

#%%
#energy use by vehicle type fuel type combination
title = 'Energy use by vehicle type fuel type combination, sep by transport type for {}'.format(economy)

#remove drive type from model_output_with_fuels
model_output_with_fuels_no_drive = model_output_with_fuels.drop(columns=['Drive'])
#sum
model_output_with_fuels_no_drive = model_output_with_fuels_no_drive.groupby(['Economy','Vehicle Type','Transport Type','Fuel','Year']).sum().reset_index()

#create col for vehicle type and fuel type combination
model_output_with_fuels_no_drive['vehicle_type_fuel_type'] = model_output_with_fuels_no_drive['Vehicle Type'] + ' ' + model_output_with_fuels_no_drive['Fuel']
#plot using plotly
fig = px.line(model_output_with_fuels_no_drive, x="Year", y="Energy", facet_col="Transport Type", facet_col_wrap=2, color="vehicle_type_fuel_type", title=title)

plotly.offline.plot(fig, filename='./plotting_output/{}/'.format(economy) + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/{}/static/".format(economy) + title + '.png', scale=1, width=2000, height=800)

#%%
#energy use by vehicle type fuel type combination
title = 'Energy use by Drive fuel type combination, sep by transport type for {}'.format(economy)

#remove drive type from model_output_with_fuels
model_output_with_fuels_no_v = model_output_with_fuels.drop(columns=['Vehicle Type'])
#sum
model_output_with_fuels_no_v = model_output_with_fuels_no_v.groupby(['Economy','Drive','Transport Type','Fuel','Year']).sum().reset_index()

#create col for vehicle type and fuel type combination
model_output_with_fuels_no_v['drive_fuel_type'] = model_output_with_fuels_no_v['Drive'] + ' ' + model_output_with_fuels_no_v['Fuel']
#plot using plotly
fig = px.line(model_output_with_fuels_no_v, x="Year", y="Energy", facet_col="Transport Type", facet_col_wrap=2, color="drive_fuel_type", title=title)

plotly.offline.plot(fig, filename='./plotting_output/{}/'.format(economy) + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/{}/static/".format(economy) + title + '.png', scale=1, width=2000, height=800)

#%%









