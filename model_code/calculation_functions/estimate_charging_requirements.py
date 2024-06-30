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
current_working_dir = os.getcwd()
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir =  "\\\\?\\" + re.split('transport_model_9th_edition', script_dir)[0] + 'transport_model_9th_edition'
from .. import utility_functions
from .. import config
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

def prepare_inputs_for_estimating_charging_requirements(ECONOMY_ID):
    ##############################################

    df = pd.read_csv(root_dir + '\\' + 'output_data\\model_output\\{}_{}'.format(ECONOMY_ID,config.model_output_file_name))
    #reaple any nan values with 0
    df = df.fillna(0)#bit of a temp measure, but will do for now
    ##############################################
    parameters = {'average_kwh_of_battery_capacity_by_vehicle_type': {'car': 50, 'bus': 100, '2w': 20, 'mt': 200, 'ht': 200, 'lt': 100, 'lcv': 100, 'suv': 80},
                'stocks_magnitude': 1000000,#stocks are in millions
                'stocks_magnitude_name': 'millions',
                'expected_kw_of_chargers_per_ev': 0.1,#based on iea graph in ev outlook 2023 (around page 48)
                'expected_kw_of_chargers_per_kwh_of_battery': 0.002,#Just 0.1/50  (expected_kw_of_chargers_per_ev / average_kwh_of_battery_capacity_by_vehicle_type['car'])
                'average_kw_per_non_fast_charger': 50,#based on iea graph in ev outlook 2023 #assumed it didnt include fast chargers because technology isnt there yet for the vehicles that would need fast chargers
                'average_kw_per_charger': 60,#guess
                'average_kw_per_fast_charger': 200,#guess
                'average_ratio_of_fast_chargers_to_chargers': 0.05,#guess
                'public_charger_utilisation_rate': {'car': 0.5, 'bus': 0.5, '2w': 0.3, 'mt': 1, 'ht': 1, 'lt': 0.5, 'lcv': 0.5, 'suv': 0.5},
                # 'public_charger_utilisation_rate': {'car': 1, 'bus': 1, '2w': 0.8, 'mt': 1, 'ht': 1.5, 'lt': 1, 'lcv': 1, 'suv': 1}, 
                #vehicle type specific. ones that are commercial and expected to be used in urban areas may have lower rates because they might be charged at depots. then private vehicles also might have lower rates because they might be charged at home as they have lower daily mileage
                #im not 100% sure whether i should assume that heavy trucks use public chargers at all, but i think we should at least assume that what they use is what people expect when they think of public chargers?
                'fast_charger_utilisation_rate': {'car': 0.2, 'bus': 0.2, '2w': 0, 'mt': 1, 'ht': 1, 'lt': 0.5, 'lcv': 0.5, 'suv': 0.2},
                #'fast_charger_utilisation_rate': {'car': 1, 'bus': 1, '2w': 0.8, 'mt': 1, 'ht': 1.5, 'lt': 1, 'lcv': 1, 'suv': 1},
                
    }
    colors_dict = {'2w': 'pink', 'car': 'blue', 'suv': 'teal', 'lt': 'green', 'bus': 'purple', 'ht': 'red', 'mt': 'orange', 'lcv': 'brown'}
    INCORPORATE_UTILISATION_RATE = True
    
    return df, parameters, colors_dict, INCORPORATE_UTILISATION_RATE
#%%
##############################################
def estimate_kwh_of_ev_battery_capacity(df, parameters):
    #take in the number of evs for each vehicle type in an economy and calcualte the total kwh of battery capacity for that economy, given the number of evs and the average kwh of battery capacity for each vehicle type
    evs = df.loc[(df['Drive']=='bev')].copy()
    evs['sum_of_stocks'] = evs.groupby(['Economy','Date','Scenario'])['Stocks'].transform('sum')
    
    #map parameters['average_kwh_of_battery_capacity_by_vehicle_type'] to the evs dataframe by the Vehicle Type column
    evs['average_kwh_of_battery_capacity_by_vehicle_type'] = evs['Vehicle Type'].map(parameters['average_kwh_of_battery_capacity_by_vehicle_type'])
    #calculate the kwh of battery capacity for all evs in the economy, by vehicle type
    evs['kwh_of_battery_capacity'] = evs['average_kwh_of_battery_capacity_by_vehicle_type']*evs['Stocks'] * parameters['stocks_magnitude']
    # #calcualte  kwh_of_battery_capacity by economy, date, scenario and vehicle type
    # evs['kwh_of_battery_capacity'] = evs.groupby(['Economy','Date','Scenario','Vehicle Type'])['kwh_of_battery_capacity'].transform('sum')
    #create sum of total_kwh_of_battery_capacity by economy, date, scenario 
    evs['sum_of_kwh_of_battery_capacity'] = evs.groupby(['Economy','Date','Scenario'])['kwh_of_battery_capacity'].transform('sum')
    
    return evs[['Economy','Date','Scenario','Vehicle Type','Stocks', 'sum_of_stocks','kwh_of_battery_capacity','sum_of_kwh_of_battery_capacity','average_kwh_of_battery_capacity_by_vehicle_type']].drop_duplicates()

