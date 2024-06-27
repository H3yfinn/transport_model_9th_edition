#######################################################################
#%%
#Calcualtions
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
import numpy as np
from scipy.optimize import newton
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
import sys
sys.path.append("./config")
import config

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
#######################################################################
# #TESTING. CALCUALTE PARAMETER TO ADJUST ACTIVITY GROWTH USING A MEASURE OF STOCKS PER CAPITA. todo
# #FIRST CALCUALTE STOCKS PER CAPITA. 

# #USE GOMPERTZ CURVE TO CALCUALTE EXPECTED GROWTH IN STOCKS PER CAPITA GIVEN THE CURRENT STOCKS PER CAPITA AND SOME MEASURE OF :
# # THE EXPECTED MAXIMUM STOCKS PER CAPITA?
# # THE INCOME PER CAPITA?
# # gdp PER CAPITA
#%%
test_params = False
if test_params:
    from plotly.subplots import make_subplots

    def gompertz_stocks(gdp_per_capita, gamma, beta, alpha):
        return gamma * np.exp(alpha * np.exp(beta * gdp_per_capita))

    # Define GDP per capita range
    gdp_per_capita = np.linspace(0, 0.8, 100)
    # # Define parameter ranges
    # min_gamma = 439.02
    # max_gamma = 571.36
    # step = (max_gamma - min_gamma)/5
    # gamma_values = np.arange(400, 801, 100)
    # min_beta = -162.88
    # max_beta = 72.4
    # step = (max_beta - min_beta)/5
    # beta_values = np.arange(60, 0, -10)#beta_values = np.arange(30, -30, -10)
    # min_alpha = 361279.15
    # max_alpha = 335165.29
    # step = (max_alpha - min_alpha)/5
    # alpha_values = np.arange(5, -5, -2)#alpha_values = np.arange(10, 1, -2)
    # Define parameter ranges
    min_gamma = 0.1#439#.02
    max_gamma = 0.871#.36
    step = (max_gamma - min_gamma)/10
    gamma_values = np.arange(min_gamma, max_gamma, step).round(2)
    min_beta = -20#steepness
    max_beta = -40
    step = (max_beta - min_beta)/5
    beta_values = np.arange(min_beta, max_beta, step).round(2)#beta_values = np.arange(30, -30, -10)
    min_alpha = -50#where the curve starts (greater =  later)
    max_alpha = -500
    step = (max_alpha - min_alpha)/5
    alpha_values = np.arange(min_alpha, max_alpha, step).round(2)#alpha_values = np.arange(10, 1, -2)

    # Create a subplot for each combination of gamma and beta values
    fig = make_subplots(rows=len(beta_values), cols=len(alpha_values), subplot_titles=[f'beta={beta}, alpha={alpha}' for beta in beta_values for alpha in alpha_values])

    # Iterate over all combinations of gamma, beta, and alpha values
    for i, gamma in enumerate(gamma_values):
        for j, beta in enumerate(beta_values):
            for k, alpha in enumerate(alpha_values):
                # Calculate vehicle ownership rates
                vehicle_ownership_rates = gompertz_stocks(gdp_per_capita, gamma, beta, alpha)
                
                # Add a line to the appropriate subplot
                fig.add_trace(go.Scatter(x=gdp_per_capita, y=vehicle_ownership_rates, mode='lines', name=f'gamma={gamma}'), row=j+1, col=k+1)

    # Update layout
    fig.update_layout(title_text=f"Vehicle Ownership Rates for Different Parameter Values")
    #drop legend
    # fig.update_layout(showlegend=False)
    # Show the plot
    fig.write_html(f'plotting_output/input_exploration/gompertz/gompertz_curve_test_{gamma}.html', auto_open=True)
