#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
from os.path import join
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
def import_macro_data(config, UPDATE_INDUSTRY_VALUES, PLOT=False):
    #grab the file D:\APERC\transport_model_9th_edition\input_data\macro\APEC_Gdp_population.csv
    #from 
    # Modelling/Data/Gdp/Gdp projections 9th/Gdp_estimates/Gdp_estimates_12May2023/data
    
    macro_date_id = utility_functions.get_latest_date_for_data_file(os.path.join(config.root_dir, 'input_data', 'macro'), 'APEC_GDP_data_')
    macro = pd.read_csv(os.path.join(config.root_dir, 'input_data', 'macro', f'APEC_GDP_data_{macro_date_id}.csv'))
    
    #convert 17_SIN to 17_SGP, as well as 15_RP to 15_PHL
    if '17_SIN' in macro.economy_code.unique():
        macro['economy_code'] = macro['economy_code'].replace('17_SIN', '17_SGP')
    if '15_RP' in macro.economy_code.unique():
        macro['economy_code'] = macro['economy_code'].replace('15_RP', '15_PHL')
        
    #filter so  variable is in ['real_Gdp', 'population','Gdp_per_capita']
    macro = macro[macro['variable'].isin(['real_GDP', 'population','GDP_per_capita'])]
    #drop units col
    macro = macro.drop(columns=['units'])

    #import coeffficients prodcuied in create_growth_parameters:
    # 'input_data\\growth_coefficients_by_region.csv'
    growth_coeff = pd.read_csv(os.path.join(config.root_dir, 'input_data', 'growth_coefficients_by_region.csv'))
    #drop Region	alpha	r2	Model
    growth_coeff = growth_coeff.drop(columns=['Region', 'alpha', 'r2', 'Model'])
    growth_coeff.rename(columns={'Economy':'economy'}, inplace=True)
    #pull in activity_growth 
    activity_growth_8th = pd.read_csv(os.path.join(config.root_dir, 'input_data', 'from_8th', 'reformatted', 'activity_growth_8th.csv'))

    #pivot so each measure in the vairable column is its own column.
    macro = macro.pivot_table(index=['economy_code', 'economy', 'year'], columns='variable', values='value').reset_index()
    # macro.columns#Index(['economy_code', 'economy', 'date', 'real_Gdp', 'Gdp_per_capita', 'population'], dtype='object', name='variable')
    
    #make lowercase
    activity_growth_8th.columns = activity_growth_8th.columns.str.lower()
    #drop scenario and remove duplicvates
    activity_growth_8th = activity_growth_8th.drop(columns=['scenario']).drop_duplicates()
    #rename activity_growth to activity_growth_8th
    activity_growth_8th = activity_growth_8th.rename(columns={'activity_growth':'activity_growth_8th'})
    #soret by date
    activity_growth_8th = activity_growth_8th.sort_values(by=['economy', 'date'])
    #calcualte the growth rates compounded over time for use in diagnostics:
    activity_growth_8th['activity_growth_8th_index'] = activity_growth_8th.groupby('economy', group_keys=False)['activity_growth_8th'].apply(lambda x: (1 + x).cumprod())

    #cahnge real_Gdp to Gdp for brevity (we dont use the actual values anyway(just growth rates)) and some other stuff:
    macro = macro.drop(columns=['economy'])
    macro = macro.rename(columns={'real_GDP':'Gdp', 'GDP_per_capita': 'Gdp_per_capita','population':'Population', 'economy_code':'economy', 'year':'date'})

    
    #times population and gdp by 1000 to get it in actual numbers
    macro['Population'] = macro['Population'] * 1000
    macro['Gdp'] = macro['Gdp'] * 1000000

    #calcualate gdp_times_capita
    macro['Gdp_times_capita'] = macro['Gdp'] * macro['Population']
    
    #calcualte growth, duplicated or lag/leaded growth rates to be timesed by the coefficents in the growth_coeff file:
    macro1 = macro.copy()
    macro1 = macro1.sort_values(by=['economy', 'date'])
    coeff_vars = []
    for col in growth_coeff.columns:
        if col.endswith('_coeff'):
            col = col.replace('_coeff', '')
            coeff_vars.append(col)
            if col.endswith('growth'):
                original_col = re.sub(r'_growth$', '', col)
                macro1[col] = macro1.groupby('economy')[original_col].pct_change()
            elif re.search(r'_\d*$', col):
                original_col = re.sub(r'_\d*$', '', col)
                macro1[col] = macro1[original_col].copy()#duplicated cols
            elif re.search(r'_lag\d*$', col):
                num = int(re.search(r'\d*$', col).group())
                original_col = re.sub(r'_lag\d*$', '', col)
                macro1[col] = macro1.groupby('economy')[original_col].shift(num)
            elif re.search(r'_lead\d*$', col):
                num = int(re.search(r'\d*$', col).group())
                original_col = re.sub(r'_lead\d*$', '', col)
                macro1[col] = macro1.groupby('economy')[original_col].shift(-num)
    if not set(coeff_vars).issubset(set(macro1.columns)):
        missing_cols = [col for col in coeff_vars if col not in macro1.columns]
        raise ValueError('The following variables are not in macro1: {}'.format(missing_cols))
    #combine it with above data using a merge
    macro1 = pd.merge(macro1, growth_coeff, on=['economy'], how='left')
    
    #filter any rows with nas
    macro1 = macro1.dropna()

    #calcuilate energy growth rate using the coefficents in the growth_coeff file:
    macro1['energy_growth_est'] = macro1['const']
    for col in coeff_vars:
        macro1['energy_growth_est'] = macro1['energy_growth_est'] + macro1[col] * macro1[col+'_coeff']
    #since we currently have no idea about intensity, we will assume that energy growth is the same as activity growth
    macro1['Activity_growth'] = macro1['energy_growth_est']
    #ADD ONE
    macro1['Activity_growth'] = macro1['Activity_growth'] + 1
    #also add one to activity_growth_8th.activity_growth_8th
    activity_growth_8th['activity_growth_8th'] = activity_growth_8th['activity_growth_8th'] + 1
    
    #join activity_growth_8th on for diagnostics so they are from same date
    macro1 = pd.merge(macro1, activity_growth_8th, on=['economy', 'date'], how='left')

    #make all cols start with caps 
    macro1.columns = [col.capitalize() for col in macro1.columns]
    #make tall and then attach units:
    macro1 = macro1.melt(id_vars=['Economy', 'Date'], value_vars=['Gdp_per_capita', 'Population', 'Gdp',
    'Gdp_times_capita', 'Gdp_growth', 'Population_growth',
    'Gdp_per_capita_growth', 'Gdp_times_capita_growth', 'Const',
    'Energy_growth_est', 'Activity_growth', 'Activity_growth_8th',
    'Activity_growth_8th_index']+coeff_vars, var_name='Measure', value_name='Value')

    
    #split into 'Transport Type' by creating one df for each transport type in 'passenger' and 'freight'
    macro1_passenger = macro1.copy()
    macro1_passenger['Transport Type'] = 'passenger'
    macro1_freight = macro1.copy()
    macro1_freight['Transport Type'] = 'freight'
    #concat
    macro1 = pd.concat([macro1_passenger, macro1_freight])

    
    #split macro into the required scenarios. perhaps later, if the macro differs by scenario we will do this somehwere ese:
    new_macro = pd.DataFrame()
    for scenario in config.SCENARIOS_LIST:
        s_macro = macro1.copy()
        s_macro['Scenario'] = scenario
        new_macro = pd.concat([new_macro, s_macro])
    macro1 = new_macro.copy()
    
    macro2= tie_freight_growth_to_gdp_growth(config, macro1,UPDATE_INDUSTRY_VALUES)
    macro2 = pd.merge(macro2, config.measure_to_unit_concordance[['Unit', 'Measure']], on=['Measure'], how='left')
    #save to intermediate_data/model_inputs/regression_based_growth_estimates.csv 
    #slightly increase PNG growth rates.
    macro3 = update_png_growth_rates(config, macro2, PLOT=PLOT)
    
    macro3.to_csv(os.path.join(config.root_dir, 'intermediate_data', 'model_inputs', 'regression_based_growth_estimates.csv'), index=False)


