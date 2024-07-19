# STILL TO DO
#need to do fuel mixes later
# detailed_fuels = energy_BASE_YEAR.merge(biofuel_blending_ratio, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
#is there a better way to to the new stock dist?


#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
from .. import utility_functions
from . import road_model_functions
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

def calculate_turnover_rate(config, df, k, L, x0):
    df['Turnover_rate'] = L / (1 + np.exp(-k * (df['Average_age'] - x0)))
    df['Turnover_rate'].fillna(0, inplace=True)
    return df

def load_non_road_model_data(config, ECONOMY_ID, USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD):
    """
    Loads the non-road model data for the specified economy.

    Args:
        ECONOMY_ID (str): The ID of the economy for which the data is being loaded.
        USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD (bool): Whether to use road activity growth rates to estimate non-road activity.

    Returns:
        pandas.DataFrame: A dataframe containing the non-road model data for the specified economy.
    """
    #load all data except activity data (which is calcualteed separately to other calcualted inputs)
    if USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD:
        growth_forecasts = pd.read_pickle(os.path.join(config.root_dir,  f'intermediate_data', 'road_model', f'{ECONOMY_ID}_final_road_growth_forecasts.pkl'))
    else:
        growth_forecasts = pd.read_csv(os.path.join(config.root_dir,  'intermediate_data', 'model_inputs', config.FILE_DATE_ID, f'{ECONOMY_ID}_growth_forecasts_wide.csv'))
    #load all other data
    non_road_model_input = pd.read_csv(os.path.join(config.root_dir,  'intermediate_data', 'model_inputs', config.FILE_DATE_ID, f'{ECONOMY_ID}_non_road_model_input_wide.csv'))

    #Merge growth forecasts with non_road_model_input:
    non_road_model_input.drop(columns=['Activity_growth'], inplace=True)
    non_road_model_input = non_road_model_input.merge(growth_forecasts[['Date', 'Economy','Scenario','Transport Type','Activity_growth']].drop_duplicates(), on=['Date', 'Economy','Scenario','Transport Type'], how='left')
    
    #load the parameters from the config file
    turnover_rate_parameters_dict = yaml.load(open(os.path.join(config.root_dir,  'config', 'parameters.yml')), Loader=yaml.FullLoader)['turnover_rate_parameters_dict']
    turnover_rate_steepness = turnover_rate_parameters_dict['turnover_rate_steepness_non_road']
    turnover_rate_max_value = turnover_rate_parameters_dict['turnover_rate_max_value_non_road']
    turnover_rate_midpoint = turnover_rate_parameters_dict['turnover_rate_midpoint_non_road']
        
    turnover_rate_midpoint_mult_adjustment_road_reference = yaml.load(open(os.path.join(config.root_dir,  'config', 'parameters.yml')), Loader=yaml.FullLoader)['TURNOVER_RATE_MIDPOINT_MULT_ADJUSTMENT_NON_ROAD_REFERENCE']
    turnover_rate_midpoint_mult_adjustment_road_target = yaml.load(open(os.path.join(config.root_dir,  'config', 'parameters.yml')), Loader=yaml.FullLoader)['TURNOVER_RATE_MIDPOINT_MULT_ADJUSTMENT_ROAD_TARGET']
    
    #extract the value for the economy, if it exists
    if ECONOMY_ID in turnover_rate_midpoint_mult_adjustment_road_reference.keys():
        turnover_rate_midpoint_mult_adjustment_road_reference = turnover_rate_midpoint_mult_adjustment_road_reference[ECONOMY_ID]
    else:
        turnover_rate_midpoint_mult_adjustment_road_reference = 1
    if ECONOMY_ID in turnover_rate_midpoint_mult_adjustment_road_target.keys():
        turnover_rate_midpoint_mult_adjustment_road_target = turnover_rate_midpoint_mult_adjustment_road_target[ECONOMY_ID]
    else:
        turnover_rate_midpoint_mult_adjustment_road_target = 1
        
    turnover_rate_midpoint_target = turnover_rate_midpoint * turnover_rate_midpoint_mult_adjustment_road_target
    turnover_rate_midpoint_reference = turnover_rate_midpoint * turnover_rate_midpoint_mult_adjustment_road_reference
    
    return non_road_model_input, turnover_rate_steepness, turnover_rate_midpoint_reference, turnover_rate_midpoint_target, turnover_rate_max_value
    

