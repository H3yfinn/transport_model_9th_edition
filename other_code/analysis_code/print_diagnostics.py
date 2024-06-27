#take in detailed output data and print out any useful metrics/statisitcs to summarise the reults of the model. the intention is that the output willbe easy to view through the command line, and that the output will be saved to a file for later viewing.

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
#%%

#load data in
model_output_all = pd.read_csv('output_data/model_output/{}'.format(config.model_output_file_name))
model_output_detailed = pd.read_csv('output_data/model_output_detailed/{}'.format(config.model_output_file_name))

model_output_8th = pd.read_csv('intermediate_data/activity_efficiency_energy_road_stocks.csv')

#%%
#FILTER FOR SCENARIO OF INTEREST
#this should be temporary as the scenario should be passed in as a parameter through config if it is useed elsewhere
SCENARIO_OF_INTEREST = 'Carbon Neutral'
model_output_all = model_output_all[model_output_all['Scenario']==SCENARIO_OF_INTEREST]
model_output_8th = model_output_8th[model_output_8th['Scenario']==SCENARIO_OF_INTEREST]
model_output_detailed = model_output_detailed[model_output_detailed['Scenario']==SCENARIO_OF_INTEREST]
#%%
#create a dataframe that has the 8th and 9th concatenated
#create column in both datasets that states the dataset
model_output_9th = model_output_all.copy()
model_output_9th['Dataset'] = '9th'
model_output_8th['Dataset'] = '8th'

#concatenate data together
model_output_both_scenarios = pd.concat([model_output_9th, model_output_8th], axis=0)



################################################################################################################################################################
#%%
#plot energy use for all economys for each year, by drive type.
title = 'Total energy use for all economys for each year, drive type'
model_output_detailed_vtype = model_output_detailed.groupby(['Year', 'Drive'])['Energy'].sum().reset_index()

