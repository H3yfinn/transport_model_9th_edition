
#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re

# Get the directory of the current script (main.py) regardless of where it's run from
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the root dir, relative to the script's location
root_dir = re.split('transport_model_9th_edition', script_dir)[0] + '\\transport_model_9th_edition'
# Check if the first path is not already in sys.path, then append it
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Construct the second path to check, also relative to the script's location
path_to_add_2 = os.path.join(root_dir, 'config')
# Check if the second path is not already in sys.path, then append it
if path_to_add_2 not in sys.path:
    sys.path.append(path_to_add_2)


    
#################
current_working_dir = os.getcwd()
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = re.split('transport_model_9th_edition', script_dir)[0] + 'transport_model_9th_edition'
if current_working_dir == script_dir: #this allows the script to be run directly or from the main.py file as you cannot use relative imports when running a script directly
    # Modify sys.path to include the directory where utility_functions is located
    sys.path.append(f"{root_dir}/workflow/utility_functions")
    sys.path.append(f"{root_dir}/config")
    import config
    import utility_functions
else:
    # Assuming the script is being run from main.py located at the root of the project, we want to avoid using sys.path.append and instead use relative imports 
    from ..utility_functions import *
    from ...config.config import *
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
#PREPARATION FUNCTIONS
sys.path.append(f"{root_dir}/workflow/preparation_functions")
import concordance_scripts
import import_macro_data
import import_transport_system_data
import create_and_clean_user_input
import aggregate_data_for_model
import filter_for_modelling_years
#UTILITY FUNCTIONS
sys.path.append(f"{root_dir}/workflow/utility_functions")
import archiving_scripts
import utility_functions
#CALCUALTION FUNCTIONS
sys.path.append(f"{root_dir}/workflow/calculation_functions")
import calculate_inputs_for_model
import run_road_model
import run_non_road_model
import apply_fuel_mix_demand_side
import apply_fuel_mix_supply_side
import estimate_charging_requirements
import international_bunkers
#FORMATTING FUNCTIONS
sys.path.append(f"{root_dir}/workflow/formatting_functions")
import concatenate_model_output
import clean_model_output
import create_output_for_outlook_data_system
#PLOTTING FUNCTIONS
sys.path.append(f"{root_dir}/workflow/plotting_functions")
import produce_LMDI_graphs
import plot_charging_graphs
import create_assumptions_dashboards
import calculate_and_plot_oil_displacement
import compare_esto_energy_to_data

