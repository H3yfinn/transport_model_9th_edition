

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
sys.path.append("./workflow/calculation_functions")
import adjust_data_to_match_esto

#%%
def import_transport_system_data():
    """
    Imports data from the transport data system and returns a dictionary of data frames.

    Args:
        TRANSPORT_DATA_SYSTEM_DATE_TO_USE_FOR_NON_ROAD_TRANSPORT_TYPE_SPLITS (int): The year to use for non-road transport type splits. this should be the year for which we have the most trust in the non road transport data accuracy. Defaults to 2017.

    Returns:
        dict: A dictionary of data frames containing the imported data.
    """
    # function code here
    #import data from the transport data system and extract what we need from it.
    # We can use the model_concordances_measures concordance file to determine what we need to extract from the transport data system. This way we dont rely on things like dataset names.

    model_concordances_measures = pd.read_csv('intermediate_data/computer_generated_concordances/{}'.format(config.model_concordances_base_year_measures_file_name))


    #load transport data  from the transport data system which is out of this repo but is in the same folder as this repo #file name is like DATE20221214_interpolated_combined_data_concordance

    #transport datasystem currently usees a diff file date id structure where it ahs no _ at  the start so we need to remove that#TODO: change the transport data system to use the same file date id structure as the model
    # FILE_DATE_ID2 = config.FILE_DATE_ID.replace('_','')
    
    # combined_data_DATE20230531
    if config.IMPORT_FROM_TRANSPORT_DATA_SYSTEM:
        transport_data_system_folder = '../transport_data_system/output_data'
    else:
        transport_data_system_folder = 'input_data/transport_data_system'
    transport_data_system_df = pd.read_csv('{}/combined_data_{}.csv'.format(transport_data_system_folder,config.transport_data_system_FILE_DATE_ID))

    
    #if they are there, remove cols called index, level_0
    if 'index' in transport_data_system_df.columns:
        transport_data_system_df = transport_data_system_df.drop(columns=['index'])
    if 'level_0' in transport_data_system_df.columns:
        transport_data_system_df = transport_data_system_df.drop(columns=['level_0'])
    if 'Unnamed: 0' in transport_data_system_df.columns:
        transport_data_system_df = transport_data_system_df.drop(columns=['Unnamed: 0'])

    
    #TEMP
    #change the column names to be in capital letters with spaces instead of underscores
    transport_data_system_df.columns = [x.title().replace('_',' ') for x in transport_data_system_df.columns]
    #change some of the columns to have capitals in the first letter of their names (the columns are: Frequency, Measure, Unit ). BUT MAKE SURE ALL THE OTEHR LETTERS ARE LOWER CASE
    transport_data_system_df['Frequency'] = transport_data_system_df['Frequency'].str.capitalize()
    transport_data_system_df['Scope'] = transport_data_system_df['Scope'].str.capitalize()
    transport_data_system_df['Measure'] = transport_data_system_df['Measure'].str.capitalize()
    transport_data_system_df['Unit'] = transport_data_system_df['Unit'].str.capitalize()
    #TEMP
    
    #TEMPORARY FIX, CHANGE THE MEASURE IN TRANSPORT DATA SYSTEM FOR passenger_km and freight_tonne_km to Activity so that it matches the model concordance.
    # transport_data_system_df.loc[transport_data_system_df['Measure']=='passenger_km','Measure'] = 'Activity'
    # transport_data_system_df.loc[transport_data_system_df['Measure']=='freight_tonne_km','Measure'] = 'Activity'

    # #change Date to year and filter out all non yearly data
    # transport_data_system_df['Date'] = transport_data_system_df['Date'].str.split('-').str[0].astype(int)
    transport_data_system_df = transport_data_system_df[transport_data_system_df['Frequency']=='Yearly']
    #make sure scope is National
    transport_data_system_df = transport_data_system_df[transport_data_system_df['Scope']=='National']

    
    #drop unneccessary columns: 'Dataset', 'Source', 'Fuel', 'Comment', 'Scope' if they are in there
    transport_data_system_df = transport_data_system_df.drop(columns=['Dataset', 'Source', 'Fuel', 'Comment', 'Scope'], errors='ignore')
    
    USE_BASE_DATE_ONLY=False#testing if we can utilise years otehr than ust the base year. this cold be useful for better creation of growth curves and gompertz parameters
    if USE_BASE_DATE_ONLY:
        #filter for the same years as are in the model concordances in the transport data system (should just be base Date)
        transport_data_system_df = transport_data_system_df[transport_data_system_df.Date.isin(model_concordances_measures.Date.unique())]

    #filter for the same measures as are in the model concordances in the transport data system
    transport_data_system_df = transport_data_system_df[transport_data_system_df.Measure.isin(model_concordances_measures.Measure.unique())]
    
    TRANSPORT_DATA_SYSTEM_DATE_TO_USE_FOR_NON_ROAD_TRANSPORT_TYPE_SPLITS = yaml.load(open('config/parameters.yml'), Loader=yaml.FullLoader)['TRANSPORT_DATA_SYSTEM_DATE_TO_USE_FOR_NON_ROAD_TRANSPORT_TYPE_SPLITS']
    new_transport_data_system_df = pd.DataFrame()
    
    for economy in transport_data_system_df.Economy.unique():
        DATE_TO_USE_FOR_NON_ROAD_TRANSPORT_TYPE_SPLITS = TRANSPORT_DATA_SYSTEM_DATE_TO_USE_FOR_NON_ROAD_TRANSPORT_TYPE_SPLITS[economy]
        transport_data_system_df_economy = transport_data_system_df[transport_data_system_df.Economy==economy].copy()
        
        transport_data_system_df_economy = adjust_non_road_TEMP(transport_data_system_df_economy,model_concordances_measures,DATE_TO_USE_FOR_NON_ROAD_TRANSPORT_TYPE_SPLITS, economy)   
    
        new_transport_data_system_df = pd.concat([new_transport_data_system_df, transport_data_system_df_economy]) 
    
    transport_data_system_df = new_transport_data_system_df



    ################################MANUAL FIXES HERE################################
    transport_data_system_df = manual_fixes(transport_data_system_df)
    
    ################################MANUAL FIXES HERE################################
    
    
    #now we have filtered out the majority of rows we dont need from the transport data system, we can use pandas difference() function to find out what rows we are missing from the transport data system. This will be useful for debugging and for the user to know what data is missing from the transport data system (as its expected that no data will be missing for the model to actually run))

    INDEX_COLS_NO_SCENARIO = config.INDEX_COLS.copy()
    INDEX_COLS_NO_SCENARIO.remove('Scenario')

    INDEX_COLS_NO_SCENARIO_no_date = INDEX_COLS_NO_SCENARIO.copy()
    INDEX_COLS_NO_SCENARIO_no_date.remove('Date')

    #set index
    transport_data_system_df.set_index(INDEX_COLS_NO_SCENARIO, inplace=True)
    model_concordances_measures.set_index(INDEX_COLS_NO_SCENARIO, inplace=True)

    #create empty df which is a copy of the transport_data_system_df to store the data we extract from the transport data system using an iterative loop
    new_transport_dataset = []

    #create column which will be used to indicate whether the data is available in the transport system, or not
    #options will be:
    #1. data_available
    #2. data_not_available
    #3. row_and_data_not_available

    #we can determine data available and not available now, and then find out option 3 by comparing to the model concordances:

    #where vlaues arent na, set the data_available column to 1, else set to 2
    transport_data_system_df.loc[transport_data_system_df.Value.notna(), 'Data_available'] = 'data_available'
    transport_data_system_df.loc[transport_data_system_df.Value.isna(), 'Data_available'] = 'data_not_available'

    
    # use the difference method to find the index values that are missing from the transport system dataset # this is a lot faster than looping through each index row in the concordance and checking if it is in the user_input
    # we will not print out what values are in the dataset but missing from the concordance as this is expected to be a lot of values (but we will remove them from the dataset as they are not needed for the model to run)
    missing_index_values1 = model_concordances_measures.index.difference(transport_data_system_df.index)
    USE_REPLACEMENTS = False
    replacement_values = None 
    if missing_index_values1.empty:
        pass
    else:
        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
            print(f'Missing {len(missing_index_values1)}rows in our user transport system dataset when we compare it to the concordance')
        #there are some cases where we are just missing data because those specific transport modes arent availavble yet for that economy, eg. bev ht. Thois is ok, since weset them to 0. But then for the measures:, 'Occupancy_or_load', 'Turnover_rate', 'New_vehicle_efficiency', 'Efficiency','Mileage', we will need them available and not 0, so we will need to check for these cases and raise an error if they are missing
        missing_important_values = pd.DataFrame(index=missing_index_values1)
        missing_important_values = missing_important_values.reset_index()
        missing_important_values = missing_important_values.loc[missing_important_values['Measure'].isin(['Occupancy_or_load', 'Turnover_rate', 'New_vehicle_efficiency', 'Efficiency','Mileage'])]

        if not missing_important_values.empty:
            a = missing_important_values.reset_index()[['Measure', 'Vehicle Type', 
        'Transport Type', 'Drive']].drop_duplicates()
            #create df which has some replacements we know we can make:
            #first identify if there are any of these combinations in transport_data_system_df:
            b = transport_data_system_df.copy().reset_index()[['Economy', 'Date', 'Measure', 'Vehicle Type', 
        'Transport Type', 'Drive', 'Value']].drop_duplicates()
        #set index and then find the rows that are in a and b for that index
            a.set_index(['Measure', 'Vehicle Type', 
        'Transport Type', 'Drive'], inplace=True)
            b.set_index(['Measure', 'Vehicle Type', 
        'Transport Type', 'Drive'], inplace=True)
            #find the rows that are in both a and b
            values_can_replace_with = a.index.intersection(b.index)
            #now we have the rows that are in both a and b, we can use this to replace the missing rows in a with the values from b
            if len(values_can_replace_with) > 0:
                print('Missing important values in the transport system dataset. They can be replaced with the following values:', b.loc[values_can_replace_with])
            # else:
            #     #we can still fill them with similar values. for values where drive is cng or lpg, we can fill all values for the same vehicle type and transport type with the means of values where drive is ice
            #     #first find the rows where drive is cng or lpg
            #     cng_lpg = missing_important_values.loc[missing_important_values['Drive'].isin(['cng', 'lpg'])]
            #     #then find the rows where drive is ice
            #     ice = missing_important_values.loc[missing_important_values['Drive'] == 'ice']
            #save a to a csv so we can see what values are missing and fill them in in the trans[port datasyetem
            save_this = True
            if save_this:
              a.to_csv('intermediate_data/transport_data_system/missing_important_values.csv')
            if USE_REPLACEMENTS:#im not sure what the intendsed option if this was false was? I guess it doesnt really matter, we have made it so that the data coming from the transport data system is what we need.
                #for now jsut replace them with the mean for the same vehicle type:
                #first find the mean for each vehicle type by measure and then replace the missing values with these means
                b = transport_data_system_df.copy().reset_index()[['Measure', 'Vehicle Type', 'Value']].drop_duplicates()
                #filter for only the measures we need 
                b = b.loc[b['Measure'].isin(['Occupancy_or_load', 'Turnover_rate', 'New_vehicle_efficiency', 'Efficiency','Mileage'])]
                b.set_index(['Measure', 'Vehicle Type'], inplace=True)
                b = b.groupby(['Measure', 'Vehicle Type']).mean()
                b = b.reset_index()
                replacement_values =b.copy() 
                #create row_and_data_not_available column
                replacement_values['Data_available'] = 'row_and_data_not_available'

        #now we need to add these rows to the transport_data_system_df
        #first create a df with the missing index values
        missing_index_values1 = pd.DataFrame(index=missing_index_values1)
        missing_index_values1['Data_available'] = 'row_and_data_not_available'
        missing_index_values1['Value'] = 0
        #then append to transport_data_system_df
        transport_data_system_df = pd.concat([missing_index_values1, transport_data_system_df], sort=False)
        if USE_REPLACEMENTS and replacement_values is not None:
            #join on the replacement_values
            transport_data_system_df = pd.merge(transport_data_system_df.reset_index(), replacement_values, how='left', on=['Data_available','Measure', 'Vehicle Type'], suffixes=('', '_y'))
            #fill in the missing values with the replacement values where data_available is row_and_data_not_available  and value_y is not null or 0

            transport_data_system_df['Value'] = np.where((transport_data_system_df['Data_available'] == 'row_and_data_not_available') & (transport_data_system_df['Value_y'].notnull())& (transport_data_system_df['Value_y']!=0), transport_data_system_df['Value_y'], transport_data_system_df['Value'])
            #we can leave row_and_data_not_available as is. drop the value_y column
            transport_data_system_df.drop(columns=['Value_y'], inplace=True)
            transport_data_system_df.set_index(INDEX_COLS_NO_SCENARIO_no_date, inplace=True)
    

    if USE_BASE_DATE_ONLY:

        missing_index_values2 = transport_data_system_df.index.difference(model_concordances_measures.index)
    else:
        #set index so date isnt included, then find rows that shouldnt be in the data:
        transport_data_system_df.reset_index(inplace=True)
        transport_data_system_df.set_index(INDEX_COLS_NO_SCENARIO_no_date, inplace=True)
        model_concordances_measures.reset_index(inplace=True)
        model_concordances_measures.set_index(INDEX_COLS_NO_SCENARIO_no_date, inplace=True)
        missing_index_values2 = transport_data_system_df.index.difference(model_concordances_measures.index)

    if missing_index_values2.empty:
        #this is unexpected so create an error
        # raise ValueError('All rows in the transport system dataset are present in the concordance. This is unexpected. Please check the code.')
        pass
    else:
        #we just want to make sure the user is aware that we will be removing rows from the user input
        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
            print('Removing unnecessary rows from the transport datasystem dataset. If you intended to have new data in the dataset, please make sure you have added them to the concordance table as well.')
        #remove these rows from the user_input
        transport_data_system_df.drop(missing_index_values2, inplace=True)


    
    #TEMP
    #if any of the missing values were for turnover rate then set it to 0.03
    transport_data_system_df.loc[((transport_data_system_df.index.get_level_values('Measure')=='Turnover_rate') & (transport_data_system_df.Data_available=='row_and_data_not_available')), 'Value'] = 0.03
    


    #resrt index
    transport_data_system_df.reset_index(inplace=True)
    model_concordances_measures.reset_index(inplace=True)
    # #test what values in x dont equal the values in missing_index_values1
    # for col in x.columns:
    #     print(col)
    #     print(x[col].equals(missing_index_values1[col]))
    
    if not missing_index_values1.empty:
        missing_index_values1.reset_index(inplace=True)
        #save the missing values to a csv for use separately:
        missing_index_values1.to_csv('output_data/for_other_modellers/missing_values/{}_missing_input_values.csv'.format(config.FILE_DATE_ID), index=False)
    else:
        print('No missing values in the transport data system dataset')
    
    #create a scenario column in the transport data system dataset which will have a scenario for each in teh scenarios list in config

    i = 0
    for scenario in config.SCENARIOS_LIST:
        if i == 0:
            #create copy df
            new_transport_data_system_df = transport_data_system_df.copy()
            new_transport_data_system_df['Scenario'] = scenario
            i += 1
        else:
            transport_data_system_df['Scenario'] = scenario
            new_transport_data_system_df = pd.concat([new_transport_data_system_df, transport_data_system_df])
        
    
    #TEMP DROP ANY DATA THAT IS FOR DATES AFTER THE BASE DATE. WE WILL FIGURE OUT HOW TO INCLUDE THEM IN THE FUTURE BUT FOR NOW IT WILL PROBS BE TOO COMPLICATED
    # new_transport_data_system_df = new_transport_data_system_df[new_transport_data_system_df.Date <= config.DEFAULT_BASE_YEAR]
    
    #save the new transport dataset
    new_transport_data_system_df.to_csv('intermediate_data/model_inputs/transport_data_system_extract.csv', index=False)


