#we will get the data from teh spreadsheet, change the structure to long and make the value column 'Value'
#This is from the data in vehicle_sales_share_model.xlsx which i copied from vehicle_sales_share_mod.xlsx  in hughs model from the sheets Refeence and Net zero. 

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
###IMPORT GLOBAL VARIABLES FROM config.py
import sys
sys.path.append("./config")
import config
####Use this to load libraries and set variables. Feel free to edit that file as you need.

import plotly
import plotly.express as px
pd.options.plotting.backend = "plotly"#set pandas backend to plotly plotting instead of matplotlib
import plotly.io as pio
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook

#%%
##
# PLEASE NOTE THAT CURRENTLY THE DATAA IS NOT FORMATTED FOR USE WITH THE GRAPHS BELOW.\
#load data.
#we will load the vehicle sales shares that we INTEND  to use
Vehicle_sales_share = pd.read_csv('intermediate_data/non_aggregated_input_data/Vehicle_sales_share.csv')

# #we will load the vehicle sales shares in the input data folder of 8th edition, whoch it seems hugh projected.
vehicle_sales_share_normalised = pd.read_csv('input_data/from_8th/reformatted/vehicle_sales_share_normalised.csv')

#we will merge a regions dataframe so that we can treat data wrt regions if need be
# regions = pd.read_csv('intermediate_data/non_aggregated_input_data/regions.csv')

#we will also load the output stocks data from hughs model and calcualte a vehicle sales share for each year from that. This will be used to test the model works like the 8th edition. it might also be better than the vehicle sales shares that were in the input data folder of 8th edition 
#load 8th edition data
road_stocks= pd.read_csv('intermediate_data/non_aggregated_input_data/road_stocks.csv')


################################################################################################################################################################

#%%
#calcualte vehicle sales share from the stocks data that hugh projected. Do it so that we have vehicle sales of vehiclke type, and vehicle sales of drive type within vehicel type. They will then by timesed to get the vehicle sales share of each vehicle type, within each transport type
#the issue we have is that we kind of have to asusme that any decrease in vehicle sales is 'turnover'. but any growth in stocks is 100% vehicle stocks sales, and isnt affected by turnover. So we end up seeing sales overexagerated, and probably turnover underexagerated too.

#so first step is to clauclate how many new stocks of each vehicle type threre are in each year.
#then the amount of new stocks of each drive type for each vehicel type in each year. 
new_road_vehicle_stocks = road_stocks[['Economy', 'Scenario', 'Transport Type', 'Year', 'Vehicle Type', 'Stocks']]
#sum the stocks for each vehicle type in each year
new_road_vehicle_stocks = new_road_vehicle_stocks.groupby(['Economy', 'Scenario', 'Transport Type', 'Year', 'Vehicle Type']).sum().reset_index()
#sort by year
new_road_vehicle_stocks = new_road_vehicle_stocks.sort_values(by=['Year'])
#calcualte new stocks each eyar for each group
new_road_vehicle_stocks['New Stocks'] = new_road_vehicle_stocks.groupby(['Economy', 'Scenario', 'Transport Type', 'Vehicle Type'])['Stocks'].diff().fillna(0)
#set any negative vlaues to 0 as we will assume they are due to stock turnover
new_road_vehicle_stocks.loc[new_road_vehicle_stocks['New Stocks'] < 0, 'New Stocks'] = 0
#calcualte sales share as the number of new stocks of eaach vehicle type divided by the number of new stocks of each transport type. 
#so first calc the new stocks for each transport type
new_road_transport_type_stocks = new_road_vehicle_stocks[['Economy', 'Scenario', 'Transport Type', 'Year', 'New Stocks']]
#sum
new_road_transport_type_stocks = new_road_transport_type_stocks.groupby(['Economy', 'Scenario', 'Transport Type', 'Year']).sum().reset_index()
#rename stocks to transport type stocks
new_road_transport_type_stocks.rename(columns={"New Stocks": "New Transport Type Stocks"}, inplace=True)
#merge back onto df
new_road_vehicle_stocks = new_road_vehicle_stocks.reset_index().merge(new_road_transport_type_stocks, on=['Economy', 'Scenario', 'Transport Type', 'Year'], how='left')
#calcualte sales share
new_road_vehicle_stocks['Vehicle_sales_share'] = new_road_vehicle_stocks['New Stocks'] / new_road_vehicle_stocks["New Transport Type Stocks"]
#replace inf with 0
new_road_vehicle_stocks['Vehicle_sales_share'] = new_road_vehicle_stocks['Vehicle_sales_share'].replace([np.inf, -np.inf], 0)
#replace na with 0
new_road_vehicle_stocks['Vehicle_sales_share'] = new_road_vehicle_stocks['Vehicle_sales_share'].fillna(0)
#%%

