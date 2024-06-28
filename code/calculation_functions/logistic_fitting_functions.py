
#######################################################################
#%%
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
    sys.path.append(f"{root_dir}/code/plotting_functions")
    import plot_logistic_fitting_data
else:
    # Assuming the script is being run from main.py located at the root of the project, we want to avoid using sys.path.append and instead use relative imports 
    try:
        from ..utility_functions import *
        from ..config import *
    except ImportError:
        import utility_functions
        import config
    from ..plotting_functions import plot_logistic_fitting_data
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
from scipy.optimize import curve_fit
#######################################################################
#######################################################################
#######################################################################
#######################################################################
#LOGISTIC FITTING FUNCTIONS
#######################################################################
#######################################################################
#######################################################################
#######################################################################


def logistic_fitting_function_handler(ECONOMY_ID, model_data,show_plots=False,matplotlib_bool=False, plotly_bool=False, FIT_LOGISTIC_CURVE_TO_DATA=False, PROPORTION_BELOW_GAMMA= 0.4, EXTRA_YEARS_TO_REACH_GAMMA=10, APPLY_SMOOTHING_TO_GROWTH_RATE=True, INTERPOLATE_ALL_DATES=False):
    """Take in output of stocks,occupancy, travel_km, activity and mileage from running road model on a gdp per cpita based growth rate. Then fit a logistic curve to the stocks data with the gamma value from each economy provided. 
    Then with this curve, extract the expected activity per year based on the expected stocks per year and the expected mileage per year. Then recalculate the growth rate over time based on this. We will then use this to rerun the road model with the new growth rate.
    This was origianlly done for each economy and vehicle type in passenger vehicles, now for each economy and transport type. 
    
    This will be done for each scenario too because movement between Transport Types might change the growth rate?
    
    Args:
        ECONOMY_ID (str): The economy to run the logistic fitting for
        model_data (pd.DataFrame): The model data from the road model for that economy
        show_plots (bool, optional): Whether to show plots. Defaults to False.
        matplotlib_bool (bool, optional): Whether to show matplotlib plots. Defaults to False.
        plotly_bool (bool, optional): Whether to show plotly plots. Defaults to False.
        FIT_LOGISTIC_CURVE_TO_DATA (bool, optional): Whether to fit the logistic curve to the data. Defaults to False.
        PROPORTION_BELOW_GAMMA (float, optional): The proportion of the stocks data that can be below the gamma value. Defaults to 0.05.
        EXTRA_YEARS_TO_REACH_GAMMA (int, optional): The number of years to reach the gamma value that are added onto the previous point where it was passed. Defaults to 5.
        APPLY_SMOOTHING_TO_GROWTH_RATE (bool, optional): Whether to apply smoothing to the growth rate. Defaults to False.
        INTERPOLATE_ALL_DATES: Whether to interpolate all dates below gamma. Defaults to False.
    
    """
    model_data_to_edit = model_data.copy()
        
    model_data_to_edit = model_data_to_edit.loc[(model_data_to_edit['Transport Type'] == 'passenger')] 
    
    new_model_data = prepare_data_for_logistic_fitting(model_data_to_edit,ECONOMY_ID)
        
    #EXTRACT PARAMETERS FOR LOGISTIC FUNCTION:
    parameters_estimates, new_stocks_per_capita_estimates, date_where_gamma_is_reached = find_parameters_for_logistic_function(new_model_data, show_plots, matplotlib_bool, plotly_bool, FIT_LOGISTIC_CURVE_TO_DATA, PROPORTION_BELOW_GAMMA, EXTRA_YEARS_TO_REACH_GAMMA, INTERPOLATE_ALL_DATES)
    #some parameters will be np.nan because we dont need to fit the curve for all economies. We will drop these and not recalculate the growth rate for these economies
    parameters_estimates = parameters_estimates.dropna(subset=['Gompertz_gamma'])
    #grab only cols we need
    new_model_data = new_model_data[['Date', 'Economy', 'Scenario','Transport Type', 'Stocks', 'Occupancy_or_load', 'Mileage', 'Population', 'Gdp_per_capita','Activity', 'Travel_km','Gompertz_gamma']]
    #join the params on:
    new_model_data.drop(columns=['Gompertz_gamma'], inplace=True)
    new_model_data = new_model_data.merge(parameters_estimates, on=['Economy', 'Scenario','Transport Type'], how='inner')
    #sum stocks,'Activity', Travel_km, , with any NAs set to 0
    new_model_data['Stocks'] = new_model_data['Stocks'].fillna(0)
    new_model_data['Activity'] = new_model_data['Activity'].fillna(0)
    new_model_data['Travel_km'] = new_model_data['Travel_km'].fillna(0)
    
    summed_values = new_model_data.groupby(['Date','Economy', 'Scenario','Transport Type'])[['Stocks','Activity', 'Travel_km']].sum().reset_index().copy()
    #join stocks with other data
    new_model_data.drop(columns=['Stocks','Activity', 'Travel_km'], inplace=True)
    new_model_data.drop_duplicates(inplace=True)
    new_model_data = new_model_data.merge(summed_values, on=['Date','Economy', 'Scenario','Transport Type'], how='left')
    model_data_logistic_predictions = create_new_dataframe_with_logistic_predictions(new_model_data, new_stocks_per_capita_estimates, FIT_LOGISTIC_CURVE_TO_DATA)
    # model_data_logistic_predictions[['Scenario', 'Economy', 'Date', 'Transport Type', 'Stocks_per_thousand_capita']].pivot(index=['Economy', 'Date', 'Transport Type'], columns='Scenario', values='Stocks_per_thousand_capita').reset_index()
    #find growth rate of activity as the percentage change in activity from the previous year plus 1. make sur eto group by economy and scenario BUT NOT BY VEHICLE TYPE (PLEASE NOTE THAT THIS MAY CHANGE IN THE FUTURE)
    activity_growth_estimates = estimate_new_growth_rate(model_data_logistic_predictions, date_where_gamma_is_reached, APPLY_SMOOTHING_TO_GROWTH_RATE)
    #if matplotlib_bool or plotly_bool:
    if matplotlib_bool or plotly_bool:
        plot_logistic_fitting_data.plot_logistic_function_all_economies(model_data_logistic_predictions, activity_growth_estimates, parameters_estimates, new_model_data, show_plots, matplotlib_bool, plotly_bool, FIT_LOGISTIC_CURVE_TO_DATA)
        plot_logistic_fitting_data.plot_logistic_function_by_economy(model_data_logistic_predictions, activity_growth_estimates, parameters_estimates, new_model_data, show_plots, matplotlib_bool, plotly_bool, FIT_LOGISTIC_CURVE_TO_DATA)

    #drop Activity from activity_growth_estimates
    activity_growth_estimates.drop(columns=['Activity'], inplace=True)
    
    #fill missing activity growth estimates (because there was no need for an adjustment) with their original growth rate:
    old_activity_growth = model_data_to_edit.copy()
    old_activity_growth = old_activity_growth[['Date', 'Economy', 'Scenario', 'Activity_growth', 'Transport Type']].drop_duplicates()
    if old_activity_growth.groupby(['Date', 'Economy', 'Scenario', 'Transport Type']).size().max()!=1:
        raise ValueError('We have more than one row for each date, economy, transport type and scenario in the old_activity_growth dataframe')
    #merge old activity growth with new activity growth
    activity_growth_estimates = old_activity_growth.merge(activity_growth_estimates, on=['Date', 'Economy', 'Scenario', 'Transport Type'], how='left', suffixes=('_old', ''))
    #fill na with old activity growth
    activity_growth_estimates['Activity_growth'] = activity_growth_estimates['Activity_growth'].fillna(activity_growth_estimates['Activity_growth_old'])
    #drop old activity growth
    activity_growth_estimates.drop(columns=['Activity_growth_old'], inplace=True)

    #save parameters_estimates. at the very elast we will plot these later
    parameters_estimates.to_csv(root_dir + '/' + 'intermediate_data/road_model/{}_parameters_estimates_{}.csv'.format(ECONOMY_ID, config.FILE_DATE_ID), index=False)
        
    return activity_growth_estimates 

