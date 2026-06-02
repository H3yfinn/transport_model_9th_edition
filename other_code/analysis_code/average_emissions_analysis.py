#first load in all files from transport_model_9th_edition\output_data\for_other_modellers\{ECONOMY_ID}\{date_id}_{ECONOMY_ID}_detailed_incl_non_road.csv
#and extract rows where Drive is in bev, fcev, ice_d,ice_g, phev_d, phev_g and Vehicle Type is car

#we will find the average efficiency of each vehicle type and drive type combination across all economies for each scenario and year. 
#%%
import os
import re
import pandas as pd
from plotly import express as px
import glob
import numpy as np
folder_path = '../../output_data/for_other_modellers'
dataframes = []
ALL_ECONOMY_IDS = ["01_AUS", "02_BD", "03_CDA", "04_CHL", "05_PRC", "06_HKC", "07_INA", "08_JPN", "09_ROK", "10_MAS", "11_MEX", "12_NZ", "13_PNG", "14_PE", "15_PHL", "16_RUS", "17_SGP", "18_CT", "19_THA", "20_USA", "21_VN"]
for economy_id in ALL_ECONOMY_IDS:
    economy_path = os.path.join(folder_path, economy_id)
    if not os.path.isdir(economy_path):
        continue
    pattern = os.path.join(economy_path, f'*_{economy_id}_detailed_incl_non_road.csv')
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"No detailed files found for {economy_id}. Please check the input data directory.")
    if len(files) > 1:
        raise ValueError(f"Multiple detailed files found for {economy_id}. Please ensure there is only one file per economy.")
    df = pd.read_csv(files[0])
    dataframes.append(df)
#%%
model_output_detailed = pd.concat(dataframes, ignore_index=True)
# Filter for relevant vehicle types and drives
relevant_drives = ['bev', 'ice_g', 'phev_g']#'fcev',
relevant_vehicle_types = ['car']
model_output_filtered = model_output_detailed[(model_output_detailed['Drive'].isin(relevant_drives)) & 
                                             (model_output_detailed['Vehicle Type'].isin(relevant_vehicle_types))]

#drop average_efficiency that is > 2060 date
model_output_filtered = model_output_filtered[model_output_filtered['Date'] <= 2060]
model_output_filtered = model_output_filtered[model_output_filtered['Date'] > 2022]


# Calculate average efficiency by year, drive, and vehicle type
average_efficiency_with_econ = model_output_filtered.groupby(['Date', 'Scenario', 'Economy', 'Drive'])['New_vehicle_efficiency'].mean().reset_index()

# Create a line plot for average efficiency
fig = px.line(average_efficiency_with_econ, x='Date', y='New_vehicle_efficiency', color='Drive',
              title='Average Efficiency by Drive Type and Vehicle Type (Billion_km_per_pj)', facet_col_wrap=3,
              facet_col='Economy', line_dash='Scenario',
              labels={'New_vehicle_efficiency': 'Average Efficiency (billion km/pj)', 'Date': 'Date', 'Drive': 'Drive Type', 'Vehicle Type': 'Vehicle Type'})

# Save the plot as an HTML file and a static image
output_dir = '../../plotting_output/experimental'
# os.makedirs(output_dir, exist_ok=True)
fig.write_html(os.path.join(output_dir, 'average_efficiency_by_drive_type_by_econ.html'))
fig.write_image(os.path.join(output_dir, 'average_efficiency_by_drive_type_by_econ.png'), scale=1, width=2000, height=800)

#then drop the Economy column as it is not needed for the plot
# Calculate average efficiency by year, drive, and vehicle type
average_efficiency = model_output_filtered.groupby(['Date', 'Scenario',  'Drive'])['New_vehicle_efficiency'].mean().reset_index()

fig = px.line(average_efficiency, x='Date', y='New_vehicle_efficiency', color='Drive',
              title='Average Efficiency by Drive Type and Vehicle Type (Billion_km_per_pj)', facet_row='Scenario',
              labels={'New_vehicle_efficiency': 'Average Efficiency (billion km/pj)', 'Date': 'Date', 'Drive': 'Drive Type', 'Vehicle Type': 'Vehicle Type'})

