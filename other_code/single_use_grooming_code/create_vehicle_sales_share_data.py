#we will take in the vehicle sales from historical data, then adjust them according to the patterns we expect to see. i.e. nz moves to 100% ev's by 2030.

#we will also create a vehicle sales distribution that replicates what each scenario in the 8th edition shows. We can use this to help also load all stocks data so that we can test the model works like the 8th edition
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
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive 
# notebook in vscode #or set to notebook
import plotly
import plotly.express as px
pd.options.plotting.backend = "matplotlib"
import plotly.io as pio
pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook

#%%
#load data.
#we will load the vehicle sales shares that were in the input data folder of 8th edition, whoch it seems hugh projected.
# vehicle_sales_share = pd.read_excel('input_data/adjustments_spreadsheet.xlsx', sheet_name='Vehicle_sales_share')
# vehicle_sales_share = pd.read_csv('intermediate_data/non_aggregated_input_data/vehicle_sales_share.csv')#this is jsut a formatted version of above
#load data
vehicle_sales_share_ref = pd.read_excel('input_data/from_8th/raw_data/vehicle_sales_share_model.xlsx', sheet_name='Reference')

vehicle_sales_share_netzero = pd.read_excel('input_data/from_8th/raw_data/vehicle_sales_share_model.xlsx', sheet_name='Net-zero')

#we will merge a regions dataframe so that we can treat data wrt regions if need be
# regions = pd.read_csv('intermediate_data/non_aggregated_input_data/regions.csv')

#we will also load the output stocks data from hughs model and calcualte a vehicle sales share for each year from that. This will be used to test the model works like the 8th edition. it might also be better than the vehicle sales shares that were in the input data folder of 8th edition 
#load 8th edition data
road_stocks= pd.read_csv('intermediate_data/non_aggregated_input_data/road_stocks.csv')

################################################################################################################################################################

#%%
#OPTION 1:


#%%
#calcualte vehicle sales share from the stocks data that hugh projected. Do it so that we have vehicle sales of vehiclke type, and vehicle sales of drive type within vehicel type. They will then by timesed to get the vehicle sales share of each vehicle type, within each transport type
#the issue we have is that we kind of have to asusme that any decrease in vehicle sales is 'turnover'. but any growth in stocks is 100% vehicle stocks sales, and isnt affected by turnover. So we end up seeing sales overexagerated, and probably turnover underexagerated too.

#so first step is to clauclate how many new stocks of each vehicle type threre are in each year.
#then the amount of new stocks of each drive type for each vehicel type in each year. 
new_road_vehicle_stocks = road_stocks[['Economy', 'Scenario', 'Transport Type', 'Year', 'Vehicle Type', 'Stocks']]
#sum the stocks for each vehicle type in each year
new_road_vehicle_stocks = new_road_vehicle_stocks.groupby(['Economy', 'Scenario', 'Transport Type', 'Year', 'Vehicle Type']).sum().reset_index()
#sort by year
new_road_vehicle_stocks = new_road_vehicle_stocks.sort_values(by=['Year'])
#calcualte new stocks each eyar for each group
new_road_vehicle_stocks['New Stocks'] = new_road_vehicle_stocks.groupby(['Economy', 'Scenario', 'Transport Type', 'Vehicle Type'])['Stocks'].diff().fillna(0)
#set any negative vlaues to 0 as we will assume they are due to stock turnover
new_road_vehicle_stocks.loc[new_road_vehicle_stocks['New Stocks'] < 0, 'New Stocks'] = 0
#calcualte sales share as the number of new stocks of eaach vehicle type divided by the number of new stocks of each transport type. 
#so first calc the new stocks for each transport type
new_road_transport_type_stocks = new_road_vehicle_stocks[['Economy', 'Scenario', 'Transport Type', 'Year', 'New Stocks']]
#sum
new_road_transport_type_stocks = new_road_transport_type_stocks.groupby(['Economy', 'Scenario', 'Transport Type', 'Year']).sum().reset_index()
#rename stocks to transport type stocks
new_road_transport_type_stocks.rename(columns={"New Stocks": "New Transport Type Stocks"}, inplace=True)
#merge back onto df
new_road_vehicle_stocks = new_road_vehicle_stocks.reset_index().merge(new_road_transport_type_stocks, on=['Economy', 'Scenario', 'Transport Type', 'Year'], how='left')
#calcualte sales share
new_road_vehicle_stocks['Vehicle_sales_share'] = new_road_vehicle_stocks['New Stocks'] / new_road_vehicle_stocks["New Transport Type Stocks"]
#replace inf with 0
new_road_vehicle_stocks['Vehicle_sales_share'] = new_road_vehicle_stocks['Vehicle_sales_share'].replace([np.inf, -np.inf], 0)
#replace na with 0
new_road_vehicle_stocks['Vehicle_sales_share'] = new_road_vehicle_stocks['Vehicle_sales_share'].fillna(0)
#%%

