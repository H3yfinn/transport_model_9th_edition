#%%
import pandas as pd
import plotly.express as px
import numpy as np
# ── 1. Load your DataFrame ─────────────────────────────────────────────────────
df = pd.read_excel("../../industry inteprolations tgt.xlsx", sheet_name='interpolations input tgt')
# It must have columns:
#    scenarios, economy, …, fuels (or Fuel), subfuels, 2030, 2031, …, 2060

# ── 2. Normalize year‐columns to ints ───────────────────────────────────────────
# If your year headers are strings like "2030", this converts them to ints.
year_strs = [c for c in df.columns if isinstance(c, str) and c.isdigit()]
df = df.rename(columns={c: int(c) for c in year_strs})

# ── 3. Pick out the years you care about ────────────────────────────────────────
years = sorted(y for y in df.columns if isinstance(y, int) and 2030 <= y <= 2060)
import re
all_years = [year for year in df.columns if re.match(r'^\d{4}$', str(year))]

# #set rows with nas to 0 then drop rows which are all 0s in year cols

# df[years] = df[years].fillna(0)
# df = df[(df[years] != 0).any(axis=1)]

#drop wherte fuels is 19_total

df = df[df['fuels'] != '19_total']
#%%
# ── 4. Interpolate row‑by‑row ─────────────────────────────────────────────────
# This will fill every gap between known values in each row
df[years] = df[years].astype(float).interpolate(axis=1)

#dont adjust growth rate for gas data
# df_gas = df_orig[df_orig.subfuels=='08_01_natural_gas']
df_gas2 = df[df['fuels'] == '08_gas']
# df_orig = df_orig[df_orig.subfuels != '08_01_natural_gas']
df = df[df['fuels'] != '08_gas']  #adjusted to filter out gas data

# Copy the interpolated years
df_orig = df[all_years].copy()

#adjust growth:
#for eyars aafter 2022 adfjust ehe growth rate by X
X = 0.2
years_to_adjust_growth = [year for year in all_years if year > 2022]
# Reduce each annual increment by 5%
for year in years_to_adjust_growth:
    prev = year - 1
    curr = year
    df[curr] = df[prev] + (df_orig[curr] - df_orig[prev]) * (1 - X)
    
#concat teh old gas data on
df = pd.concat([df, df_gas2], ignore_index=True)

df.reset_index(drop=True, inplace=True)


#%%
# ── 5. Pivot to “long” form for Plotly ──────────────────────────────────────────
# Here we keep only the fuel identifier + the year/value columns.
key_cols = ['sectors', 'sub1sectors', 'sub2sectors',  'fuels', 'subfuels']

#%%

df_plot = df.melt(
    id_vars=key_cols,
    value_vars=all_years,
    var_name='Year',
    value_name='Value'
)
df_plot['Year'] = df_plot['Year'].astype(int)



#use the right most column out of sectors that isnt x, and same for fuels:
#e.g. sectors	sub1sectors	sub2sectors
# 14_industry_sector	14_03_manufacturing	14_03_11_nonspecified_industry
# 14_industry_sector	14_03_manufacturing	x
# 14_industry_sector	x	x
#in this, the first row should use sub2sectors, second uses sub1, and first is sectors
df_plot['sectors_'] = np.where(
    df_plot['sub2sectors']!='x', df_plot['sub2sectors'], 
    np.where(df_plot['sub1sectors']!='x', df_plot['sub1sectors'], df_plot['sectors'])
)
df_plot['fuels_'] = np.where(
    df_plot['subfuels']!='x', df_plot['subfuels'], df_plot['fuels']
)
#where sector is 17_nonenergy_use , make that clear in the fuel

df_plot['fuels_'] = np.where(
    df_plot['sectors'] == '17_nonenergy_use', 'gas for ammonia production', df_plot['fuels_']
)
# ── 6. Make the interactive line plot ─────────────────────────────────────────
fig = px.line(
    df_plot,
    x='Year',
    y='Value',
    color='fuels_',
    # line_dash='sectors_',
    title="Interpolated Fuel Series (2030–2060)",
    markers=True
)
fig.update_layout(
    title_font=dict(size=24),
    xaxis_title='Year',
    yaxis_title='Value',
    legend_title='Fuels',
    template='plotly_white'
)
fig.show()
#write to html
import plotly.io as pio
pio.write_html(fig, '../../interpolated_fuel_series.html')
#save as png so we can save it to the sheet
pio.write_image(fig, '../../interpolated_fuel_series.png')
#%%
#plot an area chart. to do this, keep only the fuels subfuels, years cols, drop dupliocates and then p[lot:"
df_plot_area = df_plot.copy()
#where sector is 17_nonenergy_use , make that clear in the fuel
df_plot_area['fuels'] = np.where(
    df_plot_area['sectors'] == '17_nonenergy_use', 'gas for ammonia production', df_plot_area['fuels']
)
df_plot_area = df_plot_area[['fuels', 'subfuels', 'Year', 'Value']].drop_duplicates()
#drop where subfuels != x
df_plot_area = df_plot_area[df_plot_area['subfuels'] == 'x']


