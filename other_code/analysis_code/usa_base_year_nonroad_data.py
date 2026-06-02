"""
Extract USA base year non-road transport data for model redesign.

For each medium x transport_type, outputs:
  activity, intensity, energy (calculated + ESTO comparison)
  plus ESTO fuel breakdown as reference

Energy formula (row-by-row):
  energy_PJ = activity_Bkm * intensity_MJ_per_km
  where:
    activity_Bkm  = activity [pkm or tkm] / 1e9    (billion passenger-km or tonne-km)
    intensity_MJ_per_km = intensity [PJ/pkm or tkm] * 1e9   (MJ per pkm or tkm)
  Check: Bkm * MJ/km = 1e9 km * MJ/km = 1e9 MJ = 1 PJ exactly

Non-road mediums: air, rail, ship (+ pipeline, nonspecified where present)
No vehicle_type or drive breakdown — everything is 'all' in the input data.
Fuel breakdown comes from ESTO only (model assigns fuels via fuel-mixing spreadsheets).

Data source priority:
  1. intermediate_data/model_inputs/{latest_date}/20_USA_non_road_model_input_wide.csv
  2. input_data/transport_data_system/combined_data_DATE20250122.csv
"""

import os
from pathlib import Path
import pandas as pd
import numpy as np

# ── Configuration ─────────────────────────────────────────────────────────────
ROOT_DIR  = Path(__file__).parents[2]
ECONOMY   = '20_USA'
BASE_YEAR = 2022
ESTO_SCENARIO = 'target'  # set to 'reference' to switch

# Maps ESTO sub1sectors to model medium labels
ESTO_SECTOR_TO_MEDIUM = {
    '15_01_domestic_air_transport': 'air',
    '15_03_rail':                   'rail',
    '15_04_domestic_navigation':    'ship',
    '15_05_pipeline_transport':     'pipeline',
    '15_06_nonspecified_transport': 'nonspecified',
}

FUEL_LABEL_MAP = {
    '07_01_motor_gasoline':  'gasoline',
    '07_02_aviation_gasoline': 'aviation_gasoline',
    '07_06_kerosene':        'kerosene',
    '07_07_gas_diesel_oil':  'diesel',
    '07_08_fuel_oil':        'fuel_oil',
    '07_09_lpg':             'lpg',
    '07_x_jet_fuel':         'jet_fuel',
    '08_01_natural_gas':     'natural_gas',
    '08_02_lng':             'lng',
    '16_01_biogas':          'biogas',
    '16_05_biogasoline':     'biogasoline',
    '16_06_biodiesel':       'biodiesel',
    '16_07_bio_jet_kerosene':'bio_jet_kerosene',
    '16_x_hydrogen':         'hydrogen',
    '17_electricity':        'electricity',
}

OUTPUT_DIR = ROOT_DIR / 'other_code' / 'analysis_code' / 'output'
OUTPUT_DIR.mkdir(exist_ok=True)


# ── Data loading ──────────────────────────────────────────────────────────────

def find_latest_nonroad_model_input(root_dir, economy):
    """Return path to latest non_road_model_input_wide CSV, or None."""
    model_inputs_dir = root_dir / 'intermediate_data' / 'model_inputs'
    if not model_inputs_dir.exists():
        return None
    date_folders = sorted(
        [d for d in model_inputs_dir.iterdir() if d.is_dir()],
        reverse=True
    )
    for folder in date_folders:
        candidate = folder / f'{economy}_non_road_model_input_wide.csv'
        if candidate.exists():
            return candidate
    return None


def load_from_intermediate(path):
    df = pd.read_csv(path)
    if 'Scenario' in df.columns:
        scenarios = df['Scenario'].unique()
        scenario = 'reference' if 'reference' in scenarios else scenarios[0]
        df = df[df['Scenario'] == scenario]
    return df, 'intermediate (optimised)'


def load_from_combined_data(root_dir, economy, base_year):
    path = root_dir / 'input_data' / 'transport_data_system' / 'combined_data_DATE20250122.csv'
    print(f'  Reading: {path}')
    raw = pd.read_csv(path)
    # Warn if non-road activity values appear frozen (identical to prior year — common for 2022/2023)
    if base_year > 2019:
        act = raw[(raw.economy == economy) & (raw.medium.isin(['air','rail','ship'])) &
                  (raw.measure == 'activity') & (raw.date.isin([base_year - 1, base_year]))]
        act_pivot = act.pivot_table(index=['medium','transport_type'], columns='date', values='value')
        frozen = act_pivot[act_pivot[base_year - 1] == act_pivot[base_year]]
        if len(frozen):
            print(f'  WARNING: {len(frozen)} non-road activity rows are identical to {base_year-1}.')
            print(f'  These appear frozen at {base_year-1} values (possible COVID-era data not updated):')
            print(f'  {frozen.index.tolist()}')
            print(f'  Use ESTO as the authoritative energy reference for {base_year}.')
    nonroad = raw[
        (raw.economy == economy) &
        (raw.date == base_year) &
        (raw.medium.isin(['air', 'rail', 'ship', 'pipeline', 'nonspecified'])) &
        (raw.measure.isin(['energy', 'activity', 'intensity'])) &
        (raw.drive == 'all') &
        (raw.vehicle_type == 'all')
    ].copy()
    wide = nonroad.pivot_table(
        index=['economy', 'date', 'medium', 'transport_type'],
        columns='measure',
        values='value',
        aggfunc='first'
    ).reset_index()
    wide.columns.name = None
    wide = wide.rename(columns={
        'economy':        'Economy',
        'date':           'Date',
        'medium':         'Medium',
        'transport_type': 'Transport Type',
        'energy':         'Energy',
        'activity':       'Activity',
        'intensity':      'Intensity',
    })
    wide['Scenario'] = 'reference'
    return wide, 'combined_data (raw, pre-optimisation)'


