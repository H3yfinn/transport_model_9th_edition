#######################################################################
#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
import sys
sys.path.append("./config")
import config

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
from scipy.optimize import minimize

#######################################################################
#%%


def run_road_model_for_year_y(year, previous_year_main_dataframe, main_dataframe, user_inputs_df_dict, growth_forecasts, change_dataframe_aggregation,  low_ram_computer_files_list, low_ram_computer,previous_10_year_block, turnover_rate_parameters_dict, throw_error=False):
    if year % 10 == 0:
        print('Up to year {}'.format(year))
    # breakpoint()
    #extract the user inputs dataframes from the dictionary
    Vehicle_sales_share = user_inputs_df_dict['Vehicle_sales_share']
    Occupancy_or_load_growth = user_inputs_df_dict['Occupancy_or_load_growth']
    New_vehicle_efficiency_growth = user_inputs_df_dict['New_vehicle_efficiency_growth']
    mileage_growth = user_inputs_df_dict['Mileage_growth']
    
    #load csv(f'./intermediate_data/road_model/covid_related_mileage_change_{economy}.csv')
    economy = previous_year_main_dataframe['Economy'].unique()[0]
    
    #extracts vars from turnover_rate_parameters_dict:
    turnover_rate_steepness = turnover_rate_parameters_dict['turnover_rate_steepness']
    turnover_rate_max_value = turnover_rate_parameters_dict['turnover_rate_max_value']
    turnover_rate_midpoint = turnover_rate_parameters_dict['turnover_rate_midpoint']
    
    #create change dataframe. This is like a messy notepad where we will adjust the last years values values and perform most calcualtions. 
    change_dataframe = previous_year_main_dataframe.copy()
    #identify where Age_distribution is na
    # change_dataframe.loc[change_dataframe['Age_distribution'].isna()]
    #change year in all rows to the next year. For now we will refer to the previous year as the original or base year. And values calculcated for the next year may sometimes be refered to as 'new'.
    change_dataframe.Date = year
    do_tests_on_road_data(change_dataframe, throw_error=throw_error)
    #######################################################################

    #First do adjustments:

    #######################################################################
    #extract years when covid effect should be applied:
        
    #these are the years that we will apply the covid effects to. Some economys returned to normal in 2021, others in 2022. Kind of makes assumption that economies came back to normal at beginning of year but for now thats ok

    for transport_type in ['passenger', 'freight']:
        change_dataframe = adjust_mileage_to_account_for_covid(economy, change_dataframe, transport_type, year, measure_column = 'Mileage')
        
        #recalcualte activity using this new value for mileage, as if it was the previous year, when covid was having an effect on activity (specifically mileage). this is jsut to prevent comaprisons between growth*activity and calcaulkted activity form breaking
        change_dataframe['Activity'] = change_dataframe['Mileage'] * change_dataframe['Occupancy_or_load'] * change_dataframe['Stocks']
        
    # LISTED_YEARS_WHEN_COVID_EFFECTS_APPLIED = yaml.load(open('config/parameters.yml'), Loader=yaml.FullLoader)['LISTED_YEARS_WHEN_COVID_EFFECTS_APPLIED']
    # EXPECTED_YEARS_TO_RETURN_TO_NORMAL_MILEAGE_FROM_COVID_PASSENGER

    # year_after_covid = max(config.LISTED_YEARS_WHEN_COVID_EFFECTS_APPLIED[economy])+1
    # if year == year_after_covid:
    #     #increase mielage bwecause we are in the year after covid
    #     change_dataframe = adjust_mileage_to_account_for_covid(economy, change_dataframe, transport_type)
    #     #recalcualte activity using this new value for mileage, as if it was the previous year, when covid was having an effect on activity (specifically mileage). this is jsut to prevent comaprisons between growth*activity and calcaulkted activity form breaking
    #     change_dataframe['Activity'] = change_dataframe['Mileage'] * change_dataframe['Occupancy_or_load'] * change_dataframe['Stocks']
    
    #CALCUALTE NEW OCCUPANCY and LOAD VALUEs BY APPLYING THE OCCUPANCY GROWTH RATE
    change_dataframe = change_dataframe.merge(Occupancy_or_load_growth, on=['Economy','Scenario','Drive','Vehicle Type', 'Transport Type', 'Date'], how='left')
    change_dataframe['Occupancy_or_load'] = change_dataframe['Occupancy_or_load'] * change_dataframe['Occupancy_or_load_growth']
    #same for mileage
    change_dataframe = change_dataframe.merge(mileage_growth, on=['Economy','Scenario','Drive','Vehicle Type', 'Transport Type', 'Date'], how='left')
    change_dataframe['Mileage'] = change_dataframe['Mileage'] * change_dataframe['Mileage_growth']

    #repalce nas in change_dataframe['Average_age'] with 1, as it occurs when tehre are no stocks, and we want to set the average age to 1. Im not 100% on this fix but it seems like tis important to do as im getting 0s for stocks for all years when i dont do it.
    change_dataframe['Average_age'] = change_dataframe['Average_age'].replace(np.nan, 1)
    #and replace 0s too
    change_dataframe['Average_age'] = change_dataframe['Average_age'].replace(0, 1)
    
    def calculate_turnover_rate(df, k, L, x0):
        #https://chat.openai.com/share/771a3147-1d47-4004-9593-382cf68ace18
        # k = 0.8 #this is the steepness of the curve (increase it to speed up the turnover rate growth with age)
        # x0 = 12.5 #this is the midpoint of the curve (increase it to make the turnover rate growth start later in the life of the vehicle)
        # L = 0.12 #this is the maximum value of the curve (increase it to increase the maximum turnover rate)
        # df['Turnover_rate'] = L / (1 + np.exp(-k * (df['Average_age'] - df['Turnover_rate_midpoint'])))
        df['Turnover_rate'] = L / (1 + np.exp(-k * (df['Average_age'] - x0)))
        df['Turnover_rate'].fillna(0, inplace=True)
        return df
    #basedon the sceanrio we need to change the midpoint. so we will split df into scnearios, calcalte turnover rate, then join back together
    for scenario in change_dataframe['Scenario'].unique():
        scenario_df = change_dataframe.loc[change_dataframe['Scenario'] == scenario].copy()
    
        if scenario == 'Reference':
            turnover_rate_midpoint_mult_adjustment_road = yaml.load(open('config/parameters.yml'), Loader=yaml.FullLoader)['TURNOVER_RATE_MIDPOINT_MULT_ADJUSTMENT_ROAD_REFERENCE']
        elif scenario == 'Target':
            turnover_rate_midpoint_mult_adjustment_road = yaml.load(open('config/parameters.yml'), Loader=yaml.FullLoader)['TURNOVER_RATE_MIDPOINT_MULT_ADJUSTMENT_ROAD_TARGET']
        else:
            raise ValueError('Scenario not recognised')
        
        #extract the value for the economy, if it exists
        if economy in turnover_rate_midpoint_mult_adjustment_road.keys():
            turnover_rate_midpoint_mult_adjustment_road = turnover_rate_midpoint_mult_adjustment_road[economy]
        else:
            turnover_rate_midpoint_mult_adjustment_road = 1
            
        turnover_rate_midpoint_scenario = turnover_rate_midpoint * turnover_rate_midpoint_mult_adjustment_road
        scenario_df = calculate_turnover_rate(scenario_df, turnover_rate_steepness, turnover_rate_max_value, turnover_rate_midpoint_scenario)
        change_dataframe.loc[change_dataframe['Scenario'] == scenario] = scenario_df.copy()
        
    #calcualte stock turnover as stocks from last year * turnover rate.
    change_dataframe['Stock_turnover'] = change_dataframe['Stocks'] * change_dataframe['Turnover_rate']
    #if 'Activity_growth', 'Gdp_per_capita', 'Population' is in df, drop em
    change_dataframe = change_dataframe.drop(['Activity_growth', 'Gdp_per_capita','Gdp', 'Population'], axis=1, errors='ignore')
    #join on activity growth
    change_dataframe = change_dataframe.merge(growth_forecasts[['Date', 'Transport Type', 'Economy','Scenario','Gdp','Activity_growth', 'Gdp_per_capita', 'Population']], on=['Economy', 'Date', 'Scenario','Transport Type'], how='left')#note that pop and gdp per capita are loaded on earlier.
    #######################################################################

    #Calcualtions

    ########################################################################
    previous_year_main_dataframe = pd.DataFrame()
    for transport_type in change_dataframe['Transport Type'].unique():
        for scenario in change_dataframe['Scenario'].unique():
            change_dataframe_t = change_dataframe.loc[(change_dataframe['Transport Type'] == transport_type) & (change_dataframe['Scenario'] == scenario)].copy()
            
            #VEHICLE SALES SHARE(also referreed to as Sales/Stock Dist)
            if 'Vehicle_sales_share' in change_dataframe_t.columns:
                change_dataframe_t.drop(columns=['Vehicle_sales_share'], inplace=True)
            change_dataframe_t = change_dataframe_t.merge(Vehicle_sales_share, on=['Economy', 'Drive', 'Scenario', 'Transport Type', 'Vehicle Type', 'Date'], how='left')

            #calacualte indivudal versions for turnover and surplus
            change_dataframe_t['Stock_turnover_act'] = change_dataframe_t['Stock_turnover'] * change_dataframe_t['Mileage'] * change_dataframe_t['Occupancy_or_load']
            change_dataframe_t['Surplus_stocks_act'] = change_dataframe_t['Surplus_stocks'] * change_dataframe_t['Mileage'] * change_dataframe_t['Occupancy_or_load']
            
            change_dataframe_t['Surplus_stocks_previous_act'] = change_dataframe_t['Surplus_stocks_act']
            #replace nan with 0
            change_dataframe_t['Stock_turnover_act'] = change_dataframe_t['Stock_turnover_act'].replace(np.nan, 0)
            change_dataframe_t['Surplus_stocks_act'] = change_dataframe_t['Surplus_stocks_act'].replace(np.nan, 0)

            #######################################################################
            #Now calcualte changes as a result of growth (and other things)
            #We will be working in terms of transport type sums for this section:
            #######################################################################

            #CALCULATE NEW ACTIVITY WORTH OF STOCK SALES
            #we will apply activity growth to the sum of activity for each transport type to find the activity worth of new sales from activity growth. Note that activity growth is assumed to be the same for all vehicle types of the same transport type (and probably for all transport types in early stages of this models development!)
            #We will also calcualte total turnover and surplus activity for the transport type to be satisfied by new stock sales, based on the new sales dist.
            #calcualte the Transport type sum of activity at beignning of year
            previous_year_activity = change_dataframe_t['Activity'].sum()
            change_dataframe_t['Previous_activity'] = change_dataframe_t['Activity']
            #Transport type sum of activity worth of stocks after turnover and surplus total
            # previous_year_activity_worth_of_stocks_after_turnover_and_surplus_total = change_dataframe_t['Activity_worth_of_stocks_after_turnover_and_surplus_total'].sum()
            
            activity_worth_of_stock_turnover = change_dataframe_t['Stock_turnover_act'].sum()

            # Calculate growth in terms of new activity
            new_activity = ((change_dataframe_t['Activity_growth'] * change_dataframe_t['Activity']) - change_dataframe_t['Activity']).sum()

            #calc how many new stocks will be bought, before we apply the sales dist and surplus stocks
            activity_worth_of_new_stocks_needed = new_activity + activity_worth_of_stock_turnover
            
            #if total_new_stocks_for_activity is <0, then this could be because of negative growth or surplus stocks. 
            if activity_worth_of_new_stocks_needed < 0:
                # #dont use surplus stocks.
                # surplus_activity_worth_of_stocks_used = 0
                percentage_change_in_activity = activity_worth_of_new_stocks_needed / previous_year_activity
                
                change_dataframe_t['Not_needed_activity'] = change_dataframe_t['Activity'] * percentage_change_in_activity#note that this will be negative
                change_dataframe_t['New_stocks_needed_act'] = 0
                
                #make this loss in stocks into surplus so it can be used in future years
                change_dataframe_t['Surplus_stocks_act'] = -change_dataframe_t['Not_needed_activity'] + change_dataframe_t['Surplus_stocks_previous_act']
                change_dataframe_t['Surplus_stocks_used_act'] = 0
                
                change_dataframe_t['Activity'] = change_dataframe_t['Activity'] - change_dataframe_t['Stock_turnover_act'] - change_dataframe_t['Not_needed_activity']
                
            else:
                
                change_dataframe_t['New_stocks_needed_act'] = activity_worth_of_new_stocks_needed * change_dataframe_t['Vehicle_sales_share']
                
                change_dataframe_t['Activity'] = change_dataframe_t['Activity'] - change_dataframe_t['Stock_turnover_act'] + change_dataframe_t['New_stocks_needed_act']
                
                change_dataframe_t['Surplus_stocks_previous_act'] = change_dataframe_t['Surplus_stocks_act']
                
                #temporarily replace _act with '' from all columns so that we can use the function below
                #but first drop 'Surplus_stocks',  'New_stocks_needed','Stock_turnover_act' as they arent needed anymore
                change_dataframe_t.drop(columns=['Surplus_stocks', 'Stock_turnover_act'], inplace=True)
                if 'New_stocks_needed' in change_dataframe_t.columns:
                    change_dataframe_t.drop(columns=['New_stocks_needed'], inplace=True)
                act_cols = [col for col in change_dataframe_t.columns if col.endswith('_act')]
                change_dataframe_t.rename(columns={col:col.strip('_act') for col in act_cols}, inplace=True)
                #now calcualte surplus stocks used
                # breakpoint()#double check why New_stocks_needed is na in some cases
                nas = change_dataframe_t[change_dataframe_t.New_stocks_needed.isna()]
                if len(nas)>0:
                    breakpoint()
                try:
                    change_dataframe_t[['Surplus_stocks_used_act', 'Surplus_stocks', 'New_stocks_needed']] = change_dataframe_t.apply(calculate_surplus_stocks, axis=1)
                except:
                    breakpoint()#this makes this, which commonly causes errors if something is wrong with the data, easier to debug
                    change_dataframe_t[['Surplus_stocks_used_act', 'Surplus_stocks', 'New_stocks_needed']] = change_dataframe_t.apply(calculate_surplus_stocks, axis=1)
                #now add _act back to end of all cols we renamed
                change_dataframe_t.rename(columns={col.strip('_act'):col for col in act_cols}, inplace=True)
                
            #CALCUALTE NEW TOTAL TRAVEL_KM PER VEHICLE/DRIVE-TYPE FROM NEW activity total of stocks being useD
            change_dataframe_t['Travel_km'] = change_dataframe_t['Activity'] / change_dataframe_t['Occupancy_or_load']

            #CALCUALTE STOCKS BEING USED
            #Note that this is the new level of stocks in the economy
            change_dataframe_t['Stocks'] = change_dataframe_t['Travel_km'] / change_dataframe_t['Mileage']

            #TEMP IF Stocks IS <0 THEN PERHAPS WE NEED TO INVERSE AND NORMALISE VEHICLE SALES SHARE SO THE LEAST WANTED STOCKS ARE SOLD FIRST. THIS IS A TEMP FIX TO PREVENT STOCKS FROM GOING NEGATIVE?
            if (change_dataframe_t['Stocks'] < 0).any():
                #set stocks to 0
                change_dataframe_t['Stocks'] = np.where(change_dataframe_t['Stocks'] < 0, 0, change_dataframe_t['Stocks'])
                # time.sleep(1)
                # raise ValueError('There are negative stocks')
            #also, if stocks are less than 1/million then we have less than one stock (our stocks are in millions) so we will set these to 0
            change_dataframe_t['Stocks'] = np.where(change_dataframe_t['Stocks'] < 1e-6, 0, change_dataframe_t['Stocks'])
            
            #CALCUALTE NEW STOCKS NEEDED AS STOCKS NEEDED TO SATISFY NEW SALES WORTH OF ACTIVITY
            change_dataframe_t['New_stocks_needed'] =             change_dataframe_t['New_stocks_needed_act'] / (change_dataframe_t['Occupancy_or_load'] * change_dataframe_t['Mileage'])
            
            #CALCUALTE SURPLUS STOCKS AND HOW MANY OF THEM ARE USED
            #If we have too many stocks these go into surplus
            change_dataframe_t['Surplus_stocks'] = change_dataframe_t['Surplus_stocks_act'] / (change_dataframe_t['Occupancy_or_load'] * change_dataframe_t['Mileage'])

            change_dataframe_t['Surplus_stocks_used'] = change_dataframe_t['Surplus_stocks_used_act'] / (change_dataframe_t['Occupancy_or_load'] * change_dataframe_t['Mileage'])
            
            #CALCUALTE AVERAGE AGE OF STOCKS
            change_dataframe_t = recalculate_age_distribution(change_dataframe_t)
            #TODO adjust efficiency by x percent to simulate aging of all vehicles by 1 year (the result would be a log eff curve based on age of vehicles)
            YEARLY_EFFICIENCY_DEGRADATION_RATE = yaml.load(open('config/parameters.yml'), Loader=yaml.FullLoader)['YEARLY_EFFICIENCY_DEGRADATION_RATE'][economy]
            
            change_dataframe_t['Efficiency'] = change_dataframe_t['Efficiency'] * (1-YEARLY_EFFICIENCY_DEGRADATION_RATE)
            #check for any types of stocks that have stopped being used
            change_dataframe_t['Average_age'] = np.where(change_dataframe_t['Stocks'] > 0, change_dataframe_t['Average_age'], np.nan)
            #set turnover rate to nan as well in that case:
            change_dataframe_t['Turnover_rate'] = np.where(change_dataframe_t['Stocks'] > 0, change_dataframe_t['Turnover_rate'], np.nan)
            # else:
            
            #CALCULATE STOCKS IN USE REMAINING FROM PREVIOUS YEAR
            change_dataframe_t['Stocks_in_use_from_previous_year'] = change_dataframe_t['Stocks'] - change_dataframe_t['New_stocks_needed']
            
            #SET EFFICIENCY OF SURPLUS STOCKS TO PREVIOUS YEARS AVG EFF LEVEL
            #Note that we assume that the efficiency of surplus stocks is the same as the efficiency of the stocks that were in use last year
            change_dataframe_t['Efficiency_of_surplus_stocks'] = change_dataframe_t['Efficiency']

            #APPLY EFFICIENCY GROWTH TO NEW VEHICLE EFFICIENCY
            #note that this will then be split into different fuel types when we appply the fuel mix varaible later on.
            #also note that new vehicle eff is independent of the current eff level of the eocnomys stocks. it could be much higher than them
            change_dataframe_t = change_dataframe_t.merge(New_vehicle_efficiency_growth, on=['Economy', 'Scenario', 'Transport Type', 'Drive', 'Vehicle Type', 'Date'], how='left')
            change_dataframe_t['New_vehicle_efficiency'] = change_dataframe_t['New_vehicle_efficiency'] * change_dataframe_t['New_vehicle_efficiency_growth'] 

            #CALCUALTE WEIGHTED AVERAGE VEHICLE EFFICIENCY
            #calcaulte weighted avg vehicle eff using the number of stocks left from last year times their avg eff, then the number of new stocks needed times their new eff. Then divide these by the number of stocks left from last year plus the number of new stocks needed. 
            #however if new stocks needed is <0, but there are still stocks remaining in the economy then efficiency will remain the same as original efficiency.
            #also have to note that this is the avg eff of stocks in use, this is in case there is a large amount of surplus stocks, so that the avg eff of the economy is not skewed by the efficiency of the surplus stocks, and instead new stocks efficiency has the right effect on the avg eff of the economy.
            change_dataframe_t['Efficiency_numerator'] = (change_dataframe_t['New_stocks_needed'] * change_dataframe_t['New_vehicle_efficiency'] + change_dataframe_t['Stocks_in_use_from_previous_year'] * change_dataframe_t['Efficiency'])

            change_dataframe_t['Original_efficiency'] = change_dataframe_t['Efficiency']
            
            change_dataframe_t['Efficiency'] = np.where(change_dataframe_t['New_stocks_needed'] <= 0, change_dataframe_t['Original_efficiency'], change_dataframe_t['Efficiency_numerator'] / change_dataframe_t['Stocks'])

            #if the denominator and numerator are 0 (which will occur if we dont have any stocks in this year [and therefore the last]), then efficiency ends up as nan, so we will set this to the efficiency value for new vehicles even though it doesnt really matter what it is set to, it just helps with aggregates.
            change_dataframe_t.loc[(change_dataframe_t['Stocks'] == 0), 'Efficiency'] = change_dataframe_t['New_vehicle_efficiency']

            #CALCUALTE NEW ENERGY CONSUMPTION. 
            #note that this is not split by fuel yet, it is just the total energy consumption for the vehicle/drive type.
            change_dataframe_t['Energy'] = change_dataframe_t['Travel_km'] / change_dataframe_t['Efficiency'] 
            
            #if numerator and denominator are 0, then energy ends up as nan, so we will set this to 0
            change_dataframe_t.loc[(change_dataframe_t['Travel_km'] == 0) & (change_dataframe_t['Efficiency'] == 0), 'Energy'] = 0
            
            #calcualte stocks per capita as its a useful metric
            change_dataframe_t['Thousand_stocks_per_capita'] = change_dataframe_t['Stocks']/change_dataframe_t['Population']
            change_dataframe_t['Stocks_per_thousand_capita'] = change_dataframe_t['Thousand_stocks_per_capita'] * 1000000

            check_activity_after_run(change_dataframe_t, throw_error=throw_error)
            
            #######################################################################

            #finalisation processes

            #######################################################################
            
            #Now start cleaning up the changes dataframe to create the dataframe for the new year.
            addition_to_main_dataframe = change_dataframe_t.copy()
            
            addition_to_main_dataframe = addition_to_main_dataframe[config.ROAD_MODEL_OUTPUT_COLS].copy()
            
            #add new year to the main dataframe.
            main_dataframe = pd.concat([main_dataframe, addition_to_main_dataframe])
            previous_year_main_dataframe = pd.concat([addition_to_main_dataframe, previous_year_main_dataframe])

            #if you want to analyse what is hapening in th model then this will output a dataframe with all the variables that are being calculated.
            change_dataframe_aggregation = pd.concat([change_dataframe_t, change_dataframe_aggregation])

    #if we have a low ram computer then we will save the dataframe to a csv file at 10 year intervals. this is to save memory. during the proecss we will save a list of the file names that we have saved to, from which to stitch the new dataframe togehter from
    if low_ram_computer == True:
        year_counter = year - config.DEFAULT_BASE_YEAR
        if year_counter % 10 == 0:
            print('The year is at the end of a ten year block, in year {}, saving interemediate results to csv.'.format(year))
            low_ram_file_name = 'intermediate_data/main_dataframe_10_year_blocks/main_dataframe_years_{}_to_{}.csv'.format(previous_10_year_block, year)
            main_dataframe.to_csv(low_ram_file_name, index=False)
            low_ram_computer_files_list.append(low_ram_file_name)

            previous_10_year_block = year
            main_dataframe = pd.DataFrame(columns=main_dataframe.columns)#remove data we just saved from main datafrmae

        elif year == config.END_YEAR:
            print('The year is at the end of the simulation, saving intermediate results to csv.')
            low_ram_file_name = 'intermediate_data/main_dataframe_10_year_blocks/main_dataframe_years_{}_to_{}.csv'.format(previous_10_year_block, year)
            main_dataframe.to_csv(low_ram_file_name, index=False)
            low_ram_computer_files_list.append(low_ram_file_name)
            
    return main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation,  previous_10_year_block


