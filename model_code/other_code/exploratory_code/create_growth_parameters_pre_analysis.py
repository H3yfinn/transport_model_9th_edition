
# Modelling >> Data >> GDP >> GDP projections 9th >> GDP_estimates >> GDP_estimates_12May2023
import pandas as pd
#set working directory as one folder back so that config works
import os
import sys
import re
sys.path.append(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
current_working_dir = os.getcwd()
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir =  "\\\\?\\" + re.split('transport_model_9th_edition', script_dir)[0] + 'transport_model_9th_edition'
if __name__ == "__main__": #this allows the script to be run directly or from the main.py file as you cannot use relative imports when running a script directly
    # Modify sys.path to include the directory where utility_functions is located
    sys.path.append(f"{root_dir}\\code")
    import config
    import utility_functions
else:
    # Assuming the script is being run from main.py located at the root of the project, we want to avoid using sys.path.append and instead use relative imports 
    from .. import utility_functions
    from .. import config
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

#grab the file D:\APERC\transport_model_9th_edition\input_data\macro\APEC_GDP_population.csv
macro = pd.read_csv(root_dir + '\\' + 'D:\\APERC\\transport_model_9th_edition\\input_data\\macro\\APEC_GDP_population.csv')
#pull in activity_growth 
activity_growth = pd.read_csv(root_dir + '\\' + 'intermediate_data\\model_inputs\\activity_growth.csv')
# macro.columns#Index(['economy_code', 'economy', 'date', 'variable', 'value'], dtype='object')
#pivot so each measure in the vairable column is its own column.
macro = macro.pivot_table(index=['economy_code', 'economy', 'year'], columns='variable', values='value').reset_index()
# macro.columns#Index(['economy_code', 'economy', 'date', 'real_GDP', 'GDP_per_capita', 'population'], dtype='object', name='variable')
#%%
#cahnge real_GDP to GDP for brevity (we dont use the actual values anyway(just growth rates)) and some other stuff:
macro = macro.drop(columns=['economy'])
macro = macro.rename(columns={'real_GDP':'GDP', 'population':'Population', 'economy_code':'economy', 'year':'date'})
#%%

#make activity growth columns into lowercase
activity_growth.columns = [x.lower() for x in activity_growth.columns]
scenarios = activity_growth['scenario'].unique()
#pivot the scenario column 
activity_growth = activity_growth.pivot(index=['economy', 'date'], columns='scenario', values='activity_growth').reset_index()
#change the scenario column names to be more descriptive (so they end with _activity_growth)
activity_growth.columns = [x+'_activity_growth' if x in scenarios else x for x in activity_growth.columns]

#%%
#calcaulte grwoth rates for all when you group by economy (make sure that date is sorted form low to high)
macro1 = macro.copy()
macro1 = macro1.sort_values(by=['economy', 'date'])
macro1['GDP_growth'] = macro1.groupby('economy')['GDP'].pct_change()
macro1['Population_growth'] = macro1.groupby('economy')['Population'].pct_change()
macro1['GDP_per_capita_growth'] = macro1.groupby('economy')['GDP_per_capita'].pct_change()
#%%
#combine it with above data using a merge
macro1 = pd.merge(macro1, activity_growth, on=['economy', 'date'], how='left')
#filter any rows with nas
macro1 = macro1.dropna()

#####
#convert the 'Carbon Neutral_activity_growth' and 'Reference_activity_growth' to be in terms of actual numbers rather than growth rates (i.e. inverse of growth rate)
macro1['Carbon Neutral_activity'] = (1 + macro1['Carbon Neutral_activity_growth']).cumprod()
macro1['Reference_activity'] = (1 + macro1['Reference_activity_growth']).cumprod()
#index it to be in terms of the other indexes 
macro1['Carbon Neutral_activity_growth_index'] = macro1.groupby('economy')['Carbon Neutral_activity'].apply(lambda x: x/x.iloc[0])
macro1['Reference_activity_growth_index'] = macro1.groupby('economy')['Reference_activity'].apply(lambda x: x/x.iloc[0])
#calcaulte an index of all values so we can plot them on the same graph
macro1['GDP_index'] = macro1.groupby('economy')['GDP'].apply(lambda x: x/x.iloc[0])
macro1['Population_index'] = macro1.groupby('economy')['Population'].apply(lambda x: x/x.iloc[0])
macro1['GDP_per_capita_index'] = macro1.groupby('economy')['GDP_per_capita'].apply(lambda x: x/x.iloc[0])
#####
#try it differently by using the smae method as (1 + df['Carbon Neutral_activity_growth']).cumprod() for all the variables
macro1_indexed_pct_growth = macro1.copy()
macro1_indexed_pct_growth['GDP_index'] = (1 + macro1_indexed_pct_growth['GDP_growth']).cumprod()
macro1_indexed_pct_growth['Population_index'] = (1 + macro1_indexed_pct_growth['Population_growth']).cumprod()
macro1_indexed_pct_growth['GDP_per_capita_index'] = (1 + macro1_indexed_pct_growth['GDP_per_capita_growth']).cumprod()
macro1_indexed_pct_growth['Carbon Neutral_activity_growth_index'] = (1 + macro1_indexed_pct_growth['Carbon Neutral_activity_growth']).cumprod()
macro1_indexed_pct_growth['Reference_activity_growth_index'] = (1 + macro1_indexed_pct_growth['Reference_activity_growth']).cumprod()
#####
#%%
plot_this = False
if plot_this:
    #plot these as line graphs using plotly
    #first melt
    macro1_melt = macro1.melt(id_vars=['economy', 'date'], value_vars=['GDP_index', 'Population_index', 'GDP_per_capita_index', 'Carbon Neutral_activity_growth_index', 'Reference_activity_growth_index'], var_name='variable', value_name='value')
    #then plot
    import plotly.express as px
    fig = px.line(macro1_melt, x='date', y='value', color='variable', facet_col='economy', facet_col_wrap=3)
    #name y axis as an indexed
    fig.update_yaxes(title_text='Index (base date = {}'.format(macro1['date'].min()))
    #save to plotting_output\input_analysis
    fig.write_html(root_dir + '\\' + 'plotting_output\\input_analysis\\macro_data_growth_indexes2.html')

    macro1_melt = macro1_indexed_pct_growth.melt(id_vars=['economy', 'date'], value_vars=['GDP_index', 'Population_index', 'GDP_per_capita_index', 'Carbon Neutral_activity_growth_index', 'Reference_activity_growth_index'], var_name='variable', value_name='value')
    #then plot
    import plotly.express as px
    fig = px.line(macro1_melt, x='date', y='value', color='variable', facet_col='economy', facet_col_wrap=3)
    #name y axis as an indexed
    fig.update_yaxes(title_text='Index (base date = {}'.format(macro1['date'].min()))
    #save to plotting_output\input_analysis
    fig.write_html(root_dir + '\\' + 'plotting_output\\input_analysis\\macro_data_growth_indexes1.html')


#if it is not similar then we should try and estiamte an average multiplicative diffeence. We could use this to times by growth in gdp per capita to find the activity growth rate. 

# if similar then great, we can use the gdp per capita growth rate to calcualte activity growth by timesing it by activity.
# %%
######################################

#try somethihng different: we will take in the og data and then test the effect of different ggrowth rates vs the actual growth rates hugh used.
#also to help, we will split the data into similar regions in terms of growth and geography:

#first, split data into regions using D:\APERC\transport_model_9th_edition\config\concordances_and_config_data\region_economy_mapping.csv and the columns Economy Region_growth_analysis



#so take in the activity data and calcualte the growth rates for each economy
#%%
#data
#take in activity data from 8th edition up to 2050 (activity_from_OSEMOSYS-hughslast.csv)
activity = pd.read_csv(root_dir + '\\' + 'input_data\\from_8th\\reformatted\\activity_from_OSEMOSYS-hughslast.csv')

region_economy_mapping = pd.read_csv(root_dir + '\\' + 'config\\concordances_and_config_data\\region_economy_mapping.csv')
#make cols lower case
region_economy_mapping.columns = [col.lower() for col in region_economy_mapping.columns]
#drop Region col
region_economy_mapping.drop('region', axis=1, inplace=True)

#keep reference only since the growth rates are the same
activity = activity[activity['Scenario'] == 'Reference']
#%%
#define index cols
INDEX_COLS = ['Economy','Date']

#remove unnecessary cols and remove duplicates (all cols that arent INDEX_COLS or Value)
activity.drop([col for col in activity.columns if col not in INDEX_COLS + ['Activity']], axis=1, inplace=True)
activity.drop_duplicates(inplace=True)

#sum up Value col by index cols
activity_growth = activity.groupby(INDEX_COLS).sum().reset_index()

#sort by year and everything else in ascending order
activity_growth = activity_growth.sort_values(by=INDEX_COLS)

#make cols lower case
activity_growth.columns = [col.lower() for col in activity_growth.columns]
#%%
#join activity_growth with macro data
macro2 = macro.copy()
macro2 = macro2.merge(activity_growth, how='inner', on=['economy', 'date'])

#merge the regions on and sum by region
macro2 = macro2.merge(region_economy_mapping, how='left', on='economy')
#drop nonneeded cols
macro2.drop(['economy'], axis=1, inplace=True)
macro2 = macro2.groupby(['region_growth_analysis', 'date']).sum().reset_index()
#change actvitiy to be called 8th_activity
macro2.rename(columns={'activity': '8th_activity'}, inplace=True)
#calcaulte grwoth rates for all (except activity) when you group by region_growth_analysis (make sure that date is sorted form low to high)
macro2 = macro2.sort_values(by=['region_growth_analysis', 'date'])
macro2['GDP_growth'] = macro2.groupby('region_growth_analysis')['GDP'].pct_change()
macro2['Population_growth'] = macro2.groupby('region_growth_analysis')['Population'].pct_change()
macro2['GDP_per_capita_growth'] = macro2.groupby('region_growth_analysis')['GDP_per_capita'].pct_change()

#the base year to 1 as the growth rate is not defined for the base year (in the code its actually using the row above for 2050 currently)
macro2.loc[macro2['date'] == config.DEFAULT_BASE_YEAR, ['GDP_growth', 'Population_growth', 'GDP_per_capita_growth']] = 0

# Calculate cumulative product of growth rates+1
#add 1 to the growth rates
macro2['GDP_growth2'] = macro2['GDP_growth'] + 1
macro2['Population_growth2'] = macro2['Population_growth'] + 1   
macro2['GDP_per_capita_growth2'] = macro2['GDP_per_capita_growth'] + 1

macro2['GDP_index'] = macro2.groupby('region_growth_analysis')['GDP_growth2'].cumprod()
macro2['Population_index'] = macro2.groupby('region_growth_analysis')['Population_growth2'].cumprod()
macro2['GDP_per_capita_index'] = macro2.groupby('region_growth_analysis')['GDP_per_capita_growth2'].cumprod()

#calcuale activity using the growth rates
#grab the 8th activity in first year (and keep region_growth_analysis)
first_year_activity = macro2.loc[macro2['date'] == config.DEFAULT_BASE_YEAR, ['region_growth_analysis', '8th_activity']]
#call the col 8th_activity_first_year
first_year_activity = first_year_activity.rename(columns={'8th_activity': '8th_activity_first_year'})
#now join it on
macro2 = macro2.merge(first_year_activity, how='left', on='region_growth_analysis')
#now calcualte the activity for each growth rate
macro2['GDP_activity'] = macro2['GDP_index'] * macro2['8th_activity_first_year']
macro2['Population_activity'] = macro2['Population_index'] * macro2['8th_activity_first_year']
macro2['GDP_per_capita_activity'] = macro2['GDP_per_capita_index'] * macro2['8th_activity_first_year']

#melt so the cols GDP_activity, Population_activity, GDP_per_capita_activity and 8th_activity are all in one col called activity with a col called variable that says which one it is
#first filter for useful cols
macro2_melt = macro2[['region_growth_analysis', 'date', 'GDP_activity', 'Population_activity', 'GDP_per_capita_activity', '8th_activity']]

macro2_melt = macro2.melt(id_vars=['region_growth_analysis', 'date'], value_vars=['GDP_activity', 'Population_activity', 'GDP_per_capita_activity', '8th_activity'], var_name='variable', value_name='activity')

#%%
#drop china and North America because they are too big and mess up the graph
macro2_melt = macro2_melt[macro2_melt['region_growth_analysis'] != 'China']
macro2_melt = macro2_melt[macro2_melt['region_growth_analysis'] != 'North America']
#where variable is 8th acitivty, make 'line_dash' = '8th_activity' and everything else make it 'line_dash' = 'variable'
macro2_melt['line_dash'] = macro2_melt['variable'].apply(lambda x: '8th_activity' if x == '8th_activity' else 'variable')
plot_this = False
if plot_this:
    #plot these as line graphs using plotly
    #then plot
    #make the lines for everythign except 8th activity be dashed and slihtly transparent. Make sure the 8th activity is solid and not transparent
    import plotly.express as px
    fig = px.line(macro2_melt, x='date', y='activity', color='variable', line_dash='line_dash', color_discrete_sequence=px.colors.qualitative.Plotly, facet_col='region_growth_analysis', facet_col_wrap=3)
    #name y axis as activity
    fig.update_yaxes(title_text='Activity')
    #save to plotting_output\input_analysis
    fig.write_html(root_dir + '\\' + 'plotting_output\\input_analysis\\macro_data_growth_analysis_no_china.html')

#for now save a dummy growth rate so we can continue with the model (this will be replaced with the real growth rates later)
#we can gernally assume that gdp per capita is the best to use, and then the S curves for stocks will serve as a way of decreasing growth if stocks are too high.
#it seems likely that passenger transport is slightly weighted towards population growth, and freight transport is slightly weighted towards GDP growth so we can slightly adjust the values for these and recalcultate gdp per capita using this. 

# freight_transport_population_parameter = 0.9
# passenger_transport_population_parameter = 1.1
# freight_transport_gdp_parameter = 1.1
# passenger_transport_gdp_parameter = 0.9

# new_macro = macro.copy()
# new_macro['freight_GDP_per_capita'] = (new_macro['GDP'] * freight_transport_gdp_parameter) / (new_macro['Population'] * freight_transport_population_parameter)

#join together passenger and frieght growth rates

#save the new macro data






##################################################################################################











# %%
#try taking in energy use for transport from these ecoinomys balance tables. We have this data form the ESTO team:
#\transport_data_system\intermediate_data\EGEDA\EGEDA_transport_outputDATE20230215.csv
#load it in
energy_use = pd.read_csv(root_dir + '\\' + 'D:\\APERC\\transport_data_system\\intermediate_data\\EGEDA\\EGEDA_transport_outputDATE20230215.csv')

#take in egeda_industry_output from same place as egeda_transport
egeda_industry_output = pd.read_csv(root_dir + '\\' + 'D:\\APERC\\transport_data_system\\intermediate_data\\EGEDA\\egeda_industry_outputDATE20230522.csv')
#now do the same cleaning process

#cols: ['Economy', 'Fuel_Type', 'Date', 'Value', 'Transport Type', 'Frequency','Unit', 'Source', 'Dataset', 'Measure', 'Vehicle Type', 'Drive','Medium'],
#get unique vlaues for each col
# energy_use['Economy'].unique()
# energy_use['Fuel_Type'].unique()
#array(['1.2 Other bituminous coal', '7.01 Motor gasoline',
#    '7.02 Aviation gasoline', '7.05 Kerosene type jet fuel',
#    '7.07 Gas/diesel oil', '7.08 Fuel oil', '7.09 LPG',
#    '17 Electricity', '19 Total', '21 Modern renewables',
#    '7.04 Gasoline type jet fuel', '8.1 Natural gas', '7.06 Kerosene',
#    '1.3 Sub-bituminous coal', '2.1 Coke oven coke',
#    '7.12 White spirit SBP', '7.14 Bitumen', '1.1 Coking coal',
#    '1.4 Anthracite', '1.5 Lignite', '6.1 Crude oil', '3 Peat',
#    '2.3 Coke oven gas', '8.3 Gas works gas', '16.5 Biogasoline',
#    '20 Total Renewables', '2.8 BKB/PB', '16.6 Biodiesel',
#    '7.13 Lubricants', '6.2 Natural gas liquids',
#    '7.17 Other products'], dtype=object)
# energy_use['Date'].min()#'1980-12-31'
# energy_use['Date'].max()#'2020-12-31'
# energy_use['Medium'].unique()#array([nan, 'rail', 'road', 'air', 'ship', 'pipeline', 'nonspecified'],
#   dtype=object)


#TRANSPORT EGEDA
#LETS DO A FULL ANALYSIS OF HOW ENERGY USE IS CORRELATED WITH THE GROWTH RATES LIEK ABOVE, SINCE WE HAVE ENEGRY USE FOR HISTORICAL DATA.
#we will just grab '19 Total' for now
energy_use = energy_use[energy_use['Fuel_Type'] == '19 Total']
#double check that the sum of medium=nan is equal to the sum of all the other mediums
# energy_use[energy_use['Medium'].isna()]['Value'].sum() == energy_use[energy_use['Medium'].notna()]['Value'].sum()#True
#filter for medium = nan
# energy_use = energy_use[energy_use['Medium'].isna()]
#rename where medium = nan to 'Total'
energy_use.loc[energy_use['Medium'].isna(), 'Medium'] = 'Total'
#drop nonneeded cols
energy_use = energy_use.drop(columns=['Fuel_Type', 'Frequency', 'Source', 'Dataset', 'Measure', 'Vehicle Type', 'Drive'])
#pivot so we have a column for each medium
energy_use = energy_use.pivot(index=['Economy', 'Date'], columns='Medium', values='Value').reset_index()
#while we are analysing medium we shjould also not aggregate into reigons, as certain economys focus on certain mediums more

#INDUSTRY EGEDA
#we will just grab '19 Total' for now
egeda_industry_output = egeda_industry_output[egeda_industry_output['Fuel_Type'] == '19 Total']
#drop nonneeded cols
egeda_industry_output = egeda_industry_output.drop(columns=['Fuel_Type'])
#call value industry_energy_use
egeda_industry_output = egeda_industry_output.rename(columns={'Value': 'Industry'})

#JOIN TRANSPORT AND INDUSTRY EGEDA
#join together
energy_use = energy_use.merge(egeda_industry_output, left_on=['Economy', 'Date'], right_on=['Economy', 'Date'], how='inner')

#while we are analysing medium we shjould also not aggregate into reigons, as certain economys focus on certain mediums more
#make all cols lowercase
energy_use.columns = energy_use.columns.str.lower()
#reformat date to be in year only
energy_use['date'] = energy_use['date'].apply(lambda x: x[:4])
#make into int
energy_use['date'] = energy_use['date'].astype(int)
#%%
##########################################
#%%
#do same for macro
new_macro=macro.copy()
new_macro.columns = new_macro.columns.str.lower()

#join together
energy_macro = energy_use.merge(new_macro, left_on=['economy', 'date'], right_on=['economy', 'date'], how='inner')

#calculaqte a test value that is GDP * Population. this might be better than gdp/population
energy_macro['gdp_times_capita'] = energy_macro['gdp'] * energy_macro['population']
#%%
# Make sure data is sorted by year
energy_macro = energy_macro.sort_values('date')

# Calculate growth rates for each column except date and economy
for col in energy_macro.columns:
    if col not in ['date', 'economy']:
        
        energy_macro[col + ' Growth Rate'] = energy_macro.groupby('economy')[col].pct_change()
        #growth rates arent veryt interesting to look at, instead calcualte df['Cumulative Growth'] = (1 + df['Growth Rate']).cumprod() - 1
        #thing is though, these will be made difficult to analyse by nas
        energy_macro[col + ' Cumulative Growth'] = (1 + energy_macro[col + ' Growth Rate'])
        energy_macro[col + ' Cumulative Growth'] = energy_macro.groupby('economy')[col + ' Cumulative Growth'].cumprod(skipna=True)

#%%
# Remove the first year (since it has no growth rate)
energy_macro = energy_macro[energy_macro['date'] != energy_macro['date'].min()]

#redo above plot but plot by region so we have bigger graphs.
#import  reigonal mappigns from 'D:\APERC\transport_model_9th_edition\config\concordances_and_config_data\region_economy_mapping.csv'
region_mappings = pd.read_csv(root_dir + '\\' + 'D:\\APERC\\transport_model_9th_edition\\config\\concordances_and_config_data\\region_economy_mapping.csv')
# region_mappings 	Economy	Region	Region_growth_analysis
#so join on region
energy_macro_r_old = energy_macro.merge(region_mappings, left_on='economy', right_on='Economy', how='inner')
#we want to remove any cols with nan if they are based on medium, then remove any rows with nan if they are based on macro. BUT we want to do this by economy
mediums = ['total', 'air','rail', 'road', 'ship', 'pipeline', 'nonspecified', 'industry']
macros = ['gdp', 'population', 'gdp_per_capita','gdp_times_capita']
#new df
energy_macro_r = pd.DataFrame()
#first remove cols with nan
for economy in energy_macro_r_old.Economy.unique():
    #grab just the economy
    energy_macro_e = energy_macro_r_old[energy_macro_r_old['Economy'] == economy]
    for col in energy_macro_e.columns:
        for medium in mediums:
            if medium == 'total':
                continue
            if medium in col:
                if energy_macro_e[col].isna().sum() > 0:
                    print('Dropping ' + col + ' because there are ' + str(energy_macro_e[col].isna().sum()) + ' missing values')
                    energy_macro_e = energy_macro_e.drop(columns=[col])
                break
        for macro in macros:
            if macro in col:
                if energy_macro_e[col].isna().sum() > 0:
                    print('Dropping rows for ' + col + ' because there are ' + str(energy_macro_e[col].isna().sum()) + ' missing values')
                    energy_macro_e = energy_macro_e.dropna(subset=[col])
                break
    #now add to new df
    energy_macro_r = pd.concat([energy_macro_r, energy_macro_e], ignore_index=True)


#then iterate through regions
plot_this = False
plot_all_mediums=False
if plot_this:
    for region in region_mappings.Region_growth_analysis.unique():
        
        energy_macro_melt = energy_macro_r[energy_macro_r['Region_growth_analysis'] == region]
        #drop Region, Economy and Region_growth_analysis cpls
        energy_macro_melt = energy_macro_melt.drop(columns=['Region', 'Economy', 'Region_growth_analysis'])
        #melt all, but keep date and economy
        energy_macro_melt = energy_macro_melt.melt(id_vars=['economy', 'date'])
        if not plot_all_mediums:
            #drop all mediums except total and road
            medium_values_to_remove = [value for value in energy_macro_melt['variable'].unique() if any(x in value for x in mediums) and not any(x in value for x in ['total', 'road', 'industry'])]
            energy_macro_melt = energy_macro_melt[~energy_macro_melt['variable'].isin(medium_values_to_remove)]
        #filter so variable only contains vlauyes with Growth Rate in it
        energy_macro_melt = energy_macro_melt[energy_macro_melt['variable'].str.contains('Cumulative Growth')]
        #create col to inidciate if it is a medium or macro
        medium_values = [value for value in energy_macro_melt['variable'].unique() if any(x in value for x in mediums)]
        energy_macro_melt['type'] = energy_macro_melt['variable'].apply(lambda x: 'medium' if x in medium_values else 'macro')

        title = 'Energy Use Cumulative growth vs Macro Cumulative growth for ' + region
        #plot with type as the dash
        fig = px.line(energy_macro_melt, x='date', y='value', color='variable', facet_col='economy', line_dash='type', facet_col_wrap=3, title=title)

        #save to html
        fig.write_html(root_dir + '\\' + 'plotting_output\\input_analysis\\regions\\energy_use_cumulative_growth_vs_macro_growth_cumulative' + region + '.html')

        # #and plot correlation df
        # title = 'Correlation Between Energy Use Cumulative growth and Cumulative growth Rate for ' + region
        # fig2 = px.scatter(correlation_df_r[correlation_df_r['Region_growth_analysis'] == region], x='Medium', y='Macro', color='Correlation', facet_col='Economy', facet_col_wrap=3, title=title)

        # #save to html
        # fig2.write_html(root_dir + '\\' + 'plotting_output\\input_analysis\\regions\\correlation_between_energy_use_cumulative_growth_rate_and_macro_growth_cumulative_' + region + '.html')
        

#%%


#################################################
#################################################


from scipy.stats import pearsonr

# Calculate correlation between each medium and each macro variable
#we will do it by economy as well
mediums = ['total', 'air','rail', 'road', 'ship', 'nonspecified', 'pipeline', 'industry']
macros = ['gdp', 'population', 'gdp_per_capita','gdp_times_capita']
correlation_df = pd.DataFrame(columns=['Medium', 'Macro', 'Correlation', 'P-Value', 'Economy'])
for medium in mediums:
    for macro in macros:
        for economy in energy_macro['economy'].unique():
            #if there are nas in either of the columns, then the correlation will be nan, so as long as there are not more than 10 missing vlaues we will calculate the correlation
            #ACTUALLY WE WILL JUST DROP ANY COLS WITH NA, BECAUSE THEY MAKE IT TOO DIFFICULT TO ANALYSE
            #that is, unless the na is in a macro variable, in which case we drop the rows with na (because the na's will be at the start of the df, rtahter than in the middle)
            economy_df = energy_macro[energy_macro['economy'] == economy]
            if economy_df[medium + ' Growth Rate'].isna().sum() > 0 and (medium != 'total'):
                print('Not enough data for ' + economy + ' for ' + medium + ' and ' + macro + 'because there are ' + str(economy_df[medium + ' Growth Rate'].isna().sum()) + ' missing values in ' + medium)
            elif economy_df[macro + ' Growth Rate'].isna().sum() > 0:
                print('Not enough data for ' + economy + ' for ' + medium + ' and ' + macro + 'because there are ' + str(economy_df[macro + ' Growth Rate'].isna().sum()) + ' missing values in ' + macro)
            else:
                #drop infs 
                economy_df = economy_df.replace([np.inf, -np.inf], np.nan)
                #drop rows wiuth na
                economy_df = economy_df.dropna(subset=[medium + ' Growth Rate', macro + ' Growth Rate'])
                correlation, _ = pearsonr(economy_df[medium + ' Growth Rate'], economy_df[macro + ' Growth Rate'])
                #roudn to 2 dp
                correlation = round(correlation, 2)
                _ = round(_, 2)
                print('The correlation between ' + medium + ' and ' + macro + ' for ' + economy + ' is ' + str(correlation))
                #add as a row to df using pd.concat
                new_row = pd.DataFrame([[medium, macro, correlation, _, economy]], columns=['Medium', 'Macro', 'Correlation', 'P-Value', 'Economy'])
                correlation_df = pd.concat([correlation_df, new_row], ignore_index=True)
#%%
#do the same as above but for Cumulative Growth to see if it is more correlated

# Calculate correlation between each medium and each macro variable
#we will do it by economy as well
mediums = ['total', 'air','rail', 'road', 'ship', 'nonspecified', 'pipeline','industry']
macros = ['gdp', 'population', 'gdp_per_capita','gdp_times_capita']
correlation_df_cumulative = pd.DataFrame(columns=['Medium', 'Macro', 'Correlation', 'P-Value', 'Economy'])
for medium in mediums:
    for macro in macros:
        for economy in energy_macro['economy'].unique():
            #if there are nas in either of the columns, then the correlation will be nan, so as long as there are not more than 10 missing vlaues we will calculate the correlation
            economy_df = energy_macro[energy_macro['economy'] == economy]
            if (economy_df[medium + ' Cumulative Growth'].isna().sum() >  0) and (medium != 'total'):
                print('Not enough data for ' + economy + ' for ' + medium + ' and ' + macro + 'because there are ' + str(economy_df[medium + ' Cumulative Growth'].isna().sum()) + ' missing values in ' + medium)
            elif economy_df[macro + ' Cumulative Growth'].isna().sum() > 0:
                print('Not enough data for ' + economy + ' for ' + medium + ' and ' + macro + 'because there are ' + str(economy_df[macro + ' Cumulative Growth'].isna().sum()) + ' missing values in ' + macro)
            else:
                #drop infs 
                economy_df = economy_df.replace([np.inf, -np.inf], np.nan)
                #drop rows wiuth na
                economy_df = economy_df.dropna(subset=[medium + ' Cumulative Growth', macro + ' Cumulative Growth'])
                correlation, _ = pearsonr(economy_df[medium + ' Cumulative Growth'], economy_df[macro + ' Cumulative Growth'])
                #roudn to 2 dp
                correlation = round(correlation, 2)
                _ = round(_, 2)
                print('The correlation between ' + medium + ' and ' + macro + ' for ' + economy + ' is ' + str(correlation))
                #add as a row to df using pd.concat
                new_row = pd.DataFrame([[medium, macro, correlation, _, economy]], columns=['Medium', 'Macro', 'Correlation', 'P-Value', 'Economy'])
                correlation_df_cumulative = pd.concat([correlation_df_cumulative, new_row], ignore_index=True)


correlation_df_r = correlation_df.merge(region_mappings, left_on='Economy', right_on='Economy', how='inner')
# %%
plot_this = False
if plot_this:
    #attempt heatmap from chatgpt:
    import plotly.express as px

    # Assume your DataFrame is named correlation_df
    economies = correlation_df['Economy'].unique()

    for economy in economies:
        # Create a pivot table for each economy
        pivot_table = correlation_df[correlation_df['Economy'] == economy].pivot('Macro', 'Medium', 'Correlation')

        # Create a heatmap for each pivot table
        fig = px.imshow(pivot_table,
                        labels=dict(x="Medium", y="Macro", color="Correlation"),
                        title='Correlation Heatmap for ' + economy)
        #save to html   
        fig.write_html(root_dir + '\\' + 'plotting_output\\input_analysis\\economies\\correlation_heatmap_' + economy + '.html')
# %%
plot_this = False
if plot_this:
    #attempt heatmap from chatgpt:
    import plotly.express as px

    # Assume your DataFrame is named correlation_df
    economies = correlation_df_cumulative['Economy'].unique()

    for economy in economies:
        # Create a pivot table for each economy
        pivot_table = correlation_df_cumulative[correlation_df_cumulative['Economy'] == economy].pivot('Macro', 'Medium', 'Correlation')

        # Create a heatmap for each pivot table
        fig = px.imshow(pivot_table,
                        labels=dict(x="Medium", y="Macro", color="Correlation"),
                        title='Correlation Heatmap for ' + economy)
        #save to html   
        fig.write_html(root_dir + '\\' + 'plotting_output\\input_analysis\\economies\\correlation_heatmap_' + economy + '.html')