#most important thing is to save the input and CONCORDANCES data to a folder in case we need to use that data again. 
# This saves the archived data to a folder with the date id. If the user needs to use that then they will use a separate script to extract the information they need from the data (as of 2022 this is not yet implemented)

#name folder with the config.FILE_DATE_ID

###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
current_working_dir = os.getcwd()
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = re.split('transport_model_9th_edition', script_dir)[0] + 'transport_model_9th_edition'
from . import config
from . import utility_functions
#################

import datetime
import shutil
import pandas as pd

###
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive 
# notebook in vscode #or set to notebook

def create_archiving_folder_for_FILE_DATE_ID():
    #create folder
    #if file data id is '' then just save the data to foler 'latest_test_run' as we assume this run isnt important enough to save the data in a unique folder
    if config.FILE_DATE_ID == '':
        archive_folder_name = root_dir + '/' + 'input_data/previous_run_archive/latest_test_run'
    else:
        archive_folder_name = root_dir + '/' + 'input_data/previous_run_archive/' + config.FILE_DATE_ID
        #since config.FILE_DATE_ID might not be the actual day, we need to create a subfolder for the actual day
        
        if os.path.exists(archive_folder_name):
            import datetime
            new_FILE_DATE_ID = '_{}'.format(datetime.datetime.now().strftime("%Y%m%d"))#Note that this is not the official file date id anymore because it was interacting badly with how we should instead set it in onfig.py
            archive_folder_name = root_dir + '/' + 'input_data/previous_run_archive/' + config.FILE_DATE_ID +'/'+ new_FILE_DATE_ID
        
            if not os.path.exists(archive_folder_name):
                os.mkdir(archive_folder_name)
        else:
            if not os.path.exists(root_dir + '/' + 'input_data/previous_run_archive/'):
                os.mkdir('input_data/previous_run_archive/')
            os.mkdir(archive_folder_name)
    return archive_folder_name

def archive_lots_of_files(archive_folder_name):
    #load data that we want to archive 
    #t omake thigns simple while we havent got a clear idea of what we need we will just load and save the model inputs and fuel mixing data

    # #Major model inputs:

    #load output data
    model_output_detailed = pd.read_csv(root_dir + '/' + 'output_data/model_output_detailed/{}'.format(config.model_output_file_name))
    model_output_non_detailed = pd.read_csv(root_dir + '/' + 'output_data/model_output/{}'.format(config.model_output_file_name))
    model_output_all_with_fuels = pd.read_csv(root_dir + '/' + 'output_data/model_output_with_fuels/{}'.format(config.model_output_file_name))

    #save output data
    model_output_detailed.to_csv(root_dir + '/' + '{}/model_output_detailed.csv'.format(archive_folder_name))
    model_output_non_detailed.to_csv(root_dir + '/' + '{}/model_output_non_detailed.csv'.format(archive_folder_name))
    model_output_all_with_fuels.to_csv(root_dir + '/' + '{}/model_output_all_with_fuels.csv'.format(archive_folder_name))
    
    #save config file to folder
    shutil.copyfile(root_dir + '/' + 'code/config.py', '{}/config.py'.format(archive_folder_name))

    #save all code files to folder, incmluding all subfolders (they are the code).
    recursively_save_file(root_dir + '/' + './code', archive_folder_name, 'file_extension=.py', exclude_archive_folder=True)
    #save all csvs in \input_data\user_input_spreadsheets
    recursively_save_file(root_dir + '/' + 'input_data/user_input_spreadsheets', archive_folder_name, file_extension='.csv', exclude_archive_folder=True)
    recursively_save_file(f'intermediate_data/model_inputs/{config.FILE_DATE_ID}', archive_folder_name, file_extension='.csv', exclude_archive_folder=True)
    recursively_save_file(root_dir + '/' + 'output_data/for_other_modellers', archive_folder_name, exclude_archive_folder=True)
    
    #and save individual files
    fuel_mixing_assumptions = root_dir + '/' + 'input_data/fuel_mixing_assumptions.xlsx'
    shutil.copyfile(fuel_mixing_assumptions, '{}/fuel_mixing_assumptions.xlsx'.format(archive_folder_name))

    recursively_save_file(root_dir + '/' + 'config/concordances_and_config_data/computer_generated_concordances', archive_folder_name, '.csv', exclude_archive_folder=True)

    # zip_up_folder(archive_folder_name)
    
    
def recursively_save_file(source_dir, dest_dir, file_extension='*', exclude_archive_folder=True, keep_folder_structure=False):
    import os
    import shutil

    # create the destination directory if it doesn't already exist
    os.makedirs(dest_dir, exist_ok=True)

    # walk the source directory
    for dirpath, dirnames, filenames in os.walk(source_dir):
        for filename in filenames:
            if (filename.endswith(file_extension)) or (file_extension == '*'):
                dest_dir2 =dest_dir
                if exclude_archive_folder:
                    if '/archive' in dirpath:
                        continue
                # construct full file path
                full_file_path = os.path.join(dirpath, filename)
                if keep_folder_structure:
                    #create copy of folder structure in destination directory
                    folder_structure = dirpath.split(source_dir)[1]
                    dest_dir2 = dest_dir + folder_structure
                    if not os.path.exists(dest_dir2):
                        os.makedirs(dest_dir2)
                # copy file to destination directory
                shutil.copy2(full_file_path, dest_dir2)

    print('Done.')