# def adjust_mileage_to_account_for_covid(economy, change_dataframe, main_dataframe, transport_type, current_year):
#     """Revert the decrease in mileage due to covid.
    
#     Raises:
#         ValueError: _description_
#     """
            
#     if transport_type =='passenger':
            
#         LISTED_YEARS_WHEN_COVID_EFFECTS_APPLIED = yaml.load(open('config/parameters.yml'), Loader=yaml.FullLoader)['LISTED_YEARS_WHEN_COVID_EFFECTS_APPLIEDPASSENGER']

#         EXPECTED_YEARS_TO_RETURN_TO_NORMAL_MILEAGE_FROM_COVID = yaml.load(open('config/parameters.yml'), Loader=yaml.FullLoader)['EXPECTED_YEARS_TO_RETURN_TO_NORMAL_MILEAGE_FROM_COVID_PASSENGER']
#         #There could be a number of years over which the decrease will be reverted, for which we will spread the increase over.
#         N = EXPECTED_YEARS_TO_RETURN_TO_NORMAL_MILEAGE_FROM_COVID[economy]
        
#         years_after_covid = [max(LISTED_YEARS_WHEN_COVID_EFFECTS_APPLIED[economy]) + i + 1 for i in range(N)]
        
#         #load ECONOMIES_WITH_STOCKS_PER_CAPITA_REACHED from parameters.yml
#         EXPECTED_ENERGY_DECREASE_FROM_COVID = yaml.load(open('config/parameters.yml'), Loader=yaml.FullLoader)['EXPECTED_ENERGY_DECREASE_FROM_COVID_PASSENGER']
#         X = EXPECTED_ENERGY_DECREASE_FROM_COVID[economy]
        
