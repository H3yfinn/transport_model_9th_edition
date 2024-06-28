
#%%

#set working directory as one folder back so that config works
import os
import re
import pandas as pd
sys.path.append(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
import plotly.express as px
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
current_working_dir = os.getcwd()
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = re.split('transport_model_9th_edition', script_dir)[0] + 'transport_model_9th_edition'
if __name__ == "__main__": #this allows the script to be run directly or from the main.py file as you cannot use relative imports when running a script directly
    # Modify sys.path to include the directory where utility_functions is located
    sys.path.append(f"{root_dir}/code")
    import config
    import utility_functions
else:
    # Assuming the script is being run from main.py located at the root of the project, we want to avoid using sys.path.append and instead use relative imports 
    from .. import utility_functions
    from .. import config
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

#%%
#we're oging to take in the data that we have from teh transport datasyetm and see if we can calcualte vehicle efficiency.

FILE_DATE_ID2 = 'DATE20230214'

transport_data_system_folder = '../transport_data_system'
transport_data_system_df_original = pd.read_csv(root_dir + '/' + '{}/output_data/9th_dataset/combined_dataset_{}.csv'.format(transport_data_system_folder,FILE_DATE_ID2))

INDEX_COLS = ['Date',
 'Economy',
 'Vehicle Type',
 'Medium',
 'Transport Type',
 'Drive',
 'Scope',
 'Frequency']
#%%
analyse = False
if analyse:
    #this ends up at 0
    #filter for the same years as are in the model concordances in the transport data system (should just be base year)
    transport_data_system_df = transport_data_system_df_original.copy()
    transport_data_system_df.Measure.unique()
    #we want Efficiency and new_vehicle_efficiency from the transport data system
    transport_data_system_df = transport_data_system_df[transport_data_system_df.Measure.isin(['New_vehicle_efficiency'])]
    #where dataset is nan set it to Dataset_selection_method
    transport_data_system_df.loc[transport_data_system_df.Dataset.isna(),'Dataset'] = transport_data_system_df.loc[transport_data_system_df.Dataset.isna(),'Dataset_selection_method'] 
    #grab cols we need:
    transport_data_system_df = transport_data_system_df[INDEX_COLS+['Measure','Value']+['Dataset']]
    #pivot the measure col to get an efficiency and new_vehicle_efficiency col
    transport_data_system_df = transport_data_system_df.pivot(index=INDEX_COLS+['Dataset'],columns='Measure',values='Value').reset_index()
#%%
analyse = True
if analyse:
    #lets also load in passengerkm, freight tonne km and energy use data from the transport data system.
    transport_data_system_df2 = pd.read_csv(root_dir + '/' + '{}/output_data/9th_dataset/combined_dataset_{}.csv'.format(transport_data_system_folder,FILE_DATE_ID2))
    transport_data_system_df2 = transport_data_system_df2[transport_data_system_df2.Measure.isin(['passenger_km','freight_tonne_km','Energy','Occupancy', 'Load'])]

    #filter for 2017 only
    transport_data_system_df2 = transport_data_system_df2[transport_data_system_df2.Date == '2017-12-31']
    #keep only road
    transport_data_system_df2 = transport_data_system_df2[transport_data_system_df2.Medium == 'road']
    #drop nonnec cols
    transport_data_system_df2 = transport_data_system_df2.drop(columns=['Fuel_Type','Source','Dataset','Dataset_selection_method','Unit'])

    #and we want to calcualte a value for efficiency per km so we will convert x_km to km by dividing by occupancy or load rate. To do thsi we will sep two dfs, based on transport type then pivot the m,easure col to get energy, km and occupancy/load cols. Then we can calcualte efficiency by dividing energy by (km/occupancy or load)

    freight = transport_data_system_df2[transport_data_system_df2['Transport Type'] == 'freight']
    passenger = transport_data_system_df2[transport_data_system_df2['Transport Type'] == 'passenger']
    
    #pivot
    cols = transport_data_system_df2.columns.to_list()
    cols.remove('Measure')
    cols.remove('Value')
    freight = freight.pivot(index=cols,columns='Measure',values='Value').reset_index()
    passenger = passenger.pivot(index=cols,columns='Measure',values='Value').reset_index()

    #calcualte efficiency
    freight['Efficiency'] = freight['Energy']/(freight['freight_tonne_km']/freight['Load'])
    passenger['Efficiency'] = passenger['Energy']/(passenger['passenger_km']/passenger['Occupancy'])

    # #drop efficiency = na since itll come from0/0
    freight = freight.dropna(subset=['Efficiency'])
    passenger = passenger.dropna(subset=['Efficiency'])
    #concat
    transport_data_system_df2 = pd.concat([freight,passenger],sort=False)

    #set dataset to 'Calculated'
    transport_data_system_df2['Dataset'] = 'Calculated'
#%%
analyse = True
if analyse:
    #we will concat with the other eff data so we can plot it altogether.
    # eff_data = pd.concat([transport_data_system_df,transport_data_system_df2],sort=False)
    eff_data = transport_data_system_df2.copy()#atm we only get 0 values for new vehicle eff form the transport data system so lets just use the calculated data
    #drop na and 0 values
    eff_data = eff_data.dropna(subset=['Efficiency'])
    eff_data = eff_data[eff_data.Efficiency != 0]   
    #most of the data ranges from xe-10 to xe-8 whjere x is a number between 1 and 9. the higher numbers are making it hard to see the lower numbers. Lets try filter out bad numbers to get a better plot
    do_this = False
    if do_this:
        #to properly analyse it would be best if kept only the economys where we have data in 'IEA Fuel Economy $ GFEI'
        IEA_economys = transport_data_system_df.loc[transport_data_system_df.Dataset == 'IEA Fuel Economy $ GFEI','Economy'].unique()
        eff_data = eff_data[eff_data.Economy.isin(IEA_economys)]

    # #and keep only drive = 'g' 'd' and 'ice'
    # eff_data = eff_data[eff_data.Drive.isin(['g','d','ice'])]

    #and make a colwhich joins 'Vehicle Type','Transport Type','Drive'
    eff_data['index'] = eff_data['Vehicle Type'] + ' ' + eff_data['Transport Type'] + ' ' + eff_data['Drive']

#%%
#convert vlaues to litres per km we need to divide eff by 3.42e-8
eff_data['L_per_100km'] = (eff_data['Efficiency']/3.42e-8)*100
#convert date to just the first 4 digits so its easier to plot
eff_data['Date'] = eff_data['Date'].astype(str).str[:4]
#now 
#%%
analyse = False
if analyse:
    #now plot violin for y=Efficiency,x=Date and label=Dataset, facet=Economy, hue=Vehicle Type
    plot = px.bar(eff_data,x='index',y='Efficiency',color='Vehicle Type',facet_col='Economy',facet_col_wrap=3,hover_data=['Vehicle Type','Transport Type','Drive'])
    #make each y axis independent
    plot = plot.update_yaxes(matches=None)
    plot.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
    plot.write_html(root_dir + '/' + 'plotting_output/testing/efficiency_data_bar.html', auto_open=True)

    # print avg eff for each economy for each dataset
    for economy in eff_data.Economy.unique():
        print('\nXXXXX Economy: {} XXXXXXX'.format(economy))
        for dataset in eff_data.Dataset.unique():
            #ignore 'interpolation' dataset
            if dataset == 'interpolation':
                continue
            print('Dataset: {}'.format(dataset))
            print(eff_data[(eff_data.Economy == economy) & (eff_data.Dataset == dataset)].Efficiency.mean())
    #ok great it loks (jsut from a quick look no avg's) like the eff value centres around 3e-9 PJ per km for all data we plotted. If we convert that to litres of gasoline it is 3e-9/3.42e-8 = 0.087 litres per km.which is 8.7 per 100km which is just a bit higher than the average fuel economy of cars and vans in 2021 in the IEA https://www.iea.org/fuels-and-technologies/fuel-economy which is good because it measn we can feel happy using the IEA value, times the occupancy rate of 1.5 to get the eff per passenger km for ldv's!
    #Its also good because it means that the ratio of enegry use to passenger km for ldv g or d drives is correct. 

#ALSO PLOT EFFICIENCY IN LITRES PER KM
analyse = False
if analyse:
    #now plot y=Efficiency,x=Date and label=Dataset, facet=Economy, hue=Vehicle Type
    plot = px.bar(eff_data,x='index',y='L_per_100km',color='Vehicle Type',facet_col='Economy',facet_col_wrap=3,hover_data=['Vehicle Type','Transport Type','Drive'])
    plot = plot.update_yaxes(matches=None)
    plot.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))

    plot.write_html(root_dir + '/' + 'plotting_output/testing/efficiency_data_l_per_100km_bar.html', auto_open=True)

    # print avg eff for each economy for each dataset
    for economy in eff_data.Economy.unique():
        print('\nXXXXX Economy: {} XXXXXXX'.format(economy))
        for dataset in eff_data.Dataset.unique():
            #ignore 'interpolation' dataset
            if dataset == 'interpolation':
                continue
            print('Dataset: {}'.format(dataset))
            print(eff_data[(eff_data.Economy == economy) & (eff_data.Dataset == dataset)].Efficiency.mean())
    #ok great it loks (jsut from a quick look no avg's) like the eff value centres around 3e-9 PJ per km for all data we plotted. If we convert that to litres of gasoline it is 3e-9/3.42e-8 = 0.87 litres per km.which is 8.7 per 100km which is just a bit higher than the average fuel economy of cars and vans in 2021 in the IEA https://www.iea.org/fuels-and-technologies/fuel-economy which is good because it measn we can feel happy using the IEA value, times the occupancy rate of 1.5 to get the eff per passenger km for ldv's!
    #Its also good because it means that the ratio of enegry use to passenger km for ldv g or d drives is correct. 
    #some others to expect:
    #heavy truck = 30-40 l/100km
    #bus = 20-30 l/100km
    #freight ldv = probably 10-20 l/100km
    #ldv = 8-10 l/100km
    #motorcycle = 5-8 l/100km
    #The typical hybrid offers fuel savings and CO2 reductions of 20 to 40% over gasoline-only vehicles.
    #The typical ev efficiency of energy conversion from on-board storage to turning the wheels is nearly five times greater for electricity than gasoline ~ which would be equiv to 1-2l/100km for an ldv i think