# Save the plot as an HTML file and a static image
output_dir = '../../plotting_output/experimental'
# os.makedirs(output_dir, exist_ok=True)
fig.write_html(os.path.join(output_dir, 'average_efficiency_by_drive_type.html'))
fig.write_image(os.path.join(output_dir, 'average_efficiency_by_drive_type.png'), scale=1, width=2000, height=800)

USE_ECONS = True
if USE_ECONS:
    key_cols = ['Date', 'Scenario', 'Economy', 'Drive']
    key_cols2 = ['Date', 'Scenario', 'Economy']
    average_efficiency = average_efficiency_with_econ.copy()  # Use the dataframe with Economy
else:
    key_cols = ['Date', 'Scenario', 'Drive']
    key_cols2 = ['Date', 'Scenario']
#%%
#caLCAULTE ratio between average efficiency of bev and ice_g in each year to find the eff of phev gasoline vs bev engine. assuming utilisation rate of 0.5 for phev_g
#we will assume that the efficiency of phev_g is the same as bev, but we will use the proportional difference of bev and ice_g to their average to find the efficiency of phev_g when using gasolin or electricity.
#first we need to pivot the average_efficiency dataframe so that we have a column for each drive type
average_efficiency_pivot = average_efficiency.pivot(index=key_cols2, columns='Drive', values='New_vehicle_efficiency').reset_index()
#%%
#now we can calculate the ratio of bev to ice_g
average_efficiency_pivot['average_efficiency_ratio'] = (average_efficiency_pivot['bev'] + average_efficiency_pivot['ice_g']) / 2
average_efficiency_pivot['bev_diff'] = average_efficiency_pivot['bev'] / average_efficiency_pivot['average_efficiency_ratio']
average_efficiency_pivot['ice_g_diff'] = average_efficiency_pivot['ice_g'] / average_efficiency_pivot['average_efficiency_ratio']

#now we can calculate the efficiency of phev_g
average_efficiency_pivot['phev_g_electricity'] = average_efficiency_pivot['phev_g'] * average_efficiency_pivot['bev_diff']
average_efficiency_pivot['phev_g_gasoline'] = average_efficiency_pivot['phev_g'] * average_efficiency_pivot['ice_g_diff']
#%%
#drop the average_efficiency_ratio, bev_diff and ice_g_diff columns as they are not needed anymore
average_efficiency_pivot.drop(columns=['average_efficiency_ratio', 'bev_diff', 'ice_g_diff'], inplace=True)
#melt back
average_efficiency = average_efficiency_pivot.melt(id_vars=key_cols2,
                                                    value_vars=['bev', 'ice_g', 'phev_g_electricity', 'phev_g_gasoline', 'phev_g'],
                                                    var_name='Drive',
                                                    value_name='New_vehicle_efficiency')
#plot
if USE_ECONS:
    fig = px.line(average_efficiency, x='Date', y='New_vehicle_efficiency', color='Drive',
                  title='Average Efficiency by Drive Type and Vehicle Type (Billion_km_per_pj)', facet_row='Scenario',
                  facet_col='Economy',
                  labels={'New_vehicle_efficiency': 'Average Efficiency (billion km/pj)', 'Date': 'Date', 'Drive': 'Drive Type', 'Vehicle Type': 'Vehicle Type'})
else:
    fig = px.line(average_efficiency, x='Date', y='New_vehicle_efficiency', color='Drive',
              title='Average Efficiency by Drive Type and Vehicle Type (Billion_km_per_pj)', facet_row='Scenario',
              labels={'New_vehicle_efficiency': 'Average Efficiency (billion km/pj)', 'Date': 'Date', 'Drive': 'Drive Type', 'Vehicle Type': 'Vehicle Type'})
