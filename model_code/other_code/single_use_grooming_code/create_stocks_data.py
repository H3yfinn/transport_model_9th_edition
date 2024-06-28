#goal is to create stocks data for the model. The data we do have is:
# PASSENGER
#8th edition transport model $ Reference
#  - by drive type
#  - not very good quality
#ATO/iTem data:
#  - by drive type for asian economies
#  - will need to estaimte g/d splits for all economies, and for phevs
#IEA evs data
#  - ev stocks data for all iea economies
#  - ev sales data for all iea economies
#  - ev STOCK SHARE DATA FOR ALL IEA ECONOMIES

#FREIGHT
#8th edition transport model $ Reference
#  - by drive type
#  - not very good quality
#ATO/iTem data:
#  - only total road freight stocks
#  - some van stocks may also be part of passenger stocks
#IEA evs data
#  - ht ev stocks and sales data for all iea economies?
#%%

#given the above we want to estimate stocks for as many data points as possible. I think we should do this by:
#PASSSENGER
#use ATO data where avaiable 
#For bev and phev calcualte passenger drive proportions using the proportions in tranpsort type = combined. 
#for  non bev and phev then set drive proportions to what we have in the 8th edition transport model divided by 1 - bev and phev proporitons.

#also what if we were to assume there were no ldvs in freight. just a thought. 

#%%
#so to gbet this straight:
#1.
#PASSENGER
##for ato economys:
#we have data for vehicle types = bev and phev and a total of all drives. So we can calcualte the proportion of passenger ldvs and buses that are phev and bev.
##For iea economys
#For buses, vans, cars and trucks: we have data for (bev+phev) = bev stock share. But we also ahve bev stocks and phev stocks. But we dont have total stocks in each vehicle type so we cant calcualte the proportion of bev and phev in each vehicle type.
#EXCEPT we could clauclate bev stock share using: bev_stocks + phev_stocks = ev_stocks > bev_stocks / ev_stocks = bev stock share of evs. bev stock share of evs * ev_stock_share = bev stock share of all drive types.
#so have stock share for bev and phev from iea too.
#if we add vans and cars then we can have 'ldv's too, which we'll jsut assume to be passenger. 

#Given the above it is probably best to use 8th data like so:
#for buses and ldvs, sum up all stocks in all drive types. 
#calculate proportion for each drive type. 
#where we do have bev and/or phev proportions then swap those in and set column 'better_ev_data'=True, and calculate 1 minus those. Then where better_ev_data'=True divide the 8th proportions for remainign drive types by "1 minus those".
#now we should have a series of drive proportions for buses and ldvs that add up to 1.
#times the drive proportions by the total stocks for each vehicle type to get the stocks for each drive type.
#The effect of this will be updating the stocks data to better reflect the amount of bev and phev in each vehicle type, accoridng to the iea and/or ato data.

# 2.
#since we want to be able to do this again if we get better data we should design a system that allows us to do this. It will also be useful for applying to other problems.

#function design:
#original_drive_proportions
#original_total_stocks
#better_drive_proportions
#better_total_stocks
#new_original_drive_proportions = original_drive_proportions * (1 - sum(better_drive_proportions))

#as an extra example we can also apply this to passenger 2w where we only have new data for the better_total_stocks. We would just times origianl_drive_proportions by better_total_stocks to get better drive values.

# 3.
#The above can then be applied to freight like so:
#fROM iea we have better ht ev and phev stocks and the ev stock share. So we can do a similar thing to what was done for buses and ldvs above to calcualte bev and phev stock shares for freight.

#one issue for freight is that we arent very sure about our total stocks for the ht vehicle type, so we should keep a look out for better data on that. Also ldvs are currently all being counted as passenger, even though one could expect many ldv's are used for freight. 

# 4.
#PERHAPS we can apply the function to energy and activity too. As follows:
#activity:
#freight: We only have new data for the total freight-tone-km for each medium. However this is good enough for such a difficult type
#Passenger: Like freight, except we do have new bus passengerkm for some economies. We can create a similar function to the above for this but liek so:

