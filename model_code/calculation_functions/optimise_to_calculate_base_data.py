#%%

###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
from .. import utility_functions
from .road_model_functions import adjust_mileage_to_account_for_covid
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
###
import pickle
from itertools import product
from scipy.optimize import minimize, differential_evolution, basinhopping, shgo, dual_annealing



# import warnings    
# # Convert warnings into exceptions
# warnings.filterwarnings('error')
#%%
pd.options.mode.chained_assignment = None  # default='warn'
#L-BFGS-B is fast and generally works.
#basinhopping is super slow but normally works more often
#trust-constr has been useful occasionaly. kinda fast. but i think doesnt work anymore since things got more complex

#these ranges will be iterated through during optimisation until one combination is found that works.
def objective_function(config, x, df_transport, actual_values, actual_energy_by_drive, parameters_dict, bounds, stocks_per_capita_constants):
    # Weighting factors
    w_mse_stocks = parameters_dict['w_mse_stocks']
    w_mse_mileage = parameters_dict['w_mse_mileage']
    w_mse_intensity = parameters_dict['w_mse_intensity']
    w_mse_opposite_drive_types = parameters_dict['w_mse_opposite_drive_types']
    w_mse_energy = parameters_dict['w_mse_energy']
    mse_stocks_dominant_vehicles_exponent = parameters_dict['mse_stocks_dominant_vehicles_exponent']
    w_mse_spc = parameters_dict['w_mse_spc']#spc stands for stocks per cpita
    STOCKS_PER_CAPITA_PCT_DIFF_THRESHOLD = parameters_dict['STOCKS_PER_CAPITA_PCT_DIFF_THRESHOLD']
    USE_SAME_MILEAGE_ACROSS_VEHICLE_TYPES = parameters_dict['USE_SAME_MILEAGE_ACROSS_VEHICLE_TYPES']
    # Secondary Objective: Minimize the difference between the stocks, mileage and intensity of the optimised values and the actual values
    df_transport.loc[:, 'Value'] = x
    mileage = df_transport.loc[df_transport['Measure'] == 'Mileage', 'Value'].to_numpy()
    intensity = df_transport.loc[df_transport['Measure'] == 'Intensity', 'Value'].to_numpy()    
    
    df_transport.loc[:, 'Value_actual'] = actual_values
    actual_mileage = df_transport.loc[df_transport['Measure'] == 'Mileage', 'Value_actual'].to_numpy()
    actual_intensity = df_transport.loc[df_transport['Measure'] == 'Intensity', 'Value_actual'].to_numpy()  
    
    EPSILON = 1e-9
    mse_mileage = np.mean((mileage - actual_mileage)**2)
    mse_intensity = np.mean((intensity - actual_intensity)**2)
    
    # Secondary Objective:
    #penalise differences in stocks between actual and optimised values
    stocks_df = df_transport.loc[df_transport['Measure'] == 'Stocks'].copy()
    mse_stocks = calculate_mse_stocks(config, stocks_df, EPSILON,mse_stocks_dominant_vehicles_exponent)
    mse_opposite_drives = calculate_mse_opposite_drives(config, stocks_df, EPSILON)
    
    #Secondary objective
    #penalise difference in stocks per cpaita in passenger transport compared to what is expected in the base year. 
    # For now, that is the calcaulted stocks per capita in the base year.    
    mse_diff_spc = calculate_stocks_per_capita_mse(config, stocks_df, stocks_per_capita_constants, STOCKS_PER_CAPITA_PCT_DIFF_THRESHOLD)
    # Primary Objective:
    # include energy in objective function
    df_transport['Value'] = x
    difference = []
    energy_list = []
    actual_energy_sum = 0
    for drive in actual_energy_by_drive.keys():
        stocks = df_transport.loc[(df_transport['Measure'] == 'Stocks') & (df_transport['Drive'] == drive), 'Value'].to_numpy()
        intensity = df_transport.loc[(df_transport['Measure'] == 'Intensity') & (df_transport['Drive'] == drive), 'Value'].to_numpy()
        vehicle_types_for_this_drive = df_transport.loc[(df_transport['Measure'] == 'Stocks') & (df_transport['Drive'] == drive), 'Vehicle Type'].to_numpy()
        if USE_SAME_MILEAGE_ACROSS_VEHICLE_TYPES:
            mileage = df_transport.loc[((df_transport['Measure'] == 'Mileage') & (df_transport['Vehicle Type'].isin(vehicle_types_for_this_drive))), 'Value'].to_numpy()#since mileage is the same for all drive types in a vehicle type, we ignore the drive type, but need to make sure we only get the mileage for the vehicle types that are in this drive type (e.g. there is no cng in 2w so we dont want to include 2w mileage in the cng drive type)
        else:
            mileage = df_transport.loc[(df_transport['Measure'] == 'Mileage'), 'Value'].to_numpy()
        # test_df = df_transport.pivot(index=['Economy', 'Date', 'Medium', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive'], columns='Measure', values='Value').reset_index()#use this to check why it might be continually failing
        energy = np.sum((mileage * stocks)*intensity)
        energy_list = np.append(energy_list, energy)
        actual_energy = actual_energy_by_drive[drive]
        
        actual_energy_sum += actual_energy
        difference.append((energy - actual_energy)**2)
    mse_energy = np.mean(difference)
    # breakpoint()
    # Weighted sum


    # try:
    #     # Your code here...
    #     total_objective = (w_mse_stocks * mse_stocks) + (w_mse_mileage * mse_mileage) + (w_mse_intensity * mse_intensity) + (w_mse_energy*mse_energy) + (w_mse_opposite_drive_types * mse_opposite_drives) + (w_mse_spc * mse_diff_spc)
    # except np.RankWarning:
    #     breakpoint()
        
    #     total_objective = (w_mse_stocks * mse_stocks) + (w_mse_mileage * mse_mileage) + (w_mse_intensity * mse_intensity) + (w_mse_energy*mse_energy) + (w_mse_opposite_drive_types * mse_opposite_drives) + (w_mse_spc * mse_diff_spc)
    # if np.isnan(total_objective) or np.isinf(total_objective):
    #     breakpoint()
    #     print("Variable contains NaN or INF values:", var)
    total_objective = (w_mse_stocks * mse_stocks) + (w_mse_mileage * mse_mileage) + (w_mse_intensity * mse_intensity) + (w_mse_energy*mse_energy) + (w_mse_opposite_drive_types * mse_opposite_drives) + (w_mse_spc * mse_diff_spc)
        
    return total_objective

def calculate_mse_stocks(config, stocks, EPSILON, mse_stocks_dominant_vehicles_exponent):
    # Calculate proportions of stocks relative to each other
    stocks['Proportion'] = stocks['Value'] / (stocks['Value'].sum() + EPSILON)
    stocks['Proportion_actual'] = stocks['Value_actual'] / (stocks['Value_actual'].sum() + EPSILON)

    proportional_mse = 0

    # Iterate through each row in the DataFrame
    for row in stocks.itertuples():
        predicted_prop = row.Proportion
        actual_prop = row.Proportion_actual

        # Using a square root of the actual proportion as the weight > use the actual proportion because otherwise in say the case where cars are less than expected, their mse will be very high and will dominate the mse. I think!?
        weight = actual_prop ** mse_stocks_dominant_vehicles_exponent

        # Calculate the weighted squared difference for each stock type
        proportional_mse += (predicted_prop - actual_prop) ** 2 * weight

    #if stocks are 0 throughout the whole df for a single transprot type, then we should heavily penalise this(its something tht the model seems to trend towards when it cant find a solution). 
    # if stocks['Value'].sum() == 0:
    #     proportional_mse = 1e6
    if stocks.groupby(['Transport Type'])['Value'].sum().min() == 0:
        proportional_mse = 1e6
    return proportional_mse

def calculate_mse_opposite_drives(config, stocks, EPSILON):
    # Secondary Objective: Minimize amount of stocks that are in undesired drive types. Since we are already trying to minimse the difference in stocks for each drive type, we should just create another penalty which further penalises extra stocks in the undesired drive types (but doesnt penalise when there are less stocks than expected in the undesired drive types). We will do this using the proportion of stocks that are in that respective drive/vehicle type rather than absolute amount, so big decreases in all stocks dont get ignored.
    #get proportions of stocks for everyhting:
    stocks['Proportion'] = stocks['Value'] / stocks.groupby(['Drive'])['Value'].transform('sum')
    stocks['Proportion_actual'] = stocks['Value_actual'] / stocks.groupby(['Drive'])['Value_actual'].transform('sum')
    
    vehicle_to_undesired_drive_types ={
        'lcv':'ice_g',#lcv are not undesired in any drive type. does potentially result in too much ice_g use in freight tho, resulting in underestimation of energy use in passenger, resulting in low stocks per capita estimates
        'ht':'ice_g',
        'mt':'ice_g',
        # 'bus':'ice_d',
        # 'car':'ice_d',
        # 'suv':'ice_d',
        'lt':'ice_d',
        '2w':'ice_d',
        'ht':'bev',#especailly for early years
        'mt':'bev',
        'bus':'bev',
        'lcv':'bev'
    }
    
    # Initialize lists to store the results
    undesired_actual_values = []
    undesired_values = []

    # Iterate through the dictionary and filter the DataFrame
    for vehicle, drive in vehicle_to_undesired_drive_types.items():
        condition = (
            (stocks['Vehicle Type'] == vehicle) & 
            (stocks['Drive'] == drive)
        )

        undesired_actual_values.extend(stocks.loc[condition, 'Proportion_actual'].to_numpy())
        undesired_values.extend(stocks.loc[condition, 'Proportion'].to_numpy())

    # Convert lists to numpy arrays (if needed)
    undesired_actual_values = np.array(undesired_actual_values)
    undesired_values = np.array(undesired_values)
    undesired_values_copy = undesired_values.copy()
    undesired_values = undesired_values[(undesired_values_copy - undesired_actual_values)>EPSILON]
    undesired_actual_values = undesired_actual_values[(undesired_values_copy - undesired_actual_values)>EPSILON]

    #now calcualte the penalty as a mse
    if len(undesired_values) == 0:
        mse_opposite_drives = 0
    else:
        mse_opposite_drives = np.mean((undesired_values.sum() - undesired_actual_values.sum())**2)
    return mse_opposite_drives


def calculate_stocks_per_capita_mse(config, stocks_df, stocks_per_capita_constants, STOCKS_PER_CAPITA_PCT_DIFF_THRESHOLD):
    """Calculates the mean squared error between the stocks per capita and the targets for the stocks per capita.

    Args:
        stocks_df (_type_): _description_
        stocks_per_capita_constants (_type_): _description_
        STOCKS_PER_CAPITA_PCT_DIFF_THRESHOLD (_type_): THIS IS Used to define a level of tolerance for the difference between the stocks per capita and the targets. If the difference is less than this threshold, the mse will be set to 0.

    Returns:
        _type_: _description_
    """
    stocks_df = stocks_df.rename(columns={'Value':'Stocks'})
    #filter for only passsenger, drop the drive col then drop duplicates
    stocks_per_capita_constants = stocks_per_capita_constants.drop(columns='Drive')
    stocks_per_capita_constants = stocks_per_capita_constants.loc[stocks_per_capita_constants['Transport Type']=='passenger']
    stocks_per_capita_constants.drop_duplicates(inplace=True)
    
    #make it wide then join with stocs
    stocks_per_capita = stocks_per_capita_constants.merge(stocks_df, on=['Economy', 'Date', 'Scenario', 'Transport Type', 'Vehicle Type'], how='left')
    #calcaulte stocks_per_captia:
    stocks_per_capita['Thousand_stocks_per_capita'] = (stocks_per_capita['Stocks']*stocks_per_capita['spc_factors'])/stocks_per_capita['Population']
    stocks_per_capita['Stocks_per_thousand_capita'] = stocks_per_capita['Thousand_stocks_per_capita'] * 1000000
    #sum it up by transport type
    #keep only stocks_per_cpaita and sum it up too:
    stocks_per_capita_calc = stocks_per_capita[['Stocks_per_thousand_capita', 'Economy', 'Scenario', 'Date', 'Transport Type']].groupby([ 'Economy', 'Scenario', 'Date', 'Transport Type']).sum().reset_index()#todo check this is right syntax
    #merge with Stocks_per_capita_targets
    stocks_per_capita = stocks_per_capita[['Stocks_per_capita_targets', 'Economy', 'Scenario', 'Date', 'Transport Type']].drop_duplicates().merge(stocks_per_capita_calc, on=['Economy', 'Scenario', 'Date', 'Transport Type'])
    #find pct diff between target and current, then if it is less than X then set mse to 0:
    pct_diff = abs(stocks_per_capita['Stocks_per_thousand_capita']-stocks_per_capita['Stocks_per_capita_targets'])/stocks_per_capita['Stocks_per_capita_targets']
    if pct_diff[0] <= STOCKS_PER_CAPITA_PCT_DIFF_THRESHOLD:
        mse_diff_spc=0
    else:
        #find mse diff between Stocks_per_thousand_capita and Stocks_per_capita_targets:
        mse_diff_spc = np.mean((stocks_per_capita['Stocks_per_thousand_capita']-stocks_per_capita['Stocks_per_capita_targets'])**2)
        
    return mse_diff_spc

