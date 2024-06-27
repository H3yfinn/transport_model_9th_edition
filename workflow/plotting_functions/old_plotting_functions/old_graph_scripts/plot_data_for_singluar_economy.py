#take in detailed output data and print out any useful metrics/statisitcs to summarise the reults of the model. the intention is that the output willbe easy to view through the command line, and that the output will be saved to a file for later viewing.
#also make it so you can plot data for all of apec by creating an economy called 'all'
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
economy =  '12_NZ'#19_THA'
AUTO_OPEN_PLOTLY_GRAPHS = True

#%%

#load data in
model_output_all = pd.read_csv('output_data/model_output/{}'.format(config.model_output_file_name))
model_output_detailed = pd.read_csv('output_data/model_output_detailed/{}'.format(config.model_output_file_name))
model_output_with_fuels = pd.read_csv('output_data/model_output_with_fuels/{}'.format(config.model_output_file_name))
model_output_8th = pd.read_csv('intermediate_data/activity_energy_road_stocks.csv')
#%%
#create 'all' economy by grouping by all categories but economy and summing
#'Date', 'Scenario', 'Transport Type', 'Vehicle Type',
#    'Drive', 'Medium'
model_output_all_APEC = model_output_all.groupby(['Date', 'Scenario', 'Transport Type', 'Vehicle Type',
       'Drive', 'Medium']).sum().reset_index()
model_output_detailed_APEC = model_output_detailed.groupby(['Date',  'Vehicle Type', 'Medium', 'Transport Type', 'Drive',
       'Scenario', 'Frequency']).sum().reset_index()
model_output_with_fuels_APEC = model_output_with_fuels.groupby(['Date','Scenario', 'Transport Type', 'Vehicle Type',
       'Drive', 'Medium', 'Fuel']).sum().reset_index()
model_output_8th_APEC = model_output_8th.groupby(['Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Year','Scenario']).sum().reset_index()
#create economy called 'all' and append to the dataframes
model_output_all_APEC['Economy'] = 'all'
model_output_detailed_APEC['Economy'] = 'all'
model_output_with_fuels_APEC['Economy'] = 'all'
model_output_8th_APEC['Economy'] = 'all'

#concat to the dataframes
model_output_all = pd.concat([model_output_all, model_output_all_APEC])
model_output_detailed = pd.concat([model_output_detailed, model_output_detailed_APEC])
model_output_with_fuels = pd.concat([model_output_with_fuels, model_output_with_fuels_APEC])
model_output_8th = pd.concat([model_output_8th, model_output_8th_APEC])

#%%

#filter for only ref scenario
model_output_all = model_output_all[model_output_all['Scenario'] == 'Reference']
model_output_detailed = model_output_detailed[model_output_detailed['Scenario'] == 'Reference']
model_output_with_fuels = model_output_with_fuels[model_output_with_fuels['Scenario'] == 'Reference']
model_output_8th = model_output_8th[model_output_8th['Scenario'] == 'Reference']

#%%
#check we have graph folder for the economy we are interested in
if not os.path.exists('plotting_output/{}'.format(economy)):
    os.mkdir('plotting_output/{}'.format(economy))
    os.mkdir('plotting_output/{}/static/'.format(economy))
else:
    print('folder already exists')

#filter for data from that economy
model_output_all = model_output_all[model_output_all['Economy']==economy]
model_output_detailed = model_output_detailed[model_output_detailed['Economy']==economy]
model_output_8th = model_output_8th[model_output_8th['Economy']==economy]
model_output_with_fuels = model_output_with_fuels[model_output_with_fuels['Economy']==economy]

#set nans to '' so that they dont cause issues with the plotly graphs
model_output_all = model_output_all.fillna('')
model_output_detailed = model_output_detailed.fillna('')
model_output_8th = model_output_8th.fillna('')
model_output_with_fuels = model_output_with_fuels.fillna('')

