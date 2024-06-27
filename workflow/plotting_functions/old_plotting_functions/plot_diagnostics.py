#take in detailed output data and print out any useful metrics/statisitcs to summarise the reults of the model. the intention is that the output willbe easy to view through the command line, and that the output will be saved to a file for later viewing.

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
import sys
sys.path.append("./config")
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
import plotly.express as px
import plotly.graph_objects as go
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook
import matplotlib.pyplot as plt
plt.rcParams['figure.facecolor'] = 'w'

save_html=True
save_fig=False
#%%

#load data in
model_output_all = pd.read_csv('output_data/model_output/{}'.format(config.model_output_file_name))
model_output_detailed = pd.read_csv('output_data/model_output_detailed/{}'.format(config.model_output_file_name))
# gompertz_function_diagnostics_dataframe = pd.read_csv('intermediate_data/road_model/{}'.format(gompertz_function_diagnostics_dataframe_file_name))

model_output_8th = pd.read_csv('intermediate_data/activity_energy_road_stocks.csv')
#%%
#load in growth estimates and related data:
# macro1.to_csv('intermediate_data/model_inputs/regression_based_growth_estimates.csv', index=False)
regression_based_growth_estimates = pd.read_csv('intermediate_data/model_inputs/regression_based_growth_estimates.csv')
#drop unit
regression_based_growth_estimates = regression_based_growth_estimates.drop(columns=['Unit']).drop_duplicates()
#make wide
regression_based_growth_estimates = regression_based_growth_estimates.pivot(index=['Economy','Transport Type',	'Scenario', 'Date'], columns='Measure', values='Value').reset_index()
#Index(['economy', 'date', 'Gdp_per_capita', 'Population', 'GDP',
#    'GDP_times_capita', 'GDP_growth', 'Population_growth',
#    'Gdp_per_capita_growth', 'GDP_times_capita_growth', 'region', 'const',
#    'Gdp_per_capita_growth_coeff', 'gdp_times_capita_growth_coeff', 'r2',
#    'energy_growth_est', 'Activity_growth', 'activity_growth_8th',
#    'activity_growth_8th_index', 'activity_growth_est_index',
#    'energy_growth_est_index'],
#   dtype='object')
#%%


#%%
################################################################################################################################################################

#plot data from the gompertz_function_diagnostics_dataframe. this contians the columns: 'Economy','Scenario', 'Drive', 'Vehicle Type', 'Transport Type', 'Date', 'Stocks_per_thousand_capita', 'Expected_Gdp_per_capita', 'Gdp_per_capita','Expected_stocks_per_thousand_capita_derivative', 'Activity_growth_adjusted', 'Activity_growth','Mileage_growth_adjusted', 'Mielage_growth', 'Mileage', 'Expected_stocks_per_thousand_capita', 
# Note that the below vars have been temproarily or permanently dropped
# 'Expected_Gdp_per_capita', 
# 'Expected_stocks_per_thousand_capita_2', 'Expected_stocks_per_thousand_capita_derivative_2'
#we will plot these all, but provide the option to plot only the most important ones
#first we will plot:
#scatter of the stocks per capita (y) and Gdp_per_capita (x) for each economy and each year
#overlay of a line showing the stocks per capita (y) and Expected_Gdp_per_capita (x) for each economy and scenario and each year. It might eb that this line is too messy though.

################################
#%%
################################################################################################################################################################
# Drop nas in regression_based_growth_estimates so we are calculating compound growth rates for the same time period as the 8th edition data
regression_based_growth_estimates = regression_based_growth_estimates.dropna(subset=['Activity_growth_8th', 'Activity_growth', 'Energy_growth_est'])

# Calculate the growth rates compounded over time to compare to the 8th edition data:
regression_based_growth_estimates['Activity_growth_est_index'] = regression_based_growth_estimates.groupby(['Transport Type','Scenario','Economy'])['Activity_growth'].apply(lambda x: (1 + x).cumprod())
regression_based_growth_estimates['Energy_growth_est_index'] = regression_based_growth_estimates.groupby(['Transport Type','Scenario','Economy'])['Energy_growth_est'].apply(lambda x: (1 + x).cumprod())
regression_based_growth_estimates['Gdp_times_capita_growth_index'] = regression_based_growth_estimates.groupby(['Transport Type','Scenario','Economy'])['Gdp_times_capita_growth'].apply(lambda x: (1 + x).cumprod())
regression_based_growth_estimates['Gdp_per_capita_growth_index'] = regression_based_growth_estimates.groupby(['Transport Type','Scenario','Economy'])['Gdp_per_capita_growth'].apply(lambda x: (1 + x).cumprod())

