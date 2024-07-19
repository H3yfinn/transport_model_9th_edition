model_output_detailed_vtype = model_output_detailed_vtype.groupby(['Date', 'Economy', 'Drive'])[['Vehicle_efficiency', 'New_vehicle_efficiency']].mean().reset_index()

        fig = px.scatter(model_output_detailed_vtype, x="Vehicle_efficiency", y="New_vehicle_efficiency", color='Economy', facet_col="Drive", facet_row="Date", trendline="ols")

        plotly.offline.plot(fig, filename=os.path.join(config.root_dir, 'plotting_output', title + '.html'), auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
#since we have the vehicle eff in the same scale we can just put the data in one column with a measure column. To do this use melt
        model_output_detailed_vtype_melt = model_output_detailed_vtype.melt(id_vars=['Date', 'Economy', 'Drive'], value_vars=['Efficiency', 'New_vehicle_efficiency'], var_name='Measure', value_name='Efficiency')

        fig = px.line(model_output_detailed_vtype_melt, x="Date", y="Efficiency", color="Drive", line_dash='Measure', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",

        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1])
        plotly.offline.plot(fig, filename=os.path.join(config.root_dir, 'plotting_output', 'for_others', title + '_' + vehicle + '_' + transport_type + '.html'), auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
        #fig.write_image(os.path.join(config.root_dir, 'plotting_output', 'static', title + '_' + vehicle + '_' + transport_type + '.png'), scale=1, width=2000, height=1500)



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
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1])

plotly.offline.plot(fig, filename=os.path.join(config.root_dir, 'plotting_output', 'input_exploration', title + '.html'), auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
#fig.write_image(os.path.join(config.root_dir, 'plotting_output', 'input_exploration', 'static', title + '.png'), scale=1, width=2000, height=800)

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

plotly.offline.plot(fig, filename=os.path.join(config.root_dir, 'plotting_output', 'input_exploration', title + '.html'), auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
#fig.write_image(os.path.join(config.root_dir, 'plotting_output', 'input_exploration', 'static', title + '.png'), scale=1, width=2000, height=1500)
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
plt.savefig(os.path.join(config.root_dir, 'plotting_output', 'diagnostics', '{}.png'.format(title))

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
plt.savefig(os.path.join(config.root_dir, 'plotting_output', 'diagnostics', '{}.png'.format(title))
%%#
