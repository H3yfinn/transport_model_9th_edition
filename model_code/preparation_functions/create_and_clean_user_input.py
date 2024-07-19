#this is intended to be where all data that is used in the model is cleaned before being adjusted to be used in the model.

#CLEANING IS anything that involves changing the format of the data. The next step is filling in missing values. 
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
# data_available
def create_and_clean_user_input(config, ECONOMY_ID, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=False):
        
    from ..data_creation_functions import vehicle_sales_share_creation_handler, create_demand_side_fuel_mixing_input, create_supply_side_fuel_mixing_input
    ######################################################################################################    
    if config.NEW_SALES_SHARES:
        # vehicle_sales_share_economy = create_vehicle_sales_share_input(config, ECONOMY_ID)
        vehicle_sales_share_economy = vehicle_sales_share_creation_handler(config, ECONOMY_ID,RECALCULATE_SALES_SHARES_USING_RECALCULATED_INPUT_DATA = False, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, USE_LARGE_EPSILON=True)

    if config.NEW_FUEL_MIXING_DATA:
        #note that this wont be saved to user input, as it has a different data structure.
        demand_side_fuel_mixing_economy = create_demand_side_fuel_mixing_input(config, ECONOMY_ID)
        supply_side_fuel_mixing_economy = create_supply_side_fuel_mixing_input(config, ECONOMY_ID)

    user_input = extract_economy_data_from_user_input_spreadsheets(config, ECONOMY_ID)
    user_input = pd.concat([user_input, vehicle_sales_share_economy, supply_side_fuel_mixing_economy, demand_side_fuel_mixing_economy], sort=False)
    
    # #first, prepare user input 
    # #load these files in and concat them
    # user_input = pd.DataFrame()
    # print(f'There are {len(os.listdir(os.path.join("input_data", "user_input_spreadsheets", ECONOMY_ID))} user input files to import')
    # for file in os.listdir(os.path.join(config.root_dir, "input_data", "user_input_spreadsheets", ECONOMY_ID)):
    #     #check its a csv
    #     if file[-4:] != '.csv':
    #         continue
    #     print(f'Importing user input file: {file}')
    #     user_input = pd.concat([user_input, pd.read_csv(os.path.join(config.root_dir, "input_data", "user_input_spreadsheets", ECONOMY_ID, file))])
    
    #laod concordances for checking
    model_concordances_user_input_and_growth_rates = pd.read_csv(os.path.join(config.root_dir, "intermediate_data", "computer_generated_concordances", config.model_concordances_user_input_and_growth_rates_file_name))#seems we're missing ghompertz hbere?
    model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates[model_concordances_user_input_and_growth_rates.Economy == ECONOMY_ID]
    #print then remove any measures not in model_concordances_user_input_and_growth_rates
    if len(user_input[~user_input.Measure.isin(model_concordances_user_input_and_growth_rates.Measure)]) >0:
        print('Measures in user input that are not in the model concordances:', user_input[~user_input.Measure.isin(model_concordances_user_input_and_growth_rates.Measure)].Measure.unique())
    user_input = user_input[user_input.Measure.isin(model_concordances_user_input_and_growth_rates.Measure)]
    
    ################################################################################
    #we need intensity improvement for all new non road drive types. so filter for non road in user input then merge with the concordance table to get the new drive types, and replicate the intensity improvement for all. 
    
    #drop any rows in user input that are for the base year (why? i geuss there arent any base year values in the user inputanyway, but could be useful not to rmeove them ?)
    user_input = user_input[user_input.Date != config.DEFAULT_BASE_YEAR]
    
    #then filter for the same rows that are in the concordance table for user inputs and  grwoth rates. these rows will be based on a set of index columns as defined below. Once we have done this we can print out what data is unavailable (its expected that no data will be missing for the model to actually run)
    
    #set index
    user_input.set_index(config.INDEX_COLS, inplace=True)
    model_concordances_user_input_and_growth_rates.set_index(config.INDEX_COLS, inplace=True)

    #create empty list which we will append the data we extract from the user_inputs using an iterative loop. Then we will concat it all together into one dataframe
    new_user_inputs = []

    #create column which will be used to indicate whether the data is available in the user_inputs, or not
    #options will be:
    #1. data_available
    #2. data_not_available
    #3. row_and_data_not_available

    #we can determine data available and not available now, and then find out option 3 by comparing to the model concordances:

    #where vlaues arent na, set the data_available column to 1, else set to 2
    user_input.loc[user_input.Value.notna(), 'Data_available'] = 'data_available'
    user_input.loc[user_input.Value.isna(), 'Data_available'] = 'data_not_available'
    
    # use the difference method to find:
    #missing_index_values1 :  the index values that are missing from the user_input 
    #missing_index_values2 : and also the index values that are present in the user_input but not in the concordance 
    # # this is a lot faster than looping through each index row in the concordance and checking if it is in the user_input
    missing_index_values1 = model_concordances_user_input_and_growth_rates.index.difference(user_input.index)
    missing_index_values2 = user_input.index.difference(model_concordances_user_input_and_growth_rates.index)
    if missing_index_values1.empty:
        pass
    else:
        #add these rows to the user_input and set them to row_and_data_not_available
        missing_index_values1 = pd.DataFrame(index=missing_index_values1).reset_index()
        missing_index_values1['Data_available'] = 'row_and_data_not_available'
        missing_index_values1['Value'] = np.nan
        #then append to transport_data_system_df
        user_input = user_input.reset_index()
        user_input = pd.concat([missing_index_values1, user_input], sort=False)
        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
            print('Missing rows in our user input dataset when we compare it to the concordance:', missing_index_values1)
        user_input.set_index(config.INDEX_COLS, inplace=True)

    if missing_index_values2.empty:
        pass#this is to be expected as the cocnordance should always have everything we need in it!
    else:
        #we want to make sure user is aware of this as we will be removing rows from the user input
        #remove these rows from the user_input
        user_input.drop(missing_index_values2, inplace=True)
        #convert missing_index_values to df
        missing_index_values2 = pd.DataFrame(index=missing_index_values2).reset_index()
        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
            print('Number of missing rows in the user input concordance: {}'.format(len(missing_index_values2)))
            print('We will remove these rows from the user input dataset. If you intended to have data for these rows, please add them to the concordance table.')

        # #print the unique Vehicle types and drives that are missing
        # print('Unique Vehicle types and drives that are missing: {}'.format(missing_index_values2[['Vehicle Type', 'Drive']].drop_duplicates()))#as of /4 we ha
    
    user_input = user_input.reset_index()
    
    # # a= user_input.copy()
    # user_input = a.copy()
    
    #we may be missing user inputs because the config.END_YEAR was extended. So just fill in missing values with the last available value when grouping by the index cols
    #so first insert all the missing years
    #make sure to print strong wanrings so the user is aware that they could be filling in missing data where it should be missing
    #also, jsut to be safe, only do thisstep if the missing data is for years greater than 2050
    if (user_input[user_input.Data_available == 'row_and_data_not_available'].Date.max() > 2050) or (user_input[user_input.Data_available == 'data_not_available'].Date.max() > 2050):
        print('WARNING: You are filling in missing data for years greater than 2050. Please check that this is what you want to do.')
        #check that where Value is NA that Data_available is row_and_data_not_available or data_not_available for all cases
        if len(user_input[(user_input.Value.isna()) & ((user_input.Data_available != 'row_and_data_not_available') & (user_input.Data_available != 'data_not_available'))]) >0:
            #raise error if this is not the case
            raise ValueError('There are some rows where Value is NA but Data_available is not row_and_data_not_available or data_not_available. Please check this.')
        #and check the opposite, i.e. that where Data_available is row_and_data_not_available or data_not_available that Value is NA
        if len(user_input[(user_input.Value.notna()) & ((user_input.Data_available == 'row_and_data_not_available') | (user_input.Data_available == 'data_not_available'))]) >0:
            #raise error if this is not the case
            raise ValueError('There are some rows where Value is not NA but Data_available is row_and_data_not_available or data_not_available. Please check this.')
        #create new df that contains dates that are less than 2050 and the values are NA
        user_input_missing_values_dont_change = user_input.loc[(user_input.Date <= 2050) & (user_input.Value.isna())]

        #create new df that contains dates that are greater than 2050 and the values are NA
        user_input_missing_values_change = user_input.loc[~((user_input.Date <= 2050) & (user_input.Value.isna()))]

        # first sort by date
        user_input_missing_values_change.sort_values('Date', inplace=True)
        # now ffill na on Value col when grouping by the index cols
        
        user_input_missing_values_change['Value'] = user_input_missing_values_change.groupby(config.INDEX_COLS_no_date)['Value'].apply(lambda group: group.ffill())

        # reset index
        user_input_missing_values_change.reset_index(drop=True, inplace=True)

        #now concat the two dfs
        user_input_new = pd.concat([user_input_missing_values_dont_change, user_input_missing_values_change], sort=False)
        #check for nas and throw error if so. might need to utilise the commented out code below (that i didnt finish gettting working) to do this
        
        if len(user_input_new[user_input_new.Value.isna()]) >0:
            #identify the rows where there are still nas in the Value col:
            user_input_new_nas = user_input_new[user_input_new.Value.isna()]
            #save them to csv
            user_input_new_nas.to_csv(os.path.join(config.root_dir, "intermediate_data", "errors", "user_input_new_nas.csv"), index=False)
            raise ValueError('There are still some rows where Value is NA. Please check this.')
        # #there will be soe cases where there are still nas because there are nas for every year in the group of config.INDEX_COLS_no_date. We will check for these cases and separate them for analysis. THen identify any extra cases where there are still nas in the Value col. these are problematic and we will raise an error
        # user_input_new_groups_with_all_nas = user_input_new.groupby(config.INDEX_COLS_no_date).apply(lambda group: group.isna().all()).reset_index()

        # #drop tehse rwos from the user_input_new so we can check for any other cases where there are still nas in the Value col:
        # user_input_new = user_input_new.loc[~user_input_new_groups_with_all_nas[0]]
        # #then identify the other cases where there are still nas in the Value col:
        # user_input_new_groups_with_nas_in_value = user_input_new.groupby(config.INDEX_COLS_no_date).apply(lambda group: group.Value.isna().any()).reset_index()
    else:
        user_input_new = user_input.copy()
    
    # #resvae tehse values back to the user_input df, by measure
    # #now save the sheet to the excel file
    # save_progress=False
    # if save_progress:
    #     file_date = datetime.datetime.now().strftime("%Y%m%d")
    #     FILE_DATE_ID_x = '_{}'.format(file_date)
    #     #save the original user_input_spreadsheet to the archive with the File date
    #     shutil.copy(os.path.join('input_data', 'user_input_spreadsheet.xlsx'), os.path.join('input_data', 'archive', 'user_input_spreadsheet{}.xlsx'.format(FILE_DATE_ID_x)))
    #     #remove the original user_input_spreadsheet
    #     os.remove(os.path.join('input_data', 'user_input_spreadsheet.xlsx'))
    #     with pd.ExcelWriter(os.path.join('input_data', 'user_input_spreadsheet.xlsx')) as writer:
    #         for sheet in user_input_new.Measure.unique():
    #             print('Saving user input sheet: {}'.format(sheet))
    #             sheet_data = user_input_new[user_input_new.Measure == sheet]
    #             sheet_data.to_excel(writer, sheet_name=sheet, index=False)
    
    #the  data is probably missing data for the years previous to OUTLOOK_BASE_YEAR. Where this is the case we will fill in the missing data with the earliest available value.
    ECONOMY_BASE_YEARS_DICT = yaml.load(open(os.path.join(config.root_dir, 'config', 'parameters.yml')), Loader=yaml.FullLoader)['ECONOMY_BASE_YEARS_DICT']
    for economy in ECONOMY_BASE_YEARS_DICT.keys():
        economy_df = user_input_new[user_input_new.Economy == economy]
        if len(economy_df) == 0:
            continue
        BASE_YEAR = ECONOMY_BASE_YEARS_DICT[economy]
        #check taht dagta is available for the base year and up to the OUTLOOK_BASE_YEAR
        for measure in economy_df.Measure.unique():
            for date in range(BASE_YEAR, config.OUTLOOK_BASE_YEAR+1):
                measure_df = economy_df[(economy_df.Measure == measure)]
                if date not in measure_df.Date.unique():
                    #copy the next earliest year and change the date
                    date_df = measure_df[(measure_df.Date == measure_df.Date.min())].copy()
                    date_df.Date = date
                    economy_df = pd.concat([economy_df, date_df])
        #now save back to the user_input_new df
        user_input_new = user_input_new[user_input_new.Economy != economy] 
        user_input_new = pd.concat([user_input_new, economy_df])
        
    #save the new_user_inputs
    user_input_new.to_csv(os.path.join(config.root_dir, 'intermediate_data', 'model_inputs', '{}_user_inputs_and_growth_rates.csv'.format(ECONOMY_ID)), index=False)


