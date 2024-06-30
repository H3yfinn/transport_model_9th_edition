#we will take in the vehicle sales from historical data, then adjust them according to the patterns we expect to see. i.e. nz moves to 100% ev's by 2030.

#we will also create a vehicle sales distribution that replicates what each scenario in the 8th edition shows. We can use this to help also load all stocks data so that we can test the model works like the 8th edition
#%%
#set working directory as one folder back so that config works
import os
import re
import shutil
from turtle import title
sys.path.append(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
###IMPORT GLOBAL VARIABLES FROM config.py
sys.path.append("./config")
from config import *
####Use this to load libraries and set variables. Feel free to edit that file as you need.
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive 
# notebook in vscode #or set to notebook
import plotly
import plotly.express as px
pd.options.plotting.backend = "matplotlib"
import plotly.io as pio
pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook

#%%

#load data
new_sales_shares = pd.read_csv(root_dir + '/' + 'input_data/from_8th/reformatted/vehicle_stocks_change_share_normalised.csv')
#%%
#first we need to separate the sales share of vehicle types from the sales share of drives, by transport type. Since the way the values were created was simply mutliplication, we can jsut reverse that, i think.
#so sum by vehicle type to get the total sales share of each vehicle type
#then if we divide this by the final sales share values for each v-type/drive we can recreate the shares by drive type, witihin each vehicle type.
#now for shares by drive type, witihin each vehicle type, we can create the shares we want.
#sum by vtype economy year and scenario
new_sales_shares_sum = new_sales_shares.copy()

new_sales_shares_sum['V_sum'] = new_sales_shares_sum.groupby(['Economy', 'Scenario', 'Vehicle Type', 'Transport Type', 'Year'])['Value'].transform('sum')

new_sales_shares_sum['Drive_share'] = new_sales_shares_sum['Value']/new_sales_shares_sum['V_sum']

#now we can create the shares we want

#%%

#first create a clean dataframe with all values set to NA after 2019 and annoying cols removed
new_sales_shares_sum_clean = new_sales_shares_sum[['Economy', 'Scenario',  'Transport Type', 'Year', 'Vehicle Type', 'Drive', 'Drive_share']]

new_sales_shares_sum_0 = new_sales_shares_sum_clean.copy()

new_sales_shares_sum_0.loc[new_sales_shares_sum_0['Year']>2019, 'Drive_share'] = np.nan

#sort
new_sales_shares_sum_0 = new_sales_shares_sum_0.sort_values(by=['Economy', 'Scenario', 'Year', 'Vehicle Type', 'Transport Type', 'Drive'])

#%%
################################################################################
#for this we will perfrom the hcanges on passenger and freight separately. So here we will separate them and then combine them at the end
new_sales_shares_passenger_0 = new_sales_shares_sum_0[new_sales_shares_sum_0['Transport Type']=='passenger']
new_sales_shares_freight_0 = new_sales_shares_sum_0[new_sales_shares_sum_0['Transport Type']=='freight']

#for all values we wil interpolate between them with a spline. To set values we will just set the value for the year we want to the value we want, then interpolate between the values we have set and the values in 2017, 2018, 2019. At the end of this we will also normalise all values by vehicle type to sum to 1.

#%%

################################################################################
#first create a set of varaibles to use for the shares we want to set.we will set all the variables now and then save this file for rreference of them later

#create groups of economys based on how fast we expect them to switch to ev's or phevs or fcevs
fast_ev_adoption_econs = ['01_AUS', '03_CDA', '05_PRC', '06_HKC', '08_JPN', '12_NZ', '09_ROK', '17_SGP', '18_CT', '20_USA']#not sure about rok and ct. genralyl these are the more economically developed countries i think

#PASSENGER
#FASt econs
fast_econs_pass_phev1, fast_econs_pass_phev1_year = 0.5, 2027
fast_econs_pass_bev1, fast_econs_pass_bev1_year = 0.7, 2035
fast_econs_pass_bev2, fast_econs_pass_bev2_year = 1, 2040
fast_econs_pass_moto1, fast_econs_pass_moto1_year = 0.7, 2025
fast_econs_pass_moto2, fast_econs_pass_moto2_year = 1, 2030
fast_econs_pass_others1, fast_econs_pass_others1_year = 0, 2035

#slow econs
slow_econs_pass_phev1, slow_econs_pass_phev1_year = 0.5, 2032
slow_econs_pass_bev1, slow_econs_pass_bev1_year = 0.7, 2040
slow_econs_pass_bev2, slow_econs_pass_bev2_year = 1, 2045
slow_econs_pass_moto1, slow_econs_pass_moto1_year = 0.7, 2030
slow_econs_pass_moto2, slow_econs_pass_moto2_year = 1, 2035
slow_econs_pass_others1, slow_econs_pass_others1_year = 0, 2040

#FREIGHT
#fast economys

#for heavy trucks:
fast_econs_freight_ht_fcev_bev_1, fast_econs_freight_ht_fcev_bev_1_year = 0.7, 2040
fast_econs_freight_ht_fcev_bev_2, fast_econs_freight_ht_fcev_bev_2_year = 1, 2045
fast_econs_freight_others_ht_1, fast_econs_freight_others_ht_1_year = 0, 2045
#for light trucks:
fast_econs_freight_lt_phev_1, fast_econs_freight_lt_phev_1_year = 0.5, 2027
fast_econs_freight_lt_bev_1, fast_econs_freight_lt_bev_1_year = 0.7, 2035
fast_econs_freight_lt_bev_2, fast_econs_freight_lt_bev_2_year = 1, 2040
fast_econs_freight_others_lt_1, fast_econs_freight_others_lt_1_year = 0, 2040
#for motorcycles:
fast_econs_freight_moto_bev_1, fast_econs_freight_moto_bev_1_year = 1, 2030
fast_econs_freight_moto_others, fast_econs_freight_moto_others_year = 0, 2030

#slow economys

slow_econs_freight_ht_fcev_bev_1, slow_econs_freight_ht_fcev_bev_1_year = 0.7, 2040
slow_econs_freight_ht_fcev_bev_2, slow_econs_freight_ht_fcev_bev_2_year = 1, 2045
slow_econs_freight_others_ht_1, slow_econs_freight_others_ht_1_year = 0, 2045
#for light trucks:
slow_econs_freight_lt_phev_1, slow_econs_freight_lt_phev_1_year = 0.5, 2027
slow_econs_freight_lt_bev_1, slow_econs_freight_lt_bev_1_year = 0.7, 2035
slow_econs_freight_lt_bev_2, slow_econs_freight_lt_bev_2_year = 1, 2040
slow_econs_freight_others_lt_1, slow_econs_freight_others_lt_1_year = 0, 2040
#for motorcycles:
slow_econs_freight_moto_bev_1, slow_econs_freight_moto_bev_1_year = 1, 2030
slow_econs_freight_moto_others, slow_econs_freight_moto_others_year = 0, 2030

################################################################################
#%%

#get data where econ is in fast_ev_adoption_econs
new_sales_shares_passenger_0_fast_econs = new_sales_shares_passenger_0[new_sales_shares_passenger_0['Economy'].isin(fast_ev_adoption_econs)]

new_sales_shares_passenger_0_fast_econs.loc[(new_sales_shares_passenger_0_fast_econs['Drive']=='bev') & (new_sales_shares_passenger_0_fast_econs['Year']>= fast_econs_pass_bev1_year) & (new_sales_shares_passenger_0_fast_econs['Vehicle Type']!='2w'), 'Drive_share'] = fast_econs_pass_bev1

new_sales_shares_passenger_0_fast_econs.loc[(new_sales_shares_passenger_0_fast_econs['Drive']=='bev') & (new_sales_shares_passenger_0_fast_econs['Year']>=fast_econs_pass_bev2_year) & (new_sales_shares_passenger_0_fast_econs['Vehicle Type']!='2w'), 'Drive_share'] = fast_econs_pass_bev2

new_sales_shares_passenger_0_fast_econs.loc[(new_sales_shares_passenger_0_fast_econs['Drive']=='bev') & (new_sales_shares_passenger_0_fast_econs['Year']>=fast_econs_pass_moto1_year) & (new_sales_shares_passenger_0_fast_econs['Vehicle Type']=='2w'), 'Drive_share'] = fast_econs_pass_moto1

new_sales_shares_passenger_0_fast_econs.loc[(new_sales_shares_passenger_0_fast_econs['Drive']=='bev') & (new_sales_shares_passenger_0_fast_econs['Year']>=fast_econs_pass_moto2_year) & (new_sales_shares_passenger_0_fast_econs['Vehicle Type']=='2w'), 'Drive_share'] = fast_econs_pass_moto2

new_sales_shares_passenger_0_fast_econs.loc[(new_sales_shares_passenger_0_fast_econs['Drive']=='phevd') & (new_sales_shares_passenger_0_fast_econs['Year']==fast_econs_pass_phev1_year) & (new_sales_shares_passenger_0_fast_econs['Vehicle Type']!='2w'), 'Drive_share'] = fast_econs_pass_phev1/2

new_sales_shares_passenger_0_fast_econs.loc[(new_sales_shares_passenger_0_fast_econs['Drive']=='phevg') & (new_sales_shares_passenger_0_fast_econs['Year']==fast_econs_pass_phev1_year) & (new_sales_shares_passenger_0_fast_econs['Vehicle Type']!='2w'), 'Drive_share'] =fast_econs_pass_phev1

new_sales_shares_passenger_0_fast_econs.loc[(new_sales_shares_passenger_0_fast_econs['Drive']!='bev') & (new_sales_shares_passenger_0_fast_econs['Year']>=fast_econs_pass_others1_year), 'Drive_share'] = fast_econs_pass_others1

################################################################################
#And for data where econ is not in fast_ev_adoption_econs:
new_sales_shares_passenger_0_slow_econs = new_sales_shares_passenger_0[~new_sales_shares_passenger_0['Economy'].isin(fast_ev_adoption_econs)]

new_sales_shares_passenger_0_slow_econs.loc[(new_sales_shares_passenger_0_slow_econs['Drive']=='bev') & (new_sales_shares_passenger_0_slow_econs['Year']>=slow_econs_pass_bev1_year) & (new_sales_shares_passenger_0_slow_econs['Vehicle Type']!='2w'), 'Drive_share'] = slow_econs_pass_bev1

new_sales_shares_passenger_0_slow_econs.loc[(new_sales_shares_passenger_0_slow_econs['Drive']=='bev') & (new_sales_shares_passenger_0_slow_econs['Year']>=slow_econs_pass_bev2_year) & (new_sales_shares_passenger_0_slow_econs['Vehicle Type']!='2w'), 'Drive_share'] = slow_econs_pass_bev2

new_sales_shares_passenger_0_slow_econs.loc[(new_sales_shares_passenger_0_slow_econs['Drive']=='bev') & (new_sales_shares_passenger_0_slow_econs['Year']>=slow_econs_pass_moto1_year) & (new_sales_shares_passenger_0_slow_econs['Vehicle Type']=='2w'), 'Drive_share'] = slow_econs_pass_moto1

new_sales_shares_passenger_0_slow_econs.loc[(new_sales_shares_passenger_0_slow_econs['Drive']=='bev') & (new_sales_shares_passenger_0_slow_econs['Year']>=slow_econs_pass_moto2_year) & (new_sales_shares_passenger_0_slow_econs['Vehicle Type']=='2w'), 'Drive_share'] = slow_econs_pass_moto2

new_sales_shares_passenger_0_slow_econs.loc[(new_sales_shares_passenger_0_slow_econs['Drive']=='phevd') & (new_sales_shares_passenger_0_slow_econs['Year']==slow_econs_pass_phev1_year) & (new_sales_shares_passenger_0_slow_econs['Vehicle Type']!='2w'), 'Drive_share'] = slow_econs_pass_phev1/2

new_sales_shares_passenger_0_slow_econs.loc[(new_sales_shares_passenger_0_slow_econs['Drive']=='phevg') & (new_sales_shares_passenger_0_slow_econs['Year']==slow_econs_pass_phev1_year) & (new_sales_shares_passenger_0_slow_econs['Vehicle Type']!='2w'), 'Drive_share'] =slow_econs_pass_phev1

new_sales_shares_passenger_0_slow_econs.loc[(new_sales_shares_passenger_0_slow_econs['Drive']!='bev') & (new_sales_shares_passenger_0_slow_econs['Year']>=slow_econs_pass_others1_year), 'Drive_share'] = slow_econs_pass_others1

################################################################################

#concatenate data again
new_sales_shares_passenger_0_all_econs = pd.concat([new_sales_shares_passenger_0_fast_econs, new_sales_shares_passenger_0_slow_econs])

#%%
################################################################################################################################################################
#FREIGHT#

#get data where econ is in fast_ev_adoption_econs
new_sales_shares_freight_0_fast_econs = new_sales_shares_freight_0[new_sales_shares_freight_0['Economy'].isin(fast_ev_adoption_econs)]


#HT
new_sales_shares_freight_0_fast_econs.loc[(new_sales_shares_freight_0_fast_econs['Drive'].isin(['fcev', 'bev']) & (new_sales_shares_freight_0_fast_econs['Year']>=fast_econs_freight_ht_fcev_bev_1_year) & (new_sales_shares_freight_0_fast_econs['Vehicle Type']=='ht')), 'Drive_share'] = fast_econs_freight_ht_fcev_bev_1

new_sales_shares_freight_0_fast_econs.loc[(new_sales_shares_freight_0_fast_econs['Drive'].isin(['fcev', 'bev']) & (new_sales_shares_freight_0_fast_econs['Year']>=fast_econs_freight_ht_fcev_bev_2_year) & (new_sales_shares_freight_0_fast_econs['Vehicle Type']=='ht')), 'Drive_share'] = fast_econs_freight_ht_fcev_bev_2

new_sales_shares_freight_0_fast_econs.loc[(~new_sales_shares_freight_0_fast_econs['Drive'].isin(['fcev', 'bev']) & (new_sales_shares_freight_0_fast_econs['Year']>=fast_econs_freight_others_ht_1_year) & (new_sales_shares_freight_0_fast_econs['Vehicle Type']=='ht')), 'Drive_share'] = fast_econs_freight_others_ht_1#double check this

#LT
new_sales_shares_freight_0_fast_econs.loc[(new_sales_shares_freight_0_fast_econs['Drive'].isin(['phevd', 'phevg']) & (new_sales_shares_freight_0_fast_econs['Year']>=fast_econs_freight_lt_phev_1_year) & (new_sales_shares_freight_0_fast_econs['Vehicle Type']=='lt')), 'Drive_share'] = fast_econs_freight_lt_phev_1

new_sales_shares_freight_0_fast_econs.loc[(new_sales_shares_freight_0_fast_econs['Drive'].isin(['bev']) & (new_sales_shares_freight_0_fast_econs['Year']>=fast_econs_freight_lt_bev_1_year) & (new_sales_shares_freight_0_fast_econs['Vehicle Type']=='lt')), 'Drive_share'] = fast_econs_freight_lt_bev_1

new_sales_shares_freight_0_fast_econs.loc[(new_sales_shares_freight_0_fast_econs['Drive'].isin(['bev']) & (new_sales_shares_freight_0_fast_econs['Year']>=fast_econs_freight_lt_bev_2_year) & (new_sales_shares_freight_0_fast_econs['Vehicle Type']=='lt')), 'Drive_share'] = fast_econs_freight_lt_bev_2

new_sales_shares_freight_0_fast_econs.loc[(~new_sales_shares_freight_0_fast_econs['Drive'].isin(['bev']) & (new_sales_shares_freight_0_fast_econs['Year']>=fast_econs_freight_others_lt_1_year) & (new_sales_shares_freight_0_fast_econs['Vehicle Type']=='lt')), 'Drive_share'] = fast_econs_freight_others_lt_1

#2/3W
new_sales_shares_freight_0_fast_econs.loc[(new_sales_shares_freight_0_fast_econs['Drive']=='bev') & (new_sales_shares_freight_0_fast_econs['Year']>=fast_econs_freight_moto_bev_1_year) & (new_sales_shares_freight_0_fast_econs['Vehicle Type']=='2w'), 'Drive_share'] = fast_econs_freight_moto_bev_1

new_sales_shares_freight_0_fast_econs.loc[(new_sales_shares_freight_0_fast_econs['Drive']!='bev') & (new_sales_shares_freight_0_fast_econs['Year']>=fast_econs_freight_moto_others_year) & (new_sales_shares_freight_0_fast_econs['Vehicle Type']=='2w'), 'Drive_share'] = fast_econs_freight_moto_others


################################################################################
#And for data where econ is not in fast_ev_adoption_econs:
new_sales_shares_freight_0_slow_econs = new_sales_shares_freight_0[~new_sales_shares_freight_0['Economy'].isin(fast_ev_adoption_econs)]

#HT
new_sales_shares_freight_0_slow_econs.loc[(new_sales_shares_freight_0_slow_econs['Drive'].isin(['fcev', 'bev']) & (new_sales_shares_freight_0_slow_econs['Year']>=slow_econs_freight_ht_fcev_bev_1_year) & (new_sales_shares_freight_0_slow_econs['Vehicle Type']=='ht')), 'Drive_share'] = slow_econs_freight_ht_fcev_bev_1

new_sales_shares_freight_0_slow_econs.loc[(new_sales_shares_freight_0_slow_econs['Drive'].isin(['fcev', 'bev']) & (new_sales_shares_freight_0_slow_econs['Year']>=slow_econs_freight_ht_fcev_bev_2_year) & (new_sales_shares_freight_0_slow_econs['Vehicle Type']=='ht')), 'Drive_share'] = slow_econs_freight_ht_fcev_bev_2

new_sales_shares_freight_0_slow_econs.loc[(~new_sales_shares_freight_0_slow_econs['Drive'].isin(['fcev', 'bev']) & (new_sales_shares_freight_0_slow_econs['Year']>=slow_econs_freight_others_ht_1_year) & (new_sales_shares_freight_0_slow_econs['Vehicle Type']=='ht')), 'Drive_share'] = slow_econs_freight_others_ht_1#double check this

#LT
new_sales_shares_freight_0_slow_econs.loc[(new_sales_shares_freight_0_slow_econs['Drive'].isin(['phevd', 'phevg']) & (new_sales_shares_freight_0_slow_econs['Year']>=slow_econs_freight_lt_phev_1_year) & (new_sales_shares_freight_0_slow_econs['Vehicle Type']=='lt')), 'Drive_share'] = slow_econs_freight_lt_phev_1

new_sales_shares_freight_0_slow_econs.loc[(new_sales_shares_freight_0_slow_econs['Drive'].isin(['bev']) & (new_sales_shares_freight_0_slow_econs['Year']>=slow_econs_freight_lt_bev_1_year) & (new_sales_shares_freight_0_slow_econs['Vehicle Type']=='lt')), 'Drive_share'] = slow_econs_freight_lt_bev_1

new_sales_shares_freight_0_slow_econs.loc[(new_sales_shares_freight_0_slow_econs['Drive'].isin(['bev']) & (new_sales_shares_freight_0_slow_econs['Year']>=slow_econs_freight_lt_bev_2_year) & (new_sales_shares_freight_0_slow_econs['Vehicle Type']=='lt')), 'Drive_share'] = slow_econs_freight_lt_bev_2

new_sales_shares_freight_0_slow_econs.loc[(~new_sales_shares_freight_0_slow_econs['Drive'].isin(['bev']) & (new_sales_shares_freight_0_slow_econs['Year']>=slow_econs_freight_others_lt_1_year) & (new_sales_shares_freight_0_slow_econs['Vehicle Type']=='lt')), 'Drive_share'] = slow_econs_freight_others_lt_1

#2/3W
new_sales_shares_freight_0_slow_econs.loc[(new_sales_shares_freight_0_slow_econs['Drive']=='bev') & (new_sales_shares_freight_0_slow_econs['Year']>=slow_econs_freight_moto_bev_1_year) & (new_sales_shares_freight_0_slow_econs['Vehicle Type']=='2w'), 'Drive_share'] = slow_econs_freight_moto_bev_1

new_sales_shares_freight_0_slow_econs.loc[(new_sales_shares_freight_0_slow_econs['Drive']!='bev') & (new_sales_shares_freight_0_slow_econs['Year']>=slow_econs_freight_moto_others_year) & (new_sales_shares_freight_0_slow_econs['Vehicle Type']=='2w'), 'Drive_share'] = slow_econs_freight_moto_others

#%%
#combine the two dataframes:
new_sales_shares_freight_0_all_econs = pd.concat([new_sales_shares_freight_0_fast_econs, new_sales_shares_freight_0_slow_econs])

#%%

################################################################################
################################################################################################################################################################################################################################################################################################################################################################################################################################################################################################

#concatenate transport types
new_sales_shares_pre_interp = pd.concat([new_sales_shares_freight_0_all_econs, new_sales_shares_passenger_0_all_econs])
#%%
#finally, before we interpolate, if a value is na (missing) in 2017, 2018 or 2019, it is because it has no sales share at all for its vehicle type. we will set the sales share to the average of all otehr economys values for that vehicle type and drive type #this is jsut an error in the orignal data

#get missing data
new_sales_shares_pre_interp_missing = new_sales_shares_pre_interp.loc[(new_sales_shares_pre_interp['Year']>=2017) & (new_sales_shares_pre_interp['Year']<=2019) & (new_sales_shares_pre_interp['Drive_share'].isna())]

#drop cols we dont need
new_sales_shares_pre_interp_missing = new_sales_shares_pre_interp_missing.drop(columns=['Drive_share'])

#keep all other data in another df
new_sales_shares_pre_interp_not_missing = new_sales_shares_pre_interp.loc[~((new_sales_shares_pre_interp['Year']>=2017) & (new_sales_shares_pre_interp['Year']<=2019) & (new_sales_shares_pre_interp['Drive_share'].isna()))]

#get avg of not missing data
new_sales_shares_pre_interp_not_missing_avg = new_sales_shares_pre_interp_not_missing.groupby(['Year', 'Vehicle Type', 'Transport Type','Drive', 'Scenario'])['Drive_share'].mean().reset_index()

#join avg of not missing to missing
new_sales_shares_pre_interp_missing = new_sales_shares_pre_interp_missing.merge(new_sales_shares_pre_interp_not_missing_avg, on=['Year', 'Vehicle Type', 'Transport Type','Drive', 'Scenario'], how='left')

#and concat back to not missing to recreate original full set
new_sales_shares_concat = pd.concat([new_sales_shares_pre_interp_missing, new_sales_shares_pre_interp_not_missing])

#reset index. for some reason this needed to happen. dont know why
new_sales_shares_concat = new_sales_shares_concat.reset_index(drop=True)
#%%
#order data by year
new_sales_shares_concat_interp = new_sales_shares_concat.sort_values(by=['Economy', 'Scenario', 'Year', 'Transport Type', 'Vehicle Type', 'Drive']).copy()

#do interpolation using spline adn order = X
X_order = 3#the higher the order the more smoothing but the less detail
new_sales_shares_concat_interp['Drive_share'] = new_sales_shares_concat_interp.groupby(['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive'])['Drive_share'].apply(lambda group: group.interpolate(method='spline', order=X_order))

#%%
#where any values are negatives just set them to 0
new_sales_shares_concat_interp.loc[new_sales_shares_concat_interp['Drive_share']<0, 'Drive_share'] = 0

#now we just need to normalise by vehicle type
new_sales_shares_concat_interp['D_sum'] = new_sales_shares_concat_interp.groupby(['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Year'])['Drive_share'].transform('sum')

new_sales_shares_concat_interp['Drive_share'] = new_sales_shares_concat_interp['Drive_share']/new_sales_shares_concat_interp['D_sum']

#%%
#drop uneeded cols
new_sales_shares_interp_by_drive = new_sales_shares_concat_interp.drop(['D_sum'], axis=1)
original_new_sales_shares_by_vehicle = new_sales_shares_sum.drop(['Value', 'Drive_share'], axis=1)
#now merge the values onto the oroginal df and times by the vehicle type shares
new_sales_shares_all = new_sales_shares_interp_by_drive.merge(original_new_sales_shares_by_vehicle, on=['Economy', 'Scenario', 'Year', 'Transport Type', 'Vehicle Type', 'Drive'], how='left')

#%%
#times the values to get the final values
new_sales_shares_all['Value'] = new_sales_shares_all['V_sum']*new_sales_shares_all['Drive_share']

#drop uneeded cols
new_sales_shares_all = new_sales_shares_all.drop(['V_sum', 'Drive_share'], axis=1)
###############################################################################
#%%
#now we will plot the data to see if it looks ok and capore to original data
#plot only ref data for now, for each tranposrt type:

new_sales_shares_ref_plot = new_sales_shares_all.loc[new_sales_shares_all['Scenario']=='Reference']
new_sales_shares_ref_original = new_sales_shares.loc[new_sales_shares['Scenario']=='Reference']

for ttype in new_sales_shares_ref_plot['Transport Type'].unique():
       #filter for ttype
       new_sales_shares_ref_plot_ttype = new_sales_shares_ref_plot.loc[new_sales_shares_ref_plot['Transport Type']==ttype]
       #order data
       new_sales_shares_ref_plot_ttype = new_sales_shares_ref_plot_ttype.sort_values(by=['Economy', 'Year', 'Vehicle Type', 'Drive'])
       #plot using plotly
       title = 'New Sales Shares by Drive Type for {}'.format(ttype)

       #plot
       fig = px.line(new_sales_shares_ref_plot_ttype, x="Year", y="Value", color="Vehicle Type", line_dash='Drive', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
              #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
       fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

       plotly.offline.plot(fig, filename=root_dir + '\\' + './plotting_output/' + title + '.html')
       fig.write_image(root_dir + '\\' + "./plotting_output/static/" + title + '.png', scale=1, width=2000, height=1500)

       #and plot the orignal data for comparison:

       #filter for ttype
       new_sales_shares_ref_original_ttype = new_sales_shares_ref_original.loc[new_sales_shares_ref_original['Transport Type']==ttype]
       #order data
       new_sales_shares_ref_original_ttype = new_sales_shares_ref_original_ttype.sort_values(by=['Economy', 'Year', 'Vehicle Type', 'Drive'])
       title = 'New Sales Shares by Drive Type Original Data for {}'.format(ttype)

       #plot
       fig = px.line(new_sales_shares_ref_original_ttype, x="Year", y="Value", color="Vehicle Type", line_dash='Drive', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
              #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
       fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

       plotly.offline.plot(fig, filename=root_dir + '\\' + './plotting_output/' + title + '.html')
       fig.write_image(root_dir + '\\' + "./plotting_output/static/" + title + '.png', scale=1, width=2000, height=1500)

###############################################################################

#%%
#save using scenario_id
new_sales_shares_all.to_csv(root_dir + '/' + 'input_data/calculated/vehicle_stocks_change_share_{}.csv'.format(scenario_id), index = False)

#save the variables we used to calculate the data by just saving this file
shutil.copyfile(root_dir + '/' + 'other_code/create_user_inputs/edit_vehicle_sales_share_data.py', 'input_data/calculated/saved_scripts/edit_vehicle_sales_share_data_{}.py'.format(scenario_id))

#%%
#also save the data to the user_input_spreadsheet
with pd.ExcelWriter('input_data/user_input_spreadsheet.xlsx',engine='openpyxl', mode='a',if_sheet_exists = 'replace') as writer: 
       new_sales_shares_all.to_excel(writer, sheet_name='Vehicle_sales_share',  index=False)

#%%
REVERT = False
if REVERT:
       #if we want to revert the cahgnes so we use the data we imported to created this data at first in the spreadsheet:
       with pd.ExcelWriter('input_data/user_input_spreadsheet.xlsx',engine='openpyxl', mode='a',if_sheet_exists = 'replace') as writer:
              new_sales_shares.to_excel(writer, sheet_name='Vehicle_sales_share',  index=False)
       
#%%


