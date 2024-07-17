
#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
from model_code import configurations
from model_code.preparation_functions.import_macro_data import import_macro_data
from model_code.preparation_functions.import_transport_system_data import import_transport_system_data
from model_code.preparation_functions.concordance_scripts import create_all_concordances
from model_code.preparation_functions import (
    create_and_clean_user_input,
    aggregate_data_for_model,
    filter_for_modelling_years
)
from model_code.calculation_functions import (
    calculate_inputs_for_model,
    run_road_model,
    apply_fuel_mix_demand_side
)
from model_code.formatting_functions import concatenate_model_output
from model_code.formatting_functions.concatenate_model_output import fill_missing_output_cols_with_nans
from model_code.formatting_functions import clean_model_output
from model_code.calculation_functions import run_non_road_model
from model_code.formatting_functions import concatenate_model_output
from model_code.calculation_functions import apply_fuel_mix_demand_side
from model_code.calculation_functions import apply_fuel_mix_supply_side
from model_code.formatting_functions import clean_model_output
from model_code.preparation_functions import filter_for_modelling_years
from model_code.calculation_functions import calculate_inputs_for_model
from model_code.preparation_functions import aggregate_data_for_model
from model_code.calculation_functions import run_road_model
from model_code.calculation_functions import run_non_road_model
from model_code.formatting_functions import create_output_for_outlook_data_system
from model_code.calculation_functions import estimate_kw_of_required_chargers
from model_code.plotting_functions import plot_required_chargers
from model_code.plotting_functions import calculate_and_plot_oil_displacement
from model_code.calculation_functions import international_bunker_share_calculation_handler

from model_code.plotting_functions import produce_lots_of_LMDI_charts
from model_code.plotting_functions import dashboard_creation_handler, setup_and_run_multi_economy_plots
from model_code.utility_functions import copy_required_output_files_to_one_folder
from model_code.formatting_functions import concatenate_outlook_data_system_outputs
from model_code import utility_functions
from model_code.formatting_functions import concatenate_output_data
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
###
import ctypes
USE_PREVIOUS_OPTIMISATION_RESULTS_FOR_THIS_DATA_SYSTEM_INPUT=True
USE_SAVED_OPT_PARAMATERS=True   
#%%
def setup_for_main(root_dir_param, script_dir_param, economy_to_run, progress_callback):
    #setup the root and script directories which will be passed into functions to know where to look for files. This allwos for multiple threads of this module to be run at the same time without setting the root and script directories as global variables or including them all in sys.path
    if script_dir_param is not None:
        script_dir = script_dir_param
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    if root_dir_param is not None:
        root_dir = root_dir_param
        if os.name == 'nt':#if we are on windows, we need to add the \\?\ prefix to the root_dir to allow for long file paths
            if "\\\\?\\" not in root_dir:
                root_dir =  "\\\\?\\" + root_dir
    else:
        if os.name == 'nt':
            root_dir =  "\\\\?\\" + re.split('transport_model_9th_edition', script_dir)[0] + 'transport_model_9th_edition'
        else:
            root_dir = re.split('transport_model_9th_edition', script_dir)[0] + 'transport_model_9th_edition'

    config = configurations.Config(root_dir)
    
    #make config global:
    def update_progress(progress):
        if progress_callback:
            progress_callback(progress)
    progress = 0
    update_progress(progress)
    #if economy_to_run is all, set increment to 100/21+1, if its a single economy, set increment to 100/1+1, and if its a list of economies, set increment to 100/len(economy_to_run)+1
    if economy_to_run == 'all':
        increment = 100/((3*21)+1)
    elif type(economy_to_run) == str:
        increment = 100/((3*1)+1)
    elif type(economy_to_run) == list:
        increment = 100/((3*len(economy_to_run))+1)
    else:
        raise Exception('Somethings going wrong with the economy_to_run variable')
    
    return increment, progress, update_progress, config