#%%
#lets group by index, remove outliers then calculate the mean of L_per_100km and Efficiency then plot again:
avg_eff = eff_data[['index','Efficiency','L_per_100km','Vehicle Type','Transport Type','Drive']]
#remove outliers within the group ['index','Vehicle Type']
avg_eff = avg_eff.groupby(['index','Vehicle Type','Transport Type','Drive']).apply(lambda x: x[(x.Efficiency-x.Efficiency.mean()).abs() < 2*x.Efficiency.std()])

#drop index and vehicle type
avg_eff.reset_index(inplace=True,drop=True)

#now do again
avg_eff = avg_eff.groupby(['index','Vehicle Type','Transport Type','Drive']).apply(lambda x: x[(x.Efficiency-x.Efficiency.mean()).abs() < 2*x.Efficiency.std()])

#drop index and vehicle type
avg_eff.reset_index(inplace=True,drop=True)
#%%
if analyse:
    #plot with no outliers
    plot = px.box(avg_eff,x='index',y='L_per_100km',color='Vehicle Type',facet_col_wrap=3)
    plot = plot.update_yaxes(matches=None)
    plot.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))

    plot.write_html(root_dir + '/' + 'plotting_output/testing/efficiency_data_l_per_100km_box_no_outliers.html', auto_open=True)