def calculate_vehicles_per_stock_parameters(model_data,ECONOMY_ID, car_base_amount=1,lcv_base_amount=3):
    breakpoint()#phl getting nans?
    #usig cars as the base (1) and for freight, lcv as the base (as 3?) then we will calcualte the relative amount if activity theat the other vehicle types have compared to this base. This will be used to calcualte the 'comparitive stocks' of each vehicle type in each economy, which is only used to idneifty if the maximum stocks per cpita for that transport type has been reached.
    #the base_amounts are used to allow for the two transport types to use the same gompertz gamma value, which is based on passenger transport.
    passenger_stocks = model_data[model_data['Transport Type']=='passenger'].copy()
    freight_stocks = model_data[model_data['Transport Type']=='freight'].copy()
    
    #sum by economy, scenario, date and vehicle type
    passenger_stocks = passenger_stocks.groupby(['Economy', 'Scenario', 'Date', 'Transport Type','Vehicle Type'])[['Stocks', 'Activity']].sum().reset_index()
    #calcualte amount of activity per stocks for each vehicle type
    passenger_stocks['Activity_per_stocks'] = passenger_stocks['Activity'] / passenger_stocks['Stocks']
    #set base as the vlaue of the cars. so extract that and then join on
    cars = passenger_stocks[passenger_stocks['Vehicle Type']=='car'].copy()
    cars.drop(columns=['Vehicle Type'], inplace=True)
    cars.rename(columns={'Activity_per_stocks':'cars'}, inplace=True)
    #adjust base amount to be in terms of the base amount of cars so that we can compare the relative amount of activity per stocks for each vehicle type
    cars['cars'] =  cars['cars']/car_base_amount
    #join on cars
    passenger_stocks = passenger_stocks.merge(cars, on=['Economy', 'Scenario', 'Date'], how='left', suffixes=('', '_base'))
    #calcualte relative amount of activity per stocks for each vehicle type
    passenger_stocks['Activity_per_stocks_relative_to_cars'] = passenger_stocks['Activity_per_stocks'] / passenger_stocks['cars']
    #and thats all. just set the gompertz_vehicles_per_stock to be this value since it represents the amount of activity that each vehicle types stock represents compared to the base amount. This can be timesed by the stocks to get the representative amount of stocks for each vehicle type so tehy can be compared to each other
    passenger_stocks['gompertz_vehicles_per_stock'] = passenger_stocks['Activity_per_stocks_relative_to_cars'] 
    #keep only cols we need
    passenger_stocks = passenger_stocks[['Economy', 'Scenario', 'Date', 'Vehicle Type', 'Transport Type','gompertz_vehicles_per_stock']]
    
    #combine passenger and freight stocks
    vehicles_per_stock_parameters = passenger_stocks.copy()
    # else:
    #     vehicles_per_stock_parameters = passenger_stocks.copy()
        
    #check for nas. if there are any, base the gompertz_vehicles_per_stock on the mean of all other econbomies for that vehicle type:
    if vehicles_per_stock_parameters.isna().sum().sum()>0:
        #load in the mean values for each vehicle type
        mean_df = pd.DataFrame()
        for economy in config.economy_scenario_concordance['Economy'].unique():
            # if os.path.exists(root_dir + '/' + 'intermediate_data/road_model/{}_vehicles_per_stock_parameters_{}.csv'.format(economy, 'passenger_only')) & ONLY_PASSENGER_VEHICLES:
            #     e = pd.read_csv(root_dir + '/' + 'intermediate_data/road_model/{}_vehicles_per_stock_parameters_{}.csv'.format(economy, 'passenger_only'))
            if os.path.exists(root_dir + '/' + 'intermediate_data/road_model/{}_vehicles_per_stock_parameters.csv'.format(economy)):
                e = pd.read_csv(root_dir + '/' + 'intermediate_data/road_model/{}_vehicles_per_stock_parameters.csv'.format(economy))
            else:
                continue
            #calc mean while ignoring date and scenario
            e = e.groupby(['Vehicle Type','Transport Type'])['gompertz_vehicles_per_stock'].mean().reset_index()
            mean_df = pd.concat([mean_df, e], axis=0)
        #calc mean of all economies
        mean_df = mean_df.groupby(['Vehicle Type','Transport Type'])['gompertz_vehicles_per_stock'].mean().reset_index()
        #now join on mean values
        vehicles_per_stock_parameters = vehicles_per_stock_parameters.merge(mean_df, on=['Vehicle Type','Transport Type'], how='left', suffixes=('', '_mean'))
        #fill na with mean
        vehicles_per_stock_parameters['gompertz_vehicles_per_stock'] = vehicles_per_stock_parameters['gompertz_vehicles_per_stock'].fillna(vehicles_per_stock_parameters['gompertz_vehicles_per_stock_mean'])
        #drop mean
        vehicles_per_stock_parameters.drop(columns=['gompertz_vehicles_per_stock_mean'], inplace=True) 
        
        # #if reaminging nas is freight 2w just set the vlaue to 0.5. there are hardly any anyway
        # if vehicles_per_stock_parameters.loc[(vehicles_per_stock_parameters['gompertz_vehicles_per_stock'].isna()) & (vehicles_per_stock_parameters['Vehicle Type']=='2w') & (vehicles_per_stock_parameters['Transport Type']=='freight'), 'gompertz_vehicles_per_stock'].shape[0]>0: 
        #     #set to 0.5
        #     vehicles_per_stock_parameters.loc[(vehicles_per_stock_parameters['gompertz_vehicles_per_stock'].isna()) & (vehicles_per_stock_parameters['Vehicle Type']=='2w') & (vehicles_per_stock_parameters['Transport Type']=='freight'), 'gompertz_vehicles_per_stock'] = 0.5 
              
        #check no nas remaining
        if vehicles_per_stock_parameters.isna().sum().sum()>0:
            breakpoint()
            time.sleep(1)
            raise ValueError('We still have NAs in the vehicles_per_stock_parameters dataframe')    
    
    #save for later use
    # if ONLY_PASSENGER_VEHICLES:
    #     vehicles_per_stock_parameters.to_csv(root_dir + '/' + 'intermediate_data/road_model/{}_vehicles_per_stock_parameters_{}_{}.csv'.format(ECONOMY_ID, 'passenger_only'), index=False)
    # else:
    vehicles_per_stock_parameters.to_csv(root_dir + '/' + 'intermediate_data/road_model/{}_vehicles_per_stock_parameters.csv'.format(ECONOMY_ID), index=False)
    
    return vehicles_per_stock_parameters
    
