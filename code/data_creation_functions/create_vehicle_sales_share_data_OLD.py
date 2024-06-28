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
if __name__ == "__main__": #this allows the script to be run directly or from the main.py file as you cannot use relative imports when running a script directly
    # Modify sys.path to include the directory where utility_functions is located
    sys.path.append(f"{root_dir}/code")
    import config
    import utility_functions
    sys.path.append(f"{root_dir}/code/plotting_functions")
    import plot_user_input_data

    import archiving_scripts
else:
    # Assuming the script is being run from main.py located at the root of the project, we want to avoid using sys.path.append and instead use relative imports 
    try:
        from ..utility_functions import *
        from ..config import *
    except ImportError:
        import utility_functions
        import config
    from ..plotting_functions import plot_user_input_data
    from .. import archiving_scripts
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

import user_input_creation_functions
X_ORDER = 'linear'#set me to linear or the order for the spline
#%%

def create_vehicle_sales_share_input(ECONOMY_ID,RECALCULATE_SALES_SHARES_USING_RECALCULATED_INPUT_DATA = False):
    """_summary_

    Args:
        ECONOMY_ID (_type_): _description_
        RECALCULATE_SALES_SHARES_USING_RECALCULATED_INPUT_DATA (bool, optional): _description_. Defaults to False. Determines if we base sales share off a previous model run, which normally occurs if advance bsae year is true and we adjusted the transport data system input data to reflect ESTO values. 
        
    Raises:
        ValueError: _description_
        Exception: _description_
        ValueError: _description_
        ValueError: _description_
        ValueError: _description_

    Returns:
        _type_: _description_
    """
    YEARS_TO_KEEP_AFTER_BASE_YEAR= 3
    
    ECONOMIES_WITH_MODELLING_COMPLETE_DICT = yaml.load(open(root_dir + '/' + 'config/parameters.yml'), Loader=yaml.FullLoader)['ECONOMIES_WITH_MODELLING_COMPLETE']
    SET_YEAR_WITH_MOST_VALUES_TO_BASE_YEAR = ECONOMIES_WITH_MODELLING_COMPLETE_DICT[ECONOMY_ID]
    #if we calculate using recalcualted input data we need to format the data differently*
    if RECALCULATE_SALES_SHARES_USING_RECALCULATED_INPUT_DATA:
        
        # road_model_input_wide.to_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
        # non_road_model_input_wide.to_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_non_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
        road_model_input_wide = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))
        non_road_model_input_wide = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_non_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))
        
        #reforma:
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
    else:
            
        # new_sales_shares = pd.read_csv(root_dir + '/' + 'input_data/from_8th/reformatted/vehicle_stocks_change_share_normalised.csv')
        #load groomed data from transport data system
        transport_data_system_df = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/transport_data_system_extract.csv')
        #filter for ECONOMY_ID
        transport_data_system_df = transport_data_system_df.loc[transport_data_system_df['Economy']==ECONOMY_ID]
        new_transport_data_system_df = transport_data_system_df.copy() 
    
        #drop non road
        new_transport_data_system_df = new_transport_data_system_df.loc[new_transport_data_system_df['Medium']=='road']
        #insert stocks data for non road. do this by copying the activity data and setting stocks to be the same (i.e. the activity per stock is 1)
        non_road_stocks = transport_data_system_df.copy()
        non_road_stocks = non_road_stocks.loc[(non_road_stocks['Measure']=='Activity') & (non_road_stocks['Medium']!='road')].copy()
        non_road_stocks['Measure'] = 'Stocks'
        non_road_stocks['Unit'] = 'Stocks'
        #now concat again
        new_transport_data_system_df = pd.concat([new_transport_data_system_df, non_road_stocks])
    #this means we ahve to calcualte the sales by finding the difference between the stock in the current year and the stock in the previous year.
    #this could rersult in issues because we may have gaps in our data. but for now we will just assume that we have data for every year and see how it goes:
    new_transport_data_system_df['road'] = new_transport_data_system_df['Medium']=='road'
    # if RECALCULATE_SALES_SHARES_USING_RECALCULATED_INPUT_DATA:
    #     breakpoint()#div by 0 in following function.#it seems that the passenger sales share is being set to 0 here for ct and jp. not sure why.
    #     #why is there only passenger data for non road
    sales = estimate_transport_data_system_sales_share_using_share_of_activity(ECONOMY_ID, new_transport_data_system_df,YEARS_TO_KEEP_AFTER_BASE_YEAR, SET_YEAR_WITH_MOST_VALUES_TO_BASE_YEAR)
    #drop 'road' for now (it wont work with the concordances)
    sales = sales.drop(columns=['road'])
    #extract dictionary from csv
    #for later, load in vehicle_type_growth_regions sheet and vehicle_type_growth sheet
    vehicle_type_growth_regions = pd.read_excel(root_dir + '/' + 'input_data/vehicle_sales_share_inputs.xlsx',sheet_name='vehicle_type_growth_regions')
    vehicle_type_growth = pd.read_excel(root_dir + '/' + 'input_data/vehicle_sales_share_inputs.xlsx',sheet_name='vehicle_type_growth').drop(columns=['Comment'])

    passenger_drive_shares = pd.read_excel(root_dir + '/' + 'input_data/vehicle_sales_share_inputs.xlsx',sheet_name='passenger_drive_shares').drop(columns=['Comment'])
    freight_drive_shares = pd.read_excel(root_dir + '/' + 'input_data/vehicle_sales_share_inputs.xlsx',sheet_name='freight_drive_shares').drop(columns=['Comment'])    
    
    regions_passenger = pd.read_excel(root_dir + '/' + 'input_data/vehicle_sales_share_inputs.xlsx',sheet_name='regions_passenger')
    regions_freight = pd.read_excel(root_dir + '/' + 'input_data/vehicle_sales_share_inputs.xlsx',sheet_name='regions_freight')


    ######################################
    #TESTING
    #check the regions in regions_passenger and regions_freight are the same as in passenger_drive_shares and freight_drive_shares, also check that the regions in vehicle_type_growth_regions are the same as in vehicle_type_growth
    
    user_input_creation_functions.check_region(regions_passenger, passenger_drive_shares)
    user_input_creation_functions.check_region(regions_freight, freight_drive_shares)
    user_input_creation_functions.check_region(vehicle_type_growth_regions, vehicle_type_growth)
    #join regions
    passenger_drive_shares = pd.merge(passenger_drive_shares, regions_passenger, how='left', on='Region')
    freight_drive_shares = pd.merge(freight_drive_shares, regions_freight, how='left', on='Region')
    vehicle_type_growth = pd.merge(vehicle_type_growth, vehicle_type_growth_regions, how='left', on='Region')
    #extract only the economy we want and drop the region col
    passenger_drive_shares = passenger_drive_shares.loc[passenger_drive_shares['Economy']==ECONOMY_ID].drop(columns=['Region'])
    freight_drive_shares = freight_drive_shares.loc[freight_drive_shares['Economy']==ECONOMY_ID].drop(columns=['Region'])
    vehicle_type_growth = vehicle_type_growth.loc[vehicle_type_growth['Economy']==ECONOMY_ID].drop(columns=['Region'])

    #####################################
    #PREPARE INPUT DATA
    #####################################

    #first we need to separate the sales share of vehicle types from the sales share of drives, by transport type. Since the way the values were created was simply mutliplication, we can jsut reverse that, i think.
    #so sum by vehicle type to get the total sales share of each vehicle type
    #then if we divide this by the final sales share values for each v-type/drive we can recreate the shares by drive type, witihin each vehicle type.
    #now for shares by drive type, witihin each vehicle type, we can create the shares we want.
    #sum by vtype economy year and scenario
    new_sales_shares_sum = sales.copy()

    #Identify duplicates in case we have multiple rows for the same economy, vehicle type, drive type, transport type and date
    # #todo for some reason we need to do this and i htink its
    new_sales_shares_sum_dupes = new_sales_shares_sum[new_sales_shares_sum.duplicated(subset=['Economy', 'Scenario', 'Medium','Vehicle Type', 'Transport Type','Drive', 'Date','Medium'])]
    if len(new_sales_shares_sum_dupes)>0:#somehow getting dupes. 
        raise ValueError('new_sales_shares_sum_dupes is not empty. This should not happen. Investigate')
        
    #now doulbe check we have therequired categories that are in the concordances
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

    #add BASE YEAR to the concordances which canb be a copy of the config.DEFAULT_BASE_YEAR +1
    model_concordances_user_input_and_growth_rates_base = model_concordances_user_input_and_growth_rates.loc[model_concordances_user_input_and_growth_rates['Date']==config.DEFAULT_BASE_YEAR+1].copy()
    model_concordances_user_input_and_growth_rates_base['Date'] = config.DEFAULT_BASE_YEAR
    model_concordances_user_input_and_growth_rates = pd.concat([model_concordances_user_input_and_growth_rates,model_concordances_user_input_and_growth_rates_base])

    #set index for both dfs
    new_sales_shares_sum.set_index(new_INDEX_COLS, inplace=True)
    model_concordances_user_input_and_growth_rates.set_index(new_INDEX_COLS, inplace=True)

    # use the difference method to find:
    #missing_index_values1 :  the index values that are missing from the new_sales_shares_sum 
    # #missing_index_values2 : and also the index values that are present in the new_sales_shares_sum but not in the concordance 
    # this method is a lot faster than looping through each index row in the concordance and checking if it is in the new_sales_shares_sum
    missing_index_values1 = model_concordances_user_input_and_growth_rates.index.difference(new_sales_shares_sum.index)
    missing_index_values2 = new_sales_shares_sum.index.difference(model_concordances_user_input_and_growth_rates.index)

    if missing_index_values1.empty:
        pass
    else:
        #add these rows to the new_sales_shares_sum and set them to row_and_data_not_available
        missing_index_values1 = pd.DataFrame(index=missing_index_values1).reset_index()
        missing_index_values1['Sales Share'] = np.nan
        #then append to transport_data_system_df
        new_sales_shares_sum = new_sales_shares_sum.reset_index()
        new_sales_shares_sum = pd.concat([missing_index_values1, new_sales_shares_sum], sort=False)
        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
            print(f'Missing {len(missing_index_values1)} rows in our user input dataset when we compare it to the concordance')
        new_sales_shares_sum.set_index(new_INDEX_COLS, inplace=True)

    if missing_index_values2.empty:
        pass#this is to be expected as the cocnordance should always have everything we need in it!
    else:
        #we want to make sure user is aware of this as we will be removing rows from the user input
        #remove these rows from the new_sales_shares_sum
        new_sales_shares_sum.drop(missing_index_values2, inplace=True)
        #convert missing_index_values to df
        missing_index_values2 = pd.DataFrame(index=missing_index_values2).reset_index()
        print('Missing {} rows in the user input concordance'.format(len(missing_index_values2)))
        print('We will remove these rows from the user input dataset. If you intended to have data for these rows, please add them to the concordance table.')

        # #print the unique Vehicle types and drives that are missing
        # print('Unique Vehicle types and drives that are missing: {}'.format(missing_index_values2[['Vehicle Type', 'Drive']].drop_duplicates()))#as of /4 we ha

    #replace all nan values with 0 now
    # new_sales_shares_sum.fillna(0, inplace=True)

    #reset index
    new_sales_shares_sum.reset_index(inplace=True)
    model_concordances_user_input_and_growth_rates.reset_index(inplace=True)
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

    new_sales_shares_sum['Drive_share'] = new_sales_shares_sum['Transport_type_share']/new_sales_shares_sum['Vehicle_type_share_sum']

    #now we can create the shares we want


    
    #first create a clean dataframe with all values set to NA for every year after the base year
    new_sales_shares_sum_clean = new_sales_shares_sum[['Economy', 'Scenario','Medium', 'road', 'Transport Type', 'Date', 'Vehicle Type', 'Drive', 'Drive_share']].drop_duplicates()

    new_sales_shares_sum_0 = new_sales_shares_sum_clean.copy()

    new_sales_shares_sum_0.loc[new_sales_shares_sum_0['Date']>config.DEFAULT_BASE_YEAR+YEARS_TO_KEEP_AFTER_BASE_YEAR, 'Drive_share'] = np.nan

    #sort
    new_sales_shares_sum_0 = new_sales_shares_sum_0.sort_values(by=['Economy', 'Scenario', 'Date', 'Vehicle Type','Medium','road', 'Transport Type', 'Drive'])

    #were getting no values fro Drive_share for <=config.DEFAULT_BASE_YEAR
    ########################################################################################################################################################
    #BEGIN INCORPORATING USER INPUTTED SALES SHARES
    ########################################################################################################################################################
    
    #for this we will perfrom the hcanges on passenger and freight separately. So here we will separate them and then combine them at the end
    new_sales_shares_passenger_0 = new_sales_shares_sum_0[new_sales_shares_sum_0['Transport Type']=='passenger']
    new_sales_shares_freight_0 = new_sales_shares_sum_0[new_sales_shares_sum_0['Transport Type']=='freight']

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

    passenger_drive_shares = passenger_drive_shares.melt(id_vars=['Economy', 'Medium','Vehicle Type', 'Drive', 'Date'],var_name='Scenario', value_name='Share')
    freight_drive_shares = freight_drive_shares.melt(id_vars=['Economy', 'Medium','Vehicle Type', 'Drive', 'Date'],var_name='Scenario', value_name='Share')
    
    #drop any rows with 'Will make up the rest' in the Drive_share col. These are just pllaceholders to let the user know they can ignore that row
    passenger_drive_shares = passenger_drive_shares.loc[passenger_drive_shares['Share']!='Will make up the rest']
    freight_drive_shares = freight_drive_shares.loc[freight_drive_shares['Share']!='Will make up the rest']
    
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
                                df.loc[(df['Economy'] == economy) & (df['Vehicle Type'] == veh_type) & (df['Drive'] == drive) & (df['Date'] == year) & (df['Scenario'] == scenario)& (df['Medium'] == mediums), 'Drive_share'] = share_
        return df

    #using the drive shares we laoded in, create a df with which to set the drive shares
    new_sales_shares_passenger_1 = create_drive_shares_df(new_sales_shares_passenger_0, drive_shares_passenger_dict) 
    new_sales_shares_freight_1 = create_drive_shares_df(new_sales_shares_freight_0, drive_shares_freight_dict)
    ############################################################################

    #concatenate transport types
    new_sales_shares_pre_interp = pd.concat([new_sales_shares_passenger_1, new_sales_shares_freight_1])
    
    #TODO NOT SURE IF NECESSARY
    passenger_drive_shares['road'] = passenger_drive_shares['Medium']=='road'
    freight_drive_shares['road'] = freight_drive_shares['Medium']=='road'
    ################################################################################
    new_sales_shares_pre_interp = calcaulte_missing_drive_shares_from_manually_inputted_data(new_sales_shares_pre_interp, model_concordances_user_input_and_growth_rates, passenger_drive_shares, freight_drive_shares,YEARS_TO_KEEP_AFTER_BASE_YEAR)

    #thewn plot the new sales shares before inteproaltions:
    plotting = False
    if plotting:
        plot_user_input_data.plot_input_sales_shares_before_interpolation(new_sales_shares_pre_interp)
    
    ################################################################################################################################################################
    #TEST FOR MISSING DATA
    ################################################################################################################################################################
    
    #for each group in new_sales_shares_pre_interp check that there is at least 4 sales share values for the group, so that the interpolation can be done
    new_sales_shares_test = new_sales_shares_pre_interp.copy()
    #drop na in Drive Share col
    new_sales_shares_test = new_sales_shares_test.dropna(subset=['Drive_share'])
    new_sales_shares_test = new_sales_shares_test.groupby(['Economy', 'Scenario','Medium', 'road','Transport Type', 'Vehicle Type', 'Drive']).count().reset_index()
    #where we have very few sales shares to interpoalte by, we can just set the sales share to 0, but tell teh user.
    new_sales_shares_test = new_sales_shares_test.loc[new_sales_shares_test['Date']<=4]
    
    if len(new_sales_shares_test) > 0:
        #get unique groups
        new_sales_shares_test = new_sales_shares_test[['Economy', 'Scenario', 'Transport Type','Medium','road', 'Vehicle Type', 'Drive']].drop_duplicates()
        #print unique groups when you ignore scenario and economy
        new_sales_shares_test_unique = new_sales_shares_test[['Transport Type', 'Medium','Vehicle Type', 'Drive']].drop_duplicates()
        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
            print(f'{len(new_sales_shares_test_unique)} groups have less than 4 sales shares to interpolate by. Sales shares for these groups will be set to 0 for beginnig years.Please check the data and rerun the model if this is not what you want')

        #set sales share to 0 in the begbinning years for these groups by retrievinmg them by index. So set index of both to [['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive']] and then set the sales share to 0 for the index of the groups in new_sales_shares_test
        new_sales_shares_test = new_sales_shares_test.set_index(['Economy', 'Scenario', 'Transport Type','Medium','road', 'Vehicle Type', 'Drive'])
        new_sales_shares_pre_interp = new_sales_shares_pre_interp.set_index(['Economy', 'Scenario', 'Transport Type','Medium','road', 'Vehicle Type', 'Drive'])

        common_indices = new_sales_shares_test.index.intersection(new_sales_shares_pre_interp.index)

        new_sales_shares_pre_interp.loc[(new_sales_shares_pre_interp.index.isin(common_indices))&(new_sales_shares_pre_interp['Date']<=config.DEFAULT_BASE_YEAR + YEARS_TO_KEEP_AFTER_BASE_YEAR), 'Drive_share'] = 0

        
        # new_sales_shares_pre_interp.loc[(new_sales_shares_test.index)&(new_sales_shares_pre_interp['Date']<=config.config.DEFAULT_BASE_YEAR + YEARS_TO_KEEP_AFTER_config.config.DEFAULT_BASE_YEAR), 'Drive_share'] = 0
        #reset index
        new_sales_shares_pre_interp = new_sales_shares_pre_interp.reset_index()
    
    ################################################################################
    # INTERPOLATE BETWEEN SALES SHARES
    ################################################################################
    #NOW DO INTERPOLATION
    #check for duplicates on the cols we will group by
    new_sales_shares_concat_interp_dupes = new_sales_shares_pre_interp[new_sales_shares_pre_interp.duplicated(subset=['Economy', 'Scenario', 'Date', 'Transport Type','Medium','road', 'Vehicle Type', 'Drive'], keep=False)]
    if len(new_sales_shares_concat_interp_dupes) > 0:
        raise Exception(f'ERROR: DUPLICATES IN NEW SALES SHARES CONCAT INTERP {new_sales_shares_concat_interp_dupes}')
    
    #order data by year
    new_sales_shares_concat_interp = new_sales_shares_pre_interp.sort_values(by=['Economy', 'Scenario', 'Date','road', 'Transport Type', 'Medium','Vehicle Type', 'Drive']).copy()
    
    new_sales_shares_concat_interp['Drive_share'] = new_sales_shares_concat_interp['Drive_share'].astype(float)#sometimes this needs to be set to float for some reason, otherwise the ouput will jsut be same as input
    if X_ORDER == 'linear':
        #do interpolation using spline and order = X
        
        new_sales_shares_concat_interp['Drive_share'] = new_sales_shares_concat_interp.groupby(['Economy', 'Scenario', 'Transport Type','Medium','road', 'Vehicle Type', 'Drive'], group_keys=False)['Drive_share'].apply(lambda group: group.interpolate(method='linear'))
    else:
        #do interpolation using spline and order = X
        
        new_sales_shares_concat_interp['Drive_share'] = new_sales_shares_concat_interp.groupby(['Economy', 'Scenario', 'Transport Type', 'Medium','road','Vehicle Type', 'Drive'])['Drive_share'].apply(lambda group: group.interpolate(method='spline', order=X_ORDER))
    
    #where any values are negatives or na just set them to 0
    new_sales_shares_concat_interp.loc[new_sales_shares_concat_interp['Drive_share'].isna(), 'Drive_share'] = 0
    new_sales_shares_concat_interp.loc[new_sales_shares_concat_interp['Drive_share']<0, 'Drive_share'] = 0
    
    #save the values at this point in time to use in the future if we need
    new_sales_shares_concat_interp.to_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_new_sales_shares_concat_interp.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
    
    #now we just need to normalise by vehicle type so that the drive share for each vehicle type sums to 1
    new_sales_shares_concat_interp['Drive_sum'] = new_sales_shares_concat_interp.groupby(['Economy', 'Scenario','road', 'Transport Type','Medium', 'Vehicle Type', 'Date'])['Drive_share'].transform('sum')

    new_sales_shares_concat_interp['Drive_share'] = new_sales_shares_concat_interp['Drive_share']/new_sales_shares_concat_interp['Drive_sum']
    
    #since we might have had div by 0's here, just set any nas to 0
    new_sales_shares_concat_interp.loc[new_sales_shares_concat_interp['Drive_share'].isna(), 'Drive_share'] = 0
    
    #Prepare sum of vehicle type share for each economy, scenario, transport type, vehicle type and date. THis will be used to normalise the drive share for each vehicle type
    new_sales_shares_interp_by_drive = new_sales_shares_concat_interp.drop(['Drive_sum'], axis=1).copy()
    original_new_sales_shares_by_vehicle = new_sales_shares_sum.drop(['Transport_type_share', 'Drive_share'], axis=1).copy()
    #ffill the vehicle type share sum col so that we can times it by the drive share for new years. currently 0 for all new years. we need it to be something, so we will at least ffill it with the latest available vehicle type share sum value
    # #first set all years where all values are 0 to nan so they can be filled too. Sorry this is a bit complicated, probably could be simplified.
    original_data_all_zero_years = original_new_sales_shares_by_vehicle.groupby(['Economy', 'Date','Transport Type','Scenario', 'road'])['Vehicle_type_share_sum'].apply(lambda group: group.sum()==0).reset_index().copy()
    original_data_all_zero_years = original_data_all_zero_years.loc[original_data_all_zero_years['Vehicle_type_share_sum']==True][['Economy', 'Date','Scenario','Transport Type', 'road']].drop_duplicates()
    original_data_all_zero_years['Vehicle_type_share_sum_nas'] = True
    original_new_sales_shares_by_vehicle = original_new_sales_shares_by_vehicle.merge(original_data_all_zero_years, on=['Economy','Scenario', 'Date','Transport Type', 'road'], how='left')
    original_new_sales_shares_by_vehicle['Vehicle_type_share_sum'] = np.where(original_new_sales_shares_by_vehicle['Vehicle_type_share_sum_nas']==True, np.nan, original_new_sales_shares_by_vehicle['Vehicle_type_share_sum'])
    #now sort by date then ffill the missing values
    original_new_sales_shares_by_vehicle = original_new_sales_shares_by_vehicle.sort_values(by=['Economy', 'Scenario', 'Date','road', 'Transport Type','Medium', 'Vehicle Type', 'Drive'])
    original_new_sales_shares_by_vehicle['Vehicle_type_share_sum'] = original_new_sales_shares_by_vehicle.groupby(['Economy', 'Scenario', 'Transport Type','Medium','road', 'Vehicle Type'], group_keys=False)['Vehicle_type_share_sum'].apply(lambda group: group.ffill())
    
    #If theres still any nas its because theres no data for that vehicle type at all. So we can just set these to 0. Note that this will cause all drive shares to be 0 for that vehicle type for all years, even after we apply vehicle type grwoth rates to hem, as theres nothing to grow from. So just to be safe, print and tell teh user
    if original_new_sales_shares_by_vehicle['Vehicle_type_share_sum'].isna().sum()>0:
        #identify unique economy and vehicle type combos that have no data
        combos = original_new_sales_shares_by_vehicle.loc[original_new_sales_shares_by_vehicle['Vehicle_type_share_sum'].isna()][['Economy', 'Vehicle Type']].drop_duplicates()
        print('WARNING: The following economy and vehicle type combos have no data. This means that the drive share for all drive types for these vehicle types will be 0 for all years. Please check the data and rerun the model if this is not what you want {}'.format(combos))
        #set nas to 0
        original_new_sales_shares_by_vehicle.loc[original_new_sales_shares_by_vehicle['Vehicle_type_share_sum'].isna(), 'Vehicle_type_share_sum'] = 0

    #now merge the values onto the oroginal df and times by the vehicle type shares
    new_sales_shares_all = new_sales_shares_interp_by_drive.merge(original_new_sales_shares_by_vehicle, on=['Economy', 'Scenario', 'Date', 'Transport Type', 'Vehicle Type', 'Medium','road','Drive'], how='left').copy()

    #times the values to get the final values so that they sum to 1 by transport type
    new_sales_shares_all['Transport_type_share'] = new_sales_shares_all['Vehicle_type_share_sum']*new_sales_shares_all['Drive_share']
    #set any nas to 0
    new_sales_shares_all.loc[new_sales_shares_all['Transport_type_share'].isna(), 'Transport_type_share'] = 0
    
    ################################################################################################################################################################
    #PLOT INTERPOLATED DATA
    ################################################################################################################################################################
    # 
    plotting = False
    
    if plotting:
        plot_user_input_data.plot_new_sales_shares(new_sales_shares_all,ECONOMY_ID)
    
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

    plotting = False
    if plotting:
        plot_user_input_data.plot_new_sales_shares_normalised_by_transport_type(new_sales_shares_all, new_sales_shares_sum,new_sales_shares_all_new)

    #check that the sumof transport type share is 1 for road=False, transport type = freight
    test = new_sales_shares_all_new.loc[(new_sales_shares_all_new['Economy']==ECONOMY_ID)&(new_sales_shares_all_new['road']==False)&(new_sales_shares_all_new['Transport Type']=='freight')&(new_sales_shares_all_new['Date']==2023)&(new_sales_shares_all_new['Scenario']=='Reference')].copy()
    if abs(1-test.Transport_type_share_new.sum()) > 0.0001:
        if ECONOMY_ID in ['02_BD', '17_SGP']:
            pass
        else:
            breakpoint()
            time.sleep(1)
            raise ValueError('The sum of the transport type share for {} road=False, transport type = freight, date = 2023 is not 1. Please check the user input data and fix this. Porbalby occuring for all econmoies and transport types'.format(ECONOMY_ID))

    #rename Transport_type_share_new to Vehicle^sales_share
    new_sales_shares_all_new = new_sales_shares_all_new.rename(columns={'Transport_type_share_new':'Vehicle_sales_share'})
    #drop cols
    new_sales_shares_all_new = new_sales_shares_all_new.drop(columns=[ 'Drive_share', 'Vehicle_type_share_sum',
        'Transport_type_share', 'Region', 'Growth', 'Compound_growth_rate','road','Vehicle_type_share_sum_nas'])
    #identify if there anre any dupes. there shoudltn be and they should be fixed rather than removed.
    dupes = new_sales_shares_all_new[new_sales_shares_all_new.duplicated()]
    if len(dupes) > 0:
        breakpoint()
        time.sleep(1)
        raise ValueError(f'There are duplicates in the new_sales_shares_all_new df. Please fix this. {dupes}')

    ###########################################################################
    
    #archive previous results:
    archiving_folder = transport_model_9th_edition.code.archiving_scripts.create_archiving_folder_for_FILE_DATE_ID()
    #save the variables we used to calculate the data by savinbg the 'input_data/vehicle_sales_share_inputs.xlsx' file
    shutil.copy('input_data/vehicle_sales_share_inputs.xlsx', archiving_folder + '/vehicle_sales_share_inputs.xlsx')

    
    #before saving data to user input spreadsheety we will do some formatting:
    #add cols for Unit,Medium,Data_available, frequency and Measure
    new_sales_shares_all_new['Unit'] = '%'
    new_sales_shares_all_new['Data_available'] = 'data_available'
    new_sales_shares_all_new['Measure'] = 'Vehicle_sales_share'
    new_sales_shares_all_new['Frequency'] = 'Yearly'
    #rename 'Vehicle_sales_share' to 'Value'
    new_sales_shares_all_new = new_sales_shares_all_new.rename(columns={'Vehicle_sales_share':'Value'})

    #final check before saving:
    a = new_sales_shares_all_new.loc[(new_sales_shares_all_new['Measure']=='Vehicle_sales_share') & (new_sales_shares_all_new['Transport Type']=='passenger') & (new_sales_shares_all_new['Date']==2023) & (new_sales_shares_all_new['Economy']==ECONOMY_ID) & (new_sales_shares_all_new['Scenario']=='Reference') &(new_sales_shares_all_new['Medium']=='road')].copy()
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
            
    #save data so it can be used for plotting and such:
    new_sales_shares_all_new.to_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_vehicle_sales_share.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index = False)
    return new_sales_shares_all_new



