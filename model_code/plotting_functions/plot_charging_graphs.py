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
#ok lets simplify things a bit. want to create a dashboard with plots for num,ber of fast and slow chargers, number of evs by vehicle type, ratio of chargers to evs by vehicle type, and kw of chargers per vehicle type.

def plot_ratios(df, iea_df=None):
            
    #now calaculate
    if iea_df is not None:
        #calcualte the ratios for the IEA data. We'll use the same public charger utilisation rate as the model data
        #first change the vehicle types to match the model data categories:
        iea_df_ratio= iea_df.copy()
        iea_df_ratio['vehicle type'] = iea_df_ratio['vehicle type'].replace({'ht':'ht','mt':'mt','2w':'2w','bus':'bus','suv':'suv','car':'car','lpv':'car','lcv':'lcv'})
        #convert Date to YYYY and drop the rest of the date
        iea_df_ratio['date'] = pd.to_datetime(iea_df_ratio['date']).dt.year
        #keep only drive == phev and bev
        iea_df_ratio = iea_df_ratio[(iea_df_ratio['drive'].isin(['bev','phev']) | (iea_df_ratio['measure'] == 'EV Charging points'))]
        #keep iea_df_ratio['measure'] == 'Stocks' and 'EV Charging points' then pviot to get the stocks and chargers in their own columns
        iea_df_ratio = iea_df_ratio[iea_df_ratio['measure'].isin(['Stocks','EV Charging points'])]
        #and get source == Projection-STEPS
        iea_df_ratio = iea_df_ratio[iea_df_ratio['source'] == 'Projection-STEPS']
        #where drive is Publicly available fast, set measure to fast_chargers and where drive is Publicly available slow, set measure to slow_chargers
        iea_df_ratio.loc[iea_df_ratio['drive'] == 'Publicly available fast', 'measure'] = 'fast_chargers'
        iea_df_ratio.loc[iea_df_ratio['drive'] == 'Publicly available slow', 'measure'] = 'slow_chargers'
        
        #rename certain cols and drop others: make vehicle type and drive have capitals
        iea_df_ratio = iea_df_ratio.rename(columns={'vehicle type':'Vehicle Type', 'drive':'Drive', 'date':'Date'})
        
        #join the avg utilisation rate onto iea df from the model data
        iea_df_ratio = iea_df_ratio.merge(df[['public_charger_utilisation_rate','Drive', 'Vehicle Type']].groupby(['Drive', 'Vehicle Type']).mean().reset_index(), on=['Drive', 'Vehicle Type'], how='left')

        #times util rate by stocks to adjust them
        iea_df_ratio.loc[iea_df_ratio['measure'] == 'Stocks', 'value'] = iea_df_ratio['value'] * iea_df_ratio['public_charger_utilisation_rate']
        
        iea_df_ratio = iea_df_ratio.pivot(index=['Date','Vehicle Type','Drive'], columns='measure', values='value').reset_index()
        
        #now calculate the ratio of chargers to evs. We will ignore kw of chargers to evs for now
        iea_df_ratio = iea_df_ratio.groupby(['Date']).sum(numeric_only=True).reset_index()
        try:
            iea_df_ratio['ratio_of_chargers_to_stocks'] = (iea_df_ratio['slow_chargers'] + iea_df_ratio['fast_chargers'])/iea_df_ratio['Stocks']
        except:
            breakpoint()  
        iea_df_ratio['stocks_per_charger'] =1/iea_df_ratio['ratio_of_chargers_to_stocks']
        iea_df_ratio['Dataset'] = 'IEA'

    #we will calcculate the ratio of chargers to evs, and kw of chargers to evs. We will ignore vehicle type for now since it complicates things.
    df['Stocks'] = df['Stocks_millions'] * 1e6 * df['public_charger_utilisation_rate']
    #sum up stocks and chargers by date
    df_summed = df.groupby(['Date']).sum(numeric_only=True).reset_index()
    df_summed['ratio_of_chargers_to_stocks'] = (df_summed['slow_chargers'] + df_summed['fast_chargers'])/df_summed['Stocks']

    #and calculate the ratio of kw of chargers to evs
    df_summed['ratio_of_kw_of_chargers_to_stocks'] = df_summed['kw_of_chargers']/df_summed['Stocks']

    df_summed['stocks_per_charger'] =1/df_summed['ratio_of_chargers_to_stocks']

    if iea_df_ratio is not None:
        df_summed['Dataset'] = 'APERC'
        df_summed = pd.concat([df_summed, iea_df_ratio], ignore_index=True)
        #now plot the ratios
        title_ratio_of_chargers_to_stocks = 'Number of (adjusted) EV stocks per public charger, compared to IEA'
        fig_ratio_of_chargers_to_stocks = px.line(df_summed, x='Date', y='stocks_per_charger', title=title_ratio_of_chargers_to_stocks, line_dash='Dataset')
    else:
        title_ratio_of_chargers_to_stocks = 'Number of (adjusted) EV stocks per public charger'
        fig_ratio_of_chargers_to_stocks = px.line(df_summed, x='Date', y='stocks_per_charger', title=title_ratio_of_chargers_to_stocks)
    title_ratio_of_kw_of_chargers_to_stocks='Ratio of kw of chargers to stocks'
    fig_ratio_of_kw_of_chargers_to_stocks = px.line(df_summed, x='Date', y='ratio_of_kw_of_chargers_to_stocks', title=title_ratio_of_kw_of_chargers_to_stocks)

    return fig_ratio_of_chargers_to_stocks, fig_ratio_of_kw_of_chargers_to_stocks, title_ratio_of_chargers_to_stocks, title_ratio_of_kw_of_chargers_to_stocks

