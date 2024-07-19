#the point of this file is to calculate extra variables that may be needed by the model, for example travel_km_per_stock or nromalised stock sales etc.
#these varaibles are essentially the same varaibles which will be calcualted in the model as these variables act as the base year variables.
# 
# #to do: 
#remove scenario from data in all data for the base year as that is intended to be independent of the sceanrio. This will mean adding the scenario in the actual model.
#%%
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
#%%
def aggregate_data_for_model(config, ECONOMY_ID, REPLACE_ZEROS_WITH_AVGS_FROM_DIFFERENT_DATES_FOR_FACTOR_MEASURES=True, REPLACE_NAS_WITH_ZEROS=True, REPLACE_ZEROS_WITH_ONES_IN_GROWTH_VALUES=True):
    #load data from transport datasystem
    new_transport_dataset = pd.read_csv(os.path.join(config.root_dir, 'intermediate_data', 'model_inputs', 'transport_data_system_extract.csv'))
    user_input = pd.read_csv(os.path.join(config.root_dir, 'intermediate_data', 'model_inputs', f'{ECONOMY_ID}_user_inputs_and_growth_rates.csv'))
    growth = pd.read_csv(os.path.join(config.root_dir, 'intermediate_data', 'model_inputs', 'regression_based_growth_estimates.csv'))
    
    # #drop age from new_transport_dataset
    # new_transport_dataset = new_transport_dataset.loc[new_transport_dataset['Measure']!='Average_age']
    # new_transport_dataset[(new_transport_dataset['Vehicle Type']=='car') & (user_input['Drive']=='bev') & (new_transport_dataset['Date']==2020) & (new_transport_dataset['Scenario']=='Target')]
    # growth[(growth['Transport Type']=='freight') & (growth['Measure']=='Activity_growth') & (growth['Date']==2021) & (growth['Scenario']=='Target')]
    #filter for {ECONOMY_ID} in Economy column
    new_transport_dataset = new_transport_dataset.loc[new_transport_dataset['Economy'] == ECONOMY_ID]
    growth = growth.loc[growth['Economy'] == ECONOMY_ID]
    
    #create Dataset column in user input and call it 'user_input'
    user_input['Dataset'] = 'user_input'
    #same for growth but call it 'growth_forecasts'
    growth['Dataset'] = 'growth_forecasts'

    #filter fvor only nans in value col and print what measures they are from. iof they are jsut ['Activity_growth_8th' 'Activity_growth_8th_index'] then ignore, else throw an error and fix the nans
    if growth.loc[growth['Value'].isna(), 'Measure'].unique().tolist() != ['Activity_growth_8th', 'Activity_growth_8th_index']:
        nans= growth.loc[growth['Value'].isna(), 'Measure'].unique().tolist()
        if 'Activity_growth_8th' in nans:
            nans.remove('Activity_growth_8th')
        if 'Activity_growth_8th_index' in nans:
            nans.remove('Activity_growth_8th_index')
        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
            print('These measures contains nans in the value column. They will be ignored in the model. Please check the data and fix the nans if you want to use them in the model. ', nans)
    
    #concat user inputs to transport dataset
    aggregated_model_data = pd.concat([new_transport_dataset, user_input], sort=False)
    #concat growth to transport dataset
    aggregated_model_data = pd.concat([aggregated_model_data, growth], sort=False)
    
    #make sure that the data is in the right format. We will have date as int, value as float and all others as objects. if there si an error, then something is probably wrong with the data
    aggregated_model_data['Date'] = aggregated_model_data['Date'].astype(int)
    aggregated_model_data['Value'] = aggregated_model_data['Value'].astype(float)
    other_cols = aggregated_model_data.columns.tolist()
    other_cols.remove('Date')
    other_cols.remove('Value')
    aggregated_model_data[other_cols] = aggregated_model_data[other_cols].astype(str)

    #convert 'nan' to np.nan
    aggregated_model_data = aggregated_model_data.replace('nan', np.nan)
    
    #convert units to similar magnitudes. We might need to change the units as well.
    #convert to dict
    unit_to_adj_unit_concordance_dict = config.measure_to_unit_concordance.set_index('Unit').to_dict()['Magnitude_adjusted_unit']
    value_adjustment_concordance_dict = config.measure_to_unit_concordance.set_index('Unit').to_dict()['Magnitude_adjustment']
    #just go through the concordance and convert the units and values
    for unit in unit_to_adj_unit_concordance_dict.keys():
        
        #convert values
        aggregated_model_data.loc[aggregated_model_data['Unit']==unit, 'Value'] = aggregated_model_data.loc[aggregated_model_data['Unit']==unit, 'Value'] * value_adjustment_concordance_dict[unit]

        #convert units
        aggregated_model_data.loc[aggregated_model_data['Unit']==unit, 'Unit'] = unit_to_adj_unit_concordance_dict[unit]
    
    #IMPORTANT ERROR CHECK SINCE THE RATIO OF THESE UNITS IS IMPORTANT
    #check that the units for stocks and populatin are in millions and thousands respectively
    if aggregated_model_data.loc[aggregated_model_data['Measure']=='Stocks', 'Unit'].unique().tolist() != ['Million_stocks']:
        print('ERROR: The units for stocks are not in millions. Please fix the data')
    if aggregated_model_data.loc[aggregated_model_data['Measure']=='Population', 'Unit'].unique().tolist() != ['Population_thousands']:
        print('ERROR: The units for population are not in thousands. Please fix the data')
    
    ###############################
    #remove uneeded columns
    unneeded_cols =['Unit','Dataset', 'Data_available', 'Frequency']
    aggregated_model_data.drop(unneeded_cols, axis=1, inplace=True)
    aggregated_model_data.drop_duplicates(inplace=True)
    #separate into road, non road asnd everything else
    road_model_input = aggregated_model_data.loc[aggregated_model_data['Medium'] == 'road']
    non_road_model_input = aggregated_model_data.loc[aggregated_model_data['Medium'].isin(['air', 'rail', 'ship'])]#TODO remove nonspec from the model or at least decide wehat to do with it
    growth_forecasts = aggregated_model_data.loc[~aggregated_model_data['Medium'].isin(['road', 'air', 'rail', 'ship'])]

    ###############################
    # Make wide so each unique category of the measure col is a column with the values in the value col as the values. This is how we will use the data from now on.
    road_model_input_wide = road_model_input.pivot(index=config.INDEX_COLS_NO_MEASURE, columns='Measure', values='Value').reset_index()
    non_road_model_input_wide = non_road_model_input.pivot(index=config.INDEX_COLS_NO_MEASURE, columns='Measure', values='Value').reset_index()
    growth_forecasts_wide = growth_forecasts.pivot(index=config.INDEX_COLS_NO_MEASURE, columns='Measure', values='Value').reset_index()
    #join on the Population, GDP and activity_growth cols from growth_forecasts to the otehrs
    road_model_input_wide = road_model_input_wide.merge(growth_forecasts_wide[['Date', 'Economy','Transport Type', 'Population', 'Gdp','Gdp_per_capita', 'Activity_growth']].drop_duplicates(), on=['Date','Transport Type', 'Economy'], how='left')
    non_road_model_input_wide = non_road_model_input_wide.merge(growth_forecasts_wide[['Date', 'Economy','Transport Type', 'Population', 'Gdp','Gdp_per_capita', 'Activity_growth']].drop_duplicates(), on=['Date', 'Transport Type','Economy'], how='left')
    ###############################
    road_model_input_wide, non_road_model_input_wide, growth_forecasts_wide = check_na_and_zero_values(config, road_model_input_wide, non_road_model_input_wide, growth_forecasts_wide, REPLACE_NAS_WITH_ZEROS, REPLACE_ZEROS_WITH_AVGS_FROM_DIFFERENT_DATES_FOR_FACTOR_MEASURES, REPLACE_ZEROS_WITH_ONES_IN_GROWTH_VALUES)
    ###############################
    #extrract gompertz data from road model input wide and put it in a separate df:
    stocks_per_capita_threshold = road_model_input_wide[['Economy','Scenario','Date', 'Transport Type','Vehicle Type', 'Stocks_per_capita']].drop_duplicates().dropna().copy()
    road_model_input_wide = road_model_input_wide.drop(['Stocks_per_capita'], axis=1).drop_duplicates()
    if len(road_model_input_wide.loc[road_model_input_wide['Vehicle Type']=='all']):
        breakpoint()#get rid of it
    
    #save data    
    road_model_input_wide.to_csv(os.path.join(config.root_dir, 'intermediate_data', 'model_inputs', config.FILE_DATE_ID, f'{ECONOMY_ID}_aggregated_road_model_input_wide.csv'), index=False)
    non_road_model_input_wide.to_csv(os.path.join(config.root_dir, 'intermediate_data', 'model_inputs', config.FILE_DATE_ID, f'{ECONOMY_ID}_aggregated_non_road_model_input_wide.csv'), index=False)
    growth_forecasts_wide.to_csv(os.path.join(config.root_dir, 'intermediate_data', 'model_inputs', config.FILE_DATE_ID, f'{ECONOMY_ID}_aggregated_growth_forecasts_wide.csv'), index=False)

    stocks_per_capita_threshold.to_csv(os.path.join(config.root_dir, 'intermediate_data', 'model_inputs', config.FILE_DATE_ID, f'{ECONOMY_ID}_stocks_per_capita_threshold.csv'), index=False)
    
    #lastly resave these files before they get changed in the modelling process
    supply_side_fuel_mixing = pd.read_csv(os.path.join(config.root_dir, 'intermediate_data', 'model_inputs', config.FILE_DATE_ID, f'{ECONOMY_ID}_supply_side_fuel_mixing.csv'))
    demand_side_fuel_mixing = pd.read_csv(os.path.join(config.root_dir, 'intermediate_data', 'model_inputs', config.FILE_DATE_ID, f'{ECONOMY_ID}_demand_side_fuel_mixing.csv'))
    supply_side_fuel_mixing.to_csv(os.path.join(config.root_dir, 'intermediate_data', 'model_inputs', config.FILE_DATE_ID, f'{ECONOMY_ID}_aggregated_supply_side_fuel_mixing.csv'), index=False)
    demand_side_fuel_mixing.to_csv(os.path.join(config.root_dir, 'intermediate_data', 'model_inputs', config.FILE_DATE_ID, f'{ECONOMY_ID}_aggregated_demand_side_fuel_mixing.csv'), index=False)

