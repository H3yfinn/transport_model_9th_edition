#%%
import pandas as pd
import matplotlib.pyplot as plt
import re

# --- 1. Load the CSV file ---

# Adjust the file path and delimiter if needed.
# In your case, the file seems to be tab-delimited.
file_path = '../other_data/Table_39._Light-Duty_Vehicle_Stock_by_Technology_Type (1).csv'  # update with your CSV file path
df = pd.read_csv(file_path)

# Inspect the data – it should have columns: "Car Stock", "full name", and year columns (e.g. 2024, 2025, 2026, ..., 2050)
print("Original DataFrame head:")
print(df.head())

# --- 2. Reshape the Data ---
# Melt the DataFrame so that each year becomes a row entry.
df_melt = df.melt(id_vars=['Car Stock', 'full name'], 
                  var_name='Year', 
                  value_name='Stocks')

# Convert the Year column to numeric (if it’s read as string) and Stock_Shares to float
# df_melt['Year'] = pd.to_numeric(df_melt['Year'], errors='coerce')
#make it an int so tehres no decimal
#drop , 'Growth (2024-2050)' from year

df_melt = df_melt[df_melt['Year'] != 'Growth (2024-2050)']

df_melt['Year'] = df_melt['Year'].astype(int)
df_melt['Stocks'] = pd.to_numeric(df_melt['Stocks'], errors='coerce')

print("\nMelted DataFrame head:")
print(df_melt.head())
# --- 3. Parse Engine Type and Scenario Details from 'full name' ---

def parse_full_name(full_name):
    """
    Splits the full name (colon-delimited) and returns the following:
    - Vehicle Type (1st token)
    - Engine Type (2nd token)
    - Fuel Type (3rd token)
    - Scenario (last token)
    """
    parts = [p.strip() for p in full_name.split(':')]
    vehicle_type = parts[0] if len(parts) > 0 else None
    engine_type = parts[1] if len(parts) > 1 else None
    fuel_type = parts[2] if len(parts) > 2 else None
    scenario = parts[-1] if len(parts) > 3 else None
    return pd.Series({
        'Measure': vehicle_type,
        'Vehicle_Type': engine_type,
        'Drive': fuel_type,
        'Scenario': scenario
    })

# Apply the parsing function to create new columns.
engine_info = df_melt['full name'].apply(parse_full_name)
df_melt = pd.concat([df_melt, engine_info], axis=1)

print("\nData with Engine_Type and Detail columns:")
print(df_melt.head())
# --- 4. Clean the Data ---

# # Drop any rows with missing values in key columns (Car Stock, Vehicle_Type, Year, or Stock_Shares)
df_clean = df_melt.copy()
#drop where scneario is None
df_clean = df_clean[df_clean['Scenario'].notna()]
# df_clean = df_clean.dropna(subset=['Car Stock', 'Vehicle_Type', 'Year', 'Stock_Shares'])