def run_non_road_model(config, ECONOMY_ID, USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD = True, USE_COVID_RELATED_MILEAGE_CHANGE = True):
    output_file_name = os.path.join(config.root_dir,  'intermediate_data', 'non_road_model', '{}_{}'.format(ECONOMY_ID, config.model_output_file_name))
    
    non_road_model_input, turnover_rate_steepness, turnover_rate_midpoint_reference, turnover_rate_midpoint_target, turnover_rate_max_value = load_non_road_model_data(config, ECONOMY_ID,USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD)
    
    non_road_model_input.sort_values(by=['Economy', 'Scenario','Transport Type','Date', 'Medium', 'Vehicle Type', 'Drive'])

    output_df = pd.DataFrame()
    
    for _, group in non_road_model_input.groupby(['Economy', 'Scenario','Transport Type']):
        #this group will contain categorical columns for Date, Medium, Vehicle Type and Drive. It will at times aggreagte them all (except for date, which will be looped through now)
        
        #add data for teh base year:
        previous_year = group[group.Date == non_road_model_input.Date.min()].copy().reset_index(drop=True)
        
        scenario = previous_year['Scenario'].iloc[0]
        transport_type = previous_year['Transport Type'].iloc[0]
        
        if scenario == 'Reference':
            turnover_rate_midpoint = turnover_rate_midpoint_reference
        elif scenario == 'Target':
            turnover_rate_midpoint = turnover_rate_midpoint_target
            
        previous_year = calculate_turnover_rate(config, previous_year, turnover_rate_steepness, turnover_rate_max_value, turnover_rate_midpoint)
        
        output_df = pd.concat([output_df,previous_year])
        
        for i in range(non_road_model_input.Date.min()+1, non_road_model_input.Date.max()+1):
            #getting negatives in age_distribution. so open them up and see if any are neggy:
            age_dist = previous_year['Age_distribution'].copy()
            for g in age_dist:
                try:
                    g = str(g).split(',')
                except:
                    breakpoint()
                g = [float(g) for g in g]
                if any([g < 0 for g in g]):
                    breakpoint()
            # previous_year = group[group.Date == i-1].copy().reset_index(drop=True)
            current_year = group[group.Date == i].copy().reset_index(drop=True)
            # current_year = group[group.Date == i].copy().sort_values(by=['Medium', 'Vehicle Type', 'Drive']).reset_index(drop=True)
            # #and reset the index of previous year, jsut in case
            # previous_year = previous_year.sort_values(by=['Medium', 'Vehicle Type', 'Drive']).reset_index(drop=True)
            # current_year=current_year[current_year.Drive=='ship_ammonia']
            #join to previous year and name all variables with _previous
            # if i == 2025 and transport_type == 'passenger':
            #     breakpoint()
            current_year = current_year.merge(previous_year, on=['Medium', 'Vehicle Type', 'Drive'], suffixes=('', '_previous'))
            # if transport_type == 'freight' and i ==2022 and scenario == 'Target':
            # breakpoint()#why is hsip ammonia popiing off>?
            #set average age to the previous year's average age
            current_year['Average_age'] = current_year['Average_age_previous']
            current_year['Age_distribution'] = current_year['Age_distribution_previous']
            
            current_year['Activity'] = current_year['Activity_previous'] * current_year['Activity_growth']
            
            #incorp covid_related_activity_change. THis will affect all mediums and will just increase activity to reflect a return to normal
            if USE_COVID_RELATED_MILEAGE_CHANGE:
                # breakpoint()
                # current_year = revert_covid_activity_decrease_non_road(ECONOMY_ID, current_year)
                if i<=2025 and transport_type == 'passenger':
                    
                    # print('1.a sum of value before increase in year {}: {}'.format(i, current_year.loc[(current_year['Economy'] == ECONOMY_ID) & (current_year['Transport Type'] == transport_type) & (current_year['Medium']=='air'), 'Activity'].sum()))
                    pass#breakpoint()
                if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                    print('WARNING: COVID-19 related mileage changes have not been implemented in a way that lends to 100% confidence for non-road transport. This will be implemented in a future version.')
                current_year = road_model_functions.adjust_mileage_to_account_for_covid(config, ECONOMY_ID, current_year, transport_type, i, measure_column='Stocks_previous')#'Activity') #MAYBE WE INCREASE STOCKS HERE??? WOULD SEPARATE IT BY MEDIUM THEN, I THINK. going TO TRY CHEATING IT BY ADJUSTING STOCKS. IT MIGHT HAVE WEIRD FLOW ON EFFECTS SO BE CAREFUL
                if i<=2025 and transport_type == 'passenger':
                    
                    # print('1.a sum of value after increase in year {}: {}'.format(i, current_year.loc[(current_year['Economy'] == ECONOMY_ID) & (current_year['Transport Type'] == transport_type) & (current_year['Medium']=='air'), 'Activity'].sum()))
                    pass#breakpoint()
            
            # if i == 2024 and transport_type == 'passenger':
            #     breakpoint()
            total_new_stocks_for_activity = ((current_year['Activity'] - current_year['Activity_previous']) / current_year['Activity_per_Stock']).sum()
            
            current_year = calculate_turnover_rate(config, current_year, turnover_rate_steepness, turnover_rate_max_value, turnover_rate_midpoint)
            current_year['Stock_turnover'] = (current_year['Stocks_previous'] * current_year['Turnover_rate']) 
            
            # if 'passenger' in _:
            #     breakpoint()
            total_sales_for_that_year = total_new_stocks_for_activity + current_year['Stock_turnover'].sum()
            
            #if total_sales_for_that_year is <0, then this si because of negative growth and we will just apply the % change in stocks equally to all stocks so that no stocks end up below 0:
            if total_sales_for_that_year < 0:
                #previous method was to find inverse and normalise but it got too complicated. This is a simpler method that will just apply the % change to all stocks equally. 
                percentage_change_in_stocks = total_sales_for_that_year / current_year['Stocks_previous'].sum()
                
                current_year['Not_needed_stocks'] = current_year['Stocks_previous'] * percentage_change_in_stocks#note that this will be negative
                current_year['New_stocks_needed'] = 0
                
                #make this loss in stocks into surplus so it can be sued in future years
                current_year['Surplus_stocks'] = -current_year['Not_needed_stocks'] + current_year['Surplus_stocks_previous']
                current_year['Surplus_stocks_used'] = 0
                
                current_year['Stocks'] = current_year['Stocks_previous'] - current_year['Stock_turnover'] - current_year['Not_needed_stocks']
            else:
                current_year['New_stocks_needed'] = total_sales_for_that_year * current_year['Vehicle_sales_share']
                
                current_year['Stocks'] = current_year['Stocks_previous'] - current_year['Stock_turnover'] + current_year['New_stocks_needed']
                
                current_year['Surplus_stocks_previous'] = current_year['Surplus_stocks_previous']
                current_year['Surplus_stocks'] = current_year['Surplus_stocks_previous'] 
                
                current_year[['Surplus_stocks_used', 'Surplus_stocks', 'New_stocks_needed']] = current_year.apply(road_model_functions.calculate_surplus_stocks, axis=1)
            
            #double check there are no stocks below 0. if so need to change something. maybe just put min=0 limit on
            if (current_year['Stocks'] < -0.0001).any():
                breakpoint()
                time.sleep(1)
                raise ValueError("There are stocks below 0. This should not happen.")
            #set any negative stocks to 0. they wont go negative again after being set to 0
            current_year['Stocks'] = current_year['Stocks'].apply(lambda x: 0 if x < 0 else x)
            if i == 2024 and transport_type == 'passenger':
                if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                    print('Just check this out, i thnk its solved but need to check')
                    breakpoint()#why is this causing activity to revert. ##29/may2024. what is this about?
            current_year['Activity'] = current_year['Stocks'] * current_year['Activity_per_Stock']

            #RECALCAULTE AGE DISTRIBUTION
            # current_year['New_stocks_needed'] = new_stocks
            # current_year['Surplus_stocks_used']  = surplus_stocks_used
            # current_year['Stock_turnover'] = stock_turnover
            try:
                current_year = road_model_functions.recalculate_age_distribution(config, current_year)
            except:
                breakpoint()
                current_year = road_model_functions.recalculate_age_distribution(config, current_year)
            current_year.drop(columns=['Surplus_stocks_used'], inplace=True)
            #check for any types of stocks that have stopped being used
            current_year['Average_age'] = np.where(current_year['Stocks'] > 0, current_year['Average_age'], np.nan)
            #set turnover rate to nan as well in that case:
            current_year['Turnover_rate'] = np.where(current_year['Stocks'] > 0, current_year['Turnover_rate'], np.nan)

            current_year['Intensity'] = current_year['Intensity_previous'] * (1/ current_year['Non_road_intensity_improvement'])#since increasing intensity is actually a 'worsening' of intensity, we need to divide by the improvement factor

            current_year['Energy'] = current_year['Activity'] * current_year['Intensity']

            #drop all the previous cols
            current_year.drop(columns=[col for col in current_year.columns if '_previous' in col], inplace=True)
            
            output_df = pd.concat([output_df, current_year])
            #set previous_year to current_year for next iteration
            previous_year = current_year.copy()

    #double check that the cols are what we expect:
    diff_cols = list(set(output_df.columns.to_list()) - set(config.NON_ROAD_MODEL_OUTPUT_COLS))
    if len(diff_cols) > 0:
        #drop the cols we dont want
        output_df.drop(columns=diff_cols, inplace=True)
        # raise ValueError("The columns in the output_df are not what we expect. {} are the extra cols. Please check the config file or any changes made to run_non_road_model.py".format(diff_cols))
    
    # output_df.to_csv(os.path.join(config.root_dir, 'a.csv'), index=False)
    output_df.to_csv(output_file_name, index=False)
    
    

