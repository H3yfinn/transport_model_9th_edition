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
#laod data
df = pd.read_excel('other_code/other_data/iea-outlook-data-transport.xlsx', sheet_name = 'IEA-EV-data', header = 0)

#load our data for the latest outlook run
df_outlook = pd.read_csv('output_data/model_output_detailed/{}'.format(config.model_output_file_name))
#%%
#rename some columns so i may merge with my own data to compare (probably wont thoguh)
df.rename(columns = {'parameter':'Measure', 'powertrain': 'Drive', 'mode' : 'Vehicle Type'}, inplace = True)

#%%
#analyse some data to explore:
# df['Vehicle Type'].unique()#array(['Cars', 'EV', 'Trucks', 'Vans', 'Buses'], dtype=object)

# df['Drive'].unique()#array(['BEV', 'EV', 'PHEV', 'Publicly available fast',
    #    'Publicly available slow'], dtype=object)

# df['Measure'].unique()#array(['EV sales', 'EV stock', 'EV sales share', 'EV stock share',
    #    'EV charging points', 'Oil displacement Mbd',
    #    'Oil displacement Mlge', 'Electricity demand'], dtype=object)

#%%
#decapitilase data in all columns
new_df = df.applymap(lambda s:s.lower() if type(s) == str else s)

#%%
#get together the data we want to analyse for ogss report
new_df.reset_index(inplace = True, drop=True)

#filter for only region = world since we only have 'china', 'europe', 'india', 'rest of the world', 'usa', 'world'
new_df = new_df[new_df['region'] == 'world']

#for simplicity we will grab only cars data
new_df = new_df[new_df['Vehicle Type'] == 'cars']

#filter for only bev (and perhaps ev) data
new_df = new_df[new_df['Drive'].isin(['bev', 'ev'])]

#filter for 'projection- steps' and historical in category
new_df = new_df[new_df['category'].isin(['projection-steps', 'historical'])]

#group into datasets for each measure
df_stocks_sales = new_df.loc[new_df['Measure'].isin(['ev sales', 'ev stock'])]

df_shares = new_df.loc[new_df['Measure'].isin(['ev sales share', 'ev stock share'])]

df_energy_use = new_df.loc[new_df['Measure'].isin(['electricity demand','oil displacement mbd'])]

df_stocks_sales_share = new_df.loc[new_df['Measure'].isin(['ev sales share', 'ev stock share','ev sales', 'ev stock'])]
#%%
#convert mbd to mb and then to pj
#so mbd *365 *6.12
df_energy_use.loc[df_energy_use['Measure'] == 'oil displacement mbd', 'value'] = df_energy_use.loc[df_energy_use['Measure'] == 'oil displacement mbd', 'value']*365*6.12

#convert elec gwh to pj by multiplying by 0.0036
df_energy_use.loc[df_energy_use['Measure'] == 'electricity demand', 'value'] = df_energy_use.loc[df_energy_use['Measure'] == 'electricity demand', 'value'] * 0.0036


#%%
#plot a graph of EV stocks vs sales
#plot energy use by fuel type

title='Energy use in evs vs oil displacement based on iea data'
#plot using plotly
fig = px.line(df_energy_use, x="year", y="value", color="Measure", title=title)