# Save the plot as an HTML file and a static image
# os.makedirs(output_dir, exist_ok=True)
fig.write_html(os.path.join(output_dir, 'average_efficiency_by_drive_type_phev_g.html'))
fig.write_image(os.path.join(output_dir, 'average_efficiency_by_drive_type_phev_g.png'), scale=1, width=2000, height=800)
#%%

#calcaulte the inverse of New_vehicle_efficiency
average_efficiency['New_vehicle_intensity'] = 1 / average_efficiency['New_vehicle_efficiency']  # Convert to km/PJ


AVERAGE_EFFICIENCY = False
if AVERAGE_EFFICIENCY and USE_ECONS:
    #we will take the average of the vehicle wfficiency per year and give that to economys instead. to simplify things.
    average_efficiency_no_econ = average_efficiency.groupby(['Date', 'Scenario', 'Drive']).mean(numeric_only=True).reset_index()
    average_efficiency.drop(columns=['New_vehicle_efficiency', 'New_vehicle_intensity'], inplace=True)  # Drop value cols that we arereplacing with averages
    #then join that to the average_efficiency_with_econ dataframe
    average_efficiency = average_efficiency.merge(average_efficiency_no_econ, on=['Date', 'Scenario', 'Drive'], how='left')
REMOVE_INA_PHEV = False
if REMOVE_INA_PHEV:#data for ina phev is weird so just going to set the efficiency to that of
    #remove ina phev_g
    average_efficiency = average_efficiency[~((average_efficiency['Drive'] == 'phev_g') & (average_efficiency['Economy'] == '07_INA'))]
#%%
#searparate the phev_g_electricity and phev_g_gasoline into separate cols
phev_g_electricity = average_efficiency[average_efficiency['Drive'] == 'phev_g_electricity'].copy()
phev_g_gasoline = average_efficiency[average_efficiency['Drive'] == 'phev_g_gasoline'].copy()
#now we can rename the Drive column to phev_g
phev_g_electricity['Drive'] = 'phev_g'
phev_g_gasoline['Drive'] = 'phev_g'
#then cahgne the name of the New_vehicle_efficiency column to New_vehicle_efficiency_electricity and New_vehicle_efficiency_gasoline
phev_g_electricity.rename(columns={'New_vehicle_intensity': 'New_vehicle_intensity_phev_electricity'}, inplace=True)
phev_g_gasoline.rename(columns={'New_vehicle_intensity': 'New_vehicle_intensity_phev_gasoline'}, inplace=True)

phev_g_electricity = phev_g_electricity[key_cols+[ 'New_vehicle_intensity_phev_electricity']]
phev_g_gasoline = phev_g_gasoline[key_cols+['New_vehicle_intensity_phev_gasoline']]
#now we can merge the two dataframes back together
average_efficiency = average_efficiency[average_efficiency['Drive'].isin(['phev_g','bev', 'ice_g'])].copy()  # Keep only bev and ice_g
#%%
average_efficiency = average_efficiency.merge(phev_g_electricity, on=key_cols, how='left')
average_efficiency = average_efficiency.merge(phev_g_gasoline, on=key_cols, how='left')
SIMPLIFY_PHEV=False
if SIMPLIFY_PHEV:
    #change the phev values TO BE SAME AS PHEV_G
    average_efficiency.loc[average_efficiency['Drive'] == 'phev_g', 'New_vehicle_intensity_phev_electricity'] = average_efficiency.loc[average_efficiency['Drive'] == 'phev_g', 'New_vehicle_intensity']
    average_efficiency.loc[average_efficiency['Drive'] == 'phev_g', 'New_vehicle_intensity_phev_gasoline'] = average_efficiency.loc[average_efficiency['Drive'] == 'phev_g', 'New_vehicle_intensity']

