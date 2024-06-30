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
from ..calculation_functions import road_model_functions
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

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

#USE THIS FILE TO DO PLOTS THAT MAY ONLY BE USED ONCE OR HAVE PROCESSES THAT DONT REALLY FIT INTO THE SYSTEM FLOW OF THE MODEL.

# def compare_values_between_projections_using_two_files(projection_filename1, projection_filename2, measure, title, filter_dict, grouping, graph_type, save_folder):
#     #this was first created to analyse difference in passenger energy use and cumulative emissions when using high hevs vs not. this just takes two files and will filter for the set of columns and items to filter for in filter_dict.(e.g. transport_types, mediums, drives, economies, fuels, last_date) and sum all by grouping (except date) and then compare the measure. 
#     # if the measure is cumulative emissions this will calcualte those from emissions too.
#     #the final graph can be a timeseries or a waterfall based on the final year 
    
#     #load in data. we wont check the data is similar. if its not then it should be obvious via an error or weird graph
    
#     #filter for data by looping through the filterables:
#     for column, values in filter_dict:
#         #grab the data for the column and fitler for it.
    
#     #if the measure is 'cumulative_emissions' then sum by emissions and calcualte cumulative emissions using the grouping
#     #else sum by the grouping for the measure.
    
#     #proceed based on if the graph_type is waterfall or timeseries.
    
#     #if graph type is waterfall, comapre file1 vs file2 for final date using the difference as the 'waterflow?'
    
#     #if graph type is timeseries, first clacualte difference and then plot 3 graphs: plot both as a timeseries and then the difference as a timeseries.
    
#     #save all graphs in save_folder using the title as the name
    
#     return


def calculate_emissions_from_energy_col(emissions_factors,model_output_with_fuels, USE_AVG_GENERATION_EMISSIONS_FACTOR=False):
            
    #rename fuel_code to fuel in emissions_factors
    emissions_factors = emissions_factors.rename(columns={'fuel_code':'Fuel'})
    #join on the emissions factors (has the cols fuel_code,	Emissions factor (MT/PJ))
    model_output_with_fuels = model_output_with_fuels.merge(emissions_factors, how='left', on='Fuel')
    
    if USE_AVG_GENERATION_EMISSIONS_FACTOR:
        gen='_gen'
        #pull in the 8th outlook emissions factors by year, then use that to claculate the emissions for electricity.
        emissions_factor_elec = pd.read_csv(root_dir + '\\' + 'input_data\\from_8th\\outlook_8th_emissions_factors_with_electricity.csv')#c:\Users\finbar.maunsell\github\aperc-emissions\output_data\outlook_8th_emissions_factors_with_electricity.csv
        #extract the emissions factor for elctricity for each economy
        emissions_factor_elec = emissions_factor_elec[emissions_factor_elec.fuel_code=='17_electricity'].copy()
        #rename Carbon Neutral Scenario to Target
        emissions_factor_elec['Scenario'] = emissions_factor_elec['Scenario'].replace('Carbon Neutral', 'Target')
        #capitalise the cols
        emissions_factor_elec.columns = [x.capitalize() for x in emissions_factor_elec.columns]
        #rename fuel code to fuel
        emissions_factor_elec = emissions_factor_elec.rename(columns={'Fuel_code':'Fuel', 'Year':'Date', 'Emissions factor (mt/pj)':'Emissions factor (MT/PJ)'})
        #merge on economy and year and fuel code
        model_output_with_fuels = model_output_with_fuels.merge(emissions_factor_elec, on=['Date', 'Economy', 'Scenario', 'Fuel'], how='left', indicator=True, suffixes=('', '_elec'))
        #where indicator is both, use the new value
        model_output_with_fuels['Emissions factor (MT/PJ)'] = np.where(model_output_with_fuels['_merge']=='both', model_output_with_fuels['Emissions factor (MT/PJ)_elec'], model_output_with_fuels['Emissions factor (MT/PJ)'])
        #fill any missing values using ffill after sorting by date and grouping by 'Economy', 'Scenario','Date', 'Fuel', 'Transport Type'
        model_output_with_fuels['Emissions factor (MT/PJ)'] = model_output_with_fuels.sort_values(by='Date').groupby(['Economy', 'Scenario','Date','Transport Type', 'Fuel'])['Emissions factor (MT/PJ)'].fillna(method='ffill')
        #drop columns
        model_output_with_fuels = model_output_with_fuels.drop(columns=['Emissions factor (MT/PJ)_elec', '_merge'])
        
    #identify where there are no emissions factors:
    missing_emissions_factors = model_output_with_fuels.loc[model_output_with_fuels['Emissions factor (MT/PJ)'].isna()].copy()
    if len(missing_emissions_factors)>0:
        breakpoint()
        time.sleep(1)
        raise ValueError(f'missing emissions factors, {missing_emissions_factors.Fuel.unique()}')
    
    #calculate emissions:
    model_output_with_fuels['Emissions'] = model_output_with_fuels['Energy'] * model_output_with_fuels['Emissions factor (MT/PJ)']

    model_output_with_fuels['Measure'] = 'Emissions'
    model_output_with_fuels['Unit'] = 'Mt CO2'
    
    return model_output_with_fuels
    


