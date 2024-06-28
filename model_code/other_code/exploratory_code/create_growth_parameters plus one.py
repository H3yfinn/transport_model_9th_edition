# %%
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
root_dir = re.split('transport_model_9th_edition', script_dir)[0] + 'transport_model_9th_edition'
if __name__ == "__main__": #this allows the script to be run directly or from the main.py file as you cannot use relative imports when running a script directly
    # Modify sys.path to include the directory where utility_functions is located
    sys.path.append(f"{root_dir}/code")
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
macro = pd.read_csv(root_dir + '/' + 'D:/APERC/transport_model_9th_edition/input_data/macro/APEC_GDP_population.csv')
#pull in activity_growth 
activity_growth = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/activity_growth.csv')
# macro.columns#Index(['economy_code', 'economy', 'date', 'variable', 'value'], dtype='object')
#pivot so each measure in the vairable column is its own column.
macro = macro.pivot_table(index=['economy_code', 'economy', 'year'], columns='variable', values='value').reset_index()
# macro.columns#Index(['economy_code', 'economy', 'date', 'real_GDP', 'GDP_per_capita', 'population'], dtype='object', name='variable')
#%%
#cahnge real_GDP to GDP for brevity (we dont use the actual values anyway(just growth rates)) and some other stuff:
macro = macro.drop(columns=['economy'])
macro = macro.rename(columns={'real_GDP':'GDP', 'population':'Population', 'economy_code':'economy', 'year':'date'})
#%%

# %%
#try taking in energy use for transport from these ecoinomys balance tables. We have this data form the ESTO team:
#\transport_data_system\intermediate_data\EGEDA\EGEDA_transport_outputDATE20230215.csv
#load it in
energy_use = pd.read_csv(root_dir + '/' + 'D:/APERC/transport_data_system/intermediate_data/EGEDA/EGEDA_transport_outputDATE20230215.csv')


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
        
        energy_macro[col + ' Growth Rate'] = energy_macro.groupby('economy')[col].pct_change()+1
        #growth rates arent veryt interesting to look at, instead calcualte df['Cumulative Growth'] = (df['Growth Rate']).cumprod() - 1
        #thing is though, these will be made difficult to analyse by nas
        energy_macro[col + ' Cumulative Growth'] = (energy_macro[col + ' Growth Rate'])
        energy_macro[col + ' Cumulative Growth'] = energy_macro.groupby('economy')[col + ' Cumulative Growth'].cumprod(skipna=True)

#%%
# Remove the first year (since it has no growth rate)
energy_macro = energy_macro[energy_macro['date'] != energy_macro['date'].min()]

#%%
# energy_macro.columns
# Index(['economy', 'date', 'total', 'air', 'nonspecified', 'pipeline', 'rail',
#    'road', 'ship', 'industry', 'gdp_per_capita', 'population', 'gdp',
#    'gdp_times_capita', 'total Growth Rate', 'total Cumulative Growth',
#    'air Growth Rate', 'air Cumulative Growth', 'nonspecified Growth Rate',
#    'nonspecified Cumulative Growth', 'pipeline Growth Rate',
#    'pipeline Cumulative Growth', 'rail Growth Rate',
#    'rail Cumulative Growth', 'road Growth Rate', 'road Cumulative Growth',
#    'ship Growth Rate', 'ship Cumulative Growth', 'industry Growth Rate',
#    'industry Cumulative Growth', 'gdp_per_capita Growth Rate',
#    'gdp_per_capita Cumulative Growth', 'population Growth Rate',
#    'population Cumulative Growth', 'gdp Growth Rate',
#    'gdp Cumulative Growth', 'gdp_times_capita Growth Rate',
#    'gdp_times_capita Cumulative Growth'],

