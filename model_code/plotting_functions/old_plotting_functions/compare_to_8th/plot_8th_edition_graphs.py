fig.add_trace(go.Scatter(x=model_output_8th_plot_df_economy_drive['Date'], y=model_output_8th_plot_df_economy_drive['Stocks'], mode='lines', name=legend_name, line=dict(color=color)), row=row_number, col=col_number, secondary_y=False)
                fig.add_trace(go.Scatter(x=model_output_8th_plot_df_economy_drive['Date'], y=model_output_8th_plot_df_economy_drive['Sales share'], mode='lines', name=drive_type+'_Sales Share', line=dict(color=color, dash='dash')), row=row_number, col=col_number, secondary_y=True)
            else:
                #create subplot for this economy AND DRIVE
                fig.add_trace(go.Scatter(x=model_output_8th_plot_df_economy_drive['Date'], y=model_output_8th_plot_df_economy_drive['Stocks'], mode='lines', name=drive_type+'_Stocks', line=dict(color=color)), row=row_number, col=col_number, secondary_y=False)
                fig.add_trace(go.Scatter(x=model_output_8th_plot_df_economy_drive['Date'], y=model_output_8th_plot_df_economy_drive['Sales share'], mode='lines', name=drive_type+'_Sales Share', line=dict(color=color, dash='dash')), row=row_number, col=col_number, secondary_y=True)
        legend_set = True
    #update the x axis title
    fig.update_xaxes(title_text="Date", row=row_number, col=1)
    fig.update_xaxes(title_text="Date", row=row_number, col=2)
    #update the y axis title
    fig.update_yaxes(title_text="Stocks", row=row_number, col=1, range=[0, max_y_stocks])
    fig.update_yaxes(title_text="Sales Share", row=row_number, col=2, range=[0, max_y_sales])
    #update the figure layout
    fig.update_layout(title=title, showlegend=legend_set)
    #show the figure
    fig.show()