#%%
#https://www.mdpi.com/2071-1050/6/8/4877
test_params = False
if test_params:
    from plotly.subplots import make_subplots

    def gompertz_stocks(gdp_per_capita, gamma, beta, alpha):
        return gamma * np.exp(alpha * np.exp(beta * gdp_per_capita))


    # # Define parameter ranges
    # min_gamma = 439.02
    # max_gamma = 571.36
    # step = (max_gamma - min_gamma)/5
    # gamma_values = np.arange(400, 801, 100)
    # min_beta = -162.88
    # max_beta = 72.4
    # step = (max_beta - min_beta)/5
    # beta_values = np.arange(60, 0, -10)#beta_values = np.arange(30, -30, -10)
    # min_alpha = 361279.15
    # max_alpha = 335165.29
    # step = (max_alpha - min_alpha)/5
    # # alpha_values = np.arange(5, -5, -2)#alpha_values = np.arange(10, 1, -2)
    # # Define parameter ranges
    # min_gamma = 0.1#439#.02
    # max_gamma = 0.871#.36
    # step = (max_gamma - min_gamma)/10
    # gamma_values = np.arange(min_gamma, max_gamma, step).round(2)
    # min_beta = -20#steepness
    # max_beta = -40
    # step = (max_beta - min_beta)/5
    # beta_values = np.arange(min_beta, max_beta, step).round(2)#beta_values = np.arange(30, -30, -10)
    # min_alpha = -50#where the curve starts (greater =  later)
    # max_alpha = -500
    # step = (max_alpha - min_alpha)/5
    # alpha_values = np.arange(min_alpha, max_alpha, step).round(2)#alpha_values = np.arange(10, 1, -2)
    ######################
    gamma_values = [800]
    beta_values = [-0.000207]
    alpha_values = [-17.8499]
    # Define GDP per capita range
    gdp_per_capita = np.linspace(-500, 5*10**4, 1000)

    # Create a subplot for each combination of gamma and beta values
    fig = make_subplots(rows=len(beta_values), cols=len(alpha_values), subplot_titles=[f'beta={beta}, alpha={alpha}' for beta in beta_values for alpha in alpha_values])

    # Iterate over all combinations of gamma, beta, and alpha values
    for i, gamma in enumerate(gamma_values):
        for j, beta in enumerate(beta_values):
            for k, alpha in enumerate(alpha_values):
                # Calculate vehicle ownership rates
                vehicle_ownership_rates = gompertz_stocks(gdp_per_capita, gamma, beta, alpha)
                
                # Add a line to the appropriate subplot
                fig.add_trace(go.Scatter(x=gdp_per_capita, y=vehicle_ownership_rates, mode='lines', name=f'gamma={gamma}'), row=j+1, col=k+1)

    # Update layout
    fig.update_layout(title_text=f"Vehicle Ownership Rates for Different Parameter Values")
    #drop legend
    # fig.update_layout(showlegend=False)
    # Show the plot
    fig.write_html(f'plotting_output/input_exploration/gompertz/gompertz_curve_test_{gamma}.html', auto_open=True)
#%%