def update_png_growth_rates(config, macro2, PLOT=True):
    #slightly increase PNG growth rates. Unfortunately its hard to tell exactly how mcuh they should increase by. Maybe enough to match the 8th edition? or enough to match economies which went through similar levels of growth in the past? for now lets jsut match activity_growth_8th
    macro2_png_8th = macro2.loc[(macro2['Economy']=='13_PNG') & (macro2['Measure']=='Activity_growth_8th')].copy()
    macro2_png = macro2.loc[(macro2['Economy']=='13_PNG') & (macro2['Measure']=='Activity_growth')].copy()
    macro2_png.rename(columns={'Value':'Activity_growth'}, inplace=True)
    macro2_png = macro2_png.drop(columns=['Measure'])
    macro2_png_8th.rename(columns={'Value':'Activity_growth_8th'}, inplace=True)
    macro2_png_8th = macro2_png_8th.drop(columns=['Measure'])
    #join and start the process to match the growth rates. However, we want to copy the annual variation of Activity growth, yet use the trend and level of the 8th edition. This is also important because we dont have all the years in the 8th edition, so we cant just use the 8th edition as is.
    png_growth = pd.merge(macro2_png, macro2_png_8th, on=['Economy', 'Date', 'Transport Type', 'Scenario'], how='left')

    # Calculate the ratio of 'Activity_growth_8th' to 'Activity_growth'
    png_growth['growth_ratio'] = png_growth['Activity_growth_8th'] / png_growth['Activity_growth']
    #smooth the ratio by removeing outliers and then taking the 5 year rolling avg (outliers are probably 2022)
    growth_ratio = png_growth[['Economy','Transport Type', 'Scenario', 'Date', 'growth_ratio']].copy()
    #drop outliers
    def remove_outliers(config, df, column):
        from scipy import stats
        #drop nas
        df = df.dropna()
        df = df[(np.abs(stats.zscore(df[column])) < 3)]
        return df

    growth_ratio = remove_outliers(config, growth_ratio, 'growth_ratio')
    #print the dates for vlaues that were removed:
    png_growth_no_nas = png_growth.dropna(subset=['growth_ratio'])
    missing_dates = png_growth_no_nas.loc[~png_growth_no_nas['Date'].isin(growth_ratio['Date'])]['Date'].unique()
    # print(f'The following dates were removed from the growth_ratio calculation due to being outliers: {missing_dates}')
    
    growth_ratio = growth_ratio.sort_values(by=['Economy','Transport Type', 'Scenario', 'Date'])
    #merge back to png_growth and interpolate missing values
    png_growth = pd.merge(png_growth, growth_ratio, on=['Economy','Transport Type', 'Scenario', 'Date'], how='left')
    png_growth['growth_ratio_y'] = png_growth.groupby(['Economy', 'Transport Type', 'Scenario'])['growth_ratio_y'].transform(lambda x: x.interpolate())
    #finallly take the 10 year rolling avg since its just meant to apply a step change to the growth rates
    png_growth['growth_ratio_y'] = png_growth.groupby(['Economy', 'Transport Type', 'Scenario'])['growth_ratio_y'].transform(lambda x: x.rolling(10, min_periods=1).mean())
    png_growth['growth_ratio'] = png_growth['growth_ratio_y']
    png_growth = png_growth.drop(columns=['growth_ratio_x', 'growth_ratio_y'])
    
    # Apply the ratio to 'Activity_growth' to match the trend and level of 'Activity_growth_8th'
    png_growth['Activity_growth_new'] = png_growth['Activity_growth'] * png_growth['growth_ratio']

    if PLOT:
        png_growth_melt = plot_png_growth(config, png_growth)
    
    # Drop the 'Activity_growth_8th' and 'growth_ratio' columns as they are no longer needed
    png_growth = png_growth.drop(columns=['Activity_growth_8th', 'growth_ratio', 'Activity_growth'])
    #and now create measure and value cols
    png_growth['Measure'] = 'Activity_growth'
    png_growth = png_growth.rename(columns={'Activity_growth_new':'Value'})
    
    #add it bavl to macro2
    macro2 = macro2.loc[~((macro2['Economy']=='13_PNG') & (macro2['Measure']=='Activity_growth'))]
    macro2 = pd.concat([macro2, png_growth])
    return macro2
    