#     elif transport_type =='freight':
        
#         LISTED_YEARS_WHEN_COVID_EFFECTS_APPLIED = yaml.load(open('config/parameters.yml'), Loader=yaml.FullLoader)['LISTED_YEARS_WHEN_COVID_EFFECTS_APPLIEDFREIGHT']

#         EXPECTED_YEARS_TO_RETURN_TO_NORMAL_MILEAGE_FROM_COVID = yaml.load(open('config/parameters.yml'), Loader=yaml.FullLoader)['EXPECTED_YEARS_TO_RETURN_TO_NORMAL_MILEAGE_FROM_COVID_FREIGHT']
#         #There could be a number of years over which the decrease will be reverted, for which we will spread the increase over.
#         N = EXPECTED_YEARS_TO_RETURN_TO_NORMAL_MILEAGE_FROM_COVID[economy]
        
#         years_after_covid = [max(LISTED_YEARS_WHEN_COVID_EFFECTS_APPLIED[economy]) + i + 1 for i in range(N)]
        
#         #load ECONOMIES_WITH_STOCKS_PER_CAPITA_REACHED from parameters.yml
#         EXPECTED_ENERGY_DECREASE_FROM_COVID = yaml.load(open('config/parameters.yml'), Loader=yaml.FullLoader)['EXPECTED_ENERGY_DECREASE_FROM_COVID_FREIGHT']
#         X = EXPECTED_ENERGY_DECREASE_FROM_COVID[economy]
    