#save data as pickle to be analysed seprartely )we want to see if we can estimate beter paramter vlaues to aovid stocks per cpita estiamtes being equal to the gamma value (theoretical amximum for stocks per capita)
gompertz_parameters = pd.read_pickle('intermediate_data/analysis_single_use/gompertz_change_dataframe_road_model.pkl')
analyse_this = True
if analyse_this:
    #frist lets look at 01_AUS, and try find parameters that fit the data better
    #get the data. filter for reference and feight
    gompertz_parameters = gompertz_parameters[(gompertz_parameters['Economy'] == '01_AUS') & (gompertz_parameters['Scenario'] == 'Reference') & (gompertz_parameters['Transport Type'] != 'freight')]
    
    from plotly.subplots import make_subplots

    def gompertz_stocks(gdp_per_capita, gamma, beta, alpha):
        return gamma * np.exp(alpha * np.exp(beta * gdp_per_capita))

    #grab parameter value and create a range that is plus or minus 200% of the value
    min_gamma = gompertz_parameters['Gompertz_gamma'].values[0] * 0.5
    max_gamma = gompertz_parameters['Gompertz_gamma'].values[0] * 1.5
    step = (max_gamma - min_gamma)/20
    gamma_values = np.arange(min_gamma, max_gamma, step)
    gamma_values = [gompertz_parameters['Gompertz_gamma'].values[0]]

    min_beta = -0.0001035# gompertz_parameters['Gompertz_beta'].values[0] * 0.5
    max_beta = -0.00001035#gompertz_parameters['Gompertz_beta'].values[0] * 10
    step = (max_beta - min_beta)/5
    beta_values = np.arange(min_beta, max_beta, step)#beta_values = np.arange(30, -30, -10)
    min_alpha = -100#gompertz_parameters['Gompertz_alpha'].values[0] * 0.01
    max_alpha = -17.8499#gompertz_parameters['Gompertz_alpha'].values[0]
    step = (max_alpha - min_alpha)/5
    alpha_values = np.arange(min_alpha, max_alpha, step)#alpha_values = np.arange(10, 1, -2)
    ######################
    #use the range of gdp per cpita from first to last year in gompertz_parameters

    #melt to get Stocks_per_thousand_capita and Expected_stocks_per_thousand_capita in one col
    gompertz_parameters_long = gompertz_parameters[['Economy', 'Date', 'Gdp_per_capita', 'Stocks_per_thousand_capita', 'Expected_stocks_per_thousand_capita','Gompertz_gamma']].drop_duplicates()

    #set Stocks_per_thousand_capita to 3.427014e+02 cause thats the vlaue for first year and all other values are way too large
    gompertz_parameters_long.loc[gompertz_parameters_long['Stocks_per_thousand_capita'] > 1000, 'Stocks_per_thousand_capita'] = 3.427014e+02

    # gompertz_parameters_long = pd.melt(gompertz_parameters_long, id_vars=['Economy', 'Date', 'Gdp_per_capita'], value_vars=['Stocks_per_thousand_capita', 'Expected_stocks_per_thousand_capita'], var_name='Measure', value_name='Value')

    # Iterate over all combinations of gamma, beta, and alpha values and compare the resutls to the originally estimated Stocks_per_thousand_capita and Expected_stocks_per_thousand_capita using different colors
    for i, gamma in enumerate(gamma_values):
        gompertz_parameters_long['gamma'] = gamma
            
        # Create a subplot for each combination of gamma and beta values
        fig = make_subplots(rows=len(beta_values), cols=len(alpha_values), subplot_titles=[f'beta={beta}, alpha={alpha}' for beta in beta_values for alpha in alpha_values])

        for j, beta in enumerate(beta_values):
            gompertz_parameters_long['beta'] = beta
            for k, alpha in enumerate(alpha_values):
                gompertz_parameters_long['alpha'] = alpha
                # Calculate vehicle ownership rates
                            
                gompertz_parameters_long['New_stocks_per_thousand_capita'] = gompertz_parameters_long.apply(lambda x: gompertz_stocks(x['Gdp_per_capita'], x['gamma'], x['beta'], x['alpha']), axis=1)
                                
                # Add a line to the appropriate subplot
                fig.add_trace(go.Scatter(x=gompertz_parameters_long['Gdp_per_capita'], y=gompertz_parameters_long['New_stocks_per_thousand_capita'], name=f"New_stocks_per_thousand_capita", mode='markers'), row=j+1, col=k+1)
                fig.add_trace(go.Scatter(x=gompertz_parameters_long['Gdp_per_capita'], y=gompertz_parameters_long['Stocks_per_thousand_capita'], name=f"Stocks_per_thousand_capita", mode='markers'), row=j+1, col=k+1)
                fig.add_trace(go.Scatter(x=gompertz_parameters_long['Gdp_per_capita'], y=gompertz_parameters_long['Expected_stocks_per_thousand_capita'], name=f"Expected_stocks_per_thousand_capita", mode='markers'), row=j+1, col=k+1)
                fig.add_trace(go.Scatter(x=gompertz_parameters_long['Gdp_per_capita'], y=gompertz_parameters_long['Gompertz_gamma'], name=f"Gompertz_gamma", mode='markers'), row=j+1, col=k+1)
                fig.add_trace(go.Scatter(x=gompertz_parameters_long['Gdp_per_capita'], y=gompertz_parameters_long['gamma'], name=f"gamma", mode='markers'), row=j+1, col=k+1)

        #specify color based on the name
        fig.for_each_trace(lambda t: t.update(marker_color='red') if t.name == 'Stocks_per_thousand_capita' else ())
        fig.for_each_trace(lambda t: t.update(marker_color='blue') if t.name == 'Expected_stocks_per_thousand_capita' else ())
        fig.for_each_trace(lambda t: t.update(marker_color='green') if t.name == 'New_stocks_per_thousand_capita' else ())
        fig.for_each_trace(lambda t: t.update(marker_color='black') if t.name == 'Gompertz_gamma' else ())
        fig.for_each_trace(lambda t: t.update(marker_color='orange') if t.name == 'gamma' else ())

        # Update layout
        fig.update_layout(title_text=f"Vehicle Ownership Rates for Different Parameter Values")
        #drop legend for all but the first plot
        fig.update_layout(showlegend=True)
        # Show the plot
        fig.write_html(f'plotting_output/input_exploration/gompertz/01aus_gompertz_curve_test_{gamma}.html', auto_open=True)