def plot_png_growth(config, png_growth):
    
    # Melt the dataframe to long format for plotting
    png_growth_melt = png_growth.melt(id_vars=['Date', 'Transport Type'], value_vars=['Activity_growth', 'Activity_growth_new', 'Activity_growth_8th'], var_name='Measure', value_name='Growth Rate')
    
    #sort data so it is in the right order
    png_growth_melt = png_growth_melt.sort_values(by=['Date', 'Transport Type', 'Measure'])
    
    # Create a facet grid plot with plotly
    fig = px.line(png_growth_melt, x='Date', y='Growth Rate', color='Measure', facet_row='Transport Type', title='Growth Rates Over Time')
    #write html to plotting_output/growth_analysis/png_growth_rates.html
    fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'growth_analysis', 'png_growth_rates.html'), auto_open=True) 
    
    return png_growth_melt
    
def tie_freight_growth_to_gdp_growth(config, macro1, UPDATE_INDUSTRY_VALUES):
    #after realising that freight and stocks per cpita arent a great mix for estimaitn freight growth, i figured basing it off gdp growth  would be better. this was because i found that my growth rates were realtively similar anyway, and then research online suggested that people use elasticity of freight transport demand relative to GDP. So by setting this manully, based on what i think an economy is like, i can get a better estimate of freight growth.
    
    #frist take in freight_to_gdp_growth_ratio from parameters.xlsx
    # freight_to_gdp_growth_ratio = pd.read_excel(os.path.join(config.root_dir, 'input_data', 'parameters.xlsx'), sheet_name='freight_to_gdp_growth_ratio')
    #take in services and industry share of gdp from industry model:
    freight_to_gdp_growth_ratio = grab_gdp_shares_from_industry(config, UPDATE_INDUSTRY_VALUES)
    
    #add a specified amount to the freight_to_gdp_growth_ratio for each economy to represent freight not connected to industry growth (eg. deliveries to homes, etc.)
    
    NON_INDUSTRY_FREIGHT_ADDITION =  yaml.load(open(os.path.join(config.root_dir, 'config', 'parameters.yml')), Loader=yaml.FullLoader)['NON_INDUSTRY_FREIGHT_ADDITION']
    for economy in freight_to_gdp_growth_ratio.Economy.unique():
        addition = NON_INDUSTRY_FREIGHT_ADDITION[economy]
        freight_to_gdp_growth_ratio.loc[freight_to_gdp_growth_ratio['Economy']==economy, 'freight_growth_to_gdp_growth_ratio'] = freight_to_gdp_growth_ratio.loc[freight_to_gdp_growth_ratio['Economy']==economy, 'freight_growth_to_gdp_growth_ratio'] + addition
            
    #where freight is teh transport type, and gdp_growth is the measure multiply gdp_growth by freight_to_gdp_growth_ratio to get the new growth rate. then isolate that. then replace that for acitvity groewth where freight is the transport type
    New_Activity_growth = macro1.loc[(macro1['Transport Type']=='freight')&(macro1['Measure']=='Gdp_growth')].copy()
    New_Activity_growth = pd.merge(New_Activity_growth, freight_to_gdp_growth_ratio, on=['Economy', 'Date'], how='left')
    New_Activity_growth['Value'] = (New_Activity_growth['Value'] * New_Activity_growth['freight_growth_to_gdp_growth_ratio']) + 1
    New_Activity_growth['Measure'] = 'Activity_growth'
    
    macro1 = macro1.loc[~((macro1['Transport Type']=='freight')&(macro1['Measure']=='Activity_growth'))]
    New_Activity_growth = New_Activity_growth.drop(columns=['freight_growth_to_gdp_growth_ratio'])

    macro2 = pd.concat([macro1, New_Activity_growth])
    
    return macro2