def estimate_transport_data_system_sales_share(ECONOMY_ID, new_transport_data_system_df, YEARS_TO_KEEP_AFTER_BASE_YEAR):
    
    sales = new_transport_data_system_df.copy()
    #filter for Stocks in Measutre
    sales = sales.loc[sales['Measure']=='Stocks']
    cols = config.INDEX_COLS.copy()
    cols = cols + ['road']#used for allowing swithicvn between non road mediums
    cols.remove('Medium')
    cols.remove('Vehicle Type')
    cols.remove('Drive')
    total_stocks = sales.copy()
    total_stocks = sales.groupby(cols)['Value'].sum().reset_index()
    total_stocks = total_stocks.rename(columns={'Value':'Total Stocks'})
    sales = sales.merge(total_stocks, on=cols, how='left')
    sales['Sales Share'] = sales['Value']/sales['Total Stocks']
    #set measure to 'Vehicle_sales_share'
    sales['Measure'] = 'Vehicle_sales_share'
    sales['Unit'] = '%'
    #repalce nan with 0
    sales = sales.fillna(0)
    #now we want to find the year with the most values that arent 0. this is essentially the year with the most data and is therefor emost suitable to abse our sales shares off (data with less values may be missing values and tehrefore exaggerating sales share fr certain vehicle types)
    #we will do this by grouping by year and counting the number of non zero values. then we will sort by this count and take the year with the most non zero values
    # making an update to make this identify the year with most values by transport type and economy (rather than just date), so we can have more flexibility:
    year_with_most_values = sales.dropna().loc[sales['Value']>=0.0001].groupby(['Date', 'Economy', 'road','Transport Type'])['Value'].count().reset_index()
    #filter for max count for each economy and transport type:
    for economy in year_with_most_values.Economy.unique():
        for transport_type in year_with_most_values['Transport Type'].unique():
            for road_bool in year_with_most_values.road.unique():
                    
                max_count = year_with_most_values.loc[(year_with_most_values['Economy']==economy)&(year_with_most_values['Transport Type']==transport_type)&(year_with_most_values['road']==road_bool)]['Value'].max()
                #drop rows without the max count
                year_with_most_values = year_with_most_values.loc[~((year_with_most_values['Economy']==economy)&(year_with_most_values['Transport Type']==transport_type)&(year_with_most_values['Value']!=max_count)&(year_with_most_values['road']==road_bool))]
                #also keep only the maximum date of these
                max_date = year_with_most_values.loc[(year_with_most_values['Economy']==economy)&(year_with_most_values['Transport Type']==transport_type)&(year_with_most_values['road']==road_bool)]['Date'].max()
                year_with_most_values = year_with_most_values.loc[~((year_with_most_values['Economy']==economy)&(year_with_most_values['Transport Type']==transport_type)&(year_with_most_values['Date']!=max_date)&(year_with_most_values['road']==road_bool))]
    
    #drop value
    year_with_most_values = year_with_most_values.drop(columns=['Value'])                 
    #join to sales and keep only the rows with the max year
    sales = sales.merge(year_with_most_values, on=['Economy', 'Transport Type', 'Date', 'road'], how='inner')
    # #filter for the year with the most values
    # sales = sales.loc[sales['Date']==max_year]
    plotting = False
    if plotting:
        plot_user_input_data.plot_estimated_data_system_sales_share(sales,ECONOMY_ID, YEARS_TO_KEEP_AFTER_BASE_YEAR)
        
    #drop Total Stocks column and Value column
    sales = sales.drop(columns=['Total Stocks', 'Value'])

    #now replicate the sales shares for each scenario and for each year between the config.DEFAULT_BASE_YEAR and the config.END_YEAR of the scenario.

    #filter for a unique scenario in the sales df
    sales = sales[sales.Scenario==sales.Scenario.unique()[0]]
    sales_dummy = sales.copy()
    new_sales = pd.DataFrame()
    for scenario in config.SCENARIOS_LIST:
        sales_dummy['Scenario'] = scenario
        new_sales = pd.concat([new_sales, sales_dummy])
    
    #now we want to replicate the df (BUT NOT THE SALES SHARE) for each year between the config.DEFAULT_BASE_YEAR and the config.END_YEAR of the scenario
    sales_dummy = new_sales.copy()
    new_sales_years = pd.DataFrame()
    for year in range(config.DEFAULT_BASE_YEAR, config.END_YEAR+1):
        sales_dummy['Date'] = year
        new_sales_years = pd.concat([new_sales_years, sales_dummy])
    
    #set sales share for all values after config.DEFAULT_BASE_YEAR+YEARS_TO_KEEP_AFTER_BASE_YEAR to np.nan (add three so that we still have a few values for the interpoaltion to go off)
    new_sales_years.loc[new_sales_years['Date']>config.DEFAULT_BASE_YEAR+YEARS_TO_KEEP_AFTER_BASE_YEAR, 'Sales Share'] = np.nan
    
    return new_sales_years


