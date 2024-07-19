#this will apply any fuel mixing on the supply side. This is currently only biofuel mixing to petroleum products but could include other fuel types in the future

#this will merge a fuel sharing dataframe onto the model output, by the fuel column, and apply the shares by doing that. There will be a new fuel column after this

#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
from .. import utility_functions
from .. import plotting_functions
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
def create_supply_side_fuel_mixing_input(config, ECONOMY_ID, X_ORDER='linear', AUTO_OPEN=False, PLOT=False):
            
    #load model concordances with fuels
    model_concordances_fuels = pd.read_csv(os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', config.model_concordances_file_name_fuels))
    #filter for the Economy id
    model_concordances_fuels = model_concordances_fuels[model_concordances_fuels['Economy'] == ECONOMY_ID]
    
    mixing_assumptions = pd.read_excel(os.path.join(config.root_dir, 'input_data', 'fuel_mixing_assumptions.xlsx'), sheet_name='supply_side')
    #drop comment col
    mixing_assumptions.drop(columns=['Comment'], inplace=True)
    #cols Region	Fuel	New_fuel	Date	Reference	Target

    regions = pd.read_excel(os.path.join(config.root_dir, 'input_data', 'fuel_mixing_assumptions.xlsx'), sheet_name='regions')

    #####################################
    #TEST
    #check the regions in regions_passenger and regions_freight are the same as in passenger_drive_shares and freight_drive_shares, also check that the regions in vehicle_type_growth_regions are the same as in vehicle_type_growth
    user_input_creation_functions.check_region(config, regions, mixing_assumptions)

    #####################################
    #convert regions to economys
    mixing_assumptions = pd.merge(mixing_assumptions, regions, how='left', on='Region')
    #filter for the economy
    mixing_assumptions = mixing_assumptions.loc[mixing_assumptions['Economy'] == ECONOMY_ID]
    ############################
    #check for any nas, which will be caused by regions not being in the regions sheet:
    if mixing_assumptions.Region.isna().any():
        #get the regions that are not in the regions sheet
        missing_region = mixing_assumptions.Region[mixing_assumptions.Region.isna()].unique().tolist()
        raise ValueError('The following regions are not in the regions sheet for fuel mixing on supply side: {}'.format(missing_region))
    
    #check for duplicates when we ignore the scenarios cols (so we can make sure were not setting two supply side fuel shares for the same Economy, Fuel, New_fuel, Date, Region combination)
    dupes = mixing_assumptions[mixing_assumptions.duplicated(subset=['Economy', 'Fuel', 'New_fuel', 'Date', 'Region'], keep=False)]
    if len(dupes) > 0:
        breakpoint()
        time.sleep(1)
        raise ValueError('There are duplicate rows in the fuel mixing assumptions sheet for the same Economy, Fuel, New_fuel, Date, Region combination. Please check the fuel mixing assumptions sheet for the Economy, Fuel, New_fuel, Date, Region combinations and make sure there is only one row for each Economy, Fuel, New_fuel, Date, Region combination. \n {}'.format(dupes))
    
    #also check that no values in Fuel or New_fuel are different to what is in the model concordances
    fuel_diff = mixing_assumptions[~mixing_assumptions['Fuel'].isin(model_concordances_fuels['Fuel'])]
    if len(fuel_diff) > 0:
        breakpoint()
        raise ValueError('The following fuels are in the fuel mixing assumptions sheet but not in the model concordances: {}'.format(fuel_diff['Fuel'].unique().tolist()))
    new_fuel_diff = mixing_assumptions[~mixing_assumptions['New_fuel'].isin(model_concordances_fuels['Fuel'])]
    if len(new_fuel_diff) > 0:
        breakpoint()
        raise ValueError('The following new fuels are in the fuel mixing assumptions sheet but not in the model concordances: {}'.format(new_fuel_diff['New_fuel'].unique().tolist()))
    ############################
    #drop region
    mixing_assumptions.drop(columns=['Region'], inplace=True)

    #melt so Scenario is a column
    mixing_assumptions = pd.melt(mixing_assumptions, id_vars=['Economy', 'Fuel', 'New_fuel', 'Date'], var_name='Scenario', value_name='Supply_side_fuel_share')
    #drop nas
    mixing_assumptions.dropna(inplace=True)
    mixing_assumptions.drop_duplicates(inplace=True)
    #Start filling in fuel mixing using the demand side fuel mixes to start with
    supply_side_fuel_mixing = model_concordances_fuels.copy()
    #first join so we have the New Fuels col, non dependent of Date
    supply_side_fuel_mixing = pd.merge(supply_side_fuel_mixing, mixing_assumptions[['Economy', 'Fuel', 'New_fuel', 'Scenario']], how='inner', on=['Economy', 'Fuel', 'Scenario']).drop_duplicates()

    supply_side_fuel_mixing_intermediate = supply_side_fuel_mixing.copy()

    #then join so we have the Supply Side fuel share col, so join on the Date
    supply_side_fuel_mixing = pd.merge(supply_side_fuel_mixing, mixing_assumptions, how='left', on=['Economy', 'Fuel', 'Date', 'New_fuel','Scenario'])

    cols = supply_side_fuel_mixing.columns.tolist()
    cols.remove('Supply_side_fuel_share')
    cols_no_date = cols.copy()
    cols_no_date.remove('Date')
    #now sort by economy, fuel,New_fuel, scenario, date and fill Supply_side_fuel_share using an interpoaltion and a bfill
    supply_side_fuel_mixing.sort_values(by=cols, inplace=True)

    
    ########################################
    #
    EXPAND_DATES=False#found out it doesnt do much ):
    if EXPAND_DATES:

        #add more vlaue in x axis so the interp is smoother. then remove them after 
        # Define the multiplier for the x-axis values
        x_axis_length_multiplier = 3

        # Function to add expanded dates for each group
        def add_expanded_dates(group, multiplier):
            #set date to float
            group['Date'] = group['Date'].astype(float)
            original_dates = group['Date'].unique()
            additions = np.arange(0, multiplier) / 10
            expanded_dates = np.repeat(original_dates, len(additions)) + np.tile(additions, len(original_dates))
            expanded_group = pd.DataFrame({'Date': expanded_dates})
            expanded_group = pd.merge(expanded_group, group, on='Date', how='left')
            return expanded_group

        # Apply the function to add expanded dates to each group in the DataFrame
        supply_side_fuel_mixing_expanded = supply_side_fuel_mixing.groupby(cols_no_date, group_keys=False).apply(lambda group: add_expanded_dates(group, x_axis_length_multiplier)).reset_index(drop=True)

        # Sort values by the necessary columns to prepare for interpolation
        supply_side_fuel_mixing_expanded.sort_values(by=cols, inplace=True)
    else:
        supply_side_fuel_mixing_expanded = supply_side_fuel_mixing.copy()
    if X_ORDER == 'linear':
        # Interpolate on the expanded x-axis
        supply_side_fuel_mixing_expanded['Supply_side_fuel_share'] = supply_side_fuel_mixing_expanded.groupby(cols_no_date, group_keys=False)['Supply_side_fuel_share'].apply(lambda group: group.interpolate(method='linear', limit_area='inside'))
    else:
        #do interpolation using spline and order = X
        supply_side_fuel_mixing_expanded['Supply_side_fuel_share'] = supply_side_fuel_mixing_expanded.groupby(cols_no_date, group_keys=False)['Supply_side_fuel_share'].apply(lambda group: group.interpolate(method='spline', order=X_ORDER, limit_area='inside'))

    if EXPAND_DATES:
        # Filter out the intermediate x-axis values to return to original granularity
        supply_side_fuel_mixing = supply_side_fuel_mixing_expanded[supply_side_fuel_mixing_expanded['Date'] % 1 == 0].copy()
        #set date back to int
        supply_side_fuel_mixing['Date'] = supply_side_fuel_mixing['Date'].astype(int).copy()
    else:
        supply_side_fuel_mixing = supply_side_fuel_mixing_expanded.copy()
        
    supply_side_fuel_mixing['Supply_side_fuel_share'] = supply_side_fuel_mixing.groupby(cols_no_date, group_keys=False)['Supply_side_fuel_share'].apply(lambda x: x.ffill())
    supply_side_fuel_mixing['Supply_side_fuel_share'] = supply_side_fuel_mixing.groupby(cols_no_date, group_keys=False)['Supply_side_fuel_share'].apply(lambda x: x.bfill())
    ########################################
        
    #reaplce any nas with 0
    supply_side_fuel_mixing['Supply_side_fuel_share'].fillna(0, inplace=True)
    
    #make sure that the sum of the supply side fuel shares is between 0 and 1 for each Economy, Fuel, Scenario, Date
    supply_side_fuel_mixing_sums = supply_side_fuel_mixing.groupby(['Economy', 'Fuel', 'Scenario', 'Drive', 'Medium', 'Vehicle Type', 'Transport Type', 'Date'])['Supply_side_fuel_share'].sum().reset_index().copy()
    MIN_THRESHOLD = -0.1
    supply_side_fuel_mixing_sums = supply_side_fuel_mixing_sums[(supply_side_fuel_mixing_sums['Supply_side_fuel_share'] < MIN_THRESHOLD) | (supply_side_fuel_mixing_sums['Supply_side_fuel_share'] > 1- MIN_THRESHOLD)]
    if len(supply_side_fuel_mixing_sums) > 0:
        breakpoint()
        time.sleep(1)
        raise ValueError('The supply side fuel shares are less than 0 for the rows below. Please check the fuel mixing assumptions sheet for the Economy, Fuel, Scenario, Date combinations and make sure the sum of the supply side fuel shares is between 0 and 1 for each Economy, Fuel, Scenario, Date. \n {}'.format(supply_side_fuel_mixing_sums))
    else:
        #set any values less than 0 to 0 and any values greater than 1 to 1
        supply_side_fuel_mixing['Supply_side_fuel_share'] = np.where(supply_side_fuel_mixing['Supply_side_fuel_share'] < 0, 0, supply_side_fuel_mixing['Supply_side_fuel_share'])
        supply_side_fuel_mixing['Supply_side_fuel_share'] = np.where(supply_side_fuel_mixing['Supply_side_fuel_share'] > 1, 1, supply_side_fuel_mixing['Supply_side_fuel_share'])
    
    #archive previous results:
    archiving_folder = archiving_scripts.create_archiving_folder_for_FILE_DATE_ID(config)
    
    #save the variables we used to calculate the data by savinbg the 'input_data\\vehicle_sales_share_inputs.xlsx' file
    shutil.copy(os.path.join(config.root_dir, 'input_data', 'fuel_mixing_assumptions.xlsx'), os.path.join(archiving_folder, 'fuel_mixing_assumptions.xlsx'))

    #save as user input csv
    supply_side_fuel_mixing.to_csv(os.path.join(config.root_dir, 'intermediate_data', 'model_inputs', config.FILE_DATE_ID, '{}_supply_side_fuel_mixing.csv'.format(ECONOMY_ID)), index=False)

    if PLOT:
        plotting_functions.plot_user_input_data.plot_supply_side_fuel_mixing(config, supply_side_fuel_mixing,ECONOMY_ID, AUTO_OPEN=AUTO_OPEN)
    
#%%
# create_supply_side_fuel_mixing_input(config, '10_MAS', X_ORDER='linear', AUTO_OPEN=True)
# %%