#OKAY. BASICALLY IT SEEMS THAT THE CORRELATION IS PRETTY CLEAR, OF COURSE. BUT THERE ARE SOME DIFFERENCES WHICH DONT SEEM TO BE BASED ON WHETHER AN ECONOMY IS DEVELOPING OR NOT: THE CORRELATION  BETWEEN GDP/ENERGY VS GDP_PER_CAPITA/ENERGY IS DIFFERENT FOR DIFFERENT ECONOMIES. FOR EXAMPLE, NZ IS MORE CORRELATED WITH GDP, BUT AUS IS MORE CORRELATED WITH GDP_PER_CAPITA. ITS NOT CLEAR WHAT IS CAUSING THE DIFFERENCE. HAVE LOOKED AT THINGS LIKE: EFFECT OF POPULATION GROWTH RATE ON GDP PER CPITA. 
#COULD BE BECAUSE OF RELATIVE EFFICIENCY LEVELS COMING FROM THE INDUSTRY MIX. LIKE MAYBE HTERE IS A CORRELATION BETWEEN ENERGY USE IN INDUSTRY AND ENERGY USE IN TRANSPORT?
#PERHAPS ITS ENOUGH JUST TO TAKE IT AS IT IS AND SLIGHTLY CHANGE THE WEIGHTING OF THE MACRO VARIABLES DEPENDING ON THE ECONOMY? This can be done by using a regression analysis to find the best weights for each economy.

#%%
#i want to create a functionised version of the regression analysis done above so i dont have to repeat it for each variable
from sklearn.linear_model import LinearRegression
import statsmodels.api as sm
def regression_analysis(df, x, y, drop_outliers=False):
    #drop rows with na
    df = df.dropna()

    # Assume you have a DataFrame df with 'independent_variable1', 'independent_variable2' and 'dependent_variable'
    X = df[x]
    Y = df[y]

    if drop_outliers:
        def drop_outliers(X, Y, x, y):
            #join together X and Y
            df = X.merge(Y, left_index=True, right_index=True)
            if isinstance(x, list):
                for i in x:
                    #do the Local Outlier Factor (LOF) method
                    Q1 = df[i].quantile(0.25)
                    Q3 = df[i].quantile(0.75)
                    IQR = Q3 - Q1

                    # only keep rows in the dataframe that do not have outliers in any column
                    df = df[~((df[i] < (Q1 - 1.5 * IQR)) |(df[i] > (Q3 + 1.5 * IQR)))]
            else:
                #do the Local Outlier Factor (LOF) method
                Q1 = df[x].quantile(0.25)
                Q3 = df[x].quantile(0.75)
                IQR = Q3 - Q1

                # only keep rows in the dataframe that do not have outliers in any column
                df = df[~((df[x] < (Q1 - 1.5 * IQR)) |(df[x] > (Q3 + 1.5 * IQR)))]
            return df[x], df[y]
        X, Y = drop_outliers(X, Y, x, y)
                

    # Add a constant (intercept term) to the independent variables
    X = sm.add_constant(X)

    # Fit the model
    model = sm.OLS(Y, X)
    results = model.fit()

    # Print out the statistics
    #print out the names of the variables
    print('Regression analysis for {} and {}'.format(x,y))
    print(results.summary())
    return results,model, X,Y

