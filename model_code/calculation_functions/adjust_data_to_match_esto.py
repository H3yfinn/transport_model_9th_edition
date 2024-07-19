#we have data from the ESTO energy data set that the output from this model needs to match. hwoever the way this model works is that its output is a function of the input data, which is activity data (the energy use is the final results). so we need to adjust the input data so that the output matches the ESTO data. because there are so many steps in teh system, this will be a bit complicated. We will do this as follows:
# - biofuels: just base it off the total esto demadn for gasoline adn diesel. calculate share of oil use that the biofuels would make up
# - gasoline/diesel: adjust road: cars and lcvs to make it easy. split the difference in half and then apply half change to each.
# - elec: just decrease ev car stocks
# - non road fuels: decrease use in non road
# - gas: bit more difficult. decrease what vehicle types?

#but also we need to know the expected energy use for the period betwen (and including) BASE_YEAR and config.OUTLOOK_BASE_YEAR. so we need to run the model for that period first to get the output energy use. so we need to run the model twice. once for the period between BASE_YEAR and config.OUTLOOK_BASE_YEAR, and then finally for the period between config.OUTLOOK_BASE_YEAR and OUTLOOK_END_YEAR (not base year and end year bcause its important the results in config.OUTLOOK_BASE_YEAR are what we expect) then we can adjust the data for the first period so that the output matches the ESTO data. then we can use the data for the second period as the input data for the outlook model.
#adjusting data will involve:
#rescaling energy use for each fuel type so that the total energy use matches the ESTO data > apply this to the most suitable drive types/vehicle types so its less complicated.
#then based on the new energy use for each vehicle type/drive  type, recalcualte the activity and stocks (given the data which should be constant for mielage/occupancy_load). 
# #done

#hwoever one thing that will be different is that for biofuels demand, we will maek the 'supplyside share of biofeusl demand equivalent to the share of biofuels in the esto data.


#%%
#aslo note that esto data is by medium. i think it ha road split into freight and passenger transport types too.

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
###

#################
from .. import utility_functions
from . import apply_fuel_mix_demand_side, apply_fuel_mix_supply_side, optimise_to_calculate_base_data
#################

from scipy.optimize import minimize

def adjust_data_to_match_esto_handler(config, BASE_YEAR, ECONOMY_ID, road_model_input_wide, non_road_model_input_wide, supply_side_fuel_mixing, demand_side_fuel_mixing, USE_PREVIOUS_OPTIMISATION_RESULTS_FOR_THIS_DATA_SYSTEM_INPUT, USE_SAVED_OPT_PARAMATERS, TESTING=False):
    """this function is a handler for the code in this file. It will run the code in this file to adjust the data to match the ESTO energy data. This is quite a complicated process, especially the use of the optimisation functions to find the best balance of changes to make the data we have in road_model_input_wide equate to match the energy from ESTO. 

    Args:
        BASE_YEAR (_type_): _description_
        ECONOMY_ID (_type_): _description_
        road_model_input_wide (_type_): _description_
        non_road_model_input_wide (_type_): _description_
        supply_side_fuel_mixing (_type_): _description_
        demand_side_fuel_mixing (_type_): _description_
        USE_PREVIOUS_OPTIMISATION_RESULTS_FOR_THIS_DATA_SYSTEM_INPUT (_type_): _description_
        TESTING (bool, optional): _description_. Defaults to False.

    Raises:
        ValueError: _description_

    Returns:
        _type_: _description_
    """    
    energy_use_esto = format_9th_input_energy_from_esto(config, ECONOMY_ID=ECONOMY_ID)#Economy missing in here
    
    #move electricity use in road to rail. This is based on the parameters the user has set. It should generally default to False unless the user things that Elec use in road is overexaggerated.
    ECONOMY_TO_MOVE_ROAD_ELEC_USE_TO_RAIL_FOR = yaml.load(open(os.path.join(config.root_dir, 'config', 'parameters.yml')), Loader=yaml.FullLoader)['ECONOMY_TO_MOVE_ROAD_ELEC_USE_TO_RAIL_FOR']
    if ECONOMY_TO_MOVE_ROAD_ELEC_USE_TO_RAIL_FOR[ECONOMY_ID]:
        USE_MOVE_ELECTRICITY_USE_IN_ROAD_TO_RAIL_ESTO=True
        energy_use_esto = move_electricity_use_in_road_to_rail_esto(config, energy_use_esto, ECONOMY_ID)
    else:
        USE_MOVE_ELECTRICITY_USE_IN_ROAD_TO_RAIL_ESTO=False 
            
    input_data_based_on_previous_model_run = pd.read_csv(os.path.join(config.root_dir, 'output_data', 'model_output_detailed', '{}_NON_ROAD_DETAILED_{}'.format(ECONOMY_ID, config.model_output_file_name)))
    energy_use_output = pd.read_csv(os.path.join(config.root_dir, 'output_data', 'model_output_with_fuels', '{}_NON_ROAD_DETAILED_{}'.format(ECONOMY_ID, config.model_output_file_name)))
    
    #save them for archiving because they will be overwritten later
    input_data_based_on_previous_model_run.to_csv(os.path.join(config.root_dir, 'intermediate_data', 'model_outputs', '{}_input_data_based_on_previous_model_run_NON_ROAD_DETAILED_{}'.format(ECONOMY_ID, config.model_output_file_name)))
    energy_use_output.to_csv(os.path.join(config.root_dir, 'intermediate_data', 'model_outputs', '{}_energy_use_output_NON_ROAD_DETAILED_{}'.format(ECONOMY_ID, config.model_output_file_name)))
    
    #double check that the max and min dates for the input data match the BASEYEAR AND config.OUTLOOK_BASE_YEAR, OTHERWISE THE USER NEEDS TO RUN THE MODEL WITH ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR SET TO FALSE AGAIN:
    if input_data_based_on_previous_model_run['Date'].max() != config.OUTLOOK_BASE_YEAR or input_data_based_on_previous_model_run['Date'].min() != BASE_YEAR:
        raise ValueError('The max and min dates for the input data do not match the base year and outlook base year. This means that the user needs to run the model with ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR set to False again')
    
    #make the values before and including the config.OUTLOOK_BASE_YEAR all equal to the Reference scenario values. This is because we are assuming that the Reference scenario reflects the reality of the config.OUTLOOK_BASE_YEAR, and it will reflect it even more so once we have adjusted the energy use to match the esto data! (it shoudlnt be very consequential, as there wont be much difference between the two scenarios during the period between BASE_YEAR and config.OUTLOOK_BASE_YEAR, especailly as its not expected that the user will have included any scenario related assumptions (e.g. vehicle sales shares))
    energy_use_output_post_BASE_YEAR = energy_use_output.loc[energy_use_output['Date'] > config.OUTLOOK_BASE_YEAR].copy()
    energy_use_output_pre_BASE_YEAR_ref = energy_use_output.loc[(energy_use_output['Date'] <= config.OUTLOOK_BASE_YEAR) & (energy_use_output['Scenario'] == 'Reference')].copy()
    #for each otehr scenario in scenario_list, just creatre a copy of energy_use_output_pre_BASE_YEAR_ref:
    energy_use_output_pre_BASE_YEAR = energy_use_output_pre_BASE_YEAR_ref.copy()
    for scenario in config.SCENARIOS_LIST:
        if scenario == 'Reference':
            continue
        energy_use_output_pre_BASE_YEAR_new = energy_use_output_pre_BASE_YEAR_ref.copy()
        energy_use_output_pre_BASE_YEAR_new['Scenario'] = scenario
        energy_use_output_pre_BASE_YEAR = pd.concat([energy_use_output_pre_BASE_YEAR, energy_use_output_pre_BASE_YEAR_new])
        
    energy_use_output = pd.concat([energy_use_output_pre_BASE_YEAR, energy_use_output_post_BASE_YEAR])
    #replace any nas with 0
    energy_use_output['Energy'] = energy_use_output['Energy'].fillna(0)
    if TESTING:
        road_model_input_wide, non_road_model_input_wide, supply_side_fuel_mixing, input_data_based_on_previous_model_run, energy_use_output, energy_use_esto = filter_for_testing_data_only(config, road_model_input_wide, non_road_model_input_wide, supply_side_fuel_mixing, input_data_based_on_previous_model_run, energy_use_output, energy_use_esto)
        
    energy_use_output_no_drive, energy_use_esto, energy_use_esto_pipeline = format_energy_use_for_rescaling(config, energy_use_esto, energy_use_output, SPREAD_NON_SPECIFIED_AND_SEPARATE_PIPELINE = False, REMOVE_ANNOYING_FUELS = False)
    energy_use_merged = merge_and_find_ratio_between_esto_and_input_data(config, energy_use_esto, energy_use_output_no_drive)

    supply_side_fuel_mixing = adjust_supply_side_fuel_share(config, energy_use_esto,supply_side_fuel_mixing)
    
    required_energy_use_by_drive = calculate_required_energy_use_by_drive(config, input_data_based_on_previous_model_run,energy_use_merged,energy_use_output)
    #############################
    #OPTIMISATION STEP: (use optimisation to find the best balance of changes to make the data we have in input_data_new_road equate to match the energy from ESTO.)
    input_data_new_road = required_energy_use_by_drive.loc[required_energy_use_by_drive['Medium'] == 'road'].copy()  
    #find the latest LATEST_FILE_DATE_ID for this file f'intermediate_data/input_data_optimisations/optimised_data_{ECONOMY_ID}_{LATEST_FILE_DATE_ID}_{config.transport_data_system_FILE_DATE_ID}.pkl'
    
    date_id = utility_functions.get_latest_date_for_data_file(os.path.join(config.root_dir, f'intermediate_data', 'input_data_optimisations'), f'optimised_data_{ECONOMY_ID}_', file_name_end=f'_{config.transport_data_system_FILE_DATE_ID}.pkl') 
    if USE_PREVIOUS_OPTIMISATION_RESULTS_FOR_THIS_DATA_SYSTEM_INPUT and date_id is not None:
        filename = os.path.join(config.root_dir, f'intermediate_data', 'input_data_optimisations', f'optimised_data_{ECONOMY_ID}_{date_id}_{config.transport_data_system_FILE_DATE_ID}.pkl')
        #LOAD PREVIOUS OPT RESULTS INSTEAD OF RECALCULATING. THIS HELPS TO KEEP CONSISETNCY BETWEEN THE RESULTS AS WELL AS REDUCING RUN TIME
        optimised_data = pd.read_pickle(filename)
    else:
        population = road_model_input_wide[['Economy', 'Scenario', 'Date','Vehicle Type', 'Transport Type', 'Population']].drop_duplicates()
        #merge it
        input_data_new_road = input_data_new_road.merge(population, on=['Economy', 'Scenario', 'Date','Vehicle Type', 'Transport Type'])
        # if ECONOMY_ID == '04_CHL':
        #     breakpoint()#try work out why japan isnt calcualting well. 
        #     input_data_new_road.to_pickle('chl_input_to_optimisation.pkl')
        #     optimised_data = optimise_to_calculate_base_data.optimisation_handler(config, input_data_new_road, SAVE_ALL_RESULTS=True, REMOVE_NON_MAJOR_VARIABLES=False, USE_MOVE_ELECTRICITY_USE_IN_ROAD_TO_RAIL_ESTO=USE_MOVE_ELECTRICITY_USE_IN_ROAD_TO_RAIL_ESTO, USE_SAVED_OPT_PARAMATERS=USE_SAVED_OPT_PARAMATERS, PARAMETERS_RANGES_KEY='ALL2')
        # else:
        optimised_data = optimise_to_calculate_base_data.optimisation_handler(config, input_data_new_road, SAVE_ALL_RESULTS=True, REMOVE_NON_MAJOR_VARIABLES=False, USE_MOVE_ELECTRICITY_USE_IN_ROAD_TO_RAIL_ESTO=USE_MOVE_ELECTRICITY_USE_IN_ROAD_TO_RAIL_ESTO, USE_SAVED_OPT_PARAMATERS=USE_SAVED_OPT_PARAMATERS, PARAMETERS_RANGES_KEY='ALL')
        
    input_data_new_road_recalculated = reformat_optimised_results(config, optimised_data, input_data_new_road)
    input_data_new_road_recalculated = match_optimised_results_to_required_energy_use_exactly(config, input_data_new_road_recalculated, input_data_new_road)
    #############################
    
    input_data_new_non_road = calculate_required_values_by_measure_for_non_road(config, required_energy_use_by_drive,non_road_model_input_wide)
    
    road_all_wide, non_road_all_wide = merge_and_replace_old_input_data_with_new_input_data(config, input_data_new_road_recalculated, input_data_new_non_road, road_model_input_wide, non_road_model_input_wide)
    #now do tests to check data matches expectations:
    #test that the total road enegry use matches the total energy use in the esto data:
    test_output_matches_expectations(config, ECONOMY_ID, supply_side_fuel_mixing,demand_side_fuel_mixing, road_all_wide, non_road_all_wide, energy_use_merged, BASE_YEAR,  ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=True)
    
    #make sure data is all after config.OUTLOOK_BASE_YEAR. Since we merged it with the ESTO data we ended up with some data before config.OUTLOOK_BASE_YEAR:
    road_all_wide = road_all_wide.loc[road_all_wide['Date'] >= config.OUTLOOK_BASE_YEAR].copy()
    non_road_all_wide = non_road_all_wide.loc[non_road_all_wide['Date'] >= config.OUTLOOK_BASE_YEAR].copy()
    supply_side_fuel_mixing = supply_side_fuel_mixing.loc[supply_side_fuel_mixing['Date'] >= config.OUTLOOK_BASE_YEAR].copy()
        
    return road_all_wide, non_road_all_wide, supply_side_fuel_mixing


