#take in detailed output data and print out any useful metrics/statisitcs to summarise the reults of the model. the intention is that the output willbe easy to view through the command line, and that the output will be saved to a file for later viewing.

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
###IMPORT GLOBAL VARIABLES FROM config.py
import sys
sys.path.append("./config")
from config import *
####Use this to load libraries and set variables. Feel free to edit that file as you need.

import plotly
import plotly.express as px
pd.options.plotting.backend = "plotly"#set pandas backend to plotly plotting instead of matplotlib
import plotly.io as pio
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook
#%%

#load data in
model_output_all = pd.read_csv('output_data/model_output/{}'.format(config.model_output_file_name))
model_output_detailed = pd.read_csv('output_data/model_output_detailed/{}'.format(config.model_output_file_name))
change_dataframe_aggregation = pd.read_csv('intermediate_data/road_model/change_dataframe_aggregation.csv')

#lkoad 8th data
model_output_8th = pd.read_csv('intermediate_data/activity_efficiency_energy_road_stocks.csv')

#%%
#keep only columns in model_output_8th
model_output = model_output_all[model_output_all.columns.intersection(model_output_8th.columns)]

#%%
#filter for data within the same years of each dataset
model_output = model_output[model_output['Year'].isin(model_output_8th['Year'])]
model_output_8th = model_output_8th[model_output_8th['Year'].isin(model_output['Year'])]

#create column in both datasets that states the dataset
model_output['Dataset'] = '9th'
model_output_8th['Dataset'] = '8th'

#concatenate data together
model_output_concat = pd.concat([model_output, model_output_8th], axis=0)
#%%
#FILTER FOR SCENARIO OF INTEREST
#this should be temporary as the scenario should be passed in as a parameter through config if it is useed elsewhere

model_output_all = model_output_all[model_output_all['Scenario']==SCENARIO_OF_INTEREST]
model_output_detailed = model_output_detailed[model_output_detailed['Scenario']==SCENARIO_OF_INTEREST]
change_dataframe_aggregation = change_dataframe_aggregation[change_dataframe_aggregation['Scenario']==SCENARIO_OF_INTEREST]
model_output_concat = model_output_concat[model_output_concat['Scenario']==SCENARIO_OF_INTEREST]
#%%

################################################################################################################################################################

#when we look at stocks and sales of bevs vs ices we see that the stock of bevs doesnt rise at all even when its sales are higher than ices, and ice stocks are rising fast.
#lets dig into it. lets look at nz lv sales

model_output_detailed_nz_lv = model_output_detailed[model_output_detailed['Economy']=='12_NZ']
model_output_detailed_nz_lv = model_output_detailed_nz_lv[model_output_detailed_nz_lv['Vehicle Type']=='lv']
model_output_detailed_nz_lv = model_output_detailed_nz_lv[model_output_detailed_nz_lv['Drive'].isin(['g', 'bev'])]

#for this we will use matplotlib
import matplotlib.pyplot as plt
plt.rcParams['figure.facecolor'] = 'w'
pd.options.plotting.backend = "matplotlib"


