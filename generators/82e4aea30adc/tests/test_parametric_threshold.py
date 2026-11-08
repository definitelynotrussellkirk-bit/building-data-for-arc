"""Prototype-only checks for the episode-level interior-area threshold."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest
from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, load_selected_generator

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace" / "parametric"))

from prototype import (  # noqa: E402
    ALLOWED_THRESHOLDS,
    DEFAULT_THRESHOLD,
    canonical_program,
    execute,
    fixture_inputs,
    generate_episode,
    materialize,
    public_challenge,
    render_program,
)

ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator("82e4aea30adc", root=ROOT)


def test_default_program_is_exact_canonical_and_canonical_labels_execute() -> None:
    canonical = canonical_program(ROOT)
    assert ALLOWED_THRESHOLDS == (1, 2)
    assert DEFAULT_THRESHOLD == 1
    assert render_program(canonical, 1) == canonical
    with RacketBridge() as bridge:
        for pair in canonical_pairs("82e4aea30adc", root=ROOT):
            assert execute(bridge, canonical, pair["input"]) == pair["output"]


def test_fixture_inputs_are_lawful_and_cover_both_sides_of_threshold() -> None:
    grids = fixture_inputs(17)
    assert len(grids) == 4
    for grid in grids:
        assert GEN.self_check(grid) == []
        profile = GEN.semantic_profile(grid)
        assert 1 in profile["interior_areas"]
        assert 2 in profile["interior_areas"]
        assert any(area > 2 for area in profile["interior_areas"])


def test_threshold_one_and_two_diverge_exactly_on_area_two_interiors() -> None:
    canonical = canonical_program(ROOT)
    grids = fixture_inputs(17)
    with RacketBridge() as bridge:
        outputs = {
            threshold: [
                execute(bridge, render_program(canonical, threshold), grid)
                for grid in grids
            ]
            for threshold in ALLOWED_THRESHOLDS
        }
    for low, high in zip(outputs[1], outputs[2]):
        assert low != high
        differing_cells = sum(
            value_low != value_high
            for row_low, row_high in zip(low, high)
            for value_low, value_high in zip(row_low, row_high)
        )
        assert differing_cells == 2


@pytest.mark.parametrize("threshold", ALLOWED_THRESHOLDS)
def test_episode_chooses_parameter_once_and_every_demo_refutes_other_setting(
    threshold: int,
) -> None:
    with RacketBridge() as bridge:
        episode = generate_episode(
            23,
            gray_max_interior_area=threshold,
            bridge=bridge,
        )
    assert episode["parameters"] == {"gray_max_interior_area": threshold}
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 1
    assert episode["rival"]["status"] == "distinguished"
    assert episode["rival"]["demo_differences"] == [0, 1, 2]
    assert episode["rival"]["query_differs"] is True
    public = public_challenge(episode)
    assert all("output" in pair for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert "parameters" not in public


def test_invalid_parameter_rejected() -> None:
    canonical = canonical_program(ROOT)
    with pytest.raises(ValueError):
        render_program(canonical, 3)
    with pytest.raises((TypeError, ValueError)):
        generate_episode(True, gray_max_interior_area=1)
    with pytest.raises(ValueError):
        generate_episode(0, gray_max_interior_area=0)


def test_materialized_gallery_has_both_settings_and_racket_provenance(
    tmp_path: Path,
) -> None:
    out = tmp_path / "gallery"
    report = materialize(out)
    assert report["status"] == "prototype"
    assert report["complete_episodes"] == 2
    assert report["default_program_exact_canonical"] is True
    assert report["all_labels_and_rivals_executed_in_racket"] is True
    private = [
        json.loads(path.read_text())
        for path in sorted((out / "private").glob("episode-*.json"))
    ]
    assert {
        row["parameters"]["gray_max_interior_area"] for row in private
    } == {1, 2}
    for path in sorted((out / "public").glob("episode-*.json")):
        public = json.loads(path.read_text())
        assert all(set(pair) == {"input"} for pair in public["test"])