# Plot, with economies as facets, the 'Activity_growth_8th_index', 'Activity_growth_est_index', ''Energy_growth_est_index' and 'GDP_times_capita_growth_index' and 'Gdp_per_capita_growth_index'
title = 'Growth estimates for each economy'
regression_based_growth_estimates_long = pd.melt(regression_based_growth_estimates, id_vars=['Transport Type','Scenario','Economy', 'Date'], value_vars=['Activity_growth_8th_index', 'Activity_growth_est_index', 'Energy_growth_est_index', 'Gdp_times_capita_growth_index', 'Gdp_per_capita_growth_index'], var_name='Variable', value_name='Value')

# Plot with plotly
fig = px.line(regression_based_growth_estimates_long, x='Date', y='Value', color='Variable', facet_col='Economy', facet_col_wrap=3, title=title)

# Save html
if save_html:
    fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))

# Save fig
if save_fig:
    fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))



#%%
#FILTER FOR SCENARIO OF INTEREST
#this should be temporary as the scenario should be passed in as a parameter through config if it is useed elsewhere
config.SCENARIO_OF_INTEREST = 'Reference'
model_output_all = model_output_all[model_output_all['Scenario']==config.SCENARIO_OF_INTEREST]
model_output_8th = model_output_8th[model_output_8th['Scenario']==config.SCENARIO_OF_INTEREST]
model_output_detailed = model_output_detailed[model_output_detailed['Scenario']==config.SCENARIO_OF_INTEREST]
#%%
#create a dataframe that has the 8th and 9th concatenated
#create column in both datasets that states the dataset
model_output_9th = model_output_all.copy()
model_output_9th['Dataset'] = '9th'
model_output_8th['Dataset'] = '8th'

#concatenate data together
model_output_both_scenarios = pd.concat([model_output_9th, model_output_8th], axis=0)



################################################################################################################################################################
#%%
#plot energy use for all economys for each Date, by drive type.
title = 'Total energy use for all economys for each Date, drive type'
model_output_detailed_vtype = model_output_detailed.groupby(['Date', 'Drive'])['Energy'].sum().reset_index()

#plot
fig, ax = plt.subplots()
for key, grp in model_output_detailed_vtype.groupby(['Drive']):
    ax = grp.plot(ax=ax, kind='line', x='Date', y='Energy', label=key)
plt.title(title)
#save
plt.savefig('./plotting_output/diagnostics/png/{}.png'.format(title))

################################################################################################################################################################
#%%
#plot stocks use for all economys for each Date, by drive type.
title='Total stocks for all economys for each Date, drive type'
model_output_detailed_vtype = model_output_detailed.groupby(['Date', 'Drive'])['Stocks'].sum().reset_index()

#plot
fig, ax = plt.subplots()
for key, grp in model_output_detailed_vtype.groupby(['Drive']):
    ax = grp.plot(ax=ax, kind='line', x='Date', y='Stocks', label=key)
plt.title(title)
#save
plt.savefig('./plotting_output/diagnostics/png/{}.png'.format(title))

################################################################################################################################################################
#%%
#show the uptake of BEVs by Date, per economy
title = 'Total stocks of BEVs for each Date, by economy'
model_output_detailed_bevs = model_output_detailed[model_output_detailed['Drive'] == 'bev']
model_output_detailed_bevs = model_output_detailed_bevs.groupby(['Date', 'Economy'])['Stocks'].sum().reset_index()

#plot
fig, ax = plt.subplots()
for key, grp in model_output_detailed_bevs.groupby(['Economy']):
    ax = grp.plot(ax=ax, kind='line', x='Date', y='Stocks', label=key)
plt.title(title)
#save
plt.savefig('./plotting_output/diagnostics/png/{}.png'.format(title))


#%%
################################################################################################################################################################
#plot the average vehivle sales shares for each economy for each Date, for LV's
title = 'Average vehicle sales shares for each drive for passenger LDVs'
model_output_detailed_sales = model_output_detailed[model_output_detailed['Vehicle Type'] == 'ldv']
# #tet out excludeing china 05_PRC
# model_output_detailed_sales = model_output_detailed_sales[model_output_detailed_sales['Economy'] != '05_PRC']
model_output_detailed_sales = model_output_detailed_sales[model_output_detailed_sales['Transport Type'] == 'passenger']
model_output_detailed_sales = model_output_detailed_sales.groupby(['Date', 'Drive'])['Vehicle_sales_share'].mean().reset_index()

