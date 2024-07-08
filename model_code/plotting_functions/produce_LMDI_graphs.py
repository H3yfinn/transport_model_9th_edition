# d:\APERC\PyLMDI\saved_runs\transport_8th_analysis.py
#run the PyLMDI functiosn to produce LMDI graphs of the results. 
#note that the library is in ../PyLMDI

#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
from .. import utility_functions
from ..pylmdi import main_function, plot_output
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

#%%
def produce_lots_of_LMDI_charts(config, ECONOMY_ID=None, USE_LIST_OF_CHARTS_TO_PRODUCE = False, PLOTTING = False, USE_LIST_OF_DATASETS_TO_PRODUCE=True, END_DATE=2070, PLOT_EFFECT_OF_ELEC_EMISSIONS_FACTOR=True, INCLUDE_LIFECYCLE_EMISSIONS=True, PLOT_EMISSIONS_FACTORS=False, SET_START_DATE_TO_AFTER_COVID=True):
    #take in energy and activity data 
    if ECONOMY_ID == None:
        all_data = pd.read_csv(config.root_dir + '\\' + 'output_data\\model_output\\all_economies_{}_{}'.format(config.FILE_DATE_ID, config.model_output_file_name))
        energy_use_by_fuels = pd.read_csv(config.root_dir + '\\' + 'output_data\\model_output_with_fuels\\all_economies_{}_{}'.format(config.FILE_DATE_ID, config.model_output_file_name))
        detailed_data = pd.read_csv(config.root_dir + '\\' + 'output_data\\model_output_detailed\\all_economies_{}_{}'.format(config.FILE_DATE_ID, config.model_output_file_name))
    else:
        all_data = pd.read_csv(config.root_dir + '\\' + 'output_data\\model_output\\{}_{}'.format(ECONOMY_ID,config.model_output_file_name))
        energy_use_by_fuels = pd.read_csv(config.root_dir + '\\' + 'output_data\\model_output_with_fuels\\{}_{}'.format(ECONOMY_ID,config.model_output_file_name))
        detailed_data = pd.read_csv(config.root_dir + '\\' + 'output_data\\model_output_detailed\\{}_{}'.format(ECONOMY_ID,config.model_output_file_name))
    
    if SET_START_DATE_TO_AFTER_COVID:
        #TO BE SAFE WE HAVE TO SET THE START DATE TO AFTER WHEN ANY RETURN TO NORMAL AFTER COVID WAS OVER. SO WE WILL SET IT TO 2024, EVEN THOUGH THAT IS 3 YEARS AFTER OUR BASE YEAR DATA:
        all_data = all_data[all_data['Date']>=2024]
        energy_use_by_fuels = energy_use_by_fuels[energy_use_by_fuels['Date']>=2024]
        detailed_data = detailed_data[detailed_data['Date']>=2024]
        
    #here write the charts you want to produce.. can use this to make the function run quicker by only producing some of the charts
    if USE_LIST_OF_CHARTS_TO_PRODUCE:
        charts_to_produce = []
        for economy in all_data.Economy.unique():
            for scenario in all_data.Scenario.unique():
                for transport_type in all_data['Transport Type'].unique():
                    charts_to_produce.append(f'{economy}_{scenario}_{transport_type}_road_2_Energy use_Hierarchical_{END_DATE}')
                    charts_to_produce.append(f'{economy}_{scenario}_{transport_type}_road_2_Emissions_Hierarchical_{END_DATE}')
                charts_to_produce.append(f'{economy}_{scenario}_road_1_Energy use_{END_DATE}')
                charts_to_produce.append(f'{economy}_{scenario}_road_2_Energy use_Hierarchical_{END_DATE}')
            charts_to_produce.append(f'{economy}_road_1_Energy use_{END_DATE}')
            charts_to_produce.append(f'{economy}_road_2_Energy use_Hierarchical_{END_DATE}')
    
    if USE_LIST_OF_DATASETS_TO_PRODUCE:
        datasets_to_produce = []
        for economy in all_data.Economy.unique():
            for scenario in all_data.Scenario.unique():
                for transport_type in all_data['Transport Type'].unique():
                    datasets_to_produce.append(f'{economy}_{scenario}_{transport_type}_road_1_Energy use_{END_DATE}')
                    datasets_to_produce.append(f'{economy}_{scenario}_{transport_type}_road_2_Energy use_Hierarchical_{END_DATE}')
                    datasets_to_produce.append(f'{economy}_{scenario}_{transport_type}_road_2_Emissions_Hierarchical_{END_DATE}')
                datasets_to_produce.append(f'{economy}_{scenario}_road_1_Energy use_{END_DATE}')
                datasets_to_produce.append(f'{economy}_{scenario}_road_2_Energy use_Hierarchical_{END_DATE}')
            datasets_to_produce.append(f'{economy}_road_1_Energy use_{END_DATE}')
            datasets_to_produce.append(f'{economy}_road_2_Energy use_Hierarchical_{END_DATE}')
    # #simplify by filtering for road medium only
    # all_data = all_data[all_data['Medium'] == 'road']
    #make drive and vehicle type = medium where it is no road
    temp = all_data.loc[all_data['Medium'] != 'road'].copy()
    temp['Drive'] = temp['Medium']
    temp['Vehicle Type'] = temp['Medium']
    all_data.loc[all_data['Medium'] != 'road'] = temp
    temp = energy_use_by_fuels.loc[energy_use_by_fuels['Medium'] != 'road'].copy()
    temp['Drive'] = temp['Medium']
    temp['Vehicle Type'] = temp['Medium']
    energy_use_by_fuels.loc[energy_use_by_fuels['Medium'] != 'road'] = temp
    
    # #filter for Date >= config.OUTLOOK_BASE_YEAR
    # all_data = all_data[all_data['Date']>=config.OUTLOOK_BASE_YEAR]
    # #and filter so data is less than config.GRAPHING_END_YEAR
    # all_data = all_data[all_data['Date']<=config.GRAPHING_END_YEAR]
    ################################################
    #drop nans?
    all_data = all_data.dropna()
    
    #create a 'APEC' economy which is the sum of all and concat it on:
    APEC = all_data.copy()
    #set economy to APEC
    APEC['Economy'] = 'APEC'
    APEC.groupby(['Date', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Medium']).sum(numeric_only=True).reset_index()

    #concat APEC on
    all_data = pd.concat([all_data, APEC])

    ###########################################################################

    #we will create a script which will loop through the different combinations of data we have and run the LMDI model on them and plot them

    AUTO_OPEN = False

    combined_transport_type_waterfall_inputs = {}
    combined_scenario_waterfall_inputs = {}
    combination_dict_list = []
    #instead of specifiying them manually which is quite repetivitve i am going to create the combinations for wehich we want to run the lmdi method and its graphing functions in a loop by creating a set of different values for each of the variables in the dictionary and then looping through all the combinations of these values to create a permutation of each of the combinations. In some cases there will need to be some extra logic because some values can only go with each other. 
    scenario_list = ['Reference', 'Target']
    transport_type_list = ['passenger', 'freight']
    medium_list = ['everything', 'road']
    structure_variables_list = [['Economy','Vehicle Type', 'Engine switching'],['Vehicle Type', 'Engine switching'], ['Engine switching']]
    emissions_divisia_list = [False, True]
    hierarchical_list = [False, True]
    economy_list = all_data.Economy.unique()
    for scenario in scenario_list:
        if scenario == 'Reference':
            scenario_text = 'Reference'
        elif scenario == 'Target':
            scenario_text = 'Target'

        for transport_type in transport_type_list:
            if transport_type == 'passenger':
                activity_variable = 'passenger_km'
            elif transport_type == 'freight':
                activity_variable = 'freight_tonne_km'

            for medium in medium_list:
                if medium == 'everything':
                    medium = 'all_mediums'
                for structure_variables in structure_variables_list:
                    residual_variable1 = '{} efficiency'.format(structure_variables[-1])
                    if residual_variable1== 'Engine switching efficiency':
                        residual_variable1 = 'Vehicle efficiency'
                        
                    for emissions_divisia in emissions_divisia_list:
                        emissions_string = 'Energy use'
                        if emissions_divisia == True:
                            emissions_string = 'Emissions'
                            
                        for hierarchical in hierarchical_list:
                            hierarchical_string = '' 
                            if hierarchical == True:
                                hierarchical_string = 'Hierarchical'                          
                                if len(structure_variables) == 1:
                                    continue#hierarchical only for more than one structure variable
                            else:
                                if len(structure_variables) > 1:
                                    continue
                                    # print('hierarchical shoudl almost always be used where there is more than one structure variable, so the graphing tools are not built to handle this case since each residual efficiency value wont have the correct labels')
                            for economy in economy_list:
                                if hierarchical:
                                    
                                    extra_identifier = '{}_{}_{}_{}_{}_{}_{}_{}'.format(economy,scenario, transport_type, medium, len(structure_variables),emissions_string, hierarchical_string, END_DATE)
                                    graph_title = '{} {} {} - Drivers of {} - LMDI'.format(economy, medium, transport_type,emissions_string)
                                    graph_title = scenario_text #+ ' 1.4% improvement in efficiency'
                                else:
                                    
                                    extra_identifier = '{}_{}_{}_{}_{}_{}_{}'.format(economy,scenario, transport_type, medium, len(structure_variables),emissions_string, END_DATE)
                                    graph_title = '{} {} {} - Drivers of {} - LMDI'.format(economy, medium, transport_type,emissions_string)
                                    graph_title = scenario_text# + ' 1.4% improvement in efficiency'

                                combination_dict_list.append({'economy':economy,'scenario':scenario, 'transport_type':transport_type, 'medium':medium, 'activity_variable':activity_variable, 'structure_variables_list':structure_variables, 'graph_title':graph_title, 'extra_identifier':extra_identifier, 'emissions_divisia':emissions_divisia, 'hierarchical':hierarchical, 'residual_variable1':residual_variable1,
                                'output_data_folder': f'intermediate_data\\LMDI\\{economy}\\', 'plotting_output_folder':f'plotting_output\\LMDI\\{economy}\\'})
                                
                                extra_identifier_no_transport_type = extra_identifier.replace(f'{transport_type}_', '')
                                graph_title = graph_title.replace(f'{transport_type} ', '')
                                extra_identifier_no_scenario = extra_identifier.replace(f'{scenario}_', '')
                                if extra_identifier_no_transport_type not in combined_transport_type_waterfall_inputs.keys():
                                    combined_transport_type_waterfall_inputs[extra_identifier_no_transport_type] = [{'economy':economy, 'scenario':scenario, 'activity_variable':activity_variable, 'structure_variables_list':structure_variables, 'graph_title':graph_title, 'extra_identifier':extra_identifier, 'emissions_divisia':emissions_divisia, 'hierarchical':hierarchical, 'residual_variable1':residual_variable1,'output_data_folder': f'intermediate_data\\LMDI\\{economy}\\', 'plotting_output_folder':f'plotting_output\\LMDI\\{economy}\\'}]
                                else:
                                    combined_transport_type_waterfall_inputs[extra_identifier_no_transport_type].append({'economy':economy, 'scenario':scenario, 'activity_variable':activity_variable, 'structure_variables_list':structure_variables, 'graph_title':graph_title, 'extra_identifier':extra_identifier, 'emissions_divisia':emissions_divisia, 'hierarchical':hierarchical, 'residual_variable1':residual_variable1,'output_data_folder': f'intermediate_data\\LMDI\\{economy}\\', 'plotting_output_folder':f'plotting_output\\LMDI\\{economy}\\'})
                                
                                if extra_identifier_no_scenario not in combined_scenario_waterfall_inputs.keys():
                                    combined_scenario_waterfall_inputs[extra_identifier_no_scenario] = [{'economy':economy,'activity_variable':activity_variable, 'structure_variables_list':structure_variables, 'graph_title':graph_title, 'extra_identifier':extra_identifier, 'emissions_divisia':emissions_divisia, 'hierarchical':hierarchical, 'residual_variable1':residual_variable1,'output_data_folder': f'intermediate_data\\LMDI\\{economy}\\', 'plotting_output_folder':f'plotting_output\\LMDI\\{economy}\\'}]
                                else:
                                    combined_scenario_waterfall_inputs[extra_identifier_no_scenario].append({'economy':economy,'activity_variable':activity_variable, 'structure_variables_list':structure_variables, 'graph_title':graph_title, 'extra_identifier':extra_identifier, 'emissions_divisia':emissions_divisia, 'hierarchical':hierarchical, 'residual_variable1':residual_variable1,'output_data_folder': f'intermediate_data\\LMDI\\{economy}\\', 'plotting_output_folder':f'plotting_output\\LMDI\\{economy}\\'})
    
    ###########################################################################
    # Do final data prep and then run the LMDI method and plot the results
    #extract stocks cols from detailed data
    stocks = detailed_data[['Economy', 'Scenario', 'Date', 'Transport Type', 'Vehicle Type', 'Drive', 'Medium', 'New_stocks_needed']].copy()
    #drop Stocks col
    all_data = all_data.drop(columns = ['Stocks'])

    all_data, electricity_emissions = calculate_emissions(config, energy_use_by_fuels, all_data, USE_AVG_GENERATION_EMISSIONS_FACTOR=False)
    
    better_names_dict = {'Drive': 'Engine switching', 'Energy':'Energy use'}
    #before going through the data lets rename some structural variables to be more readable
    all_data = all_data.rename(columns=better_names_dict)
    ###########################################################################
    #create loop to run through the combinations
    i=0
    
    # f'{economy}_{scenario}_{transport_type}_road_2_Emissions_Hierarchical_{END_DATE}'
    for combination_dict in combination_dict_list:
        
        try:
            if USE_LIST_OF_DATASETS_TO_PRODUCE and combination_dict['extra_identifier'] not in datasets_to_produce:
                # if 
                # print('skipping {}'.format(combination_dict['extra_identifier']))
                continue
            
            i+=1
            # print('\n\nRunning lmdi method for {}th iteration for '.format(i,combination_dict['extra_identifier']))
            # if combination_dict['extra_identifier'] == '15_PHL_Reference_passenger_road_2_Energy use_Hierarchical':
            #     breakpoint()
            #create a dataframe for each combination
            try:
                activity_data, energy_data, emissions_data = prepare_data_for_divisia(config, combination_dict, all_data, END_DATE)
            except Exception as e:
                if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                    breakpoint()
                    print(e)
            #set variables to input into the LMDI function
            economy = combination_dict['economy']
            activity_variable = combination_dict['activity_variable']
            structure_variables_list = combination_dict['structure_variables_list']
            graph_title = combination_dict['graph_title']
            extra_identifier = combination_dict['extra_identifier']
            data_title = ''
            energy_variable = 'Energy use'
            time_variable = 'Date'
            font_size=35
            INCLUDE_TEXT = True
            y_axis_min_percent_decrease=0
            residual_variable1=combination_dict['residual_variable1']
            emissions_divisia = combination_dict['emissions_divisia']
            hierarchical = combination_dict['hierarchical']
            output_data_folder=config.root_dir + '\\' + combination_dict['output_data_folder']
            plotting_output_folder=config.root_dir + '\\' + combination_dict['plotting_output_folder']

            # if not emissions_divisia:
            #     continue
            # elif not hierarchical:
            #     # print('plotting of hierarchical emissions divisia is not currently supported')
            #     continue#currently we cannto do hierarchical for emissions

            #check the folders exist:
            if not os.path.exists(output_data_folder):
                os.makedirs(output_data_folder)
            if not os.path.exists(plotting_output_folder):
                os.makedirs(plotting_output_folder)
            #run LMDI
            # if hierarchical:
            #     breakpoint()
        except Exception as e:
            if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                breakpoint()
                print(e)
        try:
            main_function.run_divisia(config, data_title, extra_identifier, activity_data, energy_data, structure_variables_list, activity_variable, emissions_variable = 'Emissions', energy_variable = energy_variable, emissions_divisia = emissions_divisia, emissions_data=emissions_data, time_variable=time_variable,hierarchical=hierarchical,output_data_folder=output_data_folder)
        except Exception as e:
            if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                breakpoint()
                print(e)
            
        try:
            if PLOT_EFFECT_OF_ELEC_EMISSIONS_FACTOR and emissions_divisia:
                extra_identifier2 = calculate_emissions_effect_from_additive_data(config, extra_identifier, output_data_folder, energy_use_by_fuels, all_data, combination_dict, PLOT_EMISSIONS_FACTORS=PLOT_EMISSIONS_FACTORS)
                extra_identifier2 = calculate_emissions_effect_from_multiplicative_data(config, extra_identifier, output_data_folder, energy_use_by_fuels, all_data, combination_dict)
                #now we can plot the additive and multiplicatve effecst of electricity emissions factor on the engine switching effect using the specially deisgiend INCLUDE_EXTRA_FACTORS_AT_END argument in the plotting functions
                #TODO
                if INCLUDE_LIFECYCLE_EMISSIONS:
                    attach_lifecycle_emissions_series(config, extra_identifier2, output_data_folder, combination_dict, stocks)  
            if USE_LIST_OF_CHARTS_TO_PRODUCE and combination_dict['extra_identifier'] not in charts_to_produce:
                continue
            if PLOTTING:
                #####################
                # if energy_variable == 'Energy use' and combination_dict['hierarchical'] == True and combination_dict['emissions_divisia'] == False and combination_dict['residual_variable1'] == 'Vehicle efficiency' and combination_dict['scenario'] == 'Target':
                #     breakpoint()
                # else:
                #     continue
                        
                #     print('plotting {}'.format(extra_identifier))
                #     print('energy_variable: {}'.format(energy_variable))
                #     print('emissions_divisia: {}'.format(emissions_divisia))
                #     print('hierarchical: {}'.format(hierarchical))
                #     print('residual_variable1: {}'.format(residual_variable1))
                    
                #     breakpoint()
                #     continue
                #####################
                try: 
                    if PLOT_EFFECT_OF_ELEC_EMISSIONS_FACTOR and emissions_divisia:
                        
                        # # if _Target_passenger_road then brakpoiint
                        # if '_Target_passenger_road' in extra_identifier2:
                        #     breakpoint()
                            
                        #use structure_variables_list_with_elec_emissions_factor sine we have added the effect of electricity emissions factor to it. Also use the data for extra_identifier2
                        
                        #create a dataset to be used for cumulative version of the addtive data as well
                        def save_copy_of_data_for_cumulative_version(extra_identifier, output_data_folder):
                            data = pd.read_csv(config.root_dir + '\\' +f'{output_data_folder}{extra_identifier}_additive.csv')
                            data.to_csv(config.root_dir + '\\' +f'{output_data_folder}{extra_identifier}_cumulative_additive.csv', index=False)
                            return extra_identifier+'_cumulative'
                        extra_identifier3 = save_copy_of_data_for_cumulative_version(extra_identifier2, output_data_folder)
                        try:
                            plot_output.plot_additive_waterfall(config, data_title, extra_identifier2, structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size, y_axis_min_percent_decrease=y_axis_min_percent_decrease,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical,output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder, INCLUDE_TEXT = INCLUDE_TEXT, INCLUDE_EXTRA_FACTORS_AT_END = True,PLOT_CUMULATIVE_VERSION = False)
                        except:
                            if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                                plot_output.plot_additive_waterfall(config, data_title, extra_identifier2, structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size, y_axis_min_percent_decrease=y_axis_min_percent_decrease,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical,output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder, INCLUDE_TEXT = INCLUDE_TEXT, INCLUDE_EXTRA_FACTORS_AT_END = True,PLOT_CUMULATIVE_VERSION = False)
                                breakpoint()
                            else:
                                pass
                        try:
                            plot_output.plot_additive_waterfall(config, data_title, extra_identifier3, structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size, y_axis_min_percent_decrease=y_axis_min_percent_decrease,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical,output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder, INCLUDE_TEXT = INCLUDE_TEXT, INCLUDE_EXTRA_FACTORS_AT_END = True,PLOT_CUMULATIVE_VERSION = True)
                        except:
                            if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                                breakpoint()
                                plot_output.plot_additive_waterfall(config, data_title, extra_identifier3, structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size, y_axis_min_percent_decrease=y_axis_min_percent_decrease,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical,output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder, INCLUDE_TEXT = INCLUDE_TEXT, INCLUDE_EXTRA_FACTORS_AT_END = True,PLOT_CUMULATIVE_VERSION = True)
                            else:
                                pass
                            
                        #and then plot the same data but with the original structure_variables_list and extra_identifier
                        #PLEASE NOTE THAT THE TIMESERIES VALUES DONT INCLUDE THE EFFECT OF THE ELECTRICITY EMISSIONS FACTOR OR THE LIFECYCLE EMISSIONS FACTOR IN THEIR 'TOTAL' VALUES SICNEIT WOULD BE MORE CONFUSING THAN HELPFUL
                        try:
                            plot_output.plot_multiplicative_timeseries(config, data_title, extra_identifier2,structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical, output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder, INCLUDE_EXTRA_FACTORS_AT_END = True)
                        except:
                            if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                                breakpoint()
                                plot_output.plot_multiplicative_timeseries(config, data_title, extra_identifier2,structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical, output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder, INCLUDE_EXTRA_FACTORS_AT_END = True)
                            else:
                                pass
                        try:
                            plot_output.plot_additive_timeseries(config, data_title, extra_identifier2,structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical, output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder, INCLUDE_EXTRA_FACTORS_AT_END = True)  
                        except:
                            if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                                breakpoint()
                                plot_output.plot_additive_timeseries(config, data_title, extra_identifier2,structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical, output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder, INCLUDE_EXTRA_FACTORS_AT_END = True)  
                            else:
                                pass
                    try:
                        plot_output.plot_additive_waterfall(config, data_title, extra_identifier, structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size, y_axis_min_percent_decrease=y_axis_min_percent_decrease,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical,output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder, INCLUDE_TEXT = INCLUDE_TEXT)
                    except:
                        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                            breakpoint()
                            plot_output.plot_additive_waterfall(config, data_title, extra_identifier, structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size, y_axis_min_percent_decrease=y_axis_min_percent_decrease,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical,output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder, INCLUDE_TEXT = INCLUDE_TEXT)
                        else:
                            pass
                    # if hierarchical:
                    #     breakpoint()  
                    try:
                        plot_output.plot_additive_timeseries(config, data_title, extra_identifier,structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical, output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder)
                    except:
                        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                            breakpoint()
                            plot_output.plot_additive_timeseries(config, data_title, extra_identifier,structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical, output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder)
                        else:
                            pass
                    try:
                        plot_output.plot_multiplicative_timeseries(config, data_title, extra_identifier,structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical, output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder)
                    except:
                        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                            breakpoint()
                            plot_output.plot_multiplicative_timeseries(config, data_title, extra_identifier,structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical, output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder)
                        else:
                            pass
                except:
                    # breakpoint()
                    print('error plotting {}'.format(extra_identifier))
                    continue
        except Exception as e:
            if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                print(e)
                breakpoint()
            else:
                pass
            
            if PLOT_EFFECT_OF_ELEC_EMISSIONS_FACTOR and emissions_divisia:
                extra_identifier2 = calculate_emissions_effect_from_additive_data(config, extra_identifier, output_data_folder, energy_use_by_fuels, all_data, combination_dict, PLOT_EMISSIONS_FACTORS=PLOT_EMISSIONS_FACTORS)
                extra_identifier2 = calculate_emissions_effect_from_multiplicative_data(config, extra_identifier, output_data_folder, energy_use_by_fuels, all_data, combination_dict)
                #now we can plot the additive and multiplicatve effecst of electricity emissions factor on the engine switching effect using the specially deisgiend INCLUDE_EXTRA_FACTORS_AT_END argument in the plotting functions
                #TODO
                if INCLUDE_LIFECYCLE_EMISSIONS:
                    attach_lifecycle_emissions_series(config, extra_identifier2, output_data_folder, combination_dict, stocks)  
            if USE_LIST_OF_CHARTS_TO_PRODUCE and combination_dict['extra_identifier'] not in charts_to_produce:
                continue
            if PLOTTING:
                #####################
                # if energy_variable == 'Energy use' and combination_dict['hierarchical'] == True and combination_dict['emissions_divisia'] == False and combination_dict['residual_variable1'] == 'Vehicle efficiency' and combination_dict['scenario'] == 'Target':
                #     breakpoint()
                # else:
                #     continue
                        
                #     print('plotting {}'.format(extra_identifier))
                #     print('energy_variable: {}'.format(energy_variable))
                #     print('emissions_divisia: {}'.format(emissions_divisia))
                #     print('hierarchical: {}'.format(hierarchical))
                #     print('residual_variable1: {}'.format(residual_variable1))
                    
                #     breakpoint()
                #     continue
                #####################
                try: 
                    if PLOT_EFFECT_OF_ELEC_EMISSIONS_FACTOR and emissions_divisia:
                        
                        # # if _Target_passenger_road then brakpoiint
                        # if '_Target_passenger_road' in extra_identifier2:
                        #     breakpoint()
                            
                        #use structure_variables_list_with_elec_emissions_factor sine we have added the effect of electricity emissions factor to it. Also use the data for extra_identifier2
                        
                        #create a dataset to be used for cumulative version of the addtive data as well
                        def save_copy_of_data_for_cumulative_version(extra_identifier, output_data_folder):
                            data = pd.read_csv(config.root_dir + '\\' +f'{output_data_folder}{extra_identifier}_additive.csv')
                            data.to_csv(config.root_dir + '\\' +f'{output_data_folder}{extra_identifier}_cumulative_additive.csv', index=False)
                            return extra_identifier+'_cumulative'
                        extra_identifier3 = save_copy_of_data_for_cumulative_version(extra_identifier2, output_data_folder)
                        try:
                            plot_output.plot_additive_waterfall(config, data_title, extra_identifier2, structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size, y_axis_min_percent_decrease=y_axis_min_percent_decrease,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical,output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder, INCLUDE_TEXT = INCLUDE_TEXT, INCLUDE_EXTRA_FACTORS_AT_END = True,PLOT_CUMULATIVE_VERSION = False)
                        except:
                            if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                                breakpoint()
                                plot_output.plot_additive_waterfall(config, data_title, extra_identifier2, structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size, y_axis_min_percent_decrease=y_axis_min_percent_decrease,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical,output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder, INCLUDE_TEXT = INCLUDE_TEXT, INCLUDE_EXTRA_FACTORS_AT_END = True,PLOT_CUMULATIVE_VERSION = False)
                            else:
                                print('error plotting {}'.format(extra_identifier))                                
                        try:
                            plot_output.plot_additive_waterfall(config, data_title, extra_identifier3, structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size, y_axis_min_percent_decrease=y_axis_min_percent_decrease,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical,output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder, INCLUDE_TEXT = INCLUDE_TEXT, INCLUDE_EXTRA_FACTORS_AT_END = True,PLOT_CUMULATIVE_VERSION = True)
                        except:
                            if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                                breakpoint()
                                plot_output.plot_additive_waterfall(config, data_title, extra_identifier3, structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size, y_axis_min_percent_decrease=y_axis_min_percent_decrease,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical,output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder, INCLUDE_TEXT = INCLUDE_TEXT, INCLUDE_EXTRA_FACTORS_AT_END = True,PLOT_CUMULATIVE_VERSION = True)
                            else:
                                print('error plotting {}'.format(extra_identifier))
                            
                        #and then plot the same data but with the original structure_variables_list and extra_identifier
                        #PLEASE NOTE THAT THE TIMESERIES VALUES DONT INCLUDE THE EFFECT OF THE ELECTRICITY EMISSIONS FACTOR OR THE LIFECYCLE EMISSIONS FACTOR IN THEIR 'TOTAL' VALUES SICNEIT WOULD BE MORE CONFUSING THAN HELPFUL
                        try:
                            plot_output.plot_multiplicative_timeseries(config, data_title, extra_identifier2,structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical, output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder, INCLUDE_EXTRA_FACTORS_AT_END = True)
                        except:
                            if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                                breakpoint()
                                plot_output.plot_multiplicative_timeseries(config, data_title, extra_identifier2,structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical, output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder, INCLUDE_EXTRA_FACTORS_AT_END = True)
                            else:
                                print('error plotting {}'.format(extra_identifier))
                        try:
                            plot_output.plot_additive_timeseries(config, data_title, extra_identifier2,structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical, output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder, INCLUDE_EXTRA_FACTORS_AT_END = True)  
                        except:
                            if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                                breakpoint()
                                plot_output.plot_additive_timeseries(config, data_title, extra_identifier2,structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical, output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder, INCLUDE_EXTRA_FACTORS_AT_END = True) 
                            else:
                                print('error plotting {}'.format(extra_identifier))
                    try:
                        plot_output.plot_additive_waterfall(config, data_title, extra_identifier, structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size, y_axis_min_percent_decrease=y_axis_min_percent_decrease,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical,output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder, INCLUDE_TEXT = INCLUDE_TEXT)
                    except:
                        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                            breakpoint()
                            plot_output.plot_additive_waterfall(config, data_title, extra_identifier, structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size, y_axis_min_percent_decrease=y_axis_min_percent_decrease,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical,output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder, INCLUDE_TEXT = INCLUDE_TEXT)
                        else:
                            print('error plotting {}'.format(extra_identifier))
                    # if hierarchical:
                    #     breakpoint()  
                    try:
                        plot_output.plot_additive_timeseries(config, data_title, extra_identifier,structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical, output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder)
                    except:
                        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                            breakpoint()
                            plot_output.plot_additive_timeseries(config, data_title, extra_identifier,structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical, output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder)
                        else:
                            print('error plotting {}'.format(extra_identifier))
                    try:
                        plot_output.plot_multiplicative_timeseries(config, data_title, extra_identifier,structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical, output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder)
                    except:
                        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                            plot_output.plot_multiplicative_timeseries(config, data_title, extra_identifier,structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical, output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder)
                            breakpoint()
                        else:
                            print('error plotting {}'.format(extra_identifier))
                except:
                    # breakpoint()
                    print('error plotting {}'.format(extra_identifier))
                    continue

    #now loop through unqiue keys in combined_transport_type_waterfall_inputs and plot them all together:
    
    for key in combined_transport_type_waterfall_inputs.keys():
        new_extra_identifier = key 
        if USE_LIST_OF_DATASETS_TO_PRODUCE and new_extra_identifier not in datasets_to_produce:
            continue
                    
        extra_identifiers = []
        structure_variables_list = []
        activity_variables = []
        new_activity_variable = 'passenger_and_freight_km'
        for combination_dict in combined_transport_type_waterfall_inputs[key]:
            extra_identifiers.append(combination_dict['extra_identifier'])
            structure_variables_list.append(combination_dict['structure_variables_list'])
            activity_variables.append(combination_dict['activity_variable'])
        if structure_variables_list[0] != structure_variables_list[1]:
            raise ValueError('structure variables are not the same for all combinations')
        else:
            structure_variables_list = structure_variables_list[0]#we only need one of these and they are all the same
        hierarchical = combination_dict['hierarchical']#will be the same for all
        emissions_divisia = combination_dict['emissions_divisia']#will be the same for all
        residual_variable1 = combination_dict['residual_variable1']#will be the same for all
        scenario = combination_dict['scenario']#will be the same for all
        economy = combination_dict['economy']
        plotting_output_folder = combination_dict['plotting_output_folder']
        output_data_folder = combination_dict['output_data_folder']
        
        graph_title = combination_dict['graph_title']#will be the same for all
        #temp, find where things are going wrong:
        #concat the data
        # if emissions_divisia:#I THINK ITS OK NOW
        # if hierarchical:
        #     print('plotting of hierarchical emissions divisia is not currently supported')
        #     continue#currently we cannto do hierarchical for emissions

                
        plot_output.concat_waterfall_inputs(config, data_title, new_extra_identifier, extra_identifiers,activity_variables, new_activity_variable, time_variable='Date', hierarchical=hierarchical, output_data_folder=output_data_folder)
        
        new_extra_identifier2 = new_extra_identifier+'_concatenated'
        if USE_LIST_OF_CHARTS_TO_PRODUCE and new_extra_identifier not in charts_to_produce:
            continue
        try:
            plot_output.plot_additive_waterfall(config, data_title, new_extra_identifier2, structure_variables_list=structure_variables_list,activity_variable=new_activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size, y_axis_min_percent_decrease=y_axis_min_percent_decrease,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical,output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder,INCLUDE_TEXT = INCLUDE_TEXT)#in the output we just added _concatenated to the end of the extra identifier, berfore additive, so we need to update it hereas the additive plotting function will not look for this
        
        except:
            if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                breakpoint()
                plot_output.plot_additive_waterfall(config, data_title, new_extra_identifier2, structure_variables_list=structure_variables_list,activity_variable=new_activity_variable,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size, y_axis_min_percent_decrease=y_axis_min_percent_decrease,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical,output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder,INCLUDE_TEXT = INCLUDE_TEXT)#in the output we just added _concatenated to the end of the extra identifier, berfore additive, so we need to update it hereas the additive plotting function will not look for this
            print('error plotting {}'.format(extra_identifier))
            continue
        
        #add the plot to combined_scenario_waterfall_inputs so we can plot them all together later
        extra_identifier_no_transport_type_no_scenario = new_extra_identifier.replace(f'{scenario}_', '')
        if extra_identifier_no_transport_type_no_scenario not in combined_scenario_waterfall_inputs.keys():
            combined_scenario_waterfall_inputs[extra_identifier_no_transport_type_no_scenario] = [{'economy':economy, 'activity_variable':new_activity_variable, 'structure_variables_list':structure_variables_list, 'graph_title':graph_title, 'extra_identifier':new_extra_identifier, #make sure to use the extra identifier without the transport type in it
            'emissions_divisia':emissions_divisia, 'hierarchical':hierarchical, 'residual_variable1':residual_variable1,'plotting_output_folder':plotting_output_folder, 'output_data_folder':output_data_folder}]
        else:
            combined_scenario_waterfall_inputs[extra_identifier_no_transport_type_no_scenario].append({'economy':economy, 'activity_variable':new_activity_variable, 'structure_variables_list':structure_variables_list, 'graph_title':graph_title, 'extra_identifier':new_extra_identifier, #make sure to use the extra identifier without the transport type in it
            'emissions_divisia':emissions_divisia, 'hierarchical':hierarchical, 'residual_variable1':residual_variable1,'plotting_output_folder':plotting_output_folder, 'output_data_folder':output_data_folder})

    #now loop through unqiue keys in combined_scenario_waterfall_inputs and plot them all together:
    try:
        for key in combined_scenario_waterfall_inputs.keys():
            new_extra_identifier = key
            
            if USE_LIST_OF_CHARTS_TO_PRODUCE and new_extra_identifier not in charts_to_produce:
                continue
            
            extra_identifiers = []
            structure_variables_list = []
            activity_variables = []
            graph_titles= []
            for combination_dict in combined_scenario_waterfall_inputs[key]:
                extra_identifiers.append(combination_dict['extra_identifier'])
                structure_variables_list.append(combination_dict['structure_variables_list'])
                activity_variables.append(combination_dict['activity_variable'])
                graph_titles.append(combination_dict['graph_title'])
            if structure_variables_list[0] != structure_variables_list[1]:
                if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
                    breakpoint()
                    print('structure variables are not the same for all combinations')
            else:
                structure_variables_list = structure_variables_list[0]#we only need one of these and they are all the same
            hierarchical = combination_dict['hierarchical']#will be the same for all
            economy = combination_dict['economy']
            emissions_divisia = combination_dict['emissions_divisia']
            residual_variable1 = combination_dict['residual_variable1']
            plotting_output_folder = combination_dict['plotting_output_folder']
            output_data_folder = combination_dict['output_data_folder']
            
            # if hierarchical:
            #     continue#not sure about summing up multiplicative effects
            
            #plot the data
            try:
                plot_output.plot_combined_waterfalls(config, data_title,graph_titles,extra_identifiers, new_extra_identifier, structure_variables_list, activity_variables,energy_variable='Energy use', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size, y_axis_min_percent_decrease=y_axis_min_percent_decrease,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical,output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder,INCLUDE_TEXT = INCLUDE_TEXT)
            except:
                # breakpoint()
                print('error plotting {}'.format(extra_identifier))
                continue
    except:
        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
            breakpoint()
        else:
            pass


def calculate_emissions(config, energy_use_by_fuels, all_data, USE_AVG_GENERATION_EMISSIONS_FACTOR=False, drive_column='Drive', energy_column = 'Energy use', PLOT_EMISSIONS_FACTORS=False):
    """take in energy_use_by_fuels and all_data, calcaulte emissions in energy_use_by_fuels and then merge them back into all_data, since all data didnt have energy use by fuel, so it wasnt possible to calculate emissions in all_data

    Args:
        energy_use_by_fuels (_type_): _description_
        all_data (_type_): _description_
        USE_AVG_GENERATION_EMISSIONS_FACTOR (bool, optional): _description_. Defaults to False.

    Raises:
        ValueError: _description_
    """
    
    emissions_factors = pd.read_csv(config.root_dir + '\\' + 'config\\9th_edition_emissions_factors.csv')
    if drive_column != 'Drive':
        energy_use_by_fuels = energy_use_by_fuels.rename(columns={'Drive':drive_column})
    if energy_column != 'Energy':
        energy_use_by_fuels = energy_use_by_fuels.rename(columns={'Energy':energy_column})
        
    #load in data and recreate plot, as created in all_economy_graphs
    #loop through scenarios and grab the data for each scenario:
    energy_use_by_fuels = energy_use_by_fuels[['Economy', 'Scenario','Date', 'Fuel', 'Transport Type','Vehicle Type',drive_column,'Medium',energy_column]].groupby(['Economy', 'Scenario','Date','Transport Type','Vehicle Type',drive_column,'Medium', 'Fuel']).sum().reset_index().copy()
    
    #rename fuel_code to fuel in emissions_factors
    emissions_factors = emissions_factors.rename(columns={'fuel_code':'Fuel'})
    #join on the emissions factors (has the cols fuel_code,	Emissions factor (MT/PJ))
    energy_use_by_fuels = energy_use_by_fuels.merge(emissions_factors, how='left', on='Fuel')
    
    if USE_AVG_GENERATION_EMISSIONS_FACTOR:
        #pull in the 8th outlook emissions factors by year then use that to claculate the emissions for electricity.
        emissions_factor_elec = pd.read_csv(config.root_dir + '\\' + 'input_data\\from_8th\\outlook_8th_emissions_factors_with_electricity.csv')#c:\Users\finbar.maunsell\github\aperc-emissions\output_data\outlook_8th_emissions_factors_with_electricity.csv
        #extract the emissions factor for elctricity for each economy
        emissions_factor_elec = emissions_factor_elec[emissions_factor_elec.fuel_code=='17_electricity'].copy()
        #rename Carbon Neutral Scenario to Target
        emissions_factor_elec['Scenario'] = emissions_factor_elec['Scenario'].replace('Carbon Neutral', 'Target')
        #capitalise the cols
        emissions_factor_elec.columns = [x.capitalize() for x in emissions_factor_elec.columns]
        #rename fuel code to fuel
        emissions_factor_elec = emissions_factor_elec.rename(columns={'Fuel_code':'Fuel', 'Year':'Date', 'Emissions factor (mt/pj)':'Emissions factor (MT/PJ)'})
        
        #merge on economy and year and fuel code
        energy_use_by_fuels = energy_use_by_fuels.merge(emissions_factor_elec, on=['Date', 'Economy', 'Scenario', 'Fuel'], how='left', indicator=True, suffixes=('', '_elec'))
        #where indicator is both, use the new value
        energy_use_by_fuels['Emissions factor (MT/PJ)'] = np.where(energy_use_by_fuels['_merge']=='both', energy_use_by_fuels['Emissions factor (MT/PJ)_elec'], energy_use_by_fuels['Emissions factor (MT/PJ)'])
        
        #fill any missing values using ffill after sorting by date and grouping by 'Economy', 'Scenario','Date', 'Fuel', 'Transport Type'
        energy_use_by_fuels['Emissions factor (MT/PJ)'] = energy_use_by_fuels.sort_values(by='Date').groupby(['Economy', 'Scenario','Date', 'Fuel','Transport Type','Vehicle Type',drive_column,'Medium'])['Emissions factor (MT/PJ)'].fillna(method='ffill')
        
        #drop columns
        energy_use_by_fuels = energy_use_by_fuels.drop(columns=['Emissions factor (MT/PJ)_elec', '_merge'])
        
    #identify where there are no emissions factors:
    missing_emissions_factors = energy_use_by_fuels.loc[energy_use_by_fuels['Emissions factor (MT/PJ)'].isna()].copy()
    if len(missing_emissions_factors)>0:
        breakpoint()
        time.sleep(1)
        raise ValueError(f'missing emissions factors, {missing_emissions_factors.Fuel.unique()}')
    
    #calculate emissions:
    energy_use_by_fuels['Emissions'] = energy_use_by_fuels[energy_column] * energy_use_by_fuels['Emissions factor (MT/PJ)']
    #extract the emissions factor so we can also use that in the lifecycle emissions graphs
    
    emissions_factors = energy_use_by_fuels.loc[(energy_use_by_fuels['Emissions factor (MT/PJ)']>0)][['Economy','Date','Fuel','Emissions factor (MT/PJ)']].drop_duplicates().copy()
    #extract the electricity emissions to use them separately if need be:
    electricity_emissions = energy_use_by_fuels[energy_use_by_fuels.Fuel=='17_electricity'].copy()
    #drop fuels and then sum
    energy_use_by_fuels = energy_use_by_fuels.drop(columns=['Fuel', 'Emissions factor (MT/PJ)']).groupby(['Economy', 'Scenario','Date', 'Transport Type','Vehicle Type',drive_column,'Medium']).sum().reset_index()
    electricity_emissions = electricity_emissions.drop(columns=['Fuel', 'Emissions factor (MT/PJ)']).groupby(['Economy', 'Scenario','Date', 'Transport Type','Vehicle Type',drive_column,'Medium']).sum().reset_index()
    #now merge emissions back into all_data
    all_data = all_data.merge(energy_use_by_fuels[['Economy', 'Scenario','Date', 'Transport Type','Vehicle Type',drive_column,'Medium','Emissions']], how='left', on=['Economy', 'Scenario','Date', 'Vehicle Type',drive_column,'Medium', 'Transport Type'])
    
    if PLOT_EMISSIONS_FACTORS:
        #RENAME fuels from 07_01_motor_gasoline to petrol and 17_electricity to electricity
        emissions_factors = emissions_factors.replace({'Fuel':{'07_01_motor_gasoline':'petrol', '17_electricity':'electricity'}})
        plot_lifecycle_emissions(config, emissions_factors, fuels_to_plot=['petrol', 'electricity'])
    return all_data, electricity_emissions

def prepare_data_for_divisia(config, combination_dict, all_data, END_DATE):
    data = all_data.copy()
    #filter data by scenario
    data = data[data['Scenario']==combination_dict['scenario']]
    #filter data by economy
    data = data[data['Economy']==combination_dict['economy']]
    #filter data by transport type
    data = data[data['Transport Type']==combination_dict['transport_type']]
    #filter data by medium
    if combination_dict['medium'] == 'road':
        data = data[data['Medium']==combination_dict['medium']]
    else:
        pass
    #filter data by end date
    data = data[data['Date']<=END_DATE]
    structure_variables_list = combination_dict['structure_variables_list']
    #sum the data
    data = data.groupby(['Date']+structure_variables_list).sum(numeric_only=True).reset_index()

    #Separate energy and activity data
    energy_data = data[['Date','Energy use']+structure_variables_list]
    activity_data = data[['Date', 'Activity']+structure_variables_list]
    emissions_data = data[['Date',  'Emissions']+structure_variables_list]
    #rename activity with variable
    activity_data = activity_data.rename(columns={'Activity':combination_dict['activity_variable']})
    return activity_data, energy_data, emissions_data

def calculate_emissions_effect_from_additive_data(config, extra_identifier, output_data_folder, energy_use_by_fuels, all_data, combination_dict, PLOT_EMISSIONS_FACTORS):
    #we want to serparate the effect of electricity emissions from the engine switching effect. To do this we will run the LMDI again but this time we will use the emissions factor for electricity from the 8th outlook. We will then subtract the effect of the electricity emissions from the engine switching effect to get the effect of engine switching on non-electricity emissions. Then include a new structure_variable in structure_variables_list which is the electricity emissions factor. This will be used to calculate the effect of engine switching on electricity emissions. Note that this is quite a crude way of doing this as it assumes that the effect of the electricity emissions factor is entriely within the engine switching effect. This is not true, as you will get a slight amount of reduction in emissions from other effects (for example making evs more efficient), but it is the best we can do with the time we have...
    #run again but with USE_AVG_GENERATION_EMISSIONS_FACTOR = True
    
    #OR alternatively we could jsut calcualte the emissions from electricity in that transport type/medium and set that as an extra bar, maybe yellow colored after everything. then it will 'seem' more separate to the drivers, seem more simple and not invovling potentially wrong calcs and yet still show the same thing!
    
    all_data_generation_emissions, electricity_emissions = calculate_emissions(config, energy_use_by_fuels, all_data.drop(columns=['Emissions']), USE_AVG_GENERATION_EMISSIONS_FACTOR=True, drive_column='Engine switching', energy_column = 'Energy use',PLOT_EMISSIONS_FACTORS=PLOT_EMISSIONS_FACTORS)
    extra_identifier2 = extra_identifier+'_generation_emissions'
    # activity_data_gen, energy_data_gen, emissions_data_gen = prepare_data_for_divisia(config, combination_dict, all_data_generation_emissions, END_DATE)
    # main_function.run_divisia(config, data_title, extra_identifier2, activity_data_gen, energy_data_gen, structure_variables_list, activity_variable, emissions_variable = 'Emissions', energy_variable = energy_variable, emissions_divisia = emissions_divisia, emissions_data=emissions_data_gen, time_variable=time_variable,hierarchical=hierarchical,output_data_folder=output_data_folder)
    #load in the additive effect data and find the effect of electricity emissions on engine switching:
    # data_generation_emissions = pd.read_csv(f'{output_data_folder}{extra_identifier2}_additive.csv')
    data = pd.read_csv(config.root_dir + '\\' +f'{output_data_folder}{extra_identifier}_additive.csv')
    #keep only the date column and emissions column, also filter for transport type, medium from combination_dict
    electricity_emissions = electricity_emissions[(electricity_emissions['Transport Type']==combination_dict['transport_type']) & (electricity_emissions['Scenario']==combination_dict['scenario'])]
    if combination_dict['medium'] == 'road':
        electricity_emissions = electricity_emissions[electricity_emissions['Medium']==combination_dict['medium']]
    electricity_emissions = electricity_emissions[['Date', 'Emissions']].groupby(['Date']).sum().reset_index()
    #find the difference in all the effects, add them together andcreate a new column in the original data, after the activity effect valled 'Effect of electricity emissions factor'
    #rename the Emissions column to 'Effect of electricity emissions'
    electricity_emissions = electricity_emissions.rename(columns={'Emissions':'Effect of electricity emissions'})
    data = data.merge(electricity_emissions, on='Date')
    
    data.to_csv(config.root_dir + '\\' +f'{output_data_folder}{extra_identifier2}_additive.csv', index=False)
    
    return extra_identifier2
    
def attach_lifecycle_emissions_series(config, extra_identifier2, output_data_folder, combination_dict, stocks):
    
    #to help make the graph even more informative, we will add a series that represents the lifecyle emissions from purchasing ice and ev cars. This way the user can observe the difference in emissions when there are lots of evs vs not many purchased.
    #load in the lifecycle emissions data that was gatehred from multiple soruces and then averaged
    lca = pd.read_excel(config.root_dir + '\\' +'input_data\\lifecycle_emissions.xlsx')
    #drop where READY_TO_USE is not True
    lca = lca[lca['READY_TO_USE']==True]
    #grab the cols we need and average them out (we will exclude the cols on use phase emissions for now)
    # cols:
    # vehicle type,	category,	drive,	study, source,	materials production and refining,	battery production,	car manufacturing,	use phase emissions,	end of life,	other,	READY_TO_USE
    #set cols that are na to 0
    lca = lca.fillna(0)
    #make sure that all the numeric cols are numeric
    numeric_cols = ['materials production and refining', 'battery production', 'car manufacturing', 'end of life', 'other']
    if not all([lca[col].dtype == 'float64' for col in numeric_cols]):
        for col in numeric_cols:
            lca[col] = lca[col].astype('float64')
    plot_lca_bars(config, lca, numeric_cols=numeric_cols, SIMPLE=False)
    
    #add the values across their respective columns to get the lifecycle emissions
    lca['non-use lifecycle emissions'] = lca['materials production and refining'] + lca['battery production'] + lca['car manufacturing'] + lca['end of life'] + lca['other']
    lca = lca[['vehicle type', 'drive', 'non-use lifecycle emissions', 'source']]
    #average them out but make sure to do it by study source too at first so that step cahnges between studies where some studies may have mroe data on bevs or ice cars than others dont affet the average too much
    lca = lca.groupby(['vehicle type', 'drive', 'source']).mean(numeric_only=True).reset_index()
    plot_lca_bars(config, lca, numeric_cols=[], SIMPLE=True)
    
    #now average them out by vehicle type and drive
    lca = lca.groupby(['vehicle type', 'drive']).mean(numeric_only=True).reset_index()
    #if vehicle type is only car then drop it and mean all
    if len(lca['vehicle type'].unique()) == 1:
        lca = lca.groupby(['drive']).mean(numeric_only=True).reset_index()
    else:
        raise ValueError('lca has more than 1 vehicle type, not expected')
    #now times this by the nubmer of new stocks of cars in each year to get the lifecycle emissions
    #grab the stocks of new cars for this transport type,medium and scenario
    stocks =  stocks[(stocks['Transport Type']==combination_dict['transport_type']) & (stocks['Scenario']==combination_dict['scenario'])]
    if combination_dict['medium'] == 'road':
        stocks = stocks[stocks['Medium']==combination_dict['medium']]
        
    #add 'Stock_turnover' to stocks and then calculate the sales of cars each year as the difference in stocks 
    #first lag stockturnover by 1 year so the turnover from the current year is applied to the previous year. need to sort by date and group by drive first
    # breakpoint()
    stocks = stocks.sort_values(by=['Drive', 'Date', 'Vehicle Type'])
    # stocks['Stock_turnover_lagged'] = stocks.groupby(['Drive', 'Vehicle Type'])['Stock_turnover'].shift(-1)    
    stocks = stocks[['Date', 'Drive', 'New_stocks_needed']].groupby(['Date', 'Drive']).sum().reset_index()
    # stocks['Stocks'] = stocks['Stocks'] + stocks['Stock_turnover']
    # breakpoint()
    # stocks = stocks[['Date', 'Drive', 'Stocks']].groupby(['Date', 'Drive']).sum().reset_index()
    
    #calcualte change in stocks each year, after sorting by date and grouping by drive
    # stocks = stocks.sort_values(by='Date')
    # stocks['Sales'] = stocks.groupby('Drive')['Stocks'].diff()
    # #add Stock_turnover to sales
    # stocks['Sales'] = stocks['Sales'] + stocks['Stock_turnover']
    # #drop stock turnover
    # stocks = stocks.drop(columns=['Stock_turnover'])
    #in stocks, if bev and ice_g are the only drives in lca, then where drive is not bev set it to ice_g
    if len(lca['drive'].unique()) == 2:
        if 'bev' in lca['drive'].unique() and 'ice_g' in lca['drive'].unique():
            stocks.loc[stocks['Drive']!='bev', 'Drive'] = 'ice_g'
    else:
        raise ValueError('lca has more than 2 drives, not expected')
    #rename drive to Drive
    lca = lca.rename(columns={'drive':'Drive', 'non-use lifecycle emissions':'lifecycle emissions'})
    #merge the stocks and lca data
    lca = lca.merge(stocks, on=['Drive'], how='left')
    #times the lifecycle emissions by the saels
    
    lca['lifecycle emissions'] = lca['lifecycle emissions'] * lca['New_stocks_needed']
    #sumby date and drop everythin by date and lifecycle emissions
    lca = lca.groupby(['Date', 'Drive']).sum().reset_index()
    #pivot so we have a column for each drive for 'lifecycle emissions'
    lca_wide = lca.pivot(index='Date', columns='Drive', values='lifecycle emissions').reset_index()
    #add Effect of lifecycle emissions to the start of the non date column names
    lca_wide.columns = ['Date'] + [f'Effect of lifecycle emissions {col}' for col in lca_wide.columns if col != 'Date']
    
    #add this to the data                            
    data_mult = pd.read_csv(config.root_dir + '\\' +f'{output_data_folder}{extra_identifier2}_multiplicative.csv')
    data_add = pd.read_csv(config.root_dir + '\\' +f'{output_data_folder}{extra_identifier2}_additive.csv')
    
    # add the lifecycle emissions to the data. convert to mult for data_mult and add for data_add
    data_mult = pd.merge(data_mult, lca_wide, on='Date', how='left')
    data_add = pd.merge(data_add, lca_wide, on='Date', how='left')
    #calcualte the multiplacite effect of this new effect: it is the (total emissions  for that year, + the effect of  lifecycle emissions factor) divided by the total emissions for that year
    
    for col in [col for col in data_mult.columns if 'Effect of lifecycle emissions' in col]:
        data_mult[col] = (data_mult['Total Emissions']+data_mult[col])/data_mult['Total Emissions']
    #save back to csv
    data_mult.to_csv(config.root_dir + '\\' +f'{output_data_folder}{extra_identifier2}_multiplicative.csv', index=False)
    data_add.to_csv(config.root_dir + '\\' +f'{output_data_folder}{extra_identifier2}_additive.csv', index=False)


def plot_lca_bars(config, lca, numeric_cols=[], SIMPLE=True):
    if SIMPLE:
        #create a bar graph to shjow the 'source' as a different color for each bar, and then each unique drive as a differet set. make sure to color ice as purple and bev as green
        fig = px.bar(lca, x='drive', y='non-use lifecycle emissions', color='source', barmode='group', color_discrete_map={'bev':'green', 'ice_g':'purple'})
        #make text bigger
        fig.update_layout(font_size=35)
        fig.write_html(config.root_dir + '\\' + f'plotting_output\\lifecycle_emissions\\lifecycle_emissions_by_source_SIMPLE.html')
        
        
        lca = lca.drop(columns=['source'])
        lca = lca.groupby(['drive']).mean(numeric_only=True).reset_index()
        
        fig = px.bar(lca, x='drive', y='non-use lifecycle emissions', color='drive', barmode='group', color_discrete_map={'bev':'green', 'ice_g':'purple'})
        #make text bigger
        fig.update_layout(font_size=35)
        fig.write_html(config.root_dir + '\\' +f'plotting_output\\lifecycle_emissions\\lifecycle_emissions_SIMPLE.html')

    else:
        #make the value cols into one col
        lca_melt = lca.melt(id_vars=['vehicle type', 'drive', 'source'], value_vars=numeric_cols, var_name='lifecycle stage', value_name='non-use lifecycle emissions')
        
        lca_melt = lca_melt.groupby(['vehicle type', 'drive', 'source', 'lifecycle stage']).sum().reset_index()
        
        fig = px.bar(lca_melt, x='lifecycle stage', y='non-use lifecycle emissions', color='source', barmode='group', color_discrete_map={'bev':'green', 'ice_g':'purple'}, title='Lifecycle emissions by source', facet_col='drive')
        
        #make text bigger
        fig.update_layout(font_size=35)
        fig.write_html(config.root_dir + '\\' +f'plotting_output\\lifecycle_emissions\\lifecycle_emissions_by_source_FACETED.html')  


def plot_lifecycle_emissions(config, emissions_factors, fuels_to_plot):
    
    # Keep only the fuels in fuels_to_plot
    emissions_factors_filtered = emissions_factors[emissions_factors['Fuel'].isin(fuels_to_plot)]
    economy = emissions_factors_filtered['Economy'].unique()[0]
    # Aggregate emissions factors by 'fuel' and 'Date', if necessary
    emissions_factors_filtered = emissions_factors_filtered.groupby(['Date', 'Fuel']).mean(numeric_only=True).reset_index()
    
    # Define color mapping (optional, px.line will automatically assign colors if not used)
    color_discrete_map = {'electricity': 'green', 'gasoline': 'purple'}
    for drive in fuels_to_plot:
        color_discrete_map[drive] = 'black'

    # Create the line chart using px.line
    fig = px.line(emissions_factors_filtered, x='Date', y='Emissions factor (MT/PJ)', color='Fuel',
                  color_discrete_map=color_discrete_map, 
                  labels={'Emissions factor (MT/PJ)': 'Emissions Factor'}, 
                  title=f'Emissions factor by Fuel - {economy}')

    # Update layout if needed (e.g., making text bigger)
    fig.update_layout(font_size=35)

    fig.write_html(config.root_dir + '\\' +f'plotting_output\\lifecycle_emissions\\{economy}_lifecycle_emissions_LINE.html')

def calculate_emissions_effect_from_multiplicative_data(config, extra_identifier, output_data_folder, energy_use_by_fuels, all_data, combination_dict):
    """please note that because emissions for passenger transport will likely go to 0, the multiplicative effect of the electricity emissions will be very high, making the graph look ugly.

    Args:
        data_title (_type_): _description_
        extra_identifier (_type_): _description_
        structure_variables_list (_type_): _description_
        activity_variable (_type_): _description_
        energy_variable (_type_): _description_
        emissions_divisia (_type_): _description_
        time_variable (_type_): _description_
        hierarchical (_type_): _description_
        output_data_folder (_type_): _description_
        energy_use_by_fuels (_type_): _description_
        all_data (_type_): _description_
        combination_dict (_type_): _description_
        END_DATE (_type_): _description_

    Returns:
        _type_: _description_
    """
    #we want to serparate the effect of electricity emissions from the engine switching effect. To do this we will run the LMDI again but this time we will use the emissions factor for electricity from the 8th outlook. We will then subtract the effect of the electricity emissions from the engine switching effect to get the effect of engine switching on non-electricity emissions. Then include a new structure_variable in structure_variables_list which is the electricity emissions factor. This will be used to calculate the effect of engine switching on electricity emissions. Note that this is quite a crude way of doing this as it assumes that the effect of the electricity emissions factor is entriely within the engine switching effect. This is not true, as you will get a slight amount of reduction in emissions from other effects (for example making evs more efficient), but it is the best we can do with the time we have...
    #run again but with USE_AVG_GENERATION_EMISSIONS_FACTOR = True
    #OR alternatively we could jsut calcualte the emissions from electricity in that transport type/medium and set that as an extra bar, maybe yellow colored after everything. then it will 'seem' more separate to the drivers, seem more simple and not invovling potentially wrong calcs and yet still show the same thing! 
    
    all_data_generation_emissions, electricity_emissions = calculate_emissions(config, energy_use_by_fuels, all_data.drop(columns=['Emissions']), USE_AVG_GENERATION_EMISSIONS_FACTOR=True, drive_column='Engine switching', energy_column = 'Energy use')
    extra_identifier2 = extra_identifier+'_generation_emissions'
    
    data = pd.read_csv(f'{output_data_folder}{extra_identifier}_multiplicative.csv')
    #keep only the date column and emissions column, also filter for transport type, medium, scneaio from combination_dict
    electricity_emissions =  electricity_emissions[(electricity_emissions['Transport Type']==combination_dict['transport_type']) & (electricity_emissions['Scenario']==combination_dict['scenario'])]
    if combination_dict['medium'] == 'road':
        electricity_emissions = electricity_emissions[electricity_emissions['Medium']==combination_dict['medium']]
    electricity_emissions = electricity_emissions[['Date', 'Emissions']].groupby(['Date']).sum().reset_index()
    #find the difference in all the effects, add them together andcreate a new column in the original data, after the activity effect valled 'Effect of electricity emissions factor'
    #rename the Emissions column to 'Effect of electricity emissions'
    electricity_emissions = electricity_emissions.rename(columns={'Emissions':'Effect of electricity emissions'})
    data = data.merge(electricity_emissions, on=['Date'])
    
    #calcualte the multiplacite effect of this new effect: it is the (total emissions  for that year, + the effect of electricity emissions factor) divided by the total emissions for that year
    data['Effect of electricity emissions'] = (data['Total Emissions']+data['Effect of electricity emissions'])/data['Total Emissions']
    data.to_csv(config.root_dir + '\\' +f'{output_data_folder}{extra_identifier2}_multiplicative.csv', index=False)
    
    return extra_identifier2

#%%
# produce_lots_of_LMDI_charts(config, '03_CDA', USE_LIST_OF_CHARTS_TO_PRODUCE = True, PLOTTING = True, USE_LIST_OF_DATASETS_TO_PRODUCE=True, END_DATE=2050, PLOT_EFFECT_OF_ELEC_EMISSIONS_FACTOR=True, INCLUDE_LIFECYCLE_EMISSIONS=False)

# produce_lots_of_LMDI_charts(config, '07_INA', USE_LIST_OF_CHARTS_TO_PRODUCE = True, PLOTTING = True, USE_LIST_OF_DATASETS_TO_PRODUCE=True, END_DATE=2050, PLOT_EFFECT_OF_ELEC_EMISSIONS_FACTOR=True, INCLUDE_LIFECYCLE_EMISSIONS=False)
# produce_lots_of_LMDI_charts(config, '05_PRC', USE_LIST_OF_CHARTS_TO_PRODUCE = False, PLOTTING = True, USE_LIST_OF_DATASETS_TO_PRODUCE=False, END_DATE=2050, PLOT_EFFECT_OF_ELEC_EMISSIONS_FACTOR=True, INCLUDE_LIFECYCLE_EMISSIONS=False)
# ECONOMY_ID = '01_AUS'
# produce_lots_of_LMDI_charts(config, ECONOMY_ID, USE_LIST_OF_CHARTS_TO_PRODUCE = True, PLOTTING = True, USE_LIST_OF_DATASETS_TO_PRODUCE=True, END_DATE=2070)

# produce_lots_of_LMDI_charts(config, ECONOMY_ID, USE_LIST_OF_CHARTS_TO_PRODUCE = True, PLOTTING = True, USE_LIST_OF_DATASETS_TO_PRODUCE=False, END_DATE=2050)
# produce_lots_of_LMDI_charts(config, ECONOMY_ID, USE_LIST_OF_CHARTS_TO_PRODUCE = True, PLOTTING = True, USE_LIST_OF_DATASETS_TO_PRODUCE=False, END_DATE=2070)
#%%

