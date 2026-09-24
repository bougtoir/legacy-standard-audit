from collections.abc import Callable

import numpy as np


def percentile_interval(values: np.ndarray) -> tuple[float, float]:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return float("nan"), float("nan")
    return float(np.percentile(finite, 2.5)), float(np.percentile(finite, 97.5))


def bootstrap_ratio(
    numerators: np.ndarray,
    denominators: np.ndarray,
    replicates: int,
    rng: np.random.Generator,
) -> tuple[float, float]:
    numerator = np.asarray(numerators, dtype=float)
    denominator = np.asarray(denominators, dtype=float)
    if numerator.shape != denominator.shape or numerator.ndim != 1:
        raise ValueError("Bootstrap inputs must be aligned one-dimensional arrays")
    estimates = np.empty(replicates, dtype=float)
    for index in range(replicates):
        sample = rng.integers(0, numerator.size, numerator.size)
        sampled_denominator = denominator[sample].sum()
        estimates[index] = (
            numerator[sample].sum() / sampled_denominator
            if sampled_denominator != 0
            else np.nan
        )
    return percentile_interval(estimates)


def circular_block_bootstrap_ratio(
    numerators: np.ndarray,
    denominators: np.ndarray,
    block_size: int,
    replicates: int,
    rng: np.random.Generator,
) -> tuple[float, float]:
    numerator = np.asarray(numerators, dtype=float)
    denominator = np.asarray(denominators, dtype=float)
    if numerator.shape != denominator.shape or numerator.ndim != 1:
        raise ValueError("Bootstrap inputs must be aligned one-dimensional arrays")
    if numerator.size == 0:
        raise ValueError("Bootstrap inputs must not be empty")
    if block_size < 1 or block_size > numerator.size:
        raise ValueError("Block size must be between one and the sample size")
    block_offsets = np.arange(block_size)
    block_count = int(np.ceil(numerator.size / block_size))
    estimates = np.empty(replicates, dtype=float)
    for index in range(replicates):
        starts = rng.integers(0, numerator.size, block_count)
        sample = ((starts[:, None] + block_offsets) % numerator.size).ravel()
        sample = sample[: numerator.size]
        sampled_denominator = denominator[sample].sum()
        estimates[index] = (
            numerator[sample].sum() / sampled_denominator
            if sampled_denominator != 0
            else np.nan
        )
    return percentile_interval(estimates)


def contiguous_group_blocks(
    groups: np.ndarray,
    block_size: int,
) -> list[list[np.ndarray]]:
    labels = np.asarray(groups)
    if labels.ndim != 1 or labels.size == 0:
        raise ValueError("Group labels must be a non-empty one-dimensional array")
    if block_size < 1:
        raise ValueError("Block size must be positive")
    boundaries = np.flatnonzero(labels[1:] != labels[:-1]) + 1
    segments = np.split(np.arange(labels.size), boundaries)
    if any(segment.size < block_size for segment in segments):
        raise ValueError("Block size must not exceed any contiguous group")
    return [
        [
            segment[start : start + block_size]
            for start in range(segment.size - block_size + 1)
        ]
        for segment in segments
    ]


def grouped_block_bootstrap_ratio(
    numerators: np.ndarray,
    denominators: np.ndarray,
    groups: np.ndarray,
    block_size: int,
    replicates: int,
    rng: np.random.Generator,
) -> tuple[float, float]:
    numerator = np.asarray(numerators, dtype=float)
    denominator = np.asarray(denominators, dtype=float)
    labels = np.asarray(groups)
    if (
        numerator.shape != denominator.shape
        or numerator.shape != labels.shape
        or numerator.ndim != 1
    ):
        raise ValueError(
            "Bootstrap inputs and group labels must be aligned one-dimensional arrays"
        )
    blocks = [
        block
        for grouped_blocks in contiguous_group_blocks(labels, block_size)
        for block in grouped_blocks
    ]
    block_count = int(np.ceil(numerator.size / block_size))
    estimates = np.empty(replicates, dtype=float)
    for replicate in range(replicates):
        selections = rng.integers(0, len(blocks), block_count)
        sample = np.concatenate([blocks[index] for index in selections])
        sample = sample[: numerator.size]
        sampled_denominator = denominator[sample].sum()
        estimates[replicate] = (
            numerator[sample].sum() / sampled_denominator
            if sampled_denominator != 0
            else np.nan
        )
    return percentile_interval(estimates)


def bootstrap_statistic(
    values: np.ndarray,
    statistic: Callable[[np.ndarray], float],
    replicates: int,
    rng: np.random.Generator,
) -> tuple[float, float]:
    data = np.asarray(values, dtype=float)
    estimates = np.empty(replicates, dtype=float)
    for index in range(replicates):
        estimates[index] = statistic(rng.choice(data, data.size, replace=True))
    return percentile_interval(estimates)


def maintenance_cost_rate(
    lifetimes: np.ndarray,
    replacement_age: int,
    preventive_cost: float,
    failure_cost: float,
) -> float:
    lives = np.asarray(lifetimes, dtype=float)
    failed = lives <= replacement_age
    costs = np.where(failed, failure_cost, preventive_cost)
    durations = np.minimum(lives, replacement_age)
    return float(costs.sum() / durations.sum())


def select_fixed_replacement_age(
    lifetimes: np.ndarray,
    preventive_cost: float,
    failure_cost: float,
) -> tuple[int, float]:
    lives = np.asarray(lifetimes, dtype=int)
    candidates = range(1, int(lives.max()) + 1)
    scored = [
        (
            age,
            maintenance_cost_rate(lives, age, preventive_cost, failure_cost),
        )
        for age in candidates
    ]
    return min(scored, key=lambda item: (item[1], item[0]))