#%%
#calcualte the mean
avg_eff = avg_eff.groupby(['index','Vehicle Type','Transport Type','Drive']).mean()
avg_eff.reset_index(inplace=True)
#%%
if analyse:
    #now plot y=Efficiency,x=Date and label=Dataset, facet=Economy, hue=Vehicle Type
    plot = px.bar(avg_eff,x='index',y='L_per_100km',color='Vehicle Type',facet_col_wrap=3)
    plot = plot.update_yaxes(matches=None)
    plot.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))

    plot.write_html(root_dir + '/' + 'plotting_output/testing/efficiency_data_l_per_100km_bar_no_outliers.html', auto_open=True)
#%%
#drop index col and L_per_100km then merge on all the otehr nec cols
avg_eff = avg_eff.drop(columns=['L_per_100km', 'index'])
avg_eff = avg_eff.rename(columns={'Efficiency':'Value'})
avg_eff['Measure'] = 'new_vehicle_efficiency'
avg_eff['Unit'] = 'PJ_per_km'
avg_eff['Dataset'] = 'avg_eff_no_outliers'
avg_eff['Date'] = '2017-12-31'
# avg_eff['Source'] = 'transport_data_system_9th'
avg_eff['Medium'] = 'road'
avg_eff['Frequency'] = 'Yearly'
avg_eff['Scope'] = 'National'

