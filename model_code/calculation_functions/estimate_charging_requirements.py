#to do: simplify magnitudes, drop the aggregates from output, 
#quick script for now. will take in dictioanry of parameters such as:
#expected number of chargers per kw of kwh of ev battery capacity # this value can be arrived at by first using the following aprameters
#expected cahrgers per ev (given avg kwh of ev battery capacity)
#average kwh of ev battery capacity (also broken dwon by vehicle type and perhaps economy based on some kind of urbanisation metric - perhaps this will need another script to calculate)
#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
from os.path import join
from .. import utility_functions
from ..plotting_functions import plot_charging_graphs
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
####usae this to load libraries and set variables. Feel free to edit that file as you need
#%%
def prepare_inputs_for_estimating_charging_requirements(config, ECONOMY_ID):
    ##############################################

    df = pd.read_csv(os.path.join(config.root_dir,  'output_data', 'model_output', '{}_{}'.format(ECONOMY_ID, config.model_output_file_name)))
    #reaple any nan values with 0
    df = df.fillna(0)#bit of a temp measure, but will do for now
    
    # 2) Grab population density from input data
    def import_population_density_data(ECONOMY_ID):
        # Load population density data from Economy	EconomyName	Population Density (people per km²),	Urbanization (%)
        # #note the data is not actually from the transport data system but direct download from, ourworldindata.org
        density_data = pd.read_csv(os.path.join(config.root_dir, 'input_data','transport_data_system', 'pop_density.csv'))
        
        #drop EconomyName and then extract the row for the economy of interest as a key value pair
        population_density_data = density_data.drop(columns=['EconomyName', 'Urbanization (%)'])
        population_density_data = population_density_data.set_index('Economy')
        population_density = population_density_data.loc[ECONOMY_ID, 'Population Density (people per km2)']
        
        # 3) Grab urbanisation from input data
        urbanisation_data = density_data.drop(columns=['EconomyName', 'Population Density (people per km2)'])
        urbanisation_data = urbanisation_data.set_index('Economy')
        urbanisation = urbanisation_data.loc[ECONOMY_ID, 'Urbanization (%)']
        
        return population_density, urbanisation
    # breakpoint()
    population_density, urbanisation = import_population_density_data(ECONOMY_ID)
    ##############################################
    parameters = {
        # 'average_kwh_of_battery_capacity_by_vehicle_type': {'car': 50, 'bus': 100, '2w': 20, 'mt': 200, 'ht': 200, 'lt': 100, 'lcv': 100, 'suv': 80, 'car_phev': 50, 'bus_phev': 100, '2w_phev': 20, 'mt_phev': 200, 'ht_phev': 200, 'lt_phev': 100, 'lcv_phev': 100, 'suv_phev': 80},
            'average_kwh_of_battery_capacity_by_vehicle_type': {
                    # BEVs
                    'car': 50, 
                    'bus': 200, 
                    '2w': 5, 
                    'mt': 300, 
                    'ht': 500, 
                    'lt': 100, 
                    'lcv': 80, 
                    'suv': 70, 
                    # PHEVs (typically 25–50% of BEV capacity)
                    'car_phev': 12, 
                    'bus_phev': 60, 
                    '2w_phev': 1.5, 
                    'mt_phev': 80, 
                    'ht_phev': 150, 
                    'lt_phev': 25, 
                    'lcv_phev': 20, 
                    'suv_phev': 18
                },
                'stocks_magnitude': 1000000,#stocks are in millions
                'stocks_magnitude_name': 'millions',
                # 'kw_of_chargers_per_ev': 0.1,#based on iea graph in ev outlook 2023 (around page 48)
                'kw_of_chargers_per_kwh_of_battery': 0.048,#02,#Just 0.1/50  (kw_of_chargers_per_ev / average_kwh_of_battery_capacity_by_vehicle_type['car'])
                'average_kw_per_slow_charger': 11,#based on iea graph in ev outlook 2023 #assumed it didnt include fast chargers because technology isnt there yet for the vehicles that would need fast chargers
                # 'average_kw_per_charger': 60,#guess
                'average_kw_per_fast_charger': 200,#guess
                'average_ratio_of_fast_chargers_to_chargers': 0.05,#guess
                
                'public_charger_utilisation_rate': {'car': 1, 'bus': 0.1, '2w': 0.05, 'mt': 1, 'ht': 1, 'lt': 1, 'lcv': 1, 'suv': 1},
                # 'public_charger_utilisation_rate': {'car': 0.5, 'bus': 0.5, '2w': 0.3, 'mt': 1, 'ht': 1, 'lt': 0.5, 'lcv': 0.5, 'suv': 0.5},
                # 'public_charger_utilisation_rate': {'car': 1, 'bus': 1, '2w': 0.8, 'mt': 1, 'ht': 1.5, 'lt': 1, 'lcv': 1, 'suv': 1}, 
                
                'phev_charger_utilisation_rate': 0.15,# A U.S. Department of Energy report found that PHEVs accounted for only 10–20% of the usage at public Level 2 chargers, despite making up a larger share of the EV fleet in certain regions.
                # In the EU, PHEV users were found to use public chargers only 25% as often as BEV users.
                #note that both of these could be partly because of the smaller size of the phev fleet, but also because they are more likely to be charged at home
                
                #vehicle type specific. ones that are commercial and expected to be used in urban areas may have lower rates because they might be charged at depots. then private vehicles also might have lower rates because they might be charged at home as they have lower daily mileage.. although i think this might be encouraging too much complexity. i will make it so that most vehicles use public chargers at a ratio of 1 except those who obviously dont (e.g. 2w, bus)
                #im not 100% sure whether i should assume that heavy trucks use public chargers at all, but i think we should at least assume that what they use is what people expect when they think of public chargers?
                'fast_charger_share': {'car': 0.3, 'bus': 0.5, '2w': 0, 'mt': 0.8, 'ht': 0.8, 'lt': 0.5, 'lcv': 0.5, 'suv': 0.3},
                #'fast_charger_share': {'car': 1, 'bus': 1, '2w': 0.8, 'mt': 1, 'ht': 1.5, 'lt': 1, 'lcv': 1, 'suv': 1},
                
    }
    # 4) Incorporate population density by scaling the main charging parameter
    pop_density_multiplier = get_pop_density_multiplier(population_density, urbanisation)
    parameters['kw_of_chargers_per_kwh_of_battery'] *= pop_density_multiplier
    
    colors_dict = {'2w': 'pink', 'car': 'blue', 'suv': 'teal', 'lt': 'green', 'bus': 'purple', 'ht': 'red', 'mt': 'orange', 'lcv': 'brown'}
    INCORPORATE_UTILISATION_RATE = True
    
    return df, parameters, colors_dict, INCORPORATE_UTILISATION_RATE

