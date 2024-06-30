#plot output
#aim to keep plots so they can handle any output from general_run but there will be somethings that need to be asdjusted easch time so we have many variables you can input
#if things get out of hand then suggest making a new function in a new file
#%%

import pandas as pd
import numpy as np

import plotly.express as px
# pd.options.plotting.backend = "plotly"#set pandas backend to plotly plotting instead of matplotlib
import plotly.io as pio
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook
import plotly.graph_objects as go
import plotly

import warnings

warnings.filterwarnings('ignore', message='Calling int on a single element Series is deprecated')#from line ~190

#%%
def plot_multiplicative_timeseries(data_title, extra_identifier, structure_variables_list,activity_variable,energy_variable='Energy', emissions_variable='Emissions',emissions_divisia=False, time_variable='Year', graph_title='', residual_variable1='Energy intensity', residual_variable2='Emissions intensity', font_size=25,AUTO_OPEN=False, hierarchical=False,output_data_folder='output_data',plotting_output_folder='\\plotting_output\\', INCLUDE_EXTRA_FACTORS_AT_END = False):
    """
    data used by this function:
        
        data_title eg. 'outlook-transport-divisia'
        extra_identifier eg. 'PASSENGER_REF'
        lmdi_output_multiplicative eg. pd.read_csv('output_data\\{}{}_lmdi_output_multiplicative.csv'.format(data_title, extra_identifier))
        lmdi_output_additive = pd.read_csv('output_data\\{}{}_lmdi_output_additive.csv'.format(data_title, extra_identifier))
        emissions_divisia eg. False
        structure_variables_list eg. ['Economy','Vehicle Type', 'Drive']
        graph_title eg. 'Road passenger - Drivers of changes in energy use (Ref)'
        residual_variable1 eg. f'{energy_variable} intensity' - this can be used to make the residual variable a bit more explanatory
        residual_variable2 eg. 'Emissions intensity' - this can be used to make the residual variable a bit more explanatory
        
        INCLUDE_EXTRA_FACTORS_AT_END - if you use this make sure to put the extra columns right at teh end of the df, and so that the next last column is the activity variable
    """
    if emissions_divisia == False and hierarchical == False:
        
        #get data
        lmdi_output_multiplicative = pd.read_csv('{}\\{}{}_multiplicative.csv'.format(output_data_folder,data_title, extra_identifier))

        #remove activity and total energy data from the dataset
        lmdi_output_multiplicative.drop('Total_{}'.format(activity_variable), axis=1, inplace=True)
        lmdi_output_multiplicative.drop('Total {}'.format(energy_variable), axis=1, inplace=True)

        #rename the energy intensity column to residual_variable1
        lmdi_output_multiplicative.rename(columns={'{} intensity'.format(energy_variable):residual_variable1}, inplace=True)
        
        #need to make the data in long format so we have a driver column instead fo a column for each driver:
        mult_plot = pd.melt(lmdi_output_multiplicative, id_vars=[time_variable], var_name='Driver', value_name='Value')

        #create category based on whether data is driver or change in energy use
        mult_plot['Line type'] = mult_plot['Driver'].apply(lambda i: i if i == 'Multiplicative change in {}'.format(energy_variable) else 'Driver')
        #set title

        if graph_title == '':
            title = '{}{} - Multiplicative LMDI'.format(data_title, extra_identifier)
        else:
            title = graph_title
            
        driver_name_list = ['Multiplicative change in {}'.format(energy_variable), 'Activity']+structure_variables_list+[residual_variable1]
        if INCLUDE_EXTRA_FACTORS_AT_END:
            #add extra factors at the end of the graph. this allows for things like calcualting the effect of including the effect of electricity gernation emissions, which are treated as being independent of the other drivers (even though they are not - it would usually change the effect of the other drivers)
            cols_after_total_var = lmdi_output_multiplicative.columns.tolist()[lmdi_output_multiplicative.columns.tolist().index('Multiplicative change in {}'.format(energy_variable))+1:]
            driver_name_list += cols_after_total_var
        #plot
        fig = px.line(mult_plot, x=time_variable, y="Value", color="Driver", line_dash = 'Line type', title=title, category_orders={"Line type":['Multiplicative change in {}'.format(energy_variable), 'Driver'],"Driver":driver_name_list})#,

        fig.update_layout(
            font=dict(
                size=font_size
            )
        )
        plotly.offline.plot(fig, filename=plotting_output_folder + data_title + extra_identifier + '_multiplicative_timeseries.html', auto_open=AUTO_OPEN)
        #fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + data_title + extra_identifier + 'multiplicative_timeseries.png')

    elif emissions_divisia == True and hierarchical == False:
        
        #get data
        lmdi_output_multiplicative = pd.read_csv('{}\\{}{}_multiplicative.csv'.format(output_data_folder,data_title, extra_identifier))
        # lmdi_output_multiplicative = pd.read_csv('output_data\\{}{}_multiplicative.csv'.format(data_title, extra_identifier))

        #remove ' effect' where it is at the end of all column names using regex ($ marks the end of the string)
        lmdi_output_multiplicative.columns = lmdi_output_multiplicative.columns.str.replace(' effect$', '', regex=True)

        #remove activity and total energy/emissions data from the dataset
        lmdi_output_multiplicative.drop('Total_{}'.format(activity_variable), axis=1, inplace=True)
        
        lmdi_output_multiplicative.drop('Total {}'.format(emissions_variable), axis=1, inplace=True)

        #rename the energy intensity column to residual_variable1
        lmdi_output_multiplicative.rename(columns={'{} intensity'.format(energy_variable):residual_variable1}, inplace=True)
        #rename the emissions intensity column to residual_variable2
        lmdi_output_multiplicative.rename(columns={'{} intensity'.format(emissions_variable):residual_variable2}, inplace=True)

        #need to make the data in long format first:
        mult_plot = pd.melt(lmdi_output_multiplicative, id_vars=[time_variable], var_name='Driver', value_name='Value')
        
        #create category based on whether dfata is driver or change in erggy use
        mult_plot['Line type'] = mult_plot['Driver'].apply(lambda i: i if i == 'Multiplicative change in {}'.format(emissions_variable) else 'Driver')

        #set title
        if graph_title == '':
            title = '{}{} - Multiplicative LMDI decomposition of emissions'.format(data_title, extra_identifier)
        else:
            title = graph_title

        driver_name_list = ['Multiplicative change in {}'.format(emissions_variable), 'Activity']+structure_variables_list+[residual_variable1, residual_variable2]
        if INCLUDE_EXTRA_FACTORS_AT_END:
            #add extra factors at the end of the graph. this allows for things like calcualting the effect of including the effect of electricity gernation emissions, which are treated as being independent of the other drivers (even though they are not - it would usually change the effect of the other drivers)
            cols_after_total_var = lmdi_output_multiplicative.columns.tolist()[lmdi_output_multiplicative.columns.tolist().index('Multiplicative change in {}'.format(emissions_variable))+1:]
            driver_name_list += cols_after_total_var
            
        #plot
        fig = px.line(mult_plot, x=time_variable, y="Value", color="Driver", line_dash = 'Line type', title=title, category_orders={"Line type":['Change in {}'.format(emissions_variable), 'Driver'],"Driver":driver_name_list})

        fig.update_layout(
            font=dict(
                size=font_size
            )
        )
        plotly.offline.plot(fig, filename=plotting_output_folder + data_title + extra_identifier + '_multiplicative_timeseries.html',auto_open=AUTO_OPEN)
        #fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + data_title + extra_identifier + 'multiplicative_timeseries.png')
    
    elif emissions_divisia == False and hierarchical == True:
                
        #get data
        lmdi_output_multiplicative = pd.read_csv('{}\\{}{}_multiplicative.csv'.format(output_data_folder,data_title, extra_identifier))

        #remove activity and total energy data from the dataset
        lmdi_output_multiplicative.drop('Total_{}'.format(activity_variable), axis=1, inplace=True)
        lmdi_output_multiplicative.drop('Total {}'.format(energy_variable), axis=1, inplace=True)
        
        #Regardless of the column names, rename data in order of, 'Year', activity_variable, structure_variables_list, residual_variable1, 'Multiplicative change in {}'.format(energy_variable)
        lmdi_output_multiplicative.columns = [time_variable, activity_variable] + structure_variables_list + [residual_variable1, 'Multiplicative change in {}'.format(energy_variable)]

        #create list of driver names in the order we want them to appear in the graph
        driver_list = [activity_variable] + structure_variables_list + [residual_variable1]

        #need to make the data in long format so we have a driver column instead fo a column for each driver:
        mult_plot = pd.melt(lmdi_output_multiplicative, id_vars=[time_variable], var_name='Driver', value_name='Value')

        #create category based on whether data is driver or change in energy use. because we dont want it to show in the graph we will just make driver a double space, and the change in enegry a singel space
        mult_plot['Line type'] = mult_plot['Driver'].apply(lambda i: '' if i == 'Multiplicative change in {}'.format(energy_variable) else ' ')

        #set title
        if graph_title == '':
            title = '{}{} - Multiplicative LMDI'.format(data_title, extra_identifier)
        else:
            title = graph_title

        driver_name_list = ['Multiplicative change in {}'.format(energy_variable)]+driver_list
        if INCLUDE_EXTRA_FACTORS_AT_END:
            #add extra factors at the end of the graph. this allows for things like calcualting the effect of including the effect of electricity gernation emissions, which are treated as being independent of the other drivers (even though they are not - it would usually change the effect of the other drivers)
            cols_after_total_var = lmdi_output_multiplicative.columns.tolist()[lmdi_output_multiplicative.columns.tolist().index('Multiplicative change in {}'.format(energy_variable))+1:]
            driver_name_list += cols_after_total_var
        #plot
        fig = px.line(mult_plot, x=time_variable, y="Value", color="Driver", line_dash = 'Line type',  category_orders={"Line type":['', ' '],"Driver":driver_name_list},title=title)#,

        fig.update_layout(
            font=dict(
                size=font_size
            ),legend_title_text='Line\\Driver')
        #set name of y axis to 'Proportional effect on energy use'
        fig.update_yaxes(title_text='Proportional effect on energy use')

        plotly.offline.plot(fig, filename=plotting_output_folder + data_title + extra_identifier + '_multiplicative_timeseries.html', auto_open=AUTO_OPEN)
        #fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + data_title + extra_identifier + 'multiplicative_timeseries.png')
        
    elif emissions_divisia == True and hierarchical == True:
                
        #get data
        lmdi_output_multiplicative = pd.read_csv('{}\\{}{}_multiplicative.csv'.format(output_data_folder,data_title, extra_identifier))

        #remove activity and total energy data from the dataset
        lmdi_output_multiplicative.drop('Total_{}'.format(activity_variable), axis=1, inplace=True)
        lmdi_output_multiplicative.drop('Total {}'.format(emissions_variable), axis=1, inplace=True)
        
        #Regardless of the column names, rename data in order of, 'Year', activity_variable, structure_variables_list, residual_variable1, 'Multiplicative change in {}'.format(energy_variable)
        lmdi_output_multiplicative.columns = [time_variable, activity_variable] + structure_variables_list + [residual_variable1,residual_variable2, 'Multiplicative change in {}'.format(emissions_variable)]

        #create list of driver names in the order we want them to appear in the graph
        driver_list = [activity_variable] + structure_variables_list + [residual_variable1, residual_variable2]

        #need to make the data in long format so we have a driver column instead fo a column for each driver:
        mult_plot = pd.melt(lmdi_output_multiplicative, id_vars=[time_variable], var_name='Driver', value_name='Value')

        #create category based on whether data is driver or change in emissions use. because we dont want it to show in the graph we will just make driver a double space, and the change in enegry a singel space
        mult_plot['Line type'] = mult_plot['Driver'].apply(lambda i: '' if i == 'Multiplicative change in {}'.format(emissions_variable) else ' ')

        #set title
        if graph_title == '':
            title = '{}{} - Multiplicative LMDI'.format(data_title, extra_identifier)
        else:
            title = graph_title

        driver_name_list = ['Multiplicative change in {}'.format(emissions_variable)]+driver_list
        if INCLUDE_EXTRA_FACTORS_AT_END:
            #add extra factors at the end of the graph. this allows for things like calcualting the effect of including the effect of electricity gernation emissions, which are treated as being independent of the other drivers (even though they are not - it would usually change the effect of the other drivers)
            cols_after_total_var = lmdi_output_multiplicative.columns.tolist()[lmdi_output_multiplicative.columns.tolist().index('Multiplicative change in {}'.format(emissions_variable))+1:]
            driver_name_list += cols_after_total_var
        #plot
        fig = px.line(mult_plot, x=time_variable, y="Value", color="Driver", line_dash = 'Line type',  category_orders={"Line type":['', ' '],"Driver":driver_name_list},title=title)#,

        fig.update_layout(
            font=dict(
                size=font_size
            ),legend_title_text='Line\\Driver')
        #set name of y axis to 'Proportional effect on energy use'
        fig.update_yaxes(title_text='Proportional effect on emissions use')

        plotly.offline.plot(fig, filename=plotting_output_folder + data_title + extra_identifier + '_multiplicative_timeseries.html', auto_open=AUTO_OPEN)
        #fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + data_title + extra_identifier + 'multiplicative_timeseries.png')


