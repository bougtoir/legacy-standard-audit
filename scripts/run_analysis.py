import csv
import json
import math
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from analysis_methods import (
    circular_block_bootstrap_ratio,
    condition_informed_cost_rate,
    fao56_reference_et0,
    maintenance_cost_rate,
    repeated_halving_loss,
    saturation_delay_proxy,
    select_fixed_replacement_age,
    shift_load_to_low_price_hours,
)


PROJECT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT / "analysis_config.json"
OUTPUT_DIR = PROJECT / "outputs" / "analysis"
VALUES_PATH = PROJECT / "MANUSCRIPT_VALUES.csv"
SUMMARY_PATH = OUTPUT_DIR / "case_summary.csv"
RESULTS_PATH = OUTPUT_DIR / "case_results.json"
SENSITIVITY_PATH = OUTPUT_DIR / "model_sensitivity.csv"
FALSIFICATION_PATH = OUTPUT_DIR / "cross_case_falsification.csv"


def load_config() -> dict[str, object]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def value_row(
    config: dict[str, object],
    value_id: str,
    case_id: str,
    metric: str,
    estimate: object,
    unit: str,
    output: str,
    lower: object = "",
    upper: object = "",
    format_spec: str = ".3f",
    notes: str = "",
) -> dict[str, object]:
    return {
        "value_id": value_id,
        "case_id": case_id,
        "metric": metric,
        "estimate": estimate,
        "lower": lower,
        "upper": upper,
        "unit": unit,
        "analysis_output": output,
        "generated_utc": config["generated_utc"],
        "format_spec": format_spec,
        "notes": notes,
    }


def analyze_be03(
    config: dict[str, object],
    rng: np.random.Generator,
) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    case_config = config["BE03"]
    if not isinstance(case_config, dict):
        raise TypeError("BE03 configuration must be an object")
    path = (
        PROJECT
        / "data/raw/case_selection/BE03_uci_occupancy_data_2026-09-24.csv"
    )
    raw = pd.read_csv(path, dtype=str)
    timestamps = pd.to_datetime(raw["date"], errors="coerce")
    occupancy = pd.to_numeric(raw["Occupancy"], errors="coerce")
    valid = timestamps.notna() & occupancy.notna()
    data = pd.DataFrame(
        {
            "timestamp": timestamps[valid],
            "occupied": occupancy[valid].astype(int),
        }
    )
    invalid_rows = int((~valid).sum())
    data = data.sort_values("timestamp").drop_duplicates("timestamp")
    start_hour = int(case_config["schedule_start_hour"])
    end_hour = int(case_config["schedule_end_hour"])
    data["fixed_on"] = (
        (data["timestamp"].dt.dayofweek < 5)
        & (data["timestamp"].dt.hour >= start_hour)
        & (data["timestamp"].dt.hour < end_hour)
    )
    hold = int(case_config["occupancy_hold_minutes"])
    occupied_series = data.set_index("timestamp")["occupied"]
    adaptive = occupied_series.rolling(
        f"{hold + 1}min", min_periods=1
    ).max()
    data["adaptive_on"] = adaptive.to_numpy(dtype=bool)
    data["fixed_false_off"] = (data["occupied"] == 1) & ~data["fixed_on"]
    data["adaptive_false_off"] = (data["occupied"] == 1) & ~data["adaptive_on"]
    data["date"] = data["timestamp"].dt.date

    daily = data.groupby("date").agg(
        fixed_on=("fixed_on", "sum"),
        adaptive_on=("adaptive_on", "sum"),
        fixed_false_off=("fixed_false_off", "sum"),
        adaptive_false_off=("adaptive_false_off", "sum"),
        observations=("occupied", "size"),
    )
    daily.to_csv(OUTPUT_DIR / "BE03_daily_policy.csv", lineterminator="\n")
    energy_saved = daily["fixed_on"] - daily["adaptive_on"]
    energy_ratio = float(energy_saved.sum() / daily["fixed_on"].sum())
    lower, upper = circular_block_bootstrap_ratio(
        energy_saved.to_numpy(),
        daily["fixed_on"].to_numpy(),
        int(config["temporal_block_sizes"]["BE03_days"]),
        int(config["bootstrap_replicates"]),
        rng,
    )
    penalty = float(case_config["occupied_false_off_penalty"])
    fixed_objective = float(
        data["fixed_on"].sum() + penalty * data["fixed_false_off"].sum()
    )
    adaptive_objective = float(
        data["adaptive_on"].sum() + penalty * data["adaptive_false_off"].sum()
    )
    objective_regret = (fixed_objective - adaptive_objective) / len(data)
    classification_thresholds = config["classification_thresholds"]
    classification = (
        "material_mismatch_under_oracle_benchmark"
        if lower
        > float(classification_thresholds["BE03_lower_energy_reduction"])
        and data["adaptive_false_off"].sum() == 0
        else "small_or_uncertain_mismatch"
    )
    result = {
        "case_id": "BE03",
        "role": "primary",
        "classification": classification,
        "observations": int(len(data)),
        "invalid_repeated_header_rows_removed": invalid_rows,
        "fixed_schedule": f"weekdays {start_hour:02d}:00-{end_hour:02d}:00",
        "occupancy_hold_minutes": hold,
        "fixed_on_nominal_minutes": int(data["fixed_on"].sum()),
        "adaptive_on_nominal_minutes": int(data["adaptive_on"].sum()),
        "energy_reduction_fraction": energy_ratio,
        "energy_reduction_95_interval": [lower, upper],
        "fixed_occupied_false_off_minutes": int(data["fixed_false_off"].sum()),
        "adaptive_occupied_false_off_minutes": int(
            data["adaptive_false_off"].sum()
        ),
        "normalized_objective_regret_per_observation": objective_regret,
        "limitation": (
            "Adaptive policy is an oracle occupancy-responsive upper bound; "
            "sensor error, commissioning, lamp power, and installation cost are not observed."
        ),
    }
    values = [
        value_row(
            config,
            "BE03_ENERGY_REDUCTION",
            "BE03",
            "fixed_schedule_energy_reduction",
            energy_ratio,
            "fraction",
            "outputs/analysis/case_results.json",
            lower,
            upper,
            ".1%",
            "Oracle occupancy response with ten-minute hold",
        ),
        value_row(
            config,
            "BE03_FALSE_OFF_FIXED",
            "BE03",
            "fixed_schedule_occupied_false_off",
            int(data["fixed_false_off"].sum()),
            "nominal minute-observations",
            "outputs/analysis/case_results.json",
            format_spec=",d",
        ),
        value_row(
            config,
            "BE03_CLASSIFICATION",
            "BE03",
            "case_classification",
            classification,
            "category",
            "outputs/analysis/case_results.json",
            format_spec="s",
        ),
    ]
    sensitivity = []
    for hours in case_config["schedule_sensitivity"]:
        sensitivity_start, sensitivity_end = int(hours[0]), int(hours[1])
        fixed = (
            (data["timestamp"].dt.dayofweek < 5)
            & (data["timestamp"].dt.hour >= sensitivity_start)
            & (data["timestamp"].dt.hour < sensitivity_end)
        )
        if fixed.sum() == 0:
            reduction = float("nan")
        else:
            reduction = float((fixed.sum() - data["adaptive_on"].sum()) / fixed.sum())
        sensitivity.append(
            {
                "case_id": "BE03",
                "parameter": "fixed_schedule_hours",
                "setting": f"{sensitivity_start:02d}:00-{sensitivity_end:02d}:00",
                "metric": "energy_reduction_fraction",
                "estimate": reduction,
                "unit": "fraction",
            }
        )
    return result, values, sensitivity