def constraint_function(config, x, actual_energy_by_drive, df_transport, parameters_dict, bounds):
    df_transport['Value'] = x
    try:
        df_transport_upper_bounds = df_transport.copy()
        df_transport_upper_bounds['Value'] = [b[1] for b in bounds]
        df_transport_lower_bounds = df_transport.copy()
        df_transport_lower_bounds['Value'] = [b[0] for b in bounds]
    except:
        breakpoint()
    difference = 0
    actual_energy_sum = 0
    # breakpoint()#wats hapenning with cng here
    for drive in actual_energy_by_drive.keys():
        
        if parameters_dict['USE_SAME_MILEAGE_ACROSS_VEHICLE_TYPES']:
            mileage = df_transport.loc[(df_transport['Measure'] == 'Mileage'), 'Value'].to_numpy()
        else:
            mileage = df_transport.loc[(df_transport['Measure'] == 'Mileage') & (df_transport['Drive'] == drive), 'Value'].to_numpy()
        stocks = df_transport.loc[(df_transport['Measure'] == 'Stocks') & (df_transport['Drive'] == drive), 'Value'].to_numpy()
        intensity = df_transport.loc[(df_transport['Measure'] == 'Intensity') & (df_transport['Drive'] == drive), 'Value'].to_numpy()
        
        
        #to do away with the positive_values_constraint which doesnt seem to be working, we will check for negatives here. if there are, just return a large number
        if np.any(mileage < 0) or np.any(stocks < 0) or np.any(intensity < 0):
            return 1e6
        try:
            #and check the bounds since we are also having issues with that
            if parameters_dict['USE_SAME_MILEAGE_ACROSS_VEHICLE_TYPES']:
                if np.any(mileage > df_transport_upper_bounds.loc[(df_transport_upper_bounds['Measure'] == 'Mileage'), 'Value'].to_numpy()) or np.any(stocks > df_transport_upper_bounds.loc[(df_transport_upper_bounds['Measure'] == 'Stocks') & (df_transport_upper_bounds['Drive'] == drive), 'Value'].to_numpy()) or np.any(intensity > df_transport_upper_bounds.loc[(df_transport_upper_bounds['Measure'] == 'Intensity') & (df_transport_upper_bounds['Drive'] == drive), 'Value'].to_numpy()):
                    return 1e6
                if np.any(mileage < df_transport_lower_bounds.loc[(df_transport_lower_bounds['Measure'] == 'Mileage'), 'Value'].to_numpy()) or np.any(stocks < df_transport_lower_bounds.loc[(df_transport_lower_bounds['Measure'] == 'Stocks') & (df_transport_lower_bounds['Drive'] == drive), 'Value'].to_numpy()) or np.any(intensity < df_transport_lower_bounds.loc[(df_transport_lower_bounds['Measure'] == 'Intensity') & (df_transport_lower_bounds['Drive'] == drive), 'Value'].to_numpy()):
                    return 1e6
            else:
                if np.any(mileage > df_transport_upper_bounds.loc[(df_transport_upper_bounds['Measure'] == 'Mileage') & (df_transport_upper_bounds['Drive'] == drive), 'Value'].to_numpy()) or np.any(stocks > df_transport_upper_bounds.loc[(df_transport_upper_bounds['Measure'] == 'Stocks') & (df_transport_upper_bounds['Drive'] == drive), 'Value'].to_numpy()) or np.any(intensity > df_transport_upper_bounds.loc[(df_transport_upper_bounds['Measure'] == 'Intensity') & (df_transport_upper_bounds['Drive'] == drive), 'Value'].to_numpy()):
                    return 1e6
                if np.any(mileage < df_transport_lower_bounds.loc[(df_transport_lower_bounds['Measure'] == 'Mileage'), 'Value'].to_numpy()) or np.any(stocks < df_transport_lower_bounds.loc[(df_transport_lower_bounds['Measure'] == 'Stocks') & (df_transport_lower_bounds['Drive'] == drive), 'Value'].to_numpy()) or np.any(intensity < df_transport_lower_bounds.loc[(df_transport_lower_bounds['Measure'] == 'Intensity') & (df_transport_lower_bounds['Drive'] == drive), 'Value'].to_numpy()):
                    return 1e6
        except:
            breakpoint()
        
        energy = np.sum(mileage * intensity * stocks)
        actual_energy = actual_energy_by_drive[drive]
        
        actual_energy_sum += actual_energy
        difference += abs(energy - actual_energy)#since we want to make sure that energy for each drive is the same as the actual energy for that drive, we will just sum the abvsolute difference for each drive so every drive must be the same as the actual energy for that drive (instead of the sum of energy for all drives)

    # #Prevent certain vehicle types from having certain drives:
    # vehicle_to_unwanted_drive_types = {
    #     'ht':'ice_g',
    #     '2w':'ice_d'
    # }
    # #if any of the unwanted drive types are in the df_transport and the values are >0, then return a large number
    # for vehicle_type, drive_type in vehicle_to_unwanted_drive_types.items():
    #     if (df_transport['Vehicle Type'] == vehicle_type).any() and (df_transport['Drive'] == drive_type).any():
    #         return 1e6
    
    tolerance_pct = parameters_dict['tolerance_pct']
    
    # Return the constraint value, accounting for the tolerance
    if difference < actual_energy_sum * tolerance_pct:
        # breakpoint()#trying to find where this actually happens
        return 0
    else:
        return difference

# def positive_values_constraint(x):
#     return np.min(x)

def callback_fn(config, x):
    print(f"Current solution: {x}")

