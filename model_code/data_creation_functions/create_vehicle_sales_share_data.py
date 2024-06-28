#we will take in the vehicle sales from historical data, then adjust them according to the patterns we expect to see. i.e. nz moves to 100% ev's by 2030.

#we will also create a vehicle sales distribution that replicates what each scenario in the 8th edition shows. We can use this to help also load all stocks data so that we can test the model works like the 8th edition



#NOTE, ONE DAY IT WOULD BE GOOD TO REDO ALL  THIS CODE. ITS REALLY HARD TO USE AND FIX. AND CONFUSING!
#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
current_working_dir = os.getcwd()
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = re.split('transport_model_9th_edition', script_dir)[0] + 'transport_model_9th_edition'
from .. import utility_functions
from .. import config
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

X_ORDER = 'linear'#set me to linear or the order for the spline
#%%

def vehicle_sales_share_creation_handler(ECONOMY_ID,  RECALCULATE_SALES_SHARES_USING_RECALCULATED_INPUT_DATA, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, USE_LARGE_EPSILON=False):
    """
    Args:
    """
    if ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR:    
        CURRENT_BASE_YEAR = config.OUTLOOK_BASE_YEAR
    else:
        CURRENT_BASE_YEAR = config.DEFAULT_BASE_YEAR
    
    ECONOMIES_WITH_MODELLING_COMPLETE_DICT = yaml.load(open(root_dir + '/' + 'config/parameters.yml'), Loader=yaml.FullLoader)['ECONOMIES_WITH_MODELLING_COMPLETE']
    SET_YEAR_WITH_MOST_VALUES_TO_BASE_YEAR = ECONOMIES_WITH_MODELLING_COMPLETE_DICT[ECONOMY_ID]
    
    transport_data_system_df = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/transport_data_system_extract.csv')

    if RECALCULATE_SALES_SHARES_USING_RECALCULATED_INPUT_DATA: 
        # breakpoint()   
        transport_data_system_df = use_previous_projection_for_current_and_historical_sales_shares(ECONOMY_ID)
    transport_data_system_df['road'] = transport_data_system_df['Medium']=='road'
    new_transport_data_system_df = create_current_and_historical_shares_from_activity(ECONOMY_ID, transport_data_system_df, SET_YEAR_WITH_MOST_VALUES_TO_BASE_YEAR, CURRENT_BASE_YEAR)
    #drop 'road' for now (it wont work with the concordances)
    new_transport_data_system_df = new_transport_data_system_df.drop(columns=['road'])
    new_sales_shares_sum, model_concordances_user_input_and_growth_rates =   format_and_check_current_and_historical_shares(ECONOMY_ID,new_transport_data_system_df, CURRENT_BASE_YEAR)
    new_sales_shares_sum, new_sales_shares_sum_original = calculate_current_and_historical_shares(new_sales_shares_sum, CURRENT_BASE_YEAR)
    alternate_sales_shares, alternate_filepaths = incorporate_alternate_sales_shares(ECONOMY_ID)
    
    passenger_drive_shares, freight_drive_shares = check_and_format_manually_specified_sales_shares(ECONOMY_ID)
    
    passenger_drive_shares, freight_drive_shares = incorporate_manually_specified_sales_shares(ECONOMY_ID, passenger_drive_shares, freight_drive_shares)
    
    sales_shares =    merge_manually_specified_with_alternate_and_early_year_sales_shares(ECONOMY_ID, passenger_drive_shares, freight_drive_shares, alternate_sales_shares, new_sales_shares_sum)
    sales_shares = clean_and_format_sales_shares_before_calcualtions(ECONOMY_ID, sales_shares, CURRENT_BASE_YEAR)
    sales_shares = check_for_series_with_too_few_values_to_interpolate(sales_shares, CURRENT_BASE_YEAR)
    sales_shares = interpolate_missing_sales_shares(sales_shares, ECONOMY_ID,  interpolation_method='linear')
    
    sales_shares = fill_missing_drives_using_median_of_early_years(ECONOMY_ID, sales_shares, model_concordances_user_input_and_growth_rates, CURRENT_BASE_YEAR, USE_LARGE_EPSILON=USE_LARGE_EPSILON)
    sales_shares = normalize_drive_shares(sales_shares, new_sales_shares_sum_original)

    sales_shares = apply_vehicle_type_growth_rates(sales_shares)
    # if ECONOMY_ID=='13_PNG' and RECALCULATE_SALES_SHARES_USING_RECALCULATED_INPUT_DATA:
    #     breakpoint()
    sales_shares = clean_and_run_final_checks_on_data(ECONOMY_ID, sales_shares)
    
    # #extract reference buys
    # a = new_transport_data_system_df[(new_transport_data_system_df['Vehicle Type']=='bus') & (new_transport_data_system_df['Scenario']=='Reference')].copy()
    archive_inputs_and_previous_results(ECONOMY_ID, sales_shares, alternate_filepaths)
    return sales_shares

def create_alternate_sales_share_file(ECONOMY_ID, sales_shares=None, vehicle_type=None, medium=None, drives=None, transport_type=None, scenario=None, filepath=None, LOAD_LATEST_SALES_SHARES=False, secondary_economy_ID = None, DELETE_ALL_FILES_IN_FOLDER=False, ALL_IN_ONE_FILE=False, chosen_scenario= None):
    #helper function: take in sales shares as a series that arent in the right format and create a df with the right format thn save to input_data/alternate_sales_shares/ECONOMY_ID
    #e.g. load in latest sales shares creeated:
    if secondary_economy_ID is None:
        #if you set secondary_economy_ID to an economy then all the sales shares we save will be based on the sales shares of that economy. This is useful for when we want to save the sales shares of one economy for another economy to use.
        secondary_economy_ID = ECONOMY_ID
    if LOAD_LATEST_SALES_SHARES:
        directory = "intermediate_data/model_inputs/"  # Replace with your actual directory path
        import utility_functions
        new_directory = utility_functions.find_latest_folder_via_regex(directory)
        breakpoint()
        try:
            sales_shares = pd.read_csv(root_dir + '/' + '{}/{}/{}_new_sales_shares_concat_interp.csv'.format(directory,new_directory, secondary_economy_ID))
        except FileNotFoundError:
            print(f'Since this file is not in the directory, you probably ran this function after half running the model for {secondary_economy_ID}. Please fully run the model for {secondary_economy_ID} first and then run this function again')
            raise FileNotFoundError
        #split sales shares into transporty type, vehicle type, medium, scenario and save as inidivdual folders in input_data/model_inputs/{}/{}'.format(ECONOMY_ID, filepath)), where filepath is the vehicle type and transport type
        #set economy to ECONOMY_ID where previously it was secondary_economy_ID
        sales_shares['Economy'] = ECONOMY_ID
    
        if chosen_scenario != None:
            sales_shares = sales_shares.loc[sales_shares['Scenario']==chosen_scenario]
        if ALL_IN_ONE_FILE:
            for scenario in sales_shares['Scenario'].unique():
                sales_shares_0 = sales_shares.loc[sales_shares['Scenario']==scenario].copy()
                if len(sales_shares_0)==0:
                    continue
                #cahnge Drive_share to Share
                sales_shares_0.rename(columns={'Drive_share':'Share'}, inplace=True)
                #drop road
                sales_shares_0.drop(columns=['road'], inplace=True)
                if medium != None:
                    sales_shares_0 = sales_shares_0[sales_shares_0.Medium==medium]
                if drives != None:
                    sales_shares_0 = sales_shares_0[sales_shares_0.Drive.isin(drives)]
                #remove all files from the folder first
                folder = 'input_data/alternate_sales_shares/{}'.format(ECONOMY_ID)
                #remove all files from the folder first
                if DELETE_ALL_FILES_IN_FOLDER:
                    for the_file in os.listdir(folder):
                        file_path = os.path.join(folder, the_file)
                        try:
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                        except Exception as e:
                            print(e)
                        
                sales_shares_0.to_csv(root_dir + '/' + 'input_data/alternate_sales_shares/{}/{}_{}.csv'.format(ECONOMY_ID, 'all_usa_ref_shares', scenario), index=False)
        else:
            for transport_type in sales_shares['Transport Type'].unique():
                for vehicle_type in sales_shares['Vehicle Type'].unique():
                    for medium in sales_shares['Medium'].unique():
                        for scenario in sales_shares['Scenario'].unique():
                            sales_shares_0 = sales_shares.loc[(sales_shares['Transport Type']==transport_type)&(sales_shares['Vehicle Type']==vehicle_type)&(sales_shares['Medium']==medium)&(sales_shares['Scenario']==scenario)].copy()
                            if len(sales_shares_0)==0:
                                continue
                            #cahnge Drive_share to Share
                            sales_shares_0.rename(columns={'Drive_share':'Share'}, inplace=True)
                            #drop road
                            sales_shares_0.drop(columns=['road'], inplace=True)
                            sales_shares_0.to_csv(root_dir + '/' + 'input_data/alternate_sales_shares/{}/{}_{}_{}_{}.csv'.format(ECONOMY_ID, transport_type, vehicle_type, medium, scenario), index=False)
                            
    else:
        #use the sales shares passed in as an arg
        pass
    
    return        

def archive_inputs_and_previous_results(ECONOMY_ID, new_sales_shares_all_new, alternate_filepaths):

    #archive previous results:
    archiving_folder = archiving_scripts.create_archiving_folder_for_FILE_DATE_ID()
    #save the variables we used to calculate the data by savinbg the 'input_data/vehicle_sales_share_inputs.xlsx' file
    shutil.copy('input_data/vehicle_sales_share_inputs.xlsx', archiving_folder + '/vehicle_sales_share_inputs.xlsx')

    #and save thsoe form alternate_filepaths to same place
    for filepath in alternate_filepaths:
        filename = os.path.basename(filepath)
        shutil.copy(filepath, archiving_folder + '/{}'.format(filename))
        
    #save data so it can be used for plotting and such:
    new_sales_shares_all_new.to_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_vehicle_sales_share.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index = False)  
    
