"""This file is intended to be able ot be used in the beginnning of any jupyter ntoebook to set the config variables for the model. This helps to reduce clutter, as that is a big issue for notebooks. So if you ever need to chnage conifgurations, just change this. """
#to make the code in this library clear we will name every variable that is stated in here with all caps
#%%
#FREQUENTLY CHANGED CONFIG VARIABLES:

NEW_SALES_SHARES = True

NEW_FUEL_MIXING_DATA = True

IMPORT_FROM_TRANSPORT_DATA_SYSTEM = False
transport_data_system_FILE_DATE_ID ='DATE20240612'#DATE20240530' #'DATE20240304_DATE20240215' 
# FILE_DATE_ID ='20240327'#set me if you want to use a specific date_id for the model run. else it will be based on the date the model is run. if the FILE DATE ID might be lilke this DATE20230731_19_THA, inlude the eoconmoy codee!
# FILE_DATE_ID='20240315'
PRINT_LESS_IMPORTANT_DETAILS = False
PRINT_WARNINGS_FOR_FUTURE_WORK = False
#%%

#import common libraries 
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
# %config Completer.use_jedi = False#Jupiter lab specific setting to fix Auto fill bug

#################
current_working_dir = os.getcwd()
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = re.split('transport_model_9th_edition', script_dir)[0] + 'transport_model_9th_edition'
# from utility_functions import get_latest_date_for_data_file

#################
#%%
#TODO find way to put this in a different file. 

#can activate below to remove caveat warnings. but for now keep it there till confident:
# pd.options.mode.chained_assignment = None  # default='warn'

def get_latest_date_for_data_file(data_folder_path, file_name_start, file_name_end=None, EXCLUDE_DATE_STR_START=False):
    """Note that if file_name_end is not specified then it will just take the first file that matches the file_name_start, eben if that matches the end if the file name as well. This is because the file_name_end is not always needed, and this cahnge was made post hoc, so we want to keep the old functionality.

    Args:
        data_folder_path (_type_): _description_
        file_name_start (_type_): _description_
        file_name_end (_type_, optional): _description_. Defaults to None.
        EXCLUDE_DATE_STR_START if true, if there is DATE at th start of a file_date_id dont treat it as a date. Defaults to False.

    Returns:
        _type_: _description_
    """
    regex_pattern_date = r'\d{8}'
    if EXCLUDE_DATE_STR_START:
        regex_pattern_date = r'(?<!DATE)\d{8}'
    
    #get list of all files in the data folder
    all_files = os.listdir(data_folder_path)
    #filter for only the files with the correct file extension
    if file_name_end is None:
        all_files = [file for file in all_files if file_name_start in file]
    else:
        all_files = [file for file in all_files if file_name_start in file and file_name_end in file]
    #drop any files with no date in the name
    all_files = [file for file in all_files if re.search(regex_pattern_date, file)]
    #get the date from the file name
    all_files = [re.search(regex_pattern_date, file).group() for file in all_files]
    #convert the dates to datetime objects
    all_files = [datetime.datetime.strptime(date, '%Y%m%d') for date in all_files]
    #get the latest date
    if len(all_files) == 0:
        print('No files found for ' + file_name_start + ' ' + file_name_end)
        return None
    # try:
    latest_date = max(all_files)
    # except ValueError:
    #     print('No files found for ' + file_name_start + ' ' + file_name_end)
    #     return None
    #convert the latest date to a string
    latest_date = latest_date.strftime('%Y%m%d')
    return latest_date

#%%
#we can set FILE_DATE_ID to something other than the date here which is useful if we are running the script alone, versus through integrate.py
USE_LATEST_OUTPUT_DATE_ID = True
#create option to set FILE_DATE_ID to the date_id of the latest created output files. this can be helpful when producing graphs and analysing output data
# FILE_DATE_ID = '20240529'
try:
    if FILE_DATE_ID:
       pass
    elif USE_LATEST_OUTPUT_DATE_ID:
        data_folder_path = './output_data/model_output/'
        file_name = 'model_output_years_'
        date_id = get_latest_date_for_data_file(data_folder_path, file_name)
        FILE_DATE_ID ='_'+ date_id
except NameError:
    # FILE_DATE_ID = ''
    file_date = datetime.datetime.now().strftime("%Y%m%d")
    FILE_DATE_ID = '{}'.format(file_date)#Note that this is not the official file date id anymore because it was interacting badly with how we should instead set it in onfig.py