import plotly.graph_objects as go
def plot_regression_results(results,model, x_values, y_values, df, x, y,plot_name,add_one=True,log_x=False):
    #if x is list, then it is a multiple regression
    if isinstance(x, list):
        if len(x) > 2:
            regression_type = 'multiple_plus'#we will plot each variabl;e against the dependent variable on a different facet
        else:
            regression_type = 'multiple'
    else:
        regression_type = 'simple'
    
    # Create the prediction plane/line
    if regression_type == 'multiple':
        x_pred = np.linspace(df[x[0]].min(), df[x[0]].max(), 10)
        y_pred = np.linspace(df[x[1]].min(), df[x[1]].max(), 10)
        xx_pred, yy_pred = np.meshgrid(x_pred, y_pred)
        model_viz = np.array([xx_pred.flatten(), yy_pred.flatten()]).T
        model_viz = sm.add_constant(model_viz)
        predicted = results.predict(exog=model_viz)
        zz_pred = predicted.reshape(xx_pred.shape)
    elif regression_type == 'simple':
        x_pred = np.linspace(df[x].min(), df[x].max(), 10)
        model_viz = sm.add_constant(x_pred)
        predicted = results.predict(exog=model_viz)
        y_pred = predicted.reshape(x_pred.shape)
    else:
        multiple_plus_df = pd.DataFrame()
        for x_var in x:
            #put the variable into dataframe with cols: independent_var_name, independent_var_value, dependent_var_value

            new_df_values = pd.DataFrame()
            new_df_values['independent_var_value'] = x_values[x_var]
            new_df_values['dependent_var_value'] = y_values
            new_df_values['independent_var_name'] = x_var

            multiple_plus_df = pd.concat([multiple_plus_df,new_df_values])
                


    # Creating the scatter plot
    if regression_type == 'multiple':
        fig = go.Figure(data=[go.Scatter3d(
            x=df[x[0]],
            y=df[x[1]],
            z=df[y],
            mode='markers',
            marker=dict(
                size=4,
                color='blue',
                opacity=0.8
            )
        )])
    elif regression_type == 'simple':
        fig = go.Figure(data=[go.Scatter(
            x=df[x],
            y=df[y],
            mode='markers',
            marker=dict(
                size=4,
                color='blue',
                opacity=0.8
            )
        )])
    elif regression_type == 'multiple_plus':
        #plot using express
        # if there are negative x vlaues then dont use log scale
        if log_x:
            if add_one and (multiple_plus_df['independent_var_value'].min() < 0):
                multiple_plus_df['independent_var_value'] = multiple_plus_df['independent_var_value'] + 1
                multiple_plus_df['dependent_var_value'] = multiple_plus_df['dependent_var_value'] + 1
                fig = px.scatter(multiple_plus_df, x="independent_var_value", y="dependent_var_value", facet_col="independent_var_name", trendline="ols", log_x=True)
                fig.update_layout(title_text=plot_name)
            else:
                fig = px.scatter(multiple_plus_df, x="independent_var_value", y="dependent_var_value", facet_col="independent_var_name", trendline="ols", log_x=True)
                fig.update_layout(title_text=plot_name)
        else:
            fig = px.scatter(multiple_plus_df, x="independent_var_value", y="dependent_var_value", facet_col="independent_var_name", trendline="ols", log_x= False)
            fig.update_layout(title_text=plot_name)

        #save the plot
        fig.write_html(root_dir + '/' + 'plotting_output/growth_analysis/macro_regression_final/{}.html'.format(plot_name))
        return

    # Adding the plane of best fit to the figure
    if regression_type == 'multiple':
        fig.add_trace(go.Surface(x=x_pred, y=y_pred, z=zz_pred, name='Predicted Plane'))
    elif regression_type == 'simple':
        fig.add_trace(go.Scatter(x=x_pred, y=y_pred, name='Predicted Line'))

    # Set labels
    if regression_type == 'multiple':
        fig.update_layout(scene = dict(
                            xaxis_title=x[0],
                            yaxis_title=x[1],
                            zaxis_title=y),
                            width=700,
                            margin=dict(r=20, b=10, l=10, t=10))
    elif regression_type == 'simple':
        fig.update_layout(xaxis_title=x,
                            yaxis_title=y,
                            width=700,
                            margin=dict(r=20, b=10, l=10, t=10))
        
    #save the plot
    fig.write_html(root_dir + '/' + 'plotting_output/growth_analysis/macro_regression_final/{}.html'.format(plot_name))
    