def plot_additive_timeseries(data_title, extra_identifier, structure_variables_list,activity_variable,energy_variable='Energy', emissions_variable='Emissions',emissions_divisia=False, time_variable='Year', graph_title='', residual_variable1='Energy intensity', residual_variable2='Emissions intensity', font_size=25,AUTO_OPEN=False, hierarchical=False,output_data_folder='output_data',plotting_output_folder='\\plotting_output\\', INCLUDE_EXTRA_FACTORS_AT_END = False):
    """
    data used by this function:
        
        data_title eg. 'outlook-transport-divisia'
        extra_identifier eg. 'PASSENGER_REF'
        lmdi_output_additive eg. pd.read_csv('output_data\\{}{}_lmdi_output_additive.csv'.format(data_title, extra_identifier))
        lmdi_output_additive = pd.read_csv('output_data\\{}{}_lmdi_output_additive.csv'.format(data_title, extra_identifier))
        emissions_divisia eg. False
        structure_variables_list eg. ['Economy','Vehicle Type', 'Drive']
        graph_title eg. 'Road passenger - Drivers of changes in energy use (Ref)'
        residual_variable1 eg. f'{energy_variable} intensity' - this can be used to make the residual variable a bit more explanatory
        residual_variable2 eg. 'Emissions intensity' - this can be used to make the residual variable a bit more explanatory
        
        INCLUDE_EXTRA_FACTORS_AT_END - if you use this make sure to put the extra columns right at teh end of the df, and so that the next last column is the activity variable
    """
    if emissions_divisia == False and hierarchical == False:
        
        #get data
        lmdi_output_additive = pd.read_csv('{}\\{}{}_additive.csv'.format(output_data_folder,data_title, extra_identifier))

        #remove activity and total energy data from the dataset
        lmdi_output_additive.drop('Total_{}'.format(activity_variable), axis=1, inplace=True)
        lmdi_output_additive.drop('Total {}'.format(energy_variable), axis=1, inplace=True)

        #rename the energy intensity column to residual_variable1
        lmdi_output_additive.rename(columns={'{} intensity'.format(energy_variable):residual_variable1}, inplace=True)
        
        #need to make the data in long format so we have a driver column instead fo a column for each driver:
        mult_plot = pd.melt(lmdi_output_additive, id_vars=[time_variable], var_name='Driver', value_name='Value')

        #create category based on whether data is driver or change in energy use
        mult_plot['Line type'] = mult_plot['Driver'].apply(lambda i: i if i == 'additive change in {}'.format(energy_variable) else 'Driver')
        #set title

        if graph_title == '':
            title = '{}{} - additive LMDI'.format(data_title, extra_identifier)
        else:
            title = graph_title
            
        driver_name_list = ['Change in {}'.format(energy_variable), 'Activity']+structure_variables_list+[residual_variable1]
        if INCLUDE_EXTRA_FACTORS_AT_END:
            #add extra factors at the end of the graph. this allows for things like calcualting the effect of including the effect of electricity gernation emissions, which are treated as being independent of the other drivers (even though they are not - it would usually change the effect of the other drivers)
            cols_after_total_var = lmdi_output_additive.columns.tolist()[lmdi_output_additive.columns.tolist().index('Change in {}'.format(energy_variable))+1:]
            breakpoint()#will this work
            driver_name_list += cols_after_total_var
        #plot
        fig = px.line(mult_plot, x=time_variable, y="Value", color="Driver", line_dash = 'Line type', title=title, category_orders={"Line type":['additive change in {}'.format(energy_variable), 'Driver'],"Driver":driver_name_list})#,

        fig.update_layout(
            font=dict(
                size=font_size
            )
        )
        plotly.offline.plot(fig, filename=plotting_output_folder + data_title + extra_identifier + '_additive_timeseries.html', auto_open=AUTO_OPEN)
        #fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + data_title + extra_identifier + 'additive_timeseries.png')

    elif emissions_divisia == True and hierarchical == False:
        
        #get data
        lmdi_output_additive = pd.read_csv('{}\\{}{}_additive.csv'.format(output_data_folder,data_title, extra_identifier))
        # lmdi_output_additive = pd.read_csv('output_data\\{}{}_additive.csv'.format(data_title, extra_identifier))

        #remove ' effect' where it is at the end of all column names using regex ($ marks the end of the string)
        lmdi_output_additive.columns = lmdi_output_additive.columns.str.replace(' effect$', '', regex=True)

        #remove activity and total energy/emissions data from the dataset
        lmdi_output_additive.drop('Total_{}'.format(activity_variable), axis=1, inplace=True)
        lmdi_output_additive.drop('Total {}'.format(emissions_variable), axis=1, inplace=True)

        #rename the energy intensity column to residual_variable1
        lmdi_output_additive.rename(columns={'{} intensity'.format(energy_variable):residual_variable1}, inplace=True)
        #rename the emissions intensity column to residual_variable2
        lmdi_output_additive.rename(columns={'{} intensity'.format(emissions_variable):residual_variable2}, inplace=True)

        #need to make the data in long format first:
        mult_plot = pd.melt(lmdi_output_additive, id_vars=[time_variable], var_name='Driver', value_name='Value')
        
        #create category based on whether dfata is driver or change in erggy use
        mult_plot['Line type'] = mult_plot['Driver'].apply(lambda i: i if i == 'additive change in {}'.format(emissions_variable) else 'Driver')

        #set title
        if graph_title == '':
            title = '{}{} - additive LMDI decomposition of emissions'.format(data_title, extra_identifier)
        else:
            title = graph_title

        driver_name_list = ['additive change in {}'.format(emissions_variable), 'Activity']+structure_variables_list+[residual_variable1, residual_variable2]
        if INCLUDE_EXTRA_FACTORS_AT_END:
            #add extra factors at the end of the graph. this allows for things like calcualting the effect of including the effect of electricity gernation emissions, which are treated as being independent of the other drivers (even though they are not - it would usually change the effect of the other drivers)
            cols_after_total_var = lmdi_output_additive.columns.tolist()[lmdi_output_additive.columns.tolist().index('additive change in {}'.format(emissions_variable))+1:]
            driver_name_list += cols_after_total_var
            
        #plot
        fig = px.line(mult_plot, x=time_variable, y="Value", color="Driver", line_dash = 'Line type', title=title, category_orders={"Line type":['Change in {}'.format(emissions_variable), 'Driver'],"Driver":driver_name_list})

        fig.update_layout(
            font=dict(
                size=font_size
            )
        )
        plotly.offline.plot(fig, filename=plotting_output_folder + data_title + extra_identifier + '_additive_timeseries.html',auto_open=AUTO_OPEN)
        #fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + data_title + extra_identifier + 'additive_timeseries.png')
    
    elif emissions_divisia == False and hierarchical == True:
                
        #get data
        lmdi_output_additive = pd.read_csv('{}\\{}{}_additive.csv'.format(output_data_folder,data_title, extra_identifier))

        #if there is a row in the minimum year that contains nans in the effects columns, then remove it. We get this because of the way additive df is created to include the total energy and activity data from the year before the effects are recorded (we record effects in the year that that effect is felt, so the first year in the df will always have nans in the effects columns if we include it)
        effects = [col for col in lmdi_output_additive.columns if ' effect' in col]
        if lmdi_output_additive[lmdi_output_additive[time_variable] == lmdi_output_additive[time_variable].min()][effects].isnull().values.all():
            lmdi_output_additive = lmdi_output_additive[lmdi_output_additive[time_variable] != lmdi_output_additive[time_variable].min()]
            
        #remove activity and total energy data from the dataset
        lmdi_output_additive.drop('Total_{}'.format(activity_variable), axis=1, inplace=True)
        lmdi_output_additive.drop('Total {}'.format(energy_variable), axis=1, inplace=True)
        
        #Regardless of the column names, rename data in order of, 'Year', activity_variable, structure_variables_list, residual_variable1, 'additive change in {}'.format(energy_variable)
        lmdi_output_additive.columns = [time_variable, activity_variable] + structure_variables_list + [residual_variable1, 'additive change in {}'.format(energy_variable)]

        #create list of driver names in the order we want them to appear in the graph
        driver_list = [activity_variable] + structure_variables_list + [residual_variable1]

        #need to make the data in long format so we have a driver column instead fo a column for each driver:
        mult_plot = pd.melt(lmdi_output_additive, id_vars=[time_variable], var_name='Driver', value_name='Value')

        #create category based on whether data is driver or change in energy use. because we dont want it to show in the graph we will just make driver a double space, and the change in enegry a singel space
        mult_plot['Line type'] = mult_plot['Driver'].apply(lambda i: '' if i == 'additive change in {}'.format(energy_variable) else ' ')

        #set title
        if graph_title == '':
            title = '{}{} - additive LMDI'.format(data_title, extra_identifier)
        else:
            title = graph_title

        driver_name_list = ['additive change in {}'.format(energy_variable)]+driver_list
        if INCLUDE_EXTRA_FACTORS_AT_END:
            #add extra factors at the end of the graph. this allows for things like calcualting the effect of including the effect of electricity gernation emissions, which are treated as being independent of the other drivers (even though they are not - it would usually change the effect of the other drivers)
            cols_after_total_var = lmdi_output_additive.columns.tolist()[lmdi_output_additive.columns.tolist().index('additive change in {}'.format(energy_variable))+1:]
            driver_name_list += cols_after_total_var
        #plot
        fig = px.line(mult_plot, x=time_variable, y="Value", color="Driver", line_dash = 'Line type',  category_orders={"Line type":['', ' '],"Driver":driver_name_list},title=title)#,

        fig.update_layout(
            font=dict(
                size=font_size
            ),legend_title_text='Line\\Driver')
        #set name of y axis to 'Proportional effect on energy use'
        fig.update_yaxes(title_text='Proportional effect on energy use')

        plotly.offline.plot(fig, filename=plotting_output_folder + data_title + extra_identifier + '_additive_timeseries.html', auto_open=AUTO_OPEN)
        #fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + data_title + extra_identifier + 'additive_timeseries.png')
    
    elif emissions_divisia == True and hierarchical == True:
                
        #get data
        lmdi_output_additive = pd.read_csv('{}\\{}{}_additive.csv'.format(output_data_folder,data_title, extra_identifier))

        #if there is a row in the minimum year that contains nans in the effects columns, then remove it. We get this because of the way additive df is created to include the total energy and activity data from the year before the effects are recorded (we record effects in the year that that effect is felt, so the first year in the df will always have nans in the effects columns if we include it)
        effects = [col for col in lmdi_output_additive.columns if ' effect' in col]
        if lmdi_output_additive[lmdi_output_additive[time_variable] == lmdi_output_additive[time_variable].min()][effects].isnull().values.all():
            lmdi_output_additive = lmdi_output_additive[lmdi_output_additive[time_variable] != lmdi_output_additive[time_variable].min()]
            
        #remove activity and total energy data from the dataset
        lmdi_output_additive.drop('Total_{}'.format(activity_variable), axis=1, inplace=True)
        lmdi_output_additive.drop('Total {}'.format(emissions_variable), axis=1, inplace=True)
        
        #Regardless of the column names, rename data in order of, 'Year', activity_variable, structure_variables_list, residual_variable1, 'additive change in {}'.format(emissions_variable)
        lmdi_output_additive.columns = [time_variable, activity_variable] + structure_variables_list + [residual_variable1,residual_variable2, 'additive change in {}'.format(emissions_variable)]

        #create list of driver names in the order we want them to appear in the graph
        driver_list = [activity_variable] + structure_variables_list + [residual_variable1, residual_variable2]

        #need to make the data in long format so we have a driver column instead fo a column for each driver:
        mult_plot = pd.melt(lmdi_output_additive, id_vars=[time_variable], var_name='Driver', value_name='Value')

        #create category based on whether data is driver or change in energy use. because we dont want it to show in the graph we will just make driver a double space, and the change in enegry a singel space
        mult_plot['Line type'] = mult_plot['Driver'].apply(lambda i: '' if i == 'additive change in {}'.format(emissions_variable) else ' ')

        #set title
        if graph_title == '':
            title = '{}{} - additive LMDI'.format(data_title, extra_identifier)
        else:
            title = graph_title

        driver_name_list = ['additive change in {}'.format(emissions_variable)]+driver_list
        if INCLUDE_EXTRA_FACTORS_AT_END:
            #add extra factors at the end of the graph. this allows for things like calcualting the effect of including the effect of electricity gernation emissions, which are treated as being independent of the other drivers (even though they are not - it would usually change the effect of the other drivers)
            cols_after_total_var = lmdi_output_additive.columns.tolist()[lmdi_output_additive.columns.tolist().index('additive change in {}'.format(emissions_variable))+1:]
            driver_name_list += cols_after_total_var
        #plot
        fig = px.line(mult_plot, x=time_variable, y="Value", color="Driver", line_dash = 'Line type',  category_orders={"Line type":['', ' '],"Driver":driver_name_list},title=title)#,

        fig.update_layout(
            font=dict(
                size=font_size
            ),legend_title_text='Line\\Driver')
        #set name of y axis to 'Proportional effect on emissions use'
        fig.update_yaxes(title_text='Proportional effect on emissions')

        plotly.offline.plot(fig, filename=plotting_output_folder + data_title + extra_identifier + '_additive_timeseries.html', auto_open=AUTO_OPEN)
        #fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + data_title + extra_identifier + 'additive_timeseries.png')


    
