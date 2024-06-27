#the point of this file is to calculate extra variables that may be needed by the model, for example travel_km_per_stock or nromalised stock sales etc.
#these varaibles are essentially the same varaibles which will be calcualted in the model as these variables act as the base year variables. 

#please note that in the current state of the input data, this file has become qite messy with hte need to fill in missing data at this stage of the creation of the input data for the model. When we have good data we can make this more clean and suit the intended porupose to fthe file.
   

#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
import sys
sys.path.append("./config")
import config

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
sys.path.append("./workflow")
sys.path.append("./workflow/plotting_functions")
import plot_user_input_data
import adjust_data_to_match_esto
import road_model_functions

sys.path.append("./workflow/data_creation_functions")
from create_vehicle_sales_share_data import vehicle_sales_share_creation_handler

def calculate_inputs_for_model(road_model_input_wide,non_road_model_input_wide,growth_forecasts_wide, supply_side_fuel_mixing, demand_side_fuel_mixing, ECONOMY_ID, BASE_YEAR, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=False, adjust_data_to_match_esto_TESTING=False, USE_PREVIOUS_OPTIMISATION_RESULTS_FOR_THIS_DATA_SYSTEM_INPUT=False, USE_SAVED_OPT_PARAMATERS=False):
    """
    This function works differently based on the ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR variable. If this is False then the function will calculate the following variables for the model input data: Travel_km, Surplus_stocks, Stocks_per_thousand_capita, Turnover_rate, Activity_per_Stock, Stocks, Intensity, Surplus_stocks, Turnover_rate, New_vehicle_efficiency, Age_distribution. If this is True then the function will adjust the input data to match the esto data in the MODEL_BASE_YEAR. This is done by using the functions in adjust_data_to_match_esto.py. The function will then save the input data to the intermediate_data/model_inputs folder. < this was quickly written by chatgpt and needs to be updated to be more clear and accurate.

    Args:
        road_model_input_wide (_type_): _description_
        non_road_model_input_wide (_type_): _description_
        growth_forecasts_wide (_type_): _description_
        supply_side_fuel_mixing (_type_): _description_
        demand_side_fuel_mixing (_type_): _description_
        ECONOMY_ID (_type_): _description_
        BASE_YEAR (_type_): _description_
        ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR (bool, optional): _description_. Defaults to False. Defines whether...???TODO
        adjust_data_to_match_esto_TESTING (bool, optional): _description_. Defaults to False.
        USE_PREVIOUS_OPTIMISATION_RESULTS_FOR_THIS_DATA_SYSTEM_INPUT (bool, optional): _description_. Defaults to False.
    """
    ########################################################################### 
    road_model_input_wide['Travel_km'] = road_model_input_wide['Activity'] / road_model_input_wide['Occupancy_or_load']  # TRAVEL KM is not provided by transport data system atm
    road_model_input_wide['Surplus_stocks'] = 0
    road_model_input_wide['Stocks_per_thousand_capita'] = (road_model_input_wide['Stocks'] / road_model_input_wide['Population']) * 1000000
    road_model_input_wide['Turnover_rate'] = np.nan

    non_road_model_input_wide['Activity_per_Stock'] = 1
    non_road_model_input_wide['Stocks'] = non_road_model_input_wide['Activity'] / non_road_model_input_wide['Activity_per_Stock']
    non_road_model_input_wide.loc[(non_road_model_input_wide['Intensity'] == 0), 'Intensity'] = np.nan 
    non_road_model_input_wide['Intensity'] = non_road_model_input_wide.groupby(['Date', 'Economy', 'Scenario', 'Transport Type', 'Drive'])['Intensity'].transform(lambda x: x.fillna(x.mean()))
    if non_road_model_input_wide['Intensity'].isna().any():
        non_road_model_input_wide = set_intensity_manually(non_road_model_input_wide)
    non_road_model_input_wide['Surplus_stocks'] = 0
    non_road_model_input_wide['Turnover_rate'] = np.nan
    # PLOT AVERAGE INTENSITY ACROSS ALL ECONOMIES AND SCENARIOS
    plotting = False
    if plotting:
        plot_user_input_data.plot_average_intensity(non_road_model_input_wide)
    ############################################################################
    #EVEN OUT ANY INBALANCES IN THE INPUT DATA.
    if not ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR:
        
        
        #RECALCUALTE ACTIVITY AND THEN ENERGY BASED ON THE VALUES FOR STOCKS
        road_model_input_wide['Activity'] = road_model_input_wide['Mileage'] * road_model_input_wide['Occupancy_or_load'] * road_model_input_wide['Stocks']
        road_model_input_wide['Travel_km'] = road_model_input_wide['Mileage'] * road_model_input_wide['Stocks']
        road_model_input_wide['Energy'] = road_model_input_wide['Travel_km'] / road_model_input_wide['Efficiency']
        
        #anbd i guess do the same thing for non road, except, since we are most confident in energy here, calcualte everything based off enerrgy and intensity:
        non_road_model_input_wide['Activity'] = non_road_model_input_wide['Energy'] * non_road_model_input_wide['Intensity']
        non_road_model_input_wide['Stocks'] = non_road_model_input_wide['Activity'] / non_road_model_input_wide['Activity_per_Stock']

    if ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR:
        #use teh funcitons in adjust_data_to_match_esto.py to adjust the energy use to match the esto data in the MODEL_BASE_YEAR. To do this we will have needed to run the model up ot htat year already, and saved the results. We will then use the results to adjust the energy use to match the esto data. This is so that we can make sure that stocks, mileage and efficiency are still relatively close to their previous estiamtes while energy use is equal to the esto data. Currently this is done with optimisation in the optimise_to_calcualte_base_data.py file.
        
        
        #save non_road_model_input_wide
        non_road_model_input_wide.to_csv('1_non_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
        
        road_model_input_wide, non_road_model_input_wide, supply_side_fuel_mixing = adjust_data_to_match_esto.adjust_data_to_match_esto_handler(BASE_YEAR, ECONOMY_ID, road_model_input_wide,non_road_model_input_wide, supply_side_fuel_mixing, demand_side_fuel_mixing, TESTING=adjust_data_to_match_esto_TESTING, USE_PREVIOUS_OPTIMISATION_RESULTS_FOR_THIS_DATA_SYSTEM_INPUT=USE_PREVIOUS_OPTIMISATION_RESULTS_FOR_THIS_DATA_SYSTEM_INPUT, USE_SAVED_OPT_PARAMATERS=USE_SAVED_OPT_PARAMATERS)
        
        #save non_road_model_input_wide
        non_road_model_input_wide.to_csv('2_non_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
        
    #set New_vehicle_efficiency now, since it may have been affected by efficie4ncy adjsutments in adjust_data_to_match_esto.py
    road_model_input_wide['New_vehicle_efficiency'] = road_model_input_wide['Efficiency'] *1.15#seems like new vehicles are 15% more efficient than the average vehicle (which is probasbly about 10 years old. this would make sense with an avg 1.5% efficiency improvement per year (leading to about 16% improvement).
    road_model_input_wide, non_road_model_input_wide= insert_new_age_distribution_col(road_model_input_wide, non_road_model_input_wide, BASE_YEAR, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR)
    
    road_model_input_wide, growth_forecasts_wide = apply_activity_efficiency_improvements(road_model_input_wide, growth_forecasts_wide)#todo check that growth_forecasts_wide is being used in foloowing functions
    
    #save
    supply_side_fuel_mixing.to_csv('intermediate_data/model_inputs/{}/{}_supply_side_fuel_mixing.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
    demand_side_fuel_mixing.to_csv('intermediate_data/model_inputs/{}/{}_demand_side_fuel_mixing.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
    growth_forecasts_wide.to_csv('intermediate_data/model_inputs/{}/{}_growth_forecasts_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
    road_model_input_wide.to_csv('intermediate_data/model_inputs/{}/{}_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
    non_road_model_input_wide.to_csv('intermediate_data/model_inputs/{}/{}_non_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
    
    if ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR:
        #because we jsut made changes to the input data we should adjsut the vehicle sales shares so that they are consistent with the new data. We'll do this now out of simplicity:
        sales_share_data =vehicle_sales_share_creation_handler(ECONOMY_ID, RECALCULATE_SALES_SHARES_USING_RECALCULATED_INPUT_DATA = True, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, USE_LARGE_EPSILON=True)# create_vehicle_sales_share_input(ECONOMY_ID, 
        #RECALCULATE_SALES_SHARES_USING_RECALCULATED_INPUT_DATA=True)
        #drop sales share form the road model input wide and non road model input wide, then merge in the new sales share data
        road_model_input_wide = road_model_input_wide.drop(columns=['Vehicle_sales_share'])
        #rename value in sales_share_data to Vehicle_sales_share
        sales_share_data = sales_share_data.rename(columns={'Value':'Vehicle_sales_share'})
        
        road_model_input_wide = road_model_input_wide.merge(sales_share_data, on=['Economy', 'Scenario', 'Date', 'Transport Type','Vehicle Type', 'Medium', 'Drive'], how='left')
        #and do the same for non road
        non_road_model_input_wide = non_road_model_input_wide.drop(columns=['Vehicle_sales_share'])
        non_road_model_input_wide = non_road_model_input_wide.merge(sales_share_data, on=['Economy', 'Scenario', 'Date', 'Transport Type','Vehicle Type', 'Medium', 'Drive'], how='left')
                
        road_model_input_wide.to_csv('intermediate_data/model_inputs/{}/{}_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
        non_road_model_input_wide.to_csv('intermediate_data/model_inputs/{}/{}_non_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
#%%


def set_intensity_manually(non_road_model_input_wide):
    
    #if intensity is still na then we need to set it manually. We will use the same process done in 'import_transport_system_data.py' which is using a constant value for non new drive types, and new drive types will be set to 0.5 of that. 
    new_drive_types = [drive for drive in non_road_model_input_wide.Drive.dropna().unique().tolist() if 'electric' in drive]# or 'ammonia' in drive or 'hydrogen' in drive
    
    non_new_drive_types = [drive for drive in non_road_model_input_wide.Drive.dropna().unique().tolist() if drive not in new_drive_types]
    
    #get average intensity for drives that are not new
    average_intensity_for_non_new_drives = non_road_model_input_wide.loc[non_road_model_input_wide.Drive.isin(non_new_drive_types)].groupby(['Economy', 'Scenario', 'Transport Type'])['Intensity'].mean().reset_index()
    #if its na then raise an error
    if average_intensity_for_non_new_drives.Intensity.isna().any():
        breakpoint()
        time.sleep(1)
        raise ValueError('average_intensity_for_non_new_drives has na values')

    #join the average intensity to the non road model input wide
    non_road_model_input_wide = non_road_model_input_wide.merge(average_intensity_for_non_new_drives, on=['Economy', 'Scenario', 'Transport Type'], how='left', suffixes=('', '_y'))
    #where intensity is na and the drive is in new drive types, set intensity to 0.5 of the average intensity for non new drives
    non_road_model_input_wide.loc[(non_road_model_input_wide['Intensity'].isna()) & (non_road_model_input_wide['Drive'].isin(new_drive_types)), 'Intensity'] = non_road_model_input_wide.loc[(non_road_model_input_wide['Intensity'].isna()) & (non_road_model_input_wide['Drive'].isin(new_drive_types)), 'Intensity_y'] * 0.5
    #and set intensity to the average intensity for non new drives where intensity is na and the drive is not in new drive types
    non_road_model_input_wide.loc[(non_road_model_input_wide['Intensity'].isna()) & (~non_road_model_input_wide['Drive'].isin(new_drive_types)), 'Intensity'] = non_road_model_input_wide.loc[(non_road_model_input_wide['Intensity'].isna()) & (~non_road_model_input_wide['Drive'].isin(new_drive_types)), 'Intensity_y']
    #drop the intensity_y column
    non_road_model_input_wide = non_road_model_input_wide.drop(columns=['Intensity_y'])
    
    return non_road_model_input_wide

def insert_new_age_distribution_col(road_model_input_wide, non_road_model_input_wide, BASE_YEAR, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR):
    if ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR:
        BASE_YEAR = config.OUTLOOK_BASE_YEAR
    #insert age distribution in the first col of the road model input wide
    road_model_input_wide_first_year = road_model_input_wide.loc[road_model_input_wide.Date == BASE_YEAR].copy()
    #first, if stocks are nan set them to 0
    road_model_input_wide_first_year.loc[road_model_input_wide_first_year.Stocks.isna(), 'Stocks'] = 0
    # then if stocks are 0 then set Average age to nan
    road_model_input_wide_first_year.loc[(road_model_input_wide_first_year.Stocks == 0), 'Average_age'] = np.nan
    
    # road_model_input_wide_first_year['Age_distribution'] = road_model_input_wide_first_year.apply(road_model_functions.create_age_distribution_entry, axis=1)
    
    road_model_input_wide_first_year['Age_distribution'] = road_model_input_wide_first_year.apply(lambda row: road_model_functions.create_age_distribution_entry(row), axis=1)
    
    road_model_input_wide = pd.concat([road_model_input_wide_first_year, road_model_input_wide.loc[road_model_input_wide.Date != BASE_YEAR]])
    #insert age distribution in the first col of the non-road model input wide
    #insert age distribution in the first col of the road model input wide
    non_road_model_input_wide_first_year = non_road_model_input_wide.loc[non_road_model_input_wide.Date == BASE_YEAR].copy()
    #first, if stocks are nan set them to 0
    non_road_model_input_wide_first_year.loc[non_road_model_input_wide_first_year.Stocks.isna(), 'Stocks'] = 0
    # then if stocks are 0 then set Average age to nan
    non_road_model_input_wide_first_year.loc[(non_road_model_input_wide_first_year.Stocks == 0), 'Average_age'] = np.nan
    #also, in some cases we might have added some stocks in where they were prev 0, so there is an average age of np.nan or 0. we will set this to the average of all otehr ages (anything >1)
    if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
        #make a not that we are doing this as its soemthing tat should be fixed in the future
        print('WARNING: we are filling in missing average ages with the average of all other ages. This is not ideal and should be fixed in the future, this is in the function fill_missing_ages_where_stocks_greater_than_zero() in calculate_inputs_for_model.py')
    non_road_model_input_wide_first_year = fill_missing_ages_where_stocks_greater_than_zero(non_road_model_input_wide_first_year)#currently on;y used for non road because no issues with road data yet
    #now we can create the age distribution

    non_road_model_input_wide_first_year['Age_distribution'] = non_road_model_input_wide_first_year.apply(lambda row: road_model_functions.create_age_distribution_entry(row), axis=1)
    non_road_model_input_wide = pd.concat([non_road_model_input_wide_first_year, non_road_model_input_wide.loc[non_road_model_input_wide.Date != BASE_YEAR]])
    
    return road_model_input_wide, non_road_model_input_wide

def fill_missing_ages_where_stocks_greater_than_zero(model_input_wide_first_year):
    missing_ages = model_input_wide_first_year[(model_input_wide_first_year.Stocks>0)&((model_input_wide_first_year.Average_age.isna())|(model_input_wide_first_year.Average_age==0))]
    if missing_ages.empty:
        return model_input_wide_first_year
    other_ages = model_input_wide_first_year[(model_input_wide_first_year.Stocks>0)&(model_input_wide_first_year.Average_age>1)]
    #find avg by medium then join it onto missing_ages:
    avg_age_by_medium = other_ages.groupby(['Medium'])['Average_age'].mean().reset_index()
    #double check there is an avg age for each medium, if not calcualte it using other mediums
    if avg_age_by_medium.Average_age.isna().any():
        avg_age = other_ages.Average_age.mean()
        avg_age_by_medium.loc[avg_age_by_medium.Average_age.isna(), 'Average_age'] = avg_age
    missing_ages = missing_ages.merge(avg_age_by_medium, on=['Medium'], how='left', suffixes=('_old', ''))
    #drop the avg age_y column
    missing_ages = missing_ages.drop(columns=['Average_age_old'])
    #now join missing ages back onto model_input_wide_first_year after dropping the rows that are in missing_ages
    model_input_wide_first_year = model_input_wide_first_year[~((model_input_wide_first_year.Stocks>0)&((model_input_wide_first_year.Average_age.isna())|(model_input_wide_first_year.Average_age==0)))]
    model_input_wide_first_year = pd.concat([model_input_wide_first_year, missing_ages])
    return model_input_wide_first_year

def apply_activity_efficiency_improvements(road_model_input_wide, growth_forecasts_wide):
    #apply efficiency improvements to activity growth before using it in the mdoel. This will be done by minsing the change in activity as a result of the activity efficiency (which would normally be tiemsed by activity) from the activity growth by the activity efficiency in each year. 
    # The activity efficiency in each year will also be calcualted, starting at 1 in the base year and then increasing by the efficiency improvement rate each year.
    activity_efficiency_improvement_df = road_model_input_wide[['Date', 'Economy', 'Scenario', 'Transport Type','Activity_efficiency_improvement']].drop_duplicates()
    activity_efficiency_improvement_df['Activity_efficiency'] = 1
    # #apply the efficiency improvement rate, compounding each year #NB i dont think this needs to be done because we ae already essentially compounding the efficiency improvement rate in the activity efficiency improvement rate by timesing it by activity efficiency in the model each year. 
    # activity_efficiency_improvement_df['Activity_efficiency_improvement'] = activity_efficiency_improvement_df.groupby(['Economy', 'Scenario', 'Transport Type'])['Activity_efficiency_improvement'].cumprod()
    activity_efficiency_improvement_df['Activity_efficiency'] = activity_efficiency_improvement_df['Activity_efficiency'] * activity_efficiency_improvement_df['Activity_efficiency_improvement']
    #minus activity efficiency from activity growth
    growth_forecasts_wide = growth_forecasts_wide.merge(activity_efficiency_improvement_df, on=['Economy', 'Scenario', 'Date', 'Transport Type'], how='left')#TODO CHECK THAT VEHICLE TYPE IS IN THE DF?
    
    growth_forecasts_wide['Activity_growth'] = growth_forecasts_wide['Activity_growth'] - (growth_forecasts_wide['Activity_efficiency']-1)
    
    return road_model_input_wide, growth_forecasts_wide


    