def grab_gdp_shares_from_industry(config, UPDATE_INDUSTRY_VALUES):
    #loop through economies and grab the shares from either:
    # if UPDATE_VALUES: C:/Users/finbar.maunsell/OneDrive - APERC/outlook 9th/Modelling/Sector models/Industry/Interim production/1_industry_interim1/{ECONOMY_ID}/{ECONOMY_ID}_NV.IND.TOTL.ZS.csv.
    # else: input_data/macro/industry_gdp_shares/{ECONOMY_ID}_NV.IND.TOTL.ZS.csv
    #the reason why we grab manufacturing shares is becuase some economies dont have industry shares, but they do have manufacturing shares. so we will use the average difference between industry and manufacturing shares in other economies to add to the manufacturing shares in the economy that doesnt have industry shares.(eg. VN)
    all_shares = pd.DataFrame() 
    for economy in config.economy_scenario_concordance['Economy'].unique():
        if economy == '18_CT':
            continue
        avg_df = False
        
        root_onedrive = os.path.join('C:', 'Users', 'finbar.maunsell', 'OneDrive - APERC', 'outlook 9th', 'Modelling', 'Sector models', 'Industry', 'Interim production', '1_industry_interim1')
        root_local = os.path.join('input_data', 'macro', 'industry_gdp_shares')
        industry_filename = f'{economy}_NV.IND.TOTL.ZS.csv'
        manu_filename = f'{economy}_NV.IND.MANF.ZS.csv'
        industry_path_onedrive = os.path.join(root_onedrive, economy, industry_filename)
        industry_path_local = os.path.join(config.root_dir, root_local, industry_filename)
        manu_path_onedrive = os.path.join(root_onedrive, economy, manu_filename)
        manu_path_local = os.path.join(config.root_dir, root_local, manu_filename)
        
        if UPDATE_INDUSTRY_VALUES:
            
            try:
                if economy == '21_VN':
                    df = pd.read_csv(manu_path_onedrive)
                else:
                    df = pd.read_csv(industry_path_onedrive)
                    #move data to input_data/macro/industry_gdp_shares/ so we can use it later wihtout having to go through onedrive
                    shutil.copy(industry_path_onedrive, industry_path_local)
                #also move the manu data
                shutil.copy(manu_path_onedrive, manu_path_local)
                
            except FileNotFoundError:   
                              
                avg_df = True
                #for now raise warning but can use average of other economies later
                
                #just quickly, if the economy is 15_PHL or 17_SGP then try load in using 15_RP as economy and 17_SING as economy
                if economy in ['15_PHL', '17_SGP']:
                    a = {
                        '15_PHL': '15_RP',
                        '17_SGP': '17_SIN'
                    }
                    alt_econ_name = a[economy]
                    alt_ind_filepath = os.path.join(root_onedrive, alt_econ_name, f'{alt_econ_name}_NV.IND.TOTL.ZS.csv')
                    alt_manu_filepath = os.path.join(root_onedrive, alt_econ_name, f'{alt_econ_name}_NV.IND.MANF.ZS.csv')
                    try:
                        df = pd.read_csv(alt_ind_filepath)
                        df['economy_code'] = economy
                        #save it in the location with the updated economy col too
                        df.to_csv(industry_path_local, index=False)
                        # shutil.copy(alt_ind_filepath, industry_path_local)
                        #also move the manu data
                        df_manu = pd.read_csv(alt_manu_filepath)
                        df_manu['economy_code'] = economy
                        df_manu.to_csv(manu_path_local, index=False)
                        # shutil.copy(alt_manu_filepath, manu_path_local)
                    except FileNotFoundError:
                        raise FileNotFoundError(f'No file found at {alt_ind_filepath}')
                elif economy == '21_VN':
                    raise FileNotFoundError(f'No file found at {manu_path_onedrive}')
                else:
                    raise FileNotFoundError(f'No file found at {industry_path_onedrive}')
        else:
            try:
                if economy == '21_VN':
                    df = pd.read_csv(manu_path_local)
                else:
                    df = pd.read_csv(industry_path_local)
            except FileNotFoundError:
                
                avg_df = True
                #for now raise warning but can use average of other economies later
                if economy == '21_VN':
                    raise FileNotFoundError(f'No file found at {manu_path_local}')
                raise FileNotFoundError(f'No file found at {industry_path_local}')
        if not avg_df:
            #drop economy, series_code, series cols
            df = df.drop(columns=['economy', 'series_code', 'series'])
            #chagne year to Date col
            df = df.rename(columns={'year':'Date', 'economy_code': 'Economy', 'value': 'freight_growth_to_gdp_growth_ratio'})
            #divide freight_growth_to_gdp_growth_ratio by 100 to get it in decimal form
            df['freight_growth_to_gdp_growth_ratio'] = df['freight_growth_to_gdp_growth_ratio'] / 100
            #concat
        else:
            #need to create a df with avg of all others for now
            df = all_shares.copy()
            df['Economy'] = economy
            df= df.groupby(['Economy', 'Date']).mean().reset_index()
        all_shares = pd.concat([all_shares, df])

    all_shares = calculate_CT_share(config, all_shares)
    all_shares = calculate_VN_share(config, all_shares)    
    # all_shares['Measure'] = 'Industry_gdp_share'
    #save to intermediate_data/model_inputs/industry_gdp_shares.csv for use in future
    all_shares.to_csv(os.path.join(config.root_dir, 'intermediate_data', 'model_inputs', 'industry_gdp_shares.csv'), index=False)
    
    if UPDATE_INDUSTRY_VALUES:
        #plot the gdp shares for each economy suing a line plot
        fig = px.line(all_shares, x='Date', y='freight_growth_to_gdp_growth_ratio', color='Economy')
        fig.write_html(os.path.join(config.root_dir, 'plotting_output', 'growth_analysis', 'industry_gdp_shares.html'), auto_open=True)
        
    return all_shares   
        