#%%
import numpy as np
# Plot average emissions by drive type and vehicle type. we will load in average_emissions_generation_20250711.csv for this:
average_emissions_file = 'average_emissions_generation_20250715.csv'
average_emissions_generation = pd.read_csv(average_emissions_file).rename(columns={'average_emissions_per_pj':'average_emissions_per_pj_elec_gen'})
#economy	year	scenarios	average_emissions_per_pj_elec_gen	unit
# 01_AUS	1980	reference	0.257508751	MtCO2/PJ (generation)
emissions_factors = pd.read_csv('../../config/9th_edition_emissions_factors.csv')

#convert from co2/pj to pj/co2
# average_emissions_generation['pj_per_emissions_avg'] = 1 / average_emissions_generation['average_emissions_per_pj_elec_gen']

# emissions_factors['Emissions factor (MT/PJ)'] = 1 / emissions_factors['Emissions factor (MT/PJ)']

#where inf, if date is >2022, set to 0, otherwise set to NaN
average_emissions_generation.loc[(average_emissions_generation['year'] > 2022) & (average_emissions_generation['average_emissions_per_pj_elec_gen'] == np.inf), 'average_emissions_per_pj_elec_gen'] = 0.0

average_emissions_generation.loc[(average_emissions_generation['year'] <= 2022) & (average_emissions_generation['average_emissions_per_pj_elec_gen'] == np.inf), 'average_emissions_per_pj_elec_gen'] = np.nan

#%%
average_emissions_per_km = average_efficiency.copy()
#now we need to find the average energy use of different fuels by drive type :
#first, for phevs we need to assume that they have a utilisation rate of UTILISATION_RATE_PHEV = 0.5 #this is a guess, we can change it later
UTILISATION_RATE_PHEV = 0.8
#what we'll do is create a column for each fuel type and calc the average emissions per km for each drive type of that fuel. e.g. for phev_g's there will be >0 in the gasoline and electricity columns, but 0 in the diesel column.
#we will then sum the emissions in each row 
average_emissions_per_km['Electricity_PJ_per_km'] = 0.0
average_emissions_per_km['Gasoline_PJ_per_km'] = 0.0

average_emissions_per_km.loc[average_emissions_per_km['Drive'] == 'phev_g', 'Electricity_PJ_per_km'] = average_emissions_per_km.loc[average_emissions_per_km['Drive'] == 'phev_g', 'New_vehicle_intensity_phev_electricity'] * UTILISATION_RATE_PHEV#we should probably assume that the efficiency when using electricity is slighlty lower than when using gasoline, but for now we will assume it is the same. can probably do it using a ratio of efficiency of bevs vs gasoline, then apply that to the phev_g's efficiency:
average_emissions_per_km.loc[average_emissions_per_km['Drive'] == 'phev_g', 'Gasoline_PJ_per_km'] = average_emissions_per_km.loc[average_emissions_per_km['Drive'] == 'phev_g', 'New_vehicle_intensity_phev_gasoline'] * (1 - UTILISATION_RATE_PHEV)

average_emissions_per_km.loc[average_emissions_per_km['Drive'] == 'bev', 'Electricity_PJ_per_km'] = average_emissions_per_km.loc[average_emissions_per_km['Drive'] == 'bev', 'New_vehicle_intensity']  # Assuming no gasoline for BEVs
average_emissions_per_km.loc[average_emissions_per_km['Drive'] == 'ice_g', 'Gasoline_PJ_per_km'] = average_emissions_per_km.loc[average_emissions_per_km['Drive'] == 'ice_g', 'New_vehicle_intensity']
#%%
# Calculate total emissions for each drive type. First extract the max and min generation emissions from the average_emissions_generation dataframe
max_emissions_per_pj_elec_gen = average_emissions_generation['average_emissions_per_pj_elec_gen'].max()
min_emissions_per_pj_elec_gen = average_emissions_generation['average_emissions_per_pj_elec_gen'].min()
if USE_ECONS:
    #remove economy == 00_APEC_average_across_years' and economy == 00_APEC
    average_emissions_generation_apec = average_emissions_generation[~average_emissions_generation['economy'].isin(['00_APEC_average_across_years', '00_APEC'])][['year', 'economy', 'scenarios', 'average_emissions_per_pj_elec_gen']].copy()
    average_emissions_generation_apec.rename(columns={'economy': 'Economy'}, inplace=True)
    ECONOMY = 'all'