def plot_fast_and_slow_chargers(df, iea_df=None): 

    if iea_df is not None:
        #we will icnlude the iea data in this plot
        #need to filter for source==Projection-STEPS and measure==EV Charging points then pivot the drive col so we have fast and slow chargers in their own cols
        iea_df = iea_df[(iea_df['source'] == 'Projection-STEPS') & (iea_df['measure'] == 'EV Charging points')]
        iea_df = iea_df[iea_df['drive'].isin(['Publicly available fast', 'Publicly available slow'])]
        iea_df['date'] = pd.to_datetime(iea_df['date']).dt.year 
        iea_df = iea_df.pivot(index=['date'], columns='drive', values='value').reset_index()
        #convert Publicly available fast  Publicly available slow to fast_chargers and slow_chargers
        iea_df = iea_df.rename(columns={'Publicly available fast':'fast_chargers', 'Publicly available slow':'slow_chargers', 'date':'Date'})
        iea_df['Dataset'] = 'IEA'
        
        #sum up stocks and chargers by date
        df_summed = df.groupby(['Date']).sum().reset_index()
        df_summed['Dataset'] = 'APERC'
        df_summed = pd.concat([df_summed, iea_df], ignore_index=True)
        df_summed = df_summed.sort_values(by=['Date'])
        title = 'Number of fast and slow public chargers'
        fig = px.line(df_summed, x='Date', y=['slow_chargers','fast_chargers'], title=title, line_dash='Dataset')
    else:
        #sum up stocks and chargers by date
        df_summed = df.groupby(['Date']).sum().reset_index()
        df_summed = df_summed.sort_values(by=['Date'])
        title = 'Number of fast and slow public chargers'
        fig = px.line(df_summed, x='Date', y=['slow_chargers','fast_chargers'], title=title)
        
    return fig, title

def plot_kw_per_fast_charger_kw_per_slow_charger(df_filtered):

    #extract average_kw_per_fast_charger and average_kw_per_slow_charger
    average_kw_per_fast_charger = df_filtered['average_kw_per_fast_charger'].iloc[0]
    average_kw_per_slow_charger = df_filtered['average_kw_per_slow_charger'].iloc[0]

    temp = pd.DataFrame({'Average Kw Per Charger':[average_kw_per_fast_charger, average_kw_per_slow_charger], 'Charger Type':['Fast Chargers', 'Slow Chargers']})

    title = 'Average kw per fast and slow public chargers'

    fig = px.bar(temp, x='Charger Type', y='Average Kw Per Charger', color='Charger Type', title=title)
    return fig, title


