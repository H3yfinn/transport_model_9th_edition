model_output_v_sales_share = model_output_detailed.groupby(['Economy', 'Date', 'Drive', 'Transport Type', 'Vehicle Type'])['Vehicle_sales_share'].mean().reset_index()

model_output_v_sales_share['Transport_Vehicle_type'] = model_output_v_sales_share['Transport Type'] + '_' + model_output_v_sales_share['Vehicle Type']

#plot
fig = px.line(model_output_v_sales_share, x="Date", y="Vehicle_sales_share", color="Transport_Vehicle_type", line_dash='Drive', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]) )#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename=os.path.join(config.root_dir,  'plotting_output', 'plot_input_data', title + '.html'), auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image(os.path.join(config.root_dir,  'plotting_output', 'plot_input_data', 'static', title + '.png'), scale=1, width=2000, height=800)
model_output_sales = model_output_detailed.groupby(['Economy', 'Date', 'Drive', 'Transport Type', 'Vehicle Type'])['Vehicle_sales_share'].mean().reset_index()

model_output_sales['Transport_Vehicle_type'] = model_output_sales['Transport Type'] + '_' + model_output_sales['Vehicle Type']

#plot
fig = px.line(model_output_sales, x="Date", y="Vehicle_sales_share", color="Transport_Vehicle_type", line_dash='Drive', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename=os.path.join(config.root_dir, 'plotting_output', 'plot_input_data', title + '.html'), auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image(os.path.join(config.root_dir, 'plotting_output', 'plot_input_data', 'static', title + '.png'), scale=1, width=2000, height=800)

################################################################################################################################################################
#%%
#plot travel km per stock by Date, transport type, vehicle type
model_output_travel_km_per_stock = model_output_detailed.groupby(['Date', 'Transport Type', 'Vehicle Type'])['Travel_km_per_stock'].mean().reset_index()

model_output_travel_km_per_stock_pass = model_output_travel_km_per_stock[model_output_travel_km_per_stock['Transport Type']=='passenger']
model_output_travel_km_per_stock_freight = model_output_travel_km_per_stock[model_output_travel_km_per_stock['Transport Type']=='freight']

title='Average Travel_km_per_stock by Date, vehicle type and drive type for passenger'

#plot
fig, ax = plt.subplots()
for key, grp in model_output_travel_km_per_stock_pass.groupby(['Vehicle Type']):
    ax = grp.plot(ax=ax, kind='line', x='Date', y='Travel_km_per_stock', label=key)
plt.title(title)


title='Average Travel_km_per_stock by Date, vehicle type and drive type for freight'

#plot
fig, ax = plt.subplots()
for key, grp in model_output_travel_km_per_stock_freight.groupby(['Vehicle Type']):
    ax = grp.plot(ax=ax, kind='line', x='Date', y='Travel_km_per_stock', label=key)
plt.title(title)


#%%
################################################################################################################################################################
title = 'Average Travel_km_per_stock by Date, transport type, vehicle type and economy'

model_output_trav_p_stock = model_output_detailed.groupby(['Economy', 'Date',  'Transport Type', 'Vehicle Type'])['Travel_km_per_stock'].mean().reset_index()

#plot
fig = px.line(model_output_trav_p_stock, x="Date", y="Travel_km_per_stock", color="Vehicle Type", line_dash='Transport Type', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename=os.path.join(config.root_dir, 'plotting_output', 'plot_input_data', title + '.html'), auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image(os.path.join(config.root_dir, 'plotting_output', 'plot_input_data', 'static', title + '.png'), scale=1, width=2000, height=800)


################################################################################################################################################################
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

plotly.offline.plot(fig, filename=os.path.join(config.root_dir, 'plotting_output', 'plot_input_data', title + '.html'), auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image(os.path.join(config.root_dir, 'plotting_output', 'plot_input_data', 'static', title + '.png'), scale=1, width=2000, height=800)

#%%
################################################################################################################################################################
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

plotly.offline.plot(fig, filename=os.path.join(config.root_dir, 'plotting_output', 'plot_input_data', title + '.html'), auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image(os.path.join(config.root_dir, 'plotting_output', 'plot_input_data', 'static', title + '.png'), scale=1, width=2000, height=1500)
#%%