else:
    ECONOMY='00_APEC_average_across_years'#00_APEC
    #then keep only economy =='00_APEC'
    average_emissions_generation_apec = average_emissions_generation[average_emissions_generation['economy'] == ECONOMY][['year', 'scenarios', 'average_emissions_per_pj_elec_gen']].copy()
#%%
#map scenarios from reference to Reference and target to Target
average_emissions_generation_apec['scenarios'] = average_emissions_generation_apec['scenarios'].replace({'reference': 'Reference', 'target': 'Target'})
#convert year to int
average_emissions_generation_apec['year'] = average_emissions_generation_apec['year'].astype(int)
average_emissions_per_km['Date'] = average_emissions_per_km['Date'].astype(int)  # Ensure Date is in the same format as year
#rename cols
average_emissions_generation_apec.rename(columns={'year': 'Date', 'scenarios': 'Scenario'}, inplace=True)
#join the average emissions with the average efficiency dataframe
average_emissions_per_km = average_emissions_per_km.merge(average_emissions_generation_apec, on=key_cols2, how='left', suffixes=('', '_emissions'))

#%%
average_emissions_per_km['gasoline_emissions_factor'] = emissions_factors[emissions_factors['fuel_code'] == '07_01_motor_gasoline']['Emissions factor (MT/PJ)'].values[0]
#%%
#also add in the max and min emissions for the generation. this is a bit confusing because the way they are inverses of each other.
average_emissions_per_km['min_emissions_per_pj_elec_gen'] = min_emissions_per_pj_elec_gen
average_emissions_per_km['max_emissions_per_pj_elec_gen'] = max_emissions_per_pj_elec_gen

# Calculate total emissions for each drive type. the emissions for gasoline is 07_01_motor_gasoline
average_emissions_per_km['gasoline_co2_per_km'] = average_emissions_per_km['Gasoline_PJ_per_km'] * average_emissions_per_km['gasoline_emissions_factor']
average_emissions_per_km['Electricity_co2_per_km'] = average_emissions_per_km['Electricity_PJ_per_km'] * average_emissions_per_km['average_emissions_per_pj_elec_gen']
average_emissions_per_km['Electricity_co2_per_km_max'] = average_emissions_per_km['Electricity_PJ_per_km'] * average_emissions_per_km['max_emissions_per_pj_elec_gen']
average_emissions_per_km['Electricity_co2_per_km_min'] = average_emissions_per_km['Electricity_PJ_per_km'] * average_emissions_per_km['min_emissions_per_pj_elec_gen']
# Calculate total emissions for each drive type. note that min_emissions_per_pj_elec_gen is equivalent to pj/co2
average_emissions_per_km['emissions_per_km'] = (average_emissions_per_km['Electricity_co2_per_km'] + average_emissions_per_km['gasoline_co2_per_km'])
#and the min and max emissions if we assume the max and min emissions for generation
average_emissions_per_km['emissions_per_km_max'] = (average_emissions_per_km['Electricity_co2_per_km_max'] +
                                             average_emissions_per_km['gasoline_co2_per_km'])
average_emissions_per_km['emissions_per_km_min'] = (average_emissions_per_km['Electricity_co2_per_km_min'] * average_emissions_per_km['min_emissions_per_pj_elec_gen'] +
                                             average_emissions_per_km['gasoline_co2_per_km'])

#%%
#remove the columns we don't need anymore
average_emissions_per_km.drop(columns=['Electricity_PJ_per_km', 'Gasoline_PJ_per_km', 'gasoline_co2_per_km',
                                'max_emissions_per_pj_elec_gen', 'min_emissions_per_pj_elec_gen'], inplace=True)
