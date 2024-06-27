#%%
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
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import LassoCV
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import RidgeCV
import statsmodels.api as sm

standardize_growth_coefficients_dict = {'lasso': True, 'linear': False, 'ridge': True}
drop_outliers = True
#%%



#%%
#%%
def prepare_comparison_inputs(growth_coefficients_df, energy_macro, BASE_YEAR_activity_9th, activity_growth_8th, activity_8th,independent_variables, models):
    growth_coefficients_df_copy = growth_coefficients_df.copy()
    energy_macro_copy = energy_macro.copy()
    BASE_YEAR_activity_9th_copy = BASE_YEAR_activity_9th.copy()
    activity_growth_8th_copy = activity_growth_8th.copy()
    activity_8th_copy = activity_8th.copy()
    independent_variables_copy = independent_variables.copy()
    models_copy = models.copy()
    #do teh oppostie now:
    copy= True
    if copy:
        growth_coefficients_df= growth_coefficients_df_copy.copy()
        energy_macro= energy_macro_copy.copy()
        BASE_YEAR_activity_9th= BASE_YEAR_activity_9th_copy.copy()
        activity_growth_8th= activity_growth_8th_copy.copy()
        activity_8th= activity_8th_copy.copy()
        independent_variables= independent_variables_copy.copy()
        models= models_copy.copy()
    useful_macro_vars = ['Population', 'Gdp', 'Gdp_per_capita', 'Gdp_times_capita', 'Gdp_growth', 'Population_growth', 'Gdp_per_capita_growth', 'Gdp_times_capita_growth']
    #if any if those vars arent in energy_macro then drop them
    for useful_macro_var in useful_macro_vars:
        if useful_macro_var not in energy_macro.columns:
            useful_macro_vars.remove(useful_macro_var)
    
    measures_to_index = ['passenger_activity_8th', 'freight_activity_8th','passenger_activity_growth_8th', 'freight_activity_growth_8th'] + useful_macro_vars
    #combine all dfs
    df = pd.merge(BASE_YEAR_activity_9th, activity_growth_8th, on=['Economy', 'Date'], how='outer')
    df = pd.merge(df, activity_8th, on=['Economy', 'Date'], how='left')
    df = pd.merge(df, energy_macro[['Economy', 'Date'] + independent_variables], on=['Economy', 'Date'], how='outer')
    df = pd.merge(df, growth_coefficients_df, on=['Economy'], how='outer')
    #also join on some macro variables we might want in case they werent in independent variables:
    for variable in useful_macro_vars:
        if variable not in independent_variables:
            df = pd.merge(df, energy_macro[['Economy', 'Date', variable]], on=['Economy', 'Date'], how='outer')
    ########        
    #now we need to calculate the activity growth estimate for each model for each year. We will create a separate col for each model for each  independent varaible and for each coefficient. Then we will apply the coefficients to the independent variables and sum them to get the activity growth estimate for each model for each year.
    #prepare columns:
    #extract the coeffcieints and independent variable columns plus index_cols, then create a new df for each model with the named columns. then remerge them all together
    #get the columns we will be using:
    id_coeff =[independent_variable+'_coeff' for independent_variable in independent_variables]
    
    coefficients_and_independent_variables_df = df[['Economy', 'Date', 'Model','const'] + independent_variables + id_coeff].drop_duplicates()
    df = df.drop(columns=id_coeff+independent_variables+['r2','alpha', 'const', 'Model']).drop_duplicates()
    for model in models:
        model_df = coefficients_and_independent_variables_df.copy()
        model_df = model_df[model_df['Model'] == model]
        #drop model
        model_df = model_df.drop(columns=['Model'])
        
        model_df.rename(columns={independent_variable+'_coeff': independent_variable+'_'+model+'_coeff' for independent_variable in independent_variables}, inplace=True)
        model_df.rename(columns={independent_variable: independent_variable+'_'+model for independent_variable in independent_variables}, inplace=True)
        model_df.rename(columns={'const': 'const_'+model}, inplace=True)
        
        df = pd.merge(df, model_df, on=['Economy', 'Date'], how='outer')
    
    #and readd the indepenedent variables back in, since they were dropped in the previous step and will be useful in plotting:
    df = pd.merge(df, energy_macro[['Economy', 'Date'] + independent_variables], on=['Economy', 'Date'], how='outer')
    
    #calcualte activity growth:
    #take in activity from input data for 9th edition and calcualte the resulting activity growth for the modelling years using the new growth coefficients for every model. depending on the model might need to standardize the input data first:
    for model in models:
        df['activity_growth_estimate_'+model] = df['const_'+model]#dont think this needs to be standardized
        if standardize_growth_coefficients_dict[model]:
            # Initialize a scaler
            scaler = StandardScaler()
            standardised_vars = [independent_variable+'_'+model for independent_variable in independent_variables]
            # Scale X
            df[standardised_vars] = scaler.fit_transform(df[standardised_vars])
        for independent_variable in independent_variables:
            df[f'activity_growth_estimate_'+model] = df['activity_growth_estimate_'+model] + df[independent_variable+'_'+model] * df[independent_variable+'_'+model + '_coeff']
            #add it to the measures to index:
            measures_to_index += [f'activity_growth_estimate_'+model]
    ########
    
    #now calcaulte the activity per year using the activity growth and the BASE YEAR activity from the 8th edition and 9th edition:
    #sort by economy and date:
    df = df.sort_values(by=['Economy', 'Date'])
    
    for model in models:
        for edition in ['8th', '9th']:
            for year in range(config.DEFAULT_BASE_YEAR, config.END_YEAR+1):
                if (year>2050) and (edition == '8th'):
                    break
                for transport_type in ['freight', 'passenger']:
                    activity_column = f'{transport_type}_activity_{edition}_{model}'
                    #if not already there add it to the measures to index:
                    if activity_column not in measures_to_index:
                        measures_to_index = measures_to_index + [activity_column]
                    for economy in df['Economy'].unique():#doing this makes it a bit easier to visualise. but it takes longer.
                        df_economy = df[df['Economy'] == economy]
                        df = df[df['Economy'] != economy]
                        if year == config.DEFAULT_BASE_YEAR:
                            # prepare the base year data by creatinng a new col for the activity:
                            df_economy.loc[df_economy['Date'] == year, activity_column] = df_economy.loc[df_economy['Date'] == year, f'{transport_type}_activity_{edition}']
                            
                        else:    
                            
                            # Calculate the new activity by doing growth times previoous years activity + previous years activity
                            df_economy.loc[df_economy['Date'] == year, activity_column] = (df_economy.loc[df_economy['Date'] == year-1, activity_column].values[0] * df_economy.loc[df_economy['Date'] == year, 'activity_growth_estimate_'+model]) + df_economy.loc[df_economy['Date'] == year-1, activity_column].values[0]
                        df = pd.concat([df, df_economy])

    #pivot using the model column so we have the activity growth for each 
    #now index everything to the base year so we can see how it all grows:
    def calc_index(df, col):
        df = df.sort_values(by='Date')
        BASE_YEAR_value = df[df.Date == config.DEFAULT_BASE_YEAR][col].iloc[0]
        df[col+'_index'] = df[col]/BASE_YEAR_value
        return df    
    
    for measure_to_index in measures_to_index:
        df = calc_index(df, measure_to_index)
    indexed_measures_to_plot = [measure_to_index + '_index' for measure_to_index in measures_to_index]
    
    measures_to_plot = measures_to_index
    return df, measures_to_plot, indexed_measures_to_plot