#importing bus passengerkm and new total for road passenger km:
#original drive proportions of vehicle total
#original vehicle proportions of transport type total
#better drive proportions of vehicle total
#better vehicle proportions of transport type total
#new_original_drive_proportions = original_drive_proportions * (1 - sum(better_drive_proportions))
#new_original_vehicle_proportions = original_vehicle_proportions * (1 - sum(better_vehicle_proportions))

#this will allow us to incorporate a new total for the bus and road passengerkm for each economy. BUT it should probably only be done when the new total for bus and road are from the same dataset, otherwise we will be mixing data from different sources and the bus poroportion will probably be wrong. Instead, in that situation we would just incorpoarte the new total for road passenger km and leave the bus passenger km as it is.

#energy:
#Mostly the new energy data is just for each medium when you dont consider the transpoort type. So that can be used to udpate the energy data for each medium like so:

# function:
#original energy proportion of all energy total
#new energy proportion of all energy total
#THIS WILL THEN AFFECT THE ENERGY TOTALS FOR EACH SUBSEQUENT LEVEL DOWN (LIKE MEDIUMS, TRANSPORT TPYES, V TYPES, ETC)]

#NEW IDEA, WHY NOT CONVERT EVERYTHIG INTO SHARES? THAT WAY WE CAN JUST ADD THEM UP AND THEN MULTIPLY BY THE TOTALS. THIS WILL MAKE IT EASIER TO DO THE ABOVE.





#we have new air/rail/ship values for freight-tonne-km. Done.