# %%
#i think we actually want to try find the relation between 'growth' in energy and growth in gdp/population. So we need to do a regression on the growth rates.
df = energy_macro[['economy', 'date', 'total Growth Rate','road Growth Rate', 'gdp Growth Rate', 'population Growth Rate', 'gdp_per_capita Growth Rate', 'gdp_times_capita Growth Rate', 'total','road', 'gdp', 'population', 'gdp_per_capita', 'gdp_times_capita']]
df.rename(columns={'total': 'energy_total', 'road': 'energy_road', 'gdp Growth Rate': 'gdp_growth', 'population Growth Rate': 'population_growth', 'gdp_per_capita Growth Rate': 'gdp_per_capita_growth', 'gdp_times_capita Growth Rate': 'gdp_times_capita_growth', 'total Growth Rate': 'energy_total_growth', 'road Growth Rate': 'energy_road_growth'}, inplace=True)
#%%
#
analyse = False
if analyse:
    # df = df[df['economy'] == '07_INA']
    for economy in df.economy.unique():
        economy_df = df[df['economy'] == economy]
        independent_variables = ['gdp_per_capita_growth', 'gdp_times_capita_growth', 'gdp_growth', 'population_growth']
        dependent_variable = 'energy_total_growth'

        plot_regression_results(regression_analysis(economy_df, independent_variables, dependent_variable), economy_df, independent_variables, dependent_variable, '{}_regression_macro_growth_vs_energy_total_growth'.format(economy))
        
        independent_variables = ['gdp_per_capita', 'gdp_times_capita', 'gdp', 'population']
        dependent_variable = 'energy_total'

        plot_regression_results(regression_analysis(economy_df, independent_variables, dependent_variable), economy_df, independent_variables, dependent_variable, '{}_regression_macro_vs_energy_total'.format(economy))

        independent_variables = ['gdp_per_capita_growth', 'gdp_times_capita_growth', 'gdp_growth']
        dependent_variable = 'energy_total_growth'

        plot_regression_results(regression_analysis(economy_df, independent_variables, dependent_variable), economy_df, independent_variables, dependent_variable, '{}_regression_macro_growth_vs_energy_total_growth_no_pop'.format(economy))

# %%
#Looks like ['gdp_per_capita_growth', 'gdp_times_capita_growth', 'gdp_growth'] is best when you look at the graphs themselves, even if the r2 is lower. So lets do that for all economies.
growth_coefficients_df = pd.DataFrame(columns=['economy', 'const', 'gdp_per_capita_growth', 'gdp_times_capita_growth', 'gdp_growth', 'r2'])
for economy in df.economy.unique():
    economy_df = df[df['economy'] == economy]
    independent_variables = ['gdp_per_capita_growth', 'gdp_times_capita_growth', 'gdp_growth']
    dependent_variable = 'energy_total_growth'
    results,model, x_values, y_values = regression_analysis(economy_df, independent_variables, dependent_variable, drop_outliers=True)
    plot_regression_results(results,model, x_values, y_values, economy_df, independent_variables, dependent_variable, '{}_regression_macro_growth_vs_energy_total_growth_no_pop'.format(economy))
    #extract coefficients from model
    coefficients = results.params
    #save coefficients to df
    growth_coefficients_df = growth_coefficients_df.append({'economy': economy, 'const': coefficients[0], 'gdp_per_capita_growth': coefficients[1], 'gdp_times_capita_growth': coefficients[2], 'gdp_growth': coefficients[3], 'r2': results.rsquared}, ignore_index=True)
# %%
#save to csv
growth_coefficients_df.to_csv(root_dir + '/' + 'plotting_output/growth_analysis/macro_regression_final/growth_coefficients.csv')
#plot all growth coefficients on a bar chart with facets for economys and x as the coefficients
#melt
growth_coefficients_df_melt = pd.melt(growth_coefficients_df, id_vars=['economy', 'r2'], value_vars=['const', 'gdp_per_capita_growth', 'gdp_times_capita_growth', 'gdp_growth'])
#plot
fig = px.bar(growth_coefficients_df_melt, x = 'variable', y = 'value', color = 'economy', facet_col = 'economy', facet_col_wrap=3, barmode='group', title='Macro regression coefficients for growth vs energy total growth')
#save
fig.write_html(root_dir + '/' + 'plotting_output/growth_analysis/macro_regression_final/growth_coefficients.html')
    
#%%
###########################################################################
###########################################################################

#double check that these coefficients work well with activity growth using the 8th edition activity growth as a comparison. 
#load in the activity growth data
#pull in activity_growth 
activity_growth = pd.read_csv(root_dir + '/' + 'intermediate_data/model_inputs/activity_growth.csv')
#make activity growth columns into lowercase
activity_growth.columns = [x.lower() for x in activity_growth.columns]
#drop scenario col and filter out duplicates
activity_growth = activity_growth.drop(columns=['scenario']).drop_duplicates()

