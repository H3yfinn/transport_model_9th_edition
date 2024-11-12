#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
from os.path import join
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

#%%

def process_data(config, df, is_fuel=False):
    mean_value_cols = ['Activity_growth','Gdp_per_capita', 'Gdp', 'Population', 'Stocks_per_thousand_capita']
    weighted_mean_value_cols = ['Intensity','Occupancy_or_load', 'Turnover_rate', 'New_vehicle_efficiency', 'Efficiency','Mileage','Average_age']
    summable_value_cols = ['Activity', 'Energy', 'Stocks', 'Travel_km',  'Surplus_stocks','Vehicle_sales_share']
    other_cols = ['Age_distribution']
    non_road_df = df[df['Medium'] != 'road'].copy()
    non_road_df['Drive'] = 'all'

    for col in weighted_mean_value_cols:
        if col in non_road_df.columns:
            non_road_df[col] = non_road_df[col].multiply(non_road_df['Activity_growth'], axis='index')

    summable_value_cols_1 = [col for col in non_road_df.columns if col in summable_value_cols]
    mean_value_cols_1 = [col for col in non_road_df.columns if col in mean_value_cols]
    weighted_mean_value_cols_1 = [col for col in non_road_df.columns if col in weighted_mean_value_cols]

    agg_dict = {**{col: 'sum' for col in summable_value_cols_1 + weighted_mean_value_cols_1}, **{col: 'mean' for col in mean_value_cols_1}}

    group_cols = ['Date', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Medium']
    if is_fuel:
        group_cols.append('Fuel')

    grouped_df = non_road_df.groupby(group_cols).agg(agg_dict).reset_index()

    for col in weighted_mean_value_cols_1:
        grouped_df[col] = grouped_df[col].divide(grouped_df['Activity_growth'], axis='index')

    grouped_df = grouped_df.fillna(0)
    
    # def add_together_age_distributions(config, age_distribution):
    #     #take in age distribution col and add them together so the sum of stocks in each bin is the sum of the stocks in each bin of the input age distributions
    #     #drop any nans
    #     breakpoint()
    #     age_distribution = age_distribution.dropna()
    #     new_age_distribution = []
    #     for dist in age_distribution:
    #         dist = dist.split(',')
    #         dist = [float(i) for i in dist]
    #         #add the values in each bin together
    #         new_age_distribution = [sum(x) for x in zip(new_age_distribution, dist)]
    #     new_age_distribution = [str(i) for i in new_age_distribution]
    #     return ','.join(new_age_distribution)
    
    #handle other cols seperately:
    other_cols_1 = [col for col in non_road_df.columns if col in other_cols]
    other_cols_df = non_road_df[other_cols_1+group_cols].copy()
    for col in other_cols_1:
        if col =='Age_distribution':#need to add together the age distributions
            #if all age distributions are na then just skip
            if other_cols_df['Age_distribution'].isna().all():
                continue
            try:
                other_cols_age_dist = other_cols_df.groupby(group_cols)['Age_distribution'].agg(road_model_functions.combine_age_distributions).reset_index()
                grouped_df = grouped_df.merge(other_cols_age_dist, on=group_cols, how='left')
            except:
                breakpoint()
                raise ValueError('age distribution not combined correctly')
                # continue
        else:
            raise ValueError('other col not recognised')
    
    return pd.concat([df[df['Medium'] == 'road'], grouped_df])

def clean_non_road_drive_types(config, model_output_all_with_fuels, model_output_detailed, model_output_non_detailed):
    # Then you can use the function like this:
    new_model_output_all_with_fuels = process_data(config, model_output_all_with_fuels, is_fuel=True)
    new_model_output_detailed = process_data(config, model_output_detailed, is_fuel=False)
    new_model_output_non_detailed = process_data(config, model_output_non_detailed, is_fuel=False)
    
    #jsuty in case we make updates, mcalcaulte Stocks per thousand cpita again:
    new_model_output_detailed['Stocks_per_thousand_capita'] = (new_model_output_detailed['Stocks']/new_model_output_detailed['Population'])* 1000000
    return new_model_output_all_with_fuels,new_model_output_detailed,new_model_output_non_detailed 

def clean_model_output(config, ECONOMY_ID, model_output_with_fuel_mixing, model_output_all_df):
    #take in model ouput and clean ready to use in analysis
    model_output_all_with_fuels = model_output_with_fuel_mixing.copy()
    model_output_all = model_output_all_df.copy()
    
    #if frequncy col is in either datafrasme, drop it
    if 'Frequency' in model_output_all.columns:
        model_output_all.drop(columns=['Frequency'], inplace=True)
    if 'Frequency' in model_output_all_with_fuels.columns:
        model_output_all_with_fuels.drop(columns=['Frequency'], inplace=True)
        
    #create a detailed and non detailed output from the 'without fuels' dataframes. Then create a model output which is jsut energy use, with the fuels. 
    #detailed output can jsut be the current output, the non_deetailed can just have stocks, energy and activity data
    model_output_detailed = model_output_all.copy()
    model_output_non_detailed = model_output_all.copy()
    model_output_non_detailed = model_output_non_detailed[['Date', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Medium','Stocks', 'Activity', 'Energy']]

    #now create 'with fuels' output which will only contain energy use. This is to avoid any confusion because the 'with fuels' output contians activity and stocks replicated for each fuel type within a vehicel type / drive combination. 
    model_output_all_with_fuels = model_output_all_with_fuels[['Date', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Medium', 'Fuel',  'Energy']]

    #at sxoem point in the model we get rows full of ans. jsut drop them here for now:
    model_output_detailed = model_output_detailed.dropna(how='all')
    model_output_non_detailed = model_output_non_detailed.dropna(how='all')
    model_output_all_with_fuels = model_output_all_with_fuels.dropna(how='all')
    
    #dsrop where Drive or Vehicle type is 'all' and the mdeium s road
    model_output_detailed = model_output_detailed[~((model_output_detailed['Drive'] == 'all') & (model_output_detailed['Medium'] == 'road'))]
    model_output_non_detailed = model_output_non_detailed[~((model_output_non_detailed['Drive'] == 'all') & (model_output_non_detailed['Medium'] == 'road'))]
    model_output_all_with_fuels = model_output_all_with_fuels[~((model_output_all_with_fuels['Drive'] == 'all') & (model_output_all_with_fuels['Medium'] == 'road'))]
    
    
    #save data without the new drive cols for non road
    model_output_detailed.to_csv(os.path.join(config.root_dir, 'output_data', 'model_output_detailed', '{}_NON_ROAD_DETAILED_{}'.format(ECONOMY_ID, config.model_output_file_name)), index=False)

    model_output_non_detailed.to_csv(os.path.join(config.root_dir, 'output_data', 'model_output', '{}_NON_ROAD_DETAILED_{}'.format(ECONOMY_ID, config.model_output_file_name)), index=False)

    model_output_all_with_fuels.to_csv(os.path.join(config.root_dir, 'output_data', 'model_output_with_fuels', '{}_NON_ROAD_DETAILED_{}'.format(ECONOMY_ID, config.model_output_file_name)), index=False)
   
    model_output_all_with_fuels,model_output_detailed,model_output_non_detailed = clean_non_road_drive_types(config, model_output_all_with_fuels,model_output_detailed,model_output_non_detailed)
   
   
    #save data with the new drive cols for non road:
    
    model_output_detailed.to_csv(os.path.join(config.root_dir, 'output_data', 'model_output_detailed', '{}_{}'.format(ECONOMY_ID, config.model_output_file_name)), index=False)

    model_output_non_detailed.to_csv(os.path.join(config.root_dir, 'output_data', 'model_output', '{}_{}'.format(ECONOMY_ID, config.model_output_file_name)), index=False)

    model_output_all_with_fuels.to_csv(os.path.join(config.root_dir, 'output_data', 'model_output_with_fuels', '{}_{}'.format(ECONOMY_ID, config.model_output_file_name)), index=False)
      
    create_output_for_cost_modelling(config, model_output_detailed, ECONOMY_ID)
    

def concatenate_output_data(config):
    #concatenate all the other output data together
    model_output_detailed = pd.DataFrame()
    model_output_non_detailed = pd.DataFrame()
    model_output_all_with_fuels = pd.DataFrame()
    #and for NON_ROAD_DETAILED_ files:
    model_output_detailed_non_road = pd.DataFrame()
    model_output_non_detailed_non_road = pd.DataFrame()
    model_output_all_with_fuels_non_road = pd.DataFrame()
    not_all_economies = False
    for e in config.ECONOMY_LIST:
        if not os.path.exists(os.path.join(config.root_dir, 'output_data', 'model_output_detailed', '{}_{}'.format(e, config.model_output_file_name))):
            #find altest date available for the file:
            # get_latest_date_for_data_file(data_folder_path, file_name_start, file_name_end=None, EXCLUDE_DATE_STR_START=False)
            file_date_id_for_economy = utility_functions.get_latest_date_for_data_file(os.path.join(config.root_dir, 'output_data', 'model_output_detailed'), f"{e}_{config.model_output_file_name.replace(config.FILE_DATE_ID, '')}".strip('.csv'), '.csv')
            if file_date_id_for_economy is None:
                not_all_economies = True
                break
            model_output_detailed_economy = pd.read_csv(os.path.join(config.root_dir, 'output_data', 'model_output_detailed', '{}_{}'.format(e, config.model_output_file_name.replace(config.FILE_DATE_ID, file_date_id_for_economy))))
            model_output_non_detailed_economy = pd.read_csv(os.path.join(config.root_dir, 'output_data', 'model_output', '{}_{}'.format(e, config.model_output_file_name.replace(config.FILE_DATE_ID, file_date_id_for_economy))))
            model_output_all_with_fuels_economy = pd.read_csv(os.path.join(config.root_dir, 'output_data', 'model_output_with_fuels', '{}_{}'.format(e, config.model_output_file_name.replace(config.FILE_DATE_ID, file_date_id_for_economy))))
            
            #now for NON_ROAD_DETAILED_ files:
            model_output_detailed_non_road_economy = pd.read_csv(os.path.join(config.root_dir, 'output_data', 'model_output_detailed', '{}_NON_ROAD_DETAILED_{}'.format(e, config.model_output_file_name.replace(config.FILE_DATE_ID, file_date_id_for_economy))))
            model_output_non_detailed_non_road_economy = pd.read_csv(os.path.join(config.root_dir, 'output_data', 'model_output', '{}_NON_ROAD_DETAILED_{}'.format(e, config.model_output_file_name.replace(config.FILE_DATE_ID, file_date_id_for_economy))))
            model_output_all_with_fuels_non_road_economy = pd.read_csv(os.path.join(config.root_dir, 'output_data', 'model_output_with_fuels', '{}_NON_ROAD_DETAILED_{}'.format(e, config.model_output_file_name.replace(config.FILE_DATE_ID, file_date_id_for_economy))))
            
            model_output_detailed = pd.concat([model_output_detailed, model_output_detailed_economy])
            model_output_non_detailed = pd.concat([model_output_non_detailed, model_output_non_detailed_economy])
            model_output_all_with_fuels = pd.concat([model_output_all_with_fuels, model_output_all_with_fuels_economy])
            
            #concatenate the NON_ROAD_DETAILED_ dataframes
            model_output_detailed_non_road = pd.concat([model_output_detailed_non_road, model_output_detailed_non_road_economy])
            model_output_non_detailed_non_road = pd.concat([model_output_non_detailed_non_road, model_output_non_detailed_non_road_economy])
            model_output_all_with_fuels_non_road = pd.concat([model_output_all_with_fuels_non_road, model_output_all_with_fuels_non_road_economy])
        else:
            
            model_output_detailed_economy = pd.read_csv(os.path.join(config.root_dir, 'output_data', 'model_output_detailed', '{}_{}'.format(e, config.model_output_file_name)))
            
            model_output_non_detailed_economy = pd.read_csv(os.path.join(config.root_dir, 'output_data', 'model_output', '{}_{}'.format(e, config.model_output_file_name)))
            model_output_all_with_fuels_economy = pd.read_csv(os.path.join(config.root_dir, 'output_data', 'model_output_with_fuels', '{}_{}'.format(e, config.model_output_file_name)))
            
            #now for NON_ROAD_DETAILED_ files:
            model_output_detailed_non_road_economy = pd.read_csv(os.path.join(config.root_dir, 'output_data', 'model_output_detailed', '{}_NON_ROAD_DETAILED_{}'.format(e, config.model_output_file_name)))
            model_output_non_detailed_non_road_economy = pd.read_csv(os.path.join(config.root_dir, 'output_data', 'model_output', '{}_NON_ROAD_DETAILED_{}'.format(e, config.model_output_file_name)))
            model_output_all_with_fuels_non_road_economy = pd.read_csv(os.path.join(config.root_dir, 'output_data', 'model_output_with_fuels', '{}_NON_ROAD_DETAILED_{}'.format(e, config.model_output_file_name)))
            
            model_output_detailed = pd.concat([model_output_detailed, model_output_detailed_economy])
            model_output_non_detailed = pd.concat([model_output_non_detailed, model_output_non_detailed_economy])
            model_output_all_with_fuels = pd.concat([model_output_all_with_fuels, model_output_all_with_fuels_economy])
            
            #concatenate the NON_ROAD_DETAILED_ dataframes
            model_output_detailed_non_road = pd.concat([model_output_detailed_non_road, model_output_detailed_non_road_economy])
            model_output_non_detailed_non_road = pd.concat([model_output_non_detailed_non_road, model_output_non_detailed_non_road_economy])
            model_output_all_with_fuels_non_road = pd.concat([model_output_all_with_fuels_non_road, model_output_all_with_fuels_non_road_economy])
    
    if not_all_economies:
        print('Not all economies have been run, so not all data has been concatenated')
        return False
    #save the final df: 
    model_output_detailed.to_csv(os.path.join(config.root_dir, 'output_data', 'model_output_detailed', 'all_economies_{}_{}'.format(config.FILE_DATE_ID, config.model_output_file_name)), index=False)
    model_output_non_detailed.to_csv(os.path.join(config.root_dir, 'output_data', 'model_output', 'all_economies_{}_{}'.format(config.FILE_DATE_ID, config.model_output_file_name)), index=False)
    model_output_all_with_fuels.to_csv(os.path.join(config.root_dir, 'output_data', 'model_output_with_fuels', 'all_economies_{}_{}'.format(config.FILE_DATE_ID, config.model_output_file_name)), index=False)
    
    #save the final df: 
    model_output_detailed_non_road.to_csv(os.path.join(config.root_dir, 'output_data', 'model_output_detailed', 'all_economies_NON_ROAD_DETAILED_{}_{}'.format(config.FILE_DATE_ID, config.model_output_file_name)), index=False)
    model_output_non_detailed_non_road.to_csv(os.path.join(config.root_dir, 'output_data', 'model_output', 'all_economies_NON_ROAD_DETAILED_{}_{}'.format(config.FILE_DATE_ID, config.model_output_file_name)), index=False)
    model_output_all_with_fuels_non_road.to_csv(os.path.join(config.root_dir, 'output_data', 'model_output_with_fuels', 'all_economies_NON_ROAD_DETAILED_{}_{}'.format(config.FILE_DATE_ID, config.model_output_file_name)), index=False)
    return True

def create_output_for_cost_modelling(config, model_output_detailed, ECONOMY_ID):
    #create a version of the model output which is just the energy use, stocks and sales by vehicle type and drive. Later on we might also want to provid enegry use by fuel type so cost of fuel can be more precisely calculated (because of fuel mixing).
    model_output_detailed = model_output_detailed.loc[model_output_detailed['Medium']=='road'].copy()
    #keep only  some cols 
    model_output_detailed=model_output_detailed[['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Date', 'Drive', 'Stocks', 'Energy', 'New_stocks_needed']].groupby(['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Date', 'Drive']).sum().reset_index()
    
    #reanme New_stocks_needed to 'Sales'
    model_output_detailed = model_output_detailed.rename(columns={'New_stocks_needed':'Sales'})
    
    #save
    model_output_detailed.to_csv(os.path.join(config.root_dir, 'output_data', 'for_other_modellers', 'cost_estimation', '{}_{}_cost_inputs.csv'.format(config.FILE_DATE_ID, ECONOMY_ID)), index=False)
    return

def create_output_for_cost_modelling_from_old_data(config, model_output_detailed, ECONOMY_ID):
    #useful for when we want to use the old data to create the cost estimation files.
    #take in model output detailed and backcalc new stocks needed.
    stocks_9th = model_output_detailed.loc[model_output_detailed['Medium']=='road'].copy()
    
    index_cols = ['Economy',  'Scenario','Transport Type', 'Vehicle Type', 'Drive']
    stocks_9th = stocks_9th[index_cols +['Date', 'Stocks','Energy', 'Turnover_rate']].copy()
    
    #make turnover rate in min year 0
    stocks_9th.loc[stocks_9th['Date']==stocks_9th['Date'].min(),'Turnover_rate'] = 0
    
    #shift turnover back by one year so we can calculate the turnover for the previous year, usign the year afters turnover rate (this is jsut because of hwo the data is structured)
    breakpoint()
    stocks_9th['Turnover_rate'] = stocks_9th.groupby(index_cols)['Turnover_rate'].shift(-1)
    #calcaulte turnover for stocks 9th
    stocks_9th['Turnover'] = stocks_9th['Stocks'] * stocks_9th['Turnover_rate']
    
    #reaplce nans with 0
    stocks_9th['Turnover'] = stocks_9th['Turnover'].fillna(0)
    #calculate sales. First calcualte stocks after turnover by subtracting turnover from stocks. then calcalte sales by subtracting stocks after turnover from  stocks after turnover  from previous year:
    stocks_9th['stocks_after_turnover'] = stocks_9th['Stocks'] - stocks_9th['Turnover'] 
    
    #sales is the stocks before turnover in this year, minus the stocks after turnover in the previous year
    stocks_9th['previous_year_stocks_after_turnover'] = stocks_9th.groupby(index_cols)['stocks_after_turnover'].shift(1)
    stocks_9th['New_stocks_needed'] = np.maximum(0, stocks_9th['Stocks'] - stocks_9th['previous_year_stocks_after_turnover'])
    
    #now extract only cols we need:
    stocks_9th = stocks_9th[index_cols +['Date', 'Stocks','Energy', 'New_stocks_needed']].copy()
    
    #and sum up
    stocks_9th = stocks_9th.groupby(index_cols+['Date']).sum().reset_index()
    
    stocks_9th.to_csv(os.path.join(config.root_dir, 'output_data', 'for_other_modellers', 'cost_estimation', '{}_{}_cost_inputs_BASED_ON_OLD_DATA.csv'.format(config.FILE_DATE_ID, ECONOMY_ID)), index=False)
    
    return stocks_9th
    
#%%

# ECONOMY_ID='08_JPN'
# model_output_all=pd.read_pickle('intermediate_data', 'analysis_single_use', '{}_model_output_all.pkl'.format(ECONOMY_ID))
# model_output_with_fuel_mixing=pd.read_pickle('intermediate_data', 'analysis_single_use', '{}_model_output_with_fuel_mixing.pkl'.format(ECONOMY_ID))
# clean_model_output(config, ECONOMY_ID, model_output_with_fuel_mixing, model_output_all)

# model_output_detailed = pd.read_csv(os.path.join(config.root_dir, '19_THA_model_output20230902.csv'))
# ECONOMY_ID = '19_THA'
# stocks_9th = create_output_for_cost_modelling_from_old_data(config, model_output_detailed,ECONOMY_ID)




# %%
