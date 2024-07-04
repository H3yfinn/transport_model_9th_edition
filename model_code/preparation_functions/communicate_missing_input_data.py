


#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import sys
import re
#################
from .. import utility_functions
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
#load in the transport dataset that contains all data and plot the data coverage usinga  kind of scatterplot. 
#this will allow the user to understand where data is missing and where it is present so that if any errors occur they can find out with ease
def communicate_missing_input_data(config):
    aggregated_model_data = pd.read_csv(config.root_dir + '\\' + 'intermediate_data\\model_inputs\\{}\\aggregated_model_data.csv'.format(config.FILE_DATE_ID))

    #now plot the data available column to see what data is available and what is not using the data coverage plotting style;
    #%%

    #check for duplicates
    duplicates = aggregated_model_data[aggregated_model_data.duplicated()]
    if len(duplicates) > 0:
        print('Duplicates found. Please remove duplicates before proceeding')
        print(duplicates)
        sys.exit()

    #%%
    ################################################################################
    ##PLOTTING##
    ################################################################################
    #to make things easy in the next plotting segment, we will set dataset to  the data_available column if it shows 'data_not_available' or 'row_and_data_not_available'
    aggregated_model_data['Dataset'] = np.where(aggregated_model_data['Data_available'] == 'data_not_available', 'data_not_available', aggregated_model_data['Dataset'])
    aggregated_model_data['Dataset'] = np.where(aggregated_model_data['Data_available'] == 'row_and_data_not_available', 'row_and_data_not_available', aggregated_model_data['Dataset'])

    #and repalce nonspecified with nonspec in 'Medium','Vehicle Type', 'Drive' cols
    aggregated_model_data['Medium'] = np.where(aggregated_model_data['Medium'] == 'nonspecified', 'nonspec', aggregated_model_data['Medium'])
    aggregated_model_data['Vehicle Type'] = np.where(aggregated_model_data['Vehicle Type'] == 'nonspecified', 'nonspec', aggregated_model_data['Vehicle Type'])
    aggregated_model_data['Drive'] = np.where(aggregated_model_data['Drive'] == 'nonspecified', 'nonspec', aggregated_model_data['Drive'])
    #%%

    #SET COLORS AND MARKERS
    #COLORS
    #we are going to want to keep the label colors constant across all subplots. So we will set them now based on the unique index rows in the data
    #get unique index rows
    unique_index_rows = aggregated_model_data.Dataset.unique()
    #set the colors to use using a color map
    colors = plt.get_cmap('tab10')
    #set the number of colors to use
    num_colors = len(unique_index_rows)
    #set the colors to use, making sure that the colors are as different as possible
    colors_to_use = [colors(i) for i in np.linspace(0, 1, num_colors)]

    #plot the colors in case we want to see them
    plot_colors_to_use = True
    if plot_colors_to_use:
        plt.figure()
        plt.title('Colors to use')
        for i, color in enumerate(colors_to_use):
            plt.plot([i], [i], 'o', color=color)
        plt.savefig(config.root_dir + '\\' + 'plotting_output\\plot_data_coverage\\{}_colors_to_use.png'.format(config.FILE_DATE_ID))
        plt.close()

    #assign each color to a unique index row
    color_dict = dict(zip(unique_index_rows, colors_to_use))

    #make both row_and_data_not_available and data not available the same color, and make it grey
    color_dict['row_and_data_not_available'] = 'grey'
    color_dict['data_not_available'] = 'grey'

    #MARKERS
    marker_dict = {'row_and_data_not_available':'x', 'data_not_available':'x','data_available':'o'}
    #%%
    #TO DO CHANGE THE BELOW SO THAT WE HAVE A SCATTERPLOT WHERE 
    # THE Y AXIS IS A CATEGORICAL SCALE OF THE UNIQUE ROWS, 
    # THE X AXIS IS THE YEARS 
    # AND THE DIFFERENT SUBPLOTS ARE THE ECONOMYS. 
    # THEN EACH SAVED PLOT WILL BE FOR A SINGLE MEASURE. 
    # THE COLOR OF THE MARKER WILL BE:
    # LIGHT GREY IF DATA_AVAILABLE IS FALSE AND THEN FOR THE OTHER DATASETS IT WILL BE A BOLDER COLOR WHICH IS DIFFERENT FOR EACH DATASET USED (SO USER INPUT WILL ALWAYS BE A SINGLE COLOR).
    #WE can EVEN make the marker different depending on if DATA_AVAILABLE IS DATA_AVAILABLE or not. For example can use the marker 'o' for not na and 'x' for na
    for scenario in aggregated_model_data['Scenario'].unique():
        #filter for the current scenario
        aggregated_model_data_scenario = aggregated_model_data[aggregated_model_data['Scenario'] == scenario]
        for measure in aggregated_model_data['Measure'].unique():
            for transport_type in aggregated_model_data['Transport Type'].unique():
                #######################
                # Create a figure with 7 rows and 3 columns
                fig, ax = plt.subplots(7, 3,figsize=(40, 40))
                plt.subplots_adjust(wspace=0.2, hspace=0.2)

                #make backgrounbd white
                fig.patch.set_facecolor('white')

                handles_list = []
                labels_list = []

                row = 0
                col = 0

                for i,economy in enumerate(sorted(aggregated_model_data['Economy'].unique())):
                    #Calculate the row and column index for the subplot
                    row = i // 3
                    col = i % 3
                    #subset the data for the current economy and measure
                    current_economy_measure_data = aggregated_model_data_scenario.loc[(aggregated_model_data_scenario['Economy'] == economy) & (aggregated_model_data_scenario['Measure'] == measure) & (aggregated_model_data_scenario['Transport Type'] == transport_type)]
                    
                    #we will be plotting the y axis as the combination of index cols 'Medium','Vehicle Type', 'Drive'. So comboine them with _'s
                    current_economy_measure_data['index_col'] = current_economy_measure_data['Medium'] + '_' + current_economy_measure_data['Vehicle Type'] + '_' + current_economy_measure_data['Drive']

                    #sort
                    current_economy_measure_data = current_economy_measure_data.sort_values(by=['index_col'])

                    #make the index_col the index
                    current_economy_measure_data = current_economy_measure_data.set_index('index_col')

                    #make x axis ticks every year and make sure they are spread out evenly (sometimes there is no data, for which we will just pass)
                    try:
                        ax[row, col].set_xticks(range(current_economy_measure_data.Year.min()-1, current_economy_measure_data.Year.max()+1, 1))
                        ax[row, col].set_xlim([current_economy_measure_data.Year.min()-1, current_economy_measure_data.Year.max()+1])
                    except:
                        pass
                    num_economy_datapoints = len(current_economy_measure_data.Value.dropna())
                    ax[row,col].set_title('{} - {} data points'.format(economy, num_economy_datapoints))
                    # if row != 6:
                    #     #make x labels invisible if not the bottom row
                    #     ax[row,col].set_xticklabels([])
                    if col == 0:
                        #create unit label if on the left column
                        ax[row,col].set_ylabel('(Medium, Vehicle Type, Drive)')


                    #loop through the different datasets in the data and plot the scatter marks for that dataset
                    for dataset in current_economy_measure_data.Dataset.unique():#rows are based on vehicle type medium and drive
                        for data_availability in current_economy_measure_data.Data_available.unique():
                            #get the data for the current row
                            current_row_data = current_economy_measure_data.loc[(current_economy_measure_data['Dataset'] == dataset) & (current_economy_measure_data['Data_available'] == data_availability)]

                            #define the marker based on if there is a value or not
                            marker = marker_dict[data_availability]
                            #define the color based on dataset
                            color = color_dict[dataset]

                            ax[row, col].scatter(current_row_data.Year, current_row_data.index,label=dataset,color=color, marker=marker, s=20)

                            #create a grid in the chart with lines between each tick on each axis
                            ax[row, col].grid(True, which='both', axis='both', color='grey', linestyle='-', linewidth=0.5, alpha=0.5)

                            #get legend handles and labels
                            handles, labels = ax[row, col].get_legend_handles_labels()
                            #add the handles and labels to the list
                            handles_list.extend(handles)
                            labels_list.extend(labels)

                #get number of actual values in the data
                number_of_values = len(aggregated_model_data_scenario.loc[(aggregated_model_data_scenario['Measure'] == measure) & (aggregated_model_data_scenario['Transport Type'] == transport_type), 'Value'].dropna())   

                #Set the title of the figure
                fig.suptitle('{}_{} \nNumber of datapoints: {}'.format(measure,transport_type,number_of_values), fontsize=matplotlib.rcParams['font.size']*2)

                #Create custom legend based on the markers and color_dict and not handles or labels
                #create a list of colors
                colors = [color for color in color_dict.values()]
                colors_datasets = [dataset for dataset in color_dict.keys()]
                #and then a copy of colors_datasets but for markers. it will be 'x' if the dataset is in the marker_dict.keys() and 'o' otherwise
                markers = ['x' if dataset in marker_dict.keys() else 'o' for dataset in color_dict.keys()]
                #create patches for the legend
                patches = [matplotlib.lines.Line2D([0], [0], color=colors[i], label=colors_datasets[i], marker='o') for i in range(len(colors))]
                #add the patches to the legend and make the legend appear in the top right corner and be a bit large
                fig.legend(handles=patches, loc='upper right',  bbox_to_anchor=(0.95, 0.95), fontsize=matplotlib.rcParams['font.size']+1, markerscale=2.5, frameon=False,  title='Dataset', fancybox=True,  ncol=1)
                #, fancybox=True, shadow=True, ncol=5)

                #save the plot with id for the date and the measure. Make the plot really high resolution so that it can be zoomed in on
                if number_of_values == 0:
                    plt.savefig(config.root_dir + '\\' + 'plotting_output\\plot_data_coverage\\NOVALUES_{}_{}_{}_{}_plot.png'.format(config.FILE_DATE_ID, measure, transport_type, scenario))
                else:
                    plt.savefig(config.root_dir + '\\' + 'plotting_output\\plot_data_coverage\\{}_{}_{}_{}_plot.png'.format(config.FILE_DATE_ID, measure, transport_type, scenario))

    #%%

    #lets also communicate the missing datapoints in the data.
    #So how about plotting the number of missing data points in each economy for each measure using a tree plot, which uses similar colors for each measure
    aggregated_model_data['index_col'] = aggregated_model_data['Transport Type'] + '_' + aggregated_model_data['Medium'] + '_' + aggregated_model_data['Vehicle Type'] + '_' + aggregated_model_data['Drive']

    # %matplotlib inline
    #%%
    #plot the user input measures vs other measures
    user_input = pd.read_csv(config.root_dir + '\\' + 'intermediate_data\\model_inputs\\user_inputs_and_growth_rates.csv')
    #loop through the measures
    user_input_measures = user_input.Measure.unique()
    non_user_input_measures = [measure for measure in aggregated_model_data.Measure.unique() if measure not in user_input_measures]

    #put them in a dict
    measures_to_plot = dict()
    measures_to_plot['user_input_measures'] = user_input_measures
    measures_to_plot['non_user_input_measures'] = non_user_input_measures
    #loop through the measures
    for measures_name in measures_to_plot.keys():
        #get the data for the measures
        measures = measures_to_plot[measures_name]
        #filter for the measures
        aggregated_model_data_measures = aggregated_model_data.loc[aggregated_model_data['Measure'].isin(measures)]
        #set the colors to use using a color map
        colors = plt.get_cmap('tab10')
        #set the number of colors to use
        num_colors = len(measures)
        #set the colors to use, making sure that the colors are as different as possible
        colors_to_use_measure = [colors(i) for i in np.linspace(0, 1, num_colors)]

        # unique_index_rows_index_col = aggregated_model_data.index_col.unique()
        # #set the colors to use using a color map
        # colors = plt.get_cmap('tab10')
        # #set the number of colors to use
        # num_colors = len(unique_index_rows_index_col)
        # #set the colors to use, making sure that the colors are as different as possible
        # colors_to_use_index_col = [colors(i) for i in np.linspace(0, 1, num_colors)]

        #plot tree using plotly
        #now check data by creating a visualisation of it
        #for now we'll use a treemap in plotly to visualise the data
        import plotly.express as px
        columns_to_plot =[ 'Economy', 'Measure','index_col']
        #set colors for the plot using colors_to_use_measure and colors_to_use_index_col
        fig = px.treemap(aggregated_model_data_measures, path=columns_to_plot,  color='Measure')#color_discrete_map =colors_to_use_measure,
        #make it bigger
        fig.update_layout(width=1000, height=1000)
        #show it in browser rather than in the notebook
        fig.show()
        fig.write_html("plotting_output\\plot_data_coverage\\missing_data\\all_data_tree_{}.html".format(measures_name))

        columns_to_plot =[ 'Economy', 'Measure','index_col']
        #set colors for the plot using colors_to_use_measure and colors_to_use_index_col
        fig = px.treemap(aggregated_model_data_measures, path=columns_to_plot, color='Measure')#color_discrete_map =colors_to_use_measure, 
        #make it bigger
        fig.update_layout(width=2500, height=1300)
        #show it in browser rather than in the notebook
        fig.show()
        fig.write_html("plotting_output\\plot_data_coverage\\missing_data\\all_data_tree_{}.html".format(measures_name))

        #try a sunburst
        fig = px.sunburst(aggregated_model_data_measures, path=columns_to_plot, color='Measure')#, color_discrete_map =colors_to_use_measure)
        #make it bigger
        fig.update_layout(width=1000, height=1000)
        #show it in browser rather than in the notebook
        fig.show()
        fig.write_html("plotting_output\\plot_data_coverage\\missing_data\\all_data_sun_{}.html".format(measures_name))

        #and make one that can fit on my home screen which will be 1.3 times taller and 3 times wider
        fig = px.sunburst(aggregated_model_data_measures, path=columns_to_plot, color='Measure')#, color_discrete_map =colors_to_use_measure)
        #make it bigger
        fig.update_layout(width=3000, height=2000)
        #show it in browser rather than in the notebook
        fig.write_html("plotting_output\\plot_data_coverage\\missing_data\\all_data_sun_big_{}.html".format(measures_name))

        # %%
