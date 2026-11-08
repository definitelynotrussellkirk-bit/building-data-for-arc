"""Prototype-only checks for the episode-level diagonal match threshold."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest
from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root

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


def test_default_program_is_exact_canonical_and_canonical_labels_execute():
    canonical = canonical_program(ROOT)
    assert ALLOWED_THRESHOLDS == (3, 4)
    assert DEFAULT_THRESHOLD == 4
    assert render_program(canonical, 4) == canonical
    with RacketBridge() as bridge:
        for pair in canonical_pairs("ad92d10d919c", root=ROOT):
            assert execute(bridge, render_program(canonical, 4), pair["input"]) == pair["output"]


def test_threshold_three_and_four_diverge_only_on_three_matching_corners():
    canonical = canonical_program(ROOT)
    grids = fixture_inputs(17)
    with RacketBridge() as bridge:
        outputs = {
            threshold: [execute(bridge, render_program(canonical, threshold), grid) for grid in grids]
            for threshold in ALLOWED_THRESHOLDS
        }
    assert all(outputs[3][index] != outputs[4][index] for index in range(len(grids)))
    for grid, low, high in zip(grids, outputs[3], outputs[4]):
        changed_low = sum(a != b for row_a, row_b in zip(grid, low) for a, b in zip(row_a, row_b))
        changed_high = sum(a != b for row_a, row_b in zip(grid, high) for a, b in zip(row_a, row_b))
        assert changed_low == changed_high + 1


@pytest.mark.parametrize("threshold", ALLOWED_THRESHOLDS)
def test_episode_chooses_parameter_once_and_every_demo_refutes_the_other_setting(threshold):
    with RacketBridge() as bridge:
        episode = generate_episode(23, required_matches=threshold, bridge=bridge)
    assert episode["parameters"] == {"required_matches": threshold}
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 1
    assert episode["rival"]["status"] == "distinguished"
    assert episode["rival"]["demo_differences"] == [0, 1, 2]
    assert episode["rival"]["query_differs"] is True
    public = public_challenge(episode)
    assert all("output" in pair for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert "parameters" not in public


def test_invalid_parameter_rejected():
    canonical = canonical_program(ROOT)
    with pytest.raises(ValueError):
        render_program(canonical, 2)
    with pytest.raises((TypeError, ValueError)):
        generate_episode(True, required_matches=3)
    with pytest.raises(ValueError):
        generate_episode(0, required_matches=5)


def test_materialized_gallery_has_both_settings_racket_provenance_and_masked_queries(tmp_path):
    out = tmp_path / "gallery"
    report = materialize(out)
    assert report["status"] == "prototype"
    assert report["complete_episodes"] == 2
    assert report["all_labels_and_rivals_executed_in_racket"] is True
    private = [json.loads(path.read_text()) for path in sorted((out / "private").glob("episode-*.json"))]
    assert {row["parameters"]["required_matches"] for row in private} == {3, 4}
    for path in sorted((out / "public").glob("episode-*.json")):
        public = json.loads(path.read_text())
        assert all(set(pair) == {"input"} for pair in public["test"])