def replace_zeros_with_avgs_from_different_dates(config, df, measure):
    #requires a df with a date col, a measure col and a value col so that we can group by everything except the value and date col to calcualte the avcerage. note that we will exclude the effect of 0s and nans on teh aavg
    df_measure_no_date_avgs = df.loc[df['Measure']==measure].copy()
    df_measure_no_date_avgs['Value'] = df_measure_no_date_avgs['Value'].replace(0, np.nan)
    df_measure_no_date_avgs = df_measure_no_date_avgs.dropna(subset=['Value'])
    group_cols = df_measure_no_date_avgs.columns.to_list()
    group_cols.remove('Date')
    group_cols.remove('Value')
    #drop date and calcualte the avg of value
    df_measure_no_date_avgs.drop(columns=['Date'], inplace=True)
    df_measure_no_date_avgs = df_measure_no_date_avgs.groupby(group_cols).mean().reset_index()
    df = df.merge(df_measure_no_date_avgs, on=group_cols, how='left', suffixes=('', '_avg'))
    df.loc[(df['Value']==0) & (~df['Value_avg'].isna()), 'Value'] = df.loc[(df['Value']==0) & (~df['Value_avg'].isna()), 'Value_avg']
    df.drop(columns=['Value_avg'], inplace=True)
    return df

