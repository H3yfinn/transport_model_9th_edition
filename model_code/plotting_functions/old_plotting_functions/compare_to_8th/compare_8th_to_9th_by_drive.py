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
current_working_dir = os.getcwd()
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir =  "\\\\?\\" + re.split('transport_model_9th_edition', script_dir)[0] + 'transport_model_9th_edition'
if __name__ == "__main__": #this allows the script to be run directly or from the main.py file as you cannot use relative imports when running a script directly
    # Modify sys.path to include the directory where utility_functions is located
    sys.path.append(f"{root_dir}\\code")
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

import plotly
import plotly.express as px
pd.options.plotting.backend = "plotly"#set pandas backend to plotly plotting instead of matplotlib
import plotly.io as pio
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook

#%%
#compare model output to 8th edition output. If there are any differences, print them
#laod output from 8th edition
model_output = pd.read_csv(root_dir + '\\' + 'output_data\\model_output_detailed\\{}'.format(config.model_output_file_name))
model_output_8th = pd.read_csv(root_dir + '\\' + 'intermediate_data\\activity_efficiency_energy_road_stocks.csv')

#%%
#keep only columns in model_output_8th
model_output = model_output[model_output.columns.intersection(model_output_8th.columns)]

#%%
#filter for data within the same Dates of each dataset
model_output = model_output[model_output['Date'].isin(model_output_8th['Date'])]
model_output_8th = model_output_8th[model_output_8th['Date'].isin(model_output['Date'])]

#create column in both datasets that states the dataset
model_output['Dataset'] = '9th'
model_output_8th['Dataset'] = '8th'

#concatenate data together
model_output_concat = pd.concat([model_output, model_output_8th], axis=0)
#%%
#plot energy use
#sum up data for energy use by Date, medium, economy, transport type, vehicle type and drive in both scenarios for each dataset
model_output_concat_sum = model_output_concat.groupby(['Date', 'Scenario', 'Economy', 'Medium', 'Dataset', 'Transport Type', 'Vehicle Type', 'Drive'], as_index=False).sum()

#join together the  'Transport Type', 'Vehicle Type', 'Drive' and 'Scenario' columns
model_output_concat_sum['TransportType_VehicleType_Drive_Scenario'] = model_output_concat_sum['Transport Type'] + '_' + model_output_concat_sum['Vehicle Type'] + '_' + model_output_concat_sum['Drive'] + '_' + model_output_concat_sum['Scenario']

# #drop cols we joined together
# model_output_concat_sum = model_output_concat_sum.drop(['Transport Type', 'Vehicle Type', 'Drive', 'Scenario'], axis=1)

#filter out data in Dates that are not in both datasets
model_output_concat_sum = model_output_concat_sum[model_output_concat_sum['Date'].isin(model_output_8th['Date'])]
model_output_concat_sum = model_output_concat_sum[model_output_concat_sum['Date'].isin(model_output['Date'])]
#%%
################################################################################################################################################################

title = 'Compared to 8th Energy use by Date, economy, in both scenarios, for each drive, USA and PRC removed'

model_output_concat_sum_other_regions = model_output_concat_sum[~model_output_concat_sum['Economy'].isin(['05_PRC', '20_USA'])]

