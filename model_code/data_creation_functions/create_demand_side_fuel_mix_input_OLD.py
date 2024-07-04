#this will apply any fuel mixing on the demand side. It contains the use of different fule types for each drive type, for example, electricity vs oil in phev's, or even treating rail as a drive type, and splitting demand into electricity, coal and dieel rpoprtions. 
#This could include any mixing, even biofuels, but is intended for use from the perspective of the demand side only. If you do include biofuels in this mix, you will have to remove it from the supply side mixing.
#Once finished this will merge a fuel mixing dataframe onto the model output, by the Drive column, and apply the shares by doing that, resulting in a fuel column.
#this means that the supply side fuel mixing needs to occur after this script, because it will be merging on the fuel column.

#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
from .. import utility_functions
from ..plotting_functions import plot_user_input_data
from .. import archiving_scripts
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

#create fake user input for demand side fuel mixes using model concordances

def create_demand_side_fuel_mixing_input(config, ECONOMY_ID):
    """Could do with some fixing up but for now it works"""
    #load model concordances for filling in 
    model_concordances_fuels = pd.read_csv(config.root_dir + '\\' + 'intermediate_data\\computer_generated_concordances\\{}'.format(config.model_concordances_file_name_fuels))
    #filter for the Economy id
    model_concordances_fuels = model_concordances_fuels[model_concordances_fuels['Economy'] == ECONOMY_ID]

    
    #the process will run like:
    #load in fuel concrdacnes, filter for drive type and then pivot so each fuel is a column. then manually set the fuels columns to the shares you want. if a column is missing, it will be assumed to be 0. this allows for biofuels to be excluded and handled by the supply side fuel mixing.
    #first create a dummy value col for when pivoting
    model_concordances_fuels['dummy'] = np.nan

    #PHEV_g
    model_concordances_PHEVD = model_concordances_fuels.loc[(model_concordances_fuels['Drive'] == 'phev_d')]
    #make wide
    model_concordances_PHEVD = model_concordances_PHEVD.pivot(index=config.INDEX_COLS_NO_MEASURE, columns='Fuel', values='dummy').reset_index()
    #fill cols with values
    model_concordances_PHEVD['17_electricity'] = 0.5
    model_concordances_PHEVD['07_07_gas_diesel_oil'] = 0.5
    #fill na with 0
    model_concordances_PHEVD = model_concordances_PHEVD.fillna(0)
    #now melt so we have a tall dataframe
    model_concordances_PHEVD_melt = pd.melt(model_concordances_PHEVD, id_vars=config.INDEX_COLS_NO_MEASURE, var_name='Fuel', value_name='Demand_side_fuel_share')

    #PHEV ldv
    model_concordances_PHEVG = model_concordances_fuels.loc[(model_concordances_fuels['Drive'] == 'phev_g')]
    #make wide
    model_concordances_PHEVG = model_concordances_PHEVG.pivot(index=config.INDEX_COLS_NO_MEASURE, columns='Fuel', values='dummy').reset_index()
    #fill cols with values
    model_concordances_PHEVG['17_electricity'] = 0.5
    model_concordances_PHEVG['07_01_motor_gasoline'] = 0.5
    #fill na with 0
    model_concordances_PHEVG = model_concordances_PHEVG.fillna(0)
    #now melt so we have a tall dataframe
    model_concordances_PHEVG_melt = pd.melt(model_concordances_PHEVG, id_vars=config.INDEX_COLS_NO_MEASURE, var_name='Fuel', value_name='Demand_side_fuel_share')

    
    #CONCATENATE all
    demand_side_fuel_mixing = pd.concat([model_concordances_PHEVD_melt, model_concordances_PHEVG_melt], axis=0)#, model_concordances_BEV_melt,model_concordances_FCEV_melt,model_concordances_LPG_melt,model_concordances_CNG_melt,model_concordances_ICEG_melt,model_concordances_ICED_melt], axis=0)#model_concordances_rail_melt, model_concordances_air_melt, model_concordances_ship_melt,

    #remove any rows where demand side fuel share is 0 as they are just fuels where there is no use of the fuel
    demand_side_fuel_mixing = demand_side_fuel_mixing[demand_side_fuel_mixing['Demand_side_fuel_share'] != 0]
    
    do_this = False
    if do_this:
        #actually throw an errorhere because we want to double check its what we expect when we start using lcv's and iceg and so on
        raise ValueError('Check this with the updates youre making to the ice fuel splits')
        breakpoint()
        #include data for these economies for ldv, ices in freight. the daata can be the same as or other economies. This was done because we were missing that data. It would be good to reuturn to it 
        # '04_CHL', '10_MAS', '12_NZ', '13_PNG'
        #filter for the other economies
        ice_ldv_freight_econs = demand_side_fuel_mixing[~demand_side_fuel_mixing['Economy'].isin(['04_CHL', '10_MAS', '12_NZ', '13_PNG']) & (demand_side_fuel_mixing['Transport Type'] == 'freight') & (demand_side_fuel_mixing['Vehicle Type'] == 'lcv') & (demand_side_fuel_mixing['Drive'].isin(['ice_g','ice_d']))]
        #average it all by a;; the cols ecxcept economy
        ice_ldv_freight_econs = ice_ldv_freight_econs.groupby(['Date', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive',
            'Scenario', 'Frequency', 'Fuel']).mean().reset_index()
        #normalise all to 1
        ice_ldv_freight_econs['Demand_side_fuel_share'] = ice_ldv_freight_econs.groupby(['Date', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive',
            'Scenario', 'Frequency'])['Demand_side_fuel_share'].apply(lambda x: x/x.sum())
        ice_ldv_freight_econs_dummy = ice_ldv_freight_econs.copy()
        empty_ice_ldv_freight_econs = pd.DataFrame()
        #copy this for each of the other economies
        for econ in ['04_CHL', '10_MAS', '12_NZ', '13_PNG']:
            ice_ldv_freight_econs_dummy['Economy'] = econ
            empty_ice_ldv_freight_econs = pd.concat([empty_ice_ldv_freight_econs, ice_ldv_freight_econs_dummy], axis=0, ignore_index=True)
        #concatenate onto demand_side_fuel_mixing
        demand_side_fuel_mixing = pd.concat([demand_side_fuel_mixing, empty_ice_ldv_freight_econs], axis=0, ignore_index=True)

    
    #to handle years that are before the config.DEFAULT_BASE_YEAR, jsut carry the fuel shares backwards for 10 years
    data_base_minus_10 = demand_side_fuel_mixing.copy()
    data_base_minus_10 = data_base_minus_10[data_base_minus_10['Date'] == config.DEFAULT_BASE_YEAR+1]
    demand_side_fuel_mixing_minus_10 = pd.DataFrame()
    for year in range(config.DEFAULT_BASE_YEAR-10, config.DEFAULT_BASE_YEAR-1):
        data_base_minus_10['Date'] = year
        demand_side_fuel_mixing_minus_10 = pd.concat([demand_side_fuel_mixing_minus_10, data_base_minus_10], axis=0, ignore_index=True)
    #concat onto demand_side_fuel_mixing
    demand_side_fuel_mixing = pd.concat([demand_side_fuel_mixing, demand_side_fuel_mixing_minus_10], axis=0, ignore_index=True)

    #####################
    #save as user input csv
    
    demand_side_fuel_mixing.to_csv(config.root_dir + '\\' + 'intermediate_data\\model_inputs\\{}\\{}_demand_side_fuel_mixing.csv'.format(config.FILE_DATE_ID, ECONOMY_ID), index=False)
    plot_user_input_data.plot_demand_side_fuel_mixing(config, demand_side_fuel_mixing,ECONOMY_ID)
#%%

# create_demand_side_fuel_mixing_input(config)

#%%