def calculate_CT_share(config, all_shares):
    #sicne chinese taipei (ehem' taiwan) isnt allowed to share gdp data or something we will use the average of the other similar economies (09_ROK, 08_JPN)
    ct_data = all_shares.loc[all_shares['Economy'].isin(['09_ROK', '08_JPN'])].copy()
    ct_data['Economy'] = '18_CT'
    ct_data = ct_data.groupby(['Economy', 'Date']).mean().reset_index()
    all_shares = pd.concat([all_shares, ct_data])
    return all_shares 

def calculate_VN_share(config, all_shares):
    #we will add what is missing from idnustry shares to manu shares by finding the average difference between manu and industry in the other SEA economies. then we will add that to the manu shares
    #first load in the manu shares for the sea economies (excl bd and sing):
    sea_economies = ['07_INA', '10_MAS', '15_PHL', '19_THA']
    manu_diffs = pd.DataFrame()
    for economy in sea_economies:
        df = pd.read_csv(os.path.join(config.root_dir, 'input_data', 'macro', 'industry_gdp_shares', f'{economy}_NV.IND.MANF.ZS.csv')).rename(columns={'value': 'manu_share', 'year':'Date'})
        #grab the industry data
        ind_df = all_shares.loc[all_shares['Economy']==economy].copy()
        #join on date
        df = pd.merge(df, ind_df, on=[os.path.join('Date')], how='left')
        #calculate the difference between manu and industry
        df['diff'] = df['freight_growth_to_gdp_growth_ratio'] - (df['manu_share']/100)
        #add to manu_diffs
        manu_diffs = pd.concat([manu_diffs, df[[os.path.join('Date'), 'diff']]])
    #calculate the average difference
    manu_diffs = manu_diffs.groupby([os.path.join('Date')]).mean().reset_index()
    #set economy to VN then join to all_shares
    manu_diffs['Economy'] = '21_VN'
    all_shares = pd.merge(all_shares, manu_diffs, on=['Economy', os.path.join('Date')], how='left')
    #set all_shares['diff'] to 0 if it is na
    all_shares['diff'] = all_shares['diff'].fillna(0)
    #add the diff to the manu share
    all_shares['freight_growth_to_gdp_growth_ratio'] = all_shares['freight_growth_to_gdp_growth_ratio'] + all_shares['diff']
    #drop diff
    all_shares = all_shares.drop(columns=['diff'])
    return all_shares
#%%
# import_macro_data(config, True, PLOT=False)
#%%