#now plot the results:
def plot_and_compare_new_growth_coefficients(GROWTH_MEASURES_TO_PLOT, ACTIVITY_MEASURES_TO_PLOT):
    #LOAD DATA:
    with open('intermediate_data/growth_analysis/measures_to_plot.txt', 'r') as f:
        measures_to_plot = [line.rstrip() for line in f]
        
    with open('intermediate_data/growth_analysis/indexed_measures_to_plot.txt', 'r') as f:
        indexed_measures_to_plot = [line.rstrip() for line in f]
    df = pd.read_pickle('intermediate_data/growth_analysis/df_growth_parameter_analysis.pkl')
    
    #PLOT:
    #do this for the measures to plot and the indexed measures to plot:
    #plot a line graph for each economy using plotly express
    for economy in df['Economy'].unique():
        df_economy = df[df['Economy'] == economy]
        title = f'{economy} - activity growth using new growth coefficients'
        fig = px.line(df_economy, x='Date', y=measures_to_plot, title=title)
        #write to html
        fig.write_html(f'plotting_output/growth_analysis/{title}.html')
        
        #and plot for the indexed measures:
        title = f'{economy} - indexed activity growth using new growth coefficients'
        fig = px.line(df_economy, x='Date', y=indexed_measures_to_plot, title=title)
        #write to html
        fig.write_html(f'plotting_output/growth_analysis/{title}.html')
    
        #and plot for hand picked measure using MEASURES_TO_PLOT:
        title = f'{economy} chosen growth measures'
        #  Economy	Date 
        fig = px.line(df_economy, x='Date', y=GROWTH_MEASURES_TO_PLOT, title=title)
        fig.write_html(f'plotting_output/growth_analysis/{title}.html')
        
        title = f'{economy} chosen activity measures'
        fig = px.line(df_economy, x='Date', y=ACTIVITY_MEASURES_TO_PLOT, title=title)
        fig.write_html(f'plotting_output/growth_analysis/{title}.html')
    
    #PLOT GROWTH_MEASURES_TO_PLOT AND ACTIVITY_MEASURES_TO_PLOT FOR ALL ECONOMIES IN ONE PLOT USING FACETS
    title = f'chosen growth measures for all economies'
    fig = px.line(df, x='Date', y=GROWTH_MEASURES_TO_PLOT, facet_col='Economy', facet_col_wrap=7, title=title)
    fig.write_html(f'plotting_output/growth_analysis/{title}.html')
    
    title = f'chosen activity measures for all economies'
    fig = px.line(df, x='Date', y=ACTIVITY_MEASURES_TO_PLOT, facet_col='Economy', facet_col_wrap=7, title=title)
    fig.write_html(f'plotting_output/growth_analysis/{title}.html')
    
       