import pandas as pd
import plotly.express as px
import plotly.io as pio

def compare_values_between_projections_using_two_files(projection_filename1, projection_filename2, measure, title, filter_dict, grouping, graph_type, save_folder, emissions_factors=None, font_size=24):
    # Load data
    if projection_filename1.endswith('.csv'):
        df1 = pd.read_csv(projection_filename1)
        df2 = pd.read_csv(projection_filename2)
    else:
        df1 = pd.read_excel(projection_filename1)
        df2 = pd.read_excel(projection_filename2)

    # Filter data
    for column, values in filter_dict.items():
        df1 = df1[df1[column].isin(values)]
        df2 = df2[df2[column].isin(values)]
    
    grouping_no_date = [x for x in grouping if x != 'Date']
    
    if 'emissions' in measure or 'Emissions' in measure:
        #we will have to calcualte emissions from the energy column
        df1 = calculate_emissions_from_energy_col(emissions_factors,df1, USE_AVG_GENERATION_EMISSIONS_FACTOR=False)
        df2 = calculate_emissions_from_energy_col(emissions_factors,df2, USE_AVG_GENERATION_EMISSIONS_FACTOR=False)
        
    # Calculate cumulative emissions if necessary
    if measure == 'cumulative_emissions':
        
        df1 = df1.groupby(grouping)['Emissions'].sum().reset_index()
        df2 = df2.groupby(grouping)['Emissions'].sum().reset_index()
        df1[measure] = df1.groupby(grouping_no_date)['Emissions'].transform(pd.Series.cumsum)
        df2[measure] = df2.groupby(grouping_no_date)['Emissions'].transform(pd.Series.cumsum)
        y_axis_primary ='Cumulative Emissions (Mt CO2)'
    else:
        df1 = df1.groupby(grouping)[measure].sum().reset_index()
        df2 = df2.groupby(grouping)[measure].sum().reset_index()
        if measure == 'Emissions':
            y_axis_primary = measure + ' (Mt CO2)'
        elif measure == 'Energy':
            y_axis_primary = measure + ' (PJ)'
        else:
            y_axis_primary = measure
    
    #if grouping contains fuel then change the fuel type to more readble names
    if 'Fuel' in grouping:
        df1 = df1.replace({'Fuel':{'07_01_motor_gasoline':'petrol', '17_electricity':'electricity', '07_07_gas_diesel_oil':'diesel'}})
        df2 = df2.replace({'Fuel':{'07_01_motor_gasoline':'petrol', '17_electricity':'electricity', '07_07_gas_diesel_oil':'diesel'}})
        
    difference = pd.merge(df1, df2, on=grouping, suffixes=('_1', '_2'))
    difference[measure] = difference[measure + '_1'] - difference[measure + '_2']
    
    #combine all the cols in grouping_no_date to make a new grouping col that we will base the color in graphs on
    color_col_name = '_'.join(grouping_no_date)
    difference[color_col_name] = difference[grouping_no_date].apply(lambda x: '_'.join(x), axis=1)
    df1[color_col_name] = df1[grouping_no_date].apply(lambda x: '_'.join(x), axis=1)
    df2[color_col_name] = df2[grouping_no_date].apply(lambda x: '_'.join(x), axis=1)
    
    difference = difference[difference[measure] != 0]
    df1 = df1[df1[measure] != 0]
    df2 = df2[df2[measure] != 0]
    # Proceed based on graph type
    if graph_type == 'waterfall':
        # Compare final date
        final_date = df1['Date'].max()
        difference = difference[difference['Date'] == final_date]
        fig = px.bar(difference, x='Date', color=color_col_name, y=measure, title=title)
        fig.update_layout(yaxis_title=y_axis_primary)
        figs = {'final_date': fig}
    elif graph_type == 'timeseries':
        # Calculate difference and plot
        
        fig1 = px.area(df1, x='Date', y=measure, color=color_col_name)
        fig2 = px.area(df2, x='Date', y=measure, color=color_col_name)
        fig3 = px.area(difference, x='Date', y=measure, color=color_col_name, title=title)
        fig.update_layout(yaxis_title=y_axis_primary)
        figs = {'df1': fig1, 'df2': fig2, 'difference': fig3}
        
    elif graph_type == 'timeseries_proportion':
        #convert the values to a proportion by finding the proportion of the differencve in emissions compare to the emissions for df1
        #however, since its a percentage dfifference we will also find the percent difference between sums of all emissions by date (ignoring the grouping) so that small values are not overemphasised.
        difference_percent = difference.groupby('Date')[measure].sum().reset_index().copy()
        df1_percent = df1.groupby('Date')[measure].sum().reset_index().copy()
        difference_percent[measure+'_percent'] = 100*(difference_percent[measure]/df1_percent[measure])
        
        # #join it to the difference df so we can plot a multi axis graph
        # difference = difference.merge(difference_percent, on='Date', suffixes=('', '_percent'))
        #(difference[measure]/df1[measure]) * 100
        # Calculate difference and plot
        
        fig1 = px.area(df1, x='Date', y=measure, color=color_col_name)
        fig2 = px.area(df2, x='Date', y=measure, color=color_col_name)
        # fig3 = px.line(difference_percent, x='Date', y=measure+'_percent')
        #fig3 will have two y axes, one with the difference in emissions as an area and the other with the percent difference in emissions as a line. 
        fig3 = make_subplots(specs=[[{"secondary_y": True}]])
        fig3.add_trace(go.Scatter(x=difference_percent['Date'], 
                          y=difference_percent[measure+'_percent'], 
                          mode='lines', 
                          name='Difference in {} (%)'.format(measure),
                          line=dict(width=6)),  # Set line width to 4
              secondary_y=True)
        for color in difference[color_col_name].unique():
            fig3.add_trace(go.Scatter(x=difference[difference[color_col_name]==color]['Date'], 
                                      y=difference[difference[color_col_name]==color][measure], 
                                      fill='tozeroy', 
                                      name=color), 
                           secondary_y=False)
        fig3.update_yaxes(showgrid=False)
        fig3.update_layout(
            title={
                'text': title,
                'y':0.9,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=font_size)},
            legend=dict(
                title=dict(
                    text='',
                    font=dict(
                        size=font_size,
                    )
                ),
                font=dict(
                    size=font_size,
                )
            )
        )
        
        fig3.update_yaxes(title_text=y_axis_primary, secondary_y=False)
        fig3.update_yaxes(title_text='(%)', secondary_y=True)
         
        fig3.update_xaxes(title_font=dict(size=font_size))  # Set x-axis title font size to font_size
        fig3.update_yaxes(title_font=dict(size=font_size))  # Set y-axis title font size to font_size
        fig3.update_xaxes(tickfont=dict(size=font_size))  # Set x-axis tick font size to font_size
        fig3.update_yaxes(tickfont=dict(size=font_size-font_size*0.2), secondary_y=False)  # Set y-axis tick font size to font_size
        fig3.update_yaxes(tickfont=dict(size=font_size-font_size*0.2), secondary_y=True)  # Set secondary y-axis tick font size to font_size
        figs = {'df1': fig1, 'df2': fig2, 'difference_percent': fig3}
        
    else:
        raise ValueError('Graph type not recognised')
    
    # Save figures
    for name, fig in figs.items():
        fig.write_html(root_dir + '\\' +f'{save_folder}\\{title}_{name}.html')

    #save data
    df1.to_csv(f'{save_folder}\\{title}_{name}_df1.csv', index=False)
    df2.to_csv(f'{save_folder}\\{title}_{name}_df2.csv', index=False)
    difference.to_csv(f'{save_folder}\\{title}_{name}_difference.csv', index=False)
    output_tuple = (df1, df2, difference)
    if graph_type == 'timeseries_proportion':
        difference_percent.to_csv(f'{save_folder}\\{title}_{name}_difference_percent.csv', index=False)
        output_tuple = (df1, df2, difference, difference_percent)
    return output_tuple