fig_area = px.area(
    df_plot_area,
    x='Year',
    y='Value',
    color='fuels',
    title="Area Chart of Fuel Values (2030–2060)",
    markers=True
)
fig_area.update_layout(
    title_font=dict(size=24),
    xaxis_title='Year',
    yaxis_title='Value',
    legend_title='Fuels',
    template='plotly_white'
)
fig_area.show()
pio.write_html(fig_area, '../../interpolated_fuel_series_area.html')
#save as png so we can save it to the sheet
pio.write_image(fig_area, '../../interpolated_fuel_series_area.png')
#%%
# 2. Define your periods
periods = [(start, start + 10) for start in range(min(all_years), max(all_years)+10, 10)]


#filter for years in periods in df_plot_area so we can create a stacked bar chart for every 10th year
df_plot_area_filtered = df_plot_area[df_plot_area['Year'].isin([start for start, end in periods])]
#now create bar charts:
# ── Create Stacked Bar Chart for Every 10th Year ────────────────────────────────
import plotly.express as px
import plotly.io as pio

fig_bar = px.bar(
    df_plot_area_filtered,
    x='Year',
    y='Value',
    color='fuels',
    title="Fuel Distribution Every 10th Year (Stacked)",
    barmode='stack',
    category_orders={"Year": sorted(df_plot_area_filtered["Year"].unique())}
)
fig_bar.update_layout(
    title_font=dict(size=24),
    xaxis_title='Year',
    yaxis_title='Value',
    legend_title='Fuels',
    template='plotly_white'
)
fig_bar.show()

# Save outputs
pio.write_html(fig_bar, '../../stacked_fuel_distribution.html')
pio.write_image(fig_bar, '../../stacked_fuel_distribution.png')
# %%

#%%
#save the df in the orignal excel book with sheet name 'python modelled png industry'
#open new book and save the data and graph to it
# Create a new workbook

import numpy as np
from openpyxl import Workbook
from openpyxl.drawing.image import Image
from openpyxl.utils.dataframe import dataframe_to_rows

workbook = Workbook()
sheet = workbook.active
sheet.title = 'python modelled png industry'

# Save the DataFrame to the sheet
for row in dataframe_to_rows(df, index=False, header=True):
    sheet.append(row)

# Insert the image
img = Image('../../interpolated_fuel_series_area.png')
sheet.add_image(img, 'A1')

img = Image('../../interpolated_fuel_series.png')
sheet.add_image(img, 'A10')

img = Image('../../stacked_fuel_distribution.png')
sheet.add_image(img, 'A5')


# Save the workbook
workbook.save("../../python modelled png industry.xlsx")

# df.to_excel(workbook, sheet_name='python modelled png industry', index=False)

# worksheet = workbook.sheets['python modelled png industry']
# worksheet.insert_image('A1', '../../interpolated_fuel_series.png')
# workbook.close()
#%%


#calcaulte the CAGR for each row in each 10 years of the whole series

def calculate_cagr(start_value, end_value, periods):
    if start_value <= 0 or end_value <= 0 or periods <= 0:
        return None
    return (end_value / start_value) ** (1 / periods) - 1

# Assuming df and calculate_cagr are already defined in the notebook:

# 1. Sum values across all rows for each year
sum_series = df[all_years].sum()

# 2. Define your periods
periods = [(start, start + 10) for start in range(min(all_years), max(all_years), 10)]

# 3. Compute CAGR for each period on the sum series
cagr_values = {}
for start, end in periods:
    cagr_values[f"{start}-{end}"] = calculate_cagr(
        sum_series[start], sum_series[end], end - start
    )