def read_cmapss_lifetimes() -> tuple[np.ndarray, np.ndarray]:
    path = PROJECT / "data/raw/case_selection/WK07_CMAPSSData_2026-09-24.zip"
    with zipfile.ZipFile(path) as archive:
        with archive.open("train_FD001.txt") as handle:
            train = pd.read_csv(
                handle, sep=r"\s+", header=None, usecols=[0, 1], names=["unit", "cycle"]
            )
        with archive.open("test_FD001.txt") as handle:
            test = pd.read_csv(
                handle, sep=r"\s+", header=None, usecols=[0, 1], names=["unit", "cycle"]
            )
        with archive.open("RUL_FD001.txt") as handle:
            rul = pd.read_csv(handle, sep=r"\s+", header=None, names=["rul"])
    train_lifetimes = train.groupby("unit")["cycle"].max().to_numpy(dtype=int)
    observed_test = test.groupby("unit")["cycle"].max().to_numpy(dtype=int)
    test_lifetimes = observed_test + rul["rul"].to_numpy(dtype=int)
    if train_lifetimes.size != 100 or test_lifetimes.size != 100:
        raise RuntimeError("Unexpected C-MAPSS FD001 unit count")
    return train_lifetimes, test_lifetimes


def analyze_wk07(
    config: dict[str, object],
    rng: np.random.Generator,
) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    case_config = config["WK07"]
    if not isinstance(case_config, dict):
        raise TypeError("WK07 configuration must be an object")
    train_lifetimes, test_lifetimes = read_cmapss_lifetimes()
    pd.DataFrame(
        {
            "unit": np.arange(1, train_lifetimes.size + 1),
            "training_lifetime_cycles": train_lifetimes,
            "evaluation_lifetime_cycles": test_lifetimes,
        }
    ).to_csv(OUTPUT_DIR / "WK07_lifetimes.csv", index=False, lineterminator="\n")
    preventive = float(case_config["preventive_cost"])
    failure = preventive * float(case_config["failure_cost_ratio"])
    lead = int(case_config["condition_lead_cycles"])
    replacement_age, training_rate = select_fixed_replacement_age(
        train_lifetimes, preventive, failure
    )
    fixed_rate = maintenance_cost_rate(
        test_lifetimes, replacement_age, preventive, failure
    )
    condition_rate = condition_informed_cost_rate(
        test_lifetimes, lead, preventive
    )
    regret = fixed_rate - condition_rate
    relative_regret = regret / fixed_rate
    replicates = int(config["bootstrap_replicates"])
    boot = np.empty(replicates)
    for index in range(replicates):
        sample = rng.choice(test_lifetimes, test_lifetimes.size, replace=True)
        boot[index] = maintenance_cost_rate(
            sample, replacement_age, preventive, failure
        ) - condition_informed_cost_rate(sample, lead, preventive)
    lower, upper = float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))
    classification_thresholds = config["classification_thresholds"]
    classification = (
        "material_mismatch_under_oracle_benchmark"
        if lower > 0
        and relative_regret
        > float(classification_thresholds["WK07_relative_regret"])
        else "small_or_uncertain_mismatch"
    )
    result = {
        "case_id": "WK07",
        "role": "primary",
        "classification": classification,
        "dataset_type": "simulated run-to-failure trajectories",
        "training_units": int(train_lifetimes.size),
        "evaluation_units": int(test_lifetimes.size),
        "failure_to_preventive_cost_ratio": failure / preventive,
        "condition_lead_cycles": lead,
        "training_selected_fixed_age_cycles": replacement_age,
        "training_fixed_cost_rate": training_rate,
        "evaluation_fixed_cost_rate": fixed_rate,
        "evaluation_oracle_condition_cost_rate": condition_rate,
        "static_regret_cost_per_cycle": regret,
        "static_regret_95_interval": [lower, upper],
        "relative_regret_fraction": relative_regret,
        "limitation": (
            "C-MAPSS is simulated and the condition policy has perfect remaining-life "
            "information; results compare policy classes rather than an observed maintenance program."
        ),
    }
    values = [
        value_row(
            config,
            "WK07_FIXED_AGE",
            "WK07",
            "training_selected_fixed_replacement_age",
            replacement_age,
            "cycles",
            "outputs/analysis/case_results.json",
            format_spec=".0f",
        ),
        value_row(
            config,
            "WK07_STATIC_REGRET",
            "WK07",
            "fixed_vs_oracle_condition_static_regret",
            regret,
            "normalized cost per cycle",
            "outputs/analysis/case_results.json",
            lower,
            upper,
            ".5f",
        ),
        value_row(
            config,
            "WK07_RELATIVE_REGRET",
            "WK07",
            "fixed_vs_oracle_condition_relative_regret",
            relative_regret,
            "fraction",
            "outputs/analysis/case_results.json",
            format_spec=".1%",
        ),
        value_row(
            config,
            "WK07_CLASSIFICATION",
            "WK07",
            "case_classification",
            classification,
            "category",
            "outputs/analysis/case_results.json",
            format_spec="s",
        ),
    ]
    sensitivity = []
    for cost_ratio in case_config["failure_cost_sensitivity"]:
        age, _ = select_fixed_replacement_age(
            train_lifetimes, preventive, preventive * float(cost_ratio)
        )
        fixed = maintenance_cost_rate(
            test_lifetimes, age, preventive, preventive * float(cost_ratio)
        )
        for lead_cycles in case_config["lead_cycle_sensitivity"]:
            condition = condition_informed_cost_rate(
                test_lifetimes, int(lead_cycles), preventive
            )
            sensitivity.append(
                {
                    "case_id": "WK07",
                    "parameter": "failure_cost_ratio_and_lead",
                    "setting": f"cost={cost_ratio};lead={lead_cycles}",
                    "metric": "static_regret_cost_per_cycle",
                    "estimate": fixed - condition,
                    "unit": "normalized cost per cycle",
                }
            )
    return result, values, sensitivity