def prepare_data_for_logistic_fitting(model_data, ECONOMY_ID):
    # #extract the vehicles_per_stock_parameters:
    # vehicles_per_stock_parameters = pd.read_excel(root_dir + '/' + 'input_data/parameters.xlsx', sheet_name='gompertz_vehicles_per_stock')
    # #convert from regiosn to economies:
    # vehicles_per_stock_regions = pd.read_excel(root_dir + '/' + 'input_data/parameters.xlsx', sheet_name='vehicles_per_stock_regions')
    # #join on region
    # vehicles_per_stock_parameters = vehicles_per_stock_parameters.merge(vehicles_per_stock_regions, on='Region', how='left')
    #dro regions
    # vehicles_per_stock_parameters.drop(columns=['Region'], inplace=True)
    breakpoint()
    vehicles_per_stock_parameters = calculate_vehicles_per_stock_parameters(model_data, ECONOMY_ID)
    #Convert some stocks to gompertz adjusted stocks by multiplying them by the vehicle_gompertz_factors. This is because you can expect some economies to have more or less of that vehicle type than others. These are very general estiamtes, and could be refined later.
    new_stocks = model_data.merge(vehicles_per_stock_parameters, on=['Vehicle Type','Transport Type','Scenario', 'Date', 'Economy'], how='left')
    new_stocks['Stocks'] = new_stocks['Stocks'] * new_stocks['gompertz_vehicles_per_stock']
    #since we adjusted stocks by this amount we should reclaculte activity and travel km. this will only have the effect o fmaking it so that when we are obseriving and comparing activity growth it will reflect the amount that each stok represents.. i think?
    new_stocks['Activity'] = new_stocks['Activity'] * new_stocks['gompertz_vehicles_per_stock']
    new_stocks['Travel_km'] = new_stocks['Travel_km'] * new_stocks['gompertz_vehicles_per_stock']
    new_stocks_copy = new_stocks.copy()
    cols_to_sum_by = ['Economy', 'Scenario', 'Date', 'Transport Type']
    #sum up new stocks and other values specific to each vehicle type, by economy, scenario, date and transport type (so remove vehicle type)
    new_stocks = new_stocks[cols_to_sum_by+['Stocks','Activity', 'Travel_km']].groupby(cols_to_sum_by).sum().reset_index()
    
    #now, as we are going to reestiamte the growth rate using adjusted stocks, and these stocks are goign to be timesed by their vehicle_gompertz_factors and summed, we need to come up with the equivalent mileage and Occupancy_or_load weighted average for each transport ytpe, using a weighting based on the amount of stocks (or 'Travel_km') for each vehicle type. this will prevent them from ebeing overexagerated due to the effect of rarer vehicle types which have higher values for these cols, which will increase effective activity (eg buses have high occupancy and mielsage comapred to 2w, but a fraction of the stoskcs).
    weighted_average_model_data = model_data.copy()
    weighted_average_model_data = weighted_average_model_data[cols_to_sum_by+['Mileage','Occupancy_or_load', 'Vehicle Type']].drop_duplicates()
    #merge on the new stocks, travel km and act since they have been adjusted by the vehicle_gompertz_factors
    weighted_average_model_data = weighted_average_model_data.merge(new_stocks_copy, on=cols_to_sum_by+['Vehicle Type'], how='left', suffixes=('', '_new'))
    #multiply mileage and occupancy by stocks and travel km respectively
    weighted_average_model_data['Mileage'] = weighted_average_model_data['Mileage'] * weighted_average_model_data['Stocks']
    weighted_average_model_data['Occupancy_or_load'] = weighted_average_model_data['Occupancy_or_load'] * weighted_average_model_data['Travel_km']#timeseing by travel km allos you to take into account the amount that each vehicle type drives, so that you dont overestimate the occupancy of a vehicle type that drives less but has a high occupancy.
    #then sum and divide these cols by the sum of stocks
    weighted_average_model_data = weighted_average_model_data.groupby(cols_to_sum_by).sum().reset_index()
    weighted_average_model_data['Mileage'] = weighted_average_model_data['Mileage'] / weighted_average_model_data['Stocks']
    weighted_average_model_data['Occupancy_or_load'] = weighted_average_model_data['Occupancy_or_load'] / weighted_average_model_data['Travel_km']
    #drop 'Stocks'
    weighted_average_model_data = weighted_average_model_data[['Economy', 'Scenario', 'Date', 'Transport Type', 'Mileage','Occupancy_or_load']]
    #now merge this back into new_model_data after summing up that data's new stocks

    #extract other values we'll need but ont want to sum (because they are constant for each economy and year)
    non_summed_values = model_data.copy()
    non_summed_values = non_summed_values[cols_to_sum_by+['Population','Gompertz_gamma','Gdp_per_capita']].drop_duplicates()

    #now join all values together with a merge
    new_model_data = new_stocks.merge(non_summed_values, on = cols_to_sum_by, how = 'left')
    new_model_data = new_model_data.merge(weighted_average_model_data, on = cols_to_sum_by, how = 'left')
    #breakpoint()
    #test that activity is the same as before:
    new_model_data['Activity'] = new_model_data['Stocks'] * new_model_data['Occupancy_or_load'] * new_model_data['Travel_km']
    
    plot_logistic_fitting_data.plot_aggregated_input_data_for_logisitc_fitting(ECONOMY_ID, new_model_data)
        
    # if new_model_data['Activity'].sum() != model_data['Activity'].sum():
    #     breakpoint()
    #     time.sleep(1)
    #     print('Activity is not the same as before, it was {} before and is {} now'.format(model_data['Activity'].sum(), new_model_data['Activity'].sum()))
    #     # raise ValueError('Activity is not the same as before')
    #seems needless to test this now, since of course the activity will be different because we have adjusted the stocks. But it would e good to have some sort of test here
    return new_model_data