def main(economy_to_run='all', progress_callback=None, root_dir_param=None, script_dir_param=None):
    error_message = None
    increment, progress, update_progress, config = setup_for_main(root_dir_param, script_dir_param, economy_to_run, progress_callback)

    # Prevent the system from going to sleep
    # ctypes.windll.kernel32.SetThreadExecutionState(0x80000002)
    # To restore the original state, use:
    # ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)

    # Your long-running code here
    try:
        #Things to do once a day:
        do_these_once_a_day = True
        if do_these_once_a_day:
            create_all_concordances(config, USE_LATEST_CONCORDANCES=True)
        
        PREPARE_DATA = True#only needs to be done if the macro or transport system data changes
        if PREPARE_DATA:
            import_macro_data(config, UPDATE_INDUSTRY_VALUES=False)
            import_transport_system_data(config)
        #####################################################################
        #since we're going to find that some economies have better base years than 2017 to start with, lets start changing the Base year vlaue and run the model economy by economy:
        ECONOMY_BASE_YEARS_DICT = yaml.load(open(config.root_dir + '\\' + 'config\\parameters.yml'), Loader=yaml.FullLoader)['ECONOMY_BASE_YEARS_DICT']
        ECONOMIES_TO_USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD_dict = yaml.load(open(config.root_dir + '\\' + 'config\\parameters.yml'), Loader=yaml.FullLoader)['ECONOMIES_TO_USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD']
        #####################################################################
        progress += increment
        update_progress(progress)
        FOUND = False
        RUN_MODEL = True#set me
        if not RUN_MODEL:
            MODEL_RUN_1  = False
            MODEL_RUN_2  = False
        else:
            MODEL_RUN_1  = True#set me
            MODEL_RUN_2  = True#set me
            
        for economy in ECONOMY_BASE_YEARS_DICT.keys():
            if economy_to_run == 'all' or 'all' in economy_to_run:
                pass
            elif economy in economy_to_run:
                pass
            elif economy == economy_to_run:
                pass
            else:
                continue
             
            print('\nRunning model for {}\n'.format(economy))
            ECONOMY_ID = economy
            BASE_YEAR = ECONOMY_BASE_YEARS_DICT[economy]
            
            create_and_clean_user_input(config, ECONOMY_ID)
            aggregate_data_for_model(config, ECONOMY_ID)
            progress += increment
            update_progress(progress)
            if MODEL_RUN_1:   
                print('\nDoing first model run for {}\n'.format(economy))   
                #MODEL RUN 1: (RUN MODEL FOR DATA BETWEEN AND INCLUDIONG BASE YEAR AND config.OUTLOOK_BASE_YEAR. This is important because we often dont have the data up to OUTLOOK_BASE_YEAR, so we have to model it. But its also important the data in the OUTLOOK_BASE_YEAR matches the energy use from ESTO. Otherwise we'd just model it all in one go)).
                #do this run to generate the base year (config.OUTLOOK_BASE_YEAR) data for the model
                PROJECT_TO_JUST_OUTLOOK_BASE_YEAR = True
                ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR = False
                
                #perform final filtering of data (eg for one economy only)
                supply_side_fuel_mixing, demand_side_fuel_mixing, road_model_input_wide, non_road_model_input_wide, growth_forecasts_wide = filter_for_modelling_years(config, BASE_YEAR, ECONOMY_ID, PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=PROJECT_TO_JUST_OUTLOOK_BASE_YEAR,ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR)
                calculate_inputs_for_model(config, road_model_input_wide,non_road_model_input_wide,growth_forecasts_wide, supply_side_fuel_mixing, demand_side_fuel_mixing, ECONOMY_ID, BASE_YEAR, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, adjust_data_to_match_esto_TESTING=False)
                
                if BASE_YEAR == config.OUTLOOK_BASE_YEAR:
                    #since we wont run the model, just fill the input with requried output cols and put nans in them
                    fill_missing_output_cols_with_nans(config, ECONOMY_ID, road_model_input_wide, non_road_model_input_wide)
                else:
                    run_road_model_df = run_road_model(config, ECONOMY_ID)
                    run_non_road_model(config, ECONOMY_ID, USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD = ECONOMIES_TO_USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD_dict[ECONOMY_ID])
                model_output_all = concatenate_model_output(config, ECONOMY_ID, PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=PROJECT_TO_JUST_OUTLOOK_BASE_YEAR)
                model_output_with_fuel_mixing = apply_fuel_mix_demand_side(config, model_output_all,ECONOMY_ID)
                model_output_with_fuel_mixing = apply_fuel_mix_supply_side(config, model_output_with_fuel_mixing,ECONOMY_ID)
                clean_model_output(config, ECONOMY_ID, model_output_with_fuel_mixing, model_output_all)
            
            progress += increment
            update_progress(progress)
            #below are required for MODEL_RUN_2. only chasnge them if you just want to run the model for the base year and not the whole period
            PROJECT_TO_JUST_OUTLOOK_BASE_YEAR = False
            ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR = True
            if MODEL_RUN_2:
                print('\nDoing 2nd model run for {}\n'.format(economy))
                #MODEL RUN 1: (RUN MODEL FOR DATA BETWEEN  AND INCLUDIONG BASE YEAR AND config.OUTLOOK_BASE_YEAR)
                #perform final filtering of data (eg for one economy only)
                supply_side_fuel_mixing, demand_side_fuel_mixing, road_model_input_wide, non_road_model_input_wide, growth_forecasts_wide = filter_for_modelling_years(config, BASE_YEAR, ECONOMY_ID, PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=PROJECT_TO_JUST_OUTLOOK_BASE_YEAR,ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR)
                calculate_inputs_for_model(config, road_model_input_wide,non_road_model_input_wide,growth_forecasts_wide, supply_side_fuel_mixing, demand_side_fuel_mixing, ECONOMY_ID, BASE_YEAR, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, adjust_data_to_match_esto_TESTING=False, USE_PREVIOUS_OPTIMISATION_RESULTS_FOR_THIS_DATA_SYSTEM_INPUT=USE_PREVIOUS_OPTIMISATION_RESULTS_FOR_THIS_DATA_SYSTEM_INPUT, USE_SAVED_OPT_PARAMATERS=USE_SAVED_OPT_PARAMATERS)
                aggregate_data_for_model(config, ECONOMY_ID)
                run_road_model_df = run_road_model(config, ECONOMY_ID)
                
                run_non_road_model(config, ECONOMY_ID,USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD=ECONOMIES_TO_USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD_dict[ECONOMY_ID])
                
                model_output_all = concatenate_model_output(config, ECONOMY_ID, PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=PROJECT_TO_JUST_OUTLOOK_BASE_YEAR)
                model_output_with_fuel_mixing = apply_fuel_mix_demand_side(config, model_output_all,ECONOMY_ID=ECONOMY_ID)
                model_output_with_fuel_mixing = apply_fuel_mix_supply_side(config, model_output_with_fuel_mixing,ECONOMY_ID=ECONOMY_ID)
                
                clean_model_output(config, ECONOMY_ID, model_output_with_fuel_mixing, model_output_all)
                
                #now concatenate all the model outputs together
                create_output_for_outlook_data_system(config, ECONOMY_ID)

                ANALYSE_OUTPUT = True
                ARCHIVE_PREVIOUS_DASHBOARDS = False
                if ANALYSE_OUTPUT: 
                    estimate_kw_of_required_chargers(config, ECONOMY_ID)
                    plot_required_chargers(config, ECONOMY_ID)
                    calculate_and_plot_oil_displacement(config, ECONOMY_ID)  
                    ###################do bunkers calc for this economy###################
                    international_bunker_share_calculation_handler(config, ECONOMY_ID=ECONOMY_ID)
                    ###################do bunkers calc for this economy###################
                    try:
                        produce_lots_of_LMDI_charts(config, ECONOMY_ID, USE_LIST_OF_CHARTS_TO_PRODUCE = True, PLOTTING = True, USE_LIST_OF_DATASETS_TO_PRODUCE=True, END_DATE=2070)
                    except:
                        print('produce_lots_of_LMDI_charts() not working for {}'.format(ECONOMY_ID))
                        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                            breakpoint()
                        pass
                    dashboard_creation_handler(config, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, ECONOMY_ID, ARCHIVE_PREVIOUS_DASHBOARDS=ARCHIVE_PREVIOUS_DASHBOARDS) 
                
                progress += increment
                update_progress(progress)
                copy_required_output_files_to_one_folder(config, ECONOMY_ID=ECONOMY_ID, output_folder_path='output_data\\for_other_modellers')
        
        print('\nFinished running model for all economies, now doing final formatting\n')
        
        concatenate_outlook_data_system_outputs(config)
        
        progress += increment
        update_progress(progress)
        
        SETUP_AND_RUN_MULTI_ECONOMY_PLOTS = True
        if concatenate_output_data(config):
            international_bunker_share_calculation_handler(config)
            if SETUP_AND_RUN_MULTI_ECONOMY_PLOTS:
                try:
                    produce_lots_of_LMDI_charts(config, ECONOMY_ID='all', USE_LIST_OF_CHARTS_TO_PRODUCE = True, PLOTTING = True, USE_LIST_OF_DATASETS_TO_PRODUCE=True, END_DATE=2070)
                except:
                    breakpoint()
                    print('produce_lots_of_LMDI_charts() not working for {}'.format(ECONOMY_ID))
                    produce_lots_of_LMDI_charts(config, ECONOMY_ID='all', USE_LIST_OF_CHARTS_TO_PRODUCE = True, PLOTTING = True, USE_LIST_OF_DATASETS_TO_PRODUCE=True, END_DATE=2070)
                try:
                    PRODUCE_ONLY_AGGREGATE_OF_ALL_ECONOMIES = True
                    setup_and_run_multi_economy_plots(config,ONLY_AGG_OF_ALL=PRODUCE_ONLY_AGGREGATE_OF_ALL_ECONOMIES)
                except:
                    breakpoint()
                    PRODUCE_ONLY_AGGREGATE_OF_ALL_ECONOMIES = True
                    setup_and_run_multi_economy_plots(config,ONLY_AGG_OF_ALL=PRODUCE_ONLY_AGGREGATE_OF_ALL_ECONOMIES)
                
            # except:
            #     pass#usually happens because the economies in ECONOMIES_WITH_MODELLING_COMPLETE_DICT havent been run for this file date id. check extract_non_road_modelled_data(config) in international_bunkers
        copy_required_output_files_to_one_folder(config, output_folder_path='output_data\\for_other_modellers')
        
        progress += increment
        update_progress(progress)
        # ARCHIVE_INPUT_DATA = False
        # if ARCHIVE_INPUT_DATA:
        #     #set up archive folder:
        #     archiving_folder = archiving_scripts.create_archiving_folder_for_FILE_DATE_ID(config)
        #     archiving_scripts.archive_lots_of_files(config, archiving_folder)    
        ARCHIVE_RESULTS=False
        if ARCHIVE_RESULTS:
            economies_to_archive = ['01_AUS', '21_VN', '07_INA']
            for economy in economies_to_archive:
                folder_name = utility_functions.save_economy_projections_and_all_inputs(config, economy, ARCHIVED_FILE_DATE_ID=config.FILE_DATE_ID)
        UNARCHIVE_RESULTS=False
        if UNARCHIVE_RESULTS:
            folder_name =None# 'output_data\\archived_runs\\20_USA_20230902_2331'
            # archiving_scripts.revert_to_previous_version_of_files(config, '03_CDA', 'output_dataarchived_runs03_CDA_20230902_1626', CURRENT_FILE_DATE_ID='20230902')
        COMPLETED = True
    except Exception as e:
        error_message = str(e)
        print('Error in main(): {}'.format(error_message))
        COMPLETED=False
        # return config.FILE_DATE_ID, COMPLETED, error_message
    return config.FILE_DATE_ID, COMPLETED, error_message
    #     # Restore the original state
    #     ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
