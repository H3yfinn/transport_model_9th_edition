"""
non_road_reconciliation.py

Prototype reconciliation of non-road transport activity / intensity to ESTO energy targets.

-------------------------------------------------------------------------------------
Conceptual model
-------------------------------------------------------------------------------------
ESTO already provides energy by medium AND by fuel.
We therefore do NOT split service energy across fuels from scratch.
Instead:
  - Activity is split across fuels using activity_shares.
  - Relative intensity values weight fuels against each other within a
    service + medium group (e.g. electricity = 0.25 means it requires 25%
    of the energy per unit activity compared to oil products at 1.0).
  - A base_intensity scalar is derived per service+medium so that the
    service-level energy total is exactly preserved.
  - Reconciliation then adjusts activity_shares, relative_intensity values,
    and passenger/freight service_energy_shares so that calculated fuel-level
    energy (summed across passenger and freight) matches ESTO by medium/fuel.

-------------------------------------------------------------------------------------
Key variables
-------------------------------------------------------------------------------------
  activity          [Bpkm or Btkm]   total activity by service + medium
  activity_share    [0-1]            fraction of activity on each fuel
  relative_intensity [dimensionless] fuel's energy demand relative to the
                                     reference fuel within this service+medium
  base_intensity    [MJ/Bkm = PJ]    scaling factor so service energy is exact
  final_intensity   [MJ/Bkm]         base_intensity * relative_intensity
  service_energy    [PJ]             total energy for this service + medium
  calculated_energy [PJ]             activity_by_fuel * final_intensity

Energy formula (row-by-row):
  activity_by_fuel  = activity * activity_share
  weighted_activity = activity_by_fuel * relative_intensity
  base_intensity    = service_energy / sum_f(weighted_activity)
  final_intensity   = base_intensity * relative_intensity
  calculated_energy = activity_by_fuel * final_intensity

  --> sum_f(calculated_energy) == service_energy  [exact by construction]
  --> sum_s(service_energy)    == total_medium_energy  [if service_energy_shares sum to 1]
  --> sum_s,f(calculated_energy by fuel) may differ from ESTO by medium/fuel [before reconciliation]

Reconciliation closes the remaining gap by adjusting the three variable groups
while keeping them as close as possible to the user-supplied starting values.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

try:
    from scipy.optimize import minimize
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


# ── Validation ────────────────────────────────────────────────────────────────

def validate_non_road_inputs(
    activity_df: pd.DataFrame,
    service_energy_split_df: pd.DataFrame,
    activity_share_df: pd.DataFrame,
    relative_intensity_df: pd.DataFrame,
    relative_intensity_band_df: pd.DataFrame,
    esto_energy_df: pd.DataFrame,
) -> List[str]:
    """
    Check all input DataFrames for required columns, non-negativity,
    and share consistency. Returns a list of error strings (empty = OK).
    """
    errors = []

    required_cols = {
        'activity_df':              ['economy', 'scenario', 'year', 'service', 'medium', 'activity'],
        'service_energy_split_df':  ['economy', 'scenario', 'year', 'service', 'medium', 'service_energy_share'],
        'activity_share_df':        ['economy', 'scenario', 'year', 'service', 'medium', 'fuel', 'activity_share'],
        'relative_intensity_df':    ['economy', 'scenario', 'year', 'service', 'medium', 'fuel', 'relative_intensity'],
        'relative_intensity_band_df': [
            'economy', 'scenario', 'year', 'service', 'medium', 'fuel',
            'relative_intensity_min', 'relative_intensity_max',
        ],
        'esto_energy_df': ['economy', 'scenario', 'year', 'medium', 'fuel', 'esto_energy'],
    }
    frames = {
        'activity_df': activity_df,
        'service_energy_split_df': service_energy_split_df,
        'activity_share_df': activity_share_df,
        'relative_intensity_df': relative_intensity_df,
        'relative_intensity_band_df': relative_intensity_band_df,
        'esto_energy_df': esto_energy_df,
    }
    for name, cols in required_cols.items():
        missing = [c for c in cols if c not in frames[name].columns]
        if missing:
            errors.append(f'{name}: missing columns {missing}')

    if errors:
        return errors  # can't safely check values without columns

    # Non-negativity
    for name, col in [
        ('activity_df',           'activity'),
        ('activity_share_df',     'activity_share'),
        ('relative_intensity_df', 'relative_intensity'),
        ('esto_energy_df',        'esto_energy'),
    ]:
        if (frames[name][col] < 0).any():
            errors.append(f'{name}.{col} contains negative values')

    # Service energy shares must sum to 1 per economy/scenario/year/medium
    svc_sums = (
        service_energy_split_df
        .groupby(['economy', 'scenario', 'year', 'medium'])['service_energy_share']
        .sum()
    )
    bad = svc_sums[~svc_sums.between(0.999, 1.001)]
    if len(bad):
        errors.append(
            f'service_energy_split_df: shares do not sum to 1 for {bad.index.tolist()}'
        )

    # Activity shares must sum to 1 per economy/scenario/year/service/medium
    act_sums = (
        activity_share_df
        .groupby(['economy', 'scenario', 'year', 'service', 'medium'])['activity_share']
        .sum()
    )
    bad2 = act_sums[~act_sums.between(0.999, 1.001)]
    if len(bad2):
        errors.append(
            f'activity_share_df: shares do not sum to 1 for {bad2.index.tolist()}'
        )

    # Band validity: min <= max
    band_ok = (
        relative_intensity_band_df['relative_intensity_min']
        <= relative_intensity_band_df['relative_intensity_max']
    )
    if not band_ok.all():
        errors.append('relative_intensity_band_df: some relative_intensity_min > relative_intensity_max')

    # Initial relative intensities should be inside their bands
    check = relative_intensity_df.merge(
        relative_intensity_band_df[
            ['economy', 'scenario', 'year', 'service', 'medium', 'fuel',
             'relative_intensity_min', 'relative_intensity_max']
        ],
        on=['economy', 'scenario', 'year', 'service', 'medium', 'fuel'],
        how='left',
    )
    outside = check[
        (check['relative_intensity'] < check['relative_intensity_min'] - 1e-6) |
        (check['relative_intensity'] > check['relative_intensity_max'] + 1e-6)
    ]
    if len(outside):
        errors.append(
            f'relative_intensity_df: {len(outside)} rows outside their allowed bands'
        )

    return errors


# ── Normalisation ─────────────────────────────────────────────────────────────

def normalise_service_energy_splits(service_energy_split_df: pd.DataFrame) -> pd.DataFrame:
    """
    Rescale passenger/freight service_energy_share so they sum exactly to 1
    within each economy/scenario/year/medium group.
    Needed when user inputs do not already sum to 1.
    """
    df = service_energy_split_df.copy()
    group = ['economy', 'scenario', 'year', 'medium']
    totals = df.groupby(group)['service_energy_share'].transform('sum')
    df['service_energy_share'] = df['service_energy_share'] / totals
    return df


def normalise_activity_shares(activity_share_df: pd.DataFrame) -> pd.DataFrame:
    """
    Rescale activity_share so it sums exactly to 1 across fuels within
    each economy/scenario/year/service/medium group.
    """
    df = activity_share_df.copy()
    group = ['economy', 'scenario', 'year', 'service', 'medium']
    totals = df.groupby(group)['activity_share'].transform('sum')
    df['activity_share'] = df['activity_share'] / totals
    return df


def fill_default_intensity_bands(
    relative_intensity_df: pd.DataFrame,
    band_pct: float = 0.05,
) -> pd.DataFrame:
    """
    Build a relative_intensity_band_df where each fuel's band is ±band_pct
    (default ±5%) around its starting relative_intensity value.
    Use this when no explicit bands are supplied.
    """
    df = relative_intensity_df.copy()
    df['relative_intensity_min'] = df['relative_intensity'] * (1.0 - band_pct)
    df['relative_intensity_max'] = df['relative_intensity'] * (1.0 + band_pct)
    return df[
        ['economy', 'scenario', 'year', 'service', 'medium', 'fuel',
         'relative_intensity_min', 'relative_intensity_max']
    ]


# ── Core energy calculation ───────────────────────────────────────────────────

def _calc_energy_arrays(
    activity: np.ndarray,       # (n_services,)
    act_share: np.ndarray,      # (n_services, n_fuels)
    rel_int: np.ndarray,        # (n_services, n_fuels)
    svc_share: np.ndarray,      # (n_services,)
    total_medium_energy: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Low-level calculation of energy from numpy arrays.
    Used both during initial calculation and inside the optimiser.

    Returns:
      service_energy     (n_services,)
      base_intensity     (n_services,)
      final_intensity    (n_services, n_fuels)
      calculated_energy  (n_services, n_fuels)
    """
    service_energy = svc_share * total_medium_energy                      # (n_s,)
    activity_by_fuel = activity[:, None] * act_share                      # (n_s, n_f)
    weighted_activity = activity_by_fuel * rel_int                        # (n_s, n_f)
    sum_weighted = weighted_activity.sum(axis=1)                          # (n_s,)

    base_intensity = np.where(
        sum_weighted > 1e-15,
        service_energy / sum_weighted,
        0.0,
    )                                                                      # (n_s,)

    final_intensity = base_intensity[:, None] * rel_int                   # (n_s, n_f)
    calculated_energy = activity_by_fuel * final_intensity                # (n_s, n_f)

    return service_energy, base_intensity, final_intensity, calculated_energy