def estimate_new_growth_rate(model_data_logistic_predictions, date_where_gamma_is_reached, APPLY_SMOOTHING_TO_GROWTH_RATE):
    #take in the activity data we just estiamted and then calcualte the growth rate of activity as the percentage change in activity from the previous year plus 1. 
    #also do some smoothing to make sure that the growth rate doesnt change too much from year to year
    activity_growth_estimates = model_data_logistic_predictions[['Date', 'Economy', 'Scenario', 'Activity', 'Transport Type']].drop_duplicates().groupby(['Date', 'Economy', 'Scenario', 'Transport Type'])['Activity'].sum().reset_index().copy()

    activity_growth_estimates.sort_values(['Economy', 'Scenario', 'Date', 'Transport Type'], inplace=True)
    activity_growth_estimates['Activity_growth'] = activity_growth_estimates.groupby(['Economy', 'Scenario', 'Transport Type'])['Activity'].pct_change()+1
    #replace nan with 1
    activity_growth_estimates['Activity_growth'] = activity_growth_estimates['Activity_growth'].fillna(1)
    
    if APPLY_SMOOTHING_TO_GROWTH_RATE:
        method1=False
        method2=True
        if method2:
            #using the year where the gamma has een reached and the frist year of the projection, linearly interpolate between the two activity growth rates so that the growth slowly decreases to the activity growth rate at the projected vlaue.
            
            #however it is important that the area between the top of the growth curve (at min date) and the bottom of the growth curve (at date_marker) remains equal to what it used to be, so that the sum of growth doesnt change, andtehrefore the stocks per cpita actually reaches the gamma value. This will also make ti important to make sure that the growth rate is not too high in the first year, as it has to be realistic
            # breakpoint() 
            # activity_growth_estimates.to_pickle('a.pkl')
            # date_where_gamma_is_reached.to_pickle('b.pkl')
            # activity_growth_estimates = pd.read_pickle('a.pkl')
            # date_where_gamma_is_reached = pd.read_pickle('b.pkl')
            #join date_where_gamma_is_reached onto activity_growth_estimates using an indicator, and where its both, we can assume this is the year where the gamma is reached. Then we can use this to interpolate between the two years
            # Merge and find the date marker
            activity_growth_estimates = activity_growth_estimates.merge(date_where_gamma_is_reached, on=['Economy', 'Scenario', 'Transport Type', 'Date'], how='left', indicator=True)
            if len(activity_growth_estimates[activity_growth_estimates['_merge'] == 'both'])==0:
                return activity_growth_estimates
            
            date_marker = activity_growth_estimates[activity_growth_estimates['_merge'] == 'both'].Date.unique()[0] + 1
            # Calculate area under curve before date marker. this is not as simple as clacuaitng the sum of acitvity growth. we should instead reduce activity growth by the height at the date marker and then sum. this will hadnle negatives too.
            height_at_marker = activity_growth_estimates[activity_growth_estimates['Date'] == date_marker][['Economy', 'Scenario', 'Transport Type', 'Activity_growth']].rename(columns={'Activity_growth':'height_at_date_marker'}).copy()
            activity_growth_estimates=activity_growth_estimates.merge(height_at_marker, how='left', on=['Economy', 'Scenario', 'Transport Type'])
            activity_growth_estimates['area_before'] = activity_growth_estimates['Activity_growth'] - activity_growth_estimates['height_at_date_marker']
            area_before = activity_growth_estimates[activity_growth_estimates['Date'] < date_marker].groupby(['Economy', 'Scenario', 'Transport Type'])['area_before'].sum().reset_index()            
            activity_growth_estimates = activity_growth_estimates.drop(columns=['area_before'])
        
            # Prepare for theoretical calculations
            unique_rows = activity_growth_estimates[['Economy', 'Scenario', 'Transport Type']].drop_duplicates().reset_index(drop=True)
            base = date_marker - activity_growth_estimates['Date'].min() + 1
            height_at_min = activity_growth_estimates[activity_growth_estimates['Date'] == activity_growth_estimates['Date'].min() + 1][['Economy', 'Scenario', 'Transport Type', 'Activity_growth']].rename(columns={'Activity_growth':'height_at_min_date'})

            # Merge and calculate theoretical area
            theoretical = unique_rows.merge(height_at_marker, how='left', on=['Economy', 'Scenario', 'Transport Type']).merge(height_at_min, how='left', on=['Economy', 'Scenario', 'Transport Type'])
            theoretical['actual_height'] = theoretical['height_at_min_date'] - theoretical['height_at_date_marker']
            theoretical['Activity_growth_at_min_date'] = theoretical['height_at_min_date']
            theoretical['base'] = base
            theoretical['area'] = 0.5 * theoretical['base'] * theoretical['actual_height']

            # Adjust height to match actual area
            theoretical = theoretical.merge(area_before, how='left', on=['Economy', 'Scenario', 'Transport Type'])
            theoretical['new_actual_height'] = (2 * theoretical['area_before']) / theoretical['base']
            
            #it might be that the height is too high. we can identify this if it is 1.25 times higher than theoretical['height_at_min_date']-theoretical['height_at_date_marker'] . if this is so, we will set the height to be this value and then adjust the base to be wider than it was before so that the area is the same
            theoretical['actual_height'] = np.where(theoretical['new_actual_height'] > 1.25 * (theoretical['actual_height']), 1.25 * (theoretical['actual_height']), theoretical['new_actual_height'])
            theoretical['Activity_growth_at_min_date'] = theoretical['height_at_date_marker'] + theoretical['actual_height']
            theoretical['base'] = (2 * theoretical['area_before']) / theoretical['actual_height']
            #reclauclate date_marker. if it is beyond date.max() then introduce new dates beyond it for the interpolation
            date_marker = theoretical['base'].max() + activity_growth_estimates['Date'].min() - 1
            #note,, i think this will have issues if the growth trajectory is different for the groups in the df. currnetly its the same so it works, akso this issue will probavlby occur for a lot of code here
            extra_rows = pd.DataFrame()
            max_date = activity_growth_estimates['Date'].max()
            if date_marker > max_date:
                for date in range(int(activity_growth_estimates['Date'].max()+1), int(date_marker+2)):
                    
                    new_row = activity_growth_estimates.loc[activity_growth_estimates['Date']==activity_growth_estimates['Date'].max()].copy()
                    new_row['Date'] = date
                    extra_rows = pd.concat([extra_rows, new_row], axis=0)
                    
                activity_growth_estimates = pd.concat([activity_growth_estimates, extra_rows], axis=0)
                #set the activity growth to ['height_at_date_marker'] in the final year
                activity_growth_estimates.loc[activity_growth_estimates['Date']==activity_growth_estimates['Date'].max(), 'Activity_growth'] = theoretical['height_at_date_marker'].values
            # Update activity_growth_estimates
            activity_growth_estimates = activity_growth_estimates.merge(theoretical[['Economy', 'Scenario', 'Transport Type', 'Activity_growth_at_min_date']], how='left', on=['Economy', 'Scenario', 'Transport Type']).reset_index(drop=True)
            activity_growth_estimates.loc[(activity_growth_estimates['Date'] == activity_growth_estimates['Date'].min() + 1), 'Activity_growth'] = activity_growth_estimates.loc[(activity_growth_estimates['Date'] == activity_growth_estimates['Date'].min() + 1), 'Activity_growth_at_min_date']
            
            activity_growth_estimates.loc[(activity_growth_estimates['Date'] < date_marker) & (activity_growth_estimates['Date'] > activity_growth_estimates['Date'].min() + 1), 'Activity_growth'] = np.nan

            #drop first date so it doesnt affect the interpolation (its always 1 anyway)
            first_date_df = activity_growth_estimates.loc[activity_growth_estimates['Date']==activity_growth_estimates['Date'].min()].copy()
            activity_growth_estimates = activity_growth_estimates.loc[activity_growth_estimates['Date']!=activity_growth_estimates['Date'].min()].copy()
            manual_interpolation=False
            
            if manual_interpolation:
                #pandas interpolation linear libary doesnt give a constant gradient so we will do it manually:
                for group in activity_growth_estimates[['Economy', 'Scenario', 'Transport Type']].drop_duplicates().values.tolist():
                    #grab the group and then grab x1, y1, x2, y2
                    group_df = activity_growth_estimates.loc[(activity_growth_estimates['Economy']==group[0]) & (activity_growth_estimates['Scenario']==group[1]) & (activity_growth_estimates['Transport Type']==group[2])].copy()
                    x1 = group_df.loc[group_df['Date']==group_df['Date'].min(), 'Date'].values[0]
                    y1 = group_df.loc[group_df['Date']==group_df['Date'].min(), 'Activity_growth'].values[0]
                    x2 = group_df.loc[group_df['Date']==date_marker, 'Date'].values[0]
                    y2 = group_df.loc[group_df['Date']==date_marker, 'Activity_growth'].values[0]
                    gradient = (y2-y1)/(x2-x1)
                    
                    # Get the linear function
                    linear_func = linear_interpolation(x1, y1, x2, y2, gradient)
                    
                    #fill na with linear function
                    nas = group_df.loc[group_df['Activity_growth'].isna(), 'Date'].values.tolist()
                    group_df.loc[group_df['Activity_growth'].isna(), 'Activity_growth'] = linear_func(nas)
                    #add back to activity_growth_estimates
                    activity_growth_estimates.loc[(activity_growth_estimates['Economy']==group[0]) & (activity_growth_estimates['Scenario']==group[1]) & (activity_growth_estimates['Transport Type']==group[2]), 'Activity_growth'] = group_df['Activity_growth'].values.tolist()
            else:
                
                # Interpolate:
                activity_growth_estimates.sort_values([ 'Economy', 'Scenario', 'Transport Type', 'Date'], inplace=True)
                activity_growth_estimates.reset_index(drop=True, inplace=True)
                # Create a new Series with the interpolated values
                interpolated_series = activity_growth_estimates.groupby(['Economy', 'Scenario', 'Transport Type'])['Activity_growth'].apply(lambda x: x.interpolate(method='linear')).reset_index(drop=True)

                activity_growth_estimates['Activity_growth'] = interpolated_series
            
            #add back first date
            activity_growth_estimates = pd.concat([first_date_df, activity_growth_estimates], axis=0)
            
            #remove dates that natch the dates in extra_rows
            if extra_rows.shape[0]>0:
                activity_growth_estimates = activity_growth_estimates.loc[~activity_growth_estimates['Date'].isin(extra_rows['Date'].unique())].copy()
            
            #drop cols
            activity_growth_estimates.drop(columns=['Activity_growth_at_min_date', '_merge', 'height_at_date_marker'], inplace=True)
        if method1:
            #identify any years where there are abrupt changes in growth rate and smooth them out. FOr now, we will identify this as anywhere the diff is greater than 1% and smooth it out by applying a quadratic interpolation to the 3 years around it (this was chosen because the issue was occuring where duringthe year that the gamma was reached, the growth would go negative, then bounce up to around 0.5% in following year, and then just follow population generally)
            
            #do smoothing, but ignore 2021, 2020  and 2022 because these are affected by covid
            activity_growth_estimates_covid = activity_growth_estimates.loc[activity_growth_estimates['Date']<=2022].copy()
            activity_growth_estimates = activity_growth_estimates.loc[activity_growth_estimates['Date']>2022].copy()
            
            activity_growth_estimates['Activity_growth_diff'] = activity_growth_estimates.groupby(['Economy', 'Scenario', 'Transport Type'])['Activity_growth'].diff()
            activity_growth_estimates['Activity_growth_diff'] = activity_growth_estimates['Activity_growth_diff'].fillna(0)
            activity_growth_estimates['Activity_growth_diff'] = activity_growth_estimates['Activity_growth_diff'].abs()
            years_to_interpolate = activity_growth_estimates.loc[activity_growth_estimates['Activity_growth_diff']>0.01]['Date'].unique()
            #add the years before and after to the list
            years_to_interpolate = np.unique(np.concatenate([years_to_interpolate-2, years_to_interpolate, years_to_interpolate+2])).tolist()
            #remove any years that are not in the dataframe
            years_to_interpolate = [year for year in years_to_interpolate if year in activity_growth_estimates['Date'].unique()]
            #loop drop all years that are in the list
            for year in years_to_interpolate:
                activity_growth_estimates.loc[activity_growth_estimates['Date']==year, 'Activity_growth'] = np.nan
            #interpolate
            activity_growth_estimates= activity_growth_estimates.reset_index(drop=True).sort_values([ 'Date', 'Economy', 'Scenario', 'Date', 'Transport Type'])
            
            activity_growth_estimates['Activity_growth'] = activity_growth_estimates.groupby(['Economy', 'Scenario', 'Transport Type'], group_keys=False)['Activity_growth'].apply(lambda x: x.interpolate(method='linear'))#, order=2))
            
            #drop diff
            activity_growth_estimates.drop(columns=['Activity_growth_diff'], inplace=True)
            #concat back together
            activity_growth_estimates = pd.concat([activity_growth_estimates_covid, activity_growth_estimates], axis=0)
        
    return activity_growth_estimates

