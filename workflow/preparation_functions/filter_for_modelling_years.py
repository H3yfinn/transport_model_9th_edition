
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
current_working_dir = os.getcwd()
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = re.split('transport_model_9th_edition', script_dir)[0] + 'transport_model_9th_edition'
if current_working_dir == script_dir: #this allows the script to be run directly or from the main.py file as you cannot use relative imports when running a script directly
    # Modify sys.path to include the directory where utility_functions is located
    sys.path.append(f"{root_dir}/workflow/utility_functions")
    sys.path.append(f"{root_dir}/config")
    import config
    import utility_functions
else:
    # Assuming the script is being run from main.py located at the root of the project, we want to avoid using sys.path.append and instead use relative imports 
    from ..utility_functions import *
    from ...config.config import *
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

def filter_for_modelling_years(BASE_YEAR, ECONOMY_ID, PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=False,ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=False):
    ###############################
    supply_side_fuel_mixing = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_aggregated_supply_side_fuel_mixing.csv'.format(config.FILE_DATE_ID,ECONOMY_ID))
    demand_side_fuel_mixing = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_aggregated_demand_side_fuel_mixing.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))
    road_model_input_wide = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_aggregated_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))
    non_road_model_input_wide = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_aggregated_non_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))
    growth_forecasts_wide = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_aggregated_growth_forecasts_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))
    #check for vehicle type = car, rive = bev, date = 2020, scenario = target
    # road_model_input_wide[(road_model_input_wide['Vehicle Type']=='car') & (road_model_input_wide['Drive']=='bev') & (road_model_input_wide['Date']==2020) & (road_model_input_wide['Scenario']=='Target')]
    
    # #filter for ECONOMY_ID:
    # road_model_input_wide = road_model_input_wide.loc[road_model_input_wide['Economy']==ECONOMY_ID]
    # non_road_model_input_wide = non_road_model_input_wide.loc[non_road_model_input_wide['Economy']==ECONOMY_ID]
    # growth_forecasts_wide = growth_forecasts_wide.loc[growth_forecasts_wide['Economy']==ECONOMY_ID]
    # demand_side_fuel_mixing = demand_side_fuel_mixing.loc[demand_side_fuel_mixing['Economy']==ECONOMY_ID]
    # supply_side_fuel_mixing = supply_side_fuel_mixing.loc[supply_side_fuel_mixing['Economy']==ECONOMY_ID]
    
    
    if PROJECT_TO_JUST_OUTLOOK_BASE_YEAR:
        #filter so the data is from config.OUTLOOK_BASE_YEAR and back
        # demand_side_fuel_mixing = demand_side_fuel_mixing[(demand_side_fuel_mixing['Date'] >= BASE_YEAR) & (demand_side_fuel_mixing['Date'] <= config.OUTLOOK_BASE_YEAR)]
        # supply_side_fuel_mixing = supply_side_fuel_mixing[(supply_side_fuel_mixing['Date'] >= BASE_YEAR) & (supply_side_fuel_mixing['Date'] <= config.OUTLOOK_BASE_YEAR)]
        road_model_input_wide = road_model_input_wide[(road_model_input_wide['Date'] >= BASE_YEAR) & (road_model_input_wide['Date'] <= config.OUTLOOK_BASE_YEAR)]
        non_road_model_input_wide = non_road_model_input_wide[(non_road_model_input_wide['Date'] >= BASE_YEAR) & (non_road_model_input_wide['Date'] <= config.OUTLOOK_BASE_YEAR)]
        growth_forecasts_wide = growth_forecasts_wide[(growth_forecasts_wide['Date'] >= BASE_YEAR) & (growth_forecasts_wide['Date'] <= config.OUTLOOK_BASE_YEAR)]
    elif ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR:
        
        #apply growth rates up to the outlook base year for all the growth rates that are in the model
        growth_columns_dict = {'New_vehicle_efficiency_growth':'New_vehicle_efficiency', 
        'Occupancy_or_load_growth':'Occupancy_or_load'}
        road_model_input_wide = apply_growth_up_to_outlook_BASE_YEAR(BASE_YEAR, road_model_input_wide,growth_columns_dict)
        growth_columns_dict = {'Non_road_intensity_improvement':'Intensity'}
        non_road_model_input_wide = apply_growth_up_to_outlook_BASE_YEAR(BASE_YEAR, non_road_model_input_wide,growth_columns_dict)
        
        # demand_side_fuel_mixing = demand_side_fuel_mixing[demand_side_fuel_mixing['Date'] >= config.OUTLOOK_BASE_YEAR]
        # supply_side_fuel_mixing = supply_side_fuel_mixing[supply_side_fuel_mixing['Date'] >= config.OUTLOOK_BASE_YEAR]
        road_model_input_wide = road_model_input_wide[road_model_input_wide['Date'] >= config.OUTLOOK_BASE_YEAR]
        non_road_model_input_wide = non_road_model_input_wide[non_road_model_input_wide['Date'] >= config.OUTLOOK_BASE_YEAR]
        
        growth_forecasts_wide = growth_forecasts_wide[growth_forecasts_wide['Date'] >= config.OUTLOOK_BASE_YEAR]
               
    ################################################################################
    
    return supply_side_fuel_mixing, demand_side_fuel_mixing, road_model_input_wide, non_road_model_input_wide, growth_forecasts_wide