# 4. Build a DataFrame of period vs CAGR
cagr_df = pd.DataFrame.from_dict(cagr_values, orient='index', columns=['CAGR'])
cagr_df.index.name = 'Period'

# 5. Calculate average CAGR across the periods
average_cagr = cagr_df['CAGR'].mean()

# 6. Append average to the table
cagr_df.loc['Average'] = average_cagr
cagr_df


#%%







# %%
import pandas as pd
import re
import plotly.express as px
DO_THIS = True
if DO_THIS:
    # 1. Load your mix table and total generation table
    df_mix = pd.read_excel("../../power interpolations.xlsx", sheet_name="Prev Generation Mix")
    power_total = pd.read_excel("../../power interpolations.xlsx", sheet_name="power total tgt")
    manually_edited_power_shares = pd.read_excel("../../power interpolations.xlsx", sheet_name="Manually Edited Power Shares")
    power_interpolations = pd.read_excel('../../industry inteprolations tgt.xlsx', sheet_name='power interpolations')
    COMPUTE_FROM_ORIGINALS=False
    USE_manually_edited_power_shares  =False
    USE_POWER_INTERPOLATIONS=True
    # 2. Identify the year columns
    year_cols = [int(col) for col in df_mix.columns if re.match(r'^\d{4}$', str(col))]

    # 3. Extract the "Total" row from power_total
    total_row = power_total.loc[
        (power_total["Sector"] == "Electricity") & (power_total["Fuel"] == "Total"),
        year_cols
    ].iloc[0].astype(float)
    # #%%
    if COMPUTE_FROM_ORIGINALS: 
        # 4. Compute fraction share of each fuel per year
        df_share = df_mix.copy()
        df_share[year_cols] = df_share[year_cols].astype(float).div(df_share[year_cols].sum(axis=0), axis=1)

        # Display the percentage share table
        print("Electricity Generation Share by Fuel")
        print(df_share[["Fuel"] + year_cols])
    if USE_POWER_INTERPOLATIONS:
            
        # ── 1. Load your DataFrame ─────────────────────────────────────────────────────
        df=power_interpolations.copy()
        # It must have columns:
        #    scenarios, economy, …, fuels (or Fuel), subfuels, 2030, 2031, …, 2060

        # ── 2. Normalize year‐columns to ints ───────────────────────────────────────────
        # If your year headers are strings like "2030", this converts them to ints.
        year_strs = [c for c in df.columns if isinstance(c, str) and c.isdigit()]
        df = df.rename(columns={c: int(c) for c in year_strs})

        # ── 3. Pick out the years you care about ────────────────────────────────────────
        import re
        all_years = [year for year in df.columns if re.match(r'^\d{4}$', str(year))]

        years = all_years
        
        # ── 4. Interpolate row‑by‑row ─────────────────────────────────────────────────
        # This will fill every gap between known values in each row
        df[years] = df[years].astype(float).interpolate(axis=1)

        # Copy the interpolated years
        df_share = df.copy()

        # #adjust growth:
        # #for eyars aafter 2022 adfjust ehe growth rate by X
        # X = 0.2
        # years_to_adjust_growth = [year for year in all_years if year > 2022]
        # # Reduce each annual increment by 5%
        # for year in years_to_adjust_growth:
        #     prev = year - 1
        #     curr = year
        #     df[curr] = df[prev] + (df_orig[curr] - df_orig[prev]) * (1 - X)
            
    if USE_manually_edited_power_shares:
        df_share = manually_edited_power_shares.copy()
    # #%%
    # 5. Compute actual generation by fuel = share * total generation
    df_gen = df_share.copy()
    df_gen[year_cols] = df_share[year_cols].multiply(total_row, axis=1)

    # Display the generation table
    print("Electricity Generation by Fuel (Actual Values)")
    print(df_gen[["Fuel"] + year_cols])

    # 6. Melt for plotting
    df_gen_long = df_gen.melt(
        id_vars=["Fuel"],
        value_vars=year_cols,
        var_name="Year",
        value_name="Generation"
    )
    df_gen_long["Year"] = df_gen_long["Year"].astype(int)

    # 7. Plot stacked area chart of actual generation
    fig = px.area(
        df_gen_long,
        x="Year",
        y="Generation",
        color="Fuel",
        title="Electricity Generation by Fuel (2000–2060)",
        labels={"Generation": "Generation (TWh or your units)"}
    )
    fig.update_layout(template="plotly_white")
    fig.show()

    #save the proportions so we can adjust them manually:
    df_share.to_excel("../../adjusted_power_shares.xlsx", index=False)
    df_gen.to_excel("../../adjusted_power_gen.xlsx", index=False)
    # #%%

