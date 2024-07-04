

###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
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

###########################################
#PLOTTING:
###########################################


def plot_estimated_data_system_sales_share(config, sales, ECONOMY_ID):
    #plot to check., we will sum all values by everythign except col, then plot
    sales_plot = sales.copy()
    #filter for reference only
    sales_plot = sales_plot.loc[sales_plot['Scenario']=='Reference']
    cols = config.INDEX_COLS.copy()
    cols.remove('Economy')
    sales_plot = sales_plot.groupby(cols)['Sales Share'].sum().reset_index()
    # plot using plotly
    fig = px.bar(sales_plot, x='Drive', y='Sales Share', color='Drive',facet_col='Vehicle Type', facet_col_wrap=2)
    #WRite to html in plotting_output/input_exploration/
    fig.write_html(config.root_dir + '\\' + 'plotting_output\\input_exploration\\vehicle_sales_shares\\transport_data_system_testing\\{}_{}_sales_share.html'.format(ECONOMY_ID,config.FILE_DATE_ID))
    #it doesnt really matter what the values are since we'll be adjusting them as we get more data.

def plot_new_sales_shares(config, new_sales_shares_all, ECONOMY_ID):
        
    #now we wnat to plot the data using plotly. we will plot with facets for each economy, and a different plot for each vehicle type, transport tyep combo
    #first we need to create a new column that is the vehicle type and transport type
    #we will also plot for comparison between new_sales_shares_sum and new_sales_shares_all so nerge that on now
    # breakpoint()
    plotting = True
    if plotting:
        import plotly.express as px
        new_sales_shares_all_plot = new_sales_shares_all.copy()
        #replace road bool with 'road' or 'non_road'
        new_sales_shares_all_plot['road'] = new_sales_shares_all_plot['road'].replace({True:'road', False:'non_road'})
        new_sales_shares_all_plot['Vehicle_Transport_Medium'] = new_sales_shares_all_plot['Vehicle Type'] + '_' + new_sales_shares_all_plot['road']

        for scenario in new_sales_shares_all_plot['Scenario'].unique():
            for Vehicle_Transport_Medium in new_sales_shares_all_plot['Vehicle_Transport_Medium'].unique():
                plot_data = new_sales_shares_all_plot.loc[(new_sales_shares_all_plot['Vehicle_Transport_Medium']==Vehicle_Transport_Medium) & (new_sales_shares_all_plot['Scenario']==scenario)].copy()

                fig = px.line(plot_data, x='Date', y='Drive_share', color='Drive', facet_col='Transport Type',facet_col_wrap=3, title=Vehicle_Transport_Medium)
                #write to html in plotting_output\input_exploration\vehicle_sales_shares
                fig.write_html(config.root_dir + '\\' +f'plotting_output\\input_exploration\\vehicle_sales_shares\\{ECONOMY_ID}_{Vehicle_Transport_Medium}_{scenario}_drive_share.html', auto_open=False)
                
                #and then plot the transport type share
                fig = px.line(plot_data, x='Date', y='Transport_type_share', color='Drive', facet_col='Transport Type',facet_col_wrap=3, title=Vehicle_Transport_Medium, markers=True)
                #write to html in plotting_output\input_exploration\vehicle_sales_shares
                fig.write_html(config.root_dir + '\\' +f'plotting_output\\input_exploration\\vehicle_sales_shares\\{ECONOMY_ID}_{Vehicle_Transport_Medium}_{scenario}Transport_type_share_pre_vehicle_share_adj.html', auto_open=False)

        #it is also usefu to plot the vehicle sales share by economy now. This is because it is a useful graph for analysis of assumptions. So loop through economys and just plkot the Drive_share by economy, with vehicle type and transport type as facets
        
        new_sales_shares_all_plot = new_sales_shares_all.copy()
        #replace road bool with 'road' or 'non_road'
        new_sales_shares_all_plot['road'] = new_sales_shares_all_plot['road'].replace({True:'road', False:'non_road'})
        new_sales_shares_all_plot['Vehicle_Transport_Medium'] = new_sales_shares_all_plot['Vehicle Type'] + '_' +  '_' + new_sales_shares_all_plot['road']
        for scenario in new_sales_shares_all_plot['Scenario'].unique():
            for transport_type in new_sales_shares_all_plot['Transport Type'].unique():
                plot_data = new_sales_shares_all_plot.loc[(new_sales_shares_all_plot['Scenario']==scenario) & (new_sales_shares_all_plot['Transport Type']==transport_type)].copy()
                title = f'{transport_type} {scenario} Drive Share by Vehicle Type and medium'
                fig = px.line(plot_data, x='Date', y='Drive_share', color='Drive', facet_col='Vehicle_Transport_Medium',facet_col_wrap=3, title=title)
                #write to html in plotting_output\input_exploration\vehicle_sales_shares
                fig.write_html(config.root_dir + '\\' +f'plotting_output\\input_exploration\\vehicle_sales_shares\\by_economy\\{ECONOMY_ID}_{transport_type}_{scenario}_drive_share.html', auto_open=False)

                #also plot the data like the iea does. So plot the data for 2022 and previous, then plot for the follwoign eyars: [2025, 2030, 2035, 2040, 2050, 2060]. Also < also wat??
                plot_data = plot_data.apply(lambda x: x if x['Date'] <= 2022 or x['Date'] in [2025, 2030, 2035, 2040, 2050, 2060] else 0, axis=1)
                #drop all vehicle types except phev and bev
                plot_data = plot_data.loc[(plot_data['Drive']=='bev') | (plot_data['Drive']=='phev') | (plot_data['Drive']=='fcev')].copy()
                title = f'EV sales share, {transport_type}, {scenario}'
                #now plot
                fig = px.bar(plot_data, x='Date', y='Drive_share', color='Drive', facet_col='Vehicle Type', title=title, barmode='stack')
                
                fig.write_html(config.root_dir + '\\' +f'plotting_output\\input_exploration\\vehicle_sales_shares\\by_economy\\stacked_{ECONOMY_ID}_{transport_type}_{scenario}_drive_share.html', auto_open=False)
                #############
                # plot_data = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Scenario']==scenario) & (new_sales_shares_all_plot_drive_shares['Economy']==economy)].copy()
                
                # title = f'{economy} {scenario} Drive Share by Vehicle Type and Transport Type'
                # fig = px.line(plot_data, x='Date', y='Transport_type_share', color='Drive', line_dash = 'Measure', facet_col='Transport Type',facet_col_wrap=3, title=Vehicle_Transport)
                # #write to html in plotting_output\input_exploration\vehicle_sales_shares
                # fig.write_html(config.root_dir + '\\' +f'plotting_output\\input_exploration\\vehicle_sales_shares\\{Vehicle_Transport}_{scenario}Transport_type_share_pre_vehicke_share_adj.html', auto_open=False)
    #save vehicels sales share data for use in plotting our asumtions. we will save it as an excel file to be read in by the plotting assumptions script
    new_sales_shares_all_plot.to_csv(config.root_dir + '\\' + f'output_data\\assumptions_outputs\\vehicle_sales_shares_{ECONOMY_ID}_{config.FILE_DATE_ID}.csv', index=False)