#%%
######################################################
######################################################

            
def plot_additive_waterfall(data_title, extra_identifier, structure_variables_list, activity_variable,energy_variable='Energy', emissions_variable='Emissions',emissions_divisia=False, time_variable='Year', graph_title='', residual_variable1='Energy intensity', residual_variable2='Emissions intensity', font_size=25,y_axis_min_percent_decrease=0.9,AUTO_OPEN=False, hierarchical=False, output_data_folder='output_data', plotting_output_folder='plotting_output', INCLUDE_TEXT = False, INCLUDE_EXTRA_FACTORS_AT_END = False, PLOT_CUMULATIVE_VERSION=False):
    """
    data used by this function:
        
        data_title eg. 'outlook-transport-divisia'
        extra_identifier eg. 'PASSENGER_REF'
        lmdi_output_multiplicative eg. pd.read_csv('output_data\\{}{}_lmdi_output_multiplicative.csv'.format(data_title, extra_identifier))
        lmdi_output_additive = pd.read_csv('output_data\\{}{}_lmdi_output_additive.csv'.format(data_title, extra_identifier))
        emissions_divisia eg. False
        structure_variables_list eg. ['Economy','Vehicle Type', 'Drive']
        graph_title eg. 'Road passenger - Drivers of changes in energy use (Ref)'
        residual_variable1 eg. 'Energy intensity' - this can be used to make the residual variable a bit more explanatory
        residual_variable2 eg. 'Emissions intensity' - this can be used to make the residual variable a bit more explanatory
        
        INCLUDE_EXTRA_FACTORS_AT_END - if you use this make sure to put the extra columns right at teh end of the df, and so that the next last column is the activity variable
    """
    #take in teh data and accumulate it so we can view the accumulated effects:
    #calculate the accumulated value of each column except the date column
    def calculate_accumulated_values_for_cumulative_version_of_graph(lmdi_output_additive, time_variable):
        # Exclude the time variable from the columns to calculate cumulative sum
        columns_to_accumulate = [col for col in lmdi_output_additive.columns if col != time_variable]

        # Calculate cumulative sum for each column and update the DataFrame in place
        for col in columns_to_accumulate:
            lmdi_output_additive[col] = lmdi_output_additive.sort_values(by=time_variable)[col].cumsum()

        return lmdi_output_additive
        
    if emissions_divisia == False and hierarchical == False:
        
        lmdi_output_additive = pd.read_csv('{}\\{}{}_additive.csv'.format(output_data_folder,data_title, extra_identifier))

        if PLOT_CUMULATIVE_VERSION:
            lmdi_output_additive = calculate_accumulated_values_for_cumulative_version_of_graph(lmdi_output_additive, time_variable)
        
        #remove activity data from the dataset
        lmdi_output_additive.drop('Total_{}'.format(activity_variable), axis=1, inplace=True)

        #remove ' effect' where it is at the end of all column names using regex ($ marks the end of the string)
        lmdi_output_additive.columns = lmdi_output_additive.columns.str.replace(' effect$', '', regex=True)
        
        #replace 'Energy intensity' with residual_variable1
        lmdi_output_additive.columns = lmdi_output_additive.columns.str.replace(f'{energy_variable} intensity', residual_variable1)

        #format data for waterfall plot
        #use the latest year, and the energy value for the first year
        beginning_year = lmdi_output_additive[time_variable].min()
        final_year = lmdi_output_additive[time_variable].max()
        add_plot_first_year_energy = lmdi_output_additive[lmdi_output_additive[time_variable] == beginning_year]['Total {}'.format(energy_variable)].values[0]
        add_plot = lmdi_output_additive[lmdi_output_additive[time_variable] == final_year]

        #set where the base for the y axis of the graph will begin 
        base_amount =  add_plot_first_year_energy * y_axis_min_percent_decrease
        #create a 'relative' vlaue  in the list for each driver in the dataset. to count the number of drivers, we can use the number of structure variables + 2 (activity and 2xresidual)
        measure_list = ['absolute'] + ['relative'] * (len(structure_variables_list) + 2) + ['total']

        if graph_title == '':
            title = '{}{} - Additive LMDI'.format(data_title, extra_identifier)
        else:
            title = graph_title

        y = [add_plot_first_year_energy-base_amount, 
        add_plot[activity_variable].iloc[0]] + add_plot[structure_variables_list].iloc[0].tolist() + [add_plot[residual_variable1].iloc[0],
        add_plot["Total {}".format(energy_variable)].iloc[0]]
        x = [str(beginning_year) + ' {}'.format(energy_variable),
        activity_variable] + structure_variables_list + [residual_variable1,
        str(final_year)+' {}'.format(energy_variable)]
        if INCLUDE_TEXT:
            text = [
                str(int(add_plot_first_year_energy.round(0))), 
                str(int(add_plot[activity_variable].round(0).iloc[0]))
            ] + [str(int(add_plot[var].round(0).iloc[0])) for var in structure_variables_list] + [
                str(int(add_plot[residual_variable1].round(0).iloc[0])), 
                str(int(add_plot["Total {}".format(energy_variable)].round(0).iloc[0]))
            ]
        else:
            text = None
            
        if INCLUDE_EXTRA_FACTORS_AT_END:
            #add extra factors at the end of the graph. this allows for things like calcualting the effect of including the effect of electricity gernation emissions, which are treated as being independent of the other drivers (even though they are not - it would usually change the effect of the other drivers)
            cols_after_total_var = lmdi_output_additive.columns.tolist()[lmdi_output_additive.columns.tolist().index('Total {}'.format(energy_variable))+1:]
            measure_list += ['relative'] * len(cols_after_total_var)
            y += add_plot[cols_after_total_var].iloc[0].tolist()
            x += cols_after_total_var
            text += [str(int(add_plot[var].round(0).iloc[0])) for var in cols_after_total_var]
            
        
        fig = go.Figure(go.Waterfall(
            orientation = "v",
            measure = measure_list,
            base = base_amount,

            x = x,

            textposition = "outside",

            #can add text to the waterfall plot here to show the values of the drivers
            text = text,

            y = y,

            decreasing = {"marker":{"color":"#377eb8"}},
            increasing = {"marker":{"color":"#ff7f00"}},
            totals = {"marker":{"color":"#787878"}}
        ))

        fig.update_layout(
                title = title,
                font=dict(
                size=font_size
            ), waterfallgap = 0.01
        )
        
        #create unit for y axis
        fig.update_yaxes(title_text='PJ')
        #add a slight slant to the x axis labels
        fig.update_xaxes(tickangle=25)
        
        plotly.offline.plot(fig, filename=plotting_output_folder + data_title + extra_identifier + '.html',auto_open=AUTO_OPEN)
        #fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + data_title + extra_identifier + '.png')

    elif emissions_divisia  == True and hierarchical == False:
        #this is for emissions plot:
        lmdi_output_additive = pd.read_csv('{}\\{}{}_additive.csv'.format(output_data_folder,data_title, extra_identifier))
        
        if PLOT_CUMULATIVE_VERSION:
            lmdi_output_additive = calculate_accumulated_values_for_cumulative_version_of_graph(lmdi_output_additive, time_variable)
        
        #remove activity data from the dataset
        lmdi_output_additive.drop('Total_{}'.format(activity_variable), axis=1, inplace=True)

        #remove ' effect' where it is at the end of all column names using regex ($ marks the end of the string)
        lmdi_output_additive.columns = lmdi_output_additive.columns.str.replace(' effect$', '', regex=True)

        #replace f'{energy_variable} intensity' with residual_variable1
        lmdi_output_additive.columns = lmdi_output_additive.columns.str.replace(f'{energy_variable} intensity', residual_variable1)
        #replace 'Emissions intensity' with residual_variable2
        lmdi_output_additive.columns = lmdi_output_additive.columns.str.replace('Emissions intensity', residual_variable2)
        
        #format data for waterfall plot
        #use the latest year, and the energy value for the first year
        beginning_year = lmdi_output_additive[time_variable].min()
        final_year = lmdi_output_additive[time_variable].max()
        
        add_plot_first_year_emissions = lmdi_output_additive[lmdi_output_additive[time_variable] == beginning_year]['Total {}'.format(emissions_variable)].values[0]
        add_plot = lmdi_output_additive[lmdi_output_additive[time_variable] == final_year]

        #set where the base for the y axis of the graph will begin 
        base_amount =  add_plot_first_year_emissions * y_axis_min_percent_decrease
        #create a 'relative' vlaue  in the list for each driver in the dataset. to count the number of drivers, we can use the number of structure variables + 2 (activity and 2xresidual)
        measure_list = ['absolute'] + ['relative'] * (len(structure_variables_list) + 3) + ['total']

        if graph_title == '':
            title = '{}{} - Additive LMDI'.format(data_title, extra_identifier)
        else:
            title = graph_title
            
        x = [str(beginning_year) + ' {}'.format(emissions_variable),
            activity_variable] + structure_variables_list + [residual_variable1,residual_variable2,
            str(final_year)+' {}'.format(emissions_variable)]
        y = [add_plot_first_year_emissions-base_amount, 
            add_plot[activity_variable].iloc[0]] + add_plot[structure_variables_list].iloc[0].tolist() + [add_plot[residual_variable1].iloc[0], 
            add_plot[residual_variable2].iloc[0],
            add_plot["Total {}".format(emissions_variable)].iloc[0]-base_amount]
            
        if INCLUDE_EXTRA_FACTORS_AT_END:
            #add extra factors at the end of the graph. this allows for things like calcualting the effect of including the effect of electricity gernation emissions, which are treated as being independent of the other drivers (even though they are not - it would usually change the effect of the other drivers)
            
            cols_after_total_var = lmdi_output_additive.columns.tolist()[lmdi_output_additive.columns.tolist().index('Total {}'.format(emissions_variable))+1:]
            measure_list += ['relative'] * len(cols_after_total_var)
            y += add_plot[cols_after_total_var].iloc[0].tolist()
            x += cols_after_total_var
            # text += [str(int(add_plot[var].round(0).iloc[0])) for var in cols_after_total_var]
            
        fig = go.Figure(go.Waterfall(
            orientation = "v",
            measure = measure_list,
            base = base_amount,

            x = x,

            textposition = "outside",

            #can add text to the waterfall plot here to show the values of the drivers
            # text = [int(add_plot_first_year_energy), 
            # str(int(add_plot["Activity"].round(0).iloc[0])), 
            # str(int(add_plot[structure_variable].round(0).iloc[0])),
            # str(int(add_plot["Energy intensity"].round(0).iloc[0])), 
            # str(int(add_plot["Energy"].round(0).iloc[0]))],

            y = y,

            decreasing = {"marker":{"color":"#377eb8"}},
            increasing = {"marker":{"color":"#ff7f00"}},
            totals = {"marker":{"color":"#787878"}}
        ))

        fig.update_layout(
                title = title,
                font=dict(
                size=font_size
            ), waterfallgap = 0.01
        )

        #create unit for y axis
        fig.update_yaxes(title_text='MtCO2')
        
        plotly.offline.plot(fig, filename=plotting_output_folder + data_title + extra_identifier + '.html',auto_open=AUTO_OPEN)
        #fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + data_title + extra_identifier + '.png')

    elif emissions_divisia == False and hierarchical == True: 
        lmdi_output_additive = pd.read_csv('{}\\{}{}_additive.csv'.format(output_data_folder,data_title, extra_identifier))

        if PLOT_CUMULATIVE_VERSION:
            lmdi_output_additive = calculate_accumulated_values_for_cumulative_version_of_graph(lmdi_output_additive, time_variable)
        
        #remove activity data from the dataset
        lmdi_output_additive.drop('Total_{}'.format(activity_variable), axis=1, inplace=True)
        #drop additive change in energy from the dataset
        try:
            lmdi_output_additive.drop('Additive change in {}'.format(energy_variable), axis=1, inplace=True)
        except:
            breakpoint()
        
        #remove ' effect' where it is at the end of all column names using regex ($ marks the end of the string)
        lmdi_output_additive.columns = lmdi_output_additive.columns.str.replace(' effect$', '', regex=True)
        
        #somewhere in the code we name the residual variable with 'intensity' in name so we need to replace that with residual_variable1.
        if '{} intensity'.format(structure_variables_list[-1]) not in lmdi_output_additive.columns:
            breakpoint()
            print('WARNING: {} intensity not in columns of lmdi_output_additive. This may cause a mistake in the plotting of the hierarchical additive waterfall plot.'.format(structure_variables_list[-1]))
        lmdi_output_additive.columns = lmdi_output_additive.columns.str.replace('{} intensity'.format(structure_variables_list[-1]), residual_variable1)
         
        #format data for waterfall plot
        #use the latest year, and the energy value for the first year
        beginning_year = lmdi_output_additive[time_variable].min()
        final_year = lmdi_output_additive[time_variable].max()
        add_plot_first_year_energy = lmdi_output_additive[lmdi_output_additive[time_variable] == beginning_year]['Total {}'.format(energy_variable)].values[0]
        add_plot = lmdi_output_additive[lmdi_output_additive[time_variable] == final_year]

        #set where the base for the y axis of the graph will begin 
        base_amount =  add_plot_first_year_energy * y_axis_min_percent_decrease
        #create a 'relative' vlaue  in the list for each driver in the dataset. to count the number of drivers, we can use the number of structure variables + 2 (activity and 2xresidual)
        measure_list = ['absolute'] + ['relative'] * (len(structure_variables_list) + 2) + ['total']

        if graph_title == '':
            title = '{}{} - Additive hierarchical LMDI'.format(data_title, extra_identifier)
        else:
            title = graph_title
        
        y = [add_plot_first_year_energy-base_amount, 
        add_plot[activity_variable].iloc[0]] + add_plot[structure_variables_list].iloc[0].tolist() + [add_plot[residual_variable1].iloc[0],
        add_plot["Total {}".format(energy_variable)].iloc[0]]
        x = [str(beginning_year) + ' {}'.format(energy_variable),
        activity_variable] + structure_variables_list + [residual_variable1,
        str(final_year)+' {}'.format(energy_variable)]
        if INCLUDE_TEXT:
            text = [
                str(int(add_plot_first_year_energy.round(0))), 
                str(int(add_plot[activity_variable].round(0).iloc[0]))
            ] + [str(int(add_plot[var].round(0).iloc[0])) for var in structure_variables_list] + [
                str(int(add_plot[residual_variable1].round(0).iloc[0])), 
                str(int(add_plot["Total {}".format(energy_variable)].round(0).iloc[0]))
            ]
        else:
            text = None
        
        if INCLUDE_EXTRA_FACTORS_AT_END:
            #add extra factors at the end of the graph. this allows for things like calcualting the effect of including the effect of electricity gernation emissions, which are treated as being independent of the other drivers (even though they are not - it would usually change the effect of the other drivers)
            cols_after_total_var = lmdi_output_additive.columns.tolist()[lmdi_output_additive.columns.tolist().index('Total {}'.format(energy_variable))+1:]
            measure_list += ['relative'] * len(cols_after_total_var)
            y += add_plot[cols_after_total_var].iloc[0].tolist()
            x += cols_after_total_var
            text += [str(int(add_plot[var].round(0).iloc[0])) for var in cols_after_total_var]
        
        fig = go.Figure(go.Waterfall(
            orientation = "v",
            measure = measure_list,
            base = base_amount,

            x = x,

            textposition = "outside",

            #can add text to the waterfall plot here to show the values of the drivers
            text = text,

            y = y,

            decreasing = {"marker":{"color":"#377eb8"}},
            increasing = {"marker":{"color":"#ff7f00"}},
            totals = {"marker":{"color":"#787878"}}
        ))

        fig.update_layout(
                title = title,
                font=dict(
                size=font_size
            ), waterfallgap = 0.01
        )

        #create unit for y axis
        fig.update_yaxes(title_text='PJ')
        #add a slight slant to the x axis labels
        fig.update_xaxes(tickangle=25)
        
        plotly.offline.plot(fig, filename=plotting_output_folder + data_title + extra_identifier +'_additive_hierarchical.html',auto_open=AUTO_OPEN)
        #fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + data_title + extra_identifier + '.png')
    
    
    elif emissions_divisia == True and hierarchical == True: 
        lmdi_output_additive = pd.read_csv('{}\\{}{}_additive.csv'.format(output_data_folder,data_title, extra_identifier))

        if PLOT_CUMULATIVE_VERSION:
            lmdi_output_additive = calculate_accumulated_values_for_cumulative_version_of_graph(lmdi_output_additive, time_variable)
        
        #remove activity data from the dataset
        lmdi_output_additive.drop('Total_{}'.format(activity_variable), axis=1, inplace=True)
        try:
            #drop additive change in energy from the dataset
            lmdi_output_additive.drop('Additive change in {}'.format(emissions_variable), axis=1, inplace=True)
        except:
            breakpoint()
        #remove ' effect' where it is at the end of all column names using regex ($ marks the end of the string)
        lmdi_output_additive.columns = lmdi_output_additive.columns.str.replace(' effect$', '', regex=True)
        
        #somewhere in the code we name the residual variable with 'intensity' in name so we need to replace that with residual_variable1.
        if '{} emissions intensity'.format(structure_variables_list[-1]) not in lmdi_output_additive.columns:
            breakpoint()
            print('WARNING: {} emissions intensity not in columns of lmdi_output_additive. This may cause a mistake in the plotting of the hierarchical additive waterfall plot.'.format(structure_variables_list[-1]))
            
        if '{} energy intensity'.format(structure_variables_list[-1]) not in lmdi_output_additive.columns:
            breakpoint()
            print('WARNING: {} energy intensity not in columns of lmdi_output_additive. This may cause a mistake in the plotting of the hierarchical additive waterfall plot.'.format(structure_variables_list[-1]))
            
        lmdi_output_additive.columns = lmdi_output_additive.columns.str.replace('{} emissions intensity'.format(structure_variables_list[-1]), residual_variable2)
        lmdi_output_additive.columns = lmdi_output_additive.columns.str.replace('{} energy intensity'.format(structure_variables_list[-1]), residual_variable1)
        
        
        #format data for waterfall plot
        #use the latest year, and the energy value for the first year
        beginning_year = lmdi_output_additive[time_variable].min()
        final_year = lmdi_output_additive[time_variable].max()
        add_plot_first_year_emissions = lmdi_output_additive[lmdi_output_additive[time_variable] == beginning_year]['Total {}'.format(emissions_variable)].values[0]
        add_plot = lmdi_output_additive[lmdi_output_additive[time_variable] == final_year]

        #set where the base for the y axis of the graph will begin 
        base_amount =  add_plot_first_year_emissions * y_axis_min_percent_decrease
        #create a 'relative' vlaue  in the list for each driver in the dataset. to count the number of drivers, we can use the number of structure variables + 2 (activity and 2xresidual)
        measure_list = ['absolute'] + ['relative'] * (len(structure_variables_list) + 3) + ['total']

        if graph_title == '':
            title = '{}{} - Additive hierarchical LMDI'.format(data_title, extra_identifier)
        else:
            title = graph_title
        
        y = [add_plot_first_year_emissions-base_amount, 
        add_plot[activity_variable].iloc[0]] + add_plot[structure_variables_list].iloc[0].tolist() + [add_plot[residual_variable1].iloc[0],add_plot[residual_variable2].iloc[0],
        add_plot["Total {}".format(emissions_variable)].iloc[0]]
        x = [str(beginning_year) + ' {}'.format(emissions_variable),
        activity_variable] + structure_variables_list + [residual_variable1,residual_variable2,
        str(final_year)+' {}'.format(emissions_variable)]
        if INCLUDE_TEXT:
            text = [
                str(int(add_plot_first_year_emissions.round(0))), 
                str(int(add_plot[activity_variable].round(0).iloc[0]))
            ] + [str(int(add_plot[var].round(0).iloc[0])) for var in structure_variables_list] + [
                str(int(add_plot[residual_variable1].round(0).iloc[0])), str(int(add_plot[residual_variable2].round(0).iloc[0])),
                str(int(add_plot["Total {}".format(emissions_variable)].round(0).iloc[0]))
            ]
        else:
            text = None
        
        if INCLUDE_EXTRA_FACTORS_AT_END:
            #add extra factors at the end of the graph. this allows for things like calcualting the effect of including the effect of electricity gernation emissions, which are treated as being independent of the other drivers (even though they are not - it would usually change the effect of the other drivers)
            
            cols_after_total_var = lmdi_output_additive.columns.tolist()[lmdi_output_additive.columns.tolist().index('Total {}'.format(emissions_variable))+1:]
            measure_list += ['relative'] * len(cols_after_total_var)
            y += add_plot[cols_after_total_var].iloc[0].tolist()
            x += cols_after_total_var
            text += [str(int(add_plot[var].round(0).iloc[0])) for var in cols_after_total_var]
        
        fig = go.Figure(go.Waterfall(
            orientation = "v",
            measure = measure_list,
            base = base_amount,

            x = x,

            textposition = "outside",

            #can add text to the waterfall plot here to show the values of the drivers
            text = text,

            y = y,

            decreasing = {"marker":{"color":"#377eb8"}},
            increasing = {"marker":{"color":"#ff7f00"}},
            totals = {"marker":{"color":"#787878"}}
        ))

        fig.update_layout(
                title = title,
                font=dict(
                size=font_size
            ), waterfallgap = 0.01
        )

        #create unit for y axis
        fig.update_yaxes(title_text='MtCO2')
        #add a slight slant to the x axis labels
        fig.update_xaxes(tickangle=25)
        
        plotly.offline.plot(fig, filename=plotting_output_folder + data_title + extra_identifier +'_additive_hierarchical.html',auto_open=AUTO_OPEN)
        #fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + data_title + extra_identifier + '.png')
        
        
