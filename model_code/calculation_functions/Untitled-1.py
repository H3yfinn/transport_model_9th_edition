#load in refined prod use in power.csv. then group and sum numeric only by these cols economy	sectors
#%%
import pandas as pd
import numpy as np
import os
import sys
import re
#make the folder ../../
os.chdir('../../')
power = pd.read_csv('refined prod use in power.csv')
#%%
#group by economy and sector
power_grouped = power.groupby(['economy','sectors']).sum(numeric_only=True).reset_index()
#drop is_subtotal
power_grouped = power_grouped.drop(columns=['is_subtotal'])

#melt the cols that are not economy and sector
power_melted = power_grouped.melt(id_vars=['economy','sectors'], var_name='year', value_name='value')
#pivot the sectors col
power_pivoted = power_melted.pivot(index=['economy','year'], columns='sectors', values='value').reset_index()

#convert all cols to absolute
power_pivoted['09_total_transformation_sector'] = power_pivoted['09_total_transformation_sector'].abs()
power_pivoted['07_total_primary_energy_supply'] = power_pivoted['07_total_primary_energy_supply'].abs()
power_pivoted['12_total_final_consumption'] = power_pivoted['12_total_final_consumption'].abs()

#calc 09_total_transformation_sector/ 07_total_primary_energy_supply as a new col as well as 09_total_transformation_sector /12_total_final_consumption
power_pivoted['transformation/supply'] = (power_pivoted['09_total_transformation_sector']/power_pivoted['07_total_primary_energy_supply']) * 100

power_pivoted['transformation/consumption'] = (power_pivoted['09_total_transformation_sector']/power_pivoted['12_total_final_consumption']) * 100

#calc average across the years 2010 to 2019
power_pivoted = power_pivoted.loc[power_pivoted['year'].isin(['2010','2011','2012','2013','2014','2015','2016','2017','2018','2019'])]
#%%
power_pivoted = power_pivoted.groupby('economy').mean().reset_index()
#%%
#now plot it all using plotly so we have economy on x
import plotly.express as px

fig = px.bar(power_pivoted, x='economy', y='transformation/supply', title='09_total_transformation_sector/ 07_total_primary_energy_supply')
fig.write_html('transformation_supply.html')

fig = px.bar(power_pivoted, x='economy', y='transformation/consumption', title='09_total_transformation_sector/ 12_total_final_consumption')
fig.write_html('transformation_consumption.html')  




#%%