#TODO need to update thids

def adjust_non_road_TEMP(transport_data_system_df, model_concordances_measures,TRANSPORT_DATA_SYSTEM_DATE_TO_USE_FOR_NON_ROAD_TRANSPORT_TYPE_SPLITS, SINGLE_ECONOMY=None, RAISE_ERROR=False):
    """
    Adjusts the non-road transport data in the transport data system dataframe.

    Args:
        transport_data_system_df (pandas.DataFrame): A dataframe containing the transport data system data.
        model_concordances_measures (pandas.DataFrame): A dataframe containing the concordance between model output measures and transport data system measures.

    Returns:
        pandas.DataFrame: A dataframe containing the adjusted transport data system data.
    """
    #we added drive types to non road. now we need to make sure that the input from datasyustem contains them. 
    #essentailly, the input datasystem data will contain a row for each non road medium (air, rail, ship) and the drive and vehicle types will be 'all'. 
    #now we have created drive types and they are in the concordance.
    #so separate the non road data and merge on the drive types from the concordance, to repalce the 'all' drive types with the new drive types and create new rows where we need. 
    #one issue will be that we will be replicating the vlaues for activity and enegry use, resulting in double counting. so for now, pull in the data from ESTO and make the amount of energy use in each drve type match its repsective fuel use. Then recalcualte the acitvity using the intensity. 
    #however, we will also adjsut the intensity values a tad, since you can expect inttensity of electiricty to be at least a half of that of the fossil fuel types. so we will adjust the intensity of electricity to be 0.5 of the fossil fuel types.
    transport_data_system_df_road=transport_data_system_df[transport_data_system_df['Medium']=='road'].copy()
    #load model concordances with fuels
    model_concordances_fuels = pd.read_csv('intermediate_data/computer_generated_concordances/{}'.format(config.model_concordances_file_name_fuels))


    # date_id = utility_functions.get_latest_date_for_data_file('../transport_data_system/intermediate_data/EGEDA/', 'model_input_9th_cleaned')
    # esto_non_road = pd.read_csv(f'../transport_data_system/intermediate_data/EGEDA/model_input_9th_cleanedDATE{date_id}.csv')
    
    energy_use_esto = adjust_data_to_match_esto.format_9th_input_energy_from_esto()
    
    #keep medium in rail, air and ship
    esto_non_road = energy_use_esto[energy_use_esto.Medium.isin(['rail', 'air', 'ship'])].copy()
    
    # energy_use_esto = energy_use_esto.rename(columns={'Fuel_Type': 'Fuel', 'Value': 'Energy'})

    # #drop these fuels and then check for any otehrs that are missing
    # esto_fuels_to_remove = ['01_coal',
    # '07_petroleum_products',
    # '19_total',
    # '21_modern_renewables',
    # '08_gas',
    # '02_coal_products',
    # '01_01_coking_coal',
    # '01_05_lignite',
    # '06_01_crude_oil',
    # '06_crude_oil_and_ngl',
    # '03_peat',
    # '08_03_gas_works_gas',
    # '16_others',
    # '20_total_renewables',
    # '06_02_natural_gas_liquids']
    # esto_non_road = esto_non_road[~esto_non_road['Fuel'].isin(esto_fuels_to_remove)]
    
    # esto_non_road['Date'] = esto_non_road['Date'].apply(lambda x: x[:4])
    # esto_non_road['Date'] = esto_non_road['Date'].astype(int)

    # #filter for data in years great or = to config.DEFAULT_BASE_YEAR
    # esto_non_road = esto_non_road[esto_non_road['Date'] >= config.DEFAULT_BASE_YEAR]

    #drop economy in APEC '22_SEA', '23_NEA', '23b_ONEA', '24_OAM', '24b_OOAM', '25_OCE'
    # esto_non_road = esto_non_road.loc[~esto_non_road['Economy'].isin(['22_SEA', '23_NEA', '23b_ONEA', '24_OAM', '24b_OOAM', '25_OCE', 'APEC'])].copy()

    # #drop nonneeded cols
    # esto_non_road = esto_non_road.drop(columns=['Frequency', 'Source', 'Dataset', 'Measure', 'Vehicle Type', 'Drive', 'Transport Type', 'Unit'])


    model_concordances_fuels_non_road = model_concordances_fuels[model_concordances_fuels.Medium.isin(['rail', 'air', 'ship'])]
    model_concordances_fuels_non_road = model_concordances_fuels_non_road[[ 'Medium', 'Fuel', 'Drive']].drop_duplicates()
    #join the model_concordances_fuels onto it so we can get the correspinding drive type for each fuel type.
    esto_non_road_drives = pd.merge(esto_non_road, model_concordances_fuels_non_road, how='outer', on=['Medium', 'Fuel'])

    #also drop any fuels that are mixed in on the supply side only (i.e. biofuels):    
    supply_side_fuel_mixing_fuels = pd.read_csv('intermediate_data/computer_generated_concordances/{}'.format(config.model_concordances_supply_side_fuel_mixing_file_name), dtype={'Demand_side_fuel_mixing': str}).New_fuel.unique().tolist()
    # #TEMP
    # #IF 16_01_biogas ISNT IN THERE, ADD IT
    # if '16_01_biogas' not in supply_side_fuel_mixing_fuels:
    #     print('######################\n 16_01_biogas not in supply_side_fuel_mixing_fuels. Adding it \n ################')
    #     supply_side_fuel_mixing_fuels.append('16_01_biogas')
    # else:
    #     print('REMOVE THIS LINE!')
    esto_non_road_drives = esto_non_road_drives[~esto_non_road_drives.Fuel.isin(supply_side_fuel_mixing_fuels)]
    
    #if there are any nans in the following list then throw error:
    # new_fuels= ['16_x_ammonia']
    if len(esto_non_road_drives[esto_non_road_drives.Date.isna()]) > 0:
        breakpoint()
        time.sleep(1)
        raise ValueError('There are some new fuels in the non road data that are not in the model concordances. Please add them {} to the model concordances'.format(esto_non_road_drives[esto_non_road_drives.Date.isna()].Fuel.unique().tolist()))

    #drop the rows where the fuel is not na but economy and Date are na (this is where the fuel is not in the esto data but is in the model concordances)
    # esto_non_road_drives = esto_non_road_drives[~((esto_non_road_drives.Fuel.notna()) & (esto_non_road_drives.Economy.isna()) & (esto_non_road_drives.Date.isna()))]#ifgnore this because the dfata we are using is now the 9th eidtion model inport, so eveyr possible orw should be there with at least 0's or nas

    #and then find where we may  be missing some data in the conocrdances by findin where the drive is na but the fuel is not na, and the date is greater than config.OUTLOOK_BASE_YEAR-1
    missing_drives = esto_non_road_drives[esto_non_road_drives.Drive.isna() & esto_non_road_drives.Fuel.notna() & (esto_non_road_drives.Date >= config.OUTLOOK_BASE_YEAR)][['Medium', 'Fuel']].drop_duplicates()
    if not missing_drives.empty:
        raise ValueError('There are some fuels in the non road data that are not in the model concordances. Please add them {} to the model concordances'.format(missing_drives))

    if SINGLE_ECONOMY != None:
        a = esto_non_road_drives.copy()
        b = energy_use_esto.copy()
        c = model_concordances_fuels.copy()
        # esto_non_road_drives = a.copy()
        # energy_use_esto = b.copy()
        # model_concordances_fuels = c.copy()
        energy_use_esto = energy_use_esto[energy_use_esto.Economy == SINGLE_ECONOMY]
        esto_non_road_drives = esto_non_road_drives[esto_non_road_drives.Economy == SINGLE_ECONOMY]
        model_concordances_fuels = model_concordances_fuels[model_concordances_fuels.Economy == SINGLE_ECONOMY]
        
    #set date to int as its become a float ):
    esto_non_road_drives['Date'] = esto_non_road_drives['Date'].astype(int)
    
    #great. now we want to create these new rows in the transport data system dataset. Use the energy use in the esto data and then recalc activity using the intensity. 
    transport_data_system_non_road = transport_data_system_df[transport_data_system_df['Medium'].isin(['rail', 'air', 'ship'])].copy()
    #drop Unit and then pivot the MEasure
    transport_data_system_non_road = transport_data_system_non_road.drop(columns=['Frequency','Unit'])
    #checking for duplicates
    dupes = transport_data_system_non_road[transport_data_system_non_road[['Measure','Economy', 'Date', 'Medium', 'Drive', 'Vehicle Type', 'Transport Type']].duplicated()]
    if len(dupes) > 0:
        breakpoint()
        raise ValueError('There are some duplicates in the transport data system non road data. Please check the code: {}'.format(dupes))
    transport_data_system_non_road = transport_data_system_non_road.pivot(index=['Economy', 'Date', 'Medium', 'Drive', 'Vehicle Type', 'Transport Type'], columns='Measure', values='Value').reset_index()
    
    #keep energy measures only so that dropping na rows doesnt drop any rows we need
    transport_data_system_non_road_energy_only = transport_data_system_non_road.drop([col for col in transport_data_system_non_road.columns if col not in ['Economy', 'Date', 'Medium', 'Drive', 'Vehicle Type', 'Transport Type', 'Energy']], axis=1).copy()

    #get the previous splits between passenger and freight transport in energy, by economy and date (also drop na rows)
    transport_data_system_transport_type_splits = transport_data_system_non_road_energy_only.dropna().pivot(index=['Economy', 'Date', 'Medium','Drive', 'Vehicle Type'], columns='Transport Type', values='Energy').reset_index().copy()
    #if transport_data_system_transport_type_splits is empty then just create a df with the columns we need
    if transport_data_system_transport_type_splits.empty:
        transport_data_system_transport_type_splits = pd.DataFrame(columns=['Economy', 'Date', 'Medium','Drive', 'Vehicle Type', 'freight', 'passenger'])
    #calc the ratio between passenger and freight

    transport_data_system_transport_type_splits['freight_ratio'] = transport_data_system_transport_type_splits['freight'] / (transport_data_system_transport_type_splits['passenger']+transport_data_system_transport_type_splits['freight'])
    #if the Date is not only for config.DEFAULT_BASE_YEAR then throw an erorr, because resty of code is predicated on this:
    # if not set(transport_data_system_transport_type_splits.Date.unique().tolist()) == set(TRANSPORT_DATA_SYSTEM_DATE_TO_USE_FOR_NON_ROAD_TRANSPORT_TYPE_SPLITS):
    #filter fopr only TRANSPORT_DATA_SYSTEM_DATE_TO_USE_FOR_NON_ROAD_TRANSPORT_TYPE_SPLITS

    # breakpoint()#why is this important actually? i think maybe its already done by the previoous fuinction?
    #filter for only the years in TRANSPORT_DATA_SYSTEM_DATE_TO_USE_FOR_NON_ROAD_TRANSPORT_TYPE_SPLITS
    transport_data_system_transport_type_splits = transport_data_system_transport_type_splits[transport_data_system_transport_type_splits.Date==TRANSPORT_DATA_SYSTEM_DATE_TO_USE_FOR_NON_ROAD_TRANSPORT_TYPE_SPLITS]
    # raise ValueError(f'The transport data system data for non road is not only for {config.DEFAULT_BASE_YEAR}. Please make sure it is only for {config.DEFAULT_BASE_YEAR}')
    
    transport_data_system_transport_type_splits = transport_data_system_transport_type_splits.drop(columns=['Date'])
    #filter for 2017 plus in the esto data (we need all dates for esto data since we need this energy use to be in the output data)
    esto_non_road_drives = esto_non_road_drives[esto_non_road_drives.Date >= config.DEFAULT_BASE_YEAR]
    #use freight ratio to pslit the esto data before we join it on:
    esto_non_road_drives_ttype_split = pd.merge(esto_non_road_drives, transport_data_system_transport_type_splits[['Economy', 'Medium', 'freight_ratio']], how='left', on=['Economy', 'Medium'])#'Date', #dropped date from here
    #############
    #identify if there are any nas:
    # allowed_rows = [#this is where the data just isnt in esto. we can ignore these
    #     ['15_PHL', 'air'],
    #     ['02_BD', 'air'],
    #     ['17_SGP', 'air'],
    #     ['15_PHL', 'rail'],
    #     ['02_BD', 'rail'],
    #     ['13_PNG', 'rail'],
    #     ['17_SGP', 'rail'],
    #     ['15_PHL', 'ship'],
    #     ['17_SGP', 'ship'],
    #     ['02_BD', 'ship'],
    #     ['14_PE', 'ship'],
    #       
    allowed_rows = [
        # ['04_CHL', 'air'],
        # ['11_MEX', 'air'],
        # ['15_PHL', 'air'],
        # ['16_RUS', 'air'],
        ['02_BD', 'air'],
        # ['05_PRC', 'air'],
        # ['06_HKC', 'air'],
        ['17_SGP', 'air'],
        # ['21_VN', 'air'],
        # ['16_RUS', 'rail'],
        ['02_BD', 'rail'],
        # ['06_HKC', 'rail'],
        ['10_MAS', 'rail'],
        ['13_PNG', 'rail'],
        ['14_PE', 'rail'],
        # ['15_PHL', 'rail'],
        ['17_SGP', 'rail'],
        # ['19_THA', 'rail'],
        # ['21_VN', 'rail'],
        # ['05_PRC', 'ship'],
        # ['06_HKC', 'ship'],
        # ['15_PHL', 'ship'],
        # ['16_RUS', 'ship'],
        # ['11_MEX', 'ship'],
        ['17_SGP', 'ship'],
        # ['21_VN', 'ship'],
        ['10_MAS', 'ship'],
        ['14_PE', 'ship'],
        ['02_BD', 'ship']
        # ['07_INA', 'ship'],
    ]

    allowed_rows = pd.DataFrame(allowed_rows, columns=['Economy', 'Medium'])

    if SINGLE_ECONOMY != None:
        #filter for economy in allowed rows
        allowed_rows = allowed_rows[allowed_rows.Economy == SINGLE_ECONOMY]
        
    missing_values = esto_non_road_drives_ttype_split[esto_non_road_drives_ttype_split.freight_ratio.isna()][['Economy', 'Medium']].drop_duplicates()  
    non_missing_values = esto_non_road_drives_ttype_split[esto_non_road_drives_ttype_split.freight_ratio.notna()][['Economy', 'Medium']].drop_duplicates()
    if not missing_values.empty:
        # Check if any missing rows are not in allowed rows
        invalid_rows = missing_values.merge(allowed_rows, on=['Economy', 'Medium'], how='left', indicator=True)
        invalid_rows = invalid_rows[invalid_rows['_merge'] == 'left_only']

        if not invalid_rows.empty:
            breakpoint()
            raise ValueError('There are missing freight ratios in the transport data system dataset that are not allowed. Please make sure all data is present for each economy and medium. {}'.format(invalid_rows[['Economy', 'Medium']].values.tolist()))
    else:
        # Check if any allowed rows have non-missing values
        invalid_rows = allowed_rows.merge(non_missing_values, on=['Economy', 'Medium'], how='left', indicator=True)
        invalid_rows = invalid_rows[invalid_rows['_merge'] == 'both']

        if not invalid_rows.empty:
            if RAISE_ERROR:
                breakpoint()
                raise ValueError('The following rows have non-na values in the freight ratio column. Please check the code because we didn\'t expect this: {}'.format(invalid_rows[['Economy', 'Medium']].values.tolist()))
            else:
                print('The following rows have non-na values in the freight ratio column. Please check the code because we didn\'t expect this: {}'.format(invalid_rows[['Economy', 'Medium']].values.tolist()))
    #############
    #get passengernand freight energy
    esto_non_road_drives_ttype_split['passenger'] = esto_non_road_drives_ttype_split['Energy'] * (1-esto_non_road_drives_ttype_split['freight_ratio'])
    esto_non_road_drives_ttype_split['freight'] = esto_non_road_drives_ttype_split['Energy'] * esto_non_road_drives_ttype_split['freight_ratio']
    
    #drop energy and then melt the df so we have a row for each transport type
    esto_non_road_drives_ttype_split = esto_non_road_drives_ttype_split.drop(columns=['Energy', 'freight_ratio'])
    esto_non_road_drives_ttype_split = esto_non_road_drives_ttype_split.melt(id_vars=['Economy', 'Date', 'Medium', 'Fuel', 'Drive'], var_name='Transport Type', value_name='Energy')
    
    #now this can be joined to the transport_data_system_non_road and times by intensity to get the acitvity
    final_df_non_road = pd.merge(transport_data_system_non_road[['Economy', 'Date', 'Medium', 'Transport Type', 'Intensity', 'Average_age']].drop_duplicates(), esto_non_road_drives_ttype_split, how='left', on=['Economy', 'Date', 'Medium', 'Transport Type'])#PLEASE NOTE THAT I ADDED AVERAGE AGE HERE. THE CODE WORKS FOR IT BUT DOESNT SEEM TO BE MEANT FOR IT. lATER WOULD BE GOD TO MAKE THIS MORE ROBUST/UNDERSTANDABLE
    
    #drop where Drive is nan. this is where we didnt have any data in the esto data and so we dont wqant to cosider it in the model:
    #ACTUALLY JUST CHECK IF THERE ARE ANY NANS IN THE DRIVE COL. IF THERE ARE THEN THROW AN ERROR. IM PRETTY SURE WE REQUIRE THAT THE ESTO DATA NEEDS TO HAVE ALL THE DATA?
    if final_df_non_road.Drive.isna().any():
        #drop allowed_rows and filter for Date >= config.DEFAULT_BASE_YEAR and then check if there are any nans in the drive col still:
        nas = final_df_non_road[final_df_non_road.Drive.isna()]
        nas= nas.merge(allowed_rows, on=['Economy', 'Medium'], how='left', indicator=True)
        nas = nas.loc[(nas['_merge'] == 'left_only') & (nas['Date'] >= config.DEFAULT_BASE_YEAR) & (nas['Date'] <= config.OUTLOOK_BASE_YEAR)]
        if not nas.empty:
            breakpoint()
            #pause briefly to allow breakpoint to be hit
            import time
            time.sleep(0.1)
            raise ValueError('There are some missing drive types in the transport data system dataset. Please make sure they are all present for each economy and medium {}'.format(nas))
            # final_df_non_road = final_df_non_road.dropna(subset=['Drive'])
        else:
            #drop the rows where the drive is na
            final_df_non_road = final_df_non_road.dropna(subset=['Drive'])
        
    
    #adust intensity where electi4ricty/ammonia/hydrogen is being used:
    new_drive_types = [drive for drive in final_df_non_road.Drive.dropna().unique().tolist() if 'electric' in drive]# or 'ammonia' in drive or 'hydrogen' in drive]

    #set intensity to 0.5 for electric drive types
    final_df_non_road['Intensity'] = final_df_non_road.apply(lambda row: set_new_non_road_drives_to_half_intensity(row,new_drive_types), axis=1)
    
    #where the drive is in electric_drive_types, set the intensity to 0.5 of the intensity 
    # final_df_non_road.loc[final_df_non_road['Drive'].isin(electric_drive_types), 'Intensity'] = final_df_non_road.loc[final_df_non_road['Drive'].isin(electric_drive_types)].Intensity * 0.5
    #calc activity
    final_df_non_road['Activity'] = final_df_non_road['Energy'] / final_df_non_road['Intensity']

    #create vehicle type col and makle it all 'all'
    final_df_non_road['Vehicle Type'] = 'all'
    final_df_non_road['Frequency'] = 'Yearly'
    #melt the df so we have a row for each measure
    final_df_non_road = final_df_non_road.melt(id_vars=['Economy', 'Date', 'Medium', 'Transport Type', 'Fuel', 'Drive', 'Vehicle Type', 'Frequency'], var_name='Measure', value_name='Value')
    #map units to the col. do this by using them from moel concordances
    units_map = model_concordances_measures[['Measure', 'Unit']].drop_duplicates()
    final_df_non_road = pd.merge(final_df_non_road, units_map, how='left', on='Measure')
    #drop Fuel since its not needed
    final_df_non_road = final_df_non_road.drop(columns=['Fuel'])
    #conat to transport_data_system_df_road then finis
    transport_data_system_df_new = pd.concat([transport_data_system_df_road, final_df_non_road], sort=False)
    #in final_df_non_road search for any duplciates in teh columns INDEX_COLS
    INDEX_COLS_no_scenario = config.INDEX_COLS.copy()
    INDEX_COLS_no_scenario.remove('Scenario')
    dupes = final_df_non_road[final_df_non_road.duplicated(subset=INDEX_COLS_no_scenario, keep=False)]
    if len(dupes) > 0:
        breakpoint()
        
        import time
        time.sleep(0.1)
        raise ValueError('There are some duplicated rows in the final_df_non_road. Please check the code')
    # transport_data_system_non_road[transport_data_system_non_road.duplicated(subset=['Date', 'Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive'], keep=False)]
    return transport_data_system_df_new

    
def set_new_non_road_drives_to_half_intensity(row,new_drive_types):
    #made in to a funciton for visibilty!
    if row.Drive in new_drive_types:
        return row.Intensity * 0.5
    else:
        return row.Intensity
    
def manual_fixes(transport_data_system_df):
    #in rare occasions its necessary to manually fix the transport data system data. This is where we do that.

    #halve the intensity of indonesian rail so we get more activity per pj
    transport_data_system_df.loc[(transport_data_system_df.Economy=='07_INA') & (transport_data_system_df.Medium=='rail') & (transport_data_system_df.Measure=='Intensity'), 'Value'] = transport_data_system_df.loc[(transport_data_system_df.Economy=='07_INA') & (transport_data_system_df.Medium=='rail') & (transport_data_system_df.Measure=='Intensity'), 'Value'] * 0.5
    
    return transport_data_system_df
#%%
# import_transport_system_data()
#%%