#plot
fig, ax = plt.subplots()
for key, grp in model_output_detailed_sales.groupby(['Drive']):
    ax = grp.plot(ax=ax, kind='line', x='Date', y='Vehicle_sales_share', label=key)
    
plt.title(title)
#save
plt.savefig('./plotting_output/diagnostics/png/{}.png'.format(title))


#%%
################################################################################################################################################################

#plot the average vehivle sales shares for each economy for each Date
title = 'Average vehicle sales shares for each drive for passenger'
model_output_detailed_sales = model_output_detailed[model_output_detailed['Transport Type'] == 'passenger']
model_output_detailed_sales = model_output_detailed_sales.groupby(['Date', 'Drive'])['Vehicle_sales_share'].mean().reset_index()

#plot
fig, ax = plt.subplots()
for key, grp in model_output_detailed_sales.groupby(['Drive']):
    ax = grp.plot(ax=ax, kind='line', x='Date', y='Vehicle_sales_share', label=key)

plt.title(title)
#save
plt.savefig('./plotting_output/diagnostics/png/{}.png'.format(title))


################################################################################################################################################################

#%%
#plot the total surplus stocks for all economy dor each Date
title='Total surplus stocks for all economys for each Date'
#sum surplus stocks for each economy for each Date
model_output_surplus = model_output_detailed.groupby(['Date'])['Surplus_stocks'].sum().reset_index()

plt.plot(model_output_surplus['Date'], model_output_surplus['Surplus_stocks'])
plt.title(title)
#save
plt.savefig('./plotting_output/diagnostics/png/{}.png'.format(title))

################################################################################################################################################################
#%%
#plot total energy use, activity and stocks compared to the 8th edition
title = 'Total energy use compared to the 8th edition'
#sum energy use for each dataset for each Date
model_output_energy = model_output_both_scenarios.groupby(['Date', 'Dataset'])['Energy'].sum().reset_index()
#plot
fig, ax = plt.subplots()
for key, grp in model_output_energy.groupby(['Dataset']):
    ax = grp.plot(ax=ax, kind='line', x='Date', y='Energy', label=key)
plt.title(title)
#save
plt.savefig('./plotting_output/diagnostics/png/{}.png'.format(title))

title = 'Total activity compared to the 8th edition'
#sum activity for each dataset for each Date
model_output_activity = model_output_both_scenarios.groupby(['Date', 'Dataset'])['Activity'].sum().reset_index()
#plot
fig, ax = plt.subplots()
for key, grp in model_output_activity.groupby(['Dataset']):
    ax = grp.plot(ax=ax, kind='line', x='Date', y='Activity', label=key)
plt.title(title)
#save
plt.savefig('./plotting_output/diagnostics/png/{}.png'.format(title))


title = 'Total stocks compared to the 8th edition'
#sum stocks for each dataset for each Date
model_output_stocks = model_output_both_scenarios.groupby(['Date', 'Dataset'])['Stocks'].sum().reset_index()
#plot
fig, ax = plt.subplots()
for key, grp in model_output_stocks.groupby(['Dataset']):
    ax = grp.plot(ax=ax, kind='line', x='Date', y='Stocks', label=key)
plt.title(title)
#save
plt.savefig('./plotting_output/diagnostics/png/{}.png'.format(title))


################################################################################################################################################################
#%%
#plot activity by drive type 
#plot passenger_km for passenger transport type:
passenger_km = model_output_detailed[model_output_detailed['Transport Type'] == 'passenger']
passenger_km = passenger_km.groupby(['Date', 'Drive'])['Activity'].sum().reset_index()
title = 'passenger_km by drive type'
model_output_activity_drive = model_output_detailed.groupby(['Date', 'Drive'])['Activity'].sum().reset_index()

from matplotlib.pyplot import cm
color = iter(cm.rainbow(np.linspace(0, 1, 15)))
i=0
   
#plot
fig, ax = plt.subplots()
for key, grp in model_output_activity_drive.groupby(['Drive']):
    i+=1
    ax = grp.plot(ax=ax, kind='line', x='Date', y='Activity', label=key,c=next(color))
plt.title(title)
#save
plt.savefig('./plotting_output/diagnostics/png/{}.png'.format(title))





