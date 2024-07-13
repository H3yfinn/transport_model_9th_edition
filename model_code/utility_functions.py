

#####################################################

###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
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
import glob
     
def copy_required_output_files_to_one_folder(config, ECONOMY_ID='all', output_folder_path='output_data\\for_other_modellers'):
    #to make it easier to give the output to others use ths function to make it a bit easier to group the files that people find useful together, so i can quickly send them.
    useful_file_paths = []
    output_file_paths = []
    files_in_output_folder = []
    #dashboard fiels:
    for economy in config.ECONOMY_LIST:
        if economy == ECONOMY_ID or ECONOMY_ID == 'all':
            for scenario in config.SCENARIOS_LIST:
                useful_file_paths.append(config.root_dir + '\\' +'plotting_output\\dashboards\\' + economy + f'\\{economy}_{scenario}_dashboard_results.html')
                output_file_paths.append(config.root_dir + '\\' +output_folder_path + '\\' + economy + f'\\{economy}_{scenario}_{config.FILE_DATE_ID}_dashboard_results.html')
                
                useful_file_paths.append(config.root_dir + '\\' +'plotting_output\\dashboards\\' + economy + f'\\{economy}_{scenario}_dashboard_assumptions.html')
                output_file_paths.append(config.root_dir + '\\' +output_folder_path + '\\' + economy + f'\\{economy}_{scenario}_{config.FILE_DATE_ID}_dashboard_assumptions.html')
                
                useful_file_paths.append(config.root_dir + '\\' +'plotting_output\\dashboards\\' + economy + f'\\{economy}_{scenario}_dashboard_assumptions_extra.html')
                output_file_paths.append(config.root_dir + '\\' +output_folder_path + '\\' + economy + f'\\{economy}_{scenario}_{config.FILE_DATE_ID}_dashboard_assumptions_extra.html')
                
                useful_file_paths.append(config.root_dir + '\\' + f'output_data\\for_other_modellers\\output_for_outlook_data_system\\{economy}_{config.FILE_DATE_ID}_transport_energy_use.csv')
                output_file_paths.append(config.root_dir + '\\' +output_folder_path + '\\' + economy + f'\\{economy}_{config.FILE_DATE_ID}_transport_energy_use.csv')
                useful_file_paths.append(config.root_dir + '\\' + f'output_data\\for_other_modellers\\cost_estimation\\{config.FILE_DATE_ID}_{economy}_cost_inputs.csv')
                output_file_paths.append(config.root_dir + '\\' +output_folder_path + '\\' + economy + f'\\{config.FILE_DATE_ID}_{economy}_cost_inputs.csv')
                
                useful_file_paths.append(config.root_dir + '\\' + f'output_data\\for_other_modellers\\output_for_outlook_data_system\\{economy}_{config.FILE_DATE_ID}_transport_stocks.csv')
                output_file_paths.append(config.root_dir + '\\' +output_folder_path + '\\' + economy + f'\\{config.FILE_DATE_ID}_{economy}_transport_stocks.csv')
                
                useful_file_paths.append(config.root_dir + '\\' + f'output_data\\for_other_modellers\\output_for_outlook_data_system\\{economy}_{config.FILE_DATE_ID}_transport_activity.csv')
                output_file_paths.append(config.root_dir + '\\' +output_folder_path + '\\' + economy + f'\\{config.FILE_DATE_ID}_{economy}_transport_activity.csv')
                
                useful_file_paths.append(config.root_dir + '\\' + f'output_data\\for_other_modellers\\output_for_outlook_data_system\\{economy}_{config.FILE_DATE_ID}_transport_stock_shares.csv')
                output_file_paths.append(config.root_dir + '\\' +output_folder_path + '\\' + economy + f'\\{config.FILE_DATE_ID}_{economy}_transport_stock_shares.csv')
                # output_data\\for_other_modellers\\charging
                
                useful_file_paths.append(config.root_dir + '\\' + f'output_data\\for_other_modellers\\charging\\{economy}_estimated_number_of_chargers.csv')
                output_file_paths.append(config.root_dir + '\\' +output_folder_path + '\\' + economy + f'\\{economy}_{config.FILE_DATE_ID}_estimated_number_of_chargers.csv')
                
                useful_file_paths.append(config.root_dir + '\\' + f'output_data\\model_output_detailed\\{economy}_NON_ROAD_DETAILED_model_output{config.FILE_DATE_ID}.csv')
                output_file_paths.append(config.root_dir + '\\' +output_folder_path + '\\' + economy + f'\\{config.FILE_DATE_ID}_{economy}_detailed_incl_non_road.csv')
            
                useful_file_paths.append(config.root_dir + '\\' + f'output_data\\for_other_modellers\\output_for_outlook_data_system\\{economy}_international_bunker_energy_use_{config.FILE_DATE_ID}.csv')
                output_file_paths.append(config.root_dir + '\\' +output_folder_path + '\\' + economy + f'\\{economy}_international_bunker_energy_use_{config.FILE_DATE_ID}.csv')
    
    #go through the files output_file_paths and put them in a list but repalce the dateid with a wildcard
    for file in output_file_paths:
        files_in_output_folder.append(re.sub(config.FILE_DATE_ID, '*', file))
    #for every file in useful file paths, copy it to its corresponding output file path
    for f in range(len(useful_file_paths)):
        try:
            #first test that the folders exist, if not create them
            if not os.path.exists(os.path.dirname(output_file_paths[f])):
                os.makedirs(os.path.dirname(output_file_paths[f]))
            #then if the file exists, copy it in after removing the old file
            if os.path.exists(useful_file_paths[f]):
                # for file f (with a regex wildcard) in files_in_output_folder , find them and remove them
                files_to_delete = glob.glob(files_in_output_folder[f])
                for file in files_to_delete:
                    os.unlink(file)
                shutil.copyfile(useful_file_paths[f], output_file_paths[f])
            
            # shutil.copyfile(useful_file_paths[f], output_file_paths[f])
        except FileNotFoundError:
            print('File not found: ' + useful_file_paths[f])
        except shutil.Error:
            # print('File already exists: ' + output_file_paths[f])
            raise shutil.Error('File already exists: ' + output_file_paths[f])
        except Exception as e:
            print('Error: ' + str(e))
            breakpoint()
            raise e 
    
