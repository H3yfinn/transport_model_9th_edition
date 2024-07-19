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

def filter_for_modelling_years(config, BASE_YEAR, ECONOMY_ID, PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=False, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=False):
    ###############################
    supply_side_fuel_mixing = pd.read_csv(os.path.join(config.root_dir, 'intermediate_data', 'model_inputs', config.FILE_DATE_ID, f'{ECONOMY_ID}_aggregated_supply_side_fuel_mixing.csv'))
    demand_side_fuel_mixing = pd.read_csv(os.path.join(config.root_dir, 'intermediate_data', 'model_inputs', config.FILE_DATE_ID, f'{ECONOMY_ID}_aggregated_demand_side_fuel_mixing.csv'))
    road_model_input_wide = pd.read_csv(os.path.join(config.root_dir, 'intermediate_data', 'model_inputs', config.FILE_DATE_ID, f'{ECONOMY_ID}_aggregated_road_model_input_wide.csv'))
    non_road_model_input_wide = pd.read_csv(os.path.join(config.root_dir, 'intermediate_data', 'model_inputs', config.FILE_DATE_ID, f'{ECONOMY_ID}_aggregated_non_road_model_input_wide.csv'))
    growth_forecasts_wide = pd.read_csv(os.path.join(config.root_dir, 'intermediate_data', 'model_inputs', config.FILE_DATE_ID, f'{ECONOMY_ID}_aggregated_growth_forecasts_wide.csv'))
    
    if PROJECT_TO_JUST_OUTLOOK_BASE_YEAR:
        road_model_input_wide = road_model_input_wide[(road_model_input_wide['Date'] >= BASE_YEAR) & (road_model_input_wide['Date'] <= config.OUTLOOK_BASE_YEAR)]
        non_road_model_input_wide = non_road_model_input_wide[(non_road_model_input_wide['Date'] >= BASE_YEAR) & (non_road_model_input_wide['Date'] <= config.OUTLOOK_BASE_YEAR)]
        growth_forecasts_wide = growth_forecasts_wide[(growth_forecasts_wide['Date'] >= BASE_YEAR) & (growth_forecasts_wide['Date'] <= config.OUTLOOK_BASE_YEAR)]
    elif ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR:
        growth_columns_dict = {
            'New_vehicle_efficiency_growth':'New_vehicle_efficiency', 
            'Occupancy_or_load_growth':'Occupancy_or_load'
        }
        road_model_input_wide = apply_growth_up_to_outlook_BASE_YEAR(config, BASE_YEAR, road_model_input_wide, growth_columns_dict)
        
        growth_columns_dict = {'Non_road_intensity_improvement':'Intensity'}
        non_road_model_input_wide = apply_growth_up_to_outlook_BASE_YEAR(config, BASE_YEAR, non_road_model_input_wide, growth_columns_dict)
        
        road_model_input_wide = road_model_input_wide[road_model_input_wide['Date'] >= config.OUTLOOK_BASE_YEAR]
        non_road_model_input_wide = non_road_model_input_wide[non_road_model_input_wide['Date'] >= config.OUTLOOK_BASE_YEAR]
        growth_forecasts_wide = growth_forecasts_wide[growth_forecasts_wide['Date'] >= config.OUTLOOK_BASE_YEAR]
               
    ################################################################################
    
    return supply_side_fuel_mixing, demand_side_fuel_mixing, road_model_input_wide, non_road_model_input_wide, growth_forecasts_wide

#%%

def apply_growth_up_to_outlook_BASE_YEAR(config, BASE_YEAR, model_input_wide, growth_columns_dict):
    for growth, value in growth_columns_dict.items():
        new_values = model_input_wide[(model_input_wide['Date'] >= BASE_YEAR) & (model_input_wide['Date'] <= config.OUTLOOK_BASE_YEAR)].copy()
        BASE_YEAR_values = model_input_wide[model_input_wide['Date'] == BASE_YEAR].copy()
        
        new_values[growth] = new_values[growth].fillna(1)
        new_values[growth] = new_values.groupby(['Economy', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario'])[growth].transform('cumprod')
        new_values = new_values[new_values['Date'] == config.OUTLOOK_BASE_YEAR]
        
        cum_growth = new_values[['Economy', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario', growth]].merge(BASE_YEAR_values[['Economy', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario', value]], on=['Economy', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario'])
        
        cum_growth[value] = cum_growth[growth] * cum_growth[value]
        cum_growth['Date'] = config.OUTLOOK_BASE_YEAR
        
        model_input_wide = model_input_wide.merge(cum_growth[['Economy', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario', 'Date', value]], on=['Economy', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario', 'Date'], how='left', suffixes=('', '_y'))
        model_input_wide[value] = model_input_wide[value+'_y'].fillna(model_input_wide[value])
        model_input_wide = model_input_wide.drop(columns=[value+'_y'])
    return model_input_wide

#%%
# supply_side_fuel_mixing, demand_side_fuel_mixing, road_model_input_wide, non_road_model_input_wide, growth_forecasts_wide = filter_for_modelling_years(config, 2020, '19_THA')
# %%