#%%



gompertz_parameters = pd.read_pickle('intermediate_data/analysis_single_use/gompertz_change_dataframe_road_model.pkl')
#get the data. filter for reference and feight
gompertz_parameters = gompertz_parameters[(gompertz_parameters['Economy'] == '01_AUS') & (gompertz_parameters['Scenario'] == 'Reference') & (gompertz_parameters['Transport Type'] != 'freight')]
def gompertz_stocks(gdp_per_capita, gamma, beta, alpha):
    return gamma * np.exp(alpha * np.exp(beta * gdp_per_capita))

def log_func(x, a, b):
    return a + b * np.log(x + 1)  # Add 1 to x to avoid taking the log of zero
import numpy as np
from scipy.optimize import curve_fit
import plotly.graph_objects as go
analyse_this = False
if analyse_this:

    #ok. lets design a function that will calcualte alpha and beta so that the gompertz curve fits the maximum and minimum values it needs for stocks per cpita. that is, for the years we ahve stocks and per capita gdp data for, we want to find the alpha and beta values that will give us the stocks per capita values we have for those years, for the gdp per cpita values we have for thise years. we can then use those alpha and beta values to calculate the stocks per capita for all other years, so that the stocks per cpita doesnt go above the gamma value, but also comes close to the gamma value.

    #we will do this by first fitting a log curve to the values for:
    #values that are pre-2018 (i.e. values we have available)
    #values in 2050, so that the stocks_per_thousand_capita in 2050 is equal to Gomperz_gamma and the gdp_per_capita in 2050 is availble because it was projected for this.

    # Define your GDP per capita and vehicle ownership rates data that is available (which is any data that is less than 2018 currently)
    gdp_per_capita_data = gompertz_parameters[gompertz_parameters['Date']<=2018]['Gdp_per_capita'].values
    vehicle_ownership_rates_data = gompertz_parameters[gompertz_parameters['Date']<=2018]['Stocks_per_thousand_capita'].values
    #if vehicle_ownership_rates_data is not a list, make it a list
    if type(vehicle_ownership_rates_data) != list:
        vehicle_ownership_rates_data = vehicle_ownership_rates_data.tolist()
        gdp_per_capita_data = gdp_per_capita_data.tolist()
    #then add on values for 2050:
    gdp_per_capita_data.append(gompertz_parameters[gompertz_parameters['Date']==2050]['Gdp_per_capita'].values[0])
    vehicle_ownership_rates_data.append(gompertz_parameters[gompertz_parameters['Date']==2018]['Gompertz_gamma'].values[0]-10)

    # Define the gamma value
    gamma = gompertz_parameters[gompertz_parameters['Date']==2018]['Gompertz_gamma'].values[0]

    # Initial guess for the parameters (a, b)
    initial_guess_gompertz = [gompertz_parameters[gompertz_parameters['Date']==2018]['Gompertz_alpha'].values[0], gompertz_parameters[gompertz_parameters['Date']==2018]['Gompertz_beta'].values[0]]
    initial_guess_gompertz = [-0.0001035, -100]
    initial_guess_log = [1,1]

    # Use curve_fit to find the best parameters
    params_log, params_log_covariance = curve_fit(log_func, gdp_per_capita_data, vehicle_ownership_rates_data, p0=initial_guess_log)

    # Print the best fit parameters
    print("Best fit parameters: a = {}, b = {}".format(params_log[0], params_log[1]))
    #cahnge  params_log[0], params_log[1]) to make the curve artifically curvier
    params_log[0] = 1
    params_log[1] = 1
    # Generate data for the fitted function:
    x_fit = gompertz_parameters['Gdp_per_capita']
    gompertz_parameters['Fitted_log_stocks_per_thousand_capita'] = log_func(gompertz_parameters['Gdp_per_capita'], params_log[0], params_log[1])
    y_fit = gompertz_parameters['Fitted_log_stocks_per_thousand_capita']

    # Use curve_fit to find the best parameters
    params, params_covariance = curve_fit(lambda x, beta, alpha: gompertz_stocks(x, gamma, beta, alpha), x_fit, y_fit, p0=initial_guess_gompertz)

    # Print the best fit parameters
    print("Best fit parameters: beta = {}, alpha = {}".format(params[0], params[1]))
    
    # #recreate best fit params: 
    # params[0] = -0.0001035
    # params[1] = -100

    # Generate data for the fitted function
    vehicle_ownership_rates_fit = gompertz_stocks(x_fit, gamma, params[0], params[1])

    # Create a plot
    fig = go.Figure()

    # Add the original data to the plot
    fig.add_trace(go.Scatter(x=gdp_per_capita_data, y=vehicle_ownership_rates_data, mode='markers', name='Original data'))

    #add the log fit to the plot
    fig.add_trace(go.Scatter(x=x_fit, y=y_fit, mode='lines', name='Log fit'))

    # Add the fitted function to the plot
    fig.add_trace(go.Scatter(x=x_fit, y=vehicle_ownership_rates_fit, mode='lines', name='Fitted function'))

    #plot the gamma value as a horizontal line
    fig.add_trace(go.Scatter(x=x_fit, y=[gompertz_parameters[gompertz_parameters['Date']==2018]['Gompertz_gamma'].values[0]]*len(x_fit), mode='lines', name='Gamma value'))
    # Set plot title and labels
    fig.update_layout(title='Vehicle Ownership Rates',
                    xaxis_title='GDP per Capita',
                    yaxis_title='Vehicle Ownership Rates')

    # save plot as html
    fig.write_html(f'plotting_output/input_exploration/gompertz/01aus_gompertz_curve_log_fit.html', auto_open=True)