def get_latest_date_for_data_file(data_folder_path, file_name_start, file_name_end='', EXCLUDE_DATE_STR_START=False):
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
    if file_name_end == '':
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

def find_latest_folder_via_regex(config, directory, pattern=r"^\d{4}((0[1-9])|(1[0-2]))((0[1-9])|([12]\d)|(3[01]))$"):
    # List all folders in the given directory
    folders = [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]
    
    # Filter folders based on the expected pattern
    valid_folders = [folder for folder in folders if re.match(pattern,folder) is not None]
    
    if not valid_folders:
        return None

    # Parse the valid folder names as dates
    dates = [datetime.datetime.strptime(folder, "%Y%m%d") for folder in valid_folders]
    
    # Find the latest date
    latest_date = max(dates)

    # Convert the latest date back to folder name format
    latest_folder = latest_date.strftime("%Y%m%d")

    return latest_folder


def produce_data_system_data_for_others(config):
    #take in data from the transport datasystem and clean it up a bit so others can use it.
    #most importantly just set the units to what tey shoud be
    unit_to_adj_unit_concordance_dict = config.measure_to_unit_concordance.set_index('Unit').to_dict()['Magnitude_adjusted_unit']
    #join to the transport data system
    transport_data_system_extract = pd.read_csv(config.root_dir + '\\' + 'intermediate_data\\model_inputs\\transport_data_system_extract.csv')
    
    transport_data_system_extract['Unit'] = transport_data_system_extract['Measure'].map(unit_to_adj_unit_concordance_dict)