def get_pop_density_multiplier(pop_density, urbanisation_rate):
    """
    Returns a single multiplier to scale up/down the
    expected chargers per kWh of battery, based on population density.
    Adjust thresholds and multipliers as you see fit!
    """
    #first times by urbanisation rate
    pop_density = pop_density * (urbanisation_rate/100)
    if pop_density < 50:
        # Lower density => fewer public chargers needed per kWh
        return 0.8
    elif 50 <= pop_density < 300:
        # Medium density => baseline
        return 1.0
    else:
        # High density => more public chargers per kWh since less room fr home charging
        return 1.2
#%%

##############################################    

def estimate_kwh_of_ev_battery_capacity(config, df, parameters):
    #take in the number of evs for each vehicle type in an economy and calcualte the total kwh of battery capacity for that economy, given the number of evs and the average kwh of battery capacity for each vehicle type
    #where drive is phev cahnge the vehjicle type to have _phev at the end so we can set the average kwh of battery capacity for phevs to be different to that of bevs
    
    evs =  df.loc[(df['Drive'].isin(['phev_g', 'phev_d', 'bev']))].copy()
    evs['Drive'] = np.where(evs['Drive'].str.contains('phev'), 'phev', evs['Drive'])
    evs['Vehicle Type'] = np.where(evs['Drive'].str.contains('phev'), evs['Vehicle Type']+'_phev', evs['Vehicle Type'])
    
    #quickly sum by vehicle type and drive since we grounped phev_d and phev_g together
    evs = evs.groupby(['Economy','Date','Scenario','Drive','Vehicle Type']).sum().reset_index()
    
    #map parameters['average_kwh_of_battery_capacity_by_vehicle_type'] to the evs dataframe by the Vehicle Type column
    evs['average_kwh_of_battery_capacity_by_vehicle_type'] = evs['Vehicle Type'].map(parameters['average_kwh_of_battery_capacity_by_vehicle_type'])
    #calculate the kwh of battery capacity for all evs in the economy, by vehicle type
    evs['kwh_of_battery_capacity'] = evs['average_kwh_of_battery_capacity_by_vehicle_type']*evs['Stocks'] * parameters['stocks_magnitude']

    return evs[['Economy','Date','Scenario', 'Drive', 'Vehicle Type','Stocks', 'kwh_of_battery_capacity','average_kwh_of_battery_capacity_by_vehicle_type']].drop_duplicates()