def format_and_check_current_and_historical_shares(ECONOMY_ID, new_transport_data_system_df, CURRENT_BASE_YEAR):
        
        #####################################
        #PREPARE INPUT DATA
        #####################################

        #first we need to separate the sales share of vehicle types from the sales share of drives, by transport type. Since the way the values we created was simply mutliplication, we can jsut reverse that, i think.
        #so sum by vehicle type to get the total sales share of each vehicle type
        #then if we divide this by the final sales share values for each v-type/drive we can recreate the shares by drive type, witihin each vehicle type.
        #now for shares by drive type, witihin each vehicle type, we can create the shares we want.
        #sum by vtype economy year and scenario
        new_sales_shares_sum = new_transport_data_system_df.copy()

        #Identify duplicates in case we have multiple rows for the same economy, vehicle type, drive type, transport type and date
        new_sales_shares_sum_dupes = new_sales_shares_sum[new_sales_shares_sum.duplicated(subset=['Economy', 'Scenario', 'Medium','Vehicle Type', 'Transport Type','Drive', 'Date','Medium'])]
        if len(new_sales_shares_sum_dupes)>0:#somehow getting dupes. 
            raise ValueError('new_sales_shares_sum_dupes is not empty. This should not happen. Investigate')
            
        #now doulbe check we have the required categories that are in the concordances
        model_concordances_user_input_and_growth_rates = pd.read_csv(root_dir + '/' + 'intermediate_data/computer_generated_concordances/{}'.format(config.model_concordances_user_input_and_growth_rates_file_name))
        #filter for ECONOMY_ID
        model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates.loc[model_concordances_user_input_and_growth_rates['Economy']==ECONOMY_ID]
        #drop all measures that are not vehicle sales share
        model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates[model_concordances_user_input_and_growth_rates['Measure']=='Vehicle_sales_share']
        #drop any cols not in the new_sales_shares_sum
        cols = [col for col in model_concordances_user_input_and_growth_rates.columns if col in new_sales_shares_sum.columns]
        model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates[cols]
        model_concordances_user_input_and_growth_rates.drop_duplicates(inplace=True)
        new_INDEX_COLS = [col for col in config.INDEX_COLS if col in model_concordances_user_input_and_growth_rates.columns]
        
        #in case its not there, add BASE YEAR to the concordances which canb be a copy of the CURRENT_BASE_YEAR +1
        if CURRENT_BASE_YEAR not in model_concordances_user_input_and_growth_rates['Date'].unique():
            model_concordances_user_input_and_growth_rates_base = model_concordances_user_input_and_growth_rates.loc[model_concordances_user_input_and_growth_rates['Date']==CURRENT_BASE_YEAR+1].copy()
            model_concordances_user_input_and_growth_rates_base['Date'] = CURRENT_BASE_YEAR
            model_concordances_user_input_and_growth_rates = pd.concat([model_concordances_user_input_and_growth_rates,model_concordances_user_input_and_growth_rates_base])

        ############################
        #NOW CHECK FOR MISSING ROWS
        ############################
        # # Ensure the index is set for both dataframes
        # new_sales_shares_sum.set_index(new_INDEX_COLS, inplace=True)
        # model_concordances_user_input_and_growth_rates.set_index(new_INDEX_COLS, inplace=True)

        # # Reset index to use 'merge' and 'indicator'
        # new_sales_shares_sum_reset = new_sales_shares_sum.reset_index()
        # model_concordances_reset = model_concordances_user_input_and_growth_rates.reset_index()

        # Perform a full outer join to find missing index values in both dataframes
        merged_df = pd.merge(new_sales_shares_sum, model_concordances_user_input_and_growth_rates, on=new_INDEX_COLS, how='outer', indicator=True)

        # Identify missing values from both sides
        missing_in_new_sales = merged_df[merged_df['_merge'] == 'right_only']
        missing_in_model_concordances = merged_df[merged_df['_merge'] == 'left_only']
        merged_df = merged_df[merged_df['_merge'] == 'both']
        # Drop the extra '_merge' column
        merged_df.drop(columns=['_merge'], inplace=True)
        
        # Handle missing values in new_sales_shares_sum BY ADDING THEM TO THE DATAFRAME WITH NAN VALUES
        if not missing_in_new_sales.empty:
            missing_in_new_sales = missing_in_new_sales[new_INDEX_COLS]
            missing_in_new_sales['Sales Share'] = np.nan
            merged_df = pd.concat([merged_df, missing_in_new_sales])
            if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                print(f'Missing {len(missing_in_new_sales)} rows in our user input dataset when we compare it to the concordance')
            
        new_sales_shares_sum = merged_df.copy()
        #show user the rows that were only in new_sales_shares_sum and not in concordances
        if not missing_in_model_concordances.empty:
            print('Missing {} rows in the user input concordance'.format(len(missing_in_model_concordances)))
            print('We removed these rows from the user input dataset. If you intended to have data for these rows, please add them to the concordance table.')
        
        return new_sales_shares_sum, model_concordances_user_input_and_growth_rates
    
def calculate_current_and_historical_shares(new_sales_shares_sum, CURRENT_BASE_YEAR):
    #####################################
    #CALCAULTE CURRENT SHARES  
    #####################################
    #before doing anything, create new col called 'road' that is True or False based on the medium. That way we can easily handle switching between non road types by treating any transport type share sums, as also having to be grouped by 'road'.
    new_sales_shares_sum['road'] = new_sales_shares_sum['Medium']=='road'
    
    
    #PLEASE NOTE THAT VALUE IS THE % OF THE TRANSPORT TYPE FOR THAT VEHICLE TYPE AND DRIVE TYPE. SO IF WE SUM BY VEHICLE TYPE WE GET THE TOTAL SHARE OF EACH VEHICLE TYPE. IF WE DIVIDE BY THIS WE GET THE SHARE OF EACH DRIVE TYPE WITHIN EACH VEHICLE TYPE
    #reaplce Value with Transport_type_share
    #I THINK WE NEED TO CONVERT THIS TO THE SHARE OF ACTIVITY RATHER THAN NEW STOCKS SO THE VEHICLE TYPE SHARE IS CARRIED BETTER.
    new_sales_shares_sum = new_sales_shares_sum.rename(columns={'Sales Share':'Transport_type_share'})

    new_sales_shares_sum['Vehicle_type_share_sum'] = new_sales_shares_sum.groupby(['Economy', 'Scenario', 'Vehicle Type','road', 'Medium','Transport Type', 'Date'])['Transport_type_share'].transform('sum')

    #just to be safe, where all Transport_type_share values for a group are na, set Vehicle_type_share_sum to na too, not 0 as that is misleading
    #identify groups where all 'Transport_type_share' values are NaN and set 'Vehicle_type_share_sum' to NaN for those groups
    all_nan_groups = new_sales_shares_sum.groupby(['Economy', 'Scenario', 'Vehicle Type', 'road', 'Medium', 'Transport Type', 'Date'])['Transport_type_share'].transform(lambda x: x.isna().all())
    new_sales_shares_sum.loc[all_nan_groups, 'Vehicle_type_share_sum'] = np.nan

    new_sales_shares_sum['Drive_share'] = new_sales_shares_sum['Transport_type_share']/new_sales_shares_sum['Vehicle_type_share_sum']

    #now we can create the shares we want

    #first create a clean dataframe with all values set to NA for every year after the base year
    new_sales_shares_sum_clean = new_sales_shares_sum[['Economy', 'Scenario','Medium', 'road', 'Transport Type', 'Date', 'Vehicle Type', 'Drive', 'Drive_share']].drop_duplicates()

    new_sales_shares_sum_0 = new_sales_shares_sum_clean.copy()

    new_sales_shares_sum_0.loc[new_sales_shares_sum_0['Date']>CURRENT_BASE_YEAR, 'Drive_share'] = np.nan

    #sort
    new_sales_shares_sum_0 = new_sales_shares_sum_0.sort_values(by=['Economy', 'Scenario', 'Date', 'Vehicle Type','Medium','road', 'Transport Type', 'Drive'])
    
    return new_sales_shares_sum_0, new_sales_shares_sum