#%%


import numpy as np
import plotly.graph_objects as go

# Define the log function
def log_func(x, a, b):
    return a + b * np.log(x + 1)  # Add 1 to x to avoid taking the log of zero
def gompertz_stocks(gdp_per_capita, gamma, beta, alpha):
    return gamma * np.exp(alpha * np.exp(beta * gdp_per_capita))

# # Define your GDP per capita and vehicle ownership rates data
# gdp_per_capita_data = np.array(gdp_per_capita_data)
# vehicle_ownership_rates_data = np.array(vehicle_ownership_rates_data)

# Define your GDP per capita and vehicle ownership rates data that is available (which is any data that is less than 2018 currently)
gdp_per_capita_data = gompertz_parameters[gompertz_parameters['Date']<=2018]['Gdp_per_capita'].values
vehicle_ownership_rates_data = np.array(500)#gompertz_parameters[gompertz_parameters['Date']<=2018]['Stocks_per_thousand_capita'].values
#if vehicle_ownership_rates_data is not a list or array, make it a list

#then add on target values to encourage the curve to start to flatten out later
gdp_per_capita_data = np.append(gdp_per_capita_data, gompertz_parameters[gompertz_parameters['Date']==2050]['Gdp_per_capita'].values[0])
vehicle_ownership_rates_data = np.append(vehicle_ownership_rates_data,gompertz_parameters[gompertz_parameters['Date']==2018]['Gompertz_gamma'].values[0]-10)

#make it an array again
gdp_per_capita_data = np.array(gdp_per_capita_data)
vehicle_ownership_rates_data = np.array(vehicle_ownership_rates_data)

#######################################################
# Define range of parameter values to test
steps_per_parameter = 50
precent_spread_of_parameters = 5  #500% spread
#GOMPERTZ
target_alpha = -100#value which 'looks' right for similar economies
max_alpha = target_alpha + (target_alpha * precent_spread_of_parameters)  #100% increase
min_alpha = target_alpha - (target_alpha * precent_spread_of_parameters)  #100% decrease
step_alpha = (max_alpha - min_alpha)/steps_per_parameter
alpha_values = np.arange(min_alpha, max_alpha, step_alpha)
target_beta = -0.0001035#value which 'looks' right for similar economies
max_beta = target_beta + (target_beta * precent_spread_of_parameters)  #100% increase
min_beta = target_beta - (target_beta * precent_spread_of_parameters)  #100% decrease
step_beta = (max_beta - min_beta)/steps_per_parameter
beta_values = np.arange(min_beta, max_beta, step_beta)