def check_na_and_zero_values(config, road_model_input_wide, non_road_model_input_wide, growth_forecasts_wide, REPLACE_NAS_WITH_ZEROS, REPLACE_ZEROS_WITH_AVGS_FROM_DIFFERENT_DATES_FOR_FACTOR_MEASURES, REPLACE_ZEROS_WITH_ONES_IN_GROWTH_VALUES):
    #CHECK FOR NAS IN ALL MEASURES AND ALSO 0'S IN config.FACTOR_MEASURES and config.GROWTH_MEASURES. If REPLACE_NAS_WITH_ZEROS is true then replace all nans with 0's, 
    #IF REPLACE_ZEROS_WITH_AVGS_FROM_DIFFERENT_DATES_FOR_FACTOR_MEASURES is true then try to replace 0's (including what we might have just set to 0) for config.FACTOR_MEASURES with the average of the same rows in other dates, and if that cant be done, throw an error with clear instructions on how to fix the data.
    #IF REPLACE_ZEROS_WITH_ONES_IN_GROWTH_VALUES is true then try to replace 0's (including what we might have just set to 0) for config.GROWTH_MEASURES with 1's
    #first check for any nas in non measure cols since these definitely shouldnt be there
    def check_nans(df, df_name, cols):
        nas = df.loc[:, cols].isna().sum().loc[df.loc[:, cols].isna().sum()>0].index.tolist()
        if len(nas) > 0:
            breakpoint()
            raise ValueError('There are nans in the columns {} in the {} data. Please fix the data'.format(nas, df_name))

    check_nans(road_model_input_wide, 'road_model_input_wide', config.INDEX_COLS_NO_MEASURE)
    check_nans(non_road_model_input_wide, 'non_road_model_input_wide', config.INDEX_COLS_NO_MEASURE)
    #ignore Vehicle Type	Medium	Transport Type	Drive in the growth forecasts as they are na for all rows
    cols = config.INDEX_COLS_NO_MEASURE.copy()
    cols.remove('Vehicle Type')
    cols.remove('Medium')
    cols.remove('Transport Type')
    cols.remove('Drive')
    check_nans(growth_forecasts_wide, 'growth_forecasts_wide', cols)
    
    if REPLACE_NAS_WITH_ZEROS:
        #only do it on measures, not anything in INDEX_COLS
        def fill_na(df, non_measure_cols):
            cols = [col for col in df.columns.tolist() if col not in non_measure_cols]
            df[cols] = df[cols].fillna(0)
            return df

        road_model_input_wide = fill_na(road_model_input_wide, config.INDEX_COLS)
        non_road_model_input_wide = fill_na(non_road_model_input_wide, config.INDEX_COLS)
        growth_forecasts_wide = fill_na(growth_forecasts_wide, config.INDEX_COLS)
    
    if REPLACE_ZEROS_WITH_AVGS_FROM_DIFFERENT_DATES_FOR_FACTOR_MEASURES:
        for measure in config.FACTOR_MEASURES:
            if measure in road_model_input_wide.columns.tolist():
                if len(road_model_input_wide.loc[(road_model_input_wide[measure]==0), 'Date'].unique())>0:
                    print('WARNING: There are zeros in the {} measure in the road_model_input_wide data. We will try to replace these with averages from other dates. Either wway, it would be best to fix the data'.format(measure))
                road_model_input_tall = road_model_input_wide.melt(id_vars=config.INDEX_COLS_NO_MEASURE, var_name='Measure', value_name='Value')
                road_model_input_tall = replace_zeros_with_avgs_from_different_dates(config, road_model_input_tall, measure)
                #m,ake wide again
                road_model_input_wide = road_model_input_tall.pivot(index=config.INDEX_COLS_NO_MEASURE, columns='Measure', values='Value').reset_index()
                
            if measure in non_road_model_input_wide.columns.tolist():
                if len(non_road_model_input_wide.loc[(non_road_model_input_wide[measure]==0), 'Date'].unique())>0:
                    print('WARNING: There are zeros in the {} measure in the non_road_model_input_wide data. We will try to replace these with averages from other dates. Either wway, it would be best to fix the data'.format(measure))
                non_road_model_input_tall = non_road_model_input_wide.melt(id_vars=config.INDEX_COLS_NO_MEASURE, var_name='Measure', value_name='Value')
                #replace zeros with averages
                non_road_model_input_tall = replace_zeros_with_avgs_from_different_dates(config, non_road_model_input_tall, measure)
                non_road_model_input_wide = non_road_model_input_tall.pivot(index=config.INDEX_COLS_NO_MEASURE, columns='Measure', values='Value').reset_index()

        if REPLACE_ZEROS_WITH_ONES_IN_GROWTH_VALUES:#TODO IS IT RIGHT TO BE REPALCING WITH 1S ? OR SHOULD THEY ALSO BE 0S?
            for measure in config.GROWTH_MEASURES:
                if measure in growth_forecasts_wide.columns.tolist():
                    if len(growth_forecasts_wide.loc[(growth_forecasts_wide[measure]==0), 'Date'].unique())>0:
                        print('WARNING: There are zeros in the {} measure in the growth_forecasts_wide data. We will try to replace these with 1s. Either wway, it would be best to fix the data'.format(measure))
                    growth_forecasts_wide[measure] = growth_forecasts_wide[measure].replace(0, 1)
                if measure in road_model_input_wide.columns.tolist():
                    if len(road_model_input_wide.loc[(road_model_input_wide[measure]==0), 'Date'].unique())>0:
                        print('WARNING: There are zeros in the {} measure in the road_model_input_wide data. We will try to replace these with 1s. Either wway, it would be best to fix the data'.format(measure))
                    road_model_input_wide[measure] = road_model_input_wide[measure].replace(0, 1)
                if measure in non_road_model_input_wide.columns.tolist():
                    if len(non_road_model_input_wide.loc[(non_road_model_input_wide[measure]==0), 'Date'].unique())>0:
                        print('WARNING: There are zeros in the {} measure in the non_road_model_input_wide data. We will try to replace these with 1s. Either wway, it would be best to fix the data'.format(measure))
                    non_road_model_input_wide[measure] = non_road_model_input_wide[measure].replace(0, 1)
    
    return road_model_input_wide, non_road_model_input_wide, growth_forecasts_wide
#%%
# aggregate_data_for_model(config, '08_JPN')

# %%