def incorporate_utilisation_rates(config, total_kwh_of_battery_capacity, parameters):
    """
    Note that this function will not change the total number of chargers, it will just change the number of chargers for each vehicle type, as it distributes the chargers based on the utilisation rates (for phevs and bevs). This is important because we have a parameter which is an estimate of the number of chargers per kwh of battery capacity, but we also have an estimate for the utilisation rate of public chargers for each vehicle type. These two cannot be used in a calcualtion at the same time without changing their effect; i.e. if you applied this utilisation rate then the number of chargers per kwh of battery will be lower in the final calculation than what we wanted. 
    
    Inevitably this will result in a higher number of chargers per kwh for a certain vehicle type, but lwoer for another. That is ok - the total number of chargers will remain the same and having a higher number of chargers per kwh for a certain vehicle type is not a problem, just means they will charge publicly instead of privately more often."""
    total_kwh_of_battery_capacity['public_charger_utilisation_rate'] = np.where(total_kwh_of_battery_capacity['Drive']=='phev', parameters['phev_charger_utilisation_rate'], 1)
    #drop _phev from name so we can map the public charger utilisation rate to the vehicle type
    total_kwh_of_battery_capacity['Vehicle Type'] = total_kwh_of_battery_capacity['Vehicle Type'].str.replace('_phev', '')
    
    #map the public charger utilisation rate to the vehicle type but also times it by the public charger utilisation rate for that vehicle type in case it is a phev
    total_kwh_of_battery_capacity['public_charger_utilisation_rate'] = total_kwh_of_battery_capacity['public_charger_utilisation_rate'] * total_kwh_of_battery_capacity['Vehicle Type'].map(parameters['public_charger_utilisation_rate'])
    
    total_kwh_of_battery_capacity['kw_of_chargers_WITHOUT_UTILISATION_RATE'] = total_kwh_of_battery_capacity['kwh_of_battery_capacity']*parameters['kw_of_chargers_per_kwh_of_battery']
    total_kwh_of_battery_capacity['sum_of_kw_of_chargers_WITHOUT_UTILISATION_RATE'] = total_kwh_of_battery_capacity.groupby(['Economy','Date','Scenario'])['kw_of_chargers_WITHOUT_UTILISATION_RATE'].transform('sum')
    
    total_kwh_of_battery_capacity['kw_of_chargers_WITH_UTILISATION_RATE'] = total_kwh_of_battery_capacity['kwh_of_battery_capacity']*parameters['kw_of_chargers_per_kwh_of_battery']*total_kwh_of_battery_capacity['public_charger_utilisation_rate']
    total_kwh_of_battery_capacity['sum_of_kw_of_chargers_WITH_UTILISATION_RATE'] = total_kwh_of_battery_capacity.groupby(['Economy','Date','Scenario'])['kw_of_chargers_WITH_UTILISATION_RATE'].transform('sum')
    
    #CALC PROPORTIONAL DIFFERENCE
    total_kwh_of_battery_capacity['proportional_difference'] = total_kwh_of_battery_capacity['sum_of_kw_of_chargers_WITHOUT_UTILISATION_RATE']/total_kwh_of_battery_capacity['sum_of_kw_of_chargers_WITH_UTILISATION_RATE']
    
    #RECALCAULTE kw_of_chargers_WITH_UTILISATION_RATE BUT TIMES ALL BY THE PROPORTIONAL DIFFERENCE SO THE EFFECT OF THE UTILISATION RATE IS INCORPORATED BUT DOESNT CHANGE THE TOTAL!
    total_kwh_of_battery_capacity['kw_of_chargers'] = total_kwh_of_battery_capacity['kw_of_chargers_WITH_UTILISATION_RATE'] * total_kwh_of_battery_capacity['proportional_difference']
    
    #check that the sum of kw_of_chargers is the same as the sum of kw_of_chargers_WITHOUT_UTILISATION_RATE
    total_kwh_of_battery_capacity['sum_of_kw_of_chargers'] = total_kwh_of_battery_capacity.groupby(['Economy','Date','Scenario'])['kw_of_chargers'].transform('sum')
    if abs(total_kwh_of_battery_capacity['sum_of_kw_of_chargers'].sum() - total_kwh_of_battery_capacity['sum_of_kw_of_chargers_WITHOUT_UTILISATION_RATE'].sum()) > 0.0001:
        breakpoint()
        raise ValueError('The sum of kw_of_chargers is not the same as the sum of kw_of_chargers_WITHOUT_UTILISATION_RATE')
        # raise ValueError('The sum of kw_of_chargers is not the same as the sum of kw_of_chargers_WITHOUT_UTILISATION_RATE')
    
    #DROP COLUMNS
    total_kwh_of_battery_capacity.drop(columns=['kw_of_chargers_WITHOUT_UTILISATION_RATE','sum_of_kw_of_chargers_WITHOUT_UTILISATION_RATE','kw_of_chargers_WITH_UTILISATION_RATE','sum_of_kw_of_chargers_WITH_UTILISATION_RATE','proportional_difference'], inplace=True)
    
    return total_kwh_of_battery_capacity