#pull in forecasted growth rates:
macro = pd.read_csv(root_dir + '/' + 'D:/APERC/transport_model_9th_edition/input_data/macro/APEC_GDP_population.csv')
# macro.columns#Index(['economy_code', 'economy', 'date', 'variable', 'value'], dtype='object')
#pivot so each measure in the vairable column is its own column.
macro = macro.pivot_table(index=['economy_code', 'economy', 'year'], columns='variable', values='value').reset_index()
# macro.columns#Index(['economy_code', 'economy', 'date', 'real_GDP', 'GDP_per_capita', 'population'], dtype='object', name='variable')
#cahnge real_GDP to GDP for brevity (we dont use the actual values anyway(just growth rates)) and some other stuff:
macro = macro.drop(columns=['economy'])
macro = macro.rename(columns={'real_GDP':'gdp', 'economy_code':'economy', 'year':'date', 'GDP_per_capita':'gdp_per_capita'})
macro = macro.sort_values(by=['economy', 'date'])
#calc gdp_times_capitaq
macro['gdp_times_capita'] = macro['gdp'] * macro['gdp_per_capita']
macro['gdp_times_capita_growth'] = macro.groupby('economy')['gdp_times_capita'].pct_change()+1
macro['gdp_growth'] = macro.groupby('economy')['gdp'].pct_change() +1
macro['population_growth'] = macro.groupby('economy')['population'].pct_change()+1
macro['gdp_per_capita_growth'] = macro.groupby('economy')['gdp_per_capita'].pct_change()+1
#remove na rows
macro = macro.dropna()

#%%
#combine it with above data using a merge
#rename coefficients cols
growth_coefficients_df.rename(columns={'economy': 'economy', 'const': 'const', 'gdp_per_capita_growth': 'gdp_per_capita_growth_coeff', 'gdp_times_capita_growth': 'gdp_times_capita_growth_coeff', 'gdp_growth': 'gdp_growth_coeff', 'r2': 'r2'}, inplace=True)

activity_macro_energy_coefficients = pd.merge(growth_coefficients_df, activity_growth, on=['economy'], how='left')
activity_macro_energy_coefficients = pd.merge(activity_macro_energy_coefficients, df[['economy', 'date', 'energy_total_growth']], on=['economy', 'date'], how='left')
activity_macro_energy_coefficients = pd.merge(activity_macro_energy_coefficients, macro[['economy', 'date', 'gdp_growth', 'population_growth', 'gdp_per_capita_growth','gdp_times_capita_growth']], on=['economy', 'date'], how='left')
#times the coefficients by the macro variables to get the activity growth and then convert to cumulative growth then compare it on a line graph with the actual activity growth. 
activity_macro_energy_coefficients['activity_growth_estimate'] = activity_macro_energy_coefficients['const'] + activity_macro_energy_coefficients['gdp_per_capita_growth_coeff'] * activity_macro_energy_coefficients['gdp_per_capita_growth'] + activity_macro_energy_coefficients['gdp_times_capita_growth_coeff'] * activity_macro_energy_coefficients['gdp_times_capita_growth'] + activity_macro_energy_coefficients['gdp_growth'] * activity_macro_energy_coefficients['gdp_growth_coeff']
activity_macro_energy_coefficients['activity_growth_estimate_cumulative'] = (activity_macro_energy_coefficients['activity_growth_estimate']).groupby(activity_macro_energy_coefficients['economy']).cumprod()
activity_macro_energy_coefficients['activity_growth_cumulative'] = (activity_macro_energy_coefficients['activity_growth']).groupby(activity_macro_energy_coefficients['economy']).cumprod()

# #index it to be in terms of the other indexes 
# activity_macro_energy_coefficients['activity_growth_estimate_cumulative_index'] = activity_macro_energy_coefficients['activity_growth_estimate_cumulative'] / activity_macro_energy_coefficients['activity_growth_estimate_cumulative'].iloc[0]
# activity_macro_energy_coefficients['activity_growth_cumulative_index'] = activity_macro_energy_coefficients['activity_growth_cumulative'] / activity_macro_energy_coefficients['activity_growth_cumulative'].iloc[0]
#####