def incorporate_utilisation_rate(total_kwh_of_battery_capacity, parameters):
    """ note that this function will not change the total number of chargers, it will just change the number of chargers for each vehicle type, as it distributes the chargers based on the utilisation rate."""
    total_kwh_of_battery_capacity['public_charger_utilisation_rate'] = total_kwh_of_battery_capacity['Vehicle Type'].map(parameters['public_charger_utilisation_rate'])
    
    total_kwh_of_battery_capacity['expected_kw_of_chargers_WITHOUT_UTILISATION_RATE'] = total_kwh_of_battery_capacity['kwh_of_battery_capacity']*parameters['expected_kw_of_chargers_per_kwh_of_battery']
    total_kwh_of_battery_capacity['sum_of_expected_kw_of_chargers_WITHOUT_UTILISATION_RATE'] = total_kwh_of_battery_capacity.groupby(['Economy','Date','Scenario'])['expected_kw_of_chargers_WITHOUT_UTILISATION_RATE'].transform('sum')
    
    total_kwh_of_battery_capacity['expected_kw_of_chargers_WITH_UTILISATION_RATE'] = total_kwh_of_battery_capacity['kwh_of_battery_capacity']*parameters['expected_kw_of_chargers_per_kwh_of_battery']*total_kwh_of_battery_capacity['public_charger_utilisation_rate']
    total_kwh_of_battery_capacity['sum_of_expected_kw_of_chargers_WITH_UTILISATION_RATE'] = total_kwh_of_battery_capacity.groupby(['Economy','Date','Scenario'])['expected_kw_of_chargers_WITH_UTILISATION_RATE'].transform('sum')
    
    #CALC PROPORTIONAL DIFFERENCE
    total_kwh_of_battery_capacity['proportional_difference'] = total_kwh_of_battery_capacity['sum_of_expected_kw_of_chargers_WITHOUT_UTILISATION_RATE']/total_kwh_of_battery_capacity['sum_of_expected_kw_of_chargers_WITH_UTILISATION_RATE']
    
    #RECALCAULTE expected_kw_of_chargers_WITH_UTILISATION_RATE BUT TIMES ALL BY THE PROPORTIONAL DIFFERENCE SO THE EFFECT OF THE UTILISATION RATE IS INCORPORATED BUT DOESNT CHANGE THE TOTAL!
    total_kwh_of_battery_capacity['expected_kw_of_chargers'] = total_kwh_of_battery_capacity['expected_kw_of_chargers_WITH_UTILISATION_RATE'] * total_kwh_of_battery_capacity['proportional_difference']
    
    #check that the sum of expected_kw_of_chargers is the same as the sum of expected_kw_of_chargers_WITHOUT_UTILISATION_RATE
    total_kwh_of_battery_capacity['sum_of_expected_kw_of_chargers'] = total_kwh_of_battery_capacity.groupby(['Economy','Date','Scenario'])['expected_kw_of_chargers'].transform('sum')
    if abs(total_kwh_of_battery_capacity['sum_of_expected_kw_of_chargers'].sum() - total_kwh_of_battery_capacity['sum_of_expected_kw_of_chargers_WITHOUT_UTILISATION_RATE'].sum()) > 0.0001:
        breakpoint()
        #if date isnt 24 october then fail
        if datetime.datetime.today().strftime('%d-%m') != '25-10':
            raise ValueError('The sum of expected_kw_of_chargers is not the same as the sum of expected_kw_of_chargers_WITHOUT_UTILISATION_RATE')
        # raise ValueError('The sum of expected_kw_of_chargers is not the same as the sum of expected_kw_of_chargers_WITHOUT_UTILISATION_RATE')
    
    #DROP COLUMNS
    total_kwh_of_battery_capacity.drop(columns=['expected_kw_of_chargers_WITHOUT_UTILISATION_RATE','sum_of_expected_kw_of_chargers_WITHOUT_UTILISATION_RATE','expected_kw_of_chargers_WITH_UTILISATION_RATE','sum_of_expected_kw_of_chargers_WITH_UTILISATION_RATE','proportional_difference'], inplace=True)
    
    return total_kwh_of_battery_capacity

