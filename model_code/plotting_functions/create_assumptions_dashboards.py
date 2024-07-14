#%%
#craete an assumptions dashboard in plotly which will display the most important data for the user to see.
# To simplify things, we will keep this to road data only. Our non road dta is too reliant on intensity from egeda right now, which is probably wrong.
# The most important data will probably be: drive shares by transport type (2 graphs), eneryg use by vehicle type, fuel type (1 line graph), freight tone km by drive, passenger km by drive, activity growth?

#PLEASE NOTE THAT THIS NEEDS TO BE RUN AFTER THE all_economy_graphs.py and create_sales_share_data.py scripts, as that script creates the data that this script uses to create the dashboard

###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
from .. import utility_functions
from . import assumptions_dashboard_plotting_scripts
#################

import kaleido
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
import copy
import math
DROP_NON_ROAD_TRANSPORT = False

#print every unique name/labels used in the plots and match it to a color. the colors will be themed so that things like electricity and bev's are always the same color
#following done with this chatgpt:https://chat.openai.com/share/d39fec42-e2b2-497a-8826-30a59bd09940
colors_dict = {
    # Electric vehicles and related items (blue shades)
    'bev': '#1488c6',  # aperc blue
    #passenger types
    'bev 2w': '#10326a',  # dark blue
    'bev lpv': '#1ca3db',  # light blue
    'bev bus': '#05519b',  # medium blue
    'bev passenger': '#1ecfed',  # light blue
    
    #freight types
    'bev lcv': '#022546',  # darkest blue
    'bev trucks': '#05429b',  # #quite dark blue
    'bev freight': '#10326a',  # dark blue

    #phevs (yellow)
    'phev': '#E8ce15',  # dark yellow
    'phev_g': '#E8ce15',  # dark yellow
    'phev_d': '#C7e815',  # greeny yellow
    'phev passenger': '#E8ce15',  # dark yellow
    'phev freight': '#C7e815',  # greeny yellow
    
    #other:
    '17_electricity': '#05519b',  # blue

    'Fast chargers (200kW)': '#10326a',  # aperc dark blue
    'Slow chargers (60kW)': '#1494cc',  # aperc light blue
    
    #GAS
    'gas': '#7d2472',  # plum
    '07_09_lpg': '#E4a0dc',  # lightorchid
    '08_01_natural_gas': '#7d2472',  # plum

    # Oil vehicles and related items (red shades)
    'ice': '#FF0000',  # red
    'ice_d': '#B22222',  # firebrick
    'ice_g': '#CD5C5C',  # indianred
    'diesel': '#B22222',  # firebrick
    'gasoline': '#FF0000',  # red

    '07_01_motor_gasoline': '#B22222',  # firebrick
    '07_07_gas_diesel_oil': '#CD5C5C',  # indianred

    # Fuel cell vehicles and related items (purple shades)
    'fcev': '#800080',  # purple
    #passenger types
    'fcev bus': '#DA70D6',  # orchid
    'fcev lpv': '#9932CC',  # darkorchid
    'fcev passenger': '#BA55D3',  # mediumorchid
    #fregith types
    'fcev trucks': '#EE82EE',  # violet
    'fcev lcv': '#9400D3',  # darkviolet
    'fcev freight': '#8A2BE2',  # darkviolet

    '16_x_hydrogen': '#BA55D3',  # mediumorchid
    '16_x_efuel' : '#D615e8',  # Electric Violet
    '16_x_ammonia': '#8A2BE2',  # darkviolet
    'hydrogens_efuels': '#BA55D3',  # mediumorchid
    
    # Biofuels (orange shades)
    '16_06_biodiesel': '#7cd886',  #  Pastel Green
    '16_05_biogasoline': '#0bea23',  # Malachite
    '16_07_bio_jet_kerosene': '#8d9b05',  # ochre
    'biofuels': '#7cd886',  #  Pastel Green
    
    # Unique fuel types, non-road vehicles and related items (cyan shades)
    '01_x_coal_thermal': '#000000',  # black
    '07_08_fuel_oil': '#774a0b',  # dark orange
    '07_02_aviation_gasoline': '#FFFF00',  # darkyellow
    'non-road': '#774a0b',  # dark orange
    '07_x_jet_fuel': '#FFAA00',  # yellow
    '07_x_other_petroleum_products': '#F19411',  # light orange
    '07_06_kerosene':  '#FFA500', #pale orange
    'jet_fuels': '#FFAA00',  # yellow
    'other_fossil_fuels': '#000000',  # dark orange
    
    #non road activity/fuel combos:
    'air_jet_fuel': '#FFAA00',      # yellow
    'air_av_gasoline': '#FFFF33',   # lighter yellow
    'air_gasoline': '#CCCC00',      # darker yellow
    'air_diesel':  '#B22222',       # firebrick
    'air_electric': '#1488C6',      # aperc blue
    'air_hydrogen': '#800080',      # purple
    'ship_fuel_oil': '#774A0B',     # dark orange
    'ship_diesel':  '#E34234',      # lighter firebrick
    'ship_kerosene': '#F19411',     # light orange
    'ship_ammonia': '#8A2BE2',      # darkviolet
    'ship_electric': '#1BA0E2',     # lighter aperc blue
    'rail_diesel':  '#8B0000',      # darker firebrick
    'rail_electricity': '#10689B',  # darker aperc blue

    # Other categories
    'Population_index': '#808080',  # grey
    'passenger_km_index': '#FF0000',  # red
    'Gdp_index': '#A9A9A9',  # darkgray
    'Activity_8th_index': '#C0C0C0',  # lightgray
    'freight_tonne_km_index': '#0000FF',  # blue
    'Population': '#808080',  # grey
    'Gdp': '#FF0000',  # red
    'Gdp_per_capita': '#A9A9A9',  # darkgray
    'GDP_growth all': '#FF0000',  # red
    'Population_growth all': '#C0C0C0',  # lightgray
    
    'Activity_growth passenger non_road': '#774a0b',  # dark orange
    'Activity_growth freight non_road': '#160b77',  # dark blue
    'Activity_growth freight road': '#857cd8',  # light blue
    'Activity_growth passenger road': '#F19411',  # light orange

    'Total': '#808080',  # grey
    
    #passenger types
    '2w': '#FF0000',  # red
    'lpv': '#FFA500',  # orange
    'bus': '#FFFF00',  # yellow
    
    'passenger': '#FFA500',  # orange

    #freight types
    'lcv': '#0000FF',  # blue
    'truck': '#000000',  # black
    
    'freight': '#0000FF'  # blue
    
}

def prepare_fig_dict_and_subfolders(config, ECONOMY_IDs, plots, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR):
    """
    Prepares a dictionary of figures and creates subfolders for each economy.

    Args:
        ECONOMY_IDs (list): A list of economy IDs for which the figures are being created.
        plots (list): A list of plot names to include in the figures.
        ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR (int): The base year for the data being displayed in the figures.

    Returns:
        fig_dict (dict): A dictionary of figures, with keys corresponding to the economy IDs.
    """

    #fig dict will have the following structure:
    #economy > scenario > plots
    #so you can iterate through each economy, scenaio and plot the dashboard for the plots ordered as is in the list in the dict.
    #so in the end there will be a dashboard for every scenario and economy, with the plots in the order specified in the plots list
    fig_dict= {}
    for economy in config.economy_scenario_concordance['Economy'].unique():
        if economy in ECONOMY_IDs:

            if not ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR and not os.path.exists(config.root_dir + '\\' + 'plotting_output\\dashboards\\{}\\{}'.format(economy,config.OUTLOOK_BASE_YEAR)):#put plots in a subfolder if we are projecting to the outlook base year
                os.makedirs(config.root_dir + '\\' + 'plotting_output\\dashboards\\{}\\{}'.format(economy,config.OUTLOOK_BASE_YEAR))
            #create economy folder in plotting_output/dashboards too
            elif ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR and not os.path.exists(config.root_dir + '\\' + 'plotting_output\\dashboards\\{}'.format(economy)):
                os.makedirs(config.root_dir + '\\' + 'plotting_output\\dashboards\\{}'.format(economy))

            fig_dict[economy] = {}
            for scenario in config.economy_scenario_concordance['Scenario'].unique():
                fig_dict[economy][scenario] = {}
                for plot in plots:
                    fig_dict[economy][scenario][plot] = None
    return fig_dict

def create_dashboard(config, ECONOMY_IDs, plots, DROP_NON_ROAD_TRANSPORT, colors_dict, dashboard_name_id, hidden_legend_names, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, ARCHIVE_PREVIOUS_DASHBOARDS, CREATE_SINGLE_TRANSPORT_TYPE_MEDIUM_PLOTS_DICT=None, PRODUCE_AS_SINGLE_POTS=False, PREVIOUS_PROJECTION_FILE_DATE_ID=None, WRITE_INDIVIDUAL_HTMLS=False):
    """
    Creates an assumptions dashboard for the specified economies and plots.

    Args: 
        ECONOMY_IDs (list): A list of economy IDs for which the dashboard is being created.
        plots (list): A list of plot names to include in the dashboard.
        DROP_NON_ROAD_TRANSPORT (bool): Whether to drop non-road transport data from the dashboard.
        colors_dict (dict): A dictionary of colors to use for the dashboard.
        dashboard_name_id (str): The name or ID of the dashboard being created.
        hidden_legend_names (list): A list of legend names to hide in the dashboard.
        ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR (int): The base year for the data being displayed in the dashboard.
        ARCHIVE_PREVIOUS_DASHBOARDS (bool): Whether to archive previous dashboards before saving a new one.

    Returns:
        None
    """
    color_preparation_list = []
    fig_dict = prepare_fig_dict_and_subfolders(config, ECONOMY_IDs, plots,ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR)

    #get the plots:
    fig_dict, color_preparation_list = plotting_handler(config, ECONOMY_IDs, plots, fig_dict,  color_preparation_list, colors_dict, DROP_NON_ROAD_TRANSPORT,ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, CREATE_SINGLE_TRANSPORT_TYPE_MEDIUM_PLOTS_DICT=CREATE_SINGLE_TRANSPORT_TYPE_MEDIUM_PLOTS_DICT, PREVIOUS_PROJECTION_FILE_DATE_ID=PREVIOUS_PROJECTION_FILE_DATE_ID, WRITE_INDIVIDUAL_HTMLS=WRITE_INDIVIDUAL_HTMLS)

    check_colors_in_color_preparation_list(config, color_preparation_list, colors_dict)
    #now create the dashboards:
    for economy in fig_dict.keys():
            
        if PRODUCE_AS_SINGLE_POTS:
            #check that there is a folder with the name of the dashboard_name_id to put the single plots in
            if not os.path.exists(config.root_dir + '\\' + 'plotting_output\\dashboards\\{}\\{}'.format(economy, dashboard_name_id)):
                os.makedirs(config.root_dir + '\\' + 'plotting_output\\dashboards\\{}\\{}'.format(economy, dashboard_name_id))
                
        for scenario in fig_dict[economy].keys():
            #extract titles:
            titles= []
            fig_dict_new = copy.deepcopy(fig_dict.copy())
            for plot in fig_dict[economy][scenario].keys():
                if not fig_dict[economy][scenario][plot]:
                    #drop this plot from fig_dict as it doesnt exist anymore #should fix #'NoneType' object is not subscriptable
                    fig_dict_new[economy][scenario].pop(plot)
                    #for china , what are we ropping?
                    continue
                try:
                    if not fig_dict[economy][scenario][plot][2]:
                        #drop this plot from fig_dict
                        fig_dict_new[economy][scenario].pop(plot)
                        #for china , what are we ropping?
                        continue
                except TypeError:#'NoneType' object is not subscriptable
                    
                    #drop this plot from fig_dict since its probaly not enven there!
                    fig_dict_new[economy][scenario].pop(plot)
                    continue
                try:
                    titles.append(fig_dict[economy][scenario][plot][1])
                except:
                    breakpoint()
                    time.sleep(1)
                    raise ValueError(f'No title found for {plot}')
            
            # rows = int(np.ceil(np.sqrt(len(fig_dict_new[economy][scenario].keys()))))
            # cols = int(np.ceil(len(fig_dict_new[economy][scenario].keys())/rows))
            rows, cols = find_best_grid(config, len(fig_dict_new[economy][scenario].keys()))
            fig_dict = fig_dict_new.copy()
            fig  = make_subplots(
                rows=rows, cols=cols,
                #specs types will all be xy
                specs=[[{"type": "xy"} for col in range(cols)] for row in range(rows)],
                subplot_titles=titles
            )
            for i, plot in enumerate(fig_dict[economy][scenario].keys()):
                row = int(i/cols)+1
                col = i%cols+1
                #add the traceas for entire fig_i to the fig. This is because we are suing plotly express which returns a fig with multiple traces, however, plotly subplots only accepts one trace per subplot
                for trace in fig_dict[economy][scenario][plot][0]['data']:
                    #we need to change the line_dash in the sales shares data and this is the only way i could find how:
                    fig.add_trace(trace, row=row, col=col)
                if PRODUCE_AS_SINGLE_POTS:
                    #check that there is a folder for 
                    #write the plot to png for use in a presentation:
                    #PLEASE NOTE THAT THIS WONT SAVE ANYTHING UNLESS YOU ARE RUNNING PYTHON FILES FROM THE COMMAND LINE, I THINK.
                    fig_dict[economy][scenario][plot][0].write_image( config.root_dir + '\\' + 'plotting_output\\dashboards\\{}\\{}\\{}_graph_{}.png'.format(economy,dashboard_name_id, plot, scenario) , engine="kaleido")
                    #write as html
                    # pio.write_html(fig_dict[economy][scenario][plot][0], 'plotting_output\\dashboards\\{}\\{}\\{}_graph_{}.html'.format(economy,dashboard_name_id, plot, scenario))
                # fig.update_layout(fig_dict[economy][scenario][plot]['layout'])
                # fig.add_trace(fig_dict[economy][scenario][plot], row=row, col=col)
                # fig.update_layout(fig_dict[economy][scenario][plot]['layout'])#dont know why copliot rec'd this. could be sueful
                #this is a great function to remove duplicate legend items

            names = set()
            fig.for_each_trace(
                lambda trace:
                    trace.update(showlegend=False)
                    if (trace.name in hidden_legend_names or trace.name in names)
                    else names.add(trace.name))

            fig.update_layout(title_text=f"Dashboard for {economy} {scenario} - {dashboard_name_id}")
            if ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR:
                if ARCHIVE_PREVIOUS_DASHBOARDS:
                    archive_previous_dashboards_before_saving(config, economy, scenario, dashboard_name_id,config.GRAPHING_END_YEAR)
                pio.write_html(fig, config.root_dir + '\\' + 'plotting_output\\dashboards\\{}\\{}_{}_dashboard_{}.html'.format(economy, economy, scenario,dashboard_name_id))
            else:
                if ARCHIVE_PREVIOUS_DASHBOARDS:
                    archive_previous_dashboards_before_saving(config, economy, scenario,dashboard_name_id, config.OUTLOOK_BASE_YEAR)
                pio.write_html(fig, config.root_dir + '\\' + 'plotting_output\\dashboards\\{}\\{}\\{}_{}_dashboard_{}.html'.format(economy,config.OUTLOOK_BASE_YEAR,economy,  scenario,dashboard_name_id))

    return fig_dict
       