def create_current_and_historical_shares_from_activity(ECONOMY_ID, transport_data_system_df, SET_YEAR_WITH_MOST_VALUES_TO_BASE_YEAR, CURRENT_BASE_YEAR, DATAPOINTS_AVAILABLE_THRESHOLD=10, PLOTTING=False):
    """
    Creates data for the sales shares for the years where we have input data available. This should be used instead of anything that is specified in the input sales share series.
    This process should calcualte the sales share using activity data rather than actual sales (change in stocks) data since the way we calcualte new sales is sales share times new activity (divided by mileage and occupancy_or_load to get new stocks)
    
    Args:
        ECONOMY_ID (str): The economy identifier.
        transport_data_system_df (DataFrame): The DataFrame containing transport data.
        YEARS_TO_KEEP_AFTER_BASE_YEAR (int): Number of years to keep data after the base year.
        SET_YEAR_WITH_MOST_VALUES_TO_BASE_YEAR (bool): Whether to set the year with most values as the base year.

    Returns:
        DataFrame: A DataFrame with calculated sales shares.
    """
    sales = transport_data_system_df.copy()
    #grab ECONOMY_ID
    sales = sales.loc[sales['Economy']==ECONOMY_ID]
    #calcualte activity (except for non road where we just keep same activity)
    sales = sales.loc[sales['Measure'].isin(['Occupancy_or_load', 'Mileage','Stocks', 'Activity'])]
    index_cols_no_measure = config.INDEX_COLS.copy()
    index_cols_no_measure.remove('Measure')
    index_cols_no_measure.remove('Unit')
    index_cols_no_measure = index_cols_no_measure + ['road']
    sales = sales.pivot(index =index_cols_no_measure, columns = 'Measure', values = 'Value').reset_index()
    #where road is true, clacualte activity and call it Value so it can be used later. where road is false, set activity as stocks, since this is what it originally was anyway (i.e. activity is stocks for non road)
    sales['Value'] = np.where(sales['road']==True, sales['Mileage'] * sales['Occupancy_or_load']* sales['Stocks'], sales['Activity'])
    
    ############TEMP###############
    #theres a slight chance we get inf/na values from one of the prodcuts being inf/na themselves. in this case we really should be tracking dsown the cause of the sisue.. but for now, just remove them (and use a breakpoint so we can find this later) 
    inf_or_na = sales.loc[sales['Value'].isna()|sales['Value'].isin([np.inf, -np.inf])]
    if len(inf_or_na)>0:
        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
            breakpoint()
        #set them to 0
        sales.loc[sales['Value'].isna()|sales['Value'].isin([np.inf, -np.inf]), 'Value'] = 0
    ############TEMP###############
    
    sales = sales.drop(columns=['Mileage', 'Occupancy_or_load', 'Stocks', 'Activity'])
    #calcualte share of activity
    EPSILON = 1e-9

    sales['Sales Share'] = sales.groupby(['Economy', 'Scenario', 'Date', 'Transport Type','road'])['Value'].transform(lambda x: x / (x.sum() + EPSILON))
    
    #set measure to 'Vehicle_sales_share'
    sales['Measure'] = 'Vehicle_sales_share'
    sales['Unit'] = '%'
    #repalce nan with 0
    sales = sales.fillna(0)
    
    #now we want to find the year with the most values that arent 0. this is essentially the year with the most data and is therefor emost suitable to abse our sales shares off (data with less values may be missing values and tehrefore exaggerating sales share fr certain vehicle types)
    #we will do this by grouping by year an counting the number of non zero values. then we will sort by this count and take the year with the most non zero values
    # making an update to make this identify the year with most values by transport type and economy (rather than just date), so we can have more flexibility:
    year_with_most_values = sales.loc[sales['Value']>0.].groupby(['Date', 'Economy', 'road','Transport Type'])['Value'].count().reset_index()
    
    #filter for max count for each economy and transport type:
    for economy in year_with_most_values.Economy.unique():
        for transport_type in year_with_most_values['Transport Type'].unique():
            for road_bool in year_with_most_values.road.unique():
                
                #grab date with most values
                max_count = year_with_most_values.loc[(year_with_most_values['Economy']==economy)&(year_with_most_values['Transport Type']==transport_type)&(year_with_most_values['road']==road_bool)]['Value'].max()
                #drop rows without the max count
                year_with_most_values = year_with_most_values.loc[~((year_with_most_values['Economy']==economy)&(year_with_most_values['Transport Type']==transport_type)&(year_with_most_values['Value']!=max_count)&(year_with_most_values['road']==road_bool))]
                
                #also keep only the maximum date of these
                max_date = year_with_most_values.loc[(year_with_most_values['Economy']==economy)&(year_with_most_values['Transport Type']==transport_type)&(year_with_most_values['road']==road_bool)]['Date'].max()
                #but if we are not setting the year with the most values to the base year, then we want to grab the data for the base year, if there are enough datapoints available
                if not SET_YEAR_WITH_MOST_VALUES_TO_BASE_YEAR:
                    proposed_max_date = CURRENT_BASE_YEAR
                    x = year_with_most_values.loc[(year_with_most_values['Economy']==economy)&(year_with_most_values['Transport Type']==transport_type)&(year_with_most_values['road']==road_bool)&(year_with_most_values['Date']==proposed_max_date)]
                    if len(x) > 0:
                        if x.Value.values[0] > DATAPOINTS_AVAILABLE_THRESHOLD:
                            max_date = proposed_max_date
                        else:
                            #take the date with most values available
                            pass                       
                #filter out the other dates for this subset
                year_with_most_values = year_with_most_values.loc[~((year_with_most_values['Economy']==economy)&(year_with_most_values['Transport Type']==transport_type)&(year_with_most_values['Date']!=max_date)&(year_with_most_values['road']==road_bool))]
                
    #drop value
    year_with_most_values = year_with_most_values.drop(columns=['Value'])                 
    #join to sales and keep only the rows with the max year
    sales = sales.merge(year_with_most_values, on=['Economy', 'Transport Type', 'Date', 'road'], how='inner')

    if PLOTTING:
        from ..plotting_functions import plot_user_input_data
        plot_user_input_data.plot_estimated_data_system_sales_share(sales,ECONOMY_ID)
    
    #drop Total Stocks column and Value column
    sales = sales.drop(columns=['Value'])

    #now replicate the sales shares for each scenario and for each year between the CURRENT_BASE_YEAR and the config.END_YEAR of the scenario.
    try:
        #filter for a unique scenario in the sales df
        sales = sales[sales.Scenario==sales.Scenario.unique()[0]]
    except:
        breakpoint()#seems were getting 0s for bd
    sales_dummy = sales.copy()
    new_sales = pd.DataFrame()
    for scenario in config.SCENARIOS_LIST:
        sales_dummy['Scenario'] = scenario
        new_sales = pd.concat([new_sales, sales_dummy])
    
    #now we want to replicate the df (BUT NOT THE SALES SHARE) for each year between the CURRENT_BASE_YEAR and the config.END_YEAR of the scenario
    sales_dummy = new_sales.copy()
    new_sales_years = pd.DataFrame()
    for year in range(CURRENT_BASE_YEAR, config.END_YEAR+1):
        sales_dummy['Date'] = year
        new_sales_years = pd.concat([new_sales_years, sales_dummy])
    
    #set sales share for all values after CURRENT_BASE_YEAR to np.nan (add three so that we still have a few values for the interpoaltion to go off)
    new_sales_years.loc[new_sales_years['Date']>CURRENT_BASE_YEAR, 'Sales Share'] = np.nan

    #set unit to %
    new_sales_years['Unit'] = '%'
    
    return new_sales_years

def use_previous_projection_for_current_and_historical_sales_shares(ECONOMY_ID):
    """
    Use the data from running the model up to the Actual base year to calcualte the sales shares for the years where we have input data available. This should be used instead of anything that is specified in the input sales share series, but is only used when RECALCULATE_SALES_SHARES_USING_RECALCULATED_INPUT_DATA for this ECONOMY_ID is True (otherwise we use the data from the transport data system in create_current_and_historical_shares_from_activity)
    """
    try:
        road_model_input_wide = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))
        non_road_model_input_wide = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_non_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))
    except FileNotFoundError: 
        #try find the  most recent available folder:
        directory = "intermediate_data/model_inputs/"  # Replace with your actual directory path
        import utility_functions
        new_directory = utility_functions.find_latest_folder_via_regex(directory)
        road_model_input_wide = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_road_model_input_wide.csv'.format(new_directory, ECONOMY_ID))
        non_road_model_input_wide = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_non_road_model_input_wide.csv'.format(new_directory, ECONOMY_ID))
    #reformat:
    #first make them tall
    road_model_input= road_model_input_wide.melt(id_vars=['Economy', 'Scenario', 'Date', 'Vehicle Type', 'Drive', 'Transport Type' , 'Medium'], var_name='Measure', value_name='Value')
    non_road = non_road_model_input_wide.melt(id_vars=['Economy', 'Scenario', 'Date', 'Vehicle Type', 'Drive', 'Transport Type' , 'Medium'], var_name='Measure', value_name='Value')
    
    #concat them
    new_transport_data_system_df = pd.concat([road_model_input, non_road])
    
    #set Unit and frequency and Data_available to na (this is jsut so we dont get errors later on, they arent important for this)
    new_transport_data_system_df['Unit'] = np.nan
    new_transport_data_system_df['Frequency'] = np.nan
    new_transport_data_system_df['Data_available'] = np.nan
    
    #keep only the outlook base uear
    new_transport_data_system_df = new_transport_data_system_df.loc[new_transport_data_system_df['Date']==config.OUTLOOK_BASE_YEAR]
    return new_transport_data_system_df

def load_and_check_alternate_sales_share_files(filepath, sales_shares, ECONOMY_ID):
    #double check it has all the same columns
    series = pd.read_csv(root_dir + '/' + 'input_data/alternate_sales_shares/{}/{}'.format(ECONOMY_ID, filepath))
    if not set(series.columns)==set(['Economy', 'Scenario', 'Date', 'Vehicle Type', 'Drive', 'Transport Type', 'Medium', 'Share']):
        breakpoint()
        raise ValueError('The file {} does not have the correct columns. Please check it has the following columns: Economy, Scenario, Date, Vehicle Type, Drive, Transport Type, Share'.format(filepath))
    #now check that the share is for the drive share. if not, raise an error
    #to do this, group by and sum up all shares for everything ecpt drive
    ones = series.groupby(['Economy', 'Scenario', 'Date','Medium', 'Vehicle Type', 'Transport Type']).sum().reset_index()
    #where any values are > 1, raise an error (we cannot assume they will add up to 1 because user probably forgot to include all drives, which is totally fine)
    EPSILON = 1e-9
    if len(ones.loc[ones.Share>1+EPSILON])>0:
        breakpoint()
        raise ValueError('The file {} has shares that sum to more than 1. Please check that they are the share of each drive for each vehicle type, not transport type'.format(filepath))
    
    #double check the same rows are not in sales share already. if so we need to remove one of these files from alternate_sales_share_filess. leave it to user.
    rows = series[['Economy', 'Scenario', 'Date', 'Vehicle Type','Medium', 'Drive', 'Transport Type']].drop_duplicates()
    if len(sales_shares)>0:
        if len(sales_shares.merge(rows, how='inner', on=['Economy', 'Scenario', 'Date', 'Vehicle Type','Medium', 'Drive', 'Transport Type']))>0:
            breakpoint()
            raise ValueError('The file {} has rows that are already in the sales share. Please remove these rows from the sales share or remove the file from alternate_sales_share_files'.format(filepath)) 
    
    full_filepath = 'input_data/alternate_sales_shares/{}/{}'.format(ECONOMY_ID, filepath)

    return series, full_filepath


