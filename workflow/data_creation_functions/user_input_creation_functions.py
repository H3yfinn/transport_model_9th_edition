#we will take in the vehicle sales from historical data, then adjust them according to the patterns we expect to see. i.e. nz moves to 100% ev's by 2030.

#we will also create a vehicle sales distribution that replicates what each scenario in the 8th edition shows. We can use this to help also load all stocks data so that we can test the model works like the 8th edition
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
#%%
##########################################
#UTILITY FUNCTIONS:
##########################################

def check_region(df_regions, data_df):
    
    #first find a col that is in one of the dfs not the other, for each df, and make sure there are no nas in htat col
    unique_col1 = [col for col in df_regions.columns if col not in data_df.columns][0]
    unique_col2 = [col for col in data_df.columns if col not in df_regions.columns][0]
    #check no nas in unique col
    if df_regions[unique_col1].isna().sum()>0:
        breakpoint()
        raise ValueError('There are nas in the {} col of the df_regions'.format(unique_col1))
    if data_df[unique_col2].isna().sum()>0:
        breakpoint()
        raise ValueError('There are nas in the {} col of the data_df'.format(unique_col2))
    
    ##############################
    
    #join on region col
    df_regions = df_regions.merge(data_df, on='Region', how='outer')
    #if there are nas in the economy col then there are regions in the data_df that are not in the df_regions. if there are nas in the Date col then there are regions in the df_regions that are not in the data_df
    missing_regions1 = df_regions[df_regions[unique_col1].isna()].Region.unique()
    missing_regions2 = df_regions[df_regions[unique_col2].isna()].Region.unique()
    if len(missing_regions1)>0:
        breakpoint()
        raise ValueError('The following regions are in the data_df but not in the df_regions: {}'.format(missing_regions1))
    if len(missing_regions2)>0:
        breakpoint()
        raise ValueError('The following regions are in the df_regions but not in the data_df: {}'.format(missing_regions2))
    







