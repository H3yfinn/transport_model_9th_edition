# #use this to create an easy to read table of the data needs for the model
# #will need to be really concise since we want to use this to communicate datawe are looking for to the data providers, as well as make it clear what data we have/havent got (not including the quality of the data we have, yet)


# #%%
# #set working directory as one folder back so that config works
# from datetime import datetime
# import os
# import re
# sys.path.append(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
# ###IMPORT GLOBAL VARIABLES FROM config.py
# import os
# import re
# sys.path.append(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
# import sys
# sys.path.append("\\config")

# import pandas as pd 
# import numpy as np
# import yaml
import time
# import datetime
# import shutil
# import sys
# import os 
# import re
# import plotly.express as px
# import plotly.io as pio
# import plotly.graph_objects as go
# import matplotlib
# import matplotlib.pyplot as plt
# ####Use this to load libraries and set variables. Feel free to edit that file as you need.


# #%%

# #impoort model concordances
# # all_df = pd.read_csv(config.root_dir + config.slash + 'intermediate_data\\computer_generated_concordances\\{}'.format(model_concordances_all_file_name))

# # general_df = pd.read_csv(config.root_dir + config.slash + 'intermediate_data\\computer_generated_concordances\\{}'.format(model_concordances_file_name))

# user_input_concordances = pd.read_csv(config.root_dir + config.slash + 'intermediate_data\\computer_generated_concordances\\{}'.format(model_concordances_user_input_and_growth_rates_file_name))
# BASE_YEAR_measure_concordances = pd.read_csv(config.root_dir + config.slash + 'intermediate_data\\computer_generated_concordances\\{}'.format(model_concordances_BASE_YEAR_measures_file_name))
# demand_side_fuel_mixing_concordances = pd.read_csv(config.root_dir + config.slash + 'intermediate_data\\computer_generated_concordances\\{}'.format(model_concordances_demand_side_fuel_mixing_file_name))
# supply_side_fuel_mixing_concordances = pd.read_csv(config.root_dir + config.slash + 'intermediate_data\\computer_generated_concordances\\{}'.format(model_concordances_supply_side_fuel_mixing_file_name))

# #%%
# #realistically we just want data for the base year and then for user inputs and growth rates plus fuel mixing, we would jsut estimate our own growth rates for future years

# #so just remove year column from all dfs and then remove duplicates (including base year limtis us, better just to ask for the latest avaialble data, whether or not that is one or more years of data)
# BASE_YEAR_measure_concordances = BASE_YEAR_measure_concordances.drop(columns = ['Year']).drop_duplicates()
# demand_side_fuel_mixing_concordances = demand_side_fuel_mixing_concordances.drop(columns = ['Year']).drop_duplicates()
# supply_side_fuel_mixing_concordances = supply_side_fuel_mixing_concordances.drop(columns = ['Year']).drop_duplicates()
# user_input_concordances = user_input_concordances.drop(columns = ['Year']).drop_duplicates()

# #%%
# #and remove scenario column from user input concordances and fuel mixing concordances
# user_input_concordances = user_input_concordances.drop(columns = ['Scenario'])
# demand_side_fuel_mixing_concordances = demand_side_fuel_mixing_concordances.drop(columns = ['Scenario'])
# supply_side_fuel_mixing_concordances = supply_side_fuel_mixing_concordances.drop(columns = ['Scenario'])

# #and remove meidum column from all since it is reaally just a helper column
# BASE_YEAR_measure_concordances = BASE_YEAR_measure_concordances.drop(columns = ['Medium'])
# demand_side_fuel_mixing_concordances = demand_side_fuel_mixing_concordances.drop(columns = ['Medium'])
# supply_side_fuel_mixing_concordances = supply_side_fuel_mixing_concordances.drop(columns = ['Medium'])
# user_input_concordances = user_input_concordances.drop(columns = ['Medium'])

# ########################################################
# #CATEGORICAL HIERARCHIES:
# #%%
# #now we want to print categorical hierarchys. such as how in the columns we have a hierarchy of: Transport Type > Vehicle Type > Drive
# # so for every unique value in the transport type column, we want to print all the unique values in the vehicle type column, and then all the unique values in the drive type column. And then format that nicely, in a kind of tree structure

# #lets try by using a sunburst diagram
# #drop ecconomy and measure cols 
# BASE_YEAR_measure_concordances = BASE_YEAR_measure_concordances.drop(columns = ['Economy', 'Measure']).drop_duplicates()
# demand_side_fuel_mixing_concordances = demand_side_fuel_mixing_concordances.drop(columns = ['Economy', 'Measure']).drop_duplicates()
# supply_side_fuel_mixing_concordances = supply_side_fuel_mixing_concordances.drop(columns = ['Economy', 'Measure']).drop_duplicates()
# user_input_concordances = user_input_concordances.drop(columns = ['Economy', 'Measure']).drop_duplicates()


# #remove nonspecified from all columns in 'Transport Type' which will remove it from 'Vehicle Type', 'Drive'
# BASE_YEAR_measure_concordances = BASE_YEAR_measure_concordances[~BASE_YEAR_measure_concordances['Transport Type'].isin(['nonspecified'])]
# demand_side_fuel_mixing_concordances = demand_side_fuel_mixing_concordances[~demand_side_fuel_mixing_concordances['Transport Type'].isin(['nonspecified'])]
# supply_side_fuel_mixing_concordances = supply_side_fuel_mixing_concordances[~supply_side_fuel_mixing_concordances['Transport Type'].isin(['nonspecified'])]
# user_input_concordances = user_input_concordances[~user_input_concordances['Transport Type'].isin(['nonspecified'])]


# #make Drive = None for all Vehicle Types in air ship and rail
# BASE_YEAR_measure_concordances.loc[BASE_YEAR_measure_concordances['Vehicle Type'].isin(['air', 'ship', 'rail']), 'Drive'] = None
# #remove duplicates
# # BASE_YEAR_measure_concordances = BASE_YEAR_measure_concordances.drop_duplicates()
# #%%
# #now plot for jsut one of the concordances
# import plotly.express as px
# df = BASE_YEAR_measure_concordances
# fig = px.sunburst(df, path=['Transport Type', 'Vehicle Type', 'Drive'])
# #make fig bigger
# fig.update_layout(margin = dict(t=0, l=0, r=0, b=0))

# fig.show()

# #save
# fig.write_html("plotting_output\\input_data_communication\\transport_type_vehicle_type_drive_sunburst.html")
# #%%

# ##########################################
# #MEASURES
# #we now want to communicate the different measures we observe in the data