def load_nonroad_input(root_dir, economy, base_year):
    intermediate_path = find_latest_nonroad_model_input(root_dir, economy)
    if intermediate_path is not None:
        print(f'Found optimised file: {intermediate_path}')
        df, source = load_from_intermediate(intermediate_path)
    else:
        print('No intermediate file found -- using combined_data')
        df, source = load_from_combined_data(root_dir, economy, base_year)
    return df, source


def load_esto_nonroad_energy(root_dir, economy, base_year, scenario):
    """Return non-road energy from ESTO by (medium, fuel_id)."""
    path = root_dir / 'input_data' / '9th_model_inputs' / 'model_df_wide_20250221.csv'
    print(f'  Reading ESTO: {path}')
    esto = pd.read_csv(path)

    nonroad = esto[
        (esto.economy == economy) &
        (esto.scenarios == scenario) &
        (esto.sub1sectors.isin(ESTO_SECTOR_TO_MEDIUM.keys())) &
        (esto.is_subtotal == False) &
        (esto[str(base_year)].notna())
    ].copy()

    nonroad['energy_esto_PJ'] = nonroad[str(base_year)]
    nonroad['medium'] = nonroad['sub1sectors'].map(ESTO_SECTOR_TO_MEDIUM)

    # Use subfuel where set, else fall back to fuel code
    nonroad['fuel_id'] = nonroad.apply(
        lambda r: r['subfuels'] if r['subfuels'] != 'x' else r['fuels'],
        axis=1
    )

    # Exclude subtotals and zero/negative
    exclude_fuels = {'19_total', '20_total_renewables', '21_modern_renewables'}
    nonroad = nonroad[~nonroad['fuels'].isin(exclude_fuels)].copy()
    nonroad = nonroad[nonroad['energy_esto_PJ'] > 0].copy()

    return nonroad.groupby(['medium', 'fuel_id'])['energy_esto_PJ'].sum().reset_index()


# ── Build output tables ───────────────────────────────────────────────────────

def build_nonroad_table(nonroad_df, esto_energy, base_year):
    df = nonroad_df.copy()

    if 'Date' in df.columns:
        df = df[df['Date'] == base_year]

    def col(name):
        if name in df.columns:
            return name
        for c in df.columns:
            if c.lower() == name.lower():
                return c
        return None

    c_medium = col('Medium')
    c_ttype  = col('Transport Type')
    c_act    = col('Activity')
    c_inten  = col('Intensity')
    c_energy = col('Energy')

    if any(c is None for c in [c_medium, c_ttype, c_act, c_inten]):
        missing = [n for n, c in zip(
            ['Medium', 'Transport Type', 'Activity', 'Intensity'],
            [c_medium, c_ttype, c_act, c_inten]
        ) if c is None]
        raise ValueError(f'Missing columns: {missing}. Available: {df.columns.tolist()}')

    out = pd.DataFrame({
        'medium':         df[c_medium].values,
        'transport_type': df[c_ttype].values,
    })

    activity_raw = df[c_act].values
    intensity_raw = df[c_inten].replace(0, np.nan).values  # PJ/pkm or PJ/tkm

    # Convert to intuitive units for row-by-row checking:
    #   activity_Bkm  = activity [pkm or tkm] / 1e9   (billion km)
    #   intensity_MJ  = intensity [PJ/km] * 1e9        (MJ per km)
    # Formula: energy_PJ = activity_Bkm * intensity_MJ
    out['activity_pkm_or_tkm']   = activity_raw
    out['activity_Bkm']          = activity_raw / 1e9
    out['intensity_PJ_per_km']   = intensity_raw
    out['intensity_MJ_per_km']   = np.where(intensity_raw > 0, intensity_raw * 1e9, np.nan)
    out['energy_calculated_PJ']  = out['activity_Bkm'] * out['intensity_MJ_per_km']
    out['energy_input_PJ']       = df[c_energy].values if c_energy else np.nan

    # ESTO has no passenger/freight split for non-road — map total medium energy to all rows
    # (both freight and passenger rows for a medium show the same ESTO total)
    esto_total = esto_energy.groupby('medium')['energy_esto_PJ'].sum().to_dict()
    out['energy_esto_medium_total_PJ'] = out['medium'].map(esto_total)

    # Human-readable formula note for each row
    out['energy_calc_notes'] = out.apply(
        lambda r: (
            f"energy_PJ = activity_Bkm ({r['activity_Bkm']:.3f} Bkm) "
            f"x intensity ({r['intensity_MJ_per_km']:.4f} MJ/km)  =  {r['energy_calculated_PJ']:.3f} PJ"
        ) if pd.notna(r['intensity_MJ_per_km']) else 'no intensity data',
        axis=1
    )

    out = out.sort_values(['medium', 'transport_type']).reset_index(drop=True)
    return out