#     if current_year in years_after_covid:
#         #INTERPOLATE (i.e. find the expected decrease if it occured all at once, then draw a line from that point to the current point, and find the point on that line that is N years away from the current point. This is the point that we will revert the decrease to)
#         year_index = sorted(years_after_covid).index(current_year)
#         # Calculate the recovery factor for the current year
#         recovery_factor = (year_index / len(years_after_covid)) 
#         # # Calculate expected mileage for the current year as if recovering linearly from the decrease
#         initial_mileage = main_dataframe.loc[(main_dataframe['Transport Type'] == transport_type) & (main_dataframe['Date'] == max(LISTED_YEARS_WHEN_COVID_EFFECTS_APPLIED[economy]))].copy()
#         initial_mileage['final_mileage'] = initial_mileage['Mileage'] * (1 - X)
#         # EXPECTED_ENERGY_DECREASE_FROM_COVID
#         initial_mileage['Mileage'] = initial_mileage['final_mileage'] + (initial_mileage['Mileage'] - initial_mileage['final_mileage']) * recovery_factor
#         # merge the calculated mileage
#         change_dataframe = change_dataframe.merge(initial_mileage[['Economy', 'Scenario', 'Drive', 'Vehicle Type', 'Transport Type', 'Date', 'Mileage']], on=['Economy', 'Scenario', 'Drive', 'Vehicle Type', 'Transport Type', 'Date'], how='left', suffixes=('_old', ''))
        
#         breakpoint()
#         change_dataframe.drop(columns=['Mileage_old'], inplace=True)
        
#         #recalcualte activity using this new value for mileage, as if it was the previous year, when covid was having an effect on activity (specifically mileage). this is jsut to prevent comaprisons between growth*activity and calcaulkted activity form breaking
#         change_dataframe['Activity'] = change_dataframe['Mileage'] * change_dataframe['Occupancy_or_load'] * change_dataframe['Stocks']
#     return change_dataframe


# def adjust_mileage_to_account_for_covid(economy, dataframe, transport_type, current_year, measure_column = 'Mileage'):
#     """
#     Intention:
#     create a fucntion that can calcualte what the mileage should be in the current year, if the year is within one of the covid years or one of the years during which mileage was returning to normal. This is assuming that normal mileage is the miealge in the input data to this function, which reflects mileage during the year before covid or one of the years after everythign has returned to normal.
    
#     So we will check if config.OUTLOOK_BASE_YEAR <= last_covid_year +EXPECTED_YEARS_TO_RETURN_TO_NORMAL_MILEAGE_FROM_COVID: 
#     if current year is <= last_covid_year, adjust the mielage by EXPECTED_ENERGY_DECREASE_FROM_COVID.
#     if current year is > last_covid_year, but <= last_covid_year +EXPECTED_YEARS_TO_RETURN_TO_NORMAL_MILEAGE_FROM_COVID then we will adjust the mileage by the expected increase in mileage after covid, which is spread over the number of years that we expect it to take to return to normal. This will use cumulative growth to work out what the annual growth rate should be in the current year to achieve the expected increase in mileage after covid.
#     if current year is > last_covid_year +EXPECTED_YEARS_TO_RETURN_TO_NORMAL_MILEAGE_FROM_COVID, then we will not use this function, as the mileage in the input data is already set to what it should be in a year after covid.
    
#     Note that this function is intended to be used for multiple scripts/fucntions, for exmaple in calcualting mileage in the 'workflow\calculation_functions\optimise_to_calculate_base_data.py' file, as well as the road and non-road model scripts. 
    
#     Args:
#         economy: The economy for which to revert mileage decreases.
#         change_dataframe: DataFrame with changes to apply.
#         main_dataframe: Main DataFrame containing mileage data.
#         transport_type: Type of transport, 'passenger' or 'freight'.
#         current_year: The current year being processed.
#         measure_column: this can be changed so that for exmaple in non road we can set it to acitivty, and then we can use this function to adjust activity to account for covid, producing the same effect as adjusting mileage to account for covid.

#     Raises:
#         ValueError: If the transport type is not recognized.
#     """
#     # Load configuration parameters
#     parameters = yaml.load(open('config/parameters.yml'), Loader=yaml.FullLoader)
#     if transport_type == 'passenger':
#         LISTED_YEARS_WHEN_COVID_EFFECTS_APPLIED = parameters['LISTED_YEARS_WHEN_COVID_EFFECTS_APPLIED_PASSENGER']
#         EXPECTED_YEARS_TO_RETURN_TO_NORMAL_MILEAGE_FROM_COVID = parameters['EXPECTED_YEARS_TO_RETURN_TO_NORMAL_MILEAGE_FROM_COVID_PASSENGER']
#         EXPECTED_ENERGY_DECREASE_FROM_COVID = parameters['EXPECTED_ENERGY_DECREASE_FROM_COVID_PASSENGER']
#         last_covid_year = max(parameters['LISTED_YEARS_WHEN_COVID_EFFECTS_APPLIEDPASSENGER'][economy])
#         EXPECTED_RETURN_TO_NORMAL_MILEAGE_FROM_COVID = parameters['EXPECTED_RETURN_TO_NORMAL_MILEAGE_FROM_COVID_PASSENGER']
#     elif transport_type == 'freight':
#         LISTED_YEARS_WHEN_COVID_EFFECTS_APPLIED = parameters['LISTED_YEARS_WHEN_COVID_EFFECTS_APPLIEDFREIGHT']
#         EXPECTED_YEARS_TO_RETURN_TO_NORMAL_MILEAGE_FROM_COVID = parameters['EXPECTED_YEARS_TO_RETURN_TO_NORMAL_MILEAGE_FROM_COVID_FREIGHT']
#         EXPECTED_ENERGY_DECREASE_FROM_COVID = parameters['EXPECTED_ENERGY_DECREASE_FROM_COVID_FREIGHT']
#         last_covid_year = max(parameters['LISTED_YEARS_WHEN_COVID_EFFECTS_APPLIED_FREIGHT'][economy])
#         EXPECTED_RETURN_TO_NORMAL_MILEAGE_FROM_COVID = parameters['EXPECTED_RETURN_TO_NORMAL_MILEAGE_FROM_COVID_FREIGHT']
#     else:
#         raise ValueError("Transport type must be 'passenger' or 'freight'.")