gamma = gompertz_parameters[gompertz_parameters['Date']==2018]['Gompertz_gamma'].values[0]

#LOG
target_a = 1#value which 'looks' right for similar economies
max_a = target_a + (target_a * precent_spread_of_parameters)  #100% increase
min_a = target_a - (target_a * precent_spread_of_parameters)  #100% decrease
step_a = (max_a - min_a)/steps_per_parameter
a_values = np.arange(min_a, max_a, step_a)
target_b = 1#value which 'looks' right for similar economies
max_b = target_b + (target_b * precent_spread_of_parameters)  #100% increase
min_b = target_b - (target_b * precent_spread_of_parameters)  #100% decrease
step_b = (max_b - min_b)/steps_per_parameter
b_values = np.arange(min_b, max_b, step_b)
#######################################################
# Define the GDP per capita values for the fitted function
gdp_per_capita_fit = gompertz_parameters['Gdp_per_capita'].values

# Create a plot
fig = go.Figure()

# Add the original data to the plot
fig.add_trace(go.Scatter(x=gdp_per_capita_data, y=vehicle_ownership_rates_data, mode='markers', name='Original data'))

# Iterate over all combinations of a and b values
for a in a_values:
    for b in b_values:
        # Calculate vehicle ownership rates for the fitted function
        vehicle_ownership_rates_fit = log_func(gdp_per_capita_fit, a, b)
        # Calculate vehicle ownership rates for the fitted function at the specific GDP per capita values
        vehicle_ownership_rates_fit_specific = log_func(gdp_per_capita_data, a, b)
        # Check if the current alpha/beta pair intercepts the two data points
        if np.isclose(vehicle_ownership_rates_fit_specific, vehicle_ownership_rates_data,rtol=0.1).all():
            # Add the fitted function to the plot
            fig.add_trace(go.Scatter(x=gdp_per_capita_fit, y=vehicle_ownership_rates_fit, mode='lines', name=f'Fitted function: a={a}, b={b}'))

#iterate over all combinations of alpha and beta values
for alpha in alpha_values:
    for beta in beta_values:
        # Calculate vehicle ownership rates for the fitted function
        vehicle_ownership_rates_fit = gompertz_stocks(gdp_per_capita_fit, gamma, beta, alpha)
        # Calculate vehicle ownership rates for the fitted function at the specific GDP per capita values
        vehicle_ownership_rates_fit_specific = gompertz_stocks(gdp_per_capita_data, gamma, beta, alpha)
        # Check if the current alpha/beta pair intercepts the two data points
        if np.isclose(vehicle_ownership_rates_fit_specific, vehicle_ownership_rates_data,rtol=0.1).all():
            # Add the fitted function to the plot
            fig.add_trace(go.Scatter(x=gdp_per_capita_fit, y=vehicle_ownership_rates_fit, mode='lines', name=f'Fitted function: alpha={alpha}, beta={beta}'))


# Set plot title and labels
fig.update_layout(title='Vehicle Ownership Rates',
                xaxis_title='GDP per Capita',
                yaxis_title='Vehicle Ownership Rates')

# write the plot
fig.write_html(f'plotting_output/input_exploration/gompertz/01aus_gompertz_curve_log_fit.html', auto_open=True)


