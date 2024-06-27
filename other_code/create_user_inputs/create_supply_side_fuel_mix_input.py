#this will apply any fuel mixing on the supply side. This is currently only biofuel mixing but could include other fuel types in the future

#this will merge a fuel sharing dataframe onto the model output, by the fuel column, and apply the shares by doing that. There will be a new fuel column after this


#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
###IMPORT GLOBAL VARIABLES FROM config.py
import sys
sys.path.append("./config")
from config import *
####Use this to load libraries and set variables. Feel free to edit that file as you need.

#%%
#create fake user input for demand side fuel mixes using model concordances

#load model concordances
model_concordances = pd.read_csv('config/concordances/{}'.format(model_concordances_file_name_fuels))
#%%
#startwith the model concordances with fuel types, filter for each fuel type, and split it into biofuel and fuel type. have to do each fuel type separately depnding on the resulting biofuel mix.
#Remember this allows for the option of not splitting all diesel use into biofuels. you can set it so vehicle type doesnt equal rail for example
model_concordances_diesel = model_concordances.loc[(model_concordances['Fuel'] == '7_7_gas_diesel_oil')]
model_concordances_diesel['16_6_biodiesel'] = 0.05
model_concordances_diesel['7_7_gas_diesel_oil'] = 0.95
#now melt so we have a tall dataframe
model_concordances_diesel_melt = pd.melt(model_concordances_diesel, id_vars=['Scenario', 'Economy', 'Transport Type',  'Medium','Vehicle Type', 'Drive', 'Fuel', 'Year'], var_name='New_fuel', value_name='Supply_side_fuel_share')

model_concordances_petrol = model_concordances.loc[(model_concordances['Fuel'] == '7_1_motor_gasoline')]
model_concordances_petrol['16_5_biogasoline'] = 0.05
model_concordances_petrol['7_1_motor_gasoline'] = 0.95
#now melt so we have a tall dataframe
model_concordances_petrol_melt = pd.melt(model_concordances_petrol, id_vars=['Scenario', 'Economy', 'Transport Type',  'Medium','Vehicle Type', 'Drive', 'Fuel', 'Year'], var_name='New_fuel', value_name='Supply_side_fuel_share')

model_concordances_jet_fuel = model_concordances.loc[(model_concordances['Fuel'] == '7_x_jet_fuel')]
model_concordances_jet_fuel['16_7_bio_jet_kerosene'] = 0.05
model_concordances_jet_fuel['7_x_jet_fuel'] = 0.95
#now melt so we have a tall dataframe
model_concordances_jet_fuel_melt = pd.melt(model_concordances_jet_fuel, id_vars=['Scenario', 'Economy', 'Transport Type',  'Medium','Vehicle Type', 'Drive', 'Fuel', 'Year'], var_name='New_fuel', value_name='Supply_side_fuel_share')

model_concordances_avgas = model_concordances.loc[(model_concordances['Fuel'] == '7_2_aviation_gasoline')]
model_concordances_avgas['16_7_bio_jet_kerosene'] = 0.05
model_concordances_avgas['7_2_aviation_gasoline'] = 0.95
#now melt so we have a tall dataframe
model_concordances_avgas_melt = pd.melt(model_concordances_avgas, id_vars=['Scenario', 'Economy', 'Transport Type',  'Medium','Vehicle Type', 'Drive', 'Fuel', 'Year'], var_name='New_fuel', value_name='Supply_side_fuel_share')

#%%
#CONCATENATE all
model_concordances_all = pd.concat([model_concordances_petrol_melt, model_concordances_diesel_melt, model_concordances_jet_fuel_melt, model_concordances_avgas_melt])

#%%
#save as user input csv
model_concordances_all.to_csv('intermediate_data/model_inputs/{}/supply_side_fuel_mixing.csv'.format(config.FILE_DATE_ID), index=False)
#%%