def find_best_grid(config, num_plots, max_diff=2):
    if num_plots <= 0:
        raise ValueError("Number of plots must be greater than 0.")
    
    best_pair = (1, num_plots)
    min_diff = abs(num_plots - 1)
    
    for i in range(1, int(math.sqrt(num_plots)) + 1):
        if num_plots % i == 0:
            pair = (i, num_plots // i)
            diff = abs(pair[0] - pair[1])
            if diff < min_diff:
                min_diff = diff
                best_pair = pair

    # If no pair found within max_diff, find the most square-like configuration
    if abs(pair[0] - pair[1]) > max_diff:
        for i in range(1, int(math.sqrt(num_plots)) + 1):
            pair = (i, math.ceil(num_plots / i))
            diff = abs(pair[0] - pair[1])
            if diff < min_diff:
                min_diff = diff
                best_pair = pair
    return best_pair


def archive_previous_dashboards_before_saving(config, economy, scenario, dashboard_name_id, end_year):
    """
    Archives the previous dashboards before saving a new one.

    Args:
        economy (str): The economy for which the dashboard is being created.
        scenario (str): The scenario for which the dashboard is being created.
        dashboard_name_id (str): The name or ID of the dashboard being created.
        end_year (int): The end year of the data being displayed in the dashboard.

    Returns:
        None
    """
    if end_year == config.GRAPHING_END_YEAR:
        #archive previous dashboards:
        if os.path.exists(config.root_dir + '\\' + 'plotting_output\\dashboards\\{}\\{}_{}_dashboard_{}.html'.format(economy,economy,  scenario,dashboard_name_id)):
            #create dir:
            if not os.path.exists(config.root_dir + '\\' + 'plotting_output\\dashboards\\archive\\{}\\{}'.format(datetime.datetime.now().strftime("%Y%m%d_%H"), economy)):
                os.makedirs(config.root_dir + '\\' + 'plotting_output\\dashboards\\archive\\{}\\{}'.format(datetime.datetime.now().strftime("%Y%m%d_%H"), economy))
            shutil.move(config.root_dir + '\\' + 'plotting_output\\dashboards\\{}\\{}_{}_dashboard_{}.html'.format(economy,economy,  scenario,dashboard_name_id), config.root_dir + '\\' + 'plotting_output\\dashboards\\archive\\{}\\{}\\{}_{}_{}_dashboard_{}.html'.format(datetime.datetime.now().strftime("%Y%m%d_%H"), economy,config.GRAPHING_END_YEAR, economy, scenario,dashboard_name_id))

    elif end_year == config.OUTLOOK_BASE_YEAR:
        if os.path.exists(config.root_dir + '\\' + 'plotting_output\\dashboards\\{}\\{}\\{}_{}_dashboard_{}.html'.format(economy,config.OUTLOOK_BASE_YEAR,economy,  scenario,dashboard_name_id)):
            #create dir:
            if not os.path.exists(config.root_dir + '\\' + 'plotting_output\\dashboards\\archive\\{}\\{}'.format(datetime.datetime.now().strftime("%Y%m%d_%H"), economy)):
                os.makedirs(config.root_dir + '\\' + 'plotting_output\\dashboards\\archive\\{}\\{}'.format(datetime.datetime.now().strftime("%Y%m%d_%H"), economy))
            shutil.move(config.root_dir + '\\' + 'plotting_output\\dashboards\\{}\\{}\\{}_{}_dashboard_{}.html'.format(economy,config.OUTLOOK_BASE_YEAR, economy, scenario,dashboard_name_id), config.root_dir + '\\' + 'plotting_output\\dashboards\\archive\\{}\\{}\\{}_{}_{}_dashboard_{}.html'.format(datetime.datetime.now().strftime("%Y%m%d_%H"), economy,config.OUTLOOK_BASE_YEAR, economy, scenario,dashboard_name_id))


def load_and_format_input_data(config, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, ECONOMY_IDs, PREVIOUS_PROJECTION_FILE_DATE_ID):
    """
    Loads and formats the input data for the specified economies.

    Args:
        ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR (int): The base year for the data being displayed in the dashboard.
        ECONOMY_IDs (list): A list of economy IDs for which the input data is being loaded.

    Returns:
        model_output_detailed (pandas.DataFrame): A dataframe containing the detailed model output data for the specified economies.
        measure_to_unit_concordance_dict (dict): A dictionary mapping measure names to unit names.
        economy_scenario_concordance (pandas.DataFrame): A dataframe containing the concordance between economy IDs and scenario names.
    """
    #LAOD IN REQURIED DATA FOR PLOTTING EVERYTHING:
    model_output_detailed = pd.DataFrame()
    energy_output_for_outlook_data_system = pd.DataFrame()
    chargers = pd.DataFrame()
    supply_side_fuel_mixing = pd.DataFrame()
    demand_side_fuel_mixing = pd.DataFrame()
    road_model_input = pd.DataFrame()
    model_output_detailed_detailed_non_road_drives = pd.DataFrame()
    growth_forecasts = pd.DataFrame()
    first_road_model_run_data = pd.DataFrame()
    model_output_with_fuels = pd.DataFrame()
    new_sales_shares_all_plot_drive_shares = pd.DataFrame()
    gompertz_parameters_df = pd.DataFrame()
    activity_change_for_plotting = pd.DataFrame()
    previous_projection_energy_output_for_outlook_data_system = pd.DataFrame()
    previous_bunkers_data = pd.DataFrame()
    bunkers_data = pd.DataFrame()
    supply_side_fuel_mixing_output = pd.DataFrame()
    def assign_FILE_DATE_ID(ECONOMY_IDs):
        #in some cases we dont have the data for the file date id that is stated in the config.py file so this will first check that we have the data for the file date id, and if not, it will assign the latest file date id that we do have data for.
        ECONOMY_IDs_dict = {}
        for economy in ECONOMY_IDs:
            if os.path.exists(config.root_dir + '\\' + 'output_data\\model_output_with_fuels\\{}_{}'.format(economy, config.model_output_file_name)):
                ECONOMY_IDs_dict[economy] = config.FILE_DATE_ID
            else:
                date_id = utility_functions.get_latest_date_for_data_file(config.root_dir + '\\' + 'output_data\\model_output_with_fuels', '{}_'.format(economy))
                ECONOMY_IDs_dict[economy] = date_id
        return ECONOMY_IDs_dict
    
    #please note that this ECONOMY_IDs_dict only works within the for loop below, so any use of file ids outside of this loop will still use only the config.FILE_DATE_ID
    ECONOMY_IDs_dict = assign_FILE_DATE_ID(ECONOMY_IDs)
    for economy in ECONOMY_IDs_dict.keys():
        date_id = ECONOMY_IDs_dict[economy]
        if date_id == None:
            continue
        model_output_file_name = 'model_output{}.csv'.format(date_id)
        model_output_with_fuels_ = pd.read_csv(config.root_dir + '\\' + 'output_data\\model_output_with_fuels\\{}_{}'.format(economy, model_output_file_name))
        model_output_detailed_ = pd.read_csv(config.root_dir + '\\' + 'output_data\\model_output_detailed\\{}_{}'.format(economy, model_output_file_name))
        energy_output_for_outlook_data_system_ = pd.read_csv(config.root_dir + '\\' + f'output_data\\for_other_modellers\\output_for_outlook_data_system\\{economy}_{date_id}_transport_energy_use.csv')
        chargers_ = pd.read_csv(config.root_dir + '\\' + 'output_data\\for_other_modellers\\charging\\{}_estimated_number_of_chargers.csv'.format(economy))
        supply_side_fuel_mixing_ = pd.read_csv(config.root_dir + '\\' + 'intermediate_data\\model_inputs\\{}\\{}_supply_side_fuel_mixing.csv'.format(date_id, economy))
        demand_side_fuel_mixing_ = pd.read_csv(config.root_dir + '\\' + 'intermediate_data\\model_inputs\\{}\\{}_aggregated_demand_side_fuel_mixing.csv'.format(date_id, economy))
        road_model_input_ = pd.read_csv(config.root_dir + '\\' + 'intermediate_data\\model_inputs\\{}\\{}_road_model_input_wide.csv'.format(date_id, economy))
        model_output_detailed_detailed_non_road_drives_ = pd.read_csv(config.root_dir + '\\' + 'output_data\\model_output_detailed\\{}_NON_ROAD_DETAILED_{}'.format(economy, model_output_file_name))
        growth_forecasts_ = pd.read_csv(config.root_dir + '\\' +f'intermediate_data\\model_inputs\\{date_id}\\{economy}_growth_forecasts_wide.csv')
        first_road_model_run_data_ = pd.read_csv(config.root_dir + '\\' + 'intermediate_data\\road_model\\first_run_{}_{}'.format(economy, model_output_file_name))
        new_sales_shares_all_plot_drive_shares_ = pd.read_csv(config.root_dir + '\\' + 'intermediate_data\\model_inputs\\{}\\{}_vehicle_sales_share.csv'.format(date_id, economy))
        gompertz_parameters_df_ = pd.read_csv(config.root_dir + '\\' + 'intermediate_data\\road_model\\{}_parameters_estimates_{}.csv'.format(economy, date_id)) 
        activity_change_for_plotting_ = pd.read_csv(config.root_dir + '\\' + 'intermediate_data\\model_outputs\\{}_medium_to_medium_activity_change_for_plotting{}.csv'.format(economy, date_id))
        bunkers_data_ = pd.read_csv(config.root_dir + '\\' +f'output_data\\for_other_modellers\\output_for_outlook_data_system\\{economy}_international_bunker_energy_use_{date_id}.csv'.format(economy))
        supply_side_fuel_mixing_output_ = pd.read_csv(config.root_dir + '\\' + 'intermediate_data\\model_outputs\\{}_supply_side_fuel_shares_{}.csv'.format(economy, date_id))
                
        ##################
        #NOTE THAT WITH THE PREVIOUS_PROJECTION_FILE_DATE_ID THE FILE SHOULD BE SAVED IN C:\Users\finbar.maunsell\OneDrive - APERC\outlook 9th\Modelling\Sector models\Transport - results only\01_AUS/01_AUS_20240327_transport_energy_use.csv SO YOU CAN ALWAYS GRAB THAT AND PUT IT IN C:\Users\finbar.maunsell\github\transport_model_9th_edition\output_data\for_other_modellers\output_for_outlook_data_system IF YOU WANT TO MAKE SURE YOU'RE USING THAT FILE AND NOT A DIFFERENT VERSION WITH SAME DATE ID

        if PREVIOUS_PROJECTION_FILE_DATE_ID!=None:
            previous_projection_energy_output_for_outlook_data_system_ = pd.read_csv(config.root_dir + '\\' +f'output_data\\for_other_modellers\\output_for_outlook_data_system\\{economy}_{PREVIOUS_PROJECTION_FILE_DATE_ID}_transport_energy_use.csv')
            previous_bunkers_data_ = pd.read_csv(config.root_dir + '\\' +f'output_data\\for_other_modellers\\output_for_outlook_data_system\\{economy}_international_bunker_energy_use_{PREVIOUS_PROJECTION_FILE_DATE_ID}.csv'.format(economy))
        ##################
        model_output_with_fuels = pd.concat([model_output_with_fuels, model_output_with_fuels_])
        model_output_detailed = pd.concat([model_output_detailed, model_output_detailed_])
        energy_output_for_outlook_data_system = pd.concat([energy_output_for_outlook_data_system, energy_output_for_outlook_data_system_])
        chargers = pd.concat([chargers, chargers_])
        supply_side_fuel_mixing = pd.concat([supply_side_fuel_mixing, supply_side_fuel_mixing_])
        demand_side_fuel_mixing = pd.concat([demand_side_fuel_mixing, demand_side_fuel_mixing_])
        road_model_input = pd.concat([road_model_input, road_model_input_])
        model_output_detailed_detailed_non_road_drives = pd.concat([model_output_detailed_detailed_non_road_drives, model_output_detailed_detailed_non_road_drives_])
        growth_forecasts = pd.concat([growth_forecasts, growth_forecasts_])
        first_road_model_run_data = pd.concat([first_road_model_run_data, first_road_model_run_data_])
        new_sales_shares_all_plot_drive_shares = pd.concat([new_sales_shares_all_plot_drive_shares, new_sales_shares_all_plot_drive_shares_])
        gompertz_parameters_df = pd.concat([gompertz_parameters_df, gompertz_parameters_df_])
        activity_change_for_plotting = pd.concat([activity_change_for_plotting, activity_change_for_plotting_])
        bunkers_data = pd.concat([bunkers_data, bunkers_data_])
        supply_side_fuel_mixing_output = pd.concat([supply_side_fuel_mixing_output, supply_side_fuel_mixing_output_])
        if PREVIOUS_PROJECTION_FILE_DATE_ID!=None:
            previous_projection_energy_output_for_outlook_data_system = pd.concat([previous_projection_energy_output_for_outlook_data_system, previous_projection_energy_output_for_outlook_data_system_])
            previous_bunkers_data = pd.concat([previous_bunkers_data, previous_bunkers_data_])
    ###########
    #melt the energy_output_for_outlook_data_system data so that the date is in a column:
    id_cols = ['economy', 'scenarios', 'fuels', 'subfuels', 'sectors', 'sub1sectors', 'sub2sectors', 'sub3sectors', 'sub4sectors']
    energy_output_for_outlook_data_system = pd.melt(energy_output_for_outlook_data_system, id_vars=id_cols, var_name='Date', value_name='Energy')
    
    bunkers_data = pd.melt(bunkers_data, id_vars=id_cols, var_name='Date', value_name='Energy')
    #times energy by -1 so that it is not negative
    bunkers_data = bunkers_data.assign(Energy=bunkers_data['Energy']*-1)
    #set date to int
    energy_output_for_outlook_data_system['Date'] = energy_output_for_outlook_data_system['Date'].astype(int)
    bunkers_data['Date'] = bunkers_data['Date'].astype(int)
    
    if PREVIOUS_PROJECTION_FILE_DATE_ID!=None:
        previous_projection_energy_output_for_outlook_data_system = pd.melt(previous_projection_energy_output_for_outlook_data_system, id_vars=id_cols, var_name='Date', value_name='Energy')
        #set date to int
        previous_projection_energy_output_for_outlook_data_system['Date'] = previous_projection_energy_output_for_outlook_data_system['Date'].astype(int)
        previous_bunkers_data = pd.melt(previous_bunkers_data, id_vars=id_cols, var_name='Date', value_name='Energy')
        #times energy by -1 so that it is not negative
        previous_bunkers_data = previous_bunkers_data.assign(Energy=previous_bunkers_data['Energy']*-1)
        previous_bunkers_data['Date'] = previous_bunkers_data['Date'].astype(int)
    ###########

    original_model_output_8th = pd.read_csv(config.root_dir + '\\' + 'input_data\\from_8th\\reformatted\\activity_energy_road_stocks.csv').rename(columns={'Year':'Date'})
    emissions_factors = pd.read_csv(config.root_dir + '\\' + 'config\\9th_edition_emissions_factors.csv')
    date_id = utility_functions.get_latest_date_for_data_file(config.root_dir + '\\' + 'input_data\9th_model_inputs', 'model_df_wide_')
    energy_use_esto = pd.read_csv(config.root_dir + '\\' +f'input_data\\9th_model_inputs\\model_df_wide_{date_id}.csv')
    data_8th = pd.read_csv(config.root_dir + '\\' + 'input_data\\from_8th\\reformatted\\activity_energy_road_stocks.csv')
    energy_8th = pd.read_csv(config.root_dir + '\\' + 'input_data\\from_8th\\reformatted\\8th_energy_by_fuel.csv')
    
    if ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR:
        def filter_between_outlook_BASE_YEAR_and_end_year(df):
            return df.loc[(df['Date']>=config.OUTLOOK_BASE_YEAR) & (df['Date']<=config.GRAPHING_END_YEAR)].copy()
        new_sales_shares_all_plot_drive_shares = filter_between_outlook_BASE_YEAR_and_end_year(new_sales_shares_all_plot_drive_shares)
        model_output_detailed = filter_between_outlook_BASE_YEAR_and_end_year(model_output_detailed)
        energy_output_for_outlook_data_system = filter_between_outlook_BASE_YEAR_and_end_year(energy_output_for_outlook_data_system)
        bunkers_data = filter_between_outlook_BASE_YEAR_and_end_year(bunkers_data)
        original_model_output_8th = filter_between_outlook_BASE_YEAR_and_end_year(original_model_output_8th)
        chargers = filter_between_outlook_BASE_YEAR_and_end_year(chargers)
        supply_side_fuel_mixing = filter_between_outlook_BASE_YEAR_and_end_year(supply_side_fuel_mixing)
        demand_side_fuel_mixing = filter_between_outlook_BASE_YEAR_and_end_year(demand_side_fuel_mixing)
        model_output_detailed_detailed_non_road_drives = filter_between_outlook_BASE_YEAR_and_end_year(model_output_detailed_detailed_non_road_drives)
        growth_forecasts = filter_between_outlook_BASE_YEAR_and_end_year(growth_forecasts)
        first_road_model_run_data = filter_between_outlook_BASE_YEAR_and_end_year(first_road_model_run_data)
        model_output_with_fuels = filter_between_outlook_BASE_YEAR_and_end_year(model_output_with_fuels)
        
        if PREVIOUS_PROJECTION_FILE_DATE_ID!=None:
            previous_projection_energy_output_for_outlook_data_system = filter_between_outlook_BASE_YEAR_and_end_year(previous_projection_energy_output_for_outlook_data_system)
            previous_bunkers_data = filter_between_outlook_BASE_YEAR_and_end_year(previous_bunkers_data)
    else:
        def filter_outlook_BASE_YEAR(df):
            return df.loc[df['Date']<=config.OUTLOOK_BASE_YEAR].copy()
        #filter all data so it is less than or equal to the outlook base year
        new_sales_shares_all_plot_drive_shares = filter_outlook_BASE_YEAR(new_sales_shares_all_plot_drive_shares)
        model_output_detailed = filter_outlook_BASE_YEAR(model_output_detailed)
        energy_output_for_outlook_data_system = filter_outlook_BASE_YEAR(energy_output_for_outlook_data_system)
        bunkers_data = filter_outlook_BASE_YEAR(bunkers_data)
        original_model_output_8th = filter_outlook_BASE_YEAR(original_model_output_8th)
        chargers = filter_outlook_BASE_YEAR(chargers)
        supply_side_fuel_mixing = filter_outlook_BASE_YEAR(supply_side_fuel_mixing)
        demand_side_fuel_mixing = filter_outlook_BASE_YEAR(demand_side_fuel_mixing)
        model_output_detailed_detailed_non_road_drives = filter_outlook_BASE_YEAR(model_output_detailed_detailed_non_road_drives)
        growth_forecasts = filter_outlook_BASE_YEAR(growth_forecasts)
        first_road_model_run_data = filter_outlook_BASE_YEAR(first_road_model_run_data)
        model_output_with_fuels = filter_outlook_BASE_YEAR(model_output_with_fuels)
        
        if PREVIOUS_PROJECTION_FILE_DATE_ID!=None:
            previous_projection_energy_output_for_outlook_data_system = filter_outlook_BASE_YEAR(previous_projection_energy_output_for_outlook_data_system)
            previous_bunkers_data= filter_outlook_BASE_YEAR(previous_bunkers_data)

    #Format stocks data specifically, since we use it a lot:
    stocks = model_output_detailed.loc[(model_output_detailed['Medium']=='road')][config.INDEX_COLS_NO_MEASURE+['Stocks']].rename(columns={'Stocks':'Value'}).copy()
    energy_output_for_outlook_data_system = format_energy_output_for_outlook_data_system_for_plotting(config, energy_output_for_outlook_data_system)
    bunkers_data = format_energy_output_for_outlook_data_system_for_plotting(config, bunkers_data)
    
    energy_use_esto,esto_bunkers_data = format_esto_data_for_plotting(config, energy_use_esto,ECONOMY_IDs)
    energy_8th, data_8th = format_8th_data_for_plotting(config, energy_8th, data_8th, ECONOMY_IDs)
    
    if PREVIOUS_PROJECTION_FILE_DATE_ID!=None:
        previous_projection_energy_output_for_outlook_data_system = format_energy_output_for_outlook_data_system_for_plotting(config, previous_projection_energy_output_for_outlook_data_system)
        previous_bunkers_data = format_energy_output_for_outlook_data_system_for_plotting(config, previous_bunkers_data)

    # energy_use_esto = extract_and_clean_esto_data(energy_output_for_outlook_data_system, ECONOMY_IDs)
    # #filter for ECONOMY_IDs
    # new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares.loc[new_sales_shares_all_plot_drive_shares['Economy'].isin(ECONOMY_IDs)]
    # model_output_detailed = model_output_detailed.loc[model_ostocksutput_detailed['Economy'].isin(ECONOMY_IDs)]
    # energy_output_for_outlook_data_system = energy_output_for_outlook_data_system.loc[energy_output_for_outlook_data_system['Economy'].isin(ECONOMY_IDs)]
    # original_model_output_8th = original_model_output_8th.loc[original_model_output_8th['Economy'].isin(ECONOMY_IDs)]
    # chargers = chargers.loc[chargers['Economy'].isin(ECONOMY_IDs)]
    # supply_side_fuel_mixing = supply_side_fuel_mixing.loc[supply_side_fuel_mixing['Economy'].isin(ECONOMY_IDs)]
    # stocks = stocks.loc[stocks['Economy'].isin(ECONOMY_IDs)]

    return new_sales_shares_all_plot_drive_shares, model_output_detailed, model_output_detailed_detailed_non_road_drives, energy_output_for_outlook_data_system, original_model_output_8th, chargers, supply_side_fuel_mixing,demand_side_fuel_mixing, stocks, road_model_input, gompertz_parameters_df, growth_forecasts, emissions_factors, first_road_model_run_data, energy_use_esto, data_8th, energy_8th, activity_change_for_plotting, model_output_with_fuels, previous_projection_energy_output_for_outlook_data_system, bunkers_data,previous_bunkers_data,esto_bunkers_data, supply_side_fuel_mixing_output

def format_energy_output_for_outlook_data_system_for_plotting(config, energy_output_for_outlook_data_system):

    #where energy_output_for_outlook_data_system not contians x in subfuels, set fuels to subfuels
    energy_output_for_outlook_data_system.loc[energy_output_for_outlook_data_system['subfuels']!='x', 'fuels'] = energy_output_for_outlook_data_system.loc[energy_output_for_outlook_data_system['subfuels']!='x', 'subfuels']
    #drop subfuels
    energy_output_for_outlook_data_system = energy_output_for_outlook_data_system.drop(columns=['subfuels'])
    #also rename some thigns we will have to renamne every time:
    energy_output_for_outlook_data_system.rename(columns={'fuels':'Fuel', 'scenarios':'Scenario', 'economy':'Economy'}, inplace=True)

    #where sectors is in [04_international_marine_bunkers, 05_international_aviation_bunkers], set sub1sectors to sectors
    energy_output_for_outlook_data_system.loc[energy_output_for_outlook_data_system['sectors'].isin(['04_international_marine_bunkers', '05_international_aviation_bunkers']), 'sub1sectors'] = energy_output_for_outlook_data_system.loc[energy_output_for_outlook_data_system['sectors'].isin(['04_international_marine_bunkers', '05_international_aviation_bunkers']), 'sectors']
    
    #apply the inverse of the config.medium_mapping dict to the sub1sectors col to get Medium. then drop the sub1sectors col.
    inverse_mediums = {v: k for k, v in config.medium_mapping.items()}
    energy_output_for_outlook_data_system['Medium'] = energy_output_for_outlook_data_system['sub1sectors'].map(inverse_mediums)
    energy_output_for_outlook_data_system['Transport Type'] = energy_output_for_outlook_data_system['sub2sectors'].map(config.inverse_transport_type_mapping)

    energy_output_for_outlook_data_system = energy_output_for_outlook_data_system.drop(columns=['sub1sectors', 'sub2sectors']).copy()#canct remove these yet!. need them for merge with esto data

    #make scenarios values capitalised:
    energy_output_for_outlook_data_system['Scenario'] = energy_output_for_outlook_data_system['Scenario'].str.capitalize()

    #reaplce economies liek this  .replace({'15_PHL': '15_PHL', '17_SGP':
    #  '17_SIN'})
    # energy_output_for_outlook_data_system['Economy'] = energy_output_for_outlook_data_system['Economy'].replace({'15_PHL': '15_RP', '17_SGP': '17_SIN'})

    #remove any nas in Energy col
    energy_output_for_outlook_data_system = energy_output_for_outlook_data_system.loc[~energy_output_for_outlook_data_system['Energy'].isna()].copy()
    return energy_output_for_outlook_data_system

def format_esto_data_for_plotting(config, energy_use_esto_df, ECONOMY_IDs):

    #want to include post  and pre 2020 data from esto. that way we can show the difference between outlook and esto on a line graph
    energy_use_esto = energy_use_esto_df.copy()
    #grab only the transport data+bunkers
    energy_use_esto = energy_use_esto.loc[energy_use_esto['sectors'].isin(['15_transport_sector','04_international_marine_bunkers', '05_international_aviation_bunkers'])].copy()
    #drop pipelines and non specified
    energy_use_esto = energy_use_esto.loc[~energy_use_esto['sub1sectors'].isin(['15_06_nonspecified_transport', '15_05_pipeline_transport'])].copy()
    energy_use_esto = energy_use_esto.loc[energy_use_esto['economy'].isin(ECONOMY_IDs)].copy()

    #where sectors is in [04_international_marine_bunkers, 05_international_aviation_bunkers], set sub1sectors to sectors
    energy_use_esto.loc[energy_use_esto['sectors'].isin(['04_international_marine_bunkers', '05_international_aviation_bunkers']), 'sub1sectors'] = energy_use_esto.loc[energy_use_esto['sectors'].isin(['04_international_marine_bunkers', '05_international_aviation_bunkers']), 'sectors']
    
    #FORMAT THE DATA:
    #this is the same process as used in format_energy_output_for_outlook_data_system_for_plotting(config)
    #mlet the data:
    energy_use_esto = pd.melt(energy_use_esto, id_vars=['economy', 'scenarios', 'fuels', 'subfuels', 'sectors', 'sub1sectors', 'sub2sectors', 'sub3sectors', 'sub4sectors'], var_name='Date', value_name='Energy')
    #make date into int
    energy_use_esto['Date'] = energy_use_esto['Date'].astype(int)

    #MAP THE DATA:
    #where fuels is in '19_total', '20_total_renewables','21_modern_renewables', drop the rows
    energy_use_esto = energy_use_esto.loc[~energy_use_esto['fuels'].isin(['19_total', '20_total_renewables','21_modern_renewables'])].copy()
    #where fuels is 17_electricity, set subfuels to 17_electricity
    energy_use_esto.loc[energy_use_esto['fuels']=='17_electricity', 'subfuels'] = '17_electricity'
    #drop where subfuels is x
    energy_use_esto = energy_use_esto.loc[energy_use_esto['subfuels']!='x'].copy()
    #also drop where sub1sectors is x (these are aggregates) 
    energy_use_esto = energy_use_esto.loc[(energy_use_esto['sub1sectors']!='x')]
    #drop fuels
    energy_use_esto = energy_use_esto.drop(columns=['fuels'])
    #also rename some thigns we will have to renamne every time:
    energy_use_esto.rename(columns={'subfuels':'Fuel', 'scenarios':'Scenario', 'economy':'Economy'}, inplace=True)
    
    #apply the inverse of the config.medium_mapping dict to the sub1sectors col to get Medium. then drop the sub1sectors col.
    inverse_mediums = {v: k for k, v in config.medium_mapping.items()}
    energy_use_esto['Medium'] = energy_use_esto['sub1sectors'].map(inverse_mediums)
    energy_use_esto['Transport Type'] = energy_use_esto['sub2sectors'].map(config.inverse_transport_type_mapping)

    energy_use_esto = energy_use_esto.drop(columns=['sub1sectors', 'sub2sectors']).copy()#canct remove these yet!. need them for merge with esto data

    #make scenarios values capitalised:
    energy_use_esto['Scenario'] = energy_use_esto['Scenario'].str.capitalize()

    #reaplce economies liek this  .replace({'15_PHL': '15_RP', '17_SGP':
    #  '17_SIN'})
    # energy_use_esto['Economy'] = energy_use_esto['Economy'].replace({'15_PHL': '15_PHL', '17_SGP': '17_SIN'})

    #filter so Date is >= 2017
    energy_use_esto = energy_use_esto.loc[energy_use_esto['Date']>=2000].copy()

    #remove any nas in Energy col
    energy_use_esto = energy_use_esto.loc[~energy_use_esto['Energy'].isna()].copy()
    
    #separate bunkers data
    esto_bunkers_data = energy_use_esto.loc[energy_use_esto['Medium'].isin(['international_aviation', 'international_shipping'])].copy()
    #times bunkers data by -1 so that it is not negative
    esto_bunkers_data = esto_bunkers_data.assign(Energy=esto_bunkers_data['Energy']*-1)
    energy_use_esto = energy_use_esto.loc[~energy_use_esto['Medium'].isin(['international_aviation', 'international_shipping'])].copy()
    return energy_use_esto,esto_bunkers_data


def format_8th_data_for_plotting(config, energy_8th, data_8th, ECONOMY_IDs):
    #take in transport data form the 8th edition and format it so we cna make it as similar as possibe to 8th:cosl: Medium	Transport Type	Vehicle Type	Drive	Year	Economy	Scenario	Activity	Energy	Stocks
    #fitler for same economies
    data_8th = data_8th.loc[data_8th['Economy'].isin(ECONOMY_IDs)].copy()
    energy_8th = energy_8th.loc[energy_8th['Economy'].isin(ECONOMY_IDs)].copy()
    #reanme year to date
    data_8th.rename(columns={'Year':'Date'}, inplace=True)
    energy_8th = energy_8th.rename(columns={'Year':'Date', 'Value':'Energy'})
    #where sceanrio is Carbon Netural, set to Target
    data_8th.loc[data_8th['Scenario']=='Carbon Neutral', 'Scenario'] = 'Target'
    energy_8th.loc[energy_8th['Scenario']=='Carbon Neutral', 'Scenario'] = 'Target'
    #and remap a few drive types in so they match the 9th dtaa
    # 'd',  'g', 'phevg', 'phevd' : to ice_d, ice_g, phev_g, phev_d
    data_8th['Drive'] = data_8th['Drive'].replace({'d':'ice_d', 'g':'ice_g', 'phevg':'phev_g', 'phevd':'phev_d'})
    energy_8th['Drive'] = energy_8th['Drive'].replace({'d':'ice_d', 'g':'ice_g', 'phevg':'phev_g', 'phevd':'phev_d'})

    #map fuels to 9th version of the fuels:
    fuels_mapping = pd.read_csv(config.root_dir + '\\' + 'config\\concordances_and_config_data\\8th_to_9th_fuels.csv')
    energy_8th['New Fuel'] = energy_8th['Fuel'].map(dict(zip(fuels_mapping['8th_fuel'], fuels_mapping['9th_fuel'])))
    #where New Fuel is not nan, set Fuel to New Fuel. then drop new fuel
    energy_8th.loc[~energy_8th['New Fuel'].isna(), 'Fuel'] = energy_8th.loc[~energy_8th['New Fuel'].isna(), 'New Fuel']
    energy_8th = energy_8th.drop(columns=['New Fuel'])

    #remove any nas in Energy col
    data_8th = data_8th.loc[~data_8th['Energy'].isna()].copy()
    energy_8th = energy_8th.loc[~energy_8th['Energy'].isna()].copy()

    #filter so data isnt greater tahn 2050, as hugh didnt midel them in detail
    data_8th = data_8th.loc[data_8th['Date']<=2050].copy()
    energy_8th = energy_8th.loc[energy_8th['Date']<=2050].copy()
    return  energy_8th, data_8th

def create_single_transport_type_medium_plot(config, datasets_tuple, transport_type, mediums):
    #in all of the datasets filter for the transport type and medium
    new_datasets_tuple = ()
    for dataset in datasets_tuple:
        if 'Transport Type' in dataset.columns and transport_type != 'all':
            dataset = dataset.loc[dataset['Transport Type']==transport_type].copy()
        if 'Medium' in dataset.columns:
            dataset = dataset.loc[dataset['Medium'].isin(mediums)].copy()
        #reassign the dataset to the original dataset
        new_datasets_tuple = new_datasets_tuple + (dataset,)
    return new_datasets_tuple
        
    
def plotting_handler(config, ECONOMY_IDs, plots, fig_dict, color_preparation_list, colors_dict, DROP_NON_ROAD_TRANSPORT, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, CREATE_SINGLE_TRANSPORT_TYPE_MEDIUM_PLOTS_DICT, PREVIOUS_PROJECTION_FILE_DATE_ID, WRITE_INDIVIDUAL_HTMLS):
    """
    Handles the creation of plots for the specified economies and plots.

    Args:
        ECONOMY_IDs (list): A list of economy IDs for which the plots are being created.
        plots (list): A list of plot names to include in the figures.
        fig_dict (dict): A dictionary of figures, with keys corresponding to the economy IDs.
        color_preparation_list (list): A list of colors to use for the plots.
        colors_dict (dict): A dictionary of colors to use for the dashboard.
        DROP_NON_ROAD_TRANSPORT (bool): Whether to drop non-road transport data from the plots.
        ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR (int): The base year for the data being displayed in the plots.

    Returns:
        None
    """
    #breakpoint()
    new_sales_shares_all_plot_drive_shares, model_output_detailed, model_output_detailed_detailed_non_road_drives, energy_output_for_outlook_data_system, original_model_output_8th, chargers, supply_side_fuel_mixing,demand_side_fuel_mixing, stocks,road_model_input, gompertz_parameters_df, growth_forecasts, emissions_factors, first_road_model_run_data, energy_use_esto, data_8th, energy_8th, activity_change_for_plotting,model_output_with_fuels, previous_projection_energy_output_for_outlook_data_system, bunkers_data,previous_bunkers_data,esto_bunkers_data, supply_side_fuel_mixing_output = load_and_format_input_data(config, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR,ECONOMY_IDs, PREVIOUS_PROJECTION_FILE_DATE_ID)
    
    #CREATE EXPERIMENTAL DATASETS TO PLOT. 
    if CREATE_SINGLE_TRANSPORT_TYPE_MEDIUM_PLOTS_DICT is not None:
        new_datasets_tuple = create_single_transport_type_medium_plot(config, (new_sales_shares_all_plot_drive_shares, model_output_detailed, model_output_detailed_detailed_non_road_drives, energy_output_for_outlook_data_system, original_model_output_8th, chargers, supply_side_fuel_mixing,demand_side_fuel_mixing,  stocks,road_model_input, gompertz_parameters_df, growth_forecasts, emissions_factors, first_road_model_run_data, energy_use_esto, data_8th, energy_8th, activity_change_for_plotting, model_output_with_fuels, previous_projection_energy_output_for_outlook_data_system, bunkers_data,previous_bunkers_data,esto_bunkers_data, supply_side_fuel_mixing_output), transport_type=CREATE_SINGLE_TRANSPORT_TYPE_MEDIUM_PLOTS_DICT['transport_type'], mediums=CREATE_SINGLE_TRANSPORT_TYPE_MEDIUM_PLOTS_DICT['mediums']) 
        new_sales_shares_all_plot_drive_shares, model_output_detailed, model_output_detailed_detailed_non_road_drives, energy_output_for_outlook_data_system, original_model_output_8th, chargers, supply_side_fuel_mixing, demand_side_fuel_mixing, stocks,road_model_input, gompertz_parameters_df, growth_forecasts, emissions_factors, first_road_model_run_data, energy_use_esto, data_8th, energy_8th, activity_change_for_plotting,model_output_with_fuels, previous_projection_energy_output_for_outlook_data_system, bunkers_data,previous_bunkers_data,esto_bunkers_data, supply_side_fuel_mixing_output = new_datasets_tuple
    
    #breakpoint()
    # Share of Transport Type
    share_transport_types = ['passenger', 'freight', 'all']
    for transport_type in share_transport_types:
        if f'share_of_transport_type_{transport_type}' in plots:
            fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.plot_share_of_transport_type(config, ECONOMY_IDs,new_sales_shares_all_plot_drive_shares,stocks,fig_dict, color_preparation_list, colors_dict,share_of_transport_type_type=transport_type, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    # Share of Vehicle Type by Transport Type
    share_vehicle_types = ['passenger', 'freight', 'all']
    INCLUDE_GENERAL_DRIVE_TYPES_list = ['True', 'False']
    for share_of_transport_type_type in share_vehicle_types:
        for drive_type in INCLUDE_GENERAL_DRIVE_TYPES_list:
            if f'share_of_vehicle_type_by_transport_type_{share_of_transport_type_type}_{drive_type}' in plots:
                INCLUDE_GENERAL_DRIVE_TYPES = True if drive_type == 'True' else False
                fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.plot_share_of_vehicle_type_by_transport_type(config, ECONOMY_IDs,new_sales_shares_all_plot_drive_shares,stocks,fig_dict, color_preparation_list, colors_dict, share_of_transport_type_type, INCLUDE_GENERAL_DRIVE_TYPES=INCLUDE_GENERAL_DRIVE_TYPES, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    # Sum of Vehicle Types by Transport Type
    sum_vehicle_types = ['passenger', 'freight', 'all']
    for share_of_transport_type_type in sum_vehicle_types:
        if f'sum_of_vehicle_types_by_transport_type_{share_of_transport_type_type}' in plots:
            fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.share_of_sum_of_vehicle_types_by_transport_type(config, ECONOMY_IDs,new_sales_shares_all_plot_drive_shares,stocks,fig_dict, color_preparation_list, colors_dict, share_of_transport_type_type, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    # Sum of Vehicle Types by Transport Type
    sum_vehicle_types = ['passenger', 'freight', 'all']
    for share_of_transport_type_type in sum_vehicle_types:
        if f'INTENSITY_ANALYSIS_sales_share_by_transport_type_{share_of_transport_type_type}' in plots:
            fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.INTENSITY_ANALYSIS_share_of_sum_of_vehicle_types_by_transport_type(config, ECONOMY_IDs,new_sales_shares_all_plot_drive_shares,stocks,fig_dict, color_preparation_list, colors_dict, share_of_transport_type_type, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    # Energy Use by Fuel Type
    energy_use_by_fuel_type_titles = [p for p in plots if 'energy_use_by_fuel_type' in p]
    for title in energy_use_by_fuel_type_titles:
        if 'non_road_energy_use_by_fuel_type' in title:
            continue#dealt with below
        if 'passenger' in title:
            transport_type = 'passenger'
        elif 'freight' in title:
            transport_type = 'freight'
        else:
            transport_type = 'all'
        if 'road' in title:
            medium = 'road'
        else:
            medium = 'all'
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.energy_use_by_fuel_type(config, ECONOMY_IDs,energy_output_for_outlook_data_system,fig_dict,color_preparation_list, colors_dict,transport_type, medium, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    #Non road energy Use by Fuel Type
    energy_transport_types = [p.split('_')[-1] for p in plots if 'non_road_energy_use_by_fuel_type' in p]
    for transport_type in energy_transport_types:
        if f'non_road_energy_use_by_fuel_type_{transport_type}' in plots:
            fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.plot_non_road_energy_use(config, ECONOMY_IDs,energy_output_for_outlook_data_system,fig_dict, color_preparation_list, colors_dict,transport_type, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
            
    titles = [p for p in plots if 'line_energy_use_by_' in p]
    for title in titles:
        transport_type = title.split('_')[-1]
        if 'non_road' in title:
            medium = 'non_road'
        elif 'road' in title:
            medium = 'road'
        elif 'sum' in title.split('_')[-2]:
            medium = 'sum'
        elif 'all' in title.split('_')[-2]:
            medium = 'all'
        if f'line_energy_use_by_{medium}_{transport_type}' in plots:
            assumptions_dashboard_plotting_scripts.line_energy_use_by_transport_type(config, ECONOMY_IDs,model_output_detailed,fig_dict,medium, color_preparation_list, colors_dict, transport_type, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
            
    #breakpoint()
    non_road_activity_types = [p.split('_')[-1] for p in plots if 'non_road_activity_by_drive' in p]
    for transport_type in non_road_activity_types:
        if f'non_road_activity_by_drive_{transport_type}' in plots:
            fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.non_road_activity_by_drive_type(config, ECONOMY_IDs,model_output_detailed_detailed_non_road_drives,fig_dict,color_preparation_list, colors_dict,transport_type, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    non_road_stocks_types = [p.split('_')[-1] for p in plots if 'non_road_stocks_by_drive' in p]
    for transport_type in non_road_stocks_types:
        if f'non_road_stocks_by_drive_{transport_type}' in plots:
            fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.non_road_stocks_by_drive_type(config, ECONOMY_IDs,model_output_detailed_detailed_non_road_drives, fig_dict,color_preparation_list, colors_dict,transport_type, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS) 
    # road_stocks_by_drive_type(config, ECONOMY_IDs,model_output_detailed_df, fig_dict, color_preparation_list, colors_dict,transport_type)
    road_stocks_types = [p.split('_')[-1] for p in plots if 'road_stocks_by_drive' in p and 'non_road' not in p]
    for transport_type in road_stocks_types:
        if f'road_stocks_by_drive_{transport_type}' in plots:
            fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.road_stocks_by_drive_type(config, ECONOMY_IDs,model_output_detailed, fig_dict, color_preparation_list, colors_dict,transport_type, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
            
    if 'road_sales_by_drive_vehicle' in plots:
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.road_sales_by_drive_vehicle(config, ECONOMY_IDs,model_output_detailed,fig_dict, color_preparation_list, colors_dict, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    # Emissions by Fuel Type
    
    emissions_plots = [p for p in plots if 'emissions_by_fuel_type' in p]
    for plot in emissions_plots:
        if 'gen' in plot:
            USE_AVG_GENERATION_EMISSIONS_FACTOR = True
            plot = plot.replace('_gen', '')
        else:
            USE_AVG_GENERATION_EMISSIONS_FACTOR = False
        if 'accumulated' in plot:
            USE_CUM_SUM_OF_EMISSIONS = True
            plot = plot.replace('_accumulated', '')
        else:
            USE_CUM_SUM_OF_EMISSIONS = False
        transport_type = plot.split('_')[-1]
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.emissions_by_fuel_type(config, ECONOMY_IDs, emissions_factors, energy_output_for_outlook_data_system, fig_dict, color_preparation_list, colors_dict,transport_type, USE_AVG_GENERATION_EMISSIONS_FACTOR=USE_AVG_GENERATION_EMISSIONS_FACTOR, USE_CUM_SUM_OF_EMISSIONS=USE_CUM_SUM_OF_EMISSIONS, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    if 'turnover_rate_age_curve' in plots:
        fig_dict = assumptions_dashboard_plotting_scripts.plot_turnover_rate_age_curve(config, ECONOMY_IDs,model_output_detailed,fig_dict, colors_dict, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    turnover_rate_types = [p.split('_')[-1] for p in plots if 'sales_and_turnover_lines_' in p]
    for transport_type in turnover_rate_types:
        if f'sales_and_turnover_lines_{transport_type}' in plots:
            fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.sales_and_turnover_lines(config, ECONOMY_IDs,model_output_detailed,fig_dict, color_preparation_list, colors_dict, transport_type, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    # turnover_rate_by_drive_type(fig_dict,DROP_NON_ROAD_TRANSPORT,  color_preparation_list, colors_dict,transport_type)
    turnover_rate_types = [p.split('_')[-1] for p in plots if 'turnover_rate_by_drive' in p]
    for transport_type in turnover_rate_types:
        if f'box_turnover_rate_by_drive_{transport_type}' in plots:
            
            fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.turnover_rate_by_drive_type_box(config, ECONOMY_IDs,model_output_detailed,fig_dict, color_preparation_list, colors_dict,transport_type, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)

    #breakpoint()
    turnover_rate_types = [p for p in plots if 'line_turnover_rate_by_vtype' in p]
    for title in turnover_rate_types:
        if 'non_road' in title:
            medium = 'non_road'
        elif 'road' in title:
            medium = 'road'
        else:
            medium = 'all'
        if 'passenger' in title:
            transport_type = 'passenger'
        elif 'freight' in title:
            transport_type = 'freight'
        else:
            transport_type = 'all'
        # breakpoint()
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.turnover_rate_by_vehicle_type_line(config, ECONOMY_IDs,model_output_detailed,fig_dict, color_preparation_list, colors_dict,transport_type, medium, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    mileage_types = [p.split('_')[-1] for p in plots if 'mileage_timeseries_' in p]
    for transport_type in mileage_types:
        if f'mileage_timeseries_{transport_type}' in plots:
            fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.plot_mileage_timeseries(config, ECONOMY_IDs,model_output_detailed,fig_dict, color_preparation_list, colors_dict, transport_type, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    share_of_vehicle_type_activity_ttypes = [p.split('_')[-1] for p in plots if 'share_of_vehicle_type_activity_' in p]
    for transport_type in share_of_vehicle_type_activity_ttypes:
        if f'share_of_vehicle_type_activity_{transport_type}' in plots:
            fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.plot_share_of_vehicle_type_activity(config, ECONOMY_IDs,model_output_detailed,fig_dict, color_preparation_list, colors_dict, transport_type, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)    
    #breakpoint()
    if 'mileage_strip' in plots:
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.plot_mileage_strip(config, ECONOMY_IDs,model_output_detailed,fig_dict, color_preparation_list, colors_dict, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    avg_age_types = [p for p in plots if 'avg_age' in p]
    for title in avg_age_types:
        #could be avg_age_nonroad, avg_age_road, avg_age_all
        medium = title.split('_')[-1]
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.plot_average_age_by_simplified_drive_type(config, ECONOMY_IDs,model_output_detailed_detailed_non_road_drives,fig_dict, color_preparation_list, colors_dict, medium, title, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    age_distributions_titles = [p for p in plots if 'age_distribution' in p]
    for title in age_distributions_titles:
        if 'non_road' in title:
            medium = 'non_road'
        elif 'road' in title:
            medium = 'road'
        elif 'all' in title:
            medium = 'all'
        
        if 'by_drive' in title:
           BY_DRIVE = True
        else:
            BY_DRIVE = False
        if 'by_vehicle_type' in title:
            BY_VEHICLE_TYPE = True
        else:
            BY_VEHICLE_TYPE = False
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.plot_age_distributions(config, ECONOMY_IDs,model_output_detailed_detailed_non_road_drives,fig_dict, color_preparation_list, colors_dict, medium, BY_DRIVE, BY_VEHICLE_TYPE, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    lmdi_types = [p for p in plots if 'lmdi' in p]
    for title in lmdi_types:
        if 'passenger' in title:
            transport_type = 'passenger'
        elif 'freight' in title:
            transport_type = 'freight'
        if 'road' in title:
            medium = 'road'
        elif 'all' in title:
            medium = 'all'
        if 'additive' in title:
            fig_dict= assumptions_dashboard_plotting_scripts.produce_LMDI_additive_plot(config, ECONOMY_IDs,fig_dict, colors_dict, medium, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
        else:
            fig_dict = assumptions_dashboard_plotting_scripts.prodcue_LMDI_mutliplicative_plot(config, ECONOMY_IDs,fig_dict,  colors_dict, transport_type = transport_type, medium=medium, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    freight_tonne_km_titles = [p for p in plots if 'freight_tonne_km_by_drive' in p]
    
    for title in freight_tonne_km_titles:
        if 'road' in title:
            medium = 'road'
        elif 'all' in title:
            medium = 'all'
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.freight_tonne_km_by_drive(config, ECONOMY_IDs,model_output_detailed,fig_dict,color_preparation_list, colors_dict, medium=medium, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    passenger_km_titles = [p for p in plots if 'passenger_km_by_drive' in p]
    for title in passenger_km_titles:
        if 'road' in title:
            medium = 'road'
        elif 'all' in title:
            medium = 'all'
        #create passenger km by drive plots
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.passenger_km_by_drive(config, ECONOMY_IDs,model_output_detailed,fig_dict, color_preparation_list, colors_dict, medium=medium, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    measures = [p for p in plots if '8th_9th_stocks' in p]
    for title in measures:
        if title == '8th_9th_stocks_stocks_share':
            measure = 'stocks_share'
        elif title == '8th_9th_stocks_sales_share':
            measure = 'sales_share'
        elif title == '8th_9th_stocks_sales':
            measure = 'sales'
        elif title == '8th_9th_stocks_stocks':
            measure = 'stocks'
        elif title == '8th_9th_stocks_turnover':
            measure = 'turnover'
        elif title == '8th_9th_stocks_change_in_stocks':
            measure = 'change_in_stocks'
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.compare_8th_and_9th_stocks_sales(config, ECONOMY_IDs,data_8th, model_output_detailed,fig_dict, color_preparation_list, colors_dict, measure, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    mapping_types = [p for p in plots if 'compare_energy1' in p]
    for title in mapping_types:
        if 'simplified' in title:
            mapping_type = 'simplified'
        elif 'all' in title:
            mapping_type = 'all'
        if '_8th' in title:
            INCLUDE_8TH=True
        else:
            INCLUDE_8TH=False
        if '_bunkers' in title:
            INCLUDE_BUNKERS=True
        else:
            INCLUDE_BUNKERS=False
        if '_onlybunkers' in title:
            ONLY_BUNKERS=True
        else:
            ONLY_BUNKERS=False
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.plot_comparison_of_energy_by_dataset(config, ECONOMY_IDs,energy_output_for_outlook_data_system, bunkers_data, energy_use_esto, esto_bunkers_data, energy_8th, fig_dict, color_preparation_list, colors_dict, mapping_type, INCLUDE_8TH, INCLUDE_BUNKERS,ONLY_BUNKERS, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    
    mapping_types = [p for p in plots if 'compare_energy_vs_previous_' in p]
    for title in mapping_types:
        if 'simplified' in title:
            mapping_type = 'simplified'
        elif 'all' in title:
            mapping_type = 'all'
        if '_bunkers' in title:
            INCLUDE_BUNKERS=True
        else:
            INCLUDE_BUNKERS=False
        if '_onlybunkers' in title:
            ONLY_BUNKERS=True
        else:
            ONLY_BUNKERS=False
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.plot_comparison_of_energy_to_previous_9th_projection(config, ECONOMY_IDs,energy_output_for_outlook_data_system, bunkers_data, previous_projection_energy_output_for_outlook_data_system,previous_bunkers_data, PREVIOUS_PROJECTION_FILE_DATE_ID, fig_dict, color_preparation_list, colors_dict, mapping_type, title, energy_use_esto, esto_bunkers_data, energy_8th, INCLUDE_BUNKERS,ONLY_BUNKERS, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    mapping_types = [p for p in plots if 'compare_energy2' in p]
    for title in mapping_types:
        if 'simplified' in title:
            mapping_type = 'simplified'
        elif 'all' in title:
            mapping_type = 'all'  
        if 'pct_difference' in title:
            measure = 'pct_difference' 
        elif 'difference' in title:
            measure = 'difference'
        if '_bunkers' in title:
            INCLUDE_BUNKERS=True
        else:
            INCLUDE_BUNKERS=False
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.plot_pct_comparison_of_energy_compared_to_8th(config, ECONOMY_IDs,energy_output_for_outlook_data_system, bunkers_data,  energy_8th, fig_dict, color_preparation_list, colors_dict, mapping_type,measure,INCLUDE_BUNKERS, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    mediums = [p for p in plots if 'energy_intensity_timeseries' in p]
    for medium in mediums:
        if 'all' in medium:
            medium = 'all'
        elif 'non_road' in medium:
            medium = 'non_road'
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.    plot_energy_intensity_timeseries(config, ECONOMY_IDs,model_output_detailed_detailed_non_road_drives,fig_dict, color_preparation_list, colors_dict, medium, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    if 'energy_efficiency_road_strip' in plots:
        DROP_NON_ROAD_TRANSPORT=True
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.plot_energy_efficiency_strip(config, ECONOMY_IDs,model_output_detailed,fig_dict,DROP_NON_ROAD_TRANSPORT, color_preparation_list, colors_dict, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    if 'energy_efficiency_all_strip' in plots:
        DROP_NON_ROAD_TRANSPORT=False
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.plot_energy_efficiency_strip(config, ECONOMY_IDs,model_output_detailed_detailed_non_road_drives,fig_dict,DROP_NON_ROAD_TRANSPORT, color_preparation_list, colors_dict, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    if 'INTENSITY_ANALYSIS_timeseries_passenger' in plots:
        DROP_NON_ROAD_TRANSPORT=True
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.plot_intensity_timeseries_INTENSITY_ANALYSIS(config, ECONOMY_IDs,model_output_detailed,fig_dict,DROP_NON_ROAD_TRANSPORT, color_preparation_list, colors_dict, transport_type = 'passenger', WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    if 'share_of_vehicle_type_by_transport_type_passenger_INTENSITY_ANALYSIS' in plots:
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.    INTENSITY_ANALYSIS_share_of_sum_of_vehicle_types_by_transport_type(config, ECONOMY_IDs,new_sales_shares_all_plot_drive_shares,stocks,fig_dict, color_preparation_list, colors_dict, share_of_transport_type_type, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    new_vehicle_efficiency_timeseries = [p for p in plots if 'new_vehicle_efficiency_timeseries_' in p]
    for plot in new_vehicle_efficiency_timeseries:
        if 'passenger' in plot:
            transport_type = 'passenger'
        elif 'freight' in plot:
            transport_type = 'freight'
        else:
            transport_type = 'all'
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.plot_new_vehicle_efficiency_by_vehicle_type(config, fig_dict, ECONOMY_IDs, model_output_detailed, colors_dict, color_preparation_list, DROP_NON_ROAD_TRANSPORT=True, transport_type=transport_type, extra_ice_line=True, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
        
    new_vehicle_efficiency_timeseries = [p for p in plots if 'new_vehicle_emissions_intensity_timeseries_' in p]
    for plot in new_vehicle_efficiency_timeseries:
        if 'passenger' in plot:
            transport_type = 'passenger'
        elif 'freight' in plot:
            transport_type = 'freight'
        else:
            transport_type = 'all'
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.plot_new_vehicle_emissions_intensity_by_vehicle_type(config, fig_dict, ECONOMY_IDs, model_output_detailed, emissions_factors, colors_dict, color_preparation_list, DROP_NON_ROAD_TRANSPORT=True, transport_type='all', extra_ice_line=True, extra_bev_line=True, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS, vehicle_type_grouping='simplified', USE_AVG_GENERATION_EMISSIONS_FACTOR=False)
    
    if 'energy_efficiency_timeseries_freight' in plots:
        DROP_NON_ROAD_TRANSPORT=True
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.plot_energy_efficiency_timeseries(config, ECONOMY_IDs,model_output_detailed,fig_dict,DROP_NON_ROAD_TRANSPORT, color_preparation_list, colors_dict, transport_type = 'freight', WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    if 'energy_efficiency_timeseries_passenger' in plots:
        DROP_NON_ROAD_TRANSPORT=True
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.plot_energy_efficiency_timeseries(config, ECONOMY_IDs,model_output_detailed,fig_dict,DROP_NON_ROAD_TRANSPORT, color_preparation_list, colors_dict,
        transport_type = 'passenger', WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    
    if 'energy_efficiency_timeseries_all' in plots:
        DROP_NON_ROAD_TRANSPORT=True
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.plot_energy_efficiency_timeseries(config, ECONOMY_IDs,model_output_detailed,fig_dict,DROP_NON_ROAD_TRANSPORT, color_preparation_list, colors_dict,
        transport_type = 'all', WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    if 'energy_intensity_strip' in plots:
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.        plot_energy_intensity_strip(config, ECONOMY_IDs,model_output_detailed_detailed_non_road_drives,fig_dict, color_preparation_list, colors_dict, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    if 'activity_and_macro_growth_lines' in plots:
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.activity_and_macro_growth_lines(config, ECONOMY_IDs,original_model_output_8th,model_output_detailed, growth_forecasts, fig_dict, color_preparation_list, colors_dict, indexed=False, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
            
    measures = [p for p in plots if 'macro_lines' in p]
    for measure in measures:
        #grab the words after macro_lines_ and join them with an underscore
        measure = '_'.join(measure.split('_')[2:])
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.macro_lines(config, ECONOMY_IDs, growth_forecasts, fig_dict, color_preparation_list, colors_dict, measure=measure, indexed=False, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    if 'supply_side_fuel_mixing' in plots:
        #insertt fuel mixing plots
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.plot_supply_side_fuel_mixing(config, ECONOMY_IDs,supply_side_fuel_mixing,fig_dict, color_preparation_list, colors_dict, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    if 'demand_side_fuel_mixing' in plots:
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.plot_demand_side_fuel_mixing(config, ECONOMY_IDs,demand_side_fuel_mixing,model_output_detailed,fig_dict, color_preparation_list, colors_dict, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    if 'charging' in plots:
        #charging:
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.create_charging_plot(config, ECONOMY_IDs,chargers,fig_dict, color_preparation_list, colors_dict, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    if 'vehicle_type_stocks' in plots:
        #vehicle_type_stocks
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.create_vehicle_type_stocks_plot(config, ECONOMY_IDs,stocks,fig_dict, color_preparation_list, colors_dict, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    if 'stocks_per_capita' in plots:
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.plot_stocks_per_capita(config, ECONOMY_IDs,gompertz_parameters_df,model_output_detailed, first_road_model_run_data, fig_dict, color_preparation_list, colors_dict, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    
    if 'non_road_share_of_transport_type' in plots:
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.plot_share_of_transport_type_non_road(config, ECONOMY_IDs,new_sales_shares_all_plot_drive_shares,fig_dict, color_preparation_list, colors_dict, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    if 'activity_growth' in plots:
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.activity_growth(config, ECONOMY_IDs,model_output_detailed,fig_dict,  color_preparation_list, colors_dict, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    if 'compare_ev_8th_and_9th_stocks_sales' in plots:
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.compare_ev_8th_and_9th_stocks_sales(config, ECONOMY_IDs,data_8th, model_output_detailed,fig_dict, color_preparation_list, colors_dict, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    if 'decrease_in_activity_from_activity_efficiency' in plots:
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.plot_decrease_in_activity_from_activity_efficiency(config, ECONOMY_IDs,model_output_detailed,fig_dict, color_preparation_list, colors_dict, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
    
    if 'shifted_activity_from_medium_to_medium' in plots:
        assumptions_dashboard_plotting_scripts.plot_shifted_activity_from_medium_to_medium(config, ECONOMY_IDs,activity_change_for_plotting,fig_dict, color_preparation_list, colors_dict, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
    #breakpoint()
        
    if 'lifecycle_emissions_of_cars' in plots:
        assumptions_dashboard_plotting_scripts.plot_lifecycle_emissions_of_cars(config, fig_dict,ECONOMY_IDs, model_output_detailed,colors_dict,color_preparation_list, model_output_with_fuels, ACCUMULATED=False, ONLY_CARS=True, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)    
    
    if 'share_of_emissions_by_vehicle_type' in plots:
        assumptions_dashboard_plotting_scripts.share_of_emissions_by_vehicle_type(config, fig_dict, ECONOMY_IDs, emissions_factors, model_output_with_fuels, colors_dict, color_preparation_list, WRITE_HTML=WRITE_INDIVIDUAL_HTMLS)
        
    return fig_dict, color_preparation_list

def check_colors_in_color_preparation_list(config, color_preparation_list, colors_dict):
    """
    Checks that all colors in the color preparation list are present in the colors dictionary.

    Args:
        color_preparation_list (list): A list of colors to use for the plots.
        colors_dict (dict): A dictionary of colors to use for the dashboard.

    Raises:
        ValueError: If any color in the color preparation list is not present in the colors dictionary.

    Returns:
        None
    """
    #filter out duplicates and then check what values are not in the colors_dict (which is what we set the colors in the charts with). If colors are missing then just add them manually.
    flattened_list = [item for sublist in color_preparation_list for item in sublist]
    color_preparation_list = list(set(flattened_list))
    missing_colors = []
    for color in color_preparation_list:
        if color not in colors_dict.keys():
            missing_colors.append(color)
    if len(missing_colors)>0:
        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
            print(f'The following colors are missing from the colors_dict: \n {missing_colors}')
    #save them to a csv so we can add them to the colors_dict later too
    pd.DataFrame(missing_colors).to_csv(config.root_dir + '\\' + 'plotting_output\\dashboards\\missing_colors.csv')

def remove_old_dashboards(config, ECONOMIES_TO_SKIP, dashboard_name_id):
    #quick function TO RMEOVE files from plotting_output/dashboards that are not in the ECONOMIES_TO_SKIP list. will search for the dashboard_name_id in the file name and if it is not in the ECONOMIES_TO_SKIP list then it will be removed.
    for economy in config.economy_scenario_concordance['Economy'].unique().tolist():
        if economy not in ECONOMIES_TO_SKIP:
            for file in os.listdir(config.root_dir + '\\' + f'plotting_output\\dashboards\\{economy}\\'):
                if dashboard_name_id in file:
                    os.remove(config.root_dir + '\\' + f'plotting_output\\dashboards\\{economy}\\{file}')
                    print(f'removed {file}')
                    
def dashboard_creation_handler(config, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=True, ECONOMY_ID=None, ARCHIVE_PREVIOUS_DASHBOARDS=False, PREVIOUS_PROJECTION_FILE_DATE_ID=None, WRITE_INDIVIDUAL_HTMLS=True):
    """
    Handles the creation of assumptions dashboards for the specified economies.

    Args:
        ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR (int): The base year for the data being displayed in the dashboards.
        ECONOMY_ID (str or None): The ID of the economy for which the dashboard is being created. If None, dashboards are created for all economies.
        ARCHIVE_PREVIOUS_DASHBOARDS (bool): Whether to archive previous dashboards before saving a new one.
        PREVIOUS_PROJECTION_FILE_DATE_ID: if this is not None then we use 'compare_energy_vs_previous_{mapping_type}' in the plots list for assumptions_extra with the previous projection file date id as file to comapre to.
    Returns:
        None
    """

    if ECONOMY_ID == None:
        #fill with all economys
        ECONOMY_IDs = config.economy_scenario_concordance['Economy'].unique().tolist()
    else:
        ECONOMY_IDs = [ECONOMY_ID]
    #PLOT OPTIONS:
    # energy_use_by_fuel_type_{transport_type}_{medium}
    # line_energy_use_by_{medium}_{transport_type}
    # non_road_energy_use_by_fuel_type_{transport_type}
    # share_of_transport_type_passenger
    # share_of_transport_type_freight
    # share_of_transport_type_all
    # share_of_vehicle_type_by_transport_type_passenger_{INCLUDE_GENERAL_DRIVE_TYPES} (True/False)
    # share_of_vehicle_type_by_transport_type_freight_{INCLUDE_GENERAL_DRIVE_TYPES}
    # share_of_vehicle_type_by_transport_type_all_{INCLUDE_GENERAL_DRIVE_TYPES}
    # sum_of_vehicle_types_by_transport_type_passenger
    # sum_of_vehicle_types_by_transport_type_freight
    # sum_of_vehicle_types_by_transport_type_all
    # energy_use_by_fuel_type_{transport_type}_{medium} 
    # freight_tonne_km_by_drive_{medium}
    # passenger_km_by_drive_{medium}
    # activity_and_macro_growth_lines
    # activity_growth
    # supply_side_fuel_mixing
    # demand_side_fuel_mixing
    # charging
    # vehicle_type_stocks
    # share_of_vehicle_type_activity_{transport_type} (all, freight, passenger)
    # lmdi_all
    # lmdi_passenger_road
    # lmdi_freight_road
    # lmdi_passenger_all
    # lmdi_freight_all
    # lmdi_additive_{medium}(road or all)
    # stocks_per_capita
    # non_road_activity_by_drive_{transport_type} (all, freight, passenger)
    # non_road_energy_use_by_fuel_type_{transport_type}
    # non_road_stocks_by_drive_{transport_type}
    # road_stocks_by_drive_{transport_type}
    # road_sales_by_drive_vehicle
    # box_turnover_rate_by_drive_{transport_type}
    # avg_age_nonroad, avg_age_road, avg_age_all
    # line_turnover_rate_by_vtype_{transport_type}_{medium} (all, freight, passenger) (all, non_road, road)
    # turnover_rate_age_curve
    # emissions_by_fuel_type_{transport_type}_{gen}_{accumulated} # if gen is there then use emisions factor for electricity generation. Same for accumulated, where we do a cumsum of the emissions if accumulated is there
    # share_of_emissions_by_vehicle_type
    # energy_efficiency_timeseries_freight
    # energy_efficiency_timeseries_passenger
    # energy_efficiency_timeseries_all
    # energy_efficiency_all_strip
    # energy_efficiency_road_strip
    # new_vehicle_efficiency_timeseries_
    # new_vehicle_emissions_intensity_timeseries_
    # energy_intensity_timeseries_{medium} (all, non_road)
    # energy_intensity_strip
    # mileage_strip
    # mileage_timeseries_{transport_type} (all, freight, passenger)
    # sales_and_turnover_lines_{transport_type} (all, freight, passenger)
    # 8th_9th_stocks_{measure} (stocks_share, sales_share, stocks, sales, turnover, change_in_stocks)
    # compare_energy1_{mapping_type}{_8th} (simplified, all) +_bunkers (if we want to include bunkers) +_onlybunkers (if we only want to include bunkers){the last two dont need to be included together, can be included separately}
    # compare_energy2_{measure}_{mapping_type} (pct_difference, difference) (simplified, all)
    #compare_energy_vs_previous_{mapping_type}+{'_ESTO'}{'_8th'} (simplified, all) (whre esto or 8th can be included or not)+_bunkers (if we want to include bunkers) +_onlybunkers (if we only want to include bunkers){the last two dont need to be included together, can be included separately}
    # age_distribution_{medium}{_by_drive}{_by_vehicle_type} (all, non_road, road) . For by_drive and by_vehicle_type, either leave nothng or add _by_drive or _by_vehicle_type or both
    # decrease_in_activity_from_activity_efficiency
    # shifted_activity_from_medium_to_medium
    # macro_lines_{measure} (population, gdp, gdp_per_capita)
    # lifecycle_emissions_of_cars #quite prescriptive, only one plot for now, not much customisation
    #####################################'
    # hidden_legend_names =  ['bev lcv, stocks', 'bev trucks, stocks', 'fcev trucks, stocks', 'bev 2w, stocks', 'bev bus, stocks', 'fcev bus, stocks', 'bev lpv, stocks', 'fcev lpv, stocks', 'fcev lcv, stocks']

    # plots = ['stocks_per_capita', 'avg_age_all']

    hidden_legend_names =  []

    #Create assumptions/major inputs dashboard to go along side a results dashboard:
    #Create a results dashboard:
    ######################################
    #RESULTS AND MAIN ASSUMPTIONS DASHBOARDS
    plots = ['energy_use_by_fuel_type_all_all','compare_energy1_all_8th',  'passenger_km_by_drive_road', 'freight_tonne_km_by_drive_road','non_road_energy_use_by_fuel_type_all', 'line_energy_use_by_all_all', 'sum_of_vehicle_types_by_transport_type_all', 'emissions_by_fuel_type_all']#'energy_use_by_fuel_type_passenger_road', 'energy_use_by_fuel_type_freight_road', 
    if PREVIOUS_PROJECTION_FILE_DATE_ID != None:
        #replce  'emissions_by_fuel_type_all_gen' with 'compare_energy_vs_previous_all_ESTO' and replace stocks with emissions_by_fuel_type_all_gen
        # plots.remove('vehicle_type_stocks')
        # plots.append(config.root_dir + '\\' + f'compare_energy_vs_previous_all_ESTO')
        plots = ['compare_energy_vs_previous_all_ESTO_simplified' if x == 'compare_energy1_all_8th' else x for x in plots]
        # plots = ['emissions_by_fuel_type_all_gen' if x == 'vehicle_type_stocks' else x for x in plots]
    #, 'charging']#activity_growth# 'charging',
    create_dashboard(config, ECONOMY_IDs, plots, DROP_NON_ROAD_TRANSPORT, colors_dict, dashboard_name_id = 'results',hidden_legend_names = hidden_legend_names,ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, ARCHIVE_PREVIOUS_DASHBOARDS=ARCHIVE_PREVIOUS_DASHBOARDS, PREVIOUS_PROJECTION_FILE_DATE_ID=PREVIOUS_PROJECTION_FILE_DATE_ID, WRITE_INDIVIDUAL_HTMLS=WRITE_INDIVIDUAL_HTMLS)
    #create a presentation dashboard:
    # plots = ['energy_use_by_fuel_type_all','passenger_km_by_drive', 'freight_tonne_km_by_drive', 'share_of_transport_type_passenger']#activity_growth
    # create_dashboard(config, ECONOMY_IDs, plots, DROP_NON_ROAD_TRANSPORT, colors_dict, dashboard_name_id = 'presentation',hidden_legend_names = hidden_legend_names,ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, ARCHIVE_PREVIOUS_DASHBOARDS=ARCHIVE_PREVIOUS_DASHBOARDS)
    
    #Create assumptions/major inputs dashboard to go along side a results dashboard:
    plots = ['energy_use_by_fuel_type_passenger_road', 'energy_use_by_fuel_type_freight_road', 'non_road_activity_by_drive_all','share_of_vehicle_type_by_transport_type_all_False','stocks_per_capita', 'supply_side_fuel_mixing', 'vehicle_type_stocks','lmdi_additive_road','compare_energy1_all_onlybunkers']#activity_growth
    #'energy_efficiency_timeseries_freight', 'energy_efficiency_road_strip','energy_efficiency_timeseries_passenger']#activity_growth
    if PREVIOUS_PROJECTION_FILE_DATE_ID != None:
        #replce  'emissions_by_fuel_type_all_gen' with 'compare_energy_vs_previous_all_ESTO' and replace stocks with emissions_by_fuel_type_all_gen
        # plots.remove('vehicle_type_stocks')
        # plots.append(config.root_dir + '\\' + f'compare_energy_vs_previous_all_ESTO')
        plots = ['compare_energy_vs_previous_all_ESTO_onlybunkers' if x == 'compare_energy1_all_onlybunkers' else x for x in plots]
    
    create_dashboard(config, ECONOMY_IDs, plots, DROP_NON_ROAD_TRANSPORT, colors_dict, dashboard_name_id = 'assumptions',hidden_legend_names = hidden_legend_names,ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, ARCHIVE_PREVIOUS_DASHBOARDS=ARCHIVE_PREVIOUS_DASHBOARDS, PREVIOUS_PROJECTION_FILE_DATE_ID=PREVIOUS_PROJECTION_FILE_DATE_ID,  WRITE_INDIVIDUAL_HTMLS=WRITE_INDIVIDUAL_HTMLS)
    #CREATE ASSUMPTIONS 2, WHICH IS THE EXTRA DATA THAT PROBABLY NOONE WILL WANT TO SEE, BUT AVAILABLE IF NEEDED:
    plots = ['macro_lines_population', 'macro_lines_gdp', 'energy_efficiency_timeseries_all', 'non_road_share_of_transport_type','share_of_vehicle_type_activity_all', 'energy_intensity_timeseries_non_road', 'mileage_timeseries_all',  'demand_side_fuel_mixing', 'share_of_emissions_by_vehicle_type', 'new_vehicle_efficiency_timeseries_all', 'charging','avg_age_road','decrease_in_activity_from_activity_efficiency', 'shifted_activity_from_medium_to_medium','energy_intensity_strip']#activity_growth
    #'energy_efficiency_timeseries_freight', 'energy_efficiency_road_strip','energy_efficiency_timeseries_passenger']#activity_growth #'road_sales_by_drive_vehicle','share_of_vehicle_type_by_transport_type_all_True',
    
    # if PREVIOUS_PROJECTION_FILE_DATE_ID != None:
    #     #since for results we drop stocks and include compare_energy_vs_previous_all, we will add stocks here instead
    #     plots.append(config.root_dir + '\\' + f'vehicle_type_stocks')
    try:
        create_dashboard(config, ECONOMY_IDs, plots, DROP_NON_ROAD_TRANSPORT, colors_dict, dashboard_name_id = 'assumptions_extra',hidden_legend_names = hidden_legend_names,ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, ARCHIVE_PREVIOUS_DASHBOARDS=ARCHIVE_PREVIOUS_DASHBOARDS, PREVIOUS_PROJECTION_FILE_DATE_ID=PREVIOUS_PROJECTION_FILE_DATE_ID,  WRITE_INDIVIDUAL_HTMLS=WRITE_INDIVIDUAL_HTMLS)
    except Exception as e:
        print('assumptions_extra dashboard not created, error: ', e)
        breakpoint()
    plots = ['energy_use_by_fuel_type_all_all', 'emissions_by_fuel_type_all_gen','passenger_km_by_drive_road','freight_tonne_km_by_drive_road', 'share_of_vehicle_type_by_transport_type_all','share_of_vehicle_type_activity_all', 'line_turnover_rate_by_vtype_all_road','avg_age_road',  'lmdi_freight_road',  'lmdi_passenger_road', 'energy_efficiency_timeseries_all','INTENSITY_ANALYSIS_timeseries_freight','INTENSITY_ANALYSIS_timeseries_passenger', 'share_of_vehicle_type_by_transport_type_freight_INTENSITY_ANALYSIS', 'share_of_vehicle_type_by_transport_type_passenger_INTENSITY_ANALYSIS', 'INTENSITY_ANALYSIS_sales_share_by_transport_type_passenger', 'INTENSITY_ANALYSIS_sales_share_by_transport_type_freight', 'INTENSITY_ANALYSIS_sales_share_by_transport_type_all', 'lifecycle_emissions_of_cars']
    
    CREATE_SINGLE_TRANSPORT_TYPE_MEDIUM_PLOTS_DICT = {'transport_type':'all', 'mediums':['road']}
    create_dashboard(config, ECONOMY_IDs, plots, DROP_NON_ROAD_TRANSPORT, colors_dict, dashboard_name_id = 'transport_type_intensity_analysis',hidden_legend_names = hidden_legend_names,ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, ARCHIVE_PREVIOUS_DASHBOARDS=ARCHIVE_PREVIOUS_DASHBOARDS,CREATE_SINGLE_TRANSPORT_TYPE_MEDIUM_PLOTS_DICT=CREATE_SINGLE_TRANSPORT_TYPE_MEDIUM_PLOTS_DICT, PRODUCE_AS_SINGLE_POTS=True, WRITE_INDIVIDUAL_HTMLS=WRITE_INDIVIDUAL_HTMLS)
    
    
    
    # #Create assumptions/major inputs dashboard to go along side a results dashboard:
    # plots = ['energy_use_by_fuel_type_all_all', 'emissions_by_fuel_type_all_gen','activity_growth',  'supply_side_fuel_mixing','sum_of_vehicle_types_by_transport_type_all','stocks_per_capita','avg_age_road',  'lmdi_freight_road', 'lmdi_passenger_road']#activity_growth
    # #'energy_efficiency_timeseries_freight', 'energy_efficiency_road_strip','energy_efficiency_timeseries_passenger']#activity_growth
    # create_dashboard(config, ECONOMY_IDs, plots, DROP_NON_ROAD_TRANSPORT, colors_dict, dashboard_name_id = 'presentation',hidden_legend_names = hidden_legend_names,ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, ARCHIVE_PREVIOUS_DASHBOARDS=ARCHIVE_PREVIOUS_DASHBOARDS)
    
    # #create a dashboard to compare against the 8th version of the model:
    # if '16_RUS' in ECONOMY_IDs:
        
    #     plots = ['8th_9th_stocks_stocks_share', '8th_9th_sales_share']
    #     create_dashboard(config, ECONOMY_IDs, plots, DROP_NON_ROAD_TRANSPORT, colors_dict, dashboard_name_id = 'compare_8th',hidden_legend_names = hidden_legend_names,ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, ARCHIVE_PREVIOUS_DASHBOARDS=ARCHIVE_PREVIOUS_DASHBOARDS,  WRITE_INDIVIDUAL_HTMLS=WRITE_INDIVIDUAL_HTMLS)
    # #create an extras dashboard:
    # plots = ['energy_use_by_fuel_type_all','passenger_km_by_drive', 'freight_tonne_km_by_drive', 'share_of_transport_type_passenger']#activity_growth
    # create_dashboard(config, ECONOMY_IDs, plots, DROP_NON_ROAD_TRANSPORT, colors_dict, dashboard_name_id = 'presentation',hidden_legend_names = hidden_legend_names,ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, ARCHIVE_PREVIOUS_DASHBOARDS=ARCHIVE_PREVIOUS_DASHBOARDS)
    
    
    # plots = ['energy_use_by_fuel_type_all_all', 'emissions_by_fuel_type_all_gen','activity_growth', 'stocks_per_capita', 'supply_side_fuel_mixing','share_of_vehicle_type_by_transport_type_all_False','sum_of_vehicle_types_by_transport_type_all','non_road_share_of_transport_type',  'energy_intensity_strip','energy_intensity_timeseries_non_road',  'mileage_timeseries_all', 'energy_efficiency_timeseries_all','turnover_rate_age_curve','line_turnover_rate_by_vtype_all_non_road', 'line_turnover_rate_by_vtype_all_road','avg_age_road', 'avg_age_nonroad', 'age_distribution_all','age_distribution_all_by_drive', 'decrease_in_activity_from_activity_efficiency']
    # #activity_growth
    # #'energy_efficiency_timeseries_freight', 'energy_efficiency_road_strip','energy_efficiency_timeseries_passenger']#activity_growth
    # create_dashboard(config, ECONOMY_IDs, plots, DROP_NON_ROAD_TRANSPORT, colors_dict, dashboard_name_id = 'development',hidden_legend_names = hidden_legend_names,ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR, ARCHIVE_PREVIOUS_DASHBOARDS=ARCHIVE_PREVIOUS_DASHBOARDS)
    
def plot_multi_economy_plots(config, ECONOMY_IDs, economy_grouping_name, plots, colors_dict, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=True, PREVIOUS_PROJECTION_FILE_DATE_ID=None, ONLY_AGG_OF_ALL=False):
    # config.FILE_DATE_ID = '20240327'
    new_sales_shares_all_plot_drive_shares, model_output_detailed, model_output_detailed_detailed_non_road_drives, energy_output_for_outlook_data_system, original_model_output_8th, chargers, supply_side_fuel_mixing, demand_side_fuel_mixing, stocks,road_model_input, gompertz_parameters_df, growth_forecasts, emissions_factors, first_road_model_run_data, energy_use_esto, data_8th, energy_8th, activity_change_for_plotting,model_output_with_fuels,previous_projection_energy_output_for_outlook_data_system, bunkers_data,previous_bunkers_data,esto_bunkers_data, supply_side_fuel_mixing_output  = load_and_format_input_data(config, ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR,ECONOMY_IDs, PREVIOUS_PROJECTION_FILE_DATE_ID)    
    sum_vehicle_types = ['passenger', 'freight', 'all']
    INDEPENDENT_AXIS_list = [True, False]
    AGG_OF_ALL_ECONOMIES = True
    SALES_list = [True, False]
    for transport_type in sum_vehicle_types:
        if f'plot_share_of_vehicle_type_by_transport_type_FOR_MULTIPLE_ECONOMIES_{transport_type}' in plots:
            assumptions_dashboard_plotting_scripts.plot_share_of_vehicle_type_by_transport_type_FOR_MULTIPLE_ECONOMIES(config, economy_grouping_name, new_sales_shares_all_plot_drive_shares,stocks, model_output_detailed, colors_dict, transport_type,AGG_OF_ALL_ECONOMIES=AGG_OF_ALL_ECONOMIES, ONLY_AGG_OF_ALL=ONLY_AGG_OF_ALL)
        if  f'plot_number_of_stocks_FOR_MULTIPLE_ECONOMIES_{transport_type}' in plots:
            for SALES in SALES_list:
                assumptions_dashboard_plotting_scripts.plot_number_of_stocks_FOR_MULTIPLE_ECONOMIES(config, economy_grouping_name, model_output_detailed, colors_dict, transport_type, SALES, AGG_OF_ALL_ECONOMIES = AGG_OF_ALL_ECONOMIES, ONLY_AGG_OF_ALL=ONLY_AGG_OF_ALL)
        if f'plot_emissions_by_fuel_type_FOR_MULTIPLE_ECONOMIES_{transport_type}' in plots:
            for INDEPENDENT_AXIS in INDEPENDENT_AXIS_list:
                assumptions_dashboard_plotting_scripts.emissions_by_fuel_type_FOR_MULTIPLE_ECONOMIES(config, economy_grouping_name, emissions_factors, model_output_with_fuels, colors_dict,transport_type=transport_type, AGG_OF_ALL_ECONOMIES=INDEPENDENT_AXIS, INDEPENDENT_AXIS=INDEPENDENT_AXIS, USE_AVG_GENERATION_EMISSIONS_FACTOR=True, ONLY_AGG_OF_ALL=ONLY_AGG_OF_ALL) 
        for medium in ['road', 'all']:
            if f'energy_use_by_fuel_type_FOR_MULTIPLE_ECONOMIES_{medium}_{transport_type}' in plots:
                for INDEPENDENT_AXIS in INDEPENDENT_AXIS_list:
                    assumptions_dashboard_plotting_scripts.energy_use_by_fuel_type_FOR_MULTIPLE_ECONOMIES(config, economy_grouping_name, energy_output_for_outlook_data_system, colors_dict,transport_type, medium,AGG_OF_ALL_ECONOMIES=INDEPENDENT_AXIS, INDEPENDENT_AXIS=INDEPENDENT_AXIS, ONLY_AGG_OF_ALL=ONLY_AGG_OF_ALL)
                            
            if f'prodcue_LMDI_mutliplicative_plot_FOR_MULTIPLE_ECONOMIES_{medium}_{transport_type}' in plots:
                assumptions_dashboard_plotting_scripts.prodcue_LMDI_mutliplicative_plot_FOR_MULTIPLE_ECONOMIES(config ,economy_grouping_name, model_output_with_fuels, colors_dict, ECONOMY_IDs,  transport_type=transport_type, medium=medium, AGG_OF_ALL_ECONOMIES=AGG_OF_ALL_ECONOMIES, ONLY_AGG_OF_ALL=ONLY_AGG_OF_ALL)
            if f'produce_LMDI_additive_plot_FOR_MULTIPLE_ECONOMIES_{medium}' in plots and transport_type == 'all':#dont want to repeat this for each transport type since theres only one plot for each medium
                assumptions_dashboard_plotting_scripts.produce_LMDI_additive_plot_FOR_MULTIPLE_ECONOMIES(config, economy_grouping_name, model_output_with_fuels, colors_dict, ECONOMY_IDs, medium=medium, AGG_OF_ALL_ECONOMIES=AGG_OF_ALL_ECONOMIES, ONLY_AGG_OF_ALL=ONLY_AGG_OF_ALL)
    if f'plot_supply_side_fuel_mixing_FOR_MULTIPLE_ECONOMIES' in plots:
        assumptions_dashboard_plotting_scripts.plot_supply_side_fuel_mixing_FOR_MULTIPLE_ECONOMIES(config, economy_grouping_name, supply_side_fuel_mixing, supply_side_fuel_mixing_output, colors_dict, AGG_OF_ALL_ECONOMIES=AGG_OF_ALL_ECONOMIES, ONLY_AGG_OF_ALL=ONLY_AGG_OF_ALL)
    if 'share_of_emissions_by_vehicle_type_FOR_MULTIPLE_ECONOMIES' in plots:
        assumptions_dashboard_plotting_scripts.share_of_emissions_by_vehicle_type_FOR_MULTIPLE_ECONOMIES(economy_grouping_name, emissions_factors, model_output_with_fuels, colors_dict, AGG_OF_ALL_ECONOMIES=AGG_OF_ALL_ECONOMIES, ONLY_AGG_OF_ALL=ONLY_AGG_OF_ALL)
        

    
def setup_and_run_multi_economy_plots(config, economies_to_skip=[], ONLY_AGG_OF_ALL=False):
    """helper function to run the multi economy plots.cuts down on setup and amount of code where we dont need it"""
    ECONOMY_IDs = config.economy_scenario_concordance['Economy'].unique().tolist()
    #drop png and bd from economy since they are not in the model yet
    for economy in economies_to_skip:
        ECONOMY_IDs.remove(economy)
    # ECONOMY_IDs.remove('13_PNG')
    # ECONOMY_IDs.remove('02_BD')
    economy_grouping_name = 'all'
    plots = [
    'share_of_emissions_by_vehicle_type_FOR_MULTIPLE_ECONOMIES',
    # 'plot_share_of_vehicle_type_by_transport_type_FOR_MULTIPLE_ECONOMIES_passenger', 'plot_share_of_vehicle_type_by_transport_type_FOR_MULTIPLE_ECONOMIES_freight', 
    'plot_share_of_vehicle_type_by_transport_type_FOR_MULTIPLE_ECONOMIES_all', 'plot_supply_side_fuel_mixing_FOR_MULTIPLE_ECONOMIES', 
    #  'energy_use_by_fuel_type_FOR_MULTIPLE_ECONOMIES_road_freight','energy_use_by_fuel_type_FOR_MULTIPLE_ECONOMIES_road_passenger',
    # 'energy_use_by_fuel_type_FOR_MULTIPLE_ECONOMIES_road_all',
    #  'energy_use_by_fuel_type_FOR_MULTIPLE_ECONOMIES_all_freight','energy_use_by_fuel_type_FOR_MULTIPLE_ECONOMIES_all_passenger',
    'energy_use_by_fuel_type_FOR_MULTIPLE_ECONOMIES_all_all',
    'plot_emissions_by_fuel_type_FOR_MULTIPLE_ECONOMIES_all',
    'plot_number_of_stocks_FOR_MULTIPLE_ECONOMIES_all',
    'plot_number_of_stocks_FOR_MULTIPLE_ECONOMIES_freight',
    'plot_number_of_stocks_FOR_MULTIPLE_ECONOMIES_passenger',
    # 'plot_emissions_by_fuel_type_FOR_MULTIPLE_ECONOMIES_passenger',
    # 'plot_emissions_by_fuel_type_FOR_MULTIPLE_ECONOMIES_freight',
    'prodcue_LMDI_mutliplicative_plot_FOR_MULTIPLE_ECONOMIES_road_passenger',
    'prodcue_LMDI_mutliplicative_plot_FOR_MULTIPLE_ECONOMIES_road_all',
    'prodcue_LMDI_mutliplicative_plot_FOR_MULTIPLE_ECONOMIES_road_freight',
    
    'prodcue_LMDI_mutliplicative_plot_FOR_MULTIPLE_ECONOMIES_all_passenger',
    'prodcue_LMDI_mutliplicative_plot_FOR_MULTIPLE_ECONOMIES_all_all',
    'prodcue_LMDI_mutliplicative_plot_FOR_MULTIPLE_ECONOMIES_all_freight',
    'produce_LMDI_additive_plot_FOR_MULTIPLE_ECONOMIES_road',
    'produce_LMDI_additive_plot_FOR_MULTIPLE_ECONOMIES_all',
    # 'plot_share_of_vehicle_type_by_transport_type_FOR_MULTIPLE_ECONOMIES_passenger_agg', 'plot_share_of_vehicle_type_by_transport_type_FOR_MULTIPLE_ECONOMIES_freight_agg', 
    'plot_share_of_vehicle_type_by_transport_type_FOR_MULTIPLE_ECONOMIES_all_agg', 'plot_supply_side_fuel_mixing_FOR_MULTIPLE_ECONOMIES_agg', 
    #  'energy_use_by_fuel_type_FOR_MULTIPLE_ECONOMIES_road_freight_agg','energy_use_by_fuel_type_FOR_MULTIPLE_ECONOMIES_road_passenger_agg',
    # 'energy_use_by_fuel_type_FOR_MULTIPLE_ECONOMIES_road_all_agg',
    #  'energy_use_by_fuel_type_FOR_MULTIPLE_ECONOMIES_all_freight_agg','energy_use_by_fuel_type_FOR_MULTIPLE_ECONOMIES_all_passenger_agg',
    'energy_use_by_fuel_type_FOR_MULTIPLE_ECONOMIES_all_all_agg',
    'plot_emissions_by_fuel_type_FOR_MULTIPLE_ECONOMIES_all_agg',
    'plot_number_of_stocks_FOR_MULTIPLE_ECONOMIES_all_agg',
    'plot_number_of_stocks_FOR_MULTIPLE_ECONOMIES_freight_agg',
    'plot_number_of_stocks_FOR_MULTIPLE_ECONOMIES_passenger_agg',
    # 'plot_emissions_by_fuel_type_FOR_MULTIPLE_ECONOMIES_passenger_agg',
    # 'plot_emissions_by_fuel_type_FOR_MULTIPLE_ECONOMIES_freight_agg'
    'prodcue_LMDI_mutliplicative_plot_FOR_MULTIPLE_ECONOMIES_road_passenger_agg',
    'prodcue_LMDI_mutliplicative_plot_FOR_MULTIPLE_ECONOMIES_road_all_agg',
    'prodcue_LMDI_mutliplicative_plot_FOR_MULTIPLE_ECONOMIES_road_freight_agg',
    
    'prodcue_LMDI_mutliplicative_plot_FOR_MULTIPLE_ECONOMIES_all_passenger_agg',
    'prodcue_LMDI_mutliplicative_plot_FOR_MULTIPLE_ECONOMIES_all_all_agg',
    'prodcue_LMDI_mutliplicative_plot_FOR_MULTIPLE_ECONOMIES_all_freight_agg',
    'produce_LMDI_additive_plot_FOR_MULTIPLE_ECONOMIES_road_agg',
    'produce_LMDI_additive_plot_FOR_MULTIPLE_ECONOMIES_all_agg'
    ]
    plot_multi_economy_plots(config, ECONOMY_IDs, economy_grouping_name, plots, colors_dict,  ADVANCE_BASE_YEAR_TO_OUTLOOK_BASE_YEAR=True, ONLY_AGG_OF_ALL=ONLY_AGG_OF_ALL)
#%%
#NOTE THAT WITH THE PREVIOUS_PROJECTION_FILE_DATE_ID THE FILE SHOULD BE SAVED IN C:\Users\finbar.maunsell\OneDrive - APERC\outlook 9th\Modelling\Sector models\Transport - results only\01_AUS/01_AUS_20240327_transport_energy_use.csv SO YOU CAN ALWAYS GRAB THAT AND PUT IT IN C:\Users\finbar.maunsell\github\transport_model_9th_edition\output_data\for_other_modellers\output_for_outlook_data_system IF YOU WANT TO MAKE SURE YOU'RE USING THAT FILE AND NOT A DIFFERENT VERSION WITH SAME DATE ID

# dashboard_creation_handler(config, True,'05_PRC', PREVIOUS_PROJECTION_FILE_DATE_ID='20240327')
# dashboard_creation_handler(config, True,'20_USA')
# dashboard_creation_handler(config, True,'15_PHL', PREVIOUS_PROJECTION_FILE_DATE_ID='20240327')
# dashboard_creation_handler(config, True,'03_CDA')#, 
# dashboard_creation_handler(config, True,'07_INA')#, PREVIOUS_PROJECTION_FILE_DATE_ID='20231101')
# dashboard_creation_handler(config, True,'09_ROK', PREVIOUS_PROJECTION_FILE_DATE_ID='20240117')
# dashboard_creation_handler(config, True,'18_CT', PREVIOUS_PROJECTION_FILE_DATE_ID='20240117')
# remove_old_dashboards(config, ECONOMIES_TO_SKIP=[], dashboard_name_id=' - high evs')

# setup_and_run_multi_economy_plots(config)
#'03_CDA','09_ROK', '18_CT', '05_PRC', '17_SGP', '21_VN', '15_PHL', '01_AUS', '10_MAS', '07_INA', '20_USA', '19_THA', '08_JPN'
# do for these once ive run it all
# dashboard_creation_handler(config, True,'03_CDA', PREVIOUS_PROJECTION_FILE_DATE_ID='20231101')
# dashboard_creation_handler(config, True,'09_ROK', PREVIOUS_PROJECTION_FILE_DATE_ID='20240117')
# dashboard_creation_handler(config, True,'18_CT', PREVIOUS_PROJECTION_FILE_DATE_ID='20240117')
# dashboard_creation_handler(config, True,'05_PRC', PREVIOUS_PROJECTION_FILE_DATE_ID='20240315')
# dashboard_creation_handler(config, True,'17_SGP', PREVIOUS_PROJECTION_FILE_DATE_ID='20240108')
# dashboard_creation_handler(config, True,'21_VN', PREVIOUS_PROJECTION_FILE_DATE_ID='20240327')
# dashboard_creation_handler(config, True,'15_PHL', PREVIOUS_PROJECTION_FILE_DATE_ID='20240529')
# # dashboard_creation_handler(config, True,'01_AUS', PREVIOUS_PROJECTION_FILE_DATE_ID='20240529')
# dashboard_creation_handler(config, True,'10_MAS', PREVIOUS_PROJECTION_FILE_DATE_ID='20240327')
# dashboard_creation_handler(config, True,'07_INA', PREVIOUS_PROJECTION_FILE_DATE_ID='20240327')
# # dashboard_creation_handler(config, True,'20_USA', PREVIOUS_PROJECTION_FILE_DATE_ID='20231101')
# dashboard_creation_handler(config, True,'19_THA', PREVIOUS_PROJECTION_FILE_DATE_ID='20231101')
# dashboard_creation_handler(config, True,'08_JPN', PREVIOUS_PROJECTION_FILE_DATE_ID='20231101')
#%%