def plot_new_sales_shares_normalised_by_transport_type(config, new_sales_shares_all, new_sales_shares_sum, new_sales_shares_all_new):

    #do some more plotting. just plot the Transport_type_share_new vs Transport_type_share
    plotting=True
    if plotting:
        new_sales_shares_all_plot = new_sales_shares_all_new.copy()

        import plotly.express as px
        #replace road bool with 'road' or 'non_road'
        new_sales_shares_all_plot['road'] = new_sales_shares_all_plot['road'].replace({True:'road', False:'non_road'})
        
        #extract a df for Transport_type_share measures:
        new_sales_shares_all_plot_transport_type_shares = new_sales_shares_all_plot[['Economy', 'Scenario', 'Date','Transport Type','road', 'Vehicle Type', 'Drive',  'Transport_type_share', 'Transport_type_share_new']].copy()

        #make them long
        #rename Transport_type_share to Transport_type_share_o
        new_sales_shares_all_plot_transport_type_shares = new_sales_shares_all_plot_transport_type_shares.melt(id_vars=['Economy', 'Scenario', 'Date', 'Transport Type','road','Vehicle Type', 'Drive'], value_vars=['Transport_type_share', 'Transport_type_share_new'], var_name='Measure', value_name='Value')

        #join drive and vehicle type
        new_sales_shares_all_plot_transport_type_shares['Vehicle_drive'] = new_sales_shares_all_plot_transport_type_shares['Vehicle Type'] + '_' + new_sales_shares_all_plot_transport_type_shares['Drive']
        for scenario in new_sales_shares_all_plot_transport_type_shares['Scenario'].unique():
            for economy in new_sales_shares_all_plot_transport_type_shares['Economy'].unique():
                for medium in new_sales_shares_all_plot_transport_type_shares['road'].unique():
                        
                    plot_data = new_sales_shares_all_plot_transport_type_shares.loc[(new_sales_shares_all_plot_transport_type_shares['Economy']==economy) & (new_sales_shares_all_plot_transport_type_shares['Scenario']==scenario) & (new_sales_shares_all_plot_transport_type_shares['road']==medium)].copy()

                    fig = px.line(plot_data, x='Date', y='Value', color='Vehicle_drive', line_dash = 'Measure', facet_col='Transport Type',facet_col_wrap=1, title=f'Transport_type_share {medium}', markers=True)
                    #write to html in plotting_output\input_exploration\vehicle_sales_shares
                    fig.write_html(config.root_dir + '\\' +f'plotting_output\\input_exploration\\vehicle_sales_shares\\by_economy\\{economy}_{scenario}_{medium}_Transport_type_share.html', auto_open=False)
    print('Plots of new sales shares saved to plotting_output\\input_exploration\\vehicle_sales_shares\\')