def incorporate_alternate_sales_shares(ECONOMY_ID):
    """
    Incorporates alternate sales shares from a given Excel file. These have to be the drive share for each vehicle type, or the function will throw an error. 
    
    These files will probably come from the transport data system, and fro example, be generated using projected sales shares from other organisations, eg. the EIA.
    
    The Excel file should have the following columns: Economy, Scenario, Date, Vehicle Type, Drive, Transport Type, Share, Unit, Frequency, Data_available.
    
    It is not expected that there will be these files availble for all economies not even for all vehile types. Where they arent available, teh data from vehicle_sales_share_inputs.xlsx will be used instead.
    
    Args:
        filepath (str): Path to the Excel file containing sales shares data.
        additional_params: Additional parameters needed for processing.

    Returns:
        DataFrame: A DataFrame with incorporated sales shares.
    """
    #if there is no folder for this economy, create one (eventualy they will all have one)
    if not os.path.exists(root_dir + '/' + 'input_data/alternate_sales_shares/{}/'.format(ECONOMY_ID)):
        os.makedirs('input_data/alternate_sales_shares/{}/'.format(ECONOMY_ID))
        filepaths=[]
    else:
        filepaths = [file for file in os.listdir('input_data/alternate_sales_shares/{}/'.format(ECONOMY_ID)) if file.endswith('.csv')]
    
    #load in the data that is available. to prevent issues with versioning we will only use the files that are specified in parameters.yml. They also need to be csvs!
    economy_files = yaml.load(open(root_dir + '/' + 'config/parameters.yml'), Loader=yaml.FullLoader)['alternate_sales_share_files']
    if ECONOMY_ID in economy_files.keys():
        economy_files = economy_files[ECONOMY_ID]
    else:
        economy_files = []
    #filter for the files that are in the economy_files list
    filepaths = [filepath for filepath in filepaths if filepath.split('\\')[-1] in economy_files]#TODO check me
    #now load in the data
    sales_shares = pd.DataFrame()
    full_filepaths = []
    for filepath in filepaths:
        new_sales_shares, full_filepath = load_and_check_alternate_sales_share_files(filepath, sales_shares, ECONOMY_ID)
        sales_shares = pd.concat([sales_shares, new_sales_shares])
        full_filepaths.append(full_filepath)

    return sales_shares, full_filepaths

def incorporate_manually_specified_sales_shares(ECONOMY_ID, passenger_drive_shares, freight_drive_shares):
    """
    Incorporates manually specified sales shares from vehicle_sales_share_inputs.xlsx. 
    """
    #were getting no values fro Drive_share for <=CURRENT_BASE_YEAR
    ##########################################################################################################################################
    #BEGIN INCORPORATING USER INPUTTED SALES SHARES
    ##########################################################################################################################################
    
    # #for this we will perfrom the hcanges on passenger and freight separately. So here we will separate them and then combine them at the end
    # new_sales_shares_passenger_0 = new_sales_shares_sum[new_sales_shares_sum['Transport Type']=='passenger']
    # new_sales_shares_freight_0 = new_sales_shares_sum[new_sales_shares_sum['Transport Type']=='freight']

    #CHANGE ALL PHEVD AND PHEVG TO PHEV. FOR NOW THIS IS NEEDED AS WE ARE CONVERTING PHEV TO G OR D IN DEMAND MIXING

    #for all values we wil interpolate between them with a spline. To set values we will just set the value for the year we want to the value we want, then interpolate between the values we have set and the values in 2017, 2018, 2019. At the end of this we will also normalise all values by vehicle type to sum to 1. Then we will apply growth rates to define how much of each vehicle type we see growth in compared to the others for that transport type
    # #join regions to new_sales_shares_sum_0
    # new_sales_shares_passenger_0 = pd.merge(new_sales_shares_passenger_0, regions_passenger, how='left', on='Economy')
    # new_sales_shares_freight_0 = pd.merge(new_sales_shares_freight_0, regions_freight, how='left', on='Economy')

    def df_to_nested_dict(df):
        outer_dict = {}
        for i, row in df.iterrows():
            scenario_dict = outer_dict.setdefault(row['Scenario'], {})
            inner_dict = scenario_dict.setdefault(row['Economy'], {})
            medium_dict = inner_dict.setdefault(row['Medium'], {})
            vehicle_dict = medium_dict.setdefault(row['Vehicle Type'], {})
            if row['Drive'] in vehicle_dict:
                vehicle_dict[row['Drive']].append((row['Share'], row['Date']))
            else:
                vehicle_dict[row['Drive']] = [(row['Share'], row['Date'])]
        return outer_dict

    
    drive_shares_passenger_dict = df_to_nested_dict(passenger_drive_shares)
    drive_shares_freight_dict = df_to_nested_dict(freight_drive_shares)


    def create_drive_shares_df(df, drive_shares_dict):
        for scenario, economy in drive_shares_dict.items():
            for economy, mediums in economy.items():
                for mediums, veh_types in mediums.items():
                    for veh_type, drives in veh_types.items():
                        for drive, shares in drives.items():
                            for share in shares:
                                year = share[1]
                                share_ = share[0]
                                df.loc[(df['Economy'] == economy) & (df['Vehicle Type'] == veh_type) & (df['Drive'] == drive) & (df['Date'] == year) & (df['Scenario'] == scenario)& (df['Medium'] == mediums), 'Share'] = share_
        return df

    #using the drive shares we laoded in, create a df with which to set the drive shares
    passenger_drive_shares = create_drive_shares_df(passenger_drive_shares, drive_shares_passenger_dict) 
    freight_drive_shares = create_drive_shares_df(freight_drive_shares, drive_shares_freight_dict)
    
    return passenger_drive_shares, freight_drive_shares

def check_manually_specified_vehicle_type_sales_shares(ECONOMY_ID, vehicle_type_growth_regions, vehicle_type_growth):
    user_input_creation_functions.check_region(vehicle_type_growth_regions, vehicle_type_growth)
    vehicle_type_growth = pd.merge(vehicle_type_growth, vehicle_type_growth_regions, how='left', on='Region')
    vehicle_type_growth = vehicle_type_growth.loc[vehicle_type_growth['Economy']==ECONOMY_ID].drop(columns=['Region'])
    return vehicle_type_growth

def check_and_format_manually_specified_sales_shares(ECONOMY_ID):
    """
    ######################################
    #TESTING
    #check the regions in regions_passenger and regions_freight are the same as in passenger_drive_shares and freight_drive_shares, also check that the regions in vehicle_type_growth_regions are the same as in vehicle_type_growth
    
    also check that the sum of shares for any vehicle type transport type combination dont exceed 1
    """
    
    passenger_drive_shares = pd.read_excel(root_dir + '/' + 'input_data/vehicle_sales_share_inputs.xlsx',sheet_name='passenger_drive_shares').drop(columns=['Comment'])
    freight_drive_shares = pd.read_excel(root_dir + '/' + 'input_data/vehicle_sales_share_inputs.xlsx',sheet_name='freight_drive_shares').drop(columns=['Comment'])    
    
    #CHECK AND MAP REGIONS TO ECONOMIES:
    regions_passenger = pd.read_excel(root_dir + '/' + 'input_data/vehicle_sales_share_inputs.xlsx',sheet_name='regions_passenger')
    regions_freight = pd.read_excel(root_dir + '/' + 'input_data/vehicle_sales_share_inputs.xlsx',sheet_name='regions_freight')    
    user_input_creation_functions.check_region(regions_passenger, passenger_drive_shares)
    user_input_creation_functions.check_region(regions_freight, freight_drive_shares)
    #join regions
    passenger_drive_shares = pd.merge(passenger_drive_shares, regions_passenger, how='left', on='Region')
    freight_drive_shares = pd.merge(freight_drive_shares, regions_freight, how='left', on='Region')
    #extract only the economy we want and drop the region col
    passenger_drive_shares = passenger_drive_shares.loc[passenger_drive_shares['Economy']==ECONOMY_ID].drop(columns=['Region'])
    freight_drive_shares = freight_drive_shares.loc[freight_drive_shares['Economy']==ECONOMY_ID].drop(columns=['Region'])
    
    #add transport type cols
    passenger_drive_shares['Transport Type'] = 'passenger'
    freight_drive_shares['Transport Type'] = 'freight'
    
    #FORMAT DATA: MELT AND DROP PLACEHOLDER VALUES
    passenger_drive_shares = passenger_drive_shares.melt(id_vars=['Economy', 'Medium','Vehicle Type', 'Drive', 'Date', 'Transport Type'],var_name='Scenario', value_name='Share')
    freight_drive_shares = freight_drive_shares.melt(id_vars=['Economy', 'Medium','Vehicle Type', 'Drive', 'Date', 'Transport Type'],var_name='Scenario', value_name='Share')
    
    #drop any rows with 'Will make up the rest' in the Drive_share col. These are just pllaceholders to let the user know they can ignore that row
    passenger_drive_shares = passenger_drive_shares.loc[passenger_drive_shares['Share']!='Will make up the rest']
    freight_drive_shares = freight_drive_shares.loc[freight_drive_shares['Share']!='Will make up the rest']
    
    # DOUBLE CHECK THAT THE SUM OF DRIVE SHARES FOR EACH DRIVE/TRANSPORT TYPE SUMS TO < 1
    passenger_drive_shares_ones = passenger_drive_shares.groupby(['Economy', 'Scenario', 'Date', 'Vehicle Type', 'Medium', 'Transport Type']).sum().reset_index()
    freight_drive_shares_ones = freight_drive_shares.groupby(['Economy', 'Scenario', 'Date', 'Vehicle Type', 'Medium', 'Transport Type']).sum().reset_index()
    greater_than_1 = pd.concat([passenger_drive_shares_ones.loc[passenger_drive_shares_ones['Share']>1], freight_drive_shares_ones.loc[freight_drive_shares_ones['Share']>1]])
    if len(greater_than_1)>0:
        breakpoint()
        raise ValueError('The sum of the drive shares for each drive/transport type combination should not exceed 1. Please check the following rows: {}'.format(greater_than_1))
    return passenger_drive_shares, freight_drive_shares

