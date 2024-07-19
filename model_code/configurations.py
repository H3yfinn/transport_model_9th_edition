import os
import re
import datetime
import pandas as pd
import plotly.express as px
from . import utility_functions

class Config:
    def __init__(self, root_dir):
        if os.name == 'nt':
            self.slash = '\\'
        else:
            self.slash = '/'
        self.root_dir = root_dir
        self.USE_LATEST_OUTPUT_DATE_ID = True
        self.NEW_SALES_SHARES = True
        self.NEW_FUEL_MIXING_DATA = True
        self.IMPORT_FROM_TRANSPORT_DATA_SYSTEM = False
        self.transport_data_system_FILE_DATE_ID = 'DATE20240612'
        self.latest_esto_data_FILE_DATE_ID = '20231207'
        self.PRINT_LESS_IMPORTANT_DETAILS = False
        self.PRINT_WARNINGS_FOR_FUTURE_WORK = False

        self._import_libraries()

        self.DEFAULT_BASE_YEAR = 2017
        self.OUTLOOK_BASE_YEAR = 2021
        self.END_YEAR = 2100
        self.GRAPHING_END_YEAR = 2070
        self.USE_LOGISTIC_FUNCTION = True
        self.INDEX_COLS = ['Date', 'Economy', 'Measure', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive', 'Scenario', 'Unit']
        self.INDEX_COLS_no_date = self.INDEX_COLS.copy()
        self.INDEX_COLS_no_date.remove('Date')
        self.INDEX_COLS_NO_MEASURE = self.INDEX_COLS.copy()
        self.INDEX_COLS_NO_MEASURE.remove('Measure')
        self.INDEX_COLS_NO_MEASURE.remove('Unit')
        self.FILE_DATE_ID = self._set_FILE_DATE_ID(root_dir)

        self.SCENARIOS_LIST_file_path = os.path.join('config', 'concordances_and_config_data', 'scenarios_list.csv')
        self.SCENARIOS_LIST = ['Reference', 'Target']
        self.SCENARIO_OF_INTEREST = 'Reference'

        self.user_input_measures_list_ROAD = ['Vehicle_sales_share', 'New_vehicle_efficiency_growth', 'Occupancy_or_load_growth', 'Mileage_growth', 'Stocks_per_capita', 'Activity_efficiency_improvement']
        self.user_input_measures_list_NON_ROAD = ['Vehicle_sales_share', 'Non_road_intensity_improvement']
        self.base_year_measures_list_ROAD = ['Activity', 'Energy', 'Stocks', 'Occupancy_or_load', 'New_vehicle_efficiency', 'Efficiency', 'Mileage', 'Average_age']
        self.base_year_measures_list_NON_ROAD = ['Activity', 'Energy', 'Intensity', 'Average_age']
        self.calculated_measures_ROAD = ['Travel_km', 'Surplus_stocks', 'Turnover_rate', 'Activity_per_Stock']
        self.calculated_measures_NON_ROAD = ['Stocks', 'Surplus_stocks', 'Turnover_rate']

        self.ROAD_MODEL_OUTPUT_COLS = ['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Medium', 'Date', 'Drive', 'Activity', 'Stocks', 'Efficiency', 'Energy', 'Surplus_stocks', 'Travel_km', 'Mileage', 'Vehicle_sales_share', 'Occupancy_or_load', 'Turnover_rate', 'Stock_turnover', 'New_stocks_needed', 'New_vehicle_efficiency', 'Stocks_per_thousand_capita', 'Activity_growth', 'Gdp_per_capita', 'Gdp', 'Population', 'Average_age', 'Age_distribution', 'Activity_efficiency_improvement']

        self.NON_ROAD_MODEL_OUTPUT_COLS = ['Date', 'Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive', 'Scenario', 'Activity', 'Average_age', 'Age_distribution', 'Energy', 'Intensity', 'Non_road_intensity_improvement', 'Surplus_stocks', 'Stocks', 'Vehicle_sales_share', 'Population', 'Gdp', 'Gdp_per_capita', 'Turnover_rate', 'Activity_per_Stock', 'Activity_growth', 'Stock_turnover', 'New_stocks_needed']

        self.FACTOR_MEASURES = ['Stocks_per_capita', 'Intensity', 'Average_age', 'Turnover_rate', 'Activity_per_Stock', 'Efficiency', 'Mileage', 'Occupancy_or_load', 'New_vehicle_efficiency', 'Age_distribution', 'Intensity']
        self.GROWTH_MEASURES = ['Occupancy_or_load_growth', 'Mileage_growth', 'Activity_growth', 'Activity_efficiency_improvement', 'Non_road_intensity_improvement', 'New_vehicle_efficiency_growth']

        self.measure_to_unit_concordance = self._load_concordance_file('measure_to_unit_concordance.csv', root_dir)
        self.measure_to_unit_concordance_dict = self.measure_to_unit_concordance.set_index('Measure')['Magnitude_adjusted_unit'].to_dict()
        self.transport_categories = self._load_concordance_file('manually_defined_transport_categories.csv', root_dir)
        self.economy_codes_path = self._construct_path('economy_code_to_name.csv', root_dir)
        self.ECONOMY_LIST = pd.read_csv(self.economy_codes_path).iloc[:, 0]
        self.model_output_file_name = 'model_output{}.csv'.format(self.FILE_DATE_ID)

        self.economy_regions_path = self._construct_path('region_economy_mapping.csv', root_dir)
        self.ECONOMY_REGIONS = pd.read_csv(self.economy_regions_path)

        self.PLOTLY_COLORS_LIST = px.colors.qualitative.Plotly
        self.AUTO_OPEN_PLOTLY_GRAPHS = False

        self.model_concordances_version = self.FILE_DATE_ID
        self.model_concordances_file_name = 'model_concordances_{}.csv'.format(self.model_concordances_version)
        self.model_concordances_file_name_fuels = 'model_concordances_fuels_{}.csv'.format(self.model_concordances_version)
        self.model_concordances_file_name_fuels_NO_BIOFUELS = 'model_concordances_fuels_NO_BIOFUELS_{}.csv'.format(self.model_concordances_version)
        self.model_concordances_base_year_measures_file_name = 'model_concordances_measures_{}.csv'.format(self.model_concordances_version)
        self.model_concordances_user_input_and_growth_rates_file_name = 'model_concordances_user_input_and_growth_rates_{}.csv'.format(self.model_concordances_version)
        self.model_concordances_supply_side_fuel_mixing_file_name = 'model_concordances_{}_supply_side_fuel_mixing.csv'.format(self.model_concordances_version)
        self.model_concordances_demand_side_fuel_mixing_file_name = 'model_concordances_{}_demand_side_fuel_mixing.csv'.format(self.model_concordances_version)

        self.economy_scenario_concordance = self._create_economy_scenario_concordance()

        self._check_folders(root_dir)

        self.medium_mapping = {
            'air': '15_01_domestic_air_transport', 'road': '15_02_road', 'rail': '15_03_rail', 'ship': '15_04_domestic_navigation', 'pipeline':'15_05_pipeline_transport', 'nonspecified': '15_06_nonspecified_transport', 'international_shipping':'04_international_marine_bunkers', 'international_aviation':'05_international_aviation_bunkers'
        }
        self.transport_type_mapping = {'passenger': '01_passenger', 'freight': '02_freight'}
        self.inverse_transport_type_mapping = {
            '15_01_01_passenger': 'passenger', '15_01_02_freight': 'freight', '15_02_01_passenger': 'passenger', '15_02_02_freight': 'freight', '15_03_01_passenger': 'passenger', '15_03_02_freight': 'freight', '15_04_01_passenger': 'passenger', '15_04_02_freight': 'freight', 'x':'all'
        }
        self.vehicle_type_mapping_passenger = {
            'suv': '15_02_01_03_sports_utility_vehicle', 'lt': '15_02_01_04_light_truck', 'car': '15_02_01_02_car', 'bus': '15_02_01_05_bus', '2w': '15_02_01_01_two_wheeler','all':'x'
        }
        self.vehicle_type_mapping_freight = {
            'mt': '15_02_02_03_medium_truck', 'lcv': '15_02_02_02_light_commercial_vehicle', 'ht': '15_02_02_04_heavy_truck', '2w': '15_02_02_01_two_wheeler_freight', 'all':'x'
        }
        self.drive_mapping_inversed = {
            'x':'all',
            '15_02_01_01_01_diesel_engine': 'ice_d', 
            '15_02_01_01_02_gasoline_engine': 'ice_g', 
            '15_02_01_01_03_battery_ev': 'bev', 
            '15_02_01_01_04_compressed_natual_gas': 'cng', 
            '15_02_01_01_05_plugin_hybrid_ev_gasoline': 'phev_g', 
            '15_02_01_01_06_plugin_hybrid_ev_diesel': 'phev_d',  
            '15_02_01_01_07_liquified_petroleum_gas': 'lpg', 
            '15_02_01_01_08_fuel_cell_ev': 'fcev', 

            '15_02_01_02_01_diesel_engine': 'ice_d', 
            '15_02_01_02_02_gasoline_engine': 'ice_g', 
            '15_02_01_02_03_battery_ev': 'bev', 
            '15_02_01_02_04_compressed_natual_gas': 'cng', 
            '15_02_01_02_05_plugin_hybrid_ev_gasoline': 'phev_g', 
            '15_02_01_02_06_plugin_hybrid_ev_diesel': 'phev_d',  
            '15_02_01_02_07_liquified_petroleum_gas': 'lpg', 
            '15_02_01_02_08_fuel_cell_ev': 'fcev', 

            '15_02_01_03_01_diesel_engine': 'ice_d', 
            '15_02_01_03_02_gasoline_engine': 'ice_g', 
            '15_02_01_03_03_battery_ev': 'bev', 
            '15_02_01_03_04_compressed_natual_gas': 'cng', 
            '15_02_01_03_05_plugin_hybrid_ev_gasoline': 'phev_g', 
            '15_02_01_03_06_plugin_hybrid_ev_diesel': 'phev_d',  
            '15_02_01_03_07_liquified_petroleum_gas': 'lpg', 
            '15_02_01_03_08_fuel_cell_ev': 'fcev', 

            '15_02_01_04_01_diesel_engine': 'ice_d', 
            '15_02_01_04_02_gasoline_engine': 'ice_g', 
            '15_02_01_04_03_battery_ev': 'bev', 
            '15_02_01_04_04_compressed_natual_gas': 'cng', 
            '15_02_01_04_05_plugin_hybrid_ev_gasoline': 'phev_g', 
            '15_02_01_04_06_plugin_hybrid_ev_diesel': 'phev_d',  
            '15_02_01_04_07_liquified_petroleum_gas': 'lpg', 
            '15_02_01_04_08_fuel_cell_ev': 'fcev', 

            '15_02_01_05_01_diesel_engine': 'ice_d', 
            '15_02_01_05_02_gasoline_engine': 'ice_g', 
            '15_02_01_05_03_battery_ev': 'bev', 
            '15_02_01_05_04_compressed_natual_gas': 'cng', 
            '15_02_01_05_05_plugin_hybrid_ev_gasoline': 'phev_g', 
            '15_02_01_05_06_plugin_hybrid_ev_diesel': 'phev_d',  
            '15_02_01_05_07_liquified_petroleum_gas': 'lpg', 
            '15_02_01_05_08_fuel_cell_ev': 'fcev',
'15_02_02_01_01_diesel_engine': 'ice_d', 
            '15_02_02_01_02_gasoline_engine': 'ice_g', 
            '15_02_02_01_03_battery_ev': 'bev', 
            '15_02_02_01_04_compressed_natual_gas': 'cng', 
            '15_02_02_01_05_plugin_hybrid_ev_gasoline': 'phev_g', 
            '15_02_02_01_06_plugin_hybrid_ev_diesel': 'phev_d',  
            '15_02_02_01_07_liquified_petroleum_gas': 'lpg', 
            '15_02_02_01_08_fuel_cell_ev': 'fcev', 

            '15_02_02_02_01_diesel_engine': 'ice_d', 
            '15_02_02_02_02_gasoline_engine': 'ice_g', 
            '15_02_02_02_03_battery_ev': 'bev', 
            '15_02_02_02_04_compressed_natual_gas': 'cng', 
            '15_02_02_02_05_plugin_hybrid_ev_gasoline': 'phev_g', 
            '15_02_02_02_06_plugin_hybrid_ev_diesel': 'phev_d',  
            '15_02_02_02_07_liquified_petroleum_gas': 'lpg', 
            '15_02_02_02_08_fuel_cell_ev': 'fcev', 

            '15_02_02_03_01_diesel_engine': 'ice_d', 
            '15_02_02_03_02_gasoline_engine': 'ice_g', 
            '15_02_02_03_03_battery_ev': 'bev', 
            '15_02_02_03_04_compressed_natual_gas': 'cng', 
            '15_02_02_03_05_plugin_hybrid_ev_gasoline': 'phev_g', 
            '15_02_02_03_06_plugin_hybrid_ev_diesel': 'phev_d',  
            '15_02_02_03_07_liquified_petroleum_gas': 'lpg', 
            '15_02_02_03_08_fuel_cell_ev': 'fcev', 

            '15_02_02_04_01_diesel_engine': 'ice_d', 
            '15_02_02_04_02_gasoline_engine': 'ice_g', 
            '15_02_02_04_03_battery_ev': 'bev', 
            '15_02_02_04_04_compressed_natual_gas': 'cng', 
            '15_02_02_04_05_plugin_hybrid_ev_gasoline': 'phev_g', 
            '15_02_02_04_06_plugin_hybrid_ev_diesel': 'phev_d',  
            '15_02_02_04_07_liquified_petroleum_gas': 'lpg', 
            '15_02_02_04_08_fuel_cell_ev': 'fcev'
        }

        self.subfuels_mapping = {
            '17_electricity':'x', '07_07_gas_diesel_oil':'07_07_gas_diesel_oil', '07_01_motor_gasoline':'07_01_motor_gasoline',
            '08_01_natural_gas':'08_01_natural_gas', 
            '16_x_hydrogen':'16_x_hydrogen',
            '07_09_lpg':'07_09_lpg',
            '07_02_aviation_gasoline':'07_02_aviation_gasoline', '07_x_jet_fuel':'07_x_jet_fuel', 
            '01_x_thermal_coal':'01_x_thermal_coal',
            '16_01_biogas':'16_01_biogas',
            '07_08_fuel_oil':'07_08_fuel_oil', '07_x_other_petroleum_products':'07_x_other_petroleum_products',
            '16_06_biodiesel':'16_06_biodiesel', 
            '16_05_biogasoline':'16_05_biogasoline', 
            '16_x_efuel':'16_x_efuel',
            '16_07_bio_jet_kerosene':'16_07_bio_jet_kerosene', 
            '16_x_ammonia': '16_x_ammonia',
            '07_06_kerosene':'07_06_kerosene', '08_02_lng':'08_02_lng'
        }

        self.fuels_mapping = {
            '17_electricity': '17_electricity', '07_07_gas_diesel_oil':'07_petroleum_products', '07_01_motor_gasoline':'07_petroleum_products',
            '07_06_kerosene':'07_petroleum_products',
            '08_01_natural_gas':'08_gas', 
            '08_02_lng':'08_gas',
            '16_x_hydrogen':'16_others', 
            '07_09_lpg':'07_petroleum_products',
            '07_02_aviation_gasoline':'07_petroleum_products', '07_x_jet_fuel':'07_petroleum_products', 
            '01_x_thermal_coal':'01_coal',
            '07_08_fuel_oil':'07_petroleum_products', #'07_x_other_petroleum_products':'07_petroleum_products',
            '16_01_biogas':'16_others',
            '16_06_biodiesel':'16_others', 
            '16_05_biogasoline':'16_others', 
            '16_x_efuel':'16_others',
            '16_07_bio_jet_kerosene':'16_others',  
            '16_x_ammonia': '16_others'
        }

        self.temp_esto_subfuels_to_new_subfuels_mapping = {#one day we should get the EBT code to simplify the subfuels in here but for now just use this mapping:
            '01_x_thermal_coal': '01_x_thermal_coal',
            '01_05_lignite': '01_05_lignite',
            'x': 'x',
            '07_01_motor_gasoline': '07_01_motor_gasoline',
            '07_02_aviation_gasoline': '07_02_aviation_gasoline',
            '07_x_jet_fuel': '07_x_jet_fuel',
            '07_06_kerosene': '07_06_kerosene',
            '07_07_gas_diesel_oil': '07_07_gas_diesel_oil',
            '07_08_fuel_oil': '07_08_fuel_oil',
            '07_09_lpg': '07_09_lpg',
            # '07_11_ethane': '07_x_other_petroleum_products',
            # '07_x_other_petroleum_products': '07_x_other_petroleum_products',
            '08_01_natural_gas': '08_01_natural_gas',
            '08_02_lng': '08_02_lng',
            '08_03_gas_works_gas': '08_01_natural_gas',
            '16_01_biogas': '16_01_biogas',
            '16_05_biogasoline': '16_05_biogasoline',
            '16_06_biodiesel': '16_06_biodiesel',
            '16_07_bio_jet_kerosene': '16_07_bio_jet_kerosene',
            '16_08_other_liquid_biofuels': '16_09_other_sources',
            '16_09_other_sources': '16_09_other_sources',
            '16_x_ammonia': '16_x_ammonia',
            '16_x_hydrogen': '16_x_hydrogen',
            '16_x_efuel': '16_x_efuel',
            '01_01_coking_coal': '01_01_coking_coal'
        }

        self.x_subfuel_mappings = {
            # '16_others': '16_09_other_sources',#removed because these are aggregates in the esto data
            '17_electricity': '17_electricity',
            # '03_peat':'01_coal',#removed because these are aggregates in the esto data
            # '08_gas': '08_01_natural_gas',#removed because these are aggregates in the esto data
            # '07_petroleum_products': '07_x_other_petroleum_products',#removed because these are aggregates in the esto data
            # '01_coal': '01_coal',#removed because these are aggregates in the esto data
            # '02_coal_products': '02_coal_products'#,#coal products is removed from esto data on line 489 of adjust_data_to_match_esto. it shouldn’t have any effect on the model
            # '06_crude_oil_and_ngl': '06_crude_oil_and_ngl'
        }

    def _import_libraries(self):
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
    
    def _set_FILE_DATE_ID(self, root_dir):    
        if self.USE_LATEST_OUTPUT_DATE_ID:
            data_folder_path = os.path.join(root_dir, 'output_data', 'model_output')
            file_name = 'model_output'
            FILE_DATE_ID = utility_functions.get_latest_date_for_data_file(data_folder_path, file_name)
            if FILE_DATE_ID is None:
                FILE_DATE_ID = datetime.datetime.now().strftime("%Y%m%d")
        else:
            FILE_DATE_ID = datetime.datetime.now().strftime("%Y%m%d")
        return FILE_DATE_ID
        
    def _load_concordance_file(self, file_name, root_dir):
        file_path = os.path.join(root_dir, 'config', 'concordances_and_config_data', file_name)
        return pd.read_csv(file_path)

    def _construct_path(self, file_name, root_dir):
        return os.path.join(root_dir, 'config', 'concordances_and_config_data', file_name)

    def _create_economy_scenario_concordance(self):
        economy_scenario_concordance = pd.DataFrame(columns=['Economy', 'Scenario'])
        for economy in self.ECONOMY_LIST:
            for scenario in self.SCENARIOS_LIST:
                economy_scenario_concordance = pd.concat([economy_scenario_concordance, pd.DataFrame({'Economy': [economy], 'Scenario': [scenario]})], ignore_index=True)
        return economy_scenario_concordance

    def _check_folders(self, root_dir):
        model_inputs_path = os.path.join(root_dir, "intermediate_data", "model_inputs", self.FILE_DATE_ID)
        if not os.path.exists(model_inputs_path):
            os.makedirs(model_inputs_path)

    def update_config(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError(f"{key} is not a valid attribute of Config")
#     #get the date from the file name
    #     all_files = [re.search(regex_pattern_date, file).group() for file in all_files]
    #     #convert the dates to datetime objects
    #     all_files = [datetime.datetime.strptime(date, '%Y%m%d') for date in all_files]
    #     #get the latest date
    #     if len(all_files) == 0:
    #         print('No files found for ' + file_name_start + ' ' + file_name_end)
    #         return None
    #     # try:
    #     latest_date = max(all_files)
    #     # except ValueError:
    #     #     print('No files found for ' + file_name_start + ' ' + file_name_end)
    #     #     return None
    #     #convert the latest date to a string
    #     latest_date = latest_date.strftime('%Y%m%d')
    #     return latest_date