#plot freight_km for freight transport type:
freight_km = model_output_detailed[model_output_detailed['Transport Type'] == 'freight']
freight_km = freight_km.groupby(['Date', 'Drive'])['Activity'].sum().reset_index()
title = 'freight_tonne_km by drive type'
model_output_activity_drive = model_output_detailed.groupby(['Date', 'Drive'])['Activity'].sum().reset_index()

from matplotlib.pyplot import cm
color = iter(cm.rainbow(np.linspace(0, 1, 15)))
i=0

#plot
fig, ax = plt.subplots()
for key, grp in model_output_activity_drive.groupby(['Drive']):

    i+=1
    ax = grp.plot(ax=ax, kind='line', x='Date', y='Activity', label=key,c=next(color))
plt.title(title)
#save
plt.savefig('./plotting_output/diagnostics/png/{}.png'.format(title))




#%%
#plot
# #first we must extract the data so we dont have duplciates (as the stocks per cpita and gdp per capita are the same for each vehicle type and drive type)
# gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy','Date', 'Stocks_per_thousand_capita', 'Gdp_per_capita']].drop_duplicates()
# fig = px.scatter(gompertz_function_diagnostics_dataframe, x="Gdp_per_capita", y="Stocks_per_thousand_capita", facet_col="Economy", facet_col_wrap=7, color="Economy", hover_name="Economy", trendline="ols", trendline_color_override="darkblue")










#%%
################################################################################################################################################################
# #plot total travel km per stock by vehicle type. To make things simple we will just recalcualte travl km per stock using the mean of travel km and stocks for each vehicle type and Date
# title = 'Average travel km per stock by transport and vehicle type'
# model_output_travel_km_per_stock = model_output_detailed.copy()

# model_output_travel_km_per_stock['Vehicle_transport_type'] = model_output_travel_km_per_stock['Vehicle Type'] + '_' + model_output_travel_km_per_stock['Transport Type']

# model_output_travel_km_per_stock = model_output_travel_km_per_stock.groupby(['Date', 'Vehicle_transport_type'])['Travel_km', 'Stocks'].mean().reset_index()

# model_output_travel_km_per_stock['Travel_km_per_stock'] = model_output_travel_km_per_stock['Travel_km'] / model_output_travel_km_per_stock['Stocks']

# model_output_travel_km_per_stock = model_output_travel_km_per_stock[['Date', 'Vehicle_transport_type', 'Travel_km_per_stock']]

# #remove nas cause non road doesnt have this data
# model_output_travel_km_per_stock = model_output_travel_km_per_stock.dropna()

# num_colors = len(model_output_travel_km_per_stock['Vehicle_transport_type'].unique())
# from matplotlib.pyplot import cm
# color = iter(cm.rainbow(np.linspace(0, 1, num_colors)))
# i=0
   
# #plot
# fig, ax = plt.subplots()
# for key, grp in model_output_travel_km_per_stock.groupby(['Vehicle_transport_type']):
#     i+=1
#     ax = grp.plot(ax=ax, kind='line', x='Date', y='Travel_km_per_stock', label=key,c=next(color))

# # plt.title(title)
# # #save html
# if save_html:
#     fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
# #save fig
# if save_fig:
#     fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))










#%%
################################################################################################################################################################
# #analysis
# #check for duplicates
# duplicates = model_output_all.duplicated().sum()
# if duplicates > 0:
#     print('There are {} duplicates in the model output'.format(duplicates))
# #check for missing values
# NAs = model_output_all.isna().sum().sum()
# if NAs > 0:
#     print('There are {} missing values in the model output'.format(NAs))





# #%%
# #compare model output to 8th edition output. If there are any differences, print them
# #laod output from 8th edition
# model_output = pd.read_csv('output_data/model_output_detailed/{}'.format(config.model_output_file_name))
# model_output_8th = pd.read_csv('output_data/model_output_detailed/activity_efficiency_energy_road_stocks.csv')

# #%%
# #plot energy use
# #get data for energy use by Date, economy, in both scenarios

# #%%
# title='Surplus stocks use by Date, economy, in both scenarios'

# data_3_select_Dates_other_regions = data_3_select_Dates[data_3_select_Dates['ECON_Sub_Category'] != 'China_USA']

# #plot
# fig = px.line(data_3_select_Dates_other_regions, x="Date", y="PJ", color="Scenario", line_dash='Scenario', facet_col="Economy_name", facet_col_wrap=7, title=title)#, #facet_col="Economy",
#              #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
# fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

# #fig.show()  
# import plotly
# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png')


# #%%