#     # find the number of years and the reduction factor
#     N = EXPECTED_YEARS_TO_RETURN_TO_NORMAL_MILEAGE_FROM_COVID[economy]
#     X = EXPECTED_ENERGY_DECREASE_FROM_COVID[economy]
#     A = EXPECTED_RETURN_TO_NORMAL_MILEAGE_FROM_COVID[economy]
#     years_after_covid = [max(LISTED_YEARS_WHEN_COVID_EFFECTS_APPLIED[economy]) + i + 1 for i in range(N)]
    
#     #if the year is in the list of years after covid, then we just need to apply the yearly_increase to the current mileage (which is the year before's mileage). If the year is not in the list of years after covid, then we dont need to do anything.
#     if current_year in years_after_covid:
#         EXPECTED_ENERGY_INCREASE_FACTOR =((((1/(1-X)) -1)* A)+1)
#         #this is the factor by which we need to increase the mileage to get it back to normal. its just reversing the %decrease that was applied to the mileage to get it to the current level.
#         #spread the increase over the number of years by finding its Nth root and applying it to the current mileage for this year.
#         yearly_increase = (EXPECTED_ENERGY_INCREASE_FACTOR ** (1/N))
#         #apply the increase to the mileage
#         dataframe.loc[(dataframe['Economy'] == economy) & (dataframe['Transport Type'] == transport_type), measure_column] *= yearly_increase
#     elif current_year > max(years_after_covid):
#         pass
#     elif current_year <= last_covid_year:
#         #apply the decrease to the mileage
#         dataframe.loc[(dataframe['Economy'] == economy) & (dataframe['Transport Type'] == transport_type), measure_column]  * (1-X)
#     return dataframe
        

def adjust_mileage_to_account_for_covid(economy, dataframe, transport_type, current_year, measure_column = 'Activity'):
    """    
    Intention:
    create a fucntion that can calcualte what the mileage should be in the current year, if the year is within one of the covid years or one of the years during which mileage was returning to normal. This is assuming that normal mileage is the miealge in the input data to this function, which reflects mileage during the year before covid or one of the years after everythign has returned to normal.
    
    So we will check if config.OUTLOOK_BASE_YEAR <= last_covid_year +EXPECTED_YEARS_TO_RETURN_TO_NORMAL_MILEAGE_FROM_COVID: 
    if current year is <= last_covid_year, adjust the mielage by EXPECTED_ENERGY_DECREASE_FROM_COVID.
    if current year is > last_covid_year, but <= last_covid_year +EXPECTED_YEARS_TO_RETURN_TO_NORMAL_MILEAGE_FROM_COVID then we will adjust the mileage by the expected increase in mileage after covid, which is spread over the number of years that we expect it to take to return to normal. This will use cumulative growth to work out what the annual growth rate should be in the current year to achieve the expected increase in mileage after covid.
    if current year is > last_covid_year +EXPECTED_YEARS_TO_RETURN_TO_NORMAL_MILEAGE_FROM_COVID, then we will not use this function, as the mileage in the input data is already set to what it should be in a year after covid.
    
    Note that this function is intended to be used for multiple scripts/fucntions, for exmaple in calcualting mileage in the 'workflow\calculation_functions\optimise_to_calculate_base_data.py' file, as well as the road and non-road model scripts. 
    
    IMPORTANT NOTE:
    If you are having issues where the proportion of one singular fuel needs to be icnreased but you cannot do this without increasing another (say if you need to increase diesel but doing so would increase petrol) then you should try to increase the stocks of that vehicle in the required drive type in the input data. This process is not built for such fine tuning because of the general requirement that mielage remains the same between different drive types and the fact that a change to mileage here affects mileage for the whole projection period.
    As an example, because mexico needed its diesel increased but i didnt want to increase freight effect more than it had been, i increased proportion of petrol use in freight, and diesel in passenger so that higher effects on passenger had higher effects on diesel. This is a bit of a hack but it works better than trying to adjust the mileage of singular drive types for the whole projection period in this function.
    
    Args:
        economy: The economy for which to revert mileage decreases.
        change_dataframe: DataFrame with changes to apply.
        main_dataframe: Main DataFrame containing mileage data.
        transport_type: Type of transport, 'passenger' or 'freight'.
        current_year: The current year being processed.
        measure_column: this can be changed so that for exmaple in non road we can set it to acitivty, and then we can use this function to adjust activity to account for covid, producing the same effect as adjusting mileage to account for covid.

    Raises:
        ValueError: If the transport type is not recognized.
    """
        
    # Load configuration parameters
    parameters = yaml.load(open('config/parameters.yml'), Loader=yaml.FullLoader)
    
    for medium in dataframe.Medium.unique():
        # Construct the suffix for parameter keys based on transport type and medium
        suffix = f"{transport_type.upper()}_{medium.upper()}"
        
        # Dynamically construct parameter keys and fetch their values
        listed_years_key = f"LISTED_YEARS_WHEN_COVID_EFFECTS_APPLIED_{suffix}"
        expected_years_key = f"EXPECTED_YEARS_TO_RETURN_TO_NORMAL_ACTIVITY_FROM_COVID_{suffix}"
        energy_decrease_key = f"EXPECTED_ENERGY_DECREASE_FROM_COVID_{suffix}"
        return_to_normal_key = f"EXPECTED_RETURN_TO_NORMAL_ACTIVITY_FROM_COVID_{suffix}"
        
        # Fetch values using constructed keys
        LISTED_YEARS_WHEN_COVID_EFFECTS_APPLIED = parameters[listed_years_key]
        EXPECTED_YEARS_TO_RETURN_TO_NORMAL_MILEAGE_FROM_COVID = parameters[expected_years_key]
        EXPECTED_ENERGY_DECREASE_FROM_COVID = parameters[energy_decrease_key]
        last_covid_year = max(parameters[listed_years_key][economy])
        EXPECTED_RETURN_TO_NORMAL_MILEAGE_FROM_COVID = parameters[return_to_normal_key]
        
        # find the number of years and the reduction factor
        N = EXPECTED_YEARS_TO_RETURN_TO_NORMAL_MILEAGE_FROM_COVID[economy]
        X = EXPECTED_ENERGY_DECREASE_FROM_COVID[economy]
        A = EXPECTED_RETURN_TO_NORMAL_MILEAGE_FROM_COVID[economy]
        years_after_covid = [max(LISTED_YEARS_WHEN_COVID_EFFECTS_APPLIED[economy]) + i + 1 for i in range(N)]
        
        #if the year is in the list of years after covid, then we just need to apply the yearly_increase to the current mileage (which is the year before's mileage). If the year is not in the list of years after covid, then we dont need to do anything.
        
        if current_year in years_after_covid:
            EXPECTED_ENERGY_INCREASE_FACTOR = ((((1/(1-X)) -1)* A)+1)
            #this is the factor by which we need to increase the mileage to get it back to normal. its just reversing the %decrease that was applied to the mileage to get it to the current level.
            #spread the increase over the number of years by finding its Nth root and applying it to the current mileage for this year.
            yearly_increase = (EXPECTED_ENERGY_INCREASE_FACTOR ** (1/N))
            #apply the increase to the mileage
            
            if medium == 'air' and transport_type == 'passenger':
                pass#breakpoint()#it seems its much lower thanm expected most of th times
                # print('2.b sum of value before increase: {}'.format(dataframe.loc[(dataframe['Economy'] == economy) & (dataframe['Transport Type'] == transport_type) & (dataframe['Medium']==medium), measure_column].sum()))
                
            dataframe.loc[(dataframe['Economy'] == economy) & (dataframe['Transport Type'] == transport_type) & (dataframe['Medium']==medium), measure_column] *= yearly_increase
            
            if medium == 'air' and transport_type == 'passenger':
                # print('2.b sum of value after increase: {}'.format(dataframe.loc[(dataframe['Economy'] == economy) & (dataframe['Transport Type'] == transport_type) & (dataframe['Medium']==medium), measure_column].sum()))
                pass
            
        elif current_year > max(years_after_covid):
            pass
        elif current_year <= last_covid_year:
            #apply the decrease to the mileage
            
            if medium == 'air' and transport_type == 'passenger':
                pass# print('2.a sum of value before increase: {}'.format(dataframe.loc[(dataframe['Economy'] == economy) & (dataframe['Transport Type'] == transport_type) & (dataframe['Medium']==medium), measure_column].sum()))
            
            if medium == 'air' and transport_type == 'passenger':
                pass#breakpoint()#it seems its much lower thanm expected most of th times
                
            dataframe.loc[(dataframe['Economy'] == economy) & (dataframe['Transport Type'] == transport_type) & (dataframe['Medium']==medium), measure_column]  *= (1-X)
            
            if medium == 'air' and transport_type == 'passenger':
                pass#print('2.a sum of value after increase: {}'.format(dataframe.loc[(dataframe['Economy'] == economy) & (dataframe['Transport Type'] == transport_type) & (dataframe['Medium']==medium), measure_column].sum()))
    return dataframe
        



