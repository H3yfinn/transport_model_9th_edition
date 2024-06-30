
#%%

###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
current_working_dir = os.getcwd()
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir =  "\\\\?\\" + re.split('transport_model_9th_edition', script_dir)[0] + 'transport_model_9th_edition'
# from model_code import config, preparation_functions, utility_functions, calculation_functions, formatting_functions, plotting_functions
from model_code import config
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
from model_code.plotting_functions import dashboard_creation_handler
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
def main(economy_to_run='all', progress_callback=None):
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
    
    # Prevent the system from going to sleep
    # ctypes.windll.kernel32.SetThreadExecutionState(0x80000002)
    # To restore the original state, use:
    # ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)

    # Your long-running code here
    try:
        #Things to do once a day:
        do_these_once_a_day = True
        if do_these_once_a_day:
            create_all_concordances()
        
        PREPARE_DATA = True
        if PREPARE_DATA:
            import_macro_data(UPDATE_INDUSTRY_VALUES=False)
            import_transport_system_data()
        #####################################################################
        #since we're going to find that some economies have better base years than 2017 to start with, lets start changing the Base year vlaue and run the model economy by economy:
        ECONOMY_BASE_YEARS_DICT = yaml.load(open(root_dir + '\\' + 'config\\parameters.yml'), Loader=yaml.FullLoader)['ECONOMY_BASE_YEARS_DICT']
        ECONOMIES_TO_USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD_dict = yaml.load(open(root_dir + '\\' + 'config\\parameters.yml'), Loader=yaml.FullLoader)['ECONOMIES_TO_USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD']
        #####################################################################
        progress += increment
        update_progress(progress)
        FOUND = False
        for economy in ECONOMY_BASE_YEARS_DICT.keys():
            if economy_to_run == 'all':
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
            
            create_and_clean_user_input(ECONOMY_ID)
            aggregate_data_for_model(ECONOMY_ID)
            progress += increment
            update_progress(progress)
            MODEL_RUN_1  = True
            if MODEL_RUN_1:   
                print('\nDoing first model run for {}\n'.format(economy))   
                #MODEL RUN 1: (RUN MODEL FOR DATA BETWEEN AND INCLUDIONG BASE YEAR AND config.OUTLOOK_BASE_YEAR. This is important because we often dont have the data up to OUTLOOK_BASE_YEAR, so we have to model it. But its also important the data in the OUTLOOK_BASE_YEAR matches the energy use from ESTO. Otherwise we'd just model it all in one go)).
                #do this run to generate the base year (config.OUTLOOK_BASE_YEAR) data for the model
                PROJECT_TO_JUST_OUTLOOK_BASE_YEAR = True
                ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR = False
                
                #perform final filtering of data (eg for one economy only)
                supply_side_fuel_mixing, demand_side_fuel_mixing, road_model_input_wide, non_road_model_input_wide, growth_forecasts_wide = filter_for_modelling_years(BASE_YEAR, ECONOMY_ID, PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=PROJECT_TO_JUST_OUTLOOK_BASE_YEAR,ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR)
                calculate_inputs_for_model(road_model_input_wide,non_road_model_input_wide,growth_forecasts_wide, supply_side_fuel_mixing, demand_side_fuel_mixing, ECONOMY_ID, BASE_YEAR, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, adjust_data_to_match_esto_TESTING=False)
                if BASE_YEAR == config.OUTLOOK_BASE_YEAR:
                    #since we wont run the model, just fill the input with requried output cols and put nans in them
                    fill_missing_output_cols_with_nans(ECONOMY_ID, road_model_input_wide, non_road_model_input_wide)
                else:
                    run_road_model_df = run_road_model(ECONOMY_ID)
                    run_non_road_model(ECONOMY_ID, USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD = ECONOMIES_TO_USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD_dict[ECONOMY_ID])
                model_output_all = concatenate_model_output(ECONOMY_ID, PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=PROJECT_TO_JUST_OUTLOOK_BASE_YEAR)
                model_output_with_fuel_mixing = apply_fuel_mix_demand_side(model_output_all,ECONOMY_ID)
                model_output_with_fuel_mixing = apply_fuel_mix_supply_side(model_output_with_fuel_mixing,ECONOMY_ID)
                clean_model_output(ECONOMY_ID, model_output_with_fuel_mixing, model_output_all)
            
            progress += increment
            update_progress(progress)
            MODEL_RUN_2  = True
            if MODEL_RUN_2:
                print('\nDoing 2nd model run for {}\n'.format(economy))
                #MODEL RUN 1: (RUN MODEL FOR DATA BETWEEN  AND INCLUDIONG BASE YEAR AND config.OUTLOOK_BASE_YEAR)
                PROJECT_TO_JUST_OUTLOOK_BASE_YEAR = False
                ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR = True
                #perform final filtering of data (eg for one economy only)
                supply_side_fuel_mixing, demand_side_fuel_mixing, road_model_input_wide, non_road_model_input_wide, growth_forecasts_wide = filter_for_modelling_years(BASE_YEAR, ECONOMY_ID, PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=PROJECT_TO_JUST_OUTLOOK_BASE_YEAR,ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR)
                calculate_inputs_for_model(road_model_input_wide,non_road_model_input_wide,growth_forecasts_wide, supply_side_fuel_mixing, demand_side_fuel_mixing, ECONOMY_ID, BASE_YEAR, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, adjust_data_to_match_esto_TESTING=False, USE_PREVIOUS_OPTIMISATION_RESULTS_FOR_THIS_DATA_SYSTEM_INPUT=USE_PREVIOUS_OPTIMISATION_RESULTS_FOR_THIS_DATA_SYSTEM_INPUT, USE_SAVED_OPT_PARAMATERS=USE_SAVED_OPT_PARAMATERS)
                aggregate_data_for_model(ECONOMY_ID)
                run_road_model_df = run_road_model(ECONOMY_ID)
                
                run_non_road_model(ECONOMY_ID,USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD=ECONOMIES_TO_USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD_dict[ECONOMY_ID])
                
                model_output_all = concatenate_model_output(ECONOMY_ID, PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=PROJECT_TO_JUST_OUTLOOK_BASE_YEAR)
                model_output_with_fuel_mixing = apply_fuel_mix_demand_side(model_output_all,ECONOMY_ID=ECONOMY_ID)
                model_output_with_fuel_mixing = apply_fuel_mix_supply_side(model_output_with_fuel_mixing,ECONOMY_ID=ECONOMY_ID)
                
                clean_model_output(ECONOMY_ID, model_output_with_fuel_mixing, model_output_all)
                
                #now concatenate all the model outputs together
                create_output_for_outlook_data_system(ECONOMY_ID)

                # exec(open(f"{root_dir}\\code\\6_create_osemosys_output.py").read())
                # import create_osemosys_output
                # create_osemosys_output.create_osemosys_output()
                # ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=True
                ANALYSE_OUTPUT = True
                ARCHIVE_PREVIOUS_DASHBOARDS = False
                if ANALYSE_OUTPUT: 
                    estimate_kw_of_required_chargers(ECONOMY_ID)
                    plot_required_chargers(ECONOMY_ID)
                    calculate_and_plot_oil_displacement(ECONOMY_ID)   
                    # produce_LMDI_graphs.produce_lots_of_LMDI_charts(ECONOMY_ID, USE_LIST_OF_CHARTS_TO_PRODUCE = True, PLOTTING = True, USE_LIST_OF_DATASETS_TO_PRODUCE=False, END_DATE=2035)
                    # produce_LMDI_graphs.produce_lots_of_LMDI_charts(ECONOMY_ID, USE_LIST_OF_CHARTS_TO_PRODUCE = True, PLOTTING = True, USE_LIST_OF_DATASETS_TO_PRODUCE=False, END_DATE=2050)
                    ###################do bunkers calc for this economy###################
                    international_bunker_share_calculation_handler(ECONOMY_ID=ECONOMY_ID)
                    ###################do bunkers calc for this economy###################
                    try:
                        produce_lots_of_LMDI_charts(ECONOMY_ID, USE_LIST_OF_CHARTS_TO_PRODUCE = True, PLOTTING = True, USE_LIST_OF_DATASETS_TO_PRODUCE=True, END_DATE=2070)
                    except:
                        print('produce_lots_of_LMDI_charts() not working for {}'.format(ECONOMY_ID))
                        breakpoint()
                        pass
                    dashboard_creation_handler(ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, ECONOMY_ID, ARCHIVE_PREVIOUS_DASHBOARDS=ARCHIVE_PREVIOUS_DASHBOARDS)
                    # compare_esto_energy_to_data.compare_esto_energy_to_data()#UNDER DEVELOPMENT   
                
                progress += increment
                update_progress(progress)
                copy_required_output_files_to_one_folder(ECONOMY_ID=ECONOMY_ID, output_folder_path='output_data\\for_other_modellers')
                    
                    
                    
            # except Exception as e:#TRY EXCEPT TO SKIP ECONOMIES THAT CAUSE ERRORS
                    
            #     #add the economy to the txt of errors
            #     print('Error for economy {} so skipping it'.format(economy))
            #     #open txt file and add the error and economy and timestamp to it
            #     with open(root_dir + '\\' + 'errors.txt', 'a') as f:
            #         f.write('Error for economy {} so skipping it. Error is {}. Time is {}\n'.format(economy, e, datetime.datetime.now()))
                    
                    
                
                
        # international_bunkers.international_bunker_share_calculation_handler()
        print('\nFinished running model for all economies, now doing final formatting\n')
        concatenate_outlook_data_system_outputs()
        
        progress += increment
        update_progress(progress)
        concatenate_output_data()
        try:
            international_bunker_share_calculation_handler()
        except:
            pass#usually happens because the economies in ECONOMIES_WITH_MODELLING_COMPLETE_DICT havent been run for this file date id. check extract_non_road_modelled_data() in international_bunkers
        copy_required_output_files_to_one_folder(output_folder_path='output_data\\for_other_modellers')
    
        progress += increment
        update_progress(progress)
        # ARCHIVE_INPUT_DATA = False
        # if ARCHIVE_INPUT_DATA:
        #     #set up archive folder:
        #     archiving_folder = archiving_scripts.create_archiving_folder_for_FILE_DATE_ID()
        #     archiving_scripts.archive_lots_of_files(archiving_folder)    
        ARCHIVE_RESULTS=False
        if ARCHIVE_RESULTS:
            economies_to_archive = ['01_AUS', '21_VN', '07_INA']
            for economy in economies_to_archive:
                folder_name = utility_functions.save_economy_projections_and_all_inputs(economy, ARCHIVED_FILE_DATE_ID=config.FILE_DATE_ID)
        UNARCHIVE_RESULTS=False
        if UNARCHIVE_RESULTS:
            folder_name =None# 'output_data\\archived_runs\\20_USA_20230902_2331'
            # archiving_scripts.revert_to_previous_version_of_files('03_CDA', 'output_data\\archived_runs\\03_CDA_20230902_1626', CURRENT_FILE_DATE_ID='20230902')
    finally:
        pass
    #     # Restore the original state
    #     ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
#%%

if __name__ == "__main__":
    main()  # python code/main.py > output.txt 2>&1
4#%%