fig.add_trace(go.Scatter(x=model_output_8th_plot_df_economy_drive['Date'], y=model_output_8th_plot_df_economy_drive['Stocks'],  legendgroup=legend_name, name=legend_name, line=dict(color=color, width=2)), row=row_number, col=col_number, secondary_y=False)

                legend_name = drive_type + '_Vehicle_sales_share'
                fig.add_trace(go.Scatter(x=model_output_8th_plot_df_economy_drive['Date'], y=model_output_8th_plot_df_economy_drive['Sales share'], legendgroup=legend_name, name=legend_name, line=dict(color=color, dash='dot', width=2)), row=row_number, col=col_number, secondary_y=True)
            else:#legend is already set, so just add the traces with showlegend=False
                #create subplot for this economy AND DRIVE
                legend_name = drive_type + '_Stocks'
                fig.add_trace(go.Scatter(x=model_output_8th_plot_df_economy_drive['Date'], y=model_output_8th_plot_df_economy_drive['Stocks'],  legendgroup=legend_name, name=legend_name,showlegend=False, line=dict(color=color, width=2)), row=row_number, col=col_number, secondary_y=False)

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

    plotly.offline.plot(fig, filename=os.path.join(config.root_dir, 'plotting_output', '8th_edition', title + '.html'), auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image(os.path.join(config.root_dir, 'plotting_output', '8th_edition', 'static', title + '.png'), scale=1, width=2000, height=1500)


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
        plotly.offline.plot(fig, filename=os.path.join(config.root_dir, 'plotting_output', '8th_edition', title + '.html'), auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
        # fig.write_image(os.path.join(config.root_dir, 'plotting_output', '8th_edition', 'static', title + '.png'), scale=1, width=2000, height=1500)
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
        plotly.offline.plot(fig, filename=os.path.join(config.root_dir, 'plotting_output', '8th_edition', title + '.html'), auto_open=AUTO_OPEN_PLOTLY_GRAPHS)

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
plotly.offline.plot(fig, filename=os.path.join(config.root_dir, 'plotting_output', '8th_edition', title + '.html'), auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image(os.path.join(config.root_dir, 'plotting_output', '8th_edition', 'static', title + '.png'), scale=1, width=2000, height=1500)

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

plotly.offline.plot(fig, filename=os.path.join(config.root_dir, 'plotting_output', '8th_edition', title + '.html'), auto_open=True)
# fig.write_image(os.path.join(config.root_dir, 'plotting_output', '8th_edition', 'static', title + '.png'), scale=1, width=2000, height=1500)

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
plotly.offline.plot(fig, filename=os.path.join(config.root_dir, 'plotting_output', '8th_edition', title + '.html'), auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image(os.path.join(config.root_dir, 'plotting_output', '8th_edition', 'static', title + '.png'), scale=1, width=2000, height=1500)

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
plotly.offline.plot(fig, filename=os.path.join(config.root_dir, 'plotting_output', '8th_edition', title + '.html'), auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image(os.path.join(config.root_dir, 'plotting_output', '8th_edition', 'static', title + '.png'), scale=1, width=2000, height=1500)

################################################################################
#%%
model_8th_by_fuel_no_economy.loc[model_8th_by_fuel_no_economy['Fuel'].str.contains('hydrogen')].groupby(['Vehicle Type', 'Fuel'])['Energy'].sum().reset_index()

#%%
 ################################################################################
#%%
#create region col by joining with region mapping and then summing by region
region_mapping = pd.read_csv(os.path.join(config.root_dir, 'config', 'utilities', 'region_economy_mapping.csv'))
model_8th_regions = model_output_8th_sum.merge(region_mapping, how='left', on='Economy')
#plot activity each region for each Date, by scenario by tranport type.
import os

title = 'Total activity for each region by transport type, scenario'
model_output_8th_sum_vtype = model_8th_regions.groupby(['Date', 'Transport Type', 'Scenario', 'Region'])['Activity'].sum().reset_index()
model_output_8th_sum_vtype = model_output_8th_sum_vtype.loc[model_output_8th_sum_vtype['Transport Type']!='nonspecified']

fig = px.line(model_output_8th_sum_vtype, x="Date", y="Activity", color="Region", line_dash='Scenario', facet_col="Transport Type", facet_col_wrap=7, title=title, category_orders={"Scenario":['Reference', 'Carbon Neutrality']})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1])

plotly.offline.plot(fig, filename=os.path.join(config.root_dir, 'plotting_output', '8th_edition', title + '.html'), auto_open=AUTO_OPEN_PLOTLY_GRAPHS)

model_output_8th_sum_eff = model_output_8th_sum_no_economy.loc[model_output_8th_sum_no_economy['Date']==2050]
model_output_8th_sum_eff = model_output_8th_sum_eff.groupby(['Drive', 'Vehicle Type', 'Transport Type']).sum().reset_index()
model_output_8th_sum_eff['Efficiency (Xkm \\ PJ)'] = model_output_8th_sum_eff['Activity']/model_output_8th_sum_eff['Energy']
model_output_8th_sum_eff = model_output_8th_sum_eff.loc[model_output_8th_sum_eff['Transport Type']!='nonspecified']
model_output_8th_sum_eff = model_output_8th_sum_eff.dropna()
model_output_8th_sum_eff['Vehicle Type & Drive'] = model_output_8th_sum_eff['Vehicle Type'] + ' ' + model_output_8th_sum_eff['Drive']

for transport_type in model_output_8th_sum_eff['Transport Type'].unique():
    title = 'Average vehicle efficiencies by drive type, vehicle type in 2050 for ' + transport_type
    model_output_8th_sum_eff_transport_type = model_output_8th_sum_eff.loc[model_output_8th_sum_eff['Transport Type']==transport_type]
    model_output_8th_sum_eff_transport_type = model_output_8th_sum_eff_transport_type.sort_values(by=['Vehicle Type & Drive'])
    fig = px.bar(model_output_8th_sum_eff_transport_type, x="Vehicle Type", y="Efficiency", color="Drive", title=title, barmode='group') 

    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1])

    plotly.offline.plot(fig, filename=os.path.join(config.root_dir, 'plotting_output', '8th_edition', title + '.html'), auto_open=AUTO_OPEN_PLOTLY_GRAPHS)

model_output_8th_sum_vtype = model_output_8th_sum_no_economy.groupby(['Date', 'Vehicle Type', 'Scenario']).sum().reset_index()
model_output_8th_sum_vtype.loc[model_output_8th_sum_vtype['Vehicle Type'].str.contains('ship'), 'Vehicle Type'] = 'Shipping and aviation'
model_output_8th_sum_vtype.loc[model_output_8th_sum_vtype['Vehicle Type'].str.contains('air'), 'Vehicle Type'] = 'Shipping and aviation'
model_output_8th_sum_vtype.loc[model_output_8th_sum_vtype['Vehicle Type'].str.contains('ht'), 'Vehicle Type'] = 'Heavy trucks'
model_output_8th_sum_vtype.loc[model_output_8th_sum_vtype['Vehicle Type'].str.contains('lv'), 'Vehicle Type'] = 'Light duty vehicles'
model_output_8th_sum_vtype.loc[model_output_8th_sum_vtype['Vehicle Type'].str.contains('lt'), 'Vehicle Type'] = 'Light duty vehicles'
model_output_8th_sum_vtype.loc[~model_output_8th_sum_vtype['Vehicle Type'].str.contains('Shipping and aviation|Heavy trucks|Light duty vehicles'), 'Vehicle Type'] = 'Other'
model_output_8th_sum_vtype = model_output_8th_sum_vtype.groupby(['Date', 'Vehicle Type', 'Scenario'])['Energy'].sum().reset_index()

title = 'Energy use by vehicle type in 2050 to compare to IEA'
fig = px.area(model_output_8th_sum_vtype, x="Date", y="Energy", color="Vehicle Type", title=title, facet_col="Scenario", facet_col_wrap=1, color_discrete_map={'Shipping and aviation':'yellow', 'Heavy trucks':'red', 'Light duty vehicles':'pink', 'Other':'grey'}, category_orders={"Scenario":['Reference', 'Carbon Neutrality'], "Vehicle Type":['Other', 'Shipping and aviation', 'Heavy trucks', 'Light duty vehicles']})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1])