#%%
plot_this = True
if plot_this:
    # #plot these as line graphs using plotly
    # #filter out the columns we want
    # macro1 = activity_macro_energy_coefficients[['economy', 'date', 'activity_growth_estimate_cumulative_index', 'activity_growth_cumulative_index']]
    # #first melt
    # activity_macro_energy_coefficients_melt = activity_macro_energy_coefficients.melt(id_vars=['economy', 'date'], value_vars=['activity_growth_estimate_cumulative_index', 'activity_growth_cumulative_index'], var_name='variable', value_name='value')
    # #then plot
    # import plotly.express as px
    # fig = px.line(activity_macro_energy_coefficients_melt, x='date', y='value', color='variable', facet_col='economy', facet_col_wrap=3)
    # #name y axis as an indexed
    # fig.update_yaxes(title_text='Index (base date = {}'.format(macro1['date'].min()))
    # #save to plotting_output\growth_analysis
    # fig.write_html(root_dir + '/' + 'plotting_output/growth_analysis/macro_regression_final/activity_8th_vs_regression_growth_indexes.html')

    macro1 = activity_macro_energy_coefficients[['economy', 'date', 'activity_growth_estimate_cumulative', 'activity_growth_cumulative']]

    macro1_melt = macro1.melt(id_vars=['economy', 'date'], value_vars=['activity_growth_estimate_cumulative', 'activity_growth_cumulative'], var_name='variable', value_name='value')
    #then plot
    import plotly.express as px
    fig = px.line(macro1_melt, x='date', y='value', color='variable', facet_col='economy', facet_col_wrap=3)
    #save to plotting_output\growth_analysis
    fig.write_html(root_dir + '/' + 'plotting_output/growth_analysis/macro_regression_final/activity_8th_vs_regression_growth.html')
#%%
# %%

#plot gdp per capita vs energy use on a single graph
analyse = True
if analyse == True:
    energy_gdp_per_capita = pd.merge(energy_use[['economy', 'date','total']], macro[['economy', 'date','gdp_per_capita']], on=['economy', 'date'], how='inner')
    #index all gdp per cpita anmd total energy use by each economys first date
    energy_gdp_per_capita['gdp_per_capita_index'] = energy_gdp_per_capita['gdp_per_capita'] / energy_gdp_per_capita.groupby('economy')['gdp_per_capita'].transform('first')
    energy_gdp_per_capita['total_index'] = energy_gdp_per_capita['total'] / energy_gdp_per_capita.groupby('economy')['total'].transform('first')
    #plot   
    import plotly.express as px
    fig = px.scatter(energy_gdp_per_capita, x='gdp_per_capita', y='total', color='economy', trendline='ols', log_x=True, log_y=True)
    fig.write_html(root_dir + '/' + 'plotting_output/growth_analysis/macro_regression_final/energy_vs_gdp_per_capita.html', auto_open=True)

    import plotly.express as px
    fig = px.scatter(energy_gdp_per_capita, x='gdp_per_capita_index', y='total_index', color='economy', trendline='ols', log_x=True, log_y=True)
    fig.write_html(root_dir + '/' + 'plotting_output/growth_analysis/macro_regression_final/energy_vs_gdp_per_capita_index.html', auto_open=True)

# %%



#lets try grouping the economys by regions (based on georgaphy and economic development) and then running the regression on each region. LAter on it would probably be a good idea to look into ato's urban density data and stuff
regional_mapping = pd.read_csv(root_dir + '/' + 'config/concordances_and_config_data/region_economy_mapping.csv')
#extract Region_growth_regression and Economy
regional_mapping = regional_mapping[['Region_growth_regression', 'Economy']]
#make economyt lowercase
regional_mapping.rename(columns={'Economy':'economy','Region_growth_regression':'region'}, inplace=True)

#first thing we'll try is using all the growth rates and doing the regression on each region to find coefficients for each region
#%%
#test putting USA in low density
regional_mapping.loc[regional_mapping['region'] == 'PNG', 'region'] = 'Developed_low_density'

# %%
#i think we actually want to try find the relation between 'growth' in energy and growth in gdp/population. So we need to do a regression on the growth rates.
df = energy_macro[['economy', 'date', 'total Growth Rate','road Growth Rate', 'gdp Growth Rate', 'population Growth Rate', 'gdp_per_capita Growth Rate', 'gdp_times_capita Growth Rate', 'total','road', 'gdp', 'population', 'gdp_per_capita', 'gdp_times_capita']]
df.rename(columns={'total': 'energy_total', 'road': 'energy_road', 'gdp Growth Rate': 'gdp_growth', 'population Growth Rate': 'population_growth', 'gdp_per_capita Growth Rate': 'gdp_per_capita_growth', 'gdp_times_capita Growth Rate': 'gdp_times_capita_growth', 'total Growth Rate': 'energy_total_growth', 'road Growth Rate': 'energy_road_growth'}, inplace=True)