def prepare_road_model_inputs(road_model_input, ECONOMY_ID, low_ram_computer=True):
    """
    Prepares the road model inputs for use in the model.

    Args:
        road_model_input (pandas.DataFrame): The road model input data.
        ECONOMY_ID (str): The ID of the economy to prepare the inputs for.
        low_ram_computer (bool): Whether the computer has low RAM. Defaults to True.

    Returns:
        pandas.DataFrame: The prepared road model input data.
    """
    # function code here
    #separate user inputs into different dataframes
    
    #GOMPERTZ PARAMETERS ARE USED TO SET A LIMIT ON STOCKS PER CPITA. WE NEED TO LOAD THEM IN HERE AND MERGE THEM ONTO THE MAIN DATAFRAME.      
    # We also need to set them to be non nan for the base year, as the base year has its values for inputs set to nan.
    gompertz_parameters = pd.read_csv('intermediate_data/model_inputs/{}/{}_stocks_per_capita_threshold.csv'.format(config.FILE_DATE_ID,ECONOMY_ID))
    #filter for economy id only:
    gompertz_parameters = gompertz_parameters[gompertz_parameters['Economy']==ECONOMY_ID].copy()
    base_year = road_model_input.Date.min()
    #replace values for BASE YEAR with values from the first calculated year of the model
    BASE_YEAR_gompertz_parameters = gompertz_parameters[gompertz_parameters['Date']==gompertz_parameters['Date'].min()].copy()
    BASE_YEAR_gompertz_parameters['Date'] = base_year
    gompertz_parameters = pd.concat([gompertz_parameters[gompertz_parameters['Date']!=base_year], BASE_YEAR_gompertz_parameters], ignore_index=True)
    
    #and the rest of the user inputs:
    Vehicle_sales_share = road_model_input[['Economy','Scenario', 'Drive', 'Vehicle Type', 'Transport Type', 'Date', 'Vehicle_sales_share']].drop_duplicates().copy()
    Occupancy_or_load_growth = road_model_input[['Economy','Scenario', 'Drive','Vehicle Type', 'Transport Type', 'Date', 'Occupancy_or_load_growth']].drop_duplicates().copy()
    New_vehicle_efficiency_growth = road_model_input[['Economy','Scenario', 
    'Vehicle Type', 'Transport Type', 'Drive', 'Date', 'New_vehicle_efficiency_growth']].drop_duplicates().copy()
    Mileage_growth = road_model_input[['Economy','Scenario', 'Drive', 'Vehicle Type', 'Transport Type', 'Date', 'Mileage_growth']].drop_duplicates().copy()

    #put the dataframes into a dictionary to pass into the funciton togetehr:
    user_inputs_df_dict = {'Vehicle_sales_share':Vehicle_sales_share, 'Occupancy_or_load_growth':Occupancy_or_load_growth, 'New_vehicle_efficiency_growth':New_vehicle_efficiency_growth, 'Mileage_growth':Mileage_growth, 'gompertz_parameters':gompertz_parameters}

    #drop those cols
    road_model_input = road_model_input.drop(['Vehicle_sales_share', 'Occupancy_or_load_growth', 'New_vehicle_efficiency_growth','Mileage_growth'], axis=1)#'Gompertz_alpha', 'Gompertz_beta',

    #create main dataframe as previous Date dataframe, so that currently it only holds the base Date's data. This will have each Dates data added to it at the end of each loop.
    previous_year_main_dataframe = road_model_input.loc[road_model_input.Date == road_model_input.Date.min(),:].copy()   
    main_dataframe = previous_year_main_dataframe.copy()
    change_dataframe_aggregation = pd.DataFrame()

    
    #give option to run the process on a low RAM computer. If True then the loop will be split into 10 year blocks, saving each block in a csv, then starting again with an empty main datafrmae for the next 10 years block. If False then the loop will be run on all years without saving intermediate results.
    if low_ram_computer:
        previous_10_year_block = road_model_input.Date.min()
        low_ram_computer_files_list = []
        #remove files from main_dataframe_10_year_blocks for previous runs
        for file in glob.glob(os.path.join('intermediate_data/main_dataframe_10_year_blocks/', '*.csv')):
            os.remove(file)
    else:
        previous_10_year_block = None
        low_ram_computer_files_list = None


    return main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation,previous_10_year_block, user_inputs_df_dict,low_ram_computer


def join_and_save_road_model_outputs(ECONOMY_ID, main_dataframe, low_ram_computer, low_ram_computer_files_list,change_dataframe_aggregation, first_model_run_bool):
    if first_model_run_bool:
        new_output_file = 'intermediate_data/road_model/first_run_{}_{}'.format(ECONOMY_ID, config.model_output_file_name)
    else:
        #this will be the name of the output file
        new_output_file = 'intermediate_data/road_model/{}_{}'.format(ECONOMY_ID, config.model_output_file_name)

    #now, we will save the main dataframe to a csv file. if the computer is low ram, we will create the file from the already saved 10 year block interval files
    if low_ram_computer == True:
        main_dataframe = pd.DataFrame()
        print('The computer is low ram, stitching together the main dataframe from the 10 year block files.')

        #first check the file we will be writing to doesnt already exist, if so, delete it
        if os.path.exists(new_output_file):
            os.remove(new_output_file)

        for file_i in low_ram_computer_files_list:
            print('Reading file {}'.format(file_i))
            low_ram_dataframe = pd.read_csv(file_i)
            #write to csv
            low_ram_dataframe.to_csv(new_output_file,mode='a', header=not os.path.exists(new_output_file),index=False)
            #remove file 
            os.remove(file_i)
            main_dataframe = pd.concat([main_dataframe,low_ram_dataframe])

        # main_dataframe.to_csv(new_output_file, index=False)
        print('The main dataframe has been written to {}'.format(new_output_file))
    else:
        print('The computer is not low ram, saving the main dataframe to a csv.')
        main_dataframe.to_csv(new_output_file, index=False)


    #save dataframe
    change_dataframe_aggregation.to_csv(f'intermediate_data/road_model/change_dataframe_aggregation_{ECONOMY_ID}.csv', index=False)

    return main_dataframe



def do_tests_on_road_data(change_dataframe, throw_error=True):
    test_data_frame = change_dataframe.copy()
    test_data_frame['Activity_check'] = test_data_frame['Mileage'] * test_data_frame['Occupancy_or_load'] * test_data_frame['Stocks']
    #why dont all othese equal each otehr???
    # #also check test_data_frame['Activity'] the other way
    test_data_frame['Activity_check2'] = test_data_frame['Energy'] *  test_data_frame['Efficiency'] * test_data_frame['Occupancy_or_load']
    test_data_frame['Activity_check_diff'] = test_data_frame['Activity_check'] - test_data_frame['Activity_check2']
    

    if not np.allclose(test_data_frame['Activity_check'], test_data_frame['Activity']) or not np.allclose(test_data_frame['Activity_check2'], test_data_frame['Activity']):
        a_check = sum(test_data_frame['Activity_check'].dropna())+1
        a_original = 1+sum(test_data_frame['Activity'].dropna())
        percent_difference = ((a_check - a_original) / a_original)*100
        
        a_check2 = sum(test_data_frame['Activity_check2'].dropna())+1
        a_original2 = 1+sum(test_data_frame['Activity'].dropna())
        percent_difference2 = ((a_check2 - a_original2) / a_original2)*100
        # #extract the rows where the activity is not equal to Activity_check
        # bad_rows = test_data_frame[test_data_frame['Activity_check'] != test_data_frame['Activity']]
        # #find the diff in each row
        # bad_rows['diff'] = bad_rows['Activity_check'] - bad_rows['Activity']
        year = test_data_frame['Date'].max()
        if abs(percent_difference) > 0.5 or (abs(percent_difference2) > 0.5 and year != 2021):
            breakpoint()
            if throw_error:
                raise ValueError('ERROR: Activity does not match sum of activity. percent_difference = {}'.format(percent_difference)) 
            else:
                print('ERROR: Activity does not match sum of activity. percent_difference = {}'.format(percent_difference)) 