# #%%
# title='Energy use by Date, economy, in both scenarios'

# #plot
# fig = px.line(data_3_select_Dates, x="Date", y="PJ", color="Scenario", line_dash='Scenario', facet_col="Economy_name", facet_col_wrap=7, title=title)#, #facet_col="Economy",
#              #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
# fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

# #fig.show()  
# import plotly
# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png')


# #%%




# #%%
# #we will do this using plotly
# import plotly.express as px
# import plotly.graph_objects as go

# #filter for only the Reference scenario 
# gompertz_function_diagnostics_dataframe = gompertz_function_diagnostics_dataframe[gompertz_function_diagnostics_dataframe['Scenario'] == 'Reference']
# ################################
# #plot stocks per capita (y) and Gdp_per_capita (x) for each economy and each year,. The economy will be in facets. 
# title = 'Stocks per capita (y) and Gdp_per_capita (x) for each economy and each year'
# #to plot the expected gdp per cpita, we will melt the gdp per cpitas to be in one col, and the measure name in another col so we can colr by measure name
# gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy','Date', 'Vehicle Type','Stocks_per_thousand_capita', 'Gdp_per_capita']].drop_duplicates()#,'Expected_Gdp_per_capita'
# #%%
# ################################
# #plot gdp per capita vs expected gdp per capita
# if 'Expected_Gdp_per_capita' in gompertz_function_diagnostics_dataframe.columns:
#     title = 'Gdp per capita vs expected gdp per capita'
#     gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy', 'Date','Vehicle Type', 'Expected_Gdp_per_capita', 'Gdp_per_capita']].drop_duplicates()
#     #melt
#     gompertz_function_diagnostics_dataframe_plot = pd.melt(gompertz_function_diagnostics_dataframe_plot, id_vars=['Economy', 'Date','Vehicle Type'], value_vars=['Expected_Gdp_per_capita', 'Gdp_per_capita'], var_name='Measure', value_name='Value')
#     #cnocatenate the measure name to the vehicle type
#     gompertz_function_diagnostics_dataframe_plot['Measure'] = gompertz_function_diagnostics_dataframe_plot['Vehicle Type'] + ' ' + gompertz_function_diagnostics_dataframe_plot['Measure']

#     fig = px.scatter(gompertz_function_diagnostics_dataframe_plot, x="Date", y="Value", facet_col="Economy", color='Measure',facet_col_wrap=7, title=title)
#     # #add the derivative
#     # fig.add_scatter(x=gompertz_function_diagnostics_dataframe_plot['Date'], y=gompertz_function_diagnostics_dataframe_plot['Expected_stocks_per_thousand_capita_derivative_2'], mode='lines', line=dict(color='grey', dash='dash'), name='Expected_stocks_per_thousand_capita_derivative_2')
#     #save html
#     if save_html:
#         fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
#     #save fig
#     if save_fig:
#         fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))



# ################################
# #%%
# gompertz_function_diagnostics_dataframe_plot = pd.melt(gompertz_function_diagnostics_dataframe_plot, id_vars=['Economy','Date','Vehicle Type','Stocks_per_thousand_capita'], value_vars=['Gdp_per_capita'], var_name='Measure', value_name='Gdp_per_capita')#,'Expected_Gdp_per_capita'
# #concat the  'Vehicle Type', and Measure
# gompertz_function_diagnostics_dataframe_plot['Measure'] = gompertz_function_diagnostics_dataframe_plot['Vehicle Type'] + ' ' + gompertz_function_diagnostics_dataframe_plot['Measure']
# fig = px.scatter(gompertz_function_diagnostics_dataframe_plot, x="Gdp_per_capita", y="Stocks_per_thousand_capita", facet_col="Economy", facet_col_wrap=7, color="Measure", title=title)
# #save html
# if save_html:
#     fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
# #save fig
# if save_fig:
#     fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))



