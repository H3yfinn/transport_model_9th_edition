#first created to help with producing the OGSS section on behavioural controls and their effect on energy security.
#Topics"
#1. when a car travels at a lower average speed, the wind resistance decreases and therefore the car requires less energy https://www.eea.europa.eu/themes/transport/sl2.jpg/image_preview -  https://www.eea.europa.eu/themes/transport/speed-limits-fuel-consumption-and
    # - In summary, whereas heavy goods vehicles speed limits in motorways are in line with the optimum speed in terms of energy and CO2 reductions per vehicle-km (80–90 km/h), decreasing car passenger speed limits in motorways could lead to substantial benefits.
    # to do this i would need: avg speeds per economy, accurate data on travel km per economy, effect of reduction in speed on efficiency in acutal numbers.
#2. Working from home: By analysing commuter trends and labour market data, we found that if everybody able to work from home worldwide were to do so for just one day a week, it would save around 1% of global oil consumption for road passenger transport per year. https://www.iea.org/commentaries/working-from-home-can-save-energy-and-reduce-emissions-but-how-much
    # -https://www.iea.org/data-and-statistics/charts/average-change-in-energy-demand-and-co2-emissions-from-one-day-of-home-working-for-a-single-household-with-a-car-commute - cool chart
    # - . However, for short commutes by car (less than 6 kilometres in the United States, 3 kilometres in the European Union, and 2 kilometres in China), as well as for those made by public transport, working from home could lead to a small increase in emissions as a result of extra residential energy use.
    # - https://www.iea.org/data-and-statistics/charts/change-in-global-co2-emissions-and-final-energy-consumption-by-fuel-in-the-home-working-scenario
    # - Working from home will normally reduce net energy demand for a household that commutes by car. But for commuters taking public transport, it is likely to increase net energy demand, although regional and seasonal differences are significant. Taking this into account, however, we find that during an average year, the overall energy saved as a result of less commuting is still around four times larger than the increase in residential energy consumption.
#3. car free sundays: - https://blog.gaijinpot.com/tokyos-pedestrians-paradise/
    # - does ginza car free snday have any effect on energy use? i doubt it
#4. incentivise public transport use
    # - cheaper? nz example. There are studies that show that price of transport is not very important to most users, instead it is about convenience and reliability and travel time. https://thespinoff.co.nz/politics/16-05-2022/why-universal-half-price-public-transport-shouldnt-be-made-permanent
    # - other options that have proven value (there are many) https://www.greaterauckland.org.nz/2022/05/12/would-at-rethink-the-eastern-busway/
#5. incentivise micro mobility walkign and biking 
    # - bike paths? etc.
    #SKATEBOARDS!
#6. increase occupancy and load factors
    #this we can defs do and show the effects of.
    # rural trips are best to implement car pooling but it is difficult to know the rural split of transport (or at least from what ive seen).
#7. econrouage freight efficiency improvements
#8. incentivise electric vehicles
#9. incentivise high speed and night trains instead of planes where possible.

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

#laod outputs
model_output = pd.read_csv('output_data/model_output_detailed/{}'.format(config.model_output_file_name))

behavioural_policy_df = model_output.loc[model_output['Year'] >= 2018] #filter for 2018 to 2025
behavioural_policy_df = behavioural_policy_df.loc[behavioural_policy_df['Year'] <= 2025] #filter for 2018 to 2025

#filter for road only
behavioural_policy_df = behavioural_policy_df.loc[behavioural_policy_df['Medium'] == 'road']

#filter for scenario = reference
behavioural_policy_df = behavioural_policy_df.loc[behavioural_policy_df['Scenario'] == 'Reference']

#%%
#note that we will do these calcualtions in the spreadsheet since they are so simpe. we will use this script for getting the data we need to do the calcs in the spreadsheet.
#policies:
# Reduce speeds on mways
# WFH three days
# WFH 1 days
# Public transport
# Promote efficient driving for trucks

#need energy use in 2018 to 2025 summed for the whole of apec
#issue with this is how far away our historical data is from the current year. Also the 2025 values is probably not very accurate because of covid!
behavioural_policy_df_1 = behavioural_policy_df[['Year','Energy']]
behavioural_policy_df_1 = behavioural_policy_df_1.groupby(['Year']).sum()