################################################################

def estimate_kw_of_required_chargers(config, ECONOMY_ID):
    """

    Args:
        config (_type_): _description_
        ECONOMY_ID (_type_): _description_
    """
    #MAIN FUNCTION
    df, parameters, colors_dict, INCORPORATE_UTILISATION_RATE = prepare_inputs_for_estimating_charging_requirements(config, ECONOMY_ID)
    total_kwh_of_battery_capacity = estimate_kwh_of_ev_battery_capacity(config, df, parameters)
    
    #extract stocks so we can plot it later too
    stocks = total_kwh_of_battery_capacity[['Economy','Date','Scenario','Vehicle Type','Drive', 'Stocks']].drop_duplicates()
    #rename vehicle type so it doesnt have phev at the end
    stocks['Vehicle Type'] = stocks['Vehicle Type'].str.replace('_phev', '')
    #now we can use this to estimate the number of chargers required given the expected number of chargers per kw of kwh of ev battery capacity
    
    #by vehicle type: (will use a public_charger_utilisation_rate for each vehicle type)    
    
    total_kwh_of_battery_capacity = incorporate_utilisation_rates(config, total_kwh_of_battery_capacity, parameters)
    
    #estiamte number f slow and fast chargers needed using fast_charger_share
    #first map on the fast_charger_share data by vheicle type
    total_kwh_of_battery_capacity['fast_charger_share'] = total_kwh_of_battery_capacity['Vehicle Type'].map(parameters['fast_charger_share'])
    #now times the number_of_chargers by the fast_charger_share to get the number of fast chargers needed, then calc the number of slow chargers needed as remaining chargers. Do this to kw of chargers, then calcualte the number of chargers needed by using average_kw_per_slow_charger and average_kw_per_fast_charger
    total_kwh_of_battery_capacity['slow_kw_of_chargers'] = total_kwh_of_battery_capacity['kw_of_chargers']*(1-total_kwh_of_battery_capacity['fast_charger_share'])
    total_kwh_of_battery_capacity['fast_kw_of_chargers'] = total_kwh_of_battery_capacity['kw_of_chargers']*total_kwh_of_battery_capacity['fast_charger_share']
    
    total_kwh_of_battery_capacity['average_kw_per_slow_charger'] = parameters['average_kw_per_slow_charger']
    total_kwh_of_battery_capacity['average_kw_per_fast_charger'] = parameters['average_kw_per_fast_charger']
    total_kwh_of_battery_capacity['slow_chargers'] = total_kwh_of_battery_capacity['slow_kw_of_chargers']/parameters['average_kw_per_slow_charger']
    total_kwh_of_battery_capacity['fast_chargers'] = total_kwh_of_battery_capacity['fast_kw_of_chargers']/parameters['average_kw_per_fast_charger']
    
    total_kwh_of_battery_capacity = total_kwh_of_battery_capacity[['Economy','Date','Scenario','Vehicle Type','Drive', 'slow_chargers','fast_chargers','Stocks','kwh_of_battery_capacity','kw_of_chargers','fast_charger_share','average_kwh_of_battery_capacity_by_vehicle_type','average_kw_per_slow_charger','average_kw_per_fast_charger','slow_kw_of_chargers','fast_kw_of_chargers', 'public_charger_utilisation_rate']].drop_duplicates()
    
    #rename stocks to stocks_{stocks_magnitude_name}
    total_kwh_of_battery_capacity.rename(columns={'Stocks':'Stocks_'+parameters['stocks_magnitude_name']}, inplace=True)
    #lastly, sort by date, scenario and vehicle type
    total_kwh_of_battery_capacity = total_kwh_of_battery_capacity.sort_values(by=['Date','Scenario','Vehicle Type','Drive'])
    
    
    # #there are nas with 0 in phev col wehre vehicle type is 2w, change that:
    # total_kwh_of_battery_capacity['Stocks_phev'] = np.where((total_kwh_of_battery_capacity['Stocks_phev'].isna()) & (total_kwh_of_battery_capacity['Vehicle Type']=='2w'), 0, total_kwh_of_battery_capacity['Stocks_phev'])
    
    #save data to csv for use in \\output_data\\for_other_modellers/charging
    total_kwh_of_battery_capacity.to_csv(os.path.join(config.root_dir,  f'output_data', 'for_other_modellers', 'charging', f'{ECONOMY_ID}_estimated_number_of_chargers.csv'), index=False)
    