def linear_interpolation(x1, y1, x2, y2, gradient):
    # Calculate the y-intercept b using y = mx + b
    b1 = y1 - gradient * x1
    b2 = y2 - gradient * x2
    
    # Average the y-intercepts to get a smoother transition
    b = (b1 + b2) / 2
    
    def linear_function(x):
        return gradient * x + b
    
    return linear_function

#CREATE NEW DATAFRAME WITH LOGISTIC FUNCTION PREDICTIONS
def create_new_dataframe_with_logistic_predictions(new_model_data, new_stocks_per_capita_estimates, FIT_LOGISTIC_CURVE_TO_DATA):
    """ Take in the model data and the parameters estimates and create a new dataframe with the logistic function predictions for the stocks, activity and mileage basedon the parameters and the gdp per cpita. This will first calcualte the stocks, then using mileage, calcualte the travel km, then calcualte activity based on the occupancy rate. Then later on the activity growth rate will be calcualted from this activity, which is the only new output we will use to run the road model again."""
    #breakpoint()
    #calculate new stocks:
    model_data_logistic_predictions = new_model_data.copy()
    
    #averaage out the Mileage and Occupancy_or_load for each economy and scenario. having them as a weighted average of the stocks awas causing too much variation that was too hard to keep a track of. This will essentailly just sm,ooth out the curve a bit, but it will still be the same result by the end of the forecast
    
    model_data_logistic_predictions_factors = model_data_logistic_predictions.groupby(['Economy', 'Scenario', 'Transport Type'])[['Mileage','Occupancy_or_load']].mean().reset_index().copy()#.loc[model_data_logistic_predictions['Date']>2020]. ##note that to ignore the effect of adjsuting mielage after covid we will estimate this using mielage after 2020
    
    #join on the factors
    model_data_logistic_predictions = model_data_logistic_predictions.drop(columns=['Mileage','Occupancy_or_load']).merge(model_data_logistic_predictions_factors, on=['Economy', 'Scenario', 'Transport Type'], how='left')
    
    if FIT_LOGISTIC_CURVE_TO_DATA:
        #apply logistic_function to each row
        model_data_logistic_predictions['New_Stocks_per_thousand_capita'] = model_data_logistic_predictions.apply(lambda row: logistic_function(row['Gdp_per_capita'], row['Gompertz_gamma'], row['Gompertz_beta'], row['Gompertz_alpha']), axis=1)
    else:
        #join on the new_stocks_per_capita_estimates 
        new_stocks_per_capita_estimates.rename(columns={'Stocks_per_thousand_capita':'New_Stocks_per_thousand_capita'}, inplace=True)
        model_data_logistic_predictions = model_data_logistic_predictions.merge(new_stocks_per_capita_estimates, on=['Date', 'Economy', 'Scenario', 'Transport Type'], how='left')
        
    #calaculte stocks
    model_data_logistic_predictions['New_Thousand_stocks_per_capita'] = model_data_logistic_predictions['New_Stocks_per_thousand_capita'] / 1000000
    model_data_logistic_predictions['New_Stocks'] = model_data_logistic_predictions.apply(lambda row: row['New_Thousand_stocks_per_capita'] * row['Population'], axis=1)
    #calculate new travel km:
    model_data_logistic_predictions['New_Travel_km'] = model_data_logistic_predictions.apply(lambda row: row['New_Stocks'] * row['Mileage'], axis=1)
    #calculate new activity:
    model_data_logistic_predictions['New_Activity'] = model_data_logistic_predictions.apply(lambda row: row['New_Travel_km'] * row['Occupancy_or_load'], axis=1)
    
    # model_data_logistic_predictions.to_csv(root_dir + '/' + 'b.csv')
    #repalce Thousand_stocks_per_capita, Stocks_per_thousand_capita, stocks, activity and travel km with new values
    model_data_logistic_predictions['Stocks'] = model_data_logistic_predictions['New_Stocks']
    model_data_logistic_predictions['Activity'] = model_data_logistic_predictions['New_Activity']
    model_data_logistic_predictions['Travel_km'] = model_data_logistic_predictions['New_Travel_km']
    model_data_logistic_predictions['Thousand_stocks_per_capita'] = model_data_logistic_predictions['New_Thousand_stocks_per_capita']
    model_data_logistic_predictions['Stocks_per_thousand_capita'] = model_data_logistic_predictions['New_Stocks_per_thousand_capita']
    
    #drop cols we dont need
    model_data_logistic_predictions.drop(columns=['New_Stocks_per_thousand_capita', 'New_Thousand_stocks_per_capita', 'New_Stocks', 'New_Travel_km', 'New_Activity'], inplace=True)
    
    return model_data_logistic_predictions

