
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
current_working_dir = os.getcwd()
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = re.split('transport_model_9th_edition', script_dir)[0] + 'transport_model_9th_edition'
if __name__ == "__main__": #this allows the script to be run directly or from the main.py file as you cannot use relative imports when running a script directly
    # Modify sys.path to include the directory where utility_functions is located
    sys.path.append(f"{root_dir}/code")
    import config
    import utility_functions
    sys.path.append(f"{root_dir}/code/calculation_functions")
    import logistic_fitting_functions

else:
    # Assuming the script is being run from main.py located at the root of the project, we want to avoid using sys.path.append and instead use relative imports 
    try:
        from ..utility_functions import *
        from ..config import *
    except ImportError:
        import utility_functions
        import config
    from ..calculation_functions import logistic_fitting_functions
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
def plot_logistic_fit(date, stocks_per_capita, gdp_per_capita, gamma, growth_rate, midpoint, economy_ttype_scenario,show_plots, matplotlib_bool, plotly_bool):
    if plotly_bool:
        #now plot the results with x = date, y = stocks per capita
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=date, y=stocks_per_capita, mode='markers', name='data'))
        fig.add_trace(go.Scatter(x=date, y=logistic_fitting_functions.logistic_function(gdp_per_capita, gamma, growth_rate, midpoint), mode='lines', name='fit'))
        fig.update_layout(title=f'Log fit for {economy_ttype_scenario}', xaxis_title='Year', yaxis_title='Stocks per capita')
        #plot gamma as its own value for every date
        fig.add_trace(go.Scatter(x=date, y=[gamma]*len(date), mode='lines', name='gamma'))
        #write to png and open it
        write_to_img = False
        if write_to_img:
            fig.write_image(f'plotting_output/input_exploration/gompertz/fitting/log_fit_{economy_ttype_scenario}.png')
        #write to html
        fig.write_html(root_dir + '/' +f'plotting_output/input_exploration/gompertz/fitting/log_fit_{economy_ttype_scenario}.html')

        #and plot the same but wth gdp per capita in x
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=gdp_per_capita, y=stocks_per_capita, mode='markers', name='data'))
        fig.add_trace(go.Scatter(x=gdp_per_capita, y=logistic_fitting_functions.logistic_function(gdp_per_capita, gamma, growth_rate, midpoint), mode='lines', name='fit'))
        fig.update_layout(title=f'Log fit for {economy_ttype_scenario}', xaxis_title='Gdp per capita', yaxis_title='Stocks per capita')
        #plot gamma as its own value for every date
        fig.add_trace(go.Scatter(x=gdp_per_capita, y=[gamma]*len(gdp_per_capita), mode='lines', name='gamma'))
        if write_to_img:
            fig.write_image(f'plotting_output/input_exploration/gompertz/fitting/log_fit_gdp_per_capita_{economy_ttype_scenario}.png')
        fig.write_html(root_dir + '/' +f'plotting_output/input_exploration/gompertz/fitting/logistic_fit_gdp_per_capita_{economy_ttype_scenario}.html')
        