#%%

if __name__ == "__main__":
    # sys.argv[0] is the script name, so arguments start from sys.argv[1]
    #if theres more than 1 argument and we're runinng this from the command line (need to check that the second arg doesnt wend with .json, that is in there if we are running this through jupyter notebook i think)
    if (len(sys.argv)) > 1 and (sys.argv[1][-5:] != '.json'):
        for arg in sys.argv[1:]:
            root_dir_param = sys.argv[2]
            economy_to_run = sys.argv[1]
            print('Running model for economy {}'.format(economy_to_run), 'in root directory {}'.format(root_dir_param))
            main(economy_to_run=economy_to_run, root_dir_param=root_dir_param, script_dir_param=root_dir_param) #e.g. python transport_model_9th_edition/main.py all C:\Users\finbar.maunsell\github\transport_model_9th_edition
            #e.g. python transport_model_9th_edition/main.py all /var/www/transport-modeling-guide/transport_model_9th_edition
            # os.chdir('C:\\Users\\finbar.maunsell\\github')
            # root_dir_param = 'C:\\Users\\finbar.maunsell\\github\\transport_model_9th_edition'#intensiton is to run this in  debug moode so we can easily find bugs.
    else:
        # os.chdir('C:\\Users\\finbar.maunsell\\github')
        # root_dir_param = 'C:\\Users\\finbar.maunsell\\github\\transport_model_9th_edition'#intensiton is to run this in  debug moode so we can easily find bugs.
        main('all')#, root_dir_param=root_dir_param)
    # root_dir_param = 
#%%
# %%
#   '01_AUS': 1
#   '02_BD': 1
#   '03_CDA': 1 #canada return is super weird. it goes higher than it was prevoouisly. so just dropping it to 0.5 compared to 1 for everyone else
#   '04_CHL': 1
#   '05_PRC': 1
#   '06_HKC': 1
#   '07_INA': 1
#   '08_JPN': 1
#   '09_ROK': 1
#   '10_MAS': 1
#   '11_MEX': 1
#   '12_NZ': 1
#   '13_PNG': 1
#   '14_PE': 1
#   '15_PHL': 1
#   '16_RUS': 1
#   '17_SGP': 1
#   '18_CT': 1
#   '19_THA': 1
#   '20_USA': 1
#   '21_VN': 1