##Now do the same for drive type within vehicel type
new_road_drive_stocks = road_stocks[['Economy', 'Scenario', 'Transport Type', 'Year', 'Vehicle Type', 'Drive', 'Stocks']]
#sort by year
new_road_drive_stocks = new_road_drive_stocks.sort_values(by=['Year'])
#calcualte new stocks each eyar for each group
new_road_drive_stocks['New Stocks'] = new_road_drive_stocks.groupby(['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive'])['Stocks'].diff().fillna(0)
#set any negative vlaues to 0 as we will assume they are due to stock turnover
new_road_drive_stocks.loc[new_road_drive_stocks['New Stocks'] < 0, 'New Stocks'] = 0
#calcualte sales share as the number of new stocks of eaach Drive divided by the number of new stocks of each vehicle type
#so first calc the new stocks for each vehicle type
new_road_vehicle_type_stocks = new_road_drive_stocks[['Economy', 'Scenario', 'Transport Type', 'Year', 'Vehicle Type', 'New Stocks']]
#sum
new_road_vehicle_type_stocks = new_road_vehicle_type_stocks.groupby(['Economy', 'Scenario', 'Transport Type', 'Year', 'Vehicle Type']).sum().reset_index()
#rename stocks to vehicle type stocks
new_road_vehicle_type_stocks.rename(columns={"New Stocks": "New Vehicle Type Stocks"}, inplace=True)
#merge back onto df
new_road_drive_stocks = new_road_drive_stocks.reset_index().merge(new_road_vehicle_type_stocks, on=['Economy', 'Scenario', 'Transport Type', 'Year', 'Vehicle Type'], how='left')
#calcualte sales share
new_road_drive_stocks['Vehicle_sales_share'] = new_road_drive_stocks['New Stocks'] / new_road_drive_stocks["New Vehicle Type Stocks"]
#replace inf with 0
new_road_drive_stocks['Vehicle_sales_share'] = new_road_drive_stocks['Vehicle_sales_share'].replace([np.inf, -np.inf], 0)
#replace na with 0
new_road_drive_stocks['Vehicle_sales_share'] = new_road_drive_stocks['Vehicle_sales_share'].fillna(0)

#%%
#Calcualte vehicle sales share as the product of the two sales shares
#first merge the two dfs
new_sales_shares = new_road_drive_stocks.merge(new_road_vehicle_stocks, on=['Economy', 'Scenario', 'Transport Type', 'Year', 'Vehicle Type'], how='left')
#calcualte sales share
new_sales_shares['Vehicle_sales_share'] = new_sales_shares['Vehicle_sales_share_x'] * new_sales_shares['Vehicle_sales_share_y']
#drop unneeded columns
new_sales_shares = new_sales_shares[['Economy', 'Scenario', 'Transport Type', 'Year', 'Vehicle Type', 'Drive', 'Vehicle_sales_share']]

#check it adds to 1 for each transport type
new_sales_shares.groupby(['Economy', 'Scenario', 'Year','Transport Type']).sum()
#%%
#calcualte rolling average with a window of X years, of the sales share to remove the inter-annual variability
X= 10
#sort by year
new_sales_shares_rolling_mean = new_sales_shares.copy()

new_sales_shares_rolling_mean = new_sales_shares_rolling_mean.sort_values(by=['Year'])
new_sales_shares_rolling_mean['Vehicle_sales_share_rolling_mean'] = new_sales_shares_rolling_mean.groupby(['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive'])['Vehicle_sales_share'].transform(lambda x: x.rolling(window=X, min_periods=1, center=True).mean()).fillna(0)

#%%
#now normalise so the sum of the shares for each transport type is 1
#first calcualte the sum for each transport tpye, then normalise
new_sales_shares_rolling_mean_transport_type = new_sales_shares_rolling_mean[['Economy', 'Scenario', 'Transport Type', 'Year', 'Vehicle Type', 'Drive', 'Vehicle_sales_share_rolling_mean']]
#sum
new_sales_shares_rolling_mean_transport_type = new_sales_shares_rolling_mean_transport_type.groupby(['Economy', 'Scenario', 'Transport Type', 'Year']).sum().reset_index()
#rename to Vehicle_sales_share_rolling_mean_sum
new_sales_shares_rolling_mean_transport_type.rename(columns={"Vehicle_sales_share_rolling_mean": "Vehicle_sales_share_rolling_mean_sum"}, inplace=True)
#merge back onto df
new_sales_shares_rolling_mean_normalised = new_sales_shares_rolling_mean.merge(new_sales_shares_rolling_mean_transport_type, on=['Economy', 'Scenario', 'Transport Type', 'Year'], how='left')
#calcualte sales share normalised
new_sales_shares_rolling_mean_normalised['Vehicle_sales_share_rolling_mean'] = new_sales_shares_rolling_mean_normalised['Vehicle_sales_share_rolling_mean'] * (1 / new_sales_shares_rolling_mean_normalised['Vehicle_sales_share_rolling_mean_sum'])