def adjust_supply_side_fuel_share(config, energy_use_esto, supply_side_fuel_mixing):
    #find portion of '16_06_biodiesel', '16_05_biogasoline', '16_07_bio_jet_kerosene' out of the toal '07_07_gas_diesel_oil', '07_01_motor_gasoline', '07_x_jet_fuel' in the esto data so we can change the supply side fuel mixing to match:
    energy_use_esto_wide = energy_use_esto.groupby(['Economy', 'Date', 'Fuel']).sum(numeric_only=True).reset_index()
    energy_use_esto_wide = energy_use_esto_wide.pivot(index=['Economy', 'Date'], columns='Fuel', values='Energy').reset_index()
    #some economies wont use all the fuels, so we need to catch the error, and just set the value to 0 before doing this:
    for fuel in ['07_07_gas_diesel_oil', '07_01_motor_gasoline', '07_x_jet_fuel', '07_09_lpg', '08_01_natural_gas', '07_02_aviation_gasoline', '07_06_kerosene','16_06_biodiesel', '16_05_biogasoline', '16_07_bio_jet_kerosene', '16_01_biogas']:
        if fuel not in energy_use_esto_wide.columns:
            energy_use_esto_wide[fuel] = 0
             
    energy_use_esto_wide['share_of_biodiesel'] = energy_use_esto_wide['16_06_biodiesel']/(energy_use_esto_wide['07_07_gas_diesel_oil']+energy_use_esto_wide['16_06_biodiesel'])
    energy_use_esto_wide['share_of_biogasoline'] = energy_use_esto_wide['16_05_biogasoline']/(energy_use_esto_wide['07_01_motor_gasoline']+energy_use_esto_wide['16_05_biogasoline'])
    
    energy_use_esto_wide['share_of_biogas'] = energy_use_esto_wide['16_01_biogas']/(energy_use_esto_wide['16_01_biogas']+energy_use_esto_wide['07_09_lpg']+energy_use_esto_wide['08_01_natural_gas'])
    
    try:#some economys dont sue aviation gasoline or kerosene, so we need to catch the error, and just set the value to 0 before doing this:
        energy_use_esto_wide['share_of_bio_jet'] = energy_use_esto_wide['16_07_bio_jet_kerosene']/(energy_use_esto_wide['07_x_jet_fuel']+energy_use_esto_wide['16_07_bio_jet_kerosene']+energy_use_esto_wide['07_02_aviation_gasoline']+energy_use_esto_wide['07_06_kerosene'])
    except:
        if '07_02_aviation_gasoline' not in energy_use_esto_wide.columns:
            energy_use_esto_wide['07_02_aviation_gasoline'] = 0
        if '07_06_kerosene' not in energy_use_esto_wide.columns:
            energy_use_esto_wide['07_06_kerosene'] = 0
        if '07_x_jet_fuel' not in energy_use_esto_wide.columns:
            energy_use_esto_wide['07_x_jet_fuel'] = 0
        energy_use_esto_wide['share_of_bio_jet'] = energy_use_esto_wide['16_07_bio_jet_kerosene']/(energy_use_esto_wide['07_x_jet_fuel']+energy_use_esto_wide['16_07_bio_jet_kerosene']+energy_use_esto_wide['07_02_aviation_gasoline']+energy_use_esto_wide['07_06_kerosene'])

    #manually create dfs then concat them:
    share_of_biodiesel = energy_use_esto_wide[['Economy', 'Date', 'share_of_biodiesel']].copy()
    #create cols for each fuel type:
    share_of_biodiesel['Fuel'] = '07_07_gas_diesel_oil'
    share_of_biodiesel['New_fuel'] = '16_06_biodiesel'
    share_of_biodiesel = share_of_biodiesel.rename(columns={'share_of_biodiesel': 'Supply_side_fuel_share'})

    share_of_biogasoline = energy_use_esto_wide[['Economy', 'Date', 'share_of_biogasoline']].copy()
    share_of_biogasoline['Fuel'] = '07_01_motor_gasoline'
    share_of_biogasoline['New_fuel'] = '16_05_biogasoline'
    share_of_biogasoline = share_of_biogasoline.rename(columns={'share_of_biogasoline': 'Supply_side_fuel_share'})
    #now do it for the ones where we have one biofuel for multiple fuels:
    share_of_biogas = energy_use_esto_wide[['Economy', 'Date', 'share_of_biogas']].copy()
    share_of_biogas['New_fuel'] = '16_01_biogas'
    share_of_biogas = share_of_biogas.rename(columns={'share_of_biogas': 'Supply_side_fuel_share'})
    share_of_biogas_in_lpg = share_of_biogas.copy()
    share_of_biogas_in_lpg['Fuel'] = '07_09_lpg'
    share_of_biogas_in_nat_gas = share_of_biogas.copy()
    share_of_biogas_in_nat_gas['Fuel'] = '08_01_natural_gas'
    
    share_of_bio_jet = energy_use_esto_wide[['Economy', 'Date', 'share_of_bio_jet']].copy()
    share_of_bio_jet['New_fuel'] = '16_07_bio_jet_kerosene'
    share_of_bio_jet = share_of_bio_jet.rename(columns={'share_of_bio_jet': 'Supply_side_fuel_share'})
    share_of_bio_jet_in_jet = share_of_bio_jet.copy()
    share_of_bio_jet_in_jet['Fuel'] = '07_x_jet_fuel'
    share_of_bio_jet_in_aviation_gasoline = share_of_bio_jet.copy()
    share_of_bio_jet_in_aviation_gasoline['Fuel'] = '07_02_aviation_gasoline'
    share_of_bio_jet_in_kerosene = share_of_bio_jet.copy()
    share_of_bio_jet_in_kerosene['Fuel'] = '07_06_kerosene'
    
    #concat them and then join to supplu_side_fuel_mixing, then swap supply_side_fuel_share for the new one, where available:
    new_share = pd.concat([share_of_biodiesel, share_of_biogasoline, share_of_biogas_in_lpg, share_of_biogas_in_nat_gas, share_of_bio_jet_in_jet, share_of_bio_jet_in_aviation_gasoline, share_of_bio_jet_in_kerosene]).reset_index(drop=True)
    supply_side_fuel_mixing_new = supply_side_fuel_mixing.merge(new_share, on=['Economy', 'Date', 'Fuel','New_fuel'], how='left', suffixes=('', '_new')).copy()
    #where there is a new share, use that, otherwise use the old one
    supply_side_fuel_mixing_new['Supply_side_fuel_share'] = supply_side_fuel_mixing_new['Supply_side_fuel_share_new'].fillna(supply_side_fuel_mixing_new['Supply_side_fuel_share'])
    #drop Supply_side_fuel_share_new
    supply_side_fuel_mixing_new = supply_side_fuel_mixing_new.drop(columns=['Supply_side_fuel_share_new'])
    
    return supply_side_fuel_mixing_new