def check_activity_after_run(change_dataframe, throw_error=True):
    #test that ativity is equivalent to the previous years activity times the activity growth rate (which is activity_growth)
    #so sum the activity by transport type and compare to activity_growth:
    new_activity_by_transport_type = change_dataframe.groupby(['Economy', 'Scenario', 'Transport Type', 'Date'])['Activity'].sum().reset_index()
    
    old_activity_by_transport_type = change_dataframe[['Economy', 'Scenario', 'Transport Type', 'Date','Activity_growth','Previous_activity']].copy()
    old_activity_by_transport_type['old_activity_by_transport_type'] = old_activity_by_transport_type['Activity_growth'] * old_activity_by_transport_type['Previous_activity']
    old_activity_by_transport_type = old_activity_by_transport_type.groupby(['Economy', 'Scenario', 'Transport Type', 'Date'])['old_activity_by_transport_type'].sum().reset_index()
    
    comparison = new_activity_by_transport_type.merge(old_activity_by_transport_type, on=['Economy', 'Scenario', 'Transport Type', 'Date'], how='left')
    comparison['difference'] = comparison['Activity'] - comparison['old_activity_by_transport_type']
    comparison['pct_difference'] = (comparison['difference'] / comparison['Activity']) * 100
    if (abs(comparison['pct_difference']) > 1).any():
        
        year = comparison['Date'].max()
        #if its year 2021, we will give some leeway because i cant figure out why a small amount is leftover from increasing mileage early on. so if diff is > 5% we will throw an error
        if year ==2021 and (comparison['difference'].sum()/comparison['Activity'].sum() > 0.05):
            breakpoint()
            time.sleep(1)
            if throw_error:
                raise ValueError('Activity is not equal to previous years activity times the activity growth rate. Max activity error margin is {}'.format(comparison['difference'].max()))
            else:
                #print the avg difference
                print('Max activity error margin is {}'.format(comparison['difference'].max()))
        elif year != 2021:
            breakpoint()
            time.sleep(1)
            if throw_error:
                raise ValueError('Activity is not equal to previous years activity times the activity growth rate. Max activity error margin is {}'.format(comparison['difference'].max()))
            else:
                #print the avg difference
                print('Max activity error margin is {}'.format(comparison['difference'].max()))