def plot_logistic_function_all_economies(model_data_logistic_predictions, activity_growth_estimates, parameters_estimates, new_model_data, show_plots, matplotlib_bool, plotly_bool, FIT_LOGISTIC_CURVE_TO_DATA):
    #we will plot the results of the logistic function fit. To cut down on the number of plots we will facet by economy and onily plot the first scenario
    #we will also plot the gamma value for each economy as a horizontal line if the data is on stock per capita
    #extact model_data that will be used. so grab passenger transport type, times by the 
    #calcualte stocks per capita
    new_model_data['Thousand_stocks_per_capita'] = new_model_data['Stocks']/new_model_data['Population']
    #convert to more readable units. We will convert back later if we need to #todo do we need to?
    new_model_data['Stocks_per_thousand_capita'] = new_model_data['Thousand_stocks_per_capita'] * 1000000
    new_model_data = new_model_data[['Date', 'Economy', 'Scenario', 'Transport Type', 'Stocks_per_thousand_capita', 'Activity']].drop_duplicates()
    #sum up
    new_model_data = new_model_data.groupby(['Date', 'Economy', 'Scenario', 'Transport Type']).sum().reset_index()

    #join the dataframes together
    all_data = pd.merge(model_data_logistic_predictions, new_model_data, on=['Date', 'Economy', 'Scenario', 'Transport Type'], how='left', suffixes=('_logistic', '_previous'))
    #join on activity_growth_estimates. Note that this ISNT BY VEHIcle type
    all_data = pd.merge(all_data, activity_growth_estimates, on=['Date','Economy', 'Scenario', 'Transport Type'], how='left')
    
    all_data = all_data.loc[(all_data['Scenario'] == config.SCENARIO_OF_INTEREST)]

    if plotly_bool:
        #first plot will be on the comparitive stocks per capita
        #filter for that data then melt
        all_data_stocks_per_capita = all_data[['Date','Scenario','Transport Type','Gdp_per_capita', 'Economy', 'Stocks_per_thousand_capita_logistic', 'Stocks_per_thousand_capita_previous', 'Gompertz_gamma']]
        #rename
        all_data_stocks_per_capita = all_data_stocks_per_capita.melt(id_vars=['Date', 'Economy', 'Scenario','Transport Type', 'Gdp_per_capita'], value_vars=['Stocks_per_thousand_capita_logistic', 'Stocks_per_thousand_capita_previous','Gompertz_gamma'], var_name='Measure', value_name='Stocks_per_thousand_capita_value')
        #check its not empty
        if all_data_stocks_per_capita.empty:
            pass
            # print('No data to plot log_fit_new_stocks_per_capita, this means that there was no need for adjustment of the activity growth rates, because the stocks per capita were already in the right ballpark')
        else:
            #concatenate 'Scenario', and 'Transport Type' to make a new column
            all_data_stocks_per_capita['Transport Type Scenario'] = all_data_stocks_per_capita['Transport Type'] + ' ' + all_data_stocks_per_capita['Scenario']
            fig = px.line(all_data_stocks_per_capita, x='Date', y='Stocks_per_thousand_capita_value', color='Transport Type Scenario',line_dash='Measure', facet_col='Economy', facet_col_wrap=7, title='Comparitive stocks per capita')#, markers=True)

            #write to html
            fig.write_html(root_dir + '/' +f'plotting_output/input_exploration/gompertz/log_fit_new_stocks_per_capita_all_economies.html')
            ######################
            #and plot the same but wth gdp per capita in x
            fig = px.line(all_data_stocks_per_capita, x='Gdp_per_capita', y='Stocks_per_thousand_capita_value', line_dash='Measure', facet_col='Economy', color='Transport Type Scenario',facet_col_wrap=7, title='Comparitive stocks per capita vs GDP per capita')#, markers=True)

            #write to html
            fig.write_html(root_dir + '/' +f'plotting_output/input_exploration/gompertz/log_fit_new_stocks_per_capita_gdp_per_capita_all_economies.html')
    
        ######################
        #plot stocks for each economy with x as gdp per capita and then x as date. First calcualte stocks from the logistic function 
        all_data['Stocks_logistic'] = (all_data['Stocks_per_thousand_capita_logistic'] * all_data['Population'])/ 1000000
        #now melt
        all_data_stocks = all_data[['Date','Scenario','Transport Type','Gdp_per_capita', 'Economy', 'Stocks_logistic', 'Stocks']]
        all_data_stocks = all_data_stocks.melt(id_vars=['Date', 'Economy', 'Scenario','Transport Type', 'Gdp_per_capita'], value_vars=['Stocks_logistic', 'Stocks'], var_name='Stocks', value_name='Stocks_value')#'stocks' in value_vars is teh stocks before the log adjustment
        
        #check its not empty
        if all_data_stocks.empty:
            pass
            # print('No data to plot log_fit_new_stocks, this means that there was no need for adjustment of the activity growth rates, because the stocks per capita were already in the right ballpark')
        else:
            #plot
            all_data_stocks['Transport Type Scenario'] = all_data_stocks['Transport Type'] + ' ' + all_data_stocks['Scenario']
            fig = px.line(all_data_stocks, x='Date', y='Stocks_value', color='Transport Type Scenario', line_dash = 'Stocks', facet_col='Economy', facet_col_wrap=7, title='Stocks for each economy')#, markers=True)
            #write to html
            fig.write_html(root_dir + '/' +f'plotting_output/input_exploration/gompertz/log_fit_new_stocks_all_economies.html')

            ######################
            fig = px.line(all_data_stocks, x='Gdp_per_capita', y='Stocks_value', facet_col='Economy', color='Transport Type Scenario', line_dash = 'Stocks',  facet_col_wrap=7, title='Stocks for each economy with x as gdp per cpita')#, markers=True)
            #write to html
            fig.write_html(root_dir + '/' +f'plotting_output/input_exploration/gompertz/log_fit_new_stocks_all_economies.html')

        ######################

        #now plot the activity growth vs the previous activity growth from the df activity_growth_estimates
                    
        #find growth rate of activity as the percentage change in activity from the previous year plus 1. make sur eto group by economy but not vehicle type (FOR NOW)
        #sum Activity_previous by economy and date #TODO, DOES THIS WORK
        all_data_activity_sum = all_data.groupby(['Economy', 'Transport Type','Date'])['Activity_previous'].sum().reset_index()
        all_data_activity_sum.sort_values(['Economy', 'Transport Type', 'Date'], inplace=True)
        all_data_activity_sum['Activity_growth_est_previous'] = all_data_activity_sum.groupby(['Transport Type', 'Economy'])['Activity_previous'].pct_change()+1
        #replace nan with 1
        all_data_activity_sum['Activity_growth_est_previous'].fillna(1, inplace=True)
        #merge back on to all_data
        all_data_activity = pd.merge(all_data, all_data_activity_sum[['Economy', 'Date','Transport Type', 'Activity_growth_est_previous']], on=['Economy', 'Transport Type','Date'], how='left')

        #melt
        all_data_activity_growth = all_data_activity[['Economy','Date','Transport Type', 'Gdp_per_capita', 'Activity_growth', 'Activity_growth_est_previous']]
        all_data_activity_growth = all_data_activity_growth.melt(id_vars=['Economy', 'Transport Type','Date', 'Gdp_per_capita'], value_vars=['Activity_growth', 'Activity_growth_est_previous'], var_name='Activity_growth', value_name='Activity_growth_value')
        
        #check its not empty
        if all_data_activity_growth.empty:
            pass
            #print('No data to plot log_fit_new_activity_growth, this means that there was no need for adjustment of the activity growth rates, because the stocks per capita were already in the right ballpark')
        else:
            #plot
            all_data_activity_growth['Transport Type Scenario'] = all_data_activity_growth['Transport Type'] + ' ' + all_data_activity_growth['Activity_growth']
            fig = px.line(all_data_activity_growth, x='Date', y='Activity_growth_value', color='Transport Type Scenario',line_dash='Activity_growth', facet_col='Economy', facet_col_wrap=7, title='Comparitive activity growth')#, markers=True)

            #write to html
            fig.write_html(root_dir + '/' +f'plotting_output/input_exploration/gompertz/log_fit_new_activity_growth.html')
        
        ######################

