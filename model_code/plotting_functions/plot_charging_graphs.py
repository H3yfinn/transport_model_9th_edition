
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
from .. import utility_functions
from ..calculation_functions import estimate_charging_requirements
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
def plot_required_chargers(config, ECONOMY_ID):
    # total_kwh_of_battery_capacity.to_csv(r'output_data\for_other_modellers\estimated_number_of_chargers.csv', index=False) 
    #grab colors dict:
    df, parameters, colors_dict, INCORPORATE_UTILISATION_RATE = estimate_charging_requirements.prepare_inputs_for_estimating_charging_requirements(config, ECONOMY_ID)
    
    total_kwh_of_battery_capacity = pd.read_csv(config.root_dir + '\\' +f'output_data\\for_other_modellers\\charging\\{ECONOMY_ID}_estimated_number_of_chargers.csv')

    #use plotly to plot the number of chargers required for each economy, date and scenario and also by vehicle type.
    #total_kwh_of_battery_capacity'Economy','Date','Scenario','Vehicle Type','Stocks', 'sum_of_stocks','kwh_of_battery_capacity','sum_of_kwh_of_battery_capacity','sum_of_expected_number_of_chargers','expected_kw_of_chargers','sum_of_expected_kw_of_chargers','expected_number_of_chargers','sum_of_fast_kw_of_chargers_needed',,'sum_of_slow_kw_of_chargers_needed','sum_of_fast_chargers_needed','sum_of_slow_chargers_needed','fast_charger_utilisation_rate','average_kwh_of_battery_capacity_by_vehicle_type','average_kw_per_charger','average_kw_per_non_fast_charger','average_kw_per_fast_charger','slow_kw_of_chargers_needed','fast_kw_of_chargers_needed','slow_chargers_needed','fast_chargers_needed'
    """
    1. (number of chargers vs evs)
    #number of chargers required on time series for each economy, date and scenario. this can be a line chart with a line for each economy, date and scenario, < do these for all economies only since they are simple graphs
    
    #then show the above but with the cahrgers as bars and the number of stocks of each vehicle type as lines with the other y axis, so as to show the number of chargers required compared to the number of stocks of each vehicle type. Can include a total line for total stocks of vehicles too
    2. (kw of chargers vs kwh evs)
    #number of chargers required on time series for each economy, date and scenario. this can be a line chart with a line for each economy, date and scenario, < do these for all economies only since they are simple graphs
    
    #then show the aoove but with the chargers as bars and the kwh of vehicle battery capacity of each vehicle type as lines, so as to show the number of chargers required compared to the caapcity of each vehicle type. Can include a total line for total capacity of all vehicles too
    
    3. # wherever there are two axis  we cannot facet by economy, but where we have one axis we should facet by economy so that we can see the difference between economies.
    
    """
    #1.
    #cahrgers as bars and the number of stocks of each vehicle type as lines with the other y axis, so as to show the number of chargers required compared to the number of stocks of each vehicle type. Can include a total line for total stocks of vehicles too
    # Loop through each economy and scenario
    df = total_kwh_of_battery_capacity.copy()
    for economy in df['Economy'].unique():
        for scenario in df['Scenario'].unique():
            # Filter the dataframe for the current economy and scenario
            df_filtered = df[(df['Economy'] == economy) & (df['Scenario'] == scenario)]
            #sort by date
            df_filtered = df_filtered.sort_values(by=['Date'])
            title = f'Number of chargers and stocks for {economy} in {scenario}'
            # Create subplot with 1 row and 1 column, and specify secondary y-axis
            fig = make_subplots(rows=1, cols=1, specs=[[{'secondary_y': True}]])
            
            # Add a bar trace for the number of chargers
            sum_of_expected_number_of_chargers = df_filtered[['Date','sum_of_expected_number_of_chargers']].drop_duplicates()
            fig.add_trace(
                go.Bar(x=sum_of_expected_number_of_chargers['Date'], y=sum_of_expected_number_of_chargers['sum_of_expected_number_of_chargers'], name='Number of Chargers', opacity=0.5, marker=dict(color='grey')),
                secondary_y=False
            )

            # Add a line trace for each vehicle type
            for vehicle_type in df_filtered['Vehicle Type'].unique():
                df_vehicle = df_filtered[df_filtered['Vehicle Type'] == vehicle_type]
                fig.add_trace(
                    go.Scatter(x=df_vehicle['Date'], y=df_vehicle['Stocks_'+parameters['stocks_magnitude_name']], mode='lines', name=vehicle_type,
                    line=dict(color=colors_dict[vehicle_type])),
                    secondary_y=True
                )

            # Optionally, add a total line for total stocks of vehicles
            # Assuming you have a column 'total_stocks' representing the total stocks of vehicles
            sum_of_stocks = df_filtered[['Date','sum_of_stocks']].drop_duplicates()
            fig.add_trace(
                go.Scatter(x=sum_of_stocks['Date'], y=sum_of_stocks['sum_of_stocks'], mode='lines', name='Total Stocks',
                line=dict(dash='dash', color='black')),
                secondary_y=True
            )

            
            # Set the range for the primary y-axis
            fig.update_yaxes(range=[0, sum_of_expected_number_of_chargers['sum_of_expected_number_of_chargers'].max()], secondary_y=False)

            # Set the range for the secondary y-axis
            fig.update_yaxes(range=[0, sum_of_stocks['sum_of_stocks'].max()], secondary_y=True)
            
            # Set the titles for the y-axes
            fig.update_yaxes(title_text="Number of Chargers", secondary_y=False)
            fig.update_yaxes(title_text="Stocks of Each Vehicle Type", secondary_y=True)

            # Set the title of the plot
            fig.update_layout(title_text=title)

            # wrtite the plot to a file
            fig.write_html(config.root_dir + '\\' +f'plotting_output\\charging_requirements\\{title}.html')
            
            ############################################################
            
            #and plot kw version:
            
            title = f'Kw of chargers and Kwh of bev battery capacity for {economy} in {scenario}'
            # Create subplot with 1 row and 1 column, and specify secondary y-axis
            fig = make_subplots(rows=1, cols=1, specs=[[{'secondary_y': True}]])

            # Add a bar trace for the number of chargers
            sum_of_expected_kw_of_chargers = df_filtered[['Date','sum_of_expected_kw_of_chargers']].drop_duplicates()
            fig.add_trace(
                go.Bar(x=sum_of_expected_kw_of_chargers['Date'], y=sum_of_expected_kw_of_chargers['sum_of_expected_kw_of_chargers'], name='Kw of Chargers', opacity=0.5,marker=dict(color='grey')),
                secondary_y=False
            )

            # Add a line trace for each vehicle type
            for vehicle_type in df_filtered['Vehicle Type'].unique():
                df_vehicle = df_filtered[df_filtered['Vehicle Type'] == vehicle_type]
                fig.add_trace(
                    go.Scatter(x=df_vehicle['Date'], y=df_vehicle['kwh_of_battery_capacity'], mode='lines', name=vehicle_type,line=dict(color=colors_dict[vehicle_type])),
                    secondary_y=True
                )
            # Optionally, add a total line for total stocks of vehicles
            # Assuming you have a column 'total_stocks' representing the total stocks of vehicles
            sum_of_kwh_of_battery_capacity = df_filtered[['Date','sum_of_kwh_of_battery_capacity']].drop_duplicates()
            fig.add_trace(
                go.Scatter(x=sum_of_kwh_of_battery_capacity['Date'], y=sum_of_kwh_of_battery_capacity['sum_of_kwh_of_battery_capacity'], mode='lines', name='Total battery capacity of all bev vehicles (kwh)',
                line=dict(dash='dash', color='black')),
                secondary_y=True
            )
            # Set the range for the primary y-axis
            fig.update_yaxes(range=[0, sum_of_expected_kw_of_chargers['sum_of_expected_kw_of_chargers'].max()], secondary_y=False)

            # Set the range for the secondary y-axis
            fig.update_yaxes(range=[0, sum_of_kwh_of_battery_capacity['sum_of_kwh_of_battery_capacity'].max()], secondary_y=True)
            
                        # Set the titles for the y-axes
            fig.update_yaxes(title_text="Kw of chargers", secondary_y=False)
            fig.update_yaxes(title_text="Kwh of batteries", secondary_y=True)

            # Set the title of the plot
            fig.update_layout(title_text=title)

            # wrtite the plot to a file
            fig.write_html(config.root_dir + '\\' +f'plotting_output\\charging_requirements\\{title}.html')
            
            
            ############################################################
            # FAST VS SLOW CHARGERS
            ############################################################
            #and plot number version split into fast vs slow chargers
            
            title =f'Number of fast and slow public chargers and number of stocks for {economy} in {scenario}'
            # Create subplot with 1 row and 1 column, and specify secondary y-axis
            fig = make_subplots(rows=1, cols=1, specs=[[{'secondary_y': True}]])

            # Add a bar trace for the number of fast chargers
            sum_of_expected_kw_of_fast_chargers = df_filtered[['Date','sum_of_fast_chargers_needed']].drop_duplicates()
            fig.add_trace(
                go.Bar(x=sum_of_expected_kw_of_fast_chargers['Date'], y=sum_of_expected_kw_of_fast_chargers['sum_of_fast_chargers_needed'], name='Fast chargers', opacity=0.5,marker=dict(color='orange')),
                secondary_y=False
            )

            # Add a bar trace for the number of slow chargers
            sum_of_expected_kw_of_slow_chargers = df_filtered[['Date','sum_of_slow_chargers_needed']].drop_duplicates()
            fig.add_trace(
                go.Bar(x=sum_of_expected_kw_of_slow_chargers['Date'], y=sum_of_expected_kw_of_slow_chargers['sum_of_slow_chargers_needed'], name='Slow chargers', opacity=0.5,marker=dict(color='yellow')),
                secondary_y=False
            )

            # Set the barmode to 'stack'
            fig.update_layout(barmode='stack')
            # Add a line trace for each vehicle type
            for vehicle_type in df_filtered['Vehicle Type'].unique():
                df_vehicle = df_filtered[df_filtered['Vehicle Type'] == vehicle_type]
                fig.add_trace(
                    go.Scatter(x=df_vehicle['Date'], y=df_vehicle['Stocks_'+parameters['stocks_magnitude_name']], mode='lines', name=vehicle_type,line=dict(color=colors_dict[vehicle_type])),
                    secondary_y=True
                )

            # Optionally, add a total line for total stocks of vehicles
            # Assuming you have a column 'total_stocks' representing the total stocks of vehicles
            sum_of_stocks = df_filtered[['Date','sum_of_stocks']].drop_duplicates()
            fig.add_trace(
                go.Scatter(x=sum_of_stocks['Date'], y=sum_of_stocks['sum_of_stocks'], mode='lines', name='Total Stocks',
                line=dict(dash='dash', color='black')),
                secondary_y=True
            )

            
            # Set the range for the primary y-axis
            sum_of_expected_number_of_chargers = df_filtered[['Date','sum_of_expected_number_of_chargers']].drop_duplicates()
            fig.update_yaxes(range=[0, sum_of_expected_number_of_chargers['sum_of_expected_number_of_chargers'].max()], secondary_y=False)

            # Set the range for the secondary y-axis
            fig.update_yaxes(range=[0, sum_of_stocks['sum_of_stocks'].max()], secondary_y=True)
            
            # Set the titles for the y-axes
            fig.update_yaxes(title_text="Number of Chargers", secondary_y=False)
            fig.update_yaxes(title_text="Stocks of Each Vehicle Type", secondary_y=True)

            # Set the title of the plot
            fig.update_layout(title_text=title)

            # wrtite the plot to a file
            fig.write_html(config.root_dir + '\\' +f'plotting_output\\charging_requirements\\{title}.html')
            ############################################################
            
            ############################################################
            
            #and plot kw version split into fast vs slow chargers
            
            title = f'Kw of public chargers and Kwh of bev battery capacity for {economy} in {scenario} split into fast and slow chargers'
            # Create subplot with 1 row and 1 column, and specify secondary y-axis
            fig = make_subplots(rows=1, cols=1, specs=[[{'secondary_y': True}]])

            # Add a bar trace for the number of fast chargers
            sum_of_expected_kw_of_fast_chargers = df_filtered[['Date','sum_of_fast_kw_of_chargers_needed']].drop_duplicates()
            fig.add_trace(
                go.Bar(x=sum_of_expected_kw_of_fast_chargers['Date'], y=sum_of_expected_kw_of_fast_chargers['sum_of_fast_kw_of_chargers_needed'], name='Kw of Fast chargers', opacity=0.5,marker=dict(color='orange')),
                secondary_y=False
            )

            # Add a bar trace for the number of slow chargers
            sum_of_expected_kw_of_slow_chargers = df_filtered[['Date','sum_of_slow_kw_of_chargers_needed']].drop_duplicates()
            fig.add_trace(
                go.Bar(x=sum_of_expected_kw_of_slow_chargers['Date'], y=sum_of_expected_kw_of_slow_chargers['sum_of_slow_kw_of_chargers_needed'], name='Kw of Slow chargers', opacity=0.5,marker=dict(color='yellow')),
                secondary_y=False
            )

            # Set the barmode to 'stack'
            fig.update_layout(barmode='stack')
            # Add a line trace for each vehicle type
            for vehicle_type in df_filtered['Vehicle Type'].unique():
                df_vehicle = df_filtered[df_filtered['Vehicle Type'] == vehicle_type]
                fig.add_trace(
                    go.Scatter(x=df_vehicle['Date'], y=df_vehicle['kwh_of_battery_capacity'], mode='lines', name=vehicle_type,line=dict(color=colors_dict[vehicle_type])),
                    secondary_y=True
                )
            # Optionally, add a total line for total stocks of vehicles
            # Assuming you have a column 'total_stocks' representing the total stocks of vehicles
            sum_of_kwh_of_battery_capacity = df_filtered[['Date','sum_of_kwh_of_battery_capacity']].drop_duplicates()
            fig.add_trace(
                go.Scatter(x=sum_of_kwh_of_battery_capacity['Date'], y=sum_of_kwh_of_battery_capacity['sum_of_kwh_of_battery_capacity'], mode='lines', name='Total battery capacity of all bev vehicles (kwh)',
                line=dict(dash='dash', color='black')),
                secondary_y=True
            )
            # Set the range for the primary y-axis
            sum_of_expected_kw_of_chargers = df_filtered[['Date','sum_of_expected_kw_of_chargers']].drop_duplicates()
            fig.update_yaxes(range=[0, sum_of_expected_kw_of_chargers['sum_of_expected_kw_of_chargers'].max()], secondary_y=False)

            # Set the range for the secondary y-axis
            fig.update_yaxes(range=[0, sum_of_kwh_of_battery_capacity['sum_of_kwh_of_battery_capacity'].max()], secondary_y=True)
            
                        # Set the titles for the y-axes
            fig.update_yaxes(title_text="Kw of chargers", secondary_y=False)
            fig.update_yaxes(title_text="Kwh of batteries", secondary_y=True)

            # Set the title of the plot
            fig.update_layout(title_text=title)

            # wrtite the plot to a file
            fig.write_html(config.root_dir + '\\' +f'plotting_output\\charging_requirements\\{title}.html')
            ############################################################
    # #now plot all economies together for each scenario:
    # for scenario in df['Scenario'].unique():
    #     df_scenario = df[df['Scenario'] == scenario]
        

  