################################################################

def estimate_kw_of_required_chargers(ECONOMY_ID):
    #MAIN FUNCTION
    df, parameters, colors_dict, INCORPORATE_UTILISATION_RATE = prepare_inputs_for_estimating_charging_requirements(ECONOMY_ID)
    
    total_kwh_of_battery_capacity = estimate_kwh_of_ev_battery_capacity(df, parameters)
    #now we can use this to estimate the number of chargers required given the expected number of chargers per kw of kwh of ev battery capacity

    # total_kwh_of_battery_capacity = estimate_kw_of_required_chargers(total_kwh_of_battery_capacity, parameters)
    #calcualte this for each vehicle type and then sum as a total for each economy, date and scenario
    #do this using the number of kwh of battery capacity needed per kw of charger capacity
    
    #by vehicle type: (will use a public_charger_utilisation_rate for each vehicle type)    
    if INCORPORATE_UTILISATION_RATE:
        #note that the utilisation rate wont change the total chargers, it jsut changes what vehicles use the chargers.
        total_kwh_of_battery_capacity = incorporate_utilisation_rate(total_kwh_of_battery_capacity, parameters)
    else:
        total_kwh_of_battery_capacity['expected_kw_of_chargers'] = total_kwh_of_battery_capacity['kwh_of_battery_capacity']*parameters['expected_kw_of_chargers_per_kwh_of_battery']
    
        total_kwh_of_battery_capacity['sum_of_expected_kw_of_chargers'] = total_kwh_of_battery_capacity.groupby(['Economy','Date','Scenario'])['expected_kw_of_chargers'].transform('sum')
    
    #then create sum of expected_number_of_chargers by economy, date, scenario
    total_kwh_of_battery_capacity['average_kw_per_charger'] = parameters['average_kw_per_charger']
    total_kwh_of_battery_capacity['expected_number_of_chargers'] = total_kwh_of_battery_capacity['expected_kw_of_chargers']/total_kwh_of_battery_capacity['average_kw_per_charger']
    total_kwh_of_battery_capacity['sum_of_expected_number_of_chargers'] = total_kwh_of_battery_capacity.groupby(['Economy','Date','Scenario'])['expected_number_of_chargers'].transform('sum')
    
    #estiamte number f slow and fast chargers needed using fast_charger_utilisation_rate
    #first map on the fast_charger_utilisation_rate data by vheicle type
    total_kwh_of_battery_capacity['fast_charger_utilisation_rate'] = total_kwh_of_battery_capacity['Vehicle Type'].map(parameters['fast_charger_utilisation_rate'])
    #now times the expected_number_of_chargers by the fast_charger_utilisation_rate to get the number of fast chargers needed, then calc the number of slow chargers needed as remaining chargers. Do this to kw of chargers, then calcualte the number of chargers needed by using average_kw_per_non_fast_charger and average_kw_per_fast_charger
    total_kwh_of_battery_capacity['slow_kw_of_chargers_needed'] = total_kwh_of_battery_capacity['expected_kw_of_chargers']*(1-total_kwh_of_battery_capacity['fast_charger_utilisation_rate'])
    total_kwh_of_battery_capacity['fast_kw_of_chargers_needed'] = total_kwh_of_battery_capacity['expected_kw_of_chargers']*total_kwh_of_battery_capacity['fast_charger_utilisation_rate']
    
    total_kwh_of_battery_capacity['average_kw_per_non_fast_charger'] = parameters['average_kw_per_non_fast_charger']
    total_kwh_of_battery_capacity['average_kw_per_fast_charger'] = parameters['average_kw_per_fast_charger']
    total_kwh_of_battery_capacity['slow_chargers_needed'] = total_kwh_of_battery_capacity['slow_kw_of_chargers_needed']/parameters['average_kw_per_non_fast_charger']
    total_kwh_of_battery_capacity['fast_chargers_needed'] = total_kwh_of_battery_capacity['fast_kw_of_chargers_needed']/parameters['average_kw_per_fast_charger']
    
    #calculate sums
    total_kwh_of_battery_capacity['sum_of_slow_chargers_needed'] = total_kwh_of_battery_capacity.groupby(['Economy','Date','Scenario'])['slow_chargers_needed'].transform('sum')
    total_kwh_of_battery_capacity['sum_of_fast_chargers_needed'] = total_kwh_of_battery_capacity.groupby(['Economy','Date','Scenario'])['fast_chargers_needed'].transform('sum')
    total_kwh_of_battery_capacity['sum_of_slow_kw_of_chargers_needed'] = total_kwh_of_battery_capacity.groupby(['Economy','Date','Scenario'])['slow_kw_of_chargers_needed'].transform('sum')
    total_kwh_of_battery_capacity['sum_of_fast_kw_of_chargers_needed'] = total_kwh_of_battery_capacity.groupby(['Economy','Date','Scenario'])['fast_kw_of_chargers_needed'].transform('sum')
    
    total_kwh_of_battery_capacity = total_kwh_of_battery_capacity[['Economy','Date','Scenario','Vehicle Type','Stocks', 'sum_of_stocks','kwh_of_battery_capacity','sum_of_kwh_of_battery_capacity','sum_of_expected_number_of_chargers','expected_kw_of_chargers','sum_of_expected_kw_of_chargers','expected_number_of_chargers','sum_of_fast_kw_of_chargers_needed','sum_of_slow_kw_of_chargers_needed','sum_of_fast_chargers_needed','sum_of_slow_chargers_needed','fast_charger_utilisation_rate','average_kwh_of_battery_capacity_by_vehicle_type','average_kw_per_charger','average_kw_per_non_fast_charger','average_kw_per_fast_charger','slow_kw_of_chargers_needed','fast_kw_of_chargers_needed','slow_chargers_needed','fast_chargers_needed']].drop_duplicates()
    
    #rename stocks to stocks_{stocks_magnitude_name}
    total_kwh_of_battery_capacity.rename(columns={'Stocks':'Stocks_'+parameters['stocks_magnitude_name']}, inplace=True)
    #save data to csv for use in \output_data\for_other_modellers/charging
    total_kwh_of_battery_capacity.to_csv(f'output_data\\for_other_modellers\\charging\\{ECONOMY_ID}_estimated_number_of_chargers.csv', index=False)
    
