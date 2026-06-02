"""Skeleton for a cleaner base-year optimisation flow.

This is intentionally a lightweight template, not a drop-in replacement.
It is designed to show a simple structure you can reuse if rebuilding
`optimise_to_calculate_base_data.py` from scratch.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Any, Callable, Sequence

import numpy as np
import pandas as pd
from scipy.optimize import OptimizeResult, minimize


@dataclass(frozen=True)
class ObjectiveWeights:
    """Weights for objective terms."""

    energy: float = 1.0
    stocks: float = 1.0
    mileage: float = 0.5
    intensity: float = 0.5
    opposite_drive_types: float = 0.0
    stocks_per_capita: float = 0.0


@dataclass(frozen=True)
class BoundConfig:
    """High-level bound controls."""

    max_change_stocks: float = 2.0
    max_change_mileage: float = 0.2
    max_change_intensity: float = 0.2


@dataclass(frozen=True)
class CandidateConfig:
    """Single candidate: solver + parameters."""

    method: str
    iteration_multiplier: int
    tolerance_pct: float
    use_same_mileage_across_vehicle_types: bool
    weights: ObjectiveWeights
    bounds: BoundConfig


@dataclass
class OptimisationProblem:
    """All immutable problem data needed by objective/constraints."""

    df_structure: pd.DataFrame
    actual_values: np.ndarray
    initial_values: np.ndarray
    actual_energy_by_drive: dict[str, float]
    stocks_per_capita_constants: pd.DataFrame
    lower_bounds: np.ndarray
    upper_bounds: np.ndarray
    economy: str
    year: int
    scenario: str


@dataclass
class CandidateOutcome:
    """Result wrapper for one candidate run."""

    config: CandidateConfig
    result: OptimizeResult | None
    success: bool
    reason: str


def prepare_base_year_input(
    config: Any,
    economy_id: str,
    input_data_new_road: pd.DataFrame,
    *,
    remove_non_major_variables: bool = True,
    remove_zeros: bool = True,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Prepare and filter raw input into a consistent, narrow base-year frame.

    TODO:
    - Keep only base year, scenario, and economy.
    - Convert efficiency -> intensity once.
    - Optionally remove non-major drives and zero-stock rows.
    - Return metadata needed for post-processing.
    """
    prepared = input_data_new_road.copy()
    meta: dict[str, Any] = {
        "remove_non_major_variables": remove_non_major_variables,
        "remove_zeros": remove_zeros,
    }
    return prepared, meta


def build_problem(
    config: Any,
    economy_id: str,
    prepared_input: pd.DataFrame,
    candidate: CandidateConfig,
) -> OptimisationProblem:
    """Build a complete optimisation problem for one candidate.

    TODO:
    - Build tall structure with only [Mileage, Stocks, Intensity] variables.
    - Compute actual_energy_by_drive.
    - Compute stocks-per-capita constants once per economy/base year.
    - Set and adjust bounds so target energy is reachable.
    """
    required_columns = [
        "Economy",
        "Date",
        "Medium",
        "Scenario",
        "Transport Type",
        "Vehicle Type",
        "Drive",
        "Measure",
    ]

    # Minimal frame to keep the skeleton runnable.
    if {"Measure", "Value"}.issubset(prepared_input.columns):
        tall = prepared_input.copy()
    else:
        tall = prepared_input.melt(
            id_vars=[
                "Economy",
                "Date",
                "Medium",
                "Scenario",
                "Transport Type",
                "Vehicle Type",
                "Drive",
            ],
            value_name="Value",
            var_name="Measure",
        )

    variable_df = tall.loc[tall["Measure"].isin(["Mileage", "Stocks", "Intensity"])].copy()
    if variable_df.empty:
        raise ValueError("No optimisation variables found. Expected Mileage/Stocks/Intensity.")

    variable_df = variable_df[required_columns].copy()
    initial = tall.loc[tall["Measure"].isin(["Mileage", "Stocks", "Intensity"]), "Value"].to_numpy(dtype=float)
    actual = initial.copy()
    lower = np.maximum(0.0, initial * 0.8)
    upper = initial * 1.2

    economy = str(tall["Economy"].iloc[0])
    year = int(tall["Date"].iloc[0])
    scenario = str(tall["Scenario"].iloc[0])

    actual_energy_by_drive = (
        tall.loc[tall["Measure"] == "Energy_new"]
        .groupby("Drive", as_index=True)["Value"]
        .sum()
        .to_dict()
    )

    return OptimisationProblem(
        df_structure=variable_df.reset_index(drop=True),
        actual_values=actual,
        initial_values=initial,
        actual_energy_by_drive=actual_energy_by_drive,
        stocks_per_capita_constants=pd.DataFrame(),
        lower_bounds=lower,
        upper_bounds=upper,
        economy=economy,
        year=year,
        scenario=scenario,
    )


def objective_function(x: np.ndarray, problem: OptimisationProblem, candidate: CandidateConfig) -> float:
    """Compute scalar objective for one parameter vector.

    TODO:
    - Replace this with your full weighted objective terms.
    - Keep this function pure: no file I/O, no mutation outside local scope.
    """
    delta = x - problem.actual_values
    mse = float(np.mean(np.square(delta)))
    return mse


def energy_constraint_abs_error(
    x: np.ndarray, problem: OptimisationProblem, candidate: CandidateConfig
) -> float:
    """Aggregate absolute energy mismatch against target by drive.

    TODO:
    - Reconstruct energy by drive from x.
    - Return 0 when under tolerance to support equality-style constraint.
    """
    _ = candidate
    _ = problem
    _ = x
    return 0.0


