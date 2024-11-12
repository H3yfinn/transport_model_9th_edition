import os
import sys
import re
import datetime
import shutil
import pandas as pd

from . import utility_functions

def create_archiving_folder_for_FILE_DATE_ID(config):
    # Create folder
    if config.FILE_DATE_ID == '':
        archive_folder_name = os.path.join(config.root_dir, 'input_data', 'previous_run_archive', 'latest_test_run')
    else:
        archive_folder_name = os.path.join(config.root_dir, 'input_data', 'previous_run_archive', config.FILE_DATE_ID)
        if os.path.exists(archive_folder_name):
            new_FILE_DATE_ID = '_{}'.format(datetime.datetime.now().strftime("%Y%m%d"))
            archive_folder_name = os.path.join(config.root_dir, 'input_data', 'previous_run_archive', config.FILE_DATE_ID, new_FILE_DATE_ID)
            if not os.path.exists(archive_folder_name):
                os.mkdir(archive_folder_name)
        else:
            if not os.path.exists(os.path.join(config.root_dir, 'input_data', 'previous_run_archive')):
                os.mkdir(os.path.join(config.root_dir, 'input_data', 'previous_run_archive'))
            os.mkdir(archive_folder_name)
    return archive_folder_name

def archive_lots_of_files(config, archive_folder_name):
    model_output_detailed = pd.read_csv(os.path.join(config.root_dir, 'output_data', 'model_output_detailed', config.model_output_file_name))
    model_output_non_detailed = pd.read_csv(os.path.join(config.root_dir, 'output_data', 'model_output', config.model_output_file_name))
    model_output_all_with_fuels = pd.read_csv(os.path.join(config.root_dir, 'output_data', 'model_output_with_fuels', config.model_output_file_name))

    model_output_detailed.to_csv(os.path.join(config.root_dir, archive_folder_name, 'model_output_detailed.csv'))
    model_output_non_detailed.to_csv(os.path.join(config.root_dir, archive_folder_name, 'model_output_non_detailed.csv'))
    model_output_all_with_fuels.to_csv(os.path.join(config.root_dir, archive_folder_name, 'model_output_all_with_fuels.csv'))

    shutil.copyfile(os.path.join(config.root_dir, 'model_code', 'configurations.py'), os.path.join(archive_folder_name, 'configurations.py'))

    recursively_save_file(os.path.join(config.root_dir, 'model_code'), archive_folder_name, file_extension='.py', exclude_archive_folder=True)
    recursively_save_file(os.path.join(config.root_dir, 'input_data', 'user_input_spreadsheets'), archive_folder_name, file_extension='.csv', exclude_archive_folder=True)
    recursively_save_file(os.path.join(config.root_dir, f'intermediate_data', 'model_inputs', config.FILE_DATE_ID), archive_folder_name, file_extension='.csv', exclude_archive_folder=True)
    recursively_save_file(os.path.join(config.root_dir, 'output_data', 'for_other_modellers'), archive_folder_name, exclude_archive_folder=True)

    fuel_mixing_assumptions = os.path.join(config.root_dir, 'input_data', 'fuel_mixing_assumptions.xlsx')
    shutil.copyfile(fuel_mixing_assumptions, os.path.join(archive_folder_name, 'fuel_mixing_assumptions.xlsx'))

    recursively_save_file(os.path.join(config.root_dir, 'config', 'concordances_and_config_data', 'computer_generated_concordances'), archive_folder_name, '.csv', exclude_archive_folder=True)