def condition_informed_cost_rate(
    lifetimes: np.ndarray,
    lead_cycles: int,
    preventive_cost: float,
) -> float:
    durations = np.maximum(np.asarray(lifetimes, dtype=float) - lead_cycles, 1)
    return float(preventive_cost * durations.size / durations.sum())


def shift_load_to_low_price_hours(
    load: np.ndarray,
    price: np.ndarray,
    flexible_fraction: float,
) -> np.ndarray:
    baseline = np.asarray(load, dtype=float)
    prices = np.asarray(price, dtype=float)
    if baseline.shape != prices.shape:
        raise ValueError("Load and price arrays must have matching shapes")
    if not 0 <= flexible_fraction <= 1:
        raise ValueError("Flexible fraction must be between zero and one")
    lower = baseline * (1 - flexible_fraction)
    upper = baseline * (1 + flexible_fraction)
    shifted = lower.copy()
    energy_to_allocate = float(baseline.sum() - lower.sum())
    for index in np.argsort(prices, kind="stable"):
        addition = min(float(upper[index] - shifted[index]), energy_to_allocate)
        shifted[index] += addition
        energy_to_allocate -= addition
        if energy_to_allocate <= 1e-9:
            break
    if abs(float(shifted.sum() - baseline.sum())) > 1e-6:
        raise RuntimeError("Load shifting failed to conserve daily energy")
    return shifted


def saturation_delay_proxy(
    first_volume: np.ndarray,
    second_volume: np.ndarray,
    first_green_share: float,
) -> np.ndarray:
    first = np.asarray(first_volume, dtype=float)
    second = np.asarray(second_volume, dtype=float)
    share = float(np.clip(first_green_share, 0.05, 0.95))
    return first**2 / share + second**2 / (1 - share)


def kilowatt_hours_per_square_metre_to_megajoules_per_square_metre(
    radiation_kwh_m2_day: np.ndarray,
) -> np.ndarray:
    return np.asarray(radiation_kwh_m2_day, dtype=float) * 3.6


def fao56_reference_et0(
    day_of_year: np.ndarray,
    latitude_degrees: float,
    elevation_m: float,
    temperature_mean_c: np.ndarray,
    temperature_min_c: np.ndarray,
    temperature_max_c: np.ndarray,
    relative_humidity_percent: np.ndarray,
    wind_speed_2m_m_s: np.ndarray,
    solar_radiation_mj_m2_day: np.ndarray,
) -> np.ndarray:
    day = np.asarray(day_of_year, dtype=float)
    latitude = np.deg2rad(latitude_degrees)
    t_mean = np.asarray(temperature_mean_c, dtype=float)
    t_min = np.asarray(temperature_min_c, dtype=float)
    t_max = np.asarray(temperature_max_c, dtype=float)
    humidity = np.asarray(relative_humidity_percent, dtype=float)
    wind = np.asarray(wind_speed_2m_m_s, dtype=float)
    radiation = np.asarray(solar_radiation_mj_m2_day, dtype=float)

    inverse_distance = 1 + 0.033 * np.cos(2 * np.pi * day / 365)
    solar_declination = 0.409 * np.sin(2 * np.pi * day / 365 - 1.39)
    sunset_hour_angle = np.arccos(
        np.clip(-np.tan(latitude) * np.tan(solar_declination), -1, 1)
    )
    extraterrestrial = (
        24
        * 60
        / np.pi
        * 0.0820
        * inverse_distance
        * (
            sunset_hour_angle * np.sin(latitude) * np.sin(solar_declination)
            + np.cos(latitude)
            * np.cos(solar_declination)
            * np.sin(sunset_hour_angle)
        )
    )
    clear_sky = (0.75 + 2e-5 * elevation_m) * extraterrestrial
    saturation_max = 0.6108 * np.exp(17.27 * t_max / (t_max + 237.3))
    saturation_min = 0.6108 * np.exp(17.27 * t_min / (t_min + 237.3))
    saturation_mean = (saturation_max + saturation_min) / 2
    actual_vapor = (
        humidity
        / 100
        * 0.6108
        * np.exp(17.27 * t_mean / (t_mean + 237.3))
    )
    net_shortwave = (1 - 0.23) * radiation
    stefan_boltzmann = 4.903e-9
    cloud_term = np.clip(1.35 * radiation / np.maximum(clear_sky, 1e-6) - 0.35, 0.05, 1)
    net_longwave = (
        stefan_boltzmann
        * (((t_max + 273.16) ** 4 + (t_min + 273.16) ** 4) / 2)
        * (0.34 - 0.14 * np.sqrt(np.maximum(actual_vapor, 0)))
        * cloud_term
    )
    net_radiation = net_shortwave - net_longwave
    pressure = 101.3 * ((293 - 0.0065 * elevation_m) / 293) ** 5.26
    psychrometric = 0.000665 * pressure
    slope = (
        4098
        * (0.6108 * np.exp(17.27 * t_mean / (t_mean + 237.3)))
        / (t_mean + 237.3) ** 2
    )
    numerator = (
        0.408 * slope * net_radiation
        + psychrometric
        * (900 / (t_mean + 273))
        * wind
        * (saturation_mean - actual_vapor)
    )
    denominator = slope + psychrometric * (1 + 0.34 * wind)
    return np.maximum(numerator / denominator, 0)


def repeated_halving_loss(aspect_ratio: float) -> float:
    ratio = float(aspect_ratio)
    if ratio <= 0:
        raise ValueError("Aspect ratio must be positive")
    return float((ratio - 2 / ratio) ** 2)