USE_PREVIOUS_OPTIMISATION_RESULTS_FOR_THIS_DATA_SYSTEM_INPUT=True
USE_SAVED_OPT_PARAMATERS=True   
#%%
def main():
    #Things to do once a day:
    do_these_once_a_day = True
    if do_these_once_a_day:
        concordance_scripts.create_all_concordances()
    
    PREPARE_DATA = True
    if PREPARE_DATA:
        import_macro_data.import_macro_data(UPDATE_INDUSTRY_VALUES=False)
        import_transport_system_data.import_transport_system_data()
        
    #####################################################################
    #since we're going to find that some economies have better base years than 2017 to start with, lets start changing the Base year vlaue and run the model economy by economy:
    ECONOMY_BASE_YEARS_DICT = yaml.load(open(root_dir + '/' + 'config/parameters.yml'), Loader=yaml.FullLoader)['ECONOMY_BASE_YEARS_DICT']
    ECONOMIES_TO_USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD_dict = yaml.load(open(root_dir + '/' + 'config/parameters.yml'), Loader=yaml.FullLoader)['ECONOMIES_TO_USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD']
    #####################################################################
    FOUND = False
    for economy in ECONOMY_BASE_YEARS_DICT.keys():
        # try:#TRY EXCEPT TO SKIP ECONOMIES THAT CAUSE ERRORS
        
        #completed:
        completed = [ '20_USA', '19_THA']
        #13_PNGbreakpoint()#for some reason china Max activity error margin is 788.7959117456285. need to debug this - also doesnt worrk for sales shares so that should be dealt with first.
        #02_BD # for some reason has a differnece between esto data. I think that we need to check the nonn road data during optimisation
        #malaysia 10_MAS showing same problems as bd. theis is esp for diesel/petrol
        errors = ['02_BD', '13_PNG']# '13_PNG', #png always cuaisng issues cause system data not ready yet. need to fix this
        #doing 
        doing =['07_INA']# [ '15_PHL','10_MAS', '18_CT','05_PRC','09_ROK','01_AUS', ['20_USA','07_INA']#  '15_PHL']#'05_PRC', '08_JPN', '03_CDA','09_ROK', '18_CT', '17_SGP', '01_AUS']#stopped in optimisation 
        fixing_elec_issue = ['19_THA']
        #not run yet 
        not_run_yet = ['14_PE', '16_RUS', '21_VN']
        #assumptions not completed but model works:
        assumptions_not_completed_but_model_works =  ['04_CHL', '06_HKC', '07_INA', '11_MEX', '15_PHL', '12_NZ']
        # if economy!= '12_NZ':
        #     continue
        # if economy == '03_CDA':
        #     pass
        # doing = ['09_ROK', '10_MAS','05_PRC', '18_CT', '17_SGP', '01_AUS']#'08_JPN', '03_CDA', 
        if economy in ['03_CDA']:#, '13_PNG']:#'16_RUS','11_MEX', '06_HKC', '12_NZ', '10_MAS', '15_PHL', '13_PNG']:#, '15_PHL','02_BD', '12_NZ','21_VN','10_MAS'
            pass
        else:
            continue
   
        # if economy != 
        #     pass
        # else:
        #     continue
        #     FOUND = True
        # elif FOUND == False:
        #     continue
        
        # elif economy in errors:# (economy in doing) or (economy in completed) or (economy in not_run_yet)or (economy in assumptions_not_completed_but_model_works) or (economy in errors): #(economy in doing):
        #     continue
        # if economy == '15_PHL' or economy == '21_VN':#economy == '01_AUS' or economy == '07_INA' or economy == '10_MAS' or
        #     pass
        # elif not FOUND:
        #     continue
        #     # # pass
        #     # if economy ==  '05_PRC':
        #     #     pass
        #     # else:
        # if economy not in ['13_PNG', '02_BD', '06_HKC', '04_CHL'] and FOUND:
        #     pass
        # elif economy == '04_CHL':
        #     FOUND = True
        #     continue
        # else:
        #     continue
        # if economy in ['13_PNG']:#,'15_PHL']:#,'15_PHL']:#', '07_INA']:#, '19_THA', '01_AUS']:#in ['21_VN',  ,'01_AUS',  '10_MAS', '07_INA']:#'13_PNG':#'01_AUS':# :#n ['03_CDA', '07_INA']:#'03_CDA', '13_PNG', '14_PE', '16_RUS']:#'03_CDA','09_ROK', '18_CT', '05_PRC', '17_SGP', '21_VN', '15_PHL', '01_AUS', '10_MAS', , '20_USA', '19_THA', '08_JPN'
        # #not working '04_CHL', #'15_PHL':#
        #     pass
        # else:
        #     continue
        # breakpoint()
        # if economy not in errors:# and FOUND:
        #     pass
        # if economy not in ['13_PNG', '02_BD']:, '01_AUS']:# =='01_AUS':
        #     FOUND = True
        #     pass#continue
        # else:
        #     continue
        # elif economy == '01_AUS':
        #     FOUND = True
        #     continue
        # else:
        #     continue
        # elif (economy in completed) or (economy in errors) or (economy in assumptions_not_completed_but_model_works):
        #     continue
        # elif (economy not in doing) and (economy not in not_run_yet):
        #     raise ValueError('Economy {} not in doing or not_run_yet. Not expected'.format(economy))

        print('\nRunning model for {}\n'.format(economy))
        ECONOMY_ID = economy
        BASE_YEAR = ECONOMY_BASE_YEARS_DICT[economy]
        
        create_and_clean_user_input.create_and_clean_user_input(ECONOMY_ID)
        aggregate_data_for_model.aggregate_data_for_model(ECONOMY_ID)
        MODEL_RUN_1  = True
        if MODEL_RUN_1:   
            print('\nDoing first model run for {}\n'.format(economy))   
            #MODEL RUN 1: (RUN MODEL FOR DATA BETWEEN AND INCLUDIONG BASE YEAR AND config.OUTLOOK_BASE_YEAR. This is important because we often dont have the data up to OUTLOOK_BASE_YEAR, so we have to model it. But its also important the data in the OUTLOOK_BASE_YEAR matches the energy use from ESTO. Otherwise we'd just model it all in one go)).
            #do this run to generate the base year (config.OUTLOOK_BASE_YEAR) data for the model
            PROJECT_TO_JUST_OUTLOOK_BASE_YEAR = True
            ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR = False
            
            #perform final filtering of data (eg for one economy only)
            supply_side_fuel_mixing, demand_side_fuel_mixing, road_model_input_wide, non_road_model_input_wide, growth_forecasts_wide = filter_for_modelling_years.filter_for_modelling_years(BASE_YEAR, ECONOMY_ID, PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=PROJECT_TO_JUST_OUTLOOK_BASE_YEAR,ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR)
            calculate_inputs_for_model.calculate_inputs_for_model(road_model_input_wide,non_road_model_input_wide,growth_forecasts_wide, supply_side_fuel_mixing, demand_side_fuel_mixing, ECONOMY_ID, BASE_YEAR, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, adjust_data_to_match_esto_TESTING=False)
            if BASE_YEAR == config.OUTLOOK_BASE_YEAR:
                #since we wont run the model, just fill the input with requried output cols and put nans in them
                concatenate_model_output.fill_missing_output_cols_with_nans(ECONOMY_ID, road_model_input_wide, non_road_model_input_wide)
            else:
                run_road_model_df = run_road_model.run_road_model(ECONOMY_ID)
                run_non_road_model.run_non_road_model(ECONOMY_ID, USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD = ECONOMIES_TO_USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD_dict[ECONOMY_ID])
            
            model_output_all = concatenate_model_output.concatenate_model_output(ECONOMY_ID, PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=PROJECT_TO_JUST_OUTLOOK_BASE_YEAR)
            model_output_with_fuel_mixing = apply_fuel_mix_demand_side.apply_fuel_mix_demand_side(model_output_all,ECONOMY_ID)
            model_output_with_fuel_mixing = apply_fuel_mix_supply_side.apply_fuel_mix_supply_side(model_output_with_fuel_mixing,ECONOMY_ID)
            clean_model_output.clean_model_output(ECONOMY_ID, model_output_with_fuel_mixing, model_output_all)
            
        MODEL_RUN_2  = True
        if MODEL_RUN_2:
            print('\nDoing 2nd model run for {}\n'.format(economy))
            #MODEL RUN 1: (RUN MODEL FOR DATA BETWEEN  AND INCLUDIONG BASE YEAR AND config.OUTLOOK_BASE_YEAR)
            PROJECT_TO_JUST_OUTLOOK_BASE_YEAR = False
            ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR = True
            #perform final filtering of data (eg for one economy only)
            supply_side_fuel_mixing, demand_side_fuel_mixing, road_model_input_wide, non_road_model_input_wide, growth_forecasts_wide = filter_for_modelling_years.filter_for_modelling_years(BASE_YEAR, ECONOMY_ID, PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=PROJECT_TO_JUST_OUTLOOK_BASE_YEAR,ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR)
            calculate_inputs_for_model.calculate_inputs_for_model(road_model_input_wide,non_road_model_input_wide,growth_forecasts_wide, supply_side_fuel_mixing, demand_side_fuel_mixing, ECONOMY_ID, BASE_YEAR, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, adjust_data_to_match_esto_TESTING=False, USE_PREVIOUS_OPTIMISATION_RESULTS_FOR_THIS_DATA_SYSTEM_INPUT=USE_PREVIOUS_OPTIMISATION_RESULTS_FOR_THIS_DATA_SYSTEM_INPUT, USE_SAVED_OPT_PARAMATERS=USE_SAVED_OPT_PARAMATERS)
            aggregate_data_for_model.aggregate_data_for_model(ECONOMY_ID)
            
            run_road_model_df = run_road_model.run_road_model(ECONOMY_ID)
            
            run_non_road_model.run_non_road_model(ECONOMY_ID,USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD=ECONOMIES_TO_USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD_dict[ECONOMY_ID])
            
            model_output_all = concatenate_model_output.concatenate_model_output(ECONOMY_ID, PROJECT_TO_JUST_OUTLOOK_BASE_YEAR=PROJECT_TO_JUST_OUTLOOK_BASE_YEAR)
            model_output_with_fuel_mixing = apply_fuel_mix_demand_side.apply_fuel_mix_demand_side(model_output_all,ECONOMY_ID=ECONOMY_ID)
            model_output_with_fuel_mixing = apply_fuel_mix_supply_side.apply_fuel_mix_supply_side(model_output_with_fuel_mixing,ECONOMY_ID=ECONOMY_ID)
            
            clean_model_output.clean_model_output(ECONOMY_ID, model_output_with_fuel_mixing, model_output_all)
            
            #now concatenate all the model outputs together
            create_output_for_outlook_data_system.create_output_for_outlook_data_system(ECONOMY_ID)

            # exec(open(f"{root_dir}/workflow/6_create_osemosys_output.py").read())
            # import create_osemosys_output
            # create_osemosys_output.create_osemosys_output()
            # ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=True
            ANALYSE_OUTPUT = True
            ARCHIVE_PREVIOUS_DASHBOARDS = False
            if ANALYSE_OUTPUT: 
                estimate_charging_requirements.estimate_kw_of_required_chargers(ECONOMY_ID)
                plot_charging_graphs.plot_required_chargers(ECONOMY_ID)
                calculate_and_plot_oil_displacement.calculate_and_plot_oil_displacement(ECONOMY_ID)   
                # produce_LMDI_graphs.produce_lots_of_LMDI_charts(ECONOMY_ID, USE_LIST_OF_CHARTS_TO_PRODUCE = True, PLOTTING = True, USE_LIST_OF_DATASETS_TO_PRODUCE=False, END_DATE=2035)
                # produce_LMDI_graphs.produce_lots_of_LMDI_charts(ECONOMY_ID, USE_LIST_OF_CHARTS_TO_PRODUCE = True, PLOTTING = True, USE_LIST_OF_DATASETS_TO_PRODUCE=False, END_DATE=2050)
                ###################do bunkers calc for this economy###################
                international_bunkers.international_bunker_share_calculation_handler(ECONOMY_ID=ECONOMY_ID)
                ###################do bunkers calc for this economy###################
                try:
                    produce_LMDI_graphs.produce_lots_of_LMDI_charts(ECONOMY_ID, USE_LIST_OF_CHARTS_TO_PRODUCE = True, PLOTTING = True, USE_LIST_OF_DATASETS_TO_PRODUCE=True, END_DATE=2070)
                except:
                    print('produce_lots_of_LMDI_charts() not working for {}'.format(ECONOMY_ID))
                    breakpoint()
                    pass
                create_assumptions_dashboards.dashboard_creation_handler(ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, ECONOMY_ID, ARCHIVE_PREVIOUS_DASHBOARDS=ARCHIVE_PREVIOUS_DASHBOARDS)
                #TEMP
                # if ECONOMY_ID=='08_JPN':
                #     create_assumptions_dashboards.dashboard_creation_handler(ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, ECONOMY_ID, ARCHIVE_PREVIOUS_DASHBOARDS=ARCHIVE_PREVIOUS_DASHBOARDS, PREVIOUS_PROJECTION_FILE_DATE_ID='20231101')
                # compare_esto_energy_to_data.compare_esto_energy_to_data()#UNDER DEVELOPMENT   
                
            utility_functions.copy_required_output_files_to_one_folder(ECONOMY_ID=ECONOMY_ID, output_folder_path='output_data/for_other_modellers')
                
                
                
        # except Exception as e:#TRY EXCEPT TO SKIP ECONOMIES THAT CAUSE ERRORS
                
        #     #add the economy to the txt of errors
        #     print('Error for economy {} so skipping it'.format(economy))
        #     #open txt file and add the error and economy and timestamp to it
        #     with open(root_dir + '/' + 'errors.txt', 'a') as f:
        #         f.write('Error for economy {} so skipping it. Error is {}. Time is {}\n'.format(economy, e, datetime.datetime.now()))
            
    # international_bunkers.international_bunker_share_calculation_handler()
    print('\nFinished running model for all economies, now doing final formatting\n')
    
    create_output_for_outlook_data_system.concatenate_outlook_data_system_outputs()
    
    clean_model_output.concatenate_output_data()
    try:
        international_bunkers.international_bunker_share_calculation_handler()
    except:
        raise ValueError('international_bunkers.international_bunker_share_calculation_handler() not working')
        # breakpoint()
        # pass#usually happens because the economies in ECONOMIES_WITH_MODELLING_COMPLETE_DICT havent been run for this file date id. check extract_non_road_modelled_data() in international_bunkers
    utility_functions.copy_required_output_files_to_one_folder(output_folder_path='output_data/for_other_modellers')
    
    # ARCHIVE_INPUT_DATA = False
    # if ARCHIVE_INPUT_DATA:
    #     #set up archive folder:
    #     archiving_folder = archiving_scripts.create_archiving_folder_for_FILE_DATE_ID()
    #     archiving_scripts.archive_lots_of_files(archiving_folder)

    ARCHIVE_RESULTS=False
    if ARCHIVE_RESULTS:
        economies_to_archive = ['06_HKC', '11_MEX', '21_VN']#'11_MEX',
        for economy in economies_to_archive:
            folder_name = archiving_scripts.save_economy_projections_and_all_inputs(economy, ARCHIVED_FILE_DATE_ID=config.FILE_DATE_ID)
    UNARCHIVE_RESULTS=False
    if UNARCHIVE_RESULTS:
        folder_name =None# 'output_data/archived_runs/20_USA_20230902_2331'
        # archiving_scripts.revert_to_previous_version_of_files('03_CDA', 'output_data/archived_runs/03_CDA_20230902_1626', CURRENT_FILE_DATE_ID='20230902')