#create a glossary which is a dictionary which defines the different categories and units for differernt values within the dfs:
def create_glossary(config):
    glossary_dict = {}
    glossary_dict['Stocks'] = 'Number of vehicles (millions)'
    glossary_dict['Stocks_share'] = 'Share of vehicles (%)'
    glossary_dict['Sales'] = 'Number new of vehicles (million new vehicles)'
    glossary_dict['Sales_share'] = 'Share of new vehicles (%)'
    glossary_dict['Turnover_rate'] = 'Turnover rate (% of vehicles)'
    glossary_dict['Turnover'] = 'Turnover (million vehicles)'
    glossary_dict['Mileage'] = 'Mileage (thousand km)'
    glossary_dict['Average_age'] = 'Average vehicle age (years)'
    glossary_dict['Freight_tonne_km'] = 'Freight tonne km (billion tonne km)'
    glossary_dict['Passenger_km'] = 'Passenger km (billion passenger km)'
    glossary_dict['Passenger_km_share'] = 'Share of passenger km (%)'
    glossary_dict['Energy'] = 'Energy (PJ)'
    
    #now define the different columns
    glossary_dict['Drive'] = 'Otherwise called powertrain or engine. A drive is the mechanism that converts energy into power to move a vehicle. For example, a petrol engine, a diesel engine, a battery electric motor, a fuel cell electric motor, a hybrid engine, etc.'
    glossary_dict['Vehicle Type'] = 'The type of vehicle. For example, a passenger car, a bus, a truck, a motorcycle, etc.'
    glossary_dict['Medium'] = 'The medium in which the vehicle travels. For example, road, rail, air, water, etc.'
    glossary_dict['Transport Type'] = 'The type of transport. For example, passenger or freight.'
    
    #now define  drives and vehicle types:
    glossary_dict['lpv'] = 'Light passenger vehicle. Normally is a passenger vehicle with a gross vehicle weight of less than 3.5 tonnes, but in this model definitions remain loose'
    glossary_dict['car'] = 'The lightest of lpv vehicles, and the most common, for example sedan, hatchback, coupe, etc.'
    glossary_dict['suv'] = 'A light passenger vehicle with a higher ground clearance, for example a 4x4, a crossover, etc.'
    glossary_dict['lt'] = 'Light truck. Trucks used for mostly passenger use, so normally a pickup truck, a van, etc.'
    glossary_dict['mt'] = 'Medium truck. In between a lcv and ht, expected to be around 4.5 to 12 tonnes but that is a loose definition. Even though this refers to weight (and garbage trucks may be considered on heavy end), it provides a convenient category to reflect faster electrifciation of urban trucks (eg. garbage trucks) compared to long haul trucks.'
    glossary_dict['ht'] = 'Heavy truck. The heaviest trucks. Normally truck and trailer but could include dump trucks, etc. Expected to be 8+ tonnes (even greater than 20 tonnes is included sometimes). Sometimes intersects with mt, but no vehicles are ever double counted.'
    glossary_dict['lcv'] = 'Light commercial vehicle. A vehicle used for commercial purposes, but not a truck. For example, a delivery van. Is often used to catch vehicles that have an unknown purpose and description as it is seen as a medium sized vehicle. Is around 3.5 to 7.5 tonnes, but that is a loose definition.'
    glossary_dict['bus'] = 'A bus. A vehicle used for transporting people. Can be a city bus, a school bus, a coach, etc.'
    glossary_dict['2w'] = 'A motorcycle. A vehicle with two or three wheels. Can be a scooter, a motorbike, tuktuk, etc.'
    
    glossary_dict['ice_g'] = 'Internal combustion engine, gasoline. A vehicle with an internal combustion engine that uses gasoline as its fuel.'
    glossary_dict['ice_d'] = 'Internal combustion engine, diesel. A vehicle with an internal combustion engine that uses diesel as its fuel.'
    glossary_dict['bev'] = 'Battery electric vehicle. A vehicle with an electric motor that is powered by a battery.'
    glossary_dict['phev_g'] = 'Plug-in hybrid electric vehicle that uses gasoline. A vehicle with an electric motor that is powered by a battery and an internal combustion engine.'
    glossary_dict['phev_d'] = 'Plug-in hybrid electric vehicle that uses diesel. A vehicle with an electric motor that is powered by a battery and an internal combustion engine.'
    glossary_dict['fcev'] = 'Fuel cell electric vehicle. A vehicle with an electric motor that is powered by a fuel cell and a battery.'
    
    glossary_dict['road'] = 'A vehicle that travels on a road.'
    glossary_dict['nonroad'] = 'A vehicle that does not travel on a road. For example, a train, a plane, a boat, etc.'
    glossary_dict['air'] = 'A vehicle that travels in the air. For example, a plane, a helicopter, a drone, etc.'
    glossary_dict['rail'] = 'A vehicle that travels on a rail. For example, a train, a tram, a monorail, etc.'
    glossary_dict['ship'] = 'A vehicle that travels on water. For example, a boat, a ship, a submarine, etc.'
    
    #now print to a text file in a nice format:
    with open(config.root_dir + '\\' + 'plotting_output\\glossary.txt', 'w') as f:
        for key, value in glossary_dict.items():
            f.write(f'{key}: {value}\n')
            
