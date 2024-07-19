#this will apply any fuel mixing on the demand side. This is can include, the use of different fule types for each drive type, for example, electricity vs oil in phev's, or even treating rail as a drive type, and splitting demand into electricity, coal and dieel rpoprtions. 

#as such, this will merge a fuel mixing dataframe onto the model output, by the Drive column, and apply the shares by doing that, resulting in a fuel column.
#this means that the supply side fuel mixing needs to occur after this script, because it will be merging on the fuel column.

#this script also contains the function transfer_growth_between_mediums(config, model_output_all, ECONOMY_ID) which is pretty important
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
def concatenate_model_output(config, ECONOMY_ID, SHIFT_YEARLY_GROWTH_RATE_FROM_ROAD_TO_NON_ROAD=True, PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=False):
    #load model output
    road_model_output = pd.read_csv(config.root_dir + config.slash + 'intermediate_data\\road_model\\{}_{}'.format(ECONOMY_ID, config.model_output_file_name))#TODO WHY IS MEASURE A COLUMN IN HERE?
    non_road_model_output = pd.read_csv(config.root_dir + config.slash + 'intermediate_data\\non_road_model\\{}_{}'.format(ECONOMY_ID, config.model_output_file_name))
    
    # check if there are any NA's in any columns in the output dataframes. If there are, print them out
    if road_model_output.isnull().values.any():
        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
            print('there are {} NA values in the road model output. However if they are only in the user input columns for 2017 then ignore them'.format(len(road_model_output[road_model_output.isnull().any(axis=1)].loc[:, road_model_output.isnull().any(axis=0)])))
        else:
            pass
    if non_road_model_output.isnull().values.any():
        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
            print('there are {} NA values in the non road model output. However if they are only in the user input columns for 2017 then ignore them'.format(len(non_road_model_output[non_road_model_output.isnull().any(axis=1)].loc[:, non_road_model_output.isnull().any(axis=0)])))
        else:
            pass

    #also check for duplicates
    if road_model_output.duplicated().any():
        print('there are duplicates in the road model output')
    if non_road_model_output.duplicated().any():
        print('there are duplicates in the non road model output')
    
    #set medium for road
    road_model_output['Medium'] ='road'
    #concatenate road and non road models output
    model_output_all = pd.concat([road_model_output, non_road_model_output])
    
    #save
    model_output_all.to_csv(config.root_dir + config.slash + 'intermediate_data\\model_outputs\\{}_{}'.format(ECONOMY_ID, config.model_output_file_name), index=False)
    # breakpoint()
    if SHIFT_YEARLY_GROWTH_RATE_FROM_ROAD_TO_NON_ROAD and not PROJECT_TO_JUST_OUTLOOK_BASE_YEAR:
        #no point in doing this if we are projecting to just the outlook base year (i.e. creating input data)
        df_adjustments = pd.read_excel(config.root_dir + config.slash + 'input_data\\post_hoc_adjustments\\growth_rate_adjustments.xlsx')
        model_output_all = transfer_growth_between_mediums(config, model_output_all, df_adjustments, ECONOMY_ID)               
    return model_output_all


def find_cumulative_product_of_activity_adjustment_to_FROM_medium(config, df_economy_adjustments, model_output_all):
    #this will find the cumulative product of the adjustment to activity over the outlook period, for each group of the columns: Date	Economy	Scenario	Transport Type	To_medium	From_medium
    #HOWEVER one complication is that we need to add all the dates after the last date of each group, so that the cumulative product is applied to all future years. as otherwise the activity in years after the last year of the adjustment will see a jump to what it was originally, where it shouldactually be adjusted by the same amount as the last year of the adjustment.
    final_year = model_output_all['Date'].max()
    #frist sort the df by date
    new_economy_adjustments = pd.DataFrame(columns=df_economy_adjustments.columns.tolist()+['cumulative_product_of_adjustment'])
    df_economy_adjustments.sort_values(by=['Date'], inplace=True)
    for (economy, scenario, transport_type, to_medium, from_medium), adjustments in df_economy_adjustments.groupby(['Economy', 'Scenario', 'Transport Type', 'To_medium', 'From_medium'], dropna=False):
        #first find the cumulative product of the growth rate over the adjustments period
        
        adjustments['cumulative_product_of_adjustment'] = adjustments['Adjustment'].cumprod()
        #then apply the last years adjustments to all years afterwards
        #find the last year of the adjustment
        last_year = adjustments['Date'].max()
        #if the last year of the adjustment is not the final year, then add the final year to the adjustments, with the same adjustment as the last year
        if last_year < final_year:
            last_year_to_final_year_adjustment = adjustments[adjustments['Date'] == last_year].copy()
            for year in range(last_year+1, final_year+1):
                last_year_to_final_year_adjustment['Date'] = year
                adjustments = pd.concat([adjustments, last_year_to_final_year_adjustment])
        new_economy_adjustments = pd.concat([new_economy_adjustments, adjustments]) 
    return new_economy_adjustments
          