#%%
########################
# MODEL FITTING
########################


#%%
def remove_outliers(df, column):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1

    df_out = df[~((df[column] < (Q1 - 1.5 * IQR)) | (df[column] > (Q3 + 1.5 * IQR)))]
    
    return df_out

def fit_lasso_regression(X, Y, alphas= [0.001, 0.01, 0.1, 1, 10, 100]):
    # Add a constant (intercept term) to the independent variables
    X = sm.add_constant(X)

    # Initialize a scaler
    scaler = StandardScaler()
    
    # Scale X
    X_scaled = scaler.fit_transform(X)

    # Fit the model
    model = LassoCV(alphas=alphas)
    model.fit(X_scaled, Y)

    # Create a dictionary of coefficients
    coefficients = dict(zip(X.columns, model.coef_))
    #add '_coeff' to the end of each coefficient name
    coefficients = {k+'_coeff': v for k, v in coefficients.items() if k != 'const'}
    
    coefficients['const'] = model.intercept_
    coefficients['r2'] = model.score(X_scaled, Y)
    coefficients['alpha'] = model.alpha_
    
    # The alpha parameter selected by cross-validation
    print('Optimal alpha selected for lasso CV:', model.alpha_)
    
    return coefficients

def fit_linear_regression(X, Y):
    independent_variables = X.columns.tolist()
    # Add a constant (intercept term) to the independent variables
    X = sm.add_constant(X)
    
    # Initialize a scaler
    scaler = StandardScaler()#not necessary but since it is done in the lasso regression, I will do it here too for simplicity
    
    # Scale X
    X_scaled = scaler.fit_transform(X)
    
    # Fit the model
    model = sm.OLS(Y, X_scaled)
    results = model.fit()

    # Create a dictionary of coefficients
    coefficients = dict(results.params)
    coefficients['r2'] = results.rsquared

    coefficients = map_coefficients_to_variable_names(coefficients, independent_variables)
    return coefficients

    
    