#zip up the folder and save to C drive:
#for sdome reason this taskse ages.
def zip_up_folder(archive_folder_name):
    # if os.path.exists(root_dir + '/' + 'C:/Users/finbar.maunsell/Documents'):
        
    #     output_file = 'C:/Users/finbar.maunsell/Documents'#this is really cheating but it works for now
    # else:
    #     output_file = 'C:/Users/Finbar Maunsell/Documents'

    # create a zip archive with file date id
    output_file = archive_folder_name +'/'+ config.FILE_DATE_ID + '_0'
    #if it is already there then make the number at the end one higher
    while os.path.exists(output_file + '.zip'):
        output_file = output_file[:-1] + str(int(output_file[-1])+1)

    created_zip_file = shutil.make_archive(output_file,'zip',archive_folder_name)
    if not os.path.exists(created_zip_file):
        if os.path.exists(created_zip_file + '.zip'):
            os.rename(created_zip_file + '.zip', created_zip_file)#common error is that the file is saved with .zip.zip
        else:
            raise Exception('Zip file not found')
    print(f'Zipped up {archive_folder_name} to {output_file}.zip')


def save_economy_projections_and_all_inputs(ECONOMY_ID,  ZIP_UP_ARCHIVE_FOLDER=True, ARCHIVED_FILE_DATE_ID=None,transport_data_system_FILE_DATE_ID_2=None):
    """_summary_

    Args:
        ECONOMY_ID (_type_): _description_
        ZIP_UP_ARCHIVE_FOLDER (bool, optional): _description_. Defaults to True.
        ARCHIVED_FILE_DATE_ID (_type_, optional): _description_. Defaults to None.
        transport_data_system_FILE_DATE_ID_2 (_type_, optional): _description_. Defaults to None.

    Raises:
        Exception: _description_
        Exception: _description_
        Exception: _description_

    Returns:
        _type_: _description_
    """
    if ARCHIVED_FILE_DATE_ID is None:
        ARCHIVED_FILE_DATE_ID = config.FILE_DATE_ID
    ARCHIVED_FILE_DATE_ID_2 = ARCHIVED_FILE_DATE_ID
    if transport_data_system_FILE_DATE_ID_2 is None:
        transport_data_system_FILE_DATE_ID_2 = config.transport_data_system_FILE_DATE_ID
        #test whether we can find transport_model_9th_edition\intermediate_data\model_inputs\ f'intermediate_data/model_inputs/optimised_data_{ECONOMY_ID}_{ARCHIVED_FILE_DATE_ID}_{transport_data_system_FILE_DATE_ID_2}.pkl'
        # otherwise find the next latest ARCHIVED_FILE_DATE_ID:
        # 
        # e.g if there is no optimised_data_03_CDA_20240315_DATE20240312_DATE20240215.pkl see if there is a optimised_data_03_CDA_20240314_DATE20240312_DATE20240215.pkl
        if not os.path.exists(root_dir + '/' + f'intermediate_data/input_data_optimisations/optimised_data_{ECONOMY_ID}_{ARCHIVED_FILE_DATE_ID}_{transport_data_system_FILE_DATE_ID_2}.pkl'):
            ARCHIVED_FILE_DATE_ID_2 = utility_functions.get_latest_date_for_data_file(data_folder_path=root_dir + '/' +'intermediate_data/input_data_optimisations', file_name_start=f'optimised_data_{ECONOMY_ID}_', file_name_end=f'_{transport_data_system_FILE_DATE_ID_2}.pkl', EXCLUDE_DATE_STR_START=True)
            if ARCHIVED_FILE_DATE_ID == '':
                raise Exception(f'No optimised_data_{ECONOMY_ID}_{ARCHIVED_FILE_DATE_ID}_ found in intermediate_data/input_data_optimisations')
    #to make sure that we can reproduce the results of the model we need to save the inputs and outputs of the model when we decide we have finished for an economy. So we will gather all the inputs and save them to a folder. There wil also be a function for loading the inputs and outputs and saving them to the correct place in the folder structure so that we can reproduce the results of the model.
    # The results should be zipped up by the user and put in a safe place.
    #we will save all data in output_data/archived_runs, with the FILE_DATE_ID and economy_id in the name of the folder plus, the time in minutes/hours
    #create folder:
    archive_folder_name = root_dir + '/' + 'output_data/archived_runs/{}_{}'.format(ECONOMY_ID, ARCHIVED_FILE_DATE_ID) + '_' + datetime.datetime.now().strftime("%H%M") 
    
    if not os.path.exists(archive_folder_name):
        os.mkdir(archive_folder_name)
    else:
        print('WARNING: archive folder already exists. This will overwrite the data in that folder')
        #ask user if they want to continue
        user_input = input('{} already exists. Do you want to continue? (y/n)'.format(archive_folder_name))
        if user_input == 'y':
            pass
        else:
            raise Exception('User chose not to continue')
    

    
    #the data we will need to save will be:
    # config/parameters.yml
    # code/config.py
    # intermediate_data/computer_generated_concordances/model_concordances_{FILE_DATE_ID}_demand_side_fuel_mixing
    # intermediate_data/computer_generated_concordances/model_concordances_{FILE_DATE_ID}_supply_side_fuel_mixing
    # model_concordances_user_input_and_growth_rates_{FILE_DATE_ID}
    # model_concordances_fuels_NO_BIOFUELS_{FILE_DATE_ID}
    # model_concordances_measures_{FILE_DATE_ID}
    # model_concordances_fuels_{FILE_DATE_ID}
    model_output_file_name_2 = config.model_output_file_name.replace(config.FILE_DATE_ID, ARCHIVED_FILE_DATE_ID)
    files_list = ['config/parameters.yml','config/optimisation_parameters.yml', 'code/config.py', 'intermediate_data/computer_generated_concordances/model_concordances_{}_demand_side_fuel_mixing.csv'.format(ARCHIVED_FILE_DATE_ID), 'intermediate_data/computer_generated_concordances/model_concordances_{}_supply_side_fuel_mixing.csv'.format(ARCHIVED_FILE_DATE_ID), 'intermediate_data/computer_generated_concordances/model_concordances_measures_{}.csv'.format(ARCHIVED_FILE_DATE_ID), 'intermediate_data/computer_generated_concordances/model_concordances_fuels_{}.csv'.format(ARCHIVED_FILE_DATE_ID), f'intermediate_data/computer_generated_concordances/model_concordances_fuels_NO_BIOFUELS_{ARCHIVED_FILE_DATE_ID}.csv', f'intermediate_data/computer_generated_concordances/model_concordances_user_input_and_growth_rates_{ARCHIVED_FILE_DATE_ID}.csv', 'input_data/fuel_mixing_assumptions.xlsx', 'input_data/growth_coefficients_by_region.csv', 'input_data/parameters.xlsx', 'input_data/vehicle_sales_share_inputs.xlsx', 'intermediate_data/model_outputs/{}_input_data_based_on_previous_model_run_NON_ROAD_DETAILED_{}'.format(ECONOMY_ID, model_output_file_name_2), 'intermediate_data/model_outputs/{}_energy_use_output_NON_ROAD_DETAILED_{}'.format(ECONOMY_ID, model_output_file_name_2), 'intermediate_data/model_inputs/{}/{}_aggregated_demand_side_fuel_mixing.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), 'intermediate_data/model_inputs/{}/{}_supply_side_fuel_mixing.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), 'intermediate_data/model_inputs/{}/{}_road_model_input_wide.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), 'intermediate_data/model_inputs/{}/{}_non_road_model_input_wide.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), 'intermediate_data/model_inputs/{}/{}_growth_forecasts_wide.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), 'intermediate_data/road_model/{}_vehicles_per_stock_parameters.csv'.format(ECONOMY_ID), 'intermediate_data/road_model/{}_parameters_estimates_{}.csv'.format(ECONOMY_ID, ARCHIVED_FILE_DATE_ID), 'intermediate_data/model_inputs/{}/{}_stocks_per_capita_threshold.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), 'intermediate_data/road_model/{}_{}'.format(ECONOMY_ID, model_output_file_name_2), 'intermediate_data/road_model/first_run_{}_{}'.format(ECONOMY_ID, model_output_file_name_2), f'./intermediate_data/road_model/{ECONOMY_ID}_final_road_growth_forecasts.pkl', f'intermediate_data/model_inputs/{ARCHIVED_FILE_DATE_ID}/{ECONOMY_ID}_non_road_model_input_wide.csv', 'intermediate_data/model_inputs/{}/{}_road_model_input_wide.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), 'intermediate_data/model_inputs/{}/{}_growth_forecasts_wide.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), 'intermediate_data/model_inputs/{}/{}_demand_side_fuel_mixing.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), 'intermediate_data/model_inputs/{}/{}_supply_side_fuel_mixing.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), 'intermediate_data/model_inputs/transport_data_system_extract.csv', 'intermediate_data/model_inputs/{}/{}_vehicle_sales_share.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), 'output_data/model_output_detailed/{}_NON_ROAD_DETAILED_{}'.format(ECONOMY_ID, model_output_file_name_2), 'output_data/model_output/{}_NON_ROAD_DETAILED_{}'.format(ECONOMY_ID, model_output_file_name_2), 'output_data/model_output_with_fuels/{}_NON_ROAD_DETAILED_{}'.format(ECONOMY_ID, model_output_file_name_2), 'output_data/model_output_detailed/{}_{}'.format(ECONOMY_ID, model_output_file_name_2), 'output_data/model_output/{}_{}'.format(ECONOMY_ID, model_output_file_name_2), 'output_data/model_output_with_fuels/{}_{}'.format(ECONOMY_ID, model_output_file_name_2), 'intermediate_data/road_model/{}_{}'.format(ECONOMY_ID, model_output_file_name_2), 'intermediate_data/non_road_model/{}_{}'.format(ECONOMY_ID, model_output_file_name_2), 'intermediate_data/model_outputs/{}_{}'.format(ECONOMY_ID, model_output_file_name_2), f'output_data/for_other_modellers/output_for_outlook_data_system/{ECONOMY_ID}_{ARCHIVED_FILE_DATE_ID}_transport_energy_use.csv', 'output_data/model_output_with_fuels/{}_{}'.format(ECONOMY_ID, model_output_file_name_2), 'output_data/model_output_detailed/{}_{}'.format(ECONOMY_ID, model_output_file_name_2), f'output_data/for_other_modellers/output_for_outlook_data_system/{ECONOMY_ID}_{ARCHIVED_FILE_DATE_ID}_transport_energy_use.csv', 'output_data/for_other_modellers/charging/{}_estimated_number_of_chargers.csv'.format(ECONOMY_ID), 'intermediate_data/model_inputs/{}/{}_supply_side_fuel_mixing.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), 'intermediate_data/model_inputs/{}/{}_road_model_input_wide.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), 'output_data/model_output_detailed/{}_NON_ROAD_DETAILED_{}'.format(ECONOMY_ID, model_output_file_name_2), f'intermediate_data/model_inputs/{ARCHIVED_FILE_DATE_ID}/{ECONOMY_ID}_growth_forecasts_wide.csv', 'intermediate_data/road_model/first_run_{}_{}'.format(ECONOMY_ID, model_output_file_name_2), 'intermediate_data/model_inputs/{}/{}_vehicle_sales_share.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), 'intermediate_data/road_model/{}_parameters_estimates_{}.csv'.format(ECONOMY_ID, ARCHIVED_FILE_DATE_ID), 'input_data/from_8th/reformatted/activity_energy_road_stocks.csv', 'config/9th_edition_emissions_factors.csv', 'input_data/from_8th/reformatted/activity_energy_road_stocks.csv', 'input_data/from_8th/reformatted/8th_energy_by_fuel.csv', 'output_data/model_output/{}_{}'.format(ECONOMY_ID,model_output_file_name_2), 'intermediate_data/model_inputs/transport_data_system_extract.csv', f'intermediate_data/model_inputs/{ECONOMY_ID}_user_inputs_and_growth_rates.csv', 'intermediate_data/model_inputs/regression_based_growth_estimates.csv', 'intermediate_data/model_inputs/{}/{}_aggregated_road_model_input_wide.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), 'intermediate_data/model_inputs/{}/{}_aggregated_non_road_model_input_wide.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), 'intermediate_data/model_inputs/{}/{}_aggregated_growth_forecasts_wide.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), 'intermediate_data/model_inputs/{}/{}_stocks_per_capita_threshold.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), 'intermediate_data/model_inputs/{}/{}_supply_side_fuel_mixing.csv'.format(ARCHIVED_FILE_DATE_ID,ECONOMY_ID), 'intermediate_data/model_inputs/{}/{}_demand_side_fuel_mixing.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), 'intermediate_data/model_inputs/{}/{}_aggregated_supply_side_fuel_mixing.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), 'intermediate_data/model_inputs/{}/{}_aggregated_demand_side_fuel_mixing.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), f'intermediate_data/model_inputs/{ARCHIVED_FILE_DATE_ID}/{ECONOMY_ID}_aggregated_road_model_input_wide.csv', 'intermediate_data/model_inputs/{}/{}_aggregated_non_road_model_input_wide.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), 'intermediate_data/model_inputs/{}/{}_aggregated_growth_forecasts_wide.csv'.format(ARCHIVED_FILE_DATE_ID, ECONOMY_ID), 'intermediate_data/model_inputs/regression_based_growth_estimates.csv', '../transport_data_system/output_data/combined_data_{}.csv'.format(transport_data_system_FILE_DATE_ID_2)] 
    #, 'intermediate_data/road_model/covid_related_mileage_change_{}.csv'.format(ECONOMY_ID)
    #files that are sometimes not htere:
    sometimes_files = ['intermediate_data/model_outputs/{}_medium_to_medium_activity_change_for_plotting{}.csv'.format(ECONOMY_ID, config.FILE_DATE_ID)]#i dont know hwy this file is sometimes not there. need to figure it out.
    for file in sometimes_files:
        if os.path.exists(root_dir + '/' + file):
            files_list.append(root_dir + '/' + file)
    
    #save all files in files_list by copying them to the archive folder. but save them so they have the same folder structure as they do in the transport model folder. This will make it easier to load them later
    # breakpoint()#such file or directory: 'transport_data_system/output_data/combined_data_DATE20230902.c
    for file in files_list:
        #create folder structure
        dotdot = False
        if '/' in file:
            if file.startswith(root_dir + '/' + '../transport_data_system'):
                file = file[3:]
                dotdot = True
                #this is a file that is in the transport_data_system folder. We need to save it to the archive folder. when we resave it later we will save it to the transport_data_system folder
            folder_structure = file.split('/')[:-1]
            folder_structure = '/'.join(folder_structure)
            if not os.path.exists(archive_folder_name+'/'+folder_structure):
                os.makedirs(archive_folder_name+'/'+folder_structure)
        
        if os.path.exists(archive_folder_name+'/'+file):
            print(f'WARNING: {file} already exists in archive folder. Must already have been saved there')
            
        if dotdot:
            shutil.copyfile(root_dir + '/' + '../' +file, archive_folder_name+'/'+file)
        else:
            shutil.copyfile(root_dir + '/' + file, archive_folder_name+'/'+file)
        
    # #for inputs not dated with {FILE_DATE_ID} we will save the latest version of the file
    # energy_use_esto = pd.read_csv(root_dir + '/' +f'input_data/9th_model_inputs/model_df_wide_{date_id}.csv')
    date_id = utility_functions.get_latest_date_for_data_file(root_dir + '/' + 'input_data/9th_model_inputs', 'model_df_wide_')
    #create folder structure
    if not os.path.exists(archive_folder_name+'/input_data/9th_model_inputs'):
        os.makedirs(archive_folder_name+'/input_data/9th_model_inputs')
    shutil.copyfile(root_dir + '/' + f'input_data/9th_model_inputs/model_df_wide_{date_id}.csv', archive_folder_name+f'/input_data/9th_model_inputs/model_df_wide_{date_id}.csv')
    
    macro_date_id = utility_functions.get_latest_date_for_data_file(root_dir + '/' + 'input_data/macro', 'APEC_GDP_data_')
    # macro_df_wide = pd.read_csv(root_dir + '/' +f'input_data\macro\APEC_GDP_data_{macro_date_id}.csv')
    #create folder structure
    if not os.path.exists(archive_folder_name+'/input_data/macro'):
        os.makedirs(archive_folder_name+'/input_data/macro')
    shutil.copyfile(root_dir + '/' + f'input_data/macro/APEC_GDP_data_{macro_date_id}.csv', archive_folder_name+f'/input_data/macro/APEC_GDP_data_{macro_date_id}.csv')
    
    #data that we sometimes use previous verrsions of for optimisations:
    # , f'intermediate_data/model_inputs/optimised_data_{ECONOMY_ID}_{ARCHIVED_FILE_DATE_ID_2}_{transport_data_system_FILE_DATE_ID_2}.pkl'
    optimisation_data_date_id =utility_functions.get_latest_date_for_data_file(root_dir + '/' + 'intermediate_data/input_data_optimisations', f'optimised_data_{ECONOMY_ID}_', f'_{transport_data_system_FILE_DATE_ID_2}.pkl', EXCLUDE_DATE_STR_START=True)
    if not os.path.exists(root_dir + '/' + f'intermediate_data/input_data_optimisations/optimised_data_{ECONOMY_ID}_{optimisation_data_date_id}_{transport_data_system_FILE_DATE_ID_2}.pkl'):
        raise Exception(f'No optimised_data_{ECONOMY_ID}_{optimisation_data_date_id}_{transport_data_system_FILE_DATE_ID_2}.pkl found in intermediate_data/input_data_optimisations')
    shutil.copyfile(root_dir + '/' + f'intermediate_data/input_data_optimisations/optimised_data_{ECONOMY_ID}_{optimisation_data_date_id}_{transport_data_system_FILE_DATE_ID_2}.pkl', archive_folder_name+f'/intermediate_data/input_data_optimisations/optimised_data_{ECONOMY_ID}_{optimisation_data_date_id}_{transport_data_system_FILE_DATE_ID_2}.pkl')
    
    #move the bunkers data
    date_id = utility_functions.get_latest_date_for_data_file(root_dir + '/' + 'output_data/for_other_modellers/output_for_outlook_data_system', '{}_international_bunker_energy_use_'.format(ECONOMY_ID))
    if not os.path.exists(archive_folder_name+'/output_data/for_other_modellers/output_for_outlook_data_system'):
        os.makedirs(archive_folder_name+'/output_data/for_other_modellers/output_for_outlook_data_system')
        
    shutil.copyfile(root_dir + '/' + 'output_data/for_other_modellers/output_for_outlook_data_system/{}_international_bunker_energy_use_{}.csv'.format(ECONOMY_ID,date_id), archive_folder_name+'/output_data/for_other_modellers/output_for_outlook_data_system/{}_international_bunker_energy_use_{}.csv'.format(ECONOMY_ID,date_id))
    
    #do same thing but for international_bunker_energy_use_{date_id}.csv
    shutil.copyfile(root_dir + '/' + 'output_data/for_other_modellers/output_for_outlook_data_system/international_bunker_energy_use_{}.csv'.format(date_id), archive_folder_name+'/output_data/for_other_modellers/output_for_outlook_data_system/international_bunker_energy_use_{}.csv'.format(date_id))
    
    #save all data in teh output_data/for_other_modellers/{ECONOMY_ID} folder
    if not os.path.exists(archive_folder_name+'/output_data/for_other_modellers/{}'.format(ECONOMY_ID)):
        os.makedirs(archive_folder_name+'/output_data/for_other_modellers/{}'.format(ECONOMY_ID))
    for file in os.listdir('output_data/for_other_modellers/{}'.format(ECONOMY_ID)):
        shutil.copyfile(root_dir + '/' + 'output_data/for_other_modellers/{}/'.format(ECONOMY_ID)+file, archive_folder_name+'/output_data/for_other_modellers/{}/'.format(ECONOMY_ID)+file)
            
    # input_data/fuel_mixing_assumptions.xlsx
    # input_data/growth_coefficients_by_region.csv
    # input_data/parameters.xlsx
    # input_data/vehicle_sales_share_inputs.xlsx
    # input_data\user_input_spreadsheets/*
    if not os.path.exists(archive_folder_name+'/input_data/user_input_spreadsheets'):
        os.makedirs(archive_folder_name+'/input_data/user_input_spreadsheets')
    for file in os.listdir('input_data/user_input_spreadsheets'):
        if file.endswith('.csv'):
            shutil.copyfile(root_dir + '/' + 'input_data/user_input_spreadsheets/'+file, archive_folder_name+'/input_data/user_input_spreadsheets/'+file)
    
    # # if availabel
    #     change_dataframe_aggregation.to_csv(f'intermediate_data/road_model/change_dataframe_aggregation_{ECONOMY_ID}.csv', index=False)
    if os.path.exists(root_dir + '/' + 'intermediate_data/road_model/change_dataframe_aggregation_{}.csv'.format(ECONOMY_ID)):
        if not os.path.exists(archive_folder_name+'/intermediate_data/road_model'):
            os.makedirs(archive_folder_name+'/intermediate_data/road_model')
        shutil.copyfile(root_dir + '/' + 'intermediate_data/road_model/change_dataframe_aggregation_{}.csv'.format(ECONOMY_ID), archive_folder_name+ '/intermediate_data/road_model/change_dataframe_aggregation_{}.csv'.format(ECONOMY_ID))
        
    #save all data in dashboards folder for this economy:
    if not os.path.exists(archive_folder_name+f'/plotting_output/dashboards/{ECONOMY_ID}'):
        os.makedirs(archive_folder_name+f'/plotting_output/dashboards/{ECONOMY_ID}')
    for file in os.listdir(root_dir + '/' + f'plotting_output/dashboards/{ECONOMY_ID}'):
        if file.endswith('.html'):
            shutil.copyfile(root_dir + '/' + f'plotting_output/dashboards/{ECONOMY_ID}/'+file, archive_folder_name+f'/plotting_output/dashboards/{ECONOMY_ID}/'+file)              
                
    #save entire code folder
    recursively_save_file(root_dir + '/' + './code', archive_folder_name+'/code', file_extension='.py', exclude_archive_folder=True, keep_folder_structure=True) 
    
    #save all csvs in config\concordances_and_config_data/* 
    if not os.path.exists(archive_folder_name+'/config/concordances_and_config_data'):
        os.makedirs(archive_folder_name+'/config/concordances_and_config_data')
    for file in os.listdir('config/concordances_and_config_data'):
        if file.endswith('.csv'):
            shutil.copyfile(root_dir + '/' + 'config/concordances_and_config_data/'+file, archive_folder_name+'/config/concordances_and_config_data/'+file)
    
    if ZIP_UP_ARCHIVE_FOLDER:
        # Create the zip archive
        created_zip_file  = shutil.make_archive(archive_folder_name, 'zip', archive_folder_name)
        #CHECK THE NEW ZIP FILE IS THERE
        if not os.path.exists(created_zip_file):
            # if os.path.exists(created_zip_file + '.zip'):
            #     os.rename(created_zip_file + '.zip', created_zip_file)#common error is that the file is saved with .zip.zip
            # else:
            raise Exception('Zip file not found')
        else:
            #delete the folder
            shutil.rmtree(archive_folder_name)
        
    return archive_folder_name
    # # #save them for archiving because they will be overwritten later
    # # input_data_based_on_previous_model_run.to_csv(root_dir + '/' + 'intermediate_data/model_outputs/{}_input_data_based_on_previous_model_run_NON_ROAD_DETAILED_{}'.format(ECONOMY_ID, config.model_output_file_name))
    # # energy_use_output.to_csv(root_dir + '/' + 'intermediate_data/model_outputs/{}_energy_use_output_NON_ROAD_DETAILED_{}'.format(ECONOMY_ID, config.model_output_file_name))
      
    # covid_related_mileage_change.to_csv(f'./intermediate_data/road_model/covid_related_mileage_change_{ECONOMY_ID}.csv', index=False)
    #     demand_side_fuel_mixing = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_aggregated_demand_side_fuel_mixing.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))        
    #     supply_side_fuel_mixing =  pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_supply_side_fuel_mixing.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))
        
    # road_model_input_wide.to_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
    # non_road_model_input_wide.to_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_non_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
    # growth_forecasts_wide.to_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_growth_forecasts_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
    
    # #     vehicles_per_stock_parameters.to_csv(root_dir + '/' + 'intermediate_data/road_model/{}_vehicles_per_stock_parameters.csv'.format(ECONOMY_ID), index=False)
    #find latest version of vehicles_per_stock_parameters
    # #save parameters_estimates. at the very elast we will plot these later
    # parameters_estimates.to_csv(root_dir + '/' + 'intermediate_data/road_model/{}_parameters_estimates_{}.csv'.format(ECONOMY_ID, config.FILE_DATE_ID), index=False)
    # gompertz_parameters = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_stocks_per_capita_threshold.csv'.format(config.FILE_DATE_ID,ECONOMY_ID))
    # new_output_file = 'intermediate_data/road_model/{}_{}'.format(ECONOMY_ID, config.model_output_file_name)
    # new_output_file = 'intermediate_data/road_model/first_run_{}_{}'.format(ECONOMY_ID, config.model_output_file_name)
        
    # if USE_ROAD_ACTIVITY_GROWTH_RATES_FOR_NON_ROAD:
    #     growth_forecasts = pd.read_pickle(f'./intermediate_data/road_model/{ECONOMY_ID}_final_road_growth_forecasts.pkl')
    # else:
    #     growth_forecasts = pd.read_csv(root_dir + '/' +f'intermediate_data/model_inputs/{config.FILE_DATE_ID}/{ECONOMY_ID}_growth_forecasts_wide.csv')
    # #load all other data
    # non_road_model_input = pd.read_csv(root_dir + '/' +f'intermediate_data/model_inputs/{config.FILE_DATE_ID}/{ECONOMY_ID}_non_road_model_input_wide.csv')
    # output_file_name = 'intermediate_data/non_road_model/{}_{}'.format(ECONOMY_ID, config.model_output_file_name)
    # road_model_input = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))
    # growth_forecasts = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_growth_forecasts_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))
    # demand_side_fuel_mixing.to_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_demand_side_fuel_mixing.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
    # supply_side_fuel_mixing.to_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_supply_side_fuel_mixing.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
    # transport_data_system_df = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/transport_data_system_extract.csv')
    # #save data so it can be used for plotting and such:
    # new_sales_shares_all_new.to_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_vehicle_sales_share.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index = False)
    # #save data without the new drive cols for non road
    # model_output_detailed.to_csv(root_dir + '/' + 'output_data/model_output_detailed/{}_NON_ROAD_DETAILED_{}'.format(ECONOMY_ID, config.model_output_file_name), index=False
    # model_output_non_detailed.to_csv(root_dir + '/' + 'output_data/model_output/{}_NON_ROAD_DETAILED_{}'.format(ECONOMY_ID, config.model_output_file_name), index=False
    # model_output_all_with_fuels.to_csv(root_dir + '/' + 'output_data/model_output_with_fuels/{}_NON_ROAD_DETAILED_{}'.format(ECONOMY_ID, config.model_output_file_name), index=False)
    # model_output_detailed.to_csv(root_dir + '/' + 'output_data/model_output_detailed/{}_{}'.format(ECONOMY_ID, config.model_output_file_name), index=False)
    # model_output_non_detailed.to_csv(root_dir + '/' + 'output_data/model_output/{}_{}'.format(ECONOMY_ID, config.model_output_file_name), index=False)
    # model_output_all_with_fuels.to_csv(root_dir + '/' + 'output_data/model_output_with_fuels/{}_{}'.format(ECONOMY_ID, config.model_output_file_name), index=False)
    # road_model_output = pd.read_csv(root_dir + '/' + 'intermediate_data/road_model/{}_{}'.format(ECONOMY_ID, config.model_output_file_name))
    # non_road_model_output = pd.read_csv(root_dir + '/' + 'intermediate_data/non_road_model/{}_{}'.format(ECONOMY_ID, config.model_output_file_name))
    # model_output_all.to_csv(root_dir + '/' + 'intermediate_data/model_outputs/{}_{}'.format(ECONOMY_ID, config.model_output_file_name), index=False)
    # road_model_input_wide.to_csv(root_dir + '/' + 'intermediate_data/road_model/{}_{}'.format(ECONOMY_ID, config.model_output_file_name), index=False)
    # non_road_model_input_wide.to_csv(root_dir + '/' + 'intermediate_data/non_road_model/{}_{}'.format(ECONOMY_ID, config.model_output_file_name), index=False)
    # model_output_all_with_fuels = pd.read_csv(root_dir + '/' + 'output_data/model_output_with_fuels/{}_NON_ROAD_DETAILED_{}'.format(ECONOMY_ID, config.model_output_file_name))
    # #save this file to output_data\for_other_modellers
    # new_final_df.to_csv(f'output_data/for_other_modellers/output_for_outlook_data_system/{ECONOMY_ID}_{config.FILE_DATE_ID}_transport_energy_use.csv', index=False)
    # for economy in ECONOMY_IDs:
    #     model_output_with_fuels_ = pd.read_csv(root_dir + '/' + 'output_data/model_output_with_fuels/{}_{}'.format(ECONOMY_ID, config.model_output_file_name))
    #     model_output_detailed_ = pd.read_csv(root_dir + '/' + 'output_data/model_output_detailed/{}_{}'.format(ECONOMY_ID, config.model_output_file_name))
    #     energy_output_for_outlook_data_system_ = pd.read_csv(root_dir + '/' +f'output_data/for_other_modellers/output_for_outlook_data_system/{ECONOMY_ID}_{config.FILE_DATE_ID}_transport_energy_use.csv')
    #     chargers_ = pd.read_csv(root_dir + '/' + 'output_data/for_other_modellers/charging/{}_estimated_number_of_chargers.csv'format(ECONOMY_ID))
    #     supply_side_fuel_mixing_ = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_supply_side_fuel_mixing.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))
    #     road_model_input_ = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))
    #     model_output_detailed_detailed_non_road_drives_ = pd.read_csv(root_dir + '/' + 'output_data/model_output_detailed/{}_NON_ROAD_DETAILED_{}'.format(ECONOMY_ID, config.model_output_file_name))
    #     growth_forecasts_ = pd.read_csv(root_dir + '/' +f'intermediate_data/model_inputs/{config.FILE_DATE_ID}/{ECONOMY_ID}_growth_forecasts_wide.csv')
    #     first_road_model_run_data_ = pd.read_csv(root_dir + '/' + 'intermediate_data/road_model/first_run_{}_{}'.format(ECONOMY_ID, config.model_output_file_name))
    #     new_sales_shares_all_plot_drive_shares_ = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_vehicle_sales_share.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))
    #     gompertz_parameters_df_ = pd.read_csv(root_dir + '/' + 'intermediate_data/road_model/{}_parameters_estimates_{}.csv'.format(ECONOMY_ID, config.FILE_DATE_ID))
    # original_model_output_8th = pd.read_csv(root_dir + '/' + 'input_data/from_8th/reformatted/activity_energy_road_stocks.csv').rename(columns={'Year':'Date'})
    # emissions_factors = pd.read_csv(root_dir + '/' + 'config/9th_edition_emissions_factors.csv')
    # date_id = utility_functions.get_latest_date_for_data_file(root_dir + '/' + 'input_data/9th_model_inputs', 'model_df_wide_')
    # energy_use_esto = pd.read_csv(root_dir + '/' +f'input_data/9th_model_inputs/model_df_wide_{date_id}.csv')
    # data_8th = pd.read_csv(root_dir + '/' + 'input_data/from_8th/reformatted/activity_energy_road_stocks.csv')
    # energy_8th = pd.read_csv(root_dir + '/' + 'input_data/from_8th/reformatted/8th_energy_by_fuel.csv')
    #     all_data = pd.read_csv(root_dir + '/' + 'output_data/model_output/{}_{}'.format(ECONOMY_ID,config.model_output_file_name))
    # new_transport_dataset = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/transport_data_system_extract.csv')
    # user_input = pd.read_csv(root_dir + '/' +f'intermediate_data/model_inputs/{ECONOMY_ID}_user_inputs_and_growth_rates.csv')
    # growth = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/regression_based_growth_estimates.csv')
    # #save data    
    # road_model_input_wide.to_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_aggregated_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
    # non_road_model_input_wide.to_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_aggregated_non_road_model_input_wide.csv'.format(config.FILE_DATE_ID,ECONOMY_ID), index=False)
    # growth_forecasts_wide.to_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_aggregated_growth_forecasts_wide.csv'.format(config.FILE_DATE_ID,ECONOMY_ID), index=False)
    # stocks_per_capita_threshold.to_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_stocks_per_capita_threshold.csv'.format(config.FILE_DATE_ID,ECONOMY_ID), index=False)
    # #lastly resave these files before they get changed in the modelling process
    # supply_side_fuel_mixing = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_supply_side_fuel_mixing.csv'.format(config.FILE_DATE_ID,ECONOMY_ID))
    # demand_side_fuel_mixing = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_demand_side_fuel_mixing.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))
    # supply_side_fuel_mixing.to_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_aggregated_supply_side_fuel_mixing.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
    # demand_side_fuel_mixing.to_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_aggregated_demand_side_fuel_mixing.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
    # #save the new_user_inputs
    # user_input_new.to_csv(f'intermediate_data/model_inputs/{ECONOMY_ID}_user_inputs_and_growth_rates.csv', index=False)
    # supply_side_fuel_mixing = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_aggregated_supply_side_fuel_mixing.csv'.format(config.FILE_DATE_ID,ECONOMY_ID))
    # demand_side_fuel_mixing = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_aggregated_demand_side_fuel_mixing.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))
    # road_model_input_wide = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_aggregated_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))
    # non_road_model_input_wide = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_aggregated_non_road_model_input_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))
    # growth_forecasts_wide = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/{}/{}_aggregated_growth_forecasts_wide.csv'.format(config.FILE_DATE_ID, ECONOMY_ID))
    # macro2.to_csv(root_dir + '/' + 'intermediate_data/model_inputs/regression_based_growth_estimates.csv', index=False)
    # transport_data_system_folder = '../transport_data_system'
    # transport_data_system_df = pd.read_csv(root_dir + '/' + '{}/output_data/combined_data_{}.csv'.format(transport_data_system_folder,config.transport_data_system_FILE_DATE_ID))
    