def transfer_growth_between_mediums(config, model_output_all, df_adjustments, ECONOMY_ID):
    # Filter adjustments for the specific ECONOMY_ID
    df_economy_adjustments = df_adjustments[df_adjustments['Economy'] == ECONOMY_ID]
    #set a flag so we can more quikcly identify changed rows
    model_output_all['Adjusted']=False
    very_original_activity = model_output_all[['Date', 'Scenario', 'Economy', 'Transport Type', 'Medium', 'Activity']].groupby(['Date', 'Scenario', 'Economy', 'Transport Type', 'Medium']).sum().reset_index().copy()
    very_original_activity.rename(columns={'Activity': 'Very_original_activity'}, inplace=True)
    
    df_economy_adjustments = find_cumulative_product_of_activity_adjustment_to_FROM_medium(config, df_economy_adjustments, model_output_all)
    
    # Apply adjustments to the 'from' medium and get the updated model output along with the changes in activity
    model_output_all, activity_change_all = apply_adjustment_to_FROM_medium(config, model_output_all, df_economy_adjustments, very_original_activity)

    # Now, apply the change in activity to the 'to' medium where applicable
    # Note: The apply_change_in_activity_TO_medium function will check if 'To_medium' is NA and skip those cases
    model_output_all, activity_change_all = apply_change_in_activity_TO_medium(config, model_output_all, activity_change_all,  very_original_activity)
    
    model_output_all = recalculate_metrics(config, model_output_all)
    activity_change_all.to_csv(config.root_dir + config.slash + 'intermediate_data\\model_outputs\\{}_medium_to_medium_activity_change_for_plotting{}.csv'.format(ECONOMY_ID, config.FILE_DATE_ID), index=False)
    return model_output_all


def update_activity_change_df(config, model_output, activity_change_all, very_original_activity, to_medium, from_medium, TO_or_FROM):
    activity_change = model_output[['Scenario', 'Date', 'Economy', 'Transport Type', 'Medium', 'Original_activity', 'Activity', 'Change_in_activity']].groupby(['Scenario', 'Date', 'Economy', 'Transport Type', 'Medium']).sum().reset_index()
    #set very original activity to be the original activity before any adjustments for this grouping 
    activity_change= activity_change.merge(very_original_activity[['Date', 'Scenario', 'Economy', 'Transport Type', 'Medium', 'Very_original_activity']], on=['Date', 'Scenario', 'Economy', 'Transport Type', 'Medium'], how='left')
    activity_change.rename(columns={'Activity': 'New_activity'}, inplace=True)
    #add to_medium and from_medium to the df
    activity_change['To_medium'] = to_medium
    activity_change['From_medium'] = from_medium
    activity_change['TO_or_FROM'] = TO_or_FROM
    activity_change.drop(columns=['Medium'], inplace=True)
    activity_change_all = pd.concat([activity_change_all, activity_change])
    return activity_change_all