#melt so we ahve a single column for emissions per km
average_emissions_per_km = average_emissions_per_km.melt(id_vars=key_cols,
                                              value_vars=['emissions_per_km', 'emissions_per_km_max', 'emissions_per_km_min'],
                                              var_name='emission_type',
                                              value_name='kgCO2_per_km')

#drop emissions_per_km_min and emissions_per_km_max where drive is not phev_g or bev
average_emissions_per_km = average_emissions_per_km[~((average_emissions_per_km['Drive'].isin(['phev_g', 'bev']) == False) &
                                                     (average_emissions_per_km['emission_type'].isin(['emissions_per_km_min', 'emissions_per_km_max'])))]
# Rename the emission_type values for clarity
average_emissions_per_km['emission_type'] = average_emissions_per_km['emission_type'].replace({
    'emissions_per_km': 'Average Emissions',
    'emissions_per_km_max': 'Max Emissions',
    'emissions_per_km_min': 'Min Emissions'
})
#%%
#we can convert from billion km per MtCO2 to km per kgCO2 by timesing by 1!

# #but also since we can have 0 emission factors in min_emissions, we will invert to kgco2 per km
# average_emissions_per_km['total_emissions'] = 1 / average_emissions_per_km['total_emissions']  # Convert to km/kgCO2

if USE_ECONS:
    pass
else:
    average_emissions_per_km_line = average_emissions_per_km.copy()  # Use the dataframe without Economy for line plot
    #drop max and min emissions for phevs
    average_emissions_per_km_line = average_emissions_per_km_line[~((average_emissions_per_km_line['Drive'].isin(['phev_g'])) &                                                    (average_emissions_per_km_line['emission_type'].isin(['Max Emissions', 'Min Emissions'])))]
    
    # Create a line plot for total emissions
    fig_emissions = px.line(average_emissions_per_km_line, x='Date', y='kgCO2_per_km', color='Drive', facet_row='Scenario', line_dash='emission_type',
                            title='Average kgCO2 per km by Drive Type and Vehicle Type (km/kgCO2)',
                            labels={'kgCO2_per_km': 'Average kgCO2 per km', 'Date': 'Date', 'Drive': 'Drive Type', 'Vehicle Type': 'Vehicle Type'}, line_dash_map={
                                'Average Emissions': 'solid',
                                'Max Emissions': 'dash',
                                'Min Emissions': 'dash'
                            })
    # Add min and max emissions as shaded areas
    # fig_emissions.add_scatter(x=average_emissions_per_km['Date'], y=average_emissions_per_km['total_emissions_max'], mode='lines', name='Max Emissions', line=dict(dash='dash'), showlegend=False)
    # fig_emissions.add_scatter(x=average_emissions_per_km['Date'], y=average_emissions_per_km['total_emissions_min'], mode='lines', name='Min Emissions', line=dict(dash='dash'), showlegend=False)
    # Save the plot as an HTML file and a static image
    fig_emissions.write_html(os.path.join(output_dir, 'average_emissions_by_drive_type.html'))
    fig_emissions.write_image(os.path.join(output_dir, 'average_emissions_by_drive_type.png'), scale=1, width=2000, height=800)
#%%
#produce toher charts that might be better for communicating it:

#firslty a plot showing the variability of average_emissions_generation. we can do a scatterp plot for this:
fig_emissions_gen = px.scatter(average_emissions_generation, x='year', y='average_emissions_per_pj_elec_gen', color='economy',
                               facet_col='scenarios',
                               title='Average Emissions per PJ of Electricity Generation by Scenario, economy, and Year', 
                                 labels={'average_emissions_per_pj_elec_gen': 'Average Emissions per PJ of Electricity Generation (MtCO2/PJ)',
                                            'year': 'Year', 'scenarios': 'Scenario'})
fig_emissions_gen.write_html(os.path.join(output_dir, 'average_emissions_generation_by_economy.html'))
fig_emissions_gen.write_image(os.path.join(output_dir, 'average_emissions_generation_by_economy.png'), scale=1, width=2000, height=800)

#%%
#%%

