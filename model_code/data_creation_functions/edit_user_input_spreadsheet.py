#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
from .. import utility_functions
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
######################################################################################################
do_this = False
if do_this:
    #first, prepare user input (in the future it may be smart ot aggregate this data in another file but for now it is ok)

    #Load user input from 'input_data\\user_input_spreadsheet.xlsx' by looping through the sheets in the excel file and then concat them together
    #first load the sheets
    user_input_file = pd.ExcelFile(os.path.join(config.root_dir, 'input_data', 'user_input_spreadsheet.xlsx'), engine='openpyxl')
    for sheet in user_input_file.sheet_names:
        print('Importing user input sheet: {}'.format(sheet))
        if sheet == user_input_file.sheet_names[0]:
            user_input = pd.read_excel(os.path.join(config.root_dir, 'input_data', 'user_input_spreadsheet.xlsx'), sheet_name=sheet)
        else:
            user_input = pd.concat([user_input, pd.read_excel(os.path.join(config.root_dir, 'input_data', 'user_input_spreadsheet.xlsx'), sheet_name=sheet)])




if do_this:
    # Example of dataset:
    #cols: 	Economy	Scenario	Transport Type	Date	Vehicle Type	Drive	Value	Unit	Medium	Data_available	Measure	Frequency
    # values: 01_AUS	Carbon Neutral	freight	2017	ht	bev	0.000622	%	road	data_available	Vehicle_sales_share	Yearly
    ################################################################################
    ################################################################################
    ################################################################################
    #we will replace some drive types with new ones. This may also involve changing or averaging values
    #first extract the data we will edit. it is the road meidum data
    road_data = user_input[user_input.Medium == 'road'].copy()
    #replace all g and d drives with 'ice'. 
    road_data.loc[road_data.Drive.isin(['g', 'd']), 'Drive'] = 'ice'
    #replace phevg and phevd with phev
    road_data.loc[road_data.Drive.isin(['phevg', 'phevd']), 'Drive'] = 'phev'
    #drp any drives not in the following: ['ice', 'bev', 'phev', 'fcev']
    road_data = road_data[road_data.Drive.isin(['ice', 'bev', 'phev', 'fcev', np.nan])]
    #now remove any duplicates
    road_data.drop_duplicates(inplace=True)
    #find any duplicates where the value is different
    cols = road_data.columns.tolist()
    cols.remove('Value')
    a = road_data[road_data.duplicated(subset=cols, keep=False)].sort_values(by=cols)
    print('There are {} duplicates in the road data'.format(a.shape[0]))
    #print unique measures
    print('Unique measures in dupes: {}'.format(a.Measure.unique()))
    #all are in vehicle sales share.

    #seprate vehicle sales share then sum when ignoring value, then pivot so drive is cols. Then calcualte 1- sum of the other drives
    vehicle_sales_share = road_data[road_data.Measure == 'Vehicle_sales_share']
    vehicle_sales_share = vehicle_sales_share.groupby(cols).sum().reset_index()
    cols.remove('Drive')
    vehicle_sales_share = vehicle_sales_share.pivot(index=cols, columns='Drive', values='Value')
    vehicle_sales_share['ice'] = 1 - vehicle_sales_share[['bev', 'phev', 'fcev']].sum(axis=1)
    vehicle_sales_share = vehicle_sales_share.reset_index()
    vehicle_sales_share = vehicle_sales_share.melt(id_vars=cols, value_vars=['ice', 'bev', 'phev', 'fcev'], var_name='Drive', value_name='Value')
    #drop nas in value col
    vehicle_sales_share = vehicle_sales_share[~vehicle_sales_share.Value.isna()]
    #now add this back to the user input
    road_data = pd.concat([road_data[road_data.Measure != 'Vehicle_sales_share'], vehicle_sales_share])
    #now we need to add the new drive types to the user input
    user_input = pd.concat([user_input[user_input.Medium != 'road'], road_data])

    #####

    #find number of ldvs in the freight transport type
    ldvs_in_freight = user_input[(user_input['Transport Type'] == 'freight') & (user_input['Vehicle Type'] == 'ldv')].copy()
    print('There are {} ldvs in the freight transport type'.format(ldvs_in_freight.shape[0]))
    # Drop any ldvs in the freight transport type
    user_input = user_input[~((user_input['Transport Type'] == 'freight') & (user_input['Vehicle Type'] == 'ldv'))]

    #We previously used drive and vehicle type = NA for the non road mediums. But it is better if we set them to something, as na's can cause issues and are better left for missing data. So set them to 'all' to indicate that they are for all drives and vehicle types, in case we do want to use them in the future
    user_input.loc[user_input.Medium != 'road', 'Drive'] = 'all'
    user_input.loc[user_input.Medium != 'road', 'Vehicle Type'] = 'all'

    #remove freight 2w
    user_input = user_input[~((user_input['Transport Type'] == 'freight') & (user_input['Vehicle Type'] == '2w'))]


    #make sure that for 2w the only drive types are 'ice' and 'bev'
    user_input = user_input[~((user_input['Vehicle Type'] == '2w') & (~user_input['Drive'].isin(['ice', 'bev'])))]


    #drop any nonspecified in any col
    user_input = user_input[~user_input.isin(['nonspecified']).any(axis=1)]

    #Latly make sure that everything matches our concordances. eg. units match what is in config.measure_to_unit_concordance and the transport categories match what is in manually_defined_transport_categories
    #import measure to unit concordance
    config.measure_to_unit_concordance = pd.read_csv(os.path.join(config.root_dir, 'config', 'concordances_and_config_data', 'config.measure_to_unit_concordance.csv'))

    #join to user input on the measure col an check that the units match
    user_input = user_input.merge(config.measure_to_unit_concordance, on='Measure', how='left')
    assert user_input[user_input.Unit_x != user_input.Unit_y].shape[0] == 0, 'There are some measures that do not match the unit in the measure_to_unit_concordance {} {}'.format(user_input[user_input.Unit_x != user_input.Unit_y].Measure.unique(), user_input[user_input.Unit_x != user_input.Unit_y].Unit_x.unique())
    #drop the unit_y col
    user_input.drop('Unit_y', axis=1, inplace=True)
    #rename unit_x to unit
    user_input.rename(columns={'Unit_x': 'Unit'}, inplace=True)


    #import manually_defined_transport_categories
    transport_categories = pd.read_csv(os.path.join(config.root_dir, 'config', 'concordances_and_config_data', 'manually_defined_transport_categories.csv'))
    #create dummy col which is just all cols added together
    transport_categories['dummy'] =  transport_categories['Medium'] + transport_categories['Transport Type'] + transport_categories['Vehicle Type'] + transport_categories['Drive']
    #join to user input on the Medium	Transport Type	Vehicle Type	Drive cols and if there are any that do not match then raise an error
    user_input = user_input.merge(transport_categories, on=['Medium', 'Transport Type', 'Vehicle Type', 'Drive'], how='outer')
    assert user_input[user_input.dummy.isna()].shape[0] == 0, 'There are some transport categories that do not match the manually_defined_transport_categories {}'.format(user_input[user_input.dummy.isna()][['Medium', 'Transport Type', 'Vehicle Type', 'Drive']].drop_duplicates().values)
    #check for where the dummy col is not na but the date is
    assert user_input[(user_input.Date.isna())].shape[0] == 0, 'There are some transport categories that arent in the manually_defined_transport_categories {}'.format(user_input[(user_input.Date.isna())][['Medium', 'Transport Type', 'Vehicle Type', 'Drive']].drop_duplicates().values)

    #drop the dummy col 
    user_input.drop('dummy', axis=1, inplace=True)


    #save as user input spreadhseet
    with pd.ExcelWriter(os.path.join('input_data', 'user_input_spreadsheet.xlsx')) as writer:
        for measure in user_input.Measure.unique():
            user_input[user_input.Measure == measure].to_excel(writer, sheet_name=measure, index=False)