##Now do the same for drive type within vehicel type
new_road_drive_stocks = road_stocks[['Economy', 'Scenario', 'Transport Type', 'Year', 'Vehicle Type', 'Drive', 'Stocks']]
#sort by year
new_road_drive_stocks = new_road_drive_stocks.sort_values(by=['Year'])
#calcualte new stocks each eyar for each group
new_road_drive_stocks['New Stocks'] = new_road_drive_stocks.groupby(['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive'])['Stocks'].diff().fillna(0)
#set any negative vlaues to 0 as we will assume they are due to stock turnover
new_road_drive_stocks.loc[new_road_drive_stocks['New Stocks'] < 0, 'New Stocks'] = 0
#calcualte sales share as the number of new stocks of eaach Drive divided by the number of new stocks of each vehicle type
#so first calc the new stocks for each vehicle type
new_road_vehicle_type_stocks = new_road_drive_stocks[['Economy', 'Scenario', 'Transport Type', 'Year', 'Vehicle Type', 'New Stocks']]
#sum
new_road_vehicle_type_stocks = new_road_vehicle_type_stocks.groupby(['Economy', 'Scenario', 'Transport Type', 'Year', 'Vehicle Type']).sum().reset_index()
#rename stocks to vehicle type stocks
new_road_vehicle_type_stocks.rename(columns={"New Stocks": "New Vehicle Type Stocks"}, inplace=True)
#merge back onto df
new_road_drive_stocks = new_road_drive_stocks.reset_index().merge(new_road_vehicle_type_stocks, on=['Economy', 'Scenario', 'Transport Type', 'Year', 'Vehicle Type'], how='left')
#calcualte sales share
new_road_drive_stocks['Vehicle_sales_share'] = new_road_drive_stocks['New Stocks'] / new_road_drive_stocks["New Vehicle Type Stocks"]
#replace inf with 0
new_road_drive_stocks['Vehicle_sales_share'] = new_road_drive_stocks['Vehicle_sales_share'].replace([np.inf, -np.inf], 0)
#replace na with 0
new_road_drive_stocks['Vehicle_sales_share'] = new_road_drive_stocks['Vehicle_sales_share'].fillna(0)

#%%
#Calcualte vehicle sales share as the product of the two sales shares
#first merge the two dfs
new_sales_shares = new_road_drive_stocks.merge(new_road_vehicle_stocks, on=['Economy', 'Scenario', 'Transport Type', 'Year', 'Vehicle Type'], how='left')
#calcualte sales share
new_sales_shares['Vehicle_sales_share'] = new_sales_shares['Vehicle_sales_share_x'] * new_sales_shares['Vehicle_sales_share_y']
#drop unneeded columns
new_sales_shares = new_sales_shares[['Economy', 'Scenario', 'Transport Type', 'Year', 'Vehicle Type', 'Drive', 'Vehicle_sales_share']]

#check it adds to 1 for each transport type
new_sales_shares.groupby(['Economy', 'Scenario', 'Year','Transport Type']).sum()
#%%
#calcualte rolling average with a window of X years, of the sales share to remove the inter-annual variability. We have to do this because some of values go from 0 to 1 within a year, reflexting some sort of manual intervention hugh made, rather than a growth rate of sales. so we need to remove the inter-annual variability.
X= 10#this is the number of years we want to average over
#sort by year
new_sales_shares_rolling_mean = new_sales_shares.copy()

new_sales_shares_rolling_mean = new_sales_shares_rolling_mean.sort_values(by=['Year'])
new_sales_shares_rolling_mean['Vehicle_sales_share_rolling_mean'] = new_sales_shares_rolling_mean.groupby(['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive'])['Vehicle_sales_share'].transform(lambda x: x.rolling(window=X, min_periods=1, center=True).mean()).fillna(0)

#%%
#now normalise so the sum of the shares for each transport type is 1
#first calcualte the sum for each transport tpye, then normalise
new_sales_shares_rolling_mean_transport_type = new_sales_shares_rolling_mean[['Economy', 'Scenario', 'Transport Type', 'Year', 'Vehicle Type', 'Drive', 'Vehicle_sales_share_rolling_mean']]
#sum
new_sales_shares_rolling_mean_transport_type = new_sales_shares_rolling_mean_transport_type.groupby(['Economy', 'Scenario', 'Transport Type', 'Year']).sum().reset_index()
#rename to Vehicle_sales_share_rolling_mean_sum
new_sales_shares_rolling_mean_transport_type.rename(columns={"Vehicle_sales_share_rolling_mean": "Vehicle_sales_share_rolling_mean_sum"}, inplace=True)
#merge back onto df
new_sales_shares_rolling_mean_normalised = new_sales_shares_rolling_mean.merge(new_sales_shares_rolling_mean_transport_type, on=['Economy', 'Scenario', 'Transport Type', 'Year'], how='left')
#calcualte sales share normalised
new_sales_shares_rolling_mean_normalised['Vehicle_sales_share_rolling_mean'] = new_sales_shares_rolling_mean_normalised['Vehicle_sales_share_rolling_mean'] * (1 / new_sales_shares_rolling_mean_normalised['Vehicle_sales_share_rolling_mean_sum'])