#%%
def compare_versions_of_input_spreadsheets(config, file_name1, file_name2, sheet1_name, sheet2_name, value_cols= ['Target', 'Reference'], key_cols=['Region', 'Medium', 'Vehicle Type', 'Drive', 'Date']):
    #as we create more versions of the input spreadsheets, we need to compare them to make sure that they are the same. This function does that.
    #e.g. import from input_data/vehicle_sales_share_inputs.xlsx and input_data/vehicle_sales_share_inputs phevs.xlsx and compare them to make sure they are the same.
    a= pd.read_excel(file_name1, sheet_name=sheet1_name)
    b= pd.read_excel(file_name2, sheet_name=sheet2_name)
    #if comment is a col in the df, then drop it
    a = a.drop(columns=['Comment', 'comment'], errors='ignore')
    b = b.drop(columns=['Comment', 'comment'], errors='ignore')
    
    #check that the key cols and value_cols are not in the df
    for col in key_cols + value_cols:
        if col not in a.columns:
            print(f'Column {col} not in sheet 1')
            raise ValueError(f'Column {col} not in sheet 1')
        if col not in b.columns:
            print(f'Column {col} not in sheet 2')
            raise ValueError(f'Column {col} not in sheet 2')
    
    
    #merge the two dfs
    #but first make the dfs tall, so we have all values in one col
    a = a.melt(id_vars=key_cols, value_vars=value_cols, var_name='Column_name', value_name='Value')
    b = b.melt(id_vars=key_cols, value_vars=value_cols, var_name='Column_name', value_name='Value')
    merged_files = pd.merge(a, b, on=key_cols+['Column_name'], indicator=True)
    #separate any non matching rows
    non_matching_rows = merged_files[merged_files['_merge'] != 'both']
    merged_files = merged_files[merged_files['_merge'] == 'both']
    ######################
    #quikcly just make any nan cols into strings
    merged_files['Value_x'] = merged_files['Value_x'].fillna('nan')
    merged_files['Value_y'] = merged_files['Value_y'].fillna('nan')
    #also where the value might be filled with a string and not a number, set it to 'nan' too
    merged_files['Value_x'] = merged_files['Value_x'].apply(lambda x: 'nan' if type(x) == str else x)
    merged_files['Value_y'] = merged_files['Value_y'].apply(lambda x: 'nan' if type(x) == str else x)
    
    ######################
    #check that the values are the same in Value col, where they aren't add them to a new df
    non_matching_values = merged_files[merged_files['Value_x'] != merged_files['Value_y']]
    non_matching_values['issue'] = 'Value not matching'
    non_matching_rows['issue'] = 'Row not matching'
    #add the non matching rows to the non matching values
    non_matching_values = pd.concat([non_matching_values, non_matching_rows])
    #save the non matching values to a csv
    non_matching_values.to_csv(config.root_dir + '\\' + 'plotting_output\\non_matching_values.csv')
    
#%%
# compare_versions_of_input_spreadsheets(config, 'input_data\\vehicle_sales_share_inputs.xlsx', 'input_data\\vehicle_sales_share_inputs phevs.xlsx', 'freight_drive_shares', 'freight_drive_shares')
#%%

def replicate_data_from_fuel_mixing_for_new_fuel_for_all_economys(config):
    #quick function from chatgpt. saving it in case it comes in useful again. 
    # This is the base pattern to be replicated for each country.
    # It's extracted from the provided screenshot.
    base_pattern = pd.DataFrame({
        'country': 'china',
        'fuel_type': ['07_x_jet_fuel', '07_x_jet_fuel', '07_x_jet_fuel', '07_x_jet_fuel', '07_x_jet_fuel',
                    '07_02_aviation_gasoline', '07_02_aviation_gasoline', '07_02_aviation_gasoline',
                    '07_02_aviation_gasoline', '07_02_aviation_gasoline', '07_06_kerosene', '07_06_kerosene',
                    '07_06_kerosene', '07_06_kerosene', '07_06_kerosene', '07_x_jet_fuel',
                    '07_02_aviation_gasoline', '07_06_kerosene'],
        'category': '16_x_efuel',
        'year': [2020, 2030, 2035, 2040, 2100, 2020, 2030, 2035, 2040, 2100, 2020, 2030, 2035, 2040, 2100, 2050, 2050, 2050],
        'value1': [0, 0, 0.05, 0.05, 0.05, 0, 0, 0.05, 0.05, 0.05, 0, 0, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05],
        'value2': [0, 0, 0.025, 0.07, 0.3, 0, 0, 0.025, 0.07, 0.3, 0, 0, 0.025, 0.07, 0.3, 0.15, 0.15, 0.15]
    })

    # List of countries for which to replicate the pattern
    countries = ['Canada', 'fast', 'slow', 'tha', 'USA', 'AUS', 'INA', 'malay', 'viet', 'nz']

    # Replicate the pattern for each country and store the results in a new dataframe
    replicated_data = pd.concat([base_pattern.assign(country=country) for country in countries], ignore_index=True)

    # Here you can export the dataframe to a CSV file
    replicated_data.to_csv(config.root_dir + '\\' + 'replicated_data.csv', index=False)
    
#######################################
#following are for dealing with issue that windows has, where it can't handle long file paths (past 260 characters - which is a lot but can happen with long file names and deep folder structures)
def get_extended_length_path(config, path):
    path = os.path.abspath(path)
    if not path.startswith("\\\\?\\"):
        path = "\\\\?\\" + path
    return path

#######################################
#%%
#%%