def extract_economy_data_from_user_input_spreadsheets(config, ECONOMY_ID):
    #spreadhsheets that are in input_data/user_input_spreadsheets contain all economies to make it easier to edit them all in one go. we will extract the economy specific data for use in the model    
    user_input_all = pd.DataFrame()
    for file in os.listdir(os.path.join(config.root_dir, 'input_data', 'user_input_spreadsheets')):
        #check its a csv
        if file[-4:] != '.csv':
            continue
        user_input = pd.read_csv(os.path.join(config.root_dir, 'input_data', 'user_input_spreadsheets', file))
        #if there is a comment col, drop it
        if 'Comment' in user_input.columns:
            user_input.drop('Comment', axis=1, inplace=True)
        # # #replace 15_RP with 15_PHL, and 17_SIN with 17_SGP inn all sheet in economy col
        # if 'Economy' in user_input.columns:
        #     if '15_RP' in user_input.Economy.unique():
        #         user_input.Economy.replace('15_RP', '15_PHL', inplace=True)
        #     if '17_SIN' in user_input.Economy.unique():
        #         user_input.Economy.replace('17_SIN', '17_SGP', inplace=True)
        #     user_input.to_csv(f'input_data\\user_input_spreadsheets\\{file}', index=False)
        #     print('SINGAPORE AND PHIL REPLACED. PLEASE DELETE THIS LINE')
        #     breakpoint()
        #cehck for udplciates
        if len(user_input[user_input.duplicated()]) >0:
            breakpoint()
            time.sleep(1)
            raise ValueError('There are duplicates in the user input. Please check this file {}'.format(file))
            # user_input.drop_duplicates(inplace=True)
            # user_input.to_csv(f'input_data\\user_input_spreadsheets\\{file}', index=False)
            
        model_concordances_user_input_and_growth_rates_original= pd.read_csv(os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', config.model_concordances_user_input_and_growth_rates_file_name))
        user_input = user_input[user_input.Economy == ECONOMY_ID]
        #if any cols are missing from user input then deal with them:
        missing_cols = [col for col in config.INDEX_COLS if col not in user_input.columns]
        if len(missing_cols) >0:
            #add them to the user_input by grabbing them from the model concordances and joining on the other index cols
            model_concordances_user_input_and_growth_rates= model_concordances_user_input_and_growth_rates_original.copy()
            remaining_cols = [col for col in config.INDEX_COLS_NO_MEASURE if col not in missing_cols]
            #filter for the same values in the remaining_cols:
            for col in remaining_cols:
                model_concordances_user_input_and_growth_rates=model_concordances_user_input_and_growth_rates.loc[model_concordances_user_input_and_growth_rates[col].isin(user_input[col].unique())]
                
            model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates[missing_cols].drop_duplicates()
            #create key col to join on
            model_concordances_user_input_and_growth_rates['key'] = 1
            user_input['key'] = 1
            user_input = user_input.merge(model_concordances_user_input_and_growth_rates, on='key', how='outer')
            
            user_input.drop('key', axis=1, inplace=True)
        
        user_input_all = pd.concat([user_input_all, user_input])
        
    return user_input_all
    
    
#%%
# create_and_clean_user_input(config, '17_SGP')
# extract_economy_data_from_user_input_spreadsheets(config, ECONOMY_ID)
#%%