def fit_ridge_regression(X, Y, alphas= [0.001, 0.01, 0.1, 1, 10, 100]):
    
    #add '_coeff' to the end of each coefficient name
    coeff_cols = [x+'_coeff' for x in X.columns if x != 'const']
    
    # Add a constant (intercept term) to the independent variables
    X = sm.add_constant(X)

    # Initialize a scaler
    scaler = StandardScaler()
    # Scale X
    X_scaled = scaler.fit_transform(X)
    
    # Fit the model
    model = RidgeCV(alphas=alphas)
    model.fit(X_scaled, Y)
    
    # Create a dictionary of coefficients   
    coefficients = dict(zip(['const'] + coeff_cols, np.concatenate([model.intercept_.reshape(-1), model.coef_])))
    
    # Calculate R-squared value
    y_pred = model.predict(X_scaled)
    SS_Residual = sum((Y-y_pred)**2)       
    SS_Total = sum((Y-np.mean(Y))**2)     
    r_squared = 1 - (float(SS_Residual))/SS_Total

    coefficients['r2'] = r_squared
    coefficients['alpha'] = model.alpha_
    # The alpha parameter selected by cross-validation
    print('Optimal alpha selected for ridge CV:', model.alpha_)
    
    return coefficients

def map_coefficients_to_variable_names(coefficients, independent_variables):
    # Create a copy of coefficients to not modify the original one
    coefficients_copy = coefficients.copy()

    # Loop through keys in the copy of coefficients
    for key in coefficients_copy.keys():
        if key.startswith('x'):
            # Get the index
            i = int(key[1:])
            
            # Create a new key
            new_key = independent_variables[i-1] + '_coeff'
            
            # Create a new entry in the coefficients dictionary and remove the old one
            coefficients[new_key] = coefficients.pop(key)

    return coefficients

def find_growth_coefficients(df, independent_variables,dependent_variable, models):
    independent_variables_coeff_named = [x+'_coeff' for x in independent_variables]
    columns= ['Region', 'const','alpha', 'r2', 'Model']+independent_variables_coeff_named
    growth_coefficients_df = pd.DataFrame(columns=columns)
    
    for region in df.Region.unique():
        region_df = df[df['Region'] == region]
        variables_df = region_df[independent_variables + [dependent_variable]].dropna()
        independent_variables_df = variables_df[independent_variables]
        dependent_variables_df = variables_df[dependent_variable]
        
        if drop_outliers:
            outliers_df = pd.merge(independent_variables_df, dependent_variables_df, left_index=True, right_index=True)
            for col in independent_variables + [dependent_variable]:
                outliers_df = remove_outliers(outliers_df, col)
            independent_variables_df = outliers_df[independent_variables]
            dependent_variables_df = outliers_df[dependent_variable]
        for MODEL in models:
            if MODEL == 'linear':
                coefficients = fit_linear_regression(independent_variables_df, dependent_variables_df)  # or fit_lasso_regression(X, Y, alpha=0.1)
                coefficients['alpha'] = 0
                coefficients['Region'] = region
                coefficients['Model'] = 'linear'
                growth_coefficients_df = pd.concat([growth_coefficients_df, pd.DataFrame([coefficients], columns=columns)])

                
            elif MODEL == 'lasso':
                
                coefficients = fit_lasso_regression(independent_variables_df, dependent_variables_df)  # or fit_lasso_regression(X, Y, alpha=0.1)
                
                coefficients['Region'] = region
                coefficients['Model'] = 'lasso'
                growth_coefficients_df = pd.concat([growth_coefficients_df, pd.DataFrame([coefficients], columns=columns)])
            
            elif MODEL == 'ridge':
                coefficients = fit_ridge_regression(independent_variables_df, dependent_variables_df)
                coefficients['Region'] = region
                coefficients['Model'] = 'ridge'
                growth_coefficients_df = pd.concat([growth_coefficients_df, pd.DataFrame([coefficients], columns=columns)])
            
            else:
                raise ValueError(f'Unknown model type: {MODEL}')

    return growth_coefficients_df

