#######################################################################
#%%
#Calcualtions
#set working directory as one folder back so that config works
import os
import sys
import re
sys.path.append(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
import numpy as np
from scipy.optimize import newton
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
current_working_dir = os.getcwd()
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = re.split('transport_model_9th_edition', script_dir)[0] + 'transport_model_9th_edition'
if current_working_dir == script_dir: #this allows the script to be run directly or from the main.py file as you cannot use relative imports when running a script directly
    # Modify sys.path to include the directory where utility_functions is located
    sys.path.append(f"{root_dir}/workflow/utility_functions")
    sys.path.append(f"{root_dir}/config")
    import config
    import utility_functions
else:
    # Assuming the script is being run from main.py located at the root of the project, we want to avoid using sys.path.append and instead use relative imports 
    from ..utility_functions import *
    from ...config.config import *
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
import plotly.graph_objects as go
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.optimize import minimize
#######################################################################
#%%
#Will produce a funtion for estiamting gompertz parameters for different economies given their historical data on stocks per cpaita and gdp_per_capita, gamma values and an estiamte for where the stocks per cpaita should be in 2045 and 2050, with the forecasted gdp per capita. (this can be done using the gompertz function or other forecasts)


#%%
#the function will make use of the from scipy.optimize import minimize library to find the best parameters for the gompertz function given te values of gamma, the historical values and the gdp per capita and the stocks per capita in 2045 and 2050

#to start we will attempt to use thw data from 'output_data/model_output_detailed/{}'.format(config.model_output_file_name), index=False)
model_output_detailed = pd.read_csv(root_dir + '/' + 'output_data/model_output_detailed/{}'.format(config.model_output_file_name))
#and grab macro data too
macro_data = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/growth_forecasts.csv')
#and grab gompertz inputs*
road_model_input = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/road_model_input_wide.csv')

#separate gompertz inputs
gompertz_parameters = road_model_input[['Economy','Scenario','Date', 'Transport Type'] + [col for col in road_model_input.columns if 'Gompertz_' in col]].drop_duplicates().dropna()

#filter for the data we need only:
# ['Date', 'Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive',
#        'Scenario','Stocks']
model_output_detailed = model_output_detailed[['Date', 'Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive', 'Scenario','Stocks']].drop_duplicates()

macro_data = macro_data[['Date', 'Economy', 'Gdp_per_capita','Population']].drop_duplicates()

#%%
#join the two datasets on Date and economy
model_output_detailed = model_output_detailed.merge(macro_data, on=['Date', 'Economy'], how='left')

model_output_detailed = model_output_detailed.merge(gompertz_parameters, on=['Date', 'Economy', 'Scenario', 'Transport Type'], how='left')


#%%
#now attempt first estimation by using data for ldvs from 01_AUS
#create function for this:
def gompertz_fitting_function_handler(model_data):
    """this will loop through the data inout for the road model and estimate the gompertz parameters for each economy and vehicle type"""
    #loop through economies and vehicle types
    #create empty dataframe to store results
    gompertz_parameters_estimates = pd.DataFrame()
    if 'ldv' not in model_data['Vehicle Type'].unique():
        raise ValueError('ldv not in model_data')
        #would pro bably be smart to make this for lpv's which are the sum of lt,suv,car
    for economy in model_data['Economy'].unique():
        for scenario in model_data['Scenario'].unique():
            for vehicle_type in model_data['Vehicle Type'].unique():
                #skip anything except ldv for now
                if vehicle_type != 'ldv':
                    continue
                #filter for economy and vehicle type
                model_data_economy_vehicle_type = model_data[(model_data['Economy']==economy) & (model_data['Vehicle Type']==vehicle_type) & (model_data['Scenario']==scenario)]
                #filter for cols we need:
                model_output_detailed_aus_ldv = model_output_detailed_aus_ldv[['Date', 'Stocks', 'Gdp_per_capita','Population', 'Gompertz_gamma']].drop_duplicates()#, 'Gompertz_alpha', 'Gompertz_beta'
                #sum up by Drive, with any NAs set to 0
                model_output_detailed_aus_ldv['Stocks'] = model_output_detailed_aus_ldv['Stocks'].fillna(0)
                model_output_detailed_aus_ldv = model_output_detailed_aus_ldv.groupby(['Date', 'Gdp_per_capita','Population', 'Gompertz_gamma']).agg({'Stocks':'sum'}).reset_index()#, 'Gompertz_alpha', 'Gompertz_beta'
                #calcualte stocks per capita
                model_output_detailed_aus_ldv['Thousand_stocks_per_capita'] = model_output_detailed_aus_ldv['Stocks']/model_output_detailed_aus_ldv['Population']
                #convert to correct uits:
                model_output_detailed_aus_ldv['Stocks_per_thousand_capita'] = model_output_detailed_aus_ldv['Thousand_stocks_per_capita'] * 100000
                model_output_detailed_aus_ldv['Gdp_per_capita'] = model_output_detailed_aus_ldv['Gdp_per_capita'] #/ 0.001#convert from thousands to 1's

                
#now identify if the vehicle_ownership_rates_data passes the gamma value at any point. if so we should only use the historical values and some made up values for the final years to fit the curve

gamma = model_output_detailed_aus_ldv['Gompertz_gamma'].dropna().iloc[0]
vehicle_ownership_rates_data = model_output_detailed_aus_ldv['Stocks_per_thousand_capita']
if vehicle_ownership_rates_data.max() < gamma:
    input_data = model_output_detailed_aus_ldv[['Date', 'Gdp_per_capita', 'Stocks_per_thousand_capita']].drop_duplicates().dropna()
    gdp_per_capita_fit = input_data['Gdp_per_capita']
    vehicle_ownership_rates_data = input_data['Stocks_per_thousand_capita']
    date = input_data['Date']
else:
    #historical data dates <= 2020
    input_data = model_output_detailed_aus_ldv[model_output_detailed_aus_ldv.Date <= 2020][['Date', 'Gdp_per_capita', 'Stocks_per_thousand_capita']].drop_duplicates().dropna()
    gdp_per_capita_fit = input_data['Gdp_per_capita']
    vehicle_ownership_rates_data = input_data['Stocks_per_thousand_capita']
    date = input_data['Date']

    #make up some values for the future:
    future_dates = [2045, 2050]
    future_dates_prop_diff_from_gamma = [0.1, 0.09]
    #calcualte the future_dates_prop_diff_from_gamma from the gamma value
    future_dates_stocks_per_thousand_capita =[gamma - (gamma * prop) for prop in future_dates_prop_diff_from_gamma]
    #extract gdp per capita for the future dates
    future_dates_gdp_per_capita = model_output_detailed_aus_ldv[model_output_detailed_aus_ldv.Date.isin(future_dates)]['Gdp_per_capita'].reset_index(drop=True)
    #fill

    #append these to the input_data. note that some are lists not series so we need to convert them
    future_dates = pd.Series(future_dates)
    future_dates_stocks_per_thousand_capita = pd.Series(future_dates_stocks_per_thousand_capita)

    gdp_per_capita_fit = gdp_per_capita_fit.append(future_dates_gdp_per_capita)
    vehicle_ownership_rates_data = vehicle_ownership_rates_data.append(future_dates_stocks_per_thousand_capita)
    date = date.append(future_dates)

    #append to actual input data
    input_data = input_data.append(pd.DataFrame({'Date':future_dates, 'Gdp_per_capita':future_dates_gdp_per_capita, 'Stocks_per_thousand_capita':future_dates_stocks_per_thousand_capita}))
    INTERPOLATE_DATA = True
    if INTERPOLATE_DATA:
        #interpolate between missing years using a polynomial :
        interpolated_input_data = model_output_detailed_aus_ldv[['Date', 'Gdp_per_capita', 'Stocks_per_thousand_capita']].drop_duplicates().dropna()
        #set Stocks_per_thousand_capita to na where date >2020
        interpolated_input_data['Stocks_per_thousand_capita'] = interpolated_input_data.apply(lambda x: x['Stocks_per_thousand_capita'] if x['Date'] <=2020 else np.nan, axis=1)
        #drop where date is in input_data and then concat the input_data
        interpolated_input_data = interpolated_input_data[~interpolated_input_data.Date.isin(input_data.Date)].append(input_data)
        #sort by date
        interpolated_input_data = interpolated_input_data.sort_values(by='Date').reset_index(drop=True)
        #interpolate the missing values
        interpolated_input_data['Stocks_per_thousand_capita'] = interpolated_input_data['Stocks_per_thousand_capita'].interpolate(method='linear')

        #now set vehicle_ownership_rates_data and so on to the interpolated values
        vehicle_ownership_rates_data = interpolated_input_data['Stocks_per_thousand_capita']
        gdp_per_capita_fit = interpolated_input_data['Gdp_per_capita']
        date = interpolated_input_data['Date']
        



def gompertz_stocks(gdp_per_capita, gamma, beta, alpha):
    return gamma * np.exp(alpha * np.exp(beta * gdp_per_capita))

# Define your cost function
def cost_function(params):
    alpha, beta = params
    vehicle_ownership_rates_fit = gompertz_stocks(gdp_per_capita_fit, gamma, beta, alpha)
    return np.sum((vehicle_ownership_rates_fit - vehicle_ownership_rates_data)**2)

# Initial guess for the parameters
initial_guess = [model_output_detailed_aus_ldv['Gompertz_alpha'].dropna().iloc[0], model_output_detailed_aus_ldv['Gompertz_beta'].dropna().iloc[0]]

# Use scipy.optimize.minimize to find the best parameters
result = minimize(cost_function, initial_guess,method='Nelder-Mead')
# The optimal parameters are stored in result.x
alpha_opt, beta_opt = result.x
#apply checks for results that are out of bounds we want:
#if any y from gompertz_stocks(gdp_per_capita_fit, gamma, beta_opt, alpha_opt) is >= to gamma then it didnt work
if gompertz_stocks(gdp_per_capita_fit, gamma, beta_opt, alpha_opt).max() >= gamma:
    #set alpha_opt to nan
    alpha_opt = np.nan
    beta_opt = np.nan
    print('alpha_opt:', alpha_opt)
    print('beta_opt:', beta_opt)
    print('Message: Gompertz fit failed as gompertz_stocks(gdp_per_capita_fit, gamma, beta_opt, alpha_opt).max() >= gamma')
else:
    print('Message:', result.message)
    print('alpha_opt:', alpha_opt)
    print('beta_opt:', beta_opt)
    plotly = False
    if plotly:
        #now plot the results with x = date, y = stocks per capita
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=date, y=vehicle_ownership_rates_data, mode='markers', name='data'))
        fig.add_trace(go.Scatter(x=date, y=gompertz_stocks(gdp_per_capita_fit, gamma, beta_opt, alpha_opt), mode='lines', name='fit'))
        fig.update_layout(title='Gompertz fit for 01_AUS', xaxis_title='Year', yaxis_title='Stocks per capita')
        #plot gamma as its own value for every date
        fig.add_trace(go.Scatter(x=date, y=[gamma]*len(date), mode='lines', name='gamma'))
        #write to png and open it
        fig.write_image('gompertz_fit.png')

        #and plot the same but wth gdp per capita in x
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=gdp_per_capita_fit, y=vehicle_ownership_rates_data, mode='markers', name='data'))
        fig.add_trace(go.Scatter(x=gdp_per_capita_fit, y=gompertz_stocks(gdp_per_capita_fit, gamma, beta_opt, alpha_opt), mode='lines', name='fit'))
        fig.update_layout(title='Gompertz fit for 01_AUS', xaxis_title='Gdp per capita', yaxis_title='Stocks per capita')
        #plot gamma as its own value for every date
        fig.add_trace(go.Scatter(x=gdp_per_capita_fit, y=[gamma]*len(gdp_per_capita_fit), mode='lines', name='gamma'))
        #write to png and open it
        fig.write_image('gompertz_fit_gdp_per_capita.png')

    else:
            
        # Create a new figure
        plt.figure()

        # Plot the original data
        plt.scatter(date, vehicle_ownership_rates_data, label='data')

        # Plot the fitted function
        plt.plot(date, gompertz_stocks(gdp_per_capita_fit, gamma, beta_opt, alpha_opt), label='fit')

        # Plot the gamma value
        plt.plot(date, [gamma]*len(date), label='gamma')

        # Add labels and title
        plt.xlabel('Year')
        plt.ylabel('Stocks per capita')
        plt.title(f'Gompertz fit for {economy}')

        # Add a legend
        plt.legend()

        # Show the plot
        plt.show()

        #and plot the same but wth gdp per capita in x
        plt.figure()

        # Plot the original data
        plt.scatter(gdp_per_capita_fit, vehicle_ownership_rates_data, label='data')
        
        # Plot the fitted function
        plt.plot(gdp_per_capita_fit, gompertz_stocks(gdp_per_capita_fit, gamma, beta_opt, alpha_opt), label='fit')

        # Plot the gamma value
        plt.plot(gdp_per_capita_fit, [gamma]*len(gdp_per_capita_fit), label='gamma')

        # Add labels and title
        plt.xlabel('Gdp per capita')
        plt.ylabel('Stocks per capita')
        plt.title(f'Gompertz fit for {economy}')

        # Add a legend
        plt.legend()

        # Show the plot
        plt.show()

#%%

#theres a hance it may be better just to stop the stocks per cap from passing gamma, rather than applying a line too.
# %%
