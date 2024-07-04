#calcaulte oil displacement from evs and fcevs. This can be done by recalculating the oil use if fcevs and/or evs werent used. THis will jsut be efficiency * miles driven * number of cars.

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

# This code is designed to calculate and visualize the displacement of oil use due to electric vehicles (EVs) and fuel cell electric vehicles (FCEVs). It does this by estimating how much oil would have been used if these vehicles were powered by internal combustion engines (ICEs) instead. 
#%%
def calculate_and_plot_oil_displacement(config, ECONOMY_ID, CHART_OPTION='stacked_bar', COMBINE_LPVS = True, bar_graph_year_intervals=False, INCLUDE_VTYPES = False, INCLUDE_OIL_USE=True):
        
    AUTO_OPEN_PLOTLY_GRAPHS = False
    dont_overwrite_existing_graphs = False
    plot_png = False
    plot_html = True
    subfolder_name = 'all_economy_graphs'
    default_save_folder = f'plotting_output\\oil_displacement\\{config.FILE_DATE_ID}\\'
    #CHECK THAT SAVE FOLDER EXISTS, IF NOT CREATE IT
    if not os.path.exists(config.root_dir + '\\' + default_save_folder):
        os.makedirs(config.root_dir + '\\' + default_save_folder)
    model_output_detailed = pd.read_csv(config.root_dir + '\\' + 'output_data\\model_output_detailed\\{}_{}'.format(ECONOMY_ID, config.model_output_file_name))

    #create regions dataset and then concat that on with regions = Economy. so that we can plot regions too.
    region_economy_mapping = pd.read_csv(config.root_dir + '\\' + 'config\\concordances_and_config_data\\region_economy_mapping.csv')

    #join with model_output_detailed_APEC.
    #where there is no region drop the row since we are just plotting singular economies atm
    model_output_detailed_regions = model_output_detailed.merge(region_economy_mapping[['Region', 'Economy']].drop_duplicates(), how='left', left_on='Economy', right_on='Economy')
    
    # model_output_detailed_regions['Region'] = model_output_detailed_regions['Region'].fillna(model_output_detailed_regions['Economy'])
    model_output_detailed_regions = model_output_detailed_regions.dropna(subset=['Region'])
    #then sum up stocks, and average out efficiency, occupancy, mileage
    model_output_detailed_regions = model_output_detailed_regions.groupby(['Date', 'Region', 'Medium', 'Transport Type', 'Scenario', 'Drive', 'Vehicle Type']).agg({'Stocks': 'sum', 'Efficiency': 'mean', 'Occupancy_or_load': 'mean', 'Mileage': 'mean'}).reset_index()

    #set Region to Economy
    model_output_detailed_regions['Economy'] = model_output_detailed_regions['Region']
    model_output_detailed_regions = model_output_detailed_regions.drop(columns=['Region'])
    #now concat this to model_output_detailed but keep only the cols in model_output_detailed_regions
    model_output_detailed = pd.concat([model_output_detailed[model_output_detailed_regions.columns], model_output_detailed_regions], ignore_index=True)
    
    ###################
    AUTO_OPEN_PLOTLY_GRAPHS = False
    #map vtypes to colors and associated opacity
    #vtyes: ['all', 'ht', 'ldv', '2w', 'bus']
    #     color_swap = {
    #     # Reds
    #     'mt Oil displacement': 'rgba(255, 85, 85, 1)', # medium red
    #     'lcv Oil displacement': 'rgba(255, 170, 170, 1)', # lighter red
    #     'ht Energy BEV': 'rgba(255, 50, 50, 1)', # darker red
    #     'mt Energy BEV': 'rgba(255, 85, 85, 1)', # medium red
    #     'lcv Energy BEV': 'rgba(255, 170, 170, 1)', # lighter red
    #     'lt Energy BEV': 'rgba(255, 200, 200, 1)', # lightest red
    #     'car Energy BEV': 'rgba(255, 190, 190, 1)', # slightly darker light red
    #     'suv Energy BEV': 'rgba(255, 170, 170, 1)', # light red
    #     '2w Energy BEV': 'rgba(255, 85, 85, 1)', # medium red
    #     'bus Energy BEV': 'rgba(255, 50, 50, 1)', # darker red
    #     'lpv Energy BEV': 'rgba(255, 170, 170, 1)', # light red

    #     #Greys
    #     'lt Oil displacement': 'rgba(200, 200, 200, 1)', # lightest grey
    #     'car Oil displacement': 'rgba(190, 190, 190, 1)', # slightly darker light grey
    #     'suv Oil displacement': 'rgba(170, 170, 170, 1)', # light grey
    #     '2w Oil displacement': 'rgba(85, 85, 85, 1)', # medium grey
    #     'bus Oil displacement': 'rgba(50, 50, 50, 1)', # darker grey
    #     'lpv Oil displacement': 'rgba(170, 170, 170, 1)', # light grey

    #     'all Oil displacement': 'rgba(85, 85, 85, 1)', # medium grey
    #     'all Energy BEV': 'rgba(255, 85, 85, 1)', # medium red
    #     'passenger Oil displacement': 'rgba(85, 85, 85, 1)', # medium grey
    #     'passenger Energy BEV': 'rgba(255, 85, 85, 1)', # medium red
    #     'freight Oil displacement': 'rgba(85, 85, 85, 1)', # medium grey
    #     'freight Energy BEV': 'rgba(255, 85, 85, 1)', # medium red

    #     'ht Oil use': 'rgba(50, 50, 50, 1)', # darker grey
    #     'mt Oil use': 'rgba(85, 85, 85, 1)', # medium grey
    #     'lcv Oil use': 'rgba(170, 170, 170, 1)', # light grey

    #     'lt Oil use': 'rgba(200, 200, 200, 1)', # lightest grey
    #     'car Oil use': 'rgba(190, 190, 190, 1)', # slightly darker light grey
    #     'suv Oil use': 'rgba(170, 170, 170, 1)', # light grey
    #     '2w Oil use': 'rgba(85, 85, 85, 1)', # medium grey
    #     'bus Oil use': 'rgba(50, 50, 50, 1)', # darker grey
    #     'lpv Oil use': 'rgba(170, 170, 170, 1)', # light grey
    # }
        
    #     color_map = {
    #     'ht Oil displacement': 'rgba(255, 0, 0,  1)', # dark grey
    #     'mt Oil displacement': 'rgba(255, 0, 0,  1)', # grey
    #     'lcv Oil displacement': 'rgba(255, 0, 0,  1)', # light grey

    #     'lt Oil displacement': 'rgba(255, 0, 0,  1)',   # lightest grey
    #     'car Oil displacement': 'rgba(255, 0, 0,  1)',  # lighter grey
    #     'suv Oil displacement': 'rgba(255, 0, 0,  1)',   # light grey
    #     '2w Oil displacement': 'rgba(255, 0, 0,  1)',       # grey
    #     'bus Oil displacement': 'rgba(255, 0, 0,  1)',      # dark grey
    #     'lpv Oil displacement': 'rgba(255, 0, 0,  1)',   # light grey
        
    #     'ht Energy BEV': 'rgba(0, 0, 0,  1)', # dark green
    #     'mt Energy BEV': 'rgba(0, 0, 0,  1)', # green
    #     'lcv Energy BEV': 'rgba(0, 0, 0,  1)', # light green

    #     'lt Energy BEV': 'rgba(0, 0, 0,  1)',   # lightest green
    #     'car Energy BEV': 'rgba(0, 0, 0,  1)',      # lighter green
    #     'suv Energy BEV': 'rgba(0, 0, 0,  1)',      # light green
    #     '2w Energy BEV': 'rgba(0, 0, 0,  1)',       # green
    #     'bus Energy BEV': 'rgba(0, 0, 0,  1)',       # dark green
    #     'lpv Energy BEV': 'rgba(0, 0, 0,  1)',      # light green

    #     'all Oil displacement': 'rgba(255, 0, 0,  1)', # grey
    #     'all Energy BEV': 'rgba(0, 0, 0,  1)', # green
    #     'passenger Oil displacement': 'rgba(255, 0, 0,  1)', # grey
    #     'passenger Energy BEV': 'rgba(0, 0, 0,  1)', # green
    #     'freight Oil displacement': 'rgba(255, 0, 0,  1)', # grey
    #     'freight Energy BEV': 'rgba(0, 0, 0,  1)', # green

    #     'ht Oil use': 'rgba(255, 0, 0,  1)', # dark red
    #     'mt Oil use': 'rgba(255, 0, 0,  1)', # red
    #     'lcv Oil use': 'rgba(255, 0, 0,  1)', # light red

    #     'lt Oil use': 'rgba(255, 0, 0,  1)',   # lightest red
    #     'car Oil use': 'rgba(255, 0, 0,  1)',  # lighter red
    #     'suv Oil use': 'rgba(255, 0, 0,  1)',   # light red
    #     '2w Oil use': 'rgba(255, 0, 0,  1)',       # red
    #     'bus Oil use': 'rgba(255, 0, 0,  1)',      # dark red
    #     'lpv Oil use': 'rgba(255, 0, 0,  1)',   # light red

    #     'all Oil use': 'rgba(255, 0, 0,  1)', # red
    #     'passenger Oil use': 'rgba(255, 0, 0,  1)', # red
    #     'freight Oil use': 'rgba(255, 0, 0,  1)', # red

    #     'ht Energy FCEV': 'rgba(0, 0, 255,  1)', # dark blue
    #     'mt Energy FCEV': 'rgba(70, 130, 180,  1)', # steel blue
    #     'lcv Energy FCEV': 'rgba(135, 206, 235,  1)', # sky blue

    #     'lt Energy FCEV': 'rgba(240, 248, 255,  1)',   # lightest blue
    #     'car Energy FCEV': 'rgba(100, 149, 237,  1)',  # cornflower blue
    #     'suv Energy FCEV': 'rgba(70, 130, 180,  1)',   # steel blue
    #     '2w Energy FCEV': 'rgba(0, 0, 255,  1)',       # blue
    #     'bus Energy FCEV': 'rgba(0, 0, 139,  1)',      # dark blue
    #     'lpv Energy FCEV': 'rgba(70, 130, 180,  1)',   # steel blue

    #     'all Energy FCEV': 'rgba(0, 0, 255,  1)', # blue
    #     'passenger Energy FCEV': 'rgba(70, 130, 180,  1)', # steel blue
    #     'freight Energy FCEV': 'rgba(135, 206, 235,  1)', # sky blue
    #     }
    color_map = {
        # Shades of Grey for Oil displacement
        'ht Oil displacement': 'rgba(64, 64, 64, 1)', # dark grey
        'mt Oil displacement': 'rgba(128, 128, 128, 1)', # grey
        'lcv Oil displacement': 'rgba(192, 192, 192, 1)', # light grey
        'lt Oil displacement': 'rgba(224, 224, 224, 1)', # lightest grey
        'car Oil displacement': 'rgba(208, 208, 208, 1)', # lighter grey
        'suv Oil displacement': 'rgba(192, 192, 192, 1)', # light grey
        '2w Oil displacement': 'rgba(128, 128, 128, 1)', # grey
        'bus Oil displacement': 'rgba(64, 64, 64, 1)', # dark grey
        'lpv Oil displacement': 'rgba(192, 192, 192, 1)', # light grey

        # Shades of Green for Energy BEV
        'ht Energy BEV': 'rgba(0, 100, 0, 1)', # dark green
        'mt Energy BEV': 'rgba(0, 128, 0, 1)', # green
        'lcv Energy BEV': 'rgba(0, 192, 0, 1)', # light green
        'lt Energy BEV': 'rgba(0, 255, 0, 1)', # lightest green
        'car Energy BEV': 'rgba(0, 224, 0, 1)', # lighter green
        'suv Energy BEV': 'rgba(0, 192, 0, 1)', # light green
        '2w Energy BEV': 'rgba(0, 128, 0, 1)', # green
        'bus Energy BEV': 'rgba(0, 100, 0, 1)', # dark green
        'lpv Energy BEV': 'rgba(0, 192, 0, 1)', # light green

        # General categories in Grey and Green
        'all Oil displacement': 'rgba(128, 128, 128, 1)', # grey
        'all Energy BEV': 'rgba(0, 128, 0, 1)', # green
        'passenger Oil displacement': 'rgba(128, 128, 128, 1)', # grey
        'passenger Energy BEV': 'rgba(0, 128, 0, 1)', # green
        'freight Oil displacement': 'rgba(128, 128, 128, 1)', # grey
        'freight Energy BEV': 'rgba(0, 128, 0, 1)', # green

        # Shades of Red for Oil use
        'ht Oil use': 'rgba(139, 0, 0, 1)', # dark red
        'mt Oil use': 'rgba(255, 0, 0, 1)', # red
        'lcv Oil use': 'rgba(255, 102, 102, 1)', # light red
        'lt Oil use': 'rgba(255, 204, 204, 1)', # lightest red
        'car Oil use': 'rgba(255, 153, 153, 1)', # lighter red
        'suv Oil use': 'rgba(255, 102, 102, 1)', # light red
        '2w Oil use': 'rgba(255, 0, 0, 1)', # red
        'bus Oil use': 'rgba(139, 0, 0, 1)', # dark red
        'lpv Oil use': 'rgba(255, 102, 102, 1)', # light red

        # Red for all Oil use categories
        'all Oil use': 'rgba(255, 0, 0, 1)', # red
        'passenger Oil use': 'rgba(255, 0, 0, 1)', # red
        'freight Oil use': 'rgba(255, 0, 0, 1)', # red
        
        #blues for fcev
        'ht Energy FCEV': 'rgba(0, 0, 255,  1)', # dark blue
        'mt Energy FCEV': 'rgba(70, 130, 180,  1)', # steel blue
        'lcv Energy FCEV': 'rgba(135, 206, 235,  1)', # sky blue

        'lt Energy FCEV': 'rgba(240, 248, 255,  1)',   # lightest blue
        'car Energy FCEV': 'rgba(100, 149, 237,  1)',  # cornflower blue
        'suv Energy FCEV': 'rgba(70, 130, 180,  1)',   # steel blue
        '2w Energy FCEV': 'rgba(0, 0, 255,  1)',       # blue
        'bus Energy FCEV': 'rgba(0, 0, 139,  1)',      # dark blue
        'lpv Energy FCEV': 'rgba(70, 130, 180,  1)',   # steel blue

        'all Energy FCEV': 'rgba(0, 0, 255,  1)', # blue
        'passenger Energy FCEV': 'rgba(70, 130, 180,  1)', # steel blue
        'freight Energy FCEV': 'rgba(135, 206, 235,  1)', # sky blue
    }

    # Define a function for weighted average
    def weighted_avg(group, avg_name, weight_name, extra_factors = ['Occupancy_or_load', 'Mileage']):
        """Compute the weighted average of a group."""
        d = group[avg_name]
        w = group[weight_name]
        if len(extra_factors) > 0:
            #need to times w by the extra factors. This is important because normally stocks is not the weight, but activity should be which is stocks * mileage * occupancy_or_load
            for factor in extra_factors:
                w = w * group[factor]            
        if w.sum() == 0:
            return d.mean()
        else:
            return (d * w).sum() / w.sum()
    
    #so for every econoy and transport type we will do this plot. Also we will do it for fcevs
    if COMBINE_LPVS:
        # a = model_output_detailed.copy()
        #extract cars, suvs and lts and put them into a new category called 'lpv'
        lpvs = model_output_detailed[model_output_detailed['Vehicle Type'].isin(['car', 'suv', 'lt'])].copy()
        lpvs['Vehicle Type'] = 'lpv'
        #drop the old ones
        model_output_detailed = model_output_detailed[~model_output_detailed['Vehicle Type'].isin(['car', 'suv', 'lt'])]
        #then do a weigthed average of efficiency, occupancy and mileage
        # Apply weighted average on Efficiency, Occupancy_or_load, and Mileage
        
        weighted_lpvs = lpvs.groupby(['Date', 'Economy', 'Medium', 'Transport Type', 'Scenario', 'Drive', 'Vehicle Type']).apply(
            lambda g: pd.Series({
                'Stocks': g['Stocks'].sum(),  # Sum of Stocks
                'Efficiency': weighted_avg(g, 'Efficiency', 'Stocks'),
                'Occupancy_or_load': weighted_avg(g, 'Occupancy_or_load', 'Stocks'),
                'Mileage': weighted_avg(g, 'Mileage', 'Stocks')
            })).reset_index()
            
        # Concatenate this back onto model_output_detailed
        model_output_detailed = pd.concat([model_output_detailed, weighted_lpvs], ignore_index=True)
    if CHART_OPTION == 'stacked_bar':
        #filter for the data in year_intervals if its not False:
        if bar_graph_year_intervals is not False:
            model_output_detailed = model_output_detailed[model_output_detailed.Date.isin(bar_graph_year_intervals)].copy()
            #make date a string so we can use it as a category
            model_output_detailed['Date'] = model_output_detailed['Date'].astype(str)
    unique_transport_types = model_output_detailed['Transport Type'].unique().tolist() + ['all']
    #add transport type == 'all' to the list, for which we will do most of the calcualtions the same.
    for economy in model_output_detailed.Economy.unique():
        for t_type in unique_transport_types:
            for scenario in model_output_detailed.Scenario.unique():
                #to mkae this easier to write we will jsut do the fcev and bev graphs separately rather than iterating over the drive

                plotting_data = model_output_detailed.copy()
                plotting_data = plotting_data[plotting_data['Economy']==economy]
                plotting_data = plotting_data[plotting_data['Scenario']==scenario]
                #filter for only road
                plotting_data = plotting_data[plotting_data['Medium']=='road']
                #drop those cols
                if t_type != 'all':
                    plotting_data = plotting_data[plotting_data['Transport Type']==t_type]
                    plotting_data = plotting_data.drop(columns=['Medium', 'Transport Type', 'Scenario', 'Economy'])
                else:
                    plotting_data = plotting_data.drop(columns=['Medium', 'Scenario', 'Economy'])
                #now do the oil displacement calcualtions
                ##############################################
                #DO SEP PLOT FOR EACH DRIVE TYPE IN BEV AND FCEV
                ##############################################
                
                ice_bev = plotting_data.copy()
                ice = ice_bev[ice_bev['Drive'].isin(['ice_g', 'ice_d'])]
                #grab weighted avg of Efficiency Occupancy_or_load and Mileage and the sum of stocks
                # ice = ice.groupby(['Date', 'Vehicle Type']).agg({'Efficiency': 'mean', 'Occupancy_or_load': 'mean', 'Mileage': 'mean', 'Stocks': 'sum'}).reset_index()
                if t_type != 'all': 
                    cols = ['Date', 'Vehicle Type']
                else:
                    cols = ['Date', 'Vehicle Type', 'Transport Type']
                ice = ice.groupby(cols).apply(
                    lambda g: pd.Series({
                        'Stocks': g['Stocks'].sum(),  # Sum of Stocks
                        'Efficiency': weighted_avg(g, 'Efficiency', 'Stocks'),
                        'Occupancy_or_load': weighted_avg(g, 'Occupancy_or_load', 'Stocks'),
                        'Mileage': weighted_avg(g, 'Mileage', 'Stocks')
                    })).reset_index()
                    
                
                #set Drive to ice
                ice['Drive'] = 'ice'
                #sum or avg ice values
                bev = ice_bev[ice_bev['Drive']=='bev']#later this willprobably need to include phev
                #join
                ice_bev = pd.merge(ice, bev, on=cols, suffixes=('_ice', '_bev'))
                #now we have the data we can calculate oil use.

                # get vehicle types
                v_types = ice_bev['Vehicle Type'].unique()
                #########################WARNING 
                #set efficiency for ice to 0.5 and efficiency for bev to 1. just for testign
                # ice_bev = ice_bev.assign(Efficiency_ice = 0.5)
                # ice_bev = ice_bev.assign(Efficiency_bev = 1)
                #########################WARNING 

                #oil use = efficiency * mileage * stocks
                ice_bev = ice_bev.assign(Oil_displacement = (ice_bev['Mileage_bev'] * ice_bev['Stocks_bev'])/ice_bev['Efficiency_ice'])
                ice_bev = ice_bev.assign(Energy_bev = (ice_bev['Mileage_bev'] * ice_bev['Stocks_bev'])/ice_bev['Efficiency_bev'])
                #and also calc current oil use since it is interesting to see in the graph too
                ice_bev = ice_bev.assign(Oil_use = (ice_bev['Mileage_ice'] * ice_bev['Stocks_ice'])/ice_bev['Efficiency_ice'])
                
                ###for checkinghow the data looks and why things are as they are:#############################################
                #transofrm df a single drive column, based on teh suffixes.
                # #frist extract the ice vs bev dfs then stack them
                # ice = ice_bev[cols+ ['Oil_displacement', 'Oil_use'] + ice_bev.columns[ice_bev.columns.str.contains('ice')].to_list()]
                # bev = ice_bev[cols+ ['Oil_displacement', 'Oil_use'] + ice_bev.columns[ice_bev.columns.str.contains('bev')].to_list()]
                # #remove the suffixes
                # ice = ice.rename(columns = lambda x: re.sub('_ice|_bev', '', x))
                
                # bev = bev.rename(columns = lambda x: re.sub('_ice|_bev', '', x))
                # df = pd.concat([ice, bev], axis=0)
                
                ###for checking over########################
                
                #note that we are using the mileage of bevs isteadn of ices. THis is probably not necessary to state as an assumption 
                #to make it easy to plot we want to pivot so we have the energy use of each vehicle type as a column for each other index col
                #so firt filter for only energy
                ice_bev = ice_bev[cols + ['Oil_displacement', 'Energy_bev', 'Oil_use']]
                if not INCLUDE_VTYPES:
                    #set vehicle type to the transport type then sum again
                    ice_bev['Vehicle Type'] = t_type
                    ice_bev = ice_bev.groupby(cols).sum().reset_index()
                elif t_type == 'all':
                    #sum anyway, now weve clacualte energy use split by original transport types
                    ice_bev = ice_bev.groupby(cols).sum().reset_index()
                    cols.remove('Transport Type')
                #pivot vehile type so we have suffixes to determin which is which
                cols.remove('Vehicle Type')
                ice_bev = ice_bev.pivot(index=cols, columns='Vehicle Type', values=['Oil_displacement', 'Energy_bev', 'Oil_use'])
                #take away
                v_types = ice_bev.columns.get_level_values(1).unique()
                for v_type in v_types:
                    ice_bev[('Difference', v_type)] = ice_bev[('Oil_displacement', v_type)] - ice_bev[('Energy_bev', v_type)]
                #calculate total of oiol diaplcement and total of enrgybev
                ice_bev = ice_bev.assign(Total_oil_displacement = ice_bev['Oil_displacement'].sum(axis=1))
                ice_bev = ice_bev.assign(Total_energy_bev = ice_bev['Energy_bev'].sum(axis=1))
                ice_bev = ice_bev.assign(Total_oil_use = ice_bev['Oil_use'].sum(axis=1))

                # #if any differences arent positive then tell the user and skip
                # if any(ice_bev['Difference']<0):
                #     print('negative difference for {}'.format((economy, t_type, scenario, 'bev')))
                #     continue
                ############plotting
                if CHART_OPTION == 'stacked_area_with_difference':
                    plot_stacked_area_with_difference(config, ice_bev, v_types, color_map, default_save_folder,t_type,  economy, scenario,  AUTO_OPEN_PLOTLY_GRAPHS, drive = 'bev')
                elif CHART_OPTION == 'stacked_bar':
                    plot_stacked_bar(config, ice_bev, v_types, color_map, default_save_folder, t_type, economy, scenario, AUTO_OPEN_PLOTLY_GRAPHS, drive='bev', INCLUDE_OIL_USE=INCLUDE_OIL_USE)
                            

                ####################
                #FCEV:

                
                ice_fcev = plotting_data.copy()
                
                fcev = ice_fcev[ice_fcev['Drive']=='fcev']#later this willprobably need to include phev
                ice = ice_fcev[ice_fcev['Drive'].isin(['ice_g', 'ice_d'])]
                #grab avg of Efficiency Occupancy_or_load and Mileage and the sum of stocks            
                if t_type != 'all':
                    cols = ['Date', 'Vehicle Type']
                else:
                    cols = ['Date', 'Vehicle Type', 'Transport Type']    
                ice = ice.groupby(cols).apply(
                    lambda g: pd.Series({
                        'Stocks': g['Stocks'].sum(),  # Sum of Stocks
                        'Efficiency': weighted_avg(g, 'Efficiency', 'Stocks'),
                        'Occupancy_or_load': weighted_avg(g, 'Occupancy_or_load', 'Stocks'),
                        'Mileage': weighted_avg(g, 'Mileage', 'Stocks')
                    })).reset_index()
                # ice = ice.groupby(['Date', 'Vehicle Type']).agg({'Efficiency': 'mean', 'Occupancy_or_load': 'mean', 'Mileage': 'mean', 'Stocks': 'sum'}).reset_index()
                #set Drive to ice
                ice['Drive'] = 'ice'
                
                #join
                ice_fcev = pd.merge(ice, fcev, on=cols, suffixes=('_ice', '_fcev'))
                #now we have the data we can calculate oil use.
                
                # get vehicle types
                v_types = ice_fcev['Vehicle Type'].unique()
                #########################WARNING 
                #set efficiency for ice to 0.5 and efficiency for fcev to 1. just for testign
                # ice_fcev = ice_fcev.assign(Efficiency_ice = 0.5)
                # ice_fcev = ice_fcev.assign(Efficiency_fcev = 1)
                #########################WARNING 

                #oil use = efficiency * mileage * stocks
                ice_fcev = ice_fcev.assign(Oil_displacement = (ice_fcev['Mileage_fcev'] * ice_fcev['Stocks_fcev'])/ice_fcev['Efficiency_ice'])
                ice_fcev = ice_fcev.assign(Energy_fcev = (ice_fcev['Mileage_fcev'] * ice_fcev['Stocks_fcev'])/ice_fcev['Efficiency_fcev'])
                ice_fcev = ice_fcev.assign(Oil_use = (ice_fcev['Mileage_ice'] * ice_fcev['Stocks_ice'])/ice_fcev['Efficiency_ice'])
                #note that we are using the mileage of fcevs isteadn of ices. THis is probably not necessary to state as an assumption 
                #to make it easy to plot we want to pivot so we have the energy use of each vehicle type as a column for each other index col
                #so firt filter for only energy
                ice_fcev = ice_fcev[cols + ['Oil_displacement', 'Energy_fcev', 'Oil_use']]
                if not INCLUDE_VTYPES:
                    #set vehicle type to the transport type then sum again
                    ice_fcev['Vehicle Type'] = t_type
                    ice_fcev = ice_fcev.groupby(cols).sum().reset_index()
                elif t_type == 'all':
                    #sum anyway, now weve clacualte energy use split by original transport types
                    ice_fcev = ice_fcev.groupby(cols).sum().reset_index()
                    cols.remove('Transport Type')
                    
                #pivot vehile type so we have suffixes to determin which is which
                cols.remove('Vehicle Type')
                ice_fcev = ice_fcev.pivot(index=cols, columns='Vehicle Type', values=['Oil_displacement', 'Energy_fcev', 'Oil_use'])
                #take away
                v_types = ice_fcev.columns.get_level_values(1).unique()
                for v_type in v_types:
                    ice_fcev[('Difference', v_type)] = ice_fcev[('Oil_displacement', v_type)] - ice_fcev[('Energy_fcev', v_type)]
                #calculate total of oiol diaplcement and total of enrgyfcev
                ice_fcev = ice_fcev.assign(Total_oil_displacement = ice_fcev['Oil_displacement'].sum(axis=1))
                ice_fcev = ice_fcev.assign(Total_energy_fcev = ice_fcev['Energy_fcev'].sum(axis=1))
                ice_fcev = ice_fcev.assign(Total_oil_use = ice_fcev['Oil_use'].sum(axis=1))

                #if any differences are positive then tell the user and skip because this is not expected as fcev should be more efficient
                # if any(ice_fcev['Difference']<0):
                #     print('negative difference for {}'.format((economy, t_type, scenario, 'fcev')))
                #     continue

                ############plotting
                if CHART_OPTION == 'stacked_area_with_difference':
                    plot_stacked_area_with_difference(config, ice_fcev, v_types, color_map, default_save_folder,t_type,  economy, scenario,  AUTO_OPEN_PLOTLY_GRAPHS, drive = 'fcev')
                elif CHART_OPTION == 'stacked_bar':
                    plot_stacked_bar(config, ice_fcev, v_types, color_map, default_save_folder, t_type, economy, scenario, AUTO_OPEN_PLOTLY_GRAPHS, drive='fcev', INCLUDE_OIL_USE=INCLUDE_OIL_USE)