#where medium is not road then set drive and vehicle type to medium, so that we can plot them on the same graph
model_output_all.loc[model_output_all['Medium']!='road', 'Drive'] = model_output_all['Medium']
model_output_all.loc[model_output_all['Medium']!='road', 'Vehicle Type'] = model_output_all['Medium']
model_output_detailed.loc[model_output_detailed['Medium']!='road', 'Drive'] = model_output_detailed['Medium']
model_output_detailed.loc[model_output_detailed['Medium']!='road', 'Vehicle Type'] = model_output_detailed['Medium']
model_output_with_fuels.loc[model_output_with_fuels['Medium']!='road', 'Drive'] = model_output_with_fuels['Medium']
model_output_with_fuels.loc[model_output_with_fuels['Medium']!='road', 'Vehicle Type'] = model_output_with_fuels['Medium']

#%%

# #stack passenger_km and freight_tonne_km, as well as Occupancy and load. This is so that we can plot them on the same graph
# passenger =model_output_all[model_output_all['Transport Type']=='passenger']
# #rename passenger_km to Activity and Occupancy to Occupancy_Load
# passenger = passenger.rename(columns={'passenger_km':'Activity', 'Occupancy':'Occupancy_Load'})
# freight =model_output_all[model_output_all['Transport Type']=='freight']
# #rename freight_tonne_km to Activity and load to Occupancy_Load
# freight = freight.rename(columns={'freight_tonne_km':'Activity', 'load':'Occupancy_Load'})
# #combine passenger and freight
# model_output_all_stacked = pd.concat([passenger, freight])
# #drop passenger_km and freight_tonne_km and Occupancy and load
# model_output_all_stacked = model_output_all_stacked.drop(columns=['passenger_km', 'freight_tonne_km', 'Occupancy', 'load'])

#do the process above for each df
df_stacked_list = []
for df in [model_output_all, model_output_detailed, model_output_8th, model_output_with_fuels]:
    passenger =df[df['Transport Type']=='passenger']
    #rename passenger_km to Activity and Occupancy to Occupancy_Load
    passenger = passenger.rename(columns={'passenger_km':'Activity', 'Occupancy':'Occupancy_Load'})
    freight =df[df['Transport Type']=='freight']
    #rename freight_tonne_km to Activity and load to Occupancy_Load
    freight = freight.rename(columns={'freight_tonne_km':'Activity', 'Load':'Occupancy_Load'})
    #combine passenger and freight
    df_stacked = pd.concat([passenger, freight])
    #drop passenger_km and freight_tonne_km and Occupancy and load if the
    try:
        df_stacked = df_stacked.drop(columns=['passenger_km', 'freight_tonne_km', 'Occupancy', 'Load'])
    except:
        try:
            df_stacked = df_stacked.drop(columns=['passenger_km', 'freight_tonne_km'])
        except:
            pass
    df_stacked = df_stacked.fillna('')
    #add to list
    df_stacked_list.append(df_stacked)
#sep the stacked dfs 
model_output_all, model_output_detailed, model_output_8th, model_output_with_fuels = df_stacked_list

#%%
#plot energy use by fuel type
model_output_with_fuels_plot = model_output_with_fuels.groupby(['Fuel','Date']).sum().reset_index()

title='Energy use by fuel type for {}'.format(economy)
#plot using plotly
fig = px.line(model_output_with_fuels_plot, x="Date", y="Energy", color="Fuel", title=title)

