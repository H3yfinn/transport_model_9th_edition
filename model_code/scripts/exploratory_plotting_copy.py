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
#%%
# Function to calculate emissions from energy columns
def calculate_emissions_from_energy_col(emissions_factors, model_output_with_fuels, USE_AVG_GENERATION_EMISSIONS_FACTOR=False):
    emissions_factors = emissions_factors.rename(columns={'fuel_code': 'Fuel'})
    model_output_with_fuels = model_output_with_fuels.merge(emissions_factors, how='left', on='Fuel')

    if USE_AVG_GENERATION_EMISSIONS_FACTOR:
        emissions_factor_elec = pd.read_csv(root_dir + '\\' + 'input_data\\from_8th\\outlook_8th_emissions_factors_with_electricity.csv')
        emissions_factor_elec = emissions_factor_elec[emissions_factor_elec.fuel_code == '17_electricity'].copy()
        emissions_factor_elec['Scenario'] = emissions_factor_elec['Scenario'].replace('Carbon Neutral', 'Target')
        emissions_factor_elec.columns = [x.capitalize() for x in emissions_factor_elec.columns]
        emissions_factor_elec = emissions_factor_elec.rename(columns={'Fuel_code': 'Fuel', 'Year': 'Date', 'Emissions factor (mt/pj)': 'Emissions factor (MT/PJ)'})
        model_output_with_fuels = model_output_with_fuels.merge(emissions_factor_elec, on=['Date', 'Economy', 'Scenario', 'Fuel'], how='left', indicator=True, suffixes=('', '_elec'))
        model_output_with_fuels['Emissions factor (MT/PJ)'] = np.where(model_output_with_fuels['_merge'] == 'both', model_output_with_fuels['Emissions factor (MT/PJ)_elec'], model_output_with_fuels['Emissions factor (MT/PJ)'])
        model_output_with_fuels['Emissions factor (MT/PJ)'] = model_output_with_fuels.sort_values(by='Date').groupby(['Economy', 'Scenario', 'Date', 'Transport Type', 'Fuel'])['Emissions factor (MT/PJ)'].fillna(method='ffill')
        model_output_with_fuels = model_output_with_fuels.drop(columns=['Emissions factor (MT/PJ)_elec', '_merge'])

    missing_emissions_factors = model_output_with_fuels.loc[model_output_with_fuels['Emissions factor (MT/PJ)'].isna()].copy()
    if len(missing_emissions_factors) > 0:
        raise ValueError(f'Missing emissions factors, {missing_emissions_factors.Fuel.unique()}')

    model_output_with_fuels['Emissions'] = model_output_with_fuels['Energy'] * model_output_with_fuels['Emissions factor (MT/PJ)']
    model_output_with_fuels['Measure'] = 'Emissions'
    model_output_with_fuels['Unit'] = 'Mt CO2'

    return model_output_with_fuels