def build_esto_fuel_breakdown(esto_energy):
    """Detailed ESTO energy by medium x fuel for reference."""
    fb = esto_energy.copy()
    fb['fuel_label'] = fb['fuel_id'].map(FUEL_LABEL_MAP).fillna(fb['fuel_id'])
    fb['fuel_share_%'] = fb.groupby('medium')['energy_esto_PJ'].transform(
        lambda x: (x / x.sum() * 100).round(1)
    )
    return fb[['medium', 'fuel_id', 'fuel_label', 'energy_esto_PJ', 'fuel_share_%']].sort_values(
        ['medium', 'energy_esto_PJ'], ascending=[True, False]
    ).reset_index(drop=True)


# ── Print summaries ───────────────────────────────────────────────────────────

def print_summary(result, esto_fuel_breakdown, esto_energy):
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 220)
    pd.set_option('display.float_format', '{:,.3f}'.format)

    print('\n== Non-road data by medium x transport_type ==')
    print('Formula: energy_PJ = activity_Bkm * intensity_MJ_per_km\n')
    display_cols = [
        'medium', 'transport_type',
        'activity_Bkm', 'intensity_MJ_per_km',
        'energy_calculated_PJ', 'energy_input_PJ', 'energy_esto_medium_total_PJ',
    ]
    print(result[display_cols].to_string(index=False))

    print('\n== Energy comparison: model vs ESTO by medium ==')
    agg = result.groupby('medium').agg(
        activity_Bkm=('activity_Bkm', 'sum'),
        energy_calc_PJ=('energy_calculated_PJ', 'sum'),
        energy_input_PJ=('energy_input_PJ', 'sum'),
        energy_esto_PJ=('energy_esto_medium_total_PJ', 'first'),
    ).reset_index()
    agg['calc_vs_esto_%'] = np.where(
        agg['energy_esto_PJ'] > 0,
        ((agg['energy_calc_PJ'] - agg['energy_esto_PJ']) / agg['energy_esto_PJ'] * 100).round(1),
        np.nan
    )
    agg['input_vs_esto_%'] = np.where(
        agg['energy_esto_PJ'] > 0,
        ((agg['energy_input_PJ'] - agg['energy_esto_PJ']) / agg['energy_esto_PJ'] * 100).round(1),
        np.nan
    )
    print(agg.to_string(index=False))

    print('\n== ESTO fuel breakdown by medium (reference only -- model assigns fuels separately) ==')
    print(esto_fuel_breakdown.to_string(index=False))

    print('\n== Totals ==')
    print(f"  Calculated energy (all non-road):    {result['energy_calculated_PJ'].sum():>10,.1f} PJ")
    if not result['energy_input_PJ'].isna().all():
        print(f"  Input energy (all non-road):         {result['energy_input_PJ'].sum():>10,.1f} PJ")
    print(f"  ESTO non-road energy ({ESTO_SCENARIO}):    {esto_energy['energy_esto_PJ'].sum():>10,.1f} PJ")
    print(f"  (excl. pipeline: {esto_energy[esto_energy.medium != 'pipeline']['energy_esto_PJ'].sum():,.1f} PJ)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f'== USA Non-Road Base Year Data Extraction ==')
    print(f'Economy: {ECONOMY}  Base year: {BASE_YEAR}  ESTO scenario: {ESTO_SCENARIO}\n')

    nonroad_df, source = load_nonroad_input(ROOT_DIR, ECONOMY, BASE_YEAR)
    print(f'Data source: {source}')
    print(f'Loaded {len(nonroad_df)} rows, columns: {nonroad_df.columns.tolist()}\n')

    esto_energy = load_esto_nonroad_energy(ROOT_DIR, ECONOMY, BASE_YEAR, ESTO_SCENARIO)

    result = build_nonroad_table(nonroad_df, esto_energy, BASE_YEAR)
    esto_fuel_breakdown = build_esto_fuel_breakdown(esto_energy)

    # Save outputs
    out_path = OUTPUT_DIR / f'{ECONOMY}_nonroad_base_year_{BASE_YEAR}.csv'
    fuel_path = OUTPUT_DIR / f'{ECONOMY}_nonroad_base_year_{BASE_YEAR}_esto_fuel_breakdown.csv'
    result.to_csv(out_path, index=False)
    esto_fuel_breakdown.to_csv(fuel_path, index=False)
    print(f'Saved: {out_path}  ({len(result)} rows)')
    print(f'Saved: {fuel_path}  ({len(esto_fuel_breakdown)} rows)')

    print_summary(result, esto_fuel_breakdown, esto_energy)


if __name__ == '__main__':
    main()