def merge_manually_specified_with_alternate_and_early_year_sales_shares(ECONOMY_ID, passenger_drive_shares, freight_drive_shares, alternate_sales_shares, new_sales_shares_sum):
    """
    Where there are alternate_sales_shares specified sales shares, we want to replace the sales shares from manually with these. 
    
    Then we want to use new_sales_shares_sum values instead of any, since those are our estimates for current slaes shares.

    Args:
        ECONOMY_ID (_type_): _description_
        passenger_drive_shares, freight_drive_shares (_type_): _description_
        alternate_sales_shares (_type_): _description_
    """
    # #label the manully specified sales shares as 'manually_specified'
    # passenger_drive_shares['Source'] = 'manually_specified'
    # freight_drive_shares['Source'] = 'manually_specified'
    # alternate_sales_shares['Source'] = 'alternate_sales_shares'
    #now merge the manually specified sales shares with the alternate sales shares
    passenger_drive_shares['Transport Type'] = 'passenger'
    freight_drive_shares['Transport Type'] = 'freight'
    #concat freight_drive_shares amnd passenger_drive_shares
    manually_inputted_drive_shares = pd.concat([passenger_drive_shares, freight_drive_shares])
    if len(alternate_sales_shares)>0:
        #merge with alternate_sales_shares
        all_sales_shares = pd.merge(alternate_sales_shares, manually_inputted_drive_shares, how='outer', on=['Economy', 'Scenario', 'Date', 'Vehicle Type', 'Drive', 'Transport Type', 'Medium'], indicator=True)
        
        #where _merge is both or left only we want to keep the alternate sales shares. do this by setting sales_share to value_x 
        all_sales_shares.loc[(all_sales_shares['_merge']=='both')|(all_sales_shares['_merge']=='left_only'), 'Share'] = all_sales_shares['Share_x']
        #where _merge is right only we want to keep the manually specified sales shares. do this by setting sales_share to value_y
        all_sales_shares.loc[all_sales_shares['_merge']=='right_only', 'Share'] = all_sales_shares['Share_y'].astype(all_sales_shares['Share'].dtype)
        #drop _merge and Share cols
        all_sales_shares = all_sales_shares.drop(columns=['_merge', 'Share_x', 'Share_y'])
        
    else:
        all_sales_shares = manually_inputted_drive_shares.copy()
    
    
    all_sales_shares['road'] = all_sales_shares['Medium']=='road'
    
    #now join with new_sales_shares_sum: (note that currently share is called drive_share in new_sales_shares_sum)
    all_sales_shares = all_sales_shares.merge(new_sales_shares_sum, how='outer', on=['Economy', 'Scenario', 'Date', 'Vehicle Type', 'Drive', 'Transport Type', 'Medium', 'road'], indicator=True)
    
    all_sales_shares.loc[~all_sales_shares['Drive_share'].isna(), 'Share'] = all_sales_shares['Drive_share']
    
    #check for any left_onlys in all_sales_shares. This would be where we are missing rows in what we thought was a complete df. Normally we should be ok with these but its a good checkpoint for bug checking/testing
    lefts = all_sales_shares.loc[all_sales_shares['_merge']=='left_only']
    if len(lefts)>0:
        # breakpoint()
        pass
        #  print('theres some values from the inputted sales shares we arent expecting: {}'.format(lefts))
    
    #remove lefts:
    all_sales_shares = all_sales_shares.loc[all_sales_shares['_merge']!='left_only']
    #drop merge and drive share cols
    all_sales_shares.drop(columns=['_merge', 'Drive_share'], inplace=True)
    
    return all_sales_shares

def clean_and_format_sales_shares_before_calcualtions(ECONOMY_ID, sales_shares, CURRENT_BASE_YEAR):
    """Just do some clean up before we start calcualting sales shares. THis will iclude filling in missing dates values with nas, filling in missing drives with nas. and lastly some double checking to make sure we have all the data we need and its in the right format, adds up to 1 etc.

    Args:
        ECONOMY_ID (_type_): _description_
        sales_shares (_type_): _description_
    """
    #check the slaes shares against the concordance file, and if any rows are missing let the user know. however if it is jsut a drive missing, we will fill this in with 0 and let the user know. To do this we will  check for missing rows when we ignore the drive annd date cols.

    #now doulbe check we have the required categories that are in the concordances
    model_concordances_user_input_and_growth_rates = pd.read_csv(root_dir + '/' + 'intermediate_data/computer_generated_concordances/{}'.format(config.model_concordances_user_input_and_growth_rates_file_name))
    #filter for ECONOMY_ID
    model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates.loc[model_concordances_user_input_and_growth_rates['Economy']==ECONOMY_ID]
    #drop all measures that are not vehicle sales share
    model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates[model_concordances_user_input_and_growth_rates['Measure']=='Vehicle_sales_share']
    #drop any cols not in the sales_shares
    cols = [col for col in model_concordances_user_input_and_growth_rates.columns if col in sales_shares.columns]
    model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates[cols]
    model_concordances_user_input_and_growth_rates.drop_duplicates(inplace=True)
    # new_INDEX_COLS = [col for col in config.INDEX_COLS if col in model_concordances_user_input_and_growth_rates.columns]

    #in case its not there, add BASE YEAR to the concordances which canb be a copy of the CURRENT_BASE_YEAR +1
    if CURRENT_BASE_YEAR not in model_concordances_user_input_and_growth_rates['Date'].unique():
        model_concordances_user_input_and_growth_rates_base = model_concordances_user_input_and_growth_rates.loc[model_concordances_user_input_and_growth_rates['Date']==CURRENT_BASE_YEAR+1].copy()
        model_concordances_user_input_and_growth_rates_base['Date'] = CURRENT_BASE_YEAR
        model_concordances_user_input_and_growth_rates = pd.concat([model_concordances_user_input_and_growth_rates,model_concordances_user_input_and_growth_rates_base])

    ############TEST WE HAVE EVERY ROW, WITH NO DRIVE (and date) COL########
    #we will merge and check for where we have rows in the concordance that are not in the sales shares. If so, tell user. otehrwise, consider this check passed.
    #drop drive and date col from both
    no_drive_concordance = model_concordances_user_input_and_growth_rates.drop(columns=['Drive', 'Date']).drop_duplicates()
    no_drive_sales_shares = sales_shares.drop(columns=['Drive', 'Date']).drop_duplicates()
    #now merge the two
    merged = pd.merge(no_drive_concordance, no_drive_sales_shares, how='outer', on=[col for col in config.INDEX_COLS if col in no_drive_concordance.columns], indicator=True)
    if len(merged.loc[merged['_merge']=='left_only'])>0:
        left = merged.loc[merged['_merge']=='left_only']
        breakpoint()
        raise ValueError('The sales shares are missing the following rows: {}'.format(left))
    ############INCLUDE ALL MISSING DATES FOR EVERY YEAR IN THE SALES SHARES########
    #merge the sales shares with concordance on every col. where there is a row in the concordance that is not in the sales shares, add it to the sales shares with a nan value for the sales share
    merged_df = pd.merge(model_concordances_user_input_and_growth_rates, sales_shares, how='outer', on=[col for col in config.INDEX_COLS if col in model_concordances_user_input_and_growth_rates.columns], indicator=True)
    missing = merged_df.loc[merged_df['_merge']=='left_only']
    #also need to add road col to missing
    missing['road'] = missing['Medium']=='road'
    missing.drop(columns=['_merge'], inplace=True)
    missing['Share'] = np.nan
    #add missing rows to sales shares
    sales_shares = pd.concat([sales_shares, missing])
    
    #rename Share to Drive_share
    sales_shares.rename(columns={'Share':'Drive_share'}, inplace=True)
    
    # #check years are the same between the two
    # missing = set(model_concordances_user_input_and_growth_rates['Date'].unique())-set(sales_shares['Date'].unique())
    # if len(missing)>0:
    #     breakpoint()
    #     raise ValueError('The years in the sales shares are not the same as the years in the concordance. Please check the years in the sales shares are the same as the years in the concordance: {}'.format(missing))

    return sales_shares

