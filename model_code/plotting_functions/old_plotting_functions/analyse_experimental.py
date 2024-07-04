#a conglomeration of all the non standard graphs i created. They do not YET have code for reating their input data but it should be easy to add that in when you need the graph. So basically just coe here when you are thinking of designign a specifci kind of chart and see if it is already here. If not, add it in and then add the code to create the input data in the relevant place in the code.
#%%
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
if __name__ == "__main__": #this allows the script to be run directly or from the main.py file as you cannot use relative imports when running a script directly
    # Modify sys.path to include the directory where utility_functions is located
    sys.path.append(f"{config.root_dir}\\code")
    import utility_functions
else:
    # Assuming the script is being run from main.py located at the root of the project, we want to avoid using sys.path.append and instead use relative imports 
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

# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook
import matplotlib.pyplot as plt
plt.rcParams['figure.facecolor'] = 'w'


import plotly
import plotly.express as px
pd.options.plotting.backend = "plotly"#set pandas backend to plotly plotting instead of matplotlib
import plotly.io as pio
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook

#%%

#load data in
model_output_all = pd.read_csv(config.root_dir + '\\' + 'output_data\\model_output\\{}'.format(config.model_output_file_name))
model_output_detailed = pd.read_csv(config.root_dir + '\\' + 'output_data\\model_output_detailed\\{}'.format(config.model_output_file_name))

#FILTER FOR SCENARIO OF INTEREST
#this should be temporary as the scenario should be passed in as a parameter through config if it is useed elsewhere
config.SCENARIO_OF_INTEREST = 'Reference'
model_output_all = model_output_all[model_output_all['Scenario']==config.SCENARIO_OF_INTEREST]

################################################################################
################################################################################
################################################################################
#%%
#show the ratio of BEVs and PHEVs to ICEs by year, and economy (3d plot)
model_output_detailed_ratio_drive = model_output_detailed.groupby(['Date', 'Economy', 'Drive'])['Stocks'].sum().reset_index()

model_output_detailed_ratio_drive = model_output_detailed_ratio_drive.pivot(index=['Date', 'Economy'], columns='Drive', values='Stocks')

#replace any nan's with 0's
model_output_detailed_ratio_drive = model_output_detailed_ratio_drive.fillna(0)

model_output_detailed_ratio_drive['BEV_ICE_ratio'] = model_output_detailed_ratio_drive['bev'] / (model_output_detailed_ratio_drive['bev'] + model_output_detailed_ratio_drive['ice_g'] + model_output_detailed_ratio_drive['ice_d'])

model_output_detailed_ratio_drive['PHEV_ICE_ratio'] = (model_output_detailed_ratio_drive['phev_g'] +  model_output_detailed_ratio_drive['phev_d']) / (model_output_detailed_ratio_drive['phev_g'] +  model_output_detailed_ratio_drive['phev_d'] + model_output_detailed_ratio_drive['ice_g'] + model_output_detailed_ratio_drive['ice_d'])
# model_output_detailed_ratio_drive['PHEV_ICE_ratio'] = (model_output_detailed_ratio_drive['phev'] ) / (model_output_detailed_ratio_drive['phev'] + model_output_detailed_ratio_drive['ice'])

model_output_detailed_ratio_drive = model_output_detailed_ratio_drive[['BEV_ICE_ratio', 'PHEV_ICE_ratio']]

model_output_detailed_ratio_drive = model_output_detailed_ratio_drive.reset_index()

#%%
title = 'Experiemental 3d plot of ratios for BEV to ICE and PHEV to ICE'

fig = px.line_3d(model_output_detailed_ratio_drive, x="BEV_ICE_ratio", y="PHEV_ICE_ratio", z='Date', color='Economy')
fig.update_xaxes(range=[0, 1])
fig.update_yaxes(range=[0, 1])