def concat_waterfall_inputs(data_title,new_extra_identifier, extra_identifiers,activity_variables, new_activity_variable,time_variable='Year',  hierarchical=False, output_data_folder='output_data'):
    """
    This will take in a list of the data titles, extra identifiers, and activity variables and will create a dataframe with all the data in it. The effects will be concatenated together, and the total energy/emissions will be added together. This will then be used to create a waterfall plot. It is important that the number of columns in each dataset is the same.
    
    
    data used by this function:
        
        data_title eg. 'outlook-transport-divisia'
        extra_identifier eg. 'PASSENGER_REF'
        lmdi_output_multiplicative eg. pd.read_csv('output_data\\{}{}_lmdi_output_multiplicative.csv'.format(data_title, extra_identifier))
        lmdi_output_additive = pd.read_csv('output_data\\{}{}_lmdi_output_additive.csv'.format(data_title, extra_identifier))
        emissions_divisia eg. False
        structure_variables_list eg. ['Economy','Vehicle Type', 'Drive']
        graph_title eg. 'Road passenger - Drivers of changes in energy use (Ref)'
        residual_variable1 eg. f'{energy_variable} intensity' - this can be used to make the residual variable a bit more explanatory
        residual_variable2 eg. 'Emissions intensity' - this can be used to make the residual variable a bit more explanatory
    """
    if hierarchical == False:
        lmdi_output_additive = pd.DataFrame()
        for i in range(len(extra_identifiers)):
            extra_identifier_ = extra_identifiers[i]
            activity_variable = activity_variables[i]
            
            lmdi_output_additive_ = pd.read_csv('{}\\{}{}_additive.csv'.format(output_data_folder,data_title, extra_identifier_))
            #rename the activity varaialbe to the new activity variable
            lmdi_output_additive_.rename(columns={activity_variable+' effect':new_activity_variable+' effect'}, inplace=True)
            #and change Total_{activity_variable} to Total_{new_activity_variable}
            lmdi_output_additive_.rename(columns={'Total_{}'.format(activity_variable):'Total_{}'.format(new_activity_variable)}, inplace=True)
            #check the column names are the same
            if i != 0:
                if lmdi_output_additive_.columns.tolist() != lmdi_output_additive.columns.tolist():
                    breakpoint()
                    raise Exception('The column names in the datasets {} and {} are not the same. Please check the column names in the datasets.'.format(lmdi_output_additive.columns.tolist(), lmdi_output_additive_.columns.tolist()))
            #concatenate the data
            lmdi_output_additive = pd.concat([lmdi_output_additive, lmdi_output_additive_], axis=0)
        #sum up additive effects
        lmdi_output_additive = lmdi_output_additive.groupby([time_variable]).sum(numeric_only=True).reset_index()
        #save with new id so we can plot it
        lmdi_output_additive.to_csv('{}\\{}{}_concatenated_additive.csv'.format(output_data_folder,data_title, new_extra_identifier), index=False)
        
    elif hierarchical:
        lmdi_output_additive = pd.DataFrame() 
        for i in range(len(extra_identifiers)):
            extra_identifier_ = extra_identifiers[i]
            activity_variable = activity_variables[i]
            
            lmdi_output_additive_ = pd.read_csv('{}\\{}{}_additive.csv'.format(output_data_folder,data_title, extra_identifier_))
            #rename the activity varaialbe to the new activity variable
            lmdi_output_additive_.rename(columns={activity_variable + ' effect':new_activity_variable + ' effect'}, inplace=True)
            #and change Total_{activity_variable} to Total_{new_activity_variable}
            lmdi_output_additive_.rename(columns={'Total_{}'.format(activity_variable):'Total_{}'.format(new_activity_variable)}, inplace=True)
            #check the column names are the same
            if i != 0:
                if lmdi_output_additive_.columns.tolist() != lmdi_output_additive.columns.tolist():
                    breakpoint()
                    raise Exception('The column names in the datasets {} and {} are not the same. Please check the column names in the datasets.'.format(lmdi_output_additive.columns.tolist(), lmdi_output_additive_.columns.tolist()))
            #concatenate the data
            lmdi_output_additive = pd.concat([lmdi_output_additive, lmdi_output_additive_], axis=0)
        #sum up additive effects
        lmdi_output_additive = lmdi_output_additive.groupby([time_variable]).sum(numeric_only=True).reset_index()
        #save with new id so we can plot it
        lmdi_output_additive.to_csv('{}\\{}{}_concatenated_additive.csv'.format(output_data_folder,data_title, new_extra_identifier), index=False)
        