avg_eff['Economy'] = transport_data_system_df2.Economy.unique()[0]
new_df = avg_eff.copy()
for economy in transport_data_system_df2.Economy.unique()[1:]:
    avg_eff2 = avg_eff.copy()
    avg_eff2['Economy'] = economy
    new_df = pd.concat([new_df,avg_eff2],ignore_index=True)

#
#%%
#thats good enough. lets just save that in a separate file and incorporate it with all data.
#save it so that it can be concatenated to the transport_data_system_df_original
new_df.to_csv(root_dir + '/' + 'input_data/calculated/new_vehicle_efficiency_other_estimates_2023Feb.csv',index=False)

#%%











#%%
analyse = True
if analyse:
    #lets just look at new_vehicle_efficiency quickly
    new_vehicle_efficiency_data = transport_data_system_df_original.copy()
    new_vehicle_efficiency_data = new_vehicle_efficiency_data[new_vehicle_efficiency_data.Measure == 'new_vehicle_efficiency'] 

    #we dont know what the actual unit is for this data. should we bother using it?
    plot = px.line(new_vehicle_efficiency_data,x='Date',y='Value',color='Drive',line_dash='Vehicle Type',facet_col='Economy',facet_col_wrap=3,hover_data=['Vehicle Type','Transport Type','Drive'])
    plot.write_html(root_dir + '/' + 'plotting_output/testing/new_vehicle_efficiency_data.html')
    # print avg eff for each economy but assume that this is vehicle eff per million passenger km, so we will divide by 1.5 *one million to get eff per passenger km
    print(new_vehicle_efficiency_data.groupby(['Economy','Vehicle Type','Drive'])['Value'].mean()/1.5e6)#nah doesnt seem right aye
    #so we will create a new df with the IEA value for ldv's and then we will use the eff data we have to estimate the eff for the other vehicle types



#%%
#based on the assumption that the ratio of passenger km to energy use is correct we can estimate the eff for the other vehicle types where we dont have data from the iea
#wat well do is filter for passenger km and energy use, filter out data for ldvs that are g or d drives, then pivot the measures, then filter out any rows where we dont have both passenger km and energy use and then calc eff.
#we need to double check this data is correct so we will create a box plot for all values for each vehicle type and drive type and set the color to the economy. we will also add a line for the avg value for each economy for each transport type, vehicle type and drive type

efficiency_other = transport_data_system_df_original.copy()
efficiency_other = efficiency_other[efficiency_other.Measure.isin(['passenger_km','Energy'])]
efficiency_other = efficiency_other[~((efficiency_other['Vehicle Type'] == 'ldv') & (efficiency_other.Drive.isin(['g','d'])))]
#drop vehiuclke type = road
efficiency_other = efficiency_other[efficiency_other['Vehicle Type'] != 'road']
#drop any non road mediums
efficiency_other = efficiency_other[efficiency_other.Medium == 'road']
#keep only Fuel_type.isna() 
efficiency_other = efficiency_other[efficiency_other.Fuel_Type.isna()]

efficiency_other = efficiency_other.pivot(index=['Economy','Dataset','Date','Vehicle Type','Transport Type','Drive'],columns='Measure',values='Value')
efficiency_other = efficiency_other[efficiency_other.passenger_km.notna() & efficiency_other.Energy.notna()]
efficiency_other['efficiency'] = efficiency_other.Energy/efficiency_other.passenger_km
efficiency_other = efficiency_other.reset_index()
analyse = True
#make a col which joins 'Vehicle Type','Transport Type','Drive'
efficiency_other['Vehicle_drive'] = efficiency_other['Vehicle Type']  + ' ' + efficiency_other['Drive']
#remove any outliers
efficiency_other = efficiency_other[efficiency_other.efficiency < efficiency_other.efficiency.quantile(0.9)]
analyse = True
if analyse:
    #plot a violin pllot for each vehicle type.
    for vehicle in efficiency_other['Vehicle Type'].unique():
        plot = px.violin(efficiency_other[efficiency_other['Vehicle Type'] == vehicle],x='Drive',y='efficiency',hover_data=['Economy','Vehicle Type','Drive'],box=True)
        #set title
        plot.update_layout(title_text='Efficiency for {}s'.format(vehicle))
        #show
        plot.show()
        plot.write_html(root_dir + '/' + 'plotting_output/testing/efficiency_violins/efficiency_other_{}.html'.format(vehicle))
    # #plot box with a facet for each Vehicle_drive
    # plot = px.violin(efficiency_other,y='efficiency',x='Drive',facet_col_wrap=3, hover_data=['Economy'], facet_col='Vehicle Type')#points="all",
    # plot.show()
    # plot.write_html(root_dir + '/' + 'plotting_output/testing/efficiency_other.html')