# return total_kwh_of_battery_capacity
#%%
#%%
def estimate_ev_stocks_given_chargers(df, economy, date, scenario, parameters,number_of_non_fast_chargers=0,number_of_fast_chargers=0, number_of_chargers=0):
    #use a value for the number of chargers for a specified economy, date and scenario to estimate the number of evs in that economy, date and scenario.
    #we can use the previous forecasts to estimate the portion of evs in each vehicle type too.
    
    #calcualte average kw of charger capacity given the different kw of fast and non-fast chargers:
    if number_of_chargers == 0:
        kw_of_charger_capacity = (number_of_non_fast_chargers*parameters['average_kw_per_non_fast_charger']+number_of_fast_chargers*parameters['average_kw_per_fast_charger'])/(number_of_non_fast_chargers+number_of_fast_chargers)
        kw_of_fast_charger_capacity = number_of_fast_chargers*parameters['average_kw_per_fast_charger']
        kw_of_non_fast_charger_capacity = number_of_non_fast_chargers*parameters['average_kw_per_non_fast_charger']
        number_of_chargers = kw_of_charger_capacity / parameters['average_kw_per_charger']
    elif (number_of_chargers > 0) & (number_of_non_fast_chargers == 0):
        kw_of_charger_capacity = number_of_chargers*parameters['average_kw_per_charger']
        kw_of_fast_charger_capacity = 0
        kw_of_non_fast_charger_capacity = 0
        number_of_chargers = number_of_chargers
    else:
        raise ValueError('You must provide either a value for number_of_chargers or number_of_non_fast_chargers and number_of_fast_chargers, but not both')
    
    #calcualte portion of bev stocks in each vehicle type:
    #get stocks for each vehicle type
    stocks = df[(df['Drive']=='bev') & (df['Economy']==economy) & (df['Date']==date) & (df['Scenario']==scenario)]
    #get kwh of those stocks. first map on average_kwh_of_battery_capacity_by_vehicle_type
    stocks['average_kwh_of_battery_capacity_by_vehicle_type'] = stocks['Vehicle Type'].map(parameters['average_kwh_of_battery_capacity_by_vehicle_type'])
    stocks['kwh_of_battery_capacity'] = stocks['Stocks']*stocks['average_kwh_of_battery_capacity_by_vehicle_type'] * parameters['stocks_magnitude']

    stocks['sum_of_stocks'] = stocks['Stocks'].sum()
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
        stocks = stocks.drop(columns=['public_charger_utilisation_rate'])
    
    #calcualte expected kwh of battery capacity then split this by vehicle type using the portion of stocks
    stocks['sum_of_expected_kwh_of_battery_capacity'] = kw_of_charger_capacity/parameters['expected_kw_of_chargers_per_kwh_of_battery']
    stocks['expected_kwh_of_battery_capacity'] = stocks['sum_of_expected_kwh_of_battery_capacity']*stocks['portion_of_stocks_kwh_of_battery_capacity']
    
    #calcualte stocks of each vehicle type using the expected kwh of battery capacity and the average kwh of battery capacity for each vehicle type
    stocks['average_kwh_of_battery_capacity'] = stocks['Vehicle Type'].map(parameters['average_kwh_of_battery_capacity_by_vehicle_type'])
    
    stocks['expected_stocks'] = (stocks['expected_kwh_of_battery_capacity']/stocks['average_kwh_of_battery_capacity']).round(2)
    stocks['total_expected_stocks'] = stocks['expected_stocks'].sum()
    
    stocks['number_of_chargers'] = number_of_chargers
    stocks['number_of_fast_chargers'] = number_of_fast_chargers
    stocks['number_of_non_fast_chargers'] = number_of_non_fast_chargers
    
    stocks['kw_of_charger_capacity'] = kw_of_charger_capacity
    stocks['kw_of_fast_charger_capacity'] = kw_of_fast_charger_capacity
    stocks['kw_of_non_fast_charger_capacity'] = kw_of_non_fast_charger_capacity
    
    #quickly estiamte the expected number of chargers needed for each vehicle type based on the proportion of stocks value:
    stocks['expected_number_of_chargers_by_vehicle_type'] = stocks['number_of_chargers']*stocks['portion_of_stocks_kwh_of_battery_capacity']
    stocks['expected_kw_of_chargers_by_vehicle_type'] = stocks['kw_of_charger_capacity']*stocks['portion_of_stocks_kwh_of_battery_capacity']
    
    ev_stocks_and_chargers = stocks[['Economy','Date','Scenario','Vehicle Type',"Transport Type",'expected_kwh_of_battery_capacity', 'sum_of_expected_kwh_of_battery_capacity','expected_stocks', 'total_expected_stocks', 'portion_of_stocks_kwh_of_battery_capacity','number_of_chargers','number_of_fast_chargers','number_of_non_fast_chargers','kw_of_charger_capacity','kw_of_fast_charger_capacity','kw_of_non_fast_charger_capacity','expected_number_of_chargers_by_vehicle_type','expected_kw_of_chargers_by_vehicle_type']].drop_duplicates()
    return ev_stocks_and_chargers

# %%

#%%
calculate_evs_given_chargers = False 
if calculate_evs_given_chargers:
    economy= '08_JPN'
    date=2030
    scenario='Target'
    number_of_fast_chargers = 4000
    number_of_non_fast_chargers = 150000 - number_of_fast_chargers
    number_of_chargers = 0
    
    df, parameters, colors_dict, INCORPORATE_UTILISATION_RATE = prepare_inputs_for_estimating_charging_requirements(ECONOMY_ID=economy)
    
    ev_stocks_and_chargers = estimate_ev_stocks_given_chargers(df, economy, date, scenario, parameters, number_of_non_fast_chargers=number_of_non_fast_chargers, number_of_fast_chargers=number_of_fast_chargers, number_of_chargers=number_of_chargers)
    
    plot_charging_graphs.plot_required_evs(ev_stocks_and_chargers,colors_dict, economy, date, scenario)
     
        

#%%