def plot_combined_waterfalls(data_title,graph_titles,extra_identifiers, new_extra_identifier, structure_variables_list, activity_variables,energy_variable='Energy', emissions_variable='Emissions',emissions_divisia=False, time_variable='Year', graph_title='', residual_variable1='Energy intensity', residual_variable2='Emissions intensity', font_size=25,y_axis_min_percent_decrease=0.9,AUTO_OPEN=False, hierarchical=False, output_data_folder='output_data', plotting_output_folder='plotting_output', INCLUDE_TEXT = False):  
    """
    data used by this function:
        
        data_title eg. 'outlook-transport-divisia'
        extra_identifier eg. 'PASSENGER_REF'
        lmdi_output_multiplicative eg. pd.read_csv('output_data\\{}{}_lmdi_output_multiplicative.csv'.format(data_title, extra_identifier))
        lmdi_output_additive = pd.read_csv('output_data\\{}{}_lmdi_output_additive.csv'.format(data_title, extra_identifier))
        emissions_divisia eg. False
        structure_variables_list eg. ['Economy','Vehicle Type', 'Drive']
        graph_title eg. 'Road passenger - Drivers of changes in energy use (Ref)'
        residual_variable1 eg. f'{energy_variable} intensity' - this can be used to make the residual variable a bit more explanatory
        residual_variable2 eg. 'Emissions intensity' - this can be used to make the residual variable a bit more explanatory
    """
    
    import plotly.subplots as sp
    import plotly.offline as pyo
    import plotly.graph_objects as go
    if emissions_divisia == False and hierarchical == False:
        # Employ make_subplots to create a 1x2 grid (1 row, 2 columns)
        fig = sp.make_subplots(rows=1, cols=2, shared_yaxes=True, subplot_titles=graph_titles)
        fig.update_annotations(dict(
                font=dict(
                    size=40,  # Adjust this value to your liking
                )))
        for i in range(len(extra_identifiers)):
            extra_identifier = extra_identifiers[i]
            lmdi_output_additive = pd.read_csv('{}\\{}{}_concatenated_additive.csv'.format(output_data_folder,data_title, extra_identifier))
            activity_variable = activity_variables[i]
            
            #remove activity data from the dataset
            lmdi_output_additive.drop('Total_{}'.format(activity_variable), axis=1, inplace=True)

            #remove ' effect' where it is at the end of all column names using regex ($ marks the end of the string)
            lmdi_output_additive.columns = lmdi_output_additive.columns.str.replace(' effect$', '', regex=True)
            
            #replace f'{energy_variable} intensity' with residual_variable1
            lmdi_output_additive.columns = lmdi_output_additive.columns.str.replace(f'{energy_variable} intensity', residual_variable1)
            
            #format data for waterfall plot
            #use the latest year, and the energy value for the first year
            beginning_year = lmdi_output_additive[time_variable].min()
            final_year = lmdi_output_additive[time_variable].max()
            add_plot_first_year_energy = lmdi_output_additive[lmdi_output_additive[time_variable] == beginning_year]['Total {}'.format(energy_variable)].values[0]
            add_plot = lmdi_output_additive[lmdi_output_additive[time_variable] == final_year]

            #set where the base for the y axis of the graph will begin 
            base_amount =  add_plot_first_year_energy * y_axis_min_percent_decrease
            #create a 'relative' vlaue  in the list for each driver in the dataset. to count the number of drivers, we can use the number of structure variables + 2 (activity and 2xresidual)
            measure_list = ['absolute'] + ['relative'] * (len(structure_variables_list) + 2) + ['total']

            # if graph_title == '':
            #     title = '{}{} - Additive LMDI'.format(data_title, extra_identifier)
            # else:
            #     title = graph_title

            y = [add_plot_first_year_energy-base_amount, 
            add_plot[activity_variable].iloc[0]] + add_plot[structure_variables_list].iloc[0].tolist() + [add_plot[residual_variable1].iloc[0],
            add_plot["Total {}".format(energy_variable)].iloc[0]]
            x = [str(beginning_year) + ' {}'.format(energy_variable),
            activity_variable] + structure_variables_list + [residual_variable1,
            str(final_year)+' {}'.format(energy_variable)]
            if INCLUDE_TEXT:
                text = [
                    str(int(add_plot_first_year_energy.round(0))), 
                    str(int(add_plot[activity_variable].round(0).iloc[0]))
                ] + [str(int(add_plot[var].round(0).iloc[0])) for var in structure_variables_list] + [
                    str(int(add_plot[residual_variable1].round(0).iloc[0])), 
                    str(int(add_plot["Total {}".format(energy_variable)].round(0).iloc[0]))
                ]
            else:
                text = None
            
            # Create waterfall figure
            waterfall_fig = go.Waterfall(
                orientation="v",
                measure=measure_list,
                base=base_amount,
                x=x,
                textposition="outside",
                text=text,
                y=y,
                decreasing={"marker": {"color": "#377eb8"}},
                increasing={"marker": {"color": "#ff7f00"}},
                totals={"marker": {"color": "#787878"}}
            )

            # Add the waterfall figures to the subplots
            fig.add_trace(waterfall_fig, row=1, col=i+1)
        

        # Update the layout of the subplots
        fig.update_layout(
            font=dict(size=font_size),
            waterfallgap=0.01,
            showlegend=False
        )
        
        #create unit for y axis
        fig.update_yaxes(title_text='PJ')
        #add a slight slant to the x axis labels
        fig.update_xaxes(tickangle=25)
        
        # Save the figure to an HTML file
        pyo.plot(fig, filename=plotting_output_folder + data_title + new_extra_identifier + '_combined.html',auto_open=AUTO_OPEN)
        
        
    elif emissions_divisia == False and hierarchical == True:
        # Employ make_subplots to create a 1x2 grid (1 row, 2 columns)
        fig = sp.make_subplots(rows=1, cols=2, shared_yaxes=True, subplot_titles=graph_titles)
        fig.update_annotations(dict(
                font=dict(
                    size=40,  # Adjust this value to your liking
                )))
        for i in range(len(extra_identifiers)):
            extra_identifier = extra_identifiers[i]
            lmdi_output_additive = pd.read_csv('{}\\{}{}_concatenated_additive.csv'.format(output_data_folder,data_title, extra_identifier))
            activity_variable = activity_variables[i]
            
            #remove activity data from the dataset
            lmdi_output_additive.drop('Total_{}'.format(activity_variable), axis=1, inplace=True)

            #remove ' effect' where it is at the end of all column names using regex ($ marks the end of the string)
            lmdi_output_additive.columns = lmdi_output_additive.columns.str.replace(' effect$', '', regex=True)
            
            #somewhere in the code we name the residual variable with 'intensity' in name so we need to replace that with residual_variable1.
            if '{} intensity'.format(structure_variables_list[-1]) not in lmdi_output_additive.columns:
                breakpoint()
                print('WARNING: {} intensity not in columns of lmdi_output_additive. This may cause a mistake in the plotting of the hierarchical additive waterfall plot.'.format(structure_variables_list[-1]))
            lmdi_output_additive.columns = lmdi_output_additive.columns.str.replace('{} intensity'.format(structure_variables_list[-1]), residual_variable1)

            #format data for waterfall plot
            #use the latest year, and the energy value for the first year
            beginning_year = lmdi_output_additive[time_variable].min()
            final_year = lmdi_output_additive[time_variable].max()
            add_plot_first_year_energy = lmdi_output_additive[lmdi_output_additive[time_variable] == beginning_year]['Total {}'.format(energy_variable)].values[0]
            add_plot = lmdi_output_additive[lmdi_output_additive[time_variable] == final_year]

            #set where the base for the y axis of the graph will begin 
            base_amount =  add_plot_first_year_energy * y_axis_min_percent_decrease
            #create a 'relative' vlaue  in the list for each driver in the dataset. to count the number of drivers, we can use the number of structure variables + 2 (activity and 2xresidual)
            measure_list = ['absolute'] + ['relative'] * (len(structure_variables_list) + 2) + ['total']

            # if graph_title == '':
            #     title = '{}{} - Additive LMDI'.format(data_title, extra_identifier)
            # else:
            #     title = graph_title
            y = [add_plot_first_year_energy-base_amount, 
            add_plot[activity_variable].iloc[0]] + add_plot[structure_variables_list].iloc[0].tolist() + [add_plot[residual_variable1].iloc[0],
            add_plot["Total {}".format(energy_variable)].iloc[0]]
            x = [str(beginning_year) + ' {}'.format(energy_variable),
            activity_variable] + structure_variables_list + [residual_variable1,
            str(final_year)+' {}'.format(energy_variable)]
            if INCLUDE_TEXT:
                text = [
                    str(int(add_plot_first_year_energy.round(0))), 
                    str(int(add_plot[activity_variable].round(0).iloc[0]))
                ] + [str(int(add_plot[var].round(0).iloc[0])) for var in structure_variables_list] + [
                    str(int(add_plot[residual_variable1].round(0).iloc[0])), 
                    str(int(add_plot["Total {}".format(energy_variable)].round(0).iloc[0]))
                ]
            else:
                text = None
            
            # Create waterfall figure
            waterfall_fig = go.Waterfall(
                orientation="v",
                measure=measure_list,
                base=base_amount,
                x=x,
                textposition="outside",
                text=text,
                y=y,
                decreasing={"marker": {"color": "#377eb8"}},
                increasing={"marker": {"color": "#ff7f00"}},
                totals={"marker": {"color": "#787878"}}
            )

            # Add the waterfall figures to the subplots
            fig.add_trace(waterfall_fig, row=1, col=i+1)
        

        # Update the layout of the subplots
        fig.update_layout(
            font=dict(size=font_size),
            waterfallgap=0.01,
            showlegend=False
        )

        #create unit for y axis
        fig.update_yaxes(title_text='PJ')
        #add a slight slant to the x axis labels 
        fig.update_xaxes(tickangle=25)
        
        # Save the figure to an HTML file
        pyo.plot(fig, filename=plotting_output_folder + data_title + new_extra_identifier + '_combined.html',auto_open=AUTO_OPEN)


    elif emissions_divisia == True and hierarchical == True:
        # Employ make_subplots to create a 1x2 grid (1 row, 2 columns)
        fig = sp.make_subplots(rows=1, cols=2, shared_yaxes=True, subplot_titles=graph_titles)
        fig.update_annotations(dict(
                font=dict(
                    size=40,  # Adjust this value to your liking
                )))
        for i in range(len(extra_identifiers)):
            extra_identifier = extra_identifiers[i]
            lmdi_output_additive = pd.read_csv('{}\\{}{}_concatenated_additive.csv'.format(output_data_folder,data_title, extra_identifier))
            activity_variable = activity_variables[i]
            
            #remove activity data from the dataset
            lmdi_output_additive.drop('Total_{}'.format(activity_variable), axis=1, inplace=True)

            #remove ' effect' where it is at the end of all column names using regex ($ marks the end of the string)
            lmdi_output_additive.columns = lmdi_output_additive.columns.str.replace(' effect$', '', regex=True)
            
            #somewhere in the code we name the residual variable with 'intensity' in name so we need to replace that with residual_variable1.
            if '{} emissions intensity'.format(structure_variables_list[-1]) not in lmdi_output_additive.columns:
                breakpoint()
                print('WARNING: {} emissions intensity not in columns of lmdi_output_additive. This may cause a mistake in the plotting of the hierarchical additive waterfall plot.'.format(structure_variables_list[-1]))
                
            if '{} energy intensity'.format(structure_variables_list[-1]) not in lmdi_output_additive.columns:
                breakpoint()
                print('WARNING: {} energy intensity not in columns of lmdi_output_additive. This may cause a mistake in the plotting of the hierarchical additive waterfall plot.'.format(structure_variables_list[-1]))
            lmdi_output_additive.columns = lmdi_output_additive.columns.str.replace('{} energy intensity'.format(structure_variables_list[-1]), residual_variable1)
            lmdi_output_additive.columns = lmdi_output_additive.columns.str.replace('{} emissions intensity'.format(structure_variables_list[-1]), residual_variable2)
            
            
            #format data for waterfall plot
            #use the latest year, and the emissions value for the first year
            beginning_year = lmdi_output_additive[time_variable].min()
            final_year = lmdi_output_additive[time_variable].max()
            add_plot_first_year_emissions = lmdi_output_additive[lmdi_output_additive[time_variable] == beginning_year]['Total {}'.format(emissions_variable)].values[0]
            add_plot = lmdi_output_additive[lmdi_output_additive[time_variable] == final_year]

            #set where the base for the y axis of the graph will begin 
            base_amount =  add_plot_first_year_emissions * y_axis_min_percent_decrease
            #create a 'relative' vlaue  in the list for each driver in the dataset. to count the number of drivers, we can use the number of structure variables + 2 (activity and 2xresidual)
            measure_list = ['absolute'] + ['relative'] * (len(structure_variables_list) + 3) + ['total']

            # if graph_title == '':
            #     title = '{}{} - Additive LMDI'.format(data_title, extra_identifier)
            # else:
            #     title = graph_title
            y = [add_plot_first_year_emissions-base_amount, 
            add_plot[activity_variable].iloc[0]] + add_plot[structure_variables_list].iloc[0].tolist() + [add_plot[residual_variable1].iloc[0],add_plot[residual_variable2].iloc[0],
            add_plot["Total {}".format(emissions_variable)].iloc[0]]
            x = [str(beginning_year) + ' {}'.format(emissions_variable),
            activity_variable] + structure_variables_list + [residual_variable1,residual_variable2,
            str(final_year)+' {}'.format(emissions_variable)]
            if INCLUDE_TEXT:
                text = [
                    str(int(add_plot_first_year_emissions.round(0))), 
                    str(int(add_plot[activity_variable].round(0).iloc[0]))
                ] + [str(int(add_plot[var].round(0).iloc[0])) for var in structure_variables_list] + [
                    str(int(add_plot[residual_variable1].round(0).iloc[0])),
                    str(int(add_plot[residual_variable2].round(0).iloc[0])), 
                    str(int(add_plot["Total {}".format(emissions_variable)].round(0).iloc[0]))
                ]
            else:
                text = None
            
            # Create waterfall figure
            waterfall_fig = go.Waterfall(
                orientation="v",
                measure=measure_list,
                base=base_amount,
                x=x,
                textposition="outside",
                text=text,
                y=y,
                decreasing={"marker": {"color": "#377eb8"}},
                increasing={"marker": {"color": "#ff7f00"}},
                totals={"marker": {"color": "#787878"}}
            )

            # Add the waterfall figures to the subplots
            fig.add_trace(waterfall_fig, row=1, col=i+1)
        

        # Update the layout of the subplots
        fig.update_layout(
            font=dict(size=font_size),
            waterfallgap=0.01,
            showlegend=False
        )

        #create unit for y axis
        fig.update_yaxes(title_text='MtCO2')
        #add a slight slant to the x axis labels 
        fig.update_xaxes(tickangle=25)
        
        # Save the figure to an HTML file
        pyo.plot(fig, filename=plotting_output_folder + data_title + new_extra_identifier + '_combined.html',auto_open=AUTO_OPEN)