def format_and_prepare_inputs_for_optimisation(config, ECONOMY_ID, input_data_new_road, REMOVE_NON_MAJOR_VARIABLES, REMOVE_ZEROS, methods, all_parameters_dicts):
    #format df:
    # input_data_new_road = input_data_new_road.loc[input_data_new_road['Date'] <= config.OUTLOOK_BASE_YEAR].copy()
    #and temproarily, filter for only teh base year too
    input_data_new_road = input_data_new_road.loc[input_data_new_road['Date'] == config.OUTLOOK_BASE_YEAR].copy()
    #grab only 'Reference' scenario
    input_data_new_road = input_data_new_road.loc[input_data_new_road['Scenario'] == 'Reference'].copy()
    #grab oly the ECONOMY_ID
    input_data_new_road = input_data_new_road.loc[input_data_new_road['Economy'] == ECONOMY_ID].copy()

    #to mkae things easier, we will convert intensity to intensity so it can be treated the same as mileage and stocks (via multiplication rather than division)
    input_data_new_road['Intensity'] = 1/input_data_new_road['Efficiency']
    #rename to intensity
    input_data_new_road.drop(['Efficiency'], axis=1, inplace=True)
    
    #apply a decrease to mileage if the base year (the year we are optimising) is within the covid period for that economy or the 'return to normal' period. 
    for transport_type in input_data_new_road['Transport Type'].unique():
        input_data_new_road =  adjust_mileage_to_account_for_covid(config, ECONOMY_ID, input_data_new_road, transport_type, config.OUTLOOK_BASE_YEAR)
            
    #since most of the neergy use is within one or two major drive types, we will just remove all energy use for gas and electricity, which is the drive types: bev, lpg and cng. Then we will also TENTATIVELY remove phev_g and phev_d rows since they are so minor (evenm though they take up gasoline and diesel fuel types). We will jsut be left with ice_g and iced_d which are the major drive types. This will make the optimisation much faster and will also make it more accurate since we are only optimising for the major drive types. We will then add the energy use for the minor drive types back in at the end. We will use their origianl intensity, the mileage used for ice_g and ice_d and then adjsut stocks so that the energy use is the same as the required (new) energy use.
    
    if REMOVE_NON_MAJOR_VARIABLES:
        input_data_new_road_non_major_drives = input_data_new_road.loc[input_data_new_road['Drive'].isin(['bev', 'lpg', 'cng', 'phev_g', 'phev_d', 'fcev'])].copy()
        input_data_new_road = input_data_new_road.loc[~input_data_new_road['Drive'].isin(['bev', 'lpg', 'cng', 'phev_g', 'phev_d', 'fcev'])].copy() 
        if REMOVE_ZEROS:
            input_data_new_road_zeros = input_data_new_road.loc[input_data_new_road['Stocks'] == 0].copy()
            input_data_new_road = input_data_new_road.loc[input_data_new_road['Stocks'] != 0].copy()
        else:
            input_data_new_road_zeros = None
    else:
        input_data_new_road_zeros = None
        input_data_new_road_non_major_drives = None
        
    
    df_transport = input_data_new_road.melt(id_vars=['Economy', 'Date', 'Medium', 'Scenario', 'Transport Type','Vehicle Type', 'Drive'], value_name='Value', var_name='Measure').reset_index(drop=True) 
        
    #reaplce any nas with 0 in value column
    df_transport['Value'] = df_transport['Value'].fillna(0)
    
    economy = df_transport['Economy'].unique()[0]
    year = df_transport['Date'].unique()[0]
    scenario = df_transport['Scenario'].unique()[0]
    
    results_dict = {}
    results_dict["Date"] = year
    results_dict["Scenario"] = scenario
    results_dict["Economy"] = economy
    # for key in sets_dictionary.keys():
    print(f'\\nOptimising for {economy}, {year}, {scenario} at {datetime.datetime.now().strftime("%H:%M")} for methods: {methods} and parameters: {str(all_parameters_dicts)}')
    time_start = time.time()
    
    initial_values = df_transport.loc[df_transport['Measure'].isin(['Mileage', 'Stocks', 'Intensity']), 'Value'].to_numpy()
    actual_values = initial_values.copy()

    df_transport_copy = df_transport.copy()
    df_transport = df_transport.loc[df_transport['Measure'].isin(['Mileage', 'Stocks', 'Intensity'])]
    df_transport.drop(['Value'], axis=1, inplace=True)
    
    actual_energy_by_drive = {}
    for drive in df_transport['Drive'].unique():
        actual_energy_by_drive[drive] = np.sum(df_transport_copy.loc[(df_transport_copy['Drive'] == drive) & (df_transport_copy['Measure'] == 'Energy_new'), 'Value'].to_numpy())
        
    #if the abs difference between the value for Energy_new and the energy calculated from the initial values is greater than the difference between factors_bounds_tolerance_adjustment**3 times the actual energy and the actual energy, then we need to raise the tolerance to at least the 3rd root of the proportional difference (energy_new/energy_calc) or mroe so that the optimisation can work (where energy_new is the energy we are aiming for and energy_calc is the energy calculated from the initial values)
    # This is because the optimisation will otherwise not be able to find a solution that is within the tolerance
    #example:
    #lets say that energy new is 5 and energy calc is 15. then the abs diff is 10 and the prop diff is 5/15=0.333). if the initial abs tol is 0.1 then 0.1**3 is 0.001. 
    #say the 3 factors a b c are 1, 3 and 5. so the energy calc is 1*3*5 = 15. you can see that even if you decrease the factors by the max tolerance (0.1) you get abs(15 - 15*1.1*1.1*1.1) = 5, or 15*1.1*1.1*1.1=10 which is still not 10 for the difference or 5 for the acutal calcualted energy so the optimisation will fail.
    #thereofre to solve this we need the tol to be ((energy_new/energy_calc)**(1/3)) where 3 is the proportional difference since 15 -( 15*( (0.33**(1/3))**3 ) ) = 10 which is the difference between energy_new and energy_calc and 15*( (0.33**(1/3))**3 ) = 5 which is the energy we want to achieve!
    #so we want the tolerance to be ((energy_new/energy_calc)**(1/3)) or more so that the optimisation can work. To give some leeway we will times it by 1.5 so that the tolerance is higher. This will mean that the % difference is able eg. 1.5*((energy_new/energy_calc)**(1/3))  but i dont know if that is the best way since ( 15*( (1.5*((energy_new/energy_calc)**(1/3)))**3 ) ) is -1.875. obv its because we want to apply the negsative version (like 1-x) but i dont know if this is the best way to do it.
    # tolerance = 
    
    sum_energy_new = df_transport_copy.loc[df_transport_copy['Measure'] == 'Energy_new', 'Value'].sum()
    sum_energy_calc = df_transport_copy.loc[df_transport_copy['Measure'].isin(['Mileage', 'Stocks', 'Intensity'])].pivot(index=['Economy', 'Date', 'Medium', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive'], columns='Measure', values='Value').reset_index()
    sum_energy_calc['Energy_calc'] = (sum_energy_calc['Mileage'] * sum_energy_calc['Stocks']) * sum_energy_calc['Intensity']
    sum_energy_calc = sum_energy_calc['Energy_calc'].sum()
        
    if sum_energy_new > sum_energy_calc:
        UPPER = True
    elif sum_energy_new < sum_energy_calc:
        UPPER = False
    else:
        UPPER=False
        breakpoint()
        raise ValueError('sum_energy_new and sum_energy_calc are the same. this is prbably never supposed to happen')
    return df_transport, df_transport_copy, actual_values, actual_energy_by_drive, initial_values, time_start, results_dict, UPPER, sum_energy_new, input_data_new_road_non_major_drives, input_data_new_road_zeros, economy, year, scenario

def calculate_and_format_stocks_per_capita_constants(config, input_data_new_road, ECONOMY_ID):
    #these constants will remain the same thorughout the opimisation iterations. Note that we will need to calcualte stocks per cpita 
    #constants: ['Population', 'Stocks_per_capita_targets', 'spc_factors']
    stocks_per_capita_factors = pd.read_csv(config.root_dir + '\\' + 'intermediate_data\\road_model\\{}_vehicles_per_stock_parameters.csv'.format(ECONOMY_ID))    
    stocks_per_capita_factors.rename(columns={'gompertz_vehicles_per_stock':'spc_factors'}, inplace=True)
    
    #grab stocks and population
    stocks_population = input_data_new_road[['Economy', 'Scenario', 'Date','Vehicle Type', 'Transport Type', 'Drive', 'Stocks', 'Population']].copy()

    #filter for only Reference in both dfs:
    stocks_per_capita_factors = stocks_per_capita_factors.loc[stocks_per_capita_factors.Scenario=='Reference'].copy()
    stocks_population = stocks_population.loc[stocks_population.Scenario=='Reference'].copy()
    
    #merge with spc factors
    stocks_population_spc_factors = stocks_population.merge(stocks_per_capita_factors, on=['Economy', 'Scenario', 'Date','Vehicle Type', 'Transport Type'])    
    
    #get only passenger
    stocks_per_capita = stocks_population_spc_factors.loc[stocks_population_spc_factors['Transport Type']=='passenger'].copy()
    
    #calcualte stocks per cpita now:
    stocks_per_capita['Thousand_stocks_per_capita'] = (stocks_per_capita['Stocks']*stocks_per_capita['spc_factors'])/stocks_per_capita['Population']
    stocks_per_capita['Stocks_per_capita_targets'] = stocks_per_capita['Thousand_stocks_per_capita'] * 1000000
    #keep only stocks_per_cpaita and sum it up too:
    stocks_per_capita = stocks_per_capita[['Stocks_per_capita_targets', 'Economy', 'Scenario', 'Date', 'Transport Type']].groupby([ 'Economy', 'Scenario', 'Date', 'Transport Type']).sum().reset_index()
    #merge with original df 
    stocks_per_capita_constants = stocks_per_capita.merge(stocks_population_spc_factors, on=['Economy', 'Scenario', 'Date', 'Transport Type'])
    #drop stocks
    stocks_per_capita_constants.drop(columns=['Stocks'], inplace=True)
    stocks_per_capita_constants = stocks_per_capita_constants.drop_duplicates()
    return stocks_per_capita_constants

def set_cng_lpg_stocks_to_zero_where_energy_is_zero(config, ECONOMY_ID, input_data_new_road):
    #because some economies have stocks in these but their energy for them is zero, its easier to set their stocks to 0 so that the optimisation doesnt have to deal with them.
    #there is also the option to move the stocks to diesel or gasoline depending on the vehicle type.
    for cng_or_lpg_drive in ['cng', 'lpg']:
        if input_data_new_road.loc[(input_data_new_road['Drive']==cng_or_lpg_drive) & (input_data_new_road['Economy'] == ECONOMY_ID), 'Energy_new'].sum() <= 1e-9:
            #vehicle type to ice_g or ice_d mappung:#lt, suv, ht, mt, lcv, car, bus, 2w
            vehicle_to_ice_g_or_ice_d = {
                'bus':'ice_d',
                'car':'ice_g',
                '2w':'ice_g',
                'lt':'ice_g',
                'suv':'ice_g',
                'ht':'ice_d',
                'mt':'ice_d',
                'lcv':'ice_d'
            }
            for vehicle, drive in vehicle_to_ice_g_or_ice_d.items():
                
                input_data_new_road.loc[(input_data_new_road['Drive'] == drive) & (input_data_new_road['Vehicle Type'] == vehicle) & (input_data_new_road['Economy'] == ECONOMY_ID), 'Stocks'] += input_data_new_road.loc[(input_data_new_road['Drive']==cng_or_lpg_drive) & (input_data_new_road['Vehicle Type'] == vehicle) & (input_data_new_road['Economy'] == ECONOMY_ID), 'Stocks'].sum()
            #set cng and lpg stocks to 0
            input_data_new_road.loc[(input_data_new_road['Drive']==cng_or_lpg_drive) & (input_data_new_road['Economy'] == ECONOMY_ID), 'Stocks'] = 0
            #set Energy_old to 0 as well, just to avoid confusion
            input_data_new_road.loc[(input_data_new_road['Drive']==cng_or_lpg_drive) & (input_data_new_road['Economy'] == ECONOMY_ID), 'Energy_old'] = 0
    return input_data_new_road    
    
def set_elec_vehicles_stocks_to_zero(config, ECONOMY_ID, input_data_new_road):
    #where drive is bev or phev_d or phev_g then set Stocks col values to 0 
    #double check there is no energy use for these drive types, as there shouldnt be:
    if input_data_new_road.loc[(input_data_new_road['Drive'].isin(['bev', 'phev_d', 'phev_g'])) & (input_data_new_road['Economy'] == ECONOMY_ID), 'Energy_new'].sum() != 0:
        breakpoint()
        raise ValueError('there is energy use for bev, phev_d or phev_g in input_data_new_road even though USE_MOVE_ELECTRICITY_USE_IN_ROAD_TO_RAIL_ESTO is True')
    
    input_data_new_road.loc[(input_data_new_road['Drive'].isin(['bev', 'phev_d', 'phev_g'])) & (input_data_new_road['Economy'] == ECONOMY_ID), 'Stocks'] = 0
    #set Energy_old to 0 as well, just to avoid confusion
    input_data_new_road.loc[(input_data_new_road['Drive'].isin(['bev', 'phev_d', 'phev_g'])) & (input_data_new_road['Economy'] == ECONOMY_ID), 'Energy_old'] = 0
    return input_data_new_road

def load_in_optimisation_parameters(config, ECONOMY_ID):
    with open(config.root_dir + '\\' + 'config\\optimisation_parameters.yml') as file:
        parameters_dict = yaml.load(file, Loader=yaml.FullLoader)
        #get the parameters for the economy
        if ECONOMY_ID=='ALL' or ECONOMY_ID=='ALL2':
            #this will be a ful set of different parameters to iterate over so we jsut load it in one big set
            
            parameters_dict = parameters_dict[ECONOMY_ID]
            #save each entry as a list so it can be iterated through (even if it is just one entry)
            method = parameters_dict['methods_list']
            #drop method from dict
            parameters_dict.pop('methods_list')                
        elif ECONOMY_ID in parameters_dict.keys():
            parameters_dict = parameters_dict[ECONOMY_ID]
            #save each entry as a list so it can be iterated through (even if it is just one entry)
            method = parameters_dict['method']
            #drop method from dict
            parameters_dict.pop('method')
            for key, value in parameters_dict.items():
                parameters_dict[key] = [value]
        else:
            parameters_dict, method = None, None
    return parameters_dict, method

def optimise_to_find_base_year_values(config, input_data_new_road, ECONOMY_ID, methods, all_parameters_dicts, REMOVE_NON_MAJOR_VARIABLES, USE_MOVE_ELECTRICITY_USE_IN_ROAD_TO_RAIL_ESTO, SET_CNG_LPG_STOCKS_TO_ZERO=True):
    """a quick note on the data: since in the funciton pevious to this we calculated the energy that would be required to reach esto goals, we can use 'energy new' as the energy that is required to be reached for all vehicles in each drive type. however it is not necessary that the energy by drive type is reached. 
    Then, the factors for satocks, mileage and intensity are what was used as the input data for them, so the product of these is not energy_new but its own value (energy_calc). These will need to be adjusted to make it so energy by drive type matches energy new, and hopefuly there is minimal difference between the new factors and their old values.

    Args:
        input_data_new_road (_type_): _description_
        ECONOMY_ID (_type_): _description_
        methods (_type_): _description_
        parameters_dict (_type_): _description_
        USE_MOVE_ELECTRICITY_USE_IN_ROAD_TO_RAIL_ESTO - Since in adjust_data_to_match_esto.move_electricity_use_in_road_to_rail_esto(config, energy_use_esto, ECONOMY_ID) we remove road elec use and move it to rail, we need this option to remove any elec vehicle and phev stocks.
        
    Raises:
        ValueError: _description_

    Returns:
        _type_: _description_
    """
    # REMOVE_NON_MAJOR_VARIABLES = True
    if USE_MOVE_ELECTRICITY_USE_IN_ROAD_TO_RAIL_ESTO:
        input_data_new_road = set_elec_vehicles_stocks_to_zero(config, ECONOMY_ID, input_data_new_road)
    if SET_CNG_LPG_STOCKS_TO_ZERO:
        input_data_new_road = set_cng_lpg_stocks_to_zero_where_energy_is_zero(config, ECONOMY_ID, input_data_new_road)
    REMOVE_ZEROS = True
    df_transport, df_transport_copy, actual_values, actual_energy_by_drive, initial_values, time_start, results_dict, UPPER, sum_energy_new, input_data_new_road_non_major_drives, input_data_new_road_zeros, economy, year, scenario = format_and_prepare_inputs_for_optimisation(config, ECONOMY_ID, input_data_new_road,REMOVE_NON_MAJOR_VARIABLES, REMOVE_ZEROS, methods, all_parameters_dicts)
    success = False
    methods_and_params = list(product(methods, all_parameters_dicts))#ESTIMATE STOCKS PER CAPITA FOR THIS ECONOMY USING THE DATA WE HAVE RIGHT NOW. WE WILL TRY TO KEEP THIS CONSTANT THROUGHOUT THE OPTIMISATION, UNLESS THE ECONOMY IS ONE WE EXPECT TO HAVE HIGH UNCERTAINTY ABOUT ITS STOCKS PER CAPITA IN WHICH CASE WE CAN SET THE STOCKS_PER_CAPITA_PCT_DIFF_THRESHOLD VALUE TO 1 TO ALLOW ANY STOCKS PER CAPITA TO PASS THE THRESHOLD (E.G. PNG)
    stocks_per_capita_constants = calculate_and_format_stocks_per_capita_constants(config, input_data_new_road, ECONOMY_ID)#todo make sure no issues are cuased by having population in input_data_new_road
    i = 0
    df_transport_copy2=df_transport.copy()
    initial_values_copy2 = initial_values.copy()
    actual_values_copy2 = actual_values.copy()
    for method_and_params in methods_and_params:
        #reset any changes made in previous iteration
        df_transport = df_transport_copy2.copy()
        initial_values = initial_values_copy2.copy()
        actual_values = actual_values_copy2.copy()
        method = method_and_params[0]
        parameters_dict = method_and_params[1]
        
        #initially set bounds. they still might change if we need to adjust stocks bounds so required energy can be reached
        lower_bounds, upper_bounds = set_bounds_for_optimisation(config, parameters_dict,df_transport_copy, UPPER)
        
        bounds = list(zip(lower_bounds, upper_bounds))
        initial_values, bounds, lower_bounds, upper_bounds = check_bounds_and_adjust_stocks_to_be_able_to_calculate_energy(config, initial_values, bounds,lower_bounds,upper_bounds, UPPER, df_transport, parameters_dict,sum_energy_new,df_transport_copy)
        # def ensure_stocks_by_drive_match_requried_energy():
            
        SAVE_BOUNDS=False
        if SAVE_BOUNDS:
            # Adding them to the DataFrame
            df_transport['Lower_Bound'] = lower_bounds
            df_transport['Upper_Bound'] = upper_bounds
            df_transport['Initial_Value'] = initial_values
            df_transport.to_csv(config.root_dir + '\\' + 'intermediate_data\\analysis_single_use\\bounds.csv')
            df_transport.drop(['Lower_Bound', 'Upper_Bound', 'Initial_Value'], axis=1, inplace=True)
        
        #make it so taht we only have one value for mileage for each vehicle type (or at least where mielage starts off the same, it will end up the same - allows for different mileage for different drive types if we want)
        if parameters_dict['USE_SAME_MILEAGE_ACROSS_VEHICLE_TYPES']:
            df_transport, lower_bounds, upper_bounds, initial_values, actual_values = set_mileage_to_be_the_same_for_each_vehicle_type(config, df_transport, actual_values, lower_bounds, upper_bounds, initial_values)            
        bounds = list(zip(lower_bounds, upper_bounds))
        constraints = [
            {'type': 'eq', 'fun': constraint_function, 'args': (actual_energy_by_drive, df_transport, parameters_dict, bounds)}
        ]#,{'type': 'ineq', 'fun': positive_values_constraint}
        try:
            ###################################################
            #################   IMPORTANT FUNCTION HERE. THIS IS WHERE THE OPTIMISATION HAPPENS #################
            
            # if ECONOMY_ID == '08_JPN':
            #     breakpoint()
            result = objective_function_handler(config, method, initial_values, df_transport, actual_values, parameters_dict,actual_energy_by_drive, constraints, bounds, stocks_per_capita_constants) 
            #################   IMPORTANT FUNCTION HERE. THIS IS WHERE THE OPTIMISATION HAPPENS #################
            ###################################################
            
        except:
            # if ECONOMY_ID == '08_JPN':
            #     breakpoint()
            print(f"Optimization failed with method {method}, reason: {sys.exc_info()[0]}, {sys.exc_info()[1]}")
            continue
        if result.success:
            print(f"Optimization succeeded with method {method}")
            
            ###################################################################
            #save all the inputs to objective_function_handler so we can run it again and see what happens in the obj function to get to this point
            # method, initial_values, df_transport, actual_values, parameters_dict,actual_energy_by_drive, constraints, bounds, stocks_per_capita_constants
            
            # Save all the inputs to objective_function_handler
            # timex = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            # with open(f'inputs_to_objective_function_handler_{timex}.pkl', 'wb') as f:
            #     pickle.dump({
            #         'method': method,
            #         'initial_values': initial_values,
            #         'df_transport': df_transport,
            #         'actual_values': actual_values,
            #         'parameters_dict': parameters_dict,
            #         'actual_energy_by_drive': actual_energy_by_drive,
            #         'constraints': constraints,
            #         'bounds': bounds,
            #         'stocks_per_capita_constants': stocks_per_capita_constants
            #     }, f)

            # # with open(config.root_dir + '\\' + 'inputs_to_objective_function_handler.pkl', 'rb') as f:
            # #     inputs = pickle.load(f)

            # # # Now you can access the inputs like this:
            # # method = inputs['method']
            # # initial_values = inputs['initial_values']
            # # df_transport = inputs['df_transport']
            # # actual_values = inputs['actual_values']
            # # parameters_dict = inputs['parameters_dict']
            # # actual_energy_by_drive = inputs['actual_energy_by_drive']
            # # constraints = inputs['constraints']
            # # bounds = inputs['bounds']
            # # stocks_per_capita_constants = inputs['stocks_per_capita_constants']
            # result = objective_function_handler(config, method, initial_values, df_transport, actual_values, parameters_dict,actual_energy_by_drive, constraints, bounds, stocks_per_capita_constants) 
            #################################################
            
            
            
            success = True
            df_transport_new, results_dict_new, success = format_and_check_optimisation_results_before_finalising(config, result, df_transport, df_transport_copy, results_dict, parameters_dict, economy, year, scenario, method, time_start)
            if success:    
                df_transport, results_dict = df_transport_new, results_dict_new
                break
            else:
                continue
        else:
            print(f"Optimization failed with method {method}, reason: {result.message}")                

    if not success:
        print(f'All methods failed for {economy}, {year}, {scenario} using methods: {methods}')
        results_dict['result'] = None
        results_dict['method'] = None
        results_dict['time_to_run'] = time.time() - time_start
        results_dict['parameters_dict'] = parameters_dict
        return None, results_dict
        
    if REMOVE_NON_MAJOR_VARIABLES:
        df_transport = add_back_non_major_drives(config, input_data_new_road_non_major_drives, df_transport, REMOVE_ZEROS, input_data_new_road_zeros)
    #check for any negative vlaues or nans. if there are throw a warning and set to 0 if its not a factor. if its a factor keep as na
    if df_transport['Value'].isna().sum(numeric_only=True) > 0:
        print('There are nans in df_transport. They will be set to 0 if they are not factors:')
        print(df_transport.loc[df_transport['Value'].isna()])
        breakpoint()
        #set factors that are na to 0 if their measure isnt in config.FACTOR_MEASURES
        df_transport.loc[(~df_transport.Measure.isin(config.FACTOR_MEASURES))&(df_transport.Value.isna()), 'Value'] = 0
    if df_transport['Value'].min() < 0:
        print('There are negative values in df_transport. They will be set to 0 if they arent factors:')
        print(df_transport.loc[df_transport['Value'] < 0])
        breakpoint()
        df_transport.loc[(~df_transport.Measure.isin(config.FACTOR_MEASURES))&(df_transport['Value'] < 0), 'Value']=0
        
    return df_transport, results_dict

def set_mileage_to_be_the_same_for_each_vehicle_type(config, df_transport, actual_values, lower_bounds, upper_bounds, initial_values):
    df_transport['Lower_Bound'] = lower_bounds
    df_transport['Upper_Bound'] = upper_bounds
    df_transport['Initial_Value'] = initial_values
    df_transport['Actual_Value'] = actual_values
    #grab measure == mielage and drop duplicates when we drop drive
    df_transport_mileage = df_transport.loc[df_transport['Measure'] == 'Mileage'].drop(columns='Drive').drop_duplicates().copy()
    #set drive to 'all'
    df_transport_mileage['Drive'] = 'all'
    #now merge with df_transport to get the bounds and initial values for mileage
    df_transport = df_transport.merge(df_transport_mileage, on=['Economy', 'Date', 'Medium', 'Scenario', 'Transport Type', 'Vehicle Type', 'Measure'], how='left', suffixes=('_y', ''))
    #set Value, drive and bounds to the value from df_transport_mileage if it is not nan, otherwise set it to the value from df_transport
    df_transport['Value'] = df_transport['Value'].fillna(df_transport['Value_y'])
    df_transport['Drive'] = df_transport['Drive'].fillna(df_transport['Drive_y'])
    df_transport['Lower_Bound'] = df_transport['Lower_Bound'].fillna(df_transport['Lower_Bound_y'])
    df_transport['Upper_Bound'] = df_transport['Upper_Bound'].fillna(df_transport['Upper_Bound_y'])
    df_transport['Initial_Value'] = df_transport['Initial_Value'].fillna(df_transport['Initial_Value_y'])
    df_transport['Actual_Value'] = df_transport['Actual_Value'].fillna(df_transport['Actual_Value_y'])
    df_transport.drop(columns=['Value_y', 'Drive_y', 'Lower_Bound_y', 'Upper_Bound_y', 'Initial_Value_y', 'Actual_Value_y'], inplace=True)
    df_transport.drop_duplicates(inplace=True)
    lower_bounds = df_transport['Lower_Bound'].to_numpy()
    upper_bounds = df_transport['Upper_Bound'].to_numpy()
    initial_values = df_transport['Initial_Value'].to_numpy()
    actual_values = df_transport['Actual_Value'].to_numpy()
    #drop the cols we dont need
    df_transport.drop(columns=['Lower_Bound', 'Upper_Bound', 'Initial_Value', 'Actual_Value'], inplace=True)
    return df_transport, lower_bounds, upper_bounds, initial_values, actual_values

def format_and_check_optimisation_results_before_finalising(config, result, df_transport, df_transport_copy, results_dict, parameters_dict, economy, year, scenario, method, time_start):
    
    # Extract optimized values
    optimized_x = result.x
    
    results_dict['result'] = result
    results_dict['method'] = method
    results_dict['time_to_run'] = time.time() - time_start
    results_dict['parameters_dict'] = parameters_dict
    
    #put them in the df and then concat to the new df
    if len(optimized_x) != len(df_transport):
        raise ValueError(f'length of optimized_x must be the same as the length of df_transport for {economy}, {year}, {scenario}')
        # return None, results_dict
    try:
        df_transport['Value'] = optimized_x
        
        if parameters_dict['USE_SAME_MILEAGE_ACROSS_VEHICLE_TYPES']:
            #split mielage into all the different drives again
            mileage = df_transport.loc[df_transport['Measure'] == 'Mileage'].drop(columns='Drive').drop_duplicates().copy()
            #fill drive col for mileage with all the different drives in intensity
            intensity_drives = df_transport.loc[df_transport['Measure'] == 'Intensity'][['Economy', 'Date', 'Medium', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive']].drop_duplicates().copy()
            mileage = mileage.merge(intensity_drives, on=['Economy', 'Date', 'Medium', 'Scenario', 'Transport Type', 'Vehicle Type'], how='right')
            #drop mielage from df_transport
            df_transport.drop(df_transport.loc[df_transport['Measure'] == 'Mileage'].index, inplace=True)
            df_transport = pd.concat([df_transport, mileage], axis=0)      
            
        #make wide and recalcaulte energy
        df_transport = df_transport.pivot_table(index=['Economy', 'Date', 'Medium', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive'], columns='Measure', values='Value').reset_index()
        df_transport['Energy_new'] = (df_transport['Mileage'] * df_transport['Stocks']) * df_transport['Intensity']
        #make tall again
        df_transport = df_transport.melt(id_vars=['Economy', 'Date', 'Medium', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive'], value_name='Value', var_name='Measure').reset_index(drop=True)
        df_transport, results_dict, success = check_results_difference_after_optimisation(config, df_transport, df_transport_copy, results_dict, parameters_dict, economy, year, scenario)       
        
        if df_transport is None:
            return None, results_dict, False
        if not success:
            return None, results_dict, False
        else: 
            return df_transport, results_dict, True
    
    except:#is a bit not neat but just want to catch any errors and return None rather than get an error while running and ahve to run again
        raise ValueError(f'length of optimized_x must be the same as the length of df_transport for {economy}, {year}, {scenario}')
    
# def incorporate_covid_mileage_decrease(economy, input_data_new_road):#economy, dataframe, transport_type, current_year
#     """The decrease due to covid also needs to be considered as a cuase in difference between results and what esto reports. So before optimising we should decrease the mileage by the expected decrease due to covid. This will be done by multiplying the mileage by the expected decrease due to covid. Then these will be used as teh initial values for the optimisation, and tehfore affect the bounds too. These mileage values will then be adjusted upwards in 2021 in the model. Note that even if the esto values were higher than what we have, we should still include this decrease due to covid since it is a cause of difference between the results and the esto values.In the case of esto being higer, it will just decrease the difference!
    
#     Raises:
#         ValueError: _description_
#     """
    
#     parameters = yaml.load(open(config.root_dir + '\\' + 'config\\parameters.yml'), Loader=yaml.FullLoader)
#     for transport_type in ['passenger', 'freight']:
            
#         if transport_type =='passenger':
#             #load ECONOMIES_WITH_STOCKS_PER_CAPITA_REACHED from parameters.yml
#             EXPECTED_ENERGY_DECREASE_FROM_COVID_PASSENGER =  parameters['EXPECTED_ENERGY_DECREASE_FROM_COVID_PASSENGER']
#             X = EXPECTED_ENERGY_DECREASE_FROM_COVID_PASSENGER[economy]
            
#             last_covid_year = max(parameters['LISTED_YEARS_WHEN_COVID_EFFECTS_APPLIED_PASSENGER'][economy])
            
#         elif transport_type =='freight':
#             EXPECTED_ENERGY_DECREASE_FROM_COVID_FREIGHT =  parameters['EXPECTED_ENERGY_DECREASE_FROM_COVID_FREIGHT']
#             X = EXPECTED_ENERGY_DECREASE_FROM_COVID_FREIGHT[economy]
            
#             last_covid_year = max(parameters['LISTED_YEARS_WHEN_COVID_EFFECTS_APPLIED_FREIGHT'][economy])
        
#         #if the base year is within the covid period for that economy then we will adjust the mileage by X
#         if config.OUTLOOK_BASE_YEAR <= last_covid_year:
#             #now decrease mileage by X
#             input_data_new_road.loc[(input_data_new_road['Transport Type'] == transport_type), 'Mileage'] = input_data_new_road.loc[(input_data_new_road['Transport Type'] == transport_type),'Mileage'] * (1-X)
            
#     return input_data_new_road

def add_back_non_major_drives(config, input_data_new_road_non_major_drives, df_transport, REMOVE_ZEROS, input_data_new_road_zeros):
    """note that input_data_new_road_non_major_drives is wide and df_transport is tall

    add back the 
    Args:
        input_data_new_road_non_major_drives (_type_): _description_
        df_transport (_type_): _description_
    """
    if REMOVE_ZEROS:
        input_data_new_road_non_major_drives = pd.concat([input_data_new_road_non_major_drives, input_data_new_road_zeros], axis=0)
    #filter df_transport so we can get the average mileage for each vehicle type:
    df_transport_mileage = df_transport.loc[df_transport['Measure'] == 'Mileage'].groupby(['Economy', 'Date', 'Medium', 'Scenario', 'Transport Type', 'Vehicle Type'], as_index=False).agg({'Value':'mean'})
    
    #merge with input_data_new_road_non_major_drives to use the mileage for each vehicle type
    input_data_new_road_non_major_drives = input_data_new_road_non_major_drives.merge(df_transport_mileage, on=['Economy', 'Date', 'Medium', 'Scenario', 'Transport Type', 'Vehicle Type'], how='left')
    #drop og mileage and rename vlaue to mileage
    input_data_new_road_non_major_drives.drop(['Mileage'], axis=1, inplace=True)
    input_data_new_road_non_major_drives.rename(columns={'Value':'Mileage'}, inplace=True)
    #we keep Intensity as it was. 
    #recalculate stocks so that energy is the same as Energy_new
    input_data_new_road_non_major_drives['Stocks'] =  (input_data_new_road_non_major_drives['Energy_new']) / (input_data_new_road_non_major_drives['Intensity'] * input_data_new_road_non_major_drives['Mileage'])
    #make tall.
    input_data_new_road_non_major_drives = input_data_new_road_non_major_drives.melt(id_vars=['Economy', 'Date', 'Medium', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive'], value_name='Value', var_name='Measure').reset_index(drop=True)
    #drop Measures that arent in df_transport
    input_data_new_road_non_major_drives = input_data_new_road_non_major_drives.loc[input_data_new_road_non_major_drives['Measure'].isin(df_transport['Measure'].unique())].copy()
    # breakpoint()#check that values are the same as before
    #add back to df_transport
    df_transport = pd.concat([df_transport, input_data_new_road_non_major_drives], axis=0)
    return df_transport

def check_results_difference_after_optimisation(config, df_transport, df_transport_copy, results_dict, parameters_dict, economy, year, scenario, SAVE=True, BREAKPOINT=True, IGNORE_LARGE_ENERGY_RESIDUALS=False):
    #check that the difference between the optimised energy and the actual energy is less than 1% of the actual energy. This is really just to check that the optimisation has worked. If it hasnt, then we will return None since we dont want to use the results
    #merge the output with the original data in df_transport_copy and calcualte the difference between the optimised energy and the actual energy
    sum_optimised_energy = df_transport.loc[df_transport['Measure'] == 'Energy_new', 'Value'].sum()
    sum_actual_energy = df_transport_copy.loc[df_transport_copy['Measure'] == 'Energy_new', 'Value'].sum()
    difference = abs(sum_optimised_energy - sum_actual_energy)
    if difference > sum_actual_energy * 0.1:# parameters_dict['tolerance_pct']:#testing 10% diff just to see  what soltuions looks like
        print(f'SOLUTION NOT VALID: Difference between optimised energy and actual energy is {difference} which is greater than {parameters_dict["tolerance_pct"]*100}% for {economy}, {year}, {scenario}')
        if IGNORE_LARGE_ENERGY_RESIDUALS:
            breakpoint()
            print(f'IGNORE_LARGE_ENERGY_RESIDUALS is True so we will ignore this and continue')
            return df_transport, results_dict, True
        if BREAKPOINT:
            breakpoint()
        if SAVE:
            #save results dict just in case
            results_dict['file_id'] = datetime.datetime.now().strftime("%Y%m%d_%H%M") 
            with open(config.root_dir + '\\' + f'plotting_output\\input_exploration\\results_dict_{economy}_{year}_{scenario}_{results_dict["file_id"]}_UNSUCCESSFUL.pkl', 'wb') as f:
                pickle.dump(results_dict, f)
            #and save the optimised data (df_transport)
            df_transport.to_csv(config.root_dir + '\\' + f'plotting_output\\input_exploration\\optimised_data_{economy}_{year}_{scenario}_{results_dict["file_id"]}_UNSUCCESSFUL.csv')
        return df_transport, results_dict, False #None, None
    else:
        return df_transport, results_dict, True
    
def objective_function_handler(config, method, initial_values, df_transport, actual_values, parameters_dict, actual_energy_by_drive, constraints, bounds, stocks_per_capita_constants):
    """
    Args:
        method (str): Optimization method.
        initial_values: Initial guess for the parameters.
        df_transport: DataFrame containing transport data.
        actual_values: Actual values for comparison.
        parameters_dict: Dictionary of parameters.
        actual_energy_by_drive: Energy data by drive type.
        constraints: Constraints for optimization.
        bounds: Bounds for the parameters.

    Raises:
        ValueError: If an unsupported method is passed.

    Returns:
        Result of the optimization process.
    """
    maxiter_adjusted = {
        'differential_evolution': 1000,  # Default maxiter for differential_evolution
        'basinhopping': 100,             # Default niter for basinhopping
        'shgo': None,                    # shgo doesn't use maxiter in the same way
        'dual_annealing': 1000,          # Default maxiter for dual_annealing
        'L-BFGS-B': 15000,               # Default maxiter for L-BFGS-B
        'TNC': None,                     # Default maxiter for TNC (varies)
        'SLSQP': 100,                    # Default maxiter for SLSQP
        'trust-constr': 100,             # Default maxiter for trust-constr
        'Nelder-Mead': None,             # Default maxiter for Nelder-Mead (varies)
        'Powell': None                   # Default maxiter for Powell (varies)
    }

    # parameters_dict['use_constraint_penalty_in_objective'] = False#use this to turn on or off the constraint penalty in the objective function. allows for using contraints trhough objective function when they arent allowed otherwise
    
    # Adjust maxiter based on the iteration_multiplier
    maxiter = maxiter_adjusted.get(method)
    if maxiter:
        maxiter *= parameters_dict['iteration_multiplier']
    if method == 'differential_evolution':
        result = differential_evolution(objective_function,
            args=(df_transport, actual_values, actual_energy_by_drive, parameters_dict, bounds, stocks_per_capita_constants),
            bounds=bounds, maxiter=maxiter)
    elif method == 'basinhopping':
        result = basinhopping(
            objective_function, 
            x0=initial_values, 
            minimizer_kwargs={
                "method": "L-BFGS-B", 
                "args": (df_transport, actual_values, actual_energy_by_drive, parameters_dict, bounds, stocks_per_capita_constants)
            },
            niter=maxiter
        )
    elif method == 'shgo':
        result = shgo(objective_function,
            args=(df_transport, actual_values, actual_energy_by_drive, parameters_dict, bounds, stocks_per_capita_constants), 
            bounds=bounds, 
            constraints=constraints)

    elif method == 'dual_annealing':
        result = dual_annealing(objective_function,
            args=(df_transport, actual_values, actual_energy_by_drive, parameters_dict, bounds, stocks_per_capita_constants), 
            bounds=bounds, 
            maxiter=maxiter)

    elif method in ['L-BFGS-B', 'TNC']:
        #try this and if the result is not good then retry with 'w_mse_stocks' set to 0 and then w_mse_oppsoite_drive_types set to 0 and then both:
        try:
            result = minimize(
                objective_function,
                initial_values,
                args=(df_transport, actual_values, actual_energy_by_drive, parameters_dict, bounds, stocks_per_capita_constants),
                bounds=bounds,
                method=method,
                options={"maxiter": maxiter}
            )  
        except Exception as e:
            # breakpoint()     
            print('error while running L-BFGS-B or TNC' + str(e))

    elif method in ['SLSQP', 'trust-constr']:
        result = minimize(
            objective_function,
            initial_values,
            args=(df_transport, actual_values, actual_energy_by_drive, parameters_dict, bounds, stocks_per_capita_constants),
            bounds=bounds,
            constraints=constraints,
            method=method,
            options={"maxiter": maxiter}
        )

    elif method in ['Nelder-Mead', 'Powell']:
        # For methods that don't support 'maxiter' directly, we can use 'options' to pass it, but it might not be effective
        result = minimize(
            objective_function,
            initial_values,
            args=(df_transport, actual_values, actual_energy_by_drive, parameters_dict, bounds, stocks_per_capita_constants),
            method=method,
            options={"maxiter": maxiter}
        )

    else:
        raise ValueError(f"Method {method} is not supported")
    return result


def set_bounds_for_optimisation(config, parameters_dict, df_transport_copy, UPPER):
    """we want to set the bounds so that they allow for enough change to reach the new energy but not so much that the optimisation takes too long. We will do this by first setting the bounds of the mileage and efficiency to a set % change either way. This is because we KNOW that these values wont change more than this.
    For stocks we will allow for them to change by a set percentage too, but this will be allowed to be very high so that instead the mse of difference between new and original stocks values will help to constrain that, and help the optimisation find a solution?
    Args:
        parameters_dict (_type_): _description_
        sum_energy_new (_type_): _description_
        sum_energy_calc (_type_): _description_
        df_transport_copy (_type_): _description_

    Returns:
        _type_: _description_
    """
    #since there is only so much that the Intensity or mielage can cahgne we will set bounds on that. This will mean that stocks will be able to change more to compensate if the necessary cahnge in enegry is too much for the other factors to handle
    maximum_change_in_intensity = parameters_dict['maximum_proportional_change_in_intensity']
    maximum_change_in_mileage = parameters_dict['maximum_proportional_change_in_mileage']
    #adjust upper bounds for mileage and intensity bounds to be within the maximum change and adjust stocks to be * factors_bounds_tolerance    
    upper_initial_values_bounded_by_maximum_eff_mielage = df_transport_copy.loc[df_transport_copy['Measure'].isin(['Mileage', 'Stocks', 'Intensity'])].copy()  
    lower_initial_values_bounded_by_maximum_eff_mielage = df_transport_copy.loc[df_transport_copy['Measure'].isin(['Mileage', 'Stocks', 'Intensity'])].copy()
    if UPPER:
        #adjust intensity
        upper_initial_values_bounded_by_maximum_eff_mielage.loc[upper_initial_values_bounded_by_maximum_eff_mielage['Measure'] == 'Intensity', 'Value'] = upper_initial_values_bounded_by_maximum_eff_mielage.loc[upper_initial_values_bounded_by_maximum_eff_mielage['Measure'] == 'Intensity', 'Value'] * (1+maximum_change_in_mileage)
        #adjust mileage
        upper_initial_values_bounded_by_maximum_eff_mielage.loc[upper_initial_values_bounded_by_maximum_eff_mielage['Measure'] == 'Mileage', 'Value'] = upper_initial_values_bounded_by_maximum_eff_mielage.loc[upper_initial_values_bounded_by_maximum_eff_mielage['Measure'] == 'Mileage', 'Value'] * (1+maximum_change_in_intensity)
    else:
        #adjust intensity
        lower_initial_values_bounded_by_maximum_eff_mielage.loc[lower_initial_values_bounded_by_maximum_eff_mielage['Measure'] == 'Intensity', 'Value'] = lower_initial_values_bounded_by_maximum_eff_mielage.loc[lower_initial_values_bounded_by_maximum_eff_mielage['Measure'] == 'Intensity', 'Value'] * (1-maximum_change_in_mileage)
        #adjust mileage
        lower_initial_values_bounded_by_maximum_eff_mielage.loc[lower_initial_values_bounded_by_maximum_eff_mielage['Measure'] == 'Mileage', 'Value'] = lower_initial_values_bounded_by_maximum_eff_mielage.loc[lower_initial_values_bounded_by_maximum_eff_mielage['Measure'] == 'Mileage', 'Value'] * (1-maximum_change_in_intensity)
        
    lower_bounds, upper_bounds  = lower_initial_values_bounded_by_maximum_eff_mielage['Value'].to_numpy(), upper_initial_values_bounded_by_maximum_eff_mielage['Value'].to_numpy()
    return lower_bounds, upper_bounds
    
def check_bounds_and_adjust_stocks_to_be_able_to_calculate_energy(config, initial_values, bounds, lower_bounds, upper_bounds, UPPER, df_transport, parameters_dict, sum_energy_new, df_transport_copy):
    """check that the sum of energy using the upper/lower bounds can reach the sum of energy_new. if not, this means that the bounds are too tight and we need to increase them. We will increase/decrease the upper/lower bounds for stocks so that they increase/decrease by parameters_dict['maximum_proportional_change_in_stocks'] times the required increase/decrease in energy use (if it is required) so that the required energy can be reached.
    
    after all that we finally do a check that the energy by drive type can be reached. This will be done by checking that the sum of energy using the upper bounds is greater or equal to the sum of energy_new for that drive and the sum of energy using the lower bounds is lower or equal to the sum of energy_new for that drive type (no matter whether UPPER is True or False). If not, then we will adjust the bounds enough so that the energy can be reached. to make it simple we'll adjust all bounds by an equal proportion, (except any where their stocks are already 0) so that the energy can be reached.
    
    Args:
        initial_values (_type_): _description_
        bounds (_type_): _description_
        lower_bounds (_type_): _description_
        upper_bounds (_type_): _description_
        UPPER (_type_): _description_
        df_transport (_type_): _description_
        parameters_dict (_type_): _description_
        sum_energy_new (_type_): _description_

    Raises:
        ValueError: _description_
        ValueError: _description_
        ValueError: _description_

    Returns:
        _type_: _description_
    """
    if UPPER:
        df_transport['Value'] = upper_bounds
        df_transport_other_bounds = df_transport.copy()
        df_transport_other_bounds['Value'] = lower_bounds
    else:
        df_transport['Value'] = lower_bounds
        df_transport_other_bounds = df_transport.copy()
        df_transport_other_bounds['Value'] = upper_bounds
        
    sum_energy_calc = df_transport.loc[df_transport['Measure'].isin(['Mileage', 'Stocks', 'Intensity'])].pivot(index=['Economy', 'Date', 'Medium', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive'], columns='Measure', values='Value').reset_index()
    sum_energy_calc['Energy_calc'] = (sum_energy_calc['Mileage'] * sum_energy_calc['Stocks']) * sum_energy_calc['Intensity']
    sum_energy_calc = sum_energy_calc['Energy_calc'].sum()
    EPSILON = 1e-6
    prop_difference = (sum_energy_new+EPSILON)/(sum_energy_calc+EPSILON)
    if abs(prop_difference - 1) > 0:   
        #find the change in stocks that is needed to reach the sum_energy_new
        bounds_to_check = df_transport.copy()
        bounds_to_check.loc[bounds_to_check['Measure'] == 'Stocks', 'Change_in_bounds'] = abs(bounds_to_check.loc[bounds_to_check['Measure'] == 'Stocks', 'Value'] * prop_difference - bounds_to_check.loc[bounds_to_check['Measure'] == 'Stocks', 'Value'])
        #set the chagne in the opposite bounds to this
        if UPPER:
            lower_bounds_stocks = bounds_to_check.loc[bounds_to_check['Measure'] == 'Stocks', 'Value'] - bounds_to_check.loc[bounds_to_check['Measure'] == 'Stocks', 'Change_in_bounds']
        else:
            upper_bounds_stocks = bounds_to_check.loc[bounds_to_check['Measure'] == 'Stocks', 'Value'] + bounds_to_check.loc[bounds_to_check['Measure'] == 'Stocks', 'Change_in_bounds']
            
        #Now times the cahnge in stocks by maximum_proportional_change_in_stocks to get the new change in bounds
        bounds_to_check.loc[bounds_to_check['Measure'] == 'Stocks', 'Change_in_bounds'] = bounds_to_check.loc[bounds_to_check['Measure'] == 'Stocks', 'Change_in_bounds'] * parameters_dict['maximum_proportional_change_in_stocks']    
        if UPPER:
            upper_bounds_stocks = bounds_to_check.loc[bounds_to_check['Measure'] == 'Stocks', 'Value'] + bounds_to_check.loc[bounds_to_check['Measure'] == 'Stocks', 'Change_in_bounds']
        else:
            lower_bounds_stocks = bounds_to_check.loc[bounds_to_check['Measure'] == 'Stocks', 'Value'] - bounds_to_check.loc[bounds_to_check['Measure'] == 'Stocks', 'Change_in_bounds']
        
        #if any lower bounds are less than 0, set them to 0
        lower_bounds_stocks[lower_bounds_stocks < 0] = 0
        #if any upper bounds are less than 0, set them to 0
        upper_bounds_stocks[upper_bounds_stocks < 0] = 0  
        
        #join back with the other bounds by ataching to the df and then extacting all as a series
        if UPPER:
            df_transport.loc[df_transport['Measure'] == 'Stocks', 'Value'] = upper_bounds_stocks
            upper_bounds = df_transport['Value'].to_numpy()
            df_transport_other_bounds.loc[df_transport_other_bounds['Measure'] == 'Stocks', 'Value'] = lower_bounds_stocks
            lower_bounds = df_transport_other_bounds['Value'].to_numpy()
        else:
            df_transport.loc[df_transport['Measure'] == 'Stocks', 'Value'] = lower_bounds_stocks
            lower_bounds = df_transport['Value'].to_numpy()
            df_transport_other_bounds.loc[df_transport_other_bounds['Measure'] == 'Stocks', 'Value'] = upper_bounds_stocks
            upper_bounds = df_transport_other_bounds['Value'].to_numpy()
        
        bounds = list(zip(lower_bounds, upper_bounds))
        
        #double check no lower bounds are higher than upper bounds
        if (lower_bounds > upper_bounds).any():
            breakpoint()
            raise ValueError('lower bounds are higher than upper bounds')
        #now check again taht the enegy value can be reached. This will be done by checking that the sum of energy using the upper bounds is higher than the sum of energy_new and the sum of energy using the lower bounds is lower than the sum of energy_new
        
        #clac new sum of energy using the initial values:
        #LOWER
        df_transport['Value'] = lower_bounds
        sum_energy_calc = df_transport.loc[df_transport['Measure'].isin(['Mileage', 'Stocks', 'Intensity'])].pivot(index=['Economy', 'Date', 'Medium', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive'], columns='Measure', values='Value').reset_index()
        sum_energy_calc['Energy_calc'] = (sum_energy_calc['Mileage'] * sum_energy_calc['Stocks']) * sum_energy_calc['Intensity']
        sum_energy_calc = sum_energy_calc['Energy_calc'].sum()
            
        prop_difference = (sum_energy_new+EPSILON)/(sum_energy_calc+EPSILON)
        if sum_energy_new - sum_energy_calc < 0:
            breakpoint()
            raise ValueError(f'Bounds values do not meet the constraint even after increasing the bounds,  poportional difference of sum_energy_new\\sum_energy_calc is {prop_difference}')
        # upper
        df_transport['Value'] = upper_bounds
        sum_energy_calc = df_transport.loc[df_transport['Measure'].isin(['Mileage', 'Stocks', 'Intensity'])].pivot(index=['Economy', 'Date', 'Medium', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive'], columns='Measure', values='Value').reset_index()
        sum_energy_calc['Energy_calc'] = (sum_energy_calc['Mileage'] * sum_energy_calc['Stocks']) * sum_energy_calc['Intensity']
        sum_energy_calc = sum_energy_calc['Energy_calc'].sum()
            
        prop_difference = (sum_energy_new+EPSILON)/(sum_energy_calc+EPSILON)
        if sum_energy_new - sum_energy_calc > 0:
            breakpoint()
            raise ValueError(f'Bounds values do not meet the constraint even after increasing the bounds,  poportional difference of sum_energy_new\\sum_energy_calc is {prop_difference}')
        
    #finally do a check that the energy by drive type can be reached. This will be done by checking that the sum of energy using the upper bounds is greater or equal to the sum of energy_new for that drive and the sum of energy using the lower bounds is lower or equal to the sum of energy_new for that drive type (no matter whether UPPER is True or False). If not, then we will adjust the bounds enough so that the energy can be reached. to make it simple we'll adjust all bounds by an equal proportion, (except any where their stocks are already 0 ??) so that the energy can be reached.
    # def check_bounds_by_drive(config):
    energy_target_by_drive = df_transport_copy.loc[df_transport_copy['Measure'].isin(['Energy_new'])][['Economy', 'Date', 'Medium', 'Scenario', 'Drive', 'Value']].groupby(['Economy', 'Date', 'Medium', 'Scenario', 'Drive'], as_index=False).agg({'Value':'sum'})
    
    for check in ['upper', 'lower']:
        bounds = upper_bounds if check == 'upper' else lower_bounds
        bounds = check_bounds_by_drive(config, df_transport, bounds, energy_target_by_drive, check, parameters_dict)
        #do a double check to make sure that the bounds are now correct
        bounds = check_bounds_by_drive(config, df_transport, bounds, energy_target_by_drive, check, parameters_dict, double_check=True)
        #set the bounds
        if check == 'upper':
            upper_bounds = bounds
        else:
            lower_bounds = bounds
    #zip the bounds
    bounds = list(zip(lower_bounds, upper_bounds))
    return initial_values, bounds, lower_bounds, upper_bounds

def check_bounds_by_drive(config, df_transport, bounds, energy_target_by_drive, check, parameters_dict, double_check=False):
    # Copy the original DataFrame
    energy_by_drive_check = df_transport.copy()
    
    # Set the 'Value' column to the provided bounds
    energy_by_drive_check['Value'] = bounds
    
    # Filter the DataFrame and pivot it to get the required structure
    energy_by_drive_check = energy_by_drive_check.loc[energy_by_drive_check['Measure'].isin(['Mileage', 'Stocks', 'Intensity'])].pivot(index=['Economy', 'Date', 'Medium', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive'], columns='Measure', values='Value').reset_index()
    
    # Calculate the energy
    energy_by_drive_check['Energy_calc'] = (energy_by_drive_check['Mileage'] * energy_by_drive_check['Stocks']) * energy_by_drive_check['Intensity']
    
    # Group by the required columns and sum the 'Energy_calc'
    energy_by_drive_check = energy_by_drive_check.groupby(['Economy', 'Date', 'Medium', 'Scenario', 'Drive'], as_index=False).agg({'Energy_calc':'sum'})
    
    # Merge with the energy_target_by_drive DataFrame
    energy_by_drive_check = energy_by_drive_check.merge(energy_target_by_drive, on=['Economy', 'Date', 'Medium', 'Scenario', 'Drive'], how='left')
    
    # Calculate the difference between the calculated energy and the value
    energy_by_drive_check['difference'] = energy_by_drive_check['Energy_calc'] - energy_by_drive_check['Value']
    
    # Check if we are checking for upper or lower bounds
    EPSILON = 1e-6
    if check == 'upper':
        drives = energy_by_drive_check.loc[energy_by_drive_check['difference'] < EPSILON, 'Drive'].unique().tolist()
    elif check == 'lower':
        drives = energy_by_drive_check.loc[energy_by_drive_check['difference'] > EPSILON, 'Drive'].unique().tolist()
    else:
        raise ValueError("Invalid check type. Must be 'upper' or 'lower'.")
    
    # If the condition is met and we are not double checking
    if len(drives) > 0 and not double_check:
        # Calculate the proportion difference between the calculated energy and the value. we will use that to adjust the bounds for stocks. 
        energy_by_drive_check['proportion_change'] = energy_by_drive_check['Energy_calc']/energy_by_drive_check['Value']
        energy_by_drive_check['proportion_change'] = energy_by_drive_check['proportion_change'].fillna(0)
        
        # Copy the original DataFrame and set the 'Value' column to the provided bounds
        energy_by_drive_new_bounds = df_transport.copy()
        energy_by_drive_new_bounds['Value'] = bounds
        
        # Merge with the energy_by_drive_check DataFrame
        energy_by_drive_new_bounds = energy_by_drive_new_bounds.merge(energy_by_drive_check[['Economy', 'Date', 'Medium', 'Scenario', 'Drive', 'proportion_change']], on=['Economy', 'Date', 'Medium', 'Scenario', 'Drive'], how='left')
        
        # Increase/decrease the 'Value' for 'Stocks' by the proportion increase (if check is lower its a decrease). Just dividing works here but if check is lower we wont adjust the result by max proportion increase from paramaters dict
        if check=='upper':
            proportional_increase =(parameters_dict['maximum_proportional_change_in_stocks'])
        else:
            proportional_increase=1
        #set everything we arent achanging to orignal bounds
        energy_by_drive_new_bounds.loc[(energy_by_drive_new_bounds['Measure'] != 'Stocks')| (~energy_by_drive_new_bounds['Drive'].isin(drives)), 'New_value'] = energy_by_drive_new_bounds.loc[(energy_by_drive_new_bounds['Measure'] != 'Stocks')| (~energy_by_drive_new_bounds['Drive'].isin(drives)), 'Value'] 
        #adjsut bounds of the drives we are changing using proportion change * proportional_increase
        energy_by_drive_new_bounds.loc[(energy_by_drive_new_bounds['Measure'] == 'Stocks')& (energy_by_drive_new_bounds['Drive'].isin(drives)), 'New_value'] = (energy_by_drive_new_bounds.loc[(energy_by_drive_new_bounds['Measure'] == 'Stocks')& (energy_by_drive_new_bounds['Drive'].isin(drives)), 'Value'] / (energy_by_drive_new_bounds.loc[(energy_by_drive_new_bounds['Measure'] == 'Stocks')& (energy_by_drive_new_bounds['Drive'].isin(drives)), 'proportion_change']))*proportional_increase
        
        #repalce any infs or nas with 0
        energy_by_drive_new_bounds['New_value'] = energy_by_drive_new_bounds['New_value'].replace([np.inf, -np.inf], np.nan).fillna(0)
        # Update the bounds
        bounds = energy_by_drive_new_bounds['New_value'].to_numpy()
    # If the condition is met and we are double checking
    elif len(drives) > 0 and double_check:
        BOUNDS_FIXED = False
        if check == 'upper':
            bounds, BOUNDS_FIXED = fix_zero_stocks_for_drive_type(config, df_transport, parameters_dict, energy_by_drive_check, bounds, zero_drives=['cng', 'lpg'])
        if not BOUNDS_FIXED:
            breakpoint()
            raise ValueError(f'Bounds values do not meet the constraint even after increasing the bounds for {drives}')
    else:
        pass
    
    # Return the updated bounds
    return bounds
    

def fix_zero_stocks_for_drive_type(config, df_transport, parameters_dict, energy_by_drive_check, bounds, zero_drives=['cng', 'lpg']):
    #check the cause isnt specific, unlikely drive types liek cng and lpg arent zero for stocks for all road types. we need at least one row to be non zero or else we cant calculate energy. so check that cng and/or lpg dont sum to zero stocks, and if they do, find the avg amount of stocks using the avg mileage and intensity that would be required to make up for it. then make that the upper bounds for cng and/or lpg for every vehcile type.
    #get the sum of stocks for cng and lpg
    sum_stocks_cng_lpg = df_transport.loc[(df_transport['Measure'] == 'Stocks')&(df_transport['Vehicle Type'].isin(zero_drives))].groupby(['Economy', 'Drive'], as_index=False).agg({'Value':'sum'})
    BOUNDS_FIXED = False
    #check if sum is 0
    for drive in zero_drives:
        if sum_stocks_cng_lpg.loc[sum_stocks_cng_lpg['Drive'] == drive, 'Value'].sum() == 0:
            #divide the required energy use by the avg intensity and mileage of all  vehicle types fort this drive to get the required avg stocks to fullfill all that energy use. and then times it by parameters_dict['maximum_proportional_change_in_stocks'] to get the new bounds
            required_energy_use =energy_by_drive_check.loc[energy_by_drive_check['Drive'] == drive, 'Value'].sum()
            avg_intensity = df_transport.loc[(df_transport['Measure'] == 'Intensity')&(df_transport['Drive'] == drive), 'Value'].mean()
            avg_mileage = df_transport.loc[(df_transport['Measure'] == 'Mileage')&(df_transport['Drive'] == drive), 'Value'].mean()
            required_stocks = required_energy_use / (avg_intensity * avg_mileage)
            #now times it by parameters_dict['maximum_proportional_change_in_stocks'] to get the new bounds
            required_stocks = required_stocks * parameters_dict['maximum_proportional_change_in_stocks']
            #now set the bounds for cng and/or lpg to this
            df_transport['Value'] = bounds
            df_transport.loc[(df_transport['Measure'] == 'Stocks')&(df_transport['Drive'] == drive), 'Value'] = required_stocks
            bounds = df_transport['Value'].to_numpy() 
            BOUNDS_FIXED = True
            
    return bounds, BOUNDS_FIXED
       
def plot_optimisation_results(config, optimised_data, input_data_new_road_df, results_dict, PLOT_NO_RESULTS=False):
    #for every economy, year and scenario, we will show the % differene between teh values in a bar chart with a facet for each measure.
    NO_RESULTS=False
    if optimised_data.Value.isna().all():
        print('no optimisation results to plot, so you will just see the original data')
        NO_RESULTS=True
        # return
    input_data_new_road = input_data_new_road_df.copy()
    #convert efficiency to intensity
    input_data_new_road['Intensity'] = 1/input_data_new_road['Efficiency']
    input_data_new_road.drop(['Efficiency'], axis=1, inplace=True)
    
    #set up original data
    df_original = input_data_new_road.melt(id_vars=['Economy', 'Date', 'Medium', 'Scenario', 'Transport Type','Vehicle Type', 'Drive'], value_name='Value', var_name='Measure').reset_index(drop=True)
    
    #filter for vlaues in both
    df_optimised = optimised_data.loc[(optimised_data['Economy'] == results_dict["Economy"]) & (optimised_data['Date'] == results_dict["Date"]) & (optimised_data['Scenario'] == results_dict["Scenario"])].copy()
    
    df_original = df_original.loc[(df_original['Economy'] == results_dict["Economy"]) & (df_original['Date'] == results_dict["Date"]) & (df_original['Scenario'] == results_dict["Scenario"])].copy()
    
    time = results_dict['time_to_run']
    method = results_dict['method']
    parameters_dict = results_dict['parameters_dict']
    
    #get sum of values in parameters dict so we can use it in file id:
    param_id = round(sum(parameters_dict.values()),3)
    
    #in df_optimised extract the rows for measure = Energy_new and call them Energy_optimised_vs_energy_input. This will allow us to compare the optimised energy to the energy that was inputted (not based on EGEDA/ESTO or the optimisation)
    df_optimised_energy = df_optimised.loc[df_optimised['Measure'] == 'Energy_new'].copy()
    df_optimised_energy['Measure'] = 'Energy_optimised_vs_energy_input'
    df_optimised_energy2 = df_optimised_energy.copy()
    df_optimised_energy2['Measure'] = 'Energy_optimised_vs_esto_energy'
    # df_optimised['Measure'] = 'Energy_optimised_vs_esto_energy'
    df_optimised_energy = pd.concat([df_optimised_energy2, df_optimised_energy])
    #and rename the Energy_old and Energy_new
    df_original['Measure'] = df_original['Measure'].replace({'Energy_new':'Energy_optimised_vs_esto_energy', 'Energy_old':'Energy_optimised_vs_energy_input'})
    #merge them to calcualte the % difference
    df_optimised_merge = df_optimised_energy.merge(df_original, on=['Economy', 'Date', 'Medium', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Measure'], suffixes=('_optimised', '_original'))

    #we also want to clauclate % difference for total energy for the drive, and drive and vehicle type combinations so we will sum the energy for each 'Economy', 'Date', 'Medium', 'Scenario', 'Measure and then put them back in df
    energy = df_optimised_merge.loc[df_optimised_merge['Measure'].isin(['Energy_optimised_vs_energy_input',  'Energy_optimised_vs_esto_energy']), ['Economy', 'Date', 'Medium', 'Scenario', 'Measure', 'Vehicle Type', 'Drive', 'Value_original', 'Value_optimised']].copy()
    sum_by_vehicle_type = energy.groupby(['Economy', 'Date', 'Medium', 'Scenario', 'Measure', 'Vehicle Type'])[['Value_original', 'Value_optimised']].sum().reset_index()
    sum_by_vehicle_type['Drive'] = 'All'
    sum_by_drive = energy.groupby(['Economy', 'Date', 'Medium', 'Scenario', 'Measure', 'Drive'])[['Value_original', 'Value_optimised']].sum().reset_index()
    sum_by_drive['Vehicle Type'] = 'All'
    sum_by_all = energy.groupby(['Economy', 'Date', 'Medium', 'Scenario', 'Measure'])[['Value_original', 'Value_optimised']].sum().reset_index()
    sum_by_all['Vehicle Type'] = 'All'
    sum_by_all['Drive'] = 'All'
    
    #if the sum of abs difference between energy for 'Value_original', 'Value_optimised' in sum_by_drive for Energy_optimised_vs_esto_energy is greater than 10% of the sum of 'Value_original' in sum_by_drive, then dont plot, since its not a useful result at all
    sum_by_drive_test = sum_by_drive.copy()
    sum_by_drive_test = sum_by_drive_test.loc[sum_by_drive_test['Measure'] == 'Energy_optimised_vs_esto_energy']
    if (sum(abs(sum_by_drive_test['Value_original'] - sum_by_drive_test['Value_optimised'])) > sum(sum_by_drive_test['Value_original']) * 0.1) and not NO_RESULTS:
        breakpoint()
        print(f'Energy difference between optimised and original esto values is greater than 10% of the sum of energy for {results_dict["Economy"]}, {results_dict["Date"]}, {results_dict["Scenario"]} with file_id: {results_dict["file_id"]} and param_id: {param_id}')
        
    df_all = pd.concat([df_optimised_merge, sum_by_vehicle_type, sum_by_drive, sum_by_all])
    
    df_all[f'pct_diff'] = ((df_all[f'Value_optimised'] - df_all[f'Value_original']) / df_all[f'Value_original'])*100
    
    df_all = df_all.loc[df_all['Measure'].isin(['Mileage', 'Stocks', 'Intensity', 'Energy_optimised_vs_energy_input', 'Energy_optimised_vs_esto_energy'])].copy()
    
    #just to make it clear we will adjsut the measures so they specify what comarpsions are being made:
    measures_dict = {'Mileage':'% Difference between input and optimised Mileage', 'Stocks':'% Difference between input and optimised Stocks', 'Intensity':'% Difference between input and optimised Intensity', 'Energy_optimised_vs_energy_input':'% Difference between ESTO energy and optimised energy', 'Energy_optimised_vs_esto_energy':'% Difference between input and optimised Energy'}
    df_all_pct_diff = df_all.copy()
    df_all_pct_diff['Measure'] = df_all_pct_diff['Measure'].map(measures_dict)
    
    # #drop '% Difference between input (step 2) and optimised Energy'. Dont hink we need it
    # df_all_pct_diff = df_all_pct_diff.loc[df_all_pct_diff['Measure'] != '% Difference between input (step 2) and optimised Energy']
        
    if not NO_RESULTS:
        try:
            
            df_all_pct_diff_eds = df_all_pct_diff.loc[(df_all_pct_diff['Economy'] == results_dict["Economy"]) & (df_all_pct_diff['Date'] == results_dict["Date"]) & (df_all_pct_diff['Scenario'] == results_dict["Scenario"])].copy()
            #plot as bar using px.bar
            fig = px.bar(df_all_pct_diff_eds, x='Vehicle Type', y='pct_diff', color='Drive', barmode='group', facet_col='Measure', facet_col_wrap=2, title=f'{method} in {round(time, 2)} seconds with {str(parameters_dict.values())}')
            #make the y axis independent for each facet
            fig.update_yaxes(matches=None)
            fig.write_html(config.root_dir + '\\' +f'plotting_output\\input_exploration\\optimisation_reestimations\\{results_dict["Economy"]}_{results_dict["Date"]}_{results_dict["method"]}_{param_id}.html')
            
            #write the data to a csv so we can inspect it if it seems fishy 'plotting_output\\input_exploration\\optimisation_reestimations\\{results_dict["Economy"]}_{results_dict["Date"]}_{results_dict["Scenario"]}_{param_id}.csv'
            df_all_pct_diff_eds.to_csv(config.root_dir + '\\' + f'plotting_output\\input_exploration\\optimisation_reestimations\\{results_dict["Economy"]}_{results_dict["Date"]}_{results_dict["method"]}_{param_id}.csv')
        except:
            print(f'could not plot for {results_dict["Economy"]}_{results_dict["Date"]}_{results_dict["Scenario"]}_{param_id}')
                
    #PLOT ABSOLUTE VALUES
    #loop through different results_dict.keys()
    #and to make it clear just plot a comparison of all the measures in a bar chart using the absolute values. To do this, jsut melt the Value cols with an index col called 'optimised' and then plot as bar using px.bar
    #drop [f'pct_diff']
    df_all = df_all.drop(columns=['pct_diff'])
    
    df_all_long = df_all.melt(id_vars=['Economy', 'Date', 'Medium', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Measure'], value_name='Value', var_name='optimised')
    #and replace names of optimised cols with 'optimised' and 'old'
    optimised_dict = {'Value_optimised':'optimised', 'Value_original':'old'}
    df_all_long['optimised'] = df_all_long['optimised'].map(optimised_dict)
    
    #since we're not plotting by vehicle type in this plot, drop where drive is all but vehicle type is not all
    df_all_long = df_all_long.loc[~((df_all_long['Drive'] == 'All') & (df_all_long['Vehicle Type'] != 'All'))]
    #also drop where drive is not all but vehicle type is all
    df_all_long = df_all_long.loc[~((df_all_long['Drive'] != 'All') & (df_all_long['Vehicle Type'] == 'All'))]
    
    df_all_long_eds = df_all_long.loc[(df_all_long['Economy'] == results_dict["Economy"]) & (df_all_long['Date'] == results_dict["Date"]) & (df_all_long['Scenario'] == results_dict["Scenario"])].copy()
    
    if NO_RESULTS:
        #drop optimised
        df_all_long_eds = df_all_long_eds.loc[df_all_long_eds['optimised'] == 'old']
        if not PLOT_NO_RESULTS:
            return
    fig = px.bar(df_all_long_eds, x='Drive', y='Value', color='optimised', barmode='group', facet_col='Measure', hover_data=['Vehicle Type'], facet_col_wrap=2, title=f'{method} in {round(time, 2)} seconds with {str(parameters_dict.values())}')
    fig.update_yaxes(matches=None)
    fig.write_html(config.root_dir + '\\' +f'plotting_output\\input_exploration\\optimisation_reestimations\\{results_dict["Economy"]}_{results_dict["Date"]}_{results_dict["method"]}_{param_id}_energy_comparison.html')
    #write the data to a csv so we can inspect it if it seems fishy 
    df_all_long_eds.to_csv(config.root_dir + '\\' + f'plotting_output\\input_exploration\\optimisation_reestimations\\{results_dict["Economy"]}_{results_dict["Date"]}_{results_dict["method"]}_{param_id}_energy_comparison.csv')
     
    return
    
#%%
def optimisation_handler_testing(config, ECONOMY_ID, input_data_new_road_df=None, SAVE_ALL_RESULTS=True, SAVE_INDIVIDUAL_RESULTS=False, REMOVE_NON_MAJOR_VARIABLES=True, USE_MOVE_ELECTRICITY_USE_IN_ROAD_TO_RAIL_ESTO=True, USE_SAVED_OPT_PARAMATERS=False, parameters_ranges=None, methods_list=None, PARAMETERS_RANGES_KEY='ALL'):
    """This function enables easy testing of the optimisation method. It takes in data saved at the beginning of the latest optimisation process so it can be used to test different methods/params etc.

    Args:
        ECONOMY_ID (_type_): _description_
        input_data_new_road (_type_, optional): _description_. Defaults to None.
        SAVE_ALL_RESULTS (bool, optional): _description_. Defaults to False.
    """
    #note that energy_new is the energy we want to optimise for, to achive. energy old is what  we have using the current values (stocks, mileage, eff etc).
    all_outputs = pd.DataFrame()
    all_results_dicts = {}
    
    if parameters_ranges is None and methods_list is None:
        #These are the full set of paramter ranges we can iterate over. load it in from a yaml file
        parameters_ranges, methods_list = load_in_optimisation_parameters(config, PARAMETERS_RANGES_KEY)
    elif parameters_ranges is None and methods_list is not None:
        #These are the full set of paramter ranges we can iterate over. load it in from a yaml file
        parameters_ranges = load_in_optimisation_parameters(config, PARAMETERS_RANGES_KEY)[0]
    elif parameters_ranges is not None and methods_list is None:
        #These are the full set of paramter ranges we can iterate over. load it in from a yaml file
        methods_list = load_in_optimisation_parameters(config, PARAMETERS_RANGES_KEY)[1]
    if parameters_ranges is not None and ECONOMY_ID == '13_PNG':
        # breakpoint()
        print('Adding extended ranges for stocks and mileage for PNG to parameters_ranges.')
        parameters_ranges['maximum_proportional_change_in_mileage'] += [0.5, 1]
        parameters_ranges['maximum_proportional_change_in_stocks'] += [10,30,50,100]
        parameters_ranges['STOCKS_PER_CAPITA_PCT_DIFF_THRESHOLD'] = [0.8, 1]
    if USE_SAVED_OPT_PARAMATERS:
        #if we can just use the saved params in the optimisation_parameters.yml file to save time
        parameters_ranges_, method_ = load_in_optimisation_parameters(config, ECONOMY_ID)
        
        if parameters_ranges_ is None:
            #use global parameters
            all_params = [dict(zip(parameters_ranges.keys(), values)) for values in product(*parameters_ranges.values())]
        else:
            #because sometimes prev used params dont result in success we will just try them first, but then also try the global params if they dont work
            all_params = [dict(zip(parameters_ranges_.keys(), values)) for values in product(*parameters_ranges_.values())] + [dict(zip(parameters_ranges.keys(), values)) for values in product(*parameters_ranges.values())]
            methods_list = [method_] + methods_list
    else:
        all_params = [dict(zip(parameters_ranges.keys(), values)) for values in product(*parameters_ranges.values())]

    #drop any duplicates in methods_list, but always keep the first one
    methods_list = list(dict.fromkeys(methods_list))
    #now loop through all_params and methods_list
    for parameters_dict in all_params:
        for method in methods_list:
            if input_data_new_road_df is None:
                input_data_new_road = pd.read_pickle(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\input_data_new_road_{ECONOMY_ID}.pkl')
            else:
                input_data_new_road = input_data_new_road_df.copy()
            optimised_data, results_dict = optimise_to_find_base_year_values(config, input_data_new_road,ECONOMY_ID, methods=[method], all_parameters_dicts=[parameters_dict], REMOVE_NON_MAJOR_VARIABLES=REMOVE_NON_MAJOR_VARIABLES, USE_MOVE_ELECTRICITY_USE_IN_ROAD_TO_RAIL_ESTO=USE_MOVE_ELECTRICITY_USE_IN_ROAD_TO_RAIL_ESTO)
            
            file_id = datetime.datetime.now().strftime("%Y%m%d_%H%M") 
            results_dict['file_id'] = file_id
            
            if optimised_data is None:
                #no values returned so go to next
                print(f'No values returned for {ECONOMY_ID} with file_id: {file_id}, going to next iteration after this one for {method} and parameters_dict: {parameters_dict}')
                #frist plot
                optimised_data = input_data_new_road.copy()
                #set it up to be in the same format as the optimised data would be 
                optimised_data = input_data_new_road.melt(id_vars=['Economy', 'Date', 'Medium', 'Scenario', 'Transport Type','Vehicle Type', 'Drive'], value_name='Value', var_name='Measure').reset_index(drop=True)
                optimised_data['Value'] = np.nan
                
                plot_optimisation_results(config, optimised_data, input_data_new_road, results_dict=results_dict)
                continue      
            plot_optimisation_results(config, optimised_data, input_data_new_road, results_dict=results_dict)
            
            #return intensity to efficiency
            optimised_data.loc[optimised_data['Measure'] == 'Intensity', 'Value'] = 1/ optimised_data.loc[optimised_data['Measure'] == 'Intensity', 'Value']
            optimised_data.loc[optimised_data['Measure'] == 'Intensity', 'Measure'] = 'Efficiency'
            
            #save all outputs with file_date_id with mins and hours
            if SAVE_INDIVIDUAL_RESULTS:
                print(f'Saving optimisation outputs and results dicts for {ECONOMY_ID} with file_id: {file_id}')
                pickle.dump(results_dict, open(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\results_dict_{ECONOMY_ID}_{file_id}_{config.transport_data_system_FILE_DATE_ID}.pkl', 'wb'))
                optimised_data.to_pickle(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\optimised_data_{ECONOMY_ID}_{file_id}_{config.transport_data_system_FILE_DATE_ID}.pkl')             
                
            all_outputs = pd.concat([all_outputs, optimised_data])
            all_results_dicts[(ECONOMY_ID, method, round(sum(parameters_dict.values()),3))] = results_dict
            
    
    #save all outputs with file_date_id with mins and hours
    if SAVE_ALL_RESULTS:
        file_id = datetime.datetime.now().strftime("%Y%m%d_%H%M") 
        all_outputs.to_pickle(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\all_outputs_{ECONOMY_ID}_{file_id}_{config.transport_data_system_FILE_DATE_ID}.pkl')
        pickle.dump(all_results_dicts, open(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\all_results_dicts_{ECONOMY_ID}_{file_id}_{config.transport_data_system_FILE_DATE_ID}.pkl', 'wb'))
        
  
def optimisation_handler(config, input_data_new_road, SAVE_ALL_RESULTS=False, method='L-BFGS-B', PLOT=False, REMOVE_NON_MAJOR_VARIABLES=True, USE_MOVE_ELECTRICITY_USE_IN_ROAD_TO_RAIL_ESTO=True, USE_SAVED_OPT_PARAMATERS=False, parameters_ranges = None, methods_list=None, PARAMETERS_RANGES_KEY='ALL'):
    ECONOMY_ID = input_data_new_road['Economy'].unique()[0]
    file_id = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    input_data_new_road.to_pickle(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\input_data_new_road_actual_run_{ECONOMY_ID}_{config.FILE_DATE_ID}_{config.transport_data_system_FILE_DATE_ID}.pkl')
    #note that energy_new is the energy we want to optimise for, to achive. energy old is what  we have using the current values (stocks, mileage, eff etc).
    if parameters_ranges is None:
        #These are the full set of paramter ranges we can iterate over. load it in from a yaml file
        parameters_ranges, methods_list = load_in_optimisation_parameters(config, PARAMETERS_RANGES_KEY)
    elif parameters_ranges is None and methods_list is not None:
        #These are the full set of paramter ranges we can iterate over. load it in from a yaml file
        parameters_ranges = load_in_optimisation_parameters(config, PARAMETERS_RANGES_KEY)[0]
    elif parameters_ranges is not None and methods_list is None:
        #These are the full set of paramter ranges we can iterate over. load it in from a yaml file
        methods_list = load_in_optimisation_parameters(config, PARAMETERS_RANGES_KEY)[1]
    if parameters_ranges is not None and ECONOMY_ID == '13_PNG':
        print('Adding extended ranges for stocks and mileage for PNG to parameters_ranges.')
        # breakpoint()
        parameters_ranges['maximum_proportional_change_in_mileage'] += [0.5, 1]
        parameters_ranges['maximum_proportional_change_in_stocks'] += [10,30,50,100]
        parameters_ranges['STOCKS_PER_CAPITA_PCT_DIFF_THRESHOLD'] = [0.8, 1]
    # Generate all combinations of parameters
    if USE_SAVED_OPT_PARAMATERS:
        #if we can just use the saved params in the optimisation_parameters.yml file to save time
        parameters_ranges_, method_ = load_in_optimisation_parameters(config, ECONOMY_ID)
        if parameters_ranges_ is None:
            #use global parameters
            all_params = [dict(zip(parameters_ranges.keys(), values)) for values in product(*parameters_ranges.values())]
            methods_list = [method]
        else:
            #because sometimes prev used params dont result in success we will just try them first, but then also try the global params if they dont work
            all_params = [dict(zip(parameters_ranges_.keys(), values)) for values in product(*parameters_ranges_.values())] + [dict(zip(parameters_ranges.keys(), values)) for values in product(*parameters_ranges.values())]
            methods_list = [method_] + [method]
    else:
        #use global parameters
        all_params = [dict(zip(parameters_ranges.keys(), values)) for values in product(*parameters_ranges.values())]
        methods_list = [method]
    #drop any duplicates in methods_list, but always keep the first one
    methods_list = list(dict.fromkeys(methods_list))
    #bow loop through all_params and methods_list and find the first one that works in optimise_to_find_base_year_values
    
    optimised_data, results_dict = optimise_to_find_base_year_values(config, input_data_new_road,ECONOMY_ID, methods=methods_list, all_parameters_dicts=all_params,  REMOVE_NON_MAJOR_VARIABLES=REMOVE_NON_MAJOR_VARIABLES,USE_MOVE_ELECTRICITY_USE_IN_ROAD_TO_RAIL_ESTO=USE_MOVE_ELECTRICITY_USE_IN_ROAD_TO_RAIL_ESTO)
    results_dict['file_id'] = file_id
    if optimised_data is None:
        #no values returned so throw error
        input_data_new_road.to_pickle(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\failed_run_input_data_new_road_{ECONOMY_ID}_{file_id}_{config.transport_data_system_FILE_DATE_ID}.pkl')
        #plot the input data so user can try identify why it failed. 
        #first create a results df so we can use the plot_optimisation_results function:
        optimised_data = input_data_new_road.copy()
        #set it up to be in the same format as the optimised data would be 
        optimised_data = input_data_new_road.melt(id_vars=['Economy', 'Date', 'Medium', 'Scenario', 'Transport Type','Vehicle Type', 'Drive'], value_name='Value', var_name='Measure').reset_index(drop=True)
        #set the value to nan so it doesnt plot
        optimised_data['Value'] = np.nan
        plot_optimisation_results(config, optimised_data, input_data_new_road, results_dict=results_dict)       
            
        raise ValueError('no values returned from optimisation. data saved so you can test different methods\\params etc. at {}'.format(f'intermediate_data\\analysis_single_use\\failed_run_input_data_new_road_{ECONOMY_ID}_{file_id}_{config.transport_data_system_FILE_DATE_ID}.pkl'))
    
    if PLOT:
        plot_optimisation_results(config, optimised_data, input_data_new_road, results_dict=results_dict)
    
    #return intensity to efficiency
    optimised_data.loc[optimised_data['Measure'] == 'Intensity', 'Value'] = 1/ optimised_data.loc[optimised_data['Measure'] == 'Intensity', 'Value']
    optimised_data.loc[optimised_data['Measure'] == 'Intensity', 'Measure'] = 'Efficiency'
    
    #save all outputs with file_date_id with mins and hours
    if SAVE_ALL_RESULTS:
        print(f'Saving all optimisation outputs and results dicts for {ECONOMY_ID} with file_id: {file_id}')
        pickle.dump(results_dict, open(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\results_dict_{ECONOMY_ID}_{file_id}_{config.transport_data_system_FILE_DATE_ID}.pkl', 'wb'))
        optimised_data.to_pickle(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\optimised_data_{ECONOMY_ID}_{file_id}_{config.transport_data_system_FILE_DATE_ID}.pkl')       
           
    #save final resutls to a more permanent location:
    optimised_data.to_pickle(config.root_dir + '\\' + f'intermediate_data\\input_data_optimisations\\optimised_data_{ECONOMY_ID}_{config.FILE_DATE_ID}_{config.transport_data_system_FILE_DATE_ID}.pkl')         
    
    save_and_overwrite_parameters_in_yaml(config, ECONOMY_ID, results_dict)
    
    return optimised_data

def save_and_overwrite_parameters_in_yaml(config, ECONOMY_ID, results_dict):
    #save parameters to a yaml file. if there are parameters already in the yaml file, then overwrite them.
    #just in case, save the original yaml file with a date id to config/archive
    
    #load yaml
    with open(config.root_dir + '\\' + 'config\\optimisation_parameters.yml') as file:
        parameters_dict = yaml.load(file, Loader=yaml.FullLoader)
    
    if parameters_dict is not None:
        if ECONOMY_ID in parameters_dict.keys():
            #add methid to parameters dict
            parameters_dict[ECONOMY_ID]['method'] = results_dict['method']
            #save as new file to archive with just that economy and date id
            with open(config.root_dir + '\\' + f'config\\archive\\optimisation_parameters_{ECONOMY_ID}_{config.FILE_DATE_ID}_{config.transport_data_system_FILE_DATE_ID}.yml', 'w') as file:
                yaml.dump(parameters_dict[ECONOMY_ID], file)
    else:
        parameters_dict = {}
        
    #update with new parameters for economy
    parameters_dict[ECONOMY_ID] = results_dict['parameters_dict']
    
    #add methid to parameters dict
    parameters_dict[ECONOMY_ID]['method'] = results_dict['method']
    #save
    with open(config.root_dir + '\\' + 'config\\optimisation_parameters.yml', 'w') as file:
        yaml.dump(parameters_dict, file)
#%%
def plot_data_from_saved_results(config, ECONOMY_ID, FILE_DATE_ID=None, FILE_DATE_ID_MIN_HOURS=None, BY_FILE_NAME=False, optimised_data_filename=None, input_data_new_road_filename=None, results_dict_filename=None):
    #note that energy_new is the energy we want to optimise for, to achive. energy old is what  we have using the current values (stocks, mileage, eff etc).
    #if the FIlE_DATE_ID is None, and FILE_DATE_ID_MIN_HOURS is None, then we will just plot the latest results. But then if FILE_DATE_ID_MIN_HOURS is not None, then we will plot the results for that FILE_DATE_ID_MIN_HOURS. If only FILE_DATE_ID is available, then we will plot all the results for that FILE_DATE_ID by using str.contains(FILE_DATE_ID) to filter the results.
    if BY_FILE_NAME:
        breakpoint()
        input_data_new_road = pd.read_pickle(input_data_new_road_filename)
        optimised_data = pd.read_csv(optimised_data_filename)
        results_dict = pickle.load(open(results_dict_filename, 'rb'))
        plot_optimisation_results(config, optimised_data, input_data_new_road, results_dict=results_dict)
    elif FILE_DATE_ID_MIN_HOURS is not None:
        FILE_DATE_ID = FILE_DATE_ID_MIN_HOURS.split('_')[0]
        input_data_new_road = pd.read_pickle(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\input_data_new_road_actual_run_{ECONOMY_ID}_{FILE_DATE_ID}_{config.transport_data_system_FILE_DATE_ID}.pkl')

        optimised_data = pd.read_pickle(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\optimised_data_{ECONOMY_ID}_{FILE_DATE_ID_MIN_HOURS}_{config.transport_data_system_FILE_DATE_ID}.pkl')

        results_dict = pickle.load(open(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\results_dict_{ECONOMY_ID}_{FILE_DATE_ID_MIN_HOURS}_{config.transport_data_system_FILE_DATE_ID}.pkl', 'rb'))
        plot_optimisation_results(config, optimised_data, input_data_new_road, results_dict=results_dict)
    elif FILE_DATE_ID is not None:
        for file in os.listdir(config.root_dir + '\\' + 'intermediate_data\\analysis_single_use\\'):
            if file.startswith(f'results_dict_{ECONOMY_ID}_{FILE_DATE_ID}'):
                MIN_HOURS = file.split('_')[-1].split('.')[0]
                FILE_DATE_ID_MIN_HOURS = f'{FILE_DATE_ID}_{MIN_HOURS}'
                input_data_new_road = pd.read_pickle(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\input_data_new_road_actual_run_{ECONOMY_ID}_{FILE_DATE_ID}_{config.transport_data_system_FILE_DATE_ID}.pkl')
                optimised_data = pd.read_pickle(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\optimised_data_{ECONOMY_ID}_{FILE_DATE_ID_MIN_HOURS}_{config.transport_data_system_FILE_DATE_ID}.pkl')
                results_dict = pickle.load(open(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\results_dict_{ECONOMY_ID}_{FILE_DATE_ID_MIN_HOURS}_{config.transport_data_system_FILE_DATE_ID}.pkl', 'rb'))
                plot_optimisation_results(config, optimised_data, input_data_new_road, results_dict=results_dict)
    else:
        #find latest file_date_id
        file_date_ids = []
        for file in os.listdir(config.root_dir + '\\' + 'intermediate_data\\analysis_single_use\\'):
            if file.startswith(f'results_dict_{ECONOMY_ID}_'):
                file_date_ids.append(file.split('_')[-1].split('.')[0])
        file_date_ids.sort()
        FILE_DATE_ID_MIN_HOURS = file_date_ids[-1]
        input_data_new_road = pd.read_pickle(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\input_data_new_road_actual_run_{ECONOMY_ID}_{FILE_DATE_ID}_{config.transport_data_system_FILE_DATE_ID}.pkl')
        optimised_data = pd.read_pickle(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\opti    mised_data_{ECONOMY_ID}_{FILE_DATE_ID_MIN_HOURS}_{config.transport_data_system_FILE_DATE_ID}.pkl')
        results_dict = pickle.load(open(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\results_dict_{ECONOMY_ID}_{FILE_DATE_ID_MIN_HOURS}_{config.transport_data_system_FILE_DATE_ID}.pkl', 'rb'))
        #breakpoint()
        plot_optimisation_results(config, optimised_data, input_data_new_road, results_dict=results_dict)
        
        
#%%

#create parameters ranges for png where we have much larger proportional changes in stocks and mileage allowed:
for ECONOMY_ID in ['08_JPN']:#01_AUS, '03_CDA', '01_AUS']:
# ECONOMY_ID = '08_JPN'
    REMOVE_NON_MAJOR_VARIABLES=False
    USE_MOVE_ELECTRICITY_USE_IN_ROAD_TO_RAIL_ESTO=True
    USE_SAVED_OPT_PARAMATERS=True
    # input_data_new_road = pd.read_pickle(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\input_data_new_road_actual_run_08_JPN_20240611_DATE20240605.pkl')
    
    # input_data_new_road = pd.read_pickle(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\input_data_new_road_actual_run_15_PHL_20240530.pkl')
    
    # input_data_new_road_actual_run_01_AUS_20240311_DATE20240304_DATE20240215
    
    # input_data_new_road = pd.read_pickle(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\input_data_new_road_actual_run_01_AUS_20240311_DATE20240304_DATE20240215.pkl')
    # # # # # # # # # # # # # input_data_new_road = pd.read_pickle(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\failed_run_input_data_new_road_05_PRC_20231120_1341_DATE20231106.pkl')
    # # # # # # # # # # # input_data_new_road = pd.read_pickle(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\input_data_new_road_actual_run_21_VN_20231128_DATE20231106.pkl')
    # # # # # # # # # # # # # # input_data_new_road = pd.read_pickle(config.root_dir + '\\' + f' \\analysis_single_use\\failed_run_input_data_new_road_20_USA_20231010HYUJ7NADZXQE 1613_DATE20231010_DATE20231010.pkl')
    # plotting_output/input_exploration/{economy}_{year}_{scenario}_{results_dict["file_id"]}_UNSUCCESSFUL.pkl
    # # # # # # # # # # # #%%
    # optimisation_handler_testing(config, ECONOMY_ID, input_data_new_road_df=input_data_new_road, SAVE_ALL_RESULTS=True,SAVE_INDIVIDUAL_RESULTS=True, REMOVE_NON_MAJOR_VARIABLES=REMOVE_NON_MAJOR_VARIABLES, USE_MOVE_ELECTRICITY_USE_IN_ROAD_TO_RAIL_ESTO=USE_MOVE_ELECTRICITY_USE_IN_ROAD_TO_RAIL_ESTO, USE_SAVED_OPT_PARAMATERS=USE_SAVED_OPT_PARAMATERS, PARAMETERS_RANGES_KEY='ALL2')
    # plot_data_from_saved_results(config, '08_JPN',FILE_DATE_ID_MIN_HOURS=None, FILE_DATE_ID=config.FILE_DATE_ID)#'20231128')#FILE_DATE_ID='20230917')#, #optimised_data_08_JPN_20230917_0425
    
#%%
# plot_data_from_saved_results(config, '13_PNG',BY_FILE_NAME=True, optimised_data_filename=config.root_dir + '\\' + 'plotting_output\\input_exploration\\optimised_data_13_PNG_2021_Reference_20240528_1840_UNSUCCESSFUL.csv', input_data_new_road_filename=f'intermediate_data\\analysis_single_use\\input_data_new_road_actual_run_{ECONOMY_ID}_20240306_DATE20240304_DATE20240215.pkl', results_dict_filename=config.root_dir + '\\' + 'plotting_output\\input_exploration\\results_dict_13_PNG_2021_Reference_20240528_1840_UNSUCCESSFUL.pkl')
                             
#                              #'20231128')#FILE_DATE_ID='20230917')#, #optimised_data_08_JPN_20230917_0425#trying to save pong rsults from \\plotting_output\\input_exploration e.g 13_PNG_2021_Reference_20240307_1246_UNSUCCESSFUL.pkl
#%%
#%%
# results_dict = pd.read_pickle(config.root_dir + '\\' + f'intermediate_data\\analysis_single_use\\results_dict_15_PHL_20240105_1154_DATE20231213.pkl')
# %%


# # #%%
# with open(config.root_dir + '\\' + 'inputs_to_objective_function_handler.pkl', 'rb') as f:
#     inputs = pickle.load(f)

# # Now you can access the inputs like this:
# method = inputs['method']
# initial_values = inputs['initial_values']
# df_transport = inputs['df_transport']
# actual_values = inputs['actual_values']
# parameters_dict = inputs['parameters_dict']
# actual_energy_by_drive = inputs['actual_energy_by_drive']
# constraints = inputs['constraints']
# bounds = inputs['bounds']
# stocks_per_capita_constants = inputs['stocks_per_capita_constants']

# result = objective_function_handler(config, method, initial_values, df_transport, actual_values, parameters_dict,actual_energy_by_drive, constraints, bounds, stocks_per_capita_constants) 


# #%%