def fill_missing_drives_using_median_of_early_years(ECONOMY_ID, sales_shares, model_concordances_user_input_and_growth_rates, CURRENT_BASE_YEAR,USE_LARGE_EPSILON=False):
    #Sometimes our sales shares inputs dont contain all drives. This occurs because it takes to long manually write out the drive share targets for every drive. 
    
    # The follwoign funciton should take in the targets and the interpoaltions between targets we do have and calcualte the remaining drive shares for the missing drives using the median of the early years data's shares as a reference (early years being from the CURRENT_BASE_YEAR to the config.OUTLOOK_BASE_YEAR). 
    
    #the medians of the early year datas shares, for the missing drives, will be normalised to 1 so we can just times them by 1-x where x is the sum of the shares we do have, in each year we have them for.
    
    #The input files for this will be:
    #sales_shares 
    #model_concordances_user_input_and_growth_rates (which contaions the set of drives, vehicle types and transport types we need to set the drive shares for)
    
    #so first we need to split sales_shares into the early year data    
    sales_share_early_years = sales_shares.loc[sales_shares['Date']<=CURRENT_BASE_YEAR]
    
    #now, first check for any missing rows to sales_share_early_years. We can set them to 0 but to be safer we will throw an error if this is the case (currtently its expecte this should be done by an earlier fucntion). we will use the concoirdance file to do this
    missing_rows = model_concordances_user_input_and_growth_rates.loc[~model_concordances_user_input_and_growth_rates[['Transport Type', 'Medium','Vehicle Type', 'Drive']].apply(tuple,1).isin(sales_share_early_years[['Transport Type','Medium','Vehicle Type', 'Drive']].apply(tuple,1))][['Transport Type', 'Medium','Vehicle Type', 'Drive']].drop_duplicates()
    if len(missing_rows)>0:
        breakpoint()
        raise ValueError('The sales shares are missing the following rows: {}'.format(missing_rows))
        # missing_rows['Drive_share'] = 0
        # sales_share_early_years = pd.concat([sales_share_early_years, missing_rows])
    sales_share_early_years = sales_share_early_years.dropna(subset=['Drive_share'])
    #median the sales shares for each drive for each vehicle type (in the process remove the date col)
    sales_share_early_years = sales_share_early_years.groupby(['Economy', 'Scenario', 'Transport Type','Medium','road', 'Vehicle Type', 'Drive'])['Drive_share'].median().reset_index()
    
    #find unique combiantions outside of the early years data where drive share isnt na. these are essentially rows we have projections for, so we dont want to overwrite any missing values with 0 or the median of early years (as we will be interpolating them)
    unique_rows_in_projection = sales_shares.loc[(sales_shares['Date']>CURRENT_BASE_YEAR)&(sales_shares['Drive_share'].notna())][['Scenario','Medium','Transport Type','road', 'Vehicle Type', 'Drive']].drop_duplicates()
    
    #drop those combinations in unique_rows_in_projection from sales_share_early_years.
    sales_share_early_years = sales_share_early_years[~sales_share_early_years[['Scenario','Transport Type', 'Medium','Vehicle Type','road', 'Drive']].apply(tuple,1).isin(unique_rows_in_projection[['Scenario','Transport Type', 'Medium','Vehicle Type','road', 'Drive']].apply(tuple,1))]
        
    #set nas in drive share to 0, just in case any are na (shoudlnt happen but lets be safe and quick here)
    sales_share_early_years[ 'Drive_share'] = sales_share_early_years[ 'Drive_share'].fillna(0)
    #find the normalised shares of these shares (this will be timesed by drive_share_remainder)
    sales_share_early_years['Drive_share'] = sales_share_early_years.groupby(['Economy', 'Scenario', 'Transport Type', 'road','Medium','Vehicle Type'])['Drive_share'].transform(lambda x: x/x.sum())
    
    #now get sum of shares for each year in all years in the original dataframe 
    sales_shares_sum = sales_shares.groupby(['Economy', 'Scenario', 'Transport Type','Medium','road', 'Vehicle Type', 'Date'])['Drive_share'].sum().reset_index()
    #1 minus it
    sales_shares_sum['Drive_share_remainder'] = 1 - sales_shares_sum['Drive_share']
    #chcke for any Drive_share_remainder values les than -0.1. absolutely should not be any. if there are neghative values but they arent > 0.1 then just set any negative values to 0
    EPSILON = 1e-1
    if USE_LARGE_EPSILON:
        EPSILON = 1
    if sales_shares_sum['Drive_share_remainder'].min() < -EPSILON:
        #show them and raise
        print(sales_shares_sum.loc[sales_shares_sum['Drive_share_remainder']<0])
        breakpoint()
        raise ValueError('Drive share remainder is less than 0. Often this is because sales shares are left above 0 rather than set to 0 in the manually specified sales shares. Please check the sales shares are set to 0 where you want them to be 0.')
    else:
        #set any values less than 0 to 0
        sales_shares_sum.loc[sales_shares_sum['Drive_share_remainder']<0, 'Drive_share_remainder'] = 0
    
    #drop drive share
    sales_shares_sum = sales_shares_sum.drop(columns=['Drive_share'])
    #join this to the base year data using right join, ignoring date
    missing_sales_shares = sales_share_early_years[['Economy', 'Scenario', 'Transport Type','Medium', 'Vehicle Type','Drive', 'road','Drive_share']].merge(sales_shares_sum, on=['Economy','road', 'Scenario', 'Medium','Transport Type', 'Vehicle Type'], how='right')
    #times the early year data by the 1-x to get the sahre for each missing drive
    missing_sales_shares['Drive_share'] = missing_sales_shares['Drive_share'] * missing_sales_shares['Drive_share_remainder']

    #now we need to insert these rows into the sales_shares, rmeoving their original rows (which will be nas.) so do a join and then repalce drive share with the new drive share where it is not na
    final_df = sales_shares.merge(missing_sales_shares, on=['Economy', 'Scenario','Medium', 'Transport Type','road', 'Vehicle Type','Date', 'Drive'], how='left', suffixes=('', '_y'))
    #want to replace the drive share with the new drive share where it is na (replacing nas with nas too.)
    final_df['Drive_share'] = final_df['Drive_share'].fillna(final_df['Drive_share_y'])
    #drop the y cols
    final_df = final_df.drop(columns=['Drive_share_y', 'Drive_share_remainder'])
    #save the values at this point in time to use in the future if we need
    final_df.to_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_new_sales_shares_concat_interp.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
    return final_df

    
def check_for_series_with_too_few_values_to_interpolate(sales_shares, CURRENT_BASE_YEAR, min_points_required=2, PADDED_YEARS=2, PAD_DATA_IF_LESS_THAN_MIN_POINTS=False):
    """
    Analyzes a DataFrame to identify and handle groups with insufficient data points for interpolation.

    This function first identifies groups within the data that have fewer than a specified minimum number of non-NaN 'Drive_share' values. It then flags groups with no data points and optionally pads forward the data for groups with insufficient but non-zero data points.

    Args:
        sales_shares (pd.DataFrame): A DataFrame containing sales shares data.
        CURRENT_BASE_YEAR (int): The current base year for the analysis.
        min_points_required (int, optional): The minimum number of data points required for a group to be considered sufficient for interpolation. Default is 4.
        PADDED_YEARS (int, optional): The number of years to pad forward the data if a group has fewer than the required minimum points but more than zero. Default is 2.
        PAD_DATA_IF_LESS_THAN_MIN_POINTS (bool, optional): Flag to determine whether to pad data forward for groups with insufficient data points. Default is False.

    Returns:
        pd.DataFrame: The modified DataFrame with flags for interpolation and padded data where applicable.

    The function returns a DataFrame with an additional 'INTERPOLATE' column indicating whether each group should be interpolated. For groups with insufficient data points, the function can pad forward the base year data for a specified number of years or set these data points to zero.
    """
    #firstly filter for data that is greater or equal to CURRENT_BASE_YEAR
    sales_shares_earlier_than_base_year = sales_shares[sales_shares.Date<CURRENT_BASE_YEAR]
    sales_shares = sales_shares[sales_shares.Date>=CURRENT_BASE_YEAR]
    ##################
    DO_THIS = False
    if DO_THIS:
        #then where we have sums that add up to 1 or more in Drive_share, then set all other values in the same 'Economy', 'Scenario', 'Medium', 'road', 'Transport Type', 'Vehicle Type' grouping  to 0, unless they aare already something non0 or nonna. This helps to reduce the amount of values we will set as having too few values to inrterpolate, since we can assume some their values.
        #first add up all vlaues by 'Economy', 'Scenario', 'Medium', 'road', 'Transport Type', 'Vehicle Type' and then lable all rows where this adds up to >=1. Then for these rows, where the value is na, set it to 0:
        sales_shares_sums = sales_shares.groupby(['Economy', 'Scenario', 'Medium', 'road', 'Transport Type', 'Vehicle Type', 'Date']).sum().reset_index()
        sales_shares_sums['flag'] = sales_shares_sums['Drive_share'].apply(lambda x: 1 if x>=1 else 0)
        sales_shares = sales_shares.merge(sales_shares_sums, on=['Economy', 'Scenario', 'Medium', 'road', 'Transport Type', 'Vehicle Type', 'Date'], how='left', suffixes=('', '_y'))
        sales_shares['Drive_share'] = np.where((sales_shares['flag']==1)&(sales_shares['Drive_share'].isna()), 0, sales_shares['Drive_share'])
        sales_shares.drop(columns=['flag']+[col for col in sales_shares.columns if col.endswith('_y')], inplace=True)
    ##################
    # Drop NaN in 'Drive_share' and count the non-NaN entries
    count_series = sales_shares.dropna(subset=['Drive_share']).groupby(['Economy', 'Scenario', 'Medium', 'road', 'Transport Type', 'Vehicle Type', 'Drive']).size().reset_index(name='Count')

    # Identify groups with very few data points and 1 or 0 data points using .loc
    insufficient_data = count_series.loc[(count_series['Count'] > 1) & (count_series['Count'] <= min_points_required)]
    no_data = count_series.loc[count_series['Count'] <= 1]

    # Merge to flag groups with no data
    merged_data = sales_shares.merge(no_data, on=['Economy', 'Scenario', 'Medium', 'road', 'Transport Type', 'Vehicle Type', 'Drive'], how='left', indicator=True)
    merged_data['INTERPOLATE'] = ~(merged_data['_merge'] == 'both')
    merged_data.drop(columns=['Count', '_merge'], inplace=True)

    ##################
    # Pad data for groups with insufficient data points and set to 0 if required
    if PAD_DATA_IF_LESS_THAN_MIN_POINTS and len(insufficient_data) > 0:
        # Merge to flag groups with insufficient data
        insufficient_merged_data = merged_data.merge(insufficient_data, on=['Economy', 'Scenario', 'Medium', 'road', 'Transport Type', 'Vehicle Type', 'Drive'], how='left', indicator='insufficient_data_flag')
        
        # Handling groups with insufficient data
        insufficient_mask = insufficient_merged_data['insufficient_data_flag'] == 'both'

        # Grab data for year == CURRENT_BASE_YEAR. We will pad these forwards by PADDED_YEARS, unless they are na, if so set them to 0 and dont pad
        base_year_data = insufficient_merged_data[insufficient_mask & (insufficient_merged_data['Date'] == CURRENT_BASE_YEAR)].copy()
        
        #deal with nas
        base_year_nas = base_year_data[base_year_data.Drive_share.isna()].copy()
        base_year_nas['Drive_share'] = 0
        insufficient_merged_data = pd.concat([insufficient_merged_data, base_year_nas])
        base_year_data = base_year_data[~base_year_data.Drive_share.isna()].copy()
        
        # Creating padded data for forward years
        for year in range(1, PADDED_YEARS + 1):
            padded_data = base_year_data.copy()
            padded_data['Date'] = CURRENT_BASE_YEAR + year
            insufficient_merged_data = pd.concat([insufficient_merged_data, padded_data])

        # Reset the index after concatenation
        insufficient_merged_data.reset_index(drop=True, inplace=True)

        # Drop the 'insufficient_data_flag' column
        insufficient_merged_data.drop(columns=['insufficient_data_flag'], inplace=True)

        #add insufficient data to merged_data:
        merged_data = pd.concat([insufficient_merged_data, merged_data])
    
    #lastly attach the sales_shares_earlier_than_base_year with INTERPOLATE set to true
    sales_shares_earlier_than_base_year['INTERPOLATE'] = True
    merged_data = pd.concat([sales_shares_earlier_than_base_year, merged_data])
    return merged_data

