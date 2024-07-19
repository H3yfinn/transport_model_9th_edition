with open(os.path.join(config.root_dir, 'plotting_output', 'all_economy_graphs_plotting_times.csv'), 'a') as f:
                    f.write(f'{section},{elapsed_time}\n')
            except:
                pass

        def print_expected_time_to_run(section):
            try:
                with open(os.path.join(config.root_dir, 'plotting_output', 'all_economy_graphs_plotting_times.csv'), 'r') as f:
                    times = f.readlines()
                    times = [time.split(',') for time in times]
                    times = {time[0]: float(time[1]) for time in times}
                    total_time = sum(times.values())
                    print('Expected time to run: {}'.format(total_time))
            except:
                pass

        #start timer
        start_time = start_timer('Formatting', True)

        #load in the data
        model_output_all = pd.read_csv(os.path.join(config.root_dir, 'output_data', 'model_output', 'all_economies_{}_{}'.format(config.FILE_DATE_ID, config.model_output_file_name)))
        model_output_detailed = pd.read_csv(os.path.join(config.root_dir, 'output_data', 'model_output_detailed', 'all_economies_{}_{}'.format(config.FILE_DATE_ID, config.model_output_file_name)))
        model_output_with_fuels = pd.read_csv(os.path.join(config.root_dir, 'output_data', 'model_output_with_fuels', 'all_economies_{}_{}'.format(config.FILE_DATE_ID, config.model_output_file_name)))
        activity_growth = pd.read_csv(os.path.join(config.root_dir, 'input_data', 'from_8th', 'reformatted', 'activity_growth_8th.csv'))

        #end timer
        end_timer(start_time, 'Formatting', True)
os.makedirs(os.path.join(config.root_dir, f'{save_folder}\\'))
            if not os.path.exists(os.path.join(config.root_dir, f'{save_folder}\\static')):
                os.makedirs(os.path.join(config.root_dir, f'{save_folder}\\static'))

            if line_group_categories != None:
                df = df.groupby([x_column, facet_col,color, line_group,hover_name])[y_column].sum().reset_index()
            else:
                if hover_name == color:
                    df = df.groupby([x_column, facet_col,color])[y_column].sum().reset_index()
                else:
                    df = df.groupby([x_column, facet_col,color,hover_name])[y_column].sum().reset_index()
            
            plot_area(df, y_column, x_column, color, line_group, facet_col_wrap, facet_col, hover_name, hover_data, log_y, log_x, title, independent_y_axis, y_axis_title, x_axis_title, plot_html, plot_png, save_folder, AUTO_OPEN_PLOTLY_GRAPHS, width, height)
