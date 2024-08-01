###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
from .. import utility_functions
from ..calculation_functions import road_model_functions
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


import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

#%%

def write_graph_to_html(config, filename, graph_type, plot_data, economy, x=None, y=None, color=None, title=None, line_dash=None, y_axes_title=None, legend_title=None, font_size=30, marker_line_width=2.5, line_width=10, colors_dict={}):
    
    # Create the graph based on the specified graph_type
    if graph_type == 'line':
        fig = px.line(plot_data, x=x, y=y, color=color, title=title, line_dash=line_dash, color_discrete_map=colors_dict)
        fig.update_traces(line_width=line_width)
    elif graph_type == 'scatter':
        fig = px.scatter(plot_data, x=x, y=y, color=color, title=title, color_discrete_map=colors_dict)
    elif graph_type == 'area':
        fig =px.area(plot_data, x=x, y=y, color=color, title=title, color_discrete_map=colors_dict)
    elif graph_type == 'bar':
        fig = px.bar(plot_data, x=x, y=y, color=color, title=title, color_discrete_map=colors_dict)
        fig.update_traces(marker_line_width=marker_line_width)
    elif graph_type == 'box':
        fig = px.box(plot_data, x=x, y=y, color=color, title=title, color_discrete_map=colors_dict)
    elif graph_type == 'histogram':
        fig = px.histogram(plot_data, x=x, y=y, color=color, title=title, color_discrete_map=colors_dict)
    elif graph_type == 'strip':
        fig = px.strip(plot_data, x=x, y=y, color=color, title=title, color_discrete_map=colors_dict)
    else:
        raise ValueError('graph_type must be either line, scatter, or area')

    # Update layout with y_axes_title and legend_title
    fig.update_layout(yaxis_title=y_axes_title, legend_title=legend_title,font_size=font_size)   
    fig.write_html(os.path.join(config.root_dir,  'plotting_output', 'dashboards', economy, 'individual_graphs', filename))
    
    
def remap_vehicle_types(config, df, value_col='Value', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'], vehicle_type_mapping_set='simplified', include_non_road=True, aggregation_type=('sum', )):
    """
    

    Args:
        df (_type_): _description_
        value_col (str, optional): _description_. Defaults to 'Value'.
        new_index_cols (list, optional): _description_. Defaults to ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'].
        vehicle_type_mapping_set (str, optional): _description_. Defaults to 'simplified'.
        include_non_road (bool, optional): _description_. Defaults to True.
        aggregation_type (tuple, optional): _description_. Defaults to ('sum',). can be ('sum',) or ('weighted_average', 'Weight')

    Returns:
        _type_: _description_
    """
    if vehicle_type_mapping_set == 'original':
        vehicle_type_combinations = {
            'lt': 'lt', 'suv': 'suv', 'car': 'car', 'ht': 'ht', 'mt': 'mt', 'bus': 'bus', '2w': '2w', 'lcv': 'lcv'}
    elif vehicle_type_mapping_set == 'simplified':
        #also group and sum by the following vehicle type cmbinations:
        vehicle_type_combinations = {'lt':'lpv', 'suv':'lpv', 'car':'lpv', 'ht':'trucks', 'mt':'trucks', 'bus':'bus', '2w':'2w', 'lcv':'lcv'}
    elif vehicle_type_mapping_set == 'similar_trajectories':
        vehicle_type_combinations = {'lt':'lpv', 'suv':'lpv', 'car':'lpv', 'ht':'trucks', 'mt':'trucks', 'bus':'bus_2w', '2w':'bus_2w', 'lcv':'lcv'}
    elif vehicle_type_mapping_set == 'similar_trajectories_lpv_detailed':
        vehicle_type_combinations = {'lt':'lt', 'suv':'suv', 'car':'car', 'ht':'trucks', 'mt':'trucks', 'bus':'bus_2w', '2w':'bus_2w', 'lcv':'lcv'}
    if include_non_road:
        vehicle_type_combinations['rail'] = 'rail'
        vehicle_type_combinations['ship'] = 'ship'
        vehicle_type_combinations['air'] = 'air'
        vehicle_type_combinations['all'] = 'non-road'
    else:
        vehicle_type_combinations['rail'] = 'non-road'
        vehicle_type_combinations['ship'] = 'non-road'
        vehicle_type_combinations['air'] = 'non-road'
        vehicle_type_combinations['all'] = 'non-road'    
    
    df['Vehicle Type new'] = df['Vehicle Type'].map(vehicle_type_combinations)
    #drop then rename vehicle type
    df['Vehicle Type'] = df['Vehicle Type new']
    #dxrop the new column
    df.drop(columns=['Vehicle Type new'], inplace=True)
    
    if aggregation_type[0] == 'weighted_average':
        df['Weighted Value'] = df[value_col] * df[aggregation_type[1]]
        #create copy of aggregation_type[1] spo we can set it to 1 if it is 0
        df[aggregation_type[1] + ' copy'] = df[aggregation_type[1]]
        #sum weighted values and weights so we can calculate weighted average:
        df = df.groupby(new_index_cols).sum().reset_index()
        #fill 0 with 1
        df[aggregation_type[1] + ' copy'] = df[aggregation_type[1] + ' copy'].replace(0,1)
        #calculate weighted average
        df[value_col] = df['Weighted Value']/df[aggregation_type[1] + ' copy']
        #drop the columns we don't need anymore
        df.drop(columns=['Weighted Value', aggregation_type[1] + ' copy'], inplace=True)
        
    elif aggregation_type[0]=='sum':
        df = df.groupby(new_index_cols, group_keys=False).sum(numeric_only=True).reset_index()
        
    return df
    
def remap_drive_types(config, df, value_col='Value', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'], drive_type_mapping_set='original', aggregation_type=('sum', ), include_non_road=True):
    if drive_type_mapping_set == 'original':
        drive_type_combinations = {'ice_g':'ice_g', 'ice_d':'ice_d', 'phev_d':'phev_d', 'phev_g':'phev_g', 'bev':'bev', 'fcev':'fcev', 'cng':'cng', 'lpg':'lpg'}
    elif drive_type_mapping_set == 'simplified':
        drive_type_combinations = {'ice_g':'ice', 'ice_d':'ice', 'phev_d':'phev', 'phev_g':'phev', 'bev':'bev', 'fcev':'fcev', 'cng':'gas', 'lpg':'gas'}
    elif drive_type_mapping_set == 'extra_simplified':
        drive_type_combinations = {'ice_g':'ice', 'ice_d':'ice', 'phev_d':'phev', 'phev_g':'phev', 'bev':'bev', 'fcev':'fcev', 'cng':'ice', 'lpg':'ice'}
    if include_non_road:
        drive_type_combinations['rail'] = 'rail'
        drive_type_combinations['ship'] = 'ship'
        drive_type_combinations['air'] = 'air'
        drive_type_combinations['all'] = 'non-road'
    else:
        drive_type_combinations['rail'] = 'non-road'
        drive_type_combinations['ship'] = 'non-road'
        drive_type_combinations['air'] = 'non-road'
        drive_type_combinations['all'] = 'non-road'
            
    df["Drive new"] = df['Drive'].map(drive_type_combinations)
    df['Drive'] = df['Drive new']
    df.drop(columns=['Drive new'], inplace=True)
    
    if aggregation_type[0] == 'weighted_average':
        df['Weighted Value'] = df[value_col] * df[aggregation_type[1]]
        #create copy of aggregation_type[1] spo we can set it to 1 if it is 0
        df[aggregation_type[1] + ' copy'] = df[aggregation_type[1]]
        #sum weighted values and weights so we can calculate weighted average:
        df = df.groupby(new_index_cols).sum().reset_index()
        #fill 0 with 1
        df[aggregation_type[1] + ' copy'] = df[aggregation_type[1] + ' copy'].replace(0,1)
        #calculate weighted average
        df[value_col] = df['Weighted Value']/df[aggregation_type[1] + ' copy']
        #drop the columns we don't need anymore
        df.drop(columns=['Weighted Value', aggregation_type[1] + ' copy'], inplace=True)
        
    elif aggregation_type[0]=='sum':
        df = df.groupby(new_index_cols).sum().reset_index()
    return df

def map_fuels(config, energy_use_by_fuel_type, value_col='Energy', index_cols=['Economy', 'Scenario', 'Date', 'Dataset', 'Fuel'], mapping_type='simplified'):
    #grab Fuel = 17_electricity, hydrogens, biofuels, oil, gas:
    #group the following into fuels with the following aggregations:    #
    # '07_01_motor_gasoline', '07_07_gas_diesel_oil', '07_08_fuel_oil',
    #    '07_09_lpg', '07_x_jet_fuel', '08_01_natural_gas',
    #    '16_05_biogasoline', '16_06_biodiesel', '16_x_hydrogen',
    #    '17_electricity', '07_02_aviation_gasoline', '07_06_kerosene',
    #    '16_07_bio_jet_kerosene', '16_x_ammonia', '16_x_efuel',, 16_01_biogas 'Total'],
    #aggregations:
    #17_electricity: 17_electricity
    #hydrogens_efuels: 16_x_hydrogen, 16_x_ammonia,16_x_efuel
    #biofuels: 16_05_biogasoline, 16_06_biodiesel, 16_07_bio_jet_kerosene , 16_01_biogas
    #gas: 08_01_natural_gas, 07_09_lpg
    #oil: 07_01_motor_gasoline, 07_07_gas_diesel_oil, 07_08_fuel_oil, 07_02_aviation_gasoline, 07_06_kerosene,07_x_jet_fuel
    #Total = Total
    if mapping_type == 'simplified':
        fuels_mapping = {'17_electricity':'17_electricity', '16_x_hydrogen': 'hydrogens_efuels', '16_x_ammonia':'hydrogens_efuels','16_x_efuel':'hydrogens_efuels', '16_05_biogasoline':'biofuels', '16_06_biodiesel':'biofuels', '16_07_bio_jet_kerosene':'biofuels', '16_01_biogas':'biofuels', '08_01_natural_gas':'gas', '07_09_lpg':'other_fossil_fuels', '07_01_motor_gasoline':'gasoline', '07_07_gas_diesel_oil':'diesel', '07_08_fuel_oil':'other_fossil_fuels', '07_02_aviation_gasoline':'jet_fuels', '07_06_kerosene':'jet_fuels','07_x_jet_fuel':'jet_fuels','07_x_other_petroleum_products':'other_fossil_fuels','7_x_other_petroleum_products':'other_fossil_fuels', 'Total':'Total', '01_x_thermal_coal':'other_fossil_fuels',
        '08_02_lng':'gas'}
        #if any fuels missing raise the alarm:
        for fuel in energy_use_by_fuel_type['Fuel'].unique():
            if fuel not in fuels_mapping.keys():
                raise ValueError('fuel {} is not in the mapping'.format(fuel))
    elif mapping_type == 'all':#keep original mapping
        fuels_mapping = {}
        #add any fuels that are not in the mapping to the mapping as themselves:
        for fuel in energy_use_by_fuel_type['Fuel'].unique():
            if fuel not in fuels_mapping.keys():
                fuels_mapping[fuel] = fuel
    else:
        raise ValueError('mapping_type is not a valid option {}'.format(mapping_type))
    energy_use_by_fuel_type['Fuel'] = energy_use_by_fuel_type['Fuel'].map(fuels_mapping)
    energy_use_by_fuel_type = energy_use_by_fuel_type.groupby(index_cols)[value_col].sum().reset_index()
    return energy_use_by_fuel_type

def identify_high_2w_economies(config, stocks_df):
    #remap vehicle types only for econmoys where the 2w vehicle type makes up more than 30% of stocks. This way, tehre wont be too many lines on the plot that arent near 0.#we will spit the data into two dataframes, one with high 2w and one without, then remap the vehicle types for the one with high 2w, then concat them back together
    stocks_sum = stocks_df.groupby(['Economy', 'Vehicle Type'])['Value'].sum().reset_index().copy()
    stocks_sum['Value'] = stocks_sum['Value']/stocks_sum.groupby(['Economy'])['Value'].transform('sum')
    #keep only 2w where Value is greater than 0.3
    stocks_sum = stocks_sum.loc[(stocks_sum['Vehicle Type']=='2w') & (stocks_sum['Value']>=0.3)].copy()
    stocks_sum_economies = stocks_sum['Economy'].unique()
    return stocks_sum_economies

def identify_high_gas_reliance_economies(config, stocks_df, X=.2):
    #remap drive types only for econmoys where the gas drive type makes up more than X% of stocks. This way, tehre wont be too many lines on the plot that arent near 0.#we will spit the data into two dataframes, one with high gas and one without, then remap the drive types for the one with high gas, then concat them back together
    #first define gas mapping
    gas_drives = {'cng':'gas', 'lpg':'gas'}
    #map gas to gas
    stocks_df['Drive'] = stocks_df['Drive'].replace(gas_drives)
    stocks_sum = stocks_df.groupby(['Economy', 'Drive'])['Value'].sum().reset_index().copy()
    stocks_sum['Value'] = stocks_sum['Value']/stocks_sum.groupby(['Economy'])['Value'].transform('sum')
    #keep only gas where Value is greater than X
    stocks_sum = stocks_sum.loc[(stocks_sum['Drive']=='gas') & (stocks_sum['Value']>=X)].copy()
    stocks_sum_economies = stocks_sum['Economy'].unique()
    return stocks_sum_economies

def remap_stocks_and_sales_based_on_economy(config, stocks, new_sales_shares_all_plot_drive_shares, DRIVE_OR_VEHICLE_TYPE='Vehicle Type'):
    """ based on patterns we will make teh graphs a bit different by economy."""
    if DRIVE_OR_VEHICLE_TYPE == 'Vehicle Type':
        stocks_sum_economies = identify_high_2w_economies(config, stocks)
        #keep those economies in the stocks df
        high_2w_economies_stocks = stocks[stocks['Economy'].isin(stocks_sum_economies)].copy()
        other_economies_stocks = stocks[~stocks['Economy'].isin(stocks_sum_economies)].copy()
        high_2w_economies_sales = new_sales_shares_all_plot_drive_shares[new_sales_shares_all_plot_drive_shares['Economy'].isin(stocks_sum_economies)].copy()
        other_economies_sales = new_sales_shares_all_plot_drive_shares[~new_sales_shares_all_plot_drive_shares['Economy'].isin(stocks_sum_economies)].copy()    
        
        high_2w_economies_stocks = remap_vehicle_types(config, high_2w_economies_stocks, value_col='Value', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'],vehicle_type_mapping_set='simplified')
        high_2w_economies_sales = remap_vehicle_types(config, high_2w_economies_sales, value_col='Value', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'],vehicle_type_mapping_set='simplified')
        
        #then do remappign for the otehres:
        other_economies_stocks = remap_vehicle_types(config, other_economies_stocks, value_col='Value', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'],vehicle_type_mapping_set='simplified')
        other_economies_sales = remap_vehicle_types(config, other_economies_sales, value_col='Value', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'],vehicle_type_mapping_set='simplified')
        
        
        #concat the two dataframes
        stocks = pd.concat([high_2w_economies_stocks, other_economies_stocks])
        new_sales_shares_all_plot_drive_shares = pd.concat([high_2w_economies_sales, other_economies_sales])
        
        return stocks, new_sales_shares_all_plot_drive_shares
    elif DRIVE_OR_VEHICLE_TYPE == 'Drive':
        return None, None #havent implemented this yet
    else:
        return None, None #havent implemented this yet
    
###################################################
def plot_share_of_transport_type(config, ECONOMY_IDs, new_sales_shares_all_plot_drive_shares_df, stocks_df, fig_dict, color_preparation_list, colors_dict, share_of_transport_type_type, WRITE_HTML=True):
    PLOTTED=True
    stocks = stocks_df.copy()
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares_df.copy()
    breakpoint()#how to change drive to allow for gas here?
    stocks, new_sales_shares_all_plot_drive_shares = remap_stocks_and_sales_based_on_economy(config, stocks, new_sales_shares_all_plot_drive_shares)
    # #sum up all the sales shares for each drive type
    new_sales_shares_all_plot_drive_shares['line_dash'] = 'sales'
    #now calucalte share of total stocks as a proportion like the sales share
    stocks['Value'] = stocks.groupby(['Scenario', 'Economy', 'Date', 'Transport Type','Vehicle Type'], group_keys=False)['Value'].apply(lambda x: x/x.sum(numeric_only=True))
    #create line_dash column and call it stocks
    stocks['line_dash'] = 'stocks'
    
    for scenario in new_sales_shares_all_plot_drive_shares['Scenario'].unique():
        new_sales_shares_all_plot_drive_shares_scenario = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Scenario']==scenario)]
        stocks_scen = stocks.loc[(stocks['Scenario']==scenario)].copy()
        ###        
        
        #then concat the two dataframes
        new_sales_shares_all_plot_drive_shares_scenario = pd.concat([new_sales_shares_all_plot_drive_shares_scenario, stocks_scen])
        
        #times shares by 100 and round to 0 dp
        new_sales_shares_all_plot_drive_shares_scenario['Value'] = round(new_sales_shares_all_plot_drive_shares_scenario['Value']*100,0)
                
        for economy in ECONOMY_IDs:
            plot_data =  new_sales_shares_all_plot_drive_shares_scenario.loc[(new_sales_shares_all_plot_drive_shares_scenario['Economy']==economy)].copy()
            
            # Group by 'Drive' and filter out groups where all values are 0
            groups = plot_data.groupby(['Drive', 'line_dash'])
            plot_data = groups.filter(lambda x: not all(x['Value'] == 0))
            
            #drop all drives except phev, bev and fcev, except if economy is focusing on gas too - then keep gas (which is cng and lpg) #TODO
            
            plot_data = plot_data.loc[(plot_data['Drive']=='bev') | (plot_data['Drive']=='phev') | (plot_data['Drive']=='fcev')].copy()

            #concat drive and vehicle type
            plot_data['Drive'] = plot_data['Drive'] + ' ' + plot_data['Vehicle Type']
            #sort by date col and line_dash
            plot_data.sort_values(by=['Date'], inplace=True)
            
            #times values by 100
            plot_data['Value'] = plot_data['Value']*100
            #############
            #now plot
            title = f'Sales/stock share (%)'

            if share_of_transport_type_type == 'passenger':
                
                fig = px.line(plot_data[plot_data['Transport Type']=='passenger'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)

                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['share_of_transport_type_passenger'] = [fig, title, PLOTTED]
                
                if WRITE_HTML:
                    write_graph_to_html(config, filename=f'share_of_transport_type_passenger{scenario}.html', graph_type='line', plot_data=plot_data,economy=economy, x='Date', y='Value', color='Drive', title='Default Title', line_dash='line_dash', y_axes_title='Y Axis', legend_title='', font_size=30, marker_line_width=2.5, line_width=10, colors_dict=colors_dict)
            
            
            #############
            elif share_of_transport_type_type == 'freight':

                fig = px.line(plot_data[plot_data['Transport Type']=='freight'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)

                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['share_of_transport_type_freight'] = [fig, title, PLOTTED]
                if WRITE_HTML:
                    write_graph_to_html(config, filename=f'share_of_transport_type_freight{scenario}.html', graph_type='line', plot_data=plot_data,economy=economy, x='Date', y='Value', color='Drive', title='Default Title', line_dash='line_dash', y_axes_title='Y Axis', legend_title='', font_size=30, marker_line_width=2.5, line_width=10, colors_dict=colors_dict)
            
            elif share_of_transport_type_type == 'all':
                
                # sum up, because 2w are used in freight and passenger:
                plot_data = plot_data.groupby(['Scenario', 'Economy', 'Date', 'Drive','line_dash']).sum().reset_index()
                fig = px.line(plot_data, x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)

                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['share_of_transport_type_all'] = [fig, title, PLOTTED]
                if WRITE_HTML:
                    write_graph_to_html(config, filename=f'share_of_transport_type_all_{scenario}.html', graph_type='line', plot_data=plot_data,economy=economy, x='Date', y='Value', color='Drive', title='Default Title', line_dash='line_dash', y_axes_title='Y Axis', legend_title='', font_size=30, marker_line_width=2.5, line_width=10, colors_dict=colors_dict)
            
            #############
            else:
                breakpoint()
                raise ValueError('share_of_transport_type_type must be either passenger or freight')
    
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(plot_data['Drive'].unique().tolist())
    return fig_dict, color_preparation_list


###################################################
def plot_share_of_transport_type_non_road(config, ECONOMY_IDs, new_sales_shares_all_plot_drive_shares_df, fig_dict, color_preparation_list, colors_dict, WRITE_HTML=True):
    PLOTTED=True
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares_df[new_sales_shares_all_plot_drive_shares_df['Medium']!='road'].copy()
    
    for scenario in new_sales_shares_all_plot_drive_shares['Scenario'].unique():
        new_sales_shares_all_plot_drive_shares_scenario = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Scenario']==scenario)].copy()
        ###        
        
        #times shares by 100
        new_sales_shares_all_plot_drive_shares_scenario['Value'] = new_sales_shares_all_plot_drive_shares_scenario['Value']*100
                
        for economy in ECONOMY_IDs:
            plot_data =  new_sales_shares_all_plot_drive_shares_scenario.loc[(new_sales_shares_all_plot_drive_shares_scenario['Economy']==economy)].copy()
            # Group by 'Drive' and filter out groups where all values are 0
            groups = plot_data.groupby(['Drive', 'Transport Type'])
            plot_data = groups.filter(lambda x: not all(x['Value'] == 0))
            
            plot_data.sort_values(by=['Date'], inplace=True)
            # elif share_of_transport_type_type == 'all':
            title = f'Share of new activity for non road (%)'
            # sum up, because 2w are used in freight and passenger:
            plot_data = plot_data.groupby(['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive']).sum(numeric_only=True).reset_index()
            fig = px.line(plot_data, x='Date', y='Value', color='Drive', title=title, line_dash='Transport Type', color_discrete_map=colors_dict)

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['non_road_share_of_transport_type'] = [fig, title, PLOTTED]
            
            if WRITE_HTML:
                write_graph_to_html(config, filename=f'non_road_share_of_transport_type_{scenario}.html', graph_type='line', plot_data=plot_data,economy=economy, x='Date', y='Value', color='Drive', title=title, line_dash='Transport Type', y_axes_title='%', legend_title='', font_size=30, marker_line_width=2.5, line_width=10, colors_dict=colors_dict)
            # #############
            # else:
            #     raise ValueError('share_of_transport_type_type must be either passenger or freight')
    
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    try:
        color_preparation_list.append(plot_data['Drive'].unique().tolist())
    except:
        pass
    return fig_dict, color_preparation_list


def plot_share_of_vehicle_type_by_transport_type(config, ECONOMY_IDs, new_sales_shares_all_plot_drive_shares_df, stocks_df, fig_dict, color_preparation_list, colors_dict, share_of_transport_type_type, INCLUDE_GENERAL_DRIVE_TYPES=False, WRITE_HTML=True):
    PLOTTED=True
    
    #This data is in terms of transport type, so will need to normalise it to vehicle type by summing up the shares for each vehicle type and dividing individual shares by their sum
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares_df.copy()
    stocks = stocks_df.copy()
    
    stocks, new_sales_shares_all_plot_drive_shares = remap_stocks_and_sales_based_on_economy(config, stocks, new_sales_shares_all_plot_drive_shares)
    high_gas_reliance_economies = identify_high_gas_reliance_economies(config, stocks, X=.1)
    if INCLUDE_GENERAL_DRIVE_TYPES:
        #use categories: gasoline, diesel, ev, fcev, other
        
        drive_mapping = {
            'ice_g':'gasoline', 'ice_d':'diesel', 'phev_d':'new', 'phev_g':'new', 'bev':'new', 'fcev':'new', 'cng':'gas', 'lpg':'gas'}
        new_sales_shares_all_plot_drive_shares['Drive'] = new_sales_shares_all_plot_drive_shares['Drive'].map(drive_mapping)
        # new_sales_shares_all_plot_drive_shares['Vehicle Type'] = new_sales_shares_all_plot_drive_shares['Drive'] + '_' + new_sales_shares_all_plot_drive_shares['Vehicle Type']
        
        stocks['Drive'] = stocks['Drive'].map(drive_mapping)
        # stocks['Vehicle Type'] = stocks['Drive'] + '_' + stocks['Vehicle Type']
        #also remap the vehicle types so its a bit mroe simpl. try a 'heavy' vs 'light' approach
        vehicle_type_mapping = {
            'lt':'light', 'suv':'light', 'car':'light', 'ht':'heavy', 'mt':'heavy', 'bus':'heavy', '2w':'light', 'lcv':'light', 'trucks':'heavy', 'lpv':'light'}
        new_sales_shares_all_plot_drive_shares['Vehicle Type'] = new_sales_shares_all_plot_drive_shares['Vehicle Type'].map(vehicle_type_mapping)
        stocks['Vehicle Type'] = stocks['Vehicle Type'].map(vehicle_type_mapping)
        
    new_sales_shares_all_plot_drive_shares['Value'] = new_sales_shares_all_plot_drive_shares.groupby(['Date','Economy', 'Scenario', 'Transport Type', 'Vehicle Type'], group_keys=False)['Value'].transform(lambda x: x/x.sum())
    
    new_sales_shares_all_plot_drive_shares['line_dash'] = 'sales'
    
    stocks['Value'] = stocks.groupby(['Scenario', 'Economy', 'Date', 'Transport Type','Vehicle Type'], group_keys=False)['Value'].apply(lambda x: x/x.sum(numeric_only=True))
    stocks['line_dash'] = 'stocks'
    
    for scenario in new_sales_shares_all_plot_drive_shares['Scenario'].unique():
        new_sales_shares_all_plot_drive_shares_scenario = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Scenario']==scenario)]
        stocks_scen = stocks.loc[(stocks['Scenario']==scenario)].copy()
        ###
        
        #then concat the two dataframes
        new_sales_shares_all_plot_drive_shares_scenario = pd.concat([new_sales_shares_all_plot_drive_shares_scenario, stocks_scen])
        
        #times shares by 100
        new_sales_shares_all_plot_drive_shares_scenario['Value'] = new_sales_shares_all_plot_drive_shares_scenario['Value']*100
                
        for economy in ECONOMY_IDs:
            plot_data =  new_sales_shares_all_plot_drive_shares_scenario.loc[(new_sales_shares_all_plot_drive_shares_scenario['Economy']==economy)].copy()

            # #also plot the data like the iea does. So plot the data for 2022 and previous, then plot for the follwoign eyars: [2025, 2030, 2035, 2040, 2050, 2060]. This helps to keep the plot clean too
            # plot_data = plot_data.apply(lambda x: x if x['Date'] <= 2022 or x['Date'] in [2025, 2030, 2035, 2040, 2050, 2060, 2070, 2080,2090, 2100] else 0, axis=1)
            #drop all drives except bev and fcev
            if not INCLUDE_GENERAL_DRIVE_TYPES:
                if economy in high_gas_reliance_economies:
                    plot_data = plot_data.loc[(plot_data['Drive'].isin(['phev_g','phev','phev_d', 'bev','fcev','cng','lpg']))].copy()
                    #map gas to gas
                    plot_data['Drive'] = plot_data['Drive'].replace({'cng':'gas', 'lpg':'gas'})
                else:
                    plot_data = plot_data.loc[(plot_data['Drive'].isin(['phev_g','phev','phev_d', 'bev','fcev']))].copy()
                    
                #concat drive and vehicle type
                plot_data['Drive'] = plot_data['Drive'] + ' ' + plot_data['Vehicle Type']
            else:#actually change the line dash to drive, change drive to vehicle type and remove the sales rows
                plot_data = plot_data.loc[(plot_data['line_dash']!='sales')].copy()
                plot_data['line_dash'] = plot_data['Drive']
                plot_data['Drive'] = plot_data['Vehicle Type']
                
            # Group by 'Drive' and filter out groups where all values are 0
            groups = plot_data.groupby(['Drive', 'line_dash'])
            plot_data = groups.filter(lambda x: not all(x['Value'] == 0))
            
            #sort by date col
            plot_data.sort_values(by=['Date'], inplace=True)
            #############
            #now plot
            if share_of_transport_type_type == 'passenger':
                
                if not INCLUDE_GENERAL_DRIVE_TYPES:
                    title = f'Sales/stock shares (passenger) (%)'
                else:
                    title = f'Stock shares by broad type (passenger) (%)'

                fig = px.line(plot_data[plot_data['Transport Type']=='passenger'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)
                ###
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][f'share_of_vehicle_type_by_transport_type_passenger_{INCLUDE_GENERAL_DRIVE_TYPES}'] = [fig, title, PLOTTED]
                
                #############
            elif share_of_transport_type_type == 'freight':
                
                if not INCLUDE_GENERAL_DRIVE_TYPES:
                    title = f'Sales/stock shares (freight) (%)'
                else:
                    title = f'Stock shares by broad type (freight) (%)'

                fig = px.line(plot_data[plot_data['Transport Type']=='freight'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][f'share_of_vehicle_type_by_transport_type_freight_{INCLUDE_GENERAL_DRIVE_TYPES}'] = [fig, title, PLOTTED]
            elif share_of_transport_type_type == 'all':
                # breakpoint()#phil is being wierd.
                # sum up, because 2w are used in freight and passenger:
                plot_data = plot_data.groupby(['Scenario', 'Economy', 'Date', 'Drive','line_dash']).sum().reset_index()
                if not INCLUDE_GENERAL_DRIVE_TYPES:
                    title = f'Sales/stock shares (%)'
                else:
                    title = f'Stock shares by broad type (%)'

                fig = px.line(plot_data, x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)
                ###
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][f'share_of_vehicle_type_by_transport_type_all_{INCLUDE_GENERAL_DRIVE_TYPES}'] = [fig, title, PLOTTED]
                if WRITE_HTML:
                    write_graph_to_html(config, filename=f'share_of_vehicle_type_by_transport_type_all_{scenario}.html', graph_type= 'line', plot_data=plot_data, economy=economy, x='Date', y='Value', color='Drive', title=f'Sales/stock shares (%)', line_dash='line_dash', y_axes_title='%', legend_title='', font_size=30, colors_dict=colors_dict)
            else: 
                raise ValueError('share_of_transport_type_type must be either passenger or freight')
            #############
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(plot_data['Drive'].unique().tolist())
    
    return fig_dict,color_preparation_list
            

def plot_share_of_vehicle_type_by_transport_type_both_on_one_graph(config, ECONOMY_IDs, new_sales_shares_all_plot_drive_shares_df, stocks_df, fig_dict, color_preparation_list, colors_dict):
    PLOTTED=True
    #This data is in terms of transport type, so will need to normalise it to vehicle type by summing up the shares for each vehicle type and dividing individual shares by their sum

    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares_df.copy()
    stocks = stocks_df.copy()
    
    stocks, new_sales_shares_all_plot_drive_shares = remap_stocks_and_sales_based_on_economy(config, stocks, new_sales_shares_all_plot_drive_shares)
    high_gas_reliance_economies = identify_high_gas_reliance_economies(config, stocks, X=.1)
    new_sales_shares_all_plot_drive_shares['Value'] = new_sales_shares_all_plot_drive_shares.groupby(['Date','Economy', 'Scenario', 'Transport Type', 'Vehicle Type'])['Value'].transform(lambda x: x/x.sum())
    
    stocks['Value'] = stocks.groupby(['Scenario', 'Economy', 'Date', 'Transport Type','Vehicle Type'])['Value'].apply(lambda x: x/x.sum())
    stocks['line_dash'] = 'stocks'
    new_sales_shares_all_plot_drive_shares['line_dash'] = 'sales'
            
    for scenario in new_sales_shares_all_plot_drive_shares['Scenario'].unique():
        new_sales_shares_all_plot_drive_shares_scenario = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Scenario']==scenario)]
        stocks_scen = stocks.loc[(stocks['Scenario']==scenario)].copy()
        ###
        #then concat the two dataframes
        new_sales_shares_all_plot_drive_shares_scenario = pd.concat([new_sales_shares_all_plot_drive_shares_scenario, stocks_scen])
        
        #times shares by 100
        new_sales_shares_all_plot_drive_shares_scenario['Value'] = new_sales_shares_all_plot_drive_shares_scenario['Value']*100
                
        for economy in ECONOMY_IDs:
            plot_data =  new_sales_shares_all_plot_drive_shares_scenario.loc[(new_sales_shares_all_plot_drive_shares_scenario['Economy']==economy)].copy()

            # #also plot the data like the iea does. So plot the data for 2022 and previous, then plot for the follwoign eyars: [2025, 2030, 2035, 2040, 2050, 2060]. This helps to keep the plot clean too
            # plot_data = plot_data.apply(lambda x: x if x['Date'] <= 2022 or x['Date'] in [2025, 2030, 2035, 2040, 2050, 2060, 2070, 2080,2090, 2100] else 0, axis=1)
            if economy in high_gas_reliance_economies:
                plot_data['Drive'] = plot_data['Drive'].replace({'cng':'gas', 'lpg':'gas'})
                plot_data = plot_data.loc[(plot_data['Drive']=='bev') | (plot_data['Drive']=='fcev') | (plot_data['Drive']=='gas')].copy()
            else:
                #drop all drives except bev and fcev
                plot_data = plot_data.loc[(plot_data['Drive']=='bev') | (plot_data['Drive']=='fcev')].copy()

            #concat drive and vehicle type
            plot_data['Drive'] = plot_data['Drive'] + ' ' + plot_data['Vehicle Type']
            
            # Group by 'Drive' and filter out groups where all 'Energy' values are 0
            groups = plot_data.groupby(['Drive','line_dash'])
            plot_data = groups.filter(lambda x: not all(x['Value'] == 0))
            
            #sort by date col
            plot_data.sort_values(by=['Date'], inplace=True)
            #############
            #now plot
            
            title = f'Sales and stock shares (%)'

            fig = px.line(plot_data, x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)
            ###
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['share_of_vehicle_type_by_transport_type_on_one_graph'] = [fig, title, PLOTTED]
            
            #############
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(plot_data['Drive'].unique().tolist())
    
    return fig_dict,color_preparation_list

def share_of_sum_of_vehicle_types_by_transport_type(config, ECONOMY_IDs, new_sales_shares_all_plot_drive_shares_df, stocks_df, fig_dict, color_preparation_list, colors_dict, share_of_transport_type_type, WRITE_HTML=True):
    PLOTTED=True
    #i think that maybe stocks % can be higher than sales % here because of turnvoer rates. hard to get it correct right now
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares_df.copy()
    stocks = stocks_df.copy()
    high_gas_reliance_economies = identify_high_gas_reliance_economies(config, stocks, X=.1)
    #make phev_d and phev_g into phev
    new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Drive']=='phev_d') | (new_sales_shares_all_plot_drive_shares['Drive']=='phev_g'), 'Drive'] = 'phev'
    stocks.loc[(stocks['Drive']=='phev_d') | (stocks['Drive']=='phev_g'), 'Drive'] = 'phev'
    
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares[['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive', 'Value']].groupby(['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive'], group_keys=False).sum().reset_index()
        
    new_sales_shares_all_plot_drive_shares['line_dash'] = 'sales'
    
    stocks = stocks[['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive','Value']].groupby(['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive'], group_keys=False).sum().reset_index()
    stocks['Value'] = stocks.groupby(['Scenario', 'Economy', 'Date', 'Transport Type'], group_keys=False)['Value'].apply(lambda x: x/x.sum(numeric_only=True))
    stocks['line_dash'] = 'stocks' 
    for scenario in new_sales_shares_all_plot_drive_shares['Scenario'].unique():
        new_sales_shares_all_plot_drive_shares_scenario = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Scenario']==scenario)]
        stocks_scen = stocks.loc[(stocks['Scenario']==scenario)].copy()
        ###
        
        #then concat the two dataframes
        new_sales_shares_all_plot_drive_shares_scenario = pd.concat([new_sales_shares_all_plot_drive_shares_scenario, stocks_scen])
        
                
        for economy in ECONOMY_IDs:
            plot_data =  new_sales_shares_all_plot_drive_shares_scenario.loc[(new_sales_shares_all_plot_drive_shares_scenario['Economy']==economy)].copy()

            # #also plot the data like the iea does. So plot the data for 2022 and previous, then plot for the follwoign eyars: [2025, 2030, 2035, 2040, 2050, 2060]. This helps to keep the plot clean too
            # plot_data = plot_data.apply(lambda x: x if x['Date'] <= 2022 or x['Date'] in [2025, 2030, 2035, 2040, 2050, 2060, 2070, 2080,2090, 2100] else 0, axis=1)
            if economy in high_gas_reliance_economies:
                plot_data['Drive'] = plot_data['Drive'].replace({'cng':'gas', 'lpg':'gas'})
                plot_data = plot_data.loc[(plot_data['Drive']=='bev') | (plot_data['Drive']=='phev') | (plot_data['Drive']=='fcev') | (plot_data['Drive']=='gas')].copy()
            else:
                #drop all drives except bev and fcev
                plot_data = plot_data.loc[(plot_data['Drive']=='bev') | (plot_data['Drive']=='fcev') | (plot_data['Drive']=='phev')].copy()
            
            # Group by 'Drive' and filter out groups where all 'Energy' values are 0
            groups = plot_data.groupby(['Drive', 'line_dash'])
            plot_data = groups.filter(lambda x: not all(x['Value'] == 0))
            
            #sort by date col
            plot_data.sort_values(by=['Date'], inplace=True)
            
            #times values by 100
            plot_data['Value'] = plot_data['Value']*100
            #############
            #now plot
            if share_of_transport_type_type == 'passenger':
                title = f'Sales/stock shares - passenger (%)'

                fig = px.line(plot_data[plot_data['Transport Type']=='passenger'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['sum_of_vehicle_types_by_transport_type_passenger'] = [fig, title, PLOTTED]
                
                if WRITE_HTML:
                    write_graph_to_html(config, filename=f'sum_of_vehicle_types_by_transport_type_passenger{scenario}.html', graph_type= 'line', plot_data=plot_data, economy=economy, x='Date', y='Value', color='Drive', title=f'Sales/stock shares (%)', line_dash='line_dash', y_axes_title='%', legend_title='', font_size=30, colors_dict=colors_dict)
                #############
            elif share_of_transport_type_type == 'freight':
                title = f'Sales/stock shares - freight (%)'

                fig = px.line(plot_data[plot_data['Transport Type']=='freight'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['sum_of_vehicle_types_by_transport_type_freight'] = [fig, title, PLOTTED]
                if WRITE_HTML:
                    write_graph_to_html(config, filename=f'sum_of_vehicle_types_by_transport_type_freight{scenario}.html', graph_type= 'line', plot_data=plot_data, economy=economy, x='Date', y='Value', color='Drive', title=f'Sales/stock shares (%)', line_dash='line_dash', y_axes_title='%', legend_title='', font_size=30, colors_dict=colors_dict)
            elif share_of_transport_type_type == 'all':
                title = 'Sales/stock share (%)'
                #concat drive and transport type
                plot_data['Drive'] = plot_data['Drive'] + ' ' + plot_data['Transport Type']
                fig = px.line(plot_data, x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['sum_of_vehicle_types_by_transport_type_all'] = [fig, title, PLOTTED]
                if WRITE_HTML:
                    write_graph_to_html(config, filename=f'sum_of_vehicle_types_by_transport_type_all_{scenario}.html', graph_type= 'line', plot_data=plot_data, economy=economy, x='Date', y='Value', color='Drive', title=f'Sales/stock shares (%)', line_dash='line_dash', y_axes_title='%', legend_title='', font_size=30, colors_dict=colors_dict)
            else:
                raise ValueError('share_of_transport_type_type must be passenger or freight')
            #############

    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(plot_data['Drive'].unique().tolist())
    
    return fig_dict, color_preparation_list
###################################################



###################################################
def energy_use_by_fuel_type(config, ECONOMY_IDs, energy_output_for_outlook_data_system_tall_df, fig_dict, color_preparation_list, colors_dict, transport_type, medium, WRITE_HTML=False):
    PLOTTED=True
    energy_output_for_outlook_data_system_tall = energy_output_for_outlook_data_system_tall_df.copy()
    if medium == 'road':
        energy_output_for_outlook_data_system_tall = energy_output_for_outlook_data_system_tall.loc[(energy_output_for_outlook_data_system_tall['Medium']=='road')].copy()
    #load in data and recreate plot, as created in all_economy_graphs
    #loop through scenarios and grab the data for each scenario:
    
    energy_use_by_fuel_type= energy_output_for_outlook_data_system_tall[['Economy', 'Scenario','Date', 'Fuel', 'Transport Type','Energy']].groupby(['Economy', 'Scenario','Date','Transport Type', 'Fuel']).sum().reset_index().copy()
    energy_use_by_fuel_type['Measure'] = 'Energy'
    energy_use_by_fuel_type['Unit'] = energy_use_by_fuel_type['Measure'].map(config.measure_to_unit_concordance_dict)
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        energy_use_by_fuel_type_scen = energy_use_by_fuel_type.loc[(energy_use_by_fuel_type['Scenario']==scenario)].copy()
        
        for economy in ECONOMY_IDs:
            #filter to economy
            energy_use_by_fuel_type_economy = energy_use_by_fuel_type_scen.loc[(energy_use_by_fuel_type_scen['Economy']==economy)].copy()
            
            # Group by 'Fuel' and filter out groups where all 'Energy' values are 0
            groups = energy_use_by_fuel_type_economy.groupby('Fuel')
            energy_use_by_fuel_type_economy = groups.filter(lambda x: not all(x['Energy'] == 0))
            
            # calculate total 'Energy' for each 'Fuel' 
            total_energy_per_fuel = energy_use_by_fuel_type_economy.groupby('Fuel')['Energy'].sum()
            
            # Create an ordered category of 'Fuel' labels sorted by total 'Energy'. THIS helps make plot easyer to read
            energy_use_by_fuel_type_economy['Fuel'] = pd.Categorical(
                energy_use_by_fuel_type_economy['Fuel'],
                categories = total_energy_per_fuel.sort_values(ascending=False).index,
                ordered=True
            )

            # Now sort the DataFrame by the 'Fuel' column:
            energy_use_by_fuel_type_economy.sort_values(by='Fuel', inplace=True)
            
            if transport_type=='passenger':
                #now plot
                fig = px.area(energy_use_by_fuel_type_economy.loc[energy_use_by_fuel_type_economy['Transport Type']=='passenger'], x='Date', y='Energy', color='Fuel', title='Energy by Fuel', color_discrete_map=colors_dict)
                
                #add units to y col
                if medium == 'road':
                    title_text = 'Road energy by Fuel {} ({})'.format(transport_type, energy_use_by_fuel_type_economy['Unit'].unique()[0])
                else:
                    title_text = 'Energy by Fuel {} ({})'.format(transport_type, energy_use_by_fuel_type_economy['Unit'].unique()[0])
                    
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][f'energy_use_by_fuel_type_passenger_{medium}'] = [fig, title_text, PLOTTED]
                
                if WRITE_HTML:
                    # #drop any fuel types which take < 0.0001% of the total energy
                    energy_use_by_fuel_type_economy['Fuel'] = energy_use_by_fuel_type_economy['Fuel'].astype('object')
                    energy_use_by_fuel_type_economy = energy_use_by_fuel_type_economy.loc[energy_use_by_fuel_type_economy['Energy'] > 1]
                    #now plot
                    write_graph_to_html(config, filename=f'energy_use_by_fuel_type_passenger_{scenario}.html', graph_type= 'area', plot_data=energy_use_by_fuel_type_economy.loc[energy_use_by_fuel_type_economy['Transport Type']=='passenger'],economy=economy, x='Date', y='Energy', color='Fuel', title=f'Passenger road energy by fuel', y_axes_title='PJ', legend_title='Fuel Type', colors_dict=colors_dict, font_size=35)
                
            elif transport_type == 'freight':
                #now plot
                fig = px.area(energy_use_by_fuel_type_economy.loc[energy_use_by_fuel_type_economy['Transport Type']=='freight'], x='Date', y='Energy', color='Fuel', title='Energy by Fuel', color_discrete_map=colors_dict)
                
                #add units to y col
                if medium == 'road':
                    title_text = 'Road energy by Fuel {} ({})'.format(transport_type, energy_use_by_fuel_type_economy['Unit'].unique()[0])
                else:
                    title_text = 'Energy by Fuel {} ({})'.format(transport_type, energy_use_by_fuel_type_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][f'energy_use_by_fuel_type_freight_{medium}'] = [fig, title_text, PLOTTED]
                if WRITE_HTML:
                    write_graph_to_html(config, filename=f'energy_use_by_fuel_type_freight_{scenario}.html', graph_type= 'area', plot_data=energy_use_by_fuel_type_economy.loc[energy_use_by_fuel_type_economy['Transport Type']=='freight'],economy=economy, x='Date', y='Energy', color='Fuel', title=f'Freight road energy by fuel', y_axes_title='PJ', legend_title='Fuel Type', colors_dict=colors_dict, font_size=35)
                
            elif transport_type == 'all':
                #sum across transport types
                energy_use_by_fuel_type_economy = energy_use_by_fuel_type_economy.groupby(['Economy', 'Date', 'Fuel','Unit']).sum(numeric_only =True).reset_index()
                #now plot
                fig = px.area(energy_use_by_fuel_type_economy, x='Date', y='Energy', color='Fuel', title='Energy by Fuel', color_discrete_map=colors_dict)
                
                #add units to y col
                if medium == 'road':
                    title_text = 'Road energy by Fuel ({})'.format(energy_use_by_fuel_type_economy['Unit'].unique()[0])
                else:
                    title_text = 'Energy by Fuel ({})'.format(energy_use_by_fuel_type_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][f'energy_use_by_fuel_type_all_{medium}'] = [fig, title_text, PLOTTED]
                if WRITE_HTML:
                    write_graph_to_html(config, filename=f'energy_use_by_fuel_type_all_{scenario}.html', graph_type= 'area', plot_data=energy_use_by_fuel_type_economy,economy=economy, x='Date', y='Energy', color='Fuel', title=f'All energy by fuel', y_axes_title='PJ', legend_title='Fuel Type', colors_dict=colors_dict, font_size=35)
            else:
                raise ValueError('transport_type must be passenger, all or freight')
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(energy_use_by_fuel_type_economy['Fuel'].unique().tolist())
    return fig_dict, color_preparation_list


def create_vehicle_type_stocks_plot(config, ECONOMY_IDs, stocks_df, fig_dict, color_preparation_list, colors_dict, WRITE_HTML=True):
    PLOTTED=True
    #loop through scenarios and grab the data for each scenario:
    
    #create a new df with only the data we need:
    stocks = stocks_df.copy()
    stocks = stocks[['Economy', 'Date', 'Vehicle Type','Scenario', 'Value']].groupby(['Economy', 'Date','Scenario', 'Vehicle Type']).sum().reset_index()
    stocks['Measure'] = 'Stocks'
    stocks['Unit'] = stocks['Measure'].map(config.measure_to_unit_concordance_dict)
    
    stocks = remap_vehicle_types(config, stocks, value_col='Value', new_index_cols = ['Date', 'Vehicle Type','Unit','Scenario', 'Economy'], vehicle_type_mapping_set='original')
    
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        stocks_scenario = stocks.loc[(stocks['Scenario']==scenario)].copy()
        
        for economy in ECONOMY_IDs:
            #filter to economy
            stocks_economy = stocks_scenario.loc[stocks_scenario['Economy']==economy].copy()
            
            # #also if stocks of 2w are more than 50% of total stocks then recategorise the vehicle types a bit
            # if stocks_economy.loc[stocks_economy['Vehicle Type']=='2w']['Value'].sum() > 0.5*stocks_economy.loc[stocks_economy['Vehicle Type']!='2w']['Value'].sum():
            # ##
            
            stocks_economy = stocks_economy.groupby('Vehicle Type').filter(lambda x: not all(x['Value'] == 0))
            
            #sort by date
            # stocks_economy = stocks_economy.sort_values(by='Date')
            #now plot
            fig = px.line(stocks_economy, x='Date', y='Value', color='Vehicle Type', color_discrete_map=colors_dict)
            title_text = 'Vehicle stocks (Millions)'#.format(stocks_economy['Unit'].unique()[0])
            #add units to y col
            # fig.update_yaxes(title_text='Freight Tonne Km ({})'.format(stocks_economy['Unit'].unique()[0]))

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['vehicle_type_stocks'] = [fig, title_text, PLOTTED]
            if WRITE_HTML:
                write_graph_to_html(config, filename=f'vehicle_type_stocks_{scenario}.html', graph_type= 'line', plot_data=stocks_economy,economy=economy, x='Date', y='Value', color='Vehicle Type', title=f'Vehicle stocks', y_axes_title='Millions', legend_title='Vehicle Type', colors_dict=colors_dict, font_size=35)
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(stocks_economy['Vehicle Type'].unique().tolist())
    return fig_dict, color_preparation_list

def plot_share_of_vehicle_type_activity(config, ECONOMY_IDs, model_output_detailed_df, fig_dict, color_preparation_list, colors_dict, transport_type, WRITE_HTML=True):
    PLOTTED = True
    share_of_activity = model_output_detailed_df.copy()
    share_of_activity = share_of_activity.loc[share_of_activity['Medium'] == 'road'].copy()
    share_of_activity = share_of_activity[['Economy', 'Date', 'Vehicle Type', 'Scenario', 'Transport Type', 'Activity']].groupby(['Economy', 'Date', 'Scenario', 'Transport Type', 'Vehicle Type']).sum().reset_index()
    share_of_activity['Measure'] = 'Share of Activity'
    share_of_activity['Unit'] = '%'
    
    share_of_activity['Activity'] = share_of_activity.groupby(['Date', 'Transport Type', 'Scenario', 'Economy'])['Activity'].transform(lambda x: x / x.sum())
    share_of_activity['Activity'] = share_of_activity['Activity'] * 100
    
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        share_of_activity_scenario = share_of_activity.loc[share_of_activity['Scenario'] == scenario].copy()
        
        for economy in ECONOMY_IDs:
            share_of_activity_economy = share_of_activity_scenario.loc[share_of_activity_scenario['Economy'] == economy].copy()
            share_of_activity_economy = share_of_activity_economy.groupby(['Transport Type', 'Vehicle Type']).filter(lambda x: not all(x['Activity'] == 0))
            
            if transport_type == 'passenger':
                share_of_activity_economy = share_of_activity_economy.loc[share_of_activity_economy['Transport Type'] == 'passenger'].copy()
                title_text = 'Vehicle type share of activity (Passenger) (%)'
            elif transport_type == 'freight':
                share_of_activity_economy = share_of_activity_economy.loc[share_of_activity_economy['Transport Type'] == 'freight'].copy()
                title_text = 'Vehicle type share of activity (Freight) (%)'
            elif transport_type == 'all':
                title_text = 'Vehicle type share of activity (%)'
            
            fig = px.line(share_of_activity_economy, x='Date', y='Activity', color='Vehicle Type', line_dash='Transport Type', color_discrete_map=colors_dict)
            fig_dict[economy][scenario][f'share_of_vehicle_type_activity_{transport_type}'] = [fig, title_text, PLOTTED]
            
            if WRITE_HTML:
                write_graph_to_html(config, filename=f'share_of_vehicle_type_activity_{scenario}_{transport_type}.html', graph_type='line', plot_data=share_of_activity_economy, economy=economy, x='Date', y='Activity', color='Vehicle Type', title=title_text, line_dash='Transport Type', y_axes_title='%', legend_title='Vehicle Type', font_size=30, colors_dict=colors_dict)
    
    color_preparation_list.append(share_of_activity_economy['Vehicle Type'].unique().tolist())
    return fig_dict, color_preparation_list

def freight_tonne_km_by_drive(config, ECONOMY_IDs, model_output_detailed, fig_dict, color_preparation_list, colors_dict, medium, WRITE_HTML=True):
    PLOTTED=True
    
    fkm = model_output_detailed.loc[model_output_detailed['Transport Type']=='freight'].rename(columns={'Activity':'freight_tonne_km'}).copy()
    if medium == 'road':
        fkm = fkm.loc[fkm['Medium']=='road'].copy()
    else:
        fkm.loc[fkm['Medium'] != 'road', 'Drive'] = fkm.loc[fkm['Medium'] != 'road', 'Medium']
        
    fkm = fkm[['Economy', 'Date', 'Drive','Scenario', 'freight_tonne_km']].groupby(['Economy', 'Date', 'Scenario','Drive']).sum().reset_index()

    #simplfiy drive type using remap_drive_types
    fkm = remap_drive_types(config, fkm, value_col='freight_tonne_km', new_index_cols = ['Economy', 'Date', 'Scenario','Drive'])
    
    #add units (by setting measure to Freight_tonne_km haha)
    fkm['Measure'] = 'Freight_tonne_km'
    #add units
    fkm['Unit'] = fkm['Measure'].map(config.measure_to_unit_concordance_dict)
    
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        freight_tonne_km_by_drive = fkm.loc[(fkm['Scenario']==scenario)].copy()

        for economy in ECONOMY_IDs:
            #filter to economy
            freight_tonne_km_by_drive_economy = freight_tonne_km_by_drive.loc[freight_tonne_km_by_drive['Economy']==economy].copy()
            freight_tonne_km_by_drive_economy = freight_tonne_km_by_drive_economy.groupby(['Drive']).filter(lambda x: not all(x['freight_tonne_km'] == 0))
            
            # calculate total 'freight_tonne_km' for each 'Drive' 
            total_freight_per_drive = freight_tonne_km_by_drive_economy.groupby('Drive')['freight_tonne_km'].sum()
            # #drop any 0's
            # total_freight_per_drive = total_freight_per_drive.loc[total_freight_per_drive.freight_tonne_km!=0]
            # Create an ordered category of 'Drive' labels sorted by total 'freight_tonne_km'
            freight_tonne_km_by_drive_economy['Drive'] = pd.Categorical(
                freight_tonne_km_by_drive_economy['Drive'],
                categories = total_freight_per_drive.sort_values(ascending=False).index,
                ordered=True
            )

            # Now you can sort your DataFrame by the 'Drive' column:
            freight_tonne_km_by_drive_economy.sort_values(by='Drive', inplace=True)

            #sort by date
            # freight_tonne_km_by_drive_economy = freight_tonne_km_by_drive_economy.sort_values(by='Date')
            #now plot
            fig = px.area(freight_tonne_km_by_drive_economy, x='Date', y='freight_tonne_km', color='Drive',color_discrete_map=colors_dict)
            
            if medium == 'road':
                title_text = 'Road Freight Tonne Km (Billions)'
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['freight_tonne_km_by_drive_road'] = [fig, title_text, PLOTTED]
            else:
                title_text = 'Freight Tonne Km (Billions)'#.format
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['freight_tonne_km_by_drive_all'] = [fig, title_text, PLOTTED]
            if WRITE_HTML:
                write_graph_to_html(config, filename=f'freight_tonne_km_by_drive_{scenario}.html', graph_type= 'area', plot_data=freight_tonne_km_by_drive_economy,economy=economy, x='Date', y='freight_tonne_km', color='Drive', title=f'Freight tonne km by drive', y_axes_title='Billions', legend_title='Drive Type', colors_dict=colors_dict, font_size=35)
                
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(freight_tonne_km_by_drive_economy['Drive'].unique().tolist())
    return fig_dict, color_preparation_list

def passenger_km_by_drive(config, ECONOMY_IDs, model_output_detailed, fig_dict, color_preparation_list, colors_dict, medium, WRITE_HTML=True):
    PLOTTED=True
    pkm = model_output_detailed.loc[model_output_detailed['Transport Type']=='passenger'].rename(columns={'Activity':'passenger_km'}).copy()
    
    if medium == 'road':
        pkm = pkm.loc[pkm['Medium']=='road'].copy()
    else:
        pkm.loc[pkm['Medium'] != 'road', 'Drive'] = pkm.loc[pkm['Medium'] != 'road', 'Medium']
    
    pkm = pkm[['Economy', 'Date', 'Drive','Scenario', 'passenger_km']].groupby(['Economy', 'Date','Scenario', 'Drive']).sum().reset_index()

    #simplfiy drive type using remap_drive_types
    pkm = remap_drive_types(config, pkm, value_col='passenger_km', new_index_cols = ['Economy', 'Date', 'Scenario','Drive'])
    
    #add units
    pkm['Measure'] = 'Passenger_km'
    pkm['Unit'] = pkm['Measure'].map(config.measure_to_unit_concordance_dict)
    
    # model_output_detailed.pkl
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        passenger_km_by_drive = pkm.loc[(pkm['Scenario']==scenario)].copy()
        for economy in ECONOMY_IDs:
            #filter to economy
            passenger_km_by_drive_economy = passenger_km_by_drive.loc[passenger_km_by_drive['Economy']==economy].copy()
            
            passenger_km_by_drive_economy = passenger_km_by_drive_economy.groupby(['Drive']).filter(lambda x: not all(x['passenger_km'] == 0))
            
            # calculate total 'passenger_km' for each 'Drive' 
            total_passenger_per_drive = passenger_km_by_drive_economy.groupby('Drive')['passenger_km'].sum()

            # Create an ordered category of 'Drive' labels sorted by total 'passenger_km'
            passenger_km_by_drive_economy['Drive'] = pd.Categorical(
            passenger_km_by_drive_economy['Drive'],
            categories = total_passenger_per_drive.sort_values(ascending=False).index,
            ordered=True
            )

            # Now sort the DataFrame by the 'Drive' column:
            passenger_km_by_drive_economy.sort_values(by='Drive', inplace=True)
            #sort by date

            # passenger_km_by_drive_economy = passenger_km_by_drive_economy.sort_values(by='Date')
            #now plot
            
            if medium == 'road':
                title_text = 'Road Passenger Km (Billions)'
            else:
                title_text = 'Passenger Km (Billions)'
            fig = px.area(passenger_km_by_drive_economy, x='Date', y='passenger_km', color='Drive', color_discrete_map=colors_dict, title=title_text)
            if medium == 'road':
                fig_dict[economy][scenario]['passenger_km_by_drive_road'] = [fig, title_text, PLOTTED]
            else:
                fig_dict[economy][scenario]['passenger_km_by_drive_all'] = [fig, title_text, PLOTTED]
            if WRITE_HTML:
                write_graph_to_html(config, filename=f'passenger_km_by_drive_{scenario}.html', graph_type= 'area', plot_data=passenger_km_by_drive_economy,economy=economy, x='Date', y='passenger_km', color='Drive', title=f'Passenger km by drive', y_axes_title='Billions', legend_title='Drive Type', colors_dict=colors_dict, font_size=35)
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(passenger_km_by_drive_economy['Drive'].unique().tolist())
    return fig_dict, color_preparation_list


def activity_growth(config, ECONOMY_IDs, model_output_detailed_df, fig_dict, color_preparation_list, colors_dict, RECALCULATE=True, SMOOTH=False, WRITE_HTML=True):
    PLOTTED=True
    #calcualte population growth and gdp growth as a percentage:
    # #first grasb only the data we need for this:
    # model_output_detailed_growth = model_output_detailed[['Economy', 'Date', 'Population', 'Gdp']].copy().drop_duplicates()
    #srot by date    
    model_output_detailed = model_output_detailed_df.copy()
    
    model_output_detailed['Medium'] = np.where(model_output_detailed['Medium']=='road', 'road', 'non_road')     
    model_output_detailed['Transport Type'] = model_output_detailed['Transport Type'] + ' ' + model_output_detailed['Medium']
    #to be safge we will recalculate the Activity_growth col
    if RECALCULATE:
        model_output_detailed = model_output_detailed[['Economy', 'Date', 'Transport Type','Scenario', 'Activity']].groupby(['Economy', 'Date','Scenario','Transport Type']).sum().reset_index()
        #calcualte activity growth
        model_output_detailed = model_output_detailed.sort_values(by='Date')
        model_output_detailed['Activity_growth'] = model_output_detailed.groupby(['Economy', 'Transport Type', 'Scenario'])['Activity'].pct_change().fillna(0)
        
        #save to x.scv
        # model_output_detailed.to_csv(config.root_dir + config.slash + 'model_output_detailed.csv', index=False)
        model_output_detailed.drop(columns=['Activity'], inplace=True)
        if SMOOTH:
            model_output_detailed['Activity_growth'] = model_output_detailed.groupby(['Economy', 'Transport Type', 'Scenario'])['Activity_growth'].rolling(5, center=True).mean().reset_index()['Activity_growth']
    else:
        model_output_detailed = model_output_detailed[['Economy', 'Date', 'Transport Type','Scenario', 'Activity_growth']].drop_duplicates()
    pop_and_gdp = model_output_detailed_df[['Economy', 'Date', 'Population', 'Gdp']].copy().drop_duplicates()
    #have to filter for only one value for each year as we are gettin duplicates because of system rounding errors.
    pop_and_gdp = pop_and_gdp.groupby(['Economy', 'Date']).mean().reset_index()
    #now calculate the growth rates
    pop_and_gdp['Population_growth'] = pop_and_gdp.groupby(['Economy'])['Population'].pct_change()
    pop_and_gdp['GDP_growth'] = pop_and_gdp.groupby(['Economy'])['Gdp'].pct_change()
    #we are getting weird spikes. if there are any growth higher than 0.5 then raise an error
    if pop_and_gdp['GDP_growth'].max() > 0.5:
        breakpoint()
        time.sleep(1)
        raise ValueError('GDP growth is too high')
       
    model_output_detailed=model_output_detailed.merge(pop_and_gdp[['Economy', 'Date', 'Population_growth', 'GDP_growth']], on=['Economy', 'Date'], how='left')
    
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        for economy in ECONOMY_IDs:
            
            model_output_detailed_scen_econ = model_output_detailed.loc[(model_output_detailed['Scenario']==scenario) & (model_output_detailed['Economy']==economy)].copy()
            
            #concat the transport type and medium after renaming medium to road or non_road  
                
            INDEX_COLS_TO_USE = ['Date', 'Transport Type']
            #convert to %
            model_output_detailed_scen_econ['Population_growth'] = (model_output_detailed_scen_econ['Population_growth'])*100
            model_output_detailed_scen_econ['GDP_growth'] = (model_output_detailed_scen_econ['GDP_growth'])*100
            model_output_detailed_scen_econ['Activity_growth'] = (model_output_detailed_scen_econ['Activity_growth'])*100
            
            #now drop all cols we dont need for activity growth
            model_output_detailed_scen_econ = model_output_detailed_scen_econ[INDEX_COLS_TO_USE + ['Population_growth', 'GDP_growth', 'Activity_growth']].copy().drop_duplicates()
            
            #melt so all measures in one col
            activity_growth = pd.melt(model_output_detailed_scen_econ, id_vars=INDEX_COLS_TO_USE, value_vars=['Population_growth', 'GDP_growth', 'Activity_growth'], var_name='Measure', value_name='Macro_growth')
            #we dont actually need more than one value for each year for population and gdp growthso set their transport type to all and then drop duplicates
            activity_growth.loc[activity_growth['Measure']!='Activity_growth', 'Transport Type'] = 'all'
            activity_growth = activity_growth.drop_duplicates()
            
            # #times macro growth by 100 to get percentage
            # activity_growth['Macro_growth'] = activity_growth['Macro_growth']*100
            
            # #add units (by setting measure to Freight_tonne_km haha)
            # activity_growth['Measure'] = 'Macro_growth'
            #add units
            activity_growth['Unit'] = '%'
            
            #drop any values for 2020 and 2021 since we have no growth for this year and 2021 is a bit weird bwcause of covid
            activity_growth = activity_growth.loc[activity_growth['Date']>2021].copy()
            
            activity_growth = activity_growth.groupby(['Measure', 'Transport Type']).filter(lambda x: not all(x['Macro_growth'] == 0))
            
            #lastly identify any values greater than 10 (10%) and remove them so we can see the other values better
            activity_growth = activity_growth.loc[activity_growth['Macro_growth']<10].copy()
            
            ###########################
            #add transport type to measure
            activity_growth['Measure'] = activity_growth['Measure'] + ' ' + activity_growth['Transport Type']
            #now plot
            fig = px.line(activity_growth, x='Date', y='Macro_growth',color='Measure', color_discrete_map=colors_dict)
            #add units to y col
            title_text = 'Activity Growth ({})'.format(activity_growth['Unit'].unique()[0])
            fig.update_yaxes(title_text=title_text)#not working for some reason

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['activity_growth'] = [fig, title_text, PLOTTED]
            
            if WRITE_HTML:
                write_graph_to_html(config, filename=f'activity_growth_{scenario}_{economy}.html', graph_type='line', plot_data=activity_growth, economy=economy, x='Date', y='Macro_growth', color='Measure', title=title_text, y_axes_title='%', legend_title='', font_size=30, colors_dict=colors_dict)
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(activity_growth['Measure'].unique().tolist())

    return fig_dict, color_preparation_list

def macro_lines(config, ECONOMY_IDs, growth_forecasts, fig_dict, color_preparation_list, colors_dict, measure, indexed=False, WRITE_HTML=True):
    """plot population, gdp, gdp per capita lines.

    Args:
        ECONOMY_IDs (_type_): _description_
        original_model_output_8th_df (_type_): _description_
        model_output_detailed (_type_): _description_
        growth_forecasts (_type_): _description_
        fig_dict (_type_): _description_
        color_preparation_list (_type_): _description_
        colors_dict (_type_): _description_
        indexed (bool, optional): _description_. Defaults to False.

    Returns:
        _type_: _description_
    """
    PLOTTED=True
    growth_forecasts_tall = growth_forecasts.melt(id_vars=['Date', 'Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive', 'Scenario'], var_name='Measure', value_name='Value')
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        growth_forecasts_scen = growth_forecasts_tall.loc[(growth_forecasts_tall['Scenario']==scenario)].copy()
        
        #and filter so data is less than config.GRAPHING_END_YEAR
        growth_forecasts_scen = growth_forecasts_scen.loc[(growth_forecasts_scen['Date']<=config.GRAPHING_END_YEAR)].copy()
        
        
        for economy in ECONOMY_IDs:
            #filter to economy
            growth_forecasts_scen_economy = growth_forecasts_scen.loc[growth_forecasts_scen['Economy']==economy].copy()

            #extract the measure we want
            if measure == 'population':
                growth_forecasts_scen_economy = growth_forecasts_scen_economy.loc[growth_forecasts_scen_economy['Measure']=='Population'].copy()
                #now plot
                fig = px.line(growth_forecasts_scen_economy, x='Date', y='Value',color='Measure', color_discrete_map=colors_dict)
                title_text = 'Population'
                fig.update_yaxes(title_text=title_text)#not working for some reason

            elif measure == 'gdp':
                growth_forecasts_scen_economy = growth_forecasts_scen_economy.loc[growth_forecasts_scen_economy['Measure']=='Gdp'].copy()
                #now plot
                fig = px.line(growth_forecasts_scen_economy, x='Date', y='Value',color='Measure', color_discrete_map=colors_dict)
                title_text = 'GDP'
                fig.update_yaxes(title_text=title_text)
            elif measure == 'gdp_per_capita':
                growth_forecasts_scen_economy = growth_forecasts_scen_economy.loc[growth_forecasts_scen_economy['Measure']=='Gdp_per_capita'].copy()
                #now plot
                fig = px.line(growth_forecasts_scen_economy, x='Date', y='Value',color='Measure', color_discrete_map=colors_dict)
                title_text = 'GDP per capita'
                fig.update_yaxes(title_text=title_text)
            
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario][f'macro_lines_{measure}'] = [fig, title_text, PLOTTED]
            
            if WRITE_HTML:
                write_graph_to_html(config, filename=f'macro_lines_{measure}_{scenario}_{economy}.html', graph_type='line', plot_data=growth_forecasts_scen_economy, economy=economy, x='Date', y='Value', color='Measure', title=title_text, y_axes_title=title_text, legend_title='', font_size=30, colors_dict=colors_dict)
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(growth_forecasts_scen_economy['Measure'].unique().tolist())
    
    return fig_dict, color_preparation_list

import os

def activity_and_macro_growth_lines(config, ECONOMY_IDs, original_model_output_8th_df, model_output_detailed, growth_forecasts, fig_dict, color_preparation_list, colors_dict, indexed=False, WRITE_HTML=True):
    """plot activity and macro lines, i.e. activity, and 

    Args:
        ECONOMY_IDs (_type_): _description_
        original_model_output_8th_df (_type_): _description_
        model_output_detailed (_type_): _description_
        growth_forecasts (_type_): _description_
        fig_dict (_type_): _description_
        color_preparation_list (_type_): _description_
        colors_dict (_type_): _description_
        indexed (bool, optional): _description_. Defaults to False.

    Returns:
        _type_: _description_
    """
    PLOTTED=True
    original_model_output_8th = original_model_output_8th_df.copy()
    #grab only the Activity then sum it by economy, scenario and date
    original_model_output_8th = original_model_output_8th[['Economy', 'Scenario', 'Date', 'Activity']].copy().drop_duplicates()
    original_model_output_8th = original_model_output_8th.groupby(['Economy', 'Scenario', 'Date']).sum().reset_index()
    #rename actovity to Activity_8th
    original_model_output_8th = original_model_output_8th.rename(columns={'Activity':'Activity_8th'})
    
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        model_output_detailed_scen = model_output_detailed.loc[(model_output_detailed['Scenario']==scenario)].copy()
        growth_forecasts_scen = growth_forecasts.loc[(growth_forecasts['Scenario']==scenario)].copy()
        ###
        #if scenario is Target then look for 'Carbon Neutral' in scenario name
        if scenario == 'Target':
            original_model_output_8th_scenario = original_model_output_8th.loc[original_model_output_8th['Scenario']=='Carbon Neutral'].copy()
        else:
            original_model_output_8th_scenario = original_model_output_8th.loc[original_model_output_8th['Scenario']==scenario].copy()
    
        #drop scenario col
        original_model_output_8th_scenario = original_model_output_8th_scenario.drop(columns=['Scenario'])
        
        ###
        original_growth_forecasts = growth_forecasts_scen[['Activity_growth','Date','Economy', 'Transport Type']].copy()
        #calcualte cumulative growth so it can be compared to activity when it is converted to indexed or growth:
        original_growth_forecasts['Activity_growth'] = original_growth_forecasts.groupby(['Economy', 'Transport Type'])['Activity_growth'].cumprod()
        #split into freight and passenger, if the values are differen then we will plot them sepeartely, if not just plot one:
        original_growth_forecasts = original_growth_forecasts.pivot(index=['Economy', 'Date'], columns='Transport Type', values='Activity_growth').reset_index()
        if original_growth_forecasts['freight'].equals(original_growth_forecasts['passenger']):
            PLOT_ORIGINAL_FORECASTS_BY_TTYPE = False
            original_growth_forecasts = original_growth_forecasts[['Economy', 'Date', 'freight']].copy().rename(columns={'freight':'Original_activity'})
        else:
            PLOT_ORIGINAL_FORECASTS_BY_TTYPE = True
            original_growth_forecasts_p = original_growth_forecasts[['Economy', 'Date', 'passenger']].copy().rename(columns={'passenger':'Original_activity_passenger'})
            original_growth_forecasts_f = original_growth_forecasts[['Economy', 'Date', 'freight']].copy().rename(columns={'freight':'Original_activity_freight'})
        ###
        
        
        freight_km = model_output_detailed_scen.loc[model_output_detailed_scen['Transport Type']=='freight'].rename(columns={'Activity':'freight_tonne_km'}).copy()
        passenger_km = model_output_detailed_scen.loc[model_output_detailed_scen['Transport Type']=='passenger'].rename(columns={'Activity':'passenger_km'}).copy()
        #calcualte population, gdp, freight tonne km and passenger km as an index:
        # #first grasb only the data we need for this:
        # model_output_detailed_growth = model_output_detailed[['Economy', 'Scenario', 'Date', 'Population', 'Gdp']].copy().drop_duplicates()
        #srot by date
        # def calc_index(df, col):
        #     df = df.sort_values(by='Date')
        #     df['Value'] = df[col]/df[col].iloc[0]
        #     df['Measure'] = '{}_index'.format(col)
        #     df.drop(columns=[col], inplace=True)
        #     return df

        def calc_index(df, col, normalised=True):
            if normalised:
                df = df.sort_values(by='Date')

                # Normalize the data separately for each economy
                df[col] = df.groupby('Economy')[col].transform(lambda x: (x - x.min()) / (x.max() - x.min()))

                # Index the data separately for each economy
                df['Value'] = df.groupby('Economy')[col].transform(lambda x: x / x.iloc[0])

                df['Measure'] = '{}_index'.format(col)
                df.drop(columns=[col], inplace=True)
            else:
                df = df.sort_values(by='Date')

                # Standardize the data separately for each economy
                df[col] = df.groupby('Economy')[col].transform(lambda x: (x - x.mean()) / x.std())

                # Index the data separately for each economy
                df['Value'] = df.groupby('Economy')[col].transform(lambda x: x / x.iloc[0])

                df['Measure'] = '{}_index'.format(col)
                df.drop(columns=[col], inplace=True)

            return df

        def calc_growth(df, col):
            df = df.sort_values(by='Date')

            # Calculate percent growth separately for each economy
            df['Value'] = df.groupby('Economy')[col].transform(lambda x: (x / x.iloc[0] - 1) * 100)

            df['Measure'] = '{}_growth'.format(col)
            df.drop(columns=[col], inplace=True)

            return df
        
        if indexed:
            population = calc_index(model_output_detailed_scen[['Population','Date','Economy']].drop_duplicates(),'Population')
            gdp = calc_index(model_output_detailed_scen[['Gdp','Date','Economy']].drop_duplicates(),'Gdp')
            freight_km = calc_index(freight_km[['freight_tonne_km','Date','Economy']].drop_duplicates().dropna().groupby(['Economy','Date']).sum().reset_index(),'freight_tonne_km')
            passenger_km = calc_index(passenger_km[['passenger_km','Date','Economy']].drop_duplicates().dropna().groupby(['Economy','Date']).sum().reset_index(),'passenger_km')
            original_model_output_8th_scenario = calc_index(original_model_output_8th_scenario,'Activity_8th')
            if PLOT_ORIGINAL_FORECASTS_BY_TTYPE:
                original_growth_forecasts_p = calc_index(original_growth_forecasts_p,'Original_activity_passenger')
                original_growth_forecasts_f = calc_index(original_growth_forecasts_f,'Original_activity_passenger')
            else:
                original_growth_forecasts = calc_index(original_growth_forecasts,'Original_activity')
                

        else:#calc growth
                
            population = calc_growth(model_output_detailed_scen[['Population','Date','Economy']].drop_duplicates(),'Population')
            gdp = calc_growth(model_output_detailed_scen[['Gdp','Date','Economy']].drop_duplicates(),'Gdp')
            freight_km = calc_growth(freight_km[['freight_tonne_km','Date','Economy']].drop_duplicates().dropna().groupby(['Economy','Date']).sum().reset_index(),'freight_tonne_km')
            passenger_km = calc_growth(passenger_km[['passenger_km','Date','Economy']].drop_duplicates().dropna().groupby(['Economy','Date']).sum().reset_index(),'passenger_km')
            original_model_output_8th_scenario = calc_growth(original_model_output_8th_scenario,'Activity_8th')
            if PLOT_ORIGINAL_FORECASTS_BY_TTYPE:
                original_growth_forecasts_p = calc_growth(original_growth_forecasts_p,'Original_activity_passenger')
                original_growth_forecasts_f = calc_growth(original_growth_forecasts_f,'Original_activity_freight')
            else:
                original_growth_forecasts = calc_growth(original_growth_forecasts,'Original_activity')

            
        ##
        #set 'line_dash' to 'solid' in passenger_km and freight_km, then set to 'dash' in original_model_output_8th_scenario and  population and gdp
        passenger_km['line_dash'] = 'final'
        freight_km['line_dash'] = 'final'
        original_model_output_8th_scenario['line_dash'] = 'input'
        population['line_dash'] = 'input'
        gdp['line_dash'] = 'input'
        if PLOT_ORIGINAL_FORECASTS_BY_TTYPE:
            original_growth_forecasts_p['line_dash'] = 'input'
            original_growth_forecasts_f['line_dash'] = 'input'
            
            #concat all the data together then melt:
            index_data = pd.concat([population, gdp, freight_km, passenger_km,original_model_output_8th_scenario, original_growth_forecasts_p, original_growth_forecasts_f], axis=0)
        else:
            original_growth_forecasts['line_dash'] = 'input'
            
            #concat all the data together then melt:
            index_data = pd.concat([population, gdp, freight_km, passenger_km,original_model_output_8th_scenario, original_growth_forecasts], axis=0)
                
        if indexed:
            index_data['Unit'] = 'Index'     
        else:                 
            index_data['Unit'] = 'Growth'
            
        #and filter so data is less than config.GRAPHING_END_YEAR
        index_data = index_data.loc[(index_data['Date']<=config.GRAPHING_END_YEAR)].copy()
        
        # #melt so all measures in one col
        # index_data = index_data.melt(id_vars=['Economy', 'Date'], value_vars=['Population_index', 'Gdp_index', 'freight_tonne_km_index', 'passenger_km_index', 'Activity_8th'], var_name='Measure', value_name='Index')
        
        for economy in ECONOMY_IDs:
            #filter to economy
            index_data_economy = index_data.loc[index_data['Economy']==economy].copy()

            index_data_economy = index_data_economy.groupby(['Measure', 'line_dash']).filter(lambda x: not all(x['Value'] == 0))
            
            #now plot
            fig = px.line(index_data_economy, x='Date', y='Value',color='Measure', line_dash='line_dash',color_discrete_map=colors_dict)
            title_text = 'Activity Data ({})'.format(index_data_economy['Unit'].unique()[0])
            # fig.update_yaxes(title_text=title_text)#not working for some reason

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['activity_and_macro_lines'] = [fig, title_text, PLOTTED]
            
            if WRITE_HTML:
                write_graph_to_html(config, filename=os.path.join('activity_and_macro_lines_{}_{}.html'.format(scenario, economy)), graph_type='line', plot_data=index_data_economy, economy=economy, x='Date', y='Value', color='Measure', title=title_text, line_dash='line_dash', y_axes_title=title_text, legend_title='', font_size=30, colors_dict=colors_dict)
    
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(index_data_economy['Measure'].unique().tolist())
    
    return fig_dict, color_preparation_list

def plot_supply_side_fuel_mixing(config, ECONOMY_IDs, supply_side_fuel_mixing_df, fig_dict, color_preparation_list, colors_dict, WRITE_HTML=True):
    PLOTTED=True
    #plot supply side fuel mixing
    supply_side_fuel_mixing = supply_side_fuel_mixing_df.copy()
    #average out the supply side fuel mixing by economy, scenario and new fuel, so that we have the average share of each fuel type that is mixed into another fuel type (note that this isnt weighted by the amount of fuel mixed in, just the share of the fuel that is mixed in... its a safe asumption given that every new fuel should be mixed in with similar shares
    supply_side_fuel_mixing= supply_side_fuel_mixing[['Date', 'Economy','Scenario', 'New_fuel' ,'Supply_side_fuel_share']].groupby(['Date', 'Economy','Scenario', 'New_fuel']).mean().reset_index()
    #round the Supply_side_fuel_share column to 2dp
    supply_side_fuel_mixing['Supply_side_fuel_share'] = supply_side_fuel_mixing['Supply_side_fuel_share'].round(3)
    #supply side mixing is just the percent of a fuel type that is mixed into another fuel type, eg. 5% biodiesel mixed into diesel. We can use the concat of Fuel and New fuel cols to show the data:
    supply_side_fuel_mixing['Fuel mix'] = supply_side_fuel_mixing['New_fuel']# supply_side_fuel_mixing_plot['Fuel'] + ' mixed with ' + 
    #actually i changed that because it was too long. should be obivous that it's mixed with the fuel in the Fuel col (eg. biodesel mixed with diesel)
    
    #add units (by setting measure to Freight_tonne_km haha)
    supply_side_fuel_mixing['Measure'] = 'Fuel_mixing'
    #add units
    supply_side_fuel_mixing['Unit'] = '%'
    
    #sort by date
    supply_side_fuel_mixing = supply_side_fuel_mixing.sort_values(by='Date')
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        supply_side_fuel_mixing_plot_scenario = supply_side_fuel_mixing.loc[supply_side_fuel_mixing['Scenario']==scenario].copy()
        for economy in ECONOMY_IDs:
            #filter to economy
            supply_side_fuel_mixing_plot_economy = supply_side_fuel_mixing_plot_scenario.loc[supply_side_fuel_mixing_plot_scenario['Economy']==economy].copy()
            
            supply_side_fuel_mixing_plot_economy = supply_side_fuel_mixing_plot_economy.groupby(['New_fuel']).filter(lambda x: not all(x['Supply_side_fuel_share'] == 0))
            # title = 'Supply side fuel mixing for ' + scenario + ' scenario'
            fig = px.line(supply_side_fuel_mixing_plot_economy, x="Date", y="Supply_side_fuel_share", color='New_fuel',  color_discrete_map=colors_dict)#title=title, 
            #add units to y col
            if len(supply_side_fuel_mixing_plot_economy)>0:
                title_text = 'Supply side fuel mixing ({})'.format(supply_side_fuel_mixing_plot_economy['Unit'].unique()[0])
            else:
                title_text = 'Supply side fuel mixing'
            # fig.update_yaxes(title_text=title_text)#not working for some reason

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['supply_side_fuel_mixing'] = [fig, title_text, PLOTTED]
            
            if WRITE_HTML:
                write_graph_to_html(config, filename='fuel_mixing_{}.html'.format(scenario), graph_type='line', plot_data=supply_side_fuel_mixing_plot_economy, economy=economy, x='Date', y='Supply_side_fuel_share', color='New_fuel', title=title_text, y_axes_title='%', legend_title='', colors_dict=colors_dict, font_size=35)
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(supply_side_fuel_mixing_plot_economy['New_fuel'].unique().tolist())
    return fig_dict, color_preparation_list

def plot_demand_side_fuel_mixing(config, ECONOMY_IDs, demand_side_fuel_mixing_df, model_output_detailed_df, fig_dict, color_preparation_list, colors_dict, WRITE_HTML=True):
    PLOTTED=True
    #plot demand side fuel mixing
    demand_side_fuel_mixing = demand_side_fuel_mixing_df.copy()
    #average out the demand side fuel mixing by date, economy, scenario, fuel, drive, vehicle type
    #but to make teh graph simple we want just the average by date, economy, scenario, fuel and drive, so we will join it with activity within each economy, scenario drive, transport type and vehicle type and then find the wieghted average of the fuel mix, grouped by date, economy, scenario, fuel and drive
    model_output_detailed  = model_output_detailed_df.copy()
    activity = model_output_detailed[['Economy', 'Date', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Activity']].groupby(['Economy', 'Date', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type']).sum().reset_index()
    demand_side_fuel_mixing = demand_side_fuel_mixing.merge(activity, on=['Economy', 'Date', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type'], how='left')
    # Step 1: Multiply 'Demand_side_fuel_share' by 'Activity' to get weighted shares
    demand_side_fuel_mixing['Weighted_Share'] = demand_side_fuel_mixing['Demand_side_fuel_share'] * demand_side_fuel_mixing['Activity']

    # Step 2: Group by the necessary columns and calculate the sum of weighted shares and total activity
    grouped = demand_side_fuel_mixing.groupby(['Economy', 'Date', 'Scenario', 'Fuel', 'Drive'])

    # Calculate the sum of weighted shares and total activity within each group
    sums = grouped.agg(
        Total_Weighted_Share=('Weighted_Share', 'sum'),
        Total_Activity=('Activity', 'sum')
    ).reset_index()

    # Step 3: Calculate the weighted average of fuel mix for each group
    sums['Demand_side_fuel_share'] = sums['Total_Weighted_Share'] / sums['Total_Activity']

    #round the Demand_side_fuel_share column to 2dp
    demand_side_fuel_mixing['Demand_side_fuel_share'] = demand_side_fuel_mixing['Demand_side_fuel_share']*100
    
    #add units (by setting measure to Freight_tonne_km haha)
    demand_side_fuel_mixing['Measure'] = 'Fuel_mixing'
    #add units
    demand_side_fuel_mixing['Unit'] = '%'
    
    #sort by date
    demand_side_fuel_mixing = demand_side_fuel_mixing.sort_values(by='Date')
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        demand_side_fuel_mixing_plot_scenario = demand_side_fuel_mixing.loc[demand_side_fuel_mixing['Scenario']==scenario].copy()
        for economy in ECONOMY_IDs:
            #filter to economy
            demand_side_fuel_mixing_plot_economy = demand_side_fuel_mixing_plot_scenario.loc[demand_side_fuel_mixing_plot_scenario['Economy']==economy].copy()
            
            title = 'Demand side fuel mixing for ' + scenario + ' scenario'
            fig = px.line(demand_side_fuel_mixing_plot_economy, x="Date", y="Demand_side_fuel_share", color='Fuel',  line_dash='Drive',title=title, color_discrete_map=colors_dict)

            #add units to y col
            title_text = 'Demand side fuel mixing ({})'.format(demand_side_fuel_mixing_plot_economy['Unit'].unique()[0])
            fig.update_yaxes(title_text=title_text)#not working for some reason

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['demand_side_fuel_mixing'] = [fig, title_text, PLOTTED]
            
            if WRITE_HTML:
                write_graph_to_html(config, filename='demand_side_fuel_mixing_{}.html'.format(scenario), graph_type='line', plot_data=demand_side_fuel_mixing_plot_economy, economy=economy, x='Date', y='Demand_side_fuel_share', color='Fuel', title=title_text, line_dash='Drive', y_axes_title='%', legend_title='', colors_dict=colors_dict, font_size=30)
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(demand_side_fuel_mixing_plot_economy['Fuel'].unique().tolist())
    return fig_dict, color_preparation_list

def create_charging_plot(config, ECONOMY_IDs, chargers_df, fig_dict, color_preparation_list, colors_dict, WRITE_HTML=True):
    PLOTTED=True 
    chargers = chargers_df.copy()
    chargers = chargers[['Economy', 'Scenario', 'Date', 'sum_of_fast_chargers_needed','sum_of_slow_chargers_needed']].drop_duplicates()
    #divide chargers by a thousand so its in 1000s#actually no, otherwise its confusing
    chargers['sum_of_fast_chargers_needed'] = chargers['sum_of_fast_chargers_needed']#/1000
    chargers['sum_of_slow_chargers_needed'] = chargers['sum_of_slow_chargers_needed']#/1000
    #rename sum_of_fast_chargers_needed and sum_of_slow_chargers_needed to Fast chargers and Slow chargers
    chargers = chargers.rename(columns={'sum_of_fast_chargers_needed':'Fast chargers (200kW)', 'sum_of_slow_chargers_needed':'Slow chargers (60kW)'})
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        chargers_scenario = chargers.loc[chargers['Scenario']==scenario].copy()
        for economy in ECONOMY_IDs:
            #filter to economy
            chargers_economy = chargers_scenario.loc[chargers_scenario['Economy']==economy].copy()
            
            title = 'Expected slow and fast public chargers needed for ' + scenario + ' scenario'
            fig = px.line(chargers_economy, x="Date", y=['Fast chargers (200kW)','Slow chargers (60kW)'], title=title, color_discrete_map=colors_dict)

            #add units to y col
            title_text = 'Public chargers (thousands)'
            fig.update_yaxes(title_text=title_text)#not working for some reason

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['charging'] = [fig, title_text, PLOTTED]
            
            if WRITE_HTML:
                
                write_graph_to_html(config, filename='charging_{}.html'.format(scenario), graph_type='bar', plot_data=chargers_economy, economy=economy, x='Date', y=['Fast chargers (200kW)', 'Slow chargers (60kW)'], title=f'Public chargers', y_axes_title='(thousands)', legend_title='', colors_dict=colors_dict, font_size=30, marker_line_width=2.5)
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(['sum_of_fast_chargers_needed','sum_of_slow_chargers_needed'])
    return fig_dict, color_preparation_list

def prodcue_LMDI_mutliplicative_plot(config, ECONOMY_IDs, fig_dict, colors_dict, transport_type, medium, WRITE_HTML=True):
    PLOTTED=True
    for scenario in config.economy_scenario_concordance.Scenario.unique():
        for economy in ECONOMY_IDs:
            if medium == 'all': 
                medium_id = 'all_mediums'
            else:
                medium_id = 'road'
            # breakpoint()
            file_identifier = f'{economy}_{scenario}_{transport_type}_{medium_id}_2_Energy use_Hierarchical_2060_multiplicative'
            try:
                lmdi_data = pd.read_csv(os.path.join(config.root_dir, 'intermediate_data', 'LMDI', economy, f'{file_identifier}.csv'))
            except:
                if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                    breakpoint()
                fig_dict[economy][scenario][f'lmdi_{transport_type}_{medium}'] = [None, None, False]
                return fig_dict
            #melt data so we have the different components of the LMDI as rows. eg. for freight the cols are: Date	Change in Energy	Energy intensity effect	freight_tonne_km effect	Engine type effect	Total Energy	Total_freight_tonne_km
            #we want to drop the last two plots, then melt the data so we have the different components of the LMDI as rows. eg. for freight the cols will end up as: Date	Effect. Then we will also create a line dash col and if the Effect is Change in Energy then the line dash will be solid, otherwise it will be dotted
            #drop cols by index, not name so it doesnt matter what thei names are
            lmdi_data_melt = lmdi_data.copy()#drop(lmdi_data.columns[[len(lmdi_data.columns)-1, len(lmdi_data.columns)-2]], axis=1)
            lmdi_data_melt = lmdi_data_melt.melt(id_vars=['Date'], var_name='Effect', value_name='Value')
            #If there are any values with Effect 'Total Energy use'  or 'Total_passenger_km'  then emove them since they are totals:
            lmdi_data_melt = lmdi_data_melt.loc[(lmdi_data_melt['Effect']!='Total Energy use') & (lmdi_data_melt['Effect']!='Total_passenger_km') & (lmdi_data_melt['Effect']!='Total_freight_tonne_km')].copy()
            #if any values are > 10, create a breakpoint so we can see what they are, just in case they need to be removed like above:
            if lmdi_data_melt['Value'].max() > 10:
                breakpoint()
            lmdi_data_melt['line_dash'] = lmdi_data_melt['Effect'].apply(lambda x: 'solid' if x == 'Percent change in Energy' else 'dash')
                        
            fig = px.line(lmdi_data_melt, x="Date", y='Value',  color='Effect', line_dash='line_dash', color_discrete_map=colors_dict)
            
            if medium == 'road':
                title_text = f'Drivers of {medium} {transport_type} energy use'
            else:
                title_text = f'Drivers of {transport_type} energy use'

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario][f'lmdi_{transport_type}_{medium}'] = [fig, title_text, PLOTTED]

            if WRITE_HTML:
                write_graph_to_html(config, filename=f'lmdi_{transport_type}_{medium}_{scenario}_{economy}.html', graph_type='line', plot_data=lmdi_data_melt, economy=economy, x='Date', y='Value', color='Effect', title=title_text, line_dash='line_dash', y_axes_title='Value', legend_title='Effect', font_size=30, colors_dict=colors_dict)

    return fig_dict
    

def produce_LMDI_additive_plot(config, ECONOMY_IDs, fig_dict, colors_dict, medium, WRITE_HTML=True):
    PLOTTED=True
    for scenario in config.economy_scenario_concordance.Scenario.unique():
        for economy in ECONOMY_IDs:
            if medium == 'all': 
                medium_id = 'all_mediums'
            else:
                medium_id = 'road'
            # breakpoint()
            file_identifier = f'{economy}_{scenario}_{medium_id}_2_Energy use_Hierarchical_2060_concatenated_additive'
            lmdi_data = pd.read_csv(os.path.join(config.root_dir, 'intermediate_data', 'LMDI', economy, f'{file_identifier}.csv'))
            #melt data so we have the different components of the LMDI as rows. eg. for freight the cols are: Date	Change in Energy	Energy intensity effect	freight_tonne_km effect	Engine type effect	Total Energy	Total_freight_tonne_km
            #we want to drop the last two plots, then melt the data so we have the different components of the LMDI as rows. eg. for freight the cols will end up as: Date	Effect. Then we will also create a line dash col and if the Effect is Change in Energy then the line dash will be solid, otherwise it will be dotted
            #drop cols by index, not name so it doesnt matter what thei names are
            lmdi_data_melt = lmdi_data.copy()#drop(lmdi_data.columns[[len(lmdi_data.columns)-1, len(lmdi_data.columns)-2]], axis=1)
            #grab data for max Date
            lmdi_data_melt = lmdi_data_melt.loc[lmdi_data_melt['Date']==lmdi_data_melt['Date'].max()].copy()
            #melt data
            lmdi_data_melt = lmdi_data_melt.melt(id_vars=['Date'], var_name='Effect', value_name='Value')
            #If there are any values with Effect 'Total Energy use'  or 'Total_passenger_km'  then emove them since they are totals:
            lmdi_data_melt = lmdi_data_melt.loc[(lmdi_data_melt['Effect']!='Total Energy use') & (lmdi_data_melt['Effect']!='Total_passenger_km') & (lmdi_data_melt['Effect']!='Total_freight_tonne_km') & (lmdi_data_melt['Effect']!='Total_passenger_and_freight_km')].copy()
            #rename the effect Additive change in Energy use to Change in Energy use
            lmdi_data_melt['Effect'] = lmdi_data_melt['Effect'].apply(lambda x: 'Change in Energy use' if x == 'Additive change in Energy use' else x)
            #and rename 'Engine switching intensity effect' to 'Other intensity improvments'
            lmdi_data_melt['Effect'] = lmdi_data_melt['Effect'].apply(lambda x: 'Other intensity improvements' if x == 'Engine switching intensity effect' else x)
            #and rename passenger_and_freight_km effect to 'Activity'
            lmdi_data_melt['Effect'] = lmdi_data_melt['Effect'].apply(lambda x: 'Activity' if x == 'passenger_and_freight_km effect' else x)
            #and Vehicle Type effect to 'Switching vehicle types'
            lmdi_data_melt['Effect'] = lmdi_data_melt['Effect'].apply(lambda x: 'Switching vehicle types' if x == 'Vehicle Type effect' else x)
            #and Engine switching effect to 'Engine type switching'
            lmdi_data_melt['Effect'] = lmdi_data_melt['Effect'].apply(lambda x: 'Drive type switching' if x == 'Engine switching effect' else x)
            # decreasing = {"marker":{"color":"#93C0AC"}},
            # increasing = {"marker":{"color":"#EB9C98"}},
            # totals = {"marker":{"color":"#11374A"}}
            #first set color basser on if value is positive or negative
            lmdi_data_melt['color'] = lmdi_data_melt['Value'].apply(lambda x: '#93C0AC' if x < 0 else '#EB9C98')
            #then set color to grey if the effect is 'Change in Energy use'
            lmdi_data_melt['color'] = np.where(lmdi_data_melt['Effect']=='Change in Energy use', '#11374A', lmdi_data_melt['color'])
            #create color dict from that, amtching from effect to color
            colors_dict_new = dict(zip(lmdi_data_melt['Effect'], lmdi_data_melt['color']))
            
            #lastly, manually set the order of the bars so it goes: Change in Energy use,passenger_and_freight_km effect,	Vehicle Type effect	Engine switching effect,	Engine switching intensity effect 
            # order = ['Change in Energy use', 'passenger_and_freight_km effect', 'Vehicle Type effect', 'Engine switching effect', 'Engine switching intensity effect']
            order = ['Change in Energy use', 'Activity', 'Switching vehicle types', 'Drive type switching', 'Other intensity improvements']
            # Convert the 'Effect' column to a categorical type with the defined order
            lmdi_data_melt['Effect'] = pd.Categorical(lmdi_data_melt['Effect'], categories=order, ordered=True)
            # Sort the DataFrame by the 'Effect' column
            lmdi_data_melt = lmdi_data_melt.sort_values('Effect')
             
            # breakpoint()
            fig = px.bar(lmdi_data_melt, x='Effect', y='Value',  color='Effect', color_discrete_map=colors_dict_new)
            
            if medium == 'road':
                title_text = f'Drivers of changes in {medium} energy use'
            else:
                title_text = f'Drivers of changes in energy use'

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario][f'lmdi_additive_{medium}'] = [fig, title_text, PLOTTED]
            
            if WRITE_HTML:
                write_graph_to_html(config, filename=f'lmdi_additive_{medium}_{scenario}_{economy}.html', graph_type='bar', plot_data=lmdi_data_melt, economy=economy, x='Effect', y='Value', color='Effect', title=title_text, y_axes_title='Value', legend_title='Effect', font_size=30, colors_dict=colors_dict)


    return fig_dict
    
def plot_average_age_by_simplified_drive_type(config, ECONOMY_IDs, model_output_detailed_df, fig_dict, color_preparation_list, colors_dict, medium, title, WRITE_HTML=True):
    PLOTTED=True
    model_output_detailed = model_output_detailed_df.copy()
    if medium=='road':
        model_output_detailed = model_output_detailed.loc[model_output_detailed['Medium']==medium].copy()
    elif medium=='all':
        # make the medium the drive for non road
        model_output_detailed.loc[model_output_detailed['Medium']!='road', 'Drive'] = model_output_detailed.loc[model_output_detailed['Medium']!='road', 'Medium']
        
    elif medium=='nonroad':
        model_output_detailed = model_output_detailed.loc[model_output_detailed['Medium']!='road'].copy()
        # make the medium the drive
        model_output_detailed['Drive'] = model_output_detailed['Medium']
        #drop rows where stock is 0 or na so the average age doesnt get messed up
        model_output_detailed = model_output_detailed.loc[(model_output_detailed['Stocks']>0)].copy()
        #calcaulte the average age using a weighted average of stocks*age/stocks
        model_output_detailed['weighted_age'] = (model_output_detailed['Stocks']*model_output_detailed['Average_age'])
        model_output_detailed = model_output_detailed.groupby(['Economy', 'Date', 'Scenario', 'Transport Type', 'Drive']).sum(numeric_only=True).reset_index()
        model_output_detailed['Average_age'] = model_output_detailed['weighted_age']/model_output_detailed['Stocks']
              
        # if any avergae ages are greater than 50 its probably an error:
        if model_output_detailed['Average_age'].max() >= 51:
            breakpoint()
    else:
        raise ValueError('medium must be road, non_road or all')
    #create a new df with only the data we need:
    avg_age = model_output_detailed.copy()
    # #map drive types:
    # avg_age = avg_age[['Economy', 'Date', 'Drive','Stocks', 'Average_age']].groupby(['Economy', 'Date', 'Drive']).sum(numeric_only=True).reset_index()
    
    #simplfiy drive type using remap_drive_types
    avg_age = remap_drive_types(config, avg_age, value_col='Average_age', new_index_cols = ['Economy', 'Date','Scenario', 'Transport Type', 'Drive'], drive_type_mapping_set='simplified', aggregation_type=('weighted_average', 'Stocks'))# 'Vehicle Type',
    #drop stocks col
    avg_age.drop(columns=['Stocks'], inplace=True)
    
    #add units (by setting measure to Freight_tonne_km haha)
    avg_age['Measure'] = 'Average_age'
    #add units
    avg_age['Unit'] = 'Age'

    #if age is 0 anywhere, set it to na
    avg_age.loc[avg_age['Average_age']==0, 'Average_age'] = np.nan
    #since average age starts off at  1 or 5 years (depending on if the drive type is a new or old type) we are probably best plotting the average age grouped into these types. So group all ice style engines, and ev/hydrogen/phev engines. then grouping by vehicle type transport type and drive, find the weighted average age of each engine type over time. plot as a line. 
    # model_output_detailed.pkl
    # #
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        avg_age_s = avg_age.loc[(avg_age['Scenario']==scenario)].copy()
        for economy in ECONOMY_IDs:
            #filter to economy
            avg_age_economy = avg_age_s.loc[avg_age_s['Economy']==economy].copy()
            
            #concat drive and vehicle type cols:
            # avg_age_economy['Drive'] = avg_age_economy['Vehicle Type']+' '+ avg_age_economy['Drive'] 
            #now plot
            fig = px.line(avg_age_economy, x='Date', y='Average_age', color='Drive',line_dash = 'Transport Type', color_discrete_map=colors_dict)
            title_text = f'Average Age of {medium} vehicles by drive'

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario][title] = [fig, title_text, PLOTTED]
            
            if WRITE_HTML:
                write_graph_to_html(config, filename=f'average_age_{medium}_{scenario}_{economy}.html', graph_type='line', plot_data=avg_age_economy, economy=economy, x='Date', y='Average_age', color='Drive', title=title_text, line_dash='Transport Type', y_axes_title='Age', legend_title='Drive', font_size=30, colors_dict=colors_dict)
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(avg_age_economy['Drive'].unique().tolist())
    return fig_dict, color_preparation_list
 


def plot_stocks_per_capita(config, ECONOMY_IDs, gompertz_parameters_df, model_output_detailed, first_road_model_run_data, fig_dict, color_preparation_list, colors_dict, PLOT_ANYWAY=True, WRITE_HTML=True):
    PLOTTED=True
    #load in ECONOMIES_WITH_MAX_STOCKS_PER_CAPITA_REACHED from yaml. if the econmoy is in this we should either not plot anything or just plot the stocks per cpita, no thresholds.
    ECONOMIES_WITH_MAX_STOCKS_PER_CAPITA_REACHED = yaml.load(open(os.path.join(config.root_dir, 'config','parameters.yml')), Loader=yaml.FullLoader)['ECONOMIES_WITH_MAX_STOCKS_PER_CAPITA_REACHED']
    if (len(gompertz_parameters_df)==0) and not PLOT_ANYWAY:
        for scenario in config.economy_scenario_concordance['Scenario'].unique():
            for economy in ECONOMY_IDs:
                fig_dict[economy][scenario]['stocks_per_capita'] = [None, None, False]#likely that there was no need to plot this. havent l0ooked much into it though
        return fig_dict, color_preparation_list
    #Plot stocks per capita for each transport type. Also plot the gompertz line for the economy, which is a horizontal line. 
    first_model_run_stocks_per_capita = first_road_model_run_data[['Economy', 'Date', 'Stocks','Scenario', 'Vehicle Type', 'Transport Type', 'Population']].copy().drop_duplicates()
    #set 'model' to 'first_model_run' so we can distinguish it from the other model runs
    first_model_run_stocks_per_capita['Model'] = 'Original'
    
    stocks_per_capita = model_output_detailed[['Economy', 'Date','Medium', 'Scenario','Stocks', 'Vehicle Type', 'Transport Type','Population']].copy()
    stocks_per_capita = stocks_per_capita.loc[stocks_per_capita['Medium']=='road'].copy()
    #set 'model' to 'Adjusted' so we can distinguish it from the other model runs
    stocks_per_capita['Model'] = 'Adjusted'
    
    #now concat the two dfs:
    stocks_per_capita = pd.concat([stocks_per_capita, first_model_run_stocks_per_capita], axis=0)
    
    # #extract the vehicles_per_stock_parameters:
    # vehicles_per_stock_parameters = pd.read_excel(config.root_dir + config.slash + 'input_data/parameters.xlsx', sheet_name='gompertz_vehicles_per_stock')
    # #convert from regiosn to economies:
    # vehicles_per_stock_regions = pd.read_excel(config.root_dir + config.slash + 'input_data/parameters.xlsx', sheet_name='vehicles_per_stock_regions')
    # #join on region
    # vehicles_per_stock_parameters = vehicles_per_stock_parameters.merge(vehicles_per_stock_regions, on='Region', how='left')
    # #dro regions
    # vehicles_per_stock_parameters.drop(columns=['Region'], inplace=True)
    
    if len(ECONOMY_IDs)>1:
        raise ValueError('This function only works for one economy at a time')
    
    # DO_LOG_FITTING_ON_ONLY_PASSENGER_VEHICLES_DICT = yaml.load(open(config.root_dir + config.slash + 'config/parameters.yml'), Loader=yaml.FullLoader)['DO_LOG_FITTING_ON_ONLY_PASSENGER_VEHICLES_ECONOMIES']
    # if DO_LOG_FITTING_ON_ONLY_PASSENGER_VEHICLES_DICT[ECONOMY_IDs[0]]:
    #     vehicles_per_stock_parameters = pd.read_csv(config.root_dir + config.slash + 'intermediate_data/road_model/{}_vehicles_per_stock_parameters_passenger_only.csv'.format(ECONOMY_IDs[0]))
    #     #filter for only passenger
    #     stocks_per_capita = stocks_per_capita.loc[stocks_per_capita['Transport Type']=='passenger'].copy()
    #     gompertz_parameters_df = gompertz_parameters_df.loc[gompertz_parameters_df['Transport Type']=='passenger'].copy()
    # else:
    vehicles_per_stock_parameters = pd.read_csv(os.path.join(config.root_dir, 'intermediate_data', 'road_model', f'{ECONOMY_IDs[0]}_vehicles_per_stock_parameters.csv'))
    
    
    #Convert some stocks to gompertz adjusted stocks by multiplying them by the vehicle_gompertz_factors. This is because you can expect some economies to have more or less of that vehicle type than others. These are very general estiamtes, and could be refined later.
    stocks_per_capita = stocks_per_capita.merge(vehicles_per_stock_parameters, on=['Vehicle Type','Transport Type', 'Scenario','Economy','Date'], how='left')
    stocks_per_capita['Stocks'] = stocks_per_capita['Stocks'] * stocks_per_capita['gompertz_vehicles_per_stock']
    
    #recalcualte stocks per capita after summing up stocks by economy and transport type, scneario anmd date
    #extract population so we can join it after the sum:
    population = stocks_per_capita[['Economy', 'Scenario','Date', 'Population','Model']].drop_duplicates()
    stocks_per_capita = stocks_per_capita.drop(columns=['Population']).groupby(['Economy', 'Date', 'Scenario','Transport Type','Model']).sum(numeric_only=True).reset_index()
    #join population back on:
    stocks_per_capita = stocks_per_capita.merge(population, on=['Economy','Scenario', 'Date','Model'], how='left')
    #calcualte stocks per capita
    stocks_per_capita['Thousand_stocks_per_capita'] = stocks_per_capita['Stocks']/stocks_per_capita['Population']
    #convert to more readable units. We will convert back later if we need to #todo do we need to?
    stocks_per_capita['Stocks_per_thousand_capita'] = stocks_per_capita['Thousand_stocks_per_capita'] * 1000000
    if len(gompertz_parameters_df)>0:#will be empty if economy is in ECONOMIES_WITH_MAX_STOCKS_PER_CAPITA_REACHED as true
        gompertz_parameters = gompertz_parameters_df[['Economy','Transport Type', 'Scenario', 'Stocks_per_capita']].drop_duplicates().dropna().copy()
        #set measure to 'maximum_stocks_per_captia'
        gompertz_parameters['Model'] = 'stocks_per_capita_threshold'
        #rename Stocks_per_capita to Stocks_per_thousand_capita
        gompertz_parameters.rename(columns={'Stocks_per_capita':'Stocks_per_thousand_capita'}, inplace=True)
        
        #merge on the gompertz parameters to date col then concat it
        gompertz_parameters = stocks_per_capita[['Economy','Transport Type', 'Scenario','Date']].drop_duplicates().merge(gompertz_parameters, on=['Economy','Transport Type', 'Scenario'], how='left')
        
        stocks_per_capita = pd.concat([stocks_per_capita, gompertz_parameters], axis=0)
    PREV_PLOTTED = None
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        stocks_per_capita_s = stocks_per_capita.loc[(stocks_per_capita['Scenario']==scenario)].copy()
        #add units (by setting measure to Freight_tonne_km haha)
        stocks_per_capita_s['Measure'] = 'Stocks_per_thousand_capita'
        #add units
        stocks_per_capita_s['Unit'] = 'Stocks_per_thousand_capita'
        
        PLOTTED=True
        for economy in ECONOMY_IDs:
            if not PLOT_ANYWAY:
                if ECONOMIES_WITH_MAX_STOCKS_PER_CAPITA_REACHED[economy]:
                    PLOTTED=False
                    PREV_PLOTTED=False
            #filter to economy
            stocks_per_capita_economy = stocks_per_capita_s.loc[stocks_per_capita_s['Economy']==economy].copy()
            #identify if the stocks_per_capita_threshold is the same as the adjusted value in the min year. if so we wont plot this graph because its not useful
            #first grab the min year
            min_year = stocks_per_capita_economy['Date'].min()
            #now grab the stocks_per_capita_threshold and adjusted values for the min year
            stocks_per_capita_min_year = stocks_per_capita_economy.loc[stocks_per_capita_economy['Date']==min_year].copy()
            #now grab the stocks_per_capita_threshold and adjusted values for the min year
            stocks_per_capita_min_year = stocks_per_capita_min_year.loc[stocks_per_capita_min_year['Model'].isin(['stocks_per_capita_threshold', 'Adjusted'])].copy()
            #now grab the stocks_per_capita_threshold and adjusted values for the min year
            if len(gompertz_parameters_df)>0:
                threshold= stocks_per_capita_min_year.loc[stocks_per_capita_min_year['Model']=='stocks_per_capita_threshold', 'Stocks_per_thousand_capita'].iloc[0]
                adjusted= stocks_per_capita_min_year.loc[stocks_per_capita_min_year['Model']=='Adjusted', 'Stocks_per_thousand_capita'].iloc[0]
                #if they are within 5% of each other then we wont plot this graph because its not useful
                diff = abs((threshold-adjusted)/threshold)
            
                #if the threshold is the same as the adjusted value in the min year, then we wont plot this graph because its not useful, however if the plot was plotted for the other scenario then we will plot it for this scenario
                if not PLOT_ANYWAY:
                    if diff < 0.05:
                        PLOTTED=False
                    elif diff >= 0.05:
                        PLOTTED=True
                    if PREV_PLOTTED:
                        PLOTTED=True
                    elif PREV_PLOTTED==False:
                        PLOTTED=False
            #set PREV_PLOTTED to PLOTTED so we can use it next time
            PREV_PLOTTED = PLOTTED
            
            #for now lets just drop the original model run data so we dont confuse reader:
            stocks_per_capita_economy = stocks_per_capita_economy.loc[stocks_per_capita_economy['Model']!='Original'].copy()
            # #keep only trnapsort type = passenger#commented this out because having the freight one at 0 makes it so the scale includes 0, which cannot easily be done otherwise i think
            # stocks_per_capita_economy = stocks_per_capita_economy.loc[stocks_per_capita_economy['Transport Type']=='passenger'].copy()
            #now plot
            fig = px.line(stocks_per_capita_economy, x='Date', y='Stocks_per_thousand_capita', color='Transport Type', line_dash='Model', color_discrete_map=colors_dict)
            title_text = 'Stocks per capita (Weighted) (Thousand)'
            #make scale start at 0
            fig.update_yaxes(range=[0, 1000])
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['stocks_per_capita'] = [fig, title_text, PLOTTED]
            
            if WRITE_HTML:
                write_graph_to_html(config, filename='stocks_per_capita_{}.html'.format(scenario), graph_type='line', plot_data=stocks_per_capita_economy, economy=economy,  x='Date', y='Stocks_per_thousand_capita', color='Transport Type', title=title_text, line_dash='Model', y_axes_title='Stocks per capita (Thousand)', legend_title='', colors_dict=colors_dict, font_size=30)
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(stocks_per_capita_economy['Transport Type'].unique().tolist())
    return fig_dict, color_preparation_list


def plot_non_road_energy_use(config, ECONOMY_IDs, energy_output_for_outlook_data_system_tall, fig_dict, color_preparation_list, colors_dict, transport_type, WRITE_HTML=True):
    PLOTTED=True
    
    #we will plot the energy use by fuel type for non road as an area chart.
    model_output_with_fuels = energy_output_for_outlook_data_system_tall.copy()
    #extract Medium != road
    model_output_with_fuels = model_output_with_fuels.loc[model_output_with_fuels['Medium']!='road'].copy()
    
    #create a new df with only the data we need: 
    energy_use_by_fuel_type = model_output_with_fuels.copy()
    energy_use_by_fuel_type= energy_use_by_fuel_type[['Economy','Scenario', 'Date', 'Fuel', 'Transport Type','Energy']].groupby(['Economy','Scenario', 'Date','Transport Type', 'Fuel']).sum().reset_index()
    
    #add units (by setting measure to Energy haha)
    energy_use_by_fuel_type['Measure'] = 'Energy'
    #add units
    energy_use_by_fuel_type['Unit'] = energy_use_by_fuel_type['Measure'].map(config.measure_to_unit_concordance_dict)
    
    #load in data and recreate plot, as created in all_economy_graphs
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        energy_use_by_fuel_type_s = energy_use_by_fuel_type.loc[(energy_use_by_fuel_type['Scenario']==scenario)].copy()
        for economy in ECONOMY_IDs:
            #filter to economy
            energy_use_by_fuel_type_economy = energy_use_by_fuel_type_s.loc[energy_use_by_fuel_type_s['Economy']==economy].copy()
            
            energy_use_by_fuel_type_economy = energy_use_by_fuel_type_economy.groupby(['Fuel']).filter(lambda x: not all(x['Energy'] == 0))
            
            # calculate total 'Energy' for each 'Fuel' 
            total_energy_per_fuel = energy_use_by_fuel_type_economy.groupby('Fuel')['Energy'].sum()

            # Create an ordered category of 'Fuel' labels sorted by total 'Energy'
            energy_use_by_fuel_type_economy['Fuel'] = pd.Categorical(
                energy_use_by_fuel_type_economy['Fuel'],
                categories = total_energy_per_fuel.sort_values(ascending=False).index,
                ordered=True
            )
            
            # Now sort the DataFrame by the 'Fuel' column:
            energy_use_by_fuel_type_economy.sort_values(by='Fuel', inplace=True)
            if transport_type=='passenger':
                #now plot
                fig = px.area(energy_use_by_fuel_type_economy.loc[energy_use_by_fuel_type_economy['Transport Type']=='passenger'], x='Date', y='Energy', color='Fuel', title='Energy by Fuel', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Non road energy by Fuel {} (Pj)'.format(transport_type)
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['non_road_energy_use_by_fuel_type_passenger'] = [fig, title_text, PLOTTED]
                
                
            elif transport_type == 'freight':
                #now plot
                fig = px.area(energy_use_by_fuel_type_economy.loc[energy_use_by_fuel_type_economy['Transport Type']=='freight'], x='Date', y='Energy', color='Fuel', title='Energy by Fuel', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Non road energy by Fuel {} (Pj)'.format(transport_type)
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['non_road_energy_use_by_fuel_type_freight'] = [fig, title_text, PLOTTED]
                
            elif transport_type == 'all':
                #sum across transport types
                energy_use_by_fuel_type_economy = energy_use_by_fuel_type_economy.groupby(['Economy', 'Date', 'Fuel','Unit']).sum(numeric_only = True).reset_index()
                #now plot
                fig = px.area(energy_use_by_fuel_type_economy, x='Date', y='Energy', color='Fuel', title='Energy by Fuel', color_discrete_map=colors_dict)
                #add units to y col
                title_text = 'Non road energy by Fuel (Pj)'
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['non_road_energy_use_by_fuel_type_all'] = [fig, title_text, PLOTTED]
                
                if WRITE_HTML:
                    #drop fuel types which have < 0.00001% of the total energy use over the period
                    
                    energy_use_by_fuel_type_economy['Fuel'] = energy_use_by_fuel_type_economy['Fuel'].astype('object')
                    # energy_use_by_fuel_type_economy = energy_use_by_fuel_type_economy.groupby('Fuel').filter(lambda x: x['Energy'].sum() > energy_use_by_fuel_type_economy['Energy'].sum()*0.0001)
                    #remove any values that are less than 1
                    energy_use_by_fuel_type_economy = energy_use_by_fuel_type_economy.loc[energy_use_by_fuel_type_economy['Energy'] > 1].copy()
                    write_graph_to_html(config, filename=f'energy_use_by_fuel_type_non_road_{scenario}.html', graph_type='area', plot_data=energy_use_by_fuel_type_economy, economy=economy,  x='Date', y='Energy', color='Fuel', title=f'Non road energy by Fuel - {scenario}', y_axes_title='PJ', legend_title='', colors_dict=colors_dict, font_size=30, marker_line_width=2.5)
            else:
                raise ValueError('transport_type must be passenger, all or freight')
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(energy_use_by_fuel_type_economy['Fuel'].unique().tolist())
    return fig_dict, color_preparation_list

def non_road_activity_by_drive_type(config, ECONOMY_IDs, model_output_detailed_df, fig_dict, color_preparation_list, colors_dict, transport_type, WRITE_HTML=True):
    PLOTTED=True
    #why arent we getting different drive types.
    #break activity into its ddrive types and plot as an area chart. will do a plot for each transport type or a plot where passneger km and freight km are in same plot. in this case, it will have pattern_shape="Transport Type" to distinguish between the two:
    # model_output_detailed.pkl
    #loop through scenarios and grab the data for each scenario:
    #since we need detail on non road drive types, we have to pull the data fromm here:
    # 'output_data/model_output/NON_ROAD_DETAILED_{}'.format(config.model_output_file_name)
    model_output_detailed=model_output_detailed_df.copy()
    model_output_detailed = model_output_detailed.loc[model_output_detailed['Medium']!='road'].copy()
    
    #create a new df with only the data we need:
    activity_by_drive = model_output_detailed.copy()
    activity_by_drive = activity_by_drive[['Economy', 'Date', 'Drive','Transport Type', 'Scenario','Activity']].groupby(['Economy', 'Date', 'Transport Type','Scenario','Drive']).sum().reset_index()
    
    
    # #simplfiy drive type using remap_drive_types
    # activity_by_drive = remap_drive_types(config, activity_by_drive, value_col='Activity', new_index_cols = ['Economy', 'Date', 'Transport Type','Drive'])
    
    #add units (by setting measure to Freight_tonne_km haha)
    activity_by_drive['Measure'] = 'Activity'
    #add units
    activity_by_drive['Unit'] = 'Activity'
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        #filter for the scenario:
        activity_by_drive_s = activity_by_drive.loc[activity_by_drive['Scenario']==scenario].copy()

        for economy in ECONOMY_IDs:
            #filter to economy
            activity_by_drive_economy = activity_by_drive_s.loc[activity_by_drive_s['Economy']==economy].copy()
            
            activity_by_drive_economy = activity_by_drive_economy.groupby(['Drive']).filter(lambda x: not all(x['Activity'] == 0))
            
            # calculate total 'passenger_km' for each 'Drive' 
            total_activity = activity_by_drive_economy.groupby('Drive')['Activity'].sum()

            # Create an ordered category of 'Drive' labels sorted by total 'passenger_km'
            activity_by_drive_economy['Drive'] = pd.Categorical(
            activity_by_drive_economy['Drive'],
            categories = total_activity.sort_values(ascending=False).index,
            ordered=True
            )

            # Now sort the DataFrame by the 'Drive' column:
            activity_by_drive_economy.sort_values(by=['Drive',"Transport Type"], inplace=True)
            #sort by date
            
            if transport_type=='passenger':
                #now plot
                fig = px.area(activity_by_drive_economy.loc[activity_by_drive_economy['Transport Type']=='passenger'], x='Date', y='Activity', color='Drive', title='Non road passenger activity by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Non road passenger Km (Billions)'#.format(activity_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['non_road_activity_by_drive_passenger'] = [fig, title_text, PLOTTED]
                
            elif transport_type == 'freight':
                #now plot
                fig = px.area(activity_by_drive_economy.loc[activity_by_drive_economy['Transport Type']=='freight'], x='Date', y='Activity', color='Drive', title='Non road freight activity by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Non road freight tonne Km (Billions)'#.format(activity_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['non_road_activity_by_drive_freight'] = [fig, title_text, PLOTTED]
                
            elif transport_type == 'all':
                #sum across transport types
                fig = px.line(activity_by_drive_economy, x='Date', y='Activity', color='Drive',line_dash="Transport Type" , title='Non road activity by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Non road activity (Freight & Passenger km)'#.format(activity_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['non_road_activity_by_drive_all'] = [fig, title_text, PLOTTED]
                
                
                if WRITE_HTML:
                    write_graph_to_html(config, filename=f'non_road_activity_by_drive_all_{scenario}_{economy}.html', graph_type='line', plot_data=activity_by_drive_economy, economy=economy, x='Date', y='Activity', color='Drive', title=title_text, line_dash='Transport Type', y_axes_title='Activity (Billions)', legend_title='Drive', font_size=30, colors_dict=colors_dict)
                
            else:
                raise ValueError('transport_type must be passenger, all or freight')
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(activity_by_drive_economy['Drive'].unique().tolist())
    return fig_dict, color_preparation_list

def road_stocks_by_drive_type(config, ECONOMY_IDs, model_output_detailed_df, fig_dict, color_preparation_list, colors_dict, transport_type, WRITE_HTML=True):
    PLOTTED=True
    #break activity into its ddrive, transport and "Vehicle Type" and plot as a line chart. will do a plot for each transport type or a plot where passneger km and freight km are in same plot.
    # model_output_detailed.pkl
    #loop through scenarios and grab the data for each scenario:

    model_output_detailed=model_output_detailed_df.copy()
    
    model_output_detailed = model_output_detailed.loc[model_output_detailed['Medium']=='road'].copy()
    
    #create a new df with only the data we need:
    stocks_by_drive = model_output_detailed.copy()
    stocks_by_drive = stocks_by_drive[['Economy', 'Date', 'Drive','Scenario','Transport Type',"Vehicle Type", 'Stocks']].groupby(['Economy', 'Date', 'Transport Type','Scenario',"Vehicle Type", 'Drive']).sum().reset_index()
    
    #add units (by setting measure to Freight_tonne_km haha)
    stocks_by_drive['Measure'] = 'Stocks'
    #add units
    stocks_by_drive['Unit'] = 'Stocks'

    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        #filter for the scenario:
        stocks_by_drive_s = stocks_by_drive.loc[stocks_by_drive['Scenario']==scenario].copy()
        for economy in ECONOMY_IDs:
            #filter to economy
            stocks_by_drive_economy = stocks_by_drive_s.loc[stocks_by_drive_s['Economy']==economy].copy()
            
            stocks_by_drive_economy = stocks_by_drive_economy.groupby(['Drive']).filter(lambda x: not all(x['Stocks'] == 0))
            
            # calculate total 'passenger_km' for each 'Drive' 
            total_stocks = stocks_by_drive_economy.groupby('Drive')['Stocks'].sum()

            # Create an ordered category of 'Drive' labels sorted by total 'passenger_km'
            stocks_by_drive_economy['Drive'] = pd.Categorical(
            stocks_by_drive_economy['Drive'],
            categories = total_stocks.sort_values(ascending=False).index,
            ordered=True
            )

            # Now sort the DataFrame by the 'Drive' column:
            stocks_by_drive_economy.sort_values(by='Drive', inplace=True)
            #sort by date
            if transport_type=='passenger':
                #now plot
                fig = px.line(stocks_by_drive_economy.loc[stocks_by_drive_economy['Transport Type']=='passenger'], x='Date', y='Stocks', color='Drive',line_dash="Vehicle Type", title='Road passenger stocks by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Road passenger Km (Billions)'#.format(stocks_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['road_stocks_by_drive_passenger'] = [fig, title_text, PLOTTED]
                
            elif transport_type == 'freight':
                #now plot
                fig = px.line(stocks_by_drive_economy.loc[stocks_by_drive_economy['Transport Type']=='freight'], x='Date', y='Stocks', color='Drive', line_dash="Vehicle Type", title='Road freight stocks by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Road freight tonne Km (Billions)'#.format(stocks_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['road_stocks_by_drive_freight'] = [fig, title_text, PLOTTED]
                
            elif transport_type == 'all':
                #add vehicle type and transport ype to the same col
                stocks_by_drive_economy["Vehicle Type"] = stocks_by_drive_economy["Vehicle Type"]+' '+stocks_by_drive_economy['Transport Type']                
                #drop transport type col and sum across vehicle type
                stocks_by_drive_economy = stocks_by_drive_economy.drop(columns=['Transport Type']).groupby(['Economy', 'Date', 'Drive','Vehicle Type']).sum(numeric_only = True).reset_index()
                #sum across transport types
                fig = px.line(stocks_by_drive_economy, x='Date', y='Stocks', color='Drive',line_dash="Vehicle Type" , title='Road stocks by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Road stocks'#.format(stocks_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['road_stocks_by_drive_all'] = [fig, title_text, PLOTTED]
                
                if WRITE_HTML:
                    write_graph_to_html(config, filename=f'road_stocks_by_drive_all_{scenario}_{economy}.html', graph_type='line', plot_data=stocks_by_drive_economy, economy=economy, x='Date', y='Stocks', color='Drive', title=title_text, line_dash='Vehicle Type', y_axes_title='Stocks (Billions)', legend_title='Drive', font_size=30, colors_dict=colors_dict)
                
            else:
                raise ValueError('transport_type must be passenger, all or freight')
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(stocks_by_drive_economy['Drive'].unique().tolist())
    return fig_dict, color_preparation_list

def road_sales_by_drive_vehicle(config, ECONOMY_IDs, model_output_detailed_df, fig_dict, color_preparation_list, colors_dict, WRITE_HTML=True):
    PLOTTED=True
    #break activity into its ddrive, transport and "Vehicle Type" and plot as a line chart. will do a plot for each transport type or a plot where passneger km and freight km are in same plot.
    # model_output_detailed.pkl
    #loop through scenarios and grab the data for each scenario:
    breakpoint()
    stocks_9th=model_output_detailed_df.copy()
    
    stocks_9th = stocks_9th.loc[stocks_9th['Medium']=='road'].copy()
    index_cols = ['Economy', 'Date', 'Scenario','Transport Type', 'Vehicle Type', 'Drive']
    stocks_9th = stocks_9th[index_cols +['Stocks', 'Turnover_rate']].copy()
    #shift turnover back by one year so we can calculate the turnover for the previous year, usign the year afters turnover rate (this is jsut because of hwo the data is structured)
    index_cols_no_date = index_cols.copy()
    index_cols_no_date.remove('Date')
    stocks_9th['Turnover_rate'] = stocks_9th.groupby(index_cols_no_date)['Turnover_rate'].shift(-1)
    #calcaulte turnover for stocks 9th
    stocks_9th['Turnover'] = stocks_9th['Stocks'] * stocks_9th['Turnover_rate']
    
    #calculate sales. First calcualte stocks after turnover by subtracting turnover from stocks. then calcalte sales by subtracting stocks after turnover from  stocks after turnover  from previous year:
    stocks_9th['stocks_after_turnover'] = stocks_9th['Stocks'] - stocks_9th['Turnover'] 
    
    #sales is the stocks before turnover in this year, minus the stocks after turnover in the previous yea
    stocks_9th['previous_year_stocks_after_turnover'] = stocks_9th.groupby(index_cols_no_date)['stocks_after_turnover'].shift(1)
    stocks_9th['sales'] = stocks_9th['Stocks'] - stocks_9th['previous_year_stocks_after_turnover']
    
    # #calcaulte sales share by transprot type on the drive type
    # stocks_9th['sales_share'] = stocks_9th['sales'] / stocks_9th.groupby(index_cols_no_drive)['sales'].transform('sum')
    
    # #and clacualte stocks share
    # stocks_9th['stocks_share'] = stocks_9th['Stocks'] / stocks_9th.groupby(index_cols_no_drive)['Stocks'].transform('sum')
    
    #since its pretty difficult to compare slaes shares because we dont know the 8th sales shares, lets just observe the cahnge in stocks per year for each drive type:
    # stocks_9th['last_year_stocks'] = stocks_9th.groupby(index_cols_no_date)['Stocks'].shift(1)
    # stocks_9th['change_in_stocks'] = stocks_9th['Stocks'] - stocks_9th['last_year_stocks']
    
    #melt the data so we ahve all measures in one column
    # stocks_9th_tall = pd.melt(stocks_9th, id_vars=index_cols, value_vars=['sales'], var_name='Measure', value_name='Value')
    #keep only the cols we need
    stocks_9th_tall = stocks_9th[index_cols +['sales']].copy()
    # sales_share', 'stocks_share',,'change_in_stocks'
    #craete cols which inidcate dataset
    stocks_9th_tall['Dataset'] = '9th'
    
    stocks_9th_tall = remap_drive_types(config, stocks_9th_tall, value_col='sales', new_index_cols = index_cols, drive_type_mapping_set='extra_simplified')
    stocks_9th_tall = remap_vehicle_types(config, stocks_9th_tall, value_col='sales', new_index_cols = index_cols, vehicle_type_mapping_set='simplified')
    #now we can plot it all. since the values ar eon different scales and we can plot on both y axis we will need to make sure to only plot simiilar vlaues. so group like so:
    #shares: stocks share and sales share
    #values: stocks and sales
    
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        for economy in ECONOMY_IDs:
            #now plot
            sales_economy_scen = stocks_9th_tall.loc[(stocks_9th_tall['Economy']==economy) & (stocks_9th_tall['Scenario']==scenario)].copy()
            # sales_economy_scen = sales_economy_scen.loc[sales_economy_scen['Measure']=='sales'].copy()
            title='EV sales by drive type and vehicle type'
            fig = px.line(sales_economy_scen, x='Date', y='sales', color='Drive', line_dash='Vehicle Type', title=title, color_discrete_map=colors_dict)
            #add fig to dictionary for scenario and economy:    
            fig_dict[economy][scenario]['road_sales_by_drive_vehicle'] = [fig, title, PLOTTED]
                
            if WRITE_HTML:
                write_graph_to_html(config, filename=f'road_sales_by_drive_vehicle_{scenario}_{economy}.html', graph_type='line', plot_data=sales_economy_scen, economy=economy, x='Date', y='sales', color='Drive', title=title, line_dash='Vehicle Type', y_axes_title='Sales (Billions)', legend_title='Drive', font_size=30, colors_dict=colors_dict)
            
            # else:
            #     raise ValueError('transport_type must be passenger, all or freight')
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(sales_economy_scen['Drive'].unique().tolist())
    return fig_dict, color_preparation_list

import os

def non_road_stocks_by_drive_type(config, ECONOMY_IDs, model_output_detailed_df, fig_dict, color_preparation_list, colors_dict, transport_type, WRITE_HTML=True):
    PLOTTED=True
    #break activity into its ddrive types and plot as an area chart. will do a plot for each transport type or a plot where passneger km and freight km are in same plot. in this case, it will have pattern_shape="Transport Type" to distinguish between the two:
    # model_output_detailed.pkl
    #loop through scenarios and grab the data for each scenario:
    #since we need detail on non road drive types, we have to pull the data fromm here:

    model_output_detailed=model_output_detailed_df.copy()
    
    model_output_detailed = model_output_detailed.loc[model_output_detailed['Medium']!='road'].copy()
    
    #create a new df with only the data we need:
    stocks_by_drive = model_output_detailed.copy()
    stocks_by_drive = stocks_by_drive[['Economy', 'Date', 'Drive','Scenario','Transport Type', 'Stocks']].groupby(['Economy', 'Date', 'Transport Type','Scenario','Drive']).sum().reset_index()
    
    #add units (by setting measure to Freight_tonne_km haha)
    stocks_by_drive['Measure'] = 'Stocks'
    #add units
    stocks_by_drive['Unit'] = 'Stocks'

    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        #filter for the scenario:
        stocks_by_drive_s = stocks_by_drive.loc[stocks_by_drive['Scenario']==scenario].copy()
        for economy in ECONOMY_IDs:
            #filter to economy
            stocks_by_drive_economy = stocks_by_drive_s.loc[stocks_by_drive_s['Economy']==economy].copy()
            
            stocks_by_drive_economy = stocks_by_drive_economy.groupby(['Drive']).filter(lambda x: not all(x['Stocks'] == 0))
            
            # calculate total 'passenger_km' for each 'Drive' 
            total_stocks = stocks_by_drive_economy.groupby('Drive')['Stocks'].sum()

            # Create an ordered category of 'Drive' labels sorted by total 'passenger_km'
            stocks_by_drive_economy['Drive'] = pd.Categorical(
            stocks_by_drive_economy['Drive'],
            categories = total_stocks.sort_values(ascending=False).index,
            ordered=True
            )

            # Now sort the DataFrame by the 'Drive' column:
            stocks_by_drive_economy.sort_values(by='Drive', inplace=True)
            #sort by date

            if transport_type=='passenger':
                #now plot
                fig = px.line(stocks_by_drive_economy.loc[stocks_by_drive_economy['Transport Type']=='passenger'], x='Date', y='Stocks', color='Drive', title='Non road passenger stocks by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Non road passenger Km (Billions)'#.format(stocks_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['non_road_stocks_by_drive_passenger'] = [fig, title_text, PLOTTED]
                
            elif transport_type == 'freight':
                #now plot
                fig = px.line(stocks_by_drive_economy.loc[stocks_by_drive_economy['Transport Type']=='freight'], x='Date', y='Stocks', color='Drive', title='Non road freight stocks by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Non road freight tonne Km (Billions)'#.format(stocks_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['non_road_stocks_by_drive_freight'] = [fig, title_text, PLOTTED]
                
            elif transport_type == 'all':
                #sum across transport types
                fig = px.line(stocks_by_drive_economy, x='Date', y='Stocks', color='Drive',line_dash="Transport Type" , title='Non road stocks by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Non road stocks (Freight/Passenger km)'#.format(stocks_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['non_road_stocks_by_drive_all'] = [fig, title_text, PLOTTED]
                
                if WRITE_HTML:
                    write_graph_to_html(config, filename=f'non_road_stocks_by_drive_all_{scenario}_{economy}.html', graph_type='line', plot_data=stocks_by_drive_economy, economy=economy, x='Date', y='Stocks', color='Drive', title=title_text, line_dash='Transport Type', y_axes_title='Stocks (Billions)', legend_title='Drive', font_size=30, colors_dict=colors_dict)
                
            else:
                raise ValueError('transport_type must be passenger, all or freight')
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(stocks_by_drive_economy['Drive'].unique().tolist())
    return fig_dict, color_preparation_list



def turnover_rate_by_drive_type_box(config, ECONOMY_IDs, model_output_detailed, fig_dict, color_preparation_list, colors_dict, transport_type, WRITE_HTML=True):
    PLOTTED=True
    #break activity into its ddrive types and plot the variation by medium and treansport type on a box chart. will do a plot for each transport type or a plot where passneger km and freight km are in same plot. in this case, it will have pattern_shape="Transport Type" to distinguish between the two:
    # model_output_detailed.pkl
    #loop through scenarios and grab the data for each scenario:
    #since we need detail on non road drive types, we have to pull the data fromm here:
    #create a new df with only the data we need:
    turnover_rate_by_drive = model_output_detailed.copy()
    turnover_rate_by_drive = turnover_rate_by_drive[['Economy', 'Date', 'Medium','Drive','Transport Type','Scenario', 'Turnover_rate']].groupby(['Economy', 'Date', 'Medium','Transport Type','Scenario','Drive']).median().reset_index()#median less affected by outliers than mean
    
    #add units (by setting measure to Freight_tonne_km haha)
    turnover_rate_by_drive['Measure'] = 'Turnover_rate'
    #add units
    turnover_rate_by_drive['Unit'] = '%'

    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        #filter for the scenario:
        turnover_rate_by_drive_s = turnover_rate_by_drive.loc[turnover_rate_by_drive['Scenario']==scenario].copy()
        for economy in ECONOMY_IDs:
            #filter to economy
            turnover_rate_by_drive_economy = turnover_rate_by_drive_s.loc[turnover_rate_by_drive_s['Economy']==economy].copy()
            
            # calculate total 'passenger_km' for each 'Drive' 
            total_turnover_rate = turnover_rate_by_drive_economy.groupby('Drive')['Turnover_rate'].mean()

            # Create an ordered category of 'Drive' labels sorted by total 'passenger_km'
            turnover_rate_by_drive_economy['Drive'] = pd.Categorical(
            turnover_rate_by_drive_economy['Drive'],
            categories = total_turnover_rate.sort_values(ascending=False).index,
            ordered=True
            )

            # Now sort the DataFrame by the 'Drive' column:
            turnover_rate_by_drive_economy.sort_values(by='Drive', inplace=True)
            #sort by date

            if transport_type=='passenger':
                #now plot
                # fig = px.line(turnover_rate_by_drive_economy.loc[turnover_rate_by_drive_economy['Transport Type']=='passenger'], x='Date', y='Turnover_rate', color='Drive', title='Passenger turnover_rate by drive', color_discrete_map=colors_dict)
                fig = px.box(turnover_rate_by_drive_economy.loc[turnover_rate_by_drive_economy['Transport Type']=='passenger'],x='Medium', y='Turnover_rate', color='Drive', title='Passenger turnover_rate by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Passenger turnover rate box (based on median)'#.format(turnover_rate_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['box_turnover_rate_by_drive_passenger'] = [fig, title_text, PLOTTED]
                
            elif transport_type == 'freight':
                #now plot
                fig = px.box(turnover_rate_by_drive_economy.loc[turnover_rate_by_drive_economy['Transport Type']=='freight'],x='Medium', y='Turnover_rate', color='Drive', title='Freight turnover_rate by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Freight turnover rate box (based on median)'#.format(turnover_rate_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['box_turnover_rate_by_drive_freight'] = [fig, title_text, PLOTTED]
                
            elif transport_type == 'all':
                #sum across transport types
                fig = px.box(turnover_rate_by_drive_economy,x='Medium', y='Turnover_rate', color='Drive', title='Passenger turnover_rate by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'turnover_rate box (Freight/Passenger km) (based on median)'#.format(turnover_rate_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['box_turnover_rate_by_drive_all'] = [fig, title_text, PLOTTED]
                
                if WRITE_HTML:
                    write_graph_to_html(config, filename=f'turnover_rate_by_drive_{scenario}.html', graph_type='box', plot_data=turnover_rate_by_drive_economy, economy=economy,  x='Medium', y='Turnover_rate', color='Drive', title=f'Turnover rate by Drive - {scenario}', y_axes_title='%', legend_title='', colors_dict=colors_dict, font_size=30, marker_line_width=2.5)
                
            else:
                raise ValueError('transport_type must be passenger, all or freight')
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(turnover_rate_by_drive_economy['Drive'].unique().tolist())
    return fig_dict, color_preparation_list


def turnover_rate_by_vehicle_type_line(config, ECONOMY_IDs, model_output_detailed, fig_dict, color_preparation_list, colors_dict, transport_type, medium, WRITE_HTML=True):
    PLOTTED=True
    #break activity into its _vehicle types and plot the variation by medium and treansport type on a line chart. will do a plot for each transport type or a plot where passneger km and freight km are in same plot. in this case, it will have pattern_shape="Transport Type" to distinguish between the two:
    # model_output_detailed.pkl
    #loop through scenarios and grab the data for each scenario:
    #since we need detail on non road drive types, we have to pull the data fromm here:
    
    #create a new df with only the data we need:
    turnover_rate_by_vtype = model_output_detailed.copy()
        
    if medium == 'non_road':
        #extract Medium != road and set drive to the medium
        turnover_rate_by_vtype = turnover_rate_by_vtype.loc[turnover_rate_by_vtype['Medium']!='road'].copy()
        turnover_rate_by_vtype['Drive'] = turnover_rate_by_vtype['Medium']
        include_non_road = True
    elif medium == 'road':
        #drop non road since its turnover rate is non informative:
        turnover_rate_by_vtype = turnover_rate_by_vtype.loc[turnover_rate_by_vtype['Medium']=='road'].copy()
        
        include_non_road = False
    elif medium == 'all':
        #set drive to medium where medium is non road
        turnover_rate_by_vtype.loc[turnover_rate_by_vtype['Medium']!='road', 'Drive'] = turnover_rate_by_vtype.loc[turnover_rate_by_vtype['Medium']!='road', 'Medium']
        
        include_non_road = True
    else:
        raise ValueError('medium must be non_road, road or all')
    turnover_rate_by_vtype = remap_drive_types(config, turnover_rate_by_vtype, value_col='Turnover_rate', new_index_cols = ['Economy', 'Date', 'Medium','Transport Type','Scenario', 'Drive'], drive_type_mapping_set='simplified', aggregation_type=('weighted_average', 'Stocks'), include_non_road=include_non_road)

    #make values in 2020 have same turnover rate as in 2021 since 2020 turnover rates dont matter:
    #first double check the length of the sets would be the same, otherwise let user know with an error:
    if len(turnover_rate_by_vtype.loc[turnover_rate_by_vtype['Date']==config.OUTLOOK_BASE_YEAR]) != len(turnover_rate_by_vtype.loc[turnover_rate_by_vtype['Date']==config.OUTLOOK_BASE_YEAR+1]):
        raise ValueError('The number of turnover rates in the base year and the year after the base year are not the same when trying to plot.')
    
    turnover_rate_by_vtype.loc[turnover_rate_by_vtype['Date']==config.OUTLOOK_BASE_YEAR, 'Turnover_rate'] = turnover_rate_by_vtype.loc[turnover_rate_by_vtype['Date']==config.OUTLOOK_BASE_YEAR+1, 'Turnover_rate'].values
    
    #where any values are 0, set them to na, since thats what they should be
    turnover_rate_by_vtype.loc[turnover_rate_by_vtype['Turnover_rate']==0, 'Turnover_rate'] = np.nan
    
    # turnover_rate_by_vtype = turnover_rate_by_vtype[['Economy', 'Date', 'Medium','Transport Type','Scenario','Vehicle Type', 'Turnover_rate', 'Stocks']].groupby(['Economy', 'Date', 'Medium','Transport Type','Scenario','Vehicle Type']).agg({'Turnover_rate':'mean', 'Stocks':'sum'}).reset_index()#,'Drive'
    # #simplify the drive types:
    # turnover_rate_by_vtype = remap_drive_types(config, turnover_rate_by_vtype, value_col='Turnover_rate', new_index_cols = ['Economy', 'Date', 'Medium','Transport Type','Vehicle Type','Scenario','Drive'],drive_type_mapping_set='simplified', aggregation_type=('weighted_average', 'Stocks'))
    #and simplify the vehicle types:
    # turnover_rate_by_vtype = remap_vehicle_types(config, turnover_rate_by_vtype, value_col='Turnover_rate', new_index_cols = ['Economy', 'Date', 'Medium','Transport Type','Vehicle Type','Scenario'],vehicle_type_mapping_set='simplified', aggregation_type=('weighted_average', 'Stocks'))#,'Drive'
    #add units (by setting measure to Freight_tonne_km haha)
    turnover_rate_by_vtype['Measure'] = 'Turnover_rate'
    #add units
    turnover_rate_by_vtype['Unit'] = '%'

    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        #filter for the scenario:
        turnover_rate_by_vtype_s = turnover_rate_by_vtype.loc[turnover_rate_by_vtype['Scenario']==scenario].copy()
        for economy in ECONOMY_IDs:
            #filter to economy
            turnover_rate_by_vtype_economy = turnover_rate_by_vtype_s.loc[turnover_rate_by_vtype_s['Economy']==economy].copy()
            #TEMP:
            #CHECK FOR DUPICATES WHEN YOU INGORE THE VLAUE OCLUMN:
            cols = turnover_rate_by_vtype_economy.columns.tolist()
            cols = cols.remove('Turnover_rate')
            dupes = turnover_rate_by_vtype_economy[turnover_rate_by_vtype_economy.duplicated(subset=cols, keep=False)]
            if len(dupes)>0:
                breakpoint()
            # Now sort the DataFrame by the 'Date' column:
            turnover_rate_by_vtype_economy.sort_values(by='Date', inplace=True)
            #sort by date

            if transport_type=='passenger':
                #now plot
                # fig = px.line(turnover_rate_by_vtype_economy.loc[turnover_rate_by_vtype_economy['Transport Type']=='passenger'], x='Date', y='Turnover_rate', color='Drive', title='Passenger turnover_rate by drive', color_discrete_map=colors_dict)
                fig = px.line(turnover_rate_by_vtype_economy.loc[turnover_rate_by_vtype_economy['Transport Type']=='passenger'],x='Date', y='Turnover_rate', line_dash = 'Medium', color='Drive', title='Passenger turnover_rate by Drive', color_discrete_map=colors_dict)
                
                #add units to y col
                if medium == 'all':
                    title_text = 'Mean passenger turnover rate'#.format(turnover_rate_by_vtype_economy['Unit'].unique()[0])
                elif medium == 'non_road':
                    title_text = 'Mean passenger turnover rate for non road'
                elif medium == 'road':
                    title_text = 'Mean passenger turnover rate for road'
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][f'line_turnover_rate_by_vtype_{transport_type}_{medium}'] = [fig, title_text, PLOTTED]
                
            elif transport_type == 'freight':
                #now plot
                fig = px.line(turnover_rate_by_vtype_economy.loc[turnover_rate_by_vtype_economy['Transport Type']=='freight'],x='Date', y='Turnover_rate', line_dash = 'Medium', color='Drive', title='Freight turnover_rate by Drive', color_discrete_map=colors_dict)
                
                #add units to y col
                if medium == 'all':
                    title_text = 'Mean freight turnover rate'#.format(turnover_rate_by_vtype_economy['Unit'].unique()[0])
                elif medium == 'non_road':
                    title_text = 'Mean freight turnover rate for non road'
                elif medium == 'road':
                    title_text = 'Mean freight turnover rate for road'
                    
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][f'line_turnover_rate_by_vtype_{transport_type}_{medium}'] = [fig, title_text, PLOTTED]
                
            elif transport_type == 'all':
                # #get mean again because there are some Drives used for bnoth ttypes:
                # # turnover_rate_by_vtype_economy = turnover_rate_by_vtype_economy.groupby(['Economy', 'Date','Medium', 'Drive','Unit'])['Turnover_rate'].mean().reset_index().copy()
                #sum across transport types
                fig = px.line(turnover_rate_by_vtype_economy,x='Date', y='Turnover_rate', line_dash = 'Transport Type', color='Drive', title='Turnover_rate by Drive', color_discrete_map=colors_dict)
                #zoom graph in so y axis is from 0 to 0.3
                fig.update_yaxes(range=[0, 0.3])
                #add units to y col
                if medium == 'all':
                    title_text = 'Mean turnover rate'#.format(turnover_rate_by_vtype_economy['Unit'].unique()[0])
                elif medium == 'non_road':
                    title_text = 'Mean turnover rate for non road'
                elif medium == 'road':
                    title_text = 'Mean turnover rate for road'
                    
                            
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][f'line_turnover_rate_by_vtype_{transport_type}_{medium}'] = [fig, title_text, PLOTTED]
                if WRITE_HTML:
                    write_graph_to_html(config, filename=f'turnover_rate_by_vtype_{transport_type}_{medium}_{scenario}.html', graph_type='line', plot_data=turnover_rate_by_vtype_economy,  economy=economy, x='Date', y='Turnover_rate', line_dash = 'Transport Type', color='Drive', title=f'Turnover rate by Drive - {scenario}', y_axes_title='%', legend_title='', colors_dict=colors_dict, font_size=30, marker_line_width=2.5)
                    
            else:
                raise ValueError('transport_type must be passenger, all or freight')
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(turnover_rate_by_vtype_economy['Drive'].unique().tolist())
    return fig_dict, color_preparation_list

def emissions_by_fuel_type(config, ECONOMY_IDs, emissions_factors, model_output_with_fuels_df, fig_dict, color_preparation_list, colors_dict, transport_type, USE_AVG_GENERATION_EMISSIONS_FACTOR=True, USE_CUM_SUM_OF_EMISSIONS=False, WRITE_HTML=True):
    PLOTTED=True
    model_output_with_fuels = model_output_with_fuels_df.copy()
    #TEMP #WHERE TRANSPORT TYPE IS FREIGHT or medium is not road, SET THE electricty yse to 0. This is so we can test what the effect of electriicyt is 
    # model_output_with_fuels.loc[(model_output_with_fuels['Transport Type']=='freight') | (model_output_with_fuels['Medium']!='road') & (model_output_with_fuels['Fuel']=='17_electricity'), 'Energy'] = 0
    #load in data and recreate plot, as created in all_economy_graphs
    #loop through scenarios and grab the data for each scenario:
    model_output_with_fuels_sum= model_output_with_fuels[['Economy', 'Scenario','Date', 'Fuel', 'Transport Type','Energy']].groupby(['Economy', 'Scenario','Date','Transport Type', 'Fuel']).sum().reset_index().copy()
    
    #rename fuel_code to fuel in emissions_factors
    emissions_factors = emissions_factors.rename(columns={'fuel_code':'Fuel'})
    #join on the emissions factors (has the cols fuel_code,	Emissions factor (MT/PJ))
    model_output_with_fuels_sum = model_output_with_fuels_sum.merge(emissions_factors, how='left', on='Fuel')
    
    if USE_AVG_GENERATION_EMISSIONS_FACTOR:
        gen='_gen'
        #pull in the 8th outlook emissions factors by year, then use that to claculate the emissions for electricity.
        emissions_factor_elec = pd.read_csv(os.path.join(config.root_dir, 'input_data', 'from_8th', 'outlook_8th_emissions_factors_with_electricity.csv'))#c:\Users\finbar.maunsell\github\aperc-emissions\output_data\outlook_8th_emissions_factors_with_electricity.csv
        #extract the emissions factor for elctricity for each economy
        emissions_factor_elec = emissions_factor_elec[emissions_factor_elec.fuel_code=='17_electricity'].copy()
        #rename Carbon Neutral Scenario to Target
        emissions_factor_elec['Scenario'] = emissions_factor_elec['Scenario'].replace('Carbon Neutral', 'Target')
        #capitalise the cols
        emissions_factor_elec.columns = [x.capitalize() for x in emissions_factor_elec.columns]
        #rename fuel code to fuel
        emissions_factor_elec = emissions_factor_elec.rename(columns={'Fuel_code':'Fuel', 'Year':'Date', 'Emissions factor (mt/pj)':'Emissions factor (MT/PJ)'})
        #merge on economy and year and fuel code
        model_output_with_fuels_sum = model_output_with_fuels_sum.merge(emissions_factor_elec, on=['Date', 'Economy', 'Scenario', 'Fuel'], how='left', indicator=True, suffixes=('', '_elec'))
        #where indicator is both, use the new value
        model_output_with_fuels_sum['Emissions factor (MT/PJ)'] = np.where(model_output_with_fuels_sum['_merge']=='both', model_output_with_fuels_sum['Emissions factor (MT/PJ)_elec'], model_output_with_fuels_sum['Emissions factor (MT/PJ)'])
        #fill any missing values using ffill after sorting by date and grouping by 'Economy', 'Scenario','Date', 'Fuel', 'Transport Type'
        model_output_with_fuels_sum['Emissions factor (MT/PJ)'] = model_output_with_fuels_sum.sort_values(by='Date').groupby(['Economy', 'Scenario','Date','Transport Type', 'Fuel'])['Emissions factor (MT/PJ)'].fillna(method='ffill')
        #drop columns
        model_output_with_fuels_sum = model_output_with_fuels_sum.drop(columns=['Emissions factor (MT/PJ)_elec', '_merge'])
    else:
        gen=''
    #identify where there are no emissions factors:
    missing_emissions_factors = model_output_with_fuels_sum.loc[model_output_with_fuels_sum['Emissions factor (MT/PJ)'].isna()].copy()
    if len(missing_emissions_factors)>0:
        breakpoint()
        time.sleep(1)
        raise ValueError(f'missing emissions factors, {missing_emissions_factors.Fuel.unique()}')
    
    #calculate emissions:
    model_output_with_fuels_sum['Emissions'] = model_output_with_fuels_sum['Energy'] * model_output_with_fuels_sum['Emissions factor (MT/PJ)']

    model_output_with_fuels_sum['Measure'] = 'Emissions'
    model_output_with_fuels_sum['Unit'] = 'MtCO2'
    
    #set y axis to be the maximum sum of all values for each economy and scenario:
    y_axis_max = model_output_with_fuels_sum.groupby(['Economy', 'Scenario'])['Emissions'].sum().max() * 1.1
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        emissions_by_fuel_type_scen = model_output_with_fuels_sum.loc[(model_output_with_fuels_sum['Scenario']==scenario)].copy()
        
        for economy in ECONOMY_IDs:
            #filter to economy
            emissions_by_fuel_type_economy = emissions_by_fuel_type_scen.loc[(emissions_by_fuel_type_scen['Economy']==economy)].copy()
            
            emissions_by_fuel_type_economy = emissions_by_fuel_type_economy.groupby(['Fuel']).filter(lambda x: not all(x['Emissions'] == 0))
            # calculate total 'Emissions' for each 'Fuel' 
            total_emissions_per_fuel = emissions_by_fuel_type_economy.groupby('Fuel')['Emissions'].sum()

            if USE_CUM_SUM_OF_EMISSIONS:
                emissions_by_fuel_type_economy = emissions_by_fuel_type_economy.sort_values(by='Date').copy()
                emissions_by_fuel_type_economy['Emissions'] = emissions_by_fuel_type_economy.groupby(['Economy', 'Scenario','Transport Type', 'Fuel'])['Emissions'].transform(pd.Series.cumsum)
                # breakpoint()
            # Create an ordered category of 'Fuel' labels sorted by total 'Emissions'
            emissions_by_fuel_type_economy['Fuel'] = pd.Categorical(
                emissions_by_fuel_type_economy['Fuel'],
                categories = total_emissions_per_fuel.sort_values(ascending=False).index,
                ordered=True
            )

            # Now sort the DataFrame by the 'Fuel' column:
            emissions_by_fuel_type_economy.sort_values(by='Fuel', inplace=True)
            
            if not USE_CUM_SUM_OF_EMISSIONS:
                #add units to y col
                if transport_type!='all':
                    title_text = 'Emissions by Fuel {} ({})'.format(transport_type, emissions_by_fuel_type_economy['Unit'].unique()[0])
                else:
                    title_text = 'Emissions by Fuel ({})'.format( emissions_by_fuel_type_economy['Unit'].unique()[0])
                plot_id = f'emissions_by_fuel_type_{transport_type}{gen}'
            else:
                
                #add units to y col
                if transport_type!='all':
                    title_text = 'Accumulated emissions by Fuel {} ({})'.format(transport_type, emissions_by_fuel_type_economy['Unit'].unique()[0])
                else:
                    title_text = 'Accumulated emissions by Fuel ({})'.format( emissions_by_fuel_type_economy['Unit'].unique()[0])
                
                plot_id = f'emissions_by_fuel_type_{transport_type}{gen}_accumulated'
            if transport_type=='passenger':
                #now plot
                fig = px.area(emissions_by_fuel_type_economy.loc[emissions_by_fuel_type_economy['Transport Type']=='passenger'], x='Date', y='Emissions', color='Fuel', title='Emissions by Fuel', color_discrete_map=colors_dict)
                fig.update_layout(yaxis_range=(0, y_axis_max))
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][plot_id] = [fig, title_text, PLOTTED]
                
            elif transport_type == 'freight':
                #now plot
                fig = px.area(emissions_by_fuel_type_economy.loc[emissions_by_fuel_type_economy['Transport Type']=='freight'], x='Date', y='Emissions', color='Fuel', title='Emissions by Fuel', color_discrete_map=colors_dict)
                fig.update_layout(yaxis_range=(0, y_axis_max))
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][plot_id] = [fig, title_text, PLOTTED]
                
            elif transport_type == 'all':
                #sum across transport types
                emissions_by_fuel_type_economy = emissions_by_fuel_type_economy.groupby(['Economy', 'Date', 'Fuel','Unit'], group_keys=False).sum().reset_index()
                #now plot
                fig = px.area(emissions_by_fuel_type_economy, x='Date', y='Emissions', color='Fuel', title='Emissions by Fuel', color_discrete_map=colors_dict)
                fig.update_layout(yaxis_range=(0, y_axis_max))
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][plot_id] = [fig, title_text, PLOTTED]
                if WRITE_HTML:
                    write_graph_to_html(config, filename=f'emissions_by_fuel_type_{transport_type}{gen}_{scenario}.html', graph_type='area', plot_data=emissions_by_fuel_type_economy,  economy=economy, x='Date', y='Emissions', color='Fuel', title=f'Emissions by Fuel - {scenario}', y_axes_title='MtCO2', legend_title='', colors_dict=colors_dict, font_size=30, marker_line_width=2.5)
            else:
                raise ValueError('transport_type must be passenger, all or freight')
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(emissions_by_fuel_type_economy['Fuel'].unique().tolist())
    return fig_dict, color_preparation_list

 
def plot_comparison_of_energy_by_dataset(config, ECONOMY_IDs, energy_output_for_outlook_data_system_df, bunkers_data_df, energy_use_esto, esto_bunkers_data, energy_8th, fig_dict, color_preparation_list, colors_dict, mapping_type, EMISSIONS=False, USE_AVG_GENERATION_EMISSIONS_FACTOR=False, INCLUDE_8TH=False, INCLUDE_BUNKERS=False, ONLY_BUNKERS=False, WRITE_HTML=True):
    """plot the energy use for each economy and scenario for the 8th, 9th and ESTO models. The plot will be a line chart with energy on the y axis and year on the x axis. The lines will be the different fuels. The color of the lines will be the dataset (9th, 8th or ESTO). 

    Args:
        ECONOMY_IDs (list): list of economies to plot
        energy_output_for_outlook_data_system_df (df): energy use for 9th model
        energy_use_esto (df): energy use for esto
        energy_8th (df): energy use for 8th model
        fig_dict (dict): dictionary with keys of economy and scenario and values of a list of figs and title texts
        color_preparation_list (list): list of lists of the labels for the color parameter in each of the plots. This is so we can match them against suitable colors.
        colors_dict (dict): dictionary with keys of the labels for the color parameter in each of the plots and values of the color code for the label.
        mapping_type (str): either 'simplified' or 'all'. Used to map the fuels to a smaller set of fuels.

    Returns:
        fig_dict (dict): dictionary with keys of economy and scenario and values of a list of figs and title texts
        color_preparation_list (list): list of lists of the labels for the color parameter in each of the plots. This is so we can match them against suitable colors.
    """
    PLOTTED=True
    model_output_with_fuels = energy_output_for_outlook_data_system_df.copy()
    energy_use_esto_df = energy_use_esto.copy()
    esto_bunkers_data_df = esto_bunkers_data.copy()
    energy_8th_df = energy_8th.copy()#.drop(columns=['Stocks', 'Activity'])
    bunkers_data = bunkers_data_df.copy()
    #create col in both which refers to where they came from:
    energy_use_esto_df['Dataset'] = 'ESTO'
    esto_bunkers_data_df['Dataset'] = 'ESTO'
    model_output_with_fuels['Dataset'] = '9th_model'
    energy_8th_df['Dataset'] = '8th_model'
    bunkers_data['Dataset'] = '9th_model'
    #add bunnkers to 9th data
    if INCLUDE_BUNKERS:
        model_output_with_fuels = pd.concat([model_output_with_fuels, bunkers_data])
    else:
        pass
        #drop it from energy_8th_df and energy_use_esto_df
        # breakpoint()#todo
    if INCLUDE_8TH:
        if INCLUDE_BUNKERS:
            raise ValueError('Cannot include 8th and bunkers')
        #create a new df with only the data we need: 
        energy_use_by_fuel_type = pd.concat([model_output_with_fuels, energy_use_esto_df,energy_8th_df])
    else:
        if INCLUDE_BUNKERS:
            #create a new df with only the data we need: 
            energy_use_by_fuel_type = pd.concat([model_output_with_fuels, energy_use_esto_df,esto_bunkers_data_df])
        else:
            #create a new df with only the data we need: 
            energy_use_by_fuel_type = pd.concat([model_output_with_fuels, energy_use_esto_df])
    if ONLY_BUNKERS:
        if INCLUDE_8TH:
            raise ValueError('Cannot include 8th and bunkers')
        energy_use_by_fuel_type = pd.concat([bunkers_data, esto_bunkers_data_df])
    # #because of the way we mapped drive to fuel in the data prep phase, where medium is not road then set drive to medium. This will decrease some of the granularity of the data, but it will allow us to compare the data across the models more easily (plus there are too many lines anyway!)
    # energy_use_by_fuel_type.loc[energy_use_by_fuel_type['Medium']!='road', 'Fuel'] = energy_use_by_fuel_type.loc[energy_use_by_fuel_type['Medium']!='road', 'Medium']
    
    energy_use_by_fuel_type = energy_use_by_fuel_type[['Economy','Scenario', 'Date', 'Fuel', 'Energy','Dataset']].groupby(['Economy','Scenario', 'Date','Dataset', 'Fuel']).sum().reset_index()
    
    ############################################################################################################################################################
    if EMISSIONS:
        energy_use_by_fuel_type, electricity_emissions, emissions_factors = calculate_emissions(config, energy_use_by_fuel_type, all_data=None, USE_AVG_GENERATION_EMISSIONS_FACTOR=False, drive_column=None, energy_column = 'Energy', SUPPLIED_COLS =['Economy','Scenario', 'Date','Dataset', 'Fuel', 'Energy'],DROP_FUELS=False)
        energy_col = 'Emissions'
        extra_identifier = '_emissions'
        unit = 'MtCO2'
    else:
        energy_col = 'Energy'
        extra_identifier= ''
        unit = 'PJ'
    ############################################################################################################################################################
    #create a total fuel for each dataset. this will jsut be the sum of energy for each dataset, by year, scenario and economy:
    energy_use_by_fuel_type_totals = energy_use_by_fuel_type[['Economy','Scenario', 'Date','Dataset', energy_col]].groupby(['Economy','Scenario', 'Date','Dataset']).sum(numeric_only=True).reset_index().copy()
    #set Fuel to total:
    energy_use_by_fuel_type_totals['Fuel'] = 'Total'
    #cocnat the total onto the main df:
    energy_use_by_fuel_type = pd.concat([energy_use_by_fuel_type, energy_use_by_fuel_type_totals])
    energy_use_by_fuel_type = map_fuels(config, energy_use_by_fuel_type, value_col=energy_col, index_cols=['Economy','Scenario', 'Date','Dataset', 'Fuel'], mapping_type=mapping_type)
    
    #add units (by setting measure to Energy haha)
    energy_use_by_fuel_type['Measure'] = energy_col
    #add units
    energy_use_by_fuel_type['Unit'] = energy_use_by_fuel_type['Measure'].map(config.measure_to_unit_concordance_dict)
    #load in data and recreate plot, as created in all_economy_graphs
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        energy_use_by_fuel_type_s = energy_use_by_fuel_type.loc[(energy_use_by_fuel_type['Scenario']==scenario)].copy()
        for economy in ECONOMY_IDs:
            #filter to economy
            energy_use_by_fuel_type_economy = energy_use_by_fuel_type_s.loc[energy_use_by_fuel_type_s['Economy']==economy].copy()
            
            #now plot
            fig = px.line(energy_use_by_fuel_type_economy, x='Date', y=energy_col, color='Fuel',line_dash='Dataset', title=f'Compared {energy_col} by Fuel', color_discrete_map=colors_dict)
            plot_id = f'compare_energy_{mapping_type}{extra_identifier}'
            if INCLUDE_8TH:
                title_text = f'{energy_col} (8th,9th,ESTO)'
                plot_id = plot_id+'_8th'
            else:
                title_text = f'{energy_col} (9th,ESTO)'
            if INCLUDE_BUNKERS:
                title_text = title_text.replace(')', ',Bunkers)')
                plot_id = plot_id+'_bunkers' 
            if ONLY_BUNKERS:
                title_text = title_text.replace(energy_col, f'Bunkers {energy_col}')
                #drop ,Bunkers) if it exists
                title_text = title_text.replace(',Bunkers)', ')')
                plot_id = plot_id+'_only_bunkers'
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario][plot_id] = [fig, title_text, PLOTTED]
            
            if WRITE_HTML:
                write_graph_to_html(config, filename=f'{plot_id}_{scenario}_{economy}{extra_identifier}.html', graph_type='line', plot_data=energy_use_by_fuel_type_economy, economy=economy, x='Date', y=energy_col, color='Fuel', title=title_text, line_dash='Dataset', y_axes_title=f'{energy_col} {unit}', legend_title='Fuel', font_size=30, colors_dict=colors_dict)
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(energy_use_by_fuel_type_economy['Fuel'].unique().tolist())
    
    return fig_dict, color_preparation_list


def plot_comparison_of_energy_to_previous_9th_projection(config, ECONOMY_IDs, energy_output_for_outlook_data_system_df, bunkers_data_df, previous_projection_df, previous_bunkers_data_df, previous_projection_date_id, fig_dict, color_preparation_list, colors_dict, mapping_type, id_string, energy_use_esto, esto_bunkers_data, energy_8th, INCLUDE_BUNKERS, ONLY_BUNKERS, WRITE_HTML=True):
    """plot the energy use for each economy and scenario for the current 9th projection and a previous 9th projection to help with unerstanding the change. The plot will be a line chart with energy on the y axis and year on the x axis. The lines will be the different fuels. The color of the lines will be the fuel type and line dash will be the dataset (9th,or 'previous'). Will write the date id for previous one in the title
    Args:
        ECONOMY_IDs (list): list of economies to plot
        energy_output_for_outlook_data_system_df (df): energy use for 9th model
        previous_projection (df): energy use for previous projection
        previous_projection_date_id (str): date id for previous projection
        fig_dict (dict): dictionary with keys of economy and scenario and values of a list of figs and title texts
        color_preparation_list (list): list of lists of the labels for the color parameter in each of the plots. This is so we can match them against suitable colors.
        colors_dict (dict): dictionary with keys of the labels for the color parameter in each of the plots and values of the color code for the label.
        mapping_type (str): either 'simplified' or 'all'. Used to map the fuels to a smaller set of fuels.

    Returns:
        fig_dict (dict): dictionary with keys of economy and scenario and values of a list of figs and title texts
        color_preparation_list (list): list of lists of the labels for the color parameter in each of the plots. This is so we can match them against suitable colors.
    """
    PLOTTED=True
    model_output_with_fuels = energy_output_for_outlook_data_system_df.copy()
    previous_projection =previous_projection_df.copy()
    bunkers_data = bunkers_data_df.copy()
    previous_bunkers_data = previous_bunkers_data_df.copy()
    #create col in both which refers to where they came from:
    model_output_with_fuels['Dataset'] = '9th_model'
    previous_projection['Dataset'] = 'previous' 
    previous_bunkers_data['Dataset'] = 'previous'
    bunkers_data['Dataset'] = '9th_model'
    if INCLUDE_BUNKERS:
        model_output_with_fuels = pd.concat([model_output_with_fuels, bunkers_data])
        previous_projection = pd.concat([previous_projection, previous_bunkers_data])
    #create a new df with only the data we need: 
    energy_use_by_fuel_type = pd.concat([model_output_with_fuels, previous_projection])
    
    if 'ESTO' in id_string:
        energy_use_esto_df = energy_use_esto.copy()
        energy_use_esto_df['Dataset'] = 'ESTO'
        energy_use_by_fuel_type = pd.concat([energy_use_by_fuel_type, energy_use_esto_df])
        if INCLUDE_BUNKERS:
            esto_bunkers_data_df = esto_bunkers_data.copy()
            esto_bunkers_data_df['Dataset'] = 'ESTO'
            energy_use_by_fuel_type = pd.concat([energy_use_by_fuel_type, esto_bunkers_data_df])
    if '8th' in id_string:
        if INCLUDE_BUNKERS:
            #cannot include 8th bunkers since we have no data for it
            raise ValueError('Cannot include bunkers for 8th model')
        energy_8th_df = energy_8th.copy()
        energy_8th_df['Dataset'] = '8th_model'
        energy_use_by_fuel_type = pd.concat([energy_use_by_fuel_type, energy_8th_df])
    if ONLY_BUNKERS:
        if '8th' in id_string:
            raise ValueError('Cannot include 8th and bunkers')
        energy_use_by_fuel_type = pd.concat([bunkers_data, previous_bunkers_data])
        if 'ESTO' in id_string:
            esto_bunkers_data_df = esto_bunkers_data.copy()
            esto_bunkers_data_df['Dataset'] = 'ESTO'
            energy_use_by_fuel_type = pd.concat([energy_use_by_fuel_type, esto_bunkers_data_df])
    # #because of the way we mapped drive to fuel in the data prep phase, where medium is not road then set drive to medium. This will decrease some of the granularity of the data, but it will allow us to compare the data across the models more easily (plus there are too many lines anyway!)
    # energy_use_by_fuel_type.loc[energy_use_by_fuel_type['Medium']!='road', 'Fuel'] = energy_use_by_fuel_type.loc[energy_use_by_fuel_type['Medium']!='road', 'Medium']
    
    energy_use_by_fuel_type = energy_use_by_fuel_type[['Economy','Scenario', 'Date', 'Fuel', 'Energy','Dataset']].groupby(['Economy','Scenario', 'Date','Dataset', 'Fuel']).sum().reset_index()
    
    #create a total fuel for each dataset. this will jsut be the sum of energy for each dataset, by year, scenario and economy:
    energy_use_by_fuel_type_totals = energy_use_by_fuel_type[['Economy','Scenario', 'Date','Dataset', 'Energy']].groupby(['Economy','Scenario', 'Date','Dataset']).sum(numeric_only=True).reset_index().copy()
    #set Fuel to total:
    energy_use_by_fuel_type_totals['Fuel'] = 'Total'
    #cocnat the total onto the main df:
    energy_use_by_fuel_type = pd.concat([energy_use_by_fuel_type, energy_use_by_fuel_type_totals])
    
    energy_use_by_fuel_type = map_fuels(config, energy_use_by_fuel_type, value_col='Energy', index_cols=['Economy','Scenario', 'Date','Dataset', 'Fuel'], mapping_type=mapping_type)
    
    #add units (by setting measure to Energy haha)
    energy_use_by_fuel_type['Measure'] = 'Energy'
    #add units
    energy_use_by_fuel_type['Unit'] = energy_use_by_fuel_type['Measure'].map(config.measure_to_unit_concordance_dict)
    #load in data and recreate plot, as created in all_economy_graphs
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        energy_use_by_fuel_type_s = energy_use_by_fuel_type.loc[(energy_use_by_fuel_type['Scenario']==scenario)].copy()
        for economy in ECONOMY_IDs:
            #filter to economy
            energy_use_by_fuel_type_economy = energy_use_by_fuel_type_s.loc[energy_use_by_fuel_type_s['Economy']==economy].copy()
            
            #now plot
            fig = px.line(energy_use_by_fuel_type_economy, x='Date', y='Energy', color='Fuel',line_dash='Dataset', title='Compared Energy by Fuel', color_discrete_map=colors_dict)
            
            #add units to y col
            title_text = 'Energy (Current,{})'.format(previous_projection_date_id)#.format(energy_use_by_fuel_type_economy['Unit'].unique()[0])
            if 'ESTO' in id_string:
                title_text =  title_text.replace(')', ',ESTO)')
            if '8th' in id_string:
                title_text =  title_text.replace(')', ',8th)')
            if INCLUDE_BUNKERS:
                title_text =  title_text.replace(')', ',Bunkers)')
            if ONLY_BUNKERS:
                title_text = title_text.replace('Energy', 'Bunkers Energy')
                #drop ,Bunkers) if it exists
                title_text = title_text.replace(',Bunkers)', ')')
                
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario][id_string] = [fig, title_text, PLOTTED]
            
            if WRITE_HTML:
                write_graph_to_html(config, filename=f'{id_string}_{scenario}_{economy}.html', graph_type='line', plot_data=energy_use_by_fuel_type_economy, economy=economy, x='Date', y='Energy', color='Fuel', title=title_text, line_dash='Dataset', y_axes_title='Energy (PJ)', legend_title='Fuel', font_size=30, colors_dict=colors_dict)
            
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(energy_use_by_fuel_type_economy['Fuel'].unique().tolist())
    
    return fig_dict, color_preparation_list



def plot_pct_comparison_of_energy_compared_to_8th(config, ECONOMY_IDs, energy_output_for_outlook_data_system_df, bunkers_data_df, energy_8th, fig_dict, color_preparation_list, colors_dict, mapping_type, measure, INCLUDE_BUNKERS, WRITE_HTML=True):
    """plot the % difference between the 9th model and the 8th model for energy use by fuel type.

    Args:
        ECONOMY_IDs (list): list of economies to plot
        energy_output_for_outlook_data_system_df (df): energy output for outlook data system df
        energy_8th (df): energy output for 8th model
        fig_dict (dict): dictionary of figs for each economy and scenario
        color_preparation_list (list): list of colors used
        colors_dict (dict): dictionary of colors
        mapping_type (str): mapping type for fuel. can be 'simplified' or 'all'       
        measure (str): measure to plot. can be 'pct_difference' or 'difference'
    """
    
    PLOTTED=True
    model_output_with_fuels = energy_output_for_outlook_data_system_df.copy()
    energy_8th_df = energy_8th.copy()#.drop(columns=['Stocks', 'Activity'])
    bunkers_data = bunkers_data_df.copy()
    #create col in both which refers to where they came from:
    model_output_with_fuels['Dataset'] = '9th_model'
    energy_8th_df['Dataset'] = '8th_model'
    bunkers_data['Dataset'] = '9th_model'
    if INCLUDE_BUNKERS:
        raise ValueError('Cannot include bunkers for 8th model')
        # model_output_with_fuels = pd.concat([model_output_with_fuels, bunkers_data])
    else:
        #drop it from energy_8th_df 
        # breakpoint()#todo
        pass#we are not using bunkers for this analysis but might in the future if we format 8th bunekrs data
    #create a new df with only the data we need: 
    energy_use_by_fuel_type = pd.concat([model_output_with_fuels,energy_8th_df])
    
    # #because of the way we mapped drive to fuel in the data prep phase, where medium is not road then set drive to medium. This will decrease some of the granularity of the data, but it will allow us to compare the data across the models more easily (plus there are too many lines anyway!)
    # energy_use_by_fuel_type.loc[energy_use_by_fuel_type['Medium']!='road', 'Fuel'] = energy_use_by_fuel_type.loc[energy_use_by_fuel_type['Medium']!='road', 'Medium']

    
    energy_use_by_fuel_type = energy_use_by_fuel_type[['Economy','Scenario', 'Date', 'Fuel', 'Energy','Dataset']].groupby(['Economy','Scenario', 'Date','Dataset', 'Fuel']).sum().reset_index()
    
    #create a total fuel for each dataset. this will jsut be the sum of energy for each dataset, by year, scenario and economy:
    energy_use_by_fuel_type_totals = energy_use_by_fuel_type[['Economy','Scenario', 'Date','Dataset', 'Energy']].groupby(['Economy','Scenario', 'Date','Dataset']).sum(numeric_only=True).reset_index().copy()
    #set Fuel to total:
    energy_use_by_fuel_type_totals['Fuel'] = 'Total'
    #cocnat the total onto the main df:
    energy_use_by_fuel_type = pd.concat([energy_use_by_fuel_type, energy_use_by_fuel_type_totals])
    
    energy_use_by_fuel_type = map_fuels(config, energy_use_by_fuel_type, value_col='Energy', index_cols=['Economy','Scenario', 'Date','Dataset', 'Fuel'], mapping_type=mapping_type)
    #pivot so we have dataset as cols, then we can calculate the % difference between the datasets:
    energy_use_by_fuel_type_wide = energy_use_by_fuel_type.pivot_table(index=['Economy','Scenario', 'Date','Fuel'], columns='Dataset', values='Energy').reset_index()
    #calc % difference between 9th and the others 
    energy_use_by_fuel_type_wide['9th_vs_8th_energy_difference'] = ((energy_use_by_fuel_type_wide['9th_model'] - energy_use_by_fuel_type_wide['8th_model']))
    energy_use_by_fuel_type_wide['9th_vs_8th_%_energy_difference'] = ((energy_use_by_fuel_type_wide['9th_model'] - energy_use_by_fuel_type_wide['8th_model'])/energy_use_by_fuel_type_wide['8th_model'])*100
    
    #if there are any abs percent differences greater than 500 then just set them to 500 so we can see the other lines:
    energy_use_by_fuel_type_wide['9th_vs_8th_%_energy_difference'] = energy_use_by_fuel_type_wide['9th_vs_8th_%_energy_difference'].clip(upper=100)
    energy_use_by_fuel_type_wide['9th_vs_8th_%_energy_difference'] = energy_use_by_fuel_type_wide['9th_vs_8th_%_energy_difference'].clip(lower=-100)
    
    #drop 8th and 9th cols:
    energy_use_by_fuel_type_wide = energy_use_by_fuel_type_wide.drop(columns=['8th_model', '9th_model'])
    
    energy_use_by_fuel_type =energy_use_by_fuel_type_wide.copy()
    
    #add units (by setting measure to Energy haha)
    energy_use_by_fuel_type['Measure'] = 'Energy'
    #add units
    energy_use_by_fuel_type['Unit'] = '%'
    
    #load in data and recreate plot, as created in all_economy_graphs
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        energy_use_by_fuel_type_s = energy_use_by_fuel_type.loc[(energy_use_by_fuel_type['Scenario']==scenario)].copy()
        for economy in ECONOMY_IDs:
            #filter to economy
            energy_use_by_fuel_type_economy = energy_use_by_fuel_type_s.loc[energy_use_by_fuel_type_s['Economy']==economy].copy()
            plot_id = f'compare_energy2_{measure}_{mapping_type}'
            if measure=='difference':
                #use 9th_vs_8th_energy_difference
                
                fig = px.line(energy_use_by_fuel_type_economy, x='Date', y='9th_vs_8th_energy_difference', color='Fuel', title='% difference in 9th vs 8th Energy by Fuel', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Difference in 9th vs 8th Energy by Fuel'
                #.format(energy_use_by_fuel_type_economy['Unit'].unique()[0])
                if INCLUDE_BUNKERS:
                    title_text = title_text + ', including bunkers'
                    plot_id = plot_id+'_bunkers'                    
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][f'compare_energy2_{measure}_{mapping_type}'] = [fig, title_text, PLOTTED]
                
            elif measure == 'pct_difference':
                #now plot
                fig = px.line(energy_use_by_fuel_type_economy, x='Date', y='9th_vs_8th_%_energy_difference', color='Fuel', title='% difference in 9th vs 8th Energy by Fuel', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = '% difference in 9th vs 8th Energy by Fuel'
                if INCLUDE_BUNKERS:
                    title_text = title_text + ', including bunkers'
                    plot_id = plot_id+'_bunkers'
                #.format(energy_use_by_fuel_type_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][plot_id] = [fig, title_text, PLOTTED]
                
                if WRITE_HTML:
                    write_graph_to_html(config, filename=f'{plot_id}_{scenario}_{economy}.html', graph_type='line', plot_data=energy_use_by_fuel_type_economy, economy=economy, x='Date', y='9th_vs_8th_%_energy_difference', color='Fuel', title=title_text, y_axes_title='Percent Energy Difference (%)', legend_title='Fuel', font_size=30, colors_dict=colors_dict)
            
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(energy_use_by_fuel_type_economy['Fuel'].unique().tolist())
    
    return fig_dict, color_preparation_list



def plot_energy_efficiency_timeseries(config, ECONOMY_IDs, model_output_detailed, fig_dict, DROP_NON_ROAD_TRANSPORT, color_preparation_list, colors_dict, transport_type, extra_ice_line=True, extra_bev_line=True, vehicle_type_grouping='simplified', WRITE_HTML=True):
    PLOTTED=True
    conversion_factors = pd.read_csv(os.path.join(config.root_dir, 'config', 'concordances_and_config_data', 'conversion_factors.csv'))
    #to help with checking that the data is realistic, plot growth in energy efficiency here:
    
    energy_eff = model_output_detailed.copy()
    if DROP_NON_ROAD_TRANSPORT:
        energy_eff = energy_eff.loc[energy_eff['Medium']=='road']
    else:
        #set vehicle type to medium so we can plot strip plot by vehicle type: 
        energy_eff.loc[energy_eff['Medium'] != 'road', 'Vehicle Type'] = energy_eff.loc[energy_eff['Medium'] != 'road', 'Medium']
    if transport_type == 'passenger':
        energy_eff = energy_eff.loc[energy_eff['Transport Type']=='passenger']
    elif transport_type == 'freight':
        energy_eff = energy_eff.loc[energy_eff['Transport Type']=='freight']
    
    #group the vehicle types
    energy_eff = remap_vehicle_types(config, energy_eff, value_col='Efficiency', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'],vehicle_type_mapping_set=vehicle_type_grouping, aggregation_type=('weighted_average', 'Activity'))
    #calc weighted mean of efficiency by using activity as the weight and, importantly, remove date, scenario
    # energy_eff = energy_eff[['Date', 'Economy', 'Vehicle Type', 'Scenario','Efficiency']].groupby(['Date','Economy','Scenario','Vehicle Type']).mean().reset_index()
    
    energy_eff['ICE_ONLY'] = 'all'
    if extra_ice_line:
        #we want to create a dotted line for each vehicle type that shows the ice efficiency. that is the efficiency when you only consider the ice_d and ice_g vehicles.
        #first, filter to only ice_d and ice_g:
        energy_eff_ice = energy_eff.loc[energy_eff['Drive'].isin(['ice_d', 'ice_g'])].copy()
        #just label ICE_ONLY as True
        energy_eff_ice['ICE_ONLY'] = 'ice_only'
        #now concat the two dfs:
        energy_eff = pd.concat([energy_eff, energy_eff_ice])
    
    if extra_bev_line:
        #we want to create a dotted line for each vehicle type that shows the ice efficiency. that is the efficiency when you only consider the ice_d and ice_g vehicles.
        #first, filter to only ice_d and ice_g:
        energy_eff_bev = energy_eff.loc[energy_eff['Drive'].isin(['bev'])].copy()
        #just label ICE_ONLY as True
        energy_eff_bev['ICE_ONLY'] = 'bev_only'
        #now concat the two dfs:
        energy_eff = pd.concat([energy_eff, energy_eff_bev])
        
    energy_eff['Efficiency_weighted'] = energy_eff['Efficiency'] * energy_eff['Activity']
    energy_eff = energy_eff[['Date', 'Economy', 'Vehicle Type', 'Scenario','Efficiency_weighted', 'Efficiency', 'Activity', 'ICE_ONLY']].groupby(['Date','Economy','Scenario','Vehicle Type', 'ICE_ONLY']).sum().reset_index()
    #calculate weighted average
    energy_eff['Efficiency'] = energy_eff['Efficiency_weighted']/energy_eff['Activity']
    energy_eff = energy_eff.drop(columns=['Efficiency_weighted', 'Activity'])

    # #simplfiy drive type using remap_drive_types
    # fkm = remap_drive_types(config, fkm, value_col='freight_tonne_km', new_index_cols = ['Economy', 'Date', 'Scenario','Drive'])
    
    #add units (by setting measure to Freight_tonne_km haha)
    energy_eff['Measure'] = 'Efficiency'
    
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        energy_eff_by_scen = energy_eff.loc[(energy_eff['Scenario']==scenario)].copy()
        

        for economy in ECONOMY_IDs:
            #filter to economy
            energy_eff_by_scen_by_economy = energy_eff_by_scen.loc[energy_eff_by_scen['Economy']==economy].copy()
            ###################################
            #BASED ON THE ECONOMY, SET THE EFFICIENCY TO SOMETHING THAT IS COMPARABLE T THEIR OWN MEASURES (I.E. IN USA SET TO MPG, IN MAS SET TO L/100KM). Note that we will need to take into account the energy content of diesel and gasoline for ice_g, ice_d, phev_g and phev_d. (in hindsight had to set this based on vehicle type)
            #set unit to 'km per MJ' and we will change it if we need
            energy_eff_by_scen_by_economy['unit'] = 'km/MJ'
            energy_eff_by_scen_by_economy['conversion_fuel'] = np.where(energy_eff_by_scen_by_economy['Vehicle Type'].isin(['trucks', 'lcv']), 'diesel', 'petrol')
            #join to conversion factor using conversion fuel > fuel
            
            economy_to_conversion_factor = {
                '20_USA':'mpg_to_billion_km_per_pj',
                '10_MAS':'km_per_liter_to_km_per_mj'#a pj is 1bil mjs 
            }
            new_units = {
                '20_USA':'mpg',
                '10_MAS':'L/100km'
            }
            
            magnitude_multiplier = {
                '20_USA':1,
                '10_MAS':1/100
            }
            
            inverse_economies = ['10_MAS']
            if economy in economy_to_conversion_factor.keys():
                conversion_factors_new = conversion_factors[conversion_factors['conversion_factor']==economy_to_conversion_factor[economy]].copy()
                energy_eff_by_scen_by_economy = energy_eff_by_scen_by_economy.merge(conversion_factors_new, left_on='conversion_fuel', right_on='fuel', how='left', indicator=True)
                #check for missing merges
                bad_merges = energy_eff_by_scen_by_economy[energy_eff_by_scen_by_economy['_merge']!='both']
                if len(bad_merges)>0:
                    breakpoint()
                    raise ValueError('Cannot complete conversion factos merge, missing the rows: {}'.format(bad_merges))
                #do conversion
                energy_eff_by_scen_by_economy['Efficiency']=energy_eff_by_scen_by_economy['Efficiency']/energy_eff_by_scen_by_economy['value']
                energy_eff_by_scen_by_economy['unit'] = energy_eff_by_scen_by_economy['original_unit']   
                if economy in magnitude_multiplier.keys():
                    energy_eff_by_scen_by_economy['Efficiency']=energy_eff_by_scen_by_economy['Efficiency'] * magnitude_multiplier[economy]
                if economy in inverse_economies:
                    energy_eff_by_scen_by_economy['Efficiency'] = 1/energy_eff_by_scen_by_economy['Efficiency']   
                #rename the unit to the new unit
                energy_eff_by_scen_by_economy['unit'] = new_units[economy]
            ###################################        
            unit = energy_eff_by_scen_by_economy['unit'].unique()[0]
            if transport_type == 'all':
                title='Energy efficiency ({})'.format(unit)
            elif transport_type.isin(['passenger', 'freight']):
                title='Energy efficiency - {} ({})'.format(transport_type,unit)
                
            fig = px.line(energy_eff_by_scen_by_economy, x='Date', y='Efficiency', color='Vehicle Type',line_dash='ICE_ONLY', title=title, color_discrete_map=colors_dict)#, line_dash='Vehicle Type')
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario][f'energy_efficiency_timeseries_{transport_type}'] = [fig, title, PLOTTED]
            if WRITE_HTML:
                #keep only lpv if it is inthere
                if 'lpv' in energy_eff_by_scen_by_economy['Vehicle Type'].unique():
                    energy_eff_by_scen_by_economy = energy_eff_by_scen_by_economy.loc[energy_eff_by_scen_by_economy['Vehicle Type']=='lpv'].copy()
                
                ######TEMPORARY: save the df to a csv so we can compare scenarios
                #save the df to a csv
                # energy_eff_by_scen_by_economy.to_csv(f'plotting_output\\dashboards\\{economy}\\individual_graphs\\{scenario}_{economy}_energy_efficiency_timeseries_{transport_type}_no_HEVs.csv')
                #load the df from the csv and merge it but label it as 'no HEV's'
                # energy_eff_by_scen_by_economy_no_HEVS = pd.read_csv(config.root_dir + config.slash +f'plotting_output\\dashboards\\{economy}\\individual_graphs\\{scenario}_{economy}_energy_efficiency_timeseries_{transport_type}_no_HEVs.csv')
                # energy_eff_by_scen_by_economy['line_type'] = 'HEVs'
                # energy_eff_by_scen_by_economy_no_HEVS['line_type'] = 'no_HEVs'
                # energy_eff_by_scen_by_economy = pd.concat([energy_eff_by_scen_by_economy, energy_eff_by_scen_by_economy_no_HEVS])
                
                ######TEMPORARY: save the df to a csv so we can compare scenarios
                
                write_graph_to_html(config, filename=f'{scenario}_{economy}_energy_efficiency_timeseries_{transport_type}.html', graph_type='line', plot_data=energy_eff_by_scen_by_economy,  economy=economy, x='Date', y='Efficiency', color='ICE_ONLY', title=f'Energy efficiency - {scenario} - {economy}', y_axes_title='km per MJ', legend_title='', colors_dict=colors_dict, font_size=30, line_width=10)
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(energy_eff_by_scen_by_economy['Vehicle Type'].unique().tolist())
    
    return fig_dict, color_preparation_list


import os
import pandas as pd
import numpy as np
import plotly.express as px

def plot_energy_efficiency_strip(config, ECONOMY_IDs, model_output_detailed, fig_dict, DROP_NON_ROAD_TRANSPORT, color_preparation_list, colors_dict, WRITE_HTML=True):
    PLOTTED=True
    #to help with checking that the data is realistic, plot energy efficiency here:
    
    energy_eff = model_output_detailed.copy()
    if DROP_NON_ROAD_TRANSPORT:
        energy_eff = energy_eff.loc[energy_eff['Medium']=='road']
    else:
        #we need to calcualte efficiency from intensity for the non road transport. Unfortunately this will be in terms of pkm or fkm, not km. so it might be a bit wacky?
        energy_eff.loc[energy_eff['Medium'] != 'road', 'Efficiency'] = 1 / energy_eff.loc[energy_eff['Medium'] != 'road', 'Intensity']
        #set vehicle type to medium so we can plot strip plot by vehicle type: 
        energy_eff.loc[energy_eff['Medium'] != 'road', 'Vehicle Type'] = energy_eff.loc[energy_eff['Medium'] != 'road', 'Medium']
        #note that in the case where we are using non road transport, we are using the df model_output_detailed_detailed_non_road_drives so we can access drive var for non road.
    
    #calc mean and, importantly, remove date, scenario
    energy_eff = energy_eff[['Economy', 'Vehicle Type', 'Drive', 'Scenario','Efficiency']].groupby(['Economy', 'Vehicle Type','Scenario', 'Drive']).mean().reset_index()

    # #simplfiy drive type using remap_drive_types
    # fkm = remap_drive_types(config, fkm, value_col='freight_tonne_km', new_index_cols = ['Economy', 'Date', 'Scenario','Drive'])
    
    #add units (by setting measure to Freight_tonne_km haha)
    energy_eff['Measure'] = 'Efficiency'
    #add units
    energy_eff['Unit'] = energy_eff['Measure'].map(config.measure_to_unit_concordance_dict)
    
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        energy_eff_by_scen = energy_eff.loc[(energy_eff['Scenario']==scenario)].copy()

        for economy in ECONOMY_IDs:
            #filter to economy
            energy_eff_by_scen_by_economy = energy_eff_by_scen.loc[energy_eff_by_scen['Economy']==economy].copy()
            
            #add fig to dictionary for scenario and economy:
            if DROP_NON_ROAD_TRANSPORT:
                title='Energy efficiency by vehicle type (km per MJ)'
            else:
                title='Energy efficiency by vehicle type (non road based on inverse intensity) (km per MJ)'
            fig = px.strip(energy_eff_by_scen_by_economy, x='Vehicle Type', y='Efficiency', color='Drive', title=title, color_discrete_map=colors_dict)
            #add fig to dictionary for scenario and economy:
            if DROP_NON_ROAD_TRANSPORT:
                fig_dict[economy][scenario]['energy_efficiency_road_strip'] = [fig, title, PLOTTED]
            else:
                fig_dict[economy][scenario]['energy_efficiency_all_strip'] = [fig, title, PLOTTED]
            
            if WRITE_HTML:
                filename = f'energy_efficiency_all_strip_{scenario}_{economy}.html'
                write_graph_to_html(config, filename=filename, graph_type='strip', plot_data=energy_eff_by_scen_by_economy, economy=economy, x='Vehicle Type', y='Efficiency', color='Drive', title=title, y_axes_title='Efficiency (km per MJ)', legend_title='Drive', font_size=30, colors_dict=colors_dict)
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(energy_eff_by_scen_by_economy['Drive'].unique().tolist())
    return fig_dict, color_preparation_list


def plot_energy_intensity_strip(config, ECONOMY_IDs, model_output_detailed_detailed_non_road_drives, fig_dict, color_preparation_list, colors_dict, WRITE_HTML=True):
    PLOTTED=True
    #to help with checking that the data is realistic, plot energy intensity here:
    
    energy_int = model_output_detailed_detailed_non_road_drives.copy()
    #we need to calcualte intensity for road by doing energy / activity:
    energy_int.loc[energy_int['Medium'] == 'road', 'Intensity'] = energy_int.loc[energy_int['Medium'] == 'road', 'Energy'] / energy_int.loc[energy_int['Medium'] == 'road', 'Activity']
    #set vehicle type to medium so we can plot strip plot by vehicle type: 
    energy_int.loc[energy_int['Medium'] != 'road', 'Vehicle Type'] = energy_int.loc[energy_int['Medium'] != 'road', 'Medium']
    
    #calc mean and, importantly, remove date, scenario
    energy_int = energy_int[['Economy', 'Vehicle Type', 'Drive', 'Scenario','Intensity']].groupby(['Economy', 'Vehicle Type','Scenario', 'Drive']).mean().reset_index()

    # #simplfiy drive type using remap_drive_types
    # fkm = remap_drive_types(config, fkm, value_col='freight_tonne_km', new_index_cols = ['Economy', 'Date', 'Scenario','Drive'])
    
    #add units (by setting measure to Freight_tonne_km haha)
    energy_int['Measure'] = 'Intensity'
    #add units
    energy_int['Unit'] = energy_int['Measure'].map(config.measure_to_unit_concordance_dict)
    
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        energy_int_by_scen = energy_int.loc[(energy_int['Scenario']==scenario)].copy()

        for economy in ECONOMY_IDs:
            #filter to economy
            energy_int_by_scen_by_economy = energy_int_by_scen.loc[energy_int_by_scen['Economy']==economy].copy()

            title='Intensity by vehicle type (Pj per Bn activity km)'
            fig = px.strip(energy_int_by_scen_by_economy, x='Vehicle Type', y='Intensity', color='Drive', title=title, color_discrete_map=colors_dict)
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['energy_intensity_strip'] = [fig, title, PLOTTED]
            
            if WRITE_HTML:
                filename = f'energy_intensity_strip_{scenario}_{economy}.html'
                write_graph_to_html(config, filename=filename, graph_type='strip', plot_data=energy_int_by_scen_by_economy, economy=economy, x='Vehicle Type', y='Intensity', color='Drive', title=title, y_axes_title='Intensity (Pj per Bn activity km)', legend_title='Drive', font_size=30, colors_dict=colors_dict)
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(energy_int_by_scen_by_economy['Drive'].unique().tolist())
    return fig_dict, color_preparation_list



def plot_energy_intensity_timeseries(config, ECONOMY_IDs, model_output_detailed_detailed_non_road_drives, fig_dict, color_preparation_list, colors_dict, medium, WRITE_HTML=True):
    """plot the energy intensity by medium and drive for each economy and scenario. The plot will be a line chart with energy intensity on the y axis and year on the x axis. The lines will be the different drives. The color of the lines will be the medium.

    Args:
        ECONOMY_IDs (list): list of economies to plot
        model_output_detailed_detailed_non_road_drives (df): df of model output for non road drives
        fig_dict (dict): dictionary of figs for each economy and scenario
        color_preparation_list (list): list of colors used
        colors_dict (dict): dictionary of colors
        medium (str): either 'all' or 'non_road'. Used to filter the data by medium

    Returns:
        fig_dict (dict): dictionary of figs for each economy and scenario
        color_preparation_list (list): list of colors used 
    """
    PLOTTED=True
    #to help with checking that the data is realistic, plot growth in energy efficiency here:
    
    energy_int = model_output_detailed_detailed_non_road_drives.copy()
    if medium == 'all':
        #we need to calcualte intensity for road by doing energy / activity:
        energy_int.loc[energy_int['Medium'] == 'road', 'Intensity'] = energy_int.loc[energy_int['Medium'] == 'road', 'Energy'] / energy_int.loc[energy_int['Medium'] == 'road', 'Activity']
    elif medium == 'non_road':
        energy_int = energy_int.loc[energy_int['Medium'] != 'road']
        
    #calc mean and, importantly, remove date, scenario
    energy_int = energy_int[['Date', 'Economy', 'Drive','Medium', 'Scenario','Intensity']].groupby(['Date','Economy','Scenario', 'Medium','Drive']).mean().reset_index()

    # #simplfiy drive type using remap_drive_types
    # fkm = remap_drive_types(config, fkm, value_col='freight_tonne_km', new_index_cols = ['Economy', 'Date', 'Scenario','Drive'])
    
    #add units (by setting measure to Freight_tonne_km haha)
    energy_int['Measure'] = 'Intensity'
    
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        energy_int_by_scen = energy_int.loc[(energy_int['Scenario']==scenario)].copy()
        

        for economy in ECONOMY_IDs:
            #filter to economy
            energy_int_by_scen_by_economy = energy_int_by_scen.loc[energy_int_by_scen['Economy']==economy].copy()

            #now plot
            if medium == 'non_road':
                title='Intensity nonroad (Bn activity km per pj)'
            elif medium == 'all':
                title='Intensity (Bn activity km per pj)'
            fig = px.line(energy_int_by_scen_by_economy, x='Date', y='Intensity',line_dash='Medium', color='Drive', title=title, color_discrete_map=colors_dict)

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario][f'energy_intensity_timeseries_{medium}'] = [fig, title, PLOTTED]
            
            if WRITE_HTML:
                filename =  f'energy_intensity_timeseries_{medium}_{scenario}_{economy}.html'
                write_graph_to_html(config, filename=filename, graph_type='line', plot_data=energy_int_by_scen_by_economy, economy=economy, x='Date', y='Intensity', color='Drive', title=title, y_axes_title='Intensity (Bn activity km per pj)', legend_title='Drive', font_size=30, colors_dict=colors_dict)

    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(energy_int_by_scen_by_economy['Drive'].unique().tolist())
    
    return fig_dict, color_preparation_list

def sales_and_turnover_lines(config, ECONOMY_IDs, model_output_detailed_df, fig_dict, color_preparation_list, colors_dict, transport_type, WRITE_HTML=True):
    PLOTTED=True
    #take in data on stocks and turnover. backcalcualte the sales and turnover then plot on a  timeseries chart so the turnover is negative and the sales is positive.
    #stocks are calcualted by calculating turnover based on last  years stocks, then adding that and new sales to last years total.. So, calcaultes turnover, by grabbing the previous year value, times by the turnover rate. THen get new sales, by adding the turnover to the current year value and then calculating the change in stocks from last year.
    #then plot the sales and turnover on a line
    model_output_detailed = model_output_detailed_df.copy()
    #sum up the stocks and turnover by economy, scenario, date, drive, vehicle type:
    #sort by date
    model_output_detailed = model_output_detailed.sort_values(by='Date')
    #shift the stocks by one year so we can calculate the change in stocks:
    model_output_detailed['previous_year_stocks'] = model_output_detailed.groupby(['Economy', 'Drive', 'Vehicle Type', 'Medium','Transport Type', 'Scenario'])['Stocks'].shift(1)
    
    #calcualte turnover
    model_output_detailed['turnover'] = -(model_output_detailed['previous_year_stocks'] * model_output_detailed['Turnover_rate'])
    #calculate new sales
    model_output_detailed['new_sales'] = - model_output_detailed['turnover'] + model_output_detailed['Stocks'] - model_output_detailed['previous_year_stocks']#is this corerect or hsould we minus prev year stocks
    
    #now sum up the turnover and new sales by economy, scenario, date, drive, transport type
    model_output_detailed = model_output_detailed[['Economy', 'Date', 'Drive', 'Transport Type', 'Scenario', 'turnover', 'new_sales']].groupby(['Economy', 'Date', 'Drive', 'Transport Type', 'Scenario']).sum().reset_index()
    
    # #group by 10 year intervals and sum up the turnover and new sales:
    # #set date to nearest 10 year interval above it eg. 2020 is 2020 but 2021-2030 is 2030
    # # model_output_detailed['Date'] = model_output_detailed['Date'].apply(lambda x: x + (10 - x%10))
    # model_output_detailed['Date'] = model_output_detailed['Date'].apply(lambda x: x + (10 - x % 10) % 10)
    # #might as well drop 2020 since it is only one year
    # model_output_detailed = model_output_detailed.loc[model_output_detailed['Date']!=2020].copy()
    
    #sum up the turnover and new sales by economy, date, drive, transport type and scenario:
    model_output_detailed = model_output_detailed[['Economy', 'Date', 'Drive', 'Transport Type', 'Scenario', 'turnover', 'new_sales']].groupby(['Economy', 'Date', 'Drive', 'Transport Type', 'Scenario']).sum().reset_index()
    #put turnover and new sales into long format:
    model_output_detailed = pd.melt(model_output_detailed, id_vars=['Economy', 'Date', 'Drive', 'Transport Type', 'Scenario'], value_vars=['turnover', 'new_sales'], var_name='Measure', value_name='Value')
    #
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        sales_and_turnover_by_scen = model_output_detailed.loc[(model_output_detailed['Scenario']==scenario)].copy()
        for economy in ECONOMY_IDs:
            #filter to economy
            sales_and_turnover_by_scen_by_economy = sales_and_turnover_by_scen.loc[sales_and_turnover_by_scen['Economy']==economy].copy()
            #now plot
            if transport_type == 'passenger':
                sales_and_turnover_by_scen_by_economy = sales_and_turnover_by_scen_by_economy.loc[sales_and_turnover_by_scen_by_economy['Transport Type']==transport_type].copy()
                title='Sales and turnover by drive - {}'.format(transport_type)
                # fig = px.bar(sales_and_turnover_by_scen_by_economy, x='Date', y='Value', barmode='stack',title=title, color_discrete_map=colors_dict, color='Drive', pattern_shape='Measure',  pattern_shape_sequence=['x', '-'], pattern_shape_map={'turnover':'x', 'new_sales':'-'})
                fig = px.line(sales_and_turnover_by_scen_by_economy, x='Date', y='Value', color='Drive', title=title, color_discrete_map=colors_dict, line_dash='Measure')
                
            elif transport_type == 'freight':
                sales_and_turnover_by_scen_by_economy = sales_and_turnover_by_scen_by_economy.loc[sales_and_turnover_by_scen_by_economy['Transport Type']==transport_type].copy()
                title='Sales and turnover by drive - {}'.format(transport_type)
                # fig = px.bar(sales_and_turnover_by_scen_by_economy, x='Date', y='Value', color='Measure', title=title, color_discrete_map=colors_dict, barmode='stack')
                fig = px.line(sales_and_turnover_by_scen_by_economy, x='Date', y='Value', color='Drive', title=title, color_discrete_map=colors_dict, line_dash='Measure')
            elif transport_type == 'all':
                #sum uo so 2w for each transport type are combined:
                sales_and_turnover_by_scen_by_economy = sales_and_turnover_by_scen_by_economy.groupby(['Economy', 'Date', 'Drive', 'Scenario','Measure']).sum().reset_index()
                title='Sales and turnover of vehicles'
                # fig = px.bar(sales_and_turnover_by_scen_by_economy, x='Date', y='Value', color='Measure', title=title, color_discrete_map=colors_dict, barmode ='stack')
                fig = px.line(sales_and_turnover_by_scen_by_economy, x='Date', y='Value', color='Drive', title=title, color_discrete_map=colors_dict, line_dash='Measure')                
                
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario][f'sales_and_turnover_lines_{transport_type}'] = [fig, title, PLOTTED]
            
            if WRITE_HTML:
                filename = 'individual_graphs', f'sales_and_turnover_lines_{transport_type}_{scenario}_{economy}.html'
                write_graph_to_html(config, filename=filename, graph_type='line', plot_data=sales_and_turnover_by_scen_by_economy, economy=economy, x='Date', y='Value', color='Drive', title=title, y_axes_title='Value', legend_title='Drive', font_size=30, colors_dict=colors_dict)
                
    
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(sales_and_turnover_by_scen_by_economy['Drive'].unique().tolist())
    return fig_dict, color_preparation_list
    

def plot_turnover_rate_age_curve(config, ECONOMY_IDs, model_output_detailed_df, fig_dict, colors_dict, WRITE_HTML=True):
    PLOTTED=True
    #using the inputs for midpoint and steepness, plot the curve for turnover rate at each age, with the average age of the fleet in hte first year of the model as a vertical line, and the median age during the whole model as a vertical line.
    #Turnover_rate_midpoint is in detailed
    #steepness is currently in the parameters.yml file
    #load the parameters from the config file
    turnover_rate_parameters_dict = yaml.load(open(os.path.join(config.root_dir, 'config', 'parameters.yml')), Loader=yaml.FullLoader)['turnover_rate_parameters_dict']
    turnover_rate_steepness = turnover_rate_parameters_dict['turnover_rate_steepness']
    turnover_rate_max_value = turnover_rate_parameters_dict['turnover_rate_max_value']
    turnover_rate_midpoint = turnover_rate_parameters_dict['turnover_rate_midpoint']
    turnover_rate_steepness_non_road = turnover_rate_parameters_dict['turnover_rate_steepness_non_road']
    turnover_rate_max_value_non_road = turnover_rate_parameters_dict['turnover_rate_max_value_non_road']
    turnover_rate_midpoint_non_road = turnover_rate_parameters_dict['turnover_rate_midpoint_non_road']
    model_output_detailed = model_output_detailed_df[['Economy', 'Date', 'Scenario', 'Average_age']].copy()
    
    #now loop thorugh scenario and economy so we can set the turnover rate modpoint for each economy and scneario unqiuely, and then plot the turnover rate curve, with the median age of the fleet in first year and the median age of the fleet for all years:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        for economy in ECONOMY_IDs:
                
            #APPLY TURNOVER_RATE_MIDPOINT_MULT_ADJUSTMENT_ROAD_TARGET OR TURNOVER_RATE_MIDPOINT_MULT_ADJUSTMENT_ROAD_REFERENCE TO THE TURNOVER_RATE_MIDPOINT
            #load the parameters from the config file
            if scenario == 'Reference':
                turnover_rate_midpoint_mult_adjustment_road = yaml.load(open(os.path.join(config.root_dir, 'config', 'parameters.yml')), Loader=yaml.FullLoader)['TURNOVER_RATE_MIDPOINT_MULT_ADJUSTMENT_ROAD_REFERENCE']
            elif scenario == 'Target':
                turnover_rate_midpoint_mult_adjustment_road = yaml.load(open(os.path.join(config.root_dir, 'config', 'parameters.yml')), Loader=yaml.FullLoader)['TURNOVER_RATE_MIDPOINT_MULT_ADJUSTMENT_ROAD_TARGET']
            else:
                raise ValueError('Scenario not recognised')
            #extract the value for the economy, if it exists
            if economy in turnover_rate_midpoint_mult_adjustment_road.keys():
                turnover_rate_midpoint_mult_adjustment_road = turnover_rate_midpoint_mult_adjustment_road[economy]
            else:
                turnover_rate_midpoint_mult_adjustment_road = 1
            
            economy_scenario_specific_midpoint = turnover_rate_midpoint * turnover_rate_midpoint_mult_adjustment_road
            #this is the function for calculating the turnover rate, where k is steepness 
            def calculate_turnover_rate(config, df, k, L, x0):
                # df['Turnover_rate'] = L / (1 + np.exp(-k * (df['Average_age'] - df['Turnover_rate_midpoint'])))
                df['Turnover_rate'] = L / (1 + np.exp(-k * (df['Average_age'] - x0)))
                df['Turnover_rate'].fillna(0, inplace=True)
                return df
            
            #so input a series of ages and the mean midpoint and get a series of turnover rates out. then plot it as a line plot. then we can plot the median age of the fleet in first year as a vertical line, and the median age of the fleet for all years as a vertical line. since we have to do this in the dashboard we will just do it using the average midpoint for all vehicles.
            turnover_rate_curve = pd.DataFrame({'Average_age':np.arange(0, 100, 0.5), 'key':1})
            # join it to the df every economy and scenario
            a = model_output_detailed[['Economy', 'Scenario',]].drop_duplicates()
            a['key'] = 1
            turnover_rate_curve = pd.merge(a, turnover_rate_curve, on='key', how='outer').drop('key', axis=1)
            turnover_rate_curve_non_road = turnover_rate_curve.copy()
            turnover_rate_curve = calculate_turnover_rate(config, turnover_rate_curve, turnover_rate_steepness, turnover_rate_max_value, economy_scenario_specific_midpoint)
            turnover_rate_curve_non_road = calculate_turnover_rate(config, turnover_rate_curve_non_road, turnover_rate_steepness_non_road, turnover_rate_max_value_non_road, turnover_rate_midpoint_non_road)
            
            #calc median age of fleet in first year:
            median_age_fleet_first_year = model_output_detailed.loc[model_output_detailed['Date']==model_output_detailed['Date'].min()].groupby(['Economy', 'Scenario'])['Average_age'].median().reset_index()
            median_age_all_years = model_output_detailed.groupby(['Economy', 'Scenario'])['Average_age'].median().reset_index()
            
            #create cols to id the data
            turnover_rate_curve['Measure'] = 'Road'
            turnover_rate_curve_non_road['Measure'] = 'Non-road'
            median_age_fleet_first_year['Measure'] = 'Median_age_fleet_first_year'
            median_age_all_years['Measure'] = 'Median_age_all_years'
            
            #concat medians
            median_ages = pd.concat([median_age_fleet_first_year, median_age_all_years])
            turnover_rate_curve = pd.concat([turnover_rate_curve, turnover_rate_curve_non_road])
                
            #####################
            
            #filter to economy and scenario
            turnover_rate_curve_economy_scen = turnover_rate_curve.loc[(turnover_rate_curve['Economy']==economy) & (turnover_rate_curve['Scenario']==scenario)].copy()
            
            
            median_age_fleet_first_year_economy_scen = median_age_fleet_first_year.loc[(median_age_fleet_first_year['Economy']==economy) & (median_age_fleet_first_year['Scenario']==scenario)].copy()
            median_age_all_years_economy_scen = median_age_all_years.loc[(median_age_all_years['Economy']==economy) & (median_age_all_years['Scenario']==scenario)].copy()
            
            #now plot
            title='Turnover rate curve'
            fig = px.line(turnover_rate_curve_economy_scen, x='Average_age', y='Turnover_rate', title=title, color_discrete_map=colors_dict, color='Measure')
            
            #below difnt work anyway
            # #add median age of fleet in first year
            # fig.add_vline(x=median_age_fleet_first_year_economy_scen['Average_age'].values[0], line_dash='dash', line_color='black', annotation_text='Median age of fleet in first year')
            
            # #add median age of fleet in all years
            # fig.add_vline(x=median_age_all_years_economy_scen['Average_age'].values[0], line_dash='dash', line_color='black', annotation_text='Median age of fleet in all years')
            
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario][f'turnover_rate_age_curve'] = [fig, title, PLOTTED]
            
            if WRITE_HTML:
                filename = f'turnover_rate_age_curve_{scenario}_{economy}.html'
                write_graph_to_html(config, filename=filename, graph_type='line', plot_data=turnover_rate_curve_economy_scen, economy=economy, x='Average_age', y='Turnover_rate', color='Measure', title=title, y_axes_title='Turnover Rate', legend_title='Measure', font_size=30, colors_dict=colors_dict)
                
    return fig_dict

def plot_mileage_timeseries(config, ECONOMY_IDs, model_output_detailed, fig_dict, color_preparation_list, colors_dict, transport_type, WRITE_HTML=True):
    PLOTTED=True
 
    #to help with checking that the data is realistic, plot growth in energy efficiency here:
    mileage = model_output_detailed.copy()
    
    mileage = mileage.loc[mileage['Medium']=='road']
    if transport_type == 'passenger':
        mileage = mileage.loc[mileage['Transport Type']=='passenger']
    elif transport_type == 'freight':
        mileage = mileage.loc[mileage['Transport Type']=='freight']
        
    #calc weighted mean of mileage so the 2020 mmielage adjustment isnt confusing
    #to help with the weighted mean we need to drop rows where stocks are 0 or na  (as ther mileage is still >1 as it is a factor)
    mileage = mileage.loc[(mileage['Stocks']>0) & (mileage['Stocks'].notna())].copy()
    mileage['Mileage'] = mileage['Mileage'] * mileage['Stocks']
    mileage = mileage[['Date', 'Economy','Transport Type', 'Vehicle Type', 'Scenario','Mileage', 'Stocks']].groupby(['Date','Economy','Scenario','Transport Type', 'Vehicle Type']).sum().reset_index()
    mileage['Mileage'] = mileage['Mileage'] / mileage['Stocks']

    #add units (by setting measure to Freight_tonne_km haha)
    mileage['Measure'] = 'Mileage'
    
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        mileage_by_scen = mileage.loc[(mileage['Scenario']==scenario)].copy()
        

        for economy in ECONOMY_IDs:
            #filter to economy
            mileage_by_scen_by_economy = mileage_by_scen.loc[mileage_by_scen['Economy']==economy].copy()

            #now plot
            title='Mileage by vehicle type (Thousand km)'
            fig = px.line(mileage_by_scen_by_economy, x='Date', y='Mileage', color='Vehicle Type', title=title, color_discrete_map=colors_dict)

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario][f'mileage_timeseries_{transport_type}'] = [fig, title, PLOTTED]
            
            if WRITE_HTML:
                filename = f'mileage_timeseries_{transport_type}_{scenario}_{economy}.html'
                write_graph_to_html(config, filename=filename, graph_type='line', plot_data=mileage_by_scen_by_economy, economy=economy, x='Date', y='Mileage', color='Vehicle Type', title=title, y_axes_title='Mileage (Thousand km)', legend_title='Vehicle Type', font_size=30, colors_dict=colors_dict)
    
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(mileage_by_scen_by_economy['Vehicle Type'].unique().tolist())
    
    return fig_dict, color_preparation_list

def plot_mileage_strip(config, ECONOMY_IDs, model_output_detailed, fig_dict, color_preparation_list, colors_dict, WRITE_HTML=True):
    PLOTTED=True
    #to help with checking that the data is realistic, plot energy efficiency here:
    
    mileage = model_output_detailed.copy()
    mileage = mileage.loc[mileage['Medium']=='road']
    
    #calc mean and, importantly, remove date, scenario
    mileage = mileage[['Economy', 'Vehicle Type', 'Drive', 'Scenario','Mileage']].groupby(['Economy', 'Vehicle Type','Scenario', 'Drive']).mean().reset_index()

    # #simplfiy drive type using remap_drive_types
    # fkm = remap_drive_types(config, fkm, value_col='freight_tonne_km', new_index_cols = ['Economy', 'Date', 'Scenario','Drive'])
    
    #add units (by setting measure to Freight_tonne_km haha)
    mileage['Measure'] = 'Mileage'
    #add units
    mileage['Unit'] = mileage['Measure'].map(config.measure_to_unit_concordance_dict)
    
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        mileage_by_scen = mileage.loc[(mileage['Scenario']==scenario)].copy()

        for economy in ECONOMY_IDs:
            #filter to economy
            mileage_by_scen_by_economy = mileage_by_scen.loc[mileage_by_scen['Economy']==economy].copy()

            #now plot
            
            #add fig to dictionary for scenario and economy:
            title='Mileage by vehicle type (Thousand km)'
            fig = px.strip(mileage_by_scen_by_economy, x='Vehicle Type', y='Mileage', color='Drive', title=title, color_discrete_map=colors_dict)
            #add fig to dictionary for scenario and economy:
            
            fig_dict[economy][scenario]['mileage_strip'] = [fig, title, PLOTTED]
            
            if WRITE_HTML:
                filename =   f'mileage_strip_{scenario}_{economy}.html'
                write_graph_to_html(config, filename=filename, graph_type='strip', plot_data=mileage_by_scen_by_economy, economy=economy, x='Vehicle Type', y='Mileage', color='Drive', title=title, y_axes_title='Mileage (Thousand km)', legend_title='Drive', font_size=30, colors_dict=colors_dict)

            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(mileage_by_scen_by_economy['Drive'].unique().tolist())
    return fig_dict, color_preparation_list

def compare_8th_and_9th_stocks_sales(config, ECONOMY_IDs, data_8th, model_output_detailed, fig_dict, color_preparation_list, colors_dict, measure, WRITE_HTML=True):
    """Compare 8th and 9th stocks and sales by transport type and drive type.

    Args:
        ECONOMY_IDs (list): list of economies
        data_8th (dataframe): 8th data
        model_output_detailed (dataframe): 9th data
        fig_dict (dict): dictionary of figures
        color_preparation_list (list): list of colors
        colors_dict (dict): dictionary of colors
        measure (str): stocks_share, sales_share, stocks, sales

    Returns:
        dict: dictionary of figures
    """
    
    PLOTTED=True
    #grab road only
    stocks_8th = data_8th.loc[data_8th['Medium']=='road'].copy()
    stocks_9th = model_output_detailed.loc[model_output_detailed['Medium']=='road'].copy()
    
    index_cols = ['Economy', 'Date', 'Scenario','Transport Type', 'Vehicle Type', 'Drive']
    
    #calcualte average ev shares for passenger and freight for 8th and 9th, then plot them on a line chart to compare how they ahve changed. 
    # stocks_8th = data_8th['Stocks'].copy()
    stocks_8th = stocks_8th[index_cols +['Stocks']].copy()
    stocks_9th = stocks_9th[index_cols +['Stocks', 'Turnover_rate']].copy()
    
    #shift turnover back by one year so we can calculate the turnover for the previous year, usign the year afters turnover rate (this is jsut because of hwo the data is structured)
    index_cols_no_date = index_cols.copy()
    index_cols_no_date.remove('Date')
    stocks_9th['Turnover_rate'] = stocks_9th.groupby(index_cols_no_date)['Turnover_rate'].shift(-1)
    #calcaulte turnover for stocks 9th
    stocks_9th['Turnover'] = stocks_9th['Stocks'] * stocks_9th['Turnover_rate']
    #set turnover to 0.03 for 8th, and calacualte turnover:
    stocks_8th['Turnover'] = stocks_8th['Stocks'] * 0.03#PLEASE NOTE, THIS ISNT REALLY SUITABLE AS IT IS OBVIOUSLY THE WRONG TURNOVER RATE AND RESULTS IN WEIRD RESUTLS. SO ANYTHIGN RELYING ON THSI SHOULD BE EXCLUDED UNITL WE KNWO WHAT THE TURNVOER RATE USED WAS.
    
    #make stocks 9th tall while we remap drive types
    stocks_9th = pd.melt(stocks_9th, id_vars=index_cols, value_vars=['Stocks', 'Turnover'], var_name='Measure', value_name='Value')
    stocks_8th = pd.melt(stocks_8th, id_vars=index_cols, value_vars=['Stocks', 'Turnover'], var_name='Measure', value_name='Value')
    
    index_cols = ['Economy', 'Date', 'Scenario','Drive']
    index_cols_no_drive = ['Economy', 'Date', 'Scenario']
    index_cols_no_date = ['Economy', 'Scenario','Drive']
    #remap drive types to simplified:
    stocks_9th = remap_drive_types(config, stocks_9th, value_col='Value', new_index_cols = index_cols+['Measure'], drive_type_mapping_set='simplified', include_non_road=False)
    stocks_8th = remap_drive_types(config, stocks_8th, value_col='Value', new_index_cols = index_cols+['Measure'], drive_type_mapping_set='simplified', include_non_road=False)
    
    #pivot again
    stocks_9th = stocks_9th.pivot(index=index_cols, columns='Measure', values='Value').reset_index()
    stocks_8th = stocks_8th.pivot(index=index_cols, columns='Measure', values='Value').reset_index()   
    #calculate sales. First calcualte stocks after turnover by subtracting turnover from stocks. then calcalte sales by subtracting stocks after turnover from  stocks after turnover  from previous year:
    stocks_8th['stocks_after_turnover'] = stocks_8th['Stocks'] - stocks_8th['Turnover']
    stocks_9th['stocks_after_turnover'] = stocks_9th['Stocks'] - stocks_9th['Turnover'] 
    
    #sales is the stocks before turnover in this year, minus the stocks after turnover in the previous year
    stocks_8th['previous_year_stocks_after_turnover'] = stocks_8th.groupby(index_cols_no_date)['stocks_after_turnover'].shift(1)
    stocks_8th['sales'] = stocks_8th['Stocks'] - stocks_8th['previous_year_stocks_after_turnover']
    stocks_9th['previous_year_stocks_after_turnover'] = stocks_9th.groupby(index_cols_no_date)['stocks_after_turnover'].shift(1)
    stocks_9th['sales'] = stocks_9th['Stocks'] - stocks_9th['previous_year_stocks_after_turnover']
    
    #calcaulte sales share by transprot type on the drive type
    stocks_8th['sales_share'] = stocks_8th['sales'] / stocks_8th.groupby(index_cols_no_drive)['sales'].transform('sum')
    stocks_9th['sales_share'] = stocks_9th['sales'] / stocks_9th.groupby(index_cols_no_drive)['sales'].transform('sum')
    
    #and clacualte stocks share
    stocks_8th['stocks_share'] = stocks_8th['Stocks'] / stocks_8th.groupby(index_cols_no_drive)['Stocks'].transform('sum')
    stocks_9th['stocks_share'] = stocks_9th['Stocks'] / stocks_9th.groupby(index_cols_no_drive)['Stocks'].transform('sum')
    
    #since its pretty difficult to compare slaes shares because we dont know the 8th sales shares, lets just observe the cahnge in stocks per year for each drive type:
    stocks_8th['last_year_stocks'] = stocks_8th.groupby(index_cols_no_date)['Stocks'].shift(1)
    stocks_9th['last_year_stocks'] = stocks_9th.groupby(index_cols_no_date)['Stocks'].shift(1)
    stocks_8th['change_in_stocks'] = stocks_8th['Stocks'] - stocks_8th['last_year_stocks']
    stocks_9th['change_in_stocks'] = stocks_9th['Stocks'] - stocks_9th['last_year_stocks']
    
    #melt the data so we ahve all measures in one column
    stocks_8th_tall = pd.melt(stocks_8th, id_vars=index_cols, value_vars=['sales_share', 'stocks_share','sales', 'Stocks','Turnover','change_in_stocks'], var_name='Measure', value_name='Value')
    stocks_9th_tall = pd.melt(stocks_9th, id_vars=index_cols, value_vars=['sales_share', 'stocks_share','sales', 'Stocks','Turnover','change_in_stocks'], var_name='Measure', value_name='Value')
        
    #craete cols which inidcate dataset
    stocks_8th_tall['Dataset'] = '8th'
    stocks_9th_tall['Dataset'] = '9th'
    #concat
    stocks = pd.concat([stocks_8th_tall, stocks_9th_tall])
    
    #now we can plot it all. since the values ar eon different scales and we can plot on both y axis we will need to make sure to only plot simiilar vlaues. so group like so:
    #shares: stocks share and sales share
    #values: stocks and sales
    
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        for economy in ECONOMY_IDs:
            #now plot
            if measure == 'stocks_share':
                stocks_shares_economy_scen = stocks.loc[(stocks['Economy']==economy) & (stocks['Scenario']==scenario)].copy()
                stocks_shares_economy_scen = stocks_shares_economy_scen.loc[stocks_shares_economy_scen['Measure']=='stocks_share'].copy()
                title='EV stocks shares by drive type (8th vs 9th)'
                fig = px.line(stocks_shares_economy_scen, x='Date', y='Value', color='Drive', line_dash='Dataset', title=title, color_discrete_map=colors_dict)
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][f'8th_9th_stocks_{measure}'] = [fig, title, PLOTTED]
                
            elif measure == 'sales_share':
                sales_shares_economy_scen = stocks.loc[(stocks['Economy']==economy) & (stocks['Scenario']==scenario)].copy()
                sales_shares_economy_scen = sales_shares_economy_scen.loc[sales_shares_economy_scen['Measure']=='sales_share'].copy()
                #jsut for this we will ahve to drop sales shares in 2020, 2021 for 8th since it goes really extreme. 
                sales_shares_economy_scen = sales_shares_economy_scen.loc[~((sales_shares_economy_scen['Dataset']=='8th') & (sales_shares_economy_scen['Date']<2022))].copy()
                
                title='EV sales shares by drive type (8th vs 9th)'
                fig = px.line(sales_shares_economy_scen, x='Date', y='Value', color='Drive', line_dash='Dataset', title=title, color_discrete_map=colors_dict)
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][f'8th_9th_stocks_{measure}'] = [fig, title, PLOTTED]
            
            elif measure == 'stocks':
                stocks_economy_scen = stocks.loc[(stocks['Economy']==economy) & (stocks['Scenario']==scenario)].copy()
                stocks_economy_scen = stocks_economy_scen.loc[stocks_economy_scen['Measure']=='Stocks'].copy()
                title='EV stocks by drive type (8th vs 9th)'
                fig = px.line(stocks_economy_scen, x='Date', y='Value', color='Drive', line_dash='Dataset', title=title, color_discrete_map=colors_dict)
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][f'8th_9th_stocks_{measure}'] = [fig, title, PLOTTED]
                
            elif measure == 'turnover':
                stocks_economy_scen = stocks.loc[(stocks['Economy']==economy) & (stocks['Scenario']==scenario)].copy()
                stocks_economy_scen = stocks_economy_scen.loc[stocks_economy_scen['Measure']=='Turnover'].copy()
                title='EV turnover by drive type (8th vs 9th)'
                fig = px.line(stocks_economy_scen, x='Date', y='Value', color='Drive', line_dash='Dataset', title=title, color_discrete_map=colors_dict)
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][f'8th_9th_stocks_{measure}'] = [fig, title, PLOTTED]
                
            elif measure == 'sales':
                sales_economy_scen = stocks.loc[(stocks['Economy']==economy) & (stocks['Scenario']==scenario)].copy()
                sales_economy_scen = sales_economy_scen.loc[sales_economy_scen['Measure']=='sales'].copy()
                title='EV sales by drive type (8th vs 9th)'
                fig = px.line(sales_economy_scen, x='Date', y='Value', color='Drive', line_dash='Dataset', title=title, color_discrete_map=colors_dict)
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][f'8th_9th_stocks_{measure}'] = [fig, title, PLOTTED]
                
            elif measure == 'change_in_stocks':
                change_in_stocks_economy_scen = stocks.loc[(stocks['Economy']==economy) & (stocks['Scenario']==scenario)].copy()
                change_in_stocks_economy_scen = change_in_stocks_economy_scen.loc[change_in_stocks_economy_scen['Measure']=='change_in_stocks'].copy()
                title='Change in EV stocks by drive type (8th vs 9th)'
                fig = px.line(change_in_stocks_economy_scen, x='Date', y='Value', color='Drive', line_dash='Dataset', title=title, color_discrete_map=colors_dict)
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][f'8th_9th_stocks_{measure}'] = [fig, title, PLOTTED]
                
                if WRITE_HTML:
                    filename = f'8th_vs_9th_stocks_share_{scenario}_{economy}.html'
                    write_graph_to_html(config, filename=filename, graph_type='line', plot_data=stocks_shares_economy_scen, economy=economy, x='Date', y='Value', color='Drive', line_dash='Dataset', title=title, y_axes_title='Stocks Share', legend_title='Drive', font_size=30, colors_dict=colors_dict)
                
       
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(stocks['Drive'].unique().tolist())
    return fig_dict, color_preparation_list

def plot_age_distributions(config, ECONOMY_IDs, model_output_detailed_detailed_non_road_drives, fig_dict, color_preparation_list, colors_dict, medium, BY_DRIVE, BY_VEHICLE_TYPE, WRITE_HTML=True):

    PLOTTED=True
    group_cols = ['Economy', 'Scenario', 'Date']
    
    age_distribution = model_output_detailed_detailed_non_road_drives.copy()
    if medium == 'road':
        age_distribution = age_distribution.loc[age_distribution['Medium']=='road']
    elif medium == 'non_road':
        age_distribution = age_distribution.loc[age_distribution['Medium']!='road']
        #set the vehicle type to the meidum
        age_distribution['Vehicle Type'] = age_distribution['Medium']
    elif medium == 'all':
        #where medium is not road, set vehilce type to nonroad# medium
        age_distribution.loc[age_distribution['Medium']!='road', 'Vehicle Type'] = 'nonroad' #age_distribution.loc[age_distribution['Medium']!='road', 'Medium']
    
    if BY_DRIVE:
        group_cols.append('Drive')
    if BY_VEHICLE_TYPE:
        group_cols.append('Vehicle Type')
    #if not by drive or vehicle type, then we will do , 'Medium', 'Transport Type'
    if not BY_DRIVE and not BY_VEHICLE_TYPE:
        group_cols.append('Medium')
        group_cols.append('Transport Type')
    
    
    #grab only data for OUTLOOK_BASE_YEAR, 2040, 2070
    age_distribution = age_distribution.loc[age_distribution['Date'].isin([config.OUTLOOK_BASE_YEAR, 2040, 2070])].copy()
    
    #combine the age distributions
    age_distribution_copy = age_distribution[group_cols+['Age_distribution']].copy()
    age_distribution = age_distribution[group_cols].drop_duplicates()

    age_distribution = age_distribution_copy.groupby(group_cols)['Age_distribution'].agg(road_model_functions.combine_age_distributions).reset_index()
    
    
    # age_distribution = age_distribution.merge(age_distribution_copy, on=group_cols, how='left')
    
    #now we need to convert the age distribution from a list of values to a dataframe of values where the index is the age and the value is the share of vehicles of that age.
    #CAHTGPT PLEASE WORK HERE
    
    # Assuming Age_distribution is a list or string that can be converted to a list
    age_dfs = []
    for index, row in age_distribution.iterrows():
        age_list = row['Age_distribution']
        if str(age_list) == 'nan':
            age_list='0'
        if isinstance(age_list, str):
            age_list = [float(x) for x in age_list.split(",")]
        else:
            breakpoint()#not expecting this
        
        age_df = pd.DataFrame(age_list, columns=['number_of_vehicles'])
        age_df['Age'] = age_df.index
        age_df['key'] = index  # to keep track of which row it originally belonged to
        age_dfs.append(age_df)
    
    combined_age_df = pd.concat(age_dfs, ignore_index=True)
    #join back to age_distribution on key
    age_distribution = age_distribution.merge(combined_age_df, left_index=True, right_on='key', how='left')
    
    #drop key
    age_distribution = age_distribution.drop(columns=['key'])
    #find the share of vehicles for each age and group
    age_distribution['Age_distribution'] = age_distribution['number_of_vehicles'] / age_distribution.groupby(group_cols)['number_of_vehicles'].transform('sum')
    
       
    #add units (by setting measure to Freight_tonne_km haha)
    age_distribution['Measure'] = 'Age_distribution'
    #add units
    age_distribution['Unit'] = age_distribution['Age_distribution'].map(config.measure_to_unit_concordance_dict)
    
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        age_distribution_by_scen = age_distribution.loc[(age_distribution['Scenario']==scenario)].copy()

        for economy in ECONOMY_IDs:
            #filter to economy
            age_distribution_by_scen_by_economy = age_distribution_by_scen.loc[age_distribution_by_scen['Economy']==economy].copy()

            #now plot
            
            #add fig to dictionary for scenario and economy:
            title=f'Age distributions for {medium}'
            if BY_DRIVE and BY_VEHICLE_TYPE:
                #add date to the color key so we can differentiate between the different dates
                age_distribution_by_scen_by_economy['Drive'] = age_distribution_by_scen_by_economy['Drive'] + age_distribution_by_scen_by_economy['Date'].astype(str)
                fig = px.line(age_distribution_by_scen_by_economy, x='Age', y='Age_distribution', color='Drive', title=title, color_discrete_map=colors_dict, line_dash='Vehicle Type')
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][f'age_distribution_{medium}_by_vehicle_type_by_drive'] = [fig, title, PLOTTED]
            elif BY_DRIVE:
                #add date to the color key so we can differentiate between the different dates
                age_distribution_by_scen_by_economy['Drive'] = age_distribution_by_scen_by_economy['Drive'] + age_distribution_by_scen_by_economy['Date'].astype(str)
                fig = px.line(age_distribution_by_scen_by_economy, x='Age', y='Age_distribution', color='Drive', title=title, color_discrete_map=colors_dict)
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][f'age_distribution_{medium}_by_drive'] = [fig, title, PLOTTED]
            elif BY_VEHICLE_TYPE:
                #add date to the color key so we can differentiate between the different dates
                age_distribution_by_scen_by_economy['Vehicle Type'] = age_distribution_by_scen_by_economy['Vehicle Type'] + age_distribution_by_scen_by_economy['Date'].astype(str)
                fig = px.line(age_distribution_by_scen_by_economy, x='Age', y='Age_distribution', color='Vehicle Type', title=title, color_discrete_map=colors_dict)
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][f'age_distribution_{medium}_by_vehicle_type'] = [fig, title, PLOTTED]
            else:
                #add date to the color key so we can differentiate between the different dates
                age_distribution_by_scen_by_economy['Medium'] = age_distribution_by_scen_by_economy['Medium'] + age_distribution_by_scen_by_economy['Date'].astype(str)
                fig = px.line(age_distribution_by_scen_by_economy, x='Age', y='Age_distribution', color='Medium', title=title, color_discrete_map=colors_dict, line_dash='Transport Type')
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario][f'age_distribution_{medium}'] = [fig, title, PLOTTED]
                
            if WRITE_HTML:
                filename = f'age_distribution_{medium}_{scenario}_{economy}.html'
                write_graph_to_html(config, filename=filename, graph_type='line', plot_data=age_distribution_by_scen_by_economy, economy=economy, x='Age', y='Age_distribution', color='Drive' if BY_DRIVE else 'Vehicle Type' if BY_VEHICLE_TYPE else 'Medium', title=title, y_axes_title='Age Distribution', legend_title='Drive' if BY_DRIVE else 'Vehicle Type' if BY_VEHICLE_TYPE else 'Medium', font_size=30, colors_dict=colors_dict)
    
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    if BY_DRIVE:
        color_preparation_list.append(age_distribution_by_scen_by_economy['Drive'].unique().tolist())
    elif BY_VEHICLE_TYPE:
        color_preparation_list.append(age_distribution_by_scen_by_economy['Vehicle Type'].unique().tolist())
        
    return fig_dict, color_preparation_list

    
def plot_intensity_timeseries_INTENSITY_ANALYSIS(config, ECONOMY_IDs, model_output_detailed, fig_dict, DROP_NON_ROAD_TRANSPORT, color_preparation_list, colors_dict, transport_type, WRITE_HTML=True):
    PLOTTED=True

    #to help with checking that the data is realistic, plot growth in energy efficiency here:
    energy_eff = model_output_detailed.copy()
    if DROP_NON_ROAD_TRANSPORT:
        energy_eff = energy_eff.loc[energy_eff['Medium']=='road']
    else:
        #set vehicle type to medium so we can plot strip plot by vehicle type: 
        energy_eff.loc[energy_eff['Medium'] != 'road', 'Vehicle Type'] = energy_eff.loc[energy_eff['Medium'] != 'road', 'Medium']
    if transport_type == 'passenger':
        energy_eff = energy_eff.loc[energy_eff['Transport Type']=='passenger']
    elif transport_type == 'freight':
        energy_eff = energy_eff.loc[energy_eff['Transport Type']=='freight']
    
    #convertefficiency to intensity by 1/efficiency
    energy_eff['Intensity'] = 1 / energy_eff['Efficiency']
    #make 2020 = 2021 since 2020 is a bit weird
    if config.OUTLOOK_BASE_YEAR == 2020:
        energy_eff_2020 = energy_eff.loc[energy_eff['Date']==2021].copy()
        energy_eff_2020['Date'] = 2020
        energy_eff = energy_eff.loc[energy_eff['Date']!=2020].copy()
        energy_eff = pd.concat([energy_eff, energy_eff_2020])
    
    # #map vehicle types to simplfiy
    # remap_vehicle_types(config, df, value_col='Value', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'],vehicle_type_mapping_set='simplified', include_non_road=True, aggregation_type=('sum',))
    #filter for only cars, to make it easier to see
    energy_eff = energy_eff.loc[energy_eff['Vehicle Type'].isin(['car'])].copy()
    
    #simplify drive types
    energy_eff = remap_drive_types(config, energy_eff, value_col='Intensity', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive'], drive_type_mapping_set='extra_simplified', aggregation_type=('weighted_average', 'Activity'), include_non_road=True)
    
    #add units (by setting measure to Freight_tonne_km haha)
    energy_eff['Measure'] = 'Intensity'
    
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        energy_eff_by_scen = energy_eff.loc[(energy_eff['Scenario']==scenario)].copy()
        
        #DROP ANY groups WHERE INTENSITY IS 0
        energy_eff_by_scen = energy_eff_by_scen.groupby(['Drive']).filter(lambda x: not all(x['Intensity'] == 0))

        for economy in ECONOMY_IDs:
            #filter to economy
            energy_eff_by_scen_by_economy = energy_eff_by_scen.loc[energy_eff_by_scen['Economy']==economy].copy()

            if transport_type == 'all':
                title='Energy Intensity by drive type (Pj per Billion-km)'
            elif transport_type == 'passenger' or transport_type == 'freight':
                title='Energy Intensity by drive type - {} (Pj per Billion-km)'.format(transport_type)
            fig = px.line(energy_eff_by_scen_by_economy, x='Date', y='Intensity', color='Drive', title=title, color_discrete_map=colors_dict)#, line_dash='Vehicle Type')

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario][f'INTENSITY_ANALYSIS_timeseries_{transport_type}'] = [fig, title, PLOTTED]
            
            if WRITE_HTML:
                filename =  f'INTENSITY_ANALYSIS_timeseries_{transport_type}_{scenario}_{economy}.html'
                write_graph_to_html(config, filename=filename, graph_type='line', plot_data=energy_eff_by_scen_by_economy, economy=economy, x='Date', y='Intensity', color='Drive', title=title, y_axes_title='Intensity (Pj per Billion-km)', legend_title='Drive', font_size=30, colors_dict=colors_dict)
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(energy_eff_by_scen_by_economy['Drive'].unique().tolist())
    
    return fig_dict, color_preparation_list

def line_energy_use_by_transport_type(config, ECONOMY_IDs, model_output_detailed, fig_dict, medium, color_preparation_list, colors_dict, transport_type, WRITE_HTML=True):
    """use transport_type and medium to define if we have a graph for:
    Comparison between freight and passenger energy consumption
    Share of different methods (road, flight, rail, etc) in passenger transport
    Share of different methods (road, flight, rail, etc) in freight transport

    #note that if 'sum' is selected for transport_type or medium then we set all vlaues in that transport type or medium to 'all'.
    Args:
        ECONOMY_IDs (_type_): _description_
        model_output_detailed (_type_): _description_
        fig_dict (_type_): _description_
        medium (_type_): 'road', 'non_road', 'all', 'sum'
        color_preparation_list (_type_): _description_
        colors_dict (_type_): _description_
        transport_type (_type_): passenger, freight, all, 'sum'
    """
    
    PLOTTED=True

    #to help with checking that the data is realistic, plot energy efficiency here:
    energy_use = model_output_detailed.copy()     

    if medium == 'road':
        energy_use = energy_use.loc[energy_use['Medium']=='road']
    elif medium == 'non_road':
        energy_use = energy_use.loc[energy_use['Medium']!='road']
    elif medium == 'sum':
        energy_use['Medium'] = 'all'
    if transport_type == 'passenger':
        energy_use = energy_use.loc[energy_use['Transport Type']=='passenger']
    elif transport_type == 'freight':
        energy_use = energy_use.loc[energy_use['Transport Type']=='freight']
    elif transport_type == 'sum':
        energy_use['Transport Type'] = 'all'
        
    energy_use['Type'] = energy_use['Medium'] + ' ' + energy_use['Transport Type']
    #add units (by setting measure to Freight_tonne_km haha)
    energy_use['Measure'] = 'Energy'
    #add units
    energy_use['Unit'] = energy_use['Measure'].map(config.measure_to_unit_concordance_dict)
    
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        energy_use_by_scen = energy_use.loc[(energy_use['Scenario']==scenario)].copy()

        for economy in ECONOMY_IDs:
            #filter to economy
            energy_use_by_scen_by_economy = energy_use_by_scen.loc[energy_use_by_scen['Economy']==economy].copy()

            #now plot
            energy_use_by_scen_by_economy = energy_use_by_scen_by_economy.groupby(['Date', 'Type'])['Energy'].sum().reset_index()
            
            title_dict = {'all_all': 'Energy use by medium (Pj)',
                          'all_passenger': 'Passenger energy use by medium (Pj)',
                          'all_freight': 'Freight energy use by medium (Pj)',
                          'sum_all': 'Energy use by transport type (Pj)',
                          'sum_passenger': 'Passenger energy use (Pj)',
                          'sum_freight': 'Freight energy use (Pj)',
                          'road_sum': 'Road energy use (Pj)', 
                          'non_road_sum': 'Energy use by non road medium (Pj)',
                          'all_sum': 'Energy use by medium (Pj)',
                          'sum_sum': 'Energy use total (Pj)',
                          'road_all': 'Road energy use by transport type (Pj)',
                          'road_passenger': 'Passenger road energy use (Pj)',
                          'road_freight': 'Freight road energy use (Pj)',
                          'non_road_all': 'Energy use by non road medium (Pj)',
                          'non_road_passenger': 'Passenger energy use by non road medium (Pj)',
                          'non_road_freight': 'Freight energy use by non road medium (Pj)'}            
            
            fig = px.line(energy_use_by_scen_by_economy, x='Date', y='Energy', color='Type', title=title_dict[f'{medium}_{transport_type}'], color_discrete_map=colors_dict)
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario][f'line_energy_use_{medium}_{transport_type}'] = [fig, title_dict[f'{medium}_{transport_type}'], PLOTTED]
            
            # Write the figure to HTML if required
            if WRITE_HTML:
                filename =  f'line_energy_use_{medium}_{transport_type}_{scenario}_{economy}.html'
                write_graph_to_html(config, 
                    filename=filename, 
                    graph_type='line', 
                    plot_data=energy_use_by_scen_by_economy, 
                    economy=economy, 
                    x='Date', 
                    y='Energy', 
                    color='Type', 
                    title=title_dict[f'{medium}_{transport_type}'], 
                    y_axes_title='Energy (Pj)', 
                    legend_title='Type', 
                    font_size=30, 
                    colors_dict=colors_dict
                )
                
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(energy_use_by_scen_by_economy['Type'].unique().tolist())
    return fig_dict, color_preparation_list



def INTENSITY_ANALYSIS_share_of_sum_of_vehicle_types_by_transport_type(config, ECONOMY_IDs, new_sales_shares_all_plot_drive_shares_df, stocks_df, fig_dict, color_preparation_list, colors_dict, share_of_transport_type_type, WRITE_HTML=True, LPV_ONLY=True, SIMPLIFY_DRIVES=True):
    PLOTTED=True
    #i think that maybe stocks % can be higher than sales % here because of turnvoer rates. hard to get it correct right now
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares_df.copy()
    stocks = stocks_df.copy()
    if LPV_ONLY and share_of_transport_type_type == 'passenger':
        new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Vehicle Type'].isin(['car', 'suv', 'lt']))].copy()
        stocks = stocks.loc[(stocks['Vehicle Type'].isin(['car', 'suv', 'lt']))].copy()
    if SIMPLIFY_DRIVES:
        #make phev_d and phev_g into phev
        new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Drive']=='phev_d') |(new_sales_shares_all_plot_drive_shares['Drive']=='phev_g'), 'Drive'] = 'phev'
        
        new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Drive']=='lpg') |(new_sales_shares_all_plot_drive_shares['Drive']=='cng') |(new_sales_shares_all_plot_drive_shares['Drive']=='ice_d') | (new_sales_shares_all_plot_drive_shares['Drive']=='ice_g'), 'Drive'] = 'ice'
        
        #make phev_d and phev_g into phev
        stocks.loc[(stocks['Drive']=='lpg') |(stocks['Drive']=='cng') |(stocks['Drive']=='ice_d') | (stocks['Drive']=='ice_g'), 'Drive'] = 'ice'
        
        stocks.loc[(stocks['Drive']=='phev_d') |(stocks['Drive']=='phev_g'), 'Drive'] = 'phev'

    #sum up sales shares and stocks. useful in case they ahvent quite been summed yet anyways
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares[['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive', 'Value']].groupby(['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive'], group_keys=False).sum().reset_index()
    
    stocks = stocks[['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive','Value']].groupby(['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive'], group_keys=False).sum().reset_index()
                
    if share_of_transport_type_type == 'all':
        new_sales_shares_all_plot_drive_shares['Transport Type'] = 'all'
        stocks['Transport Type'] = 'all'
        
        #If we are setting the transport type to all, we will need to calculate the weighted average sales share for each drive type, since passenger sales are different to freigth sales and we dont want to skew the results. (currently if we average the sales shares for each drive type, we will get a value that is not representative of the actual sales share). For this we will jsut use stocks rather than sales as the weighting factor
        new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares.merge(stocks, on=['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive'], how='left', suffixes=('_sales_share', '_stocks'))
        #now we can calculate the weighted average sales share
        new_sales_shares_all_plot_drive_shares['Weighted_value'] = (new_sales_shares_all_plot_drive_shares['Value_sales_share'] * new_sales_shares_all_plot_drive_shares['Value_stocks'])
        new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares[['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive','Value_stocks', 'Weighted_value']].groupby(['Scenario', 'Economy', 'Date', 'Drive', 'Transport Type'], group_keys=False).sum(numeric_only=True).reset_index()
        new_sales_shares_all_plot_drive_shares['Value'] = new_sales_shares_all_plot_drive_shares['Weighted_value'] / new_sales_shares_all_plot_drive_shares['Value_stocks']
        #since we may be dividing by zero, we will sdet any values that are nan to 0
        new_sales_shares_all_plot_drive_shares['Value'] = new_sales_shares_all_plot_drive_shares['Value'].fillna(0)
        new_sales_shares_all_plot_drive_shares.drop(columns=['Value_stocks', 'Weighted_value'], inplace=True)
    
    if LPV_ONLY or share_of_transport_type_type == 'all' or SIMPLIFY_DRIVES:
        #Since we are dropping soem caterogires we will need to nomralise  sales shares so they add up to 1.
        new_sales_shares_all_plot_drive_shares['Value'] = new_sales_shares_all_plot_drive_shares.groupby(['Scenario', 'Economy', 'Date', 'Transport Type'], group_keys=False)['Value'].transform(lambda x: x/x.sum())
        
    # And then calcualte stocks shares 
    stocks['Value'] = stocks.groupby(['Scenario', 'Economy', 'Date', 'Transport Type'], group_keys=False)['Value'].apply(lambda x: x/x.sum(numeric_only=True))
    
    stocks[' '] = 'Stock share' 
    new_sales_shares_all_plot_drive_shares[' '] = 'Sales share'
        
    for scenario in new_sales_shares_all_plot_drive_shares['Scenario'].unique():
        new_sales_shares_all_plot_drive_shares_scenario = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Scenario']==scenario)]
        stocks_scen = stocks.loc[(stocks['Scenario']==scenario)].copy()
        ###
        
        #then concat the two dataframes
        new_sales_shares_all_plot_drive_shares_scenario = pd.concat([new_sales_shares_all_plot_drive_shares_scenario, stocks_scen])
        
        #rename value to share
        new_sales_shares_all_plot_drive_shares_scenario.rename(columns={'Value':'Share'}, inplace=True)
                
        for economy in ECONOMY_IDs:
            plot_data =  new_sales_shares_all_plot_drive_shares_scenario.loc[(new_sales_shares_all_plot_drive_shares_scenario['Economy']==economy)].copy()
                    
            if share_of_transport_type_type =='passenger':
                #after recalcualting, drop all drives except bev, ice and phev isnce the others are not used in passenger transport (except for a few rural fcev buses and gas cars). This means the mising share is obviously from these types but wont be noticeabnle except under inspection, which is good (we want to be able to notice it under inspection)
                if SIMPLIFY_DRIVES:
                    plot_data = plot_data.loc[(plot_data['Drive']=='bev') | (plot_data['Drive']=='ice') | (plot_data['Drive']=='phev')].copy()
                else:
                    plot_data = plot_data.loc[(plot_data['Drive']=='bev') | (plot_data['Drive']=='ice') | (plot_data['Drive']=='phev_g') | (plot_data['Drive']=='phev_d')].copy()
            
            # Group by 'Drive' and filter out groups where all 'Energy' values are 0
            groups = plot_data.groupby(['Drive', ' '])
            plot_data = groups.filter(lambda x: not all(x['Share'] == 0))
            
            #sort by date col
            plot_data.sort_values(by=['Date'], inplace=True)
            #############
            #now plot
            if share_of_transport_type_type == 'passenger':
                
                title = f'Shares for passenger (%)'
                fig = px.line(plot_data[plot_data['Transport Type']=='passenger'], x='Date', y='Share', color='Drive', title=title, line_dash=' ', color_discrete_map=colors_dict)                
                #prodcue individual graph
                # WRITE_HTML=True
                if WRITE_HTML:   
                    write_graph_to_html(config, filename= f'INTENSITY_ANALYSIS_sales_share_by_transport_type_passenger_{scenario}.html', graph_type='line', economy=economy,plot_data=plot_data[plot_data['Transport Type']=='passenger'], x='Date', y='Share', color='Drive', title=title, font_size=30, line_width=10, colors_dict=colors_dict)
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['INTENSITY_ANALYSIS_sales_share_by_transport_type_passenger'] = [fig, title, PLOTTED]
                #############
            elif share_of_transport_type_type == 'freight':
                title = f'Shares for freight (%)'

                fig = px.line(plot_data[plot_data['Transport Type']=='freight'], x='Date', y='Share', color='Drive', title=title, line_dash=' ', color_discrete_map=colors_dict)             
                #prodcue individual graph
                if WRITE_HTML:  
                    
                    write_graph_to_html(config, filename= f'INTENSITY_ANALYSIS_sales_share_by_transport_type_freight_{scenario}.html', graph_type='line', economy=economy,plot_data=plot_data[plot_data['Transport Type']=='freight'], x='Date', y='Share', color='Drive', title=title, font_size=30, line_width=10, colors_dict=colors_dict)
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['INTENSITY_ANALYSIS_sales_share_by_transport_type_freight'] = [fig, title, PLOTTED]
            elif share_of_transport_type_type == 'all':
                title = f'Sales and Stock share of vehicles ({scenario})'
                #drop data after 2050
                plot_data = plot_data.loc[plot_data['Date']<=2060].copy()
                fig = px.line(plot_data, x='Date', y='Share', color='Drive', title=title, line_dash=' ', color_discrete_map=colors_dict)
                            
                #prodcue individual graph
                if WRITE_HTML:    
                    #make line thicker
                    
                    write_graph_to_html(config, filename= f'INTENSITY_ANALYSIS_sales_share_by_transport_type_all_{scenario}.html', graph_type='line',economy=economy, plot_data=plot_data[plot_data['Transport Type']=='freight'], x='Date', y='Share', color='Drive', title=title, font_size=30, line_width=10, colors_dict=colors_dict)
                    
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['INTENSITY_ANALYSIS_sales_share_by_transport_type_all'] = [fig, title, PLOTTED]
            else:
                raise ValueError('share_of_transport_type_type must be passenger or freight')
            #############

    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(plot_data['Drive'].unique().tolist())
    
    return fig_dict, color_preparation_list

def plot_decrease_in_activity_from_activity_efficiency(config, ECONOMY_IDs, model_output_detailed_df, fig_dict, color_preparation_list, colors_dict, WRITE_HTML=True):
    #grab Activity_efficiency_improvement, activity and activity growth from model_output_detailed. backcalcualte activity if the activity efficiency is 1, by calcualting cumprod of Activity_efficiency_improvement and multiplying by activity. Then plot the activity vs the backcalculated activity for each transpott type
    
    #filter for road only
    model_output_detailed = model_output_detailed_df.copy()
    model_output_detailed = model_output_detailed.loc[model_output_detailed['Medium']=='road'].copy()
    
    #sum up activity by transport type befroe we do anything else
    activity = model_output_detailed.groupby(['Economy', 'Scenario', 'Date', 'Transport Type'])['Activity'].sum().reset_index()
    
    activity_efficiency_improvement = model_output_detailed[['Economy', 'Scenario', 'Date', 'Transport Type','Activity_efficiency_improvement']].drop_duplicates()
    
    #calc cumprod of activity efficiency improvement
    activity_efficiency_improvement['Activity_efficiency_improvement_cumprod'] = activity_efficiency_improvement.groupby(['Economy', 'Scenario', 'Transport Type'])['Activity_efficiency_improvement'].transform(lambda x: x.cumprod())
    
    #merge with activity
    activity_efficiency_improvement = activity_efficiency_improvement.merge(activity, on=['Economy', 'Scenario', 'Date', 'Transport Type'], how='left')
    
    #calc backcalculated activity
    activity_efficiency_improvement['Original_activity'] = (activity_efficiency_improvement['Activity_efficiency_improvement_cumprod'] * activity_efficiency_improvement['Activity'])
    #rename activity so we can melt it
    activity_efficiency_improvement.rename(columns={'Activity':'Improved_activity'}, inplace=True)
    #melt so activity and original activity are in the same column
    activity_efficiency_improvement = activity_efficiency_improvement.melt(id_vars=['Economy', 'Scenario', 'Date', 'Transport Type'], value_vars=['Improved_activity', 'Original_activity'], var_name='Activity_type', value_name='Activity')
    
    #plot the activity diff
    for scenario in activity_efficiency_improvement['Scenario'].unique():
        activity_efficiency_improvement_scenario = activity_efficiency_improvement.loc[(activity_efficiency_improvement['Scenario']==scenario)].copy()
        
        for economy in ECONOMY_IDs:
            activity_efficiency_improvement_scenario_economy = activity_efficiency_improvement_scenario.loc[(activity_efficiency_improvement_scenario['Economy']==economy)].copy()
            
            #plot the data
            title = f'Effect of activity efficiency improvement'
            fig = px.line(activity_efficiency_improvement_scenario_economy, x='Date', y='Activity', color='Transport Type', line_dash='Activity_type', title=title, color_discrete_map=colors_dict)
            
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['decrease_in_activity_from_activity_efficiency'] = [fig, title, True]
            
            if WRITE_HTML:
                write_graph_to_html(config, filename=f'decrease_in_activity_from_activity_efficiency_{scenario}_{economy}.html', graph_type='line', economy=economy,plot_data=activity_efficiency_improvement_scenario_economy, x='Date', y='Activity', color='Transport Type', title=title, font_size=30, line_width=10, colors_dict=colors_dict)
    
    return fig_dict, color_preparation_list

def plot_shifted_activity_from_medium_to_medium(config, ECONOMY_IDs, activity_change_for_plotting_df, fig_dict, color_preparation_list, colors_dict, WRITE_HTML=True):
    # breakpoint()#somethign weird going on for mas?
    #grab Activity_efficiency_improvement, activity and activity growth from model_output_detailed. backcalcualte activity if the activity efficiency is 1, by calcualting cumprod of Activity_efficiency_improvement and multiplying by activity. Then plot the activity vs the backcalculated activity for each transpott type
    activity_change_for_plotting = activity_change_for_plotting_df.copy()
    
    #filter for <=2070
    activity_change_for_plotting = activity_change_for_plotting.loc[activity_change_for_plotting['Date']<=config.GRAPHING_END_YEAR].copy()
    
    activity_change_for_plotting = activity_change_for_plotting[['Date', 'Scenario', 'Economy', 'Transport Type', 'TO_or_FROM', 'Original_activity', 'New_activity', 'To_medium', 'From_medium', 'Very_original_activity']]
    
    #if TO_or_FROM is from then set medium to from_medium, else set medium to to_medium
    activity_change_for_plotting['Medium'] = np.where(activity_change_for_plotting['TO_or_FROM']=='FROM', activity_change_for_plotting['From_medium'], activity_change_for_plotting['To_medium'])
    #set medium_to_medium to activity_change_for_plotting['From_medium'] + '_to_' + activity_change_for_plotting['To_medium'], except if to_medium is na, in which case just set it to from_medium 
    activity_change_for_plotting['medium_to_medium'] = np.where(activity_change_for_plotting['To_medium'].isna(), activity_change_for_plotting['From_medium'], activity_change_for_plotting['From_medium'] + '_to_' + activity_change_for_plotting['To_medium'])
    
    # model_output_detailed = model_output_detailed[config.INDEX_COLS_NO_MEASURE + ['Activity', 'Activity_original']]
    #now melt
    melted_df = activity_change_for_plotting.melt(id_vars=['Date', 'Scenario', 'Economy', 'Transport Type', 'Medium', 'medium_to_medium','TO_or_FROM'], value_vars=['Very_original_activity', 'New_activity'], var_name='Activity_type', value_name='Activity')
    
    #where activity type is Very_original_activity then set medium_to_medium to '' and to_or_from to '' then drop duplicates. this will mean we can only have one Very_original_activity line for each medium, scenario transpot type
    melted_df.loc[melted_df['Activity_type']=='Very_original_activity', 'medium_to_medium'] = ''
    melted_df.loc[melted_df['Activity_type']=='Very_original_activity', 'TO_or_FROM'] = ''
    melted_df = melted_df.drop_duplicates()
    
    #plot the activity diff
    for scenario in melted_df['Scenario'].unique():
        activity_scen = melted_df.loc[(melted_df['Scenario']==scenario)].copy()
                    
        for economy in ECONOMY_IDs:
            activity_econ_scen = activity_scen.loc[(activity_scen['Economy']==economy)].copy()
            
            #add medium to transport type so we can differentiate using the color                        
            if activity_econ_scen.empty:
                PLOTTED=False
            else:
                PLOTTED=True
                
            activity_econ_scen['Transport Type'] = activity_econ_scen['Transport Type'] + ' ' + activity_econ_scen['Medium'] #+ activity_econ_scen['medium_to_medium'] + activity_econ_scen['TO_or_FROM']
            
            # .astype(str).replace('False', '').replace('True', 'GROWTH_RATE_TOO_HIGH')
            #plot the data
            #add text to the hover data so that the user can see what the medium_to_medium and TO_or_FROM are
            #sort by date col
            activity_econ_scen.sort_values(by=['Date'], inplace=True)
            
            title = f'Shifted activity between mediums'
            fig = px.line(activity_econ_scen, x='Date', y='Activity', color='Transport Type', line_dash='Activity_type', title=title, color_discrete_map=colors_dict, hover_data=['medium_to_medium', 'TO_or_FROM'])
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['shifted_activity_from_medium_to_medium'] = [fig, title, PLOTTED]
            if WRITE_HTML:
                write_graph_to_html(config, filename=f'shifted_activity_from_medium_to_medium_{scenario}_{economy}.html', graph_type='line', economy=economy,plot_data=activity_econ_scen, x='Date', y='Activity', color='Transport Type', title=title, font_size=30, line_width=10, colors_dict=colors_dict)
                                
    return fig_dict, color_preparation_list


def plot_lifecycle_emissions_of_cars(config, fig_dict, ECONOMY_IDs, model_output_detailed_df, colors_dict, color_preparation_list, model_output_with_fuels_df, ACCUMULATED=False, ONLY_CARS=True, WRITE_HTML=False, AREA=False):
    #would liek to plot a area cahrt which shows the emissions from use of cars, with one color used for evs and then another for all others. Then different patterns will represent the emissions from fuel/electricity use, and then the other will represent the emissions from manufacturing and disposal. This will help to put into perspective how much the emissions from manufacturing and disposal are compared to the emissions from use, and whether they really matter in the grand scheme of things.
    #also offer to produce the accumulated version of this graph
    model_output_detailed = model_output_detailed_df.copy()
    model_output_with_fuels = model_output_with_fuels_df.copy()
    if ONLY_CARS:
        model_output_detailed = model_output_detailed.loc[model_output_detailed['Vehicle Type'].isin(['car', 'lt', 'suv'])].copy()
        model_output_with_fuels = model_output_with_fuels.loc[model_output_with_fuels['Vehicle Type'].isin(['car', 'lt', 'suv'])].copy()
        #repalce lt and suv with car
        model_output_detailed['Vehicle Type'] = 'car'
        model_output_with_fuels['Vehicle Type'] = 'car'
        #sum all 
        # breakpoint()
        model_output_detailed = model_output_detailed.groupby(config.INDEX_COLS_NO_MEASURE, as_index=False).sum(numeric_only=True)
        model_output_with_fuels = model_output_with_fuels.groupby(config.INDEX_COLS_NO_MEASURE+['Fuel'], as_index=False).sum(numeric_only=True)
        
    else:
        raise ValueError('ONLY_CARS must be True or you have to write the code to handle other vehicle types')
    lca_inputs = extract_lifecycle_emissions_series(config)
    lca = calculate_lifecycle_emissions_from_car_sales(config, model_output_detailed, lca_inputs)
    all_data, electricity_emissions, emissions_factors = calculate_emissions(config, model_output_with_fuels, model_output_detailed, USE_AVG_GENERATION_EMISSIONS_FACTOR=True, drive_column='Drive', energy_column = 'Energy')
    
    target_drives = ['bev', 'ice_g']#these are the drives or whch we'll create a graph of the emissions from use. 
    #extract the emissions from use for the target drives
    #1.
    #we can just clacualte energy use / stocks to find the amount of energy used per car, then times this by the emissions factor to find the emissions from use per car. We also know that this considers the effect of zero-emissions fuels!
    #firstgrab energy use for the primary fuels
    drive_to_primary_fuel = {'bev':'17_electricity', 'ice_g':'07_01_motor_gasoline', 'ice_d':'07_07_gas_diesel_oil'}
    target_fuels = [drive_to_primary_fuel[drive] for drive in target_drives]
    energy_use = model_output_with_fuels.loc[model_output_with_fuels['Fuel'].isin(target_fuels)].copy()
    #then join with stocks
    energy_use = energy_use.merge(model_output_detailed[['Economy', 'Scenario', 'Date', 'Drive', 'Transport Type', 'Vehicle Type', 'Stocks']], on=['Economy', 'Scenario', 'Date', 'Drive', 'Transport Type', 'Vehicle Type'], how='left')
    #then calculate the energy use per car as energy use / stocks
    energy_use['Energy_use_per_car'] = energy_use['Energy'] / energy_use['Stocks']
    #then join with emissions factors and times the energy use per car by the emissions factor to get the emissions from use per car/vehicle type
    energy_use = energy_use.merge(emissions_factors, on=['Economy', 'Scenario', 'Date', 'Fuel'], how='left')
    energy_use['Annual_use_emissions_per_car'] = energy_use['Energy_use_per_car'] * energy_use['Emissions factor (MT/PJ)']
        
    #RENAME fuels from 07_01_motor_gasoline to petrol and 17_electricity to electricity
    energy_use = energy_use.replace({'Fuel':{'07_01_motor_gasoline':'petrol', '17_electricity':'electricity', '07_07_gas_diesel_oil':'diesel'}})
    #check that no other fuels have emissions associated with them
    for fuel in energy_use['Fuel'].unique():
        if (energy_use.loc[energy_use['Fuel']==fuel].Annual_use_emissions_per_car.sum()> 0) and (fuel not in ['petrol', 'electricity', 'diesel']):
            breakpoint()
            raise ValueError(f'Fuel {fuel} has emissions associated with it')
    #plot the emissions from use
    plot_emissions_from_use_for_single_vehicle(config, energy_use, fuels_to_plot=['petrol', 'electricity'])
    
    #create plot of emissions from inputs. 
    plot_lca_inputs(config, lca_inputs)
    #just average the emissions from inputs for each drive
    ###############
    lca = clean_and_merge_lca_and_emissions(config, lca, all_data)
       
    #now if ACCUMULATED is True, then we should calculate the accumulated emissions
    if ACCUMULATED:
        #sort, group by and calcaulte the accumulated emissions
        lca = lca.sort_values(by=['Economy', 'Scenario', 'Date', 'Drive', 'Emissions_source']).copy()
        lca['Emissions'] = lca.groupby(['Economy', 'Scenario', 'Drive', 'Emissions_source'])['Emissions'].cumsum()
        
    ###############
    #now loop through the scenario and plot Emissions and  
    for scenario in lca['Scenario'].unique():
        lca_scenario = lca.loc[lca['Scenario']==scenario].copy()
        for economy in lca_scenario['Economy'].unique():
            lca_economy = lca_scenario.loc[lca_scenario['Economy']==economy].copy()
            
            #drop the first year of data, since it is a bit weird
            lca_economy = lca_economy.loc[lca_economy['Date']!=config.OUTLOOK_BASE_YEAR].copy()
            #plot the data
            #rename Emissions_source values, from 'Emisisons from inputs' to 'Emissions from production'
            lca_economy = lca_economy.replace({'Emissions_source':{'Emissions from inputs':'Emissions from production'}})
            title = f'Lifecycle emissions of all cars - {scenario} - {economy}'
            if AREA:
                fig = px.area(lca_economy, x='Date', y='Emissions', color='Drive', title=title, pattern_shape='Emissions_source', color_discrete_map=colors_dict)
            else:
                fig = px.line(lca_economy, x='Date', y='Emissions', color='Drive', title=title, color_discrete_map=colors_dict, line_dash='Emissions_source')
            # breakpoint()#save our own vertsion of the fig
            #make text a bit bigger 
            if WRITE_HTML:
                # fig.update_layout(font_size=30)#, title_x=0.5, title_y=0.9)
                # #make lines slightly thicker
                # fig.update_traces(line=dict(width=10))
                # fig.write_html(config.root_dir + config.slash +f'plotting_output\\lifecycle_emissions\\lifecycle_emissions_of_cars_{scenario}_{economy}.html')
                write_graph_to_html(config, filename=f'lifecycle_emissions_of_cars_{scenario}_{economy}.html', graph_type='line', plot_data=lca_economy,economy=economy, x='Date', y='Emissions', color='Drive', title=title, font_size=30, line_width=10, colors_dict=colors_dict)
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['lifecycle_emissions_of_cars'] = [fig, title, True]
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(lca_economy['Drive'].unique().tolist())
    return fig_dict, color_preparation_list

def plot_lca_inputs(config, lca_inputs):
    #jsut do a simple bar plot with the emissions from inputs
    color_dict = {'ice_g':'red', 'bev':'green', 'ice_d':'grey'}
    #rename 'lifecycle emissions' to 'Emissions from manufacturing, inputs and disposal'
    lca_inputs = lca_inputs.rename(columns={'lifecycle emissions':'Emissions from manufacturing, inputs and disposal'})
    fig = px.bar(lca_inputs, x='drive', y='Emissions from manufacturing, inputs and disposal', color='drive', title='Emissions from production', color_discrete_map=color_dict)
    #set yaixs title
    fig.update_yaxes(title_text='MT CO2e')
    fig.update_layout(font_size=30)
    #drop the legend
    fig.update_layout(showlegend=False)
    fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'lifecycle_emissions', 'lifecycle_emissions_of_cars_inputs.html'))

def plot_emissions_from_use_for_single_vehicle(config, emissions_factors, fuels_to_plot):
    
    # Keep only the fuels in fuels_to_plot
    emissions_factors_filtered = emissions_factors[emissions_factors['Fuel'].isin(fuels_to_plot)]
    economy = emissions_factors_filtered['Economy'].unique()[0]
    # Aggregate emissions factors by 'fuel' and 'Date', if necessary
    emissions_factors_filtered = emissions_factors_filtered.groupby(['Date', 'Fuel', 'Vehicle Type', 'Scenario']).mean(numeric_only=True).reset_index()
    
    # Create the line chart using px.line
    #rename Fuel to Drive and call petrol 'ice_g' and electricity 'bev'
    emissions_factors_filtered = emissions_factors_filtered.replace({'Fuel':{'petrol':'ice_g', 'electricity':'bev', 'diesel':'ice_d'}})
    emissions_factors_filtered = emissions_factors_filtered.rename(columns={'Fuel':'Drive'})
    
    # Define color mapping (optional, px.line will automatically assign colors if not used)
    color_discrete_map = {'bev': 'green', 'ice_g': 'red', 'diesel': 'grey'}
    for drive in emissions_factors_filtered.Drive.unique():
        if drive not in color_discrete_map.keys():
            #randomly assign a color to each fuel
            # breakpoint()
            import random
            import matplotlib.colors as mcd
            try:
                color_discrete_map[drive] = random.choice(list(mcd.XKCD_COLORS.values()))
            except:
                breakpoint()
                raise ValueError('color_discrete_map not working')
    for scenario in emissions_factors_filtered.Scenario.unique():
        emissions_factors_filtered_scenario = emissions_factors_filtered.loc[emissions_factors_filtered['Scenario']==scenario].copy()
        #identify when there are essentially 0  stocks of a drive/vehicle type at this point, drop these rows
        emissions_factors_filtered_scenario = emissions_factors_filtered_scenario.loc[emissions_factors_filtered_scenario['Stocks'] > emissions_factors_filtered_scenario['Stocks'].sum() * 0.0001]
        fig = px.line(emissions_factors_filtered_scenario, x='Date', y='Annual_use_emissions_per_car', color='Drive',
                    color_discrete_map=color_discrete_map, 
                    labels={'Annual_use_emissions_per_car':'MT CO2'}, 
                    title=f'Annual emissions from use', line_dash='Vehicle Type')#by Drive - {scenario} - {economy}
        # Update layout if needed (e.g., making text bigger)
        fig.update_layout(font_size=35)
        #make line thicker
        fig.update_traces(line=dict(width=10))
        #drop the legend
        fig.update_layout(showlegend=False)
        fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'lifecycle_emissions', f'{economy}_lifecycle_emissions_LINE_{scenario}.html'))
     
def clean_and_merge_lca_and_emissions(config, lca, all_data):
    #merge lca and all_data to get the emissions from manufacturing and disposal and use:
    #first, where drive is not bev, rename it to ice in both dataframes
    lca_bev = lca[lca.Drive == 'bev'].copy()
    lca_non_bev = lca[lca.Drive.isin(['ice_g', 'ice_d'])].copy()
    lca_non_bev['Drive'] = 'ice'
    lca = pd.concat([lca_bev, lca_non_bev])
    
    all_data_bev = all_data[all_data.Drive == 'bev'].copy()
    all_data_non_bev = all_data[all_data.Drive != 'bev'].copy()
    all_data_non_bev['Drive'] = 'ice'
    all_data = pd.concat([all_data_bev, all_data_non_bev])
    
    #drop uneeded cols and group by and sum
    lca = lca[['Economy', 'Scenario', 'Date', 'Drive', 'Lifecycle Emissions']].groupby(['Economy', 'Scenario', 'Date', 'Drive']).sum().reset_index()
    all_data = all_data[['Economy', 'Scenario', 'Date', 'Drive', 'Emissions']].groupby(['Economy', 'Scenario', 'Date', 'Drive']).sum().reset_index()
    
    lca = lca.merge(all_data, on=['Economy', 'Scenario', 'Date', 'Drive'], how='left')
    
    #rename Lifecycle Emissions to Emissions from manufacturing and disposal
    lca = lca.rename(columns={'Lifecycle Emissions':'Emissions from inputs', 'Emissions':'Emissions from use'})
    
    #nowmelt so we can have a column called Emissions source
    lca = lca.melt(id_vars=['Economy', 'Scenario', 'Date', 'Drive'], value_vars=['Emissions from inputs', 'Emissions from use'], var_name='Emissions_source', value_name='Emissions')
    return lca

def calculate_emissions(config, energy_use_by_fuels, all_data, USE_AVG_GENERATION_EMISSIONS_FACTOR=True, drive_column='Drive', energy_column = 'Energy', SUPPLIED_COLS =[], DROP_FUELS=True):
    """take in energy_use_by_fuels and all_data (any general dataframe with the index cols required for most things in this system - except a fuel column), calcaulte emissions in energy_use_by_fuels and then merge them back into all_data, since all data didnt have energy use by fuel, so it wasnt possible to calculate emissions in all_data

    Args:
        energy_use_by_fuels (_type_): _description_
        all_data (_type_): _description_
        USE_AVG_GENERATION_EMISSIONS_FACTOR (bool, optional): _description_. Defaults to False.

    Raises:
        ValueError: _description_
    """
    
    emissions_factors = pd.read_csv(os.path.join(config.root_dir, 'config', '9th_edition_emissions_factors.csv'))
    if len(SUPPLIED_COLS)>0:
        cols = SUPPLIED_COLS
    else:
        cols =['Economy', 'Scenario','Date', 'Fuel', 'Transport Type','Vehicle Type',drive_column,'Medium',energy_column]
            
        if drive_column != 'Drive':
            energy_use_by_fuels = energy_use_by_fuels.rename(columns={'Drive':drive_column})
        if energy_column != 'Energy':
            energy_use_by_fuels = energy_use_by_fuels.rename(columns={'Energy':energy_column})
        
    cols_no_energy = [x for x in cols if x != energy_column]
    cols_no_energy_no_fuel = [x for x in cols_no_energy if x != 'Fuel']
    #load in data and recreate plot, as created in all_economy_graphs
    #loop through scenarios and grab the data for each scenario:
    energy_use_by_fuels = energy_use_by_fuels[cols].groupby(cols_no_energy).sum().reset_index().copy()
    
    #rename fuel_code to fuel in emissions_factors
    emissions_factors = emissions_factors.rename(columns={'fuel_code':'Fuel'})
    #join on the emissions factors (has the cols fuel_code,	Emissions factor (MT/PJ))
    energy_use_by_fuels_TEST = energy_use_by_fuels.merge(emissions_factors, how='left', on='Fuel')
    ###########
    #identify where there a!re no emissions factors:
    missing_emissions_factors = energy_use_by_fuels_TEST.loc[energy_use_by_fuels_TEST['Emissions factor (MT/PJ)'].isna()].copy()
    if len(missing_emissions_factors)>0:
            
        #if any are in the follwoing m apping, then map them accordingly:
        fuel_mapping = {'7_x_other_petroleum_products':'07_x_other_petroleum_products'}
        energy_use_by_fuels['Fuel'] = energy_use_by_fuels['Fuel'].replace(fuel_mapping)
    #then do the mapping again
    energy_use_by_fuels = energy_use_by_fuels.merge(emissions_factors, how='left', on='Fuel')
    #identify where there are no emissions factors:
    missing_emissions_factors = energy_use_by_fuels.loc[energy_use_by_fuels['Emissions factor (MT/PJ)'].isna()].copy()
    if len(missing_emissions_factors)>0:
        breakpoint()
        raise ValueError(f'missing emissions factors, {missing_emissions_factors.Fuel.unique()}')
    ###########
    if USE_AVG_GENERATION_EMISSIONS_FACTOR:
        #pull in the 8th outlook emissions factors by year then use that to claculate the emissions for electricity.
        emissions_factor_elec = pd.read_csv(os.path.join(config.root_dir, 'input_data', 'from_8th', 'outlook_8th_emissions_factors_with_electricity.csv'))#c:\Users\finbar.maunsell\github\aperc-emissions\output_data\outlook_8th_emissions_factors_with_electricity.csv
        #extract the emissions factor for elctricity for each economy
        emissions_factor_elec = emissions_factor_elec[emissions_factor_elec.fuel_code=='17_electricity'].copy()
        #rename Carbon Neutral Scenario to Target
        emissions_factor_elec['Scenario'] = emissions_factor_elec['Scenario'].replace('Carbon Neutral', 'Target')
        #capitalise the cols
        emissions_factor_elec.columns = [x.capitalize() for x in emissions_factor_elec.columns]
        #rename fuel code to fuel
        emissions_factor_elec = emissions_factor_elec.rename(columns={'Fuel_code':'Fuel', 'Year':'Date', 'Emissions factor (mt/pj)':'Emissions factor (MT/PJ)'})
        
        #merge on economy and year and fuel code
        energy_use_by_fuels = energy_use_by_fuels.merge(emissions_factor_elec, on=['Date', 'Economy', 'Scenario', 'Fuel'], how='left', indicator=True, suffixes=('', '_elec'))
        #where indicator is both, use the new value
        energy_use_by_fuels['Emissions factor (MT/PJ)'] = np.where(energy_use_by_fuels['_merge']=='both', energy_use_by_fuels['Emissions factor (MT/PJ)_elec'], energy_use_by_fuels['Emissions factor (MT/PJ)'])
        
        #fill any missing values using ffill after sorting by date and grouping by 'Economy', 'Scenario','Date', 'Fuel', 'Transport Type'
        energy_use_by_fuels['Emissions factor (MT/PJ)'] = energy_use_by_fuels.sort_values(by='Date').groupby(cols_no_energy)['Emissions factor (MT/PJ)'].fillna(method='ffill')
        
        #drop columns
        energy_use_by_fuels = energy_use_by_fuels.drop(columns=['Emissions factor (MT/PJ)_elec', '_merge'])
        
    #identify where there are no emissions factors:
    missing_emissions_factors = energy_use_by_fuels.loc[energy_use_by_fuels['Emissions factor (MT/PJ)'].isna()].copy()
    if len(missing_emissions_factors)>0:
        breakpoint()
        raise ValueError(f'missing emissions factors, {missing_emissions_factors.Fuel.unique()}')
    
    #calculate emissions:
    energy_use_by_fuels['Emissions'] = energy_use_by_fuels[energy_column] * energy_use_by_fuels['Emissions factor (MT/PJ)']
    
    emissions_factors = energy_use_by_fuels.loc[(energy_use_by_fuels['Emissions factor (MT/PJ)']>0)][['Economy','Scenario','Date','Fuel','Emissions factor (MT/PJ)']].drop_duplicates().copy()
    
    #extract the electricity emissions to use them separately if need be:
    electricity_emissions = energy_use_by_fuels[energy_use_by_fuels.Fuel=='17_electricity'].copy()
    #drop fuels and then sum
    if DROP_FUELS:
        energy_use_by_fuels = energy_use_by_fuels.drop(columns=['Fuel', 'Emissions factor (MT/PJ)']).groupby(cols_no_energy_no_fuel).sum().reset_index()
        electricity_emissions = electricity_emissions.drop(columns=['Fuel', 'Emissions factor (MT/PJ)']).groupby(cols_no_energy_no_fuel).sum().reset_index()
        #now merge emissions back into all_data
        if all_data is not None:
            all_data = all_data.merge(energy_use_by_fuels[cols_no_energy_no_fuel +['Emissions']], how='left', on=cols_no_energy_no_fuel)
        else:
            all_data = energy_use_by_fuels.copy()
    else:
        if all_data is not None:
            all_data = all_data.merge(energy_use_by_fuels[cols_no_energy +['Emissions']], how='left', on=cols_no_energy)
        else:
            all_data = energy_use_by_fuels.copy()
        
    
    return all_data, electricity_emissions, emissions_factors

def extract_lifecycle_emissions_series(config):
    
    #to help make the graph even more informative, we will add a series that represents the lifecyle emissions from purchasing ice and ev cars. This way the user can observe the difference in emissions when there are lots of evs vs not many purchased.
    #load in the lifecycle emissions data that was gatehred from multiple soruces and then averaged
    lca = pd.read_excel(os.path.join(config.root_dir, 'input_data', 'lifecycle_emissions.xlsx'))
    #drop where READY_TO_USE is not True
    lca = lca[lca['READY_TO_USE']==True]
    #grab the cols we need and average them out (we will exclude the cols on use phase emissions for now)
    # cols:
    # vehicle type,	category,	drive,	study, source,	materials production and refining,	battery production,	car manufacturing,	use phase emissions,	end of life,	other,	READY_TO_USE
    #set cols that are na to 0
    lca = lca.fillna(0)
    #make sure that all the numeric cols are numeric
    numeric_cols = ['materials production and refining', 'battery production', 'car manufacturing', 'end of life', 'other']
    if not all([lca[col].dtype == 'float64' for col in numeric_cols]):
        for col in numeric_cols:
            lca[col] = lca[col].astype('float64')
    #add the values across their respective columns to get the lifecycle emissions
    lca['lifecycle emissions'] = lca['materials production and refining'] + lca['battery production'] + lca['car manufacturing'] + lca['end of life'] + lca['other']
    lca = lca[['vehicle type', 'drive', 'lifecycle emissions', 'study source']]
    #average them out but make sure to do it by study source too at first so that step cahnges between studies where some studies may have mroe data on bevs or ice cars than others dont affet the average too much
    lca = lca.groupby(['vehicle type', 'drive', 'study source']).mean(numeric_only=True).reset_index()
    #now average them out by vehicle type and drive
    lca = lca.groupby(['vehicle type', 'drive']).mean(numeric_only=True).reset_index()
    #if vehicle type is only car then drop it and mean all
    if len(lca['vehicle type'].unique()) == 1:
        lca = lca.groupby(['drive']).mean(numeric_only=True).reset_index()
    else:
        raise ValueError('lca has more than 1 vehicle type, not expected')
    
    return lca
    
def calculate_lifecycle_emissions_from_car_sales(config, sales, lca):
    #now times this by the nubmer of new stocks of cars in each year to get the lifecycle emissions
    sales = sales[['Economy', 'Date', 'Drive', 'Scenario', 'New_stocks_needed']].groupby(['Economy', 'Date', 'Scenario','Drive']).sum().reset_index()
    
    #calcualte change in stocks each year, after sorting by date and grouping by drive
    if len(lca['drive'].unique()) == 2:
        if 'bev' in lca['drive'].unique() and 'ice_g' in lca['drive'].unique():
            sales.loc[sales['Drive']!='bev', 'Drive'] = 'ice_g'
        else:
            raise ValueError('lca has weird drives, not expected')
    else:
        raise ValueError('lca has more than 2 drives, not expected')
    #rename drive to Drive
    lca = lca.rename(columns={'drive':'Drive', 'lifecycle emissions':'Lifecycle Emissions'})
    #merge the stocks and lca data
    lca = lca.merge(sales, on=['Drive'], how='inner')
    #times the lifecycle emissions by the saels
    lca['Lifecycle Emissions'] = lca['Lifecycle Emissions'] * lca['New_stocks_needed']
    #sumby date and drop everythin by date and lifecycle emissions
    lca = lca.groupby(['Economy', 'Date', 'Drive','Scenario']).sum().reset_index()
    #keep only the date and lifecycle emissions
    lca = lca[['Economy', 'Date', 'Drive','Scenario', 'Lifecycle Emissions']]
    return lca

def share_of_emissions_by_vehicle_type(config, fig_dict, ECONOMY_IDs, emissions_factors, model_output_with_fuels_df, colors_dict, color_preparation_list, USE_AVG_GENERATION_EMISSIONS_FACTOR=False, WRITE_HTML=True):
    model_output_with_fuels = model_output_with_fuels_df.copy()
    # drop non road:
    model_output_with_fuels = model_output_with_fuels.loc[model_output_with_fuels['Medium']=='road'].copy()
    #change suv, lt and car to all be 'lpv' and all ht and mt to be truck
    model_output_with_fuels['Vehicle Type'] = np.where(model_output_with_fuels['Vehicle Type'].isin(['suv', 'lt', 'car']), 'lpv', model_output_with_fuels['Vehicle Type'])
    model_output_with_fuels['Vehicle Type'] = np.where(model_output_with_fuels['Vehicle Type'].isin(['ht', 'mt']), 'truck', model_output_with_fuels['Vehicle Type'])
    #TEMP #WHERE TRANSPORT TYPE IS FREIGHT or medium is not road, SET THE electricty yse to 0. This is so we can test what the effect of electriicyt is 
    # model_output_with_fuels.loc[(model_output_with_fuels['Transport Type']=='freight') | (model_output_with_fuels['Medium']!='road') & (model_output_with_fuels['Fuel']=='17_electricity'), 'Energy'] = 0
    #load in data and recreate plot, as created in all_economy_graphs
    #loop through scenarios and grab the data for each scenario:
    emissions_by_vehicle_type= model_output_with_fuels[['Economy', 'Scenario','Date', 'Fuel', 'Vehicle Type','Energy']].groupby(['Economy', 'Scenario','Date','Vehicle Type', 'Fuel']).sum().reset_index().copy()
    
    #rename fuel_code to fuel in emissions_factors
    emissions_factors = emissions_factors.rename(columns={'fuel_code':'Fuel'})
    #join on the emissions factors (has the cols fuel_code,	Emissions factor (MT/PJ))
    emissions_by_vehicle_type = emissions_by_vehicle_type.merge(emissions_factors, how='left', on='Fuel')
    
    if USE_AVG_GENERATION_EMISSIONS_FACTOR:
        gen='_gen'
        #pull in the 8th outlook emissions factors by year, then use that to claculate the emissions for electricity.
        emissions_factor_elec = pd.read_csv(os.path.join(config.root_dir, 'input_data', 'from_8th', 'outlook_8th_emissions_factors_with_electricity.csv'))#c:\Users\finbar.maunsell\github\aperc-emissions\output_data\outlook_8th_emissions_factors_with_electricity.csv
        #extract the emissions factor for elctricity for each economy
        emissions_factor_elec = emissions_factor_elec[emissions_factor_elec.fuel_code=='17_electricity'].copy()
        #rename Carbon Neutral Scenario to Target
        emissions_factor_elec['Scenario'] = emissions_factor_elec['Scenario'].replace('Carbon Neutral', 'Target')
        #capitalise the cols
        emissions_factor_elec.columns = [x.capitalize() for x in emissions_factor_elec.columns]
        #rename fuel code to fuel
        emissions_factor_elec = emissions_factor_elec.rename(columns={'Fuel_code':'Fuel', 'Year':'Date', 'Emissions factor (mt/pj)':'Emissions factor (MT/PJ)'})
        #merge on economy and year and fuel code
        emissions_by_vehicle_type = emissions_by_vehicle_type.merge(emissions_factor_elec, on=['Date', 'Economy', 'Scenario', 'Fuel'], how='left', indicator=True, suffixes=('', '_elec'))
        #where indicator is both, use the new value
        emissions_by_vehicle_type['Emissions factor (MT/PJ)'] = np.where(emissions_by_vehicle_type['_merge']=='both', emissions_by_vehicle_type['Emissions factor (MT/PJ)_elec'], emissions_by_vehicle_type['Emissions factor (MT/PJ)'])
        #fill any missing values using ffill after sorting by date and grouping by 'Economy', 'Scenario','Date','Vehicle Type', 'Fuel'])
        emissions_by_vehicle_type['Emissions factor (MT/PJ)'] = emissions_by_vehicle_type.sort_values(by='Date').groupby(['Economy', 'Scenario','Date','Vehicle Type', 'Fuel'])['Emissions factor (MT/PJ)'].fillna(method='ffill')
        #drop columns
        emissions_by_vehicle_type = emissions_by_vehicle_type.drop(columns=['Emissions factor (MT/PJ)_elec', '_merge'])
    #identify where there are no emissions factors:
    missing_emissions_factors = emissions_by_vehicle_type.loc[emissions_by_vehicle_type['Emissions factor (MT/PJ)'].isna()].copy()
    if len(missing_emissions_factors)>0:
        breakpoint()
        time.sleep(1)
        raise ValueError(f'missing emissions factors, {missing_emissions_factors.Fuel.unique()}')
    
    #calculate emissions:
    emissions_by_vehicle_type['Emissions'] = emissions_by_vehicle_type['Energy'] * emissions_by_vehicle_type['Emissions factor (MT/PJ)']

    #grab the emissions by vehicle type and sum them
    emissions_by_vehicle_type = emissions_by_vehicle_type.groupby(['Economy', 'Scenario', 'Date', 'Vehicle Type']).sum().reset_index()
    #grab the total emissions for each date and economy
    total_emissions = emissions_by_vehicle_type.groupby(['Economy', 'Scenario', 'Date']).sum().reset_index()
    #merge the two dataframes and then calcaulte the share of emissions by vehicle type
    emissions_by_vehicle_type = emissions_by_vehicle_type.merge(total_emissions, on=['Economy', 'Scenario', 'Date'], how='left', suffixes=('', '_total'))
    emissions_by_vehicle_type['Share of emissions'] = emissions_by_vehicle_type['Emissions'] / emissions_by_vehicle_type['Emissions_total']
    #plot the data
    for scenario in emissions_by_vehicle_type['Scenario'].unique():
        emissions_by_vehicle_type_scenario = emissions_by_vehicle_type.loc[emissions_by_vehicle_type['Scenario']==scenario].copy()
        for economy in emissions_by_vehicle_type_scenario['Economy'].unique():
            emissions_by_vehicle_type_economy = emissions_by_vehicle_type_scenario.loc[emissions_by_vehicle_type_scenario['Economy']==economy].copy()
            #plot the data
            title = f'Share of potential emissions by vehicle type (%)'
            fig = px.line(emissions_by_vehicle_type_economy, x='Date', y='Share of emissions', color='Vehicle Type', title=title, color_discrete_map=colors_dict)
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['share_of_emissions_by_vehicle_type'] = [fig, title, True]
            if WRITE_HTML:
                write_graph_to_html(config, filename=f'share_of_emissions_by_vehicle_type_{scenario}_{economy}.html',graph_type='line', economy=economy,plot_data=emissions_by_vehicle_type_economy, x='Date', y='Share of emissions', color='Vehicle Type', title=title, font_size=30, line_width=10, colors_dict=colors_dict)
                                
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(emissions_by_vehicle_type['Vehicle Type'].unique().tolist())
    return fig_dict, color_preparation_list
    

def plot_new_vehicle_efficiency_by_vehicle_type(config, fig_dict, ECONOMY_IDs, model_output_detailed_df, colors_dict, color_preparation_list, DROP_NON_ROAD_TRANSPORT=True, transport_type='all', extra_ice_line=True, extra_bev_line=True, WRITE_HTML=True, vehicle_type_grouping='simplified'):
    # (ECONOMY_IDs,model_output_detailed,fig_dict,DROP_NON_ROAD_TRANSPORT, color_preparation_list, colors_dict, transport_type, extra_ice_line=True):
    PLOTTED=True

    conversion_factors =pd.read_csv(os.path.join(config.root_dir, 'config', 'concordances_and_config_data', 'conversion_factors.csv'))
    #to help with checking the data is, plot new vehicle energy efficiency here:
    
    energy_eff = model_output_detailed_df.copy()
    if DROP_NON_ROAD_TRANSPORT:
        energy_eff = energy_eff.loc[energy_eff['Medium']=='road']
    else:
        #set vehicle type to medium so we can plot strip plot by vehicle type: 
        energy_eff.loc[energy_eff['Medium'] != 'road', 'Vehicle Type'] = energy_eff.loc[energy_eff['Medium'] != 'road', 'Medium']
    if transport_type == 'passenger':
        energy_eff = energy_eff.loc[energy_eff['Transport Type']=='passenger']
    elif transport_type == 'freight':
        energy_eff = energy_eff.loc[energy_eff['Transport Type']=='freight']
        
    #Note that its a bit complicated to show the average new vehicle efficiency since we should be weighting it according to the drive type within each vehicle type tha makes up the marjotiy of new vehicles! So we should soon times the efficiency by 1+New_stocks_needed then divide by the sum of (New_stocks_needed +1) for each vehicle type
    energy_eff['New_stocks_needed'] = energy_eff['New_stocks_needed'].fillna(0)
    
    #group the vehicle types
    energy_eff = remap_vehicle_types(config, energy_eff, value_col='New_vehicle_efficiency', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'],vehicle_type_mapping_set=vehicle_type_grouping, aggregation_type=('weighted_average', 'New_stocks_needed'))
    
    #calc weighted mean of efficiency by using activity as the weight and, importantly, remove date, scenario
    # energy_eff = energy_eff[['Date', 'Economy', 'Vehicle Type', 'Scenario','Efficiency']].groupby(['Date','Economy','Scenario','Vehicle Type']).mean().reset_index()
    
    energy_eff['ICE_ONLY'] = 'all'
    if extra_ice_line:
        #we want to create a dotted line for each vehicle type that shows the ice efficiency. that is the efficiency when you only consider the ice_d and ice_g vehicles.
        #first, filter to only ice_d and ice_g:
        energy_eff_ice = energy_eff.loc[energy_eff['Drive'].isin(['ice_d', 'ice_g'])].copy()
        #just label ICE_ONLY as True
        energy_eff_ice['ICE_ONLY'] = 'ice_only'
        #now concat the two dfs:
        energy_eff = pd.concat([energy_eff, energy_eff_ice])
    
    if extra_bev_line:
        #we want to create a dotted line for each vehicle type that shows the ice efficiency. that is the efficiency when you only consider the ice_d and ice_g vehicles.
        #first, filter to only ice_d and ice_g:
        energy_eff_bev = energy_eff.loc[energy_eff['Drive'].isin(['bev'])].copy()
        #just label ICE_ONLY as True
        energy_eff_bev['ICE_ONLY'] = 'bev_only'
        #now concat the two dfs:
        energy_eff = pd.concat([energy_eff, energy_eff_bev])
    if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
        breakpoint()#im not 100% this is being calculated correctly. It seems that ICE_ONL=all is too high at beginning
        print('check that the new vehicle efficiency is being calculated correctly. It seems that ICE_ONL=all is too high at beginning')
    energy_eff['New_vehicle_efficiency_weighted'] = energy_eff['New_vehicle_efficiency'] * energy_eff['New_stocks_needed']
    energy_eff = energy_eff[['Date', 'Economy', 'Vehicle Type', 'Scenario','New_vehicle_efficiency_weighted', 'New_vehicle_efficiency', 'New_stocks_needed', 'ICE_ONLY']].groupby(['Date','Economy','Scenario','Vehicle Type', 'ICE_ONLY']).sum().reset_index()
    #calculate weighted average
    energy_eff['New_vehicle_efficiency'] = energy_eff['New_vehicle_efficiency_weighted']/energy_eff['New_stocks_needed']#WORRIED ABOUT THE EFFECT OF DIVIDING BY ANY VALUE BETWEEN 0 AND 1 HERE
    energy_eff = energy_eff.drop(columns=['New_vehicle_efficiency_weighted', 'New_stocks_needed'])

    # #simplfiy drive type using remap_drive_types
    # fkm = remap_drive_types(config, fkm, value_col='freight_tonne_km', new_index_cols = ['Economy', 'Date', 'Scenario','Drive'])
    
    #add units (by setting measure to Freight_tonne_km haha)
    energy_eff['Measure'] = 'New_vehicle_efficiency'
    
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        energy_eff_by_scen = energy_eff.loc[(energy_eff['Scenario']==scenario)].copy()
        

        for economy in ECONOMY_IDs:
            #filter to economy
            energy_eff_by_scen_by_economy = energy_eff_by_scen.loc[energy_eff_by_scen['Economy']==economy].copy()
            ###################################
            #BASED ON THE ECONOMY, SET THE EFFICIENCY TO SOMETHING THAT IS COMPARABLE T THEIR OWN MEASURES (I.E. IN USA SET TO MPG, IN MAS SET TO L/100KM). Note that we will need to take into account the energy content of diesel and gasoline for ice_g, ice_d, phev_g and phev_d. (in hindsight had to set this based on vehicle type)
            #set unit to 'km per MJ' and we will change it if we need
            energy_eff_by_scen_by_economy['unit'] = 'km/MJ'
            energy_eff_by_scen_by_economy['conversion_fuel'] = np.where(energy_eff_by_scen_by_economy['Vehicle Type'].isin(['trucks', 'lcv']), 'diesel', 'petrol')
            #join to conversion factor using conversion fuel > fuel
            
            economy_to_conversion_factor = {
                '20_USA':'mpg_to_billion_km_per_pj',
                '10_MAS':'km_per_liter_to_km_per_mj'#a pj is 1bil mjs 
            }
            new_units = {
                '20_USA':'mpg',
                '10_MAS':'L/km'
            }
            magnitude_multiplier = {
                '20_USA':1,
                '10_MAS':1/100
            }
            inverse_economies = ['10_MAS']
            if economy in economy_to_conversion_factor.keys():
                conversion_factors_new = conversion_factors[conversion_factors['conversion_factor']==economy_to_conversion_factor[economy]].copy()
                energy_eff_by_scen_by_economy = energy_eff_by_scen_by_economy.merge(conversion_factors_new, left_on='conversion_fuel', right_on='fuel', how='left', indicator=True)
                #check for missing merges
                bad_merges = energy_eff_by_scen_by_economy[energy_eff_by_scen_by_economy['_merge']!='both']
                if len(bad_merges)>0:
                    breakpoint()
                    raise ValueError('Cannot complete conversion factos merge, missing the rows: {}'.format(bad_merges))
                #do conversion
                energy_eff_by_scen_by_economy['New_vehicle_efficiency']=energy_eff_by_scen_by_economy['New_vehicle_efficiency']/energy_eff_by_scen_by_economy['value']
                if economy in magnitude_multiplier.keys():
                    energy_eff_by_scen_by_economy['New_vehicle_efficiency']=energy_eff_by_scen_by_economy['New_vehicle_efficiency']*magnitude_multiplier[economy]
                if economy in inverse_economies:
                    energy_eff_by_scen_by_economy['New_vehicle_efficiency'] = 1/energy_eff_by_scen_by_economy['New_vehicle_efficiency']   
                energy_eff_by_scen_by_economy['unit'] = new_units[economy]            
            unit = energy_eff_by_scen_by_economy['unit'].unique()[0]
            ###################################
            if transport_type == 'all':
                title='New vehicle efficiency ({})'.format(unit)
            elif transport_type.isin(['passenger', 'freight']):
                title='New vehicle efficiency - {}  ({})'.format(transport_type, unit)
                
            fig = px.line(energy_eff_by_scen_by_economy, x='Date', y='New_vehicle_efficiency', color='Vehicle Type',line_dash='ICE_ONLY', title=title, color_discrete_map=colors_dict)#, line_dash='Vehicle Type')

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario][f'new_vehicle_efficiency_timeseries_{transport_type}'] = [fig, title, PLOTTED]
            
            if WRITE_HTML:
                #save to html
                title ='New vehicle efficiency - {} - {} - {}'.format(scenario, economy, unit)
                #keep only lpv if it is inthere
                if 'lpv' in energy_eff_by_scen_by_economy['Vehicle Type'].unique():
                    energy_eff_by_scen_by_economy = energy_eff_by_scen_by_economy.loc[energy_eff_by_scen_by_economy['Vehicle Type']=='lpv'].copy()
                write_graph_to_html(config, filename= f'{scenario}_new_vehicle_efficiency_timeseries_{transport_type}.html', graph_type='line', plot_data=energy_eff_by_scen_by_economy, economy=economy, x='Date', y='New_vehicle_efficiency', color='Vehicle Type', title=title, line_dash='ICE_ONLY', y_axes_title=unit, legend_title='', font_size=30, marker_line_width=2.5, line_width=10, colors_dict=colors_dict)
                
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(energy_eff_by_scen_by_economy['Vehicle Type'].unique().tolist())
    
    return fig_dict, color_preparation_list
    

def plot_new_vehicle_emissions_intensity_by_vehicle_type(config, fig_dict, ECONOMY_IDs, model_output_detailed_df, emissions_factors, colors_dict, color_preparation_list, DROP_NON_ROAD_TRANSPORT=True, transport_type='all', extra_ice_line=True, extra_bev_line=True, WRITE_HTML=True, vehicle_type_grouping='simplified', USE_AVG_GENERATION_EMISSIONS_FACTOR=False):
    # (ECONOMY_IDs,model_output_detailed,fig_dict,DROP_NON_ROAD_TRANSPORT, color_preparation_list, colors_dict, transport_type, extra_ice_line=True):
    PLOTTED=True

    #to help with checking the data is, plot new vehicle energy efficiency here:
    
    emissions_intensity = model_output_detailed_df.copy()
    if DROP_NON_ROAD_TRANSPORT:
        emissions_intensity = emissions_intensity.loc[emissions_intensity['Medium']=='road']
    else:
        #set vehicle type to medium so we can plot strip plot by vehicle type: 
        emissions_intensity.loc[emissions_intensity['Medium'] != 'road', 'Vehicle Type'] = emissions_intensity.loc[emissions_intensity['Medium'] != 'road', 'Medium']
    if transport_type == 'passenger':
        emissions_intensity = emissions_intensity.loc[emissions_intensity['Transport Type']=='passenger']
    elif transport_type == 'freight':
        emissions_intensity = emissions_intensity.loc[emissions_intensity['Transport Type']=='freight']
    
    drive_type_to_fuel = pd.read_csv(os.path.join(config.root_dir, 'config', 'concordances_and_config_data', 'drive_type_to_fuel.csv'))
    drive_type_to_fuel = drive_type_to_fuel.loc[drive_type_to_fuel['Supply_side_fuel_mixing'] != 'New fuel'][['Drive','Fuel']].drop_duplicates()
    
    #convert from drive type to fuel type:
    emissions_intensity = emissions_intensity.merge(drive_type_to_fuel, on='Drive', how='left')
    
    #rename fuel_code to fuel in emissions_factors
    emissions_factors = emissions_factors.rename(columns={'fuel_code':'Fuel'})
    #join on the emissions factors (has the cols fuel_code,	Emissions factor (MT/PJ))
    emissions_intensity = emissions_intensity.merge(emissions_factors, how='left', on='Fuel')
    
    if USE_AVG_GENERATION_EMISSIONS_FACTOR:
        gen='_gen'
        #pull in the 8th outlook emissions factors by year, then use that to claculate the emissions for electricity.
        emissions_factor_elec = pd.read_csv(os.path.join(config.root_dir, 'input_data', 'from_8th', 'outlook_8th_emissions_factors_with_electricity.csv'))#c:\Users\finbar.maunsell\github\aperc-emissions\output_data\outlook_8th_emissions_factors_with_electricity.csv
        #extract the emissions factor for elctricity for each economy
        emissions_factor_elec = emissions_factor_elec[emissions_factor_elec.fuel_code=='17_electricity'].copy()
        #rename Carbon Neutral Scenario to Target
        emissions_factor_elec['Scenario'] = emissions_factor_elec['Scenario'].replace('Carbon Neutral', 'Target')
        #capitalise the cols
        emissions_factor_elec.columns = [x.capitalize() for x in emissions_factor_elec.columns]
        #rename fuel code to fuel
        emissions_factor_elec = emissions_factor_elec.rename(columns={'Fuel_code':'Fuel', 'Year':'Date', 'Emissions factor (mt/pj)':'Emissions factor (MT/PJ)'})
        #merge on economy and year and fuel code
        emissions_intensity = emissions_intensity.merge(emissions_factor_elec, on=['Date', 'Economy', 'Scenario', 'Fuel'], how='left', indicator=True, suffixes=('', '_elec'))
        #where indicator is both, use the new value
        emissions_intensity['Emissions factor (MT/PJ)'] = np.where(emissions_intensity['_merge']=='both', emissions_intensity['Emissions factor (MT/PJ)_elec'], emissions_intensity['Emissions factor (MT/PJ)'])
        #fill any missing values using ffill after sorting by date and grouping by 'Economy', 'Scenario','Date', 'Fuel', 'Transport Type']
        emissions_intensity['Emissions factor (MT/PJ)'] = emissions_intensity.sort_values(by='Date').groupby(['Economy', 'Scenario','Date','Transport Type', 'Fuel'])['Emissions factor (MT/PJ)'].fillna(method='ffill')
        #drop columns
        emissions_intensity = emissions_intensity.drop(columns=['Emissions factor (MT/PJ)_elec', '_merge'])
        
    #identify where there are no emissions factors:
    missing_emissions_factors = emissions_intensity.loc[emissions_intensity['Emissions factor (MT/PJ)'].isna()].copy()
    if len(missing_emissions_factors)>0:
        breakpoint()
        time.sleep(1)
        raise ValueError(f'missing emissions factors, {missing_emissions_factors.Fuel.unique()}')
    
    #calculate emissions version of efficiency by timesing by inverse of emissions factor, then take the inverse of that to get emissions intensity
    emissions_intensity['New_vehicle_efficiency'] = 1/(emissions_intensity['New_vehicle_efficiency'] *(1/emissions_intensity['Emissions factor (MT/PJ)']))

    #Note that its a bit complicated to show the average new vehicle efficiency since we should be weighting it according to the drive type within each vehicle type tha makes up the majority of new vehicles! So we should soon times the efficiency by 1+New_stocks_needed then divide by the sum of (New_stocks_needed +1) for each vehicle type
    emissions_intensity['New_stocks_needed'] = emissions_intensity['New_stocks_needed'].fillna(0)
    
    #group the vehicle types
    emissions_intensity = remap_vehicle_types(config, emissions_intensity, value_col='New_vehicle_efficiency', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'],vehicle_type_mapping_set=vehicle_type_grouping, aggregation_type=('weighted_average', 'New_stocks_needed'))
    
    #calc weighted mean of efficiency by using activity as the weight and, importantly, remove date, scenario
    # emissions_intensity = emissions_intensity[['Date', 'Economy', 'Vehicle Type', 'Scenario','Efficiency']].groupby(['Date','Economy','Scenario','Vehicle Type']).mean().reset_index()
    
    emissions_intensity['ICE_ONLY'] = 'all'
    if extra_ice_line:
        #we want to create a dotted line for each vehicle type that shows the ice efficiency. that is the efficiency when you only consider the ice_d and ice_g vehicles.
        #first, filter to only ice_d and ice_g:
        emissions_intensity_ice = emissions_intensity.loc[emissions_intensity['Drive'].isin(['ice_d', 'ice_g'])].copy()
        #just label ICE_ONLY as True
        emissions_intensity_ice['ICE_ONLY'] = 'ice_only'
        #now concat the two dfs:
        emissions_intensity = pd.concat([emissions_intensity, emissions_intensity_ice])
    
    if extra_bev_line:
        #we want to create a dotted line for each vehicle type that shows the ice efficiency. that is the efficiency when you only consider the ice_d and ice_g vehicles.
        #first, filter to only ice_d and ice_g:
        emissions_intensity_bev = emissions_intensity.loc[emissions_intensity['Drive'].isin(['bev'])].copy()
        #just label ICE_ONLY as True
        emissions_intensity_bev['ICE_ONLY'] = 'bev_only'
        #now concat the two dfs:
        emissions_intensity = pd.concat([emissions_intensity, emissions_intensity_bev])
    
    breakpoint()#im not 100% this is being calculated correctly. It seems that ICE_ONL=all is too high at beginning
    emissions_intensity['New_vehicle_efficiency_weighted'] = emissions_intensity['New_vehicle_efficiency'] * emissions_intensity['New_stocks_needed']
    emissions_intensity = emissions_intensity[['Date', 'Economy', 'Vehicle Type', 'Scenario','New_vehicle_efficiency_weighted', 'New_vehicle_efficiency', 'New_stocks_needed', 'ICE_ONLY']].groupby(['Date','Economy','Scenario','Vehicle Type', 'ICE_ONLY']).sum().reset_index()
    #calculate weighted average
    emissions_intensity['New_vehicle_efficiency'] = emissions_intensity['New_vehicle_efficiency_weighted']/emissions_intensity['New_stocks_needed']#WORRIED ABOUT THE EFFECT OF DIVIDING BY ANY VALUE BETWEEN 0 AND 1 HERE
    emissions_intensity = emissions_intensity.drop(columns=['New_vehicle_efficiency_weighted', 'New_stocks_needed'])

    #rename to New_vehicle_emissions_intensity
    emissions_intensity = emissions_intensity.rename(columns={'New_vehicle_efficiency':'New_vehicle_emissions_intensity'})
    # #simplfiy drive type using remap_drive_types
    # fkm = remap_drive_types(config, fkm, value_col='freight_tonne_km', new_index_cols = ['Economy', 'Date', 'Scenario','Drive'])
    
    #add units (by setting measure to Freight_tonne_km haha)
    emissions_intensity['Measure'] = 'New_vehicle_emissions_intensity'
    
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        emissions_intensity_by_scen = emissions_intensity.loc[(emissions_intensity['Scenario']==scenario)].copy()
        

        for economy in ECONOMY_IDs:
            #filter to economy
            emissions_intensity_by_scen_by_economy = emissions_intensity_by_scen.loc[emissions_intensity_by_scen['Economy']==economy].copy()

            if transport_type == 'all':
                title='New Vehicle emissions intensity by vehicle type (MtC02 per km)'
            elif transport_type.isin(['passenger', 'freight']):
                title='New Vehicle Energy efficiency by vehicle type - {} (MtC02 per km)'.format(transport_type)
            fig = px.line(emissions_intensity_by_scen_by_economy, x='Date', y='New_vehicle_emissions_intensity', color='Vehicle Type',line_dash='ICE_ONLY', title=title, color_discrete_map=colors_dict)#, line_dash='Vehicle Type')

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario][f'new_vehicle_emissions_intensity_timeseries_{transport_type}'] = [fig, title, PLOTTED]
            
            if WRITE_HTML:
                #save to html
                title ='New vehicle emissions intensity - {} - {}'.format(scenario, economy)
                #keep only lpv if it is inthere
                if 'lpv' in emissions_intensity_by_scen_by_economy['Vehicle Type'].unique():
                    emissions_intensity_by_scen_by_economy = emissions_intensity_by_scen_by_economy.loc[emissions_intensity_by_scen_by_economy['Vehicle Type']=='lpv'].copy()
                # fig = px.line(emissions_intensity_by_scen_by_economy, x='Date', y='New_vehicle_emissions_intensity', color='Vehicle Type',line_dash='ICE_ONLY', title=title, color_discrete_map=colors_dict)#, line_dash='Vehicle Type')
                
                # fig.update_yaxes(title='MtC02 per km')
                # #make text a bit bigger
                # fig.update_layout(font_size=30)
                # #make lines slightly thicker
                # fig.update_traces(line=dict(width=10))
                # #drop legend
                # fig.update_layout(showlegend=False)
                # fig.write_html(config.root_dir + config.slash +f'plotting_output\\dashboards\\{economy}\\individual_graphs\\{scenario}_{economy}_new_vehicle_emissions_intensity_timeseries_{transport_type}.html')
                
                write_graph_to_html(config, filename =f'{scenario}_new_vehicle_emissions_intensity_timeseries_{transport_type}.html', graph_type='line', plot_data=emissions_intensity_by_scen_by_economy, economy=economy, x='Date', y='New_vehicle_emissions_intensity', color='Vehicle Type', title=title, line_dash='ICE_ONLY', y_axes_title='MtC02 per km', legend_title='', font_size=30, marker_line_width=2.5, line_width=10, colors_dict=colors_dict)
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(emissions_intensity_by_scen_by_economy['Vehicle Type'].unique().tolist())
    
    return fig_dict, color_preparation_list



############################################################################################################################################################
#MULTI ECONOMY DASHBOARDS ############################################################################################################################################################


def plot_number_of_stocks_FOR_MULTIPLE_ECONOMIES(config, ECONOMY_GROUPING, model_output_detailed_df, colors_dict, transport_type, SALES, AGG_OF_ALL_ECONOMIES, ONLY_AGG_OF_ALL):
    """to help with understanding total expected stocks of vehicles in the future and how they are distributed by vehicle type and how that measures up against capcity, we can plot the number of stocks of vehicles in the future. This will be done for each economy and scenario.""" 
    stocks_9th=model_output_detailed_df.copy()
    
    stocks_9th = stocks_9th.loc[stocks_9th['Medium']=='road'].copy()
    index_cols = ['Economy', 'Date', 'Scenario','Transport Type', 'Vehicle Type', 'Drive']
    stocks_9th = stocks_9th[index_cols +['Stocks', 'Turnover_rate']].copy()
    #shift turnover back by one year so we can calculate the turnover for the previous year, usign the year afters turnover rate (this is jsut because of hwo the data is structured)
    
    if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
        breakpoint()
    index_cols_no_date = index_cols.copy()
    index_cols_no_date.remove('Date')
    stocks_9th['Turnover_rate'] = stocks_9th.groupby(index_cols_no_date)['Turnover_rate'].shift(-1)
    #calcaulte turnover for stocks 9th
    stocks_9th['Turnover'] = stocks_9th['Stocks'] * stocks_9th['Turnover_rate']
    
    #calculate sales. First calcualte stocks after turnover by subtracting turnover from stocks. then calcalte sales by subtracting stocks after turnover from  stocks after turnover  from previous year:
    stocks_9th['stocks_after_turnover'] = stocks_9th['Stocks'] - stocks_9th['Turnover'] 
    
    #sales is the stocks before turnover in this year, minus the stocks after turnover in the previous yea
    stocks_9th['previous_year_stocks_after_turnover'] = stocks_9th.groupby(index_cols_no_date)['stocks_after_turnover'].shift(1)
    stocks_9th['Sales'] = stocks_9th['Stocks'] - stocks_9th['previous_year_stocks_after_turnover']
    
    #melt
    stocks_9th =stocks_9th[['Economy', 'Date', 'Scenario','Transport Type', 'Vehicle Type', 'Drive', 'Stocks', 'Sales']]
    stocks_9th = stocks_9th.melt(id_vars=['Economy', 'Date', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive'], value_vars=['Stocks', 'Sales'], var_name='Measure', value_name='Value')
    #group similar vehicle types:
    stocks = stocks_9th[stocks_9th.Measure=='Stocks'].copy()
    sales = stocks_9th[stocks_9th.Measure=='Sales'].copy()
    
    stocks = remap_vehicle_types(config, stocks, value_col='Value', new_index_cols = ['Economy', 'Date', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive'],vehicle_type_mapping_set='simplified', aggregation_type='sum')
    
    sales = remap_vehicle_types(config, sales, value_col='Value', new_index_cols = ['Economy', 'Date', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive'],vehicle_type_mapping_set='simplified', aggregation_type='sum')
    
    #concat sales and stocks
    stocks = pd.concat([stocks, sales])
    if SALES:
        sales_or_stocks = 'sales'
        stocks = stocks.loc[stocks['Measure']=='Sales'].copy()
    else:
        sales_or_stocks = 'stocks'
        stocks = stocks.loc[stocks['Measure']=='Stocks'].copy()
    
    #################
    if ECONOMY_GROUPING != 'all':
        ECONOMY_GROUPING_DICT = extract_economy_grouping_dict_from_yml(config, ECONOMY_GROUPING)
        stocks_economy_grouping = stocks.copy()
        stocks_economy_grouping['Economy'] = stocks_economy_grouping['Economy'].replace(ECONOMY_GROUPING_DICT)
        stocks_economy_grouping = stocks_economy_grouping.groupby(['Scenario', 'Date', 'Drive','Economy', 'Transport Type','Vehicle Type']).sum().reset_index()
    if AGG_OF_ALL_ECONOMIES or ONLY_AGG_OF_ALL:
        ECONOMY_GROUPING_DICT = extract_economy_grouping_dict_from_yml(config, 'all')
        stocks_all = stocks.copy()
        stocks_all['Economy'] = stocks_all['Economy'].replace(ECONOMY_GROUPING_DICT)
        stocks_all = stocks_all.groupby(['Scenario', 'Date', 'Drive','Economy', 'Transport Type','Vehicle Type']).sum().reset_index()
        
    if ECONOMY_GROUPING != 'all':
        stocks = stocks_economy_grouping.copy()
    if AGG_OF_ALL_ECONOMIES:
        stocks = pd.concat([stocks_all, stocks])
    if ONLY_AGG_OF_ALL:
        stocks = stocks_all.copy()
    facet_col_wrap =7
    #################
        
    for scenario in stocks['Scenario'].unique():
        plot_data = stocks.loc[(stocks['Scenario']==scenario)].copy()       
        # plot_data = plot_data.loc[(plot_data['Drive']=='bev') | (plot_data['Drive']=='fcev')].copy()

        #concat drive and vehicle type
        # plot_data['Drive'] = plot_data['Drive'] + ' ' + plot_data['Vehicle Type']
        
        # Group by 'Drive' and filter out groups where all values are 0
        groups = plot_data.groupby(['Economy', 'Drive',  'Transport Type','Vehicle Type'])
        plot_data = groups.filter(lambda x: not all(x['Value'] == 0))
        
        #sort by date col
        plot_data.sort_values(by=['Date', 'Economy'], inplace=True)
        #############
        # Now plot
        if transport_type == 'passenger':
            title = f'Total {sales_or_stocks} for passenger - {ECONOMY_GROUPING} - {scenario}'

            fig = px.line(plot_data[plot_data['Transport Type'] == 'passenger'], x='Date', y='Value', color='Drive', title=title, line_dash='Vehicle Type', color_discrete_map=colors_dict, facet_col='Economy', facet_col_wrap=facet_col_wrap)
            # Save to HTML
            fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'{sales_or_stocks}_{scenario}_{ECONOMY_GROUPING}_passenger.html'))
        elif transport_type == 'freight':
            title = f'Total {sales_or_stocks} for freight - {ECONOMY_GROUPING} - {scenario}'

            fig = px.line(plot_data[plot_data['Transport Type'] == 'freight'], x='Date', y='Value', color='Drive', title=title, line_dash='Vehicle Type', color_discrete_map=colors_dict, facet_col='Economy', facet_col_wrap=facet_col_wrap)
            fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'{sales_or_stocks}_{scenario}_{ECONOMY_GROUPING}_freight.html'))

        elif transport_type == 'all':
            # Sum up, because 2w are used in freight and passenger:
            plot_data_all = plot_data.groupby(['Scenario', 'Economy', 'Date', 'Drive', 'Vehicle Type']).sum().reset_index()
            title = f'Total {sales_or_stocks} - {ECONOMY_GROUPING} - {scenario}'

            fig = px.line(plot_data_all, x='Date', y='Value', color='Drive', title=title, line_dash='Vehicle Type', color_discrete_map=colors_dict, facet_col='Economy', facet_col_wrap=facet_col_wrap)
            fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'{sales_or_stocks}_{scenario}_{ECONOMY_GROUPING}_all.html'))
        else:
            raise ValueError('transport_type must be either passenger or freight')
    return


def aggregate_sales_and_stock_shares_by_economy_grouping(new_sales_shares_all_plot_drive_shares, stocks, model_output_detailed_df_activity, grouping_dict,INDEX_COLS=['Scenario', 'Economy','Date','Vehicle Type',  'Transport Type', 'Drive']):
    #this si a bit complicated but we will use the activity data to weight the stock shares and calcualte the stock/sales shares for all economies
    
    #We will need to calculate the weighted average sales share for each drive type, since some economies have more stocks than others. But also some economies have lower mileage than otehrs so we should use activity rather than stocks, to show a better reresentatin of howmuch those stocks are used. For this we will jsut use activity rather than sales or stocks as the weighting factor
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares.merge(stocks, on=INDEX_COLS, how='left', suffixes=('_sales_share', '_stocks'))
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares.merge(model_output_detailed_df_activity[INDEX_COLS+['Value']], on=INDEX_COLS, how='left', suffixes=('_sales_share', '_activity'))
    #rename Value to Value_activity
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares.rename(columns={'Value':'Value_activity'})
    
    #####################
    #map according to grouping
    new_sales_shares_all_plot_drive_shares['Economy'] = new_sales_shares_all_plot_drive_shares['Economy'].replace(grouping_dict)
    #####################
    
    #now we can calculate the weighted average sales share
    weighted_value_sales_share = new_sales_shares_all_plot_drive_shares.copy()
    weighted_value_sales_share['Weighted_value_sales_share'] = (weighted_value_sales_share['Value_sales_share'] * weighted_value_sales_share['Value_activity'])
    weighted_value_sales_share = weighted_value_sales_share[INDEX_COLS +['Value_activity', 'Weighted_value_sales_share']].groupby(INDEX_COLS, group_keys=False).sum(numeric_only=True).reset_index()
        
    weighted_value_sales_share['Value'] = weighted_value_sales_share['Weighted_value_sales_share'] / weighted_value_sales_share['Value_activity']
    #since we may be dividing by zero, we will sdet any values that are nan to 0
    weighted_value_sales_share['Value'] = weighted_value_sales_share['Value'].fillna(0)
    weighted_value_sales_share = weighted_value_sales_share[INDEX_COLS+ ['Value']]
    
    #########################################################
    
    #and calculate the stock share in same way
    weighted_value_stock_share = new_sales_shares_all_plot_drive_shares.copy()
    weighted_value_stock_share['Weighted_value_stocks'] = (weighted_value_stock_share['Value_stocks'] * weighted_value_stock_share['Value_activity'])
    
    weighted_value_stock_share = weighted_value_stock_share[INDEX_COLS+['Value_activity', 'Weighted_value_stocks']].groupby(INDEX_COLS, group_keys=False).sum(numeric_only=True).reset_index()
    
    weighted_value_stock_share['Value'] = weighted_value_stock_share['Weighted_value_stocks'] / weighted_value_stock_share['Value_activity']
    #since we may be dividing by zero, we will sdet any values that are nan to 0
    weighted_value_stock_share['Value'] = weighted_value_stock_share['Value'].fillna(0)
    weighted_value_stock_share = weighted_value_stock_share[INDEX_COLS+['Value']]
    
    return weighted_value_sales_share, weighted_value_stock_share

def plot_share_of_vehicle_type_by_transport_type_FOR_MULTIPLE_ECONOMIES(config, ECONOMY_GROUPING, new_sales_shares_all_plot_drive_shares_df, stocks_df, model_output_detailed_df, colors_dict, share_of_transport_type_type, AGG_OF_ALL_ECONOMIES, ONLY_AGG_OF_ALL, INCLUDE_OTHER_DRIVES=True):
    """a copy of similarly named funciton but made to only plot this chart for the named economies without other charts in the same dashboard"""
    #This data is in terms of transport type, so will need to normalise it to vehicle type by summing up the shares for each vehicle type and dividing individual shares by their sum
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares_df.copy()
    stocks = stocks_df.copy()
    
    stocks, new_sales_shares_all_plot_drive_shares = remap_stocks_and_sales_based_on_economy(config, stocks, new_sales_shares_all_plot_drive_shares)
    #do the same for model_output_detailed_df[['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive']] where Measure=='Activity'
    #this is a bit hacky but we can just use the same function as for stocks
    model_output_detailed_df_activity = model_output_detailed_df[['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive', 'Activity']].copy()
    #renaem activity to value
    model_output_detailed_df_activity = model_output_detailed_df_activity.rename(columns={'Activity':'Value'})
    model_output_detailed_df_activity, model_output_detailed_df_activity1 = remap_stocks_and_sales_based_on_economy(config, model_output_detailed_df_activity, model_output_detailed_df_activity)
    
    new_sales_shares_all_plot_drive_shares['Value'] = new_sales_shares_all_plot_drive_shares.groupby(['Date','Economy', 'Scenario', 'Transport Type', 'Vehicle Type'], group_keys=False)['Value'].transform(lambda x: x/x.sum())
    
    #now calucalte share of total stocks as a proportion like the sales share
    # stocks['Value'] = stocks.groupby(['Scenario', 'Economy', 'Date', 'Transport Type','Vehicle Type'], group_keys=False)['Value'].apply(lambda x: x/x.sum(numeric_only=True))
    # Assuming 'stocks' is your DataFrame and 'Value' is the column containing the stock values
    stocks['Value'] = stocks.groupby(['Scenario', 'Economy', 'Date', 'Transport Type','Vehicle Type'])['Value'].apply(lambda x: x / x.sum()).reset_index(drop=True)
    
    # model_output_detailed_df_activity['Value'] = model_output_detailed_df_activity.groupby(['Date','Economy', 'Scenario', 'Transport Type', 'Vehicle Type'], group_keys=False)['Value'].transform(lambda x: x/x.sum())
    #####################
    extra_identifier = ''
    if ECONOMY_GROUPING != 'all':
        ECONOMY_GROUPING_DICT = extract_economy_grouping_dict_from_yml(config, ECONOMY_GROUPING)
        weighted_value_sales_share_economy_grouping, weighted_value_stock_share_economy_grouping = aggregate_sales_and_stock_shares_by_economy_grouping(new_sales_shares_all_plot_drive_shares, stocks, model_output_detailed_df_activity, grouping_dict=ECONOMY_GROUPING_DICT)
    if AGG_OF_ALL_ECONOMIES or ONLY_AGG_OF_ALL:
        ECONOMY_GROUPING_DICT = extract_economy_grouping_dict_from_yml(config, 'all')
        weighted_value_sales_share, weighted_value_stock_share = aggregate_sales_and_stock_shares_by_economy_grouping(new_sales_shares_all_plot_drive_shares, stocks, model_output_detailed_df_activity, grouping_dict=ECONOMY_GROUPING_DICT)
        
    if ECONOMY_GROUPING != 'all':
        new_sales_shares_all_plot_drive_shares = pd.concat([new_sales_shares_all_plot_drive_shares, weighted_value_sales_share_economy_grouping])
        stocks = pd.concat([stocks, weighted_value_stock_share_economy_grouping])
        extra_identifier += f'_{ECONOMY_GROUPING}'
    if AGG_OF_ALL_ECONOMIES:
        new_sales_shares_all_plot_drive_shares = pd.concat([new_sales_shares_all_plot_drive_shares, weighted_value_sales_share])
        stocks = pd.concat([stocks, weighted_value_stock_share])
    if ONLY_AGG_OF_ALL:
        new_sales_shares_all_plot_drive_shares = weighted_value_sales_share.copy()
        stocks = weighted_value_stock_share.copy()
        extra_identifier += '_agg'
    #####################
    new_sales_shares_all_plot_drive_shares['line_dash'] = 'sales'
    stocks['line_dash'] = 'stocks'
    
    for scenario in new_sales_shares_all_plot_drive_shares['Scenario'].unique():
        new_sales_shares_all_plot_drive_shares_scenario = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Scenario']==scenario)]
        stocks_scen = stocks.loc[(stocks['Scenario']==scenario)].copy()
        ###
        
        #then concat the two dataframes
        new_sales_shares_all_plot_drive_shares_scenario = pd.concat([new_sales_shares_all_plot_drive_shares_scenario, stocks_scen])
        
        #times shares by 100
        new_sales_shares_all_plot_drive_shares_scenario['Value'] = new_sales_shares_all_plot_drive_shares_scenario['Value']*100
            
        # #also plot the data like the iea does. So plot the data for 2022 and previous, then plot for the follwoign eyars: [2025, 2030, 2035, 2040, 2050, 2060]. This helps to keep the plot clean too
        # plot_data = plot_data.apply(lambda x: x if x['Date'] <= 2022 or x['Date'] in [2025, 2030, 2035, 2040, 2050, 2060, 2070, 2080,2090, 2100] else 0, axis=1)
        #drop all drives except bev and fcev
        plot_data = new_sales_shares_all_plot_drive_shares_scenario.copy()
        if INCLUDE_OTHER_DRIVES:
            mapping = {'bev':'bev', 'fcev':'fcev', 'phev_g':'phev', 'phev_d':'phev', 'cng':'gas', 'lpg':'gas'}
            plot_data['Drive'] = plot_data['Drive'].replace(mapping)
            plot_data = plot_data.loc[(plot_data['Drive']=='bev') | (plot_data['Drive']=='fcev') | (plot_data['Drive']=='gas') | (plot_data['Drive']=='phev')].copy()
        else:
            plot_data = plot_data.loc[(plot_data['Drive']=='bev') | (plot_data['Drive']=='fcev')].copy()

        #concat drive and vehicle type
        plot_data['Drive'] = plot_data['Drive'] + ' ' + plot_data['Vehicle Type']
        # Group by 'Drive' and filter out groups where all values are 0
        groups = plot_data.groupby(['Economy', 'Drive', 'line_dash'])
        plot_data = groups.filter(lambda x: not all(x['Value'] == 0))
        
        #sort by date col
        plot_data.sort_values(by=['Date', 'Economy'], inplace=True)
            
        #############
        # Now plot
        if share_of_transport_type_type == 'passenger':
            title = f'Shares for passenger (%) - {ECONOMY_GROUPING} - {scenario}'

            fig = px.line(plot_data[plot_data['Transport Type'] == 'passenger'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict, facet_col='Economy', facet_col_wrap=7)
            # Save to HTML
            fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'shares_of_vehicle_type_by_transport_type_{scenario}_{ECONOMY_GROUPING}_passenger{extra_identifier}.html'))
        elif share_of_transport_type_type == 'freight':
            title = f'Shares for freight (%) - {ECONOMY_GROUPING} - {scenario}'

            fig = px.line(plot_data[plot_data['Transport Type'] == 'freight'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict, facet_col='Economy', facet_col_wrap=7)
            fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'shares_of_vehicle_type_by_transport_type_{scenario}_{ECONOMY_GROUPING}_freight{extra_identifier}.html'))

        elif share_of_transport_type_type == 'all':
            # Sum up, because 2w are used in freight and passenger:
            plot_data_all = plot_data.groupby(['Scenario', 'Economy', 'Date', 'Drive', 'line_dash']).sum().reset_index()
            title = f'Sales and stock shares (%) - {ECONOMY_GROUPING} - {scenario}'

            fig = px.line(plot_data_all, x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict, facet_col='Economy', facet_col_wrap=7)
            fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'shares_of_vehicle_type_by_transport_type_{scenario}_{ECONOMY_GROUPING}_all{extra_identifier}.html'))
        else:
            raise ValueError('share_of_transport_type_type must be either passenger or freight')
    return
        

def plot_share_transport_type_FOR_MULTIPLE_ECONOMIES(config, ECONOMY_GROUPING, new_sales_shares_all_plot_drive_shares_df, stocks_df, model_output_detailed_df, colors_dict, share_of_transport_type_type, AGG_OF_ALL_ECONOMIES, ONLY_AGG_OF_ALL, INCLUDE_OTHER_DRIVES=True):
    """a copy of above funciton but made to only plot by transport type (not including vehicle type) for the named economies without other charts in the same dashboard"""
    #This data is in terms of transport type, so will need to normalise it to vehicle type by summing up the shares for each vehicle type and dividing individual shares by their sum
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares_df.copy()
    stocks = stocks_df.copy()
    
    stocks = remap_vehicle_types(config, stocks, value_col='Value', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'],vehicle_type_mapping_set='simplified')
    new_sales_shares_all_plot_drive_shares = remap_vehicle_types(config, new_sales_shares_all_plot_drive_shares, value_col='Value', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'],vehicle_type_mapping_set='simplified')
    #do the same for model_output_detailed_df[['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive']] where Measure=='Activity'
    #this is a bit hacky but we can just use the same function as for stocks
    model_output_detailed_df_activity = model_output_detailed_df[['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive', 'Activity']].copy()
    #renaem activity to value
    model_output_detailed_df_activity = model_output_detailed_df_activity.rename(columns={'Activity':'Value'})
    
    model_output_detailed_df_activity = remap_vehicle_types(config, model_output_detailed_df_activity, value_col='Value', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'],vehicle_type_mapping_set='simplified')
    
    new_sales_shares_all_plot_drive_shares['Value'] = new_sales_shares_all_plot_drive_shares.groupby(['Date','Economy', 'Scenario', 'Transport Type'], group_keys=False)['Value'].transform(lambda x: x/x.sum())
    
    #now calucalte share of total stocks as a proportion like the sales share
    # stocks['Value'] = stocks.groupby(['Scenario', 'Economy', 'Date', 'Transport Type','Vehicle Type'], group_keys=False)['Value'].apply(lambda x: x/x.sum(numeric_only=True))
    # Assuming 'stocks' is your DataFrame and 'Value' is the column containing the stock values
    stocks['Value'] = stocks.groupby(['Scenario', 'Economy', 'Date', 'Transport Type'])['Value'].apply(lambda x: x / x.sum()).reset_index(drop=True)
    
    #####################
    extra_identifier = ''
    if ECONOMY_GROUPING != 'all':
        ECONOMY_GROUPING_DICT = extract_economy_grouping_dict_from_yml(config, ECONOMY_GROUPING)
        weighted_value_sales_share_economy_grouping, weighted_value_stock_share_economy_grouping = aggregate_sales_and_stock_shares_by_economy_grouping(new_sales_shares_all_plot_drive_shares, stocks, model_output_detailed_df_activity, grouping_dict=ECONOMY_GROUPING_DICT, INDEX_COLS=['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive'])
    if AGG_OF_ALL_ECONOMIES or ONLY_AGG_OF_ALL:
        ECONOMY_GROUPING_DICT = extract_economy_grouping_dict_from_yml(config, 'all')
        weighted_value_sales_share, weighted_value_stock_share = aggregate_sales_and_stock_shares_by_economy_grouping(new_sales_shares_all_plot_drive_shares, stocks, model_output_detailed_df_activity, grouping_dict=ECONOMY_GROUPING_DICT, INDEX_COLS=['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive'])
        
    if ECONOMY_GROUPING != 'all':
        new_sales_shares_all_plot_drive_shares = weighted_value_sales_share_economy_grouping.copy()
        stocks =weighted_value_stock_share_economy_grouping.copy()
        extra_identifier += f'_{ECONOMY_GROUPING}'
    if AGG_OF_ALL_ECONOMIES:
        new_sales_shares_all_plot_drive_shares = pd.concat([new_sales_shares_all_plot_drive_shares, weighted_value_sales_share])
        stocks = pd.concat([stocks, weighted_value_stock_share])
    if ONLY_AGG_OF_ALL:
        new_sales_shares_all_plot_drive_shares = weighted_value_sales_share.copy()
        stocks = weighted_value_stock_share.copy()
        extra_identifier += '_agg'
    #####################
    
    new_sales_shares_all_plot_drive_shares['line_dash'] = 'sales'
    stocks['line_dash'] = 'stocks'
    
    for scenario in new_sales_shares_all_plot_drive_shares['Scenario'].unique():
        new_sales_shares_all_plot_drive_shares_scenario = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Scenario']==scenario)]
        stocks_scen = stocks.loc[(stocks['Scenario']==scenario)].copy()
        ###
        
        #then concat the two dataframes
        new_sales_shares_all_plot_drive_shares_scenario = pd.concat([new_sales_shares_all_plot_drive_shares_scenario, stocks_scen])
        
        #times shares by 100
        new_sales_shares_all_plot_drive_shares_scenario['Value'] = new_sales_shares_all_plot_drive_shares_scenario['Value']*100
            
        # #also plot the data like the iea does. So plot the data for 2022 and previous, then plot for the follwoign eyars: [2025, 2030, 2035, 2040, 2050, 2060]. This helps to keep the plot clean too
        # plot_data = plot_data.apply(lambda x: x if x['Date'] <= 2022 or x['Date'] in [2025, 2030, 2035, 2040, 2050, 2060, 2070, 2080,2090, 2100] else 0, axis=1)
        #drop all drives except bev and fcev
        plot_data = new_sales_shares_all_plot_drive_shares_scenario.copy()
        if INCLUDE_OTHER_DRIVES:
            mapping = {'bev':'bev', 'fcev':'fcev', 'phev_g':'phev', 'phev_d':'phev', 'cng':'gas', 'lpg':'gas'}
            plot_data['Drive'] = plot_data['Drive'].replace(mapping)
            plot_data = plot_data.loc[(plot_data['Drive']=='bev') | (plot_data['Drive']=='fcev') | (plot_data['Drive']=='gas') | (plot_data['Drive']=='phev')].copy()
        else:
            plot_data = plot_data.loc[(plot_data['Drive']=='bev') | (plot_data['Drive']=='fcev')].copy()

        # Group by 'Drive' and filter out groups where all values are 0
        groups = plot_data.groupby(['Economy', 'Drive', 'line_dash'])
        plot_data = groups.filter(lambda x: not all(x['Value'] == 0))
        
        #sort by date col
        plot_data.sort_values(by=['Date', 'Economy'], inplace=True)
        if ONLY_AGG_OF_ALL and AGG_OF_ALL_ECONOMIES:
            extra_identifier = '_agg'
        else:
            extra_identifier = ''
        #############
        #now plot
        if share_of_transport_type_type == 'passenger':
            title = f'Shares for passenger (%) - {ECONOMY_GROUPING} - {scenario}'

            fig = px.line(plot_data[plot_data['Transport Type']=='passenger'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict, facet_col='Economy', facet_col_wrap=7)
            #save to html
            fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'shares_of_transport_type_{scenario}_{ECONOMY_GROUPING}_passenger{extra_identifier}.html'))
        elif share_of_transport_type_type == 'freight':
            title = f'Shares for freight (%) - {ECONOMY_GROUPING} - {scenario}'

            fig = px.line(plot_data[plot_data['Transport Type']=='freight'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict, facet_col='Economy', facet_col_wrap=7)
            fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'shares_of_transport_type_{scenario}_{ECONOMY_GROUPING}_freight{extra_identifier}.html'))

        elif share_of_transport_type_type == 'all':
            # sum up, because 2w are used in freight and passenger:
            plot_data_all = plot_data.groupby(['Scenario', 'Economy', 'Date', 'Drive','line_dash']).sum().reset_index()
            title = f'Sales and stock shares (%) - {ECONOMY_GROUPING} - {scenario}'

            fig = px.line(plot_data_all, x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict, facet_col='Economy', facet_col_wrap=7)
            fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'shares_of_transport_type_{scenario}_{ECONOMY_GROUPING}_all{extra_identifier}.html'))
        else:
            raise ValueError('share_of_transport_type_type must be either passenger or freight')
    return
        
def plot_supply_side_fuel_mixing_FOR_MULTIPLE_ECONOMIES(config, ECONOMY_GROUPING, supply_side_fuel_mixing_df, supply_side_fuel_mixing_output, colors_dict, AGG_OF_ALL_ECONOMIES, ONLY_AGG_OF_ALL):
    """a copy of similarly named funciton but made to only plot this chart for the named economies without other charts in the same dashboard

    Args:
        ECONOMY_IDs (_type_): _description_
        ECONOMY_GROUPING (_type_): _description_
        supply_side_fuel_mixing_df (_type_): _description_
        fig_dict (_type_): _description_
        color_preparation_list (_type_): _description_
        colors_dict (_type_): _description_

    Returns:
        _type_: _description_
    """
    PLOTTED=True
    #plot supply side fuel mixing
    supply_side_fuel_mixing = supply_side_fuel_mixing_df.copy()
    #average out the supply side fuel mixing by economy, scenario and new fuel, so that we have the average share of each fuel type that is mixed into another fuel type (note that this isnt weighted by the amount of fuel mixed in, just the share of the fuel that is mixed in... its a safe asumption given that every new fuel should be mixed in with similar shares
    supply_side_fuel_mixing= supply_side_fuel_mixing[['Date', 'Economy','Scenario', 'New_fuel' ,'Supply_side_fuel_share']].groupby(['Date', 'Economy','Scenario', 'New_fuel']).mean().reset_index()
    #round the Supply_side_fuel_share column to 2dp
    supply_side_fuel_mixing['Supply_side_fuel_share'] = supply_side_fuel_mixing['Supply_side_fuel_share']*100
    #supply side mixing is just the percent of a fuel type that is mixed into another fuel type, eg. 5% biodiesel mixed into diesel. We can use the concat of Fuel and New fuel cols to show the data:
    supply_side_fuel_mixing['Fuel mix'] = supply_side_fuel_mixing['New_fuel']# supply_side_fuel_mixing_plot['Fuel'] + ' mixed with ' + 
    #actually i changed that because it was too long. should be obivous that it's mixed with the fuel in the Fuel col (eg. biodesel mixed with diesel)
    
    #################
    if ECONOMY_GROUPING != 'all':
        ECONOMY_GROUPING_DICT = extract_economy_grouping_dict_from_yml(config, ECONOMY_GROUPING)
        supply_side_fuel_mixing_output_economy_grouping = supply_side_fuel_mixing_output.copy()
        supply_side_fuel_mixing_output_economy_grouping['Economy'] = supply_side_fuel_mixing_output_economy_grouping['Economy'].replace(ECONOMY_GROUPING_DICT)
        supply_side_fuel_mixing_output_economy_grouping = supply_side_fuel_mixing_output_economy_grouping.rename(columns={'Fuel':'New_fuel'})
        supply_side_fuel_mixing_output_economy_grouping = supply_side_fuel_mixing_output_economy_grouping.groupby(['Scenario', 'Date','New_fuel', 'Economy']).sum().reset_index().copy()
        supply_side_fuel_mixing_output_economy_grouping['Supply_side_fuel_share'] = (supply_side_fuel_mixing_output_economy_grouping['Energy']/supply_side_fuel_mixing_output_economy_grouping['original_energy'])*100
    if AGG_OF_ALL_ECONOMIES or ONLY_AGG_OF_ALL:
        ECONOMY_GROUPING_DICT = extract_economy_grouping_dict_from_yml(config, 'all')
        supply_side_fuel_mixing_all = supply_side_fuel_mixing_output.copy()
        supply_side_fuel_mixing_all['Economy'] = supply_side_fuel_mixing_all['Economy'].replace(ECONOMY_GROUPING_DICT)
        supply_side_fuel_mixing_all = supply_side_fuel_mixing_all.rename(columns={'Fuel':'New_fuel'})
        supply_side_fuel_mixing_all = supply_side_fuel_mixing_all.groupby(['Scenario', 'Date','New_fuel', 'Economy']).sum().reset_index().copy()
        supply_side_fuel_mixing_all['Supply_side_fuel_share'] = (supply_side_fuel_mixing_all['Energy']/supply_side_fuel_mixing_all['original_energy'])*100
        
    if ECONOMY_GROUPING != 'all':
        supply_side_fuel_mixing = supply_side_fuel_mixing_output_economy_grouping.copy()
    if AGG_OF_ALL_ECONOMIES:
        supply_side_fuel_mixing = pd.concat([supply_side_fuel_mixing_all, supply_side_fuel_mixing])
    if ONLY_AGG_OF_ALL:
        supply_side_fuel_mixing = supply_side_fuel_mixing_all.copy()
    #################
        
    #add units (by setting measure to Freight_tonne_km haha)
    supply_side_fuel_mixing['Measure'] = 'Fuel_mixing'
    #add units
    supply_side_fuel_mixing['Unit'] = '%'
    
    #sort by date and economy
    supply_side_fuel_mixing = supply_side_fuel_mixing.sort_values(by=['Date', 'Economy'])
        
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        supply_side_fuel_mixing_plot_scenario = supply_side_fuel_mixing.loc[supply_side_fuel_mixing['Scenario']==scenario].copy()
        
        supply_side_fuel_mixing_plot_scenario = supply_side_fuel_mixing_plot_scenario.groupby(['New_fuel']).filter(lambda x: not all(x['Supply_side_fuel_share'] == 0))
        
        if ONLY_AGG_OF_ALL and AGG_OF_ALL_ECONOMIES:
            extra_identifier = '_agg'
        else:
            extra_identifier=''
        title = 'Supply side fuel mixing for ' + scenario + ' scenario - ' + ECONOMY_GROUPING + ' - ({})'.format(supply_side_fuel_mixing_plot_scenario['Unit'].unique()[0])
        fig = px.line(supply_side_fuel_mixing_plot_scenario, x="Date", y="Supply_side_fuel_share", color='New_fuel',  title=title, color_discrete_map=colors_dict, facet_col='Economy', facet_col_wrap=7)

        #add units to y col
        # title_text = 'Supply side fuel mixing ({})'.format(supply_side_fuel_mixing_plot_scenario['Unit'].unique()[0])
        # fig.update_yaxes(title_text=title_text)#not working for some reason

        #save to html
        fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'supply_side_fuel_mixing_{scenario}_{ECONOMY_GROUPING}{extra_identifier}.html'))

    return 

###################################################
def energy_use_by_fuel_type_FOR_MULTIPLE_ECONOMIES(config, ECONOMY_GROUPING, energy_output_for_outlook_data_system_tall_df, colors_dict, transport_type, medium, INDEPENDENT_AXIS, AGG_OF_ALL_ECONOMIES, ONLY_AGG_OF_ALL):
    PLOTTED=True
    energy_output_for_outlook_data_system_tall = energy_output_for_outlook_data_system_tall_df.copy()
    if medium == 'road':
        energy_output_for_outlook_data_system_tall = energy_output_for_outlook_data_system_tall.loc[(energy_output_for_outlook_data_system_tall['Medium']=='road')].copy()
    #load in data and recreate plot, as created in all_economy_graphs
    #loop through scenarios and grab the data for each scenario:
    
    energy_use_by_fuel_type= energy_output_for_outlook_data_system_tall[['Economy', 'Scenario','Date', 'Fuel', 'Transport Type','Energy']].groupby(['Economy', 'Scenario','Date','Transport Type', 'Fuel']).sum().reset_index().copy()
    energy_use_by_fuel_type['Measure'] = 'Energy'
    energy_use_by_fuel_type['Unit'] = energy_use_by_fuel_type['Measure'].map(config.measure_to_unit_concordance_dict)
    
    #################
    extra_identifier= '' 
    if ECONOMY_GROUPING != 'all':
        ECONOMY_GROUPING_DICT = extract_economy_grouping_dict_from_yml(config, ECONOMY_GROUPING)
        energy_use_by_fuel_type_economy_grouping = energy_use_by_fuel_type.copy()
        energy_use_by_fuel_type_economy_grouping['Economy'] = energy_use_by_fuel_type_economy_grouping['Economy'].replace(ECONOMY_GROUPING_DICT)
        energy_use_by_fuel_type_economy_grouping = energy_use_by_fuel_type_economy_grouping.groupby(['Scenario','Economy', 'Date', 'Transport Type', 'Fuel', 'Measure', 'Unit']).sum().reset_index()
    if AGG_OF_ALL_ECONOMIES or ONLY_AGG_OF_ALL:
        ECONOMY_GROUPING_DICT = extract_economy_grouping_dict_from_yml(config, 'all')
        energy_use_by_fuel_type_all = energy_use_by_fuel_type.copy()
        energy_use_by_fuel_type_all['Economy'] = energy_use_by_fuel_type_all['Economy'].replace(ECONOMY_GROUPING_DICT)
        energy_use_by_fuel_type_all = energy_use_by_fuel_type_all.groupby(['Scenario','Economy', 'Date', 'Transport Type', 'Fuel', 'Measure', 'Unit']).sum().reset_index()
    if ECONOMY_GROUPING != 'all':
        energy_use_by_fuel_type = energy_use_by_fuel_type_economy_grouping
        extra_identifier += f'_{ECONOMY_GROUPING}'
    if AGG_OF_ALL_ECONOMIES:
        energy_use_by_fuel_type = pd.concat([energy_use_by_fuel_type_all, energy_use_by_fuel_type])
    if ONLY_AGG_OF_ALL: 
        energy_use_by_fuel_type = energy_use_by_fuel_type_all.copy()
        extra_identifier='_agg'
    #################
    
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        energy_use_by_fuel_type_scen = energy_use_by_fuel_type.loc[(energy_use_by_fuel_type['Scenario']==scenario)].copy()
    
        # Group by 'Fuel' and filter out groups where all 'Energy' values are 0
        groups = energy_use_by_fuel_type_scen.groupby('Fuel')
        energy_use_by_fuel_type_scen = groups.filter(lambda x: not all(x['Energy'] == 0))
        
        # calculate total 'Energy' for each 'Fuel' 
        total_energy_per_fuel = energy_use_by_fuel_type_scen.groupby('Fuel')['Energy'].sum()
        
        # Create an ordered category of 'Fuel' labels sorted by total 'Energy'. THIS helps make plot easyer to read
        energy_use_by_fuel_type_scen['Fuel'] = pd.Categorical(
            energy_use_by_fuel_type_scen['Fuel'],
            categories = total_energy_per_fuel.sort_values(ascending=False).index,
            ordered=True
        )

        # Now sort the DataFrame by the 'Fuel' column:
        energy_use_by_fuel_type_scen.sort_values(by='Fuel', inplace=True)

        if transport_type=='passenger':
            #now plot
            #add units to y col
            if medium == 'road':
                title_text = 'Road energy by Fuel {} {} ({})'.format(scenario, transport_type, energy_use_by_fuel_type_scen['Unit'].unique()[0])
            else:
                title_text = 'Energy by Fuel {} {} ({})'.format(scenario, transport_type, energy_use_by_fuel_type_scen['Unit'].unique()[0])
                
            fig = px.area(energy_use_by_fuel_type_scen.loc[energy_use_by_fuel_type_scen['Transport Type']=='passenger'], x='Date', y='Energy', color='Fuel', title=title_text, color_discrete_map=colors_dict, facet_col='Economy', facet_col_wrap=7)
            fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'energy_use_by_fuel_type_{scenario}_{ECONOMY_GROUPING}_{transport_type}_{medium}{extra_identifier}.html'))

            if INDEPENDENT_AXIS and not ONLY_AGG_OF_ALL:
                fig.update_yaxes(matches=None)
                fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
                # Write to HTML with independent axis
                fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'energy_use_by_fuel_type_{scenario}_{ECONOMY_GROUPING}_{transport_type}_{medium}_indep_axis.html'))   
            
        elif transport_type == 'freight':
            #now plot
            if medium == 'road':
                title_text = 'Road energy by Fuel {} {} ({})'.format(scenario, transport_type, energy_use_by_fuel_type_scen['Unit'].unique()[0])
            else:
                title_text = 'Energy by Fuel {} {} ({})'.format(scenario, transport_type, energy_use_by_fuel_type_scen['Unit'].unique()[0])
            
            fig = px.area(energy_use_by_fuel_type_scen.loc[energy_use_by_fuel_type_scen['Transport Type']=='freight'], x='Date', y='Energy', color='Fuel', title=title_text, color_discrete_map=colors_dict, facet_col='Economy', facet_col_wrap=7)
            
            fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'energy_use_by_fuel_type_{scenario}_{ECONOMY_GROUPING}_{transport_type}_{medium}{extra_identifier}.html'))

            if INDEPENDENT_AXIS and not ONLY_AGG_OF_ALL:
                fig.update_yaxes(matches=None)
                fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
                # Write to HTML with independent axis
                fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'energy_use_by_fuel_type_{scenario}_{ECONOMY_GROUPING}_{transport_type}_{medium}_indep_axis.html'))
            
        elif transport_type == 'all':
            #sum across transport types
            #add units to y col
            if medium == 'road':
                title_text = 'Road energy by Fuel - {} - ({})'.format(scenario, energy_use_by_fuel_type_scen['Unit'].unique()[0])
            else:
                title_text = 'Energy by Fuel - {} - ({})'.format(scenario, energy_use_by_fuel_type_scen['Unit'].unique()[0])
            energy_use_by_fuel_type_scen = energy_use_by_fuel_type_scen.groupby(['Economy', 'Date', 'Fuel','Unit']).sum(numeric_only =True).reset_index()
            #now plot
            fig = px.area(energy_use_by_fuel_type_scen, x='Date', y='Energy', color='Fuel', title=title_text, color_discrete_map=colors_dict, facet_col='Economy', facet_col_wrap=7)
            
            fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'energy_use_by_fuel_type_{scenario}_{ECONOMY_GROUPING}_{transport_type}_{medium}{extra_identifier}.html'))

            if INDEPENDENT_AXIS and not ONLY_AGG_OF_ALL:
                fig.update_yaxes(matches=None)
                fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
                # Write to HTML with independent axis
                fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'energy_use_by_fuel_type_{scenario}_{ECONOMY_GROUPING}_{transport_type}_{medium}_indep_axis.html'))
        else:
            raise ValueError('transport_type must be passenger, all or freight')

def emissions_by_fuel_type_FOR_MULTIPLE_ECONOMIES(config, ECONOMY_GROUPING, emissions_factors, model_output_with_fuels_df, colors_dict, transport_type, INDEPENDENT_AXIS, AGG_OF_ALL_ECONOMIES, USE_AVG_GENERATION_EMISSIONS_FACTOR=False, ONLY_AGG_OF_ALL=False):
    PLOTTED=True
    model_output_with_fuels = model_output_with_fuels_df.copy()
    #TEMP #WHERE TRANSPORT TYPE IS FREIGHT or medium is not road, SET THE electricty yse to 0. This is so we can test what the effect of electriicyt is 
    # model_output_with_fuels.loc[(model_output_with_fuels['Transport Type']=='freight') | (model_output_with_fuels['Medium']!='road') & (model_output_with_fuels['Fuel']=='17_electricity'), 'Energy'] = 0
    #load in data and recreate plot, as created in all_economy_graphs
    #loop through scenarios and grab the data for each scenario:
    model_output_with_fuels_sum= model_output_with_fuels[['Economy', 'Scenario','Date', 'Fuel', 'Transport Type','Energy']].groupby(['Economy', 'Scenario','Date','Transport Type', 'Fuel']).sum().reset_index().copy()
    
    #rename fuel_code to fuel in emissions_factors
    emissions_factors = emissions_factors.rename(columns={'fuel_code':'Fuel'})
    #join on the emissions factors (has the cols fuel_code,	Emissions factor (MT/PJ))
    model_output_with_fuels_sum = model_output_with_fuels_sum.merge(emissions_factors, how='left', on='Fuel')
    if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
        breakpoint()#wharts happening with USA data here? it seems to go to 0 after 2 years
    if USE_AVG_GENERATION_EMISSIONS_FACTOR:
        gen='_gen'
        #pull in the 8th outlook emissions factors by year, then use that to claculate the emissions for electricity.
        emissions_factor_elec = pd.read_csv(os.path.join(config.root_dir, 'input_data', 'from_8th', 'outlook_8th_emissions_factors_with_electricity.csv'))#maunsell\github\aperc-emissions\output_data\outlook_8th_emissions_factors_with_electricity.csv
        #extract the emissions factor for elctricity for each economy
        emissions_factor_elec = emissions_factor_elec[emissions_factor_elec.fuel_code=='17_electricity'].copy()
        #rename Carbon Neutral Scenario to Target
        emissions_factor_elec['Scenario'] = emissions_factor_elec['Scenario'].replace('Carbon Neutral', 'Target')
        #capitalise the cols
        emissions_factor_elec.columns = [x.capitalize() for x in emissions_factor_elec.columns]
        #rename fuel code to fuel
        emissions_factor_elec = emissions_factor_elec.rename(columns={'Fuel_code':'Fuel', 'Year':'Date', 'Emissions factor (mt/pj)':'Emissions factor (MT/PJ)'})
        #merge on economy and year and fuel code
        model_output_with_fuels_sum = model_output_with_fuels_sum.merge(emissions_factor_elec, on=['Date', 'Economy', 'Scenario', 'Fuel'], how='left', indicator=True, suffixes=('', '_elec'))
        #where indicator is both, use the new value
        model_output_with_fuels_sum['Emissions factor (MT/PJ)'] = np.where(model_output_with_fuels_sum['_merge']=='both', model_output_with_fuels_sum['Emissions factor (MT/PJ)_elec'], model_output_with_fuels_sum['Emissions factor (MT/PJ)'])
        #fill any missing values using ffill after sorting by date and grouping by 'Economy', 'Scenario','Date', 'Fuel', 'Transport Type'
        model_output_with_fuels_sum['Emissions factor (MT/PJ)'] = model_output_with_fuels_sum.sort_values(by='Date').groupby(['Economy', 'Scenario','Date','Transport Type', 'Fuel'])['Emissions factor (MT/PJ)'].fillna(method='ffill')
        #drop columns
        model_output_with_fuels_sum = model_output_with_fuels_sum.drop(columns=['Emissions factor (MT/PJ)_elec', '_merge'])
    #identify where there are no emissions factors:
    missing_emissions_factors = model_output_with_fuels_sum.loc[model_output_with_fuels_sum['Emissions factor (MT/PJ)'].isna()].copy()
    if len(missing_emissions_factors)>0:
        breakpoint()
        time.sleep(1)
        raise ValueError(f'missing emissions factors, {missing_emissions_factors.Fuel.unique()}')
    
    #calculate emissions:
    model_output_with_fuels_sum['Emissions'] = model_output_with_fuels_sum['Energy'] * model_output_with_fuels_sum['Emissions factor (MT/PJ)']

    model_output_with_fuels_sum['Measure'] = 'Emissions'
    model_output_with_fuels_sum['Unit'] = 'Mt CO2'
    
    #set y axis to be the maximum sum of all values for each economy and scenario:
    y_axis_max = model_output_with_fuels_sum.groupby(['Economy', 'Scenario'])['Emissions'].sum().max() * 1.1
    #################################
    extra_identifier = ''
    if ECONOMY_GROUPING != 'all':
        ECONOMY_GROUPING_DICT = extract_economy_grouping_dict_from_yml(config, ECONOMY_GROUPING)
        model_output_with_fuels_sum_economy_grouping = model_output_with_fuels_sum.copy()
        model_output_with_fuels_sum_economy_grouping['Economy'] = model_output_with_fuels_sum_economy_grouping['Economy'].replace(ECONOMY_GROUPING_DICT)
        model_output_with_fuels_sum_economy_grouping = model_output_with_fuels_sum_economy_grouping.groupby(['Scenario', 'Date', 'Economy', 'Transport Type', 'Fuel', 'Measure', 'Unit']).sum().reset_index()
    if AGG_OF_ALL_ECONOMIES or ONLY_AGG_OF_ALL:
        ECONOMY_GROUPING_DICT = extract_economy_grouping_dict_from_yml(config, 'all')
        model_output_with_fuels_sum_all = model_output_with_fuels_sum.copy()
        model_output_with_fuels_sum_all['Economy'] = model_output_with_fuels_sum_all['Economy'].replace(ECONOMY_GROUPING_DICT)
        model_output_with_fuels_sum_all = model_output_with_fuels_sum_all.groupby(['Scenario','Economy',  'Date', 'Transport Type', 'Fuel', 'Measure', 'Unit']).sum().reset_index()
        model_output_with_fuels_sum_all['Economy'] = 'all'
    if ECONOMY_GROUPING != 'all':
        model_output_with_fuels_sum = model_output_with_fuels_sum_economy_grouping
        extra_identifier += f'_{ECONOMY_GROUPING}'
    if AGG_OF_ALL_ECONOMIES:
        model_output_with_fuels_sum = pd.concat([model_output_with_fuels_sum_all, model_output_with_fuels_sum])
    if ONLY_AGG_OF_ALL:
        model_output_with_fuels_sum = model_output_with_fuels_sum_all.copy()
        extra_identifier = '_agg'
    
    ######################
        
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        emissions_by_fuel_type_scen = model_output_with_fuels_sum.loc[(model_output_with_fuels_sum['Scenario']==scenario)].copy()
        
        emissions_by_fuel_type_scen = emissions_by_fuel_type_scen.groupby(['Fuel']).filter(lambda x: not all(x['Emissions'] == 0))
        # calculate total 'Emissions' for each 'Fuel' 
        total_emissions_per_fuel = emissions_by_fuel_type_scen.groupby('Fuel')['Emissions'].sum()

        # Create an ordered category of 'Fuel' labels sorted by total 'Emissions'
        emissions_by_fuel_type_scen['Fuel'] = pd.Categorical(
            emissions_by_fuel_type_scen['Fuel'],
            categories = total_emissions_per_fuel.sort_values(ascending=False).index,
            ordered=True
        )

        # Now sort the DataFrame by the 'Fuel' column:
        emissions_by_fuel_type_scen.sort_values(by='Fuel', inplace=True)
        if transport_type=='passenger':
            #now plot
            #add units to y col
            title_text = 'Emissions by Fuel {} {} ({})'.format(scenario, transport_type, emissions_by_fuel_type_scen['Unit'].unique()[0])
            fig = px.area(emissions_by_fuel_type_scen.loc[emissions_by_fuel_type_scen['Transport Type']=='passenger'], x='Date', y='Emissions', color='Fuel',  title=title_text, color_discrete_map=colors_dict, facet_col='Economy', facet_col_wrap=7)
                         
            #save to html
            fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'emissions_by_fuel_type_{scenario}_{ECONOMY_GROUPING}_{transport_type}{extra_identifier}.html'))

            if INDEPENDENT_AXIS:
                fig.update_yaxes(matches=None)
                fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
                
                # Save to HTML with independent axis
                fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'emissions_by_fuel_type_{scenario}_{ECONOMY_GROUPING}_{transport_type}_indep_axis.html'))
            
        elif transport_type == 'freight':
            #now plot
            #add units to y col
            title_text = 'Emissions by Fuel {} {} ({})'.format(scenario, transport_type, emissions_by_fuel_type_scen['Unit'].unique()[0])
            fig = px.area(emissions_by_fuel_type_scen.loc[emissions_by_fuel_type_scen['Transport Type']=='freight'], x='Date', y='Emissions', color='Fuel',  title=title_text, color_discrete_map=colors_dict, facet_col='Economy', facet_col_wrap=7)
            # fig.update_layout(yaxis_range=(0, y_axis_max))
            
            #save to html
            fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'emissions_by_fuel_type_{scenario}_{ECONOMY_GROUPING}_{transport_type}{extra_identifier}.html'))
            
            if INDEPENDENT_AXIS:
                fig.update_yaxes(matches=None)
                fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
                
                #save to html
                fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'emissions_by_fuel_type_{scenario}_{ECONOMY_GROUPING}_{transport_type}_indep_axis.html'))
                    
            
        elif transport_type == 'all':
            #sum across transport types
            emissions_by_fuel_type_scen = emissions_by_fuel_type_scen.groupby(['Economy', 'Date', 'Fuel','Unit'], group_keys=False).sum().reset_index()
            #add units to y col
            title_text = 'Emissions by Fuel {} ({})'.format(scenario, emissions_by_fuel_type_scen['Unit'].unique()[0])
            #now plot
            fig = px.area(emissions_by_fuel_type_scen, x='Date', y='Emissions', color='Fuel',  title=title_text, color_discrete_map=colors_dict, facet_col='Economy', facet_col_wrap=7)
            # fig.update_layout(yaxis_range=(0, y_axis_max))
                            
            #save to html
            fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'emissions_by_fuel_type_{scenario}_{ECONOMY_GROUPING}_{transport_type}{extra_identifier}.html'))
            if INDEPENDENT_AXIS:
                fig.update_yaxes(matches=None)
                fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
                
                #save to html
                fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'emissions_by_fuel_type_{scenario}_{ECONOMY_GROUPING}_{transport_type}_indep_axis.html'))
        else:
            raise ValueError('transport_type must be passenger, all or freight')
    return
            
def share_of_emissions_by_vehicle_type_FOR_MULTIPLE_ECONOMIES(config, ECONOMY_GROUPING, emissions_factors, model_output_with_fuels_df, colors_dict, AGG_OF_ALL_ECONOMIES, USE_AVG_GENERATION_EMISSIONS_FACTOR=True, ONLY_AGG_OF_ALL=False):
    extra_identifier = ''
    model_output_with_fuels = model_output_with_fuels_df.copy()
    # drop non road:
    model_output_with_fuels = model_output_with_fuels.loc[model_output_with_fuels['Medium']=='road'].copy()
    #change suv, lt and car to all be 'lpv' and all ht and mt to be truck
    model_output_with_fuels['Vehicle Type'] = np.where(model_output_with_fuels['Vehicle Type'].isin(['suv', 'lt', 'car']), 'lpv', model_output_with_fuels['Vehicle Type'])
    model_output_with_fuels['Vehicle Type'] = np.where(model_output_with_fuels['Vehicle Type'].isin(['ht', 'mt']), 'truck', model_output_with_fuels['Vehicle Type'])
    #TEMP #WHERE TRANSPORT TYPE IS FREIGHT or medium is not road, SET THE electricty yse to 0. This is so we can test what the effect of electriicyt is 
    # model_output_with_fuels.loc[(model_output_with_fuels['Transport Type']=='freight') | (model_output_with_fuels['Medium']!='road') & (model_output_with_fuels['Fuel']=='17_electricity'), 'Energy'] = 0
    #load in data and recreate plot, as created in all_economy_graphs
    #loop through scenarios and grab the data for each scenario:
    emissions_by_vehicle_type= model_output_with_fuels[['Economy', 'Scenario','Date', 'Fuel', 'Vehicle Type','Energy']].groupby(['Economy', 'Scenario','Date','Vehicle Type', 'Fuel']).sum().reset_index().copy()
    
    #rename fuel_code to fuel in emissions_factors
    emissions_factors = emissions_factors.rename(columns={'fuel_code':'Fuel'})
    #join on the emissions factors (has the cols fuel_code,	Emissions factor (MT/PJ))
    emissions_by_vehicle_type = emissions_by_vehicle_type.merge(emissions_factors, how='left', on='Fuel')
    
    if USE_AVG_GENERATION_EMISSIONS_FACTOR:
        gen='_gen'
        extra_identifier+=gen
        #pull in the 8th outlook emissions factors by year, then use that to claculate the emissions for electricity.
        emissions_factor_elec = pd.read_csv(os.path.join(config.root_dir, 'input_data', 'from_8th', 'outlook_8th_emissions_factors_with_electricity.csv'))#c:\Users\finbar.maunsell\github\aperc-emissions\output_data\outlook_8th_emissions_factors_with_electricity.csv
        #extract the emissions factor for elctricity for each economy
        emissions_factor_elec = emissions_factor_elec[emissions_factor_elec.fuel_code=='17_electricity'].copy()
        #rename Carbon Neutral Scenario to Target
        emissions_factor_elec['Scenario'] = emissions_factor_elec['Scenario'].replace('Carbon Neutral', 'Target')
        #capitalise the cols
        emissions_factor_elec.columns = [x.capitalize() for x in emissions_factor_elec.columns]
        #rename fuel code to fuel
        emissions_factor_elec = emissions_factor_elec.rename(columns={'Fuel_code':'Fuel', 'Year':'Date', 'Emissions factor (mt/pj)':'Emissions factor (MT/PJ)'})
        #merge on economy and year and fuel code
        emissions_by_vehicle_type = emissions_by_vehicle_type.merge(emissions_factor_elec, on=['Date', 'Economy', 'Scenario', 'Fuel'], how='left', indicator=True, suffixes=('', '_elec'))
        #where indicator is both, use the new value
        emissions_by_vehicle_type['Emissions factor (MT/PJ)'] = np.where(emissions_by_vehicle_type['_merge']=='both', emissions_by_vehicle_type['Emissions factor (MT/PJ)_elec'], emissions_by_vehicle_type['Emissions factor (MT/PJ)'])
        #fill any missing values using ffill after sorting by date and grouping by 'Economy', 'Scenario','Date', 'Fuel', 'Transport Type'
        emissions_by_vehicle_type['Emissions factor (MT/PJ)'] = emissions_by_vehicle_type.sort_values(by='Date').groupby(['Economy', 'Scenario','Date','Vehicle Type', 'Fuel'])['Emissions factor (MT/PJ)'].fillna(method='ffill')
        #drop columns
        emissions_by_vehicle_type = emissions_by_vehicle_type.drop(columns=['Emissions factor (MT/PJ)_elec', '_merge'])
    #identify where there are no emissions factors:
    missing_emissions_factors = emissions_by_vehicle_type.loc[emissions_by_vehicle_type['Emissions factor (MT/PJ)'].isna()].copy()
    if len(missing_emissions_factors)>0:
        breakpoint()
        time.sleep(1)
        raise ValueError(f'missing emissions factors, {missing_emissions_factors.Fuel.unique()}')
    
    #calculate emissions:
    emissions_by_vehicle_type['Emissions'] = emissions_by_vehicle_type['Energy'] * emissions_by_vehicle_type['Emissions factor (MT/PJ)']

    #grab the emissions by vehicle type and sum them
    emissions_by_vehicle_type = emissions_by_vehicle_type.groupby(['Economy', 'Scenario', 'Date', 'Vehicle Type']).sum().reset_index()
    ###############################
    extra_identifier = ''
    if ECONOMY_GROUPING != 'all':
        ECONOMY_GROUPING_DICT = extract_economy_grouping_dict_from_yml(config, ECONOMY_GROUPING)
        emissions_by_vehicle_type_economy_grouping = emissions_by_vehicle_type.copy()
        emissions_by_vehicle_type_economy_grouping['Economy'] = emissions_by_vehicle_type_economy_grouping['Economy'].replace(ECONOMY_GROUPING_DICT)
        emissions_by_vehicle_type_economy_grouping = emissions_by_vehicle_type_economy_grouping.groupby(['Scenario', 'Economy', 'Date', 'Vehicle Type']).sum().reset_index()
    if AGG_OF_ALL_ECONOMIES or ONLY_AGG_OF_ALL:
        ECONOMY_GROUPING_DICT = extract_economy_grouping_dict_from_yml(config, 'all')
        emissions_by_vehicle_type_all = emissions_by_vehicle_type.copy()
        emissions_by_vehicle_type_all['Economy'] = 'all'
        emissions_by_vehicle_type_all = emissions_by_vehicle_type_all.groupby(['Scenario', 'Date', 'Economy',  'Vehicle Type']).sum().reset_index()
    if ECONOMY_GROUPING != 'all':
        emissions_by_vehicle_type = emissions_by_vehicle_type_economy_grouping
        extra_identifier += f'_{ECONOMY_GROUPING}'
    if AGG_OF_ALL_ECONOMIES:
        emissions_by_vehicle_type = pd.concat([emissions_by_vehicle_type_all, emissions_by_vehicle_type])
    if ONLY_AGG_OF_ALL:
        emissions_by_vehicle_type = emissions_by_vehicle_type_all.copy()
        extra_identifier = '_agg'
    #################################
    
    #grab the total emissions for each date and economy
    total_emissions = emissions_by_vehicle_type.groupby(['Economy', 'Scenario', 'Date']).sum().reset_index()  
    
    #merge the two dataframes and then calcaulte the share of emissions by vehicle type
    emissions_by_vehicle_type = emissions_by_vehicle_type.merge(total_emissions, on=['Economy', 'Scenario', 'Date'], how='left', suffixes=('', '_total'))
    emissions_by_vehicle_type['Share of emissions'] = emissions_by_vehicle_type['Emissions'] / emissions_by_vehicle_type['Emissions_total']
    #plot the data
    for scenario in emissions_by_vehicle_type['Scenario'].unique():
        emissions_by_vehicle_type_scenario = emissions_by_vehicle_type.loc[emissions_by_vehicle_type['Scenario']==scenario].copy()
        title_text = 'Share of emissions by vehicle type - {}'.format(scenario)
        fig = px.line(emissions_by_vehicle_type_scenario, x='Date', y='Share of emissions', color='Vehicle Type',  title=title_text, color_discrete_map=colors_dict, facet_col='Economy', facet_col_wrap=8)
        #save to html
        fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'share_of_emissions_by_vehicle_type_{scenario}_{ECONOMY_GROUPING}{extra_identifier}.html'))
    return

        
def prodcue_LMDI_mutliplicative_plot_FOR_MULTIPLE_ECONOMIES(config,  ECONOMY_GROUPING, model_output_with_fuels, colors_dict, ECONOMY_IDs,  transport_type, medium, AGG_OF_ALL_ECONOMIES, ONLY_AGG_OF_ALL):
    #as of yet, dont think tehres any point in doing economy groupings sincethey are better calcaulted in the calcualtion phase thanhere
    if ECONOMY_GROUPING !='all':
        return
    PLOTTED=True
    extra_identifier = ''
    if AGG_OF_ALL_ECONOMIES:
        ECONOMY_IDs = ECONOMY_IDs + ['all']
        if ONLY_AGG_OF_ALL:
            ECONOMY_IDs = ['all']
            extra_identifier = '_agg'
    for scenario in config.economy_scenario_concordance.Scenario.unique():
        lmdi_data = pd.DataFrame()
        for economy in ECONOMY_IDs:
            if medium == 'all': 
                medium_id = 'all_mediums'
            else:
                medium_id = 'road'
            # breakpoint()
            file_identifier = f'{economy}_{scenario}_{transport_type}_{medium_id}_2_Energy use_Hierarchical_2060_multiplicative'
            try:
                if economy == 'all':
                    #search in folder 'APEC' and use APEC instead of economy in file_id
                    file_identifier = f'APEC_{scenario}_{transport_type}_{medium_id}_2_Energy use_Hierarchical_2060_multiplicative'
                    lmdi_data_economy = pd.read_csv(os.path.join(config.root_dir, 'intermediate_data', 'LMDI', 'APEC', f'{file_identifier}.csv'))
                else:
                    lmdi_data_economy = pd.read_csv(os.path.join(config.root_dir, 'intermediate_data', 'LMDI', economy, f'{file_identifier}.csv'))
            except:
                if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                    breakpoint()
                continue
            #add economy col and then concat to all_economy df
            lmdi_data_economy['Economy'] = economy
            lmdi_data = pd.concat([lmdi_data, lmdi_data_economy])
        if len(lmdi_data)==0:
            return
        #melt data so we have the different components of the LMDI as rows. eg. for freight the cols are: Date	Change in Energy	Energy intensity effect	freight_tonne_km effect	Engine type effect	Total Energy	Total_freight_tonne_km
        #we want to drop the last two plots, then melt the data so we have the different components of the LMDI as rows. eg. for freight the cols will end up as: Date	Effect. Then we will also create a line dash col and if the Effect is Change in Energy then the line dash will be solid, otherwise it will be dotted
        #drop cols by index, not name so it doesnt matter what thei names are
        lmdi_data_melt = lmdi_data.copy()#drop(lmdi_data.columns[[len(lmdi_data.columns)-1, len(lmdi_data.columns)-2]], axis=1)
        lmdi_data_melt = lmdi_data_melt.melt(id_vars=['Date', 'Economy'], var_name='Effect', value_name='Value')
        #If there are any values with Effect 'Total Energy use'  or 'Total_passenger_km'  then emove them since they are totals:
        lmdi_data_melt = lmdi_data_melt.loc[(lmdi_data_melt['Effect']!='Total Energy use') & (lmdi_data_melt['Effect']!='Total_passenger_km') & (lmdi_data_melt['Effect']!='Total_freight_tonne_km')].copy()
        #if any values are > 10, create a breakpoint so we can see what they are, just in case they need to be removed like above:
        if lmdi_data_melt['Value'].max() > 10: 
            breakpoint()
        lmdi_data_melt['line_dash'] = lmdi_data_melt['Effect'].apply(lambda x: 'solid' if x == 'Percent change in Energy' else 'dash')
        
        if medium == 'road':
            title_text = f'Drivers of {medium} {transport_type} energy use'
        else:
            title_text = f'Drivers of {transport_type} energy use'

        fig = px.line(lmdi_data_melt,  x="Date", y='Value',  color='Effect', line_dash='line_dash', title=title_text, color_discrete_map=colors_dict, facet_col='Economy', facet_col_wrap=8)
        #save to html
        fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'lmdi_multiplicative_{scenario}_{ECONOMY_GROUPING}{extra_identifier}.html'))
    return 

def produce_LMDI_additive_plot_FOR_MULTIPLE_ECONOMIES(config,  ECONOMY_GROUPING, model_output_with_fuels, colors_dict, ECONOMY_IDs, medium, AGG_OF_ALL_ECONOMIES, ONLY_AGG_OF_ALL):
    #as of yet, dont think tehres any point in doing economy groupings sincethey are better calcaulted in the calcualtion phase thanhere
    if ECONOMY_GROUPING !='all':
        return
    PLOTTED=True
    extra_identifier = ''
    if AGG_OF_ALL_ECONOMIES:
        ECONOMY_IDs = ECONOMY_IDs + ['all']
        if ONLY_AGG_OF_ALL:
            ECONOMY_IDs = ['all']
            extra_identifier = '_agg'
            
    for scenario in config.economy_scenario_concordance.Scenario.unique():
        lmdi_data = pd.DataFrame()
        for economy in ECONOMY_IDs:
            if medium == 'all': 
                medium_id = 'all_mediums'
            else:
                medium_id = 'road'
            # breakpoint()
            file_identifier = f'{economy}_{scenario}_{medium_id}_2_Energy use_Hierarchical_2060_concatenated_additive'
            try:
                if economy == 'all':
                    #search in folder 'APEC' and use APEC instead of economy in file_id
                    file_identifier = f'APEC_{scenario}_{medium_id}_2_Energy use_Hierarchical_2060_concatenated_additive'
                    lmdi_data_economy = pd.read_csv(os.path.join(config.root_dir, 'intermediate_data', 'LMDI','APEC', f'{file_identifier}.csv'))
                else:
                    lmdi_data_economy = pd.read_csv(os.path.join(config.root_dir, 'intermediate_data', 'LMDI', economy, f'{file_identifier}.csv'))
                
            except:
                if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                    breakpoint()
                continue
            #add economy col and then concat to all_economy df
            lmdi_data_economy['Economy'] = economy
            lmdi_data = pd.concat([lmdi_data, lmdi_data_economy])
        if len(lmdi_data)==0:
            return
        #melt data so we have the different components of the LMDI as rows. eg. for freight the cols are: Date	Change in Energy	Energy intensity effect	freight_tonne_km effect	Engine type effect	Total Energy	Total_freight_tonne_km
        #we want to drop the last two plots, then melt the data so we have the different components of the LMDI as rows. eg. for freight the cols will end up as: Date	Effect. Then we will also create a line dash col and if the Effect is Change in Energy then the line dash will be solid, otherwise it will be dotted
        #drop cols by index, not name so it doesnt matter what thei names are
        lmdi_data_melt = lmdi_data.copy()#drop(lmdi_data.columns[[len(lmdi_data.columns)-1, len(lmdi_data.columns)-2]], axis=1)
        #grab data for max Date
        lmdi_data_melt = lmdi_data_melt.loc[lmdi_data_melt['Date']==lmdi_data_melt['Date'].max()].copy()
        #melt data
        lmdi_data_melt = lmdi_data_melt.melt(id_vars=['Date', 'Economy'], var_name='Effect', value_name='Value')
        #If there are any values with Effect 'Total Energy use'  or 'Total_passenger_km'  then emove them since they are totals:
        lmdi_data_melt = lmdi_data_melt.loc[(lmdi_data_melt['Effect']!='Total Energy use') & (lmdi_data_melt['Effect']!='Total_passenger_km') & (lmdi_data_melt['Effect']!='Total_freight_tonne_km') & (lmdi_data_melt['Effect']!='Total_passenger_and_freight_km')].copy()
        #rename the effect Additive change in Energy use to Change in Energy use
        lmdi_data_melt['Effect'] = lmdi_data_melt['Effect'].apply(lambda x: 'Change in Energy use' if x == 'Additive change in Energy use' else x)
        #and rename 'Engine switching intensity effect' to 'Other intensity improvments'
        lmdi_data_melt['Effect'] = lmdi_data_melt['Effect'].apply(lambda x: 'Other intensity improvements' if x == 'Engine switching intensity effect' else x)
        #and rename passenger_and_freight_km effect to 'Activity'
        lmdi_data_melt['Effect'] = lmdi_data_melt['Effect'].apply(lambda x: 'Activity' if x == 'passenger_and_freight_km effect' else x)
        #and Vehicle Type effect to 'Switching vehicle types'
        lmdi_data_melt['Effect'] = lmdi_data_melt['Effect'].apply(lambda x: 'Switching vehicle types' if x == 'Vehicle Type effect' else x)
        #and Engine switching effect to 'Engine type switching'
        lmdi_data_melt['Effect'] = lmdi_data_melt['Effect'].apply(lambda x: 'Drive type switching' if x == 'Engine switching effect' else x)
        # decreasing = {"marker":{"color":"#93C0AC"}},
        # increasing = {"marker":{"color":"#EB9C98"}},
        # totals = {"marker":{"color":"#11374A"}}
        #first set color basser on if value is positive or negative
        lmdi_data_melt['color'] = lmdi_data_melt['Value'].apply(lambda x: '#93C0AC' if x < 0 else '#EB9C98')
        #then set color to grey if the effect is 'Change in Energy use'
        lmdi_data_melt['color'] = np.where(lmdi_data_melt['Effect']=='Change in Energy use', '#11374A', lmdi_data_melt['color'])
        #create color dict from that, amtching from effect to color
        colors_dict_new = dict(zip(lmdi_data_melt['Effect'], lmdi_data_melt['color']))
        
        #lastly, manually set the order of the bars so it goes: Change in Energy use,passenger_and_freight_km effect,	Vehicle Type effect	Engine switching effect,	Engine switching intensity effect 
        # order = ['Change in Energy use', 'passenger_and_freight_km effect', 'Vehicle Type effect', 'Engine switching effect', 'Engine switching intensity effect']
        order = ['Change in Energy use', 'Activity', 'Switching vehicle types', 'Drive type switching', 'Other intensity improvements']
        # Convert the 'Effect' column to a categorical type with the defined order
        lmdi_data_melt['Effect'] = pd.Categorical(lmdi_data_melt['Effect'], categories=order, ordered=True)
        # Sort the DataFrame by the 'Effect' column
        lmdi_data_melt = lmdi_data_melt.sort_values('Effect')
        
        if medium == 'road':
            title_text = f'Drivers of changes in {medium} energy use'
        else:
            title_text = f'Drivers of changes in energy use'

        fig = px.bar(lmdi_data_melt,  x="Effect", y='Value',  color='Effect', title=title_text, color_discrete_map=colors_dict, facet_col='Economy', facet_col_wrap=8)
        #save to html
        fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'dashboards', 'multiple_economy_dashboards', f'lmdi_additive_{scenario}_{ECONOMY_GROUPING}{extra_identifier}.html'))
    return 

def extract_economy_grouping_dict_from_yml(config, ECONOMY_GROUPING):
    #do an aggregate by econmoy grouping too.
    ECONOMY_GROUPING_DICT = yaml.load(open(os.path.join(config.root_dir, 'config','parameters.yml')), Loader=yaml.FullLoader)['ECONOMY_GROUPING_DICTS']
    if ECONOMY_GROUPING not in ECONOMY_GROUPING_DICT.keys():
        raise ValueError(f'{ECONOMY_GROUPING} not in ECONOMY_GROUPING_DICT.keys()')
    ECONOMY_GROUPING_DICT = ECONOMY_GROUPING_DICT[ECONOMY_GROUPING]
    #now reverse it so the values in lists in .values() are now keys and the keys are the values:
    ECONOMY_GROUPING_DICT_rev = {v: k for k in ECONOMY_GROUPING_DICT for v in ECONOMY_GROUPING_DICT[k]}
    return ECONOMY_GROUPING_DICT_rev