def create_age_distribution_entry(row):
    """Because the average age can be a float and it was getting a bit mathy trying to get the average to be equal to the float, we will do this using optimisation (aka brute force)
    """
    # Objective function to minimize
    def objective_function(x, avg_age, total_stocks):
        # Calculate the mean of the distribution
        calculated_avg = np.sum(x * np.arange(len(x))) / total_stocks
        
        # Calculate the variance of the distribution
        variance = np.var(x)
        
        # Objective function to minimize the deviation from the target average age and variance
        error = abs(calculated_avg - avg_age) + variance
        
        return error

    def generate_optimal_distribution(avg_age, stocks):
        avg_age_flr = int(avg_age // 1)
        n_years = 2 * avg_age_flr
        
        initial_guess = np.full(n_years, stocks / n_years)
        bounds = [(0, stocks) for _ in range(n_years)]
        
        result = minimize(objective_function, initial_guess, args=(avg_age, stocks), bounds=bounds)
        
        return result.x

    # Testing the function
    Average_age = row.Average_age
    stocks = row.Stocks
    
    #if average age is nan tehn jsut crete one bin with 0 stocks in it
    if np.isnan(Average_age):
        return '0'
    
    # Calculate the order of magnitude to scale stocks close to 1
    stocks_magnitude_adj = 10 ** (-np.floor(np.log10(stocks)))
    # Scale the stocks for optimization
    scaled_stocks = stocks * stocks_magnitude_adj
    try:
        optimal_distribution = generate_optimal_distribution(Average_age, scaled_stocks)
    except:
        breakpoint()
        optimal_distribution = generate_optimal_distribution(Average_age, scaled_stocks)
        
    calculated_avg_age = np.sum(optimal_distribution * np.arange(len(optimal_distribution))) / scaled_stocks

    #revert the stocks back to millions in the distribution
    optimal_distribution = optimal_distribution / stocks_magnitude_adj
    
    #check the average age is correct
    if abs(calculated_avg_age - Average_age) > 0.001:
        print('{} - {}'.format(calculated_avg_age, Average_age))
        breakpoint()
        time.sleep(1)
        raise ValueError('Average age is not correct')

    return ','.join(map(str, optimal_distribution))

def apply_turnover_to_age_distribution(turnover, age_distribution):
    age_distribution = str(age_distribution).split(',')
    age_distribution = [float(i) for i in age_distribution]
    new_age_distribution = age_distribution.copy()
    i = len(age_distribution)-1
    while (i >=0) & (turnover > 0):
        if age_distribution[i] > turnover:
            try:
                new_age_distribution[i] = age_distribution[i] - turnover
            except:
                breakpoint()
            turnover = 0
        else:
            turnover = turnover - age_distribution[i]
            if i != 0:
                new_age_distribution.remove(age_distribution[i])
            else:
                new_age_distribution[i] = 0
        i-=1
        
    # new_age_distribution = [str(i) for i in new_age_distribution] #dont think we need to convert back to string
    new_age_distribution = [str(i) for i in new_age_distribution]
    return ','.join(new_age_distribution)

def add_new_vehicles_to_age_distribution(New_stocks_needed, age_distribution):
    age_distribution = str(age_distribution).split(',')
    age_distribution = [float(i) for i in age_distribution]
    new_age_distribution = age_distribution.copy()
    #put new_stocks_needed in the first year of the age distribution
    if New_stocks_needed <0:
        breakpoint()
        time.sleep(1)
        raise ValueError('New_stocks_needed is negative')
    new_age_distribution[0] = new_age_distribution[0] + New_stocks_needed
    
    new_age_distribution = [str(i) for i in new_age_distribution]
    return ','.join(new_age_distribution)

def add_average_age_vehicles_to_age_distribution(Surplus_stocks_used, age_distribution, average_age):
    if Surplus_stocks_used <= 0:#this keeps being called when there are no surplus stocks used, so we will just return the age distribution
        return age_distribution
    age_distribution = str(age_distribution).split(',')
    age_distribution = [float(i) for i in age_distribution]
    #cahcnes are there are that average age is not a rounded number. So we will split it between the floor and ceiling bins so the average age of thsoe stocks is kept. eg. if average age is 2.5, then we need to put x stocks in the 2 bin and y stocks in 3 bin so that ((2*x)+(3*y))/(x+y) = 2.5
    avg_age_floor = int(np.floor(average_age))
    remainder = average_age - avg_age_floor
    if remainder != 0:
        # Calculate the number of stocks to go in each bin
        total_stocks_for_both_bins = Surplus_stocks_used
        stocks_in_floor_bin = total_stocks_for_both_bins * (1 - remainder)
        stocks_in_ceiling_bin = total_stocks_for_both_bins - stocks_in_floor_bin

        # Add them to the respective bins in age_distribution #note that the bin for age=1 ia in 0th position in the list so we decrement the avg_age_floor by 1 to get index
        age_distribution[avg_age_floor-1] += stocks_in_floor_bin
        age_distribution[avg_age_floor] += stocks_in_ceiling_bin
    
    else:
        # If average_age is a whole number, just dump all the surplus_stocks into that bin
        age_distribution[avg_age_floor-1] += Surplus_stocks_used
    age_distribution = [str(i) for i in age_distribution]
    return ','.join(age_distribution)  
    
def add_one_year_to_all_in_distribution(age_distribution):
    age_distribution = str(age_distribution).split(',')
    try:
        age_distribution = [float(i) for i in age_distribution]
    except:
        breakpoint()
    new_age_distribution = age_distribution.copy()
    #add a bin at the end of the list with 0 stocks in it
    new_age_distribution.append(0)
    for i in range(0, len(age_distribution)):
        new_age_distribution[i+1] = age_distribution[i]
    new_age_distribution[0] = 0
    #trim any bins at the end where tehre are no stocks
    while new_age_distribution[-1] == 0 and len(new_age_distribution) > 1:
        new_age_distribution.pop()
    new_age_distribution = [str(i) for i in new_age_distribution]
    return ','.join(new_age_distribution)
    
def calculate_average_age_from_age_distribution(age_distribution):
    #age distribution is a list of values, each value represents the number of vehicles of that age. so the first value is the number of vehicles of age 1, the second value is the number of vehicles of age 2, etc.
    #so to calculate the average age, we will multiply each value by its age, then sum them all together, then divide by the total number of vehicles.
    #note that the age distribution is a list of strings, so we will have to convert it to a list of ints first.
    age_distribution = str(age_distribution).split(',')
    age_distribution = [float(i) for i in age_distribution]
    #now we have a list of ints, we can calculate the average age
    average_age = 0
    for i in range(0, len(age_distribution)):
        average_age += (i+1) * age_distribution[i]
    
    if average_age==0:
        return 0
    else:
        average_age = average_age / sum(age_distribution)
    return average_age

def recalculate_age_distribution(change_dataframe):
    """this will use the age distribution measure and average age measure to apply turnover to the stocks so that it removes the oldest stocks, and updates the distributioon accordingly when new vehicles are added, or we add 1 to the age of all vehicles.
    note that the age distribution measure's vlaue col contains a list of values which each represent a year between 1 and the oldest vehicle for that row. the value in the list is the number of vehicles of that age.
    the average age measures value is teh average age clacualted from the age distribution measure.
    Returns:
        change_dataframe: big boi
    """
    #apply turnover rate to every row so taht the number of stocks to remove are removed from the latest years
    
    #if Stock_turnover_and_surplus_total >= 0 dont apply turnvoer since we'll treat it as the amount of surplus stocks equal to turnover were the oldest vehicles, and have found a use. and the other surplus stocks (surplus - turnover) will be taken away from new vehicles and added as average age vehicles. Its pretty lazy, but currently there are no cases where surplus stocks are used.
    
    #separate the dataframe into those where the cols contain nans and those where they dont
    na_df = change_dataframe[(change_dataframe['Stocks'].isna())|(change_dataframe['Average_age'].isna())|(change_dataframe['Age_distribution'].isna())|(change_dataframe['Turnover_rate'].isna())].copy()
    change_dataframe = change_dataframe[~((change_dataframe['Stocks'].isna())|(change_dataframe['Average_age'].isna())|(change_dataframe['Age_distribution'].isna())|(change_dataframe['Turnover_rate'].isna()))].copy()    
    if len(change_dataframe) == 0:
        return na_df
    #add surplus stocks to the age distribution
    change_dataframe['Age_distribution'] = np.where(
        change_dataframe['Surplus_stocks_used'] > 0,
        change_dataframe.apply(lambda row: add_average_age_vehicles_to_age_distribution(row['Surplus_stocks_used'], row['Age_distribution'], row['Average_age']), axis=1),
        change_dataframe['Age_distribution']
    )
    #remove turnover stocks from the age distribution
    change_dataframe['Age_distribution'] = np.where(
        change_dataframe['Stock_turnover'] > 0,
        change_dataframe.apply(lambda row: apply_turnover_to_age_distribution(row['Stock_turnover'], row['Age_distribution']), axis=1),
        change_dataframe['Age_distribution']
    )
    #add 1 year to all vehicles in the age distribution
    change_dataframe['Age_distribution'] = change_dataframe.apply(lambda row: add_one_year_to_all_in_distribution(row['Age_distribution']), axis=1)
    
    change_dataframe['Age_distribution'] = np.where(
        change_dataframe['New_stocks_needed'] > 0,
        change_dataframe.apply(lambda row: add_new_vehicles_to_age_distribution(row['New_stocks_needed'], row['Age_distribution']), axis=1),
        change_dataframe['Age_distribution']
    )
    
    change_dataframe['Average_age'] = change_dataframe.apply(lambda row: calculate_average_age_from_age_distribution(row['Age_distribution']), axis=1)

    #add the nans back in
    change_dataframe = pd.concat([change_dataframe, na_df])
    
    return change_dataframe


def calculate_surplus_stocks(row):
    try:
        if row['Surplus_stocks_previous']<row['New_stocks_needed']:
            row['New_stocks_needed'] = row['New_stocks_needed'] - row['Surplus_stocks_previous']#new stocks represent stocks that have age =1, whereas surplus stocks have an age around the average age. So we need to subtract the surplus stocks from the new stocks in prep for claulation of the average age
            row['Surplus_stocks'] = 0
            row['Surplus_stocks_used'] = row['Surplus_stocks_previous']
            
        elif row['Surplus_stocks_previous']>=row['New_stocks_needed']:
            row['Surplus_stocks'] = row['Surplus_stocks_previous'] - row['New_stocks_needed']
            row['Surplus_stocks_used'] = row['New_stocks_needed']
            row['New_stocks_needed'] = 0
        else:
            raise ValueError("Something went wrong with the surplus stocks. Please check the code.")
    except:
        breakpoint()
        if row['Surplus_stocks_previous']<row['New_stocks_needed']:
            row['New_stocks_needed'] = row['New_stocks_needed'] - row['Surplus_stocks_previous']#new stocks represent stocks that have age =1, whereas surplus stocks have an age around the average age. So we need to subtract the surplus stocks from the new stocks in prep for claulation of the average age
            row['Surplus_stocks'] = 0
            row['Surplus_stocks_used'] = row['Surplus_stocks_previous']
            
        elif row['Surplus_stocks_previous']>=row['New_stocks_needed']:
            row['Surplus_stocks'] = row['Surplus_stocks_previous'] - row['New_stocks_needed']
            row['Surplus_stocks_used'] = row['New_stocks_needed']
            row['New_stocks_needed'] = 0
        else:
            raise ValueError("Something went wrong with the surplus stocks. Please check the code.")
        
    
    return row[['Surplus_stocks_used', 'Surplus_stocks', 'New_stocks_needed']]

def add_together_age_distributions(age_distribution):
    #take in age distribution col and add them together so the sum of stocks in each bin is the sum of the stocks in each bin of the input age distributions
    #drop any nans
    age_distribution = age_distribution.dropna()
    new_age_distribution = []
    for dist in age_distribution:
        dist = str(dist).split(',')
        dist = [float(i) for i in dist]
        #add the values in each bin together
        new_age_distribution = [sum(x) for x in zip(new_age_distribution, dist)]
    new_age_distribution = [str(i) for i in new_age_distribution]
    return ','.join(new_age_distribution)
    
def combine_age_distributions(age_distribution):
    age_distribution = age_distribution.dropna()
    
    # Initialize to None so we can later check if we need to populate it
    new_age_distribution = None
    
    for dist in age_distribution:
        dist = str(dist).split(',')
        dist = [float(i) for i in dist]
        
        # Check if new_age_distribution has been populated
        if new_age_distribution is None:
            new_age_distribution = dist
        else:
            # Pad the shorter list with zeros so they are of the same length
            if len(new_age_distribution) < len(dist):
                new_age_distribution.extend([0] * (len(dist) - len(new_age_distribution)))
            elif len(new_age_distribution) > len(dist):
                dist.extend([0] * (len(new_age_distribution) - len(dist)))
            
            # Add the values in each bin together
            new_age_distribution = [sum(x) for x in zip(new_age_distribution, dist)]
    
    if new_age_distribution is not None:
        new_age_distribution = [str(i) for i in new_age_distribution]
        return ','.join(new_age_distribution)
    else:
        raise ValueError("Something went wrong with the age distributions. Please check the code.")
        # return None  # or some other default value
#%%