# Function to compare values between projections using two files
def compare_values_between_projections_using_two_files(projection_filename1, projection_filename2, measure, title, filter_dict, grouping, graph_type, save_folder, emissions_factors=None, font_size=24):
    if projection_filename1.endswith('.csv'):
        df1 = pd.read_csv(projection_filename1)
        df2 = pd.read_csv(projection_filename2)
    else:
        df1 = pd.read_excel(projection_filename1)
        df2 = pd.read_excel(projection_filename2)

    for column, values in filter_dict.items():
        df1 = df1[df1[column].isin(values)]
        df2 = df2[df2[column].isin(values)]

    grouping_no_date = [x for x in grouping if x != 'Date']

    if 'emissions' in measure.lower():
        df1 = calculate_emissions_from_energy_col(emissions_factors, df1, USE_AVG_GENERATION_EMISSIONS_FACTOR=False)
        df2 = calculate_emissions_from_energy_col(emissions_factors, df2, USE_AVG_GENERATION_EMISSIONS_FACTOR=False)

    if measure == 'cumulative_emissions':
        df1 = df1.groupby(grouping)['Emissions'].sum().reset_index()
        df2 = df2.groupby(grouping)['Emissions'].sum().reset_index()
        df1[measure] = df1.groupby(grouping_no_date)['Emissions'].transform(pd.Series.cumsum)
        df2[measure] = df2.groupby(grouping_no_date)['Emissions'].transform(pd.Series.cumsum)
        y_axis_primary = 'Cumulative Emissions (Mt CO2)'
    else:
        df1 = df1.groupby(grouping)[measure].sum().reset_index()
        df2 = df2.groupby(grouping)[measure].sum().reset_index()
        y_axis_primary = f"{measure} (Mt CO2)" if measure == 'Emissions' else f"{measure} (PJ)" if measure == 'Energy' else measure

    color_col_name = '_'.join(grouping_no_date)
    difference = pd.merge(df1, df2, on=grouping, suffixes=('_1', '_2'))
    difference[measure] = difference[f"{measure}_1"] - difference[f"{measure}_2"]
    difference[color_col_name] = difference[grouping_no_date].apply(lambda x: '_'.join(x), axis=1)
    df1[color_col_name] = df1[grouping_no_date].apply(lambda x: '_'.join(x), axis=1)
    df2[color_col_name] = df2[grouping_no_date].apply(lambda x: '_'.join(x), axis=1)
    difference = difference[difference[measure] != 0]
    df1 = df1[df1[measure] != 0]
    df2 = df2[df2[measure] != 0]

    if graph_type == 'timeseries_proportion':
        difference_percent = difference.groupby('Date')[measure].sum().reset_index().copy()
        df1_percent = df1.groupby('Date')[measure].sum().reset_index().copy()
        difference_percent[f"{measure}_percent"] = 100 * (difference_percent[measure] / df1_percent[measure])

        fig3 = make_subplots(specs=[[{"secondary_y": True}]])
        fig3.add_trace(go.Scatter(x=difference_percent['Date'], y=difference_percent[f"{measure}_percent"], mode='lines', name=f'Difference in {measure} (%)', line=dict(width=6)), secondary_y=True)
        
        for color in difference[color_col_name].unique():
            fig3.add_trace(go.Scatter(x=difference[difference[color_col_name] == color]['Date'], y=difference[difference[color_col_name] == color][measure], fill='tozeroy', name=color), secondary_y=False)
        
        fig3.update_layout(
            title={'text': title, 'y': 0.9, 'x': 0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': dict(size=font_size)},
            legend=dict(title=dict(text='', font=dict(size=font_size)), font=dict(size=font_size))
        )
        
        fig3.update_yaxes(title_text=y_axis_primary, secondary_y=False)
        fig3.update_yaxes(title_text='(%)', secondary_y=True)
        fig3.update_xaxes(title_font=dict(size=font_size))
        fig3.update_yaxes(title_font=dict(size=font_size))
        fig3.update_xaxes(tickfont=dict(size=font_size))
        fig3.update_yaxes(tickfont=dict(size=font_size - font_size * 0.2), secondary_y=False)
        fig3.update_yaxes(tickfont=dict(size=font_size - font_size * 0.2), secondary_y=True)

        figs = {'difference_percent': fig3}

    else:
        raise ValueError('Graph type not recognised')

    for name, fig in figs.items():
        fig.write_html(root_dir + '\\' +f'{save_folder}\\{title}_{name}.html')

    return
#%%
# Example usage
emissions_factors = pd.read_csv(root_dir + '\\' + 'config\\9th_edition_emissions_factors.csv')
filter_dict = {'Scenario': ['Reference'], 'Economy': ['03_CDA'], 'Transport Type': ['passenger'], 'Medium': ['road']}
compare_values_between_projections_using_two_files(
    'plotting_output\\experimental\\Nanjing_comparisons\\03_CDA_model_output20240327.csv',
    'plotting_output\\experimental\\Nanjing_comparisons\\03_CDA_model_output20240327_HEV.csv',
    measure='cumulative_emissions',
    title='Canada cumulative emissions comparison (REF)',
    filter_dict=filter_dict,
    grouping=['Date', 'Fuel'],
    graph_type='timeseries_proportion',
    save_folder='plotting_output\\experimental\\Nanjing_comparisons',
    emissions_factors=emissions_factors,
    font_size=24
)
#%%
filter_dict = {'Scenario': ['Target'], 'Economy': ['03_CDA'], 'Medium': ['road'], 'Transport Type': ['passenger']}
compare_values_between_projections_using_two_files(
    'plotting_output\\experimental\\Nanjing_comparisons\\03_CDA_model_output20240327.csv',
    'plotting_output\\experimental\\Nanjing_comparisons\\03_CDA_model_output20240327_HEV.csv',
    measure='cumulative_emissions',
    title='Canada cumulative emissions comparison (TGT)',
    filter_dict=filter_dict,
    grouping=['Date', 'Fuel'],
    graph_type='timeseries_proportion',
    save_folder='plotting_output\\experimental\\Nanjing_comparisons',
    emissions_factors=emissions_factors,
    font_size=24
)

filter_dict = {'Scenario': ['Reference'], 'Economy': ['03_CDA'], 'Transport Type': ['passenger'], 'Medium': ['road']}
compare_values_between_projections_using_two_files(
    'plotting_output\\experimental\\Nanjing_comparisons\\03_CDA_model_output20240327.csv',
    'plotting_output\\experimental\\Nanjing_comparisons\\03_CDA_model_output20240327_HEV.csv',
    measure='Emissions',
    title='Canada emissions comparison (REF)',
    filter_dict=filter_dict,
    grouping=['Date', 'Fuel'],
    graph_type='timeseries_proportion',
    save_folder='plotting_output\\experimental\\Nanjing_comparisons',
    emissions_factors=emissions_factors,
    font_size=24
)

filter_dict = {'Scenario': ['Target'], 'Economy': ['03_CDA'], 'Medium': ['road'], 'Transport Type': ['passenger']}
compare_values_between_projections_using_two_files(
    'plotting_output\\experimental\\Nanjing_comparisons\\03_CDA_model_output20240327.csv',
    'plotting_output\\experimental\\Nanjing_comparisons\\03_CDA_model_output20240327_HEV.csv',
    measure='Emissions',
    title='Canada emissions comparison (TGT)',
    filter_dict=filter_dict,
    grouping=['Date', 'Fuel'],
    graph_type='timeseries_proportion',
    save_folder='plotting_output\\experimental\\Nanjing_comparisons',
    emissions_factors=emissions_factors,
    font_size=24
)
#%%