def interpolate_missing_sales_shares(sales_shares, ECONOMY_ID, interpolation_method='linear'):
    """
    Interpolates missing sales shares in the sales_shares

    Args:
        merged_sales_sharesdata (DataFrame): The DataFrame containing merged sales share data.
        min_points_required (int): Minimum number of data points required for reliable interpolation.
        interpolation_method (str, optional): The method used for interpolation. Defaults to 'linear'.

    Returns:
        DataFrame: A DataFrame with missing sales shares interpolated.
    """
    
    ################################################################################
    # INTERPOLATE BETWEEN SALES SHARES
    ################################################################################
    #NOW DO INTERPOLATION
    #check for duplicates on the cols we will group by
    new_sales_shares_concat_interp_dupes = sales_shares[sales_shares.duplicated(subset=['Economy', 'Scenario', 'Date', 'Transport Type','Medium','road', 'Vehicle Type', 'Drive'], keep=False)]
    if len(new_sales_shares_concat_interp_dupes) > 0:
        breakpoint()
        raise Exception(f'ERROR: DUPLICATES IN NEW SALES SHARES CONCAT INTERP {new_sales_shares_concat_interp_dupes}')
    
    #order data by year
    new_sales_shares_concat_interp = sales_shares.sort_values(by=['Economy', 'Scenario', 'Date','road', 'Transport Type', 'Medium','Vehicle Type', 'Drive']).copy()
    
    new_sales_shares_concat_interp['Drive_share'] = new_sales_shares_concat_interp['Drive_share'].astype(float)#sometimes this needs to be set to float for some reason, otherwise the ouput will jsut be same as input
    
    #drop any where INTERPOLATE is False
    new_sales_shares_concat_no_interp = new_sales_shares_concat_interp.loc[~new_sales_shares_concat_interp.INTERPOLATE]
    new_sales_shares_concat_interp = new_sales_shares_concat_interp.loc[new_sales_shares_concat_interp.INTERPOLATE]
    
    #reset index before interp.
    new_sales_shares_concat_interp = new_sales_shares_concat_interp.reset_index(drop=True)
    
    if X_ORDER == 'linear':
        # breakpoint()
        #do interpolation using spline and order = X
        new_sales_shares_concat_interp['Drive_share'] = new_sales_shares_concat_interp.groupby(['Economy', 'Scenario', 'Transport Type','Medium','road', 'Vehicle Type', 'Drive'], group_keys=False)['Drive_share'].apply(lambda group: group.interpolate(method='linear', limit_area='inside'))
    else:
        #do interpolation using spline and order = X
        new_sales_shares_concat_interp['Drive_share'] = new_sales_shares_concat_interp.groupby(['Economy', 'Scenario', 'Transport Type', 'Medium','road','Vehicle Type', 'Drive'], group_keys=False)['Drive_share'].apply(lambda group: group.interpolate(method='spline', order=X_ORDER, limit_area='inside'))        
        
    #cocnat new_sales_shares_concat_no_interp back on
    new_sales_shares_concat_interp = pd.concat([new_sales_shares_concat_interp, new_sales_shares_concat_no_interp])
    #reset indx
    new_sales_shares_concat_interp = new_sales_shares_concat_interp.reset_index(drop=True)
    # breakpoint()
    #drop INTERPOLATE
    new_sales_shares_concat_interp.drop(columns=['INTERPOLATE'], inplace=True)
    
    return new_sales_shares_concat_interp

def normalize_drive_shares(new_sales_shares, new_sales_shares_sum_original):
    """
    Normalizes drive shares by vehicle type and calculates the share of each vehicle type within its specific transport type.

    Args:
        new_sales_shares (DataFrame): The DataFrame containing drive shares and vehicle type data.
        new_sales_shares_sum_original (DataFrame): The DataFrame containing vehicle shares.

    Returns:
        DataFrame: A DataFrame with normalized drive shares.
    """
    # Normalize drive share by vehicle type
    group_columns = ['Economy', 'Scenario', 'road', 'Transport Type', 'Medium', 'Vehicle Type', 'Date']
    #replace nas with 0
    new_sales_shares['Drive_share'].fillna(0, inplace=True)
    new_sales_shares['Drive_sum'] = new_sales_shares.groupby(group_columns)['Drive_share'].transform('sum')
    new_sales_shares['Drive_share'] /= new_sales_shares['Drive_sum']

    # Forward fill the vehicle type share sum    
    vehicle_shares = new_sales_shares_sum_original.copy()
    vehicle_shares.sort_values(by=group_columns + ['Drive'], inplace=True)
    vehicle_shares=vehicle_shares[group_columns + ['Drive','Vehicle_type_share_sum']] 
    ffill_transform = lambda group: group.ffill().fillna(0)
    vehicle_shares['Vehicle_type_share_sum'] = vehicle_shares.groupby(['Economy', 'Scenario', 'Transport Type', 'Medium', 'road', 'Vehicle Type'])['Vehicle_type_share_sum'].transform(ffill_transform)

    # Merge and calculate the final transport type share
    merged_data = new_sales_shares.merge(vehicle_shares, on=group_columns + ['Drive'], how='left')
    merged_data['Transport_type_share'] = merged_data['Vehicle_type_share_sum'] * merged_data['Drive_share']
    merged_data['Transport_type_share'].fillna(0, inplace=True)

    return merged_data