plotly.offline.plot(fig, filename='./plotting_output/other_datasets/{}.html'.format(title), auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/other_datasets/static/" + title + '.png', scale=1, width=2000, height=800)


#%%
#Want to plot a double y axis graph of stocks and sales share, with 2 lines for each, so we will just crate a df with a column for each line.

#create column for stocks, and column for sales share values. to do this we will create a column that is either stocks or sales share and then we will pivot using this column
df_stocks_sales_share_plot = df_stocks_sales_share.copy()
# #if measure is either 'ev sales' or 'ev stock' then set the column to 'stocks_sales'
# df_stocks_sales_share_plot['unit'] = df_stocks_sales_share_plot['Measure'].apply(lambda x: 'stocks' if x in ['ev sales', 'ev stock'] else 'sales_share')

#for the years 2020 and 2021 we will remove the data where category is projection-steps because we already have historical data for these years
df_stocks_sales_share_plot = df_stocks_sales_share_plot[~((df_stocks_sales_share_plot['year'].isin([2020, 2021])) & (df_stocks_sales_share_plot['category'] == 'projection-steps'))]

#pivot the data so that we have a column for each unique measue
#first drop cols we dont need
df_stocks_sales_share_plot.drop(columns = ['region', 'Vehicle Type', 'Drive', 'unit'], inplace = True)

#convert any values less than 0 to 0
df_stocks_sales_share_plot.loc[df_stocks_sales_share_plot['value'] < 0, 'value'] = 0
#then pivot
df_stocks_sales_share_plot = df_stocks_sales_share_plot.pivot(index = ['year'], columns = 'Measure', values = 'value').reset_index()

#%%
AUTO_OPEN_PLOTLY_GRAPHS = False
title='Stocks and sales share of evs in cars in the world from the iea data (projected from 2022 onwards)'

import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig = make_subplots(specs=[[{"secondary_y": True}]])

fig.add_trace(
    go.Bar(x=df_stocks_sales_share_plot['year'], y=df_stocks_sales_share_plot['ev sales'], name='ev sales'), secondary_y=False)

fig.add_trace(
    go.Bar(x=df_stocks_sales_share_plot['year'], y=df_stocks_sales_share_plot['ev stock'], name='ev stock'),     secondary_y=False)

fig.add_trace(
    go.Scatter(x=df_stocks_sales_share_plot['year'], y=df_stocks_sales_share_plot['ev sales share'], name='ev sales share'), secondary_y=True)

fig.add_trace(
    go.Scatter(x=df_stocks_sales_share_plot['year'], y=df_stocks_sales_share_plot['ev stock share'], name='ev stock share'), secondary_y=True)

# Add figure title
fig.update_layout(
    title_text=title, barmode='group')

# Set x-axis title
fig.update_xaxes(title_text="year")

# Set y-axes titles
fig.update_yaxes(title_text="<b>primary</b> absolute", secondary_y=False)
fig.update_yaxes(title_text="<b>secondary</b> percent", secondary_y=True)

plotly.offline.plot(fig, filename='./plotting_output/other_datasets/{}.html'.format(title), auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/other_datasets/static/" + title + '.png', scale=1, width=2000, height=800)
#%%
%matplotlib inline

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
pd.options.plotting.backend = "matplotlib"
#%%

#lets jsut see what will happen if we project the stocks and sales share data to 2050
#first we will calculate number of ice's as (stocks/'stocks share')-stocks 
#and the share of ices in stocks as (1-stocks share)
#and the number of ice sales as (sales/sales share)-sales
#and the share of ice sales as (1-sales share)

#then we can project our ev stocks data forward to 2050
model_data = df_stocks_sales_share_plot.copy()

#convert shares to percentages bydiviidng by 100
model_data['ev sales share'] = model_data['ev sales share']/100
model_data['ev stock share'] = model_data['ev stock share']/100

#now do calcs
model_data['ice stock'] = (model_data['ev stock']/model_data['ev stock share'])-model_data['ev stock']
model_data['ice stock share'] = 1-model_data['ev stock share']
model_data['ice sales'] = (model_data['ev sales']/model_data['ev sales share'])-model_data['ev sales']
model_data['ice sales share'] = 1-model_data['ev sales share']

#make index the year
model_data.set_index('year', inplace = True)
#insert missing years as nan
model_data = model_data.reindex(range(model_data.index.min(), model_data.index.max()+1), fill_value=np.nan)
#%%
model_data_interp = model_data.copy()
#there are negative ice sales in 2021 so we will replace the stocks and sales and shares values with nan to be fixed by interpolation 
model_data_interp.loc[2021, 'ice stock'] = np.nan

#we also have weird values for <2014 because the shares of sales for evs are so low. We will just remove all values before 2014
model_data_interp = model_data_interp[model_data_interp.index >= 2014]

#perfrom linear interpolation on years that are missing for ev ev stocks and ice stocks, then calulate sales and shares using these values
#we will use linear interp on our ice data but a polynomial interp on our ev data. this is because wiht poly on ice we end up with negative sales in 2030, which shouldnt happen
model_data_interp[['ev stock']] = model_data_interp[['ev stock']].interpolate(method='spline',order=2, axis=0).ffill().bfill()
model_data_interp[['ice stock']] = model_data_interp[['ice stock']].interpolate(method='linear', axis=0).ffill().bfill()

#%%
#now we can calculate sales and shares for interpolated values
model_data_interp['ev sales'] = model_data_interp['ev stock'].diff()
model_data_interp['ice sales'] = model_data_interp['ice stock'].diff()

# #we have a few values that are negative, so we will set these to 0, just as an easy fix
# model_data_interp.loc[model_data_interp['ev sales'] < 0, 'ev sales'] = 0
# model_data_interp.loc[model_data_interp['ice sales'] < 0, 'ice sales'] = 0

model_data_interp['ev sales share'] = model_data_interp['ev sales']/(model_data_interp['ev sales']+model_data_interp['ice sales'])
model_data_interp['ice sales share'] = model_data_interp['ice sales']/(model_data_interp['ev sales']+model_data_interp['ice sales'])

model_data_interp['ev stock share'] = model_data_interp['ev stock']/(model_data_interp['ev stock']+model_data_interp['ice stock'])
model_data_interp['ice stock share'] = model_data_interp['ice stock']/(model_data_interp['ev stock']+model_data_interp['ice stock'])

model_data_interp.index = pd.to_datetime(model_data_interp.index, format='%Y')
#%%
#get data we will project
model1 = model_data_interp['ev stock']

# Construct the model
mod = sm.tsa.SARIMAX(model1, order=(1, 0, 0), trend=[1,1,1])
# Estimate the parameters
res = mod.fit()
show_stats_details = True
if show_stats_details:
    print(res.summary())
    # The default is to get a one-step-ahead forecast:
    print(res.forecast())
    # Here we construct a more complete results object.
    fcast_res1 = res.get_forecast()

    # Most results are collected in the `summary_frame` attribute.

    # Here we specify that we want a confidence level of 90%
    print(fcast_res1.summary_frame(alpha=0.10))
    print(res.forecast(steps=20))
    fcast_res2 = res.get_forecast(steps=20)
    # Note: since we did not specify the alpha parameter, the
    # confidence level is at the default, 95%
    print(fcast_res2.summary_frame())
    print(res.forecast(steps=20))
    fcast_res3 = res.get_forecast(steps=20)
    print(fcast_res3.summary_frame())

#%%
#plot the results
fig, ax = plt.subplots(figsize=(15, 5))

# Plot the data 
model1.plot(ax=ax)

# Construct the forecasts
fcast_ev = res.get_forecast(20).summary_frame()
fcast_ev['mean'].plot(ax=ax, style='k--')
ax.fill_between(fcast_ev.index, fcast_ev['mean_ci_lower'], fcast_ev['mean_ci_upper'], color='k', alpha=0.1)

#%%
#also do the same froecast for ice stocks
model2 = model_data_interp['ice stock']

# Construct the model
mod = sm.tsa.SARIMAX(model2, order=(1, 0, 0), trend=[1,1,1])
# Estimate the parameters
res = mod.fit()

#plot the results
fig, ax = plt.subplots(figsize=(15, 5))

# Plot the data 
model2.plot(ax=ax)

# Construct the forecasts
fcast_ice = res.get_forecast(20).summary_frame()
fcast_ice['mean'].plot(ax=ax, style='k--')
ax.fill_between(fcast_ice.index, fcast_ice['mean_ci_lower'], fcast_ice['mean_ci_upper'], color='k', alpha=0.1)
#%%
fcast_ev_stocks = fcast_ev['mean'].to_frame()
fcast_ev_stocks.rename(columns = {'mean':'ev stock'}, inplace = True)

fcast_ice_stocks = fcast_ice['mean'].to_frame()
fcast_ice_stocks.rename(columns = {'mean':'ice stock'}, inplace = True)

#join the two dataframes
fcast_stocks = fcast_ev_stocks.join(fcast_ice_stocks, how = 'outer')

#concat the data
model_data_fcast = pd.concat([model_data_interp, fcast_stocks], axis = 0)

#calcualte sales as the diff each year
model_data_fcast['ev sales'] = model_data_fcast['ev stock'].diff()
model_data_fcast['ice sales'] = model_data_fcast['ice stock'].diff()

#we have a few values that are negative, so we will set these to 0, just as an easy fix
model_data_fcast.loc[model_data_fcast['ice sales'] < 0, 'ice sales'] = 0

#now we can calculate shares 
model_data_fcast['ev sales share'] = model_data_fcast['ev sales']/(model_data_fcast['ev sales']+model_data_fcast['ice sales'])
model_data_fcast['ice sales share'] = model_data_fcast['ice sales']/(model_data_fcast['ev sales']+model_data_fcast['ice sales'])

model_data_fcast['ev stock share'] = model_data_fcast['ev stock']/(model_data_fcast['ev stock']+model_data_fcast['ice stock'])
model_data_fcast['ice stock share'] = model_data_fcast['ice stock']/(model_data_fcast['ev stock']+model_data_fcast['ice stock'])

#%%
#now plot again
#prepare data
model_data_fcast_plot = model_data_fcast.reset_index()
#rename year column
model_data_fcast_plot.rename(columns = {'index':'year'}, inplace = True)

AUTO_OPEN_PLOTLY_GRAPHS = True
title='Stocks and sales share of evs in cars in the world forecasted using the iea data (projected from 2022 to 2050)'

import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig = make_subplots(specs=[[{"secondary_y": True}]])

#evs
fig.add_trace(
    go.Bar(x=model_data_fcast_plot['year'], y=model_data_fcast_plot['ev sales'], name='ev sales'), secondary_y=False)

fig.add_trace(
    go.Bar(x=model_data_fcast_plot['year'], y=model_data_fcast_plot['ev stock'], name='ev stock'),     secondary_y=False)

#ices
fig.add_trace(
    go.Bar(x=model_data_fcast_plot['year'], y=model_data_fcast_plot['ice sales'], name='ice sales'), secondary_y=False)


fig.add_trace(
    go.Bar(x=model_data_fcast_plot['year'], y=model_data_fcast_plot['ice stock'], name='ice stock'), secondary_y=False)

#evs
fig.add_trace(
    go.Scatter(x=model_data_fcast_plot['year'], y=model_data_fcast_plot['ev sales share'], name='ev sales share'), secondary_y=True)

fig.add_trace(
    go.Scatter(x=model_data_fcast_plot['year'], y=model_data_fcast_plot['ev stock share'], name='ev stock share'), secondary_y=True)

#ices
fig.add_trace(
    go.Scatter(x=model_data_fcast_plot['year'], y=model_data_fcast_plot['ice sales share'], name='ice sales share'), secondary_y=True)

fig.add_trace(
    go.Scatter(x=model_data_fcast_plot['year'], y=model_data_fcast_plot['ice stock share'], name='ice stock share'), secondary_y=True)


# Add figure title
fig.update_layout(
    title_text=title, barmode='group')

# Set x-axis title
fig.update_xaxes(title_text="year")

# Set y-axes titles
fig.update_yaxes(title_text="<b>primary</b> absolute", secondary_y=False)
fig.update_yaxes(title_text="<b>secondary</b> percent", secondary_y=True)

plotly.offline.plot(fig, filename='./plotting_output/other_datasets/{}.html'.format(title), auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/other_datasets/static/" + title + '.png', scale=1, width=2000, height=800)

#%%


#i think the problem is that we also need to look at turnober. but once we do that then we will just be creating another transport model.



#%%
#lets graph  EV electriicty dmeand vs oil displacement




# %%