#lets do a plot of emissions per km  but we will show it as box and whiskers instead,with x = scenario
average_emissions_per_km_avg = average_emissions_per_km[average_emissions_per_km['emission_type'] == 'Average Emissions'].copy()  # Keep only Average Emissions for the strip plot

if USE_ECONS:
    KEEP_5th_YEAR = False
    KEEP_ALL_YEARS = False
    if KEEP_5th_YEAR:
        #we will keep only the years 2023, 2030, 2040, 2050, 2060
        average_emissions_per_km_avg = average_emissions_per_km_avg[average_emissions_per_km_avg['Date'].isin([2023, 2030, 2040, 2050, 2060])]
    elif KEEP_ALL_YEARS:
        #keep only 07_INA
        # average_emissions_per_km_avg = average_emissions_per_km_avg[average_emissions_per_km_avg['Economy'] == '07_INA']
        #we will keep all years
        average_emissions_per_km_avg = average_emissions_per_km_avg[average_emissions_per_km_avg['Date'] > 2022]
    else:
        #we need to reduce the number of dots on the plot. So we will take the average by dropping the Date column and grouping by Economy, Scenario, Drive, and emission_type
        average_emissions_per_km_avg = average_emissions_per_km_avg.groupby(['Economy', 'Scenario', 'Drive', 'emission_type'])['kgCO2_per_km'].mean().reset_index()

#rename the drive categories to be more readable:  
average_emissions_per_km_avg['Drive'] = average_emissions_per_km_avg['Drive'].replace({
    'bev': 'Battery Electric Vehicle (BEV)',
    'ice_g': 'Internal Combustion Engine (Gasoline)',
    'phev_g': 'Plug-in Hybrid Electric Vehicle',
})
fig_emissions_box = px.box(
    average_emissions_per_km_avg,
    x='Scenario',
    y='kgCO2_per_km',
    color='Drive',
    title='Average car emissions intensity when including generation emissions (kgCO2/km)',
    labels={'kgCO2_per_km': 'Average kgCO2 per km', 'Date': 'Date', 'Drive': 'Drive Type'},
    points="all",
    hover_data=['kgCO2_per_km', 'Scenario', 'Drive', 'Economy'],  # Show Economy in hover
    color_discrete_sequence=[
        '#00B9CC',  # BEV
        '#632B8D',   # ICE_G
        "#679bdb"  # PHEV_G
    ]
)
#use tehse colors for the drives:: #00B9CC: bev, ##B8D0ED: phev_g, #632B8D: ice_g, 
# fig_emissions_box.for_each_trace(lambda t: t.update(marker_color={
#     'Battery Electric Vehicle (BEV)': '#00B9CC',
#     'Plug-in Hybrid Electric Vehicle': '#FF6F61',
#     'Internal Combustion Engine (Gasoline)': '#632B8D'
# }.get(t.name, '#000000')))  # Default color if not found

#set the background color to white
fig_emissions_box.update_layout(plot_bgcolor='white', paper_bgcolor='white')
#make the legend bigger and put it on the chart
# Remove the x axis label
fig_emissions_box.update_xaxes(title_text='')

# Move the legend to the bottom and make it bigger
fig_emissions_box.update_layout(
    legend=dict(
        title='Drive Type:',
        font=dict(size=14),
        orientation='h',
        yanchor='top',
        y=-0.1,
        xanchor='center',
        x=0.5
    )
)
#insett note at bottom
# fig_emissions_box.add_annotation(
#     text="Note: Each dot represents the average kgCO2 per km for a specific economy. The box shows the interquartile range, with the middle line indicating the median. Average generation emissions are included in the calculations.",
#     xref="paper", yref="paper", x=0.5, y=-0.15, showarrow=False
# )
#
#make text all bigger
fig_emissions_box.update_layout(font=dict(size=14))
fig_emissions_box.write_html(os.path.join(output_dir, 'average_emissions_box_by_drive_type.html'))

