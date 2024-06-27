# %%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
# Construct the first path to check
root_dir = re.split('transport_model_9th_edition', os.getcwd())[0] + '\\transport_model_9th_edition'
# Check if the first path is not already in sys.path, then append it
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Construct the second path to check (relative to the current working directory)
path_to_add_2 = os.path.abspath(f"{root_dir}/config")
# Check if the second path is not already in sys.path, then append it
if path_to_add_2 not in sys.path:
    sys.path.append(path_to_add_2)
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
import growth_parameter_creation_functions

sys.path.append(f"{root_dir}/workflow/utility_functions")
import utility_functions
##########################
#%%
#grab the file D:\APERC\transport_model_9th_edition\input_data\macro\APEC_GDP_population.csv
#find latest file in input_data/macro/ that starts with APEC_GDP_data_ using the FILE_DATE_ID:
date_id = utility_functions.get_latest_date_for_data_file('input_data/macro/', 'APEC_GDP_data_')
macro = pd.read_csv(f'input_data/macro/APEC_GDP_data_{date_id}.csv')
#pull in activity_growth from 8th edition
activity_8th = pd.read_csv('input_data/from_8th/reformatted/8th_activity_efficiency_energy_road_stocks_sales_share.csv')
# macro.columns#Index(['economy_code', 'economy', 'date', 'variable', 'value'], dtype='object')
#find latest date for our energy data that was cleaned in transpoirt data system:
date_id = utility_functions.get_latest_date_for_data_file('../transport_data_system/intermediate_data/EGEDA/', 'EGEDA_transport_output')
energy_use = pd.read_csv(f'../transport_data_system/intermediate_data/EGEDA/EGEDA_transport_outputDATE{date_id}.csv')

activity_9th = pd.read_csv('intermediate_data/model_inputs/transport_data_system_extract.csv')

independent_variables = ['Gdp_per_capita_growth', 'Gdp_times_capita_growth', 'Gdp_growth', 'Population_growth']#, 'Population_growth_2', 'Population_growth_3']
#add lagged and leaded variables:
independent_variables = independent_variables + ['Population_growth_lag1', 'Population_growth_lead1','Gdp_per_capita_growth_lag1', 'Gdp_per_capita_growth_lead1', 'Gdp_times_capita_growth_lag1', 'Gdp_times_capita_growth_lead1', 'Gdp_growth_lag1', 'Gdp_growth_lead1']#, 'Population_growth_lag2', 'Population_growth_lead2', 'Population_growth_2_lag2', 'Population_growth_2_lead2']# + ['Gdp_per_capita_growth_lag3', 'Gdp_per_capita_growth_lead3', 'Gdp_times_capita_growth_lag3', 'Gdp_times_capita_growth_lead3', 'Gdp_growth_lag3', 'Gdp_growth_lead3', 'Population_growth_lag3', 'Population_growth_lead3', 'Population_growth2_lag3', 'Population_growth2_lead3'] + ['Gdp_per_capita_growth_lag4', 'Gdp_per_capita_growth_lead4', 'Gdp_times_capita_growth_lag4', 'Gdp_times_capita_growth_lead4', 'Gdp_growth_lag4', 'Gdp_growth_lead4', 'Population_growth_lag4', 'Population_growth_lead4', 'Population_growth2_lag4', 'Population_growth2_lead4'] + ['Gdp_per_capita_growth_lag5', 'Gdp_per_capita_growth_lead5', 'Gdp_times_capita_growth_lag5', 'Gdp_times_capita_growth_lead5', 'Gdp_growth_lag5', 'Gdp_growth_lead5', 'Population_growth_lag5', 'Population_growth_lead5', 'Population_growth2_lag5', 'Population_growth2_lead5']
dependent_variable = 'energy_total_growth'
models=['linear', 'lasso', 'ridge']
GROWTH_MEASURES_TO_PLOT=['freight_activity_growth_8th',	'passenger_activity_growth_8th', 'activity_growth_estimate_linear',	'activity_growth_estimate_lasso','activity_growth_estimate_ridge']

ACTIVITY_MEASURES_TO_PLOT = [
    "freight_activity_8th_linear",
    "passenger_activity_8th_linear",
    "freight_activity_9th_linear",
    "passenger_activity_9th_linear",
    "freight_activity_8th_lasso",
    "passenger_activity_8th_lasso",
    "freight_activity_9th_lasso",
    "passenger_activity_9th_lasso",
    "freight_activity_8th_ridge",
    "passenger_activity_8th_ridge",
    "freight_activity_9th_ridge",
    "passenger_activity_9th_ridge",
    "freight_activity_8th",
    "passenger_activity_8th"
]
#%%
    
