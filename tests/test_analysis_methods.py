import math
import sys
from pathlib import Path

import numpy as np


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from analysis_methods import (  # noqa: E402
    circular_block_bootstrap_ratio,
    contiguous_group_blocks,
    condition_informed_cost_rate,
    grouped_block_bootstrap_ratio,
    kilowatt_hours_per_square_metre_to_megajoules_per_square_metre,
    maintenance_cost_rate,
    repeated_halving_loss,
    saturation_delay_proxy,
    select_fixed_replacement_age,
    shift_load_to_low_price_hours,
)
from build_final_falsification import (  # noqa: E402
    strongest_case_removal_assessment,
    strongest_case_removal_count,
)
from build_manuscript import (  # noqa: E402
    strongest_case_abstract_text,
    transition_abstract_text,
)
from build_transition_evidence import (  # noqa: E402
    apply_evidence_levels,
    transition_decision,
)
from make_figures import audit_state_rows  # noqa: E402
from publication_utils import sentence_number  # noqa: E402


def test_load_shifting_conserves_energy_and_reduces_cost():
    load = np.array([10.0, 10.0, 10.0])
    price = np.array([100.0, 10.0, 50.0])
    shifted = shift_load_to_low_price_hours(load, price, 0.1)
    assert math.isclose(float(shifted.sum()), float(load.sum()))
    assert float(np.dot(shifted, price)) < float(np.dot(load, price))


def test_circular_block_bootstrap_is_reproducible():
    numerator = np.arange(1.0, 15.0)
    denominator = np.full(14, 10.0)
    first = circular_block_bootstrap_ratio(
        numerator,
        denominator,
        block_size=7,
        replicates=100,
        rng=np.random.default_rng(123),
    )
    second = circular_block_bootstrap_ratio(
        numerator,
        denominator,
        block_size=7,
        replicates=100,
        rng=np.random.default_rng(123),
    )
    assert first == second


def test_grouped_blocks_do_not_cross_irrigation_seasons():
    years = np.repeat(np.array([2020, 2021, 2022]), 6)
    grouped_blocks = contiguous_group_blocks(years, block_size=4)
    assert len(grouped_blocks) == 3
    assert all(
        np.unique(years[block]).size == 1
        for annual_blocks in grouped_blocks
        for block in annual_blocks
    )


def test_grouped_block_bootstrap_is_reproducible():
    numerator = np.arange(1.0, 19.0)
    denominator = np.full(18, 10.0)
    years = np.repeat(np.array([2020, 2021, 2022]), 6)
    first = grouped_block_bootstrap_ratio(
        numerator,
        denominator,
        years,
        block_size=4,
        replicates=100,
        rng=np.random.default_rng(123),
    )
    second = grouped_block_bootstrap_ratio(
        numerator,
        denominator,
        years,
        block_size=4,
        replicates=100,
        rng=np.random.default_rng(123),
    )
    assert first == second


def test_fixed_age_selection_matches_minimum_cost_rate():
    lifetimes = np.array([80, 100, 120, 140])
    age, rate = select_fixed_replacement_age(lifetimes, 1, 5)
    candidates = [
        maintenance_cost_rate(lifetimes, candidate, 1, 5)
        for candidate in range(1, 141)
    ]
    assert math.isclose(rate, min(candidates))
    assert math.isclose(rate, candidates[age - 1])


def test_perfect_condition_information_uses_surviving_life():
    rate = condition_informed_cost_rate(np.array([100, 120]), 5, 1)
    assert math.isclose(rate, 2 / (95 + 115))


def test_adaptive_signal_split_minimizes_proxy():
    first = np.array([100.0])
    second = np.array([300.0])
    static = saturation_delay_proxy(first, second, 0.5)
    adaptive = saturation_delay_proxy(first, second, 0.25)
    assert adaptive[0] < static[0]


def test_nasa_power_radiation_is_converted_from_kwh_to_mj():
    converted = kilowatt_hours_per_square_metre_to_megajoules_per_square_metre(
        np.array([0.0, 1.0, 5.0])
    )
    assert np.array_equal(converted, np.array([0.0, 3.6, 18.0]))


def test_square_root_two_is_exact_halving_invariant():
    assert repeated_halving_loss(math.sqrt(2)) < 1e-30
    assert repeated_halving_loss(1.5) > 0


def test_transition_status_tracks_assessed_evidence_level():
    gates = [{"case_id": "BE03"}, {"case_id": "WK07"}]
    assessments = [
        {"case_id": "BE03;WK07", "evidence_level": "B"},
        {"case_id": "WK07", "evidence_level": "A"},
    ]
    updated = apply_evidence_levels(gates, assessments)
    assert updated[0]["highest_evidence_level"] == "B"
    assert updated[0]["transition_status"] == "threshold_only"
    assert updated[1]["highest_evidence_level"] == "A"
    assert updated[1]["transition_status"] == "level_a_evidence_available"
    decision = transition_decision(updated)
    assert "WK07" in decision
    assert "does not automatically" in decision


def test_strongest_case_removal_count_uses_current_classifications():
    case_results = {
        "BE03": {"classification": "material_mismatch"},
        "WK07": {"classification": "material_mismatch_under_oracle"},
        "UI01": {"classification": "small_or_uncertain_mismatch"},
        "UI09": {"classification": "material_mismatch_under_oracle"},
    }
    assert strongest_case_removal_count(case_results) == 1
    weakened, interpretation = strongest_case_removal_assessment(1, 2, 3)
    assert weakened == "Yes—material-count claim"
    assert "1 of 2 retained" in interpretation


def test_manuscript_and_figure_language_tracks_dynamic_evidence():
    values = {
        "FALS_REMOVE_BOTH_MATERIAL_COUNT": {"estimate": "1"},
    }
    transition = {
        "case_gates": [
            {"case_id": "BE03", "highest_evidence_level": "A"},
            {"case_id": "WK07", "highest_evidence_level": "B"},
            {"case_id": "UI01", "highest_evidence_level": "B"},
            {"case_id": "UI09", "highest_evidence_level": "B"},
        ]
    }
    results = {
        "BE03": {"classification": "material_mismatch"},
        "WK07": {"classification": "material_mismatch_under_oracle"},
        "UI01": {"classification": "small_or_uncertain_mismatch"},
        "UI09": {"classification": "material_mismatch_under_oracle"},
    }
    assert "left 1 material primary label" in strongest_case_abstract_text(
        values
    )
    assert "BE03" in transition_abstract_text(transition)
    rows = audit_state_rows(results, transition)
    assert rows[0][3].startswith("Level A")
    assert "threshold met" in rows[0][2]
    assert "Material label" in rows[0][4]


def test_sentence_initial_counts_are_spelled_out():
    assert sentence_number(0) == "Zero"
    assert sentence_number(2) == "Two"
    assert sentence_number(7) == "Seven"
    assert sentence_number(122) == "A total of 122"