def plot_bar_of_average_kw_of_fast_and_slow_chargers_per_vehicle_by_vehicle_type(df):#plot_bar_of_average_utilisation_of_fast_and_slow_chargers_by_vehicle_type(df):
    #sum up stocks and chargers by date
    df['Vehicle Type'] = df['Vehicle Type'].replace({'ht':'truck','mt':'truck','2w':'motorcycle & bus','bus':'motorcycle & bus','suv':'car','car':'car','lt':'car', 'lcv':'lcv'})
    #sum up stocks and chargers by vehicle type then divide stocks by chargers to get average chargers needed
    df = df.groupby(['Vehicle Type']).sum(numeric_only=True).reset_index()
    df['average_fast_charger_kw_per_stock'] = df['fast_kw_of_chargers']/(df['Stocks'] * 1e6)
    df['average_slow_charger_kw_per_stock'] = df['slow_kw_of_chargers']/(df['Stocks'] * 1e6)
    df = df[['Vehicle Type', 'average_fast_charger_kw_per_stock', 'average_slow_charger_kw_per_stock']]
    df = df.melt(id_vars=['Vehicle Type'], value_vars=['average_fast_charger_kw_per_stock', 'average_slow_charger_kw_per_stock'], var_name='Charger Type', value_name='Average Kw Per Stock')
    df['Charger Type'] = df['Charger Type'].replace({'average_fast_charger_kw_per_stock':'Fast Chargers', 'average_slow_charger_kw_per_stock':'Slow Chargers'})

    title = 'Average kw of charger utilisation per stock'
    fig = px.bar(df, x='Vehicle Type', y='Average Kw Per Stock', title=title, color='Charger Type')

    return fig, title

def plot_bar_of_average_utilisation_of_fast_and_slow_chargers_by_vehicle_type(df):
    #sum up stocks and chargers by date
    df['Vehicle Type'] = df['Vehicle Type'].replace({'ht':'truck','mt':'truck','2w':'motorcycle & bus','bus':'motorcycle & bus','suv':'car','car':'car','lt':'car', 'lcv':'lcv'})

    #drop drive type and sum
    df = df.drop(columns=['Drive'])
    df = df.groupby(['Date', 'Vehicle Type']).sum().reset_index()

    #calcaulte the average percent of total fast and slow charger capacity that each vehicle type uses and call it charger utilisation
    df['sum_of_fast_kw_of_chargers'] = df.groupby(['Date'])['fast_kw_of_chargers'].transform('sum')
    df['sum_of_slow_kw_of_chargers'] = df.groupby(['Date'])['slow_kw_of_chargers'].transform('sum')

    df['share_of_fast_charger_capacity'] = df['fast_kw_of_chargers']/df['sum_of_fast_kw_of_chargers'] * 100
    df['share_of_slow_charger_capacity'] = df['slow_kw_of_chargers']/df['sum_of_slow_kw_of_chargers'] * 100

    #calc average share per vehicle type
    df_avg = df.groupby(['Vehicle Type']).mean(numeric_only=True).reset_index()
    df_avg = df_avg[['Vehicle Type', 'share_of_fast_charger_capacity', 'share_of_slow_charger_capacity']]
    df_avg = df_avg.melt(id_vars=['Vehicle Type'], value_vars=['share_of_fast_charger_capacity', 'share_of_slow_charger_capacity'], var_name='Charger Type', value_name='Charger Utilisation (%)')
    df_avg['Charger Type'] = df_avg['Charger Type'].replace({'share_of_fast_charger_capacity':'Fast Chargers', 'share_of_slow_charger_capacity':'Slow Chargers'})

    title = 'Average utilisation of fast and slow public chargers by vehicle type (%)'
    fig = px.bar(df_avg, x='Vehicle Type', y='Charger Utilisation (%)', title=title, color='Charger Type')

    return fig, title