def find_parameters_for_logistic_function(new_model_data, show_plots, matplotlib_bool, plotly_bool, FIT_LOGISTIC_CURVE_TO_DATA, PROPORTION_BELOW_GAMMA, EXTRA_YEARS_TO_REACH_GAMMA, INTERPOLATE_ALL_DATES):
    #load ECONOMIES_WITH_STOCKS_PER_CAPITA_REACHED from parameters.yml
    ECONOMIES_WITH_MAX_STOCKS_PER_CAPITA_REACHED =  yaml.load(open(root_dir + '/' + 'config/parameters.yml'), Loader=yaml.FullLoader)['ECONOMIES_WITH_MAX_STOCKS_PER_CAPITA_REACHED']
    
    #loop through economies and transport types and perform the clacualtions ti find the parameters for the logistic function
    #create empty dataframe to store results
    parameters_estimates = pd.DataFrame(columns=['Gompertz_gamma', 'Economy', 'Transport Type', 'Scenario'])
    new_stocks_per_capita_estimates = pd.DataFrame(columns=['Date', 'Economy', 'Transport Type', 'Scenario', 'Stocks_per_thousand_capita'])
    date_where_gamma_is_reached = pd.DataFrame(columns=['Date', 'Economy', 'Transport Type', 'Scenario'])
    for economy in new_model_data['Economy'].unique():
        for transport_type in new_model_data['Transport Type'].unique():
            new_model_data_economy_ttype = new_model_data[(new_model_data['Economy']==economy) & (new_model_data['Transport Type']==transport_type)].copy()
            #if gamma is same for both scenarios, we should only run it once, otherwise we have changces of getting different results which isnt really right.
            if new_model_data_economy_ttype['Gompertz_gamma'].nunique()==1:
                ONE_SCENARIO = True
                scenario = new_model_data_economy_ttype['Scenario'].unique()[0]
                other_scenarios = new_model_data_economy_ttype['Scenario'].unique()[1:].tolist()
                new_model_data_economy_ttype = new_model_data_economy_ttype[new_model_data_economy_ttype['Scenario']==scenario]
            else:
                ONE_SCENARIO = False
            for scenario in new_model_data_economy_ttype['Scenario'].unique():

                economy_ttype_scenario = economy + '_' + transport_type + '_' + scenario
                
                #filter for economy and transport type
                new_model_data_economy_scenario_ttype = new_model_data_economy_ttype[new_model_data['Scenario']==scenario].copy()

                #filter for cols we need:
                new_model_data_economy_scenario_ttype = new_model_data_economy_scenario_ttype[['Date', 'Transport Type', 'Economy','Scenario', 'Stocks', 'Gdp_per_capita','Population', 'Gompertz_gamma', 'Travel_km', 'Mileage', 'Activity']].drop_duplicates()

                #sum stocks,'Activity', Travel_km, , with any NAs set to 0
                new_model_data_economy_scenario_ttype['Stocks'] = new_model_data_economy_scenario_ttype['Stocks'].fillna(0)
                new_model_data_economy_scenario_ttype['Activity'] = new_model_data_economy_scenario_ttype['Activity'].fillna(0)
                new_model_data_economy_scenario_ttype['Travel_km'] = new_model_data_economy_scenario_ttype['Travel_km'].fillna(0)
                # breakpoint()#is this really the fix?
                
                summed_values = new_model_data_economy_scenario_ttype.groupby(['Date', 'Economy','Scenario', 'Transport Type'])[['Stocks','Activity', 'Travel_km']].sum().reset_index()
                
                #join summed values with other data that didnt need to be summed
                new_model_data_economy_scenario_ttype.drop(columns=['Stocks','Activity', 'Travel_km'], inplace=True)
                new_model_data_economy_scenario_ttype.drop_duplicates(inplace=True)
                new_model_data_economy_scenario_ttype = new_model_data_economy_scenario_ttype.merge(summed_values, on=['Date', 'Economy','Scenario', 'Transport Type'], how='left')

                #calcualte stocks per capita
                new_model_data_economy_scenario_ttype['Thousand_stocks_per_capita'] = new_model_data_economy_scenario_ttype['Stocks']/new_model_data_economy_scenario_ttype['Population']
                #convert to more readable units. We will convert back later if we need to #todo do we need to?
                new_model_data_economy_scenario_ttype['Stocks_per_thousand_capita'] = new_model_data_economy_scenario_ttype['Thousand_stocks_per_capita'] * 1000000

                #find date where stocks per cpaita passes gamma, then find a proportion below that and set that as gamma_threshold, which is used in a few ways
                #find the date where stocks per capita passes gamma
                gamma = new_model_data_economy_scenario_ttype['Gompertz_gamma'].unique()[0]
                gamma_minus_PROPORTION_BELOW_GAMMA = gamma - (gamma * PROPORTION_BELOW_GAMMA)
                
                gamma_threshold = new_model_data_economy_scenario_ttype[new_model_data_economy_scenario_ttype['Stocks_per_thousand_capita'] > gamma_minus_PROPORTION_BELOW_GAMMA]['Date'].min()
                
                date_where_stocks_per_capita_passes_gamma = new_model_data_economy_scenario_ttype[new_model_data_economy_scenario_ttype['Stocks_per_thousand_capita'] > gamma]['Date'].min()

                #sometimes the date is not found. in which case we ahve no issue with the stocks per capita going aobve gamma. So we dont need to adjsut growth rates for this economy. i.e. skip
                if np.isnan(gamma_threshold):
                    if FIT_LOGISTIC_CURVE_TO_DATA:
                        #set parameters to nan so that we can filter them out later
                        params = pd.DataFrame({'Gompertz_beta':np.nan, 'Gompertz_alpha':np.nan, 'Gompertz_gamma':np.nan, 'Economy': economy, 'Transport Type': transport_type, 'Scenario': scenario}, index=[0])
                        #concat to parameters_estimates
                        parameters_estimates = pd.concat([parameters_estimates, params], axis=0).reset_index(drop=True)
                    else:
                        #just use the manually set stocks per cpita vlaues and calcualte resulting activity growth from them!                  
                        new_stocks_per_capita_estimates = pd.concat([new_stocks_per_capita_estimates, new_model_data_economy_scenario_ttype[['Date', 'Economy', 'Transport Type', 'Scenario', 'Stocks_per_thousand_capita']]], axis=0).reset_index(drop=True)
                    
                    date_where_gamma_is_reached = pd.concat([date_where_gamma_is_reached, pd.DataFrame({'Date': date_where_stocks_per_capita_passes_gamma+EXTRA_YEARS_TO_REACH_GAMMA, 'Economy': economy, 'Transport Type': transport_type, 'Scenario': scenario}, index=[0])], axis=0).reset_index(drop=True)
                    continue
                
                #we have an issue if min_date is = gamma_threshold, since we cant intepolate that as In this case we cant create data (like for max_date). So we will increase the gamma_threshold by 1 year which will make it work
                if INTERPOLATE_ALL_DATES:#by setting this to true, we will interpolate all dates where stocks per capita was below gamma
                    min_date = new_model_data_economy_scenario_ttype['Date'].min()
                else:#we will interpolate above the gamma_threshold and below where stocks per capita actually hits gamma
                    min_date = gamma_threshold
                # if :
                #     #just set ECONOMIES_WITH_MAX_STOCKS_PER_CAPITA_REACHED[economy] to True so that we can grab the stocks per capita in the first year and set all years to be that!
                #     ECONOMIES_WITH_MAX_STOCKS_PER_CAPITA_REACHED[economy] = True
                #     # gamma_threshold = gamma_threshold + 5#add 5 just so that if the min date is during covid then this wont be used to find the gradient!
                
                if ECONOMIES_WITH_MAX_STOCKS_PER_CAPITA_REACHED[economy] or date_where_stocks_per_capita_passes_gamma == min_date:
                    
                    #grab the stocks per cpaita in the first year and set all years to be that!
                    first_year_spc = new_model_data_economy_scenario_ttype.loc[new_model_data_economy_scenario_ttype['Date']==new_model_data_economy_scenario_ttype['Date'].min(), 'Stocks_per_thousand_capita'].unique()[0]
                    new_model_data_economy_scenario_ttype['Stocks_per_thousand_capita'] = first_year_spc
                    #and set gompertz gamma to be the same as the stocks per capita
                    gamma = first_year_spc
                    # breakpoint()
                else:
                    #replot the whole stocks per cpita line so that it curves from its starating point towards gamma, and ends at gamma with a gradient of 0
                    
                    # # #extract data after this date and set the stocks per capita to be a quadratic interpoalted line from the gamma - gamma*PROPORTION_BELOW_GAMMA to gamma over the time period EXTRA_YEARS_TO_REACH_GAMMA. then once we have reached the end of this time period, set the stocks per capita to be gamma
                    # # #set data between gamma_threshold and gamma_threshold+ EXTRA_YEARS_TO_REACH_GAMMA to NaN, the data after this will be set to gamma, and then we will interpolate between these two points                    
                    new_model_data_economy_scenario_ttype.loc[new_model_data_economy_scenario_ttype['Date'] >= date_where_stocks_per_capita_passes_gamma + EXTRA_YEARS_TO_REACH_GAMMA, 'Stocks_per_thousand_capita'] = gamma
                    new_model_data_economy_scenario_ttype.loc[(new_model_data_economy_scenario_ttype['Date'] <  date_where_stocks_per_capita_passes_gamma + EXTRA_YEARS_TO_REACH_GAMMA)&(new_model_data_economy_scenario_ttype['Date'] > min_date), 'Stocks_per_thousand_capita'] = np.nan
                    #if the last value is na, then we should create extra rows untilnew_model_data_economy_scenario_ttype['Date'] = gamma_threshold + EXTRA_YEARS_TO_REACH_GAMMA, and set the stocks per capita to gamma
                    
                    max_date = new_model_data_economy_scenario_ttype['Date'].max()
                    
                    if date_where_stocks_per_capita_passes_gamma + EXTRA_YEARS_TO_REACH_GAMMA > max_date:
                        #create extra rows for each date between gamma_threshold + EXTRA_YEARS_TO_REACH_GAMMA and the last date, and set the stocks per capita to gamma at date = gamma_threshold + EXTRA_YEARS_TO_REACH_GAMMA, and na otherwise
                        for year in range(max_date+1, date_where_stocks_per_capita_passes_gamma + EXTRA_YEARS_TO_REACH_GAMMA):
                            new_rows = pd.DataFrame({'Date': year, 'Economy': economy, 'Transport Type': transport_type, 'Scenario': scenario, 'Stocks_per_thousand_capita': np.nan}, index=[0])
                            new_model_data_economy_scenario_ttype = pd.concat([new_model_data_economy_scenario_ttype, new_rows], axis=0).reset_index(drop=True)
                        
                        #set final date to gamma
                        new_row = pd.DataFrame({'Date': date_where_stocks_per_capita_passes_gamma + EXTRA_YEARS_TO_REACH_GAMMA, 'Economy': economy, 'Transport Type': transport_type, 'Scenario': scenario, 'Stocks_per_thousand_capita': gamma}, index=[0])
                        new_model_data_economy_scenario_ttype = pd.concat([new_model_data_economy_scenario_ttype, new_row], axis=0).reset_index(drop=True)     
                        
                    cubic=False#not working yet
                    if cubic:
                        #Now we have a gap between the starting year and the year where we reach gamma+EXTRA_YEARS_TO_REACH_GAMMA. We will fill this gap with a quadratic interpolation between the starting year and the year where we reach gamma. It will be important that the curve is smooth and constant.
                        # new_model_data_economy_scenario_ttype['Stocks_per_thousand_capita'] = new_model_data_economy_scenario_ttype['Stocks_per_thousand_capita'].interpolate(method='quadratic')
                        from scipy.interpolate import CubicSpline     
                        # Separate the data into known and unknown points
                        known = new_model_data_economy_scenario_ttype.dropna(subset=['Stocks_per_thousand_capita'])
                        unknown = new_model_data_economy_scenario_ttype[new_model_data_economy_scenario_ttype['Stocks_per_thousand_capita'].isna()]

                        #to fit the cubic spline properly we want to get the point that is geometrically in the middle of the unknown points. So we will take the mean of the first and last known points, round to 0dp and use that as the midpoint date
                        midpoint_date = ((unknown.Date.min()-1+ unknown.Date.max()+1)/2).round(0).astype(int)
                        # at unknown.Date.min()-1 and unknown.Date.max()+1, we will grab the stocks per capita and take the mean of these two values
                        midpoint_spc = (new_model_data_economy_scenario_ttype.loc[new_model_data_economy_scenario_ttype['Date']==unknown.Date.min()-1, 'Stocks_per_thousand_capita'].unique()[0] + new_model_data_economy_scenario_ttype.loc[new_model_data_economy_scenario_ttype['Date']==unknown.Date.max()+1, 'Stocks_per_thousand_capita'].unique()[0])/2
                        #drop that date from known data
                        known = known[known['Date'] != midpoint_date]
                        #add these to the known data
                        known = pd.concat([known, pd.DataFrame({'Date': midpoint_date, 'Economy': economy, 'Transport Type': transport_type, 'Scenario': scenario, 'Stocks_per_thousand_capita': midpoint_spc}, index=[0])], axis=0).reset_index(drop=True)
                        #concat back to unknown so we can reset the index
                        new_model_data_economy_scenario_ttype = pd.concat([known, unknown], axis=0).sort_values(['Date']).reset_index(drop=True)
                        
                        known = new_model_data_economy_scenario_ttype.dropna(subset=['Stocks_per_thousand_capita'])
                        unknown = new_model_data_economy_scenario_ttype[new_model_data_economy_scenario_ttype['Stocks_per_thousand_capita'].isna()]
                        
                        # Fit a cubic spline to the known data points
                        cs = CubicSpline(known.index, known['Stocks_per_thousand_capita'])

                        # Interpolate the missing values
                        new_model_data_economy_scenario_ttype.loc[unknown.index, 'Stocks_per_thousand_capita'] = cs(unknown.index)
                        #method='linear')#, order=2)    
                        #drop the added dates if we added any
                        new_model_data_economy_scenario_ttype = new_model_data_economy_scenario_ttype[new_model_data_economy_scenario_ttype['Date'] <= max_date]
                    else:
                        #simply interpolate
                        new_model_data_economy_scenario_ttype['Stocks_per_thousand_capita'] = new_model_data_economy_scenario_ttype['Stocks_per_thousand_capita'].interpolate(method='linear')#, order=2)
                        
                        #drop the added dates if we added any
                        new_model_data_economy_scenario_ttype = new_model_data_economy_scenario_ttype[new_model_data_economy_scenario_ttype['Date'] <= max_date]
                if FIT_LOGISTIC_CURVE_TO_DATA:
                    #fit a logistic curve to the stocks per capita data
                    gamma, growth_rate, midpoint = logistic_fitting_function(new_model_data_economy_scenario_ttype, gamma, economy_ttype_scenario, show_plots,matplotlib_bool=matplotlib_bool, plotly_bool=plotly_bool)
                    
                    #note midpoint is alpha, growth is beta
                    params = pd.DataFrame({'Gompertz_beta':growth_rate, 'Gompertz_alpha':midpoint, 'Gompertz_gamma':gamma, 'Economy': economy, 'Transport Type': transport_type, 'Scenario': scenario}, index=[0])
                    #concat to parameters_estimates
                    parameters_estimates = pd.concat([parameters_estimates, params], axis=0).reset_index(drop=True)
                    
                    date_where_gamma_is_reached = pd.concat([date_where_gamma_is_reached, pd.DataFrame({'Date': date_where_stocks_per_capita_passes_gamma+EXTRA_YEARS_TO_REACH_GAMMA, 'Economy': economy, 'Transport Type': transport_type, 'Scenario': scenario}, index=[0])], axis=0).reset_index(drop=True)
                else:
                    #just use the manually set stocks per cpita vlaues and calcualte resulting activity growth from them!                  
                    new_stocks_per_capita_estimates = pd.concat([new_stocks_per_capita_estimates, new_model_data_economy_scenario_ttype[['Date', 'Economy', 'Transport Type', 'Scenario', 'Stocks_per_thousand_capita']]], axis=0).reset_index(drop=True)
                    
                    #fill params with gamma, set otehrs to nan
                    params = pd.DataFrame({'Gompertz_beta':np.nan, 'Gompertz_alpha':np.nan, 'Gompertz_gamma':gamma, 'Economy': economy, 'Transport Type': transport_type, 'Scenario': scenario}, index=[0])
                    parameters_estimates = pd.concat([parameters_estimates, params], axis=0).reset_index(drop=True)
                    
                    date_where_gamma_is_reached = pd.concat([date_where_gamma_is_reached, pd.DataFrame({'Date': date_where_stocks_per_capita_passes_gamma+EXTRA_YEARS_TO_REACH_GAMMA, 'Economy': economy, 'Transport Type': transport_type, 'Scenario': scenario}, index=[0])], axis=0).reset_index(drop=True)
            #FIX FOR WHERE GAMMA IS SAME IN BOTH SCENARIOS SO THE RESULT IS THE SAME:
            if ONE_SCENARIO:
                other_scenario_entries = new_stocks_per_capita_estimates.loc[(new_stocks_per_capita_estimates['Economy']==economy) & (new_stocks_per_capita_estimates['Transport Type']==transport_type) & (new_stocks_per_capita_estimates['Scenario']==scenario)].copy()
                other_scenario_date_where_gamma_is_reached = date_where_gamma_is_reached.loc[(date_where_gamma_is_reached['Economy']==economy) & (date_where_gamma_is_reached['Transport Type']==transport_type) & (date_where_gamma_is_reached['Scenario']==scenario)].copy()
                parameters_estimates_other_scenario = parameters_estimates.loc[(parameters_estimates['Economy']==economy) & (parameters_estimates['Transport Type']==transport_type) & (parameters_estimates['Scenario']==scenario)].copy()
                
                for scenario in other_scenarios:
                    other_scenario_entries['Scenario'] = scenario
                    new_stocks_per_capita_estimates = pd.concat([new_stocks_per_capita_estimates, other_scenario_entries], axis=0).reset_index(drop=True)
                    other_scenario_date_where_gamma_is_reached['Scenario'] = scenario
                    date_where_gamma_is_reached = pd.concat([date_where_gamma_is_reached, other_scenario_date_where_gamma_is_reached], axis=0).reset_index(drop=True)
                    parameters_estimates['Scenario'] = scenario
                    parameters_estimates = pd.concat([parameters_estimates, parameters_estimates_other_scenario], axis=0).reset_index(drop=True)
                    
    return parameters_estimates, new_stocks_per_capita_estimates, date_where_gamma_is_reached