# ################################
# #also plot stocks per capita (y) and Gdp_per_capita (x)  vs Expected_Gdp_per_capita (y) and Expected_stocks_per_thousand_capita (x) for each economy and scenario and each year. We will use grey lighter colors for the expected values
# if 'Expected_Gdp_per_capita' in gompertz_function_diagnostics_dataframe.columns:
#     title = 'Stocks per capita (y) and Gdp_per_capita (x)  vs Expected_stocks_per_thousand_capita (x) for each economy and scenario and each year'#Expected_Gdp_per_capita (y) and 
#     #to plot the expected gdp per cpita, we will melt the gdp per cpitas to be in one col, and the measure name in another col so we can colr by measure name
#     gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy','Date', 'Vehicle Type','Transport Type','Stocks_per_thousand_capita', 'Gdp_per_capita']].drop_duplicates()
#     #Create a column called 'Measure' which = 'Actual' for the actual values, and 'Expected' for the expected values
#     gompertz_function_diagnostics_dataframe_plot['Measure'] = 'Actual'
#     #add in the expected values
#     gompertz_function_diagnostics_dataframe_plot2 = gompertz_function_diagnostics_dataframe[['Economy','Date', 'Vehicle Type','Transport Type', 'Expected_stocks_per_thousand_capita','Gdp_per_capita']].drop_duplicates()#, 'Expected_Gdp_per_capita' swapped for 'Gdp_per_capita'
#     #rename the columns so they are the same as the actual values
#     gompertz_function_diagnostics_dataframe_plot2 = gompertz_function_diagnostics_dataframe_plot2.rename(columns={'Expected_stocks_per_thousand_capita':'Stocks_per_thousand_capita'})
#     gompertz_function_diagnostics_dataframe_plot2['Measure'] = 'Expected'
#     gompertz_function_diagnostics_dataframe_plot = pd.concat([gompertz_function_diagnostics_dataframe_plot, gompertz_function_diagnostics_dataframe_plot2])
#     #concat measure with vehicle type and transport type
#     gompertz_function_diagnostics_dataframe_plot['Measure'] = gompertz_function_diagnostics_dataframe_plot['Measure'] + ' ' + gompertz_function_diagnostics_dataframe_plot['Vehicle Type'] + ' ' + gompertz_function_diagnostics_dataframe_plot['Transport Type']
#     #now plot 
#     fig = px.scatter(gompertz_function_diagnostics_dataframe_plot, x="Gdp_per_capita", y="Stocks_per_thousand_capita", facet_col="Economy", facet_col_wrap=7, color="Measure", title=title, color_discrete_map={'Actual':'black', 'Expected':'grey'})
#     #save the plot
#     fig.write_html(f"./plotting_output/diagnostics/html/{title}.html", auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# ################################
# #plot Expected_stocks_per_thousand_capita vs Stocks_per_thousand_capita for each economy and scenario and each year. We will use grey lighter colors for the expected values
# if 'Expected_stocks_per_thousand_capita' in gompertz_function_diagnostics_dataframe.columns:
#     title = 'Expected_stocks_per_thousand_capita vs Stocks_per_thousand_capita for each economy and scenario and each year'
#     gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy','Date', 'Vehicle Type','Transport Type','Stocks_per_thousand_capita', 'Expected_stocks_per_thousand_capita']].drop_duplicates()
#     #melt
#     gompertz_function_diagnostics_dataframe_plot = pd.melt(gompertz_function_diagnostics_dataframe_plot, id_vars=['Economy','Date','Vehicle Type','Transport Type'], value_vars=['Expected_stocks_per_thousand_capita','Stocks_per_thousand_capita'], var_name='Measure', value_name='Value')
#     #concat measure with vehicle type and transport type
#     gompertz_function_diagnostics_dataframe_plot['Dash'] = gompertz_function_diagnostics_dataframe_plot['Measure'].apply(lambda x: 'Expected' if x == 'Expected_stocks_per_thousand_capita' else 'Actual')

#     gompertz_function_diagnostics_dataframe_plot['Measure'] = gompertz_function_diagnostics_dataframe_plot['Measure'] + ' ' + gompertz_function_diagnostics_dataframe_plot['Vehicle Type'] + ' ' + gompertz_function_diagnostics_dataframe_plot['Transport Type']

#     #now plot 
#     fig = px.scatter(gompertz_function_diagnostics_dataframe_plot, x="Date", y="Value", facet_col="Economy", facet_col_wrap=7, color="Measure", title=title, line_dash='Dash')
#     #save the plot
#     fig.write_html(f"./plotting_output/diagnostics/html/{title}.html", auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# ################################
# #then we will plot Expected_stocks_per_thousand_capita_derivative over time for each economy . also add in a dashed, lighter line which shows the Expected_stocks_per_thousand_capita_derivative_2 so we can see if that is a better fit
# title = 'Expected_stocks_per_thousand_capita_derivative over time for each economy'
# gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy', 'Date','Vehicle Type', 'Expected_stocks_per_thousand_capita_derivative']].drop_duplicates()