#its quite hard to tell but lets just assume its ok. Just for exploration lets print the average eff per drive type on a single violin plot
if analyse:
    plot = px.violin(efficiency_other,y='efficiency',x='Drive',hover_data=['Economy','Vehicle Type','Drive'],box=True)
    plot.update_layout(title_text='Efficiency for all vehicle types')
    plot.show()
    plot.write_html(root_dir + '/' + 'plotting_output/testing/efficiency_violins/efficiency_other_all.html')

#we're just going to assume that every economy has the same eff for each vehicle type and drive type. so we will just take the average for each vehicle type and drive type and use that for all economies
efficiency_other = efficiency_other.groupby(['Vehicle Type','Drive'])['efficiency'].mean().reset_index()
#%%


################################################################################

#ANALYSIS OVER

################################################################################


#%%
calculate_again = False
if calculate_again:
    #To estiamte the values for the otehr economys we will jsut take the average for available data and use that.
    finalised_new_vehicle_efficiency_ldv_ice = transport_data_system_df_original[(transport_data_system_df_original.Dataset == 'IEA Fuel Economy $ GFEI') & (transport_data_system_df_original['Vehicle Type'] == 'ldv')]
    #keep max Date only for each economy
    finalised_new_vehicle_efficiency_ldv_ice = finalised_new_vehicle_efficiency_ldv_ice[finalised_new_vehicle_efficiency_ldv_ice.Date == finalised_new_vehicle_efficiency_ldv_ice.Date.max()]
    #calc avg eff
    avg_eff = finalised_new_vehicle_efficiency_ldv_ice.Value.mean()

    #create dataframe with all other economys and set eff to avg_eff
    other_economys = transport_data_system_df_original.Economy.unique()
    #get economys not in finalised_new_vehicle_efficiency_ldv_ice
    other_economys = np.setdiff1d(other_economys,finalised_new_vehicle_efficiency_ldv_ice.Economy)
    #for each economy, add a row to finalised_new_vehicle_efficiency_ldv_ice with the avg_eff and all the same other values
    dummy_row = finalised_new_vehicle_efficiency_ldv_ice.iloc[0]
    for economy in other_economys:
        dummy_row.Economy = economy
        dummy_row.Value = avg_eff
        dummy_row.Dataset = 'Estimated'
        finalised_new_vehicle_efficiency_ldv_ice = finalised_new_vehicle_efficiency_ldv_ice.append(dummy_row,ignore_index=True)
    #set Drive = 'g' and Transport Type = 'passenger'
    finalised_new_vehicle_efficiency_ldv_ice['Drive'] = 'g'
    finalised_new_vehicle_efficiency_ldv_ice['Transport Type'] = 'passenger'
    #then copy and set drive = 'd' 
    finalised_new_vehicle_efficiency_ldv_ice_d = finalised_new_vehicle_efficiency_ldv_ice.copy()
    finalised_new_vehicle_efficiency_ldv_ice_d['Drive'] = 'd'
    #append the d drive df to the g drive df
    finalised_new_vehicle_efficiency_ldv_ice = finalised_new_vehicle_efficiency_ldv_ice.append(finalised_new_vehicle_efficiency_ldv_ice_d,ignore_index=True)

    #change values to be in terms of eff per passenger km by timesing by 1.5
    finalised_new_vehicle_efficiency_ldv_ice.Value = finalised_new_vehicle_efficiency_ldv_ice.Value * 1.5

    #change unit to PJ per pkm
    finalised_new_vehicle_efficiency_ldv_ice.Unit = 'PJ per pkm'
    #change measure to New_vehicle_efficiency
    finalised_new_vehicle_efficiency_ldv_ice.Measure = 'New_vehicle_efficiency'

    #sort out dates
    #remove date column
    finalised_new_vehicle_efficiency_ldv_ice = finalised_new_vehicle_efficiency_ldv_ice.drop(columns=['Date'])
    #drop duplicates
    finalised_new_vehicle_efficiency_ldv_ice = finalised_new_vehicle_efficiency_ldv_ice.drop_duplicates()
    #now for every year between this and 10 years ago, stack the dataframe with the date for that year
    #first get the years
    import datetime
    years = np.arange(datetime.datetime.now().year-11,datetime.datetime.now().year-1)
    #convert years to str with 12-31 at end
    years = [str(year)+'-12-31' for year in years]
    finalised_new_vehicle_efficiency_ldv_ice['Date'] = years[0]
    #now stack the dataframe
    for year in years[1:]:
        dummy_df = finalised_new_vehicle_efficiency_ldv_ice.copy()
        dummy_df['Date'] = year
        finalised_new_vehicle_efficiency_ldv_ice = finalised_new_vehicle_efficiency_ldv_ice.append(dummy_df,ignore_index=True)

    #save it so that it can be concatenated to the transport_data_system_df_original
    finalised_new_vehicle_efficiency_ldv_ice.to_csv(root_dir + '/' + 'input_data/calculated/iea_new_vehicle_efficiency_ldv_ice.csv',index=False)