def calculate_initial_non_road_energy(
    activity_df: pd.DataFrame,
    service_energy_split_df: pd.DataFrame,
    activity_share_df: pd.DataFrame,
    relative_intensity_df: pd.DataFrame,
    relative_intensity_band_df: pd.DataFrame,
    esto_energy_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate initial fuel-level energy before reconciliation.

    For each economy/scenario/year/service/medium/fuel row:
      1. total_medium_energy  = sum of esto_energy across fuels for this medium
      2. service_energy       = total_medium_energy * service_energy_share
      3. activity_by_fuel     = activity * activity_share
      4. weighted_activity    = activity_by_fuel * relative_intensity
      5. base_intensity       = service_energy / sum_f(weighted_activity)
      6. final_intensity      = base_intensity * relative_intensity
      7. calculated_energy    = activity_by_fuel * final_intensity

    Property: sum_f(calculated_energy) == service_energy  [exact]
    But: sum_s(calculated_energy by fuel) != esto_energy by fuel  [before reconciliation]

    Initial values are stored with suffix _initial for tracking movement.
    """
    # Step 1 — total medium energy from ESTO
    medium_totals = (
        esto_energy_df
        .groupby(['economy', 'scenario', 'year', 'medium'])['esto_energy']
        .sum()
        .reset_index()
        .rename(columns={'esto_energy': 'total_medium_energy'})
    )

    # Build the full fuel-level scaffold by merging all inputs
    df = activity_share_df.copy()
    df = df.merge(activity_df,            on=['economy', 'scenario', 'year', 'service', 'medium'],       how='left')
    df = df.merge(service_energy_split_df, on=['economy', 'scenario', 'year', 'service', 'medium'],       how='left')
    df = df.merge(relative_intensity_df,  on=['economy', 'scenario', 'year', 'service', 'medium', 'fuel'], how='left')
    df = df.merge(relative_intensity_band_df,
                  on=['economy', 'scenario', 'year', 'service', 'medium', 'fuel'], how='left')
    df = df.merge(medium_totals,          on=['economy', 'scenario', 'year', 'medium'],                   how='left')
    df = df.merge(esto_energy_df,         on=['economy', 'scenario', 'year', 'medium', 'fuel'],           how='left')

    # Step 2-7 via vectorised pandas operations
    df['service_energy']   = df['total_medium_energy'] * df['service_energy_share']
    df['activity_by_fuel'] = df['activity'] * df['activity_share']
    df['weighted_activity'] = df['activity_by_fuel'] * df['relative_intensity']

    svc_med_group = ['economy', 'scenario', 'year', 'service', 'medium']
    sum_weighted = (
        df.groupby(svc_med_group)['weighted_activity']
        .transform('sum')
    )
    df['base_intensity']  = np.where(sum_weighted > 1e-15, df['service_energy'] / sum_weighted, 0.0)
    df['final_intensity'] = df['base_intensity'] * df['relative_intensity']
    df['calculated_energy'] = df['activity_by_fuel'] * df['final_intensity']

    # Preserve initial values for later comparison
    df['activity_share_initial']        = df['activity_share']
    df['relative_intensity_initial']    = df['relative_intensity']
    df['service_energy_share_initial']  = df['service_energy_share']

    return df


# ── Comparison ────────────────────────────────────────────────────────────────

def compare_to_esto_targets(result_df: pd.DataFrame) -> pd.DataFrame:
    """
    Sum calculated_energy across services (passenger + freight) and compare to
    ESTO targets by medium/fuel.

    Returns a DataFrame showing the gap before reconciliation, useful for
    deciding whether reconciliation is needed and how large the corrections are.
    """
    group = ['economy', 'scenario', 'year', 'medium', 'fuel']

    calc = (
        result_df
        .groupby(group)['calculated_energy']
        .sum()
        .reset_index()
        .rename(columns={'calculated_energy': 'calculated_energy_total'})
    )
    esto = result_df[group + ['esto_energy']].drop_duplicates(group)

    diag = calc.merge(esto, on=group, how='outer')
    diag['energy_gap_PJ']  = diag['calculated_energy_total'] - diag['esto_energy']
    diag['energy_gap_pct'] = np.where(
        diag['esto_energy'].abs() > 1e-9,
        diag['energy_gap_PJ'] / diag['esto_energy'] * 100,
        np.nan,
    )
    diag['needs_reconciliation'] = diag['energy_gap_PJ'].abs() > 1e-4

    return diag.sort_values(group).reset_index(drop=True)


# ── Reconciliation ────────────────────────────────────────────────────────────

def reconcile_non_road_to_esto(
    result_df: pd.DataFrame,
    max_iter: int = 2000,
    tol: float = 1e-9,
) -> Tuple[pd.DataFrame, Dict]:
    """
    Adjust activity_shares, relative_intensities, and service_energy_shares so
    that calculated fuel-level energy (summed across services) matches ESTO exactly.

    Hard constraints:
      (a) activity_share sums to 1 across fuels within each service+medium
      (b) service_energy_share sums to 1 across services within each medium
      (c) relative_intensity stays within its allowed band
      (d) calculated energy matches ESTO by medium/fuel (equality)
      (e) all decision variables >= 0

    Soft objective — minimise relative changes in this priority order:
      1. relative_intensity  (weight=1, adjusted first)
      2. activity_share      (weight=10)
      3. service_energy_share (weight=100, adjusted last)

    Optimisation is solved independently per economy/scenario/year/medium group.

    Returns:
      updated result_df with final values replacing the _initial columns
      meta_diagnostics dict keyed by 'economy/scenario/year/medium'

    If no feasible solution is found, the original values are preserved and
    a diagnostic note is returned suggesting that total activity adjustment
    may be required as a next step.
    """
    if not SCIPY_AVAILABLE:
        diag = {
            'ALL': {
                'success': False,
                'message': 'scipy not available — install scipy to enable reconciliation.',
                'n_iterations': 0,
                'max_energy_gap_pct': None,
            }
        }
        return result_df.copy(), diag

    group_keys = ['economy', 'scenario', 'year', 'medium']
    all_results = []
    meta = {}

    for gkey, gdf in result_df.groupby(group_keys):
        economy, scenario, year, medium = gkey
        label = f'{economy}/{scenario}/{year}/{medium}'

        services = sorted(gdf['service'].unique())
        fuels    = sorted(gdf['fuel'].unique())
        n_s, n_f = len(services), len(fuels)
        s_idx = {s: i for i, s in enumerate(services)}
        f_idx = {f: i for i, f in enumerate(fuels)}

        # Pull initial arrays from the DataFrame
        rel_int_0  = np.zeros((n_s, n_f))
        act_shr_0  = np.zeros((n_s, n_f))
        ri_lo      = np.zeros((n_s, n_f))
        ri_hi      = np.zeros((n_s, n_f))
        activity   = np.zeros(n_s)
        svc_shr_0  = np.zeros(n_s)

        for _, row in gdf.iterrows():
            si = s_idx[row['service']]
            fi = f_idx[row['fuel']]
            rel_int_0[si, fi] = row['relative_intensity']
            act_shr_0[si, fi] = row['activity_share']
            ri_lo[si, fi]     = row['relative_intensity_min']
            ri_hi[si, fi]     = row['relative_intensity_max']
            if activity[si] == 0:
                activity[si] = row['activity']
            if svc_shr_0[si] == 0:
                svc_shr_0[si] = row['service_energy_share']

        # ESTO target: fuel-level energy (one value per fuel, not per service row)
        esto_by_fuel = np.zeros(n_f)
        for _, row in gdf.drop_duplicates('fuel').iterrows():
            esto_by_fuel[f_idx[row['fuel']]] = row['esto_energy']
        total_medium_energy = esto_by_fuel.sum()

        # --- Decision variable packing ---
        # x = [ rel_int (n_s*n_f) | act_share (n_s*n_f) | svc_share (n_s) ]
        n_ri, n_as, n_ss = n_s * n_f, n_s * n_f, n_s

        def unpack(x):
            ri  = x[:n_ri].reshape(n_s, n_f)
            asz = x[n_ri:n_ri + n_as].reshape(n_s, n_f)
            ss  = x[n_ri + n_as:]
            return ri, asz, ss

        def pack(ri, asz, ss):
            return np.concatenate([ri.ravel(), asz.ravel(), ss.ravel()])

        x0 = pack(rel_int_0, act_shr_0, svc_shr_0)

        # --- Objective: weighted sum of squared relative deviations ---
        # Lower weight = allowed to move more freely
        W_RI, W_AS, W_SS = 1.0, 10.0, 100.0

        def objective(x):
            ri, asz, ss = unpack(x)
            loss  = W_RI * (((ri  - rel_int_0) / (rel_int_0 + 1e-12)) ** 2).sum()
            loss += W_AS * (((asz - act_shr_0) / (act_shr_0 + 1e-12)) ** 2).sum()
            loss += W_SS * (((ss  - svc_shr_0) / (svc_shr_0 + 1e-12)) ** 2).sum()
            return loss

        # --- Constraint functions ---
        constraints = []

        # (a) activity_share sums to 1 for each service
        for si in range(n_s):
            def _act_sum(x, si=si):
                _, asz, _ = unpack(x)
                return asz[si].sum() - 1.0
            constraints.append({'type': 'eq', 'fun': _act_sum})

        # (b) service_energy_share sums to 1
        def _svc_sum(x):
            _, _, ss = unpack(x)
            return ss.sum() - 1.0
        constraints.append({'type': 'eq', 'fun': _svc_sum})

        # (d) calculated fuel energy matches ESTO
        def _medium_fuel_energy(x):
            ri, asz, ss = unpack(x)
            _, _, _, calc = _calc_energy_arrays(activity, asz, ri, ss, total_medium_energy)
            return calc.sum(axis=0)  # (n_f,)

        for fi in range(n_f):
            def _energy_eq(x, fi=fi):
                return _medium_fuel_energy(x)[fi] - esto_by_fuel[fi]
            constraints.append({'type': 'eq', 'fun': _energy_eq})

        # --- Bounds ---
        # (c) relative_intensity within band; (e) activity_share, svc_share in [0, 1]
        bounds = (
            [(ri_lo[si, fi], ri_hi[si, fi]) for si in range(n_s) for fi in range(n_f)] +
            [(0.0, 1.0)] * n_as +
            [(0.0, 1.0)] * n_ss
        )

        # --- Run optimiser ---
        opt = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': max_iter, 'ftol': tol, 'disp': False},
        )

        ri_f, as_f, ss_f = unpack(opt.x)
        _, base_int_f, final_int_f, calc_e_f = _calc_energy_arrays(
            activity, as_f, ri_f, ss_f, total_medium_energy
        )

        # Max residual gap after solving (should be near zero if successful)
        max_gap_pct = float(
            np.max(np.abs((calc_e_f.sum(axis=0) - esto_by_fuel) / (esto_by_fuel + 1e-12))) * 100
        )
        succeeded = opt.success or (max_gap_pct < 0.1)

        if not succeeded:
            meta[label] = {
                'success': False,
                'message': (
                    opt.message + ' -- total activity adjustment may be required '
                    'as a next step.'
                ),
                'n_iterations': opt.nit,
                'max_energy_gap_pct': max_gap_pct,
            }
            all_results.append(gdf)
            continue

        # Write final values back into a copy of the group DataFrame
        out = gdf.copy()
        for idx, row in out.iterrows():
            si = s_idx[row['service']]
            fi = f_idx[row['fuel']]
            svc_e_final = ss_f[si] * total_medium_energy

            out.loc[idx, 'relative_intensity']   = ri_f[si, fi]
            out.loc[idx, 'activity_share']        = as_f[si, fi]
            out.loc[idx, 'service_energy_share']  = ss_f[si]
            out.loc[idx, 'service_energy']        = svc_e_final
            out.loc[idx, 'activity_by_fuel']      = activity[si] * as_f[si, fi]
            out.loc[idx, 'base_intensity']        = base_int_f[si]
            out.loc[idx, 'final_intensity']       = final_int_f[si, fi]
            out.loc[idx, 'calculated_energy']     = calc_e_f[si, fi]

        meta[label] = {
            'success': True,
            'message': opt.message,
            'n_iterations': opt.nit,
            'max_energy_gap_pct': max_gap_pct,
            'objective_value': opt.fun,
        }
        all_results.append(out)

    return pd.concat(all_results, ignore_index=True), meta


# ── Diagnostics ───────────────────────────────────────────────────────────────

def build_non_road_diagnostics(
    initial_df: pd.DataFrame,
    reconciled_df: pd.DataFrame,
    meta_diagnostics: Dict,
) -> pd.DataFrame:
    """
    Build a summary diagnostics DataFrame comparing before/after reconciliation.

    Columns include:
      esto_energy, calculated_energy_before, calculated_energy_after,
      gap_before_PJ, gap_after_PJ, gap_after_pct,
      max_ri_change_pct, max_as_change_pct,
      ri_at_lower_bound, ri_at_upper_bound,
      reconciliation_succeeded
    """
    group = ['economy', 'scenario', 'year', 'medium', 'fuel']
    svc_med = ['economy', 'scenario', 'year', 'medium']

    before = (
        initial_df
        .groupby(group)
        .agg(
            calculated_energy_before=('calculated_energy', 'sum'),
            esto_energy=('esto_energy', 'first'),
        )
        .reset_index()
    )
    after = (
        reconciled_df
        .groupby(group)['calculated_energy']
        .sum()
        .reset_index()
        .rename(columns={'calculated_energy': 'calculated_energy_after'})
    )

    diag = before.merge(after, on=group, how='left')
    diag['gap_before_PJ'] = diag['calculated_energy_before'] - diag['esto_energy']
    diag['gap_after_PJ']  = diag['calculated_energy_after']  - diag['esto_energy']
    diag['gap_after_pct'] = np.where(
        diag['esto_energy'].abs() > 1e-9,
        diag['gap_after_PJ'] / diag['esto_energy'] * 100,
        np.nan,
    )

    # Maximum relative change in relative_intensity per medium (across all rows)
    ri_chg = (
        (reconciled_df['relative_intensity'] - reconciled_df['relative_intensity_initial']).abs()
        / (reconciled_df['relative_intensity_initial'].abs() + 1e-12)
        * 100
    )
    as_chg = (
        (reconciled_df['activity_share'] - reconciled_df['activity_share_initial']).abs()
        / (reconciled_df['activity_share_initial'].abs() + 1e-12)
        * 100
    )
    reconciled_df = reconciled_df.copy()
    reconciled_df['_ri_chg'] = ri_chg
    reconciled_df['_as_chg'] = as_chg

    max_ri = reconciled_df.groupby(svc_med)['_ri_chg'].max().reset_index().rename(columns={'_ri_chg': 'max_ri_change_pct'})
    max_as = reconciled_df.groupby(svc_med)['_as_chg'].max().reset_index().rename(columns={'_as_chg': 'max_as_change_pct'})

    diag = diag.merge(max_ri, on=svc_med, how='left')
    diag = diag.merge(max_as, on=svc_med, how='left')

    # Bound-hit flags
    ri_at_lb = (
        (reconciled_df['relative_intensity'] <= reconciled_df['relative_intensity_min'] + 1e-6)
        .groupby(reconciled_df[svc_med].apply(tuple, axis=1))
        .any()
        .reset_index()
        .rename(columns={0: 'ri_at_lower_bound', 'index': '_key'})
    )
    ri_at_ub = (
        (reconciled_df['relative_intensity'] >= reconciled_df['relative_intensity_max'] - 1e-6)
        .groupby(reconciled_df[svc_med].apply(tuple, axis=1))
        .any()
        .reset_index()
        .rename(columns={0: 'ri_at_upper_bound', 'index': '_key'})
    )

    # Attach reconciliation success
    diag['reconciliation_succeeded'] = diag.apply(
        lambda r: meta_diagnostics.get(
            f'{r["economy"]}/{r["scenario"]}/{r["year"]}/{r["medium"]}', {}
        ).get('success', None),
        axis=1,
    )

    # Merge bound flags by constructing a matching key
    key_col = diag[svc_med].apply(tuple, axis=1)
    diag['ri_at_lower_bound'] = key_col.map(
        {k: v for k, v in zip(ri_at_lb['_key'], ri_at_lb['ri_at_lower_bound'])}
    )
    diag['ri_at_upper_bound'] = key_col.map(
        {k: v for k, v in zip(ri_at_ub['_key'], ri_at_ub['ri_at_upper_bound'])}
    )

    return diag.sort_values(group).reset_index(drop=True)


# ── Toy example ───────────────────────────────────────────────────────────────

def _make_toy_inputs():
    """
    Construct a minimal toy dataset for testing.

    Setup:
      Economy: TEST, Scenario: reference, Year: 2022
      Medium: air
      Services: passenger, freight
      Fuels: oil_products, biofuels, electricity

    ESTO energy targets (air, 2022):
      oil_products = 2500 PJ
      biofuels     =  200 PJ
      electricity  =   30 PJ
      total        = 2730 PJ

    Initial state gives electricity ~12.7 PJ vs target 30 PJ — a clear
    reconciliation challenge, driven mainly by needing more electricity
    activity share and/or higher electricity relative intensity.
    """
    idx_base = dict(economy='TEST', scenario='reference', year=2022)
    mediums  = ['air']
    services = ['passenger', 'freight']
    fuels    = ['oil_products', 'biofuels', 'electricity']

    # Activity (Bpkm for passenger, Btkm for freight)
    activity_rows = [
        {**idx_base, 'service': 'passenger', 'medium': 'air', 'activity': 600.0},
        {**idx_base, 'service': 'freight',   'medium': 'air', 'activity':  90.0},
    ]
    activity_df = pd.DataFrame(activity_rows)

    # Service energy splits: 83% passenger, 17% freight (approximate for US air)
    split_rows = [
        {**idx_base, 'service': 'passenger', 'medium': 'air', 'service_energy_share': 0.83},
        {**idx_base, 'service': 'freight',   'medium': 'air', 'service_energy_share': 0.17},
    ]
    service_energy_split_df = pd.DataFrame(split_rows)

    # Activity shares: mostly oil, small biofuel, tiny electricity
    share_rows = []
    for s, shares in [
        ('passenger', {'oil_products': 0.90, 'biofuels': 0.08, 'electricity': 0.02}),
        ('freight',   {'oil_products': 0.95, 'biofuels': 0.04, 'electricity': 0.01}),
    ]:
        for f, v in shares.items():
            share_rows.append({**idx_base, 'service': s, 'medium': 'air', 'fuel': f, 'activity_share': v})
    activity_share_df = pd.DataFrame(share_rows)

    # Relative intensities: electricity is 25% of oil_products intensity
    ri_rows = []
    for s in services:
        for f, ri in [('oil_products', 1.0), ('biofuels', 1.0), ('electricity', 0.25)]:
            ri_rows.append({**idx_base, 'service': s, 'medium': 'air', 'fuel': f, 'relative_intensity': ri})
    relative_intensity_df = pd.DataFrame(ri_rows)

    # Bands: ±5% around initial relative intensities
    relative_intensity_band_df = fill_default_intensity_bands(relative_intensity_df, band_pct=0.05)

    # ESTO targets (no service split — medium+fuel only)
    esto_rows = [
        {**idx_base, 'medium': 'air', 'fuel': 'oil_products', 'esto_energy': 2500.0},
        {**idx_base, 'medium': 'air', 'fuel': 'biofuels',     'esto_energy':  200.0},
        {**idx_base, 'medium': 'air', 'fuel': 'electricity',  'esto_energy':   30.0},
    ]
    esto_energy_df = pd.DataFrame(esto_rows)

    return (
        activity_df,
        service_energy_split_df,
        activity_share_df,
        relative_intensity_df,
        relative_intensity_band_df,
        esto_energy_df,
    )


def run_toy_example(verbose: bool = True) -> Dict:
    """
    Run the full reconciliation pipeline on the toy dataset and return results.
    Demonstrates: validation -> initial calculation -> comparison -> reconciliation -> diagnostics.
    """
    (
        activity_df,
        service_energy_split_df,
        activity_share_df,
        relative_intensity_df,
        relative_intensity_band_df,
        esto_energy_df,
    ) = _make_toy_inputs()

    # 1. Validate
    errors = validate_non_road_inputs(
        activity_df, service_energy_split_df, activity_share_df,
        relative_intensity_df, relative_intensity_band_df, esto_energy_df,
    )
    if errors:
        raise ValueError(f'Input validation failed:\n' + '\n'.join(errors))
    if verbose:
        print('Validation passed.\n')

    # 2. Normalise (not strictly needed for toy, but good practice)
    service_energy_split_df = normalise_service_energy_splits(service_energy_split_df)
    activity_share_df       = normalise_activity_shares(activity_share_df)

    # 3. Initial energy calculation
    initial_df = calculate_initial_non_road_energy(
        activity_df, service_energy_split_df, activity_share_df,
        relative_intensity_df, relative_intensity_band_df, esto_energy_df,
    )

    if verbose:
        print('=== Initial calculated energy (by service/fuel) ===')
        cols = ['service', 'fuel', 'activity_by_fuel', 'final_intensity',
                'calculated_energy', 'esto_energy']
        pd.set_option('display.float_format', '{:.3f}'.format)
        print(initial_df[cols].to_string(index=False))
        print()

    # 4. Compare to ESTO before reconciliation
    pre_diag = compare_to_esto_targets(initial_df)
    if verbose:
        print('=== Pre-reconciliation gap (passenger + freight summed) ===')
        print(pre_diag[['medium', 'fuel', 'calculated_energy_total',
                         'esto_energy', 'energy_gap_PJ', 'energy_gap_pct']].to_string(index=False))
        print()

    # 5. Reconcile
    if not SCIPY_AVAILABLE:
        print('WARNING: scipy not available — skipping reconciliation step.')
        return {'initial_df': initial_df, 'pre_diag': pre_diag}

    reconciled_df, meta = reconcile_non_road_to_esto(initial_df)

    if verbose:
        print('=== Reconciliation meta ===')
        for k, v in meta.items():
            print(f'  {k}: success={v["success"]}, '
                  f'iters={v["n_iterations"]}, '
                  f'max_gap={v.get("max_energy_gap_pct", "n/a"):.4f}%')
        print()

    # 6. Post-reconciliation comparison
    post_diag = compare_to_esto_targets(reconciled_df)
    if verbose:
        print('=== Post-reconciliation gap ===')
        print(post_diag[['medium', 'fuel', 'calculated_energy_total',
                          'esto_energy', 'energy_gap_PJ', 'energy_gap_pct']].to_string(index=False))
        print()

    # 7. Show what moved
    if verbose:
        print('=== Variable movement (initial vs final) ===')
        move_cols = ['service', 'fuel',
                     'activity_share_initial', 'activity_share',
                     'relative_intensity_initial', 'relative_intensity',
                     'service_energy_share_initial', 'service_energy_share']
        print(reconciled_df[move_cols].to_string(index=False))
        print()

    # 8. Full diagnostics
    full_diag = build_non_road_diagnostics(initial_df, reconciled_df, meta)
    if verbose:
        print('=== Diagnostics summary ===')
        print(full_diag[['medium', 'fuel', 'gap_before_PJ', 'gap_after_PJ',
                          'gap_after_pct', 'max_ri_change_pct', 'max_as_change_pct',
                          'reconciliation_succeeded']].to_string(index=False))

    return {
        'initial_df':     initial_df,
        'reconciled_df':  reconciled_df,
        'pre_diag':       pre_diag,
        'post_diag':      post_diag,
        'full_diag':      full_diag,
        'meta':           meta,
    }


if __name__ == '__main__':
    run_toy_example(verbose=True)