#%%
#state important modelling variables
DEFAULT_BASE_YEAR = 2017
OUTLOOK_BASE_YEAR = 2021
END_YEAR = 2100
GRAPHING_END_YEAR = 2070
USE_LOGISTIC_FUNCTION=True
#this is important for defining how the dataframes are used. Generally this shouldnt change unless a column name changes or the model is changed
INDEX_COLS = ['Date', 'Economy', 'Measure', 'Vehicle Type', 'Medium',
       'Transport Type','Drive', 'Scenario', 'Unit']
INDEX_COLS_no_date = INDEX_COLS.copy()
INDEX_COLS_no_date.remove('Date')
INDEX_COLS_NO_MEASURE = INDEX_COLS.copy()
INDEX_COLS_NO_MEASURE.remove('Measure')
INDEX_COLS_NO_MEASURE.remove('Unit')

model_output_file_name = 'model_output{}.csv'.format(FILE_DATE_ID)

#get sceanrios from scenarios_list file
SCENARIOS_LIST = pd.read_csv(root_dir + '/' + 'config/concordances_and_config_data/scenarios_list.csv')
#grab the scenario names where 'Use' column is true and put them into a list
SCENARIOS_LIST = SCENARIOS_LIST[SCENARIOS_LIST['Use'] == True]['Scenario'].tolist()

#For graphing and analysis we sometimes will single out a scenario to look at. This is the scenario we will use for that:
SCENARIO_OF_INTEREST = 'Reference'

user_input_measures_list_ROAD = ['Vehicle_sales_share', 
       'New_vehicle_efficiency_growth', 'Occupancy_or_load_growth', 'Mileage_growth','Gompertz_gamma', 'Activity_efficiency_improvement']

user_input_measures_list_NON_ROAD = ['Vehicle_sales_share','Non_road_intensity_improvement']

base_year_measures_list_ROAD = ['Activity','Energy', 'Stocks', 'Occupancy_or_load', 'New_vehicle_efficiency', 'Efficiency','Mileage', 'Average_age']

base_year_measures_list_NON_ROAD = ['Activity','Energy', 'Intensity', 'Average_age']

calculated_measures_ROAD = ['Travel_km','Surplus_stocks', 'Turnover_rate','Activity_per_Stock']#tinclude travel km as to be calcualted as it is not widely available publicly, so its best just to calculate it.its also kind of an intermediate measure as it is reliant on what mileage,efficiency and stocks are, but is not the goal like energy or activity really are
calculated_measures_NON_ROAD = ['Stocks','Surplus_stocks', 'Turnover_rate']

ROAD_MODEL_OUTPUT_COLS = ['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Medium','Date', 'Drive', 'Activity', 'Stocks', 'Efficiency', 'Energy', 'Surplus_stocks', 'Travel_km', 'Mileage', 'Vehicle_sales_share', 'Occupancy_or_load', 'Turnover_rate', 'Stock_turnover', 'New_stocks_needed','New_vehicle_efficiency','Stocks_per_thousand_capita', 'Activity_growth', 'Gdp_per_capita','Gdp', 'Population', 'Average_age', 'Age_distribution', 'Activity_efficiency_improvement']

NON_ROAD_MODEL_OUTPUT_COLS = ['Date', 'Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive', 'Scenario', 'Activity', 'Average_age', 'Age_distribution', 'Energy', 
    'Intensity', 'Non_road_intensity_improvement', 'Surplus_stocks','Stocks', 'Vehicle_sales_share', 'Population', 
    'Gdp', 'Gdp_per_capita', 'Turnover_rate', 'Activity_per_Stock', 'Activity_growth', 'Stock_turnover', 'New_stocks_needed']

#define factors so that we can tell where setting nas to 0 is going to cause issues
FACTOR_MEASURES = ['Gompertz_gamma', 'Intensity', 'Average_age','Turnover_rate','Activity_per_Stock', 'Efficiency','Mileage', 'Occupancy_or_load','New_vehicle_efficiency','Age_distribution','Intensity']#THESE NEED TO HAVE VALUES RATHER THAN DEFAULTING TO 0 OR 1

GROWTH_MEASURES = ['Occupancy_or_load_growth', 'Mileage_growth','Activity_growth', 'Activity_efficiency_improvement', 'Non_road_intensity_improvement',
       'New_vehicle_efficiency_growth' ]#THESE WOULD NORMALLY HAVE A DEFAULT OF 1 RATHER THAN 0 FOR OTHJER MEASURES