# # print('Please note that the hierarchical LMDI method only produces a multiplicative output. So the output will be a multiplicative waterfall plot.')
        
#         #get data
#         lmdi_output_multiplicative = pd.read_csv('{}\\{}{}_multiplicative.csv'.format(output_data_folder,data_title, extra_identifier))
#         #Regardless of the column names, rename data in order of, 'Year', activity_variable, structure_variables_list, residual_variable1, 'Multiplicative change in {}'.format(energy_variable)
#         try:
#             lmdi_output_multiplicative.columns = [time_variable, activity_variable] + structure_variables_list + [residual_variable1, 'Multiplicative change in {}'.format(energy_variable)]
#         except ValueError:# Length mismatch: Expected axis has 7 elements, new values have 6 elements
#             breakpoint()
#             raise Exception('Expected axis has these cols: {} whereas new values has these cols: {}'.format(lmdi_output_multiplicative.columns, [time_variable, activity_variable] + structure_variables_list + [residual_variable1, 'Multiplicative change in {}'.format(energy_variable)]))

#         #filter data to only include the final year
#         lmdi_output_multiplicative = lmdi_output_multiplicative[lmdi_output_multiplicative[time_variable] == lmdi_output_multiplicative[time_variable].max()]
#         # #create list of driver names in the order we want them to appear in the graph
#         # driver_list = [activity_variable] + structure_variables_list + [residual_variable1]