def analyze_ui01(
    config: dict[str, object],
    rng: np.random.Generator,
) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    case_config = config["UI01"]
    if not isinstance(case_config, dict):
        raise TypeError("UI01 configuration must be an object")
    path = (
        PROJECT
        / "data/raw/case_selection/UI01_opsd_time_series_60min_2020-10-06.csv"
    )
    data = pd.read_csv(
        path,
        usecols=[
            "utc_timestamp",
            "DE_LU_load_actual_entsoe_transparency",
            "DE_LU_price_day_ahead",
        ],
    )
    data.columns = ["timestamp", "load_mw", "price_eur_mwh"]
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True)
    data = data.dropna()
    data["date"] = data["timestamp"].dt.date
    complete_dates = data.groupby("date").size()
    data = data[data["date"].isin(complete_dates[complete_dates == 24].index)]

    def evaluate_fraction(fraction: float) -> pd.DataFrame:
        rows = []
        for date, day in data.groupby("date", sort=True):
            day = day.sort_values("timestamp")
            load = day["load_mw"].to_numpy(dtype=float)
            price = day["price_eur_mwh"].to_numpy(dtype=float)
            shifted = shift_load_to_low_price_hours(load, price, fraction)
            baseline_cost = float(np.dot(load, price))
            adaptive_cost = float(np.dot(shifted, price))
            rows.append(
                {
                    "date": date,
                    "baseline_cost": baseline_cost,
                    "adaptive_cost": adaptive_cost,
                    "savings": baseline_cost - adaptive_cost,
                    "load_mwh": float(load.sum()),
                    "shifted_mwh": float(np.abs(shifted - load).sum() / 2),
                }
            )
        return pd.DataFrame(rows)

    primary_fraction = float(case_config["primary_flexible_fraction"])
    daily = evaluate_fraction(primary_fraction)
    daily.to_csv(OUTPUT_DIR / "UI01_daily_shift.csv", index=False, lineterminator="\n")
    savings_per_mwh = float(daily["savings"].sum() / daily["load_mwh"].sum())
    cost_reduction = float(daily["savings"].sum() / daily["baseline_cost"].sum())
    savings_per_shifted = float(
        daily["savings"].sum() / daily["shifted_mwh"].sum()
    )
    lower, upper = circular_block_bootstrap_ratio(
        daily["savings"].to_numpy(),
        daily["load_mwh"].to_numpy(),
        int(config["temporal_block_sizes"]["UI01_days"]),
        int(config["bootstrap_replicates"]),
        rng,
    )
    classification = "small_or_uncertain_mismatch"
    result = {
        "case_id": "UI01",
        "role": "primary",
        "classification": classification,
        "complete_days": int(len(daily)),
        "primary_flexible_fraction": primary_fraction,
        "procurement_savings_eur_per_mwh": savings_per_mwh,
        "procurement_savings_eur_per_mwh_95_interval": [lower, upper],
        "procurement_cost_reduction_fraction": cost_reduction,
        "savings_eur_per_shifted_mwh": savings_per_shifted,
        "limitation": (
            "Observed day-ahead prices are held fixed while load is shifted. This is a "
            "partial-equilibrium technical upper bound, not an estimate of customer response "
            "or equilibrium wholesale-price effects."
        ),
    }
    values = [
        value_row(
            config,
            "UI01_SAVINGS_PER_MWH",
            "UI01",
            "interval_aware_procurement_savings",
            savings_per_mwh,
            "EUR per MWh baseline load",
            "outputs/analysis/case_results.json",
            lower,
            upper,
            ".3f",
        ),
        value_row(
            config,
            "UI01_COST_REDUCTION",
            "UI01",
            "interval_aware_procurement_cost_reduction",
            cost_reduction,
            "fraction",
            "outputs/analysis/case_results.json",
            format_spec=".2%",
        ),
        value_row(
            config,
            "UI01_CLASSIFICATION",
            "UI01",
            "case_classification",
            classification,
            "category",
            "outputs/analysis/case_results.json",
            format_spec="s",
        ),
    ]
    sensitivity = []
    for fraction in case_config["flexible_fraction_sensitivity"]:
        evaluated = evaluate_fraction(float(fraction))
        sensitivity.append(
            {
                "case_id": "UI01",
                "parameter": "flexible_load_fraction",
                "setting": fraction,
                "metric": "procurement_savings_eur_per_mwh",
                "estimate": float(
                    evaluated["savings"].sum() / evaluated["load_mwh"].sum()
                ),
                "unit": "EUR per MWh baseline load",
            }
        )
    return result, values, sensitivity