def plot_logistic_function_by_economy(model_data_logistic_predictions, activity_growth_estimates, parameters_estimates, new_model_data, show_plots, matplotlib_bool, plotly_bool, FIT_LOGISTIC_CURVE_TO_DATA):
    #we will plot the results of the logistic function fit. To cut down on the number of plots we will facet by economy and onily plot the first scenario
    #we will also plot the gamma value for each economy as a horizontal line if the data is on stock per capita
    #extact new_model_data that will be used
    #calcualte Stocks_per_thousand_capita for model data
    
    #calcualte stocks per capita
    new_model_data['Thousand_stocks_per_capita'] = new_model_data['Stocks']/new_model_data['Population']
    #convert to more readable units. We will convert back later if we need to #todo do we need to?
    new_model_data['Stocks_per_thousand_capita'] = new_model_data['Thousand_stocks_per_capita'] * 1000000
    new_model_data = new_model_data[['Date', 'Economy', 'Scenario', 'Transport Type', 'Stocks_per_thousand_capita','Stocks', 'Activity']].drop_duplicates()
    #sum up
    new_model_data = new_model_data.groupby(['Date', 'Economy', 'Scenario', 'Transport Type']).sum().reset_index()

    #join the dataframes together
    all_data = pd.merge(model_data_logistic_predictions, new_model_data, on=['Date', 'Economy', 'Scenario', 'Transport Type'], how='left', suffixes=('_logistic', '_previous'))
    #join on activity_growth_estimates. Note that this ISNT BY VEHIcle type
    all_data = pd.merge(all_data, activity_growth_estimates, on=['Date','Economy', 'Transport Type','Scenario'], how='left')
    
    # all_data = all_data.loc[(all_data['Scenario'] == config.SCENARIO_OF_INTEREST)]


    # #TEMP FIX SINCE WE ONLY CAULCATED STOCKS PER CAPITA FOR LDVS
    # #i think that we should only have passenger_vehicle as a vehicle type. check this.
    # if all_data['Transport Type'].unique() != 'passenger_vehicle':
    #     raise ValueError('We dont have stocks per capita for passenger vehicles. Check this')
    # else:
    #     print('We only have stocks per capita for passenger vehicles. This is a temporary fix')

        
    # all_data = all_data.loc[(all_data['Transport Type'] == 'lt')]#todo
    if plotly_bool:
        if all_data.empty:
            pass
            #print('No data to plot logistic function by economy, this means that there was no need for adjustment of the activity growth rates, because the stocks per capita were already in the right ballpark')
        else:
            for economy in all_data.Economy.unique():
                #filter for that economy
                all_data_economy = all_data.loc[(all_data['Economy'] == economy)]

                #first plot will be on the comparitive stocks per capita
                #filter for that data then melt
                all_data_stocks_per_capita = all_data_economy[['Date','Scenario','Transport Type','Gdp_per_capita', 'Economy', 'Stocks_per_thousand_capita_logistic', 'Stocks_per_thousand_capita_previous', 'Gompertz_gamma']]
                all_data_stocks_per_capita = all_data_stocks_per_capita.melt(id_vars=['Date', 'Economy', 'Scenario','Transport Type', 'Gdp_per_capita'], value_vars=['Stocks_per_thousand_capita_logistic', 'Stocks_per_thousand_capita_previous', 'Gompertz_gamma'], var_name='Measure', value_name='Stocks_per_thousand_capita_value')

                #check its not empty
                if all_data_stocks_per_capita.empty:
                    pass
                    #print('No data to plot logistic function by economy, this means that there was no need for adjustment of the activity growth rates, because the stocks per capita were already in the right ballpark')
                else:
                        
                    fig = px.line(all_data_stocks_per_capita, x='Date', y='Stocks_per_thousand_capita_value', color='Transport Type',line_dash='Measure', title=f'Comparitive stocks per capita {economy}', facet_col='Scenario', facet_col_wrap=1)#, markers=True)

                    #write to html
                    fig.write_html(root_dir + '/' +f'plotting_output/input_exploration/gompertz/economy/log_fit_new_stocks_per_capita_{economy}.html')
                    
                    #and plot the same but wth gdp per capita in x
                    fig = px.line(all_data_stocks_per_capita, x='Gdp_per_capita', y='Stocks_per_thousand_capita_value', line_dash='Measure', color='Transport Type', title=f'Comparitive stocks per capita vs GDP per capita {economy}', facet_col='Scenario', facet_col_wrap=1)#, markers=True)#, markers=True)

                    #write to html
                    fig.write_html(root_dir + '/' +f'plotting_output/input_exploration/gompertz/economy/log_fit_new_stocks_per_capita_gdp_per_capita_{economy}.html')

                #now plot the activity growth vs the previous activity growth from the df activity_growth_estimates
                            
                #find growth rate of activity as the percentage change in activity from the previous year plus 1. make sur eto group by economy but not vehicle type (FOR NOW)
                #sum Activity_previous by economy and date #TODO, DOES THIS WORK
                all_data_activity_sum = all_data_economy.groupby(['Economy', 'Transport Type','Scenario','Date'])['Activity_previous'].sum().reset_index()
                all_data_activity_sum.sort_values(['Economy', 'Scenario', 'Transport Type', 'Date'], inplace=True)
                all_data_activity_sum['Activity_growth_est_previous'] = all_data_activity_sum.groupby(['Transport Type', 'Scenario','Economy'])['Activity_previous'].pct_change()+1
                #replace nan with 1
                all_data_activity_sum['Activity_growth_est_previous'].fillna(1, inplace=True)
                #merge back on to all_data
                all_data_activity = pd.merge(all_data_economy, all_data_activity_sum[['Economy', 'Date','Transport Type',  'Scenario','Activity_growth_est_previous']], on=['Economy','Transport Type',  'Scenario','Date'], how='left')

                #melt
                all_data_activity_growth = all_data_activity[['Economy','Date','Scenario','Transport Type', 'Gdp_per_capita', 'Activity_growth', 'Activity_growth_est_previous']]
                all_data_activity_growth = all_data_activity_growth.melt(id_vars=['Economy', 'Transport Type','Date','Scenario', 'Gdp_per_capita'], value_vars=['Activity_growth', 'Activity_growth_est_previous'], var_name='Activity_growth', value_name='Activity_growth_value')

                #check its not empty
                if all_data_activity_growth.empty:
                    pass
                    #print('No data to plot logistic function by economy, this means that there was no need for adjustment of the activity growth rates, because the stocks per capita were already in the right ballpark')
                else:
                        
                    fig = px.line(all_data_activity_growth, x='Date', y='Activity_growth_value', color='Transport Type',line_dash='Activity_growth', title=f'Comparitive activity growth {economy}', facet_col='Scenario', facet_col_wrap=1)#, markers=True)#, markers=True)

                    #write to html
                    fig.write_html(root_dir + '/' +f'plotting_output/input_exploration/gompertz/economy/log_fit_new_activity_growth_{economy}.html')
                
                #o same graph for stocks:
                all_data_economy_stocks = all_data_economy[['Economy','Date','Scenario','Transport Type', 'Gdp_per_capita', 'Stocks_logistic', 'Stocks_previous']]
                #melt
                all_data_economy_stocks_melt = all_data_economy_stocks.melt(id_vars=['Economy', 'Transport Type','Date','Scenario', 'Gdp_per_capita'], value_vars=['Stocks_logistic', 'Stocks_previous'], var_name='Stocks', value_name='Stocks_value')
                fig = px.line(all_data_economy_stocks_melt, x='Date', y='Stocks_value', color='Transport Type',line_dash='Stocks', title=f'Comparitive stocks {economy}', facet_col='Scenario', facet_col_wrap=1)#, markers=True)#, markers=True)
                fig.write_html(root_dir + '/' +f'plotting_output/input_exploration/gompertz/economy/log_fit_new_stocks_{economy}.html')
                