# fig = px.scatter(gompertz_function_diagnostics_dataframe_plot, x="Date", y="Expected_stocks_per_thousand_capita_derivative", facet_col="Economy", color='Vehicle Type',facet_col_wrap=7, title=title)
# # #add the derivative
# # fig.add_scatter(x=gompertz_function_diagnostics_dataframe_plot['Date'], y=gompertz_function_diagnostics_dataframe_plot['Expected_stocks_per_thousand_capita_derivative_2'], mode='lines', line=dict(color='grey', dash='dash'), name='Expected_stocks_per_thousand_capita_derivative_2')
# #save html
# if save_html:
#     fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
# #save fig
# if save_fig:
#     fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))
# ################################
# #then we will plot Expected_stocks_per_thousand_capita_second_derivative over time for each economy . also add in a dashed, lighter line which shows the Expected_stocks_per_thousand_capita_derivative_2 so we can see if that is a better fit
# title = 'Expected_stocks_per_thousand_capita_growth over time for each economy'
# gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy', 'Date','Vehicle Type','Expected_stocks_per_thousand_capita_growth']].drop_duplicates()

# fig = px.scatter(gompertz_function_diagnostics_dataframe_plot, x="Date", y="Expected_stocks_per_thousand_capita_growth", facet_col="Economy", color='Vehicle Type',facet_col_wrap=7, title=title)
# # #add the derivative
# # fig.add_scatter(x=gompertz_function_diagnostics_dataframe_plot['Date'], y=gompertz_function_diagnostics_dataframe_plot['Expected_stocks_per_thousand_capita_derivative_2'], mode='lines', line=dict(color='grey', dash='dash'), name='Expected_stocks_per_thousand_capita_derivative_2')
# #save html
# if save_html:
#     fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
# #save fig
# if save_fig:
#     fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))


# #%%
# ################################
# from scipy import stats
# #plot stocks per cpita with gamma line too
# title = 'Stocks per capita over time with Gompertz_gamma for each economy'
# gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy', 'Date', 'Vehicle Type','Stocks_per_thousand_capita', 'Gompertz_gamma']].drop_duplicates()
# # #melt so values are in one column
# gompertz_function_diagnostics_dataframe_plot = pd.melt(gompertz_function_diagnostics_dataframe_plot, id_vars=['Economy', 'Date', 'Vehicle Type'], value_vars=['Stocks_per_thousand_capita', 'Gompertz_gamma'], value_name='Value', var_name='Measure').dropna()
# #concat measure with vehicle type 
# gompertz_function_diagnostics_dataframe_plot['Measure'] = gompertz_function_diagnostics_dataframe_plot['Measure'] + ' ' + gompertz_function_diagnostics_dataframe_plot['Vehicle Type']
# fig = px.line(gompertz_function_diagnostics_dataframe_plot, x="Date", y="Value", facet_col="Economy",color='Measure', facet_col_wrap=7, title=title)
# #save html
# if save_html:
#     fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
# #save fig
# if save_fig:
#     fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))

# # #%%
# # ################################
# # #plot  derivative 

# # title = 'Stocks per capita derivative over time for each economy'
# # gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy', 'Date','Vehicle Type', 'Expected_stocks_per_thousand_capita_derivative']].drop_duplicates()
# # fig = px.line(gompertz_function_diagnostics_dataframe_plot, x="Date", y="Expected_stocks_per_thousand_capita_derivative", facet_col="Economy", color='Vehicle Type',facet_col_wrap=7, title=title)
# # #save html
# # if save_html:
# #     fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
# # #save fig
# # if save_fig:
# #     fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))



# # title = 'Stocks per capita 2nd derivative over time for each economy'
# # gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy', 'Date','Vehicle Type', 'Expected_stocks_per_thousand_capita_second_derivative']].drop_duplicates()
# # fig = px.line(gompertz_function_diagnostics_dataframe_plot, x="Date", y="Expected_stocks_per_thousand_capita_second_derivative", facet_col="Economy", color='Vehicle Type',facet_col_wrap=7, title=title)
# # #save html
# # if save_html:
# #     fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
# # #save fig
# # if save_fig:
# #     fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))