#%%
#import measure to unit concordance
measure_to_unit_concordance = pd.read_csv(root_dir + '/' + 'config/concordances_and_config_data/measure_to_unit_concordance.csv')

# Convert to dict
measure_to_unit_concordance_dict = measure_to_unit_concordance.set_index('Measure')['Magnitude_adjusted_unit'].to_dict()

#import manually_defined_transport_categories
transport_categories = pd.read_csv(root_dir + '/' + 'config/concordances_and_config_data/manually_defined_transport_categories.csv')
###################################################
#%%

## Choose which economies to import and calculate data for:
#first take in economy names file, then we will remove the economies we dont want (or if there are too many, just  choose the one you do want)
economy_codes_path = root_dir + '/' +'config/concordances_and_config_data/economy_code_to_name.csv'

ECONOMY_LIST = pd.read_csv(economy_codes_path).iloc[:,0]#get the first column

#ECONOMY REGIONS
#load the economy regions file so that we can easily merge it with a dataframe to create a region column
economy_regions_path = root_dir + '/' +'config/concordances_and_config_data/region_economy_mapping.csv'
ECONOMY_REGIONS = pd.read_csv(economy_regions_path)

###################################################
#%%
import plotly.express as px
#graphing tools:
PLOTLY_COLORS_LIST = px.colors.qualitative.Plotly

AUTO_OPEN_PLOTLY_GRAPHS = False

# %%
#state model concordances file names for concordances we create manually
model_concordances_version = FILE_DATE_ID#'20220824_1256'
model_concordances_file_name  = 'model_concordances_{}.csv'.format(model_concordances_version)
model_concordances_file_name_fuels = 'model_concordances_fuels_{}.csv'.format(model_concordances_version)
model_concordances_file_name_fuels_NO_BIOFUELS = 'model_concordances_fuels_NO_BIOFUELS_{}.csv'.format(model_concordances_version)

#state model concordances file names for concordances we create using inputs into the model. these model concordances state what measures are used in the model
model_concordances_base_year_measures_file_name = 'model_concordances_measures_{}.csv'.format(model_concordances_version)
model_concordances_user_input_and_growth_rates_file_name = 'model_concordances_user_input_and_growth_rates_{}.csv'.format(model_concordances_version)
model_concordances_supply_side_fuel_mixing_file_name = 'model_concordances_{}_supply_side_fuel_mixing.csv'.format(model_concordances_version)
model_concordances_demand_side_fuel_mixing_file_name = 'model_concordances_{}_demand_side_fuel_mixing.csv'.format(model_concordances_version)


#using scenarios list and economy list, create a dataframe with all possible combinations of economy and scenario
economy_scenario_concordance = pd.DataFrame(columns=['Economy', 'Scenario'])
for economy in ECONOMY_LIST:
    for scenario in SCENARIOS_LIST:
        economy_scenario_concordance = pd.concat([economy_scenario_concordance, pd.DataFrame({'Economy': [economy], 'Scenario': [scenario]})], ignore_index=True)

model_concordances_reference =  pd.read_csv(root_dir + '/' + 'config/concordances_and_config_data/manually_defined_transport_categories.csv')
#AND A model_concordances_all_file_name
# model_concordances_all_file_name = 'model_concordances_all{}.csv'.format(model_concordances_version)
#%%
#check that importnat folders exist:
# "intermediate_data/model_inputs/{}".format(FILE_DATE_ID)
if not os.path.exists(root_dir + '/' +"intermediate_data/model_inputs/{}".format(FILE_DATE_ID)):
    os.makedirs(root_dir + '/' +"intermediate_data/model_inputs/{}".format(FILE_DATE_ID))

#%%

#ESTO/9th_EBT to transport model mappings:
medium_mapping = {'air': '15_01_domestic_air_transport', 'road': '15_02_road', 'rail': '15_03_rail', 'ship': '15_04_domestic_navigation', 'pipeline':'15_05_pipeline_transport', 'nonspecified': '15_06_nonspecified_transport', 'international_shipping':'04_international_marine_bunkers', 'international_aviation':'05_international_aviation_bunkers'}

transport_type_mapping = {'passenger': '01_passenger', 'freight': '02_freight'}
inverse_transport_type_mapping = {'15_01_01_passenger': 'passenger', '15_01_02_freight': 'freight', '15_02_01_passenger': 'passenger', '15_02_02_freight': 'freight', '15_03_01_passenger': 'passenger', '15_03_02_freight': 'freight', '15_04_01_passenger': 'passenger', '15_04_02_freight': 'freight', 'x':'all'}