#%%

def apply_growth_up_to_outlook_BASE_YEAR(BASE_YEAR, model_input_wide,growth_columns_dict):
    #calcualte values from BASE YEAR up to OUTLOOK BASE YEAR just in case they are needed. that is, calcualte New Vehicle Efficienecy as the prodcut of the New Vehicle Efficienecy Growth of range(BASE_YEAR, config.OUTLOOK_BASE_YEAR-1) * the New Vehicle Efficienecy in the BASE_YEAR. Do this for all the other growth rates too.

    for growth, value in growth_columns_dict.items():
        
        new_values = model_input_wide[(model_input_wide['Date'] >= BASE_YEAR) & (model_input_wide['Date'] <= config.OUTLOOK_BASE_YEAR)].copy()
        BASE_YEAR_values = model_input_wide[model_input_wide['Date'] == BASE_YEAR].copy()
        
        # replace any nans with 1
        new_values[growth] = new_values[growth].fillna(1)
        
        # Calculate cumulative product
        new_values[growth] = new_values.groupby(['Economy', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario'])[growth].transform('cumprod')
        #filter for latest Date only
        new_values = new_values[new_values['Date'] == config.OUTLOOK_BASE_YEAR]
        # Match base year value for each group and multiply with cumulative growth
        cum_growth = new_values[['Economy', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario', growth]].merge(BASE_YEAR_values[['Economy', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario', value]], on=['Economy', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario'])
        # if value == 'New_vehicle_efficiency':
        #     breakpoint()
        # Multiply cumulative growth with base year value
        cum_growth[value] = cum_growth[growth] * cum_growth[value]

        #make Date = config.OUTLOOK_BASE_YEAR as we want to save this value as the value used for the config.OUTLOOK_BASE_YEAR, so that in the first year forecasted (config.OUTLOOK_BASE_YEAR+1) we can use this value as the base year value
        cum_growth['Date'] = config.OUTLOOK_BASE_YEAR
        
        #merge and replace original value column with adjusted growth
        model_input_wide = model_input_wide.merge(cum_growth[['Economy', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario', 'Date', value]],on=['Economy', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario', 'Date'], how='left', suffixes=('', '_y'))

        # Replace original value column with adjusted growth
        model_input_wide[value] = model_input_wide[value+'_y'].fillna(model_input_wide[value])
        model_input_wide = model_input_wide.drop(columns=[value+'_y'])
    return model_input_wide

#%%
# supply_side_fuel_mixing, demand_side_fuel_mixing, road_model_input_wide, non_road_model_input_wide, growth_forecasts_wide = filter_for_modelling_years(2020, '19_THA')
# %%