def plot_bar_of_average_utilisation_of_fast_and_slow_chargers_by_vehicle_type_and_drive(df, parameters):
    #sum up stocks and chargers by date
    df['Vehicle Type'] = df['Vehicle Type'].replace({'ht':'truck','mt':'truck','2w':'motorcycle & bus','bus':'motorcycle & bus','suv':'car','car':'car','lt':'car', 'lcv':'lcv'})

    #sum
    df = df.groupby(['Date', 'Vehicle Type', 'Drive']).sum().reset_index()
    #if there are any rows with 0 stocks, drop them
    df = df[df['Stocks_'+parameters['stocks_magnitude_name']] != 0]

    #calcaulte the average percent of total fast and slow charger capacity that each vehicle type uses and call it charger utilisation
    # df['sum_of_fast_kw_of_chargers'] = df.groupby(['Date'])['fast_kw_of_chargers'].transform('sum')
    # df['sum_of_slow_kw_of_chargers'] = df.groupby(['Date'])['slow_kw_of_chargers'].transform('sum')
    df['sum_of_kw_of_chargers'] = df.groupby(['Date'])['kw_of_chargers'].transform('sum')

    df['fast_charger_share_of_total_capacity'] = df['fast_kw_of_chargers']/df['sum_of_kw_of_chargers'] * 100
    df['slow_charger_share_of_total_capacity'] = df['slow_kw_of_chargers']/df['sum_of_kw_of_chargers'] * 100
    # df['share_of_fast_charger_capacity'] = df['fast_kw_of_chargers']/df['sum_of_fast_kw_of_chargers'] * 100
    # df['share_of_slow_charger_capacity'] = df['slow_kw_of_chargers']/df['sum_of_slow_kw_of_chargers'] * 100

    #calc average share per vehicle type
    # df_avg = df.groupby(['Vehicle Type', 'Drive']).mean(numeric_only=True).reset_index()
    # df_avg = df_avg[['Vehicle Type', 'Drive', 'share_of_fast_charger_capacity', 'share_of_slow_charger_capacity']]
    df_avg = df.groupby(['Vehicle Type', 'Drive']).mean(numeric_only=True).reset_index()
    df_avg = df_avg[['Vehicle Type', 'Drive', 'fast_charger_share_of_total_capacity', 'slow_charger_share_of_total_capacity']]

    # df_avg = df_avg.melt(id_vars=['Vehicle Type', 'Drive'], value_vars=['share_of_fast_charger_capacity', 'share_of_slow_charger_capacity'], var_name='Charger Type', value_name='Charger Utilisation (%)')
    df_avg = df_avg.melt(id_vars=['Vehicle Type', 'Drive'], value_vars=['fast_charger_share_of_total_capacity', 'slow_charger_share_of_total_capacity'], var_name='Charger Type', value_name='Charger Utilisation (%)')
    df_avg['Charger Type'] = df_avg['Charger Type'].replace({'fast_charger_share_of_total_capacity':'Fast Chargers', 'slow_charger_share_of_total_capacity':'Slow Chargers'})
    # df_avg['Charger Type'] = df_avg['Charger Type'].replace({'share_of_fast_charger_capacity':'Fast Chargers', 'share_of_slow_charger_capacity':'Slow Chargers'})
    
    title = 'Average utilisation of total charger capacity (%)'
    fig = px.bar(df_avg, x='Vehicle Type', y='Charger Utilisation (%)', title=title, color='Charger Type', pattern_shape='Drive', barmode='stack')

    return fig, title