#drop unneeded columns
new_sales_shares_rolling_mean_normalised = new_sales_shares_rolling_mean_normalised[['Economy', 'Scenario', 'Transport Type', 'Year', 'Vehicle Type', 'Drive', 'Vehicle_sales_share_rolling_mean']]
#%%
#now save the data in a csv and if we wannt, in the excel file
save_as_user_input = True
if save_as_user_input:
       #save teh data bove to the adjsutments spreadsheet

       #rename Vehicle_sales_share_rolling_mean to Value
       new_sales_shares_rolling_mean_normalised = new_sales_shares_rolling_mean_normalised.rename(columns={"Vehicle_sales_share_rolling_mean": "Value"})

       with pd.ExcelWriter('input_data/user_input_spreadsheet.xlsx',engine='openpyxl', mode='a',if_sheet_exists = 'replace') as writer: 
              new_sales_shares_rolling_mean_normalised.to_excel(writer, sheet_name='Vehicle_sales_share',  index=False)

       #save to reformatted data folder
       new_sales_shares_rolling_mean_normalised.to_csv('input_data/from_8th/reformatted/vehicle_stocks_change_share_normalised.csv', index=False)
#%%
################################################################################################################################################################









################################################################################################################################################################
#OPTION 2, cancelled
#%%
#This method seemed okay until i realised that it was the proportion of sales per vehicle type, so it didnt consider the proportion of vehicle type sales for each transport type. 

##first extract daata from hugs original data
#make data long and create scenario column then concatenate
vehicle_sales_share_ref_long = pd.melt(vehicle_sales_share_ref, id_vars=['Economy', 'Transport Type', 'Vehicle Type', 'Drive'], var_name='Year', value_name='Value')

vehicle_sales_share_cn_long = pd.melt(vehicle_sales_share_netzero, id_vars=['Economy', 'Transport Type', 'Vehicle Type', 'Drive'], var_name='Year', value_name='Value')

#create scen cols
vehicle_sales_share_ref_long['Scenario'] = 'Reference'
vehicle_sales_share_cn_long['Scenario'] = 'Carbon Neutral'

#concatenate
vehicle_sales_share_long = pd.concat([vehicle_sales_share_ref_long, vehicle_sales_share_cn_long])

#now we will create a normalised vehicle sales share from the 8th edition data
vehicle_sales_share_transport_type_sum = vehicle_sales_share_long[['Economy', 'Scenario', 'Transport Type', 'Year', 'Value']]

#group by transport type and year. we will make it so that the sum of the vehicle sales share for each transport type is 1
vehicle_sales_share_transport_type_sum = vehicle_sales_share_transport_type_sum.groupby(['Economy', 'Scenario', 'Transport Type', 'Year']).sum()

vehicle_sales_share_transport_type_sum.rename(columns={"Value": "Vehicle_sales_share_sum"}, inplace=True)

vehicle_sales_share_normalised = vehicle_sales_share_long.merge(vehicle_sales_share_transport_type_sum, on=['Economy', 'Scenario', 'Transport Type', 'Year'], how='left')
#%%
vehicle_sales_share_normalised['Vehicle_sales_share_normalised'] = vehicle_sales_share_normalised['Value'] * (1 / vehicle_sales_share_normalised['Vehicle_sales_share_sum'])

#%%
#drop cols
vehicle_sales_share_normalised.drop(columns=['Value', 'Vehicle_sales_share_sum'], inplace=True)
save_as_user_input = False
if save_as_user_input:
       #save teh data bove to the adjsutments spreadsheet

       #rename Vehicle_sales_share_normalised to Value
       vehicle_sales_share_normalised2 = vehicle_sales_share_normalised.rename(columns={"Vehicle_sales_share_normalised": "Value"})

       with pd.ExcelWriter('input_data/user_input_spreadsheet.xlsx',engine='openpyxl', mode='a',if_sheet_exists = 'replace') as writer: 
              vehicle_sales_share_normalised2.to_excel(writer, sheet_name='Vehicle_sales_share',  index=False)

       #save to reformatted data folder
       vehicle_sales_share_normalised.to_csv('input_data/from_8th/reformatted/vehicle_sales_share_normalised.csv', index=False)



#it would be interesting to compare the above to the data we create below from the final stocks data from 8th
#%%
##ERROR CHECKING
#does the vehicle_sales_share add up to 1 for each transport type
################################################################################################################################################################
#sum by economy, transport type and vehicle type
vehicle_sales_share_normalised_sum = vehicle_sales_share_normalised.groupby(['Economy', 'Scenario', 'Year', 'Transport Type']).sum()
#print where the sum is not 1
vehicle_sales_share_normalised_sum[(vehicle_sales_share_normalised_sum['Vehicle_sales_share_normalised'] >= 1.0000001) | (vehicle_sales_share_normalised_sum['Vehicle_sales_share_normalised'] <= 0.9999999999)]