def recursively_save_file(source_dir, dest_dir, file_extension='*', exclude_archive_folder=True, keep_folder_structure=False):
    os.makedirs(dest_dir, exist_ok=True)
    for dirpath, dirnames, filenames in os.walk(source_dir):
        for filename in filenames:
            if (filename.endswith(file_extension)) or (file_extension == '*'):
                dest_dir2 = dest_dir
                if exclude_archive_folder and 'archive' in dirpath:
                    continue
                full_file_path = os.path.join(dirpath, filename)
                if keep_folder_structure:
                    folder_structure = os.path.relpath(dirpath, source_dir)
                    if folder_structure == '.': # If the folder is the source folder
                        folder_structure = ''
                    dest_dir2 = os.path.join(dest_dir, folder_structure)
                    if not os.path.exists(dest_dir2):
                        os.makedirs(dest_dir2)
                shutil.copy2(full_file_path, dest_dir2)

def zip_up_folder(config, archive_folder_name):
    output_file = os.path.join(archive_folder_name, config.FILE_DATE_ID + '_0')
    while os.path.exists(output_file + '.zip'):
        output_file = output_file[:-1] + str(int(output_file[-1]) + 1)
    created_zip_file = shutil.make_archive(output_file, 'zip', archive_folder_name)
    if not os.path.exists(created_zip_file):
        if os.path.exists(created_zip_file + '.zip'):
            os.rename(created_zip_file + '.zip', created_zip_file)
        else:
            raise Exception('Zip file not found')
    print(f'Zipped up {archive_folder_name} to {output_file}.zip')