#filter for REF only in input data (since we want both scnearios to have matching input data)
# ['Scenario'] == 'Reference']

#make energy_use_esto match the format of energy_use_output for ref scenario
#drop any aggregate fuels from energy_use_esto

def spread_non_specified_and_separate_pipeline_from_esto_transport_energy(config, energy_use_esto, REMOVE_ANNOYING_FUELS = False):
    #separate pipeline and nonspecified mediums in energy use esto and then spread it among all the other transport mediums. This is because the model doesnt have any way to deal with them.. they are intended to be dealt with by the transport model at a later date
    energy_use_esto_pipeline = energy_use_esto.loc[energy_use_esto['Medium'] == 'pipeline'].copy()
    energy_use_esto_nonspecified = energy_use_esto.loc[energy_use_esto['Medium'] == 'nonspecified'].copy()
    energy_use_esto = energy_use_esto.loc[~energy_use_esto['Medium'].isin(['pipeline', 'nonspecified'])].copy()
    
    #add Fuel 07_08_fuel_oil and 07_06_kerosene use in road to the non specified amount and spread it with nonspecifieds energy use. This is because we dont have any info on these uses and they are minmimal so mimght as well drop them in with the nonspecifieds
    #NOTE THAT IN HIINDSIGHT WE STARTED USING 07_08_fuel_oil and 07_06_kerosene in the model, so we shouldnt be doing this. But we will keep it in for now in case it becomes useful.
    if REMOVE_ANNOYING_FUELS:
        annoying_road_fuels_df = energy_use_esto.loc[(energy_use_esto['Medium'] == 'road') & (energy_use_esto['Fuel'].isin(['07_08_fuel_oil', '07_06_kerosene']))].copy()
        energy_use_esto = energy_use_esto.loc[~((energy_use_esto['Medium'] == 'road') & (energy_use_esto['Fuel'].isin(['07_08_fuel_oil', '07_06_kerosene'])))].copy()
        #set meidum to nonspecified
        annoying_road_fuels_df['Medium'] = 'nonspecified'
        energy_use_esto_nonspecified = pd.concat([energy_use_esto_nonspecified, annoying_road_fuels_df]).groupby(['Economy', 'Date', 'Fuel', 'Medium']).sum(numeric_only=True).reset_index()
        
    #spread energy_use_esto_nonspecified among all mediums for that fuel, eocnomy and date. Use the % of each energy use to the total energy use for that fuel, economy and date to do this:
    energy_use_esto['proportion_of_group'] = energy_use_esto.groupby(['Economy', 'Date', 'Fuel'])['Energy'].transform(lambda x: x/x.sum(numeric_only=True))
    #join the nonspec col on
    energy_use_esto = energy_use_esto.merge(energy_use_esto_nonspecified, on=['Economy', 'Date', 'Fuel'], how='left', suffixes=('', '_nonspec'))
    #times the proportion of group by the nonspec energy use to get the new energy use, then add that to enegry
    energy_use_esto['Energy'] = energy_use_esto['Energy'] + (energy_use_esto['proportion_of_group']*energy_use_esto['Energy_nonspec'])
    energy_use_esto = energy_use_esto.drop(columns=['Energy_nonspec', 'proportion_of_group'])
    
    return energy_use_esto, energy_use_esto_pipeline, energy_use_esto_nonspecified

def format_energy_use_for_rescaling(config, energy_use_esto, energy_use_output, SPREAD_NON_SPECIFIED_AND_SEPARATE_PIPELINE = False, REMOVE_ANNOYING_FUELS=False):
    """this function formats the energy use data from the esto data set so that it can be compared to the energy use data from the model.
frist, if  SPREAD_NON_SPECIFIED_AND_SEPARATE_PIPELINE it will remove the pipeline and nonspecified mediums in energy_use_esto, as we dont want to consider those. they might be dealt with by the transport model at a later date... It also adds Fuel 07_08_fuel_oil and 07_06_kerosene use in road to the non specified amount and spread it with nonspecifieds energy use. This is because we dont have any info on these uses and they are minmimal so mimght as well drop them in with the nonspecifieds. It also spreads energy_use_esto_nonspecified among all mediums for that fuel, eocnomy and date. Use the % of each energy use to the total energy use for that fuel, economy and date to do this. It also calculates the total energy use for each fuel, scenario, medium, economy and date in energy_use_output (so it can be compared to the esto data).

    Args:
        energy_use_esto (_type_): _description_
        energy_use_output (_type_): _description_
        SPREAD_NON_SPECIFIED_AND_SEPARATE_PIPELINE (bool, optional): _description_. Defaults to True.
        REMOVE_ANNOYING_FUELS (bool, optional): _description_. Defaults to True.

    Returns:
        _type_: _description_
    """
    
    #for now ignoring this as pipeline is managed by supply model.. non specified seems unnecessary
    if SPREAD_NON_SPECIFIED_AND_SEPARATE_PIPELINE:
        spread_non_specified_and_separate_pipeline_from_esto_transport_energy(config, energy_use_esto, REMOVE_ANNOYING_FUELS = REMOVE_ANNOYING_FUELS)
    else:
        energy_use_esto_pipeline = pd.DataFrame()
    
    #calculate the total energy use for each fuel, scenario, medium, economy and date in energy_use_output (so it can be compared to the esto data)
    energy_use_output_no_drive = energy_use_output.drop(columns=[ 'Vehicle Type', 'Drive', 'Transport Type']).groupby(['Economy','Scenario', 'Date', 'Medium', 'Fuel']).sum(numeric_only=True).reset_index().copy()
    #GRAB DATA ONLY FOR DATES WITH WHICH WE HAVE ESTO DATA
    energy_use_output_no_drive = energy_use_output_no_drive.loc[energy_use_output_no_drive['Date'].isin(energy_use_output_no_drive['Date'].unique())].copy()
    #LIEKWISE FOR ESTO
    energy_use_output_no_drive = energy_use_output_no_drive.loc[energy_use_output_no_drive['Date'].isin(energy_use_output_no_drive['Date'].unique())].copy()
    
    return energy_use_output_no_drive, energy_use_esto, energy_use_esto_pipeline

def merge_and_find_ratio_between_esto_and_input_data(config, energy_use_esto, energy_use_output_no_drive):
    #NOW find the ratio between energy use in the model and energy use in the esto data. This will be used to adjust energy to be the same as in ESTO. 

    # So merge the dfs and then find it.
    energy_use_merged = energy_use_esto.merge(energy_use_output_no_drive, on=['Economy', 'Date','Medium','Fuel'], how='left', suffixes=('_esto', '_model'))
    
    #reaplce nans in  Energy_model with 0. they are nan because they arent in the model (the way the model works, it has just removed these rows, so tahts why they are nans)
    #energy_use_merged['Energy_esto'] = energy_use_merged['Energy_esto'].fillna(0)
    energy_use_merged['Energy_model'] = energy_use_merged['Energy_model'].fillna(0)
    # But , for now, if theres any nans in Energy_esto then let the uyser know sicne there shouldnt really be any there.
    if energy_use_merged['Energy_esto'].isna().sum(numeric_only=True) > 0:
        nans = energy_use_merged.loc[energy_use_merged['Energy_esto'].isna(), ['Economy', 'Date', 'Scenario','Medium','Fuel']].drop_duplicates()
        breakpoint()
        raise ValueError('There are nans in energy_use_esto for the following rows: {}'.format(nans))
    #
    energy_use_merged['ratio'] = energy_use_merged['Energy_esto']/energy_use_merged['Energy_model']
    
    #where ratio becomes inf then this means that ESTO has >0 energy use and the model has 0 energy use. This is because the model didnt assume any use at that point in time. This is a semi common occuraence. So create anotehr col and call it 'addition' and put the Energy_esto value in ther to be split among its users later:
    #but first,m print what fuel, medium, economy combos have this issue:
    inf_rows = energy_use_merged.loc[energy_use_merged['ratio'] == np.inf, ['Fuel', 'Medium', 'Scenario','Economy']].drop_duplicates()
    if len(inf_rows[~inf_rows.Fuel.isin(['16_05_biogasoline', '16_06_biodiesel', '16_07_bio_jet_kerosene','16_01_biogas'])]) > 0:
        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
            print('The following fuel, medium, economy combos have inf ratio, meaning the model had 0 energy use but the esto data had >0 energy use. This is because the model didnt assume any use at that point in time. So create anotehr col and call it addition and put the Energy_esto value in ther to be split among its users later:')
            print(f'There are fuels other than 16_05_biogasoline and 16_06_biodiesel that have inf ratio. This is unexpected {inf_rows}. they will be set in the addition column')
        
    
    energy_use_merged['addition'] = 0
    energy_use_merged.loc[energy_use_merged['ratio'] == np.inf, 'addition'] = energy_use_merged.loc[energy_use_merged['ratio'] == np.inf, 'Energy_esto']
    #then replace the inf with 1
    energy_use_merged.loc[energy_use_merged['ratio'] == np.inf, 'ratio'] = 1
    
    #also where ratio is na, its because both values are 0, so just set ratio to 0
    energy_use_merged['ratio'] = energy_use_merged['ratio'].fillna(0)
    ()
    return energy_use_merged