def plot_required_evs(config, ev_stocks_and_chargers, colors_dict, economy, date, scenario):
    #[['Economy','Date','Scenario','Vehicle Type',"Transport Type",'expected_kwh_of_battery_capacity', 'sum_of_expected_kwh_of_battery_capacity','expected_stocks', 'total_expected_stocks', 'portion_of_stocks_kwh_of_battery_capacity','number_of_chargers','number_of_fast_chargers','number_of_non_fast_chargers','kw_of_charger_capacity','kw_of_fast_charger_capacity','kw_of_non_fast_charger_capacity']]
    #use plotly to plot the number of chargers required for each economy, date and scenario and also by vehicle type.
    
    #things id like to plot:
    #number of evs of each vehicle type given the amount of cahrgers. this can be a stacked bar chart with a column for each transport type, color for each vehicle type (stacked). #then on the alternative axis show the number of chargers required for each vehicle type
    # Then produce the same graph to show the total kwh of battery capacity required (isntead of stocks), shown in same way, so as to show the amount of battery capacity required for each vehicle type, copared to the total stocks of those vehicle types. #then on the alternative axis show the kw of chargers required for each vehicle type
    number_of_chargers = ev_stocks_and_chargers['number_of_chargers'].iloc[0]
    kw_of_charger_capacity = ev_stocks_and_chargers['kw_of_charger_capacity'].iloc[0]
    
    title = 'Number of EVs for {} public chargers {}kw in {}, {}, {}'.format(number_of_chargers, round(kw_of_charger_capacity,0),economy, date, scenario)
    
    #set prder pf vehicle types using keys in colors_dict:
    vehicle_types_order = list(colors_dict.keys())
    
    # First, pivot your DataFrame so that each vehicle type is a column. This is necessary for stacked bar charts in plotly.
    stocks_pivot = ev_stocks_and_chargers.pivot(columns='Vehicle Type', values='expected_stocks')
    charger_pivot = ev_stocks_and_chargers.pivot(columns='Vehicle Type', values='expected_number_of_chargers_by_vehicle_type')
    
    #sort the df cols by vehicle type order:
    stocks_pivot = stocks_pivot[vehicle_types_order]
    charger_pivot = charger_pivot[vehicle_types_order]
    # Create subplot with 1 row and 1 column, and specify secondary y-axis
    fig = make_subplots(rows=1, cols=1, specs=[[{'secondary_y': True}]])

    # Add a bar trace for each vehicle type for expected stocks
    for vehicle_type in stocks_pivot.columns:
        fig.add_trace(
            go.Bar(x=['Stocks']*len(stocks_pivot[vehicle_type]), y=stocks_pivot[vehicle_type], name=vehicle_type,marker=dict(color=colors_dict[vehicle_type])),
            secondary_y=False
        )

    # Add a bar trace for each vehicle type for expected chargers
    for vehicle_type in charger_pivot.columns:
        fig.add_trace(
            go.Bar(x=['Chargers']*len(charger_pivot[vehicle_type]), y=charger_pivot[vehicle_type], name=vehicle_type,marker=dict(color=colors_dict[vehicle_type])),
            secondary_y=True
        )

    # Set barmode to stack
    fig.update_layout(barmode='stack')

    # Set the titles for the y-axes
    fig.update_yaxes(title_text="Expected Stocks", secondary_y=False)
    fig.update_yaxes(title_text="Expected Chargers", secondary_y=True)

    # Set the title of the plot
    fig.update_layout(title_text=title)

    # write to html in plotting_output\charging_requirements
    fig.write_html(config.root_dir + '\\' +f'plotting_output\\charging_requirements\\{title}.html')

    #############################################################################do same but using batteries instead of stocks:
    title = 'Kw of EVs for {} public chargers {}kw in {}, {}, {}'.format(number_of_chargers, round(kw_of_charger_capacity,0),economy, date, scenario)
    
    battery_pivot = ev_stocks_and_chargers.pivot(columns='Vehicle Type', values='expected_kwh_of_battery_capacity')
    charger_pivot = ev_stocks_and_chargers.pivot(columns='Vehicle Type', values='expected_kw_of_chargers_by_vehicle_type')
    
    #sort the df cols by vehicle type order:
    battery_pivot = battery_pivot[vehicle_types_order]
    charger_pivot = charger_pivot[vehicle_types_order]
    
    # Create subplot with 1 row and 1 column, and specify secondary y-axis
    fig = make_subplots(rows=1, cols=1, specs=[[{'secondary_y': True}]])

    # Add a bar trace for each vehicle type for expected battery capacity
    for vehicle_type in battery_pivot.columns:
        fig.add_trace(
            go.Bar(x=['Kwh of batteries']*len(battery_pivot[vehicle_type]), y=battery_pivot[vehicle_type], name=vehicle_type, marker=dict(color=colors_dict[vehicle_type])),
            secondary_y=False
        )
    # Add a bar trace for each vehicle type for expected chargers
    for vehicle_type in charger_pivot.columns:
        fig.add_trace(
            go.Bar(x=['Kw of chargers']*len(charger_pivot[vehicle_type]), y=charger_pivot[vehicle_type], name=vehicle_type,opacity=0.5,marker=dict(color=colors_dict[vehicle_type])),
            secondary_y=True
        )

    # Set barmode to stack
    fig.update_layout(barmode='stack')

    # Set the titles for the y-axes
    fig.update_yaxes(title_text="Expected Kwh of vehicle batteries", secondary_y=False)
    fig.update_yaxes(title_text="Expected Kw of chargers", secondary_y=True)

    # Set the title of the plot
    fig.update_layout(title_text=title)

    # write to html in plotting_output\charging_requirements
    fig.write_html(config.root_dir + '\\' +f'plotting_output\\charging_requirements\\{title}.html')

    