def save_economy_projections_and_all_inputs(config, ECONOMY_ID, ZIP_UP_ARCHIVE_FOLDER=True, ARCHIVED_FILE_DATE_ID=None, transport_data_system_FILE_DATE_ID_2=None):
    if ARCHIVED_FILE_DATE_ID is None:
        ARCHIVED_FILE_DATE_ID = config.FILE_DATE_ID
    elif ARCHIVED_FILE_DATE_ID == 'latest':
        ARCHIVED_FILE_DATE_ID = utility_functions.get_latest_date_for_data_file(data_folder_path=os.path.join(config.root_dir, 'output_data', 'model_output'), file_name_start=f'{ECONOMY_ID}_model_output', file_name_end='.csv')
        if ARCHIVED_FILE_DATE_ID == '':
            raise Exception(f'No {ECONOMY_ID}_model_output_DATEID found in output_data/model_output')
    ARCHIVED_FILE_DATE_ID_2 = ARCHIVED_FILE_DATE_ID
    if transport_data_system_FILE_DATE_ID_2 is None:
        transport_data_system_FILE_DATE_ID_2 = config.transport_data_system_FILE_DATE_ID
        if not os.path.exists(os.path.join(config.root_dir, f'intermediate_data', 'input_data_optimisations', f'optimised_data_{ECONOMY_ID}_{ARCHIVED_FILE_DATE_ID}_{transport_data_system_FILE_DATE_ID_2}.pkl')):
            #find the latest date for the optimised data file in teh first date slot in the file name
            ARCHIVED_FILE_DATE_ID_2 = utility_functions.get_latest_date_for_data_file(data_folder_path=os.path.join(config.root_dir, 'intermediate_data', 'input_data_optimisations'), file_name_start=f'optimised_data_{ECONOMY_ID}_', EXCLUDE_DATE_STR_START=True)
            
            if ARCHIVED_FILE_DATE_ID_2 == '':
                raise Exception(f'No optimised_data_{ECONOMY_ID}_{ARCHIVED_FILE_DATE_ID}_ found in intermediate_data/input_data_optimisations')
            
        if not os.path.exists(os.path.join(config.root_dir, f'intermediate_data', 'input_data_optimisations', f'optimised_data_{ECONOMY_ID}_{ARCHIVED_FILE_DATE_ID_2}_{transport_data_system_FILE_DATE_ID_2}.pkl')):
            transport_data_system_FILE_DATE_ID_2 = 'DATE'+ utility_functions.get_latest_date_for_data_file(data_folder_path=os.path.join(config.root_dir, 'intermediate_data', 'input_data_optimisations'), file_name_start=f'optimised_data_{ECONOMY_ID}_{ARCHIVED_FILE_DATE_ID_2}', EXCLUDE_DATE_STR_START=False, ONLY_WITH_DATE_STR_START=True)
            if transport_data_system_FILE_DATE_ID_2 == 'DATE':
                raise Exception(f'No optimised_data_{ECONOMY_ID}_{ARCHIVED_FILE_DATE_ID_2}_ found in intermediate_data/input_data_optimisations')
    
    archive_folder_name = os.path.join(config.root_dir, 'output_data', 'archived_runs', '{}_{}'.format(ECONOMY_ID, ARCHIVED_FILE_DATE_ID) + '_' + datetime.datetime.now().strftime("%H%M"))
    if not os.path.exists(archive_folder_name):
        os.mkdir(archive_folder_name)
    else:
        print('WARNING: archive folder already exists. This will overwrite the data in that folder')
        user_input = input('{} already exists. Do you want to continue? (y/n)'.format(archive_folder_name))
        if user_input != 'y':
            raise Exception('User chose not to continue')

    model_output_file_name_2 = config.model_output_file_name.replace(config.FILE_DATE_ID, ARCHIVED_FILE_DATE_ID)
    files_list = [
        os.path.join('config', 'parameters.yml'),
        os.path.join('config', 'optimisation_parameters.yml'),
        os.path.join('model_code', 'configurations.py'),
        os.path.join('intermediate_data', 'computer_generated_concordances', f'model_concordances_{ARCHIVED_FILE_DATE_ID}_demand_side_fuel_mixing.csv'),
        os.path.join('intermediate_data', 'computer_generated_concordances', f'model_concordances_{ARCHIVED_FILE_DATE_ID}_supply_side_fuel_mixing.csv'),
        os.path.join('intermediate_data', 'computer_generated_concordances', f'model_concordances_measures_{ARCHIVED_FILE_DATE_ID}.csv'),
        os.path.join('intermediate_data', 'computer_generated_concordances', f'model_concordances_fuels_{ARCHIVED_FILE_DATE_ID}.csv'),
        os.path.join('intermediate_data', 'computer_generated_concordances', f'model_concordances_fuels_NO_BIOFUELS_{ARCHIVED_FILE_DATE_ID}.csv'),
        os.path.join('intermediate_data', 'computer_generated_concordances', f'model_concordances_user_input_and_growth_rates_{ARCHIVED_FILE_DATE_ID}.csv'),
        os.path.join('input_data', 'fuel_mixing_assumptions.xlsx'),
        os.path.join('input_data', 'growth_coefficients_by_region.csv'),
        os.path.join('input_data', 'vehicle_sales_share_inputs.xlsx'),
        os.path.join('intermediate_data', 'model_outputs', f'{ECONOMY_ID}_input_data_based_on_previous_model_run_NON_ROAD_DETAILED_{model_output_file_name_2}'),
        os.path.join('intermediate_data', 'model_outputs', f'{ECONOMY_ID}_energy_use_output_NON_ROAD_DETAILED_{model_output_file_name_2}'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_aggregated_demand_side_fuel_mixing.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_supply_side_fuel_mixing.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_road_model_input_wide.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_non_road_model_input_wide.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_growth_forecasts_wide.csv'),
        os.path.join('intermediate_data', 'road_model', f'{ECONOMY_ID}_vehicles_per_stock_parameters.csv'),
        os.path.join('intermediate_data', 'road_model', f'{ECONOMY_ID}_parameters_estimates_{ARCHIVED_FILE_DATE_ID}.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_stocks_per_capita_threshold.csv'),
        os.path.join('intermediate_data', 'road_model', f'{ECONOMY_ID}_{model_output_file_name_2}'),
        os.path.join('intermediate_data', 'road_model', f'first_run_{ECONOMY_ID}_{model_output_file_name_2}'),
        os.path.join('intermediate_data', 'road_model', f'{ECONOMY_ID}_final_road_growth_forecasts.pkl'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_non_road_model_input_wide.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_road_model_input_wide.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_growth_forecasts_wide.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_demand_side_fuel_mixing.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_supply_side_fuel_mixing.csv'),
        os.path.join('intermediate_data', 'model_inputs', 'transport_data_system_extract.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_vehicle_sales_share.csv'),
        os.path.join('output_data', 'model_output_detailed', f'{ECONOMY_ID}_NON_ROAD_DETAILED_{model_output_file_name_2}'),
        os.path.join('output_data', 'model_output', f'{ECONOMY_ID}_NON_ROAD_DETAILED_{model_output_file_name_2}'),
        os.path.join('output_data', 'model_output_with_fuels', f'{ECONOMY_ID}_NON_ROAD_DETAILED_{model_output_file_name_2}'),
        os.path.join('output_data', 'model_output_detailed', f'{ECONOMY_ID}_{model_output_file_name_2}'),
        os.path.join('output_data', 'model_output', f'{ECONOMY_ID}_{model_output_file_name_2}'),
        os.path.join('output_data', 'model_output_with_fuels', f'{ECONOMY_ID}_{model_output_file_name_2}'),
        os.path.join('intermediate_data', 'road_model', f'{ECONOMY_ID}_{model_output_file_name_2}'),
        os.path.join('intermediate_data', 'non_road_model', f'{ECONOMY_ID}_{model_output_file_name_2}'),
        os.path.join('intermediate_data', 'model_outputs', f'{ECONOMY_ID}_{model_output_file_name_2}'),
        os.path.join('output_data', 'for_other_modellers', 'output_for_outlook_data_system', f'{ECONOMY_ID}_{ARCHIVED_FILE_DATE_ID}_transport_energy_use.csv'),
        os.path.join('output_data', 'model_output_with_fuels', f'{ECONOMY_ID}_{model_output_file_name_2}'),
        os.path.join('output_data', 'model_output_detailed', f'{ECONOMY_ID}_{model_output_file_name_2}'),
        os.path.join('output_data', 'for_other_modellers', 'output_for_outlook_data_system', f'{ECONOMY_ID}_{ARCHIVED_FILE_DATE_ID}_transport_energy_use.csv'),
        os.path.join('output_data', 'for_other_modellers', 'charging', f'{ECONOMY_ID}_estimated_number_of_chargers.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_supply_side_fuel_mixing.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_road_model_input_wide.csv'),
        os.path.join('output_data', 'model_output_detailed', f'{ECONOMY_ID}_NON_ROAD_DETAILED_{model_output_file_name_2}'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_growth_forecasts_wide.csv'),
        os.path.join('intermediate_data', 'road_model', f'first_run_{ECONOMY_ID}_{model_output_file_name_2}'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_vehicle_sales_share.csv'),
        os.path.join('intermediate_data', 'road_model', f'{ECONOMY_ID}_parameters_estimates_{ARCHIVED_FILE_DATE_ID}.csv'),
        os.path.join('input_data', 'from_8th', 'reformatted', 'activity_energy_road_stocks.csv'),
        os.path.join('config', '9th_edition_emissions_factors.csv'),
        os.path.join('input_data', 'from_8th', 'reformatted', 'activity_energy_road_stocks.csv'),
        os.path.join('input_data', 'from_8th', 'reformatted', '8th_energy_by_fuel.csv'),
        os.path.join('output_data', 'model_output', f'{ECONOMY_ID}_{model_output_file_name_2}'),
        os.path.join('intermediate_data', 'model_inputs', 'transport_data_system_extract.csv'),
        os.path.join('intermediate_data', 'model_inputs', f'{ECONOMY_ID}_user_inputs_and_growth_rates.csv'),
        os.path.join('intermediate_data', 'model_inputs', 'regression_based_growth_estimates.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_aggregated_road_model_input_wide.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_aggregated_non_road_model_input_wide.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_aggregated_growth_forecasts_wide.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_stocks_per_capita_threshold.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_supply_side_fuel_mixing.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_demand_side_fuel_mixing.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_aggregated_supply_side_fuel_mixing.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_aggregated_demand_side_fuel_mixing.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_aggregated_road_model_input_wide.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_aggregated_non_road_model_input_wide.csv'),
        os.path.join('intermediate_data', 'model_inputs', ARCHIVED_FILE_DATE_ID, f'{ECONOMY_ID}_aggregated_growth_forecasts_wide.csv'),
        os.path.join('intermediate_data', 'model_inputs', 'regression_based_growth_estimates.csv'),
        os.path.join('..', 'transport_data_system', 'output_data', f'combined_data_{transport_data_system_FILE_DATE_ID_2}.csv')
    ]

    sometimes_files = [os.path.join('intermediate_data', 'model_outputs', f'{ECONOMY_ID}_medium_to_medium_activity_change_for_plotting{config.FILE_DATE_ID}.csv')]
    for file in sometimes_files:
        if os.path.exists(os.path.join(config.root_dir, file)):
            files_list.append(file)

    for file in files_list:
        dotdot = False
        if file.startswith('..'):
            dotdot = True
            file = file[3:]
        folder_structure = os.path.dirname(file)
        if not os.path.exists(os.path.join(archive_folder_name, folder_structure)):
            os.makedirs(os.path.join(archive_folder_name, folder_structure))

        if os.path.exists(os.path.join(archive_folder_name, file)):
            print(f'WARNING: {file} already exists in archive folder. Must already have been saved there')
        
        if dotdot:
            source_path = os.path.abspath(os.path.join(config.root_dir, '..', file))
            destination_path = os.path.join(archive_folder_name, file)
            shutil.copyfile(source_path, destination_path)
        else:
            shutil.copyfile(os.path.join(config.root_dir, file), os.path.join(archive_folder_name, file))


    date_id = utility_functions.get_latest_date_for_data_file(os.path.join(config.root_dir, 'input_data', '9th_model_inputs'), 'model_df_wide_')
    if not os.path.exists(os.path.join(archive_folder_name, 'input_data', '9th_model_inputs')):
        os.makedirs(os.path.join(archive_folder_name, 'input_data', '9th_model_inputs'))
    shutil.copyfile(os.path.join(config.root_dir, 'input_data', '9th_model_inputs', f'model_df_wide_{date_id}.csv'), os.path.join(archive_folder_name, 'input_data', '9th_model_inputs', f'model_df_wide_{date_id}.csv'))

    macro_date_id = utility_functions.get_latest_date_for_data_file(os.path.join(config.root_dir, 'input_data', 'macro'), 'APEC_GDP_data_')
    if not os.path.exists(os.path.join(archive_folder_name, 'input_data', 'macro')):
        os.makedirs(os.path.join(archive_folder_name, 'input_data', 'macro'))
    shutil.copyfile(os.path.join(config.root_dir, 'input_data', 'macro', f'APEC_GDP_data_{macro_date_id}.csv'), os.path.join(archive_folder_name, 'input_data', 'macro', f'APEC_GDP_data_{macro_date_id}.csv'))

    optimisation_data_date_id = utility_functions.get_latest_date_for_data_file(os.path.join(config.root_dir, 'intermediate_data', 'input_data_optimisations'), f'optimised_data_{ECONOMY_ID}_', f'_{transport_data_system_FILE_DATE_ID_2}.pkl', EXCLUDE_DATE_STR_START=True)
    if not os.path.exists(os.path.join(config.root_dir, 'intermediate_data', 'input_data_optimisations', f'optimised_data_{ECONOMY_ID}_{optimisation_data_date_id}_{transport_data_system_FILE_DATE_ID_2}.pkl')):
        raise Exception(f'No optimised_data_{ECONOMY_ID}_{optimisation_data_date_id}_{transport_data_system_FILE_DATE_ID_2}.pkl found in intermediate_data/input_data_optimisations')
    if not os.path.exists(os.path.join(archive_folder_name, 'intermediate_data', 'input_data_optimisations')):
        os.makedirs(os.path.join(archive_folder_name, 'intermediate_data', 'input_data_optimisations'))
    shutil.copyfile(os.path.join(config.root_dir, 'intermediate_data', 'input_data_optimisations', f'optimised_data_{ECONOMY_ID}_{optimisation_data_date_id}_{transport_data_system_FILE_DATE_ID_2}.pkl'), os.path.join(archive_folder_name, 'intermediate_data', 'input_data_optimisations', f'optimised_data_{ECONOMY_ID}_{optimisation_data_date_id}_{transport_data_system_FILE_DATE_ID_2}.pkl'))

    date_id = utility_functions.get_latest_date_for_data_file(os.path.join(config.root_dir, 'output_data', 'for_other_modellers', 'output_for_outlook_data_system'), f'{ECONOMY_ID}_international_bunker_energy_use_')
    if not os.path.exists(os.path.join(archive_folder_name, 'output_data', 'for_other_modellers', 'output_for_outlook_data_system')):
        os.makedirs(os.path.join(archive_folder_name, 'output_data', 'for_other_modellers', 'output_for_outlook_data_system'))
    shutil.copyfile(os.path.join(config.root_dir, 'output_data', 'for_other_modellers', 'output_for_outlook_data_system', f'{ECONOMY_ID}_international_bunker_energy_use_{date_id}.csv'), os.path.join(archive_folder_name, 'output_data', 'for_other_modellers', 'output_for_outlook_data_system', f'{ECONOMY_ID}_international_bunker_energy_use_{date_id}.csv'))
    shutil.copyfile(os.path.join(config.root_dir, 'output_data', 'for_other_modellers', 'output_for_outlook_data_system', f'international_bunker_energy_use_{date_id}.csv'), os.path.join(archive_folder_name, 'output_data', 'for_other_modellers', 'output_for_outlook_data_system', f'international_bunker_energy_use_{date_id}.csv'))

    if not os.path.exists(os.path.join(archive_folder_name, 'output_data', 'for_other_modellers', ECONOMY_ID)):
        os.makedirs(os.path.join(archive_folder_name, 'output_data', 'for_other_modellers', ECONOMY_ID))
    for file in os.listdir(os.path.join(config.root_dir, 'output_data', 'for_other_modellers', ECONOMY_ID)):
        shutil.copyfile(os.path.join(config.root_dir, 'output_data', 'for_other_modellers', ECONOMY_ID, file), os.path.join(archive_folder_name, 'output_data', 'for_other_modellers', ECONOMY_ID, file))

    if not os.path.exists(os.path.join(archive_folder_name, 'input_data', 'user_input_spreadsheets')):
        os.makedirs(os.path.join(archive_folder_name, 'input_data', 'user_input_spreadsheets'))
    for file in os.listdir(os.path.join(config.root_dir, 'input_data', 'user_input_spreadsheets')):
        if file.endswith('.csv'):
            shutil.copyfile(os.path.join(config.root_dir, 'input_data', 'user_input_spreadsheets', file), os.path.join(archive_folder_name, 'input_data', 'user_input_spreadsheets', file))

    if os.path.exists(os.path.join(config.root_dir, 'intermediate_data', 'road_model', f'change_dataframe_aggregation_{ECONOMY_ID}.csv')):
        if not os.path.exists(os.path.join(archive_folder_name, 'intermediate_data', 'road_model')):
            os.makedirs(os.path.join(archive_folder_name, 'intermediate_data', 'road_model'))
        shutil.copyfile(os.path.join(config.root_dir, 'intermediate_data', 'road_model', f'change_dataframe_aggregation_{ECONOMY_ID}.csv'), os.path.join(archive_folder_name, 'intermediate_data', 'road_model', f'change_dataframe_aggregation_{ECONOMY_ID}.csv'))

    if not os.path.exists(os.path.join(archive_folder_name, 'plotting_output', 'dashboards', ECONOMY_ID)):
        os.makedirs(os.path.join(archive_folder_name, 'plotting_output', 'dashboards', ECONOMY_ID))
    for file in os.listdir(os.path.join(config.root_dir, 'plotting_output', 'dashboards', ECONOMY_ID)):
        if file.endswith('.html'):
            shutil.copyfile(os.path.join(config.root_dir, 'plotting_output', 'dashboards', ECONOMY_ID, file), os.path.join(archive_folder_name, 'plotting_output', 'dashboards', ECONOMY_ID, file))

    recursively_save_file(os.path.join(config.root_dir, 'model_code'), os.path.join(archive_folder_name, 'model_code'), file_extension='.py', exclude_archive_folder=True, keep_folder_structure=True)

    if not os.path.exists(os.path.join(archive_folder_name, 'config', 'concordances_and_config_data')):
        os.makedirs(os.path.join(archive_folder_name, 'config', 'concordances_and_config_data'))
    for file in os.listdir(os.path.join(config.root_dir, 'config', 'concordances_and_config_data')):
        if file.endswith('.csv'):
            shutil.copyfile(os.path.join(config.root_dir, 'config', 'concordances_and_config_data', file), os.path.join(archive_folder_name, 'config', 'concordances_and_config_data', file))

    if ZIP_UP_ARCHIVE_FOLDER:
        created_zip_file = shutil.make_archive(archive_folder_name, 'zip', archive_folder_name)
        if not os.path.exists(created_zip_file):
            raise Exception('Zip file not found')
        else:
            shutil.rmtree(archive_folder_name)

    return archive_folder_name

def revert_to_previous_version_of_files(config, economy, archive_folder_name, UNZIP_ARCHIVE_FOLDER=True, CURRENT_FILE_DATE_ID=None):
    if CURRENT_FILE_DATE_ID is None:
        CURRENT_FILE_DATE_ID = config.FILE_DATE_ID
    save_economy_projections_and_all_inputs(config, economy, ARCHIVED_FILE_DATE_ID=CURRENT_FILE_DATE_ID)
    
    if UNZIP_ARCHIVE_FOLDER:
        if not os.path.exists(archive_folder_name + '.zip'):
            raise Exception('zip file not found')
        shutil.unpack_archive(archive_folder_name + '.zip', archive_folder_name)
        if not os.path.exists(archive_folder_name):
            raise Exception('Folder not found')

    raise Exception('STOPPED HERE')
    for root, dirs, files in os.walk(archive_folder_name):
        for file in files:
            if file.endswith(('.py', '.yaml', '.csv', '.xlsx', '.pkl', '.html')):
                root = os.path.relpath(root, archive_folder_name)
                if root.startswith(os.path.join('model_code', 'utility_functions')):
                    continue
                if root.startswith(os.path.join(config.root_dir, 'transport_data_system')):
                    if not os.path.exists(os.path.join('..', root)):
                        os.makedirs(os.path.join('..', root))
                    shutil.copyfile(os.path.join(root, file), os.path.join('..', root, file))
                else:
                    if not os.path.exists(root):
                        os.makedirs(root)
                    shutil.copyfile(os.path.join(archive_folder_name, root, file), os.path.join(root, file))

def copy_folder_structure(config, src, dest):
    for dirpath, dirnames, filenames in os.walk(src):
        structure = os.path.join(dest, os.path.relpath(dirpath, src))
        if not os.path.isdir(structure):
            os.mkdir(structure)
        with open(os.path.join(structure, ".gitkeep"), "w") as f:
            pass

def remove_gitkeep_files(config, src):
    for dirpath, dirnames, filenames in os.walk(src):
        gitkeep_path = os.path.join(dirpath, ".gitkeep")
        if os.path.isfile(gitkeep_path):
            os.remove(gitkeep_path)
