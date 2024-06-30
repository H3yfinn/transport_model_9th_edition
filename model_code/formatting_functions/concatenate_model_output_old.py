#this will apply any fuel mixing on the demand side. This is can include, the use of different fule types for each drive type, for example, electricity vs oil in phev's, or even treating rail as a drive type, and splitting demand into electricity, coal and dieel rpoprtions. 

#as such, this will merge a fuel mixing dataframe onto the model output, by the Drive column, and apply the shares by doing that, resulting in a fuel column.
#this means that the supply side fuel mixing needs to occur after this script, because it will be merging on the fuel column.

#this script also contains the function transfer_growth_between_mediums(model_output_all, ECONOMY_ID) which is pretty important
#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
current_working_dir = os.getcwd()
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir =  "\\\\?\\" + re.split('transport_model_9th_edition', script_dir)[0] + 'transport_model_9th_edition'
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
def concatenate_model_output(ECONOMY_ID, SHIFT_YEARLY_GROWTH_RATE_FROM_ROAD_TO_NON_ROAD=True):
    #load model output
    road_model_output = pd.read_csv(root_dir + '\\' + 'intermediate_data\\road_model\\{}_{}'.format(ECONOMY_ID, config.model_output_file_name))#TODO WHY IS MEASURE A COLUMN IN HERE?
    non_road_model_output = pd.read_csv(root_dir + '\\' + 'intermediate_data\\non_road_model\\{}_{}'.format(ECONOMY_ID, config.model_output_file_name))
    
    # check if there are any NA's in any columns in the output dataframes. If there are, print them out
    if road_model_output.isnull().values.any():
        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
            print('there are {} NA values in the road model output. However if they are only in the user input columns for 2017 then ignore them'.format(len(road_model_output[road_model_output.isnull().any(axis=1)].loc[:, road_model_output.isnull().any(axis=0)])))
        else:
            pass
    if non_road_model_output.isnull().values.any():
        if config.PRINT_WARNINGS_FOR_FUTURE_WORK:
            print('there are {} NA values in the non road model output. However if they are only in the user input columns for 2017 then ignore them'.format(len(non_road_model_output[non_road_model_output.isnull().any(axis=1)].loc[:, non_road_model_output.isnull().any(axis=0)])))
        else:
            pass

    #also check for duplicates
    if road_model_output.duplicated().any():
        print('there are duplicates in the road model output')
    if non_road_model_output.duplicated().any():
        print('there are duplicates in the non road model output')
    
    #set medium for road
    road_model_output['Medium'] ='road'
    #concatenate road and non road models output
    model_output_all = pd.concat([road_model_output, non_road_model_output])
    
    #save
    model_output_all.to_csv(root_dir + '\\' + 'intermediate_data\\model_outputs\\{}_{}'.format(ECONOMY_ID, config.model_output_file_name), index=False)

    if SHIFT_YEARLY_GROWTH_RATE_FROM_ROAD_TO_NON_ROAD:
        model_output_all = transfer_growth_between_mediums(model_output_all, ECONOMY_ID)
                            
    return model_output_all

