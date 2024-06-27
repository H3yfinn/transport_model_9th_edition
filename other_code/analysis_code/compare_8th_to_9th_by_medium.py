#take in output data and do basic visualisationh and analysis

#TO DO THIS I FIRST NEED TO GET BY FUEL FROM 8TH AND MAKE SURE THE FUELS MATCH UP. SHOUDLNT BE TOO HARD.
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
#compare model output to 8th edition output. If there are any differences, print them
#laod output from 8th edition
model_output = pd.read_csv('output_data/model_output_detailed/{}'.format(config.model_output_file_name))
model_output_8th = pd.read_csv('intermediate_data/activity_efficiency_energy_road_stocks.csv')

#%%
#keep only columns in model_output_8th
model_output = model_output[model_output.columns.intersection(model_output_8th.columns)]

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
#plot energy use
#sum up data for energy use by year, medium, economy, in both scenarios for each dataset
model_output_concat_sum = model_output_concat.groupby(['Year', 'Scenario', 'Economy', 'Medium', 'Dataset'], as_index=False).sum()

#join together the medium and scenario columns
model_output_concat_sum['Medium_Scenario'] = model_output_concat_sum['Medium'] + '_' + model_output_concat_sum['Scenario']

#drop medium and scenario
model_output_concat_sum = model_output_concat_sum.drop(['Medium', 'Scenario'], axis=1)
#find ratio between values in 8th and 9th edition. First we have to melt so we have all values in one column and their variable names as a measure column. Then pvito so we have a column for each dataset's values
model_output_concat_sum_melt = model_output_concat_sum.melt(id_vars=['Year', 'Economy', 'Dataset', 'Medium_Scenario'], var_name='Measure', value_name='Value').reset_index(drop=True)
Ratio = model_output_concat_sum_melt.pivot(index=['Year', 'Economy', 'Medium_Scenario', 'Measure'], columns='Dataset', values='Value').reset_index()
Ratio['Ratio_9th_div_8th'] = Ratio['9th']/Ratio['8th']
#%%
################################################################################################################################################################

title='Energy use by year, economy, in both scenarios, for each medium, USA and PRC removed'

model_output_concat_sum_other_regions = model_output_concat_sum[~model_output_concat_sum['Economy'].isin(['05_PRC', '20_USA'])]

#plot
fig = px.line(model_output_concat_sum_other_regions, x="Year", y="Energy", color="Medium_Scenario", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles


plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)


#%%
################################################################################
################################################################################
title='Energy use by year, economy, medium in both scenarios'

#plot
fig = px.line(model_output_concat_sum, x="Year", y="Energy", color="Medium_Scenario", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

#%%
################################################################################################################################################################
title='Activity by year, economy, in both scenarios, for each medium, USA and PRC removed'

model_output_concat_sum_other_regions = model_output_concat_sum[~model_output_concat_sum['Economy'].isin(['05_PRC', '20_USA'])]

#plot
fig = px.line(model_output_concat_sum_other_regions, x="Year", y="Activity", color="Medium_Scenario", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles


plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

#%%
################################################################################
################################################################################
title='Activity use by year, economy, medium in both scenarios'

#plot
fig = px.line(model_output_concat_sum, x="Year", y="Activity", color="Medium_Scenario", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles


plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)


#%%
################################################################################################################################################################
title='Stocks by year, economy, in both scenarios, for each vehicle type, USA and PRC removed'

model_output_concat_sum_stocks = model_output_concat.groupby(['Year', 'Scenario', 'Economy', 'Medium', 'Vehicle Type', 'Dataset'], as_index=False).sum()

#filte rfor road only
model_output_concat_sum_stocks = model_output_concat_sum_stocks[model_output_concat_sum_stocks['Medium'].isin(['road'])]

model_output_concat_sum_stocks_other_regions = model_output_concat_sum_stocks[~model_output_concat_sum_stocks['Economy'].isin(['05_PRC', '20_USA'])]

#create vehicle type + scenario column
model_output_concat_sum_stocks_other_regions['Vehicle_Scenario'] = model_output_concat_sum_stocks_other_regions['Vehicle Type'] + '_' + model_output_concat_sum_stocks_other_regions['Scenario']

#plot
fig = px.line(model_output_concat_sum_stocks_other_regions, x="Year", y="Stocks", color="Vehicle_Scenario", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

#%%
################################################################################################################################################################
title='Stocks by year, economy, in both scenarios, for each vehicle type'

#create vehicle type + scenario column
model_output_concat_sum_stocks['Vehicle_Scenario'] = model_output_concat_sum_stocks['Vehicle Type'] + '_' + model_output_concat_sum_stocks['Scenario']

#plot
fig = px.line(model_output_concat_sum_stocks, x="Year", y="Stocks", color="Vehicle_Scenario", line_dash='Dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

#%%