plotly.offline.plot(fig, filename=config.root_dir + '\\' + 'plotting_output\\experimental\\' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# #fig.write_image(config.root_dir + '\\' + "\\plotting_output\\static\\" + title + '.png', scale=1, width=2000, height=800)

#%%
#lets take a look at this for Vehicle_sales_share instead of stocks

#show the ratio of BEVs and PHEVs to ICEs by year, and economy (3d plot)
model_output_detailed_ratio_drive = model_output_detailed.groupby(['Date', 'Economy', 'Drive'])['Vehicle_sales_share'].sum().reset_index()

model_output_detailed_ratio_drive = model_output_detailed_ratio_drive.pivot(index=['Date', 'Economy'], columns='Drive', values='Vehicle_sales_share')

#replace any nan's with 0's
model_output_detailed_ratio_drive = model_output_detailed_ratio_drive.fillna(0)

# model_output_detailed_ratio_drive['BEV_ICE_ratio'] = model_output_detailed_ratio_drive['bev'] / (model_output_detailed_ratio_drive['bev'] + model_output_detailed_ratio_drive['g'] + model_output_detailed_ratio_drive['d'])
model_output_detailed_ratio_drive['BEV_ICE_ratio'] = model_output_detailed_ratio_drive['bev'] / (model_output_detailed_ratio_drive['bev'] + model_output_detailed_ratio_drive['ice_g'] + model_output_detailed_ratio_drive['ice_d'])

model_output_detailed_ratio_drive['PHEV_ICE_ratio'] = (model_output_detailed_ratio_drive['phev_g'] +  model_output_detailed_ratio_drive['phev_d']) / (model_output_detailed_ratio_drive['phev_g'] +  model_output_detailed_ratio_drive['phev_d'] + model_output_detailed_ratio_drive['ice_g'] + model_output_detailed_ratio_drive['ice_d'])
# model_output_detailed_ratio_drive['PHEV_ICE_ratio'] = (model_output_detailed_ratio_drive['phev'] ) / (model_output_detailed_ratio_drive['phev'] + model_output_detailed_ratio_drive['ice'])

model_output_detailed_ratio_drive = model_output_detailed_ratio_drive[['BEV_ICE_ratio', 'PHEV_ICE_ratio']]

model_output_detailed_ratio_drive = model_output_detailed_ratio_drive.reset_index()

#%%
title = 'Experiemental 3d plot of sales share ratios for BEV to ICE and PHEV to ICE'

fig = px.line_3d(model_output_detailed_ratio_drive, x="BEV_ICE_ratio", y="PHEV_ICE_ratio", z='Date', color='Economy')
fig.update_xaxes(range=[0, 1])
fig.update_yaxes(range=[0, 1])

plotly.offline.plot(fig, filename=config.root_dir + '\\' + 'plotting_output\\experimental\\' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# #fig.write_image(config.root_dir + '\\' + "\\plotting_output\\static\\" + title + '.png', scale=1, width=2000, height=800)

#%%
#how about a graph which combines the two above so we can see the relationship between the sales and stock shares

################################################################################
################################################################################
################################################################################

#%%
#dont have change_dataframe_aggregation so we will skip this for now
change_dataframe_aggregation = None
if change_dataframe_aggregation is not None:
        
    #plot sum of activity and activity growth mean for each Date for each economy
    title = 'Activity and activity growth'
    change_dataframe_aggregation_act = change_dataframe_aggregation.groupby(['Date','Economy'])['Activity'].sum().reset_index()
    change_dataframe_aggregation_ag = change_dataframe_aggregation.groupby(['Date','Economy'])['Activity_growth'].mean().reset_index()


    #join the dataframes
    change_dataframe_aggregation_act_ag = change_dataframe_aggregation_act.merge(change_dataframe_aggregation_ag, on=['Date','Economy'])

    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    #create subplots specs list as a set of 3 lists with 7 dictionaries in each that are just {"secondary_y": True} to create 3 rows of 7 subplots each
    subplots_specs = [[{"secondary_y": True} for i in range(7)] for j in range(3)] 
    subplot_titles = change_dataframe_aggregation_act_ag['Economy'].unique().tolist()
    fig = make_subplots(rows=3, cols=7,
                        specs=subplots_specs,
                        subplot_titles=subplot_titles)

    col_number=0
    row_number = 1
    legend_set = False

    for economy in change_dataframe_aggregation_act_ag['Economy'].unique():
        #filter for economy
        change_dataframe_aggregation_act_ag_e = change_dataframe_aggregation_act_ag[change_dataframe_aggregation_act_ag['Economy']==economy]

        #set row and column number
        col_number +=1
        if col_number > 7:
            col_number = 1
            row_number += 1

        if (col_number == 1) & (row_number == 1):#set the legend for the first subplot, and tehrefore all of the subplots

            #create subplot for this economy
            legend_name = 'Activity'
            fig.add_trace(go.Scatter(x=change_dataframe_aggregation_act_ag_e['Date'], y=change_dataframe_aggregation_act_ag_e['Activity'],  legendgroup=legend_name, name=legend_name, line=dict(color='blue', width=2, )), row=row_number, col=col_number, secondary_y=False)

            legend_name = 'Activity_growth'
            fig.add_trace(go.Scatter(x=change_dataframe_aggregation_act_ag_e['Date'], y=change_dataframe_aggregation_act_ag_e['Activity_growth'], legendgroup=legend_name, name=legend_name, line=dict(color='red', dash='dot', width=2)), row=row_number, col=col_number, secondary_y=True)
        else:#legend is already set, so just add the traces with showlegend=False
            #create subplot for this economy
            legend_name = 'Activity'
            fig.add_trace(go.Scatter(x=change_dataframe_aggregation_act_ag_e['Date'], y=change_dataframe_aggregation_act_ag_e['Activity'],  legendgroup=legend_name, name=legend_name,showlegend=False, line=dict(color='blue', width=2, )), row=row_number, col=col_number, secondary_y=False)

            legend_name = 'Activity_growth'
            fig.add_trace(go.Scatter(x=change_dataframe_aggregation_act_ag_e['Date'], y=change_dataframe_aggregation_act_ag_e['Activity_growth'], legendgroup=legend_name, name=legend_name, showlegend=False, line=dict(color='red', dash='dot', width=2)), row=row_number, col=col_number, secondary_y=True)

    plotly.offline.plot(fig, filename=config.root_dir + '\\' + 'plotting_output\\' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
    #fig.write_image(config.root_dir + '\\' + "\\plotting_output\\static\\" + title + '.png', scale=1, width=2000, height=1500)



################################################################################
################################################################################
################################################################################

#%%
#plot vehicle efficiency vs new vehicle efficiency for all vehicles and drive types for each economy. BEcause there is so much information we wil create a new graph file individually for each vehicel type. this is going to create a lot of graphs but it has to be done 
#filter for medium = road
model_output_detailed_medium_road = model_output_detailed[model_output_detailed['Medium']=='road']
#for each in transport type:
for transport_type in model_output_detailed_medium_road['Transport Type'].unique():
    #filter 
    model_output_detailed_ttype = model_output_detailed_medium_road[model_output_detailed_medium_road['Transport Type']==transport_type]
    #for each vehicle type
    for vehicle in model_output_detailed_ttype['Vehicle Type'].unique():
        #filter
        model_output_detailed_vtype = model_output_detailed_ttype[model_output_detailed_ttype['Vehicle Type']==vehicle]
        #plot
        #create title
        title='Vehicle efficiency vs new vehicle efficiency for {} for {}'.format(vehicle, transport_type)
        #since we have the vehicle eff in the same scale we can just put the data in one column with a measure column. To do this use melt
        model_output_detailed_vtype_melt = model_output_detailed_vtype.melt(id_vars=['Date', 'Economy', 'Drive'], value_vars=['Efficiency', 'New_vehicle_efficiency'], var_name='Measure', value_name='Efficiency')

        fig = px.line(model_output_detailed_vtype_melt, x="Date", y="Efficiency", color="Drive", line_dash='Measure', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",

        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        plotly.offline.plot(fig, filename=config.root_dir + '\\' + 'plotting_output\\for_others\\' + title + '_' + vehicle + '_' + transport_type + '.html',auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
        #fig.write_image(config.root_dir + '\\' + "\\plotting_output\\static\\" + title + '_' + vehicle + '_' + transport_type + '.png', scale=1, width=2000, height=1500)



################################################################################
################################################################################
################################################################################


#plot efficiency of new vehicles by drive type vs efficiency of current stocks in use. #this is intended especially to see how the base Date efficiency of new vehicles compares to the efficiency of the current stocks in use. It should be a small difference only.. and efficiency of new stocks should be higher than current stocks.
model_output_detailed_eff_df = model_output_detailed[['Date', 'Economy', 'Vehicle Type', 'Transport Type', 'Drive', 'Efficiency', 'New_vehicle_efficiency']]

#melt the efficiency and new vehicle efficiency columns to one measur col
model_output_detailed_eff_df = pd.melt(model_output_detailed_eff_df, id_vars=['Date', 'Economy', 'Vehicle Type', 'Transport Type', 'Drive'], value_vars=['Efficiency', 'New_vehicle_efficiency'], var_name='Measure', value_name='Efficiency')

#create a new colun to concat the drive type, transport type and vehicle type
model_output_detailed_eff_df['Drive_Transport_Vehicle'] = model_output_detailed_eff_df['Drive'] + '_' + model_output_detailed_eff_df['Transport Type'] + '_' + model_output_detailed_eff_df['Vehicle Type']

#plot
title = 'Efficiency of new vehicles by drive type vs efficiency of current stocks in use'
fig = px.line(model_output_detailed_eff_df, x="Date", y="Efficiency", color="Drive_Transport_Vehicle", line_dash='Measure', facet_col="Economy", facet_col_wrap=7, title=title)
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

plotly.offline.plot(fig, filename=config.root_dir + '\\' + 'plotting_output\\input_exploration\\' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
#fig.write_image(config.root_dir + '\\' + "\\plotting_output\\input_exploration\\static\\" + title + '.png', scale=1, width=2000, height=800)

#%%
#plot the base Date efficiency values for new vehicles by drive type, transport type and vehicle type, vs the efficiency of the current stocks in use
#we will plot it using a boxplot so we can plot all economys in one plot, then separate plots for each vehicle_type/transport type 
model_output_detailed_eff_df = model_output_detailed[['Date', 'Economy', 'Vehicle Type', 'Transport Type', 'Drive', 'Efficiency', 'New_vehicle_efficiency']]

model_output_detailed_eff_df = model_output_detailed_eff_df[model_output_detailed_eff_df['Date']==config.DEFAULT_BASE_YEAR]

#melt the efficiency and new vehicle efficiency columns to one measur col
model_output_detailed_eff_df = pd.melt(model_output_detailed_eff_df, id_vars=['Date', 'Economy', 'Vehicle Type', 'Transport Type', 'Drive'], value_vars=['Efficiency', 'New_vehicle_efficiency'], var_name='Measure', value_name='Efficiency')

model_output_detailed_eff_df['Transport_Vehicle_Type'] =  model_output_detailed_eff_df['Transport Type'] + '_' + model_output_detailed_eff_df['Vehicle Type']

title = 'Box plot Efficiency of new vehicles by drive type vs efficiency of current stocks in use'
#plot
fig = px.box(model_output_detailed_eff_df, x="Drive", y="Efficiency", color="Measure", facet_col="Transport_Vehicle_Type", facet_col_wrap=6, title=title)
fig.update_traces(quartilemethod="exclusive") # or "inclusive", or "linear" by default

plotly.offline.plot(fig, filename=config.root_dir + '\\' + 'plotting_output\\input_exploration\\' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
#fig.write_image(config.root_dir + '\\' + "\\plotting_output\\input_exploration\\static\\" + title + '.png', scale=1, width=2000, height=1500)
#%%

#############################################################################################################################################################


################################################################################################################################################################
#%%
#show the uptake of BEVs by Date, per economy
title = 'Total stocks of BEVs for each Date, by economy'
model_output_detailed_bevs = model_output_detailed[model_output_detailed['Drive'] == 'bev']
model_output_detailed_bevs = model_output_detailed_bevs.groupby(['Date', 'Economy'])['Stocks'].sum().reset_index()

#plot
fig, ax = plt.subplots()
for key, grp in model_output_detailed_bevs.groupby(['Economy']):
    ax.plot(grp['Date'], grp['Stocks'], label=key)

plt.title(title)
plt.savefig(config.root_dir + '\\' + 'plotting_output\\diagnostics\\{}.png'.format(title))

#%%
################################################################################################################################################################
#plot the average vehivle sales shares for each economy for each Date, for LV's
title = 'Average vehicle sales shares for each drive for passenger lpvs'
model_output_detailed_sales = model_output_detailed[model_output_detailed['Vehicle Type'].isin(['lt', 'car', 'suv'])]
# #tet out excludeing china 05_PRC
# model_output_detailed_sales = model_output_detailed_sales[model_output_detailed_sales['Economy'] != '05_PRC']
model_output_detailed_sales = model_output_detailed_sales[model_output_detailed_sales['Transport Type'] == 'passenger']
model_output_detailed_sales = model_output_detailed_sales.groupby(['Date', 'Drive','Vehicle Type'])['Vehicle_sales_share'].mean().reset_index()

#plot
fig, ax = plt.subplots()
for key, grp in model_output_detailed_sales.groupby(['Drive','Vehicle Type']):
    ax.plot(grp['Date'], grp['Vehicle_sales_share'], label=key)
#legend
plt.legend(loc='best')


plt.title(title)
plt.savefig(config.root_dir + '\\' + 'plotting_output\\diagnostics\\{}.png'.format(title))
#%%