print("\nCleaned DataFrame head:")
print(df_clean.head())
#%%
# #now map some categories:
# df_clean.Drive.unique()
# 'Gasoline', 'TDI Diesel', 'Total', 'Ethanol-Flex Fuel ICE',
#        '100-Mile Electric Vehicle', '200-Mile Electric Vehicle',
#        '300-Mile Electric Vehicle', 'Plug-in 20 Gasoline Hybrid',
#        'Plug-in 50 Gasoline Hybrid', 'Electric-Diesel Hybrid',
#        'Electric-Gasoline Hybrid', 'Natural Gas ICE',
#        'Natural Gas Bi-fuel', 'Propane ICE', 'Propane Bi-fuel',
#        'Fuel Cell Methanol', 'Fuel Cell Hydrogen', 'Reference case',
#        'Conventional Gasoline', 'Flex-Fuel', 'Electric',
#        'Plug-in Electric Hybrid', 'Electric Hybrid', 'Gaseous',
#        'Fuel Cell', 'High Oil Price', 'High Oil and Gas Supply'
#want the categories: BEV, PHEV, HEV, ICE, FCEV, OTHER
drive_map_dict = {
    'Gasoline':'ICE',
    'TDI Diesel':'ICE',
    'Ethanol-Flex Fuel ICE':'ICE',
    '100-Mile Electric Vehicle':'BEV',
    '200-Mile Electric Vehicle':'BEV',
    '300-Mile Electric Vehicle':'BEV',
    'Plug-in 20 Gasoline Hybrid':'PHEV',
    'Plug-in 50 Gasoline Hybrid':'PHEV',
    'Electric-Diesel Hybrid':'HEV',
    'Electric-Gasoline Hybrid':'HEV',
    'Natural Gas ICE':'ICE',
    'Natural Gas Bi-fuel':'OTHER',
    'Propane ICE':'ICE',
    'Propane Bi-fuel':'OTHER',
    'Fuel Cell Methanol':'FCEV',
    'Fuel Cell Hydrogen':'FCEV',
    'Conventional Gasoline':'ICE',
    'Flex-Fuel':'OTHER',
    'Electric':'BEV',
    'Plug-in Electric Hybrid':'PHEV',
    'Electric Hybrid':'ICE',
    'Gaseous':'OTHER',
    'Fuel Cell':'FCEV'
}
df_clean['Drive'] = df_clean['Drive'].map(drive_map_dict)   
#and then keep only Light-Duty Vehicle Stock in Measure
df_clean = df_clean[df_clean['Measure'] == 'Light-Duty Vehicle Stock']  

# df_clean.Vehicle_Type.unique()
# array(['Conventional Cars', 'Alternative-Fuel Cars', 'Car Stock',
#        'Conventional Light Trucks', 'Alternative-Fuel Light Trucks',
#        'Light Truck Stock', 'Total Vehicle Stock'], dtype=object)
#map to cars, trucks
import numpy as np
vehicle_type_map = {
    'Conventional Cars': 'Car',
    'Alternative-Fuel Cars': 'Car',
    'Conventional Light Trucks': 'Truck',
    'Alternative-Fuel Light Trucks': 'Truck',
    'Light Truck Stock': np.nan,
    'Total Vehicle Stock': np.nan
}
df_clean['Vehicle_Type'] = df_clean['Vehicle_Type'].map(vehicle_type_map)

df_clean = df_clean[df_clean['Vehicle_Type'].notna()]

#drop cols 'Car Stock', 'full name'
df_clean = df_clean.drop(columns=['Car Stock', 'full name'])

#sum things up
df_clean = df_clean.groupby(['Measure','Year', 'Drive', 'Vehicle_Type', 'Scenario']).sum().reset_index()

# --- 5. Create Charts ---
#use plotly express for htis:
import plotly.express as px

#%%
fig = px.line(df_clean, x='Year', y='Stocks', color='Drive', line_dash='Scenario', title='Stocks Over Years by Vehicle Type Drive', facet_col='Vehicle_Type')
fig.update_layout(yaxis_title='Stocks', xaxis_title='Year')
fig.show()

fig.write_html('stocks_over_years_by_vehicle_type_drive.html')


#%%
#check for udplicates when we ignore Stocks
duplicates = df_clean.duplicated(subset=[ 'Year', 'Drive', 'Vehicle_Type', 'Scenario'])
print("Duplicates found:", duplicates.sum())
#%%
# Calculate stock shares for drives within each scenario, vehicle type, and year
df_clean['Stock_Share'] = df_clean.groupby(['Scenario', 'Vehicle_Type', 'Year'])['Stocks'].transform(lambda x: x / x.sum()) *100

# --- 6. Create Stock Share Charts ---
fig_share = px.line(df_clean, x='Year', y='Stock_Share', color='Drive', line_dash='Scenario', 
                    title='Stock Shares Over Years by Vehicle Type Drive', facet_col='Vehicle_Type')
fig_share.update_layout(yaxis_title='Stock Share', xaxis_title='Year')
fig_share.show()

fig_share.write_html('stock_shares_over_years_by_vehicle_type_drive.html')


# %%