#%%
#########################################################
# PLOTTING
#########################################################
def plot_growth_coefficients(growth_coefficients_df, independent_variables):
    #plot all growth coefficients on a bar chart with facets for economys and x as the coefficients
    independent_variables_coeff = [x+'_coeff' for x in independent_variables]
    growth_coefficients_df_melt = pd.melt(growth_coefficients_df, id_vars=['Region','r2','alpha', 'Model'], value_vars=['const']+independent_variables_coeff)
    # for region in growth_coefficients_df.Region.unique():
    for model in growth_coefficients_df.Model.unique():
        model_data = growth_coefficients_df_melt[growth_coefficients_df_melt['Model'] == model]
        
        #CREATE TITLE
        # extract r2, alpha values and make them part of the title
        title = f'{model} - Coeffs for growth vs energy growth<br>'

        r2 = {region: growth_coefficients_df[growth_coefficients_df['Region'] == region]['r2'].iloc[0].round(2) for region in growth_coefficients_df.Region.unique()}
        alpha = {region: growth_coefficients_df[growth_coefficients_df['Region'] == region]['alpha'].iloc[0] for region in growth_coefficients_df.Region.unique()}

        # Add these to the title
        for region in growth_coefficients_df.Region.unique():
            title += f'<br>{region} - R2: {r2[region]}, Alpha: {alpha[region]}'
        
        #CREATE PLOT
        fig = px.bar(model_data, x = 'variable', y = 'value', color = 'variable', facet_col='Region', barmode='group', title=title)
        
        #save
        fig.write_html(f'plotting_output/growth_analysis/{model}_growth_coefficients.html')
        
##########################################
#FORMATTING
##########################################
#%%

def macro_formatting(macro):
    new_macro = macro.copy()
    #make all cols start with capital letter
    new_macro.columns = [x.capitalize() for x in new_macro.columns]
    #DROP UNIT COLUMN
    new_macro = new_macro.drop(columns=['Units'])
    #pivot so each measure in the vairable column is its own column.
    new_macro = new_macro.pivot(index=['Economy_code', 'Economy', 'Year'], columns='Variable', values='Value').reset_index()
    # macro.columns#Index(['economy_code', 'Economy', 'Date', 'real_GDP', 'GDP_per_capita', 'population'], dtype='object', name='variable')

    # #cahnge real_GDP to GDP for brevity (we dont use the actual values anyway(just growth rates)) and some other stuff:
    new_macro = new_macro.drop(columns=['Economy'])
    new_macro = new_macro.rename(columns={'real_GDP':'Gdp', 'Economy_code':'Economy', 'Year':'Date', 'population':'Population', 'GDP_per_capita':'Gdp_per_capita'})
    return new_macro

def APERC_energy_formatting(energy_use):
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
    energy_use = energy_use.drop(columns=['Fuel_Type', 'Frequency', 'Source', 'Dataset', 'Measure', 'Vehicle Type', 'Drive', 'Transport Type'])
    #pivot so we have a column for each medium
    energy_use = energy_use.pivot(index=['Economy', 'Date'], columns='Medium', values='Value').reset_index()
    #while we are analysing medium we shjould also not aggregate into reigons, as certain economys focus on certain mediums more

    #reformat date to be in year only
    energy_use['Date'] = energy_use['Date'].apply(lambda x: x[:4])
    #make into int
    energy_use['Date'] = energy_use['Date'].astype(int)
    return energy_use

def merge_macro_and_energy(macro, energy_use):
    #do same for macro
    new_macro=macro.copy()

    #join together
    energy_macro = energy_use.merge(new_macro, left_on=['Economy', 'Date'], right_on=['Economy', 'Date'], how='outer')

    #calculaqte a test value that is GDP * Population. this might be better than gdp/population
    energy_macro['Gdp_times_capita'] = energy_macro['Gdp'] * energy_macro['Population']
    # Make sure data is sorted by year
    energy_macro = energy_macro.sort_values('Date')
    return energy_macro

def caculate_growth_rates(energy_macro):
    # Calculate growth rates for each column except date and economy
    for col in energy_macro.columns:
        if col not in ['Date', 'Economy']:
            
            energy_macro[col + '_growth'] = energy_macro.groupby('Economy')[col].pct_change()
            #set 0s to nan
            energy_macro[col + '_growth'] = energy_macro[col + '_growth'].replace(0, np.nan)
            #growth rates arent veryt interesting to look at, instead calcualte df['Cumulative Growth'] = (df['_growth']).cumprod() - 1
            #thing is though, these will be made difficult to analyse by nas
            energy_macro[col + '_cum_growth'] = (energy_macro[col + '_growth'])
            energy_macro[col + '_cum_growth'] = energy_macro.groupby('Economy')[col + '_cum_growth'].cumprod(skipna=True)
            
    # Remove the first year (since it has no growth rate)
    energy_macro = energy_macro[energy_macro['Date'] != energy_macro['Date'].min()]
    
    return energy_macro