#plot
fig, ax = plt.subplots()
for key, grp in model_output_detailed_vtype.groupby(['Drive']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Energy', label=key)
plt.title(title)
plt.savefig('./plotting_output/diagnostics/{}.png'.format(title))

################################################################################################################################################################
#%%
#plot stocks use for all economys for each year, by drive type.
title='Total stocks for all economys for each year, drive type'
model_output_detailed_vtype = model_output_detailed.groupby(['Year', 'Drive'])['Stocks'].sum().reset_index()

#plot
fig, ax = plt.subplots()
for key, grp in model_output_detailed_vtype.groupby(['Drive']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Stocks', label=key)
plt.title(title)
plt.savefig('./plotting_output/diagnostics/{}.png'.format(title))

################################################################################################################################################################
#%%
#show the uptake of BEVs by year, per economy
title = 'Total stocks of BEVs for each year, by economy'
model_output_detailed_bevs = model_output_detailed[model_output_detailed['Drive'] == 'bev']
model_output_detailed_bevs = model_output_detailed_bevs.groupby(['Year', 'Economy'])['Stocks'].sum().reset_index()

#plot
fig, ax = plt.subplots()
for key, grp in model_output_detailed_bevs.groupby(['Economy']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Stocks', label=key)
plt.title(title)
plt.savefig('./plotting_output/diagnostics/{}.png'.format(title))

#%%
################################################################################################################################################################
#plot the average vehivle sales shares for each economy for each year, for LV's
title = 'Average vehicle sales shares for each drive for passenger LVs'
model_output_detailed_sales = model_output_detailed[model_output_detailed['Vehicle Type'] == 'lv']
# #tet out excludeing china 05_PRC
# model_output_detailed_sales = model_output_detailed_sales[model_output_detailed_sales['Economy'] != '05_PRC']
model_output_detailed_sales = model_output_detailed_sales[model_output_detailed_sales['Transport Type'] == 'passenger']
model_output_detailed_sales = model_output_detailed_sales.groupby(['Year', 'Drive'])['Vehicle_sales_share'].mean().reset_index()

#plot
fig, ax = plt.subplots()
for key, grp in model_output_detailed_sales.groupby(['Drive']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Vehicle_sales_share', label=key)
    
plt.title(title)
plt.savefig('./plotting_output/diagnostics/{}.png'.format(title))

#%%
################################################################################################################################################################

#plot the average vehivle sales shares for each economy for each year
title = 'Average vehicle sales shares for each drive for passenger'
model_output_detailed_sales = model_output_detailed[model_output_detailed['Transport Type'] == 'passenger']
model_output_detailed_sales = model_output_detailed_sales.groupby(['Year', 'Drive'])['Vehicle_sales_share'].mean().reset_index()

#plot
fig, ax = plt.subplots()
for key, grp in model_output_detailed_sales.groupby(['Drive']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Vehicle_sales_share', label=key)

plt.title(title)
plt.savefig('./plotting_output/diagnostics/{}.png'.format(title))

################################################################################################################################################################

#%%
#plot the total surplus stocks for all economy dor each year
title='Total surplus stocks for all economys for each year'
#sum surplus stocks for each economy for each year
model_output_surplus = model_output_detailed.groupby(['Year'])['Surplus_stocks'].sum().reset_index()

plt.plot(model_output_surplus['Year'], model_output_surplus['Surplus_stocks'])
plt.title(title)
plt.savefig('./plotting_output/diagnostics/{}.png'.format(title))

################################################################################################################################################################
#%%
#plot total energy use, activity and stocks compared to the 8th edition
title = 'Total energy use compared to the 8th edition'
#sum energy use for each dataset for each year
model_output_energy = model_output_both_scenarios.groupby(['Year', 'Dataset'])['Energy'].sum().reset_index()
#plot
fig, ax = plt.subplots()
for key, grp in model_output_energy.groupby(['Dataset']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Energy', label=key)
plt.title(title)
plt.savefig('./plotting_output/diagnostics/{}.png'.format(title))

title = 'Total activity compared to the 8th edition'
#sum activity for each dataset for each year
model_output_activity = model_output_both_scenarios.groupby(['Year', 'Dataset'])['Activity'].sum().reset_index()
#plot
fig, ax = plt.subplots()
for key, grp in model_output_activity.groupby(['Dataset']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Activity', label=key)
plt.title(title)
plt.savefig('./plotting_output/diagnostics/{}.png'.format(title))

title = 'Total stocks compared to the 8th edition'
#sum stocks for each dataset for each year
model_output_stocks = model_output_both_scenarios.groupby(['Year', 'Dataset'])['Stocks'].sum().reset_index()
#plot
fig, ax = plt.subplots()
for key, grp in model_output_stocks.groupby(['Dataset']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Stocks', label=key)
plt.title(title)
plt.savefig('./plotting_output/diagnostics/{}.png'.format(title))

################################################################################################################################################################
#%%
#plot activity by drive type 
title = 'Activity by drive type'
model_output_activity_drive = model_output_detailed.groupby(['Year', 'Drive'])['Activity'].sum().reset_index()

from matplotlib.pyplot import cm
color = iter(cm.rainbow(np.linspace(0, 1, 15)))
i=0
   
#plot
fig, ax = plt.subplots()
for key, grp in model_output_activity_drive.groupby(['Drive']):
    i+=1
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Activity', label=key,c=next(color))
plt.title(title)
plt.savefig('./plotting_output/diagnostics/{}.png'.format(title))

#%%

#plot total travel km per stock by vehicle type. To make things simple we will just recalcualte travl km per stock using the mean of travel km and stocks for each vehicle type and year
title = 'Average travel km per stock by transport and vehicle type'
model_output_travel_km_per_stock = model_output_detailed.copy()

model_output_travel_km_per_stock['Vehicle_transport_type'] = model_output_travel_km_per_stock['Vehicle Type'] + '_' + model_output_travel_km_per_stock['Transport Type']

model_output_travel_km_per_stock = model_output_travel_km_per_stock.groupby(['Year', 'Vehicle_transport_type'])['Travel_km', 'Stocks'].mean().reset_index()

model_output_travel_km_per_stock['Travel_km_per_stock'] = model_output_travel_km_per_stock['Travel_km'] / model_output_travel_km_per_stock['Stocks']

model_output_travel_km_per_stock = model_output_travel_km_per_stock[['Year', 'Vehicle_transport_type', 'Travel_km_per_stock']]

#remove nas cause non road doesnt have this data
model_output_travel_km_per_stock = model_output_travel_km_per_stock.dropna()

num_colors = len(model_output_travel_km_per_stock['Vehicle_transport_type'].unique())
from matplotlib.pyplot import cm
color = iter(cm.rainbow(np.linspace(0, 1, num_colors)))
i=0
   
#plot
fig, ax = plt.subplots()
for key, grp in model_output_travel_km_per_stock.groupby(['Vehicle_transport_type']):
    i+=1
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Travel_km_per_stock', label=key,c=next(color))

plt.title(title)
plt.savefig('./plotting_output/diagnostics/{}.png'.format(title))








#%%
################################################################################################################################################################
# #analysis
# #check for duplicates
# duplicates = model_output_all.duplicated().sum()
# if duplicates > 0:
#     print('There are {} duplicates in the model output'.format(duplicates))
# #check for missing values
# NAs = model_output_all.isna().sum().sum()
# if NAs > 0:
#     print('There are {} missing values in the model output'.format(NAs))





# #%%
# #compare model output to 8th edition output. If there are any differences, print them
# #laod output from 8th edition
# model_output = pd.read_csv('output_data/model_output_detailed/{}'.format(config.model_output_file_name))
# model_output_8th = pd.read_csv('output_data/model_output_detailed/activity_efficiency_energy_road_stocks.csv')

# #%%
# #plot energy use
# #get data for energy use by year, economy, in both scenarios

# #%%
# title='Surplus stocks use by year, economy, in both scenarios'

# data_3_select_years_other_regions = data_3_select_years[data_3_select_years['ECON_Sub_Category'] != 'China_USA']

# #plot
# fig = px.line(data_3_select_years_other_regions, x="Year", y="PJ", color="Scenario", line_dash='Scenario', facet_col="Economy_name", facet_col_wrap=7, title=title)#, #facet_col="Economy",
#              #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
# fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

# #fig.show()  
# import plotly
# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png')


# #%%


# #%%
# title='Energy use by year, economy, in both scenarios'

# #plot
# fig = px.line(data_3_select_years, x="Year", y="PJ", color="Scenario", line_dash='Scenario', facet_col="Economy_name", facet_col_wrap=7, title=title)#, #facet_col="Economy",
#              #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
# fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

# #fig.show()  
# import plotly
# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png')


# #%%