#%%
#set working directory as one folder back so that config works
import os
import re
import pandas as pd
sys.path.append(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
import plotly.express as px
import plotly.subplots as subplots
import plotly.graph_objects as go
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

FILE_DATE_ID2 = 'DATE20230126'

transport_data_system_folder = '../transport_data_system'
transport_data_system_df_original = pd.read_csv(root_dir + '/' + '{}/output_data/{}_interpolated_combined_data.csv'.format(transport_data_system_folder,FILE_DATE_ID2))

#laod estimated ldv data
# './input_data/calculated/ldv_data.csv'
ldv_data = pd.read_csv(root_dir + '/' + './input_data/calculated/ldv_data.csv')

#stack ldv data onto transport data system
transport_data_system_df_original = pd.concat([transport_data_system_df_original,ldv_data],sort=False)

#%%
INDEX_COLS = ['Date',
 'Economy',
 'Medium',
 'Measure',
 'Transport Type',
 'Vehicle Type',
 'Scope',
 'Frequency',
 'Fuel_Type',
#  'Dataset',
 'Unit']

#%%
#goal is to separate the data from ato
ATO_ECONOMIES =['01_AUS', '02_BD', '05_PRC', '06_HKC', '07_INA', '08_JPN',
       '09_ROK', '10_MAS', '12_NZ', '13_PNG', '15_PHL', '16_RUS', '17_SGP',
       '18_CT', '19_THA', '21_VN']
non_ATO_ECONOMIES = [x for x in transport_data_system_df_original['Economy'].unique() if x not in ATO_ECONOMIES]
#grab stocks:
stocks_data = transport_data_system_df_original[transport_data_system_df_original['Measure']=='Stocks']
#filter for ATO economys
stocks_data = stocks_data[stocks_data['Economy'].isin(ATO_ECONOMIES)]

#and any Final_dataset_selection_method = 'interpolation'
stocks_data_non_model = stocks_data[stocks_data['Final_dataset_selection_method']!='interpolation']
#for now we will rmeove the transport model dataset
stocks_data_non_model = stocks_data_non_model[stocks_data_non_model['Dataset']!='8th edition transport model']
#filter for bus and ldv in vehicle type
stocks_data_non_model = stocks_data_non_model[stocks_data_non_model['Vehicle Type'].isin(['bus','ldv'])]
#where we have transport type = combined and vehicle type = ldv or bus then make the transport tpye = passenger. #NOTE this is making the assumption that ldvs are passenger vehicles. This is not always true but it is a good assumption for now.
stocks_data_non_model.loc[(stocks_data_non_model['Transport Type']=='combined') & (stocks_data_non_model['Vehicle Type'].isin(['ldv','bus'])),'Transport Type'] = 'passenger'

x = stocks_data_non_model.set_index(INDEX_COLS)
#check for any duplicates
x[x.duplicated(keep=False)]
#calcualte stock proportiuons for each unique index:
#first make drive into columns by pivoting. this will allow us to create a row for each unique transport type/vehicle type/economy/dataset/date combination
stocks_data_non_model_by_drive = stocks_data_non_model.pivot(index=INDEX_COLS, columns='Drive', values='Value').reset_index()

#keep only data where either of bev and phev are non nan
stocks_data_non_model_by_drive = stocks_data_non_model_by_drive[~stocks_data_non_model_by_drive[['bev','phev']].isna().all(axis=1)]

#calculate percentage of each drive type in bev and phev comapred to total
stocks_data_non_model_by_drive['bev_proportion'] = stocks_data_non_model_by_drive['bev']/(stocks_data_non_model_by_drive['road'])
stocks_data_non_model_by_drive['phev_proportion'] = stocks_data_non_model_by_drive['phev']/(stocks_data_non_model_by_drive['road'])

#%%
#now we want to join on this data onto the data we have from the 8th edition transport model 
#so first make model data have drive cols
stocks_data_model = stocks_data[stocks_data['Dataset']=='8th edition transport model']

#now make wide with drive cxols
stocks_data_model_by_drive = stocks_data_model.pivot(index=INDEX_COLS, columns='Drive', values='Value').reset_index()

#and also merge onto the 8th edition transport model data
merged_data = stocks_data_model_by_drive.merge(stocks_data_non_model_by_drive,on=INDEX_COLS,how='outer', suffixes=('','_non_model'))

#filter for only ldv and bus 
merged_data = merged_data[merged_data['Vehicle Type'].isin(['ldv','bus'])]


###################################################
#%%
# Make everything in terms of percent of above level. 
# Can insert new proportions using 1-new * old. 

# For new totals of each level, is it a good idea to insert them? Eg. We wouldn't insert new drive type values. Would we insert a new value for the amount of buses? An what about a new value for total bus passenger km? By inserting it we would be risking that the other vehicle type values aren't on same level. I think we should only do this for medium and above. The Same goes for energy

# Anyways, once we finish this are we done?

# Need to calculate: 
# Turnover rate
# ? Scale the new vehicle efficiency values?
# Find occupancy values
#%%
# levels = ['Transport Type','Medium', 'Vehicle Type','Drive']#this is like the hierarchy of the data.
# non_level_index_cols = ['Measure', 'Date', 'Scope','Frequency', 'Fuel_Type','Dataset', 'Unit']

def convert_to_proportions(levels,non_level_index_cols, df):
       #intention is to create a proportion of total value for each level of the hierarchy given one column of values for all levels
       # Levels is a list that is in order of the hierarchy within the dataframe
       #each proportion for each level is calculated by dividing the value of the level by the total value of the level above it
       current_levels_list =[]
       #create a proportions df which only contains the index cols, level cols
       proportions_df = df[levels+non_level_index_cols].copy()

       for level in levels:#[1:]:
              #Copy df
              df_copy = df.copy()
              #add level to current levels list
              current_levels_list.append(level)
              
              #CALCUALTE SUM FOR CURRENT LEVEL
              #Goupby current levels list and sum
              summed_df = df_copy.groupby(current_levels_list+non_level_index_cols,dropna=False).sum().reset_index()
              name_1 = level+'_total'
              #make the value col name the level + _total
              summed_df = summed_df.rename(columns={'Value':name_1})
              #drop unnecessary columns
              unncessary_cols = [col for col in summed_df.columns if col not in current_levels_list+non_level_index_cols+[name_1]]
              summed_df = summed_df.drop(columns=unncessary_cols)
              #drop duplicates
              summed_df = summed_df[~summed_df.duplicated(keep='first')]

              #CALCUALTE SUM FOR LEVEL ABOVE
              #if there is no level above then sum for all levels
              if len(current_levels_list) == 1:
                     #groupby non level index cols and sum
                     summed_df2 = df_copy.groupby(non_level_index_cols,dropna=False).sum().reset_index()
                     #make name_2 'total'
                     name_2 = 'total'
                     #make the value col name2
                     summed_df2 = summed_df2.rename(columns={'Value':name_2})
                     #drop unnecessary columns
                     unncessary_cols = [col for col in summed_df2.columns if col not in non_level_index_cols+[name_2]]
                     summed_df2 = summed_df2.drop(columns=unncessary_cols)
                     #drop duplicates
                     summed_df2 = summed_df2[~summed_df2.duplicated(keep='first')]

                     #join df to summed_df2
                     df_copy = df_copy.merge(summed_df2, on=non_level_index_cols, how='left')
              else:
                     #groupby current levels list minus the current level and sum
                     summed_df2 = df_copy.groupby(current_levels_list[:-1]+non_level_index_cols,dropna=False).sum().reset_index()       
                     #make the value col name the previous level + _total
                     name_2 = current_levels_list[-2]+'_total'
                     summed_df2 = summed_df2.rename(columns={'Value':name_2})
                     #drop unnecessary columns
                     unncessary_cols = [col for col in summed_df2.columns if col not in non_level_index_cols+current_levels_list[:-1]+[name_2]]
                     summed_df2 = summed_df2.drop(columns=unncessary_cols)
                     #drop duplicates
                     summed_df2 = summed_df2[~summed_df2.duplicated(keep='first')]

                     #join df to summed_df2
                     df_copy = df_copy.merge(summed_df2, on=non_level_index_cols+current_levels_list[:-1], how='left')

              #join summed_df1 to df
              df_copy = df_copy.merge(summed_df, on=current_levels_list+non_level_index_cols, how='left')

              #Divide current level total by upper level total to get current level proportion
              df_copy[level+'_proportion'] = df_copy[name_1]/df_copy[name_2]
              #remove uncessary columns
              unncessary_cols = [col for col in df_copy.columns if col not in current_levels_list+non_level_index_cols+[level+'_proportion']]
              df_copy = df_copy.drop(columns=unncessary_cols)
              #drop duplicates
              df_copy = df_copy[~df_copy.duplicated(keep='first')]
              #join proportion onto proportions_df
              proportions_df = proportions_df.merge(df_copy, on=current_levels_list+non_level_index_cols, how='left')
       return proportions_df


#one could argue that economy is a level, but it is not a level that we want to calculate proportions for.
def insert_new_proportions(proportions_df, new_proportions_df, levels, non_level_index_cols):
       """
       This will take new_proportions_df which has new values for the proportions we want to replace. Its columns will be for all index cols and then the levels up to and including the level we want to replace. For example if we want to replace buses as a proportion of total road stocks within the passenger transport type then the columns will be:
       Index cols: ['Measure', 'Date', 'Scope','Frequency', 'Fuel_Type','Dataset', 'Unit', 'Economy'] 
       Levels: ['Transport Type','Medium', 'Vehicle Type']
       and then the values we want to insert will be in a column named 'Vehicle Type_proportion'
       
       The process will merge the new vlaues into the proportions_df in a new column with suffix '_new'. 
       We will also create another df where we group by the Levels except the level we want to replace and then sum the values. Then create a new column 'one_minus' which is 1 minus the sum of the new values. This will also be joined to the proportions_df, and then we will multiply the old values by the one_minus column.
       We will finally replace the old values with the new values where we can and then drop all the columns we created.

       proportions_df: dataframe with proportions
       new_value_list: list of new values to insert
       categories_list: list of categories to insert new values for. These categories are the values for the current level. eg. if current level is Drive, then categories_list could be ['bev','phev']
       index_row_without_categories: row to insert new values for. eg. if current level is Drive, then index_row_without_categories for 2015
       
       could be ['road','ldv','2015','National','Annual','Petrol','8th edition transport model $ Reference','Million passenger km']
       """
       #this will simply replace the old value with the new one, and then recalculate the proportions for the current level using (1-new * old)=old for each old proportion. 
       values_col = levels[-1]+'_proportion'
       
       #join new_proportions_df onto proportions_df
       proportions_df = proportions_df.merge(new_proportions_df, on=non_level_index_cols+levels, how='left', suffixes=('','_new'))

       #create one_minus column in new_proportions_df:
       #group and sum the new values for all levels except the level we want to replace
       new_proportions_df_grouped = new_proportions_df.groupby(non_level_index_cols+levels[:-1]).sum()
       #calcualte one_minus
       new_proportions_df_grouped['one_minus'] = 1-new_proportions_df_grouped[values_col]
       #join onto proportions_df
       proportions_df = proportions_df.merge(new_proportions_df_grouped['one_minus'], on=non_level_index_cols+levels[:-1], how='left')
       #multiply old values by one_minus
       proportions_df[values_col] = proportions_df[values_col]*proportions_df['one_minus']
       #replace old values with new values where we can
       proportions_df.loc[proportions_df[values_col+'_new'].notnull(),values_col] = proportions_df.loc[proportions_df[values_col+'_new'].notnull(),values_col+'_new']
       #drop all the columns we created
       proportions_df = proportions_df.drop(columns=[values_col+'_new','one_minus'])

       return proportions_df

#%%

#to test this out we will insert the values for bev_proportion and phev_proportion for ldv and bus.
# proportions_df, new_proportions_df, levels, non_level_index_cols
new_proportions_df = stocks_data_non_model_by_drive.copy()
#remove bev and phev cols
new_proportions_df = new_proportions_df.drop(columns=['bev','phev','road'])
#rename bev_proportion and phev_proportion to bev and phev
new_proportions_df = new_proportions_df.rename(columns={'bev_proportion':'bev','phev_proportion':'phev'})
#melt
new_proportions_df = new_proportions_df.melt(id_vars=INDEX_COLS, value_vars=['bev','phev'], var_name='Drive', value_name='Value')#TODO double check index cols

#rename Value to Drive_proportion
new_proportions_df = new_proportions_df.rename(columns={'Value':'Drive_proportion'})
#remove rows where Drive_proportion is null
new_proportions_df = new_proportions_df[new_proportions_df['Drive_proportion'].notnull()]

# #NOW NEED TO CALCULATE A PROPORTIONS DF!
# levels = ['Transport Type','Medium', 'Vehicle Type', 'Drive']
# non_level_index_cols = [col for col in INDEX_COLS if col not in levels] + ['Dataset']#TODO double check index cols
#%%
levels = ['Transport Type','Medium', 'Vehicle Type','Drive']#this is like the hierarchy of the data.
non_level_index_cols = ['Measure', 'Date', 'Scope','Frequency', 'Fuel_Type','Dataset', 'Unit', 'Source']

# transport_data_system_df_original_proportions = convert_to_proportions(levels,non_level_index_cols, transport_data_system_df_original)

# new_proportions_df2 = insert_new_proportions(transport_data_system_df_original_proportions, new_proportions_df, levels, non_level_index_cols)
#%%
#extract the index row for ldv's

levels = ['Transport Type','Medium', 'Vehicle Type','Drive']#this is like the hierarchy of the data.
non_level_index_cols = ['Economy', 'Measure', 'Date', 'Scope','Frequency', 'Fuel_Type', 'Unit']#'Dataset', 'Source'

#proportions_df, new_proportions_df, levels, non_level_index_cols)
proportions_df = convert_to_proportions(levels,non_level_index_cols, transport_data_system_df_original)

#%%
# proportions_df, new_proportions_df, levels, non_level_index_cols)
#this will simply replace the old value with the new one, and then recalculate the proportions for the current level using (1-new * old)=old for each old proportion. 
values_col = levels[-1]+'_proportion'

#join new_proportions_df onto proportions_df
proportions_df = proportions_df.merge(new_proportions_df, on=non_level_index_cols+levels, how='left', suffixes=('','_new'))

#create one_minus column in new_proportions_df:
#group and sum the new values for all levels except the level we want to replace
new_proportions_df_grouped = new_proportions_df.groupby(non_level_index_cols+levels[:-1]).sum()
#calcualte one_minus
new_proportions_df_grouped['one_minus'] = 1-new_proportions_df_grouped[values_col]
#join onto proportions_df
proportions_df = proportions_df.merge(new_proportions_df_grouped['one_minus'], on=non_level_index_cols+levels[:-1], how='left')
#multiply old values by one_minus
proportions_df[values_col] = proportions_df[values_col]*proportions_df['one_minus']
#replace old values with new values where we can
proportions_df.loc[proportions_df[values_col+'_new'].notnull(),values_col] = proportions_df.loc[proportions_df[values_col+'_new'].notnull(),values_col+'_new']
#drop all the columns we created
proportions_df = proportions_df.drop(columns=[values_col+'_new','one_minus'])

return proportions_df


#%%
# #we will now have some cases where we have data for both


# x = stocks_data.set_index(INDEX_COLS)

# #calcualte stock proportiuons for each unique index:
# #first make drive into columns by pivoting. this will allow us to create a row for each unique transport type/vehicle type/economy/dataset/date combination
# stocks_data_by_drive = stocks_data.pivot(index=INDEX_COLS, columns='Drive', values='Value')
# #now where Dataset contains 'ATO' then 

# #%%

# def insert_new_proportions(proportions_df, new_value_list, categories_list,index_row_without_categories,level):
#        """
#        proportions_df: dataframe with proportions
#        new_value_list: list of new values to insert
#        categories_list: list of categories to insert new values for. These categories are the values for the current level. eg. if current level is Drive, then categories_list could be ['bev','phev']
#        index_row_without_categories: row to insert new values for. eg. if current level is Drive, then index_row_without_categories for 2015
       
#        could be ['road','ldv','2015','National','Annual','Petrol','8th edition transport model $ Reference','Million passenger km']
#        """
#        #this will simply replace the old value with the new one, and then recalculate the proportions for the current level using (1-new * old)=old for each old proportion. 
#        new_df = proportions_df.copy()
#        values_col = level+'_proportion'
#        #filter only for data with index_row_without_level
#        new_df = new_df.loc[index_row_without_categories]
#        #remove new df from old df
#        proportions_df = proportions_df.loc[~proportions_df.index.isin(new_df.index)]

#        #create col to indcate if the row is the one with new value
#        new_df['is_new'] = False
#        for category, new_value in zip(categories_list, new_value_list):
#               #double check new value less than 1
#               if new_value>1:
#                      raise ValueError('New value is greater than 1')
#               #replace the old value with the new one
#               index_row_with_category= (*index_row_without_categories, category)
#               new_df.loc[index_row_with_category,values_col] = new_value
#               new_df.loc[index_row_with_category,'is_new'] = True

#        sum_of_new = new_value_list.sum()
#        one_minus = 1-sum_of_new

#        #for each old proportion, multiply by one_minus
#        new_df.loc[~new_df['is_new'],values_col] = new_df.loc[~new_df['is_new'],values_col]*one_minus

#        #remove is_new col
#        new_df = new_df.drop(columns='is_new')

#        #concatenate new_df to old_df
#        proportions_df = pd.concat([proportions_df, new_df])

#        return proportions_df