def apply_adjustment_to_FROM_medium(config, model_output_all, df_economy_adjustments, very_original_activity):
    # Initialize an empty DataFrame to collect changes in activity
    activity_change_all = pd.DataFrame(columns=['Date', 'Scenario', 'Economy', 'Transport Type', 'Original_activity','New_activity', 'Very_original_activity', 'Change_in_activity','To_medium','From_medium', 'TO_or_FROM'])
    model_output_all.reset_index(drop=True, inplace=True)
    for (transport_type, scenario, from_medium, to_medium), adjustments in df_economy_adjustments.groupby(['Transport Type', 'Scenario', 'From_medium', 'To_medium'], dropna=False):

        for _, row in adjustments.iterrows():
            year = row['Date']
            adjustment = row['cumulative_product_of_adjustment']

            mask = (model_output_all['Date'] == year) & \
                (model_output_all['Transport Type'] == transport_type) & \
                (model_output_all['Medium'] == from_medium) & \
                    (model_output_all['Scenario'] == scenario)
            model_output = model_output_all[mask].copy()

            model_output['Original_activity'] = model_output['Activity']
            model_output['Activity'] *= adjustment

            model_output['Change_in_activity'] = model_output['Activity'] - model_output['Original_activity']
            
            model_output['GROWTH_RATE_TOO_HIGH'] = model_output['Activity'] < 0
            model_output.loc[model_output['Activity'] < 0, 'Change_in_activity'] = model_output['Original_activity']
            model_output.loc[model_output['Activity'] < 0, 'Activity'] = 0
            #use the update function which will utilise the common indexes to replace the activity column in place.
            model_output['Adjusted'] =True
            model_output_all.update(model_output[['Activity', 'Adjusted']])
            
            activity_change_all = update_activity_change_df(config, model_output, activity_change_all, very_original_activity, to_medium, from_medium, TO_or_FROM='FROM')
    return model_output_all, activity_change_all

def apply_change_in_activity_TO_medium(config, model_output_all, activity_change_all, very_original_activity):
    activity_changes_iterator = activity_change_all[['Scenario', 'Date', 'Economy', 'Transport Type', 'To_medium','From_medium', 'Change_in_activity']].copy()
    #to be safe,reset the index, to help with the update function
    model_output_all = model_output_all.reset_index(drop=True)
    for (transport_type, scenario, from_medium, to_medium), activity_changes in activity_changes_iterator.groupby(['Transport Type', 'Scenario', 'From_medium',  'To_medium'], dropna=False):

        for _, row in activity_changes.iterrows():
            year = row['Date']
            change_in_activity = row['Change_in_activity']

            mask = (model_output_all['Date'] == year) & \
                (model_output_all['Transport Type'] == transport_type) & \
                (model_output_all['Medium'] == to_medium) & \
                    (model_output_all['Scenario'] == scenario)
            model_output_to_medium = model_output_all[mask].copy()
            
            #take the negative of the  change in activity. Since if we are normally adding what was taken away from the from medium, we need to reverse the sign of the change in activity
            model_output_to_medium['Change_in_activity'] =-change_in_activity
            
            # Apply the change in activity to the 'to' medium
            model_output_to_medium['Original_activity'] = model_output_to_medium['Activity']
            #first find the proportion of the mediums total activity (for each ['Date','Scenario']) that the change in activity represents, then apply that proportional change to all individual rows in model_output_to_medium:
            model_output_to_medium['Total_activity'] = model_output_to_medium.groupby(['Date','Scenario'])['Activity'].transform('sum')
            model_output_to_medium['Percentage_of_total_activity'] = model_output_to_medium['Change_in_activity']/model_output_to_medium['Total_activity']
            model_output_to_medium['Change_in_activity'] = (model_output_to_medium['Percentage_of_total_activity']*model_output_to_medium['Activity'])
            model_output_to_medium['Activity'] = model_output_to_medium['Activity'] + model_output_to_medium['Change_in_activity']

            # Ensure no negative activities after the change
            model_output_to_medium['GROWTH_RATE_TOO_HIGH'] = model_output_to_medium['Activity'] < 0
            model_output_to_medium.loc[model_output_to_medium['Activity'] < 0, 'Activity'] = 0
            model_output_to_medium['Change_in_activity'] = np.where(model_output_to_medium['GROWTH_RATE_TOO_HIGH'], model_output_to_medium['Original_activity'], model_output_to_medium['Change_in_activity'])
            model_output_to_medium['Adjusted'] =True
            # Update the main model_output_all DataFrame
            model_output_all.update(model_output_to_medium[['Activity', 'Adjusted']])
            #TODO TEST THAT UPDATE WORKS OK HERE. NOT SURE IF INDEX GETS MUCKED UP
            activity_change_all = update_activity_change_df(config, model_output_to_medium, activity_change_all, very_original_activity, to_medium, from_medium, TO_or_FROM='TO')
            
    return model_output_all, activity_change_all

