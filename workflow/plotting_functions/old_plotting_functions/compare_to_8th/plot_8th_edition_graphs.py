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
import config
####Use this to load libraries and set variables. Feel free to edit that file as you need.

import plotly
import plotly.express as px
pd.options.plotting.backend = "plotly"#set pandas backend to plotly plotting instead of matplotlib
import plotly.io as pio
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook
#%%
font_size = 20
AUTO_OPEN_PLOTLY_GRAPHS = True
#%%
#laod output from 8th edition
model_output_8th = pd.read_csv('intermediate_data/activity_efficiency_energy_road_stocks.csv')
model_8th_by_fuel = pd.read_csv('intermediate_data/cleaned_input_data/energy_with_fuel.csv')
config.SCENARIO_OF_INTEREST = 'Reference'
#change 'Carbon Neutral' Scenario to Carbon Neutrality
model_output_8th.loc[model_output_8th['Scenario']=='Carbon Neutral','Scenario'] = 'Carbon Neutrality'
model_8th_by_fuel.loc[model_8th_by_fuel['Scenario']=='Carbon Neutral','Scenario'] = 'Carbon Neutrality'
#%%
#plot energy use
#sum up data for energy use by Date, medium, economy, transport type, vehicle type and drive in both scenarios for each dataset
model_output_8th_sum = model_output_8th.groupby(['Date', 'Scenario', 'Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive'], as_index=False).sum()

#join together the  'Transport Type', 'Vehicle Type', 'Drive' and 'Scenario' columns
model_output_8th_sum['TransportType_VehicleType_Drive_Scenario'] = model_output_8th_sum['Transport Type'] + '_' + model_output_8th_sum['Vehicle Type'] + '_' + model_output_8th_sum['Drive'] + '_' + model_output_8th_sum['Scenario']

#%%
#filter dfata from after 2050
model_output_8th_sum = model_output_8th_sum[model_output_8th_sum['Date']<=2050]
# model_output_8th_sum = model_output_8th_sum[model_output_8th_sum['Scenario']==config.SCENARIO_OF_INTEREST]