def nasa_power_frame() -> tuple[pd.DataFrame, float, float]:
    path = (
        PROJECT
        / "data/raw/case_selection/UI09_nasa_power_davis_2015_2024_2026-09-24.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    parameters = payload["properties"]["parameter"]
    frame = pd.DataFrame(
        {
            name: pd.Series(values)
            for name, values in parameters.items()
        }
    )
    frame.index = pd.to_datetime(frame.index, format="%Y%m%d")
    frame = frame.apply(pd.to_numeric, errors="coerce").replace(-999, np.nan).dropna()
    longitude, latitude, elevation = payload["geometry"]["coordinates"]
    if not math.isclose(float(longitude), -121.74, abs_tol=0.1):
        raise RuntimeError("Unexpected NASA POWER location")
    return frame, float(latitude), float(elevation)


def analyze_ui09(
    config: dict[str, object],
    rng: np.random.Generator,
) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    case_config = config["UI09"]
    if not isinstance(case_config, dict):
        raise TypeError("UI09 configuration must be an object")
    weather, latitude, elevation = nasa_power_frame()
    weather["et0_mm"] = fao56_reference_et0(
        weather.index.dayofyear.to_numpy(),
        latitude,
        elevation,
        weather["T2M"].to_numpy(),
        weather["T2M_MIN"].to_numpy(),
        weather["T2M_MAX"].to_numpy(),
        weather["RH2M"].to_numpy(),
        weather["WS2M"].to_numpy(),
        weather["ALLSKY_SFC_SW_DWN"].to_numpy(),
    )
    start = str(case_config["growing_season_start"])
    end = str(case_config["growing_season_end"])
    month_day = weather.index.strftime("%m-%d")
    season = weather[(month_day >= start) & (month_day <= end)].copy()
    season["week"] = season.index.to_period("W-SUN").start_time
    weekly = season.groupby("week").agg(
        et0_mm=("et0_mm", "sum"),
        precipitation_mm=("PRECTOTCORR", "sum"),
    )
    weekly["net_requirement_mm"] = np.maximum(
        weekly["et0_mm"] - weekly["precipitation_mm"], 0
    )
    training_years = {int(year) for year in case_config["training_years"]}
    evaluation_years = {int(year) for year in case_config["evaluation_years"]}
    training = weekly[weekly.index.year.isin(training_years)]
    evaluation = weekly[weekly.index.year.isin(evaluation_years)].copy()
    calendar_application = float(training["net_requirement_mm"].median())
    evaluation["calendar_application_mm"] = calendar_application
    evaluation["adaptive_application_mm"] = evaluation["net_requirement_mm"]
    evaluation["calendar_overapplication_mm"] = np.maximum(
        calendar_application - evaluation["net_requirement_mm"], 0
    )
    evaluation["calendar_shortfall_mm"] = np.maximum(
        evaluation["net_requirement_mm"] - calendar_application, 0
    )
    penalty = float(case_config["shortfall_penalty"])
    evaluation["calendar_objective"] = (
        calendar_application + penalty * evaluation["calendar_shortfall_mm"]
    )
    evaluation["adaptive_objective"] = evaluation["adaptive_application_mm"]
    evaluation["regret"] = (
        evaluation["calendar_objective"] - evaluation["adaptive_objective"]
    )
    evaluation.to_csv(
        OUTPUT_DIR / "UI09_weekly_irrigation.csv", lineterminator="\n"
    )
    objective_regret = float(
        evaluation["regret"].sum() / evaluation["calendar_objective"].sum()
    )
    lower, upper = circular_block_bootstrap_ratio(
        evaluation["regret"].to_numpy(),
        evaluation["calendar_objective"].to_numpy(),
        int(config["temporal_block_sizes"]["UI09_weeks"]),
        int(config["bootstrap_replicates"]),
        rng,
    )
    classification_thresholds = config["classification_thresholds"]
    classification = (
        "material_mismatch_under_oracle_benchmark"
        if lower
        > float(classification_thresholds["UI09_lower_objective_regret"])
        else "small_or_uncertain_mismatch"
    )
    result = {
        "case_id": "UI09",
        "role": "primary",
        "classification": classification,
        "training_weeks": int(len(training)),
        "evaluation_weeks": int(len(evaluation)),
        "calendar_application_mm_per_week": calendar_application,
        "adaptive_mean_application_mm_per_week": float(
            evaluation["adaptive_application_mm"].mean()
        ),
        "calendar_overapplication_mm": float(
            evaluation["calendar_overapplication_mm"].sum()
        ),
        "calendar_shortfall_mm": float(evaluation["calendar_shortfall_mm"].sum()),
        "transition_adjusted_break_even_mm_water_equivalent": float(
            evaluation["regret"].sum()
        ),
        "normalized_objective_regret_fraction": objective_regret,
        "normalized_objective_regret_95_interval": [lower, upper],
        "limitation": (
            "The calendar comparator is trained from historical weekly reference-crop "
            "requirements and the adaptive policy has perfect weekly weather information. "
            "Crop coefficients, soil storage, application efficiency, and yield response are omitted."
        ),
    }
    values = [
        value_row(
            config,
            "UI09_CALENDAR_APPLICATION",
            "UI09",
            "calendar_weekly_irrigation",
            calendar_application,
            "mm per week",
            "outputs/analysis/case_results.json",
            format_spec=".2f",
        ),
        value_row(
            config,
            "UI09_OBJECTIVE_REGRET",
            "UI09",
            "calendar_vs_weather_adaptive_objective_regret",
            objective_regret,
            "fraction",
            "outputs/analysis/case_results.json",
            lower,
            upper,
            ".1%",
        ),
        value_row(
            config,
            "UI09_CLASSIFICATION",
            "UI09",
            "case_classification",
            classification,
            "category",
            "outputs/analysis/case_results.json",
            format_spec="s",
        ),
    ]
    sensitivity = []
    mean_application = float(training["net_requirement_mm"].mean())
    for method, application in [
        ("median", calendar_application),
        ("mean", mean_application),
    ]:
        shortfall = np.maximum(
            evaluation["net_requirement_mm"].to_numpy() - application, 0
        )
        adaptive = evaluation["net_requirement_mm"].to_numpy()
        for penalty_value in case_config["shortfall_penalty_sensitivity"]:
            calendar_objective = application + float(penalty_value) * shortfall
            regret = calendar_objective - adaptive
            sensitivity.append(
                {
                    "case_id": "UI09",
                    "parameter": "calendar_estimator_and_shortfall_penalty",
                    "setting": f"{method};penalty={penalty_value}",
                    "metric": "normalized_objective_regret_fraction",
                    "estimate": float(regret.sum() / calendar_objective.sum()),
                    "unit": "fraction",
                }
            )
    return result, values, sensitivity


def traffic_hour_columns(columns: list[str]) -> list[str]:
    excluded = {"id", "segmentid", "roadway_name", "from", "to", "direction", "date"}
    return [column for column in columns if column not in excluded]


def analyze_tr01(
    config: dict[str, object],
    rng: np.random.Generator,
) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    path = (
        PROJECT
        / "data/raw/case_selection/TR01_nyc_traffic_counts_complete_2026-09-24.csv"
    )
    data = pd.read_csv(path)
    hours = traffic_hour_columns(data.columns.tolist())
    for column in hours:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    candidate_pairs = [("NB", "SB"), ("EB", "WB")]
    candidates: list[tuple[int, int, str, str]] = []
    for first_direction, second_direction in candidate_pairs:
        subset = data[data["direction"].isin([first_direction, second_direction])]
        counts = subset.groupby(["segmentid", "date"])["direction"].nunique()
        paired = counts[counts == 2].groupby("segmentid").size()
        for segment_id, paired_days in paired.items():
            candidates.append(
                (
                    int(paired_days),
                    int(segment_id),
                    first_direction,
                    second_direction,
                )
            )
    if not candidates:
        raise RuntimeError("No paired traffic directions found")
    paired_days, segment_id, first_direction, second_direction = max(
        candidates, key=lambda item: (item[0], -item[1])
    )
    selected = data[
        (data["segmentid"] == segment_id)
        & data["direction"].isin([first_direction, second_direction])
    ]
    grouped = selected.groupby(["date", "direction"])[hours].mean()
    dates = sorted(
        date
        for date, directions in selected.groupby("date")["direction"].nunique().items()
        if directions == 2
    )
    split = max(1, len(dates) // 2)
    training_dates = dates[:split]
    evaluation_dates = dates[split:]
    train_first = grouped.loc[
        [(date, first_direction) for date in training_dates]
    ].to_numpy(dtype=float)
    train_second = grouped.loc[
        [(date, second_direction) for date in training_dates]
    ].to_numpy(dtype=float)
    static_share = float(
        np.nansum(train_first) / (np.nansum(train_first) + np.nansum(train_second))
    )
    date_rows = []
    for date in evaluation_dates:
        first = grouped.loc[(date, first_direction)].to_numpy(dtype=float)
        second = grouped.loc[(date, second_direction)].to_numpy(dtype=float)
        valid = np.isfinite(first) & np.isfinite(second)
        first = first[valid]
        second = second[valid]
        static_proxy = saturation_delay_proxy(first, second, static_share)
        total = first + second
        adaptive_proxy = total**2
        date_rows.append(
            {
                "date": date,
                "static_proxy": float(static_proxy.sum()),
                "adaptive_proxy": float(adaptive_proxy.sum()),
                "reduction": float((static_proxy - adaptive_proxy).sum()),
                "hours": int(valid.sum()),
            }
        )
    evaluation = pd.DataFrame(date_rows)
    evaluation.to_csv(
        OUTPUT_DIR / "TR01_daily_proxy.csv", index=False, lineterminator="\n"
    )
    reduction_fraction = float(
        evaluation["reduction"].sum() / evaluation["static_proxy"].sum()
    )
    lower, upper = circular_block_bootstrap_ratio(
        evaluation["reduction"].to_numpy(),
        evaluation["static_proxy"].to_numpy(),
        int(config["temporal_block_sizes"]["TR01_days"]),
        int(config["bootstrap_replicates"]),
        rng,
    )
    metadata = selected.iloc[0]
    classification = "insufficient_evidence"
    result = {
        "case_id": "TR01",
        "role": "supplementary",
        "classification": classification,
        "selected_segment_id": segment_id,
        "roadway_name": str(metadata["roadway_name"]),
        "directions": [first_direction, second_direction],
        "paired_days": paired_days,
        "training_days": len(training_dates),
        "evaluation_days": len(evaluation_dates),
        "static_green_share_first_direction": static_share,
        "responsive_allocation_proxy_reduction_fraction": reduction_fraction,
        "responsive_allocation_proxy_reduction_95_interval": [lower, upper],
        "limitation": (
            "The dataset provides roadway counts, not verified intersection geometry, "
            "deployed signal plans, saturation flows, pedestrian constraints, queues, or crashes. "
            "The result is a demand-allocation sensitivity only and cannot support redesign."
        ),
    }
    values = [
        value_row(
            config,
            "TR01_PROXY_REDUCTION",
            "TR01",
            "responsive_allocation_delay_proxy_reduction",
            reduction_fraction,
            "fraction",
            "outputs/analysis/case_results.json",
            lower,
            upper,
            ".1%",
            "Supplementary sensitivity; not a deployment effect",
        ),
        value_row(
            config,
            "TR01_CLASSIFICATION",
            "TR01",
            "case_classification",
            classification,
            "category",
            "outputs/analysis/case_results.json",
            format_spec="s",
        ),
    ]
    sensitivity = [
        {
            "case_id": "TR01",
            "parameter": "static_green_share",
            "setting": "training_estimate",
            "metric": "responsive_allocation_proxy_reduction_fraction",
            "estimate": reduction_fraction,
            "unit": "fraction",
        }
    ]
    return result, values, sensitivity


def analyze_controls(
    config: dict[str, object],
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    nc01_classification = "insufficient_evidence"
    nc01 = {
        "case_id": "NC01",
        "role": "network_control",
        "classification": nc01_classification,
        "static_regret": None,
        "transition_adjusted_regret": None,
        "break_even_identity": (
            "Replace only when discounted compatibility-adjusted operating benefit "
            "exceeds conversion, coordination, and stranded-asset cost."
        ),
        "limitation": (
            "The public ISO metadata verifies the compatibility standard but contains "
            "no fleet, handling-network, conversion-cost, or alternative-design performance data."
        ),
    }
    optimum = math.sqrt(2)
    loss = repeated_halving_loss(optimum)
    nc03_classification = "no_mismatch_for_repeated_halving_objective"
    nc03 = {
        "case_id": "NC03",
        "role": "analytic_null_control",
        "classification": nc03_classification,
        "objective": "preserve aspect ratio after halving parallel to the shorter side",
        "optimal_aspect_ratio": optimum,
        "self_similarity_loss": loss,
        "proof": "r = 2/r implies r = sqrt(2) for positive aspect ratios",
        "limitation": (
            "The null applies only to repeated-halving geometric similarity, not to "
            "screen use, printing economics, accessibility, or every paper-format objective."
        ),
    }
    values = [
        value_row(
            config,
            "NC01_CLASSIFICATION",
            "NC01",
            "case_classification",
            nc01_classification,
            "category",
            "outputs/analysis/case_results.json",
            format_spec="s",
        ),
        value_row(
            config,
            "NC03_OPTIMAL_RATIO",
            "NC03",
            "repeated_halving_optimal_aspect_ratio",
            optimum,
            "long side / short side",
            "outputs/analysis/case_results.json",
            format_spec=".6f",
        ),
        value_row(
            config,
            "NC03_SELF_SIMILARITY_LOSS",
            "NC03",
            "repeated_halving_self_similarity_loss",
            loss,
            "squared ratio difference",
            "outputs/analysis/case_results.json",
            format_spec=".3e",
        ),
        value_row(
            config,
            "NC03_CLASSIFICATION",
            "NC03",
            "case_classification",
            nc03_classification,
            "category",
            "outputs/analysis/case_results.json",
            format_spec="s",
        ),
    ]
    sensitivity = [
        {
            "case_id": "NC03",
            "parameter": "aspect_ratio",
            "setting": "sqrt(2)",
            "metric": "repeated_halving_self_similarity_loss",
            "estimate": loss,
            "unit": "squared ratio difference",
        }
    ]
    return [nc01, nc03], values, sensitivity


def build_falsification(results: list[dict[str, object]]) -> list[dict[str, object]]:
    primary = [result for result in results if result["role"] == "primary"]
    material = {
        str(result["case_id"])
        for result in primary
        if str(result["classification"]).startswith("material_mismatch")
    }
    rows = [
        {
            "test": "baseline_primary_classification_count",
            "omitted_case": "",
            "primary_cases_retained": len(primary),
            "material_oracle_mismatches": len(material),
            "insufficient_or_uncertain": len(primary) - len(material),
            "interpretation": (
                "Classification count only; incomparable case outcomes are not pooled "
                "into a universal effect size."
            ),
        }
    ]
    for omitted in primary:
        retained = [
            result for result in primary if result["case_id"] != omitted["case_id"]
        ]
        retained_material = sum(
            str(result["classification"]).startswith("material_mismatch")
            for result in retained
        )
        rows.append(
            {
                "test": "leave_one_case_and_domain_out",
                "omitted_case": omitted["case_id"],
                "primary_cases_retained": len(retained),
                "material_oracle_mismatches": retained_material,
                "insufficient_or_uncertain": len(retained) - retained_material,
                "interpretation": (
                    "No leave-one-out result licenses a population causal claim; "
                    "the frozen cases are a designed audit set."
                ),
            }
        )
    rows.extend(
        [
            {
                "test": "exclude_simulated_case",
                "omitted_case": "WK07",
                "primary_cases_retained": len(primary) - 1,
                "material_oracle_mismatches": len(material - {"WK07"}),
                "insufficient_or_uncertain": (
                    len(primary) - 1 - len(material - {"WK07"})
                ),
                "interpretation": "Source-quality sensitivity excluding C-MAPSS simulation.",
            },
            {
                "test": "negative_controls",
                "omitted_case": "",
                "primary_cases_retained": len(primary),
                "material_oracle_mismatches": len(material),
                "insufficient_or_uncertain": len(primary) - len(material),
                "interpretation": (
                    "NC03 returns the pre-specified analytic null; NC01 remains "
                    "unquantified because transition-cost evidence is absent."
                ),
            },
        ]
    )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"No rows for {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0].keys()), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    config = load_config()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(int(config["random_seed"]))
    results = []
    values = []
    sensitivity = []
    for analysis in [analyze_be03, analyze_wk07, analyze_ui01, analyze_ui09, analyze_tr01]:
        result, case_values, case_sensitivity = analysis(config, rng)
        results.append(result)
        values.extend(case_values)
        sensitivity.extend(case_sensitivity)
    control_results, control_values, control_sensitivity = analyze_controls(config)
    results.extend(control_results)
    values.extend(control_values)
    sensitivity.extend(control_sensitivity)
    by_case = {str(result["case_id"]): result for result in results}
    context_metrics = [
        ("BE03_OBSERVATIONS", "BE03", "observations", "observations", ",d"),
        (
            "BE03_FIXED_ON",
            "BE03",
            "fixed_on_nominal_minutes",
            "nominal minute-observations",
            ",d",
        ),
        (
            "BE03_ADAPTIVE_ON",
            "BE03",
            "adaptive_on_nominal_minutes",
            "nominal minute-observations",
            ",d",
        ),
        ("BE03_HOLD", "BE03", "occupancy_hold_minutes", "minutes", ".0f"),
        ("WK07_TRAINING_UNITS", "WK07", "training_units", "simulated units", ".0f"),
        (
            "WK07_EVALUATION_UNITS",
            "WK07",
            "evaluation_units",
            "simulated units",
            ".0f",
        ),
        (
            "WK07_FIXED_RATE",
            "WK07",
            "evaluation_fixed_cost_rate",
            "normalized cost per cycle",
            ".5f",
        ),
        (
            "WK07_CONDITION_RATE",
            "WK07",
            "evaluation_oracle_condition_cost_rate",
            "normalized cost per cycle",
            ".5f",
        ),
        ("UI01_COMPLETE_DAYS", "UI01", "complete_days", "days", ",d"),
        (
            "UI01_FLEXIBLE_FRACTION",
            "UI01",
            "primary_flexible_fraction",
            "fraction",
            ".1%",
        ),
        (
            "UI01_SAVINGS_SHIFTED",
            "UI01",
            "savings_eur_per_shifted_mwh",
            "EUR per shifted MWh",
            ".2f",
        ),
        ("UI09_TRAINING_WEEKS", "UI09", "training_weeks", "weeks", ",d"),
        ("UI09_EVALUATION_WEEKS", "UI09", "evaluation_weeks", "weeks", ",d"),
        (
            "UI09_ADAPTIVE_APPLICATION",
            "UI09",
            "adaptive_mean_application_mm_per_week",
            "mm per week",
            ".2f",
        ),
        (
            "UI09_OVERAPPLICATION",
            "UI09",
            "calendar_overapplication_mm",
            "mm over evaluation period",
            ".1f",
        ),
        (
            "UI09_SHORTFALL",
            "UI09",
            "calendar_shortfall_mm",
            "mm over evaluation period",
            ".1f",
        ),
        ("TR01_PAIRED_DAYS", "TR01", "paired_days", "days", ",d"),
        ("TR01_TRAINING_DAYS", "TR01", "training_days", "days", ",d"),
        ("TR01_EVALUATION_DAYS", "TR01", "evaluation_days", "days", ",d"),
        (
            "TR01_STATIC_SHARE",
            "TR01",
            "static_green_share_first_direction",
            "fraction",
            ".1%",
        ),
    ]
    for value_id, case_id, key, unit, format_spec in context_metrics:
        values.append(
            value_row(
                config,
                value_id,
                case_id,
                key,
                by_case[case_id][key],
                unit,
                "outputs/analysis/case_results.json",
                format_spec=format_spec,
            )
        )
    for index, row in enumerate(sensitivity, start=1):
        values.append(
            value_row(
                config,
                f"SENS_{row['case_id']}_{index:02d}",
                str(row["case_id"]),
                str(row["metric"]),
                row["estimate"],
                str(row["unit"]),
                "outputs/analysis/model_sensitivity.csv",
                format_spec=".6g",
                notes=f"{row['parameter']}: {row['setting']}",
            )
        )
    primary_results = [result for result in results if result["role"] == "primary"]
    material_results = [
        result
        for result in primary_results
        if str(result["classification"]).startswith("material_mismatch")
    ]
    values.extend(
        [
            value_row(
                config,
                "CROSS_PRIMARY_CASES",
                "CROSS",
                "primary_cases",
                len(primary_results),
                "cases",
                "outputs/analysis/cross_case_falsification.csv",
                format_spec=".0f",
            ),
            value_row(
                config,
                "CROSS_MATERIAL_ORACLE_CASES",
                "CROSS",
                "material_oracle_mismatch_cases",
                len(material_results),
                "cases",
                "outputs/analysis/cross_case_falsification.csv",
                format_spec=".0f",
            ),
        ]
    )
    candidates = pd.read_csv(PROJECT / "candidate_registry.csv")
    prior_art = pd.read_csv(PROJECT / "TFSC_prior_art_matrix.csv")
    freeze = json.loads((PROJECT / "frozen_case_set.json").read_text(encoding="utf-8"))
    values.extend(
        [
            value_row(
                config,
                "DESIGN_CANDIDATES",
                "DESIGN",
                "candidate_universe_size",
                len(candidates),
                "candidates",
                "candidate_registry.csv",
                format_spec=".0f",
            ),
            value_row(
                config,
                "DESIGN_DOMAINS",
                "DESIGN",
                "candidate_domains",
                candidates["domain"].nunique(),
                "domains",
                "candidate_registry.csv",
                format_spec=".0f",
            ),
            value_row(
                config,
                "DESIGN_FROZEN_CASES",
                "DESIGN",
                "frozen_case_count",
                len(freeze["frozen_cases"]),
                "cases",
                "frozen_case_set.json",
                format_spec=".0f",
            ),
            value_row(
                config,
                "DESIGN_VERIFIED_PRIOR_ART",
                "DESIGN",
                "doi_verified_prior_art_count",
                int((prior_art["verification_status"] == "verified").sum()),
                "references",
                "TFSC_prior_art_matrix.csv",
                format_spec=".0f",
            ),
        ]
    )
    thresholds = config["classification_thresholds"]
    values.extend(
        [
            value_row(
                config,
                "THRESHOLD_BE03",
                "DESIGN",
                "BE03_material_lower_bound",
                thresholds["BE03_lower_energy_reduction"],
                "fraction",
                "analysis_config.json",
                format_spec=".0%",
            ),
            value_row(
                config,
                "THRESHOLD_WK07",
                "DESIGN",
                "WK07_material_relative_regret",
                thresholds["WK07_relative_regret"],
                "fraction",
                "analysis_config.json",
                format_spec=".0%",
            ),
            value_row(
                config,
                "THRESHOLD_UI09",
                "DESIGN",
                "UI09_material_lower_bound",
                thresholds["UI09_lower_objective_regret"],
                "fraction",
                "analysis_config.json",
                format_spec=".0%",
            ),
        ]
    )

    payload = {
        "analysis_version": config["analysis_version"],
        "generated_utc": config["generated_utc"],
        "selection_freeze_sha256": (
            PROJECT / "frozen_case_set.sha256"
        ).read_text(encoding="utf-8").split()[0],
        "case_results": results,
        "cross_case_constraints": {
            "universal_effect_size": "not_estimated",
            "causal_population_claim": "not_supported",
            "transition_adjusted_recommendations": (
                "withheld unless case-specific switching and coordination costs are observed"
            ),
        },
    }
    RESULTS_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    summary = [
        {
            "case_id": result["case_id"],
            "role": result["role"],
            "classification": result["classification"],
            "limitation": result["limitation"],
        }
        for result in results
    ]
    write_csv(SUMMARY_PATH, summary)
    write_csv(SENSITIVITY_PATH, sensitivity)
    write_csv(FALSIFICATION_PATH, build_falsification(results))
    write_csv(VALUES_PATH, values)
    print(f"Wrote {len(results)} case results and {len(values)} manuscript values")


if __name__ == "__main__":
    main()