#%%
emissions_factors = pd.read_csv(root_dir + '\\' + 'config\\9th_edition_emissions_factors.csv')
filter_dict = {'Scenario':['Reference'], 'Economy':['03_CDA'], 'Transport Type': ['passenger'], 'Medium':['road']}
df1_ref_cum, df2_ref_cum, difference_ref_cum, difference_percent_ref_cum = compare_values_between_projections_using_two_files( root_dir + '\\' +'plotting_output\\experimental\\Nanjing_comparisons\\03_CDA_model_output20240327.csv','plotting_output\\experimental\\Nanjing_comparisons\\03_CDA_model_output20240327_HEV.csv', measure='cumulative_emissions', title='Canada cumulative emissions comparison (REF)', filter_dict=filter_dict, grouping=['Date', 'Fuel'], graph_type='timeseries_proportion', save_folder=root_dir + '\\' +'plotting_output\\experimental\\Nanjing_comparisons', emissions_factors=emissions_factors,font_size=24)

emissions_factors = pd.read_csv(root_dir + '\\' + 'config\\9th_edition_emissions_factors.csv')
filter_dict = {'Scenario':['Target'], 'Economy':['03_CDA'], 'Medium':['road'],'Transport Type': ['passenger']}
df1_tgt_cum, df2_tgt_cum, difference_tgt_cum, difference_percent_tgt_cum = compare_values_between_projections_using_two_files( root_dir + '\\' +'plotting_output\\experimental\\Nanjing_comparisons\\03_CDA_model_output20240327.csv','plotting_output\\experimental\\Nanjing_comparisons\\03_CDA_model_output20240327_HEV.csv', measure='cumulative_emissions', title='Canada cumulative emissions comparison (TGT)', filter_dict=filter_dict, grouping=['Date', 'Fuel'], graph_type='timeseries_proportion', save_folder=root_dir + '\\' +'plotting_output\\experimental\\Nanjing_comparisons', emissions_factors=emissions_factors,font_size=24)