#reverse the process. Note that this is done to all files so first it will archive the current files (so if we want to revert the changes we can just copy them back, using this same function)
def revert_to_previous_version_of_files(economy, archive_folder_name, UNZIP_ARCHIVE_FOLDER=True, CURRENT_FILE_DATE_ID=None):
    if CURRENT_FILE_DATE_ID==None:
        CURRENT_FILE_DATE_ID = config.FILE_DATE_ID
    save_economy_projections_and_all_inputs(economy, ARCHIVED_FILE_DATE_ID=CURRENT_FILE_DATE_ID)#save current state of files
    
    if UNZIP_ARCHIVE_FOLDER:
        
        #double check the zip file is there
        if not os.path.exists(archive_folder_name+'.zip'):
            # #check its not there as .zip.zip
            # if os.path.exists(archive_folder_name+'.zip.zip'):
            #     os.rename(archive_folder_name+'.zip.zip', archive_folder_name+'.zip')
            # else:
            raise Exception('zip file not found')
        # Unzip the archive
        shutil.unpack_archive(archive_folder_name+'.zip', archive_folder_name)
        #double check the folder is there
        if not os.path.exists(archive_folder_name):
            raise Exception('Folder not found')
    #now using the previous files, save them all back where they came from. However, dont overwrite the files in code/utility_functions/* since that includes this function!
    #also, if the file is in the transport_data_system folder, add ../ to the start of the file name so that it is saved in the transport_data_system folder
    #recursively go through all files in the archive_folder_name and save them back to where they came from (except for the files in code/utility_functions/* and transport_data_system/*, which will be saved in the transport_data_system folder)
    breakpoint()#NOTE AFTER CREATING root_dir + '/' + FUNCTIONALITY, I DONT KNOW IF THIS IS WORKING SO IF SET IT TO RAISE AN ERROR
    raise Exception('STOPPED HERE')
    for root, dirs, files in os.walk(archive_folder_name):
        for file in files:
            if file.endswith('.py') or file.endswith('.yaml') or file.endswith('.yaml') or file.endswith('.csv') or file.endswith('.xlsx') or file.endswith('.pkl') or file.endswith('.html'):
                #remove the 'output_data/archived_runs'+ archive_folder_name from the start of the root
                root = root.replace(archive_folder_name, root_dir + '/' + '')
                root = root.strip('\\')
                
                if root.startswith('code/utility_functions'):
                    continue
                if root.startswith(root_dir + '/' +'transport_data_system'):
                    #check folder exists
                    if not os.path.exists(root_dir + '/' + '../'+root):
                        os.makedirs('../'+root)
                    #save file in transport_data_system folder
                    shutil.copyfile(root+'/'+file, '../'+root+'/'+file)
                else:
                    #check folder exists
                    if not os.path.exists(root):
                        os.makedirs(root)
                    #save file in the same place it came from
                    shutil.copyfile(archive_folder_name +'/'+ root+'/'+file, root+'/'+file)
    
    #great all done! Now we can run the model again and it will use the previous files
    