os.makedirs(os.path.join(config.root_dir,  f'{save_folder}'))
            if not os.path.exists(os.path.join(config.root_dir,  f'{save_folder}', 'static')):
                os.makedirs(os.path.join(config.root_dir,  f'{save_folder}', 'static'))
            if line_group_categories != None:
                df = df.groupby([x_column, facet_col, color, line_group, hover_name])[y_column].sum().reset_index()
            else:
                if hover_name == color:
                    df = df.groupby([x_column, facet_col, color])[y_column].sum().reset_index()
                else:
                    df = df.groupby([x_column, facet_col, color, hover_name])[y_column].sum().reset_index()
            plot_area(df, y_column, x_column, color, line_group, facet_col_wrap, facet_col, hover_name, hover_data, log_y, log_x, title, independent_y_axis, y_axis_title, x_axis_title, plot_html, plot_png, save_folder, AUTO_OPEN_PLOTLY_GRAPHS, width, height)

        ###########
        def calc_mean_if_not_summable_else_sum(df, value_cols, categorical_cols, non_summable_value_cols=non_summable_value_cols):
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
            df = df.groupby(categorical_cols + ['Date']).agg(agg_dict).reset_index()
            #now replace nan with ''
            df[value_cols] = df[value_cols].replace(np.nan, '')

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
            model_output_detailed.to_pickle(os.path.join(config.root_dir,  f'{default_save_folder}', f'{dataframe_name}.pkl'))
            print(f'{dataframe_name} saved as pickle')

        #plot each combination of: one of the value cols and then any number of the categorical cols
        n_categorical_cols = len(categorical_cols)
        do_this = True
                
        start = start_timer(dataframe_name, do_this)
        if do_this:

            #plot graphs with all economies on one graph
            for value_col in value_cols:
                for i in range(1, n_categorical_cols + 1):
                    for combo in itertools.combinations(categorical_cols, i):
                        title = f'{value_col} by {combo} - {scenario}'
                        save_folder = os.path.join(default_save_folder, f'{dataframe_name}', f'{value_col}')

                        plot_line_by_economy(model_output_detailed, color_categories=list(combo), y_column=value_col, title=title, save_folder=save_folder, facet_col='Economy', AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS, plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
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

        

        # def calc_APEC_mean_or_sum(df, value_cols, non_summable_value_cols, categorical_cols):
        #     #replace values equal to '' with nan while we calculate the mean and sum
        #     df[value_cols] = df[value_cols].replace('', np.nan)
        #     df_APEC_mean = df.groupby(categorical_cols + ['Date']).agg({col: 'mean' for col in value_cols}).reset_index()
        #     df_APEC_sum = df.groupby(categorical_cols + ['Date']).agg({col: 'sum' for col in value_cols}).reset_index()
        #     #now remove non_summable_value_cols from sum, and remove non, non_summable_value_cols from mean
        #     df_APEC_mean.drop(columns=[col for col in value_cols if col not in non_summable_value_cols], inplace=True)
        #     df_APEC_sum.drop(columns=non_summable_value_cols, inplace=True)
        #     #now merge the two dataframes
        #     df_APEC = pd.merge(df_APEC_mean, df_APEC_sum, on=categorical_cols + ['Date'], how='outer')

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
        start = start_timer(dataframe_name + ' by economy', do_this)
        if do_this:
            for economy_x in model_output_detailed['Economy'].unique():
                for value_col in value_cols:
                    for i in range(1, n_categorical_cols + 1):
                        for combo in itertools.combinations(categorical_cols, i):
                            title = f'{value_col} by {combo} - {scenario}'
                            save_folder = os.path.join(default_save_folder, f'{dataframe_name}', f'{economy_x}', f'{value_col}')
                                                    
                            #filter for that ecovnomy only and then plot
                            model_output_detailed_econ = model_output_detailed[model_output_detailed['Economy'] == economy_x].copy()
                            plot_line_by_economy(model_output_detailed_econ, color_categories=list(combo), y_column=value_col, title=title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS, plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
                            print(f'plotting {value_col} by {combo}')
        end_timer(start, dataframe_name + ' by economy', do_this)

        ##################################################################
        #TEMP
        if ECONOMY_ID == None:  # if we are plotting all economies then plot the regional data too
            #plot regional groupings of economys
            #import the region_economy_mappin.xlsx from config/concordances_and_config_data
            region_economy_mapping = pd.read_csv(os.path.join(config.root_dir,  'config', 'concordances_and_config_data', 'region_economy_mapping.csv'))
            #join with model_output_detailed_APEC.
            #where there is no region drop the row since we are just plotting singular economies atm
            model_output_detailed_regions = model_output_detailed.merge(region_economy_mapping, how='left', left_on='Economy', right_on='Economy')

            # model_output_detailed_regions['Region'] = model_output_detailed_regions['Region'].fillna(model_output_detailed_regions['Economy'])
            model_output_detailed_regions = model_output_detailed_regions.dropna(subset=['Region'])

            # model_output_detailed_regions = model_output_detailed_regions.groupby(categorical_cols + ['Date', 'Region']).agg({col: 'sum' for col in value_cols if col not in non_summable_value_cols else 'mean'}).reset_index()
            #breakpoint()#is it passenger km?
            model_output_detailed_regions = calc_mean_if_not_summable_else_sum(model_output_detailed_regions, value_cols, categorical_cols + ['Region'])

            #save copy of data as pickle for use in recreating plots. put it in save_folder
            if save_pickle:
                model_output_detailed_regions.to_pickle(os.path.join(config.root_dir,  f'{default_save_folder}', f'{dataframe_name}_regional.pkl'))
                print(f'{dataframe_name}_regional saved as pickle')
            
            n_categorical_cols = len(categorical_cols)
            do_this = True
            
            start = start_timer(dataframe_name + ' by region', do_this)
            if do_this:
                for economy_x in model_output_detailed_regions['Region'].unique():
                    #if region is nan then skip it
                    if pd.isna(economy_x):
                        continue
                    for value_col in value_cols:
                        for i in range(1, n_categorical_cols + 1):
                            for combo in itertools.combinations(categorical_cols, i):
                                title = f'{value_col} by {combo} - {scenario}'
                                save_folder = os.path.join(default_save_folder, f'{dataframe_name}', f'{economy_x}', f'{value_col}')

                                #filter for that ecovnomy only and then plot
                                model_output_detailed_econ = model_output_detailed_regions[model_output_detailed_regions['Region'] == economy_x].copy()
                                plot_line_by_economy(model_output_detailed_econ, color_categories=list(combo), y_column=value_col, title=title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS, plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
                                print(f'plotting {value_col} by {combo}')
            end_timer(start, dataframe_name + ' by region', do_this)

        ##################################################################
        ###########################plot 'Energy' by fuel type############
        ##################################################################
        #breakpoint()

        #. need to define value cols that are worth plotting
        value_cols_new = ['Energy']
        categorical_cols_new = ['Vehicle Type', 'Medium', 'Transport Type', 'Drive']
        dataframe_name = 'model_output_with_fuels'
        #create economy= 'all' which is the sum of all economies:
        model_output_with_fuels_plot = model_output_with_fuels.groupby(categorical_cols_new + ['Date', 'Fuel']).sum().reset_index()
        model_output_with_fuels_plot['Economy'] = 'all'
        model_output_with_fuels_plot_economy = model_output_with_fuels.groupby(categorical_cols_new + ['Date', 'Fuel', 'Economy']).sum().reset_index()
        model_output_with_fuels_plot = pd.concat([model_output_with_fuels_plot_economy, model_output_with_fuels_plot])

        #save copy of data as pickle for use in recreating plots. put it in save_folder
        if save_pickle:
            model_output_with_fuels_plot.to_pickle(os.path.join(config.root_dir,  f'{default_save_folder}', f'{dataframe_name}.pkl'))
        #plot singular graphs for each economy
        do_this = True
        
        start = start_timer(dataframe_name + ' by economy', do_this)
        if do_this:
            n_categorical_cols_new = len(categorical_cols_new)
            for economy_x in model_output_with_fuels_plot['Economy'].unique():
                for value_col in value_cols_new:
                    for i in range(1, n_categorical_cols_new + 1):
                        for combo in itertools.combinations(categorical_cols_new, i):
                            # Add 'Fuel' to the combo
                            combo = list(combo) + ['Fuel']
                            dataframe_name = 'model_output_with_fuels'
                            title = f'{value_col} by {combo} - {scenario}'
                            save_folder = os.path.join(default_save_folder, f'{dataframe_name}', f'{economy_x}', f'{value_col}', 'line')
                                                    
                            #filter for that ecovnomy only and then plot
model_output_with_fuels_plot_econ = model_output_with_fuels_plot[model_output_with_fuels_plot['Economy'] == economy_x].copy()
                            plot_line_by_economy(model_output_with_fuels_plot_econ, color_categories= list(combo), y_column=value_col, title=title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
                            print(f'plotting {value_col} by {combo}')
                            
                            title = f'{value_col} by {combo} - {scenario}'
                            save_folder = os.path.join(default_save_folder, dataframe_name, economy_x, value_col, 'area')

                            plot_area_by_economy(model_output_with_fuels_plot_econ, color_categories= list(combo), y_column=value_col, title=title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
        end_timer(start, dataframe_name+' by economy', do_this)

        ##################################################################
        
        if ECONOMY_ID == None:#if we are plotting all economies then plot the regional data too
            #merge with regions
            #plot regional groupings of economys
            #import the region_economy_mappin.xlsx from config/concordances_and_config_data
            region_economy_mapping = pd.read_csv(os.path.join(config.root_dir, 'config', 'concordances_and_config_data', 'region_economy_mapping.csv'))
            model_output_with_fuels_regions = model_output_with_fuels.merge(region_economy_mapping, how='left', left_on='Economy', right_on='Economy')

            #drop nas
            model_output_with_fuels_regions = model_output_with_fuels_regions.dropna(subset=['Region'])

            #sum up when we drop economy
            model_output_with_fuels_regions = model_output_with_fuels_regions.groupby(categorical_cols_new+['Date','Fuel', 'Region']).sum().reset_index()
            
            #save copy of data as pickle for use in recreating plots. put it in save_folder
            if save_pickle:
                model_output_with_fuels_regions.to_pickle(os.path.join(config.root_dir, default_save_folder, f'{dataframe_name}_regional.pkl'))
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
                                save_folder = os.path.join(default_save_folder, dataframe_name, region, value_col, 'line')
                                                        
                                #filter for that ecovnomy only and then plot
                                model_output_with_fuels_regions_region = model_output_with_fuels_regions[model_output_with_fuels_regions['Region'] == region]
                                plot_line_by_economy(model_output_with_fuels_regions_region, color_categories = list(combo), y_column=value_col, title=title,  line_dash_categories = 'Fuel', save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
                                print(f'plotting {value_col} by {list(combo) + ["Fuel"]}')
                                
                                
                                title = f'{value_col} by {list(combo) + ["Fuel"]} - {scenario}'
                                save_folder = os.path.join(default_save_folder, dataframe_name, economy_x, value_col, 'area')
                                
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
                        
                            save_folder = os.path.join(default_save_folder, 'energy_use_by_fuel', 'all_economies_plot', value_col, 'line')

                            plot_line_by_economy(model_output_with_fuels_plot, color_categories= list(combo),y_column=value_col, title=title,  line_dash_categories='Fuel', save_folder=save_folder, facet_col='Economy',AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
                            print(f'plotting {value_col} by {list(combo) + ["Fuel"]}')
                            
                            save_folder = os.path.join(default_save_folder, 'energy_use_by_fuel', 'all_economies_plot', value_col, 'area')
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
                # original_model_output_8th = pd.read_csv(os.path.join(config.root_dir, 'intermediate_data', 'activity_energy_road_stocks.csv'))
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
                #             save_folder = os.path.join(default_save_folder, dataframe_name, value_col, 'line')

                #             plot_line_by_economy(model_output_comparison, color_categories=list(combo), y_column=value_col, title=title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS, plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, facet_col='Dataset', PLOT=PLOT)
                #             print(f'plotting {value_col} by {combo}')
                            
                #             save_folder = os.path.join(default_save_folder, dataframe_name, value_col, 'area')
                #             plot_area_by_economy(model_output_comparison, color_categories=list(combo), y_column=value_col, title=title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS, plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, facet_col='Dataset', PLOT=PLOT)
                #then plot plot by economy
                
                for economy_x in model_output_comparison['Economy'].unique():
                    for value_col in value_col_comparison:
                        
                        for i in range(1, n_categorical_cols+1):
                            for combo in itertools.combinations(categorical_cols, i):
                                # # Add 'Fuel' to the combo
                                # combo = list(combo) + ['Fuel']

                                title = f'Comparison - {value_col} by {list(combo)} - {scenario}'
                                save_folder = os.path.join(default_save_folder, dataframe_name, economy_x, value_col, 'line')
                                                        
                                #filter for that ecovnomy only and then plot
                                model_output_comparison_economy = model_output_comparison[model_output_comparison['Economy'] == economy_x].copy()
                            
                                plot_line_by_economy(model_output_comparison_economy, color_categories=list(combo), y_column=value_col, title=title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS, plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, facet_col='Dataset', PLOT=plot_comparisons)
                                
                                save_folder = os.path.join(default_save_folder, dataframe_name, economy_x, value_col, 'area')
                                
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
                macro.to_pickle(os.path.join(config.root_dir, default_save_folder, f'{dataframe_name}.pkl'))
                print(f'{dataframe_name} saved as pickle')

            #for each economy plot a single graph and then plot all on one graph
            for economy_x in macro['Economy'].unique():
                for measure in macro_cols_new:
                    value_col = measure
                    title = f'{measure} for {economy_x} - {scenario}'
                    save_folder = os.path.join(default_save_folder, dataframe_name, economy_x, value_col)
#filter for that ecovnomy only and then plot
                    macro_econ = macro[macro['Economy'] == economy_x].copy()
                    plot_line_by_economy(macro_econ, color_categories= ['Economy'], y_column=value_col, title=title,  save_folder=os.path.join(save_folder), AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, facet_col=None,dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
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
                activity_growth.to_pickle(os.path.join(config.root_dir,  f'{default_save_folder}', f'{dataframe_name}.pkl'))
                print(f'{dataframe_name} saved as pickle')

            #for each economy plot a single graph and then plot all on one graph
            for value_col in ['cumulative_activity_growth', 'Activity_growth']:
                for economy_x in activity_growth['Economy'].unique():
                    
                    title = f'{value_col} for {economy_x} - {scenario}'
                    save_folder = os.path.join(default_save_folder, dataframe_name, economy_x, value_col)
                                                
                    #filter for that ecovnomy only and then plot
                    activity_growth_econ = activity_growth[activity_growth['Economy'] == economy_x].copy()
                    
                    plot_line_by_economy(activity_growth_econ, color_categories= ['Economy', 'Medium'], y_column=value_col, title=title,  save_folder=os.path.join(save_folder), AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, facet_col='Transport Type',dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
                    print(f'plotting {value_col}')
            # 'Medium' , 'Transport Type'
            #plot all in on egraph
            
            #filter for road medium omnly to reduce clutter
            activity_growth = activity_growth[activity_growth['Medium'] == 'road']

            for value_col in ['cumulative_activity_growth', 'Activity_growth']:
                title = f'{value_col}  for all economies - {scenario}'
                save_folder = os.path.join(default_save_folder, dataframe_name, value_col)

            
                plot_line_by_economy(activity_growth, color_categories= ['Economy'], y_column=value_col, title=title, save_folder=os.path.join(save_folder), AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, facet_col='Transport Type',dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
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
                        
                        save_folder = os.path.join(default_save_folder, dataframe_name, 'all_economies_plot', value_col)

                        plot_line_by_economy(model_output_detailed_int, color_categories= list(combo),y_column=value_col, title=title, save_folder=os.path.join(save_folder), AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, facet_col='Economy',dont_overwrite_existing_graphs=dont_overwrite_existing_graphs, PLOT=PLOT)
                        print(f'plotting {value_col} by {combo}')
        end_timer(start, dataframe_name+' with all economies on one graph', do_this)


#%%

# plot_all_graphs(config, ECONOMY_ID='19_THA', PLOT=True, plot_comparisons=True)#python code/plotting_functions/plot_all_graphs.py > plot_all_output.txt 2>&1

#