#DONE

#%%
# plot the rolling average for 01_AUS, reference, lv, BEV vs its actual sales share
plot_data = new_sales_shares_rolling_mean_normalised.loc[(new_sales_shares_rolling_mean_normalised['Economy'] == '01_AUS') & (new_sales_shares_rolling_mean_normalised['Scenario'] == 'Reference') & (new_sales_shares_rolling_mean_normalised['Vehicle Type'] == 'lv') & (new_sales_shares_rolling_mean_normalised['Drive'] == 'bev')]

#plot suing matplotlib
import matplotlib.pyplot as plt
plt.rcParams['figure.facecolor'] = 'w'
pd.options.plotting.backend = "matplotlib"
#plot
fig, ax = plt.subplots()
ax = plot_data.plot(ax=ax, kind='line', x='Year', y='Vehicle_sales_share', label='Vehicle_sales_share')
ax = plot_data.plot(ax=ax, kind='line', x='Year', y='Vehicle_sales_share_rolling_mean', label='Vehicle_sales_share_rolling_mean')


plot_data = new_sales_shares_rolling_mean_normalised.loc[(new_sales_shares_rolling_mean_normalised['Economy'] == '12_NZ') & (new_sales_shares_rolling_mean_normalised['Scenario'] == 'Carbon Neutral') & (new_sales_shares_rolling_mean_normalised['Transport Type'] == 'freight')& (new_sales_shares_rolling_mean_normalised['Vehicle Type'] == 'lt') & (new_sales_shares_rolling_mean_normalised['Drive'] == 'bev')]

#plot suing matplotlib
import matplotlib.pyplot as plt
plt.rcParams['figure.facecolor'] = 'w'
pd.options.plotting.backend = "matplotlib"
#plot
fig, ax = plt.subplots()
ax = plot_data.plot(ax=ax, kind='line', x='Year', y='Vehicle_sales_share', label='Vehicle_sales_share')
ax = plot_data.plot(ax=ax, kind='line', x='Year', y='Vehicle_sales_share_rolling_mean', label='Vehicle_sales_share_rolling_mean')

# new_sales_shares['Vehicle_sales_share_rolling_average'] = new_sales_shares.groupby(['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Year'])['Vehicle_sales_share'].rolling(3).mean()
#%%
################################################################################################################################################################
#%%

#PLOTTING



################################################################################################################################################################








#now plot the data we jsut created
#first plot the vehicle sales share for each transport type
################################################################################################################################################################
title = '8th vehicle_sales_share by vehicle type within transport type by economy in REF'