def estimate_transport_data_system_sales_share_using_share_of_activity(ECONOMY_ID, new_transport_data_system_df, YEARS_TO_KEEP_AFTER_BASE_YEAR,SET_YEAR_WITH_MOST_VALUES_TO_BASE_YEAR):
    """since vehicle sales share is really the share of new actiivty taken up by that vehicle and drive type within its transport type (rahter than sshare of new stocks, since stocks use a different amount of acitvity based on their vehicle type), we will estimate it by taking the share of transport type activity for each vehicle and drive type and then normalising it to 1. This will be done for each year and each scenario.
    
    """
    sales = new_transport_data_system_df.copy()
    #calcualte activity
    sales = sales.loc[sales['Measure'].isin(['Occupancy_or_load', 'Mileage','Stocks'])]
    index_cols_no_measure = config.INDEX_COLS.copy()
    index_cols_no_measure.remove('Measure')
    index_cols_no_measure.remove('Unit')
    index_cols_no_measure = index_cols_no_measure + ['road']
    sales = sales.pivot(index =index_cols_no_measure, columns = 'Measure', values = 'Value').reset_index()
    #wre road is true, clacualte activity and call it Value so it can be used later. where road is false, set activity as stocks, since this is what it originally was anyway (i.e. activity is stocks for non road)
    sales['Value'] = np.where(sales['road']==True, sales['Mileage'] * sales['Occupancy_or_load']* sales['Stocks'], sales['Stocks'])
    sales = sales.drop(columns=['Mileage', 'Occupancy_or_load', 'Stocks'])
    #calcualte share of activity
    EPSILON = 1e-9

    sales['Sales Share'] = sales.groupby(['Economy', 'Scenario', 'Date', 'Transport Type','road'])['Value'].transform(lambda x: x / (x.sum() + EPSILON))
    
    #set measure to 'Vehicle_sales_share'
    sales['Measure'] = 'Vehicle_sales_share'
    sales['Unit'] = '%'
    #repalce nan with 0
    sales = sales.fillna(0)
    
    #now we want to find the year with the most values that arent 0. this is essentially the year with the most data and is therefor emost suitable to abse our sales shares off (data with less values may be missing values and tehrefore exaggerating sales share fr certain vehicle types)
    #we will do this by grouping by year and counting the number of non zero values. then we will sort by this count and take the year with the most non zero values
    # making an update to make this identify the year with most values by transport type and economy (rather than just date), so we can have more flexibility:
    year_with_most_values = sales.loc[sales['Value']>0.].groupby(['Date', 'Economy', 'road','Transport Type'])['Value'].count().reset_index()
    #filter for max count for each economy and transport type:
    for economy in year_with_most_values.Economy.unique():
        for transport_type in year_with_most_values['Transport Type'].unique():
            for road_bool in year_with_most_values.road.unique():
                
                if not SET_YEAR_WITH_MOST_VALUES_TO_BASE_YEAR:
                    max_count = year_with_most_values.loc[(year_with_most_values['Economy']==economy)&(year_with_most_values['Transport Type']==transport_type)&(year_with_most_values['road']==road_bool)]['Value'].max()
                    #drop rows without the max count
                    year_with_most_values = year_with_most_values.loc[~((year_with_most_values['Economy']==economy)&(year_with_most_values['Transport Type']==transport_type)&(year_with_most_values['Value']!=max_count)&(year_with_most_values['road']==road_bool))]
                    
                    #also keep only the maximum date of these
                    max_date = year_with_most_values.loc[(year_with_most_values['Economy']==economy)&(year_with_most_values['Transport Type']==transport_type)&(year_with_most_values['road']==road_bool)]['Date'].max()
                
                else:
                    max_date = config.OUTLOOK_BASE_YEAR
                    
                year_with_most_values = year_with_most_values.loc[~((year_with_most_values['Economy']==economy)&(year_with_most_values['Transport Type']==transport_type)&(year_with_most_values['Date']!=max_date)&(year_with_most_values['road']==road_bool))]
    
    #drop value
    year_with_most_values = year_with_most_values.drop(columns=['Value'])                 
    #join to sales and keep only the rows with the max year
    sales = sales.merge(year_with_most_values, on=['Economy', 'Transport Type', 'Date', 'road'], how='inner')
    # #filter for the year with the most values
    # sales = sales.loc[sales['Date']==max_year]
    plotting = False
    if plotting:
        plot_user_input_data.plot_estimated_data_system_sales_share(sales,ECONOMY_ID, YEARS_TO_KEEP_AFTER_BASE_YEAR)
    
    #drop Total Stocks column and Value column
    sales = sales.drop(columns=['Value'])

    #now replicate the sales shares for each scenario and for each year between the config.DEFAULT_BASE_YEAR and the config.END_YEAR of the scenario.
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
    
    #now we want to replicate the df (BUT NOT THE SALES SHARE) for each year between the config.DEFAULT_BASE_YEAR and the config.END_YEAR of the scenario
    sales_dummy = new_sales.copy()
    new_sales_years = pd.DataFrame()
    for year in range(config.DEFAULT_BASE_YEAR, config.END_YEAR+1):
        sales_dummy['Date'] = year
        new_sales_years = pd.concat([new_sales_years, sales_dummy])
    
    #set sales share for all values after config.DEFAULT_BASE_YEAR+YEARS_TO_KEEP_AFTER_BASE_YEAR to np.nan (add three so that we still have a few values for the interpoaltion to go off)
    new_sales_years.loc[new_sales_years['Date']>config.DEFAULT_BASE_YEAR+YEARS_TO_KEEP_AFTER_BASE_YEAR, 'Sales Share'] = np.nan

    #set unit to %
    new_sales_years['Unit'] = '%'
    
    return new_sales_years