#%%
gompertz_parameters['Expected_stocks_per_thousand_capita_derivative'] = gompertz_parameters.apply(lambda x: gompertz_stocks_derivative(x['Gdp_per_capita'], x['Gompertz_gamma'], x['Gompertz_beta'], x['Gompertz_alpha']), axis=1)
#%%
run_this_section = False
if run_this_section == True:
    gompertz_change_dataframe = change_dataframe.copy()
    #drop vehicle type and drive cols
    gompertz_change_dataframe = gompertz_change_dataframe.drop(['Vehicle Type', 'Drive'], axis=1)
    #sum stocsk by economy, scenario, transport type, and year
    gompertz_change_dataframe_stocks = gompertz_change_dataframe.groupby(['Economy', 'Scenario', 'Transport Type', 'Date'])['Stocks'].sum().reset_index()
    #join the stocks sum to gompertz_change_dataframe
    gompertz_change_dataframe = gompertz_change_dataframe.merge(gompertz_change_dataframe_stocks, on=['Economy', 'Scenario', 'Transport Type', 'Date'], how='left', suffixes=('_old', ''))
    #keep only the cols we need:
    gompertz_change_dataframe = gompertz_change_dataframe[['Economy', 'Scenario', 'Transport Type', 'Date', 'Stocks', 'Gdp_per_capita','Population', 'Gdp',]]
    #drop duplicates
    gompertz_change_dataframe = gompertz_change_dataframe.drop_duplicates()

    #now we have a dataframe with the sum of stocks by economy, scenario, transport type, and year. We can use this to calcualte stocks per capita and gdp per capita anbd then use the gompertz curve to calcualte the expected stocks per capita given the current stocks per capita. We can then use this to adjust the activity growth rate and mileage growth rate.

    #during this process we hgave to choose whether we think our value for gdp per capita or stocks per capita is the most accurtate right now. I expect that we should assxume stocks per capita is more accurate, and therefore use it to estioamte gdp per capita (assuming these stocks per capita) and then use that to derive the stocks per capita growth rate.

    #however this is a bit flawed because we should really use both values to derive the growth rate. We could use it to estimate the parameters of the gompertz curve. But this is a bit complicated. So for now we will just method explained above.

    #calculate stocks per capita (stocks are currently in millions and population in thousands, as determined by workflow\grooming_code\2_aggregate_data_for_model.py line 79)
    gompertz_change_dataframe['Thousand_stocks_per_capita'] = gompertz_change_dataframe['Stocks'] / gompertz_change_dataframe['Population']
    gompertz_change_dataframe['Stocks_per_thousand_capita'] = gompertz_change_dataframe['Thousand_stocks_per_capita'] * 1000000#PLEASE NOTE THAT ANY CHANGES TO UNITS ELSWHERE IN THE CODE MAY BREAK THIS LINE AS STOCKS NEED TO BE IN MILLIONS AND POPULATION IN THOUSANDS FOR THIS TO WORK. THERE IS A CHECK IN 2_aggregate_data_for_model TO CHECK FOR THIS

    #SETUP THE GOMPERTZ CURVE
    #define the function    
    def gompertz_stocks(gdp_per_capita, gamma, beta, alpha):
        #orioginal equation, just for reference
        return gamma * np.exp(alpha * np.exp(beta * gdp_per_capita))

    def gompertz_stocks_derivative(gdp_per_capita, gamma, beta, alpha):
        return alpha * beta * gamma * np.exp(alpha * np.exp(beta * gdp_per_capita) + beta * gdp_per_capita)

    #Estimate Gdp per capita
    def solve_for_gdp_per_capita(stocks_per_capita, current_Gdp_per_capita,gamma, beta, alpha):
        # Define the function for which we want to find the root
        #the "root" is the value of gdp_per_capita that makes the function gompertz_stocks(gdp_per_capita, gamma, beta, alpha) - stocks_per_capita equal to zero
        func = lambda gdp_per_capita: gompertz_stocks(gdp_per_capita, gamma, beta, alpha) - stocks_per_capita
        # Initial guess for the root
        initial_guess = current_Gdp_per_capita
        # Use the Newton-Raphson method to find the root
        gdp_per_capita = newton(func, initial_guess)
        return gdp_per_capita

    #merge stocks per capita to the gomperts parameter dataframe
    gompertz_parameters = gompertz_parameters.merge(gompertz_change_dataframe[['Economy','Scenario', 'Transport Type', 'Date', 'Stocks_per_thousand_capita','Gdp_per_capita']], on=['Economy','Scenario', 'Transport Type', 'Date'], how='left')

    #apply the gompertz function to the dataframe to calcualte the expected stocks per capita . this is for testing and diagnostics only
    gompertz_parameters['Expected_stocks_per_thousand_capita'] = gompertz_parameters.apply(lambda x: gompertz_stocks(x['Gdp_per_capita'], x['Gompertz_gamma'], x['Gompertz_beta'], x['Gompertz_alpha']), axis=1)

    #we want to know the rate of cchange of the curve. so we will differentiate the gompertz function and find the rate of change for Expected_stocks_per_capita at this point in time using gompertz_stocks_derivative(gdp_per_capita, gamma, beta, alpha)

    #apply the gompertz derivative function to the dataframe to calcualte the expected stocks per capita growwth rate
    gompertz_parameters['Expected_stocks_per_thousand_capita_derivative'] = gompertz_parameters.apply(lambda x: gompertz_stocks_derivative(x['Gdp_per_capita'], x['Gompertz_gamma'], x['Gompertz_beta'], x['Gompertz_alpha']), axis=1)

