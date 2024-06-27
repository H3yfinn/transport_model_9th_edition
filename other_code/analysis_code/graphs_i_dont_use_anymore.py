#Plot the ratio of BEVs and PHEVs to ICEs by year, and economy
model_output_detailed_ratio_drive = model_output_detailed.groupby(['Year', 'Economy', 'Drive'])['Stocks'].sum().reset_index()

model_output_detailed_ratio_drive = model_output_detailed_ratio_drive.pivot(index=['Year', 'Economy'], columns='Drive', values='Stocks')

#replace any nan's with 0's
model_output_detailed_ratio_drive = model_output_detailed_ratio_drive.fillna(0)

model_output_detailed_ratio_drive['BEV_ICE_ratio'] = model_output_detailed_ratio_drive['bev'] / (model_output_detailed_ratio_drive['bev'] + model_output_detailed_ratio_drive['g'] + model_output_detailed_ratio_drive['d'])

model_output_detailed_ratio_drive['PHEV_ICE_ratio'] = (model_output_detailed_ratio_drive['phevg'] +  model_output_detailed_ratio_drive['phevd']) / (model_output_detailed_ratio_drive['phevg'] +  model_output_detailed_ratio_drive['phevd'] + model_output_detailed_ratio_drive['g'] + model_output_detailed_ratio_drive['d'])

model_output_detailed_ratio_drive = model_output_detailed_ratio_drive[['BEV_ICE_ratio', 'PHEV_ICE_ratio']]

model_output_detailed_ratio_drive = model_output_detailed_ratio_drive.reset_index()
title = 'Ratio of BEVs to ICEs for each year, by economy'
#plot
fig, ax = plt.subplots()
for key, grp in model_output_detailed_ratio_drive.groupby(['Economy']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='BEV_ICE_ratio', label=key)
plt.title(title)
plt.savefig('./plotting_output/diagnostics/{}.png'.format(title))

#plot
title='Ratio of PHEVs to ICEs for each year, by economy'
fig, ax = plt.subplots()
for key, grp in model_output_detailed_ratio_drive.groupby(['Economy']):
    ax = grp.plot(ax=ax, kind='line', x='Year', y='PHEV_ICE_ratio', label=key)
plt.title(title)
plt.savefig('./plotting_output/diagnostics/{}.png'.format(title))




################################################################################################################################################################
#%%
#plot sum of activity and activity growth mean for each year for each economy
title = 'Activity and activity growth'
change_dataframe_aggregation_act = change_dataframe_aggregation.groupby(['Year','Economy'])['Activity'].sum().reset_index()
change_dataframe_aggregation_ag = change_dataframe_aggregation.groupby(['Year','Economy'])['Activity_growth'].mean().reset_index()


#join the dataframes
change_dataframe_aggregation_act_ag = change_dataframe_aggregation_act.merge(change_dataframe_aggregation_ag, on=['Year','Economy'])

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
        fig.add_trace(go.Scatter(x=change_dataframe_aggregation_act_ag_e['Year'], y=change_dataframe_aggregation_act_ag_e['Activity'],  legendgroup=legend_name, name=legend_name, line=dict(color='blue', width=2, )), row=row_number, col=col_number, secondary_y=False)

        legend_name = 'Activity_growth'
        fig.add_trace(go.Scatter(x=change_dataframe_aggregation_act_ag_e['Year'], y=change_dataframe_aggregation_act_ag_e['Activity_growth'], legendgroup=legend_name, name=legend_name, line=dict(color='red', dash='dot', width=2)), row=row_number, col=col_number, secondary_y=True)
    else:#legend is already set, so just add the traces with showlegend=False
        #create subplot for this economy
        legend_name = 'Activity'
        fig.add_trace(go.Scatter(x=change_dataframe_aggregation_act_ag_e['Year'], y=change_dataframe_aggregation_act_ag_e['Activity'],  legendgroup=legend_name, name=legend_name,showlegend=False, line=dict(color='blue', width=2, )), row=row_number, col=col_number, secondary_y=False)

        legend_name = 'Activity_growth'
        fig.add_trace(go.Scatter(x=change_dataframe_aggregation_act_ag_e['Year'], y=change_dataframe_aggregation_act_ag_e['Activity_growth'], legendgroup=legend_name, name=legend_name, showlegend=False, line=dict(color='red', dash='dot', width=2)), row=row_number, col=col_number, secondary_y=True)

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=1500)