def calculate_and_analyse_activity_growth_using_new_growth_coefficients(growth_coefficients_df, energy_macro, activity_9th, activity_8th,independent_variables, models, GROWTH_MEASURES_TO_PLOT, ACTIVITY_MEASURES_TO_PLOT):
    # breakpoint()
    activity_growth_8th, activity_8th = growth_parameter_creation_functions.format_8th_edition_data(activity_8th)
    
    BASE_YEAR_activity_9th = growth_parameter_creation_functions.import_BASE_YEAR_activity_9th(activity_9th)
    
    df, measures_to_plot,indexed_measures_to_plot = growth_parameter_creation_functions.prepare_comparison_inputs(growth_coefficients_df, energy_macro, BASE_YEAR_activity_9th, activity_growth_8th, activity_8th,independent_variables,models)
    
    #####################
    # PLOTTING
    #####################
    #save results to pickle so we can plot them when we want:
    df.to_pickle('intermediate_data/growth_analysis/df_growth_parameter_analysis.pkl')
    
    with open('intermediate_data/growth_analysis/measures_to_plot.txt', 'w') as f:
        for item in measures_to_plot:
            f.write("%s\n" % item)
    with open('intermediate_data/growth_analysis/indexed_measures_to_plot.txt', 'w') as f:
        for item in indexed_measures_to_plot:
            f.write("%s\n" % item)

    growth_parameter_creation_functions.plot_and_compare_new_growth_coefficients(GROWTH_MEASURES_TO_PLOT, ACTIVITY_MEASURES_TO_PLOT)
    
    
def create_growth_parameters(macro, energy_use, independent_variables):
    macro = growth_parameter_creation_functions.macro_formatting(macro)
    energy_use = growth_parameter_creation_functions.APERC_energy_formatting(energy_use)

    energy_macro = growth_parameter_creation_functions.merge_macro_and_energy(macro, energy_use)
    energy_macro = growth_parameter_creation_functions.caculate_growth_rates(energy_macro)
    energy_macro = growth_parameter_creation_functions.group_by_region(energy_macro, region_column='Region_growth_regression2')
    
    #drop 00_apec from the data. Maybe later i can try incroporating it across all regions
    energy_macro = energy_macro[energy_macro['Economy']!='00_APEC']
    
    energy_macro = create_duplicate_columns(energy_macro, independent_variables)

    energy_macro = create_lag_and_lead_handler(energy_macro, independent_variables)
    #breakpoint()
    energy_macro = energy_macro[['Economy','Region', 'Date', 'Total_growth','road_growth', 'Total','road', 'Gdp', 'Population', 'Gdp_per_capita', 'Gdp_times_capita']+independent_variables]
    
    energy_macro.rename(columns={'Total': 'energy_total', 'road': 'energy_road',  'Total_growth': 'energy_total_growth', 'road_growth': 'energy_road_growth'}, inplace=True)        
    return energy_macro

def create_duplicate_columns(df, independent_variables):
    duplicates = [col for col in independent_variables if re.search(r'_\d*$', col)]
    for duplicate in duplicates:
        original_col = re.sub(r'_\d*$', '', duplicate)
        df[duplicate] = df[original_col].copy()
    return df

def create_lag_and_lead_handler(df, independent_variables):
    lag_cols = [col for col in independent_variables if re.search(r'_lag\d*$', col)]
    lead_cols = [col for col in independent_variables if re.search(r'_lead\d*$', col)]
    
    def create_lag(df, col, original_col):
        num = re.search(r'\d+$', col).group()
        df[col] = df[original_col].shift(int(num)).copy()
        return df
    
    def create_lead(df, col, original_col):
        num = re.search(r'\d+$', col).group()
        df[col] = df[original_col].shift(-int(num)).copy()
        return df
    
    for col in lag_cols:
        original_col = re.sub(r'_lag\d*$', '', col)
        df = create_lag(df, col, original_col)
    for col in lead_cols:
        original_col = re.sub(r'_lead\d*$', '', col)
        df = create_lead(df, col, original_col)
    
    return df