#create verison of dataframe that doesnt have  economy groupings
model_output_8th_sum_no_economy = model_output_8th_sum.copy()
model_output_8th_sum_no_economy = model_output_8th_sum_no_economy.drop(columns=['Economy'])
model_output_8th_sum_no_economy = model_output_8th_sum_no_economy.groupby(['Date', 'Scenario', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive'], as_index=False).sum()
#%%
model_8th_by_fuel_no_economy = model_8th_by_fuel.copy()
model_8th_by_fuel_no_economy = model_8th_by_fuel_no_economy.drop(columns=['Economy'])
model_8th_by_fuel_no_economy = model_8th_by_fuel_no_economy.groupby(['Date', 'Scenario', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Fuel'], as_index=False).sum()

#keep pre 2050
model_8th_by_fuel_no_economy = model_8th_by_fuel_no_economy[model_8th_by_fuel_no_economy['Date']<=2050]
#%%
# #join onto original df
# model_output_8th_sum = model_output_8th_sum.merge(model_output_concat_sum_sales[['Date', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Sales share']], on=['Date', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive'], how='left')
#%%

################################################################################################################################################################

#CALCULATE SALES SHARE FOR NO ECONOMY
#sum stocks by Date, vehicle type, drive type, dataset
model_output_concat_sum_sales = model_output_8th_sum_no_economy.groupby(['Date', 'Transport Type', 'Vehicle Type','Scenario', 'Drive'], as_index=False).sum()
#claulcate sales as teh schange in stocks each eyar
model_output_concat_sum_sales['Sales'] = model_output_concat_sum_sales.groupby(['Transport Type', 'Vehicle Type','Scenario', 'Drive'])['Stocks'].diff()
#set any negatives to 0
model_output_concat_sum_sales['Sales'] = model_output_concat_sum_sales['Sales'].clip(lower=0)
#create a column that is the sum of sales by Date, transport type and Scenario
model_output_concat_sum_sales['Sales_sum'] = model_output_concat_sum_sales.groupby(['Date','Transport Type','Vehicle Type', 'Scenario'])['Sales'].transform('sum')
#calculate sales share
model_output_concat_sum_sales['Sales share'] = model_output_concat_sum_sales['Sales'] / model_output_concat_sum_sales['Sales_sum']
#drop Sales_sum and reg measures
model_output_concat_sum_sales = model_output_concat_sum_sales.drop(columns=['Sales_sum','Activity','Efficiency','Energy','Stocks'])
#merge with the model output data using left join
model_output_8th_with_sales_share = model_output_8th_sum_no_economy.merge(model_output_concat_sum_sales, how='left', on=['Date', 'Transport Type', 'Vehicle Type','Scenario', 'Drive'])

#%%
#CALCUALTE SALES SHARE FOR ECONOMY
#sum stocks by Date, vehicle type, drive type, dataset
model_output_concat_sum_sales_with_economy = model_output_8th_sum.groupby(['Date', 'Transport Type', 'Vehicle Type','Scenario', 'Drive'], as_index=False).sum()
#claulcate sales as teh schange in stocks each eyar
model_output_concat_sum_sales_with_economy['Sales'] = model_output_concat_sum_sales_with_economy.groupby(['Transport Type', 'Vehicle Type','Scenario', 'Drive', 'Economy'])['Stocks'].diff()
#set any negatives to 0
model_output_concat_sum_sales_with_economy['Sales'] = model_output_concat_sum_sales_with_economy['Sales'].clip(lower=0)
#create a column that is the sum of sales by Date, transport type and Scenario
model_output_concat_sum_sales_with_economy['Sales_sum'] = model_output_concat_sum_sales_with_economy.groupby(['Date','Transport Type','Vehicle Type', 'Scenario', 'Economy'])['Sales'].transform('sum')
#calculate sales share
model_output_concat_sum_sales_with_economy['Sales share'] = model_output_concat_sum_sales_with_economy['Sales'] / model_output_concat_sum_sales_with_economy['Sales_sum']
#drop Sales_sum and reg measures
model_output_concat_sum_sales_with_economy = model_output_concat_sum_sales_with_economy.drop(columns=['Sales_sum','Activity','Efficiency','Energy','Stocks'])
#merge with the model output data using left join
model_output_8th_with_sales_share = model_output_8th_sum.merge(model_output_concat_sum_sales_with_economy, how='left', on=['Date', 'Transport Type', 'Vehicle Type','Scenario', 'Drive', 'Economy'])

#save this data for use later on:
#%%
















################################################################################################################################################################
#plot sales share of each drive type, in the lv vehicle type, on the same graph as the stocks of each drive type in the lv vehicle type, for each economy, Date
#this is to show the relationship between the sales share and the stock share


#NOW START FILTERING DATA FOR PLOTTING:

#filter for passenger transport
model_output_8th_sum_lv_passenger = model_output_8th_with_sales_share[model_output_8th_with_sales_share['Transport Type']=='passenger']

#filter for lv, lt and 2w then sum up data for lv and lt vehicles to create ldv and 2w vehicle types
model_output_8th_sum_no_economy_lv = model_output_8th_sum_lv_passenger[(model_output_8th_sum_lv_passenger['Vehicle Type'] == 'lv') | (model_output_8th_sum_lv_passenger['Vehicle Type'] == 'lt') | (model_output_8th_sum_lv_passenger['Vehicle Type'] == '2w')]
model_output_8th_sum_lv_passenger.loc[model_output_8th_sum_lv_passenger['Vehicle Type'] == 'lv', 'Vehicle Type'] = 'ldv'
model_output_8th_sum_no_economy_lv.loc[model_output_8th_sum_no_economy_lv['Vehicle Type'] == 'lt', 'Vehicle Type'] = 'ldv'
model_output_8th_sum_lv_passenger = model_output_8th_sum_no_economy_lv.groupby(['Date', 'Scenario', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive'], as_index=False).sum()

model_output_concat_sum_sales = model_output_8th_sum_lv_passenger[model_output_8th_sum_lv_passenger['Medium'] == 'road']

#filter data out from before 2022
model_output_8th_sum_lv_passenger = model_output_8th_sum_lv_passenger[model_output_8th_sum_lv_passenger['Date'] >= 2022]
#sort the scenario col so that it it is in reverse alphabetical order
SCENARIO_ORDER = ['Reference', 'Carbon Neutrality']

#filter for only 'bev' and 'g' and 'd' drive types. then combine 'g' and 'd' into 'ice' drive type
model_output_concat_sum_lv_passenger = model_output_8th_sum_lv_passenger[(model_output_8th_sum_lv_passenger['Drive'] == 'bev') | (model_output_8th_sum_lv_passenger['Drive'] == 'g') | (model_output_8th_sum_lv_passenger['Drive'] == 'd')]
model_output_concat_sum_lv_passenger.loc[model_output_concat_sum_lv_passenger['Drive'] == 'g', 'Drive'] = 'ice'
model_output_concat_sum_lv_passenger.loc[model_output_concat_sum_lv_passenger['Drive'] == 'd', 'Drive'] = 'ice'
#sum
model_output_8th_sum_lv_passenger = model_output_concat_sum_lv_passenger.groupby(['Date', 'Scenario', 'Medium', 'Transport Type', 'Vehicle Type', 'Drive'], as_index=False).sum()

#%%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

#we will run the following grapoh creation for 2w and then ldvs:
for vehicle_type in ['2w', 'ldv']:
    title='Stocks and sales of each drive type in passenger transport, {}'.format(vehicle_type)
    #filter for the vehicle type of interest
    model_output_8th_plot_df = model_output_8th_sum_lv_passenger[model_output_8th_sum_lv_passenger['Vehicle Type']==vehicle_type]

    #set max values for y axis using the max values of the stocks and sales columns
    max_y_stocks = model_output_8th_plot_df['Stocks'].max()
    max_y_sales = model_output_8th_plot_df['Sales share'].max()


    #create subplots specs list as a set of X lists with Y dictionaries in each that are just {"secondary_y": True} to create X rows of Y subplots each
    subplots_specs = [[{"secondary_y": True} for i in range(2)] for j in range(1)] 
    subplot_titles = SCENARIO_ORDER
    fig = make_subplots(rows=1, cols=2,
                        specs=subplots_specs,
                        subplot_titles=subplot_titles)

    col_number=0
    row_number = 1
    legend_set = False
    drive_list = model_output_8th_plot_df['Drive'].unique().tolist()

    for economy in SCENARIO_ORDER:
        #filter for economy
        model_output_8th_plot_df_economy = model_output_8th_plot_df[model_output_8th_plot_df['Scenario']==economy]

        #set row and column number
        col_number +=1
        
        #NOW GO THROUGH EACH DRIVE TYPE AND PLOT THE STOCKS AND SALES OF EACH DRIVE TYPE IN THE LV VEHICLE TYPE
        for drive_type in drive_list:
            #get the index of the current drive
            drive_type_index = drive_list.index(drive_type)
            #GET THE COLOUR WE'LL USE FOR THIS DRIVE TYPE using the index
            color = px.colors.qualitative.Plotly[drive_type_index]
            
            #get the data for this drive type
            model_output_8th_plot_df_economy_drive = model_output_8th_plot_df_economy[model_output_8th_plot_df_economy['Drive']==drive_type]

            if (col_number == 1) & (row_number == 1):#set the legend for the first subplot, and tehrefore all of the subplots

                #create subplot for this economy AND DRIVE
                legend_name = drive_type + '_Stocks'
                fig.add_trace(go.Scatter(x=model_output_8th_plot_df_economy_drive['Date'], y=model_output_8th_plot_df_economy_drive['Stocks'],  legendgroup=legend_name, name=legend_name, line=dict(color=color, width=2, )), row=row_number, col=col_number, secondary_y=False)

                legend_name = drive_type + '_Vehicle_sales_share'
                fig.add_trace(go.Scatter(x=model_output_8th_plot_df_economy_drive['Date'], y=model_output_8th_plot_df_economy_drive['Sales share'], legendgroup=legend_name, name=legend_name, line=dict(color=color, dash='dot', width=2)), row=row_number, col=col_number, secondary_y=True)
            else:#legend is already set, so just add the traces with showlegend=False
                #create subplot for this economy AND DRIVE
                legend_name = drive_type + '_Stocks'
                fig.add_trace(go.Scatter(x=model_output_8th_plot_df_economy_drive['Date'], y=model_output_8th_plot_df_economy_drive['Stocks'],  legendgroup=legend_name, name=legend_name,showlegend=False, line=dict(color=color, width=2, )), row=row_number, col=col_number, secondary_y=False)

                legend_name = drive_type + '_Vehicle_sales_share'
                fig.add_trace(go.Scatter(x=model_output_8th_plot_df_economy_drive['Date'], y=model_output_8th_plot_df_economy_drive['Sales share'], legendgroup=legend_name, name=legend_name, showlegend=False, line=dict(color=color, dash='dot', width=2)), row=row_number, col=col_number, secondary_y=True)

            #set the y axis titles
            fig.update_yaxes(title_text="Stocks (million)", row=row_number, col=col_number, secondary_y=False, range=[0, max_y_stocks])
            fig.update_yaxes(title_text="Sales share (%)", row=row_number, col=col_number, secondary_y=True, range=[0, max_y_sales])

    fig.update_layout(
        title = title,
        font=dict(
        size=font_size
    ))

    plotly.offline.plot(fig, filename='./plotting_output/8th_edition/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/8th_edition/static/" + title + '.png', scale=1, width=2000, height=1500)


################################################################################################################################################################
#%%
for scenario in model_output_8th_sum_no_economy['Scenario'].unique():
    for transport_type in model_output_8th_sum_no_economy['Transport Type'].unique():
        if transport_type == 'nonspecified':
            continue
        
        title = 'Energy use - {} - {}'.format(scenario, transport_type)

        model_output_8th_plot_df = model_8th_by_fuel_no_economy[model_8th_by_fuel_no_economy['Scenario']==scenario]
        model_output_8th_plot_df = model_output_8th_plot_df[model_output_8th_plot_df['Transport Type'] == transport_type]
        
        model_output_8th_plot_df = model_output_8th_plot_df.groupby(['Date', 'Vehicle Type'])['Energy'].sum().reset_index()

        #plot
        fig = px.line(model_output_8th_plot_df, x="Date", y="Energy", color="Vehicle Type", title=title)#, #facet_col="Economy",
                    #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles
        fig.update_layout(
            font=dict(
            size=font_size
        ))
        plotly.offline.plot(fig, filename='./plotting_output/8th_edition/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
        # fig.write_image("./plotting_output/8th_edition/static/" + title + '.png', scale=1, width=2000, height=1500)
        model_output_8th_plot_df_copy = model_output_8th_plot_df.copy()
        ################################################################################################################################################################

        title = 'Activity - {} - {}'.format(scenario, transport_type)
        
        #remove nonspecified in transport type
        model_output_8th_plot_df = model_output_8th_sum_no_economy[model_output_8th_sum_no_economy['Scenario']==scenario]
        model_output_8th_plot_df = model_output_8th_plot_df[model_output_8th_plot_df['Transport Type']==transport_type]

        model_output_8th_plot_df = model_output_8th_plot_df.groupby(['Date', 'Vehicle Type'])['Activity'].sum().reset_index()

        #plot
        fig = px.line(model_output_8th_plot_df, x="Date", y="Activity", color="Vehicle Type", title=title)#, #facet_col="Economy",
                    #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles
        fig.update_layout(
            font=dict(
            size=font_size 
        ))
        plotly.offline.plot(fig, filename='./plotting_output/8th_edition/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)

#%%
################################################################################################################################################################

#plot energy use for each economy for each Date, by drive type.
title = 'Total activity for each Date, vehicle type'
model_output_8th_sum_vtype = model_output_8th_sum_no_economy.groupby(['Date', 'Vehicle Type', 'Scenario'])['Activity'].sum().reset_index()

#plot
fig = px.line(model_output_8th_sum_vtype, x="Date", y="Activity", color="Vehicle Type", line_dash='Vehicle Type', facet_col="Scenario", facet_col_wrap=7, title=title, category_orders={"Scenario":['Carbon Neutrality','Reference']})#, #facet_col="Economy",
            #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles
fig.update_layout(
    font=dict(
    size=font_size
))
plotly.offline.plot(fig, filename='./plotting_output/8th_edition/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/8th_edition/static/" + title + '.png', scale=1, width=2000, height=1500)

################################################################################################################################################################
#%%
#plot energy use for each economy for each Date, by vehicle type, by transport type

title = 'Total activity use for each Date, vehicle type, for freight'
#filter for freight
model_output_8th_sum_vtype = model_output_8th_sum_no_economy.loc[model_output_8th_sum_no_economy['Transport Type']=='freight']
model_output_8th_sum_vtype = model_output_8th_sum_vtype.groupby(['Date', 'Vehicle Type', 'Scenario'])['Activity'].sum().reset_index()

#plot
fig = px.line(model_output_8th_sum_vtype, x="Date", y="Activity", color="Vehicle Type", line_dash='Vehicle Type', facet_col="Scenario", facet_col_wrap=7, title=title, category_orders={"Scenario":['Reference', 'Carbon Neutrality']})#, #facet_col="Economy",
            #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/8th_edition/' + title + '.html', auto_open=True)
# fig.write_image("./plotting_output/8th_edition/static/" + title + '.png', scale=1, width=2000, height=1500)

#%%
################################################################################################################################################################
#plot fuel use for for each Date, road
title = 'Total fuel use for each Date (road)'
model_output_with_fuels_plot = model_8th_by_fuel_no_economy.copy()
model_output_with_fuels_plot = model_output_with_fuels_plot.loc[model_output_with_fuels_plot['Medium']=='road']
model_output_with_fuels_plot = model_output_with_fuels_plot.groupby(['Date', 'Fuel','Scenario'])['Energy'].sum().reset_index()

#filter out fuel types which contains 'lpg' 'natural_gas'
model_output_with_fuels_plot = model_output_with_fuels_plot.loc[~model_output_with_fuels_plot['Fuel'].str.contains('lpg')]
model_output_with_fuels_plot = model_output_with_fuels_plot.loc[~model_output_with_fuels_plot['Fuel'].str.contains('natural_gas')]

#plot
fig = px.line(model_output_with_fuels_plot, x="Date", y="Energy", color="Fuel", facet_col="Scenario", facet_col_wrap=7, title=title, category_orders={"Scenario":['Reference', 'Carbon Neutrality']})#, #facet_col="Economy",
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles
plotly.offline.plot(fig, filename='./plotting_output/8th_edition/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/8th_edition/static/" + title + '.png', scale=1, width=2000, height=1500)

#plot fuel use for for each Date, non-road
title = 'Total fuel use for each Date (non-road)'
model_output_with_fuels_plot = model_8th_by_fuel_no_economy.copy()
model_output_with_fuels_plot = model_output_with_fuels_plot.loc[model_output_with_fuels_plot['Medium']!='road']
model_output_with_fuels_plot = model_output_with_fuels_plot.groupby(['Date', 'Fuel','Scenario'])['Energy'].sum().reset_index()

#filter out fuel types which contains 'lpg', 'biogasoline', 'biodiesel','coal', 'aviation', 'kerosene', 'lpg','other'
model_output_with_fuels_plot = model_output_with_fuels_plot.loc[~model_output_with_fuels_plot['Fuel'].str.contains('lpg')]
model_output_with_fuels_plot = model_output_with_fuels_plot.loc[~model_output_with_fuels_plot['Fuel'].str.contains('biogasoline')]
model_output_with_fuels_plot = model_output_with_fuels_plot.loc[~model_output_with_fuels_plot['Fuel'].str.contains('biodiesel')]
model_output_with_fuels_plot = model_output_with_fuels_plot.loc[~model_output_with_fuels_plot['Fuel'].str.contains('coal')]
model_output_with_fuels_plot = model_output_with_fuels_plot.loc[~model_output_with_fuels_plot['Fuel'].str.contains('aviation')]
model_output_with_fuels_plot = model_output_with_fuels_plot.loc[~model_output_with_fuels_plot['Fuel'].str.contains('7_6_kerosene')]
model_output_with_fuels_plot = model_output_with_fuels_plot.loc[~model_output_with_fuels_plot['Fuel'].str.contains('lpg')]
model_output_with_fuels_plot = model_output_with_fuels_plot.loc[~model_output_with_fuels_plot['Fuel'].str.contains('other')]

#plot
fig = px.line(model_output_with_fuels_plot, x="Date", y="Energy", color="Fuel",  facet_col="Scenario", facet_col_wrap=7, title=title, category_orders={"Scenario":['Reference', 'Carbon Neutrality']})#, #facet_col="Economy",
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles
plotly.offline.plot(fig, filename='./plotting_output/8th_edition/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/8th_edition/static/" + title + '.png', scale=1, width=2000, height=1500)

################################################################################
#%%
model_8th_by_fuel_no_economy.loc[model_8th_by_fuel_no_economy['Fuel'].str.contains('hydrogen')].groupby(['Vehicle Type', 'Fuel'])['Energy'].sum().reset_index()

#%%
 ################################################################################
#%%
#create region col by joining with region mapping and then summing by region
region_mapping = pd.read_csv('./config/utilities/region_economy_mapping.csv')
model_8th_regions = model_output_8th_sum.merge(region_mapping, how='left', on='Economy')
#plot activity each region for each Date, by scenario by tranport type.
title = 'Total activity for each region by transport type, scenario'
model_output_8th_sum_vtype = model_8th_regions.groupby(['Date', 'Transport Type', 'Scenario', 'Region'])['Activity'].sum().reset_index()
#remove transport type = nonspecified
model_output_8th_sum_vtype = model_output_8th_sum_vtype.loc[model_output_8th_sum_vtype['Transport Type']!='nonspecified']
#plot
fig = px.line(model_output_8th_sum_vtype, x="Date", y="Activity", color="Region", line_dash='Scenario', facet_col="Transport Type", facet_col_wrap=7, title=title, category_orders={"Scenario":['Reference', 'Carbon Neutrality']})#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/8th_edition/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/8th_edition/static/" + title + '.png', scale=1, width=2000, height=1500)

#%%

#show average vehicle efficiencies by drive type, vehicle type and transport type in 2050

model_output_8th_sum_eff = model_output_8th_sum_no_economy.loc[model_output_8th_sum_no_economy['Date']==2050]
model_output_8th_sum_eff = model_output_8th_sum_eff.groupby(['Drive', 'Vehicle Type', 'Transport Type']).sum().reset_index()
model_output_8th_sum_eff['Efficiency (Xkm / PJ)'] = model_output_8th_sum_eff['Activity']/model_output_8th_sum_eff['Energy']
model_output_8th_sum_eff = model_output_8th_sum_eff.loc[model_output_8th_sum_eff['Transport Type']!='nonspecified']

#remove na's
model_output_8th_sum_eff = model_output_8th_sum_eff.dropna()

#combine drive and vechicle type so they are all in one column
model_output_8th_sum_eff['Vehicle Type & Drive'] = model_output_8th_sum_eff['Vehicle Type'] + ' ' + model_output_8th_sum_eff['Drive']


#for each transport type create a graph
for transport_type in model_output_8th_sum_eff['Transport Type'].unique():
    title = 'Average vehicle efficiencies by drive type, vehicle type in 2050 for ' + transport_type
    #filter
    model_output_8th_sum_eff_transport_type = model_output_8th_sum_eff.loc[model_output_8th_sum_eff['Transport Type']==transport_type]
    #sort by vehicle type and drive
    model_output_8th_sum_eff_transport_type = model_output_8th_sum_eff_transport_type.sort_values(by=['Vehicle Type & Drive'])
    #plot bar chart with bars not stacked
    fig = px.bar(model_output_8th_sum_eff_transport_type, x="Vehicle Type", y="Efficiency", color="Drive", title=title, barmode='group') 

    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

    plotly.offline.plot(fig, filename='./plotting_output/8th_edition/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
#%%

#create dataset where we have the following vehicle types: 
#shipping and aviation
#heavy trucks
#light duty vehicles
#other


model_output_8th_sum_vtype = model_output_8th_sum_no_economy.groupby(['Date', 'Vehicle Type', 'Scenario']).sum().reset_index()
#combine vehicle types:
model_output_8th_sum_vtype.loc[model_output_8th_sum_vtype['Vehicle Type'].str.contains('ship'), 'Vehicle Type'] = 'Shipping and aviation'
model_output_8th_sum_vtype.loc[model_output_8th_sum_vtype['Vehicle Type'].str.contains('air'), 'Vehicle Type'] = 'Shipping and aviation'
model_output_8th_sum_vtype.loc[model_output_8th_sum_vtype['Vehicle Type'].str.contains('ht'), 'Vehicle Type'] = 'Heavy trucks'
model_output_8th_sum_vtype.loc[model_output_8th_sum_vtype['Vehicle Type'].str.contains('lv'), 'Vehicle Type'] = 'Light duty vehicles'
model_output_8th_sum_vtype.loc[model_output_8th_sum_vtype['Vehicle Type'].str.contains('lt'), 'Vehicle Type'] = 'Light duty vehicles'

#put all others in other
model_output_8th_sum_vtype.loc[~model_output_8th_sum_vtype['Vehicle Type'].str.contains('Shipping and aviation|Heavy trucks|Light duty vehicles'), 'Vehicle Type'] = 'Other'

#group by Date and vehicle type and sum energy again
model_output_8th_sum_vtype = model_output_8th_sum_vtype.groupby(['Date', 'Vehicle Type', 'Scenario'])['Energy'].sum().reset_index()


#show area chart of energy use by vehicle type faceted bvy scenario:

title = 'Energy use by vehicle type in 2050 to compare to IEA'

#plot area chart
## anbd set colors for each vehicle type manually and their order

fig = px.area(model_output_8th_sum_vtype, x="Date", y="Energy", color="Vehicle Type", title=title, facet_col="Scenario", facet_col_wrap=1, color_discrete_map={'Shipping and aviation':'yellow', 'Heavy trucks':'red', 'Light duty vehicles':'pink', 'Other':'grey'}, category_orders={"Scenario":['Reference', 'Carbon Neutrality'], "Vehicle Type":['Other', 'Shipping and aviation', 'Heavy trucks', 'Light duty vehicles']})#, #facet_col="Economy",
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/8th_edition/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
#%%


#now do the same as above buyt first import emissions factors, calc  emissions then do that:
#import emissions factors
emissions_factors = pd.read_csv('config/utilities/emission_factors_for_8th_edition_transport.csv')

#filter for only APEC in emissions factors data:
emissions_factors = emissions_factors.loc[emissions_factors['Economy']=='00_APEC']
#set 17_electricity to 0 
emissions_factors.loc[emissions_factors['Fuel_transport_8th']=='17_electricity', 'Emissions factor (MT/PJ)'] = 0
#rename Fuel_transport_8th to Fuel
emissions_factors = emissions_factors.rename(columns={'Fuel_transport_8th':'Fuel'})
#drop economy column
emissions_factors = emissions_factors.drop(columns=['Economy'])
#times energy use by emissions factors in fuels df
model_8th_by_fuel_no_economy_emissions = model_8th_by_fuel_no_economy.merge(emissions_factors, on='Fuel', how='left')

#calc emissions
model_8th_by_fuel_no_economy_emissions['Emissions'] = model_8th_by_fuel_no_economy_emissions['Energy'] * model_8th_by_fuel_no_economy_emissions['Emissions factor (MT/PJ)']


#create dataset where we have the following vehicle types: 
#shipping and aviation
#heavy trucks
#light duty vehicles
#other


model_output_8th_sum_vtype = model_8th_by_fuel_no_economy_emissions.groupby(['Date', 'Vehicle Type', 'Scenario']).sum().reset_index()
#combine vehicle types:
model_output_8th_sum_vtype.loc[model_output_8th_sum_vtype['Vehicle Type'].str.contains('ship'), 'Vehicle Type'] = 'Shipping and aviation'
model_output_8th_sum_vtype.loc[model_output_8th_sum_vtype['Vehicle Type'].str.contains('air'), 'Vehicle Type'] = 'Shipping and aviation'
model_output_8th_sum_vtype.loc[model_output_8th_sum_vtype['Vehicle Type'].str.contains('ht'), 'Vehicle Type'] = 'Heavy trucks'
model_output_8th_sum_vtype.loc[model_output_8th_sum_vtype['Vehicle Type'].str.contains('lv'), 'Vehicle Type'] = 'Light duty vehicles'
model_output_8th_sum_vtype.loc[model_output_8th_sum_vtype['Vehicle Type'].str.contains('lt'), 'Vehicle Type'] = 'Light duty vehicles'

#put all others in other
model_output_8th_sum_vtype.loc[~model_output_8th_sum_vtype['Vehicle Type'].str.contains('Shipping and aviation|Heavy trucks|Light duty vehicles'), 'Vehicle Type'] = 'Other'

#group by Date and vehicle type and sum energy again
model_output_8th_sum_vtype = model_output_8th_sum_vtype.groupby(['Date', 'Vehicle Type', 'Scenario'])['Emissions'].sum().reset_index()

#show area chart of energy use by vehicle type faceted bvy scenario:

title = 'Emissions by vehicle type in 2050 to compare to IEA'

#plot area chart
## anbd set colors for each vehicle type manually and their order

fig = px.area(model_output_8th_sum_vtype, x="Date", y="Emissions", color="Vehicle Type", title=title, facet_col="Scenario", facet_col_wrap=1, color_discrete_map={'Shipping and aviation':'yellow', 'Heavy trucks':'red', 'Light duty vehicles':'pink', 'Other':'grey'}, category_orders={"Scenario":['Reference', 'Carbon Neutrality'], "Vehicle Type":['Light duty vehicles', 'Heavy trucks', 'Shipping and aviation', 'Other'] })#, #facet_col="Economy",
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/8th_edition/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
#%%
# reverse order of this list:
# ['Other', 'Shipping and aviation', 'Heavy trucks', 'Light duty vehicles']
# reversed_list = ['Light duty vehicles', 'Heavy trucks', 'Shipping and aviation', 'Other'] 
# ################################################################################################################################################################
# #plot vehicle efficiency vs new vehicle efficiency for all vehicles and drive types for each economy. BEcause there is so much information we wil create a new graph file individually for each vehicel type. this is going to create a lot of graphs but it has to be done 
# #filter for medium = road
# model_output_8th_sum_medium_road = model_output_8th_sum[model_output_8th_sum['Medium']=='road']
# #for each in transport type:
# for transport_type in model_output_8th_sum_medium_road['Transport Type'].unique():
#     #filter 
#     model_output_8th_sum_ttype = model_output_8th_sum_medium_road[model_output_8th_sum_medium_road['Transport Type']==transport_type]
#     #for each vehicle type
#     for vehicle in model_output_8th_sum_ttype['Vehicle Type'].unique():
#         #filter
#         model_output_8th_sum_vtype = model_output_8th_sum_ttype[model_output_8th_sum_ttype['Vehicle Type']==vehicle]
#         #plot
#         #create title
#         title='Vehicle efficiency vs new vehicle efficiency for {} for {}'.format(vehicle, transport_type)
#         #since we have the vehicle eff in the same scale we can just put the data in one column with a measure column. To do this use melt
#         model_output_8th_sum_vtype_melt = model_output_8th_sum_vtype.melt(id_vars=['Date', 'Economy', 'Drive'], value_vars=['Efficiency', 'New_vehicle_efficiency'], var_name='Measure', value_name='Efficiency')

#         fig = px.line(model_output_8th_sum_vtype_melt, x="Date", y="Efficiency", color="Drive", line_dash='Measure', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",

#         fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
#         plotly.offline.plot(fig, filename='./plotting_output/8th_edition/' + title + '_' + vehicle + '_' + transport_type + '.html',auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
#         fig.write_image("./plotting_output/8th_edition/static/" + title + '_' + vehicle + '_' + transport_type + '.png', scale=1, width=2000, height=1500)


#%%
