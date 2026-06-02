"""
Extract USA base year road transport data for model redesign.

For each vehicle_type × drive combination, outputs:
  stocks, mileage, fuel_intensity (MJ/km), travel_km, energy_calculated_PJ
  + energy from ESTO for cross-check

Energy formula (row-by-row):
  travel_km = stocks_vehicles × mileage_km_per_veh
  energy_PJ = travel_km × fuel_intensity_MJ_per_km × 1e-9
     (because km × MJ/km = MJ; 1 PJ = 1e9 MJ → divide by 1e9)

Data source priority:
  1. intermediate_data/model_inputs/{latest_date}/20_USA_road_model_input_wide.csv
     (post-optimisation, energy matched to ESTO)
  2. input_data/transport_data_system/combined_data_DATE20250122.csv
     (raw input, pre-optimisation)
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# ── Configuration ─────────────────────────────────────────────────────────────
ROOT_DIR  = Path(__file__).parents[2]
ECONOMY   = '20_USA'
BASE_YEAR = 2022
ESTO_SCENARIO = 'target'  # set to 'reference' to switch

# Maps this model's drive types → LEAP drive categories
# Edit this dict to match your LEAP drive taxonomy
LEAP_DRIVE_MAP = {
    'ice_g':  'ice',
    'ice_d':  'ice',
    'cng':    'ice',
    'lpg':    'ice',
    'lng':    'ice',
    'phev_g': 'erev',
    'phev_d': 'erev',
    'bev':    'bev',
    'fcev':   'fcev',
}

# Primary fuel (ESTO subfuel code) for each drive type
# For erev (phev), primary = liquid fuel; electricity is secondary
PRIMARY_FUEL_MAP = {
    'ice_g':  '07_01_motor_gasoline',
    'ice_d':  '07_07_gas_diesel_oil',
    'cng':    '08_01_natural_gas',
    'lpg':    '07_09_lpg',
    'lng':    '08_02_lng',
    'phev_g': '07_01_motor_gasoline',
    'phev_d': '07_07_gas_diesel_oil',
    'bev':    '17_electricity',
    'fcev':   '16_x_hydrogen',
}

FUEL_LABEL_MAP = {
    '07_01_motor_gasoline': 'gasoline',
    '07_07_gas_diesel_oil': 'diesel',
    '07_09_lpg':            'lpg',
    '08_01_natural_gas':    'natural_gas',
    '08_02_lng':            'lng',
    '17_electricity':       'electricity',
    '17_electricity_x':     'electricity',   # ESTO uses fuels='17_electricity', subfuels='x'
    '16_x_hydrogen':        'hydrogen',
    '16_05_biogasoline':    'biogasoline',   # ESTO only — blended into model gasoline
    '16_06_biodiesel':      'biodiesel',     # ESTO only — blended into model diesel
}

OUTPUT_DIR = ROOT_DIR / 'other_code' / 'analysis_code' / 'output'
OUTPUT_DIR.mkdir(exist_ok=True)


# ── Data loading ──────────────────────────────────────────────────────────────

def find_latest_road_model_input(root_dir, economy):
    """Return path to latest road_model_input_wide CSV, or None."""
    model_inputs_dir = root_dir / 'intermediate_data' / 'model_inputs'
    if not model_inputs_dir.exists():
        return None
    date_folders = sorted(
        [d for d in model_inputs_dir.iterdir() if d.is_dir()],
        reverse=True
    )
    for folder in date_folders:
        candidate = folder / f'{economy}_road_model_input_wide.csv'
        if candidate.exists():
            return candidate
    return None


def load_from_intermediate(path):
    """Load wide road model input from intermediate data."""
    df = pd.read_csv(path)
    # Keep reference scenario only (base year data is scenario-independent)
    if 'Scenario' in df.columns:
        scenarios = df['Scenario'].unique()
        scenario = 'reference' if 'reference' in scenarios else scenarios[0]
        df = df[df['Scenario'] == scenario]
    return df, 'intermediate (optimised)'


def load_from_combined_data(root_dir, economy, base_year):
    """Load and pivot combined_data into wide format."""
    path = root_dir / 'input_data' / 'transport_data_system' / 'combined_data_DATE20250122.csv'
    print(f'  Reading: {path}')
    raw = pd.read_csv(path)
    # Warn if stock coverage is thin for this year (e.g. 2022 only has EV/PHEV/FCEV stocks)
    stock_check = raw[(raw.economy == economy) & (raw.date == base_year) & (raw.medium == 'road') &
                      (raw.measure == 'stocks') & (raw.drive != 'all') & (raw.vehicle_type != 'all')]
    n_nonzero = (stock_check.value > 0).sum()
    n_total   = len(stock_check)
    if n_nonzero < n_total * 0.5:
        print(f'  WARNING: Only {n_nonzero}/{n_total} road stock rows are non-zero for {base_year}.')
        print(f'  ICE stocks are likely absent. Rows without stocks will have energy_calculated=0.')
        print(f'  Run the model to generate the optimised intermediate file for complete {base_year} data.')
    road = raw[
        (raw.economy == economy) &
        (raw.date == base_year) &
        (raw.medium == 'road') &
        (raw.measure.isin(['stocks', 'mileage', 'efficiency', 'energy'])) &
        (raw.drive != 'all') &
        (raw.vehicle_type != 'all')
    ].copy()
    wide = road.pivot_table(
        index=['economy', 'date', 'medium', 'drive', 'vehicle_type', 'transport_type'],
        columns='measure',
        values='value',
        aggfunc='first'
    ).reset_index()
    wide.columns.name = None
    wide = wide.rename(columns={
        'economy':        'Economy',
        'date':           'Date',
        'medium':         'Medium',
        'drive':          'Drive',
        'vehicle_type':   'Vehicle Type',
        'transport_type': 'Transport Type',
        'stocks':         'Stocks',
        'mileage':        'Mileage',
        'efficiency':     'Efficiency',
        'energy':         'Energy',
    })
    wide['Scenario'] = 'reference'
    return wide, 'combined_data (raw, pre-optimisation)'


def load_road_model_input(root_dir, economy, base_year):
    intermediate_path = find_latest_road_model_input(root_dir, economy)
    if intermediate_path is not None:
        print(f'Found optimised file: {intermediate_path}')
        df, source = load_from_intermediate(intermediate_path)
    else:
        print('No intermediate file found — using combined_data')
        df, source = load_from_combined_data(root_dir, economy, base_year)
    return df, source


def load_esto_road_energy(root_dir, economy, base_year, scenario):
    """Return road energy from ESTO by fuel_id (no passenger/freight split in ESTO road data)."""
    path = root_dir / 'input_data' / '9th_model_inputs' / 'model_df_wide_20250221.csv'
    print(f'  Reading ESTO: {path}')
    esto = pd.read_csv(path)

    road = esto[
        (esto.economy == economy) &
        (esto.scenarios == scenario) &
        (esto.sub1sectors == '15_02_road') &
        (esto.is_subtotal == False) &
        (esto[str(base_year)].notna())
    ].copy()

    road['energy_esto_PJ'] = road[str(base_year)]

    # Use subfuel code where set, else fall back to fuel-level code
    # (electricity rows have subfuels='x', so map to '17_electricity' via fuels col)
    road['fuel_id'] = road.apply(
        lambda r: r['subfuels'] if r['subfuels'] != 'x' else r['fuels'],
        axis=1
    )

    # Exclude subtotal fuels and zero/negative rows
    exclude_fuels = {'19_total', '20_total_renewables', '21_modern_renewables'}
    road = road[~road['fuels'].isin(exclude_fuels)].copy()
    road = road[road['energy_esto_PJ'] > 0].copy()

    return road.groupby('fuel_id')['energy_esto_PJ'].sum().reset_index()


# ── Build output table ────────────────────────────────────────────────────────

def build_road_table(road_wide, esto_road, base_year):
    df = road_wide.copy()

    # Filter to base year and road if those columns exist
    if 'Date' in df.columns:
        df = df[df['Date'] == base_year]
    if 'Medium' in df.columns:
        df = df[df['Medium'] == 'road']

    # Resolve column names robustly
    def col(name):
        if name in df.columns:
            return name
        for c in df.columns:
            if c.lower() == name.lower():
                return c
        return None

    c_stocks   = col('Stocks')
    c_mileage  = col('Mileage')
    c_eff      = col('Efficiency')
    c_energy   = col('Energy')
    c_drive    = col('Drive')
    c_vtype    = col('Vehicle Type')
    c_ttype    = col('Transport Type')

    if any(c is None for c in [c_stocks, c_mileage, c_eff, c_drive, c_vtype, c_ttype]):
        missing = [n for n, c in zip(
            ['Stocks','Mileage','Efficiency','Drive','Vehicle Type','Transport Type'],
            [c_stocks, c_mileage, c_eff, c_drive, c_vtype, c_ttype]
        ) if c is None]
        raise ValueError(f'Missing required columns: {missing}. Available: {df.columns.tolist()}')

    out = pd.DataFrame({
        'transport_type':           df[c_ttype].values,
        'vehicle_type':             df[c_vtype].values,
        'drive':                    df[c_drive].values,
    })

    out['leap_drive']          = out['drive'].map(LEAP_DRIVE_MAP)
    out['primary_fuel_id']     = out['drive'].map(PRIMARY_FUEL_MAP)
    out['fuel_label']          = out['primary_fuel_id'].map(FUEL_LABEL_MAP)
    out['stocks_vehicles']     = df[c_stocks].values
    out['mileage_km_per_veh']  = df[c_mileage].values
    out['travel_km']           = df[c_stocks].values * df[c_mileage].values

    # Efficiency: model stores km/PJ; convert to MJ/km for intuitive reading
    # Energy check (row by row):
    #   energy_PJ = travel_km [km] * fuel_intensity [MJ/km] / 1e9
    #   because: km * MJ/km = MJ, and 1 PJ = 1e9 MJ
    # Derivation: fuel_intensity [MJ/km] = 1e9 [MJ/PJ] / efficiency [km/PJ]
    eff_km_pj = df[c_eff].replace(0, np.nan).values
    out['efficiency_km_per_PJ']     = eff_km_pj
    out['fuel_intensity_MJ_per_km'] = np.where(eff_km_pj > 0, 1e9 / eff_km_pj, np.nan)

    out['energy_calculated_PJ'] = out['travel_km'] * out['fuel_intensity_MJ_per_km'] / 1e9
    out['energy_input_PJ']      = df[c_energy].values if c_energy else np.nan

    # Join ESTO energy at fuel level (ESTO road has no passenger/freight split)
    esto_map = esto_road.set_index('fuel_id')['energy_esto_PJ'].to_dict()
    out['energy_esto_PJ_at_fuel_level'] = out['primary_fuel_id'].map(esto_map)

    # Human-readable formula note for each row
    out['energy_calc_notes'] = out.apply(
        lambda r: (
            f"energy_PJ = stocks ({r['stocks_vehicles']:,.0f}) "
            f"x mileage ({r['mileage_km_per_veh']:,.0f} km/veh) "
            f"x fuel_intensity ({r['fuel_intensity_MJ_per_km']:.4f} MJ/km) "
            f"/ 1e9  =  {r['energy_calculated_PJ']:.3f} PJ"
        ) if pd.notna(r['fuel_intensity_MJ_per_km']) else 'no efficiency data',
        axis=1
    )

    out = out.sort_values(['transport_type', 'vehicle_type', 'drive']).reset_index(drop=True)
    return out


# ── Summaries ─────────────────────────────────────────────────────────────────

def print_summary(result, esto_road):
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 240)
    pd.set_option('display.float_format', '{:,.3f}'.format)

    nonzero = result[result['stocks_vehicles'] > 0].copy()

    print('\n== Road data -- non-zero stocks rows ==')
    display_cols = [
        'transport_type', 'vehicle_type', 'drive', 'leap_drive', 'fuel_label',
        'stocks_vehicles', 'mileage_km_per_veh',
        'fuel_intensity_MJ_per_km', 'travel_km',
        'energy_calculated_PJ', 'energy_input_PJ',
    ]
    print(nonzero[display_cols].to_string(index=False))

    print('\n== Energy comparison: calculated vs ESTO (by fuel, road total) ==')
    print('NOTE: ESTO road data has no passenger/freight split.')
    print('      Biofuels (biogasoline, biodiesel) are blended into gasoline/diesel in the model.\n')

    agg = result.groupby(['primary_fuel_id', 'fuel_label']).agg(
        energy_calc_PJ=('energy_calculated_PJ', 'sum'),
        energy_input_PJ=('energy_input_PJ', 'sum'),
    ).reset_index()

    esto_for_merge = esto_road.rename(columns={'fuel_id': 'primary_fuel_id'})
    esto_for_merge['fuel_label'] = esto_for_merge['primary_fuel_id'].map(FUEL_LABEL_MAP)

    comp = agg.merge(esto_for_merge, on='primary_fuel_id', how='outer', suffixes=('', '_esto'))
    comp['fuel_label'] = comp['fuel_label'].combine_first(comp['fuel_label_esto'])
    comp = comp.drop(columns=['fuel_label_esto'], errors='ignore').fillna(0)

    comp['calc_vs_esto_%'] = np.where(
        comp['energy_esto_PJ'] > 0,
        ((comp['energy_calc_PJ'] - comp['energy_esto_PJ']) / comp['energy_esto_PJ'] * 100).round(1),
        np.nan
    )
    comp['input_vs_esto_%'] = np.where(
        comp['energy_esto_PJ'] > 0,
        ((comp['energy_input_PJ'] - comp['energy_esto_PJ']) / comp['energy_esto_PJ'] * 100).round(1),
        np.nan
    )
    print(comp[['primary_fuel_id','fuel_label','energy_calc_PJ','energy_input_PJ',
                'energy_esto_PJ','calc_vs_esto_%','input_vs_esto_%']].to_string(index=False))

    esto_total = esto_road['energy_esto_PJ'].sum()
    print(f'\n  ESTO total road energy includes biofuels blended into model\'s gasoline/diesel.')
    print(f'  ESTO motor_gasoline + biogasoline = {esto_road[esto_road.fuel_id.isin(["07_01_motor_gasoline","16_05_biogasoline"])].energy_esto_PJ.sum():,.1f} PJ')
    print(f'  ESTO gas_diesel_oil + biodiesel   = {esto_road[esto_road.fuel_id.isin(["07_07_gas_diesel_oil","16_06_biodiesel"])].energy_esto_PJ.sum():,.1f} PJ')

    print('\n== Totals ==')
    print(f"  Calculated energy (all road):  {result['energy_calculated_PJ'].sum():>10,.1f} PJ")
    if not result['energy_input_PJ'].isna().all():
        print(f"  Input energy (all road):       {result['energy_input_PJ'].sum():>10,.1f} PJ")
    print(f"  ESTO road energy ({ESTO_SCENARIO}):    {esto_road['energy_esto_PJ'].sum():>10,.1f} PJ")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f'== USA Road Base Year Data Extraction ==')
    print(f'Economy: {ECONOMY}  Base year: {BASE_YEAR}  ESTO scenario: {ESTO_SCENARIO}\n')

    road_wide, source = load_road_model_input(ROOT_DIR, ECONOMY, BASE_YEAR)
    print(f'Data source: {source}')
    print(f'Loaded {len(road_wide)} rows, columns: {road_wide.columns.tolist()}\n')

    esto_road = load_esto_road_energy(ROOT_DIR, ECONOMY, BASE_YEAR, ESTO_SCENARIO)

    result = build_road_table(road_wide, esto_road, BASE_YEAR)

    out_path = OUTPUT_DIR / f'{ECONOMY}_road_base_year_{BASE_YEAR}.csv'
    result.to_csv(out_path, index=False)
    print(f'\nSaved: {out_path}  ({len(result)} rows)')

    print_summary(result, esto_road)


if __name__ == '__main__':
    main()