# # ################################
# # #plot the same stocks per cpita on one y axis and its derivative on the other, but also plot the expected stocks per capita derivative 2 and the Expected_stocks_per_thousand_capita_2 on the same plot using grey lighter colors and dashed lines
# # title = 'Stocks per capita vs its derivative over time for each economy with derivative 2 and stocks per capita 2 for comparison'
# # gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy', 'Date', 'Stocks_per_thousand_capita', 'Expected_stocks_per_thousand_capita_derivative']].drop_duplicates()
# # fig = px.line(gompertz_function_diagnostics_dataframe_plot, x="Date", y="Stocks_per_thousand_capita", facet_col="Economy", facet_col_wrap=7, title=title)
# # #add the derivative
# # fig.add_scatter(x=gompertz_function_diagnostics_dataframe_plot['Date'], y=gompertz_function_diagnostics_dataframe_plot['Expected_stocks_per_thousand_capita_derivative'], mode='lines', name='Expected_stocks_per_thousand_capita_derivative')
# # #add the derivative 2
# # fig.add_scatter(x=gompertz_function_diagnostics_dataframe_plot['Date'], y=gompertz_function_diagnostics_dataframe_plot['Expected_stocks_per_thousand_capita_derivative_2'], mode='lines', line=dict(color='grey', dash='dash'), name='Expected_stocks_per_thousand_capita_derivative_2')
# # #add the stocks per capita 2
# # fig.add_scatter(x=gompertz_function_diagnostics_dataframe_plot['Date'], y=gompertz_function_diagnostics_dataframe_plot['Expected_stocks_per_thousand_capita_2'], mode='lines', line=dict(color='grey', dash='dash'), name='Expected_stocks_per_thousand_capita_2')
# # #save html
# # if save_html:
# #     fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
# # #save fig
# # if save_fig:
# #     fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))



# ################################
# #PLOT activity growth vs activity growth adjusted
# title = 'Activity growth vs activity growth adjusted over time for each economy'
# gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy', 'Date', 'Activity_growth','Transport Type', 'Activity_growth_adjusted']].drop_duplicates()
# #melt
# gompertz_function_diagnostics_dataframe_plot = pd.melt(gompertz_function_diagnostics_dataframe_plot, id_vars=['Economy','Transport Type','Date'], value_vars=['Activity_growth','Activity_growth_adjusted'], var_name='Measure', value_name='Activity_growth')
# #concat Measure and 'Transport Type'
# gompertz_function_diagnostics_dataframe_plot['Measure'] = gompertz_function_diagnostics_dataframe_plot['Measure'] + ' ' + gompertz_function_diagnostics_dataframe_plot['Transport Type']
# fig = px.line(gompertz_function_diagnostics_dataframe_plot, x="Date", y="Activity_growth_est", facet_col="Economy", facet_col_wrap=7, color='Measure', title=title)
# #save html
# if save_html:
#     fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
# #save fig
# if save_fig:
#     fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))

# #%%
# ################################
# #and lastly plot mileage growth vs mileage growth adjusted (not plotting actual mileage because it is different for each vehicle type and drive type, but the growth is the same for all vehicle type and drive types)
# title = 'Mileage over time for each economy'
# gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy', 'Date', 'Mileage', 'Vehicle Type']].drop_duplicates()
# fig = px.line(gompertz_function_diagnostics_dataframe_plot, x="Date", y="Mileage", facet_col="Economy", facet_col_wrap=7, color='Vehicle Type', title=title)
# #save html
# if save_html:
#     fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
# #save fig
# if save_fig:
#     fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))
# #%%
# #and lastly plot mileage growth vs mileage growth adjusted (not plotting actual mileage because it is different for each vehicle type and drive type, but the growth is the same for all vehicle type and drive types)
# title = 'Mileage growth vs mileage growth adjusted over time for each economy'
# gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy', 'Date', 'Mileage_growth_adjusted', 'Mileage_growth', 'Vehicle Type']].drop_duplicates()
# #melt
# gompertz_function_diagnostics_dataframe_plot = pd.melt(gompertz_function_diagnostics_dataframe_plot, id_vars=['Economy','Date', 'Vehicle Type'], value_vars=['Mileage_growth_adjusted', 'Mileage_growth'], var_name='Measure', value_name='Mileage_growth')
# #concat Measure and 'Vehicle Type'
# gompertz_function_diagnostics_dataframe_plot['Measure'] = gompertz_function_diagnostics_dataframe_plot['Measure'] + ' ' + gompertz_function_diagnostics_dataframe_plot['Vehicle Type']
# fig = px.line(gompertz_function_diagnostics_dataframe_plot, x="Date", y="Mileage_growth", facet_col="Economy", facet_col_wrap=7, color='Measure', title=title)
# #save html
# if save_html:
#     fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
# #save fig
# if save_fig:
#     fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))
