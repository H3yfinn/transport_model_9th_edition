#we will always have issues with esto energy not matching expected enrgy because of the way we calculate energy from stocks and activity. so create graphs to compare the two. Since ESTO energy is for only a few years that we have model data for, we should compare it suing something different ot a line graph i think.
#%%
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

# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook
import matplotlib.pyplot as plt
plt.rcParams['figure.facecolor'] = 'w'

def compare_esto_energy_to_data():
    #TODO, THIS NEEDS TO BE MADE TO WORK WITH THE OUTPUT FOR 9TH OUTLOOK, AS THAT IS THE MOST ACCURATE REPRESENTATION OF ESTO DATA WE NOW HAVE. AND IT SWOULD MAKE IT MRESUSTAIBNLE.
    #find latest date for our energy data that was cleaned in transpoirt data system:
    # date_id = utility_functions.get_latest_date_for_data_file(root_dir + '/' + '../transport_data_system/intermediate_data/EGEDA/', 'model_input_9th_cleaned')
    # energy_use_esto = pd.read_csv(root_dir + '/' +f'../transport_data_system/intermediate_data/EGEDA/model_input_9th_cleanedDATE{date_id}.csv')


    # original_model_output_with_fuels = pd.read_csv(root_dir + '/' + 'output_data/model_output_with_fuels/{}'.format(config.model_output_file_name))#cols 	Date	Economy	Scenario	Transport Type	Vehicle Type	Drive	Medium	Fuel	Energy
    # #grab scenario only = Reference
    # original_model_output_with_fuels = original_model_output_with_fuels[original_model_output_with_fuels['Scenario'] == 'Reference']
    # original_model_output_with_fuels_all_fuels = original_model_output_with_fuels.copy()
    
    # # cols: ['Economy', 'Fuel_Type', 'Date', 'Value', 'Transport Type', 'Frequency','Unit', 'Source', 'Dataset', 'Measure', 'Vehicle Type', 'Drive','Medium']

    # #TRANSPORT EGEDA
    # #LETS DO A FULL ANALYSIS OF HOW ENERGY USE IS CORRELATED WITH THE GROWTH RATES LIEK ABOVE, SINCE WE HAVE ENEGRY USE FOR HISTORICAL DATA.
    # #we will just grab '19 Total' for now
    # energy_use = energy_use_esto[energy_use_esto['Fuel_Type'] == '19_total']
    # energy_use_all_fuels = energy_use_esto[energy_use_esto['Fuel_Type'] != '19_total']

    # #rename Fuel_Type to Fuel in energy_use_all_fuels
    # energy_use_all_fuels = energy_use_all_fuels.rename(columns={'Fuel_Type': 'Fuel'})
    # #%%
    # #double check that the sum of medium=nan is equal to the sum of all the other mediums
    # # energy_use[energy_use['Medium'].isna()]['Value'].sum() == energy_use[energy_use['Medium'].notna()]['Value'].sum()#True
    # #filter for medium = nan
    # # energy_use = energy_use[energy_use['Medium'].isna()]
    # #rename where medium = nan to 'Total'
    # energy_use.loc[energy_use['Medium'].isna(), 'Medium'] = 'Total'
    # energy_use_all_fuels.loc[energy_use_all_fuels['Medium'].isna(), 'Medium'] = 'Total'
    # #drop nonneeded cols
    # energy_use = energy_use.drop(columns=['Fuel_Type', 'Frequency', 'Source', 'Dataset', 'Measure', 'Vehicle Type', 'Drive', 'Transport Type', 'Unit'])
    # energy_use_all_fuels = energy_use_all_fuels.drop(columns=[ 'Frequency', 'Source', 'Dataset', 'Measure', 'Vehicle Type', 'Drive', 'Transport Type', 'Unit'])
    # # #pivot so we have a column for each medium
    # # energy_use = energy_use.pivot(index=['Economy', 'Date'], columns='Medium', values='Value').reset_index()
    # #while we are analysing medium we shjould also not aggregate into reigons, as certain economys focus on certain mediums more

    # #reformat date to be in year only
    # energy_use['Date'] = energy_use['Date'].apply(lambda x: x[:4])
    # energy_use_all_fuels['Date'] = energy_use_all_fuels['Date'].apply(lambda x: x[:4])
    # #make into int
    # energy_use['Date'] = energy_use['Date'].astype(int)
    # energy_use_all_fuels['Date'] = energy_use_all_fuels['Date'].astype(int)
    # #rename Value to energy
    # energy_use = energy_use.rename(columns={'Value': 'Energy'})
    # energy_use_all_fuels = energy_use_all_fuels.rename(columns={'Value': 'Energy'})
    # #%%
    # #sum original_model_output_with_fuels by Date	Economy	Scenario	Medium
    # original_model_output_with_fuels = original_model_output_with_fuels.groupby(['Date', 'Economy', 'Medium']).sum().reset_index()
    # original_model_output_with_fuels_all_fuels = original_model_output_with_fuels_all_fuels.groupby(['Date', 'Economy', 'Fuel', 'Medium']).sum().reset_index()

    # #filter out fuels in energy_use_all_fuels that arentr in original_model_output_with_fuels_all_fuels. but keep them so  we can check there are none we want:
    # fuels_to_remove = energy_use_all_fuels[~energy_use_all_fuels['Fuel'].isin(original_model_output_with_fuels_all_fuels['Fuel'].unique())]['Fuel'].unique().tolist()
    # # #rename '01_x_thermal_coal' in energy_use_all_fuels to '01_x_coal_thermal
    # # energy_use_all_fuels.loc[energy_use_all_fuels['Fuel'] == '01_x_thermal_coal', 'Fuel'] = '01_x_coal_thermal'
    # #drop teh fuels
    # energy_use_all_fuels = energy_use_all_fuels[~energy_use_all_fuels['Fuel'].isin(fuels_to_remove)]
    # #%%
    # #extract only similar Dates
    # original_model_output_with_fuels = original_model_output_with_fuels[original_model_output_with_fuels['Date'].isin(energy_use['Date'].unique())]
    # energy_use = energy_use[energy_use['Date'].isin(original_model_output_with_fuels['Date'].unique())]

    # original_model_output_with_fuels_all_fuels = original_model_output_with_fuels_all_fuels[original_model_output_with_fuels_all_fuels['Date'].isin(original_model_output_with_fuels['Date'].unique())]
    # energy_use_all_fuels = energy_use_all_fuels[energy_use_all_fuels['Date'].isin(original_model_output_with_fuels['Date'].unique())]

    # #keep only data after 2015
    # original_model_output_with_fuels = original_model_output_with_fuels[original_model_output_with_fuels['Date'] >= 2015]
    # original_model_output_with_fuels_all_fuels = original_model_output_with_fuels_all_fuels[original_model_output_with_fuels_all_fuels['Date'] >= 2015]

    # #%%
    # #conat:
    # original_model_output_with_fuels['origin'] = 'model'
    # energy_use['origin'] = 'esto'

    # original_model_output_with_fuels_all_fuels['origin'] = 'model'
    # energy_use_all_fuels['origin'] = 'esto'
    #%%
    #conat them
    original_model_output_with_fuels = pd.concat([original_model_output_with_fuels, energy_use])
    for economy in original_model_output_with_fuels['Economy'].unique():
        #by economy create a line chart of energy use. make the color the origin, the line dash the origin and facet the medium
        title = f'Line chart of energy use by medium for {economy} - model vs esto'
        fig = px.line(original_model_output_with_fuels[original_model_output_with_fuels['Economy'] == economy], x='Date', y='Energy', color='origin', facet_col='Medium', facet_col_wrap=2, line_dash='origin', title=title, markers=True)
        fig.write_html(root_dir + '/' +f'plotting_output/diagnostics/esto_vs_model_energy_use/{title}.html')
        

    #by economy create a line chart of energy use. make the color the origin, the line dash the origin and facet the medium
    title = 'Line chart of energy use by medium for each economy - model vs esto'
    fig = px.line(original_model_output_with_fuels, x='Date', y='Energy', color='Medium', facet_col='Economy', facet_col_wrap=3, line_dash='origin', title=title, markers=True)
    fig.write_html(root_dir + '/' +f'plotting_output/diagnostics/esto_vs_model_energy_use/{title}.html')
    #%%
    #conat them
    original_model_output_with_fuels_all_fuels = pd.concat([original_model_output_with_fuels_all_fuels, energy_use_all_fuels])
    for economy in original_model_output_with_fuels_all_fuels['Economy'].unique():
        #by economy create a line chart of energy use. make the color the origin, the line dash the origin and facet the medium
        title = f'Line chart of energy use by medium and fuel for {economy} - model vs esto'

        fig = px.line(original_model_output_with_fuels_all_fuels[original_model_output_with_fuels_all_fuels['Economy'] == economy], x='Date', y='Energy', color='Fuel', facet_col='Medium', facet_col_wrap=2, line_dash='origin', title=title, markers=True)
        fig.write_html(root_dir + '/' +f'plotting_output/diagnostics/esto_vs_model_energy_use/{title}.html')
        


    #by economy create a line chart of energy use. make the color the origin, the line dash the origin and facet the medium
    title = 'Line chart of energy use by medium and fuel for each economy - model vs esto'
    #sum up all mediums
    original_model_output_with_fuels_all_fuels = original_model_output_with_fuels_all_fuels.groupby(['Date', 'Economy', 'Fuel', 'origin']).sum().reset_index()
    fig = px.line(original_model_output_with_fuels_all_fuels, x='Date', y='Energy', color='Fuel', facet_col='Economy', facet_col_wrap=3, line_dash='origin', title=title, markers=True)
    fig.write_html(root_dir + '/' +f'plotting_output/diagnostics/esto_vs_model_energy_use/{title}.html')

    #%%
    #filter for only 2017 in original_model_output_with_fuels_all_fuels and calcaaulte the diff between model and esto. then plot that as a bar, by economy, by fuel.
    original_model_output_with_fuels_all_fuels_2017 = original_model_output_with_fuels_all_fuels[original_model_output_with_fuels_all_fuels['Date'] == 2017]
    #pivot the data
    original_model_output_with_fuels_all_fuels_2017 = original_model_output_with_fuels_all_fuels_2017.pivot(index=['Economy', 'Fuel'], columns='origin', values='Energy').reset_index()
    #calculate the diff
    original_model_output_with_fuels_all_fuels_2017['diff'] = original_model_output_with_fuels_all_fuels_2017['esto'] - original_model_output_with_fuels_all_fuels_2017['model']
    #plot the diff
    title = 'Diff between model and esto energy use by fuel for each economy in 2017'
    fig = px.bar(original_model_output_with_fuels_all_fuels_2017, x='Economy', y='diff', color='Fuel', title=title)
    fig.write_html(root_dir + '/' +f'plotting_output/diagnostics/esto_vs_model_energy_use/{title}.html')

    # %%