def recalculate_metrics(config, model_output_all):
    # Apply different calculation methods based on the medium. But only do it to rows that were actually changed (to cut down on iterations)
    #grab the rows which have Adjusted=True
    model_output_all_old = model_output_all.copy()
    model_output_all_adjusted = model_output_all.loc[model_output_all['Adjusted']].copy()
    model_output_all = model_output_all[model_output_all['Adjusted'] == False].copy()
    
    i=0
    for index in model_output_all_adjusted.index:
        if model_output_all_adjusted.at[index, 'Medium'] != 'road':
            # Recalculate for non-road mediums
            model_output_all_adjusted.at[index, 'Stocks'] = model_output_all_adjusted.at[index, 'Activity'] / model_output_all_adjusted.at[index, 'Activity_per_Stock']
            model_output_all_adjusted.at[index, 'Energy'] = model_output_all_adjusted.at[index, 'Activity'] * model_output_all_adjusted.at[index, 'Intensity']
        else:
            # Recalculate for road medium
            model_output_all_adjusted.at[index, 'Stocks'] = model_output_all_adjusted.at[index, 'Activity'] / (model_output_all_adjusted.at[index, 'Occupancy_or_load'] * model_output_all_adjusted.at[index, 'Mileage'])
            model_output_all_adjusted.at[index, 'Travel_km'] = model_output_all_adjusted.at[index, 'Activity'] / model_output_all_adjusted.at[index, 'Occupancy_or_load']
            model_output_all_adjusted.at[index, 'Energy'] = model_output_all_adjusted.at[index, 'Travel_km'] / model_output_all_adjusted.at[index, 'Efficiency']
            model_output_all_adjusted.at[index, 'Stocks_per_thousand_capita'] = model_output_all_adjusted.at[index, 'Stocks'] / model_output_all_adjusted.at[index, 'Population']
            
            #check by recalculating energy using the new values:
            energy1 = model_output_all_adjusted.at[index, 'Travel_km'] / model_output_all_adjusted.at[index, 'Efficiency']
            energy2 = (1/model_output_all_adjusted.at[index, 'Efficiency']) * model_output_all_adjusted.at[index, 'Mileage'] * model_output_all_adjusted.at[index, 'Stocks']
            #if the two energies are not equal, then there is a problem
            diff = energy1-energy2
            if diff > 0.0001:
                print('energy1: {}, energy2: {}, diff: {}'.format(energy1, energy2, diff))
                breakpoint()
    model_output_all = pd.concat([model_output_all,model_output_all_adjusted])
    #drop adjusted column
    model_output_all.drop(columns=['Adjusted'], inplace=True)
    # Recalculate activity growth, grouped by 'Date','Scenario', 'Transport Type', 'Medium'
    model_output_all.sort_values(by=['Date'], inplace=True)
    activity_growth = model_output_all[['Date','Scenario', 'Transport Type', 'Medium', 'Activity']].groupby(['Date','Scenario', 'Transport Type', 'Medium']).sum().reset_index()
    activity_growth['Activity_growth'] = activity_growth.groupby(['Scenario', 'Transport Type', 'Medium']).Activity.pct_change().fillna(0)
    
    model_output_all = pd.merge(model_output_all.drop(columns=['Activity_growth']), activity_growth[['Date', 'Scenario', 'Transport Type', 'Medium', 'Activity_growth']], on=['Date', 'Scenario', 'Transport Type', 'Medium'], how='left')
    
    return model_output_all


def fill_missing_output_cols_with_nans(config, ECONOMY_ID, road_model_input_wide, non_road_model_input_wide):
    for col in config.ROAD_MODEL_OUTPUT_COLS:
        if col not in road_model_input_wide.columns:
            road_model_input_wide[col] = np.nan
    for col in config.NON_ROAD_MODEL_OUTPUT_COLS:
        if col not in non_road_model_input_wide.columns:
            non_road_model_input_wide[col] = np.nan
            
    #save to file
    road_model_input_wide.to_csv(config.root_dir + config.slash + 'intermediate_data\\road_model\\{}_{}'.format(ECONOMY_ID, config.model_output_file_name), index=False)
    non_road_model_input_wide.to_csv(config.root_dir + config.slash + 'intermediate_data\\non_road_model\\{}_{}'.format(ECONOMY_ID, config.model_output_file_name), index=False)


#%%
# a = concatenate_model_output(config, '05_PRC')#dont think its working aye

#%%