#%%
import os
import shutil

def copy_folder_structure(src, dest):
    for dirpath, dirnames, filenames in os.walk(src):
        # Create the same directory structure in the destination folder
        structure = os.path.join(dest, os.path.relpath(dirpath, src))
        if not os.path.isdir(structure):
            os.mkdir(structure)
        
        # Add a .gitkeep file in each folder
        with open(os.path.join(structure, ".gitkeep"), "w") as f:
            pass

# # Replace 'source_folder' and 'destination_folder' with your actual folder paths
# source_folder = "./plotting_output"
# destination_folder = "./plotting_output"

# source_folder = "./output_data"
# destination_folder = "./output_data"


# source_folder = "./intermediate_data"
# destination_folder = "./intermediate_data"
# # Create the destination folder if it doesn't exist
# if not os.path.exists(destination_folder):
#     os.makedirs(destination_folder)

# copy_folder_structure(source_folder, destination_folder)
def remove_gitkeep_files(src):
    for dirpath, dirnames, filenames in os.walk(src):
        gitkeep_path = os.path.join(dirpath, ".gitkeep")
        if os.path.isfile(gitkeep_path):
            os.remove(gitkeep_path)
            
# # Replace 'folder' with your actual folder path
# folder = "./env_transport_model"
# remove_gitkeep_files(folder)
#%%