#save gompertz_parameters as a pickle and we will load it in another file to analyse
# gompertz_parameters.to_pickle('intermediate_data/gompertz_parameters_analysis.pkl')

#%%
run_this_section = False
if run_this_section == True:
    #we will also do this using an estimate of Gdp_per_capita using solve_for_gdp_per_capita(). this is for testing and diagnostics only
    gompertz_parameters['Expected_Gdp_per_capita'] = gompertz_parameters.apply(lambda x: solve_for_gdp_per_capita(x['Stocks_per_thousand_capita'], x['Gdp_per_capita'], x['Gompertz_gamma'], x['Gompertz_beta'], x['Gompertz_alpha']), axis=1)
    #test#####################
    #calcualte gompertz_stocks out of function using columns from dataframe
    Expected_stocks_per_thousand_capita = gompertz_parameters.copy()
    Expected_stocks_per_thousand_capita = gompertz_parameters['Gompertz_gamma'] * np.exp(gompertz_parameters['Gompertz_alpha'] * np.exp(gompertz_parameters['Gompertz_beta'] * gompertz_parameters['Gdp_per_capita']))
    #grab first row
    Expected_stocks_per_thousand_capita[0]
    #test#####################
    #and then calculate another value for the expected stocks per capita and the derviative using the new estimate of Gdp_per_capita. this is for testing and diagnostics only
    gompertz_parameters['Expected_stocks_per_thousand_capita_2'] = gompertz_parameters.apply(lambda x: gompertz_stocks(x['Stocks_per_thousand_capita'], x['Gompertz_gamma'], x['Gompertz_beta'], x['Gompertz_alpha']), axis=1)
    gompertz_parameters['Expected_stocks_per_thousand_capita_derivative_2'] = gompertz_parameters.apply(lambda x: gompertz_stocks_derivative(x['Expected_Gdp_per_capita'], x['Gompertz_gamma'], x['Gompertz_beta'], x['Gompertz_alpha']), axis=1)

    #use the derivative to adjust the activity growth rate so the rate of change of stocks per capita impacts the activity growth rate
    #join the derivative to the change dataframe
    change_dataframe = change_dataframe.merge(gompertz_parameters[['Economy','Scenario', 'Transport Type', 'Date', 'Expected_stocks_per_thousand_capita_derivative']], on=['Economy','Scenario',  'Transport Type', 'Date'], how='left')

    #replace any nan values with 1. this is because we dont want to adjust the activity growth rate if we dont have a value for the derivative
    change_dataframe['Expected_stocks_per_thousand_capita_derivative'] = change_dataframe['Expected_stocks_per_thousand_capita_derivative'].fillna(1)
    break
    #%%
    #calcualte the adjusted activity growth
    change_dataframe['Activity_growth_adjusted'] = change_dataframe['Activity_growth'] * change_dataframe['Expected_stocks_per_thousand_capita_derivative']

    #also use this to adjust the growth in mileage. im a little unsure about this but i think it is most correct given the circumstances. We need a form of mileage growth to reflect growth in mileage in developing economys especailly. and you can expect that growth in mileage will follow similar trends to growth in stocks per capita (except perhaps at the begining of the S curve... but then again low gdp implies bad roads). so we will use the same adjustment factor as for activity growth to adjust the mileage growth rate (which, of course, will be much lower than the activity growth rate)
    change_dataframe = change_dataframe.merge(Mileage_growth, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Date'], how='left')

    change_dataframe['Mileage_growth_adjusted'] = change_dataframe['Mileage_growth'] * change_dataframe['Expected_stocks_per_thousand_capita_derivative']

    #adjust mileage now
    change_dataframe['Mileage'] = change_dataframe['Mileage'] * change_dataframe['Mileage_growth_adjusted']

    #now, because this is a bit of a commplicated process that could have things go worng, we will extract the data and save it to a csv file so we can plot it and check it is working as expected: