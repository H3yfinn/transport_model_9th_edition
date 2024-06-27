#This is not necessarily for input data only as it also plots the values that have been adjusted by grwoth factors. But essentially it is used to visualise the basic inputs to the model, and not the nmore complicated outputs, like vehicle stocks, activity or energy which require a lot of steps to caluclate

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
import plotly
import plotly.express as px
pd.options.plotting.backend = "matplotlib"
import plotly.io as pio
pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook

import matplotlib.pyplot as plt
plt.rcParams['figure.facecolor'] = 'w'
#%%
#load data in
model_output_detailed = pd.read_csv('output_data/model_output_detailed/{}'.format(config.model_output_file_name))

#FILTER FOR SCENARIO OF INTEREST
model_output_detailed = model_output_detailed[model_output_detailed['Scenario']==SCENARIO_OF_INTEREST]
#%%

#for all the following, filter only for medium = road since the input data of interest is only for road
model_output_detailed = model_output_detailed[model_output_detailed['Medium'] == 'road']
################################################################################################################################################################

#%%
#plot the average OCCUPANCY RATE by year, transport type and vehicel type 

#avergae occupancy rate for each transport type and vehicle type for each year
model_output_occ = model_output_detailed.groupby(['Year', 'Transport Type', 'Vehicle Type'])['Occupancy_or_load'].mean().reset_index()
model_output_occ_PASS = model_output_occ[model_output_occ['Transport Type']=='passenger']
model_output_occ_FR = model_output_occ[model_output_occ['Transport Type']=='freight']