vehicle_type_mapping_passenger = {'suv': '15_02_01_03_sports_utility_vehicle', 'lt': '15_02_01_04_light_truck', 'car': '15_02_01_02_car', 'bus': '15_02_01_05_bus', '2w': '15_02_01_01_two_wheeler','all':'x'}

vehicle_type_mapping_freight = {'mt': '15_02_02_03_medium_truck', 'lcv': '15_02_02_02_light_commercial_vehicle', 'ht': '15_02_02_04_heavy_truck', '2w': '15_02_02_01_two_wheeler_freight', 'all':'x'}

drive_mapping_inversed = {'x':'all',
    '15_02_01_01_01_diesel_engine': 'ice_d', 
    '15_02_01_01_02_gasoline_engine': 'ice_g', 
    '15_02_01_01_03_battery_ev': 'bev', 
    '15_02_01_01_04_compressed_natual_gas': 'cng', 
    '15_02_01_01_05_plugin_hybrid_ev_gasoline': 'phev_g', 
    '15_02_01_01_06_plugin_hybrid_ev_diesel': 'phev_d',  
    '15_02_01_01_07_liquified_petroleum_gas': 'lpg', 
    '15_02_01_01_08_fuel_cell_ev': 'fcev', 

    '15_02_01_02_01_diesel_engine': 'ice_d', 
    '15_02_01_02_02_gasoline_engine': 'ice_g', 
    '15_02_01_02_03_battery_ev': 'bev', 
    '15_02_01_02_04_compressed_natual_gas': 'cng', 
    '15_02_01_02_05_plugin_hybrid_ev_gasoline': 'phev_g', 
    '15_02_01_02_06_plugin_hybrid_ev_diesel': 'phev_d',  
    '15_02_01_02_07_liquified_petroleum_gas': 'lpg', 
    '15_02_01_02_08_fuel_cell_ev': 'fcev', 

    '15_02_01_03_01_diesel_engine': 'ice_d', 
    '15_02_01_03_02_gasoline_engine': 'ice_g', 
    '15_02_01_03_03_battery_ev': 'bev', 
    '15_02_01_03_04_compressed_natual_gas': 'cng', 
    '15_02_01_03_05_plugin_hybrid_ev_gasoline': 'phev_g', 
    '15_02_01_03_06_plugin_hybrid_ev_diesel': 'phev_d',  
    '15_02_01_03_07_liquified_petroleum_gas': 'lpg', 
    '15_02_01_03_08_fuel_cell_ev': 'fcev', 

    '15_02_01_04_01_diesel_engine': 'ice_d', 
    '15_02_01_04_02_gasoline_engine': 'ice_g', 
    '15_02_01_04_03_battery_ev': 'bev', 
    '15_02_01_04_04_compressed_natual_gas': 'cng', 
    '15_02_01_04_05_plugin_hybrid_ev_gasoline': 'phev_g', 
    '15_02_01_04_06_plugin_hybrid_ev_diesel': 'phev_d',  
    '15_02_01_04_07_liquified_petroleum_gas': 'lpg', 
    '15_02_01_04_08_fuel_cell_ev': 'fcev', 

    '15_02_01_05_01_diesel_engine': 'ice_d', 
    '15_02_01_05_02_gasoline_engine': 'ice_g', 
    '15_02_01_05_03_battery_ev': 'bev', 
    '15_02_01_05_04_compressed_natual_gas': 'cng', 
    '15_02_01_05_05_plugin_hybrid_ev_gasoline': 'phev_g', 
    '15_02_01_05_06_plugin_hybrid_ev_diesel': 'phev_d',  
    '15_02_01_05_07_liquified_petroleum_gas': 'lpg', 
    '15_02_01_05_08_fuel_cell_ev': 'fcev',

    '15_02_02_01_01_diesel_engine': 'ice_d', 
    '15_02_02_01_02_gasoline_engine': 'ice_g', 
    '15_02_02_01_03_battery_ev': 'bev', 
    '15_02_02_01_04_compressed_natual_gas': 'cng', 
    '15_02_02_01_05_plugin_hybrid_ev_gasoline': 'phev_g', 
    '15_02_02_01_06_plugin_hybrid_ev_diesel': 'phev_d',  
    '15_02_02_01_07_liquified_petroleum_gas': 'lpg', 
    '15_02_02_01_08_fuel_cell_ev': 'fcev', 

    '15_02_02_02_01_diesel_engine': 'ice_d', 
    '15_02_02_02_02_gasoline_engine': 'ice_g', 
    '15_02_02_02_03_battery_ev': 'bev', 
    '15_02_02_02_04_compressed_natual_gas': 'cng', 
    '15_02_02_02_05_plugin_hybrid_ev_gasoline': 'phev_g', 
    '15_02_02_02_06_plugin_hybrid_ev_diesel': 'phev_d',  
    '15_02_02_02_07_liquified_petroleum_gas': 'lpg', 
    '15_02_02_02_08_fuel_cell_ev': 'fcev', 

    '15_02_02_03_01_diesel_engine': 'ice_d', 
    '15_02_02_03_02_gasoline_engine': 'ice_g', 
    '15_02_02_03_03_battery_ev': 'bev', 
    '15_02_02_03_04_compressed_natual_gas': 'cng', 
    '15_02_02_03_05_plugin_hybrid_ev_gasoline': 'phev_g', 
    '15_02_02_03_06_plugin_hybrid_ev_diesel': 'phev_d',  
    '15_02_02_03_07_liquified_petroleum_gas': 'lpg', 
    '15_02_02_03_08_fuel_cell_ev': 'fcev', 

    '15_02_02_04_01_diesel_engine': 'ice_d', 
    '15_02_02_04_02_gasoline_engine': 'ice_g', 
    '15_02_02_04_03_battery_ev': 'bev', 
    '15_02_02_04_04_compressed_natual_gas': 'cng', 
    '15_02_02_04_05_plugin_hybrid_ev_gasoline': 'phev_g', 
    '15_02_02_04_06_plugin_hybrid_ev_diesel': 'phev_d',  
    '15_02_02_04_07_liquified_petroleum_gas': 'lpg', 
    '15_02_02_04_08_fuel_cell_ev': 'fcev'}
    