#%%
#we will also get the same data but only for passenger transport and split into vehicle types. Also we want energy use and activity.
behavioural_policy_df_2 = behavioural_policy_df.loc[behavioural_policy_df['Transport Type'] == 'passenger']
behavioural_policy_df_2 = behavioural_policy_df_2[['Year','Energy','Activity','Vehicle Type']]
behavioural_policy_df_2 = behavioural_policy_df_2.groupby(['Year','Vehicle Type']).sum()
#filter for only 2w and lv's
behavioural_policy_df_2 = behavioural_policy_df_2.loc[behavioural_policy_df_2.index.get_level_values('Vehicle Type').isin(['2w','lv'])].reset_index()
#pivot so we have the columns energy activity split by vehicle type
behavioural_policy_df_2 = behavioural_policy_df_2.pivot(index = 'Year', columns='Vehicle Type', values=['Energy','Activity'])
#rename columns
behavioural_policy_df_2.columns = ['Energy_2w','Energy_lv','Activity_2w','Activity_lv']
#reset index
behavioural_policy_df_2 = behavioural_policy_df_2.reset_index()

#%%

#lets try the above but with the data split byeconomic region since we expect there are a lot moe 2w in southeast asia nad china
behavioural_policy_df_3 = behavioural_policy_df.merge(economy_regions, how = 'left', on='Economy')

behavioural_policy_df_3 = behavioural_policy_df_3.loc[behavioural_policy_df_3['Transport Type'] == 'passenger']
behavioural_policy_df_3 = behavioural_policy_df_3[['Year','Energy','Activity','Region', 'Vehicle Type']]
behavioural_policy_df_3 = behavioural_policy_df_3.groupby(['Year','Vehicle Type', 'Region']).sum()
#filter for only 2w and lv's
behavioural_policy_df_3 = behavioural_policy_df_3.loc[behavioural_policy_df_3.index.get_level_values('Vehicle Type').isin(['2w','lv'])].reset_index()
#pivot so we have the columns energy activity split by vehicle type
behavioural_policy_df_3 = behavioural_policy_df_3.pivot(index = ['Year', 'Region'], columns='Vehicle Type', values=['Energy','Activity'])
#rename columns
behavioural_policy_df_3.columns = ['Energy_2w','Energy_lv','Activity_2w','Activity_lv']
#reset index
behavioural_policy_df_3 = behavioural_policy_df_3.reset_index()

#%%
#calcualte total regional energy use
behavioural_policy_df_4 = behavioural_policy_df.merge(economy_regions, how = 'left', on='Economy')
behavioural_policy_df_4 = behavioural_policy_df_4[['Year','Energy', 'Region']]
behavioural_policy_df_4 = behavioural_policy_df_4.groupby(['Year','Region']).sum()

#%%

#save the data to csvs in \other_code\other_data\archive
behavioural_policy_df_1.to_csv('other_code/other_data/archive/behavioural_policy_df_1.csv')
behavioural_policy_df_2.to_csv('other_code/other_data/archive/behavioural_policy_df_2.csv')
behavioural_policy_df_3.to_csv('other_code/other_data/archive/behavioural_policy_df_3.csv')
behavioural_policy_df_4.to_csv('other_code/other_data/archive/behavioural_policy_df_4.csv')

#%%
#calculate average vehicle efficiency
#travel km
#avg commuting distance / total commuting distance
#?average wfh?
#effect of increasing use of public transport options?
#average freight efficiency? eg. average weigth carried per travel km?, therefore how much energy is used and how much less could be used
#avg eff gain from more EVs
personal_research = False
if personal_research:
    #%%
    #for freight transport we will increase aveage load by a set proportion, and then see what the effect is on energy use.
    #filter for freight
    model_output_freight = model_output.loc[model_output['Transport Type'] == 'freight']

    model_output_freight['avg_vehicle_efficiency'] = model_output_freight['Energy'] / model_output_freight['Travel_km'] / model_output_freight['Stocks']

    #remove nans in avg vehicle eff for now but maybe we will want to set them to avgs of other eocnomys later
    model_output = model_output.loc[model_output['avg_vehicle_efficiency'].notna()] 



    #Since we dont have very good data for current, it could be better to do simulations of what could happen to an average APEC economy if they were to implement changes in a certain way. 
    #eg. if increase occupancy load factor by 10% in all economies, what would the effect be on energy use and so on.  > and then show how this could be done feasibly.
    # We can use this style to compare the effect of different policies on energy use and point out actually what is worth looking into further GIVEN THAT ALL EOCNOMYS CANT DO 10 things AT ONCE.

    # The use of this is also that it will involve analysing effect of changes to different variables and how this actually changes the total transport economy. eg. how much energy does a 10% improvement in occ_load reduce? 
    #how does a decrease in activity from incentivising micro mobility walking and biking change things 
    # incentivising public transport use and the effect of more of that?





    #%%
    #work from home module )also useful for buildings integration)

    #%%


#using IEA data instead of personal research:
# https://www.iea.org/reports/a-10-point-plan-to-cut-oil-use
# Bascially just calaculate the percent of total energy change achieved by their actions and then apply that to the total energy use of the transport sector.