def plot_input_sales_shares_before_interpolation(config, new_sales_shares_pre_interp):
    #new_sales_shares_pre_interp[['Economy', 'Scenario', 'Date', 'Transport Type', 'Vehicle Type', 'Drive','Drive_share']]
    #do some more plotting. just plot the Transport_type_share_new vs Transport_type_share
    plotting=True
    if plotting:
        new_sales_shares_all_plot = new_sales_shares_pre_interp.copy()

        import plotly.express as px
        #replace road bool with 'road' or 'non_road'
        new_sales_shares_all_plot['road'] = new_sales_shares_all_plot['road'].replace({True:'road', False:'non_road'})
        #extract a df for Transport_type_share measures:
        new_sales_shares_all_plot_transport_type_shares = new_sales_shares_all_plot[['Economy', 'Scenario', 'Date', 'road','Transport Type', 'Vehicle Type', 'Drive','Drive_share']].copy()

        #join drive and vehicle type
        new_sales_shares_all_plot_transport_type_shares['Vehicle_drive'] = new_sales_shares_all_plot_transport_type_shares['Vehicle Type'] + '_' + new_sales_shares_all_plot_transport_type_shares['Drive']
        for scenario in new_sales_shares_all_plot_transport_type_shares['Scenario'].unique():
            for economy in new_sales_shares_all_plot_transport_type_shares['Economy'].unique():
                plot_data = new_sales_shares_all_plot_transport_type_shares.loc[(new_sales_shares_all_plot_transport_type_shares['Economy']==economy) & (new_sales_shares_all_plot_transport_type_shares['Scenario']==scenario)].copy()
                #concattransport type and medium
                plot_data['Transport_type'] = plot_data['Transport Type'] + '_' + plot_data['road']
                fig = px.line(plot_data, x='Date', y='Drive_share', color='Drive', line_dash = 'Vehicle Type', facet_col='Transport Type',facet_col_wrap=3, title='Drive_share', markers=True)
                #write to html in plotting_output\input_exploration\vehicle_sales_shares
                fig.write_html(config.root_dir + '\\' +f'plotting_output\\input_exploration\\vehicle_sales_shares\\by_economy\\{economy}_{scenario}drive_share_pre_interp.html', auto_open=False)
    
    print('Plots of pre interpolation sales shares saved to plotting_output\\input_exploration\\vehicle_sales_shares\\')

    
    
def plot_supply_side_fuel_mixing(config, supply_side_fuel_mixing, ECONOMY_ID, AUTO_OPEN=False):
    #plot supply side fuel mixing
    supply_side_fuel_mixing_plot = supply_side_fuel_mixing.copy()
    #round the Supply_side_fuel_share column to 2dp
    # supply_side_fuel_mixing_plot['Supply_side_fuel_share'] = supply_side_fuel_mixing_plot['Supply_side_fuel_share'].round(2)
    supply_side_fuel_mixing_plot= supply_side_fuel_mixing_plot[['Date', 'Economy','Scenario', 'Fuel','New_fuel' ,'Supply_side_fuel_share']].drop_duplicates()
    for scenario in supply_side_fuel_mixing_plot.Scenario.unique():
        scenario_data = supply_side_fuel_mixing_plot.loc[supply_side_fuel_mixing_plot['Scenario'] == scenario].copy()
        #supply side mixing is just the percent of a fuel type that is mixed into another fuel type, eg. 5% biodiesel mixed into diesel. We can use the concat of Fuel and New fuel cols to show the data:
        scenario_data['Fuel mix'] = scenario_data['Fuel'] + ' mixed with ' + scenario_data['New_fuel']
        #concat
        title = 'Supply side fuel mixing for '+ ECONOMY_ID + scenario + ' scenario'
        fig = px.line(scenario_data, x="Date", y="Supply_side_fuel_share", color='Fuel mix',  title=title)
        #save to html
        fig.write_html(config.root_dir + '\\' + f"plotting_output\\input_exploration\\fuel_mixing\\{title}.html", auto_open=AUTO_OPEN)