def growth_analysis_handler(independent_variables, dependent_variable, macro, energy_use, activity_8th, activity_9th, models, GROWTH_MEASURES_TO_PLOT, ACTIVITY_MEASURES_TO_PLOT):
    # breakpoint()
    energy_macro = create_growth_parameters(macro, energy_use,independent_variables)
    df = energy_macro.copy()
    
    # growth_coefficients_df = model_handler(df, x, y,independent_variables, drop_outliers=False)
    growth_coefficients_df = growth_parameter_creation_functions.find_growth_coefficients(df, independent_variables,dependent_variable,models)
    
    growth_coefficients_df.to_csv(f'intermediate_data/growth_analysis/growth_coefficients_by_region{config.FILE_DATE_ID}.csv', index=False)
    #ANALYSIS
    growth_parameter_creation_functions.plot_growth_coefficients(growth_coefficients_df, independent_variables)
    
    #attach economy col to growth_coefficients_df:
    growth_coefficients_df = pd.merge(growth_coefficients_df, df[['Economy', 'Region']].drop_duplicates(), on='Region', how='left')
    #drop region col
    growth_coefficients_df.drop(columns=['Region'], inplace=True)
    
    #COMPARE THE GROWTH COEFFICIENTS TO FIND THE BEST ONE:
    calculate_and_analyse_activity_growth_using_new_growth_coefficients(growth_coefficients_df, energy_macro, activity_9th, activity_8th,independent_variables,models, GROWTH_MEASURES_TO_PLOT, ACTIVITY_MEASURES_TO_PLOT)
    
def filter_coefficients_for_chosen_model(growth_coefficients_df, models):
    # breakpoint()
    growth_coefficients_df = growth_coefficients_df[growth_coefficients_df['model'].isin(models)]
    return growth_coefficients_df

#%%

def choose_and_filter_for_model_by_region(chosen_model_by_region_dict, chosen_file_date_id=None,region_column = 'Region_growth_regression2'):
    #find latest date for this file: 
    # csv(f'intermediate_data/growth_analysis/growth_coefficients_by_region{config.FILE_DATE_ID}.csv', index=False)
    if chosen_file_date_id is not None:
        date_id = chosen_file_date_id
    else:
        
        date_id = utility_functions.get_latest_date_for_data_file('intermediate_data/growth_analysis/','growth_coefficients_by_region')
        
    growth_coefficients_df = pd.read_csv(f'intermediate_data/growth_analysis/growth_coefficients_by_region{date_id}.csv')
    #now filter out the data we dont want by choosing the model we wwant for each region
    new_df = pd.DataFrame()
    for region, model in chosen_model_by_region_dict.items():
        df_dummy = growth_coefficients_df[(growth_coefficients_df['Region']==region)&(growth_coefficients_df['Model']==model)]
        new_df = pd.concat([new_df, df_dummy])
    
    regional_mapping = pd.read_csv('config/concordances_and_config_data/region_economy_mapping.csv')
    #extract Region_growth_regression and Economy
    regional_mapping = regional_mapping[[region_column, 'Economy']]
    #make economyt lowercase
    regional_mapping.rename(columns={region_column:'Region'}, inplace=True)
    
    #join to regional mapping
    df = pd.merge(new_df, regional_mapping, on='Region', how='inner')
    
    #if input_data/growth_coefficients_by_region.csv already exists, save  it to a new file input_data/previous_growth_coefficients/ with the date_id on it
    if os.path.isfile(f'input_data/growth_coefficients_by_region.csv'):
        #save to previous_growth_coefficients
        df.to_csv(f'input_data/previous_growth_coefficients/growth_coefficients_by_region{date_id}.csv', index=False)
    
    #now save to same location as before
    df.to_csv('input_data/growth_coefficients_by_region.csv', index=False)
    
    
        
#%%

growth_analysis_handler(independent_variables, dependent_variable, macro, energy_use, activity_8th, activity_9th, models, GROWTH_MEASURES_TO_PLOT, ACTIVITY_MEASURES_TO_PLOT)
#%%
chosen=True
if chosen:
    # Low_density
    # City
    # Developing_high_density
    # Developed_high_density
    chosen_model_by_region_dict ={'Low_density':'lasso', 'City':'lasso', 'Developing_high_density':'lasso', 'Developed_high_density':'lasso'}

    choose_and_filter_for_model_by_region(chosen_model_by_region_dict,region_column = 'Region_growth_regression2')
        
    
#%%