#join to regional mapping
df = pd.merge(df, regional_mapping, on='economy', how='inner')

# %%
#Looks like ['gdp_per_capita_growth', 'gdp_times_capita_growth', 'gdp_growth'] is best when you look at the graphs themselves, even if the r2 is lower. So lets do that for all economies.
independent_variables =['gdp_per_capita_growth', 'gdp_times_capita_growth']#'gdp_per_capita_growth'# 
if independent_variables == ['gdp_per_capita_growth', 'gdp_times_capita_growth', 'gdp_growth']:

    growth_coefficients_df = pd.DataFrame(columns=['region', 'const', 'gdp_per_capita_growth', 'gdp_times_capita_growth', 'gdp_growth', 'r2'])
    for economy in df.region.unique():
        economy_df = df[df['region'] == economy]
        
        dependent_variable = 'energy_total_growth'
        results,model, x_values, y_values = regression_analysis(economy_df, independent_variables, dependent_variable, drop_outliers=True)
        plot_regression_results(results,model, x_values, y_values, economy_df, independent_variables, dependent_variable, '{}_regression_macro_growth_vs_energy_total_growth_no_pop'.format(economy))
        #extract coefficients from model
        coefficients = results.params
        #save coefficients to df
        growth_coefficients_df = growth_coefficients_df.append({'region': economy, 'const': coefficients[0], 'gdp_per_capita_growth': coefficients[1], 'gdp_times_capita_growth': coefficients[2], 'gdp_growth': coefficients[3], 'r2': results.rsquared}, ignore_index=True)
    #save to csv
    growth_coefficients_df.to_csv(root_dir + '/' + 'plotting_output/growth_analysis/macro_regression_final/growth_coefficients_by_region.csv')
    #plot all growth coefficients on a bar chart with facets for economys and x as the coefficients
    #melt
    growth_coefficients_df_melt = pd.melt(growth_coefficients_df, id_vars=['region', 'r2'], value_vars=['const', 'gdp_per_capita_growth', 'gdp_times_capita_growth', 'gdp_growth'])
    #plot
    fig = px.bar(growth_coefficients_df_melt, x = 'variable', y = 'value', color = 'region', facet_col = 'region', facet_col_wrap=3, barmode='group', title='Macro regression coefficients for growth vs energy total growth')
    #save
    fig.write_html(root_dir + '/' + 'plotting_output/growth_analysis/macro_regression_final/growth_coefficients_by_region.html')

elif independent_variables == ['gdp_per_capita_growth', 'gdp_times_capita_growth']:
    #replace PNG in regions wqith Developed_low_density
    df['region'].replace({'PNG': 'Developed_low_density'}, inplace=True)
    #change all the Developed_low_density to Low_density
    df['region'].replace({'Developed_low_density': 'Low_density'}, inplace=True)
    growth_coefficients_df = pd.DataFrame(columns=['region', 'const', 'gdp_per_capita_growth', 'gdp_times_capita_growth', 'r2'])
    for economy in df.region.unique():
        economy_df = df[df['region'] == economy]
        independent_variables = ['gdp_per_capita_growth', 'gdp_times_capita_growth']
        dependent_variable = 'energy_total_growth'
        results,model, x_values, y_values = regression_analysis(economy_df, independent_variables, dependent_variable, drop_outliers=True)
        plot_regression_results(results,model, x_values, y_values, economy_df, independent_variables, dependent_variable, '{}_regression_macro_growth_vs_energy_total_growth_no_pop'.format(economy))
        #extract coefficients from model
        coefficients = results.params
        #save coefficients to df
        growth_coefficients_df = growth_coefficients_df.append({'region': economy, 'const': coefficients[0], 'gdp_per_capita_growth': coefficients[1], 'gdp_times_capita_growth': coefficients[2], 'r2': results.rsquared}, ignore_index=True)
            #save to csv
    growth_coefficients_df.to_csv(root_dir + '/' + 'plotting_output/growth_analysis/macro_regression_final/growth_coefficients_by_region.csv')
    #plot all growth coefficients on a bar chart with facets for economys and x as the coefficients
    #melt
    growth_coefficients_df_melt = pd.melt(growth_coefficients_df, id_vars=['region', 'r2'], value_vars=['const', 'gdp_per_capita_growth', 'gdp_times_capita_growth'])
    #plot
    fig = px.bar(growth_coefficients_df_melt, x = 'variable', y = 'value', color = 'region', facet_col = 'region', facet_col_wrap=3, barmode='group', title='Macro regression coefficients for growth vs energy total growth')
    #save
    fig.write_html(root_dir + '/' + 'plotting_output/growth_analysis/macro_regression_final/growth_coefficients_by_region.html')