#%%
#and now create a similar dataframe for the other vehicle types
other_eff_data = transport_data_system_df_original.copy()
#remove duplicates when we subset by economy, vehicle type and drive
other_eff_data = other_eff_data.drop_duplicates(subset=['Economy','Vehicle Type','Drive'])
#set dataset to estimated
other_eff_data.Dataset = 'Estimated'
#set measure to New_vehicle_efficiency
other_eff_data.Measure = 'New_vehicle_efficiency'
#set unit to PJ per pkm
other_eff_data.Unit = 'PJ per pkm'
#fuel type is nan
other_eff_data['Fuel Type'] = np.nan
#scope national
other_eff_data.Scope = 'National'
#transport type is passenger
other_eff_data['Transport Type'] = 'passenger'
#final data selection method is nan
other_eff_data['Final Data Selection Method'] = np.nan
#merge with the efficiency_other df to get the eff values
other_eff_data = other_eff_data.merge(efficiency_other,on=['Vehicle Type','Drive'],how='inner')
#remove vlaue column and rename efficiency to value
other_eff_data = other_eff_data.drop(columns=['Value'])
other_eff_data = other_eff_data.rename(columns={'efficiency':'Value'})
#sort out dates
#remove date column
other_eff_data = other_eff_data.drop(columns=['Date'])
#drop duplicates
other_eff_data = other_eff_data.drop_duplicates()
#now for every year between this and 10 years ago, stack the dataframe with the date for that year
#first get the years
import datetime
years = np.arange(datetime.datetime.now().year-11,datetime.datetime.now().year-1)
#convert years to str with 12-31 at end
years = [str(year)+'-12-31' for year in years]
dummy_df = other_eff_data.copy()
other_eff_data_new = pd.DataFrame()
#now stack the dataframe
for year in years:
    dummy_df['Date'] = year
    other_eff_data_new = pd.concat([other_eff_data_new,dummy_df],ignore_index=True)
#save it so that it can be concatenated to the transport_data_system_df_original
other_eff_data_new.to_csv(root_dir + '/' + 'input_data/calculated/new_vehicle_efficiency_other_estimates.csv',index=False)
#%%
#we are going to use the efficiency data we do have to try estimate the efficiency of the vehicles that we don't have data for.
#first find what data we do have

#we also have the IEA assumption for average fuel economy of cars and vans in 2021 as 6.7. So for any missing data we will could use this. https://www.iea.org/fuels-and-technologies/fuel-economy

#we dont know trucks tho. can we even estimate this? seems unlikely. perhaps they need to go in the non road model? but then how to deal with freight tonnne km?

#perhaps to do evs we can use the data we have on ice engine eff and then calculate eff per passenger km using occ of 1.5, then calc the


#%%
#we will hvae to fill in values to import into the model so lets copy rows from the transport datasystem df and change the vlaues to the ones we ahve calculated so that we can import and concat the data with the treannsport data system data later

#%%
#we also want to check whether we have the capabilities to run the mdoel for ldvs, 2w, buses and trucks.


#%%
#also how to do turnover rate? 
#we can clauclate it using  some sort of average of the decrease in stocks minus the increase in stocks due to sales. if the value ends up being a bit all over the place we can perhaps set it manually. 
#we will have to calcualte it for each economy individually, check how that ends up and think abo0ut average for different regions or developments