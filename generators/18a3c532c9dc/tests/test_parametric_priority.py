"""Prototype-only checks for episode-level quadrant priority direction."""
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
    ALLOWED_PRIORITY_MODES,
    DEFAULT_PRIORITY_MODE,
    canonical_program,
    execute,
    fixture_inputs,
    generate_episode,
    materialize,
    public_challenge,
    render_program,
)

ROOT = find_root(__file__)
TASK_ID = "18a3c532c9dc"


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as runtime:
        yield runtime


def test_default_program_is_exact_canonical_and_canonical_labels_execute(bridge):
    canonical = canonical_program(ROOT)
    assert ALLOWED_PRIORITY_MODES == ("canonical", "reversed")
    assert DEFAULT_PRIORITY_MODE == "canonical"
    assert render_program(canonical, "canonical") == canonical
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        assert execute(bridge, canonical, pair["input"]) == pair["output"]


def test_modes_diverge_on_every_controlled_fixture(bridge):
    canonical = canonical_program(ROOT)
    programs = {
        mode: render_program(canonical, mode)
        for mode in ALLOWED_PRIORITY_MODES
    }
    assert programs["canonical"] != programs["reversed"]
    for grid in fixture_inputs(75):
        outputs = {
            mode: execute(bridge, program, grid)
            for mode, program in programs.items()
        }
        assert outputs["canonical"] != outputs["reversed"]


@pytest.mark.parametrize("mode", ALLOWED_PRIORITY_MODES)
def test_episode_chooses_mode_once_and_every_demo_refutes_the_rival(mode, bridge):
    episode = generate_episode(75, priority_mode=mode, bridge=bridge)
    assert episode["parameters"] == {"priority_mode": mode}
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 1
    assert episode["rival"]["status"] == "distinguished"
    assert episode["rival"]["demo_differences"] == [0, 1, 2]
    assert episode["rival"]["query_differs"] is True

    public = public_challenge(episode)
    assert all("output" in pair for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert "parameters" not in public
    assert "program" not in public


def test_invalid_parameter_and_seed_are_rejected():
    canonical = canonical_program(ROOT)
    with pytest.raises(ValueError):
        render_program(canonical, "clockwise")
    with pytest.raises((TypeError, ValueError)):
        generate_episode(True, priority_mode="canonical")
    with pytest.raises(ValueError):
        generate_episode(0, priority_mode="clockwise")


def test_materialized_gallery_has_both_modes_racket_provenance_and_masked_queries(tmp_path):
    out = tmp_path / "gallery"
    report = materialize(out, seed=75)
    assert report["status"] == "prototype"
    assert report["default_program_exact_canonical"] is True
    assert report["complete_episodes"] == 2
    assert report["all_labels_and_rivals_executed_in_racket"] is True
    assert report["all_demonstrations_refute_other_declared_setting"] is True
    assert set(report["source_sha256"]) == {
        "generators/18a3c532c9dc/workspace/parametric/prototype.py",
        "generators/18a3c532c9dc/workspace/parametric/README.md",
        "generators/18a3c532c9dc/tests/test_parametric_priority.py",
    }

    private = [
        json.loads(path.read_text())
        for path in sorted((out / "private").glob("episode-*.json"))
    ]
    assert {row["parameters"]["priority_mode"] for row in private} == {
        "canonical",
        "reversed",
    }
    assert (out / "private" / "setting-difference-witness.json").is_file()
    for path in sorted((out / "public").glob("episode-*.json")):
        public = json.loads(path.read_text())
        assert all(set(pair) == {"input"} for pair in public["test"])
        serialized = json.dumps(public)
        assert "priority_mode" not in serialized
        assert "rule!" not in serialized