def logistic_function(gdp_per_capita,gamma, growth_rate, midpoint):
    #gompertz funtion: gamma * np.exp(alpha * np.exp(beta * gdp_per_capita))
    #note midpoint is alpha, growth is beta e.g.  logistic_function(gdp_per_capita,gamma, beta, alpha)
    #original equation: logistic_function(x, L, k, x0): L / (1 + np.exp(-k * (x - x0)))
    # L is the maximum limit (in your case, this would be the gamma value),
    # k is the growth rate,
    # x0​ is the x-value of the sigmoid's midpoint,
    # x is the input to the function (in your case, this could be time or GDP per capita).
    return gamma / (1 + np.exp(-growth_rate * (gdp_per_capita - midpoint)))
    
def logistic_fitting_function(new_model_data_economy_scenario_ttype, gamma, economy_ttype_scenario, show_plots, matplotlib_bool, plotly_bool):
    #grab data we need
    date = new_model_data_economy_scenario_ttype['Date']
    stocks_per_capita = new_model_data_economy_scenario_ttype['Stocks_per_thousand_capita']
    #TODO NOT SURE IF WE WANT TO GRAB GDP PER CPITA OR FIT THE MODEL TO THE YEAR NOW? IM GOING TO TRY USING GDP PER CPAITA SO THAT AT ELAST THE PARAMETER ESTIMATES CAN BE SHARED BETWEEN ECONOMIES IN TERMS OF GDP PER CAPITA
    gdp_per_capita = new_model_data_economy_scenario_ttype['Gdp_per_capita']
    # 
    def logistic_function_curve_fit(gdp_per_capita, growth_rate, midpoint):
        #need a new function so we can pass in gamma (i couldnt work out how to do it in curve fit function ): 
        #gompertz funtion: gamma * np.exp(alpha * np.exp(beta * gdp_per_capita))
        #original equation: logistic_function(x, L, k, x0): L / (1 + np.exp(-k * (x - x0)))
        # L is the maximum limit (in your case, this would be the gamma value),
        # k is the growth rate,
        # x0​ is the x-value of the sigmoid's midpoint,
        # x is the input to the function (in your case, this could be time or GDP per capita).
        return gamma / (1 + np.exp(-growth_rate * (gdp_per_capita - midpoint)))
    try:
        # Fit the logistic function to your data
        popt, pcov = curve_fit(logistic_function_curve_fit, gdp_per_capita, stocks_per_capita, bounds=(0, [3., max(gdp_per_capita)]))
    except:
        breakpoint()
        time.sleep(1)
        raise ValueError('Could not fit logistic function to data for economy: ', economy_ttype_scenario)
    # Use the fitted function to calculate growth
    growth_rate, midpoint = popt
    
    if show_plots:
        #print gamma
        print('gamma: ', gamma)
        #print params
        print('growth_rate: ', growth_rate, 'midpoint: ', midpoint)

    projected_growth = logistic_function_curve_fit(gdp_per_capita, growth_rate, midpoint)

    plot_logistic_fitting_data.plot_logistic_fit(date, stocks_per_capita, gdp_per_capita, gamma, growth_rate, midpoint, economy_ttype_scenario,show_plots, matplotlib_bool=matplotlib_bool, plotly_bool=plotly_bool)

    return gamma, growth_rate, midpoint

                    