plotly.offline.plot(fig, filename='./plotting_output/{}/'.format(economy) + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/{}/static/".format(economy) + title + '.png', scale=1, width=2000, height=800)

# #%%

# #plot the total energy use by vehicle type / drive type combination sep by transport type
# #first need to create a new column that combines the vehicle type and drive type
# model_output_detailed['vehicle_type_drive_type'] = model_output_detailed['Vehicle Type'] + ' ' + model_output_detailed['Drive']

# title='Energy use by vehicle type drive type combination, sep by transport type for {}'.format(economy)
# #plot using plotly
# fig = px.line(model_output_detailed, x="Date", y="Energy", facet_col="Transport Type", facet_col_wrap=2, color="vehicle_type_drive_type", title=title)

# plotly.offline.plot(fig, filename='./plotting_output/{}/'.format(economy) + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/{}/static/".format(economy) + title + '.png', scale=1, width=2000, height=800)

# #%%
# #plot travel km by vehicle type / drive type combination
# title = 'Travel km by vehicle type drive type combination, sep by transport type for {}'.format(economy)
# #plot using plotly
# fig = px.line(model_output_detailed, x="Date", y="Travel_km", facet_col="Transport Type", facet_col_wrap=2, color="vehicle_type_drive_type", title=title)

# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

# #%%
# #plot activity by vehicle type / drive type combination
# title = 'Activity by vehicle type drive type combination, sep by transport type for {}'.format(economy)
# #plot using plotly
# fig = px.line(model_output_detailed, x="Date", y="Activity", facet_col="Transport Type", facet_col_wrap=2, color="vehicle_type_drive_type", title=title)

# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

# #%%
# #plot efficiency over time by vehicle type / drive type combination
# title = 'Efficiency by vehicle type drive type combination, sep by transport type for {}'.format(economy)
# #plot using plotly
# fig = px.line(model_output_detailed, x="Date", y="Efficiency", facet_col="Transport Type", facet_col_wrap=2, color="vehicle_type_drive_type", title=title)

# plotly.offline.plot(fig, filename='./plotting_output/{}/'.format(economy) + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/{}/static/".format(economy) + title + '.png', scale=1, width=2000, height=800)

# #%%
# #plot stocks over time by vehicle type / drive type combination
# title = 'Stocks by vehicle type drive type combination, sep by transport type for {}'.format(economy)
# #plot using plotly
# fig = px.line(model_output_detailed, x="Date", y="Stocks", facet_col="Transport Type", facet_col_wrap=2, color="vehicle_type_drive_type", title=title)

# plotly.offline.plot(fig, filename='./plotting_output/{}/'.format(economy) + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/{}/static/".format(economy) + title + '.png', scale=1, width=2000, height=800)

# #%%
# #plot sales share over time by vehicle type / drive type combination
# title = 'Sales share by vehicle type drive type combination, sep by transport type for {}'.format(economy)
# #plot using plotly
# fig = px.line(model_output_detailed, x="Date", y="Vehicle_sales_share", facet_col="Transport Type", facet_col_wrap=2, color="vehicle_type_drive_type", title=title)

# plotly.offline.plot(fig, filename='./plotting_output/{}/'.format(economy) + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/{}/static/".format(economy) + title + '.png', scale=1, width=2000, height=800)

#%%
#energy use by vehicle type fuel type combination
title = 'Energy use by vehicle type fuel type combination, sep by transport type for {}'.format(economy)

#remove drive type from model_output_with_fuels
model_output_with_fuels_no_drive = model_output_with_fuels.drop(columns=['Drive'])
#sum
model_output_with_fuels_no_drive = model_output_with_fuels_no_drive.groupby(['Economy','Vehicle Type','Transport Type','Fuel','Date']).sum().reset_index()

#create col for vehicle type and fuel type combination
model_output_with_fuels_no_drive['vehicle_type_fuel_type'] = model_output_with_fuels_no_drive['Vehicle Type'] + ' ' + model_output_with_fuels_no_drive['Fuel']
#plot using plotly
fig = px.line(model_output_with_fuels_no_drive, x="Date", y="Energy", facet_col="Transport Type", facet_col_wrap=2, color="vehicle_type_fuel_type", title=title)

plotly.offline.plot(fig, filename='./plotting_output/{}/'.format(economy) + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/{}/static/".format(economy) + title + '.png', scale=1, width=2000, height=800)

#%%
#energy use by vehicle type fuel type combination
title = 'Energy use by Drive fuel type combination, sep by transport type for {}'.format(economy)

#remove drive type from model_output_with_fuels
model_output_with_fuels_no_v = model_output_with_fuels.drop(columns=['Vehicle Type'])
#sum
model_output_with_fuels_no_v = model_output_with_fuels_no_v.groupby(['Economy','Drive','Transport Type','Fuel','Date']).sum().reset_index()

#create col for vehicle type and fuel type combination
model_output_with_fuels_no_v['drive_fuel_type'] = model_output_with_fuels_no_v['Drive'] + ' ' + model_output_with_fuels_no_v['Fuel']
#plot using plotly
fig = px.line(model_output_with_fuels_no_v, x="Date", y="Energy", facet_col="Transport Type", facet_col_wrap=2, color="drive_fuel_type", title=title)

plotly.offline.plot(fig, filename='./plotting_output/{}/'.format(economy) + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/{}/static/".format(economy) + title + '.png', scale=1, width=2000, height=800)

# #%%
# #energy use by medium, transport type combination
# title = 'Energy use by medium, transport type combination for {}'.format(economy)

# #remove drive type from model_output_with_fuels
# model_output_with_fuels_no_v = model_output_with_fuels.drop(columns=['Vehicle Type', 'Drive'])
# #sum
# model_output_with_fuels_no_v = model_output_with_fuels_no_v.groupby(['Economy','Transport Type','Fuel','Medium','Date']).sum().reset_index()

# #create col for medium and fuel type combination
# model_output_with_fuels_no_v['medium_fuel_type'] = model_output_with_fuels_no_v['Medium'] + ' ' + model_output_with_fuels_no_v['Fuel']
# #plot using plotly
# fig = px.line(model_output_with_fuels_no_v, x="Date", y="Energy", facet_col="Transport Type", facet_col_wrap=2, color="medium_fuel_type", title=title)

# plotly.offline.plot(fig, filename='./plotting_output/{}/'.format(economy) + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/{}/static/".format(economy) + title + '.png', scale=1, width=2000, height=800)

# #%%
# #passenger km by medium, transport type combination
# title = 'Activity by medium, transport type combination for {}'.format(economy)

# model_output_detailed_medium_activity = model_output_detailed.groupby(['Economy','Transport Type','Medium','Date']).sum().reset_index()

# #create col for medium and fuel type combination
# model_output_detailed_medium_activity['medium_activity'] = model_output_detailed_medium_activity['Medium'] + ' ' + 'activity'
# #plot using plotly
# fig = px.line(model_output_detailed_medium_activity, x="Date", y="Activity", facet_col="Transport Type", facet_col_wrap=2, color="medium_activity", title=title)
# #make y axis independent
# fig.update_yaxes(matches=None)
# #show y axis on both plots
# fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))

# plotly.offline.plot(fig, filename='./plotting_output/{}/'.format(economy) + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/{}/static/".format(economy) + title + '.png', scale=1, width=2000, height=800)


#%%

#plot activity growth for the economy to help understand trend:
activity_growth = pd.read_csv('intermediate_data/model_inputs/activity_growth.csv')
#filter for economy
activity_growth = activity_growth[activity_growth['Economy'] == economy]
#plot using plotly
fig = px.line(activity_growth, x="Date", y="Activity_growth",color ='Scenario', title='Activity growth for {}'.format(economy))

plotly.offline.plot(fig, filename='./plotting_output/{}/'.format(economy) + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/{}/static/".format(economy) + title + '.png', scale=1, width=2000, height=800)
#%%




# %%





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

import plotly
import plotly.express as px
pd.options.plotting.backend = "plotly"#set pandas backend to plotly plotting instead of matplotlib
import plotly.io as pio
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook
#%%

#load data in
model_output_all = pd.read_csv('output_data/model_output/{}'.format(config.model_output_file_name))
model_output_detailed = pd.read_csv('output_data/model_output_detailed/{}'.format(config.model_output_file_name))
# change_dataframe_aggregation = pd.read_csv('intermediate_data/road_model/change_dataframe_aggregation.csv')
model_output_with_fuels = pd.read_csv('output_data/model_output_with_fuels/{}'.format(config.model_output_file_name))
model_output_8th = pd.read_csv('intermediate_data/activity_energy_road_stocks.csv')
#%%
#economys:'01_AUS', '02_BD', '03_CDA', '04_CHL', '05_PRC', '06_HKC',
    #    '07_INA', '08_JPN', '09_ROK', '10_MAS', '11_MEX', '12_NZ',
    #    '13_PNG', '14_PE', '15_PHL', '16_RUS', '17_SGP', '18_CT', '19_THA',
    #    '20_USA', '21_VN'
economy =  '12_NZ'#19_THA'
AUTO_OPEN_PLOTLY_GRAPHS = True
#%%
#create 'all' economy by grouping by all categories but economy and summing
#'Date', 'Scenario', 'Transport Type', 'Vehicle Type',
#    'Drive', 'Medium'
model_output_all_APEC = model_output_all.groupby(['Date', 'Scenario', 'Transport Type', 'Vehicle Type',
       'Drive', 'Medium']).sum().reset_index()
model_output_detailed_APEC = model_output_detailed.groupby(['Date',  'Vehicle Type', 'Medium', 'Transport Type', 'Drive',
       'Scenario', 'Frequency']).sum().reset_index()
model_output_with_fuels_APEC = model_output_with_fuels.groupby(['Date','Scenario', 'Transport Type', 'Vehicle Type',
       'Drive', 'Medium', 'Fuel']).sum().reset_index()
model_output_8th_APEC = model_output_8th.groupby(['Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Year','Scenario']).sum().reset_index()
#create economy called 'all' and append to the dataframes
model_output_all_APEC['Economy'] = 'all'
model_output_detailed_APEC['Economy'] = 'all'
model_output_with_fuels_APEC['Economy'] = 'all'
model_output_8th_APEC['Economy'] = 'all'

#concat to the dataframes
model_output_all = pd.concat([model_output_all, model_output_all_APEC])
model_output_detailed = pd.concat([model_output_detailed, model_output_detailed_APEC])
model_output_with_fuels = pd.concat([model_output_with_fuels, model_output_with_fuels_APEC])
model_output_8th = pd.concat([model_output_8th, model_output_8th_APEC])

#copy data so we ahve it for all economies avaialble:
model_output_all_all_economies = model_output_all.copy()
model_output_detailed_all_economies = model_output_detailed.copy()
model_output_with_fuels_all_economies = model_output_with_fuels.copy()
model_output_8th_all_economies = model_output_8th.copy()

#filter for data from that economy
model_output_all = model_output_all[model_output_all['Economy']==economy]
model_output_detailed = model_output_detailed[model_output_detailed['Economy']==economy]
model_output_8th = model_output_8th[model_output_8th['Economy']==economy]
model_output_with_fuels = model_output_with_fuels[model_output_with_fuels['Economy']==economy]
#%%
#FILTER FOR SCENARIO OF INTEREST
#this should be temporary as the scenario should be passed in as a parameter through config if it is useed elsewhere

model_output_all = model_output_all[model_output_all['Scenario']==config.SCENARIO_OF_INTEREST]
model_output_detailed = model_output_detailed[model_output_detailed['Scenario']==config.SCENARIO_OF_INTEREST]
change_dataframe_aggregation = change_dataframe_aggregation[change_dataframe_aggregation['Scenario']==config.SCENARIO_OF_INTEREST]
model_output_with_fuels = model_output_with_fuels[model_output_with_fuels['Scenario']==config.SCENARIO_OF_INTEREST]

#%%
#set nans to '' so that they dont cause issues with the plotly graphs
model_output_all = model_output_all.fillna('')
model_output_detailed = model_output_detailed.fillna('')
model_output_8th = model_output_8th.fillna('')
model_output_with_fuels = model_output_with_fuels.fillna('')

#where medium is not road then set drive and vehicle type to medium, so that we can plot them on the same graph
model_output_all.loc[model_output_all['Medium']!='road', 'Drive'] = model_output_all['Medium']
model_output_all.loc[model_output_all['Medium']!='road', 'Vehicle Type'] = model_output_all['Medium']
model_output_detailed.loc[model_output_detailed['Medium']!='road', 'Drive'] = model_output_detailed['Medium']
model_output_detailed.loc[model_output_detailed['Medium']!='road', 'Vehicle Type'] = model_output_detailed['Medium']
model_output_with_fuels.loc[model_output_with_fuels['Medium']!='road', 'Drive'] = model_output_with_fuels['Medium']
model_output_with_fuels.loc[model_output_with_fuels['Medium']!='road', 'Vehicle Type'] = model_output_with_fuels['Medium']
stack_ttype = False
if stack_ttype:
    # #stack passenger_km and freight_tonne_km, as well as Occupancy and load. This is so that we can plot them on the same graph
    #do the process above for each df
    df_stacked_list = []
    for df in [model_output_all, model_output_detailed, model_output_8th, model_output_with_fuels]:
        passenger =df[df['Transport Type']=='passenger']
        #rename passenger_km to Activity and Occupancy to Occupancy_Load
        passenger = passenger.rename(columns={'passenger_km':'Activity', 'Occupancy':'Occupancy_Load'})
        freight =df[df['Transport Type']=='freight']
        #rename freight_tonne_km to Activity and load to Occupancy_Load
        freight = freight.rename(columns={'freight_tonne_km':'Activity', 'Load':'Occupancy_Load'})
        #combine passenger and freight
        df_stacked = pd.concat([passenger, freight])
        #drop passenger_km and freight_tonne_km and Occupancy and load if the
        try:
            df_stacked = df_stacked.drop(columns=['passenger_km', 'freight_tonne_km', 'Occupancy', 'Load'])
        except:
            try:
                df_stacked = df_stacked.drop(columns=['passenger_km', 'freight_tonne_km'])
            except:
                pass
        df_stacked = df_stacked.fillna('')
        #add to list
        df_stacked_list.append(df_stacked)
    #sep the stacked dfs 
    model_output_all_stacked, model_output_detailed_stacked, model_output_8th_stacked, model_output_with_fuels_stacked = df_stacked_list
#%%
#plot data by vehicle type and drive:
#plot energy use by vehicle type and drive:
#plot activity by vehicle type by drive
#plot stocks by vehicle type by drive

#plot energy use by economy by fuel type by drive
#plot energy use by economy by fuel type by vehicle type

#bascially we want to plot every column using economy as the facet then a mix of transport type, drive, vehicle type, medium and fuel as the categories. So we will create a function that does this:

# def plot_line_for_single_economy(df, color_categories, y_column,title,line_dash_categories=None,  x_column='Date', save_folder='single_economy_graphs', facet_col_wrap=2, facet_col ='Transport Type', hover_name = None, hover_data = None, log_y = False, log_x = False, y_axis_title = None, x_axis_title = None, width = 2000, height = 800,AUTO_OPEN_PLOTLY_GRAPHS=False, independent_y_axis = True):
        
#     #set color and line dash categories to list even if they are just one category
#     if type(color_categories) != list:
#         color_categories = [color_categories]
#     if type(line_dash_categories) != list and line_dash_categories != None:
#         line_dash_categories = [line_dash_categories]
#     # convert color and likne dash categorties to one col each seperated by a hyphen
#     color = '-'.join(color_categories)
#     if line_dash_categories != None:
#         line_dash = '-'.join(line_dash_categories)
#         #add a column for the line dash
#         df[line_dash] = df[line_dash_categories].apply(lambda x: '-'.join(x), axis=1)
#     #add a column for the color
#     df[color] = df[color_categories].apply(lambda x: '-'.join(x), axis=1)

#     #if hover name is none then set it to the color+line_dash
#     if hover_name == None:
#         if line_dash_categories == None:
#             hover_name = color
#         else:
#             hover_name = color + '-' + line_dash
#             #insert hovername into the dataframe as a column
#             df[hover_name] = df[color].astype(str) + '-' + df[line_dash].astype(str)

#     #if hover data is none then set it to the y column
#     if hover_data == None:
#         hover_data = [y_column]
#     #if y axis title is none then set it to the y column
#     if y_axis_title == None:
#         y_axis_title = y_column
#     #if x axis title is none then set it to the x column
#     if x_axis_title == None:
#         x_axis_title = x_column
#     #plot energy use by drive type
#     #title = 'Energy use by drive type'
#     #model_output_all_drive = model_output_all.groupby(['Date', 'Drive', 'Economy']).sum().reset_index()
#     #if tehre are any '' in the y column then drop them
#     df = df[df[y_column] != '']

#     #checkl that the folders wqe save to exist
#     if not os.path.exists(f'./plotting_output/{save_folder}'):
#         os.makedirs(f'./plotting_output/{save_folder}')
#     #create static folder too
#     if not os.path.exists(f'./plotting_output/{save_folder}/static'):
#         os.makedirs(f'./plotting_output/{save_folder}/static')

#     if line_dash_categories != None:
#         df = df.groupby([x_column, facet_col,color, line_dash])[y_column].sum().reset_index()
#         fig = px.line(df, x="Date", y=y_column, color=color, facet_col_wrap=facet_col_wrap, facet_col =facet_col, hover_name = hover_name, hover_data = hover_data, log_y = log_y, log_x = log_x, title=title)
#         if independent_y_axis:
#             fig.update_yaxes(matches=None)
#             #show y axis on both plots
#             fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
#         #do y_axis_title and x_axis_title
#         fig.update_layout(yaxis_title=y_axis_title, xaxis_title=x_axis_title)

#         plotly.offline.plot(fig, filename=f'./plotting_output/{save_folder}' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
#         fig.write_image(f"./plotting_output/{save_folder}/static/" + title + '.png', scale=1, width=width, height=height)
#     else:
#         df = df.groupby([x_column, facet_col,color])[y_column].sum().reset_index()
#         fig = px.line(df, x="Date", y=y_column, color=color, facet_col_wrap=facet_col_wrap, facet_col =facet_col, hover_name = hover_name, hover_data = hover_data, log_y = log_y, log_x = log_x, title=title)
#         if independent_y_axis:
#             fig.update_yaxes(matches=None)
#             #show y axis on both plots
#             fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
#         #do y_axis_title and x_axis_title
#         fig.update_layout(yaxis_title=y_axis_title, xaxis_title=x_axis_title)
#         plotly.offline.plot(fig, filename=f'./plotting_output/{save_folder}' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
#         fig.write_image(f"./plotting_output/{save_folder}/static/" + title + '.png', scale=1, width=width, height=height)


# #%%
# AUTO_OPEN_PLOTLY_GRAPHS = True
# #plot energy use by drive type
# title = 'Energy use by drive type'
# plot_line_by_economy(model_output_all, ['Drive'], 'Energy', title, save_folder='all_economy_graphs', AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS)

# #%%
# #plot all data in model_output_all:
# value_cols = ['freight_tonne_km','passenger_km', 'Energy', 'Stocks',
#        'Occupancy','Load', 'Turnover_rate', 'New_vehicle_efficiency',
#        'Travel_km', 'Efficiency', 'Travel_km_per_stock', 'Surplus_stocks',
#        'Vehicle_sales_share']
# categorical_cols = ['Vehicle Type', 'Medium', 'Transport Type', 'Drive','Scenario']
# #%%
# import itertools
# AUTO_OPEN_PLOTLY_GRAPHS = False
# #plot each combination of: one of the value cols and then any number of the categorical cols
# n_categorical_cols = len(categorical_cols)
# for economy_x in model_output_all['Economy'].unique():
#     for value_col in value_cols:
#         for i in range(1, n_categorical_cols+1):
#             for combo in itertools.combinations(categorical_cols, i):
#                 title = f'{value_col} by {combo}'
#                 #filter for that ecovnomy only and then plot
#                 model_output_all = model_output_all_all_economies[model_output_all_all_economies['Economy'] == economy_x]
#                 plot_line_by_economy(model_output_all, list(combo), value_col, title, save_folder=f'all_economy_graphs/{value_col}', AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS)
#                 print(f'plotting {value_col} by {combo}')