def transfer_growth_between_mediums(model_output_all, ECONOMY_ID):
    #some economies have plans to shift a significant portion of growth to rail or ship ior even are just expected to see above expected growth, such as air in china apparently. other examples are: chinese freight to rail or aussie passenger to rail. we dont have any interaction between the road and non road model, and also no way to shift growth to a specific medium (i.e. rail), so we will adjust the output post-hoc to account for this. Note that it will ahve weird interactions with the stocks per capita threshold we are using for passenger transport but for now we will just ignore that. (i figure im going to rewrite that part of the model anyway).
    #also, it will just assume the same makeup of drive types in the different mediums. This makes the calc easy. However if the values were large it wouldnt make sense because it should really be applied to growth and therefore new vehicles. But for now we will just assume the same makeup of drive types in the different mediums.
    #so, we will take the values from SHIFTED_YEARLY_GROWTH_RATE_FROM_MEDIUM_TO_MEDIUM_DICT, extract the transport type, medium and economy for each adjustment, and apply the shift for that subset. eg. if SHIFTED_YEARLY_GROWTH_RATE_FROM_MEDIUM_TO_MEDIUM_DICT['passenger']['road_to_rail']['01_AUS'] = 0.01, then we will take all the passenger road values for AUS and passenger rail values for aus, calcaulte the cumulative product of the growth rate over the outlook period, decrease all activity for passenger road by that amount. Calculate the effective change in passenger km and increase all activity for passenger rail by that passenger km amount.
    # e.g. in the yaml file it would look like:
    # SHIFTED_YEARLY_GROWTH_RATE_FROM_MEDIUM_TO_MEDIUM_DICT:
    #     passenger:
    #         road_to_rail:
    #             01_AUS: 0.001
    #     freight:
    #         road_to_rail:
    #             05_PRC: 0.01
    
    SHIFTED_YEARLY_GROWTH_RATE_FROM_MEDIUM_TO_MEDIUM_DICT = yaml.load(open(root_dir + '\\' + 'config\\parameters.yml', 'r'), Loader=yaml.FullLoader)['SHIFTED_YEARLY_GROWTH_RATE_FROM_MEDIUM_TO_MEDIUM_DICT']
    #create emptycsv for  _road_to_non_road_activity_change_for_plotting. it will get updated if SHIFT_YEARLY_GROWTH_RATE_FROM_ROAD_TO_NON_ROAD is true for this economy
    activity_change_for_plotting_all = pd.DataFrame(columns=config.INDEX_COLS_NO_MEASURE + ['Change_in_activity', 'New_activity', 'Original_activity', 'FROM_or_TO', 'medium_to_medium_shift'])
    for transport_type in SHIFTED_YEARLY_GROWTH_RATE_FROM_MEDIUM_TO_MEDIUM_DICT.keys():
        for medium_to_medium_shift in SHIFTED_YEARLY_GROWTH_RATE_FROM_MEDIUM_TO_MEDIUM_DICT[transport_type].keys():
            #find FROM medium and TO medium:
            from_medium = medium_to_medium_shift.split('_to_')[0]
            to_medium = medium_to_medium_shift.split('_to_')[1]
            #double check they are within the list of mediums: 
            if from_medium not in config.model_concordances_reference.Medium.unique():
                raise ValueError('from_medium {} is not in the list of mediums'.format(from_medium))
            if to_medium not in config.model_concordances_reference.Medium.unique():
                raise ValueError('to_medium {} is not in the list of mediums'.format(to_medium))
            for economy in SHIFTED_YEARLY_GROWTH_RATE_FROM_MEDIUM_TO_MEDIUM_DICT[transport_type][medium_to_medium_shift].keys():
                if economy!=ECONOMY_ID:
                    continue
                
                growth_rate_df = find_cumulative_product_of_growth_rate(SHIFTED_YEARLY_GROWTH_RATE_FROM_MEDIUM_TO_MEDIUM_DICT[transport_type][medium_to_medium_shift][economy],model_output_all)
                #apply the growth rate to the road model output    
                model_output_all, change_in_activity = apply_growth_rate_to_FROM_medium(growth_rate_df, model_output_all, economy, transport_type, from_medium)
                #and now applu the change in activity to the non road model output
                model_output_all, activity_change = apply_change_in_activity_TO_medium(change_in_activity, model_output_all, economy, transport_type, to_medium)
                
                #stack activity_change_for_plotting and change in activity so we have the shift in activity from and to each medium. and create label to indicate which is a movement from and to which medium
                
                activity_change['FROM_or_TO'] = 'TO'
                change_in_activity['FROM_or_TO'] = 'FROM'
                activity_change_for_plotting = pd.concat([activity_change, change_in_activity])
                activity_change_for_plotting['medium_to_medium_shift'] = medium_to_medium_shift
                
                activity_change_for_plotting_all = pd.concat([activity_change_for_plotting_all, activity_change_for_plotting])
    #save activity_change_for_plotting to file
    activity_change_for_plotting_all.to_csv(root_dir + '\\' + 'intermediate_data\\model_outputs\\{}_medium_to_medium_activity_change_for_plotting{}.csv'.format(ECONOMY_ID, config.FILE_DATE_ID), index=False)
    return model_output_all

def fill_missing_output_cols_with_nans(ECONOMY_ID, road_model_input_wide, non_road_model_input_wide):
    for col in config.ROAD_MODEL_OUTPUT_COLS:
        if col not in road_model_input_wide.columns:
            road_model_input_wide[col] = np.nan
    for col in config.NON_ROAD_MODEL_OUTPUT_COLS:
        if col not in non_road_model_input_wide.columns:
            non_road_model_input_wide[col] = np.nan
            
    #save to file
    road_model_input_wide.to_csv(root_dir + '\\' + 'intermediate_data\\road_model\\{}_{}'.format(ECONOMY_ID, config.model_output_file_name), index=False)
    non_road_model_input_wide.to_csv(root_dir + '\\' + 'intermediate_data\\non_road_model\\{}_{}'.format(ECONOMY_ID, config.model_output_file_name), index=False)


