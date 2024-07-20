#this file is intended to help with creating a set of 'concordances' which as i see it are blueprints of exactly what data for what categories we need for the model. Perhaps concordances are teh wrong name but for now we use that (can replace-all later).

#teh concordances are useful for systematically defining what data we need and what data we have. They are also useful for understanding exactly what to call different categories in teh data.

#One issue is that the process requires the model and data preparation to be run to create the concordances which use the inputs into the model. This is because they use the inputs to easily determine what measures were used. So if the user defines a new set of measures then at minimum they will need to create some dummy data and edit the code to use that dummy data. 


#tghe concordances created, in order are:
#model_concordances_fuels
#model_concordances_measures
#model_concordances_user_input_and_growth_rates
#model_concordances_demand_side_fuel_mixing
#model_concordances_supply_side_fuel_mixing
#model_concordances_all

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


################################################################################################################################################################


#PLEASE NOTE THAT ALL MODEL CONCORDANCE FILE NAMES VARIABLES ARE STORED AND SET IN ./code/config.py


################################################################################################################################################################

def create_all_concordances(config, USE_LATEST_CONCORDANCES=False):
    #create set of categories of data that will be output by the model. 
    #update this with the transport categories you want to use in the transport model and they should flow through so that the inputs and outputs of the model need to be like that.
    if check_for_and_save_previous_concordances(config, USE_LATEST_CONCORDANCES):
        return
    manually_defined_transport_categories = pd.read_csv(os.path.join(config.root_dir,  'config', 'concordances_and_config_data', 'manually_defined_transport_categories.csv'))
            
    #drop duplicates
    manually_defined_transport_categories.drop_duplicates(inplace=True)

    #could create concordances for each year, economy and scenario and then cross that with the osemosys_concordances to get the final concordances
    model_concordances = pd.DataFrame(columns=manually_defined_transport_categories.columns)
    for Date in range(config.DEFAULT_BASE_YEAR, config.END_YEAR+1):
        for economy in config.ECONOMY_LIST:#get economys from economy_code_to_name concordance in config.py
            for scenario in config.SCENARIOS_LIST:
                #create concordances for each year, economy and scenario
                manually_defined_transport_categories_year = manually_defined_transport_categories.copy()
                manually_defined_transport_categories_year['Date'] = int(Date)
                manually_defined_transport_categories_year['Economy'] = economy
                manually_defined_transport_categories_year['Scenario'] = scenario
                #merge with manually_defined_transport_categories_year
                model_concordances = pd.concat([model_concordances, manually_defined_transport_categories_year])

    #convert year to int
    model_concordances['Date'] = model_concordances['Date'].astype(int)
    #create 'Frequency col which is set to 'Yearly'
    model_concordances['Frequency'] = 'Yearly'
    #save model_concordances with date
    #check the folder exists
    # if not os.path.exists(os.path.join(config.root_dir,  'config', 'concordances_and_config_data', 'computer_generated_concordances')):
        # os.makedirs('config', 'concordances_and_config_data', 'computer_generated_concordances')
    model_concordances.to_csv(os.path.join(config.root_dir,  'intermediate_data', 'computer_generated_concordances', '{}'.format(config.model_concordances_file_name)), index=False)

    ################################################################################################################################################################
    
    #create model concordances with a fuel column. 
    model_concordances_fuels = model_concordances.copy()
    model_concordances_fuels_NO_BIOFUELS = model_concordances.copy()

    #thsi is important to keep up to date because it will be used to create the user input spreadsheet for the demand side fuel mixing (involving removing the biofuels as they will be stated in the supply sdide fuel mixing)
    #load csv of drive_type_to_fuel
    drive_type_to_fuel_df = pd.read_csv(os.path.join(config.root_dir,  'config', 'concordances_and_config_data', 'drive_type_to_fuel.csv'))

    #make a version of the df with no biofuels
    drive_type_to_fuel_df_NO_BIOFUELS = drive_type_to_fuel_df[~drive_type_to_fuel_df['Fuel'].str.contains('bio')]

    #merge the dict to our model concordances
    model_concordances_fuels = pd.merge(model_concordances_fuels, drive_type_to_fuel_df, how='left', on=['Drive'])

    model_concordances_fuels_NO_BIOFUELS = pd.merge(model_concordances_fuels_NO_BIOFUELS, drive_type_to_fuel_df_NO_BIOFUELS, how='left', on=['Drive'])

    #save
    model_concordances_fuels.to_csv(os.path.join(config.root_dir,  'intermediate_data', 'computer_generated_concordances', '{}'.format(config.model_concordances_file_name_fuels)), index=False)
    model_concordances_fuels_NO_BIOFUELS.to_csv(os.path.join(config.root_dir,  'intermediate_data', 'computer_generated_concordances', '{}'.format(config.model_concordances_file_name_fuels_NO_BIOFUELS)), index=False)

    ########################################################################################################################################################################
    
    #now for each measure create a copy of the model concordance for that medium and the base year only and add the measure to the copy (where non road is all non road mediums)
    BASE_YEAR_model_concordances_ROAD = model_concordances.loc[(model_concordances['Medium'] == 'road') & (model_concordances['Date'] == config.DEFAULT_BASE_YEAR)].drop(columns=['Scenario']).drop_duplicates()
    BASE_YEAR_model_concordances_NON_ROAD = model_concordances.loc[(model_concordances['Medium'] != 'road') & (model_concordances['Date'] == config.DEFAULT_BASE_YEAR)].drop(columns=['Scenario']).drop_duplicates()

    #create empty dataframes
    BASE_YEAR_non_road_measures = pd.DataFrame()
    BASE_YEAR_road_measures = pd.DataFrame()

    for measure in config.base_year_measures_list_ROAD:
        BASE_YEAR_model_concordances_ROAD_copy = BASE_YEAR_model_concordances_ROAD.copy()
        BASE_YEAR_model_concordances_ROAD_copy['Measure'] = measure
        BASE_YEAR_road_measures = pd.concat([BASE_YEAR_road_measures, BASE_YEAR_model_concordances_ROAD_copy])  

    for measure in config.base_year_measures_list_NON_ROAD:
        BASE_YEAR_model_concordances_NON_ROAD_copy = BASE_YEAR_model_concordances_NON_ROAD.copy()
        BASE_YEAR_model_concordances_NON_ROAD_copy['Measure'] = measure
        BASE_YEAR_non_road_measures = pd.concat([BASE_YEAR_non_road_measures, BASE_YEAR_model_concordances_NON_ROAD_copy])

    #join the two dfs using concat
    model_concordances_BASE_YEAR_measures = pd.concat([BASE_YEAR_road_measures, BASE_YEAR_non_road_measures])
    
    #Measure to Unit concordance (load it in and merge it to the model concordances)
    #keep only Measure and Unit columns
    measure_to_unit_concordance_copy = config.measure_to_unit_concordance[['Measure', 'Unit']].copy()

    #merge the dict to our model concordances
    model_concordances_BASE_YEAR_measures = model_concordances_BASE_YEAR_measures.merge(measure_to_unit_concordance_copy, how='left', on=['Measure'])
    
    # #TEMP
    # #where measure is Occupancy_growth, remove rows where transport type is freight
    # model_concordances_BASE_YEAR_measures = model_concordances_BASE_YEAR_measures[~((model_concordances_BASE_YEAR_measures['Measure'] == 'Occupancy') & (model_concordances_BASE_YEAR_measures['Transport Type'] == 'freight'))]
    # #and measure is Load_growth, remove rows where transport type is passenger
    # model_concordances_BASE_YEAR_measures = model_concordances_BASE_YEAR_measures[~((model_concordances_BASE_YEAR_measures['Measure'] == 'Load') & (model_concordances_BASE_YEAR_measures['Transport Type'] == 'passenger'))]

    # #Remove cases so we dont have passenger_km measure where the transport type is freight and vice versa for freight_tonne_km
    # model_concordances_BASE_YEAR_measures = model_concordances_BASE_YEAR_measures[~((model_concordances_BASE_YEAR_measures['Measure'] == 'passenger_km') & (model_concordances_BASE_YEAR_measures['Transport Type'] == 'freight'))]
    # model_concordances_BASE_YEAR_measures = model_concordances_BASE_YEAR_measures[~((model_concordances_BASE_YEAR_measures['Measure'] == 'freight_tonne_km') & (model_concordances_BASE_YEAR_measures['Transport Type'] == 'passenger'))]
    # #TEMP Over
    
    #now save
    model_concordances_BASE_YEAR_measures.to_csv(os.path.join(config.root_dir,  'intermediate_data', 'computer_generated_concordances', '{}'.format(config.model_concordances_base_year_measures_file_name)), index=False)

    ########################################################################################################################################################################
    #create a model concordance for growth rates and user defined inputs 

    #now for each measure create a copy of the model concordance for that medium and add the measure to the copy (where non road is all non road mediums)
    model_concordances_ROAD = model_concordances[model_concordances['Medium'] == 'road']
    model_concordances_NON_ROAD = model_concordances[model_concordances['Medium'] != 'road']
    #create empty dataframes
    non_road_user_input_and_growth_rates = pd.DataFrame()
    road_user_input_and_growth_rates = pd.DataFrame()

    for measure in config.user_input_measures_list_ROAD:
        model_concordances_ROAD_copy = model_concordances_ROAD.copy()
        model_concordances_ROAD_copy['Measure'] = measure
        road_user_input_and_growth_rates = pd.concat([road_user_input_and_growth_rates, model_concordances_ROAD_copy])  
    for measure in config.user_input_measures_list_NON_ROAD:
        model_concordances_NON_ROAD_copy = model_concordances_NON_ROAD.copy()
        model_concordances_NON_ROAD_copy['Measure'] = measure
        non_road_user_input_and_growth_rates = pd.concat([non_road_user_input_and_growth_rates, model_concordances_NON_ROAD_copy])

    

    #join the two dfs using concat
    model_concordances_user_input_and_growth_rates = pd.concat([non_road_user_input_and_growth_rates, road_user_input_and_growth_rates], ignore_index=True)
    #remove the BASE year as we don't need it. 
    model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates[model_concordances_user_input_and_growth_rates['Date'] != config.DEFAULT_BASE_YEAR]
    #make units = %
    model_concordances_user_input_and_growth_rates['Unit'] = '%'
    #where the measure is Stocks_per_capita then set unit to Stocks_per_thousand_capita
    model_concordances_user_input_and_growth_rates.loc[model_concordances_user_input_and_growth_rates['Measure'] == 'Stocks_per_capita', 'Unit'] = 'Stocks_per_thousand_capita'
    #and drop freight  from it
    model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates[~((model_concordances_user_input_and_growth_rates['Measure'] == 'Stocks_per_capita') & (model_concordances_user_input_and_growth_rates['Transport Type'] == 'freight'))]
    
    # #where measure is Occupancy_growth, remove rows where transport type is freight
    # model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates[~((model_concordances_user_input_and_growth_rates['Measure'] == 'Occupancy_growth') & (model_concordances_user_input_and_growth_rates['Transport Type'] == 'freight'))]
    # #and measure is Load_growth, remove rows where transport type is passenger
    # model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates[~((model_concordances_user_input_and_growth_rates['Measure'] == 'Load_growth') & (model_concordances_user_input_and_growth_rates['Transport Type'] == 'passenger'))]

    ##########################

    # #SETUP TEMP FIX FOR GOMEPRTZ PARAMETERS:
    # #since these use a bit different conventions we will treat them uniquely.
    # ##set medium to road, vehicle type to all, transport type to passenger and freight, unit to Parameter and drive to all
    # #first filter for where measure startswith Gompertz
    model_concordances_GOMPERTZ = model_concordances_user_input_and_growth_rates[model_concordances_user_input_and_growth_rates['Measure'].str.startswith('Gompertz')]
    model_concordances_user_input_and_growth_rates = model_concordances_user_input_and_growth_rates[~(model_concordances_user_input_and_growth_rates['Measure'].str.startswith('Gompertz'))]
    model_concordances_GOMPERTZ['Medium'] = 'road'
    model_concordances_GOMPERTZ['Vehicle Type'] = 'all'
    model_concordances_GOMPERTZ['Unit'] = 'Parameter'
    model_concordances_GOMPERTZ['Drive'] = 'all'
    
    
    model_concordances_GOMPERTZ_p = model_concordances_GOMPERTZ.copy()
    model_concordances_GOMPERTZ_p['Transport Type'] = 'passenger'
    model_concordances_GOMPERTZ_f = model_concordances_GOMPERTZ.copy()
    model_concordances_GOMPERTZ_f['Transport Type'] = 'freight'
    
    #drop duplicates
    model_concordances_GOMPERTZ_p.drop_duplicates(inplace=True)
    model_concordances_GOMPERTZ_f.drop_duplicates(inplace=True)
    #now add to the road_user_input_and_growth_rates df
    model_concordances_user_input_and_growth_rates = pd.concat([model_concordances_user_input_and_growth_rates, model_concordances_GOMPERTZ_p, model_concordances_GOMPERTZ_f], ignore_index=True)

    ##########################
    #now save
    
    model_concordances_user_input_and_growth_rates.to_csv(os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', config.model_concordances_user_input_and_growth_rates_file_name), index=False)

    #run create_fuel_mixing_concordances(config) to create the fuel mixing concordances. It is seperate because occasionally it will need to be done right after creating new fuel mixing inputs
    create_fuel_mixing_concordances(config, model_concordances_fuels)

    
########################################################################################################################################################

#create concordances for fuel mixxing measures. These are kept separate from the others because the tables they are in are different. this is from inputs into the model
def create_fuel_mixing_concordances(config, model_concordances_fuels):
    #load drive_type_to_fuel and use the fuel mixing vcolumns to idenitfy what fuels should be mixed together and whether they are original or new fuels, also whether they are on the demand and/or supply side., The belwo are just simeple examples of what the data looks like. The actual data is in the drive_type_to_fuel.csv file
    # Drive	Fuel	Supply_side_fuel_mixing	Demand_side_fuel_mixing
    # rail_coal	01_coal	FALSE	FALSE
    # air_gasoline	07_01_motor_gasoline	Original fuel	FALSE
    # air_lpg	16_01_biogas	New fuel	FALSE
    # phev_d	17_electricity	FALSE	New fuel
    # phev_d	07_07_gas_diesel_oil	Original fuel	Original fuel

    #Then we will format the result to be like (DEMAND SIDE):
    #     Date	Economy	Vehicle Type	Medium	Transport Type	Drive	Scenario	Frequency	Fuel	Demand_side_fuel_share
    # 2017	01_AUS	bus	road	passenger	phev_d	Reference	Yearly	07_07_gas_diesel_oil	0.5
    #OR supply side:
    #     Medium	Transport Type	Vehicle Type	Drive	Date	Economy	Scenario	Frequency	Fuel	New_fuel	Supply_side_fuel_share
    # air	freight	all	air_av_gas	2017	01_AUS	Reference	Yearly	07_02_aviation_gasoline	16_07_bio_jet_kerosene	0
    
    drive_type_to_fuel_df = pd.read_csv(os.path.join(config.root_dir, 'config', 'concordances_and_config_data', 'drive_type_to_fuel.csv'))
    
    #load in concordances and then keep only data that is in the drive_type_to_fuel_df:
    
    # model_concordances_fuels = pd.read_csv(os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', config.model_concordances_file_name_fuels))
    
    #first do demand side fuel mixing:
    drive_type_to_fuel_df_demand = drive_type_to_fuel_df[drive_type_to_fuel_df['Demand_side_fuel_mixing'].isin(['Original fuel', 'New fuel'])].copy()
    #drop Demand_side_fuel_mixing and Supply_side_fuel_mixing cols
    drive_type_to_fuel_df_demand.drop(columns=['Demand_side_fuel_mixing', 'Supply_side_fuel_mixing'], inplace=True)
    #since Demand side fuel mixing doesnt have a 'new fuel' column, we dont have to worrry about that.
    demand = model_concordances_fuels.merge(drive_type_to_fuel_df_demand, how='outer', on=['Drive', 'Fuel'], indicator=True)
    #if theres any indicators for right only, throw an error, since that means there are fuels in the drive_type_to_fuel_df that are not in the model_concordances_fuels
    if (demand['_merge'] == 'right_only').any():
        breakpoint()
        missing = demand[demand['_merge'] == 'right_only']['Drive'].unique()
        raise ValueError('There are fuels in the drive_type_to_fuel_df that are not in the model_concordances_fuels. Please check the drive_type_to_fuel_df and model_concordances_fuels - note this could be because you should add the rows manually (unfortunately) to model_concordances_fuels. {}'.format(missing))
    #drop any cases where indicator isnt both
    demand = demand[demand['_merge'] == 'both'].copy()
    #drop the indicator col
    demand.drop(columns=['_merge'], inplace=True)
    #set unit to %
    demand['Unit'] = '%'
    demand['Measure'] = 'Demand_side_fuel_share'
    #if any dupes thorw an error
    if demand.duplicated().any():
        breakpoint()
        raise ValueError('There are duplicates in the demand side fuel mixing. Please check the drive_type_to_fuel_df and model_concordances_fuels')
    
    #do supply side fuel mixing:
    drive_type_to_fuel_df_supply = drive_type_to_fuel_df[drive_type_to_fuel_df['Supply_side_fuel_mixing'].isin(['Original fuel', 'New fuel'])].copy()
    #make the df so we have col for each original fuel and its corresponding new fuel (no original fuel should have moire than one new fuel). So we'll sep the df into two, one for original fuels and one for new fuels, then merge them together
    new = drive_type_to_fuel_df_supply[drive_type_to_fuel_df_supply['Supply_side_fuel_mixing'] == 'New fuel'].copy()
    #name the fuel col to New_fuel
    new = new.rename(columns={'Fuel': 'New_fuel'})
    old = drive_type_to_fuel_df_supply[drive_type_to_fuel_df_supply['Supply_side_fuel_mixing'] == 'Original fuel'].copy()
    #drop Demand_side_fuel_mixing and Supply_side_fuel_mixing cols
    new.drop(columns=['Demand_side_fuel_mixing', 'Supply_side_fuel_mixing'], inplace=True)
    old.drop(columns=['Demand_side_fuel_mixing', 'Supply_side_fuel_mixing'], inplace=True)
    supply = old.merge(new, how='outer', on=['Drive'], indicator=True)
    #if theres any indicators that arent both, throw an error
    if (supply['_merge'] != 'both').any():
        breakpoint()
        missing = supply[supply['_merge'] != 'both']['Drive'].unique()
        raise ValueError('There are fuels in the drive_type_to_fuel_df that are not in the model_concordances_fuels. Please check the drive_type_to_fuel_df and model_concordances_fuels - note this could be because you should add the rows manually (unfortunately) to model_concordances_fuels: {}'.format(missing))
    #drop _merge col
    supply.drop(columns=['_merge'], inplace=True)
    #now we can merge the supply df with the model_concordances_fuels df on the Drive and Fuel cols
    supply = model_concordances_fuels.merge(supply, how='outer', on=['Drive', 'Fuel'], indicator=True)
    
    #if theres any indicators that are right_only, throw an error since that means there are drive fuel combos in the drive_type_to_fuel_df that are not in the model_concordances_fuels
    if (supply['_merge'] == 'right_only').any():
        
        raise ValueError('There are fuels in the drive_type_to_fuel_df that are not in the model_concordances_fuels. Please check the drive_type_to_fuel_df and model_concordances_fuels')
    #keep only cases where the indicator is both
    supply = supply[supply['_merge'] == 'both'].copy()
    #drop _merge col
    supply.drop(columns=['_merge'], inplace=True)
    #set unit to %
    supply['Unit'] = '%'
    supply['Measure'] = 'Supply_side_fuel_share'
    #if any dupes thorw an error
    if supply.duplicated().any():
        raise ValueError('There are duplicates in the supply side fuel mixing. Please check the drive_type_to_fuel_df and model_concordances_fuels')

    #save
    demand.to_csv(os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', config.model_concordances_demand_side_fuel_mixing_file_name), index=False)
    supply.to_csv(os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', config.model_concordances_supply_side_fuel_mixing_file_name), index=False)


def check_for_and_save_previous_concordances(config, USE_LATEST_CONCORDANCES):
    if USE_LATEST_CONCORDANCES:
        #check if we have concordances available to copy to save on time:
        file_date_id = utility_functions.get_latest_date_for_data_file(os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances'), 'model_concordances_', file_name_end='.csv')
        if file_date_id == config.FILE_DATE_ID:
            #check for all the oqther concordances
            if os.path.exists(os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', config.model_concordances_file_name)) and os.path.exists(os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', config.model_concordances_file_name_fuels)) and os.path.exists(os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', config.model_concordances_base_year_measures_file_name)) and os.path.exists(os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', config.model_concordances_user_input_and_growth_rates_file_name)) and os.path.exists(os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', config.model_concordances_demand_side_fuel_mixing_file_name)) and os.path.exists(os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', config.model_concordances_supply_side_fuel_mixing_file_name)):
                return True
            else:
                return False
        elif file_date_id:
            try:
                #just copy all the cocordances we'd save now to the folder with current file_date_id
                shutil.copyfile(os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', config.model_concordances_file_name_fuels.replace(file_date_id, config.FILE_DATE_ID)), os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', config.model_concordances_file_name_fuels))
                shutil.copyfile(os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', config.model_concordances_base_year_measures_file_name.replace(file_date_id, config.FILE_DATE_ID)), os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', config.model_concordances_base_year_measures_file_name))
                shutil.copyfile(os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', config.model_concordances_user_input_and_growth_rates_file_name.replace(file_date_id, config.FILE_DATE_ID)), os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', config.model_concordances_user_input_and_growth_rates_file_name))
                shutil.copyfile(os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', config.model_concordances_demand_side_fuel_mixing_file_name.replace(file_date_id, config.FILE_DATE_ID)), os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', config.model_concordances_demand_side_fuel_mixing_file_name))
                shutil.copyfile(os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', config.model_concordances_supply_side_fuel_mixing_file_name.replace(file_date_id, config.FILE_DATE_ID)), os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', config.model_concordances_supply_side_fuel_mixing_file_name))
                return True
            except FileNotFoundError:
                return False
        else:
            return False
#%%
#%%
# create_all_concordances(config)
#%%