#####################    
def calculate_required_energy_use_by_drive(config, input_data_based_on_previous_model_run, energy_use_merged, energy_use_output):
    """Times energy use in the model by the ratio between the energy use in the model and the energy use in the esto data. This will be used to adjust energy to be the same as in ESTO. Then add any additions to the Energy. this is where the ratio was inf because the model had 0 energy use but the esto data had >0. so we will add the esto data energy use to the model data energy use and just times by a ratio of 1. Then we can calcualte requried stocks for this energy use. Later when we double check that we've gfot the right energy use, we will do the mixing calcualtions to split drive into its mixed types, so we can tell if the calcualtions are correct for each fuel type.

    Args:
        input_data_based_on_previous_model_run (_type_): _description_
        energy_use_merged (_type_): _description_
        energy_use_output (_type_): _description_

    Returns:
        _type_: _description_
    """
    #CLEAN INPUT DATA 
    #get dates that match the esto data:
    input_data_new = input_data_based_on_previous_model_run.loc[input_data_based_on_previous_model_run['Date'].isin(energy_use_merged['Date'].unique())].copy()
    #merge energy_use_merged to energy_use_output using a right merge and times the ratio by the energy use in the model to get the new energy use (and the effect of timesing by the ratio will be that the total difference for that ['Economy', 'Date', 'Medium','Fuel'] spread equally among all rows for that ['Economy', 'Date', 'Medium','Fuel') (except for supply side fuel mixing fuels, which we will handle separately, and demand side fuel mixing fuels, which we will drop as they are too ahrd to handle)
    required_energy_use_by_drive_and_fuel = energy_use_merged.merge(energy_use_output, on=['Economy', 'Date','Scenario', 'Medium','Fuel'], how='right')
    #To make it a bit more simple, lets called Energy, Energy old. Then when we calcualte Energy*ratio it can be called Energy new. then rename it to energy and drop energy old before we move on:
    required_energy_use_by_drive_and_fuel.rename(columns={'Energy': 'Energy_old'}, inplace=True)   
    
    #do the ratio times enegry calc
    required_energy_use_by_drive_and_fuel['Energy_new'] = required_energy_use_by_drive_and_fuel['Energy_old']*required_energy_use_by_drive_and_fuel['ratio']

    #additions need to be split equally where they are made. do this using the proprtion of each energy use out of the total energy use for that fuel, scveanrio, medium, economy and date to do this:
    
    #replace energy with 0 where its na for the calcualtion
    required_energy_use_by_drive_and_fuel['Energy_new'] = required_energy_use_by_drive_and_fuel['Energy_new'].fillna(0)
    required_energy_use_by_drive_and_fuel['proportion_of_group'] = required_energy_use_by_drive_and_fuel.groupby(['Economy', 'Date','Scenario', 'Medium', 'Fuel'])['Energy_new'].transform(lambda x: x/x.sum(numeric_only=True))#theres an issue here that if the energy use for the whole group is 0 then the proportion will just be nan. There would be no way to estimate  the proportion bsdes absing ti off the previous year. however, this happening is really just a warning that there is somethign going wrong in the other code. To catch it, lets identify if tehre is any nan in the proportion_of_group col and if so, whether the addition col is >0. if so, then we know that there should be some energy use but its not possible to calculate the proportion. So thorw an error so the suer can track down why its happeneing
    #actually, it seems there arent going to be cases where proprotion of group is na bnut there was energy use in previous years. instead its where there is new energy use added. So we will just spread the new energy use equally among all rows for that fuel, scenario, medium, economy and date:
    na_df = required_energy_use_by_drive_and_fuel.loc[(required_energy_use_by_drive_and_fuel['proportion_of_group'].isna()) & (required_energy_use_by_drive_and_fuel['addition'] > 0)]
    required_energy_use_by_drive_and_fuel = required_energy_use_by_drive_and_fuel.loc[~((required_energy_use_by_drive_and_fuel['proportion_of_group'].isna()) & (required_energy_use_by_drive_and_fuel['addition'] > 0))]
    #spread the addition equally among all rows for that fuel, scenario, medium, economy and date:
    na_df['proportion_of_group'] = na_df.groupby(['Economy', 'Date','Scenario', 'Medium','Fuel'])['Energy_new'].transform(lambda x: 1/x.count())
    #add it to required_energy_use_by_drive_and_fuel
    required_energy_use_by_drive_and_fuel = pd.concat([required_energy_use_by_drive_and_fuel, na_df])

    required_energy_use_by_drive_and_fuel['addition'] = required_energy_use_by_drive_and_fuel['addition']*required_energy_use_by_drive_and_fuel['proportion_of_group'].replace(np.nan, 0)
    #now need to add any additions to the Energy. this is where the ratio was inf because the model had 0 energy use but the esto data had >0. so we will add the esto data energy use to the model data energy use and just times by a ratio of 1
    required_energy_use_by_drive_and_fuel['Energy_new'] = required_energy_use_by_drive_and_fuel['Energy_new'] + required_energy_use_by_drive_and_fuel['addition'].replace(np.nan, 0)
    #in a lot of cases the electricity use for road will be 0 but because phevs need elec to have been beiong used, we should add their primary fuel use to toher drives if  there is no road elec use. so lets do that now:
    required_energy_use_by_drive_and_fuel = replace_zero_elec_phevs(config, required_energy_use_by_drive_and_fuel)
    #####################################
    #INCORPORATE FUEL MIXING:
    #####################################
    required_energy_use_by_drive_and_fuel = incorporate_fuel_mixing_before_recalculating_stocks(config, required_energy_use_by_drive_and_fuel)
    #now we have the total energy use for each drive, rather than fuel. now we can calcualte requried stocks for this energy use. Later when we double check that we've gfot the right energy use, we will do the mixing calcualions to split drive into its mixed types, so we can tell if the calcualtions are correct for each fuel type.
    #####################################
    #CALCUALTE STOCKS AND OTEHR INPUTS FROM ENERGY USE:
    #####################################
    #and sum now that we've calclated the new enegry use for each 'Economy', 'Date', 'Medium', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario'
    required_energy_use_by_drive = required_energy_use_by_drive_and_fuel.groupby(['Economy', 'Date', 'Medium', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario']).sum(numeric_only=True).reset_index()
    
    #Now join on the measures we need from the detailed data so we can calcualte the new inputs for the model:
    required_energy_use_by_drive = required_energy_use_by_drive.merge(input_data_new[['Economy', 'Date', 'Medium', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario', 'Activity', 'Efficiency', 'Occupancy_or_load', 'Mileage', 'Intensity','Stocks', 'Activity_per_Stock']], on=['Economy', 'Date', 'Medium', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario'], how='left')
    
    return required_energy_use_by_drive

def calculate_required_values_by_measure_for_non_road(config, required_energy_use_by_drive, non_road_model_input_wide):
    
    input_data_new_non_road = required_energy_use_by_drive.loc[required_energy_use_by_drive['Medium'] != 'road'].copy()
    input_data_new_non_road['Activity'] = input_data_new_non_road['Energy_new'] / input_data_new_non_road['Intensity']
    
    # #TEMP, set Activity_per_Stock to 1
    # input_data_new_non_road['Activity_per_Stock'] = 1
    input_data_new_non_road['Stocks'] = input_data_new_non_road['Activity'] / input_data_new_non_road['Activity_per_Stock']
    # input_data_new_non_road.loc[(input_data_new_non_road['Energy_new'] > 0), 'Stocks'] = 1
    # input_data_new_non_road.loc[(input_data_new_non_road['Energy_new'] == 0), 'Stocks'] = 0

    #rename Energy_new to Energy
    input_data_new_non_road.rename(columns={'Energy_new': 'Energy'}, inplace=True)
    #drop cols unneeded for non road, by filtering tfor the same cols that are in non_road_model_input_wide
    input_data_new_non_road = input_data_new_non_road.loc[:, input_data_new_non_road.columns.isin(non_road_model_input_wide.columns)].copy()
    
    return input_data_new_non_road

def merge_and_replace_old_input_data_with_new_input_data(config, input_data_new_road_recalculated, input_data_new_non_road, road_model_input_wide, non_road_model_input_wide):
    ###################################
    #NOW MERGE AND REPLACE THE OLD INPUT DATA WITH THE NEW INPUT DATA
    #merge and add tehse missing cols back on usaing the original input data 
    road_all_wide = input_data_new_road_recalculated.copy()
    road_all_wide = road_all_wide.merge(road_model_input_wide, on=['Date', 'Economy', 'Medium', 'Transport Type','Vehicle Type',  'Drive', 'Scenario'], how='left', suffixes=('', '_new'))
    #check what new cols there are by seeing what cols are different between input_data_new_road and road_all_wide
    new_cols = [col for col in road_all_wide.columns if col not in input_data_new_road_recalculated.columns]
    #drop cols that end with _new
    road_all_wide = road_all_wide.loc[:,~road_all_wide.columns.str.endswith('_new')].copy()
    #and then concat road_model_input_wide to road_all_wide fopr the missing dates in road_all_wide:
    missing_dates = [date for date in road_model_input_wide['Date'].unique().tolist() if date not in road_all_wide['Date'].unique().tolist()]
    road_all_wide = pd.concat([road_all_wide, road_model_input_wide.loc[road_model_input_wide['Date'].isin(missing_dates)]])
    
    #NOW FOR NON ROAD    
    non_road_all_wide = input_data_new_non_road.copy()
    non_road_all_wide = non_road_all_wide.merge(non_road_model_input_wide, on=['Date', 'Economy', 'Medium','Vehicle Type', 'Transport Type', 'Drive', 'Scenario'], how='left', suffixes=('', '_new'))
    #check what new cols there are by seeing what cols are different between input_data_new_road_recalculated and non_road_model_input_wide
    new_cols = [col for col in input_data_new_non_road.columns if col not in non_road_all_wide.columns]
    #drop cols that end with _new
    non_road_all_wide = non_road_all_wide.loc[:,~non_road_all_wide.columns.str.endswith('_new')].copy()
    #and then concat non_road_model_input_wide to non_road_all_wide fopr the missing dates in non_road_all_wide:
    missing_dates = [date for date in non_road_model_input_wide['Date'].unique().tolist() if date not in non_road_all_wide['Date'].unique().tolist()]
    non_road_all_wide = pd.concat([non_road_all_wide, non_road_model_input_wide.loc[non_road_model_input_wide['Date'].isin(missing_dates)]])
        
    return road_all_wide, non_road_all_wide


def replace_zero_elec_phevs(config, required_energy_use_by_drive_and_fuel):
    #PLEASE NOTE I TOOK SOME SHORTCUTS WHILE MAKING THIS FUNCTION BECAUSE I FIGURED THAT THERE ARENT MANY PHEVS ON THE ROADS YET. hOWEVER AS TIME GOES ON IT WILL BECOME MORE IMPORTANT TO DO THIS PROPERLY. SO PLEASE REVISIT THIS FUNCTION AND MAKE SURE IT IS CORRECT. TODO
    #in a lot of cases the electricity use for road will be 0 but because phevs need elec to have been beiong used, we should add their primary fuel use to toher drives if  there is no road elec use. so lets do that now:
    phev_energy_use = required_energy_use_by_drive_and_fuel.loc[(required_energy_use_by_drive_and_fuel['Drive'].isin(['phev_d', 'phev_g']))].copy()
    required_energy_use_by_drive_and_fuel = required_energy_use_by_drive_and_fuel.loc[~(required_energy_use_by_drive_and_fuel['Drive'].isin(['phev_d', 'phev_g']))].copy()
    
    #grab rows only for elec use:
    phev_elec = phev_energy_use.loc[(phev_energy_use['Fuel'] == '17_electricity')].copy()
    #where elec use is 0, set missing_elec to true
    phev_elec['missing_elec'] = np.where(phev_elec['Energy_new'] == 0, True, False)
    #grab the primary fuel use for the phevs:
    phev_primary_fuel_use = phev_energy_use.loc[(phev_energy_use['Fuel'] != '17_electricity')].copy()
    #merge primary fuel sue with the phev_elec df so we can tell what primary fuel sue has 0 associated elec use. these we need to add to the other drives:
    phev_primary_fuel_use = phev_primary_fuel_use.merge(phev_elec, on=['Economy', 'Date', 'Scenario', 'Drive','Vehicle Type', 'Transport Type'], how='left', suffixes=('', '_elec'))
    #create a new df where missing_elec is true. we will set drive to ice_d and _g and concat it to main df later
    phev_primary_fuel_use_missing_elec = phev_primary_fuel_use.loc[phev_primary_fuel_use['missing_elec']].copy()
    phev_primary_fuel_use_missing_elec.loc[:, 'Drive'] = phev_primary_fuel_use_missing_elec['Drive'].str.replace('phev_', 'ice_')
    #then set the primary fuel use to 0 for these rows in the phev df:
    phev_primary_fuel_use.loc[phev_primary_fuel_use['missing_elec'], 'Energy_new'] = 0
    #concat all the dfs together
    new_rows = pd.concat([phev_primary_fuel_use_missing_elec, phev_primary_fuel_use, phev_elec])
    #drop cols ending in _elec
    new_rows = new_rows.drop(columns=[col for col in new_rows.columns if col.endswith('_elec')])
    
    #concat to main df and then sum
    required_energy_use_by_drive_and_fuel = pd.concat([required_energy_use_by_drive_and_fuel, new_rows])
    required_energy_use_by_drive_and_fuel = required_energy_use_by_drive_and_fuel.groupby(['Economy', 'Date', 'Medium', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario', 'Fuel']).sum(numeric_only=True).reset_index()   
    return required_energy_use_by_drive_and_fuel   

def incorporate_fuel_mixing_before_recalculating_stocks(config, required_energy_use_by_drive_and_fuel):
    """
    #since the fuel mixing fuels have had their energy use caslcualted, we will add their energy use to their corresponding drive types other fuels, so that when we recalcualte the required stocks we will get the stocks requried for their main fuels energy use plus the mixed fuels energy use. otherwise we'd be missing that. We will do this for demand and supply side fuel mixing: 

    Args:
        required_energy_use_by_drive_and_fuel (_type_): _description_

    Raises:
        ValueError: _description_
        ValueError: _description_
        ValueError: _description_
        ValueError: _description_

    Returns:
        _type_: _description_
    """
    #drop unneeded cols
    required_energy_use_by_drive_and_fuel = required_energy_use_by_drive_and_fuel.drop(columns=['ratio','addition','proportion_of_group', 'Energy_esto', 'Energy_model'])
    
    
    drive_type_to_fuel = pd.read_csv(os.path.join(config.root_dir, 'config', 'concordances_and_config_data', 'drive_type_to_fuel.csv'))
    #first supply side so we dont mix any biofuels with electricity which came from demand side fuel mixing:
    supply_side_fuel_mixing_drives = drive_type_to_fuel.loc[drive_type_to_fuel['Supply_side_fuel_mixing'] != False][['Drive','Fuel','Supply_side_fuel_mixing']].drop_duplicates()
    
    #then join that to the new enegry use
    supply_side_mixing_drives = required_energy_use_by_drive_and_fuel.merge(supply_side_fuel_mixing_drives, on=['Drive', 'Fuel'], how='left').copy()
    #create two dfs, one where supply_side_fuel_mixing is = to Original fuel and one where it is = to New fuel. then merge them on the drive (and other cols except fuel). Then add the energy use for the new fuel to the old fuel, then drop the new fuel col. 
    original_fuel = supply_side_mixing_drives.loc[supply_side_mixing_drives['Supply_side_fuel_mixing'] == 'Original fuel'].copy()
    new_fuel = supply_side_mixing_drives.loc[supply_side_mixing_drives['Supply_side_fuel_mixing'] == 'New fuel'].copy()    
    new_fuel = new_fuel.merge(original_fuel, on=['Economy', 'Date', 'Medium', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario'], how='left', suffixes=('', '_original'))
    #test for any nans. there shouldnt be any
    if len(new_fuel.loc[new_fuel['Energy_new'].isna()]) > 0:
        raise ValueError('There are nans in supply_side_mixing_drives')
    elif len(new_fuel.loc[new_fuel['Energy_new_original'].isna()]) > 0:
        raise ValueError('There are nans in supply_side_mixing_drives')
    #instead of adding the two energies toegehter, we need to set fuel to the Fuel_original. we will tehn concat it onto origianl
    new_fuel['Fuel'] = new_fuel['Fuel_original']
    new_fuel = new_fuel.drop(columns=['Fuel_original', 'Supply_side_fuel_mixing', 'Supply_side_fuel_mixing_original', 'Energy_new_original','Energy_old_original'])
    original_fuel = original_fuel.drop(columns=['Supply_side_fuel_mixing'])
    original_fuel = pd.concat([original_fuel, new_fuel])
    #sum 
    original_fuel = original_fuel.groupby(['Economy', 'Date', 'Medium', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario', 'Fuel']).sum(numeric_only=True).reset_index()
    #concat it to required_energy_use_by_drive_and_fuel after removing the rows that are in supply_side_mixing_drives
    required_energy_use_by_drive_and_fuel = required_energy_use_by_drive_and_fuel.loc[~(required_energy_use_by_drive_and_fuel['Drive'].isin(supply_side_mixing_drives['Drive'].unique().tolist()) & required_energy_use_by_drive_and_fuel['Fuel'].isin(supply_side_mixing_drives['Fuel'].unique().tolist()))].copy()
    required_energy_use_by_drive_and_fuel = pd.concat([required_energy_use_by_drive_and_fuel, supply_side_mixing_drives]).drop_duplicates()
    
    #separate the drives used for demand side fuel mixing. create a col which states what fuels rows are for new fuels or old. Then pivot so that for the fuel that is considered the 'new fuel' (electricity in case of phevs) then  it is on the other column, add its energy use to the main fuel then drop it.
    #identify demand side fuel mixing drives as those wherE Demand_side_fuel_mixing col is not False
    demand_side_fuel_mixing_drives = drive_type_to_fuel.loc[drive_type_to_fuel['Demand_side_fuel_mixing'] != False][['Drive','Fuel','Demand_side_fuel_mixing']].drop_duplicates()
    #then join that to the new enegry use
    demand_side_mixing_drives = required_energy_use_by_drive_and_fuel.merge(demand_side_fuel_mixing_drives, on=['Drive', 'Fuel'], how='left').copy()
    #create two dfs, one where Demand_side_fuel_mixing is = to Original fuel and one where it is = to New fuel. then merge them on the drive (and other cols except fuel). Then add the energy use for the new fuel to the old fuel, then drop the new fuel col. 
    original_fuel = demand_side_mixing_drives.loc[demand_side_mixing_drives['Demand_side_fuel_mixing'] == 'Original fuel'].copy()
    new_fuel = demand_side_mixing_drives.loc[demand_side_mixing_drives['Demand_side_fuel_mixing'] == 'New fuel'].copy()
    
    new_fuel = new_fuel.merge(original_fuel, on=['Economy', 'Date', 'Medium', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario'], how='left', suffixes=('', '_original'))
    #test for any nans. there shouldnt be any
    if len(new_fuel.loc[new_fuel['Energy_new'].isna()]) > 0:
        raise ValueError('There are nans in demand_side_mixing_drives')
    elif len(new_fuel.loc[new_fuel['Energy_new_original'].isna()]) > 0:
        raise ValueError('There are nans in demand_side_mixing_drives')
    #instead of adding the two energies toegehter, we need to set fuel to the Fuel_original. we will tehn concat it onto origianl
    new_fuel['Fuel'] = new_fuel['Fuel_original']
    new_fuel = new_fuel.drop(columns=['Fuel_original', 'Demand_side_fuel_mixing', 'Demand_side_fuel_mixing_original', 'Energy_new_original','Energy_old_original'])
    original_fuel = original_fuel.drop(columns=['Demand_side_fuel_mixing'])
    original_fuel = pd.concat([original_fuel, new_fuel])
    #sum 
    original_fuel = original_fuel.groupby(['Economy', 'Date', 'Medium', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario', 'Fuel']).sum(numeric_only=True).reset_index()
    #concat it to required_energy_use_by_drive_and_fuel after removing the rows that are in demand_side_mixing_drives
    required_energy_use_by_drive_and_fuel = required_energy_use_by_drive_and_fuel.loc[~required_energy_use_by_drive_and_fuel['Drive'].isin(demand_side_mixing_drives['Drive'].unique().tolist())].copy()
    required_energy_use_by_drive_and_fuel = pd.concat([required_energy_use_by_drive_and_fuel, demand_side_mixing_drives]).drop_duplicates(keep=False)  
    
    return required_energy_use_by_drive_and_fuel

#why is ratio so high in places? maybe need to fix.
def test_output_matches_expectations(config, ECONOMY_ID, supply_side_fuel_mixing, demand_side_fuel_mixing, road_all_wide, non_road_all_wide, energy_use_merged, BASE_YEAR, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=True):

        
    #calcauklte total energy use by year and economy for both road and non road.
    
    #we ahve an issue where the energy for diesel and petrol and their biofuels are about 10% less. it seems like it must ve because of supply side fuel mixing.. but probably becayse of the way its implemented.. rather than its value, since it seems the % diff is the same for all fuels. so lets check that first:
    #since we want to make sure that toal energy use for each fuel is the same then we will ahve to calcualte this first. this will involve fuel mixing calcs too:
    #first concat road and non road together
    energy_for_model_all  = pd.concat([road_all_wide, non_road_all_wide], axis=0)
    model_output_with_fuel_mixing = apply_fuel_mix_demand_side.apply_fuel_mix_demand_side(config, energy_for_model_all, ECONOMY_ID,  demand_side_fuel_mixing=demand_side_fuel_mixing,supply_side_fuel_mixing=supply_side_fuel_mixing)
    model_output_with_fuel_mixing = apply_fuel_mix_supply_side.apply_fuel_mix_supply_side(config, model_output_with_fuel_mixing, ECONOMY_ID, supply_side_fuel_mixing=supply_side_fuel_mixing)
    #double check the diff in enegry use is 0 between the two (since it shoudl be!)
    energy_diff = energy_for_model_all.Energy.sum(numeric_only=True) - model_output_with_fuel_mixing.Energy.sum(numeric_only=True)
    if abs(energy_diff) > 0.01:
        raise ValueError('energy use does not match between energy_for_model_all and model_output_with_fuel_mixing')
    
    # #first rmeove the supply_side_fuel_mixing_fuels from esto data!
    # energy_use_merged = energy_use_merged.loc[~energy_use_merged['Fuel'].isin(supply_side_fuel_mixing.New_fuel)].copy()
    model_output_with_fuel_mixing_test = model_output_with_fuel_mixing.groupby(['Economy','Scenario','Fuel','Medium', 'Date'])['Energy'].sum(numeric_only=True).reset_index().copy()
    esto_total_energy_use = energy_use_merged.groupby(['Economy','Scenario','Fuel','Medium', 'Date'])['Energy_esto'].sum(numeric_only=True).reset_index().copy()
    #print the differentce between total energy in the years 2017 to 2022
    print('Energy use difference after adjust_data_to_match_esto():')
    diff_pj = model_output_with_fuel_mixing_test.merge(esto_total_energy_use, on=['Economy', 'Scenario','Fuel','Medium', 'Date'], how='left', suffixes=('', '_esto'))
    if ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR:
        diff_pj = diff_pj.loc[(diff_pj.Date==config.OUTLOOK_BASE_YEAR)]
    else:
        diff_pj = diff_pj.loc[(diff_pj.Date>=BASE_YEAR) & (diff_pj.Date<=config.OUTLOOK_BASE_YEAR)]
    print((diff_pj['Energy'].sum(numeric_only=True) - diff_pj['Energy_esto'].sum(numeric_only=True))/2)#div by two to show avg diff across scenarios
    
    
    #Another test using the proportion difference between teh two:
    model_output_with_fuel_mixing_test = model_output_with_fuel_mixing.groupby(['Economy','Scenario','Fuel','Medium', 'Date'])['Energy'].sum(numeric_only=True).reset_index().copy()
    esto_total_energy_use = energy_use_merged.groupby(['Economy','Scenario','Fuel','Medium', 'Date'])['Energy_esto'].sum(numeric_only=True).reset_index().copy()

    diff_percent = model_output_with_fuel_mixing_test.merge(esto_total_energy_use, on=['Economy', 'Scenario','Fuel','Medium', 'Date'], how='left', suffixes=('', '_esto'))
    #filter for dates after base year
    if ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR:
        diff_percent = diff_percent.loc[diff_percent.Date==config.OUTLOOK_BASE_YEAR]
    else:
        diff_percent = diff_percent.loc[(diff_percent.Date>=BASE_YEAR) & (diff_percent.Date<=config.OUTLOOK_BASE_YEAR)]
    try:
        diff_percent = (sum(diff_percent['Energy'].dropna())/2) / (sum(diff_percent['Energy_esto'].dropna())/2)#div by two to show avg diff across scenarios
    except ZeroDivisionError:
        if sum(diff_percent['Energy'].dropna()) == 0 and sum(diff_percent['Energy_esto'].dropna()) == 0:
                diff_percent = 1
        else:
            diff_percent = 100#x/0 is essentially infinity, so just set it to 100
        
    if diff_percent > 1.01 or diff_percent < 0.99:
        breakpoint()
        #saev output to csv
        # diff_percent.to_csv(os.path.join(config.root_dir, 'intermediate_data', 'errors', 'ajust_data_to_match_esto_energy_use_diff.csv'))
        # raise ValueError('energy use does not match esto, proportion difference is  {}'.format(diff_percent))
        print('energy use does not match esto, proportion difference is  {}'.format(diff_percent))
        
    
def filter_for_testing_data_only(config, road_model_input_wide, non_road_model_input_wide, supply_side_fuel_mixing, input_data_based_on_previous_model_run, energy_use_output, energy_use_esto):
    
    #filter for only 01_AUS and year <= 2025 to make it run faster
    road_model_input_wide = road_model_input_wide[(road_model_input_wide['Date'] <= 2025)]
    non_road_model_input_wide = non_road_model_input_wide[(non_road_model_input_wide['Date'] <= 2025)]
    
    #  and year <= 2025 
    supply_side_fuel_mixing = supply_side_fuel_mixing[supply_side_fuel_mixing['Date'] <= 2025].copy()
    input_data_based_on_previous_model_run = input_data_based_on_previous_model_run[input_data_based_on_previous_model_run['Date'] <= 2025].copy()
    
    energy_use_esto = energy_use_esto[energy_use_esto['Date'] <= 2025].copy()
    energy_use_output = energy_use_output[energy_use_output['Date'] <= 2025].copy()
    
    return road_model_input_wide, non_road_model_input_wide, supply_side_fuel_mixing, input_data_based_on_previous_model_run, energy_use_output, energy_use_esto

def move_electricity_use_in_road_to_rail_esto(config, energy_use_esto, ECONOMY_ID):
    """In almost all cases that there is electricity use in road in the esto data it is likely this is a mistake > it is a lot more than i think there should be and results in having to allocate a large amount of ev stocks to the road sector. So lets move it to rail instead. This is a bit of a hack but it will do for now. We can revisit it later if we have time.
    
    We will only do this for specific economies, as specified in parameters.yml, which is because these economies have a significant amount of evs already, so people will want to see the results including them
    """

    road_elec = energy_use_esto.loc[(energy_use_esto['Medium'] == 'road') & (energy_use_esto['Fuel'] == '17_electricity')].copy()
    rail_elec = energy_use_esto.loc[(energy_use_esto['Medium'] == 'rail') & (energy_use_esto['Fuel'] == '17_electricity')].copy()
    
    #add road elec use to rail elec use then set road elec use to 0 in original df, remove rail elec use from original df and then concat it abck on
    rail_elec = rail_elec.merge(road_elec, on=['Economy', 'Date', 'Fuel'], how='left', suffixes=('', '_road'))
    
    #reaplce nas with 0. thse might occur where there is no road or rail elec use
    rail_elec['Energy'] = rail_elec['Energy'].replace(np.nan, 0)
    rail_elec['Energy_road'] = rail_elec['Energy_road'].replace(np.nan, 0)
    
    rail_elec['Energy'] = rail_elec['Energy'] + rail_elec['Energy_road']
    
    #drop cols ending in _road
    rail_elec = rail_elec.loc[:,~rail_elec.columns.str.endswith('_road')].copy()
    
    #set road elec use to 0 in original df
    energy_use_esto.loc[(energy_use_esto['Medium'] == 'road') & (energy_use_esto['Fuel'] == '17_electricity'), 'Energy'] = 0
    #remove rail elec use from original df
    energy_use_esto = energy_use_esto.loc[~((energy_use_esto['Medium'] == 'rail') & (energy_use_esto['Fuel'] == '17_electricity'))].copy()
    #concat it abck on
    energy_use_esto = pd.concat([energy_use_esto, rail_elec])
    return energy_use_esto
    
def format_9th_input_energy_from_esto(config, ECONOMY_ID=None, REDO_SAME_DATE_ID=False):
    
    #take in data from the EBT system of 9th and format it so that it can be used to create the energy data to whcih the model will be rescaled:
    #load the 9th data
    date_id = utility_functions.get_latest_date_for_data_file(os.path.join(config.root_dir, 'input_data', '9th_model_inputs'), 'model_df_wide_')
    energy_use_esto = pd.read_csv(os.path.join(config.root_dir, 'input_data', '9th_model_inputs', f'model_df_wide_{date_id}.csv'))
    #check that that matches config.latest_esto_data_FILE_DATE_ID. if not then jsut notify user
    if date_id != config.latest_esto_data_FILE_DATE_ID:
        print('WARNING: the date_id for the 9th model inputs does not match the latest esto data date_id. This is okay for now but it should be fixed later')
    #now check if we've already created an output for this file. if so then we dont need to do it again:energy_use_esto
    if os.path.exists(os.path.join(config.root_dir, f'intermediate_data', f'model_inputs_{date_id}.csv')) and not REDO_SAME_DATE_ID:
        energy_use_esto = pd.read_csv(os.path.join(config.root_dir, f'intermediate_data', f'model_inputs_{date_id}.csv'))
        if ECONOMY_ID != None:
            energy_use_esto = energy_use_esto.loc[energy_use_esto['Economy'] == ECONOMY_ID].copy()
        return energy_use_esto
    
    #reverse the mappings:
    medium_mapping_reverse = {v: k for k, v in config.medium_mapping.items()}

    #now format it so we only have the daata we need:
    # cols:'scenarios', 'economy', 'sectors', 'sub1sectors', 'sub2sectors',
    #    'sub3sectors', 'sub4sectors', 'fuels', 'subfuels', '1980'...
    #first filter so teh sector is transport:
    energy_use_esto = energy_use_esto.loc[energy_use_esto['sectors'] == '15_transport_sector'].copy()
    #and remove the sectors we dont consider in the model (pipeline )
    #and fiulter for ref scenario:
    energy_use_esto = energy_use_esto.loc[energy_use_esto['scenarios'] == 'reference'].copy()
    #and drop aggregate fuels:
    aggregate_cols = ['19_total', '20_total_renewables', '21_modern_renewables']
    energy_use_esto = energy_use_esto.loc[~energy_use_esto['fuels'].isin(aggregate_cols)].copy()
    #drop aggregate fuels which occur where subfuel is x:
    aggregate_x_fuels = ['16_others', '03_peat', '08_gas', '07_petroleum_products', '01_coal', '06_crude_oil_and_ngl']
    energy_use_esto = energy_use_esto.loc[~((energy_use_esto['fuels'].isin(aggregate_x_fuels)) & (energy_use_esto['subfuels'] == 'x'))].copy()
    #then do the mappings:
    #map the subfuel to the fuel
    #now map the subfuels to the subfuels in the esto data
    energy_use_esto['Fuel'] = energy_use_esto['subfuels'].map(config.temp_esto_subfuels_to_new_subfuels_mapping)
    #where subfuel is x then set Fuel to the value in fuels column:
    #frist remove any 02_coal_products in fuels col. THis is a bit of a rushed fix but it seems that since it is only for china and in 2017-2019 (0.1PJ) it will have little effect. This means we dont need to include it in the mapping or the x_subfuel_mappings dict which will crete confusion
    energy_use_esto = energy_use_esto.loc[~((energy_use_esto['fuels'] == '02_coal_products') & (energy_use_esto['subfuels'] == 'x'))].copy()
    
    energy_use_esto.loc[energy_use_esto['subfuels'] == 'x', 'Fuel'] = energy_use_esto['fuels'].map(config.x_subfuel_mappings)
    if len(energy_use_esto.loc[energy_use_esto['Fuel'].isna()]) > 0:
        
        # drop anyrows where the fuels column is 06_crude_oil_and_ngl, as we are going to remove that column on the input data side anyway (i.e. tell hyuga to drop it)
        nas = energy_use_esto.loc[energy_use_esto['Fuel'].isna()].loc[~energy_use_esto['subfuels'].isin(['06_01_crude_oil', '06_02_natural_gas_liquids', '07_11_ethane', '07_x_other_petroleum_products', '16_x_efuel'])].copy()
        if len(nas) > 0:
            breakpoint()
            raise ValueError('there are nans in Fuel because there was an x in subfuel and the fuel was not in the x_subfuel_mapping, {}'.format(energy_use_esto.loc[energy_use_esto['Fuel'].isna(), 'fuels'].unique()))
        else:
            #write big warnign just to rmeind you to remind hyuga to drop 06_crude_oil_and_ngl!
            if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                print('##########################\n\n there are nans in Fuel but they are all for the subfuels 07_11_ethane, 07_x_other_petroleum_products, 16_x_efuel, 06_01_crude_oil,06_02_natural_gas_liquids and these dont actually have any transport data asssociated with them (besides nonspecified or pipelin) so we will drop them on the input data side. AKA TELL HYUGA TO DROP them!\n\n##########################')#DONT KNOW HOW VALID THIS IS ANYMORE (11/13/2023)
            else:
                pass

    #map the medium to the sub1sector then drop the fuel and sectors cols since weve dfone all the mapping we can:
    energy_use_esto['Medium'] = energy_use_esto['sub1sectors'].map(medium_mapping_reverse)
    energy_use_esto = energy_use_esto.drop(columns=['sub1sectors', 'sub2sectors', 'sub3sectors', 'sub4sectors', 'sectors', 'fuels','subfuels', 'scenarios'])

    #then sum up the energy use by scenarios, economy, medium and subfuel:
    energy_use_esto = energy_use_esto.groupby(['economy', 'Medium', 'Fuel']).sum(numeric_only=True).reset_index()
    #melt so that the years are in one col and the energy use is in another:
    energy_use_esto = energy_use_esto.melt(id_vars=['economy', 'Medium', 'Fuel'], var_name='Date', value_name='Energy_esto')

    #rename economy to Economy, 
    energy_use_esto.rename(columns={'economy': 'Economy'}, inplace=True)

    # #drop any 0's or nas:
    energy_use_esto = energy_use_esto.loc[energy_use_esto['Energy_esto'] > 0].copy()

    #drop data that is less than the BASE_YEAR and more than config.OUTLOOK_BASE_YEAR
    energy_use_esto['Date'] = energy_use_esto['Date'].apply(lambda x: x[:4])
    energy_use_esto['Date'] = energy_use_esto['Date'].astype(int)
    energy_use_esto = energy_use_esto.loc[energy_use_esto['Date'] >= config.DEFAULT_BASE_YEAR].copy()
    energy_use_esto = energy_use_esto.loc[energy_use_esto['Date'] <= config.OUTLOOK_BASE_YEAR].copy()

    #drop '22_SEA', '23_NEA', '23b_ONEA', '24_OAM','24b_OOAM', '25_OCE', 'APEC' Economys
    energy_use_esto = energy_use_esto.loc[~energy_use_esto['Economy'].isin(['22_SEA', '23_NEA', '23b_ONEA', '24_OAM','24b_OOAM', '25_OCE', 'APEC'])].copy()

    #lastly, using the concordances, we will identify any fuel/medium combinations that arent in either and notify the user. for ones that are dealt with in the dicitonary below, do that (they are probably just errors in the data that ive already noticed), for the others, throw an error:
    missing_fuels_and_mediums_to_new_fuels_and_mediums = {
        'road':{
            # '07_x_other_petroleum_products': ('07_x_other_petroleum_products', 'nonspecified'),
            # '16_09_other_sources': ('16_09_other_sources', 'nonspecified'),
            '07_02_aviation_gasoline': ('07_02_aviation_gasoline', 'nonspecified'),
            '07_06_kerosene': ('07_06_kerosene', 'nonspecified'),
            '07_08_fuel_oil': ('07_08_fuel_oil', 'nonspecified'), 
        },
        # 'rail':{
            # '07_x_other_petroleum_products': ('07_x_other_petroleum_products', 'nonspecified'),
            # '16_09_other_sources': ('16_09_other_sources', 'nonspecified'),
        # },
        # 'air':{
        #     '07_x_other_petroleum_products': ('07_x_other_petroleum_products', 'nonspecified')
        # },
        # 'ship':{
        #     '16_09_other_sources':
        #     ('16_09_other_sources', 'nonspecified')}
    }
        
    #dso mapping now ewith the new fuels and mediums:
    for medium, fuels in missing_fuels_and_mediums_to_new_fuels_and_mediums.items():
        for fuel, new_fuel_and_medium in fuels.items():
            energy_use_esto.loc[(energy_use_esto['Medium'] == medium) & (energy_use_esto['Fuel'] == fuel), 'Fuel'] = new_fuel_and_medium[0]
            energy_use_esto.loc[(energy_use_esto['Medium'] == medium) & (energy_use_esto['Fuel'] == fuel), 'Medium'] = new_fuel_and_medium[1]
    
    concordances_fuels = pd.read_csv(os.path.join(config.root_dir, 'intermediate_data', 'computer_generated_concordances', '{}'.format(config.model_concordances_file_name_fuels)))
    concordances_fuels = concordances_fuels[['Fuel', 'Medium']].drop_duplicates()
    energy_use_esto_fuel_medium = energy_use_esto[['Fuel', 'Medium']].drop_duplicates()
    #drop nonspecified and pipeline from energy_use_esto_fuel_medium
    energy_use_esto_fuel_medium = energy_use_esto_fuel_medium.loc[~energy_use_esto_fuel_medium['Medium'].isin(['nonspecified', 'pipeline'])].copy()

    #do an outer join and then identify any nans:
    outer_join = concordances_fuels.merge(energy_use_esto_fuel_medium, on=['Fuel', 'Medium'], how='outer', indicator=True)

    #TODO MAKE THIS ACTIVIE ONCE WE HAVE THE CONCORDANCES FOR THE NEW FUELS AND MEDIUMS
    # #where merge is 'left_only' then throw an error. this is wherte a fuel is used in tthe model but isnt in esto. for now we will add these as 0 rows to the data but let the user now with a very visible message!
    left_only = outer_join.loc[outer_join['_merge'] == 'left_only']
    # ignored_fuels_and_mediums = ['07_x_other_petroleum_products', '16_09_other_sources', '07_02_aviation_gasoline', '07_06_kerosene', '07_08_fuel_oil']
    if len(left_only) > 0:
        # try:
        # energy_use_esto_new = energy_use_esto.copy()
        #for each row in left_only, add a row to energy_use_esto_new with the fuel and medium and energy set to 0, for every economy and date:
        for index, row in left_only.iterrows():
            for economy in energy_use_esto['Economy'].unique():
                for date in energy_use_esto['Date'].unique():
                    energy_use_esto_new_df_row = pd.DataFrame({'Economy': [economy], 'Date': [date], 'Medium': [row['Medium']], 'Fuel': [row['Fuel']], 'Energy_esto': [0]})
                    #concat to energy_use_esto
                    energy_use_esto = pd.concat([energy_use_esto, energy_use_esto_new_df_row])
            if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                print('###############################\n')
                print('there is a fuel\\medium combination in the model that is not in the esto data. These should at least have values = to 0. it is {} and {}'.format(row['Fuel'], row['Medium']))
        # except:#TODO i dont think this was the issue
        #     #trying to find a bug here. Its to do with 16_06_biodiesel. 
        #     breakpoint()
        #     raise ValueError('there is a fuel\\medium combination in the model that is not in the esto data. These should at least have values = to 0. it is {} and {}'.format(row['Fuel'], row['Medium']))

    #and now drop pipeline and nonspecified from energy_use_esto:
    energy_use_esto = energy_use_esto.loc[~energy_use_esto['Medium'].isin(['nonspecified', 'pipeline'])].copy()
    energy_use_esto = energy_use_esto.groupby(['Economy', 'Medium','Date', 'Fuel']).sum(numeric_only=True).reset_index()
    #reame Energy_esto to Energy:
    energy_use_esto.rename(columns={'Energy_esto': 'Energy'}, inplace=True)
    
    #save the file to the intermediate_data folder
    energy_use_esto.to_csv(os.path.join(config.root_dir, f'intermediate_data\\model_inputs_{date_id}.csv'), index=False)
    
    if ECONOMY_ID != None:
        energy_use_esto = energy_use_esto.loc[energy_use_esto['Economy'] == ECONOMY_ID].copy()
    return energy_use_esto


#%%

# format_9th_input_energy_from_esto(config, '15_PHL')
#%%
def plot_optimised_results(config, input_data_new_road_copy, new_measures_cols, original_measures_cols, id='', only_2020=True, transport_type=''):
    #plot results to double check:
    plotting_df = input_data_new_road_copy[['Economy', 'Date', 'Medium', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario']+original_measures_cols+new_measures_cols+['Energy_new', 'Energy_old']].copy()
    if only_2020:
        #drop non 2020 data
        plotting_df = plotting_df.loc[plotting_df['Date'] == 2020].copy()
    #grab only Reference scenario
    plotting_df = plotting_df.loc[plotting_df['Scenario'] == 'Reference'].copy()
    #melt so all measures are in one col
    plotting_df = plotting_df.melt(id_vars=['Economy', 'Date', 'Medium', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario'], value_vars=new_measures_cols+original_measures_cols+['Energy_new', 'Energy_old'], var_name='Measure', value_name='Value')
    #if measure ends with new, then its the new value, so set dataset to new
    plotting_df['Dataset'] = plotting_df['Measure'].apply(lambda x: 'New' if x.endswith('_new') else 'Old')
    #remove _new from measure
    plotting_df['Measure'] = plotting_df['Measure'].apply(lambda x: x.replace('_new', ''))
    
    plotting_df['Measure'] = plotting_df['Measure'].apply(lambda x: x.replace('_old', ''))
    
    #pivot so we have a col for new and old for each measure
    plotting_df = plotting_df.pivot(index=['Economy', 'Date', 'Medium', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario', 'Measure'], columns='Dataset', values='Value').reset_index()
    #now clacualte % change. where its 0, set to nan so it doesnt show up on the plot
    plotting_df['% change'] = ((plotting_df['New'] - plotting_df['Old'])/plotting_df['Old'])*100
    plotting_df.loc[plotting_df['% change'] == 0, '% change'] = np.nan
    
    
    economy = plotting_df['Economy'].unique()[0]
    title='New {} by vehicle type for {} {}'.format(' and '.join(new_measures_cols), economy, transport_type)
    #add the drive and dataset together
    # plotting_df['Drive'] = plotting_df['Drive'] + ' ' + plotting_df['Dataset']
    #and sort by them so 
    fig = px.strip(plotting_df, x='Vehicle Type', y='% change', color='Drive', title=title, facet_col='Transport Type', facet_row='Measure', hover_data=['New', 'Old'])
    #write to html in plotting_output/input_exploration/esto_reestimations
    fig.write_html(os.path.join(config.root_dir, 'plotting_output\\input_exploration\\esto_reestimations\\{}_{}_{}.html'.format(id, economy, title)), auto_open=False)
    #remember to set input_data_new_road_copy to input_data_new_road once we are happy with the results 
    

def reformat_optimised_results(config, input_data_new_road_recalculated, input_data_new_road):
                
    #get input_data_new_road_recalculated ready for use:
    #make wide
    input_data_new_road_recalculated = input_data_new_road_recalculated.pivot(index=['Economy', 'Date', 'Medium', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario'], columns='Measure', values='Value').reset_index()
    #replicate df for Target scenario
    input_data_new_road_recalculated_t = input_data_new_road_recalculated.copy()
    input_data_new_road_recalculated_t['Scenario'] = 'Target'
    
    input_data_new_road_recalculated = pd.concat([input_data_new_road_recalculated, input_data_new_road_recalculated_t])
    
    #insert prervious values for other measures form input_data_new_road
    input_data_new_road_missing_measures = input_data_new_road[['Economy', 'Date', 'Medium', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario', 'Activity', 'Occupancy_or_load',  'Intensity', 'Activity_per_Stock']].copy()
    #join it to input_data_new_road_recalculated
    input_data_new_road_recalculated = input_data_new_road_recalculated.merge(input_data_new_road_missing_measures, on=['Economy', 'Date', 'Medium', 'Vehicle Type', 'Transport Type', 'Drive', 'Scenario'], how='left')
    
    #calcualte travelkm and activity
    input_data_new_road_recalculated['Travel_km'] = input_data_new_road_recalculated['Energy_new'] *  input_data_new_road_recalculated['Efficiency']
    input_data_new_road_recalculated['Activity'] = input_data_new_road_recalculated['Travel_km'] * input_data_new_road_recalculated['Occupancy_or_load']
    
    input_data_new_road_recalculated['Energy_old'] = np.nan #just to make sure it is not used
    return input_data_new_road_recalculated 
    

def match_optimised_results_to_required_energy_use_exactly(config, input_data_new_road_recalculated, input_data_new_road):
    #need energy_use to be in a sum by drive, as each drive represents a fuel type currently (or at least a mix fuel typ with the supply side fuel mixing inherently considered as a set % of the energy use of the drive, plus the major fuel type for that drive!).
    #so just grab input_data_new_road and drop vehicle type and transport type cols then sum energy use by drive, then merge with optimised data, summed in the same way, and calcualte ratio between the two. Then times the optimised data by the ratio to get the new energy use. Then recalcualte the other measures from this new energy use! (the same process we use before but without considering a fuel column)
    input_data_new_road = input_data_new_road.drop(columns=['Vehicle Type', 'Transport Type']).groupby(['Economy', 'Date', 'Medium', 'Drive', 'Scenario']).sum(numeric_only=True).reset_index()
    input_data_new_road_recalculated_no_vtype_ttype = input_data_new_road_recalculated.drop(columns=['Vehicle Type', 'Transport Type']).groupby(['Economy', 'Date', 'Medium', 'Drive', 'Scenario']).sum(numeric_only=True).reset_index()
    #merge them
    input_data_new_road_recalculated_no_vtype_ttype = input_data_new_road_recalculated_no_vtype_ttype.merge(input_data_new_road, on=['Economy', 'Date', 'Medium', 'Drive', 'Scenario'], how='left', suffixes=('', '_required'))
    #calcualte ratio
    input_data_new_road_recalculated_no_vtype_ttype['ratio'] = input_data_new_road_recalculated_no_vtype_ttype['Energy_new']/input_data_new_road_recalculated_no_vtype_ttype['Energy_new_required']#replace nas with 1
    input_data_new_road_recalculated_no_vtype_ttype['ratio'] = input_data_new_road_recalculated_no_vtype_ttype['ratio'].fillna(1)

    #identify any infs. it seems that as a result of adding the new function move_electricity_use_in_road_to_rail_esto(config) we started getting infs for phevs because we were removing elec use in road but somewhere along the line (probably in the phev fucntion:replace_zero_elec_phevs()) we set the energy use by phevs to somethign where it shouldnt be anything (because we moved all elec use in road to rail). Anyway, its such a small amount, we will just set the inf to 1 and leave it. but make sureits noted for future reference:
    if len(input_data_new_road_recalculated_no_vtype_ttype.loc[input_data_new_road_recalculated_no_vtype_ttype['ratio'] == np.inf]) > 0:
        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
            print('###############################\n')
            # print('there are infs in the ratio column. this is because we are removing elec use in road but somewhere along the line (probably in the phev fucntion:replace_zero_elec_phevs()) we set the energy use by phevs to somethign where it shouldnt be anything (because we moved all elec use in road to rail). Anyway, its such a small amount, we will just set the inf to 1 and leave it. but make sureits noted for future reference!')
            #actually raise and error too
            raise ValueError('there are infs in the ratio column. this is because we are removing elec use in road but somewhere along the line (probably in the phev fucntion:replace_zero_elec_phevs()) we set the energy use by phevs to somethign where it shouldnt be anything (because we moved all elec use in road to rail). Anyway, its such a small amount, we will just set the inf to 1 and leave it. but make sureits noted for future reference!')
        else:
            pass
        input_data_new_road_recalculated_no_vtype_ttype['ratio'] = input_data_new_road_recalculated_no_vtype_ttype['ratio'].replace(np.inf, 1)        

    #keep only the cols we need
    input_data_new_road_recalculated_no_vtype_ttype = input_data_new_road_recalculated_no_vtype_ttype[['Economy', 'Date', 'Medium', 'Drive', 'Scenario', 'ratio']].copy()
    #merge ratio to input_data_new_road_recalculated
    input_data_new_road_recalculated = input_data_new_road_recalculated.merge(input_data_new_road_recalculated_no_vtype_ttype, on=['Economy', 'Date', 'Medium', 'Drive', 'Scenario'], how='left')
    #calcualte new energy use
    input_data_new_road_recalculated['Energy_new'] = input_data_new_road_recalculated['Energy_new']/input_data_new_road_recalculated['ratio']
    #drop ratio and any cols ending with _required
    input_data_new_road_recalculated = input_data_new_road_recalculated.drop(columns=['ratio']+input_data_new_road_recalculated.columns[input_data_new_road_recalculated.columns.str.endswith('_required')].tolist())
    #now recalcualte the stocks from this new energy use. They will only change by a smidgeon, but we need to do this to make sure the energy use is correct        
    #rename sotkcs to stocks old
    input_data_new_road_recalculated.rename(columns={'Stocks': 'Stocks_old'}, inplace=True)
    input_data_new_road_recalculated['Travel_km'] = input_data_new_road_recalculated['Energy_new'] * input_data_new_road_recalculated['Efficiency']

    input_data_new_road_recalculated['Activity'] = input_data_new_road_recalculated['Travel_km'] * input_data_new_road_recalculated['Occupancy_or_load']

    input_data_new_road_recalculated['Stocks'] = input_data_new_road_recalculated['Activity'] / (input_data_new_road_recalculated['Mileage'] * input_data_new_road_recalculated['Occupancy_or_load'])
    input_data_new_road_recalculated.rename(columns={'Energy_new': 'Energy'}, inplace=True)
    #drop energy old if ti exists    
    input_data_new_road_recalculated = input_data_new_road_recalculated.drop(columns=['Energy_old'], errors='ignore')

    return input_data_new_road_recalculated
#%%
#%%