def plot_stocks_by_vehicle_type_drive(df, parameters):
    #simplfiy stocks a little by grouping ht amnd mt together as well as 2w and bus, and suv, car and lt
    df['Vehicle Type'] = df['Vehicle Type'].replace({'ht':'truck','mt':'truck','2w':'motorcycle & bus','bus':'motorcycle & bus','suv':'car','car':'car','lt':'car', 'lcv':'lcv'})
    #sum up stocks and chargers by date and drive type
    df_summed = df.groupby(['Date', 'Vehicle Type', 'Drive']).sum().reset_index()
    a = parameters['stocks_magnitude_name']
    title = f'Stocks ({a}) by vehicle type and drive'
    fig = px.line(df_summed, x='Date', y=['Stocks_'+parameters['stocks_magnitude_name']], title=title, color='Vehicle Type', line_dash='Drive')
    return fig, title

def plot_average_kwh_of_battery_capacity_by_vehicle_type(df_filtered, parameters):
    #use the data in parameters to get this

    temp = pd.DataFrame({'Vehicle Type':parameters['average_kwh_of_battery_capacity_by_vehicle_type'].keys(), 'Average Kwh of Battery Capacity':parameters['average_kwh_of_battery_capacity_by_vehicle_type'].values()})
    #where the vehicle type ends in 'phev' make the drive type phev and drop the phev from the vehicle type
    temp['Drive'] = temp['Vehicle Type'].apply(lambda x: 'PHEV' if x.endswith('phev') else 'BEV')
    temp['Vehicle Type'] = temp['Vehicle Type'].apply(lambda x: x.replace('_phev','').replace('_bev',''))

    title = 'Average kwh of battery capacity by vehicle type'
    fig = px.bar(temp, x='Vehicle Type', y='Average Kwh of Battery Capacity', title=title, color='Drive', barmode='group')
    return fig, title

def plot_charging_dashboard(config, ECONOMY_ID, COMPARE_TO_IEA=True):

    dummy_df, parameters, colors_dict, INCORPORATE_UTILISATION_RATE = estimate_charging_requirements.prepare_inputs_for_estimating_charging_requirements(config, ECONOMY_ID)

    df = pd.read_csv(os.path.join(config.root_dir, f'output_data', 'for_other_modellers', 'charging', f'{ECONOMY_ID}_estimated_number_of_chargers.csv'))
    
    if COMPARE_TO_IEA:
        #load in IEA charging stats from their latest WEO outlook dataset, which was processed in transport datasystem: ../transport_data_system\intermediate_data\IEA/DATE20240604_evs.csv where DATEYYYYMMDD is the date the data was processed and we'll find the latest date available:
        
        date_id = utility_functions.get_latest_date_for_data_file( os.path.abspath(os.path.join(config.root_dir, '..', 'transport_data_system',  'input_data', 'IEA','processed')), 'DATE', file_name_end='_evs_cleaned_all_regions.csv')
        iea_df_path = os.path.abspath(os.path.join(config.root_dir, '..', 'transport_data_system', 'input_data', 'IEA','processed', f'DATE{date_id}_evs_cleaned_all_regions.csv'))
        iea_df = pd.read_csv(iea_df_path)
        #check economy is in there, otehrwse compare to the WORLD region
        if ECONOMY_ID not in iea_df['economy'].unique():
            ECONOMY_ID = 'World'
        iea_df = iea_df[iea_df['economy'] == ECONOMY_ID]        
    else:
        iea_df = None
    
    for scenario in df['Scenario'].unique():
        df_filtered = df[(df['Economy'] == ECONOMY_ID) & (df['Scenario'] == scenario)]

        fig_avg_kw_per_charger, title_avg_kw_per_charger =plot_kw_per_fast_charger_kw_per_slow_charger(df_filtered)
    
        fig_ratio_of_chargers_to_stocks, fig_ratio_of_kw_of_chargers_to_stocks, title_ratio_of_chargers_to_stocks, title_ratio_of_kw_of_chargers_to_stocks = plot_ratios(df_filtered, iea_df)
                    
        #now plot number of fast and slow cahrgers
        fast_and_slow_lines, fast_and_slow_title = plot_fast_and_slow_chargers(df_filtered, iea_df)

        fig_stocks_by_vehicle_type_drive, title_stocks_by_vehicle_type_drive = plot_stocks_by_vehicle_type_drive(df_filtered, parameters)

        fig_average_chargers_by_vehicle_type, title_average_chargers_by_vehicle_type = plot_bar_of_average_kw_of_fast_and_slow_chargers_per_vehicle_by_vehicle_type(df_filtered)

        fig_avg_kwh_per_vehicle, title_avg_kw_per_vehicle = plot_average_kwh_of_battery_capacity_by_vehicle_type(df_filtered, parameters)

        fig_utilisation_of_fast_and_slow_chargers_by_vehicle_type, title_utilisation_of_fast_and_slow_chargers_by_vehicle_type = plot_bar_of_average_utilisation_of_fast_and_slow_chargers_by_vehicle_type(df_filtered)
        fig_utilisation_of_fast_and_slow_chargers_by_vehicle_type_and_drive, title_utilisation_of_fast_and_slow_chargers_by_vehicle_type_and_drive = plot_bar_of_average_utilisation_of_fast_and_slow_chargers_by_vehicle_type_and_drive(df_filtered,parameters)

        #put all figs in a list
        figs = [fig_avg_kw_per_charger, fig_avg_kwh_per_vehicle, fig_ratio_of_chargers_to_stocks, fast_and_slow_lines, fig_utilisation_of_fast_and_slow_chargers_by_vehicle_type_and_drive, fig_stocks_by_vehicle_type_drive]

        subplot_titles = [title_avg_kw_per_charger, title_avg_kw_per_vehicle, title_ratio_of_chargers_to_stocks, fast_and_slow_title, title_utilisation_of_fast_and_slow_chargers_by_vehicle_type_and_drive, title_stocks_by_vehicle_type_drive]

        create_dashboard(config, figs,subplot_titles, ECONOMY_ID, scenario)