def plot_stacked_area_with_difference(config, df, v_types, color_map, default_save_folder, t_type, economy, scenario, AUTO_OPEN_PLOTLY_GRAPHS, drive):
    if drive == 'bev':
        fig = go.Figure()
        # first, an empty space
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['Total_energy_bev'],
            mode='lines',
            line_color='rgba(255, 255, 255, 0)',
            name='',
            stackgroup='one'  #this is necessary for the next traces to stack on top of this one
        ))
        # then, for each vehicle type, plot an area chart for the difference
        for v_type in v_types:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df[('Difference', v_type)],
                mode='none', # we don't want lines for individual vehicle types
                fill='tonexty', # fill to next y value
                fillcolor=color_map[f'{v_type} Oil displacement'], 
                #set opacity to 0.5
                opacity=0.01,
                name=f'{v_type} Oil displacement',
                stackgroup='one',  #this will stack the areas on top of each other                    
                hovertemplate=f'{v_type}'+'<br>%{y:.0f}PJ oil displaced'
            ))
        #removed oil displaceemtn line beecause it didnt seem useful
        # # finally, plot the 'Total_oil_displacement' line
        # fig.add_trace(go.Scatter(
        #     x=df.index,
        #     y=df['Total_oil_displacement'],
        #     mode='lines',
        #     line_color='Black',
        #     name='Oil displacement'
        # ))
        # finally, plot the 'Total_energy_bev' line
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['Total_energy_bev'],
            mode='lines',
            line_color='Green',
            name='BEV energy use'
        ))
        #add a y axis label
        fig.update_yaxes(title_text='PJ')
        fig.update_layout(title=f'Oil displacement for {t_type} in {economy} in {scenario} (BEV)')
        
        fig.write_html(config.root_dir + '\\' +f'{default_save_folder}\\oil_displacement_{t_type}_{economy}_bev_{scenario}.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
    elif drive == 'fcev':
        fig = go.Figure()
        # first, an empty space
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['Total_energy_fcev'],
            mode='lines',
            line_color='rgba(255, 255, 255, 0)',
            name='',
            stackgroup='one'  #this is necessary for the next traces to stack on top of this one
        ))
        # then, for each vehicle type, plot an area chart for the difference
        for v_type in v_types:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df[('Difference', v_type)],
                mode='none', # we don't want lines for individual vehicle types
                fill='tonexty', # fill to next y value
                fillcolor=color_map[f'{v_type} Oil displacement'], 
                #set opacity to 0.5
                opacity= 1,
                name=f'{v_type} Oil displacement',
                stackgroup='one',  #this will stack the areas on top of each other                    
                hovertemplate=f'{v_type}'+'<br>%{y:.0f}PJ oil displaced'
            ))
        # # finally, plot the 'Total_oil_displacement' line
        # fig.add_trace(go.Scatter(
        #     x=df.index,
        #     y=df['Total_oil_displacement'],
        #     mode='lines',
        #     line_color='Black',
        #     name='Oil displacement'
        # ))
        # finally, plot the 'Total_energy_fcev' line
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['Total_energy_fcev'],
            mode='lines',
            line_color='Green',
            name='FCEV energy use'
        ))
        #add a y axis label
        fig.update_yaxes(title_text='PJ')
        #give it a title:
        fig.update_layout(title=f'Oil displacement for {t_type} in {economy} in {scenario} (FCEV)')
        fig.write_html(config.root_dir + '\\' +f'{default_save_folder}\\oil_displacement_{t_type}_{economy}_fcev_{scenario}.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)

def plot_stacked_bar(config, df, v_types, color_map, default_save_folder, t_type, economy, scenario, AUTO_OPEN_PLOTLY_GRAPHS, drive, INCLUDE_OIL_USE):
    if drive == 'bev':
        #filter for the data in year_intervals if its not False:
        fig = go.Figure()
        for v_type in v_types:
            fig.add_trace(go.Bar(
                x=df.index,
                y=-df[('Oil_displacement', v_type)],
                name=f'{v_type} Oil displacement',
                marker_color=color_map[f'{v_type} Oil displacement']
            ))
            fig.add_trace(go.Bar(
                x=df.index,
                y=df[('Energy_bev', v_type)],
                name=f'{v_type} Energy BEV',
                marker_color=color_map[f'{v_type} Energy BEV']
            ))
            if INCLUDE_OIL_USE:
                fig.add_trace(go.Bar(
                    x=df.index,
                    y=df[('Oil_use', v_type)],
                    name=f'{v_type} Oil use',
                    marker_color=color_map[f'{v_type} Oil use']
                ))
        fig.update_layout(barmode='relative')
        fig.update_yaxes(title_text='PJ')
        fig.update_layout(title=f'Oil displacement for {t_type} in {economy} in {scenario} (BEV)', font_size=30)
        fig.write_html(config.root_dir + '\\' +f'{default_save_folder}\\BAR_oil_displacement_{t_type}_{economy}_bev_{scenario}.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
    if drive == 'fcev':
        fig = go.Figure()
        for v_type in v_types:
            fig.add_trace(go.Bar(
                x=df.index,
                y=-df[('Oil_displacement', v_type)],
                name=f'{v_type} Oil displacement',
                marker_color=color_map[f'{v_type} Oil displacement']
            ))
            fig.add_trace(go.Bar(
                x=df.index,
                y=df[('Energy_fcev', v_type)],
                name=f'{v_type} Energy FCEV',
                marker_color=color_map[f'{v_type} Energy FCEV']
            ))
            if INCLUDE_OIL_USE:
                fig.add_trace(go.Bar(
                    x=df.index,
                    y=df[('Oil_use', v_type)],
                    name=f'{v_type} Oil use',
                    marker_color=color_map[f'{v_type} Oil use']
                ))
        fig.update_layout(barmode='relative')
        fig.update_layout(title=f'Oil displacement for {t_type} in {economy} in {scenario} (FCEV)', font_size=30)
        fig.write_html(config.root_dir + '\\' +f'{default_save_folder}\\BAR_oil_displacement_{t_type}_{economy}_fcev_{scenario}.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
#%%
# ECONOMY_ID = '12_NZ'
# calculate_and_plot_oil_displacement(config, ECONOMY_ID, CHART_OPTION='stacked_bar', COMBINE_LPVS = True, bar_graph_year_intervals=[2025, 2035, 2050, 2070])


#%%