plotly.offline.plot(fig, filename=os.path.join(config.root_dir, 'plotting_output', '8th_edition', title + '.html'), auto_open=AUTO_OPEN_PLOTLY_GRAPHS)

emissions_factors = pd.read_csv(os.path.join(config.root_dir, 'config', 'utilities', 'emission_factors_for_8th_edition_transport.csv'))
emissions_factors = emissions_factors.loc[emissions_factors['Economy']=='00_APEC']
emissions_factors.loc[emissions_factors['Fuel_transport_8th']=='17_electricity', 'Emissions factor (MT/PJ)'] = 0
emissions_factors = emissions_factors.rename(columns={'Fuel_transport_8th':'Fuel'})
emissions_factors = emissions_factors.drop(columns=['Economy'])
model_8th_by_fuel_no_economy_emissions = model_8th_by_fuel_no_economy.merge(emissions_factors, on='Fuel', how='left')
model_8th_by_fuel_no_economy_emissions['Emissions'] = model_8th_by_fuel_no_economy_emissions['Energy'] * model_8th_by_fuel_no_economy_emissions['Emissions factor (MT/PJ)']

model_output_8th_sum_vtype = model_8th_by_fuel_no_economy_emissions.groupby(['Date', 'Vehicle Type', 'Scenario']).sum().reset_index()
model_output_8th_sum_vtype.loc[model_output_8th_sum_vtype['Vehicle Type'].str.contains('ship'), 'Vehicle Type'] = 'Shipping and aviation'
model_output_8th_sum_vtype.loc[model_output_8th_sum_vtype['Vehicle Type'].str.contains('air'), 'Vehicle Type'] = 'Shipping and aviation'
model_output_8th_sum_vtype.loc[model_output_8th_sum_vtype['Vehicle Type'].str.contains('ht'), 'Vehicle Type'] = 'Heavy trucks'
model_output_8th_sum_vtype.loc[model_output_8th_sum_vtype['Vehicle Type'].str.contains('lv'), 'Vehicle Type'] = 'Light duty vehicles'
model_output_8th_sum_vtype.loc[model_output_8th_sum_vtype['Vehicle Type'].str.contains('lt'), 'Vehicle Type'] = 'Light duty vehicles'
model_output_8th_sum_vtype.loc[~model_output_8th_sum_vtype['Vehicle Type'].str.contains('Shipping and aviation|Heavy trucks|Light duty vehicles'), 'Vehicle Type'] = 'Other'
model_output_8th_sum_vtype = model_output_8th_sum_vtype.groupby(['Date', 'Vehicle Type', 'Scenario'])['Emissions'].sum().reset_index()

title = 'Emissions by vehicle type in 2050 to compare to IEA'
fig = px.area(model_output_8th_sum_vtype, x="Date", y="Emissions", color="Vehicle Type", title=title, facet_col="Scenario", facet_col_wrap=1, color_discrete_map={'Shipping and aviation':'yellow', 'Heavy trucks':'red', 'Light duty vehicles':'pink', 'Other':'grey'}, category_orders={"Scenario":['Reference', 'Carbon Neutrality'], "Vehicle Type":['Light duty vehicles', 'Heavy trucks', 'Shipping and aviation', 'Other']})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1])

plotly.offline.plot(fig, filename=os.path.join(config.root_dir, 'plotting_output', '8th_edition', title + '.html'), auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