#theres a hance it may be better just to stop the stocks per cap from passing gamma, rather than applying a line too.
# %%

def average_out_growth_rate_using_cagr(new_growth_forecasts, economies_to_avg_growth_over_all_years_in_freight_for = ['19_THA']):

    def calculate_cagr_from_factors(factors):
        # Multiply all factors together
        total_growth = factors.product()
        
        # Take the Nth root and subtract 1
        return total_growth ** (1.0 / len(factors)) - 1

    new_freight_growth_economies = new_growth_forecasts.loc[new_growth_forecasts['Economy'].isin(economies_to_avg_growth_over_all_years_in_freight_for)].copy()

    # apply cagr on the growth factors, grouped by economy, transport type and scenario:
    cagr = new_freight_growth_economies.groupby(['Economy', 'Scenario', 'Transport Type'])['Activity_growth_new'].apply(calculate_cagr_from_factors)
    new_freight_growth_economies = pd.merge(new_freight_growth_economies.drop(columns=['Activity_growth_new']), cagr, on=['Economy', 'Scenario', 'Transport Type'], how='left')
    
                                            
    #############
    early_period = range(new_growth_forecasts.Date.min()+1, new_growth_forecasts.Date.min()+7)
    other_economies_early_growth = new_growth_forecasts.loc[~new_growth_forecasts['Economy'].isin(economies_to_avg_growth_over_all_years_in_freight_for) & (new_growth_forecasts['Date'].isin(early_period))].copy()
    
    # apply cagr on the growth factors, grouped by economy, transport type and scenario:
    cagr = other_economies_early_growth.groupby(['Economy', 'Scenario', 'Transport Type'])['Activity_growth_new'].apply(calculate_cagr_from_factors)
    other_economies_early_growth = pd.merge(other_economies_early_growth.drop(columns=['Activity_growth_new']), cagr, on=['Economy', 'Scenario', 'Transport Type'], how='left')
    
    #############
    other_data = new_growth_forecasts.loc[~new_growth_forecasts['Economy'].isin(economies_to_avg_growth_over_all_years_in_freight_for) & (~new_growth_forecasts['Date'].isin(early_period))].copy()
    all_economies_data = pd.concat([new_freight_growth_economies, other_economies_early_growth, other_data], axis=0)
    new_growth_forecasts = all_economies_data.copy()
    
    return new_growth_forecasts

def custom_interpolate_bezier(x1, y1, x2, y2, initial_gradient, n_points=100):
    #this will use the bezier curve to plot a kind of logaritmic curve between the two points, but so that p2 and p3 are the same point, so that the curve has 0 gradient at the end also will Use the average gradient as the initial gradient
    m1 = initial_gradient 
    P0 = np.array([x1, y1])
    P1 = P0 + np.array([(x2 - x1) / 3, m1 * (x2 - x1) / 3])
    P2 = np.array([x2, y2])
    P3 = np.array([x2, y2])

    def bezier(t):
        return (
            (1 - t) ** 3 * P0
            + 3 * (1 - t) ** 2 * t * P1
            + 3 * (1 - t) * t ** 2 * P2
            + t ** 3 * P3
        )

    t_values = np.linspace(0, 1, n_points)
    curve = np.array([bezier(t) for t in t_values])
    return curve[:, 0], curve[:, 1]


def piecewise_linear_interpolation(df, column_name, n_pieces, gradients_list):
    # Sort DataFrame by Date
    df.sort_values(['Date'], inplace=True)
    
    # Find the first and last NaN points
    first_nan_idx = df[column_name].index[df[column_name].isna()].min()
    last_nan_idx = df[column_name].index[df[column_name].isna()].max()
    
    # Identify the first and last non-NaN points surrounding the block of NaNs
    first_valid_idx = first_nan_idx - 1
    last_valid_idx = last_nan_idx + 1
    
    # Divide the range into n_pieces segments
    segment_lengths = np.linspace(first_valid_idx, last_valid_idx, n_pieces + 1)
    
    # Initialize y-values
    y_values = [df.loc[first_valid_idx, column_name]]
    
    # Calculate the y-values at the boundaries of the segments
    for i in range(n_pieces):
        y_values.append(y_values[-1] + gradients_list[i] * (segment_lengths[i + 1] - segment_lengths[i]))
    
    # Perform piecewise linear interpolation
    x_new = np.arange(first_valid_idx + 1, last_valid_idx)
    y_new = np.interp(x_new, segment_lengths, y_values)
    
    # Replace the NaNs with the interpolated values
    nan_indices = df.index[df[column_name].isna()]
    df.loc[nan_indices, column_name] = y_new

    return df