def plot_aggregated_input_data_for_logisitc_fitting(ECONOMY_ID, new_model_data):
    #the pltos will go in \input_exploration\gompertz\aggregated_input_data
    #plot the data for ['Economy', 'Scenario', 'Date', 'Transport Type']
    a = new_model_data.copy()
    a['Transport Type'] = a['Transport Type']+'_'+a['Scenario'] + '_'+a['Economy']
    fig = px.line(a, x='Date', y='Stocks', color='Transport Type')
    fig.write_html(root_dir + '/' + 'plotting_output/input_exploration/gompertz/aggregated_input_data/{}_stocks.html'.format(ECONOMY_ID))
    
    fig = px.line(a, x='Date', y='Activity', color='Transport Type')
    fig.write_html(root_dir + '/' + 'plotting_output/input_exploration/gompertz/aggregated_input_data/{}_activity.html'.format(ECONOMY_ID))
    
    fig = px.line(a, x='Date', y='Travel_km', color='Transport Type')
    fig.write_html(root_dir + '/' + 'plotting_output/input_exploration/gompertz/aggregated_input_data/{}_travel_km.html'.format(ECONOMY_ID))
    
    fig = px.line(a, x='Date', y='Mileage', color='Transport Type')
    fig.write_html(root_dir + '/' + 'plotting_output/input_exploration/gompertz/aggregated_input_data/{}_mileage.html'.format(ECONOMY_ID))
    
    fig = px.line(a, x='Date', y='Occupancy_or_load', color='Transport Type')
    fig.write_html(root_dir + '/' + 'plotting_output/input_exploration/gompertz/aggregated_input_data/{}_occupancy_or_load.html'.format(ECONOMY_ID))
    
    fig = px.line(a, x='Date', y='Population', color='Transport Type')
    fig.write_html(root_dir + '/' + 'plotting_output/input_exploration/gompertz/aggregated_input_data/{}_population.html'.format(ECONOMY_ID))
    
    fig = px.line(a, x='Date', y='Gdp_per_capita', color='Transport Type')
    fig.write_html(root_dir + '/' + 'plotting_output/input_exploration/gompertz/aggregated_input_data/{}_gdp_per_capita.html'.format(ECONOMY_ID))
    
    return