#%%

#%%
# update_gompertz_inputs = True
# if update_gompertz_inputs:

#     #take in Gompertz inputs and set them manually here (because changing them in the spreadsheet is a bit hard and usually results in issues - because there are so many values)
#     #where the value is Stocks_per_capita, then set the values based on the economy to the values in:
#     #so filter for measure contains Gompertz
#     gompertz_inputs = user_input[user_input.Measure.str.contains('Gompertz')]
#     #set Gompertz_beta to 28
#     gompertz_inputs.loc[gompertz_inputs.Measure == 'Gompertz_beta', 'Value'] = 28
#     #set Gompertz_alpha to 200
#     gompertz_inputs.loc[gompertz_inputs.Measure == 'Gompertz_alpha', 'Value'] = 200

#     #resave to user input with the measure as the sheet name
#     for sheet in gompertz_inputs.Measure.unique():
#         print('Saving sheet: {}'.format(sheet))
#         gompertz_inputs[gompertz_inputs.Measure == sheet].to_excel(os.path.join('input_data', 'user_input_spreadsheet.xlsx'), sheet_name=sheet, index=False)
#%%
# #load in input_data/user_input_spreadsheet/activity_efficiency_improvement and remove duplicates
# activity_efficiency_improvement = pd.read_csv(os.path.join(config.root_dir, 'input_data', 'user_input_spreadsheets', 'activity_efficiency_improvement.csv'))
# activity_efficiency_improvement = activity_efficiency_improvement.drop_duplicates()
# activity_efficiency_improvement.to_csv(os.path.join(config.root_dir, 'input_data', 'user_input_spreadsheets', 'activity_efficiency_improvement.csv'), index=False)
# %%