#plot
fig = px.line(model_output_concat_sum_other_regions, x="Date", y="Energy", color="TransportType_VehicleType_Drive_Scenario", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles


plotly.offline.plot(fig, filename=root_dir + '\\' + 'plotting_output\\' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + title + '.png', scale=1, width=2000, height=800)


#%%
################################################################################
################################################################################
title = 'Compared to 8th Energy use by Date, economy, drive in both scenarios'

#plot
fig = px.line(model_output_concat_sum, x="Date", y="Energy", color="TransportType_VehicleType_Drive_Scenario", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename=root_dir + '\\' + 'plotting_output\\' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + title + '.png', scale=1, width=2000, height=800)

#%%
################################################################################################################################################################
title = 'Compared to 8th Activity by Date, economy, in both scenarios, for each drive, USA and PRC removed'

model_output_concat_sum_other_regions = model_output_concat_sum[~model_output_concat_sum['Economy'].isin(['05_PRC', '20_USA'])]

#plot
fig = px.line(model_output_concat_sum_other_regions, x="Date", y="Activity", color="TransportType_VehicleType_Drive_Scenario", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles


plotly.offline.plot(fig, filename=root_dir + '\\' + 'plotting_output\\' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + title + '.png', scale=1, width=2000, height=800)

#%%
################################################################################
################################################################################
title = 'Compared to 8th Activity use by Date, economy, drive in both scenarios'

#plot
fig = px.line(model_output_concat_sum, x="Date", y="Activity", color="TransportType_VehicleType_Drive_Scenario", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles


plotly.offline.plot(fig, filename=root_dir + '\\' + 'plotting_output\\' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + title + '.png', scale=1, width=2000, height=800)


#%%
################################################################################################################################################################
title = 'Compared to 8th Stocks by Date, economy, in both scenarios, for each drive, USA and PRC removed'

#filte rfor road only
model_output_concat_sum_stocks = model_output_concat_sum[model_output_concat_sum['Medium'].isin(['road'])]

model_output_concat_sum_stocks_other_regions = model_output_concat_sum_stocks[~model_output_concat_sum_stocks['Economy'].isin(['05_PRC', '20_USA'])]

#plot
fig = px.line(model_output_concat_sum_stocks_other_regions, x="Date", y="Stocks", color="TransportType_VehicleType_Drive_Scenario", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename=root_dir + '\\' + 'plotting_output\\' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + title + '.png', scale=1, width=2000, height=800)

#%%
################################################################################################################################################################
title = 'Compared to 8th Stocks by Date, economy, in both scenarios, for each drive'

#plot
fig = px.line(model_output_concat_sum_stocks, x="Date", y="Stocks", color="TransportType_VehicleType_Drive_Scenario", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename=root_dir + '\\' + 'plotting_output\\' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + title + '.png', scale=1, width=2000, height=800)

#%%
#TO DO
################################################################################################################################################################
#plot the data for the whole of apec to try understand what we are over/under exagerating compare to 8th.
#first plot energy use by drive type, vehicle type split into transport types

title = 'Compared to 8th Energy use by Date, drive, vehicle in each ttype'
#filter for scenario = reference
model_output_concat_sum_ref = model_output_concat_sum[model_output_concat_sum['Scenario'] == 'Reference']
#remove non specified from transport type
model_output_concat_sum_ref = model_output_concat_sum_ref[model_output_concat_sum_ref['Transport Type'] != 'nonspecified']
#sum data
model_output_concat_sum_ref = model_output_concat_sum_ref.groupby(['Date', 'Dataset', 'Transport Type', 'Drive', 'Vehicle Type'], as_index=False).sum()

#create a column which concats the drive type and fuel type
model_output_concat_sum_ref['Drive_Vehicle'] = model_output_concat_sum_ref['Vehicle Type'] + '_' + model_output_concat_sum_ref['Drive']

#plot
fig = px.line(model_output_concat_sum_ref, x="Date", y="Energy", color="Drive_Vehicle", line_dash='Dataset', facet_col="Transport Type", facet_col_wrap=3, title=title)

plotly.offline.plot(fig, filename=root_dir + '\\' + 'plotting_output\\' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + title + '.png', scale=1, width=2000, height=1500)

#%%
title = 'Compared to 8th Activity by Date, drive, vehicle in each ttype'

#plot
fig = px.line(model_output_concat_sum_ref, x="Date", y="Activity", color="Drive_Vehicle", line_dash='Dataset', facet_col="Transport Type", facet_col_wrap=3, title=title)

plotly.offline.plot(fig, filename=root_dir + '\\' + 'plotting_output\\' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + title + '.png', scale=1, width=2000, height=1500)

#%%
title = 'Compared to 8th Stocks by Date, drive, vehicle in each ttype'

#plot
fig = px.line(model_output_concat_sum_ref, x="Date", y="Stocks", color="Drive_Vehicle", line_dash='Dataset', facet_col="Transport Type", facet_col_wrap=3, title=title)

plotly.offline.plot(fig, filename=root_dir + '\\' + 'plotting_output\\' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + title + '.png', scale=1, width=2000, height=1500)

#%%
################################################################################################################################################################
#plot sales share over time by vehicle type / drive type combination
#quickly calculate sales share in hughs model:
#sales share is the share of new stocks of a particulkar vehicle type and drive type in a particular economy in a particular Date compared to the total new stocks of that vehicle type and drive type in that economy in that Date
title = 'Compared to 8th, Sales share by vehicle type drive type combination - pasenger'
model_output_concat_sum_sales = model_output_concat_sum[model_output_concat_sum['Transport Type'] == 'freight']
model_output_concat_sum_sales = model_output_concat_sum_sales[model_output_concat_sum_sales['Medium'] == 'road']
model_output_concat_sum_sales = model_output_concat_sum_sales[model_output_concat_sum_sales['Scenario'] == 'Reference']
#sum stocks by Date, vehicle type, drive type, dataset
model_output_concat_sum_sales = model_output_concat_sum_sales.groupby(['Date', 'Dataset', 'Vehicle Type', 'Drive'], as_index=False).sum()
#claulcate sales as teh schange in stocks each eyar
model_output_concat_sum_sales['Sales'] = model_output_concat_sum_sales.groupby(['Dataset', 'Vehicle Type', 'Drive'])['Stocks'].diff()
#set any negatives to 0
model_output_concat_sum_sales['Sales'] = model_output_concat_sum_sales['Sales'].clip(lower=0)
#create a column that is the sum of sales by Date and dataset
model_output_concat_sum_sales['Sales_sum'] = model_output_concat_sum_sales.groupby(['Date', 'Dataset'])['Sales'].transform('sum')
#calculate sales share
model_output_concat_sum_sales['Sales share'] = model_output_concat_sum_sales['Sales'] / model_output_concat_sum_sales['Sales_sum']
#filter data out from before 2022
model_output_concat_sum_sales = model_output_concat_sum_sales[model_output_concat_sum_sales['Date'] >= 2022]

#plot using plotly
fig = px.line(model_output_concat_sum_sales, x="Date", y="Sales share", line_dash='Vehicle Type', color='Drive' ,facet_col="Dataset", facet_col_wrap=2, title=title)

plotly.offline.plot(fig, filename=root_dir + '\\' + 'plotting_output\\' + title + '.html', auto_open=True)
fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + title + '.png', scale=1, width=2000, height=800)

# %%
#filter for only cars
model_output_concat_sum_sales = model_output_concat_sum_sales[model_output_concat_sum_sales['Vehicle Type'] == 'lv']
#create a column that is the sum of sales by Date and dataset
model_output_concat_sum_sales['Sales_sum'] = model_output_concat_sum_sales.groupby(['Date', 'Dataset'])['Sales'].transform('sum')
#calculate sales share
model_output_concat_sum_sales['Sales share'] = model_output_concat_sum_sales['Sales'] / model_output_concat_sum_sales['Sales_sum']

#plot using plotly
fig = px.line(model_output_concat_sum_sales, x="Date", y="Sales share", color='Drive' ,facet_col="Dataset", facet_col_wrap=2, title=title)
title = 'Compared to 8th, Sales share by drive in passenger cars'
plotly.offline.plot(fig, filename=root_dir + '\\' + 'plotting_output\\' + title + '.html', auto_open=True)
fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + title + '.png', scale=1, width=2000, height=800)

title = 'APERC outlook 8th, sales share by drive in passenger cars'
#create a area plot of sales by drive type
fig = px.area(model_output_concat_sum_sales, x="Date", y="Sales share", color='Drive' ,facet_col="Dataset", facet_col_wrap=2, title=title, category_orders={'Drive': ['g', 'phevg', 'bev', 'fcev', 'cng', 'lpg', 'd']},
color_discrete_map= {'g': 'red', 'phevg': 'white', 'bev': 'blue', 'fcev': 'green', 'cng': 'orange', 'lpg': 'purple', 'd': 'black'})

plotly.offline.plot(fig, filename=root_dir + '\\' + 'plotting_output\\' + title + '.html', auto_open=True)
fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + title + '.png', scale=1, width=2000, height=800)
# %%
################################################################################################################################################################