#%%
emissions_factors = pd.read_csv(root_dir + '\\' + 'config\\9th_edition_emissions_factors.csv')
filter_dict = {'Scenario':['Reference'], 'Economy':['03_CDA'], 'Transport Type': ['passenger'], 'Medium':['road']}
df1_ref_abs, df2_ref_abs, difference_ref_abs, difference_percent_ref_abs = compare_values_between_projections_using_two_files(root_dir + '\\' + 'plotting_output\\experimental\\Nanjing_comparisons\\03_CDA_model_output20240327.csv','plotting_output\\experimental\\Nanjing_comparisons\\03_CDA_model_output20240327_HEV.csv', measure='Emissions', title='Canada emissions comparison (REF)', filter_dict=filter_dict, grouping=['Date', 'Fuel'], graph_type='timeseries_proportion', save_folder=root_dir + '\\' +'plotting_output\\experimental\\Nanjing_comparisons', emissions_factors=emissions_factors,font_size=24)

emissions_factors = pd.read_csv(root_dir + '\\' + 'config\\9th_edition_emissions_factors.csv')
filter_dict = {'Scenario':['Target'], 'Economy':['03_CDA'], 'Medium':['road'],'Transport Type': ['passenger']}
df1_tgt_abs, df2_tgt_abs, difference_tgt_abs, difference_percent_tgt_abs = compare_values_between_projections_using_two_files(root_dir + '\\' + 'plotting_output\\experimental\\Nanjing_comparisons\\03_CDA_model_output20240327.csv','plotting_output\\experimental\\Nanjing_comparisons\\03_CDA_model_output20240327_HEV.csv', measure='Emissions', title='Canada emissions comparison (TGT)', filter_dict=filter_dict, grouping=['Date', 'Fuel'], graph_type='timeseries_proportion', save_folder=root_dir + '\\' +'plotting_output\\experimental\\Nanjing_comparisons', emissions_factors=emissions_factors,font_size=24)