#         # #need to make the data in long format so we have a driver column instead fo a column for each driver:
#         # mult_plot = pd.melt(lmdi_output_multiplicative, id_vars=[time_variable], var_name='Driver', value_name='Value')

#         # #create category based on whether data is driver or change in energy use. because we dont want it to show in the graph we will just make driver a double space, and the change in enegry a singel space
#         # mult_plot['Line type'] = mult_plot['Driver'].apply(lambda i: '' if i == 'Multiplicative change in {}'.format(energy_variable) else ' ')
        
#         #rename to add_plot to make it easier to copy and paste code
#         add_plot = lmdi_output_multiplicative.copy()
#         #remove ' effect' where it is at the end of all column names using regex ($ marks the end of the string)
#         add_plot.columns = add_plot.columns.str.replace(' effect$', '', regex=True)
        
#         #create a 'relative' vlaue  in the list for each driver in the dataset. to count the number of drivers, we can use the number of structure variables + 2 (activity and residual)
#         measure_list = ['relative'] * (len(structure_variables_list) + 2) + ['total']

#         if graph_title == '':
#             title = '{}{} - Multiplicative LMDI'.format(data_title, extra_identifier)
#         else:
#             title = graph_title

#         y = [add_plot[activity_variable].iloc[0]] + add_plot[structure_variables_list].iloc[0].tolist() + [add_plot[residual_variable1].iloc[0],
#         add_plot["Multiplicative change in {}".format(energy_variable)].iloc[0]]

        
#         x = [activity_variable] + structure_variables_list + [residual_variable1,'Multiplicative change in {}'.format(energy_variable)]

#         fig = go.Figure(go.Bar(
#             orientation = "v",
#             #measure = measure_list,
#             # base = base_amount,

#             x = x,

#             textposition = "outside",

#             #can add text to the waterfall plot here to show the values of the drivers
#             # text = [int(add_plot_first_year_energy), 
#             # str(int(add_plot["Activity"].round(0).iloc[0])), 
#             # str(int(add_plot[structure_variable].round(0).iloc[0])),
#             # str(int(add_plot["Energy intensity"].round(0).iloc[0])), 
#             # str(int(add_plot["Energy"].round(0).iloc[0]))],

#             y = y,

#             # decreasing = {"marker":{"color":"#377eb8"}},
#             # increasing = {"marker":{"color":"#ff7f00"}},
#             # totals = {"marker":{"color":"#787878"}}
#             #color bars based on their x axis value. if the x axis value is 'Multiplicative change in {}'.format(energy_variable) then make it "#787878", otherwise if the y axis value is positive make it "#ff7f00" and if its negative make it "#377eb8"
#             marker_color = ["#787878" if i == 'Multiplicative change in {}'.format(energy_variable) else "#ff7f00" if j > 1 else "#377eb8" for i,j in zip(x,y)]            

#         ))
#         dotted_line_index = len(x) - 1.5
#         fig.update_layout(
#                 title = title,
#                 font=dict(
#                 size=font_size
#             ), waterfallgap = 0.01,
#             #create dotted line between residual and percent change in energy use
#             shapes = [ dict( type = 'line', x0 = dotted_line_index, y0 = -1, x1 = dotted_line_index, y1 = 1, xref = 'x', yref = 'y', line = dict( color = 'black', width = 1, dash = 'dot' ) ) ]
#         )

#         plotly.offline.plot(fig, filename=plotting_output_folder + data_title + extra_identifier + '_multiplicative_waterfall.html',auto_open=AUTO_OPEN)
#         #fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + data_title + extra_identifier + 'multiplicative_waterfall.png')


