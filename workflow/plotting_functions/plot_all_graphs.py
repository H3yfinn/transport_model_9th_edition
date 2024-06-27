#this script will plot everything you could plot on a timeseries using the data we ahve.


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
import plotly
import time
import itertools
AUTO_OPEN_PLOTLY_GRAPHS = False
dont_overwrite_existing_graphs = False
plot_png = False
plot_html = True
subfolder_name = 'all_economy_graphs'
original_default_save_folder = f'plotting_output/{subfolder_name}/{config.FILE_DATE_ID}/'#will add in scenario later to end of path
save_pickle = True
#get all useful graphs and put them in one folder
useful_graphs = []

beginning_year = config.OUTLOOK_BASE_YEAR
config.END_YEAR = config.GRAPHING_END_YEAR

#plot all data in model_output_all:
value_cols = ['passenger_km','freight_tonne_km', 'Energy', 'Stocks',
       'Occupancy', 'Load', 'Turnover_rate', 'New_vehicle_efficiency',
       'Travel_km', 'Efficiency', 'Mileage', 'Surplus_stocks',
       'Vehicle_sales_share',  'Gdp_per_capita','Gdp', 'Population', 'Stocks_per_thousand_capita','Average_age']
    
#some value cols are not summable because they are factors. so specify them for when we group by economy, then we can calculate the mean of them
non_summable_value_cols = ['Occupancy', 'Load', 'Turnover_rate', 'New_vehicle_efficiency', 'Efficiency','Mileage','Average_age']

categorical_cols = ['Vehicle Type', 'Medium', 'Transport Type', 'Drive']
macro_cols = ['Gdp_per_capita','Gdp', 'Population', 'Activity_growth']