#%%

def estimate_ev_stocks_given_chargers(config, df, economy, date, scenario, parameters, number_of_slow_chargers=0, number_of_fast_chargers=0, number_of_chargers=0):
    #use a value for the number of chargers for a specified economy, date and scenario to estimate the number of evs in that economy, date and scenario.
    #we can use the previous forecasts to estimate the portion of evs in each vehicle type too.
    #also useful for other forecasts of evs by other modellers 
    
    #note it assumes all vehicles are bevs
    
    #calcualte average kw of charger capacity given the different kw of fast and non-fast chargers:
    if number_of_chargers == 0:
        kw_of_charger_capacity = (number_of_slow_chargers*parameters['average_kw_per_slow_charger']+number_of_fast_chargers*parameters['average_kw_per_fast_charger'])/(number_of_slow_chargers+number_of_fast_chargers)
        kw_of_fast_charger_capacity = number_of_fast_chargers*parameters['average_kw_per_fast_charger']
        kw_of_slow_charger_capacity = number_of_slow_chargers*parameters['average_kw_per_slow_charger']
        number_of_chargers = kw_of_charger_capacity / parameters['average_kw_per_charger']
    elif (number_of_chargers > 0) & (number_of_slow_chargers == 0):
        kw_of_charger_capacity = number_of_chargers*parameters['average_kw_per_charger']
        kw_of_fast_charger_capacity = 0
        kw_of_slow_charger_capacity = 0
        number_of_chargers = number_of_chargers
    else:
        raise ValueError('You must provide either a value for number_of_chargers or number_of_slow_chargers and number_of_fast_chargers, but not both')
    
    #calcualte portion of bev stocks in each vehicle type:
    #get stocks for each vehicle type
    stocks = df[(df['Drive']=='bev') & (df['Economy']==economy) & (df['Date']==date) & (df['Scenario']==scenario)]
    #get kwh of those stocks. first map on average_kwh_of_battery_capacity_by_vehicle_type
    stocks['average_kwh_of_battery_capacity_by_vehicle_type'] = stocks['Vehicle Type'].map(parameters['average_kwh_of_battery_capacity_by_vehicle_type'])
    stocks['kwh_of_battery_capacity'] = stocks['Stocks']*stocks['average_kwh_of_battery_capacity_by_vehicle_type'] * parameters['stocks_magnitude']
    
    stocks['sum_of_kwh_of_battery_capacity'] = stocks['kwh_of_battery_capacity'].sum()
    #calculate portion of stocks for each vehicle type, adjsuted by the ?normalised? uitlisation rate of each vehicle type (so the sum of stocks remains the same but some of the stocks are shifted to account for the utilisation rate)
    stocks['portion_of_stocks_kwh_of_battery_capacity'] = stocks['kwh_of_battery_capacity']/stocks['sum_of_kwh_of_battery_capacity']
    
    if INCORPORATE_UTILISATION_RATE:
        stocks['public_charger_utilisation_rate'] = stocks['Vehicle Type'].map(parameters['public_charger_utilisation_rate'])
        #just times the portuin of stocks by utiliosation and then normalise to 1.
        stocks['portion_of_stocks_kwh_of_battery_capacity'] = stocks['portion_of_stocks_kwh_of_battery_capacity']*stocks['public_charger_utilisation_rate']
        stocks['portion_of_stocks_kwh_of_battery_capacity'] = stocks['portion_of_stocks_kwh_of_battery_capacity']/stocks['portion_of_stocks_kwh_of_battery_capacity'].sum()
        #check that the sum of the portion of stocks is 1
        
        if abs(1- stocks['portion_of_stocks_kwh_of_battery_capacity'].sum()) > 0.0001:
            raise ValueError('The sum of the portion of stocks is not 1')
        #drop the sum of stocks column and the utilisation rate column
        # stocks = stocks.drop(columns=['public_charger_utilisation_rate'])
    
    #calcualte expected kwh of battery capacity then split this by vehicle type using the portion of stocks
    stocks['sum_of_kwh_of_battery_capacity'] = kw_of_charger_capacity/parameters['kw_of_chargers_per_kwh_of_battery']
    stocks['kwh_of_battery_capacity'] = stocks['sum_of_kwh_of_battery_capacity']*stocks['portion_of_stocks_kwh_of_battery_capacity']
    
    #calcualte stocks of each vehicle type using the expected kwh of battery capacity and the average kwh of battery capacity for each vehicle type
    stocks['average_kwh_of_battery_capacity'] = stocks['Vehicle Type'].map(parameters['average_kwh_of_battery_capacity_by_vehicle_type'])
    
    stocks['stocks'] = (stocks['kwh_of_battery_capacity']/stocks['average_kwh_of_battery_capacity']).round(2)
    stocks['total_stocks'] = stocks['stocks'].sum()
    
    stocks['number_of_chargers'] = number_of_chargers
    stocks['number_of_fast_chargers'] = number_of_fast_chargers
    stocks['number_of_slow_chargers'] = number_of_slow_chargers
    
    stocks['kw_of_charger_capacity'] = kw_of_charger_capacity
    stocks['kw_of_fast_charger_capacity'] = kw_of_fast_charger_capacity
    stocks['kw_of_slow_charger_capacity'] = kw_of_slow_charger_capacity
    
    #quickly estiamte the expected number of chargers needed for each vehicle type based on the proportion of stocks value:
    stocks['number_of_chargers_by_vehicle_type'] = stocks['number_of_chargers']*stocks['portion_of_stocks_kwh_of_battery_capacity']
    stocks['kw_of_chargers_by_vehicle_type'] = stocks['kw_of_charger_capacity']*stocks['portion_of_stocks_kwh_of_battery_capacity']
    
    ev_stocks_and_chargers = stocks[['Economy','Date','Scenario','Vehicle Type',"Transport Type",'kwh_of_battery_capacity', 'sum_of_kwh_of_battery_capacity','stocks', 'total_stocks', 'portion_of_stocks_kwh_of_battery_capacity','number_of_chargers','number_of_fast_chargers','number_of_slow_chargers','kw_of_charger_capacity','kw_of_fast_charger_capacity','kw_of_slow_charger_capacity','number_of_chargers_by_vehicle_type','kw_of_chargers_by_vehicle_type', 'public_charger_utilisation_rate']].drop_duplicates()
    return ev_stocks_and_chargers

# %%

#%%
# calculate_evs_given_chargers = False 
# if calculate_evs_given_chargers:
#     economy= '08_JPN'
#     date=2030
#     scenario='Target'
#     number_of_fast_chargers = 4000
#     number_of_slow_chargers = 150000 - number_of_fast_chargers
#     number_of_chargers = 0
    
#     df, parameters, colors_dict, INCORPORATE_UTILISATION_RATE = prepare_inputs_for_estimating_charging_requirements(config, ECONOMY_ID=economy)
    
#     ev_stocks_and_chargers = estimate_ev_stocks_given_chargers(config, df, economy, date, scenario, parameters, number_of_slow_chargers=number_of_slow_chargers, number_of_fast_chargers=number_of_fast_chargers, number_of_chargers=number_of_chargers)
    
#     plot_charging_graphs.plot_required_evs(config, ev_stocks_and_chargers,colors_dict, economy, date, scenario)
     
        

#%%