def find_cumulative_product_of_growth_rate(growth_rate,model_output_all):
    # growth_rate: SHIFTED_YEARLY_GROWTH_RATE_FROM_MEDIUM_TO_MEDIUM_DICT[transport_type][medium][economy]
    #this will find the cumulative product of the growth rate over the outlook period
    breakpoint()#think that the growth rate should be 1 in the first year. not sure its happning.
    growth_rate = 1 + growth_rate
    growth_rate_df = model_output_all[['Date']].drop_duplicates().copy()
    growth_rate_df['growth_rate'] = growth_rate
    #then, find the cumulative product of the growth rate over the outlook period
    growth_rate_df['cumulative_product_of_growth_rate'] = growth_rate_df['growth_rate'].cumprod()
    #we want the value in outlook base year to be 1 so that energy use remains as we expect, but afterwards we want it to be the cumulative product of the growth rate. So we should shift the cumulative product of the growth rate up one year, and then fill the first year with 1
    growth_rate_df['cumulative_product_of_growth_rate'] = growth_rate_df['cumulative_product_of_growth_rate'].shift(1)
    growth_rate_df.loc[growth_rate_df['Date']==config.OUTLOOK_BASE_YEAR, 'cumulative_product_of_growth_rate'] = 1
    return growth_rate_df
                        
def apply_growth_rate_to_FROM_medium(growth_rate_df, model_output_all, economy, transport_type, medium):
    #this will apply the growth rate to the non_road_model_output
    #first, find the model_output for the economy, transport type and medium
    model_output = model_output_all[(model_output_all['Economy']==economy)&(model_output_all['Transport Type']==transport_type)&(model_output_all['Medium']==medium)].copy()
    #then, merge the growth rate onto the road model output
    model_output = pd.merge(model_output, growth_rate_df[['Date','cumulative_product_of_growth_rate']], on='Date', how='left')
    #then, apply the growth rate to the road model output to find the cahnge. we will make this change to the road model output and also sum it up by year and add it onto the non road model output! 
    model_output['Original_activity'] = model_output['Activity'].copy()
    model_output['Change_in_activity'] = (model_output['Activity']*model_output['cumulative_product_of_growth_rate']) - model_output['Activity']
    model_output['Activity'] = model_output['Activity'] - model_output['Change_in_activity']
    #if actvity becomes negative then the growth rate from SHIFTED_YEARLY_GROWTH_RATE_FROM_MEDIUM_TO_MEDIUM_DICT is too high. so we will just set it to 0 and make the change in activity equal to the original activity. We will probably adjust the growth rate in the next iteration but at least this shows the realistic effect of the growth rate. Also create a column with flag called 'growth_rate_too_high' so we can see which ones are too high when we plot it
    model_output['GROWTH_RATE_TOO_HIGH'] = model_output['Activity']<0
    model_output.loc[model_output['Activity']<0, 'Change_in_activity'] = model_output['Original_activity']
    model_output.loc[model_output['Activity']<0, 'Activity'] = 0
    if medium!='road':
        #now have to recalculate related values such as stocks and energy demand:
        model_output['Stocks'] = model_output['Activity']/model_output['Activity_per_Stock']
        model_output['Energy'] = model_output['Activity']*model_output['Intensity']
    else:
        #now have to recalculate related values such as stocks and energy demand: #also note that the effect of apply this activity adjustment posthoc is that some things like average age of stocks and average vehicle efficnecy will not be quite right since we dont have the capacity to apply this activity adjustment so it affects new vehicles only. It shouldnt be that large an effect anyway so we will just ignore it for now (generally, say in the case of decreasing activity, it may cause the average age to be lower than what it should have been by using the average age as if there were more new cars than there actually were, and the average efficiency to be higher than it should have been by using the average efficiency as if there were more new cars than there actually were - although all of these effects have counterbalancing effects so it shouldnt be that large an effect - 
        model_output['Stocks'] = model_output['Activity']/(model_output['Occupancy_or_load']*model_output['Mileage'])
        model_output['Travel_km'] = model_output['Activity']/model_output['Occupancy_or_load']
        model_output['Energy'] = model_output['Travel_km']/model_output['Efficiency']
        model_output['Stocks_per_thousand_capita'] = model_output['Stocks']/model_output['Population']
        
    #recalcualte activity growth
    activity_growth = model_output[['Date','Activity']].groupby('Date').sum().pct_change().fillna(0).reset_index()
    activity_growth.rename(columns={'Activity':'Activity_growth'}, inplace=True)
    model_output = pd.merge(model_output.drop(columns=['Activity_growth']), activity_growth, on='Date', how='left')
    
    #FINGERS CROSSED I CAN JUST LEAVE THE AGE DISTRIBUTION AS IS... AND ALSO NO ZERO RELATED ERRORS? < unless the values get too big i think its ok
    #Separate Change_in_activity to apply to non road model output
    change_in_activity = model_output[config.INDEX_COLS_NO_MEASURE + ['Change_in_activity', 'cumulative_product_of_growth_rate', 'Original_activity', 'Activity', 'GROWTH_RATE_TOO_HIGH']].reset_index().copy()
    change_in_activity.rename(columns={'Activity':'New_activity'}, inplace=True)
    #then, drop the growth rate column
    model_output.drop(columns=['cumulative_product_of_growth_rate', 'Change_in_activity', 'Original_activity', 'GROWTH_RATE_TOO_HIGH'], inplace=True)
    
    #join it to all other mediums data
    model_output_all = model_output_all.loc[(model_output_all['Economy']!=economy)|(model_output_all['Transport Type']!=transport_type)|(model_output_all['Medium']!=medium)].copy()
    model_output_all = pd.concat([model_output_all, model_output])
    return model_output_all, change_in_activity