def apply_vehicle_type_growth_rates(new_sales_shares_all):
    """
    Applies vehicle type growth rates to sales shares to find the sales share within each transport type.

    Args:
        data (DataFrame): The DataFrame containing sales share data.
        growth_rate_filepath (str): Path to the Excel file containing vehicle type growth rates.

    Returns:
        DataFrame: Updated DataFrame with applied growth rates.
    """
    
    ################################################################################################################################################################
    #APPLY VEHICLE TYPE GROWTH RATES TO SALES SHARES TO FIND SALES SHARE WITHIN EACH TRANSPORT TYPE
    ################################################################################################################################################################    
    #now apply vehicle_type_growth. 
    # first calcualte teh compound gorwth rate from the xlsx sheet=vehicle_type_growth, (it should be the growth rate . cumprod()) 
    # times that by each Transport_type_share to adjust them for the growth rate
    #then normalise all to 1 by transport type
    vehicle_type_growth_regions = pd.read_excel(root_dir + '/' + 'input_data/vehicle_sales_share_inputs.xlsx', sheet_name='vehicle_type_growth_regions')
    vehicle_type_growth = pd.read_excel(root_dir + '/' + 'input_data/vehicle_sales_share_inputs.xlsx', sheet_name='vehicle_type_growth').drop_duplicates().drop(columns=['Comment'])
    vehicle_type_growth['road'] = vehicle_type_growth['Medium']=='road'
    new_sales_shares_all_new= new_sales_shares_all.copy()
    #use vehicle_type_growth_regions to merge regions to econmy
    new_sales_shares_all_new = new_sales_shares_all_new.merge(vehicle_type_growth_regions, on=['Economy'], how='left')
    #merge vehicle_type_growth to new_sales_shares_all_new
    new_sales_shares_all_new = new_sales_shares_all_new.merge(vehicle_type_growth, on=['Region', 'Scenario', 'Transport Type', 'Medium','road','Vehicle Type'], how='left')
    #cumprod the growth rate (Growth) when grouping by Economy, Scenario, Transport Type, Vehicle Type and drive # but first sort by date
    new_sales_shares_all_new = new_sales_shares_all_new.sort_values(by=['Economy', 'Scenario', 'Transport Type','Medium', 'Vehicle Type','road', 'Drive', 'Date'])
    new_sales_shares_all_new['Compound_growth_rate'] = new_sales_shares_all_new.groupby(['Economy', 'Scenario', 'Transport Type', 'Medium','Vehicle Type','road', 'Drive'])['Growth'].cumprod()
    #apply the growth rate to the Transport_type_share
    new_sales_shares_all_new['Transport_type_share_new'] = new_sales_shares_all_new['Transport_type_share'] * new_sales_shares_all_new['Compound_growth_rate']
    
    #normalise the Transport_type_share_new to 1
    new_sales_shares_all_new['Transport_type_share_new'] = new_sales_shares_all_new.groupby(['Economy', 'Scenario', 'Date','road','Transport Type'])['Transport_type_share_new'].transform(lambda x: x/x.sum())
    #reaplce any nas with 0. thjis is where the Transport_type_share_new was 0 for all in that transport type. 
    new_sales_shares_all_new.loc[new_sales_shares_all_new['Transport_type_share_new'].isna(), 'Transport_type_share_new'] = 0

    return new_sales_shares_all_new

def clean_and_run_final_checks_on_data(ECONOMY_ID, new_sales_shares_all_new):
    """
    Cleans the data and checks for issues such as missing values, duplicates, and anomalies.

    Args:
        data (DataFrame): The DataFrame to be cleaned and validated.

    Returns:
        DataFrame: Cleaned and validated DataFrame.
    """
    #check that the sum of transport type share is 1 for road=False, transport type = freight
    test = new_sales_shares_all_new.loc[(new_sales_shares_all_new['Economy']==ECONOMY_ID)&(new_sales_shares_all_new['road']==False)&(new_sales_shares_all_new['Transport Type']=='freight')&(new_sales_shares_all_new['Date']==2023)&(new_sales_shares_all_new['Scenario']=='Reference')].copy()            
    if abs(1-test.Transport_type_share_new.sum()) > 0.0001:
        if ECONOMY_ID in ['02_BD', '17_SGP', '06_HKC', '15_PHL', '16_RUS', '21_VN']:#i dont quite know why phl and hkc, rus are in here but cant do much about it, seems its casue of esto data not having freight non road energy.
            pass
        else:
            breakpoint()
            time.sleep(1)
            raise ValueError('The sum of the transport type share for {} road=False, transport type = freight, date = 2023 is not 1. Please check the user input data and fix this. Porbalby occuring for all econmoies and transport types'.format(ECONOMY_ID))

    #rename Transport_type_share_new to Vehicle^sales_share
    new_sales_shares_all_new = new_sales_shares_all_new.rename(columns={'Transport_type_share_new':'Vehicle_sales_share'})
    #drop cols
    new_sales_shares_all_new = new_sales_shares_all_new.drop(columns=[ 'Drive_share', 'Vehicle_type_share_sum', 'Drive_sum',
        'Transport_type_share', 'Region', 'Growth', 'Compound_growth_rate','road'])
    #identify if there anre any dupes. there shoudltn be and they should be fixed rather than removed.
    dupes = new_sales_shares_all_new[new_sales_shares_all_new.duplicated()]
    if len(dupes) > 0:
        breakpoint()
        time.sleep(1)
        raise ValueError(f'There are duplicates in the new_sales_shares_all_new df. Please fix this. {dupes}')

    #before saving data to user input spreadsheety we will do some formatting:
    #add cols for Unit,Medium,Data_available, frequency and Measure
    new_sales_shares_all_new['Unit'] = '%'
    new_sales_shares_all_new['Data_available'] = 'data_available'
    new_sales_shares_all_new['Measure'] = 'Vehicle_sales_share'
    new_sales_shares_all_new['Frequency'] = 'Yearly'
    #rename 'Vehicle_sales_share' to 'Value'
    new_sales_shares_all_new = new_sales_shares_all_new.rename(columns={'Vehicle_sales_share':'Value'})

    #final check before saving:
    a = new_sales_shares_all_new.loc[(new_sales_shares_all_new['Measure']=='Vehicle_sales_share') & (new_sales_shares_all_new['Transport Type']=='passenger') & (new_sales_shares_all_new['Date']==2023) & (new_sales_shares_all_new['Economy']==ECONOMY_ID) & (new_sales_shares_all_new['Scenario']=='Reference') & (new_sales_shares_all_new['Medium']=='road')].copy()
    if abs(a.Value.sum() - 1) > 0.0001: 
        breakpoint()
        time.sleep(1)
        raise ValueError(f'The sum of the vehicle sales share for passenger vehicles in 2023 is not 1, it is {a.Value.sum()}. Please check the user input data and fix this.')
    
    #lastly, as a quick fgix, see if all vlaues for 02_BD non road are na. if so, set them to 0. this is because bd doesnt ahve any non road transport! This seems like the easiest way to make sure they haev no sales but no errors also pop up related to it:
    if ECONOMY_ID == '02_BD':
        brunei_non_road = new_sales_shares_all_new.loc[(new_sales_shares_all_new['Economy']=='02_BD')&(new_sales_shares_all_new['Medium']!='road')].copy()
        if brunei_non_road.Value.isna().all():
            new_sales_shares_all_new.loc[(new_sales_shares_all_new['Economy']=='02_BD')&(new_sales_shares_all_new['Medium']!='road'), 'Value'] = 0
    #and for singapore, they ahve no freight, non road transport, so set these to 0:
    if ECONOMY_ID == '17_SGP':
        sing_non_road = new_sales_shares_all_new.loc[(new_sales_shares_all_new['Economy']=='17_SGP')&(new_sales_shares_all_new['Medium']!='road')&(new_sales_shares_all_new['Transport Type']=='freight')].copy()
        if sing_non_road.Value.isna().all():
            new_sales_shares_all_new.loc[(new_sales_shares_all_new['Economy']=='17_SGP')&(new_sales_shares_all_new['Medium']!='road')&(new_sales_shares_all_new['Transport Type']=='freight'), 'Value'] = 0
            
    ###########################################################################
 
    return new_sales_shares_all_new


#%%
# # # ECONOMY_ID,  RECALCULATE_SALES_SHARES_USING_RECALCULATED_INPUT_DATA, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR
# ECONOMY_ID = '15_PHL'
# a = vehicle_sales_share_creation_handler(ECONOMY_ID,  RECALCULATE_SALES_SHARES_USING_RECALCULATED_INPUT_DATA = True, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR = True, USE_LARGE_EPSILON=True)

# #%%
# ECONOMY_ID = '13_PNG'
# a = vehicle_sales_share_creation_handler(ECONOMY_ID,  RECALCULATE_SALES_SHARES_USING_RECALCULATED_INPUT_DATA = False, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR = True)#, USE_LARGE_EPSILON=True)
#%%


# #ecxtract usa sales shares and then save them to input_data/alternate_sales_shares/ECONOMY_ID for every economy for their reference case. Then it will be much easier (except dont do it for china since thats a diferent case)
# breakpoint()
# for economy in  config.economy_scenario_concordance['Economy'].unique().tolist():
#     if economy != '05_PRC' or economy != '06_HKC' or economy != '17_SGP':
    
#         create_alternate_sales_share_file(economy, sales_shares=None, vehicle_type=None, medium='road', drives=['fcev','bev', 'phev_d', 'phev_g'], transport_type=None, scenario=None, filepath=None, LOAD_LATEST_SALES_SHARES=True, secondary_economy_ID = '20_USA', DELETE_ALL_FILES_IN_FOLDER=True, ALL_IN_ONE_FILE=True, chosen_scenario= 'Reference')
# breakpoint()
#%%

# breakpoint()
# #ecxtract usa sales shares and then save them to input_data/alternate_sales_shares/ECONOMY_ID for every economy for their reference case. Then it will be much easier (except dont do it for china since thats a diferent case)
# # breakpoint()
# # for economy in  config.economy_scenario_concordance['Economy'].unique().tolist():
# #     if economy != '05_PRC':
    
# #         create_alternate_sales_share_file(economy, sales_shares=sales_shares, vehicle_type=None, medium=None, drive=None, transport_type=None, scenario=None, filepath=None, LOAD_LATEST_SALES_SHARES=True, secondary_economy_ID = '20_USA', DELETE_ALL_FILES_IN_FOLDER=True, ALL_IN_ONE_FILE=True, chosen_scenario= 'Reference')
# # breakpoint()
# # #find the reference values for bus if economy is 20_USA and target values for truck if it is 19_Tha.  and see how they look:
# if ECONOMY_ID == '20_USA':
#     a = sales_shares.loc[(sales_shares['Vehicle Type']=='bus')&(sales_shares['Scenario']=='Reference')]
#     a.to_clipboard()
# elif ECONOMY_ID == '19_THA':
#     a = sales_shares.loc[(sales_shares['Vehicle Type']=='ht')&(sales_shares['Scenario']=='Target')]
#     a.to_clipboard()