def plot_demand_side_fuel_mixing(config, demand_side_fuel_mixing, ECONOMY_ID):
    #for each cat col in demand_side_fuel_mixing, plot the fuel shares using plotly line graph, with date on x axis, faceted by Economy, and color by Drive and line dash by Fuel
    #do a graph for each scenario
    demand_side_fuel_mixing_plot = demand_side_fuel_mixing.copy()
    demand_side_fuel_mixing_plot['Demand_side_fuel_share'] = demand_side_fuel_mixing_plot['Demand_side_fuel_share'].round(2)
    #drop where Demand_side_fuel_share is 1
    demand_side_fuel_mixing_plot = demand_side_fuel_mixing_plot[demand_side_fuel_mixing_plot['Demand_side_fuel_share'] <= 0.999]
    
    #where medium is not 'road', then set drive to medium
    demand_side_fuel_mixing_plot.loc[demand_side_fuel_mixing_plot['Medium'] != 'road', 'Drive'] = demand_side_fuel_mixing_plot['Medium']
    
    demand_side_fuel_mixing_plot = demand_side_fuel_mixing_plot[['Date', 'Economy','Scenario', 'Fuel','Drive', 'Demand_side_fuel_share']].drop_duplicates()
    
    for scenario in demand_side_fuel_mixing_plot.Scenario.unique():
        scenario_data = demand_side_fuel_mixing_plot[demand_side_fuel_mixing_plot['Scenario'] == scenario].copy()
        title = 'Demand side fuel mixing for '+ECONOMY_ID + scenario + ' scenario'
        #concat drive aND FUEL 
        scenario_data['Drive'] = scenario_data['Drive'] + ' ' + scenario_data['Fuel'] 
        fig = px.line(scenario_data, x="Date", y="Demand_side_fuel_share", color="Drive", title=title)
        #save to html
        fig.write_html(config.root_dir + '\\' + f"plotting_output\\input_exploration\\fuel_mixing\\{title}.html")
        
def plot_average_intensity(config, non_road_model_input_wide):
    #grab economy id
    economy_id = non_road_model_input_wide['Economy'].unique()[0]
    # non_road_model_input_wide = non_road_model_input_wide.groupby(['Date', 'Transport Type', 'Drive'])['Intensity'].mean().unstack().reset_index()
    #first drop nas
    # non_road_model_input_wide = non_road_model_input_wide.dropna()
    non_road_model_input_wide_plotting = non_road_model_input_wide.copy()
    non_road_model_input_wide_plotting['Average_intensity'] = non_road_model_input_wide_plotting.groupby(['Transport Type','Medium', 'Drive'])['Intensity'].transform('mean')
    non_road_model_input_wide_plotting = non_road_model_input_wide_plotting[['Transport Type','Medium', 'Drive', 'Average_intensity']].drop_duplicates()
    
    #because some drive/transport type combos dont ahve any data, tehy end up ahvign intensity of nan and that gets rmeoved. so add on those combos with an intensity of 0 so that they are plotted
    #get all drive/transport type combos
    drive_transport_type_combos = non_road_model_input_wide[['Transport Type','Medium', 'Drive']].drop_duplicates()
    #set vlaue to 0
    drive_transport_type_combos['Average_intensity'] = 0
    #conat and sum to get them inthere
    non_road_model_input_wide_plotting = pd.concat([non_road_model_input_wide_plotting, drive_transport_type_combos]).groupby(['Transport Type', 'Medium', 'Drive'])['Average_intensity'].sum().reset_index()
    
    #plot as bars using plotly
    fig = px.bar(non_road_model_input_wide_plotting, x='Drive', y='Average_intensity', color='Drive', facet_col='Transport Type')
    fig.write_html(config.root_dir + '\\' +f'plotting_output\\input_exploration\\average_intensity\\average_non_road_intensity_{economy_id}.html', auto_open=False)
    
    
    
    
    