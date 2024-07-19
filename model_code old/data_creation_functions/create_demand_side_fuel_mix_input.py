#this will apply any fuel mixing on the demand side. It contains the use of different fule types for each drive type, for example, electricity vs oil in phev's, or even treating rail as a drive type, and splitting demand into electricity, coal and dieel rpoprtions. 
#This could include any mixing, even biofuels, but is intended for use from the perspective of the demand side only. If you do include biofuels in this mix, you will have to remove it from the supply side mixing.
#Once finished this will merge a fuel mixing dataframe onto the model output, by the Drive column, and apply the shares by doing that, resulting in a fuel column.
#this means that the supply side fuel mixing needs to occur after this script, because it will be merging on the fuel column.

#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
from .. import utility_functions
from ..plotting_functions import plot_user_input_data
from .. import archiving_scripts
from . import user_input_creation_functions
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
#%%

#create fake user input for demand side fuel mixes using model concordances

def create_demand_side_fuel_mixing_input(config, ECONOMY_ID, X_ORDER = 1):
    """Could do with some fixing up but for now it works"""
    #load model concordances for filling in 
    model_concordances_fuels = pd.read_csv(config.root_dir + config.slash + 'intermediate_data\\computer_generated_concordances\\{}'.format(config.model_concordances_file_name_fuels))
    #filter for the Economy id
    model_concordances_fuels = model_concordances_fuels[model_concordances_fuels['Economy'] == ECONOMY_ID]
    #keep only the cols ['Date', 'Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive', 'Scenario', 'Fuel']
    model_concordances_fuels = model_concordances_fuels[['Date', 'Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive', 'Scenario', 'Fuel']].drop_duplicates()
    
    mixing_assumptions = pd.read_excel(config.root_dir + config.slash + 'input_data\\fuel_mixing_assumptions.xlsx',sheet_name='demand_side')
    #drop comment col
    mixing_assumptions.drop(columns=['Comment'], inplace=True)
    #cols Region	Fuel	New_fuel	Date	Reference	Target

    regions = pd.read_excel(config.root_dir + config.slash + 'input_data\\fuel_mixing_assumptions.xlsx',sheet_name='regions_demand_side')
    
    #####################################
    #TEST
    #check the regions in regions_passenger and regions_freight are the same as in passenger_drive_shares and freight_drive_shares, also check that the regions in vehicle_type_growth_regions are the same as in vehicle_type_growth
    user_input_creation_functions.check_region(config, regions, mixing_assumptions)

    #####################################
    
    #convert regions to economys
    mixing_assumptions = pd.merge(mixing_assumptions, regions, how='left', on='Region')
    #filter for the economy
    mixing_assumptions = mixing_assumptions.loc[mixing_assumptions['Economy'] == ECONOMY_ID]
    
    #check for duplicates (so we can make sure were not setting two demand side fuel shares for the same Date	Region	Vehicle Type	Medium	Transport Type	Drive	Fuel)
    dupes = mixing_assumptions[mixing_assumptions.duplicated(subset=['Date', 'Region', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive',  'Fuel'], keep=False)]
    if len(dupes) > 0:
        breakpoint()
        time.sleep(1)
        raise ValueError('There are duplicate rows in the demand side fuel mixing assumptions sheet for the same Date	Region	Vehicle Type	Medium	Transport Type	Drive	Fuel	Demand_side_fuel_share combination. Please check the fuel mixing assumptions sheet make sure there is only one row for each combination. \n {}'.format(dupes))
    
    #drop region
    mixing_assumptions.drop(columns=['Region'], inplace=True)
    mixing_assumptions.drop_duplicates(inplace=True)
    
    #melt so Scenario is a column
    mixing_assumptions = pd.melt(mixing_assumptions, id_vars=['Date', 'Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive',  'Fuel'], var_name='Scenario', value_name='Demand_side_fuel_share')
    
    #drop nas
    mixing_assumptions.dropna(inplace=True)
    ########################################
    #make sure that the sum of the demand side fuel shares is 1 for each 'Date', 'Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive', 'Scenario'
    test = mixing_assumptions.groupby(['Date', 'Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive', 'Scenario'])['Demand_side_fuel_share'].sum().reset_index().copy()
    test = test[(test['Demand_side_fuel_share'] != 1)]
    if len(test) > 0:
        breakpoint()
        time.sleep(1)
        raise ValueError('The demand side fuel shares are not 1 for the rows below. Please check the fuel mixing assumptions sheet for the combinations and make sure the sum of the demand side fuel shares is 1 for each [Date, Economy, Vehicle Type, Medium, Transport Type, Drive, Scenario] grouping. \n {}'.format(test))
    ########################################
    #the process will run like:
    #load in fuel concrdacnes, left merge it on mixing_assumptions, and then do a right on all columns except date to remove non matching rows so we only have the rows that match the cols Economy	Vehicle Type	Medium	Transport Type	Drive	Scenario, 'Fuel'	but we ahve every possible date and fuel for those rows. 
    #then grouping by the cols Economy	Vehicle Type	Medium	Transport Type	Drive	Scenario Fuel, we will interpoalte the fuel shares for each date. Then ffill and bfill to fill in the fuel shares for the years on the outsides. then where there are nas, we will fill with 0.
    
    demand_side_fuel_mixing = model_concordances_fuels.copy()
    demand_side_fuel_mixing = pd.merge(demand_side_fuel_mixing, mixing_assumptions, on = ['Date', 'Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive', 'Scenario', 'Fuel'], how='left')
    
    demand_side_fuel_mixing = pd.merge(demand_side_fuel_mixing, mixing_assumptions[['Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive', 'Scenario', 'Fuel']].drop_duplicates(), on = ['Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive', 'Scenario', 'Fuel'], how='right')
    ########################################
    #now sort and then interpoalte
    demand_side_fuel_mixing = demand_side_fuel_mixing.sort_values(by=['Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive', 'Scenario', 'Fuel', 'Date'])
    
    if X_ORDER == 'linear':
        #do interpolation using spline and order = X
        demand_side_fuel_mixing['Demand_side_fuel_share'] = demand_side_fuel_mixing.groupby(['Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive', 'Scenario', 'Fuel'], group_keys=False)['Demand_side_fuel_share'].apply(lambda group: group.interpolate(method='linear', limit_area='inside'))
    else:
        #do interpolation using spline and order = X
        demand_side_fuel_mixing['Demand_side_fuel_share'] = demand_side_fuel_mixing.groupby(['Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive', 'Scenario', 'Fuel'], group_keys=False)['Demand_side_fuel_share'].apply(lambda group: group.interpolate(method='spline', order=X_ORDER, limit_area='inside'))
        
    demand_side_fuel_mixing['Demand_side_fuel_share'] = demand_side_fuel_mixing.groupby(['Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive', 'Scenario', 'Fuel'], group_keys=False)['Demand_side_fuel_share'].apply(lambda x: x.ffill())
    demand_side_fuel_mixing['Demand_side_fuel_share'] = demand_side_fuel_mixing.groupby(['Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive', 'Scenario', 'Fuel'], group_keys=False)['Demand_side_fuel_share'].apply(lambda x: x.bfill())
    #drop any nas as they are just fuels where there is no use of the fuel
    demand_side_fuel_mixing = demand_side_fuel_mixing.dropna()
    ########################################
    
    #do some nromalisation to make sure that the sum of the demand side fuel shares is 1 for each set of 'Economy',  'Scenario', 'Drive', 'Medium', 'Vehicle Type', 'Transport Type', 'Date'
    demand_side_fuel_mixing['Demand_side_fuel_share'] = demand_side_fuel_mixing.groupby(['Economy', 'Scenario', 'Drive', 'Medium', 'Vehicle Type', 'Transport Type', 'Date'], group_keys=False)['Demand_side_fuel_share'].apply(lambda x: x/x.sum())
    
    ########################################    
    #to handle years that are before the config.DEFAULT_BASE_YEAR, jsut carry the fuel shares backwards for 10 years
    data_base_minus_10 = demand_side_fuel_mixing.copy()
    data_base_minus_10 = data_base_minus_10[data_base_minus_10['Date'] == config.DEFAULT_BASE_YEAR+1]
    demand_side_fuel_mixing_minus_10 = pd.DataFrame()
    for year in range(config.DEFAULT_BASE_YEAR-10, config.DEFAULT_BASE_YEAR-1):
        data_base_minus_10['Date'] = year
        demand_side_fuel_mixing_minus_10 = pd.concat([demand_side_fuel_mixing_minus_10, data_base_minus_10], axis=0, ignore_index=True)
    #concat onto demand_side_fuel_mixing
    demand_side_fuel_mixing = pd.concat([demand_side_fuel_mixing, demand_side_fuel_mixing_minus_10], axis=0, ignore_index=True)

    
    #####################
    #save as user input csv
    
    demand_side_fuel_mixing.to_csv(config.root_dir + config.slash + 'intermediate_data\\model_inputs\\{}\\{}_demand_side_fuel_mixing.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
    plot_user_input_data.plot_demand_side_fuel_mixing(config, demand_side_fuel_mixing,ECONOMY_ID)
    
#%%
# create_demand_side_fuel_mixing_input(config, '08_JPN')
    
#%%
    