#%%

















#######REF


# %%
import pandas as pd
import re
import plotly.express as px
import numpy as np

# 1. Load your mix table and total generation table
df_mix = pd.read_excel("../../power interpolations REF.xlsx", sheet_name="Prev Generation Mix")
power_total = pd.read_excel("../../power interpolations REF.xlsx", sheet_name="power total ref")
manually_edited_power_shares = pd.read_excel("../../power interpolations REF.xlsx", sheet_name="Manually Edited Power Shares")
power_interpolations = pd.read_excel('../../industry inteprolations REF.xlsx', sheet_name='power interpolations')
COMPUTE_FROM_ORIGINALS=False
USE_manually_edited_power_shares  =False
USE_POWER_INTERPOLATIONS=True
# 2. Identify the year columns
year_cols = [int(col) for col in df_mix.columns if re.match(r'^\d{4}$', str(col))]

# 3. Extract the "Total" row from power_total
total_row = power_total.loc[
    (power_total["Sector"] == "Electricity") & (power_total["Fuel"] == "Total"),
    year_cols
].iloc[0].astype(float)
#%%
if COMPUTE_FROM_ORIGINALS: 
    # 4. Compute fraction share of each fuel per year
    df_share = df_mix.copy()
    df_share[year_cols] = df_share[year_cols].astype(float).div(df_share[year_cols].sum(axis=0), axis=1)

    # Display the percentage share table
    print("Electricity Generation Share by Fuel")
    print(df_share[["Fuel"] + year_cols])
elif USE_POWER_INTERPOLATIONS:
        
    # ── 1. Load your DataFrame ─────────────────────────────────────────────────────
    df=power_interpolations.copy()
    # It must have columns:
    #    scenarios, economy, …, fuels (or Fuel), subfuels, 2030, 2031, …, 2060

    # ── 2. Normalize year‐columns to ints ───────────────────────────────────────────
    # If your year headers are strings like "2030", this converts them to ints.
    year_strs = [c for c in df.columns if isinstance(c, str) and c.isdigit()]
    df = df.rename(columns={c: int(c) for c in year_strs})

    # ── 3. Pick out the years you care about ────────────────────────────────────────
    import re
    all_years = [year for year in df.columns if re.match(r'^\d{4}$', str(year))]

    years = all_years
    
    # ── 4. Interpolate row‑by‑row ─────────────────────────────────────────────────
    # This will fill every gap between known values in each row
    df[years] = df[years].astype(float).interpolate(axis=1)

    # Copy the interpolated years
    df_share = df.copy()

    # #adjust growth:
    # #for eyars aafter 2022 adfjust ehe growth rate by X
    # X = 0.2
    # years_to_adjust_growth = [year for year in all_years if year > 2022]
    # # Reduce each annual increment by 5%
    # for year in years_to_adjust_growth:
    #     prev = year - 1
    #     curr = year
    #     df[curr] = df[prev] + (df_orig[curr] - df_orig[prev]) * (1 - X)
        
else:
    df_share = manually_edited_power_shares.copy()
#%%
# 5. Compute actual generation by fuel = share * total generation
df_gen = df_share.copy()
df_gen[year_cols] = df_share[year_cols].multiply(total_row, axis=1)

# Display the generation table
print("Electricity Generation by Fuel (Actual Values)")
print(df_gen[["Fuel"] + year_cols])

# 6. Melt for plotting
df_gen_long = df_gen.melt(
    id_vars=["Fuel"],
    value_vars=year_cols,
    var_name="Year",
    value_name="Generation"
)
df_gen_long["Year"] = df_gen_long["Year"].astype(int)

# 7. Plot stacked area chart of actual generation
fig = px.area(
    df_gen_long,
    x="Year",
    y="Generation",
    color="Fuel",
    title="Electricity Generation by Fuel (2000–2060)",
    labels={"Generation": "Generation (TWh or your units)"}
)
fig.update_layout(template="plotly_white")
fig.show()

#save the proportions so we can adjust them manually:
df_share.to_excel("../../adjusted_power_shares REF.xlsx", index=False)
df_gen.to_excel("../../adjusted_power_gen REF.xlsx", index=False)
#%%




