#%%
main()#python workflow/main.py > output.txt 2>&1
#testing what happens to the file road_model_input_wide = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_aggregated_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID)) if i run png vs usa.
#seems like something in C:\Users\finbar.maunsell\github\transport_model_9th_edition\workflow\calculation_functions\adjust_data_to_match_esto.py is causing the issue.
#%%

# utility_functions.copy_required_output_files_to_one_folder(ECONOMY_ID='06_HKC', output_folder_path='output_data/for_other_modellers')
#pull in ./EGEDA_2020_created_14112022.csv then split it into multiple files, one for each economy
# ARCHIVE_RESULTS=True
# if ARCHIVE_RESULTS:
#     economies_to_archive = ['21_VN', '15_PHL', '01_AUS', '10_MAS', '07_INA']
#     for economy in economies_to_archive:
#         folder_name = archiving_scripts.save_economy_projections_and_all_inputs(economy, ARCHIVED_FILE_DATE_ID=config.FILE_DATE_ID)
        
# folder_name = archiving_scripts.save_economy_projections_and_all_inputs('15_PHL', ARCHIVED_FILE_DATE_ID=config.FILE_DATE_ID)
#%%
# ARCHIVE_RESULTS=True
# if ARCHIVE_RESULTS:
#     economies_to_archive = ['08_JPN', '20_USA', '19_THA', '03_CDA']#, '08_JPN']
#     for economy in economies_to_archive:
#         folder_name = archiving_scripts.save_economy_projections_and_all_inputs(economy, ARCHIVED_FILE_DATE_ID=config.FILE_DATE_ID)
#%%

#%%
#%%   

#%%