def group_by_region(energy_macro, region_column = 'Region_growth_regression2'):
    #lets try grouping the economys by regions (based on georgaphy and economic development) and then running the regression on each region. LAter on it would probably be a good idea to look into ato's urban density data and stuff
    regional_mapping = pd.read_csv('config/concordances_and_config_data/region_economy_mapping.csv')
    #extract Region_growth_regression and Economy
    regional_mapping = regional_mapping[[region_column, 'Economy']]
    #make economyt lowercase
    regional_mapping.rename(columns={'Economy':'Economy',region_column:'Region'}, inplace=True)
    
    #join to regional mapping
    df = pd.merge(energy_macro, regional_mapping, on='Economy', how='inner')

    return df


def format_8th_edition_data(activity_8th):
    #filter for only Reference sicne both scenarios have the same activity growth
    activity_8th = activity_8th[activity_8th['Scenario']=='Reference']
    #drop non specified from transport type
    activity_8th = activity_8th[activity_8th['Transport Type']!='nonspecified']
    #rename year to Date
    activity_8th = activity_8th.rename(columns={'Year':'Date'})
    #filter for only the columns we need
    activity_8th = activity_8th[['Date', 'Economy', 'Transport Type','Activity']].groupby(['Date', 'Economy', 'Transport Type']).sum().reset_index()
    #drop Economy == 00_APEC
    activity_8th = activity_8th[activity_8th['Economy']!='00_APEC']
    activity_growth_8th = calculate_activity_growth_8th(activity_8th)
    activity_8th = import_activity_8th(activity_8th)
    return activity_growth_8th, activity_8th

def calculate_activity_growth_8th(activity_8th):
    
    #now calcualte pct change for each year
    activity_growth_8th = activity_8th.sort_values(['Transport Type','Economy', 'Date'])
    activity_growth_8th['Activity_growth'] = activity_growth_8th.groupby(['Transport Type','Economy'])['Activity'].pct_change()
    #drop activity column
    activity_growth_8th = activity_growth_8th.drop(columns=['Activity'])
    
    #pivot the transport type column to make it into columns
    activity_growth_8th = activity_growth_8th.pivot_table(index=['Date', 'Economy'], columns='Transport Type', values='Activity_growth').reset_index()
    #rename the columns form passneger and freight to passenger_activity_growth_8th and freight_activity_growth_8th
    activity_growth_8th = activity_growth_8th.rename(columns={'passenger':'passenger_activity_growth_8th', 'freight':'freight_activity_growth_8th'})
    
    return activity_growth_8th
    
def import_activity_8th(activity_8th):
    #pivot the transport type column to make it into columns
    activity_8th = activity_8th.pivot_table(index=['Economy', 'Date'], columns='Transport Type', values='Activity').reset_index()
    #reanme the columns to passenger_activity_9th and freight_activity_9th
    activity_8th = activity_8th.rename(columns={'passenger':'passenger_activity_8th', 'freight':'freight_activity_8th'})
    return activity_8th
    
def import_BASE_YEAR_activity_9th(BASE_YEAR_activity):
    #filter for Activity only
    BASE_YEAR_activity = BASE_YEAR_activity[BASE_YEAR_activity['Measure']=='Activity']
    #filter for config.DEFAULT_BASE_YEAR only
    BASE_YEAR_activity = BASE_YEAR_activity[BASE_YEAR_activity['Date']==config.DEFAULT_BASE_YEAR]
    #divide activity by 1billion to get on same scale as 8th edition
    BASE_YEAR_activity['Value'] = BASE_YEAR_activity['Value']/1000000000
    
    #fitler for cols we need only
    BASE_YEAR_activity = BASE_YEAR_activity[['Economy', 'Transport Type',  'Date', 'Value']].groupby(['Economy', 'Transport Type', 'Date']).sum().reset_index()
    #pivot the transport type column to make it into columns
    BASE_YEAR_activity = BASE_YEAR_activity.pivot_table(index=['Economy', 'Date'], columns='Transport Type', values='Value').reset_index()
    #reanme the columns to passenger_activity_9th and freight_activity_9th
    BASE_YEAR_activity = BASE_YEAR_activity.rename(columns={'passenger':'passenger_activity_9th', 'freight':'freight_activity_9th'})
    
    return BASE_YEAR_activity
# %%