def plot_additive_timeseries_WEIRD_COPY(data_title, extra_identifier, structure_variables_list,activity_variable,energy_variable='Energy', emissions_variable='Emissions',emissions_divisia=False, time_variable='Year', graph_title='', residual_variable1='Energy intensity', residual_variable2='Emissions intensity', font_size=25,AUTO_OPEN=False, hierarchical=False,output_data_folder='output_data',plotting_output_folder='\\plotting_output\\', INCLUDE_EXTRA_FACTORS_AT_END = False):#cant work out why this was here?
    """
    data used by this function:
        
        data_title eg. 'outlook-transport-divisia'
        extra_identifier eg. 'PASSENGER_REF'
        lmdi_output_additive eg. pd.read_csv('output_data\\{}{}_lmdi_output_additive.csv'.format(data_title, extra_identifier))
        lmdi_output_additive = pd.read_csv('output_data\\{}{}_lmdi_output_additive.csv'.format(data_title, extra_identifier))
        emissions_divisia eg. False
        structure_variables_list eg. ['Economy','Vehicle Type', 'Drive']
        graph_title eg. 'Road passenger - Drivers of changes in energy use (Ref)'
        residual_variable1 eg. f'{energy_variable} intensity' - this can be used to make the residual variable a bit more explanatory
        residual_variable2 eg. 'Emissions intensity' - this can be used to make the residual variable a bit more explanatory
        
        INCLUDE_EXTRA_FACTORS_AT_END - if you use this make sure to put the extra columns right at teh end of the df, and so that the next last column is the activity variable
    """
    if emissions_divisia == False and hierarchical == False:
        
        #get data
        lmdi_output_additive = pd.read_csv('{}\\{}{}_additive.csv'.format(output_data_folder,data_title, extra_identifier))

        #remove activity and total energy data from the dataset
        lmdi_output_additive.drop('Total_{}'.format(activity_variable), axis=1, inplace=True)
        lmdi_output_additive.drop('Total {}'.format(energy_variable), axis=1, inplace=True)

        #remove ' effect' where it is at the end of all column names using regex ($ marks the end of the string)
        lmdi_output_additive.columns = lmdi_output_additive.columns.str.replace(' effect$', '', regex=True)
        
        #rename the energy intensity column to residual_variable1
        lmdi_output_additive.rename(columns={'{} intensity'.format(energy_variable):residual_variable1}, inplace=True)
        
        #need to make the data in long format so we have a driver column instead fo a column for each driver:
        timeseries_plot = pd.melt(lmdi_output_additive, id_vars=[time_variable], var_name='Driver', value_name='Value')

        #create category based on whether data is driver or change in energy use
        timeseries_plot['Line type'] = timeseries_plot['Driver'].apply(lambda i: i if i == 'Additive change in {}'.format(energy_variable) else 'Driver')
        #set title

        if graph_title == '':
            title = '{}{} - Additive LMDI'.format(data_title, extra_identifier)
        else:
            title = graph_title
            
        driver_name_list = ['Additive change in {}'.format(energy_variable), 'Activity']+structure_variables_list+[residual_variable1]
        if INCLUDE_EXTRA_FACTORS_AT_END:
            #add extra factors at the end of the graph. this allows for things like calcualting the effect of including the effect of electricity gernation emissions, which are treated as being independent of the other drivers (even though they are not - it would usually change the effect of the other drivers)
            cols_after_total_var = lmdi_output_additive.columns.tolist()[lmdi_output_additive.columns.tolist().index('Additive change in {}'.format(energy_variable))+1:]
            driver_name_list += cols_after_total_var
        #plot
        fig = px.line(timeseries_plot, x=time_variable, y="Value", color="Driver", line_dash = 'Line type', title=title, category_orders={"Line type":['Additive change in {}'.format(energy_variable), 'Driver'],"Driver":driver_name_list})#,

        fig.update_layout(
            font=dict(
                size=font_size
            )
        )
        plotly.offline.plot(fig, filename=plotting_output_folder + data_title + extra_identifier + '_additive_timeseries.html', auto_open=AUTO_OPEN)
        #fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + data_title + extra_identifier + 'Additive_timeseries.png')

    elif emissions_divisia == True and hierarchical == False:
        
        #get data
        lmdi_output_additive = pd.read_csv('{}\\{}{}_additive.csv'.format(output_data_folder,data_title, extra_identifier))
        # lmdi_output_additive = pd.read_csv('output_data\\{}{}_additive.csv'.format(data_title, extra_identifier))

        #remove ' effect' where it is at the end of all column names using regex ($ marks the end of the string)
        lmdi_output_additive.columns = lmdi_output_additive.columns.str.replace(' effect$', '', regex=True)

        #remove activity and total energy/emissions data from the dataset
        lmdi_output_additive.drop('Total_{}'.format(activity_variable), axis=1, inplace=True)
        
        lmdi_output_additive.drop('Total {}'.format(emissions_variable), axis=1, inplace=True)

        #rename the energy intensity column to residual_variable1
        lmdi_output_additive.rename(columns={'{} intensity'.format(energy_variable):residual_variable1}, inplace=True)
        #rename the emissions intensity column to residual_variable2
        lmdi_output_additive.rename(columns={'{} intensity'.format(emissions_variable):residual_variable2}, inplace=True)
        #also rename 'Change in {}'.format(emissions_variable) to 'Additive change in {}'.format(emissions_variable))
        lmdi_output_additive.rename(columns={'Change in {}'.format(emissions_variable):'Additive change in {}'.format(emissions_variable)}, inplace=True)

        #need to make the data in long format first:
        timeseries_plot = pd.melt(lmdi_output_additive, id_vars=[time_variable], var_name='Driver', value_name='Value')
        
        #create category based on whether dfata is driver or change in erggy use
        timeseries_plot['Line type'] = timeseries_plot['Driver'].apply(lambda i: i if i == 'Additive change in {}'.format(emissions_variable) else 'Driver')

        #set title
        if graph_title == '':
            title = '{}{} - Additive LMDI decomposition of emissions'.format(data_title, extra_identifier)
        else:
            title = graph_title

        driver_name_list = ['Additive change in {}'.format(emissions_variable), 'Activity']+structure_variables_list+[residual_variable1, residual_variable2]
        if INCLUDE_EXTRA_FACTORS_AT_END:
            #add extra factors at the end of the graph. this allows for things like calcualting the effect of including the effect of electricity gernation emissions, which are treated as being independent of the other drivers (even though they are not - it would usually change the effect of the other drivers)
            cols_after_total_var = lmdi_output_additive.columns.tolist()[lmdi_output_additive.columns.tolist().index('Additive change in {}'.format(emissions_variable))+1:]
            driver_name_list += cols_after_total_var
            
        #plot
        fig = px.line(timeseries_plot, x=time_variable, y="Value", color="Driver", line_dash = 'Line type', title=title, category_orders={"Line type":['Additive change in {}'.format(emissions_variable), 'Driver'],"Driver":driver_name_list})

        fig.update_layout(
            font=dict(
                size=font_size
            )
        )
        plotly.offline.plot(fig, filename=plotting_output_folder + data_title + extra_identifier + '_additive_timeseries.html',auto_open=AUTO_OPEN)
        #fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + data_title + extra_identifier + 'Additive_timeseries.png')
    
    elif emissions_divisia == False and hierarchical == True:
        print('Not plotting timeseries of hierarchical additive data yet. Code not completed')
        pass
        #   NOTE THAT I DIDNT HAVE TIME TO FINISH THIS. NEED TO CONSNDER THAT THIS LINE NEEDS TO WORK ROUND THE HIERARCHICAL THING:
        # lmdi_output_additive.rename(columns={'{} intensity'.format(energy_variable):residual_variable1}, inplace=True)    
        
        
        # #get data
        # lmdi_output_additive = pd.read_csv('{}\\{}{}_additive.csv'.format(output_data_folder,data_title, extra_identifier))

        # #remove ' effect' where it is at the end of all column names using regex ($ marks the end of the string)
        # lmdi_output_additive.columns = lmdi_output_additive.columns.str.replace(' effect$', '', regex=True)
        
        # #rename the energy intensity column to residual_variable1
        # lmdi_output_additive.rename(columns={'{} intensity'.format(energy_variable):residual_variable1}, inplace=True)
        
        # #Regardless of the column names, rename data in order of, 'Year', activity_variable, structure_variables_list, residual_variable1, 'Additive change in {}'.format(energy_variable)
        # lmdi_output_additive.columns = [time_variable, activity_variable] + structure_variables_list + [residual_variable1, 'Additive change in {}'.format(energy_variable)]

        # #create list of driver names in the order we want them to appear in the graph
        # driver_list = [activity_variable] + structure_variables_list + [residual_variable1]

        # #need to make the data in long format so we have a driver column instead fo a column for each driver:
        # timeseries_plot = pd.melt(lmdi_output_additive, id_vars=[time_variable], var_name='Driver', value_name='Value')

        # #create category based on whether data is driver or change in energy use. because we dont want it to show in the graph we will just make driver a double space, and the change in enegry a singel space
        # timeseries_plot['Line type'] = timeseries_plot['Driver'].apply(lambda i: '' if i == 'Additive change in {}'.format(energy_variable) else ' ')

        # #set title
        # if graph_title == '':
        #     title = '{}{} - Additive LMDI'.format(data_title, extra_identifier)
        # else:
        #     title = graph_title

        # driver_name_list = ['Additive change in {}'.format(energy_variable)]+driver_list
        # if INCLUDE_EXTRA_FACTORS_AT_END:
        #     #add extra factors at the end of the graph. this allows for things like calcualting the effect of including the effect of electricity gernation emissions, which are treated as being independent of the other drivers (even though they are not - it would usually change the effect of the other drivers)
        #     cols_after_total_var = lmdi_output_additive.columns.tolist()[lmdi_output_additive.columns.tolist().index('Additive change in {}'.format(energy_variable))+1:]
        #     driver_name_list += cols_after_total_var
        # #plot
        # fig = px.line(timeseries_plot, x=time_variable, y="Value", color="Driver", line_dash = 'Line type',  category_orders={"Line type":['', ' '],"Driver":driver_name_list},title=title)#,

        # fig.update_layout(
        #     font=dict(
        #         size=font_size
        #     ),legend_title_text='Line\\Driver')
        # #set name of y axis to 'Proportional effect on energy use'
        # fig.update_yaxes(title_text='Effect on energy use')

        # plotly.offline.plot(fig, filename=plotting_output_folder + data_title + extra_identifier + '_additive_timeseries.html', auto_open=AUTO_OPEN)
        #fig.write_image(root_dir + '\\' + "\\plotting_output\\static\\" + data_title + extra_identifier + 'multiplicative_timeseries.png')



##%%