def plot_all_graphs(ECONOMY_ID=None, PLOT=True, plot_comparisons=True):

    ##############FORMATTING#############
    #load data in
    original_model_output_8th = pd.read_csv('input_data/from_8th/reformatted/activity_energy_road_stocks.csv')
    #rename Year col into Date
    original_model_output_8th = original_model_output_8th.rename(columns={'Year':'Date'})
    original_activity_growth = pd.read_csv('input_data/from_8th/reformatted/activity_growth_8th.csv')
    original_model_output_detailed = pd.read_csv('output_data/model_output_detailed/all_economies_{}_{}'.format(config.FILE_DATE_ID, config.model_output_file_name))
    original_model_output_all = pd.read_csv('output_data/model_output/all_economies_{}_{}'.format(config.FILE_DATE_ID, config.model_output_file_name))
    original_model_output_with_fuels = pd.read_csv('output_data/model_output_with_fuels/all_economies_{}_{}'.format(config.FILE_DATE_ID, config.model_output_file_name))
    #loop thorugh scenarios:
    if ECONOMY_ID != None:
        #filter for economy of interest
        original_model_output_all = original_model_output_all[original_model_output_all['Economy']==ECONOMY_ID].copy()
        original_model_output_detailed = original_model_output_detailed[original_model_output_detailed['Economy']==ECONOMY_ID].copy()
        original_model_output_with_fuels = original_model_output_with_fuels[original_model_output_with_fuels['Economy']==ECONOMY_ID].copy()
        original_activity_growth = original_activity_growth[original_activity_growth['Economy']==ECONOMY_ID].copy()
        original_model_output_8th = original_model_output_8th[original_model_output_8th['Economy']==ECONOMY_ID].copy()
    
    for scenario in original_model_output_all['Scenario'].unique():
        config.SCENARIO_OF_INTEREST = scenario
        default_save_folder = original_default_save_folder + f'{config.SCENARIO_OF_INTEREST}/'
        #CHECK THAT SAVE FOLDER EXISTS, IF NOT CREATE IT
        if not os.path.exists(default_save_folder):
            os.makedirs(default_save_folder)
            
        #now do everything
        #FILTER FOR SCENARIO OF INTEREST
        #this should be temporary as the scenario should be passed in as a parameter through config if it is useed elsewhere

        model_output_all = original_model_output_all[original_model_output_all['Scenario']==config.SCENARIO_OF_INTEREST].copy()
        model_output_detailed = original_model_output_detailed[original_model_output_detailed['Scenario']==config.SCENARIO_OF_INTEREST].copy()
        model_output_with_fuels = original_model_output_with_fuels[original_model_output_with_fuels['Scenario']==config.SCENARIO_OF_INTEREST].copy()
        activity_growth = original_activity_growth[original_activity_growth['Scenario']==config.SCENARIO_OF_INTEREST].copy()
        if config.SCENARIO_OF_INTEREST == 'Target':
            model_output_8th = original_model_output_8th[original_model_output_8th['Scenario']=='Carbon Neutral'].copy()
        else:
            model_output_8th = original_model_output_8th[original_model_output_8th['Scenario']=='Reference'].copy()
            
        
        #set nans to '' for colusmns which contain letters, then set nans to 0 for columns which contain numbers. Except for date, which we want to keep as nan
        def replace_nans_with_empty_strings_and_zero(df):
            index = 0
            for col in df.columns:
                if col == 'Date':
                    continue
                while df.reset_index()[col][index] == np.nan:
                    index = index + 1
                if str(df.reset_index()[col][index]).isalpha():
                    df[col] = df[col].fillna('')
                else:
                    df[col] = df[col].fillna(0)
            return df
        model_output_all = replace_nans_with_empty_strings_and_zero(model_output_all)
        model_output_detailed = replace_nans_with_empty_strings_and_zero(model_output_detailed)
        model_output_detailed = replace_nans_with_empty_strings_and_zero(model_output_detailed)
        model_output_8th = replace_nans_with_empty_strings_and_zero(model_output_8th)
        model_output_with_fuels = replace_nans_with_empty_strings_and_zero(model_output_with_fuels)
        
        #where medium is not road then set drive and vehicle type to medium, so that we can plot them on the same graph
        model_output_all.loc[model_output_all['Medium']!='road', 'Drive'] = model_output_all['Medium']
        model_output_all.loc[model_output_all['Medium']!='road', 'Vehicle Type'] = model_output_all['Medium']
        model_output_detailed.loc[model_output_detailed['Medium']!='road', 'Drive'] = model_output_detailed['Medium']
        model_output_detailed.loc[model_output_detailed['Medium']!='road', 'Vehicle Type'] = model_output_detailed['Medium']
        model_output_with_fuels.loc[model_output_with_fuels['Medium']!='road', 'Drive'] = model_output_with_fuels['Medium']
        model_output_with_fuels.loc[model_output_with_fuels['Medium']!='road', 'Vehicle Type'] = model_output_with_fuels['Medium']

        #also set their stocks to 1 so they arent plotted:
        model_output_all.loc[model_output_all['Medium']!='road', 'Stocks'] = 1
        model_output_detailed.loc[model_output_detailed['Medium']!='road', 'Stocks'] = 1
        #do same for Stocks_per_thousand_capita, since this is just Stocks/Population
        model_output_detailed.loc[model_output_detailed['Medium']!='road', 'Stocks_per_thousand_capita'] = 1
        
        # #filter for economies on all dfs
        # model_output_all = model_output_all[model_output_all['Economy'].isin(config.ECONOMIES_TO_PLOT_FOR)]
        # model_output_detailed = model_output_detailed[model_output_detailed['Economy'].isin(config.ECONOMIES_TO_PLOT_FOR)]
        # model_output_8th = model_output_8th[model_output_8th['Economy'].isin(config.ECONOMIES_TO_PLOT_FOR)]
        # model_output_with_fuels = model_output_with_fuels[model_output_with_fuels['Economy'].isin(config.ECONOMIES_TO_PLOT_FOR)]
        # activity_growth = activity_growth[activity_growth['Economy'].isin(config.ECONOMIES_TO_PLOT_FOR)]

        #filter for certain years:
        if beginning_year != None:
            model_output_all = model_output_all[model_output_all['Date']>=beginning_year]
            model_output_detailed = model_output_detailed[model_output_detailed['Date']>=beginning_year]
            model_output_8th = model_output_8th[model_output_8th['Date']>=beginning_year]
            model_output_with_fuels = model_output_with_fuels[model_output_with_fuels['Date']>=beginning_year]
            activity_growth = activity_growth[activity_growth['Date']>=beginning_year]
        if config.END_YEAR != None:
            model_output_all = model_output_all[model_output_all['Date']<=config.END_YEAR]
            model_output_detailed = model_output_detailed[model_output_detailed['Date']<=config.END_YEAR]
            model_output_8th = model_output_8th[model_output_8th['Date']<=config.END_YEAR]
            model_output_with_fuels = model_output_with_fuels[model_output_with_fuels['Date']<=config.END_YEAR]
            activity_growth = activity_growth[activity_growth['Date']<=config.END_YEAR]
        
        #split freight tonne km and passenger km into two columns, as well as occupancy and load
        new_dfs_list = []
        old_dfs_list = [model_output_all, model_output_detailed, model_output_8th, model_output_with_fuels]
        for df in old_dfs_list:
            # #breakpoint()#cant find why activity for non road is not being split into these yet.
            # #separate non road first since they have their data in Activity column and non occupancy_or_load column
            # df_non_road = df[df['Medium']!='road'].copy()
            # df = df[df['Medium']=='road'].copy()    
            # #drop activity in df
                    
            passenger =df[df['Transport Type']=='passenger']
            #rename passenger_km to Activity and Occupancy to Occupancy_Load
            passenger = passenger.rename(columns={'Activity':'passenger_km', 'Occupancy_or_load':'Occupancy'})
            
            freight =df[df['Transport Type']=='freight']
            #rename freight_tonne_km to Activity and load to Occupancy_Load
            freight = freight.rename(columns={'Activity':'freight_tonne_km', 'Occupancy_or_load':'Load'})

            #combine passenger and freight
            new_df = pd.concat([passenger, freight])
            #drop activity and Occupancy_or_load from df if in it
            try:
                new_df = new_df.drop(columns=['Activity', 'Occupancy_or_load'])
            except:
                pass
            new_dfs_list.append(new_df)
            #fill nas
            new_df = new_df.fillna('')

        #reset the dfs
        model_output_all, model_output_detailed, model_output_8th, model_output_with_fuels = new_dfs_list

        ##############FORMATTING OVER#############
        #set up timer:
        #since this takes a while to run, jsut set a timer so the user can understand how long it will take. we will save the times to plotting_output/all_economy_graphs_plotting_times.csv with the name of each section as the index
        def start_timer(section, do_this):
            if do_this:
                print('Starting timer for section: {}'.format(section))
                print_expected_time_to_run(section)
                return time.time()
            else:
                return None

        def end_timer(start_time, section, do_this):
            if do_this:
                end_time = time.time()
                elapsed_time = end_time - start_time
                log_time(section, elapsed_time)
                print('Finished section: {} in {}'.format(section, elapsed_time))
            else:
                pass

        def log_time(section, elapsed_time):
            try:
                times_df = pd.read_csv('plotting_output/all_economy_graphs_plotting_times.csv')
            except FileNotFoundError:
                times_df = pd.DataFrame(columns=['section', 'time'])

            times_df_new_row = pd.DataFrame({'section': section, 'time': elapsed_time, 'num_economies': 21}, index=[0])
            times_df = pd.concat([times_df, times_df_new_row])
            times_df.to_csv('plotting_output/all_economy_graphs_plotting_times.csv', index=False)
        def print_expected_time_to_run(section):
            try:
                times_df = pd.read_csv('plotting_output/all_economy_graphs_plotting_times.csv')
                times_df = times_df[times_df['section']==section]
                times_df = times_df[times_df['num_economies']==21]
                times_df = times_df['time']
                times_df = times_df.mean()
                print(f'Expected time to run {section} is {times_df} seconds')
            except:
                pass

        # # usage example
        # section = 'Section 1'
        # start = start_timer(section)

        # # some long-running code
        # end_timer(start, section)
        
        #plot data by vehicle type and drive:
        #plot energy use by vehicle type and drive:
        #plot activity by vehicle type by drive
        #plot stocks by vehicle type by drive

        #plot energy use by economy by fuel type by drive
        #plot energy use by economy by fuel type by vehicle type

        #bascially we want to plot every column using economy as the facet then a mix of transport type, drive, vehicle type, medium and fuel as the categories. So we will create a function that does this:
        def check_graph_exists(save_folder, title, dont_overwrite_existing_graphs=False):
            #double check we havent already plotted this graph:
            if (os.path.exists(f'./{save_folder}/static/' + title + '.png') | os.path.exists(f'./{save_folder}/' + title + '.html')) & dont_overwrite_existing_graphs:
                return True
            else:
                return False
            
        def plot_line(df, y_column, x_column,color, line_dash, facet_col_wrap, facet_col, hover_name, hover_data, log_y, log_x, title, independent_y_axis, y_axis_title, x_axis_title, plot_html, plot_png, save_folder, AUTO_OPEN_PLOTLY_GRAPHS=False, width = 2000, height = 800):

            #fucntion for plotting a line graph within plot_line_by_economy
            #this could probably be better as part of a class
            fig = px.line(df, x=x_column, y=y_column, color=color,line_dash=line_dash, facet_col_wrap=facet_col_wrap, facet_col =facet_col, hover_name = hover_name, hover_data = hover_data, log_y = log_y, log_x = log_x, title=title)
            if independent_y_axis:
                fig.update_yaxes(matches=None)
                #show y axis on both plots
                fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
            #do y_axis_title and x_axis_title
            fig.update_layout(yaxis_title=y_axis_title, xaxis_title=x_axis_title)
            #save the graph
            if plot_html:
                plotly.offline.plot(fig, filename=f'./{save_folder}/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
            if plot_png:
                fig.write_image(f"./{save_folder}/static/" + title + '.png', scale=1, width=width, height=height)


        def plot_line_by_economy(df, color_categories, y_column,title,line_dash_categories=None,  x_column='Date', save_folder='all_economy_graphs', facet_col_wrap=7, facet_col =None, hover_name = None, hover_data = None, log_y = False, log_x = False, y_axis_title = None, x_axis_title = None, width = 2000, height = 800,AUTO_OPEN_PLOTLY_GRAPHS=False, independent_y_axis = True,plot_png=True, plot_html=True, dont_overwrite_existing_graphs=False, PLOT=True):
            """This function is intended to make plotting liine graphs of the model data a bit less repetitive. It will take in specifications like the plotly line graphing function (px.line) but will do some formatting before plotting. Can be used to plot data for multiple economies, jsut one or even a mix."""
            if not PLOT:
                return None
            #############
            if color_categories == None:
                categories = []
            else:
                categories = color_categories
            if line_dash_categories != None:
                categories = categories + [line_dash_categories]
            if facet_col != None:
                categories = categories + [facet_col]
            df = calc_mean_if_not_summable_else_sum(df, y_column, categories)
            #############
            
            graph_exists = check_graph_exists(save_folder, title, dont_overwrite_existing_graphs)
            if graph_exists and dont_overwrite_existing_graphs:
                print(f'Graph {title} already exists, skipping')
                return
            #copy df so that we dont change the original
            df = df.copy()
            #set color and line dash categories to list even if they are just one category
            if type(color_categories) != list:
                color_categories = [color_categories]
            if type(line_dash_categories) != list and line_dash_categories != None:
                line_dash_categories = [line_dash_categories]
            # convert color and likne dash categorties to one col each seperated by a hyphen
            color = '-'.join(color_categories)
            if line_dash_categories != None:
                line_dash = '-'.join(line_dash_categories)
                #add a column for the line dash
                df[line_dash] = df[line_dash_categories].apply(lambda x: '-'.join(x), axis=1)
            else:
                line_dash = None
            #add a column for the color
            df[color] = df[color_categories].apply(lambda x: '-'.join(x), axis=1)

            #if hover name is none then set it to the color+line_dash
            if hover_name == None:
                if line_dash_categories == None:
                    hover_name = color
                else:
                    hover_name = color + '-' + line_dash
                    #insert hovername into the dataframe as a column
                    df[hover_name] = df[color].astype(str) + '-' + df[line_dash].astype(str)
            #if fascet_col = None then create a column for it. it will be called ' ' and be ' '
            if facet_col == None:
                df[' '] = ' '
                facet_col = ' '
            #if hover data is none then set it to the y column
            if hover_data == None:
                hover_data = [y_column]
            #if y axis title is none then set it to the y column + unit
            if y_axis_title == None:
                try:
                    y_axis_title = y_column + measure_to_unit_concordance_dict[y_column]
                except:
                    y_axis_title = y_column
            #if x axis title is none then set it to the x column
            if x_axis_title == None:
                x_axis_title = x_column
            #plot energy use by drive type
            #title = 'Energy use by drive type'
            #model_output_all_drive = model_output_all.groupby(['Date', 'Drive', 'Economy']).sum().reset_index()
            #if tehre are any '' in the y column then drop them
            df = df[df[y_column] != '']

            #checkl that the folders wqe save to exist
            if not os.path.exists(f'./{save_folder}/'):
                os.makedirs(f'./{save_folder}/')
            #create static folder too
            if not os.path.exists(f'./{save_folder}/static'):
                os.makedirs(f'./{save_folder}/static')

            
            #if there are no line dashes then just plot the graph
            if line_dash_categories != None:
                df = df.groupby([x_column, facet_col,color, line_dash,hover_name])[y_column].sum().reset_index()
            else:
                if hover_name == color:
                    df = df.groupby([x_column, facet_col,color])[y_column].sum().reset_index()
                else:
                    df = df.groupby([x_column, facet_col,color,hover_name])[y_column].sum().reset_index()
            
            plot_line(df, y_column,x_column, color, line_dash, facet_col_wrap, facet_col, hover_name, hover_data, log_y, log_x, title, independent_y_axis, y_axis_title, x_axis_title, plot_html, plot_png,save_folder, AUTO_OPEN_PLOTLY_GRAPHS, width, height)

        ############################################################################
        
        
        def plot_area(df, y_column,x_column, color, line_group, facet_col_wrap, facet_col, hover_name, hover_data, log_y, log_x, title, independent_y_axis, y_axis_title, x_axis_title, plot_html, plot_png, save_folder, AUTO_OPEN_PLOTLY_GRAPHS=False, width = 2000, height = 800):
            fig = px.area(df, x=x_column, y=y_column, color=color, line_group=line_group, facet_col_wrap=facet_col_wrap, facet_col=facet_col, hover_name=hover_name, hover_data=hover_data, log_y=log_y, log_x=log_x, title=title)
            if independent_y_axis:
                fig.update_yaxes(matches=None)
                fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
            fig.update_layout(yaxis_title=y_axis_title, xaxis_title=x_axis_title)
            if plot_html:
                plotly.offline.plot(fig, filename=f'./{save_folder}/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
            if plot_png:
                fig.write_image(f"./{save_folder}/static/" + title + '.png', scale=1, width=width, height=height)
                
        def plot_area_by_economy(df, color_categories, y_column, title, line_group_categories=None,  x_column='Date', save_folder='all_economy_graphs', facet_col_wrap=7, facet_col =None, hover_name = None, hover_data = None, log_y = False, log_x = False, y_axis_title = None, x_axis_title = None, width = 2000, height = 800,AUTO_OPEN_PLOTLY_GRAPHS=False, independent_y_axis = True,plot_png=True, plot_html=True, dont_overwrite_existing_graphs=False, PLOT=True):
            if not PLOT:
                return None
            
            #############
            if color_categories == None:
                categories = []
            else:
                categories = color_categories
            if line_group_categories != None:
                categories = categories + [line_group_categories]
            if facet_col != None:
                categories = categories + [facet_col]
            df = calc_mean_if_not_summable_else_sum(df, y_column,categories)
            #############
            graph_exists = check_graph_exists(save_folder, title, dont_overwrite_existing_graphs)
            if graph_exists and dont_overwrite_existing_graphs:
                print(f'Graph {title} already exists, skipping')
                return
            df = df.copy()
            if type(color_categories) != list:
                color_categories = [color_categories]
            if type(line_group_categories) != list and line_group_categories != None:
                line_group_categories = [line_group_categories]
            color = '-'.join(color_categories)
            if line_group_categories != None:
                line_group = '-'.join(line_group_categories)
                df[line_group] = df[line_group_categories].apply(lambda x: '-'.join(x), axis=1)
            else:
                line_group = None
            df[color] = df[color_categories].apply(lambda x: '-'.join(x), axis=1)
            if hover_name == None:
                if line_group_categories == None:
                    hover_name = color
                else:
                    hover_name = color + '-' + line_group
                    df[hover_name] = df[color].astype(str) + '-' + df[line_group].astype(str)
            if facet_col == None:
                df[' '] = ' '
                facet_col = ' '
            if hover_data == None:
                hover_data = [y_column]
            if y_axis_title == None:
                try:
                    y_axis_title = y_column + measure_to_unit_concordance_dict[y_column]
                except:
                    y_axis_title = y_column
            if x_axis_title == None:
                x_axis_title = x_column
            df = df[df[y_column] != '']
            if not os.path.exists(f'./{save_folder}/'):
                os.makedirs(f'./{save_folder}/')
            if not os.path.exists(f'./{save_folder}/static'):
                os.makedirs(f'./{save_folder}/static')
            if line_group_categories != None:
                df = df.groupby([x_column, facet_col,color, line_group,hover_name])[y_column].sum().reset_index()
            else:
                if hover_name == color:
                    df = df.groupby([x_column, facet_col,color])[y_column].sum().reset_index()
                else:
                    df = df.groupby([x_column, facet_col,color,hover_name])[y_column].sum().reset_index()
            plot_area(df, y_column, x_column, color, line_group, facet_col_wrap, facet_col, hover_name, hover_data, log_y, log_x, title, independent_y_axis, y_axis_title, x_axis_title, plot_html, plot_png,save_folder, AUTO_OPEN_PLOTLY_GRAPHS, width, height)

        ###########
        def calc_mean_if_not_summable_else_sum(df, value_cols,categorical_cols,non_summable_value_cols=non_summable_value_cols):
            #identifcy means
            mean_cols = []
            if type(value_cols) != list:
                value_cols = [value_cols]
            summable_cols = value_cols.copy()
            for col in value_cols:
                if col in non_summable_value_cols:
                    mean_cols = mean_cols + [col]
                    summable_cols.remove(col)
                    
            #replace values equal to '' with nan while we calculate the mean and sum 
            df[value_cols] = df[value_cols].replace('', np.nan)
            agg_dict = {col: 'sum' for col in summable_cols}
            agg_dict.update({col: 'mean' for col in mean_cols})
            df = df.groupby(categorical_cols+['Date']).agg(agg_dict).reset_index()
            #now replace nan with ''    
            df[value_cols] = df[value_cols].replace(np.nan,'')
            
            return df
        
        
        ###############################################################################
        
        # #plot energy use by drive type
        # do_this = True
        # if do_this:
        #     title = f'Energy use by drive type - {scenario}'
        #     start = start_timer(title)

        #     plot_line_by_economy(model_output_all, ['Drive'], 'Energy', title, save_folder=default_save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS, plot_png=plot_png)
            
        #     end_timer(start, title)

        ##################################################################
        ###########################plot all data in model_output_all################
        ##################################################################

        dataframe_name = 'model_output_detailed'
        #save copy of data as pickle for use in recreating plots. put it in save_folder
        if save_pickle:
            model_output_detailed.to_pickle(f'{default_save_folder}/{dataframe_name}.pkl')
            print(f'{dataframe_name} saved as pickle')

        #plot each combination of: one of the value cols and then any number of the categorical cols
        n_categorical_cols = len(categorical_cols)
        do_this = True
                
        start = start_timer(dataframe_name,do_this)
        if do_this:

            #plot graphs with all economies on one graph
            for value_col in value_cols:
                for i in range(1, n_categorical_cols+1):
                    for combo in itertools.combinations(categorical_cols, i):
                        title = f'{value_col} by {combo} - {scenario}'
                        save_folder = f'{default_save_folder}/{dataframe_name}/{value_col}'

                        plot_line_by_economy(model_output_detailed, color_categories=list(combo), y_column=value_col, title=title, save_folder=save_folder, facet_col='Economy',AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS, plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
                        print(f'plotting {value_col} by {combo}')
                        
        end_timer(start, dataframe_name, do_this)

        ##################################################################
        
        # dont_overwrite_existing_graphs = True
        # plot_png = True
        # plot_html = False
        #do it for each unique economy as a singular graph
        #first create economy= 'all' which is aplies either an avg or sum to the group of all economies depending on if the col is in non summable cols
        #make it tall with measure col      
        # #find non ints in the vlaues in the value cols

        for col in value_cols:
            #see if there are any non ints in the values
            non_ints = model_output_detailed[col].apply(lambda x: not isinstance(x, int))
            #if there are any non ints then print the col name
            if non_ints.any():
                print(col)
                #len
                print(len(non_ints))

        

        # def calc_APEC_mean_or_sum(df, value_cols, non_summable_value_cols,categorical_cols):
        #     #replace values equal to '' with nan while we calculate the mean and sum
        #     df[value_cols] = df[value_cols].replace('', np.nan)
        #     df_APEC_mean = df.groupby(categorical_cols+['Date']).agg({col: 'mean' for col in value_cols}).reset_index()
        #     df_APEC_sum = df.groupby(categorical_cols+['Date']).agg({col: 'sum' for col in value_cols}).reset_index()
        #     #now remove non_summable_value_cols from sum, and remove non, non_summable_value_cols from mean
        #     df_APEC_mean.drop(columns=[col for col in value_cols if col not in non_summable_value_cols], inplace=True)
        #     df_APEC_sum.drop(columns=non_summable_value_cols, inplace=True)
        #     #now merge the two dataframes
        #     df_APEC = pd.merge(df_APEC_mean, df_APEC_sum, on=categorical_cols+['Date'], how='outer')

        #     df_APEC['Economy'] = 'all'
        #     df = pd.concat([df, df_APEC])
            
        #     #now replace nan with ''    
        #     df = df.replace(np.nan, '', regex=True)
        #     return df

        ###########
        

        ###########
        
        #PLOT model_output_detailed BY ECONOMY
        n_categorical_cols = len(categorical_cols)
        do_this = True
        start = start_timer(dataframe_name+' by economy',do_this)
        if do_this:
            for economy_x in model_output_detailed['Economy'].unique():
                for value_col in value_cols:
                    for i in range(1, n_categorical_cols+1):
                        for combo in itertools.combinations(categorical_cols, i):
                            title = f'{value_col} by {combo} - {scenario}'
                            save_folder = f'{default_save_folder}/{dataframe_name}/{economy_x}/{value_col}'
                                                    
                            #filter for that ecovnomy only and then plot
                            model_output_detailed_econ = model_output_detailed[model_output_detailed['Economy'] == economy_x].copy()
                            plot_line_by_economy(model_output_detailed_econ, color_categories=list(combo), y_column=value_col, title=title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
                            print(f'plotting {value_col} by {combo}')
        end_timer(start, dataframe_name+' by economy', do_this)

        ##################################################################
        #TEMP
        if ECONOMY_ID == None:#if we are plotting all economies then plot the regional data too
            #plot regional groupings of economys
            #import the region_economy_mappin.xlsx from config/concordances_and_config_data
            region_economy_mapping = pd.read_csv('./config/concordances_and_config_data/region_economy_mapping.csv')
            #join with model_output_detailed_APEC.
            #where there is no region drop the row since we are just plotting singular economies atm
            model_output_detailed_regions = model_output_detailed.merge(region_economy_mapping, how='left', left_on='Economy', right_on='Economy')

            # model_output_detailed_regions['Region'] = model_output_detailed_regions['Region'].fillna(model_output_detailed_regions['Economy'])
            model_output_detailed_regions = model_output_detailed_regions.dropna(subset=['Region'])

            # model_output_detailed_regions = model_output_detailed_regions.groupby(categorical_cols+['Date',  'Region']).agg({col: 'sum' for col in value_cols if col not in non_summable_value_cols else 'mean'}).reset_index()
            #breakpoint()#is it passenger km?
            model_output_detailed_regions = calc_mean_if_not_summable_else_sum(model_output_detailed_regions, value_cols, categorical_cols+['Region'])

            #save copy of data as pickle for use in recreating plots. put it in save_folder
            if save_pickle:
                model_output_detailed_regions.to_pickle(f'{default_save_folder}/{dataframe_name}_regional.pkl')
                print(f'{dataframe_name}_regional saved as pickle')
            
            n_categorical_cols = len(categorical_cols)
            do_this = True
            
            start = start_timer(dataframe_name+' by region',do_this)
            if do_this:
                for economy_x in model_output_detailed_regions['Region'].unique():
                    #if region is nan then skip it
                    if pd.isna(economy_x):
                        continue
                    for value_col in value_cols:
                        for i in range(1, n_categorical_cols+1):
                            for combo in itertools.combinations(categorical_cols, i):
                                title = f'{value_col} by {combo} - {scenario}'
                                save_folder = f'{default_save_folder}/{dataframe_name}/{economy_x}/{value_col}'

                                #filter for that ecovnomy only and then plot
                                model_output_detailed_econ = model_output_detailed_regions[model_output_detailed_regions['Region'] == economy_x].copy()
                                plot_line_by_economy(model_output_detailed_econ, color_categories=list(combo), y_column=value_col, title=title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html,dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
                                print(f'plotting {value_col} by {combo}')
            end_timer(start, dataframe_name+' by region', do_this)

        ##################################################################
        ###########################plot 'Energy' by fuel type############
        ##################################################################
        #breakpoint()

        #. need to define value cols that are worth plotting
        value_cols_new = ['Energy']
        categorical_cols_new = ['Vehicle Type', 'Medium', 'Transport Type', 'Drive']
        dataframe_name = 'model_output_with_fuels'
        #create economy= 'all' which is the sum of all economies:
        model_output_with_fuels_plot = model_output_with_fuels.groupby(categorical_cols_new+['Date','Fuel']).sum().reset_index()
        model_output_with_fuels_plot['Economy'] = 'all'
        model_output_with_fuels_plot_economy = model_output_with_fuels.groupby(categorical_cols_new+['Date','Fuel', 'Economy']).sum().reset_index()
        model_output_with_fuels_plot = pd.concat([model_output_with_fuels_plot_economy, model_output_with_fuels_plot])

        #save copy of data as pickle for use in recreating plots. put it in save_folder
        if save_pickle:
            model_output_with_fuels_plot.to_pickle(f'{default_save_folder}/{dataframe_name}.pkl')
        #plot singular graphs for each economy
        do_this = True
        
        start = start_timer(dataframe_name+' by economy',do_this)
        if do_this:
            n_categorical_cols_new = len(categorical_cols_new)
            for economy_x in model_output_with_fuels_plot['Economy'].unique():
                for value_col in value_cols_new:
                    for i in range(1, n_categorical_cols_new+1):
                        for combo in itertools.combinations(categorical_cols_new, i):
                            # Add 'Fuel' to the combo
                            combo = list(combo) + ['Fuel']
                            dataframe_name = 'model_output_with_fuels'
                            title = f'{value_col} by {combo} - {scenario}'
                            save_folder = f'{default_save_folder}/{dataframe_name}/{economy_x}/{value_col}/line/'
                                                    
                            #filter for that ecovnomy only and then plot
                            model_output_with_fuels_plot_econ = model_output_with_fuels_plot[model_output_with_fuels_plot['Economy'] == economy_x].copy()
                            plot_line_by_economy(model_output_with_fuels_plot_econ, color_categories= list(combo), y_column=value_col, title=title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
                            print(f'plotting {value_col} by {combo}')
                            
                            title = f'{value_col} by {combo} - {scenario}'
                            save_folder = f'{default_save_folder}/{dataframe_name}/{economy_x}/{value_col}/area/'

                            plot_area_by_economy(model_output_with_fuels_plot_econ, color_categories= list(combo), y_column=value_col, title=title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
        end_timer(start, dataframe_name+' by economy', do_this)

        ##################################################################
        
        if ECONOMY_ID == None:#if we are plotting all economies then plot the regional data too
            #merge with regions
            #plot regional groupings of economys
            #import the region_economy_mappin.xlsx from config/concordances_and_config_data
            region_economy_mapping = pd.read_csv('./config/concordances_and_config_data/region_economy_mapping.csv')
            model_output_with_fuels_regions = model_output_with_fuels.merge(region_economy_mapping, how='left', left_on='Economy', right_on='Economy')

            #drop nas
            model_output_with_fuels_regions = model_output_with_fuels_regions.dropna(subset=['Region'])

            #sum up when we drop economy
            model_output_with_fuels_regions = model_output_with_fuels_regions.groupby(categorical_cols_new+['Date','Fuel', 'Region']).sum().reset_index()
            
            #save copy of data as pickle for use in recreating plots. put it in save_folder
            if save_pickle:
                model_output_with_fuels_regions.to_pickle(f'{default_save_folder}/{dataframe_name}_regional.pkl')
                print(f'{dataframe_name}_regional saved as pickle')
            do_this = True
            start = start_timer(dataframe_name+' by region',do_this)
            if do_this:
                
                #plot singular graphs for each economy #TODO error here
                n_categorical_cols_new = len(categorical_cols_new)
                for region in model_output_with_fuels_regions['Region'].unique():
                    for value_col in value_cols_new:
                        for i in range(1, n_categorical_cols_new+1):
                            for combo in itertools.combinations(categorical_cols_new, i):
                                # # Add 'Fuel' to the combo
                                # combo = list(combo) + ['Fuel']

                                title = f'{value_col} by {list(combo) + ["Fuel"]} - {scenario}'
                                save_folder = f'{default_save_folder}/{dataframe_name}/{region}/{value_col}/line/'
                                                        
                                #filter for that ecovnomy only and then plot
                                model_output_with_fuels_regions_region = model_output_with_fuels_regions[model_output_with_fuels_regions['Region'] == region]
                                plot_line_by_economy(model_output_with_fuels_regions_region, color_categories = list(combo), y_column=value_col, title=title,  line_dash_categories = 'Fuel', save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
                                print(f'plotting {value_col} by {list(combo) + ["Fuel"]}')
                                
                                
                                title = f'{value_col} by {list(combo) + ["Fuel"]} - {scenario}'
                                save_folder = f'{default_save_folder}/{dataframe_name}/{economy_x}/{value_col}/area/'
                                
                                plot_area_by_economy(model_output_with_fuels_regions_region, color_categories = list(combo), y_column=value_col, title=title,  line_group_categories = 'Fuel', save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
            end_timer(start, dataframe_name+' by region', do_this)
        ##################################################################
        ##################################################################
        #plot graphs with all economies on one graph
        if ECONOMY_ID == None:#if we are plotting all economies then plot the all on one plot too
            do_this = True
            start = start_timer(dataframe_name+' with all economies on one graph',do_this)
            if do_this:
                
                for value_col in value_cols_new:
                    for i in range(1, n_categorical_cols+1):
                        for combo in itertools.combinations(categorical_cols_new, i):
                            # combo = list(combo) + ['Fuel']
                            title = f'{value_col} by {list(combo) + ["Fuel"]} - {scenario}'
                        
                            save_folder = f'{default_save_folder}/energy_use_by_fuel/all_economies_plot/{value_col}/line'

                            plot_line_by_economy(model_output_with_fuels_plot, color_categories= list(combo),y_column=value_col, title=title,  line_dash_categories='Fuel', save_folder=save_folder, facet_col='Economy',AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
                            print(f'plotting {value_col} by {list(combo) + ["Fuel"]}')
                            
                            save_folder = f'{default_save_folder}/energy_use_by_fuel/all_economies_plot/{value_col}/area'
                            plot_area_by_economy(model_output_with_fuels_plot, color_categories= list(combo),y_column=value_col, title=title,  line_group_categories='Fuel', save_folder=save_folder, facet_col='Economy',AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
            end_timer(start, dataframe_name+' with all economies on one graph', do_this)
        ##################################################################
        if plot_comparisons or PLOT:
            plot_comparisons=True
            do_this = True
            #why is stocks grapoh not showing date on the x axis for area chart here.
            dataframe_name = 'model_output_comparison'
            start = start_timer(dataframe_name,do_this)
            if do_this:
                #PLOT 8TH VS 9TH FUEL:
                # original_model_output_8th = pd.read_csv('intermediate_data/activity_energy_road_stocks.csv')
                #['Medium', 'Transport Type', 'Vehicle Type', 'Drive', 'Date', 'Economy',
                #    'Scenario', 'Activity', 'Energy', 'Stocks']
                #we will merge together model_output_8th and model_output_all and then plot them together, with 8th on one facet, 9th on the oter. we will plot te values for 'energy, 'stocks' and 'activity'
                
                model_output_8th['Dataset'] = '8th'
                model_output_all['Dataset'] = '9th'
                #filter for same columns. drop any duplicates
                model_output_all = model_output_all[model_output_8th.columns].drop_duplicates()
                
                model_output_comparison = pd.concat([model_output_8th, model_output_all], axis=0)
                value_col_comparison = ['Energy', 'Stocks', 'passenger_km','freight_tonne_km']
                
                
                #plot each combination of: one of the value cols and then any number of the categorical cols
                n_categorical_cols = len(categorical_cols)

                # #plot graphs with all economies on one graph
                # for value_col in value_col_comparison:
                #     for i in range(1, n_categorical_cols+1):
                #         for combo in itertools.combinations(categorical_cols, i):
                #             title = f'{value_col} by {combo} - {scenario}'
                #             save_folder = f'{default_save_folder}/{dataframe_name}/{value_col}/line'

                #             plot_line_by_economy(model_output_comparison, color_categories=list(combo), y_column=value_col, title=title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS, plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, facet_col='Dataset', PLOT=PLOT)
                #             print(f'plotting {value_col} by {combo}')
                            
                #             save_folder = f'{default_save_folder}/{dataframe_name}/{value_col}/area'
                #             plot_area_by_economy(model_output_comparison, color_categories=list(combo), y_column=value_col, title=title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS, plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, facet_col='Dataset', PLOT=PLOT)
                #then plot plot by economy
                
                for economy_x in model_output_comparison['Economy'].unique():
                    for value_col in value_col_comparison:
                        
                        for i in range(1, n_categorical_cols+1):
                            for combo in itertools.combinations(categorical_cols, i):
                                # # Add 'Fuel' to the combo
                                # combo = list(combo) + ['Fuel']

                                title = f'Comparison - {value_col} by {list(combo)} - {scenario}'
                                save_folder = f'{default_save_folder}/{dataframe_name}/{economy_x}/{value_col}/line/'
                                                        
                                #filter for that ecovnomy only and then plot
                                model_output_comparison_economy = model_output_comparison[model_output_comparison['Economy'] == economy_x].copy()
                            
                                plot_line_by_economy(model_output_comparison_economy, color_categories=list(combo), y_column=value_col, title=title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS, plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, facet_col='Dataset', PLOT=plot_comparisons)
                                
                                save_folder = f'{default_save_folder}/{dataframe_name}/{economy_x}/{value_col}/area'
                                
                                # if value_col=='Stocks':#doesnt work with stocks for osmoe reason. tried ot fix it., 
                                #     breakpoint()
                                plot_area_by_economy(model_output_comparison_economy, color_categories=list(combo), y_column=value_col, title=title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS, plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, facet_col='Dataset', PLOT=plot_comparisons)
                            
                                
                                
            end_timer(start, dataframe_name, do_this)

        
        ##################################################################
        ###########################plot 'act growth'############
        ##################################################################
        do_this = True
                    
        dataframe_name = 'macro'
        start = start_timer(dataframe_name,do_this)
        if do_this:
                
            #todo, this might be better than above now. except cum growth could be good?
            #seperate individual macro observations so the graphs dont show sums or avgs of them. To do this, seperate a df for economy only and then drop all cols except economy date, and trasnsport type. Then drop all duplciates. Then plot
            macro_cols_new = macro_cols.copy()
            macro_cols_new.remove('Activity_growth')
            macro = model_output_detailed[['Economy', 'Date']+macro_cols_new].drop_duplicates()
            #now plot 
            #save copy of data as pickle for use in recreating plots. put it in save_folder
            if save_pickle:
                macro.to_pickle(f'{default_save_folder}/{dataframe_name}.pkl')
                print(f'{dataframe_name} saved as pickle')

            #for each economy plot a single graph and then plot all on one graph
            for economy_x in macro['Economy'].unique():
                for measure in macro_cols_new:
                    value_col = measure
                    title = f'{measure} for {economy_x} - {scenario}'
                    save_folder = f'{default_save_folder}/{dataframe_name}/{economy_x}/{value_col}'
                                                
                    #filter for that ecovnomy only and then plot
                    macro_econ = macro[macro['Economy'] == economy_x].copy()
                    plot_line_by_economy(macro_econ, color_categories= ['Economy'], y_column=value_col, title=title,  save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, facet_col=None,dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
                    print(f'plotting {value_col}')
        end_timer(start, dataframe_name, do_this)

        do_this = True
        dataframe_name = 'activity_growth'
        start = start_timer(dataframe_name,do_this)
        if do_this:
            
            activity_growth = model_output_detailed.copy()[['Economy', 'Date','Medium' , 'Transport Type', 'Activity_growth']].drop_duplicates()
            #drop economy=all
            activity_growth = activity_growth[activity_growth['Economy'] != 'all']
            activity_growth['Activity_growth'] = activity_growth['Activity_growth'] + 1
            activity_growth['cumulative_activity_growth'] = activity_growth.groupby(['Economy','Transport Type'])['Activity_growth'].cumprod()
            activity_growth = activity_growth[activity_growth['Date'] != activity_growth['Date'].min()]
            #save copy of data as pickle for use in recreating plots. put it in save_folder
            if save_pickle:
                activity_growth.to_pickle(f'{default_save_folder}/{dataframe_name}.pkl')
                print(f'{dataframe_name} saved as pickle')

            #for each economy plot a single graph and then plot all on one graph
            for value_col in ['cumulative_activity_growth', 'Activity_growth']:
                for economy_x in activity_growth['Economy'].unique():
                    
                    title = f'{value_col} for {economy_x} - {scenario}'
                    save_folder = f'{default_save_folder}/{dataframe_name}/{economy_x}/{value_col}'
                                                
                    #filter for that ecovnomy only and then plot
                    activity_growth_econ = activity_growth[activity_growth['Economy'] == economy_x].copy()
                    
                    plot_line_by_economy(activity_growth_econ, color_categories= ['Economy', 'Medium'], y_column=value_col, title=title,  save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, facet_col='Transport Type',dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
                    print(f'plotting {value_col}')
            # 'Medium' , 'Transport Type'
            #plot all in on egraph
            
            #filter for road medium omnly to reduce clutter
            activity_growth = activity_growth[activity_growth['Medium'] == 'road']

            for value_col in ['cumulative_activity_growth', 'Activity_growth']:
                title = f'{value_col}  for all economies - {scenario}'
                save_folder = f'{default_save_folder}/{dataframe_name}/{value_col}'

            
                plot_line_by_economy(activity_growth, color_categories= ['Economy'], y_column=value_col, title=title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, facet_col='Transport Type',dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
                print(f'plotting {value_col}')
        end_timer(start, dataframe_name, do_this)
        ##################################################################
        do_this = True
        
        dataframe_name = 'model_output_detailed_intensity'
        start = start_timer(dataframe_name+' with all economies on one graph',do_this)
        if do_this:
            #calcualte intensity of road transport
            #do this by dividing energy by activity
            model_output_detailed_int = model_output_detailed.copy()
            
            model_output_detailed_int['Activity'] = model_output_detailed_int['passenger_km']  + model_output_detailed_int['freight_tonne_km']
            #sum activity and energy by medium, transport type and vehicle type.
            model_output_detailed_int = model_output_detailed_int.groupby(['Economy', 'Medium', 'Transport Type', 'Vehicle Type', 'Date']).sum().reset_index() 
            model_output_detailed_int['new_energy_intensity'] = model_output_detailed_int['Energy'] / model_output_detailed_int['Activity']
            
            #replace nans
            model_output_detailed_int['new_energy_intensity'] = model_output_detailed_int['new_energy_intensity'].fillna(0)
            
            #plot graphs with all economies on one graph
            new_categorical_cols = ['Medium', 'Transport Type', 'Vehicle Type']
            new_n_categorical_cols = len(new_categorical_cols)
            new_value_cols = ['new_energy_intensity']#'Intensity',

            
            for value_col in new_value_cols:
                for i in range(1, new_n_categorical_cols+1):
                    for combo in itertools.combinations(new_categorical_cols, i):
                        title = f'{value_col} by {combo} - {scenario}'
                        
                        save_folder = f'{default_save_folder}/{dataframe_name}/all_economies_plot/{value_col}'

                        plot_line_by_economy(model_output_detailed_int, color_categories= list(combo),y_column=value_col, title=title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, facet_col='Economy',dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
                        print(f'plotting {value_col} by {combo}')
        end_timer(start, dataframe_name+' with all economies on one graph', do_this)


#%%

# plot_all_graphs(ECONOMY_ID='19_THA', PLOT=True, plot_comparisons=True)#python workflow/plotting_functions/plot_all_graphs.py > plot_all_output.txt 2>&1

#%%