#%%

def plot_comparison_ref_vs_tgt(difference_percent_ref_filename, difference_percent_tgt_filename, measure, title, save_folder, font_size=24):
    """
    This function reads the saved difference_percent CSVs, and plots the percent difference
    in difference_tgt_abs against difference_ref_abs.

    :param difference_percent_ref_filename: str, filename of the reference scenario difference percent CSV
    :param difference_percent_tgt_filename: str, filename of the target scenario difference percent CSV
    :param measure: str, the measure column name in the CSVs
    :param title: str, title of the plot
    :param save_folder: str, folder where the plot will be saved
    :param font_size: int, font size for the plot labels
    """
    # Load the difference percent CSVs
    difference_percent_ref = pd.read_csv(difference_percent_ref_filename)
    difference_percent_tgt = pd.read_csv(difference_percent_tgt_filename)

    # Ensure the DataFrames are sorted by Date for consistency
    difference_percent_ref.sort_values(by='Date', inplace=True)
    difference_percent_tgt.sort_values(by='Date', inplace=True)

    # Create the plot
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=difference_percent_ref['Date'],
        y=difference_percent_ref[measure],
        line=dict(width=6, color='#43cbeb'),
        name='Reference'
    ))

    fig.add_trace(go.Scatter(
        x=difference_percent_tgt['Date'],
        y=difference_percent_tgt[measure],
        line=dict(width=6, color='#b3e344'),
        name='Target'
    ))

    # Add labels and title
    fig.update_layout(
        title=title,
        yaxis_title='Emissions Reduction (%)',
        template='plotly_white',
        title_font=dict(size=font_size),
        xaxis=dict(
            title_font=dict(size=font_size),
            tickfont=dict(size=font_size)),
        yaxis=dict(
            title_font=dict(size=font_size),
            tickfont=dict(size=font_size)),
        legend=dict(font=dict(size=font_size))
    )
    # Save the figure
    fig.write_html(root_dir + '\\' +f'{save_folder}\\{title}_Percentage_Difference_Comparison.html')

    # Display the plot
    fig.show()

# Example usage
plot_comparison_ref_vs_tgt(
    difference_percent_ref_filename=root_dir + '\\' +'plotting_output\\experimental\\Nanjing_comparisons\\Canada cumulative emissions comparison (REF)_difference_percent_difference_percent.csv',
    difference_percent_tgt_filename=root_dir + '\\' +'plotting_output\\experimental\\Nanjing_comparisons\\Canada cumulative emissions comparison (TGT)_difference_percent_difference_percent.csv',
    measure='cumulative_emissions_percent',
    title='Canada Cumulative Emissions Reductions Comparison',
    save_folder=root_dir + '\\' +'plotting_output\\experimental\\Nanjing_comparisons',
    font_size=24
)

plot_comparison_ref_vs_tgt(
    difference_percent_ref_filename=root_dir + '\\' + 'plotting_output\\experimental\\Nanjing_comparisons\\Canada emissions comparison (REF)_difference_percent_difference_percent.csv',
    difference_percent_tgt_filename=root_dir + '\\' + 'plotting_output\\experimental\\Nanjing_comparisons\\Canada emissions comparison (TGT)_difference_percent_difference_percent.csv',
    measure='Emissions_percent',
    title='Canada Emissions Reductions Comparison',
    save_folder=root_dir + '\\' +'plotting_output\\experimental\\Nanjing_comparisons',
    font_size=24
)

#%%