title='Average OCCUPANCY RATE by year and vehicle type for passenger'
#plot
fig, ax = plt.subplots()
for key, grp in model_output_occ_PASS.groupby(['Vehicle Type']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Occupancy_or_load', label=key)
plt.title(title)


title='Average OCCUPANCY RATE by year and vehicle type for freight'
#plot
fig, ax = plt.subplots()
for key, grp in model_output_occ_PASS.groupby(['Vehicle Type']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Occupancy_or_load', label=key)
plt.title(title)


#%%
################################################################################################################################################################
title = 'OCCUPANCY RATE by year, transport type, vehicle type and economy'

model_output_occ = model_output_detailed.groupby(['Economy', 'Year', 'Transport Type', 'Vehicle Type'])['Occupancy_or_load'].mean().reset_index()

#plot
fig = px.line(model_output_occ, x="Year", y="Occupancy_or_load", color="Vehicle Type", line_dash='Transport Type', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

################################################################################################################################################################
#%%
#plot the average Turnover RATE by year, transport type and vehicel type 

#avergae Turnover rate for each transport type and vehicle type for each year
model_output_t = model_output_detailed.groupby(['Year', 'Transport Type', 'Vehicle Type'])['Turnover_rate'].mean().reset_index()
model_output_t_PASS = model_output_t[model_output_t['Transport Type']=='passenger']
model_output_t_FR = model_output_t[model_output_t['Transport Type']=='freight']

title='Average Turnover_rate by year and vehicle type for passenger'
#plot
fig, ax = plt.subplots()
for key, grp in model_output_t_PASS.groupby(['Vehicle Type']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Turnover_rate', label=key)
plt.title(title)


title='Average Turnover_rate by year and vehicle type for freight'
#plot
fig, ax = plt.subplots()
for key, grp in model_output_t_PASS.groupby(['Vehicle Type']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Turnover_rate', label=key)
plt.title(title)


#%%
################################################################################################################################################################
title = 'Turnover RATE by year, transport type, vehicle type and economy'

model_output_t = model_output_detailed.groupby(['Economy', 'Year', 'Transport Type', 'Vehicle Type'])['Turnover_rate'].mean().reset_index()

#plot
fig = px.line(model_output_t, x="Year", y="Turnover_rate", color="Vehicle Type", line_dash='Transport Type', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles


plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

#%%
################################################################################################################################################################
#plot the average New_vehicle_efficiency by year, transport type, vehicel type and drive type
model_output_new_v_eff = model_output_detailed.groupby(['Year', 'Transport Type', 'Vehicle Type', 'Drive'])['New_vehicle_efficiency'].mean().reset_index()

for v_type in model_output_new_v_eff['Vehicle Type'].unique():
    
    #plot transport type = pass
    model_output_new_v_eff_pass = model_output_new_v_eff[(model_output_new_v_eff['Transport Type']=='passenger') & (model_output_new_v_eff['Vehicle Type']==v_type)]
    if len(model_output_new_v_eff_pass) > 0:
        title='Average New_vehicle_efficiency for passenger, {}'.format(v_type)
        
        #plot
        fig, ax = plt.subplots()
        for key, grp in model_output_new_v_eff_pass.groupby(['Drive']):

            ax = grp.plot(ax=ax, kind='line', x='Year', y='New_vehicle_efficiency', label=key)
        plt.title(title)


    #plot transport type = freight
    model_output_new_v_eff_freight = model_output_new_v_eff[(model_output_new_v_eff['Transport Type']=='freight') & (model_output_new_v_eff['Vehicle Type']==v_type)]
    if len(model_output_new_v_eff_freight) > 0:
        title='Average New_vehicle_efficiency for freight, {}'.format(v_type)

        #plot
        fig, ax = plt.subplots()
        for key, grp in model_output_new_v_eff_freight.groupby(['Drive']):
            if len(grp) == 0:
                continue
            ax = grp.plot(ax=ax, kind='line', x='Year', y='New_vehicle_efficiency', label=key)
        plt.title(title)
        


#%%
################################################################################################################################################################
title = 'New_vehicle_efficiency by year, transport type, vehicle type, drive and economy'

model_output_v_eff = model_output_detailed.groupby(['Economy', 'Year', 'Drive', 'Transport Type', 'Vehicle Type'])['New_vehicle_efficiency'].mean().reset_index()

model_output_v_eff['Transport_Vehicle_type'] = model_output_v_eff['Transport Type'] + '_' + model_output_v_eff['Vehicle Type']

#plot
fig = px.line(model_output_v_eff, x="Year", y="New_vehicle_efficiency", color="Transport_Vehicle_type", line_dash='Drive', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

################################################################################################################################################################

#%%
#plot avged Vehicle_sales_share by vehicle type by drive 
model_output_v_sales_share = model_output_detailed.groupby(['Year', 'Transport Type', 'Vehicle Type', 'Drive'])['Vehicle_sales_share'].mean().reset_index()

for v_type in model_output_v_sales_share['Vehicle Type'].unique():
    
    #plot transport type = pass
    model_output_v_sales_share_pass = model_output_v_sales_share[(model_output_v_sales_share['Transport Type']=='passenger') & (model_output_v_sales_share['Vehicle Type']==v_type)]
    if len(model_output_v_sales_share_pass) > 0:
        title='Average Vehicle_sales_share for passenger, {}'.format(v_type)

        #plot
        fig, ax = plt.subplots()
        for key, grp in model_output_v_sales_share_pass.groupby(['Drive']):
            if len(grp) == 0:
                continue
            ax = grp.plot(ax=ax, kind='line', x='Year', y='Vehicle_sales_share', label=key)
        plt.title(title)
        

    #plot transport type = freight
    model_output_v_sales_share_freight = model_output_v_sales_share[(model_output_v_sales_share['Transport Type']=='freight') & (model_output_v_sales_share['Vehicle Type']==v_type)]

    if len(model_output_v_sales_share_freight) > 0:
        title='Average Vehicle_sales_share for freight, {}'.format(v_type)

        #plot
        fig, ax = plt.subplots()
        for key, grp in model_output_v_sales_share_freight.groupby(['Drive']):
            if len(grp) == 0:
                continue
            ax = grp.plot(ax=ax, kind='line', x='Year', y='Vehicle_sales_share', label=key)
        plt.title(title)
        

#%%
################################################################################################################################################################
title = 'Vehicle_sales_share by year, transport type, vehicle type, drive and economy'

model_output_sales = model_output_detailed.groupby(['Economy', 'Year', 'Drive', 'Transport Type', 'Vehicle Type'])['Vehicle_sales_share'].mean().reset_index()

model_output_sales['Transport_Vehicle_type'] = model_output_sales['Transport Type'] + '_' + model_output_sales['Vehicle Type']

#plot
fig = px.line(model_output_sales, x="Year", y="Vehicle_sales_share", color="Transport_Vehicle_type", line_dash='Drive', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

################################################################################################################################################################
#%%
#plot travel km per stock by year, transport type, vehicle type
model_output_travel_km_per_stock = model_output_detailed.groupby(['Year', 'Transport Type', 'Vehicle Type'])['Travel_km_per_stock'].mean().reset_index()

model_output_travel_km_per_stock_pass = model_output_travel_km_per_stock[model_output_travel_km_per_stock['Transport Type']=='passenger']
model_output_travel_km_per_stock_freight = model_output_travel_km_per_stock[model_output_travel_km_per_stock['Transport Type']=='freight']

title='Average Travel_km_per_stock by year, vehicle type and drive type for passenger'

#plot
fig, ax = plt.subplots()
for key, grp in model_output_travel_km_per_stock_pass.groupby(['Vehicle Type']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Travel_km_per_stock', label=key)
plt.title(title)


title='Average Travel_km_per_stock by year, vehicle type and drive type for freight'

#plot
fig, ax = plt.subplots()
for key, grp in model_output_travel_km_per_stock_freight.groupby(['Vehicle Type']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Travel_km_per_stock', label=key)
plt.title(title)


#%%
################################################################################################################################################################
title = 'Average Travel_km_per_stock by year, transport type, vehicle type and economy'

model_output_trav_p_stock = model_output_detailed.groupby(['Economy', 'Year',  'Transport Type', 'Vehicle Type'])['Travel_km_per_stock'].mean().reset_index()

#plot
fig = px.line(model_output_trav_p_stock, x="Year", y="Travel_km_per_stock", color="Vehicle Type", line_dash='Transport Type', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)


################################################################################################################################################################
#plot efficiency of new vehicles by drive type vs efficiency of current stocks in use. #this is intended especially to see how the base year efficiency of new vehicles compares to the efficiency of the current stocks in use. It should be a small difference only.. and efficiency of new stocks should be higher than current stocks.
model_output_detailed_eff_df = model_output_detailed[['Year', 'Economy', 'Vehicle Type', 'Transport Type', 'Drive', 'Efficiency', 'New_vehicle_efficiency']]

#melt the efficiency and new vehicle efficiency columns to one measur col
model_output_detailed_eff_df = pd.melt(model_output_detailed_eff_df, id_vars=['Year', 'Economy', 'Vehicle Type', 'Transport Type', 'Drive'], value_vars=['Efficiency', 'New_vehicle_efficiency'], var_name='Measure', value_name='Efficiency')

#create a new colun to concat the drive type, transport type and vehicle type
model_output_detailed_eff_df['Drive_Transport_Vehicle'] = model_output_detailed_eff_df['Drive'] + '_' + model_output_detailed_eff_df['Transport Type'] + '_' + model_output_detailed_eff_df['Vehicle Type']

#plot
title = 'Efficiency of new vehicles by drive type vs efficiency of current stocks in use'
fig = px.line(model_output_detailed_eff_df, x="Year", y="Efficiency", color="Drive_Transport_Vehicle", line_dash='Measure', facet_col="Economy", facet_col_wrap=7, title=title)
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

#%%
################################################################################################################################################################
#plot the base year efficiency values for new vehicles by drive type, transport type and vehicle type, vs the efficiency of the current stocks in use
#we will plot it using a boxplot so we can plot all economys in one plot, then separate plots for each vehicle_type/transport type 
model_output_detailed_eff_df = model_output_detailed[['Year', 'Economy', 'Vehicle Type', 'Transport Type', 'Drive', 'Efficiency', 'New_vehicle_efficiency']]

model_output_detailed_eff_df = model_output_detailed_eff_df[model_output_detailed_eff_df['Year']==config.DEFAULT_BASE_YEAR]

#melt the efficiency and new vehicle efficiency columns to one measur col
model_output_detailed_eff_df = pd.melt(model_output_detailed_eff_df, id_vars=['Year', 'Economy', 'Vehicle Type', 'Transport Type', 'Drive'], value_vars=['Efficiency', 'New_vehicle_efficiency'], var_name='Measure', value_name='Efficiency')

model_output_detailed_eff_df['Transport_Vehicle_Type'] =  model_output_detailed_eff_df['Transport Type'] + '_' + model_output_detailed_eff_df['Vehicle Type']

title = 'Box plot Efficiency of new vehicles by drive type vs efficiency of current stocks in use'
#plot
fig = px.box(model_output_detailed_eff_df, x="Drive", y="Efficiency", color="Measure", facet_col="Transport_Vehicle_Type", facet_col_wrap=6, title=title)
fig.update_traces(quartilemethod="exclusive") # or "inclusive", or "linear" by default

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=1500)
#%%