def apply_change_in_activity_TO_medium(change_in_activity, model_output_all, economy, transport_type, medium):
    model_output = model_output_all.loc[(model_output_all['Economy']==economy)&(model_output_all['Transport Type']==transport_type)&(model_output_all['Medium']==medium)].copy()                            
    model_output = pd.merge(model_output, change_in_activity[['Date', 'Change_in_activity', 'GROWTH_RATE_TOO_HIGH']].groupby(['Date', 'GROWTH_RATE_TOO_HIGH']).sum(numeric_only=True).reset_index(), on='Date', how='left')
    
    #calculate percentage of mediums total activity per year using transform function
    model_output['Original_activity'] = model_output['Activity'].copy()
    model_output['Percentage_of_total_activity'] = model_output.groupby('Date')['Activity'].transform(lambda x: x/x.sum())
    model_output['Drive_specific_change_in_activity'] = model_output['Percentage_of_total_activity']*(model_output['Change_in_activity'])
    model_output['Activity'] = model_output['Activity'] + model_output['Drive_specific_change_in_activity']
    
    #now have to recalculate related values such as stocks and energy demand:
    if medium!='road':
        model_output['Stocks'] = model_output['Activity']/model_output['Activity_per_Stock']
        model_output['Energy'] = model_output['Activity']*model_output['Intensity']
    else:
        model_output['Stocks'] = model_output['Activity']/(model_output['Occupancy_or_load']*model_output['Mileage'])
        model_output['Travel_km'] = model_output['Activity']/model_output['Occupancy_or_load']
        model_output['Energy'] = model_output['Travel_km']/model_output['Efficiency']
        model_output['Stocks_per_thousand_capita'] = model_output['Stocks']/model_output['Population']
        
    #recalcualte activity growth
    activity_growth = model_output[['Date','Activity']].groupby('Date').sum().pct_change().fillna(0).reset_index()
    model_output = pd.merge(model_output.drop(columns=['Activity_growth']), activity_growth.rename(columns={'Activity':'Activity_growth'}), on='Date', how='left')
    
    #seperate the change in activity so we can plot it against the change_in_activity from the road model:
    activity_change = model_output[config.INDEX_COLS_NO_MEASURE + ['Drive_specific_change_in_activity', 'Original_activity', 'Activity', 'GROWTH_RATE_TOO_HIGH']].reset_index().copy()
    activity_change.rename(columns={'Drive_specific_change_in_activity':'Change_in_activity', 'Activity':'New_activity'}, inplace=True)
    #add cumulative product of growth rate to activity_change:
    activity_change = pd.merge(activity_change, change_in_activity[['Date', 'cumulative_product_of_growth_rate']].drop_duplicates(), on='Date', how='left')
    # # activity_change_for_plotting = pd.merge(change_in_activity, activity_change, on=config.INDEX_COLS_NO_MEASURE, how='left')
    # activity_change_for_plotting = pd.concat([change_in_activity, activity_change])
    # #rename the cols
    # activity_change_for_plotting.rename(columns={'Change_in_activity':'road_change_in_activity', 'Drive_specific_change_in_activity':'non_road_change_in_activity'}, inplace=True)
    
    #now drop the change in activity column
    model_output.drop(columns=['Change_in_activity', 'Percentage_of_total_activity', 'Drive_specific_change_in_activity', 'GROWTH_RATE_TOO_HIGH'], inplace=True)
    #join model_output_all and model_output
    model_output_all = model_output_all.loc[(model_output_all['Economy']!=economy)|(model_output_all['Transport Type']!=transport_type)|(model_output_all['Medium']!=medium)].copy()
    model_output_all = pd.concat([model_output_all, model_output])
    
    return model_output_all, activity_change

#%%
# a = concatenate_model_output('05_PRC')#dont think its working aye

#%%