subfuels_mapping = {'17_electricity':'x', '07_07_gas_diesel_oil':'07_07_gas_diesel_oil', '07_01_motor_gasoline':'07_01_motor_gasoline',
'08_01_natural_gas':'08_01_natural_gas', 
'16_x_hydrogen':'16_x_hydrogen',
'07_09_lpg':'07_09_lpg',
'07_02_aviation_gasoline':'07_02_aviation_gasoline', '07_x_jet_fuel':'07_x_jet_fuel', 
'01_x_thermal_coal':'01_x_thermal_coal',
'16_01_biogas':'16_01_biogas',
'07_08_fuel_oil':'07_08_fuel_oil', '07_x_other_petroleum_products':'07_x_other_petroleum_products',
'16_06_biodiesel':'16_06_biodiesel', 
'16_05_biogasoline':'16_05_biogasoline', 
'16_x_efuel':'16_x_efuel',
'16_07_bio_jet_kerosene':'16_07_bio_jet_kerosene', 
'16_x_ammonia': '16_x_ammonia',
'07_06_kerosene':'07_06_kerosene', '08_02_lng':'08_02_lng'}

#now map fuels to subfuels. All will need to be mapped, but in most cases it will be to a more broad category than it currently is. eg. 07_07_gas_diesel_oil will be mapped to 07_petroleum_products just like 07_01_motor_gasoline is.
fuels_mapping = {'17_electricity': '17_electricity', '07_07_gas_diesel_oil':'07_petroleum_products', '07_01_motor_gasoline':'07_petroleum_products',
'07_06_kerosene':'07_petroleum_products',
'08_01_natural_gas':'08_gas', 
'08_02_lng':'08_gas',
'16_x_hydrogen':'16_others', 
'07_09_lpg':'07_petroleum_products',
'07_02_aviation_gasoline':'07_petroleum_products', '07_x_jet_fuel':'07_petroleum_products', 
'01_x_thermal_coal':'01_coal',
'07_08_fuel_oil':'07_petroleum_products', #'07_x_other_petroleum_products':'07_petroleum_products',
'16_01_biogas':'16_others',
'16_06_biodiesel':'16_others', 
'16_05_biogasoline':'16_others', 
'16_x_efuel':'16_others',
'16_07_bio_jet_kerosene':'16_others',  
'16_x_ammonia': '16_others'}