def create_dashboard(config, figs,subplot_titles, economy, scenario):

    #Note that we use the legend from the avg gen by timeslice graph because it contains all the categories used in the other graphs. If we showed the legend for other graphs we would get double ups
    #find the length of figs and create a value for rows and cols that are as close to a square as possible
    rows = int(np.ceil(np.sqrt(len(figs))))
    cols = int(np.ceil(len(figs)/rows))

    fig = make_subplots(
        rows=rows, cols=cols,
        #specs types will all be xy
        specs=[[{"type": "xy"} for col in range(cols)] for row in range(rows)],
        subplot_titles=subplot_titles
    )

    #now add traces to the fig iteratively, using the row and col values to determine where to add the trace
    for i, fig_i in enumerate(figs):
        #get the row and col values
        row = int(i/cols)+1
        col = i%cols+1

        #add the traceas for entire fig_i to the fig. This is because we are suing plotly express which returns a fig with multiple traces, however, plotly subplots only accepts one trace per subplot
        for trace in fig_i['data']:
            fig.add_trace(trace, row=row, col=col)

    #this is a great function to remove duplicate legend items
    names = set()
    fig.for_each_trace(
        lambda trace:
            trace.update(showlegend=False)
            if (trace.name in names) else names.add(trace.name))

    # use_bar_charts = False
    # if use_bar_charts:
    #     # if fig_i['layout']['barmode'] == 'stack':
    #     #make sure the barmode is stack for all graphs where it is in the layout
    #     #PLEASE NOTE THAT I COULDNT FIND A WAY TO SELECT TRACES THAT WERE APPLICABLE OTHER THAN FOR TYPE=BAR. (ROW AND COL ARENT IN THE TRACES). sO IF YOU NEED NON STACKED BARS IN THIS DASHBOARD YOU WILL HAVE TO CHANGE THIS SOMEHOW
    #     fig.update_traces(offset=0 ,selector = dict(type='bar'))#for some reasonteh legends for the bar charts are beoing wierd and all being the same color
    #     #showlegend=False

    #create title which is the folder where you can find the dashboard (base_folder)
    fig.update_layout(title_text=f"EV Charging Dashboard for {economy} in {scenario}")
    #save as html
    fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'charging_requirements', f'charging_dashboard_{economy}_{scenario}.html'), auto_open=False)

#%%