def calcaulte_missing_drive_shares_from_manually_inputted_data(new_sales_shares_pre_interp, model_concordances_user_input_and_growth_rates, passenger_drive_shares, freight_drive_shares,YEARS_TO_KEEP_AFTER_BASE_YEAR):
    #we are now only taking in data from the most important drives, to reduce the amount of time we need to spend manually writing out the drive share targets. So the follwoign funciton should take in those targets and the Base year data, and calcualte the remaining drive shares for the missing drives using the base year data's shares as a reference. 
    #the base year datas shares, for the missing drives, will be normalised to 1 so we can just times them by 1-x where x is the sum of the manully inputted shares, in each year we ahve them for. In missing years (the years we will interpoalte later), we will leave all as nan, so that we can interpolate between the values we have set and the base year values.
    #the input files for this will be:
    #new_sales_shares_pre_interp (which contains the base year data and the manually inputted data - whjich we will split at the beginning)
    #model_concordances_user_input_and_growth_rates (which contaions the set of drives, vehicle types and transport types we need to set the drive shares for)
    #passenger_drive_shares and freight_drive_shares (which only contain the manually inputted data > we will sue this to extract the data we want from new_sales_shares_pre_interp)
    #so first we need to split new_sales_shares_pre_interp into the base year data and the manually inputted data
    #QUICK FIX:
    #BECAUSE WE SOMETIMES HAVE INPUT DATA FOR YEARS NOT IN DEFAULT BASE YEAR AND NO DATA FOR BASE YEAR, WHICH IS CAUSING THE SCRIPTS TO ASUSME THERE ARE NO STOCKS OR SALES OF THAT ROW AT ALL, WE WILL GRAB SALES SHARES FOR ALL YEARS BETWEEN config.DEFAULT_BASE_YEAR AND config.OUTLOOK_BASE_YEAR
    # 
    # sales_share_BASE_YEAR = new_sales_shares_pre_interp.loc[new_sales_shares_pre_interp['Date'].isin(range(config.DEFAULT_BASE_YEAR, config.OUTLOOK_BASE_YEAR+1))]
    # #set nas to 0
    # sales_share_BASE_YEAR = sales_share_BASE_YEAR.fillna(0)
    # #sum so we ignore the date:
    # sales_share_BASE_YEAR = sales_share_BASE_YEAR.groupby(['Economy', 'Scenario', 'Transport Type','Medium','road', 'Vehicle Type', 'Drive']).sum().reset_index()
    sales_share_BASE_YEAR = new_sales_shares_pre_interp.loc[new_sales_shares_pre_interp['Date']==config.DEFAULT_BASE_YEAR].dropna(subset=['Drive_share'])
    
    sales_share_manual_input = new_sales_shares_pre_interp.loc[new_sales_shares_pre_interp['Date']>config.DEFAULT_BASE_YEAR+YEARS_TO_KEEP_AFTER_BASE_YEAR].dropna(subset=['Drive_share'])
    #extract unique drives, vehicle types and transport types from model_concordances_user_input_and_growth_rates
    # combinations = model_concordances_user_input_and_growth_rates[['Medium','Transport Type','road', 'Vehicle Type', 'Drive']].drop_duplicates()
    #find unique combiantions in passenger_drive_shares and freight_drive_shares
    p = passenger_drive_shares[['Medium','Vehicle Type','road', 'Drive']].drop_duplicates()
    p['Transport Type'] = 'passenger'
    f = freight_drive_shares[['Medium','Vehicle Type','road', 'Drive']].drop_duplicates()
    f['Transport Type'] = 'freight'
    combinations_manual_input = pd.concat([p , f])
    #dropo the combinations in sales_share_manual_input from sales_share_BASE_YEAR
    sales_share_BASE_YEAR = sales_share_BASE_YEAR[~sales_share_BASE_YEAR[['Transport Type', 'Medium','Vehicle Type','road', 'Drive']].apply(tuple,1).isin(combinations_manual_input[['Transport Type', 'road','Medium','Vehicle Type', 'Drive']].apply(tuple,1))]

    #set nas in drive share to 0
    sales_share_BASE_YEAR[ 'Drive_share'] = sales_share_BASE_YEAR[ 'Drive_share'].fillna(0)
    #find the normalised shares for the available data in the base year data
    sales_share_BASE_YEAR['Drive_share'] = sales_share_BASE_YEAR.groupby(['Economy', 'Scenario', 'Transport Type', 'road','Medium','Vehicle Type'])['Drive_share'].transform(lambda x: x/x.sum())
    #set nas in drive share to 0
    sales_share_BASE_YEAR[ 'Drive_share'] = sales_share_BASE_YEAR[ 'Drive_share'].fillna(0)
    #now get sum of manually inputted shares for each year
    sales_share_manual_input_sum = sales_share_manual_input.groupby(['Economy', 'Scenario', 'Transport Type','Medium','road', 'Vehicle Type', 'Date'])['Drive_share'].sum().reset_index()
    #1 minus it
    sales_share_manual_input_sum['Drive_share_remainder'] = 1 - sales_share_manual_input_sum['Drive_share']
    #drop drive share
    sales_share_manual_input_sum = sales_share_manual_input_sum.drop(columns=['Drive_share'])
    #chcke for any values les than 0
    if sales_share_manual_input_sum['Drive_share_remainder'].min() < 0:
        #show them and raise
        print(sales_share_manual_input_sum.loc[sales_share_manual_input_sum['Drive_share_remainder']<0])
        raise ValueError('Drive share remainder is less than 0')
    #join this to the base year data using right join
    missing_sales_shares = sales_share_BASE_YEAR[['Economy', 'Scenario', 'Transport Type','Medium', 'Vehicle Type','Drive', 'road','Drive_share']].merge(sales_share_manual_input_sum, on=['Economy','road', 'Scenario', 'Medium','Transport Type', 'Vehicle Type'], how='right')
    #times the base year data by the 1-x
    missing_sales_shares['Drive_share'] = missing_sales_shares['Drive_share'] * missing_sales_shares['Drive_share_remainder']

    #now we need to insert these rows into the  new_sales_shares_pre_interp, rmeoving their original rows (which will be nas.) so do a join and then repalce drive share with the new drive share where it is not na
    final_df = new_sales_shares_pre_interp.merge(missing_sales_shares, on=['Economy', 'Scenario','Medium', 'Transport Type','road', 'Vehicle Type','Date', 'Drive'], how='left', suffixes=('', '_y'))
    #want to replace the drive share with the new drive share where it is na (replacing nas with nas too.)
    final_df['Drive_share'] = final_df['Drive_share'].fillna(final_df['Drive_share_y'])
    #drop the y cols
    final_df = final_df.drop(columns=['Drive_share_y', 'Drive_share_remainder'])

    return final_df


#%%
# a = create_vehicle_sales_share_input('02_BD', RECALCULATE_SALES_SHARES_USING_RECALCULATED_INPUT_DATA=True)

# create_vehicle_sales_share_input('20_USA', RECALCULATE_SALES_SHARES_USING_RECALCULATED_INPUT_DATA=False)
#%%