# array(['01_01_coking_coal', '01_x_thermal_coal', '01_05_lignite', 'x',
#        '06_01_crude_oil', '06_02_natural_gas_liquids',
#        '06_x_other_hydrocarbons', '07_01_motor_gasoline',
#        '07_02_aviation_gasoline', '07_03_naphtha', '07_x_jet_fuel',
#        '07_06_kerosene', '07_07_gas_diesel_oil', '07_08_fuel_oil',
#        '07_09_lpg', '07_10_refinery_gas_not_liquefied', '07_11_ethane',
#        '07_x_other_petroleum_products', '08_01_natural_gas', '08_02_lng',
#        '08_03_gas_works_gas', '12_01_of_which_photovoltaics',
#        '12_x_other_solar', '15_01_fuelwood_and_woodwaste',
#        '15_02_bagasse', '15_03_charcoal', '15_04_black_liquor',
#        '15_05_other_biomass', '16_01_biogas', '16_02_industrial_waste',
#        '16_03_municipal_solid_waste_renewable',
#        '16_04_municipal_solid_waste_nonrenewable', '16_05_biogasoline',
#        '16_06_biodiesel', '16_07_bio_jet_kerosene',
#        '16_08_other_liquid_biofuels', '16_09_other_sources',
#        '16_x_ammonia', '16_x_hydrogen'], dtype=object)
#map the above so they map to the following fuels:
# array(['07_07_gas_diesel_oil', '17_electricity', '07_01_motor_gasoline',
#        '08_01_natural_gas', '16_x_hydrogen', '07_09_lpg',
#        '07_02_aviation_gasoline', '07_08_fuel_oil', '07_x_jet_fuel',
#        '07_06_kerosene', '01_x_thermal_coal', '16_x_ammonia',
#        '07_x_other_petroleum_products', '16_06_biodiesel', '16_x_efuel',
#        '16_05_biogasoline'], dtype=object)
temp_esto_subfuels_to_new_subfuels_mapping = {#one day we should get the EBT code to simplify the subfuels in here but for now just use this mapping:
    '01_x_thermal_coal': '01_x_thermal_coal',
    '01_05_lignite': '01_05_lignite',
    'x': 'x',
    '07_01_motor_gasoline': '07_01_motor_gasoline',
    '07_02_aviation_gasoline': '07_02_aviation_gasoline',
    '07_x_jet_fuel': '07_x_jet_fuel',
    '07_06_kerosene': '07_06_kerosene',
    '07_07_gas_diesel_oil': '07_07_gas_diesel_oil',
    '07_08_fuel_oil': '07_08_fuel_oil',
    '07_09_lpg': '07_09_lpg',
    # '07_11_ethane': '07_x_other_petroleum_products',
    # '07_x_other_petroleum_products': '07_x_other_petroleum_products',
    '08_01_natural_gas': '08_01_natural_gas',
    '08_02_lng': '08_02_lng',
    '08_03_gas_works_gas': '08_01_natural_gas',
    '16_01_biogas': '16_01_biogas',
    '16_05_biogasoline': '16_05_biogasoline',
    '16_06_biodiesel': '16_06_biodiesel',
    '16_07_bio_jet_kerosene': '16_07_bio_jet_kerosene',
    '16_08_other_liquid_biofuels': '16_09_other_sources',
    '16_09_other_sources': '16_09_other_sources',
    '16_x_ammonia': '16_x_ammonia',
    '16_x_hydrogen': '16_x_hydrogen',
    '16_x_efuel': '16_x_efuel',
    '01_01_coking_coal': '01_01_coking_coal'#,
    # '06_01_crude_oil': '06_crude_oil_and_ngl',
    # '06_02_natural_gas_liquids': '06_crude_oil_and_ngl'
}

# #where subfuel is x then map Fuel based on teh value in the fuels column. If the fuel is not in the mapping then throw an error.
x_subfuel_mappings = {
    # '16_others': '16_09_other_sources',#removed because these are agregates in the esto data
    '17_electricity': '17_electricity',
    # '03_peat':'01_coal',#removed because these are agregates in the esto data
    # '08_gas': '08_01_natural_gas',#removed because these are agregates in the esto data
    # '07_petroleum_products': '07_x_other_petroleum_products',#removed because these are agregates in the esto data
    # '01_coal': '01_coal',#removed because these are agregates in the esto data
    # '02_coal_products': '02_coal_products'#,#coal prodcuts is removed from esto data on line 489 of adjust_data_to_match_esto. it shouldnt have any effect on the model
    # '06_crude_oil_and_ngl': '06_crude_oil_and_ngl'
    }
    