#plot stocks
fig, ax = plt.subplots()
for key, grp in model_output_detailed_nz_lv.groupby(['Drive']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Stocks', label=key)

#plot sales share
fig, ax = plt.subplots()
for key, grp in model_output_detailed_nz_lv.groupby(['Drive']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Vehicle_sales_share', label=key)

#plot Travel_km_per_stock
fig, ax = plt.subplots()
for key, grp in model_output_detailed_nz_lv.groupby(['Drive']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Travel_km_per_stock', label=key)

#############################################
#%%
#look at change_dataframe_aggregation
change_dataframe_aggregation_nz_lv = change_dataframe_aggregation[change_dataframe_aggregation['Economy']=='12_NZ']
change_dataframe_aggregation_nz_lv = change_dataframe_aggregation_nz_lv[change_dataframe_aggregation_nz_lv['Vehicle Type']=='lv']
change_dataframe_aggregation_nz_lv = change_dataframe_aggregation_nz_lv[change_dataframe_aggregation_nz_lv['Drive'].isin(['g', 'bev'])]

#plot Activity_growth
fig, ax = plt.subplots()
for key, grp in change_dataframe_aggregation_nz_lv.groupby(['Drive']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='Activity_growth', label=key)
























#%%

# #calcualte activity growth from the data to double chekc its the same as the activity growth in the change dataframe. in the final dataframe we weill want ot have the total activity, orioginal activity grwoth and newly calkculated activity from the total activity's growth
# # change_dataframe_aggregation['Activity_growth_TEST'] = change_dataframe_aggregation['New_stock_sales_activity']/change_dataframe_aggregation['New_stock_sales_activity'].shift(1)

# ##NOTE I CHANGED THIS TO LOOK AT THE ISSUE BY TRANSPORT TYPE
# #first get dataframewith original activity growth. we will merge everything onto this later
# change_dataframe_aggregation_growth = change_dataframe_aggregation[['Year', 'Economy', 'Transport Type','Activity_growth']].drop_duplicates()

# #sum up the activity data for each eyar and economy then calcualte the pct change per year
# change_dataframe_aggregation_growth2 = change_dataframe_aggregation[['Year', 'Economy','Transport Type', 'Activity']].groupby(['Economy', 'Transport Type','Year']).sum().reset_index()

# #now create a new column with the pct change
# #sort by year and everything else in ascending order
# change_dataframe_aggregation_growth2 = change_dataframe_aggregation_growth2.sort_values(by=['Economy', 'Transport Type', 'Year'])

# #calc growth rate. set index so that the growth rate is calc only for Value col
# change_dataframe_aggregation_growth3 = change_dataframe_aggregation_growth2.set_index(['Economy','Transport Type', 'Year']).pct_change()

# #now set all vlaues during the base year (plus one cause this dtf ddoesnt have 2017 data) to 0 as the growth rate is not defined for the base year
# if config.DEFAULT_BASE_YEAR == 2017:
#     change_dataframe_aggregation_growth3.loc[change_dataframe_aggregation_growth3.index.get_level_values('Year') == config.DEFAULT_BASE_YEAR+1, 'Activity'] = 0
# else:
#     change_dataframe_aggregation_growth3.loc[change_dataframe_aggregation_growth3.index.get_level_values('Year') == config.DEFAULT_BASE_YEAR, 'Activity'] = 0

# #replace NAN with 0
# change_dataframe_aggregation_growth3 = change_dataframe_aggregation_growth3.fillna(0)

# #rename col to Activity_growth
# change_dataframe_aggregation_growth3.rename(columns={"Activity": "Calculated_activity_growth"}, inplace=True)

# #merge back on the activity data
# activity_growth = change_dataframe_aggregation_growth3.merge(change_dataframe_aggregation_growth2, on=['Economy', 'Transport Type','Year'], how='left')

# #merge onto the original dataframe
# change_dataframe_aggregation_growth = change_dataframe_aggregation_growth.merge(activity_growth, on=['Economy','Transport Type', 'Year'], how='left')

# #create dataframe where activity_growth isnt within 0.01 of calculated activity growth
# change_dataframe_aggregation_growth_diff = change_dataframe_aggregation_growth[(change_dataframe_aggregation_growth['Activity_growth'] - change_dataframe_aggregation_growth['Calculated_activity_growth']).abs() > 0.01]

# #thjeres somethoiing odd gooiung on in 2017/2021. lets look at just that data
# change_dataframe_aggregation_growth_2017_2021 = change_dataframe_aggregation_growth[(change_dataframe_aggregation_growth['Year'].isin([2017, 2018, 2019, 2020, 2021]))]

# #IT SEEMS THAT ACTIVITY GROWTH IS BVEING CALCULATED KINDA WEIRD. LETS TRY A DIFFERENT WAY BY LETTING GITHUB COPILOT DO IT
# change_dataframe_aggregation_growth4 = change_dataframe_aggregation[['Year', 'Economy','Transport Type', 'Activity']].groupby(['Economy', 'Transport Type','Year']).sum().reset_index()

# #now calcualte percenta change differently
# change_dataframe_aggregation_growth4 = change_dataframe_aggregation_growth4.sort_values(by=['Economy', 'Transport Type', 'Year'])


# change_dataframe_aggregation_growth4['Percentage_change'] = change_dataframe_aggregation_growth4['Activity'].pct_change()

# #set base year values to 0
# if config.DEFAULT_BASE_YEAR == 2017:
#     change_dataframe_aggregation_growth4.loc[change_dataframe_aggregation_growth4['Year'] == config.DEFAULT_BASE_YEAR+1, 'Percentage_change'] = 0
# else:
#     change_dataframe_aggregation_growth4.loc[change_dataframe_aggregation_growth4['Year']== config.DEFAULT_BASE_YEAR, 'Percentage_change'] = 0

# #drop activity
# change_dataframe_aggregation_growth4 = change_dataframe_aggregation_growth4.drop(['Activity'], axis=1)
# #merge back onto the other data
# change_dataframe_aggregation_growth = change_dataframe_aggregation_growth.merge(change_dataframe_aggregation_growth4, on=['Economy', 'Transport Type','Year'], how='left') 
# #%%
# #sdet the dataframe to the one for early years
# # change_dataframe_aggregation_growth = change_dataframe_aggregation_growth_2017_2021.copy()
# #now plot it all
# title = 'Original activity growth vs activity vs calculated activity growth early years'

# import plotly.graph_objects as go
# from plotly.subplots import make_subplots

# #create subplots specs list as a set of 3 lists with 7 dictionaries in each that are just {"secondary_y": True} to create 3 rows of 7 subplots each
# subplots_specs = [[{"secondary_y": True} for i in range(7)] for j in range(3)] 
# subplot_titles = change_dataframe_aggregation_growth['Economy'].unique().tolist()
# transport_type_list = change_dataframe_aggregation_growth['Transport Type'].unique().tolist()
# fig = make_subplots(rows=3, cols=7,
#                     specs=subplots_specs,
#                     subplot_titles=subplot_titles)

# col_number=0
# row_number = 1
# legend_set = False

# for economy in change_dataframe_aggregation_growth['Economy'].unique():
#     #filter for economy
#     change_dataframe_aggregation_act_ag_e = change_dataframe_aggregation_growth[change_dataframe_aggregation_growth['Economy']==economy]

#     #set row and column number
#     col_number +=1
#     if col_number > 7:
#         col_number = 1
#         row_number += 1
#     #NOW GO THROUGH EACH DRIVE TYPE AND PLOT THE STOCKS AND SALES OF EACH t type
#     for transport_type in transport_type_list:
#         #get the index of the current t type
#         transport_type_index = transport_type_list.index(transport_type)

#         if transport_type == 'passenger':
#             color1 = 'blue'
#             color2= 'red'
#             color3 = 'green'
#             color4 = 'pink'
#         else:
#             color1 = 'black'
#             color2= 'orange'
#             color3 = 'purple'
#             color4 = 'brown'

#         #get the data for this t type
#         model_output_detailed_lv_passenger_economy_ttype = change_dataframe_aggregation_act_ag_e[change_dataframe_aggregation_act_ag_e['Transport Type']==transport_type]

#         if (col_number == 1) & (row_number == 1):#set the legend for the first subplot, and tehrefore all of the subplots

#             #create subplot for this economy
#             legend_name = 'Activity_' + transport_type

#             fig.add_trace(go.Scatter(x=model_output_detailed_lv_passenger_economy_ttype['Year'], y=model_output_detailed_lv_passenger_economy_ttype['Activity'],  legendgroup=legend_name, name=legend_name, line=dict(color=color1, width=2, )), row=row_number, col=col_number, secondary_y=False)

#             #create subplot for this economy
#             legend_name = 'Calculated_activity_growth_'+transport_type
#             fig.add_trace(go.Scatter(x=model_output_detailed_lv_passenger_economy_ttype['Year'], y=model_output_detailed_lv_passenger_economy_ttype['Calculated_activity_growth'],  legendgroup=legend_name, name=legend_name, line=dict(color=color2, width=2, )), row=row_number, col=col_number, secondary_y=True)

#             legend_name = 'Activity_growth_'+transport_type
#             fig.add_trace(go.Scatter(x=model_output_detailed_lv_passenger_economy_ttype['Year'], y=model_output_detailed_lv_passenger_economy_ttype['Activity_growth'], legendgroup=legend_name, name=legend_name, line=dict(color=color3, dash='dot', width=2)), row=row_number, col=col_number, secondary_y=True)

#             legend_name = 'Percentage_change_'+transport_type
#             fig.add_trace(go.Scatter(x=model_output_detailed_lv_passenger_economy_ttype['Year'], y=model_output_detailed_lv_passenger_economy_ttype['Percentage_change'], legendgroup=legend_name, name=legend_name, line=dict(color=color4, dash='dot', width=2)), row=row_number, col=col_number, secondary_y=True)

#         else:#legend is already set, so just add the traces with showlegend=False
#             #create subplot for this economy
#             legend_name = 'Activity_'+transport_type
#             fig.add_trace(go.Scatter(x=model_output_detailed_lv_passenger_economy_ttype['Year'], y=model_output_detailed_lv_passenger_economy_ttype['Activity'],  legendgroup=legend_name, name=legend_name,showlegend=False, line=dict(color=color1, width=2, )), row=row_number, col=col_number, secondary_y=False)

#             #create subplot for this economy
#             legend_name = 'Calculated_activity_growth_'+transport_type
#             fig.add_trace(go.Scatter(x=model_output_detailed_lv_passenger_economy_ttype['Year'], y=model_output_detailed_lv_passenger_economy_ttype['Calculated_activity_growth'],  legendgroup=legend_name, name=legend_name, showlegend=False, line=dict(color=color2, width=2, )), row=row_number, col=col_number, secondary_y=True)

#             legend_name = 'Activity_growth_'+transport_type
#             fig.add_trace(go.Scatter(x=model_output_detailed_lv_passenger_economy_ttype['Year'], y=model_output_detailed_lv_passenger_economy_ttype['Activity_growth'], legendgroup=legend_name, name=legend_name, showlegend=False, line=dict(color=color3, dash='dot', width=2)), row=row_number, col=col_number, secondary_y=True)
                       
#             legend_name = 'Percentage_change_'+transport_type
#             fig.add_trace(go.Scatter(x=model_output_detailed_lv_passenger_economy_ttype['Year'], y=model_output_detailed_lv_passenger_economy_ttype['Percentage_change'], legendgroup=legend_name, name=legend_name, showlegend=False, line=dict(color=color4, dash='dot', width=2)), row=row_number, col=col_number, secondary_y=True)


# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=1500)
# # %%
# #seems a bit odd that nz activity is about 0.002 growth rate lower than what it was projected to be, consistently. So we will take in the 89th eidtion adata and comparea actual activity vlaues to see if there is any pattern
# # model_output_concat_nz = model_output_concat[model_output_concat['Economy']=='12_NZ']
# #sum activity by vehicle type and year
# # model_output_concat_nz_sum = model_output_concat_nz.groupby(['Year', 'Vehicle Type', 'Dataset']).sum().reset_index()
# #sum activity by dataset and year
# model_output_concat = model_output_concat.groupby(['Year', 'Economy', 'Dataset']).sum().reset_index()
# #plot activity for both datasets
# title = '9th Activity vs 8th activity'

# #
# #plot
# fig = px.line(model_output_concat, x="Year", y="Activity", color="Dataset", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
#              #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
# fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=1500)

# #after looking into it it seems that some economys do see a tiny decrease in the growth rate. why?

# # %%
# #lets look at the growth rate byt transport type