#filter for ref scen
new_road_vehicle_stocks_ref = new_road_vehicle_stocks[new_road_vehicle_stocks['Scenario']=='Reference']
#plot
fig = px.line(new_road_vehicle_stocks_ref, x="Year", y="Vehicle_sales_share", color="Transport Type", line_dash='Vehicle Type', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/archive/' + title + '.html')
fig.write_image("./plotting_output/static/archive/" + title + '.png', scale=1, width=2000, height=800)

#filter for cn scen
new_road_vehicle_stocks_cn = new_road_vehicle_stocks[new_road_vehicle_stocks['Scenario']=='Carbon Neutral']
#plot
fig = px.line(new_road_vehicle_stocks_cn, x="Year", y="Vehicle_sales_share", color="Transport Type", line_dash='Vehicle Type', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

title = '8th vehicle_sales_share by vehicle type within transport type by economy in CN'

plotly.offline.plot(fig, filename='./plotting_output/archive/' + title + '.html')
fig.write_image("./plotting_output/static/archive" + title + '.png', scale=1, width=2000, height=800)


################################################################################################################################################################
#next plot the vehicle sales share for each vehicle type
title = '8th vehicle_sales_share by drive within vehicle type by economy in REF'

new_road_drive_stocks['Transport_Vehicle_type']= new_road_drive_stocks['Transport Type']+'_'+new_road_drive_stocks['Vehicle Type']

#filter for ref scen
new_road_drive_stocks_ref = new_road_drive_stocks[new_road_drive_stocks['Scenario']=='Reference']
#plot
fig = px.line(new_road_drive_stocks_ref, x="Year", y="Vehicle_sales_share", color="Transport_Vehicle_type", line_dash='Drive', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/archive/' + title + '.html')
fig.write_image("./plotting_output/static/archive/" + title + '.png', scale=1, width=2000, height=800)

#filter for cn scen
new_road_drive_stocks_cn = new_road_drive_stocks[new_road_drive_stocks['Scenario']=='Carbon Neutral']
#plot
fig = px.line(new_road_drive_stocks_cn, x="Year", y="Vehicle_sales_share", color="Transport_Vehicle_type", line_dash='Drive',facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

title = '8th vehicle_sales_share by drive within vehicle type by economy in CN'

plotly.offline.plot(fig, filename='./plotting_output/archive/' + title + '.html')
fig.write_image("./plotting_output/static/archive" + title + '.png', scale=1, width=2000, height=800)



################################################################################################################################################################
#PLOT new_sales_shares
#next plot the vehicle sales share for each vehicle type
title = '8th vehicle_sales_share by economy in REF'

new_sales_shares['Transport_Vehicle_type']= new_sales_shares['Transport Type']+'_'+new_sales_shares['Vehicle Type']

#filter for ref scen
new_sales_shares_ref = new_sales_shares[new_sales_shares['Scenario']=='Reference']
#plot
fig = px.line(new_sales_shares_ref, x="Year", y="Vehicle_sales_share", color="Transport_Vehicle_type", line_dash='Drive', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/archive/' + title + '.html')
fig.write_image("./plotting_output/static/archive/" + title + '.png', scale=1, width=2000, height=800)

#filter for cn scen
new_sales_shares_cn = new_sales_shares[new_sales_shares['Scenario']=='Carbon Neutral']
title = '8th vehicle_sales_share by economy in CN'
#plot
fig = px.line(new_sales_shares_cn, x="Year", y="Vehicle_sales_share", color="Transport_Vehicle_type", line_dash='Drive',facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/archive/' + title + '.html')
fig.write_image("./plotting_output/static/archive" + title + '.png', scale=1, width=2000, height=800)

################################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
# %%

#plot the data we use for the modelling
################################################################################################################################################################
title = 'User input vehicle_sales_share in REF'

Vehicle_sales_share['Transport_Vehicle_type']= Vehicle_sales_share['Transport Type']+'_'+Vehicle_sales_share['Vehicle Type']

#filter for ref scen
vehicle_sales_share_ref = Vehicle_sales_share[Vehicle_sales_share['Scenario']=='Reference']
#plot
fig = px.line(vehicle_sales_share_ref, x="Year", y="Vehicle_sales_share", color="Transport_Vehicle_type", line_dash='Drive', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/archive/' + title + '.html')
fig.write_image("./plotting_output/static/archive/" + title + '.png', scale=1, width=2000, height=800)

#filter for cn scen
vehicle_sales_share_cn = Vehicle_sales_share[Vehicle_sales_share['Scenario']=='Carbon Neutral']
title = 'User input vehicle_sales_share in CN'
#plot
fig = px.line(vehicle_sales_share_cn, x="Year", y="Vehicle_sales_share", color="Transport_Vehicle_type", line_dash='Drive', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/archive/' + title + '.html')
fig.write_image("./plotting_output/static/archive" + title + '.png', scale=1, width=2000, height=800)


#%%
#lets take a look at what hugh was using
vehicle_sales_share_normalised = vehicle_sales_share_normalised[['Economy', 'Transport Type', 'Vehicle Type', 'Drive', 'Year', 'Vehicle_sales_share_normalised',
       'Scenario']]

#rename Vehicle_sales_share_normalised to Value
vehicle_sales_share_normalised = vehicle_sales_share_normalised.rename(columns={'Vehicle_sales_share_normalised':'Value'})

#plot the normalised version of the data from input data folder of 8th edition, whoch it seems hugh projected.
################################################################################################################################################################
title = 'Hughs vehicle_sales_share by year, transport type, vehicle type and economy in REF'

vehicle_sales_share_normalised['Transport_Vehicle_type']= vehicle_sales_share_normalised['Transport Type']+'_'+vehicle_sales_share_normalised['Vehicle Type']

#filter for ref scen
vehicle_sales_share_ref = vehicle_sales_share_normalised[vehicle_sales_share_normalised['Scenario']=='Reference']
#plot
fig = px.line(vehicle_sales_share_ref, x="Year", y="Value", color="Transport_Vehicle_type", line_dash='Drive', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/archive/' + title + '.html')
fig.write_image("./plotting_output/static/archive/" + title + '.png', scale=1, width=2000, height=800)

#filter for cn scen
vehicle_sales_share_cn = vehicle_sales_share_normalised[vehicle_sales_share_normalised['Scenario']=='Carbon Neutral']
#plot
fig = px.line(vehicle_sales_share_cn, x="Year", y="Value", color="Transport_Vehicle_type", line_dash='Drive', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

title = 'Hughs vehicle_sales_share by year, transport type, vehicle type and economy in CN'

plotly.offline.plot(fig, filename='./plotting_output/archive/' + title + '.html')
fig.write_image("./plotting_output/static/archive" + title + '.png', scale=1, width=2000, height=800)

# %%


# %%