# def revert_covid_activity_decrease_non_road(economy, current_year):
#     """Revert the decrease in activity due to covid. This is really jsut based off the same function for road, so might not be entirely accurate
    
#     Raises:
#         ValueError: _description_
#     """
#     for transport_type in ['passenger', 'freight']:
            
#         if transport_type =='passenger':
#             #load ECONOMIES_WITH_STOCKS_PER_CAPITA_REACHED from parameters.yml
#             EXPECTED_ENERGY_DECREASE_FROM_COVID_PASSENGER =  yaml.load(open(os.path.join(config.root_dir, 'config', 'parameters.yml')), Loader=yaml.FullLoader)['EXPECTED_ENERGY_DECREASE_FROM_COVID_PASSENGER']
#             X = EXPECTED_ENERGY_DECREASE_FROM_COVID_PASSENGER[economy]
#         elif transport_type =='freight':
#             EXPECTED_ENERGY_DECREASE_FROM_COVID_FREIGHT =  yaml.load(open(os.path.join(config.root_dir, 'config', 'parameters.yml')), Loader=yaml.FullLoader)['EXPECTED_ENERGY_DECREASE_FROM_COVID_FREIGHT']
#             X = EXPECTED_ENERGY_DECREASE_FROM_COVID_FREIGHT[economy]
        
#         #now revert decreaing mileage by a factor of 1-X
#         current_year.loc[(current_year['Transport Type'] == transport_type), 'Activity'] = current_year.loc[(current_year['Transport Type'] == transport_type),'Activity'] / (1 - X)
#     return current_year
    
#%%
# run_non_road_model(config, '01_AUS', USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD = True, USE_COVID_RELATED_MILEAGE_CHANGE = True)
#%#