def solve_candidate(problem: OptimisationProblem, candidate: CandidateConfig) -> OptimizeResult:
    """Run one optimisation solver call for one candidate config."""
    bounds = list(zip(problem.lower_bounds, problem.upper_bounds))
    constraints = [
        {
            "type": "eq",
            "fun": lambda x: energy_constraint_abs_error(x, problem, candidate),
        }
    ]

    maxiter = 2000 * max(1, candidate.iteration_multiplier)
    return minimize(
        fun=lambda x: objective_function(x, problem, candidate),
        x0=problem.initial_values,
        method=candidate.method,
        bounds=bounds,
        constraints=constraints if candidate.method in {"SLSQP", "trust-constr"} else (),
        options={"maxiter": maxiter},
    )


def validate_solution(
    result: OptimizeResult, problem: OptimisationProblem, candidate: CandidateConfig
) -> tuple[bool, str]:
    """Apply post-solve acceptance checks."""
    if not result.success:
        return False, str(result.message)

    energy_abs_error = energy_constraint_abs_error(result.x, problem, candidate)
    target_total = sum(problem.actual_energy_by_drive.values()) or 1.0
    if energy_abs_error > target_total * candidate.tolerance_pct:
        return False, f"Energy mismatch too high: {energy_abs_error:.6g}"

    return True, "accepted"


def finalize_solution(
    prepared_input: pd.DataFrame,
    problem: OptimisationProblem,
    result: OptimizeResult,
    meta: dict[str, Any],
) -> pd.DataFrame:
    """Convert optimized vector back into model output frame.

    TODO:
    - Write optimized x back to variable frame.
    - Recompute energy.
    - Add back non-major drives if they were removed.
    - Convert intensity back to efficiency if needed by caller.
    """
    _ = meta
    output = prepared_input.copy()
    output["__optimised__"] = False
    output.loc[: len(result.x) - 1, "__optimised__"] = True
    return output


def generate_candidates(
    methods: Sequence[str], parameter_grid: dict[str, Sequence[Any]]
) -> list[CandidateConfig]:
    """Expand search space into ordered candidate configs."""
    keys = list(parameter_grid.keys())
    combos = [dict(zip(keys, values)) for values in product(*parameter_grid.values())]
    candidates: list[CandidateConfig] = []
    for method in methods:
        for params in combos:
            candidates.append(
                CandidateConfig(
                    method=method,
                    iteration_multiplier=int(params.get("iteration_multiplier", 1)),
                    tolerance_pct=float(params.get("tolerance_pct", 0.001)),
                    use_same_mileage_across_vehicle_types=bool(
                        params.get("USE_SAME_MILEAGE_ACROSS_VEHICLE_TYPES", True)
                    ),
                    weights=ObjectiveWeights(
                        energy=float(params.get("w_mse_energy", 1.0)),
                        stocks=float(params.get("w_mse_stocks", 1.0)),
                        mileage=float(params.get("w_mse_mileage", 0.5)),
                        intensity=float(params.get("w_mse_intensity", 0.5)),
                        opposite_drive_types=float(params.get("w_mse_opposite_drive_types", 0.0)),
                        stocks_per_capita=float(params.get("w_mse_spc", 0.0)),
                    ),
                    bounds=BoundConfig(
                        max_change_stocks=float(params.get("maximum_proportional_change_in_stocks", 2.0)),
                        max_change_mileage=float(params.get("maximum_proportional_change_in_mileage", 0.2)),
                        max_change_intensity=float(params.get("maximum_proportional_change_in_intensity", 0.2)),
                    ),
                )
            )
    return candidates


def optimise_base_year_data(
    config: Any,
    input_data_new_road: pd.DataFrame,
    economy_id: str,
    *,
    methods: Sequence[str],
    parameter_grid: dict[str, Sequence[Any]],
    remove_non_major_variables: bool = True,
    remove_zeros: bool = True,
    logger: Callable[[str], None] | None = print,
) -> tuple[pd.DataFrame | None, dict[str, Any]]:
    """Top-level orchestration with an explicit, simple control flow."""
    prepared_input, meta = prepare_base_year_input(
        config=config,
        economy_id=economy_id,
        input_data_new_road=input_data_new_road,
        remove_non_major_variables=remove_non_major_variables,
        remove_zeros=remove_zeros,
    )

    outcomes: list[CandidateOutcome] = []
    for candidate in generate_candidates(methods, parameter_grid):
        try:
            problem = build_problem(config, economy_id, prepared_input, candidate)
            result = solve_candidate(problem, candidate)
            ok, reason = validate_solution(result, problem, candidate)
        except Exception as exc:  # noqa: BLE001
            outcomes.append(
                CandidateOutcome(config=candidate, result=None, success=False, reason=f"exception: {exc}")
            )
            if logger:
                logger(f"[FAIL] {candidate.method}: {exc}")
            continue

        outcomes.append(CandidateOutcome(config=candidate, result=result, success=ok, reason=reason))
        if logger:
            logger(f"[{'OK' if ok else 'FAIL'}] {candidate.method}: {reason}")
        if ok:
            output = finalize_solution(prepared_input, problem, result, meta)
            return output, {
                "success": True,
                "economy": problem.economy,
                "year": problem.year,
                "scenario": problem.scenario,
                "method": candidate.method,
                "candidate": candidate,
                "outcomes": outcomes,
            }

    return None, {
        "success": False,
        "economy_id": economy_id,
        "outcomes": outcomes,
    }