elif independent_variables == 'gdp_per_capita_growth':
    growth_coefficients_df = pd.DataFrame(columns=['region', 'const', 'gdp_per_capita_growth', 'r2'])
    for economy in df.region.unique():
        economy_df = df[df['region'] == economy]
        independent_variables = 'gdp_per_capita_growth'
        dependent_variable = 'energy_total_growth'
        results,model, x_values, y_values = regression_analysis(economy_df, independent_variables, dependent_variable, drop_outliers=False)
        plot_regression_results(results,model, x_values, y_values, economy_df, independent_variables, dependent_variable, '{}_regression_macro_growth_vs_energy_total_growth_no_pop'.format(economy))
        #extract coefficients from model
        coefficients = results.params
        #save coefficients to df
        growth_coefficients_df = growth_coefficients_df.append({'region': economy, 'const': coefficients[0], 'gdp_per_capita_growth': coefficients[1], 'r2': results.rsquared}, ignore_index=True)
            #save to csv
    growth_coefficients_df.to_csv(root_dir + '/' + 'plotting_output/growth_analysis/macro_regression_final/growth_coefficients_by_region.csv')
    #plot all growth coefficients on a bar chart with facets for economys and x as the coefficients
    #melt
    growth_coefficients_df_melt = pd.melt(growth_coefficients_df, id_vars=['region', 'r2'], value_vars=['const', 'gdp_per_capita_growth'])
    #plot
    fig = px.bar(growth_coefficients_df_melt, x = 'variable', y = 'value', color = 'region', facet_col = 'region', facet_col_wrap=3, barmode='group', title='Macro regression coefficients for growth vs energy total growth')
    #save
    fig.write_html(root_dir + '/' + 'plotting_output/growth_analysis/macro_regression_final/growth_coefficients_by_region.html')

# %%
#this is jsut quick might ahve to do it again.
#convert PNG to Developed_low_density so we can join it to the growth_coeff table
regional_mapping.loc[regional_mapping['region'] == 'PNG', 'region'] = 'Developed_low_density'
#convert where region = Low_density to Developed_low_density
growth_coefficients_df.loc[growth_coefficients_df['region'] == 'Low_density', 'region'] = 'Developed_low_density'
##join to regional mapping
growth_coefficients_df = pd.merge(growth_coefficients_df, regional_mapping, on='region', how='outer')
#convert region to Low_density since it now includes PNG
growth_coefficients_df.loc[growth_coefficients_df['region'] == 'Developed_low_density', 'region'] = 'Low_density'

# #join back on economys
# growth_coefficients_df = growth_coefficients_df.merge(regional_mapping, on='region', how='left')
#resave
growth_coefficients_df.to_csv(root_dir + '/' + 'input_data/growth_coefficients_by_region.csv', index=False)
# %%
#lets just  use the output for['gdp_per_capita_growth', 'gdp_times_capita_growth']. I think its thebest. but png is a bit weird so i put it in with developed low density to create Low_density
#currenlty i think the coefficients graph is the most useful. it shows how low density economies are different to the rest because they have a larger coefficient for gdp per capita growth, which is what youd expect when an ecnonmys opoulation has to drive further
#you can load the ocefficients via 'plotting_output/growth_analysis/macro_regression_final/growth_coefficients_by_region.csv'
# %%