#drop title and the space saved for it
fig_emissions_box.update_layout(title_text='')
# Reduce the top margin to remove space for the title
fig_emissions_box.update_layout(margin=dict(t=20, b=100))
#make text slightly bigger
fig_emissions_box.update_layout(font=dict(size=18), legend=dict(font=dict(size=18)))
#make legend font fize bigger

# Convert inches to pixels (1 inch = 96 pixels)
height_inches = 2.57
width_inches = 6.25
height_px = int(height_inches * 96)*2
width_px = int(width_inches * 96)*2
fig_emissions_box.write_image(
    os.path.join(output_dir, 'average_emissions_box_by_drive_type.svg'),
    format='svg',
    scale=3,
    width=width_px,
    height=height_px
)
#%%
fig_emissions_strip = px.strip(average_emissions_per_km_avg, x='Scenario', y='kgCO2_per_km', color='Drive', #facet_row='Scenario',
                        title='Average kgCO2 per km by Drive Type and Vehicle Type (km/kgCO2)',
                        labels={'kgCO2_per_km': 'Average kgCO2 per km', 'Date': 'Date', 'Drive': 'Drive Type', 'Vehicle Type': 'Vehicle Type'})
fig_emissions_strip.write_html(os.path.join(output_dir, 'average_emissions_strip_by_drive_type.html'))
fig_emissions_strip.write_image(os.path.join(output_dir, 'average_emissions_strip_by_drive_type.png'), scale=1, width=2000, height=800)

#%%
#then try a bar chart of the average emissions per km by drive type and scenario
#keep
if ECONOMY =='00_APEC_average_across_years':
    #calc the average and plot that:
    average_emissions_per_km_avg = average_emissions_per_km.groupby(['Scenario', 'Drive', 'emission_type']).mean().reset_index()
    
    fig_emissions_bar = px.bar(average_emissions_per_km, x='Scenario', y='kgCO2_per_km', color='Drive', barmode='group',

                            title='Average kgCO2 per km by drive type for all APEC economies (km/kgCO2)',
                            labels={'kgCO2_per_km': 'Average kgCO2 per km', 'Date': 'Date', 'Drive': 'Drive Type', 'Vehicle Type': 'Vehicle Type'})
    fig_emissions_bar.write_html(os.path.join(output_dir, 'average_emissions_bar_by_drive_type.html'))
    fig_emissions_bar.write_image(os.path.join(output_dir, 'average_emissions_bar_by_drive_type.png'), scale=1, width=2000, height=800) 
    
    fig_emissions_box = px.box(average_emissions_per_km_avg, x='Scenario', y='kgCO2_per_km', color='Drive', #facet_row='Scenario',
                            title='Average kgCO2 per km by drive type for all APEC economies (km/kgCO2)',
                            labels={'kgCO2_per_km': 'Average kgCO2 per km', 'Date': 'Date', 'Drive': 'Drive Type', 'Vehicle Type': 'Vehicle Type'}, points="all")
    fig_emissions_box.write_html(os.path.join(output_dir, 'average_emissions_box_by_drive_type.html'))
    fig_emissions_box.write_image(os.path.join(output_dir, 'average_emissions_box_by_drive_type.png'), scale=1, width=2000, height=800)

#%%

#try a scatter plot of the average emissions per km by drive type and scenario
fig_emissions_scatter = px.scatter(average_emissions_per_km_avg, x='Date', y='kgCO2_per_km', color='Drive', facet_row='Scenario',
                            title='Average kgCO2 per km by Drive Type and Vehicle Type (km/kgCO2)',
                            labels={'kgCO2_per_km': 'Average kgCO2 per km', 'Date': 'Date', 'Drive': 'Drive Type', 'Vehicle Type': 'Vehicle Type'})
fig_emissions_scatter.write_html(os.path.join(output_dir, 'average_emissions_scatter_by_drive_type.html'))
fig_emissions_scatter.write_image(os.path.join(output_dir, 'average_emissions_scatter_by_drive_type.png'), scale=1, width=2000, height=800)
# %%
