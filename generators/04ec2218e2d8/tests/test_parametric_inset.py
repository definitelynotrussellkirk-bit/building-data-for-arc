"""Prototype-only checks for the episode-level center-inset parameter."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "04ec2218e2d8"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = HOME / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    assert PROTOTYPE.is_file(), f"missing prototype: {PROTOTYPE}"
    spec = importlib.util.spec_from_file_location(
        "parametric_inset_prototype",
        PROTOTYPE,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as runtime:
        yield runtime


def test_default_program_is_exact_canonical_and_executes_public_labels(bridge):
    prototype = load_prototype()
    canonical = prototype.canonical_program(ROOT)
    assert prototype.ALLOWED_INSET_DIVISORS == (4, 3)
    assert prototype.DEFAULT_INSET_DIVISOR == 4
    assert prototype.render_program(canonical, 4) == canonical
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        assert prototype.execute(bridge, canonical, pair["input"]) == pair["output"]


def test_alternative_program_changes_only_the_pinned_divisor():
    prototype = load_prototype()
    canonical = prototype.canonical_program(ROOT)
    alternative = prototype.render_program(canonical, 3)
    assert alternative != canonical
    assert canonical.count("(quotient (min hh ww) 4)") == 1
    assert alternative.count("(quotient (min hh ww) 3)") == 1
    assert alternative.replace(
        "(quotient (min hh ww) 3)",
        "(quotient (min hh ww) 4)",
        1,
    ) == canonical


def test_fixture_inputs_are_lawful_and_every_one_distinguishes_settings(bridge):
    prototype = load_prototype()
    generator, _path, _digest = load_selected_generator(TASK_ID, root=ROOT)
    canonical = prototype.canonical_program(ROOT)
    programs = {
        divisor: prototype.render_program(canonical, divisor)
        for divisor in prototype.ALLOWED_INSET_DIVISORS
    }
    grids = prototype.fixture_inputs(481)
    assert len(grids) == 4
    for grid in grids:
        assert generator.self_check(grid) == []
        outputs = {
            divisor: prototype.execute(bridge, program, grid)
            for divisor, program in programs.items()
        }
        assert outputs[4] != outputs[3]


def test_seed_selects_one_setting_for_the_whole_episode_and_rival_is_refuted(bridge):
    prototype = load_prototype()
    episodes = [
        prototype.generate_episode(seed, bridge=bridge)
        for seed in (481, 482)
    ]
    assert {
        episode["parameters"]["inset_divisor"]
        for episode in episodes
    } == {3, 4}
    for episode in episodes:
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert episode["rival"]["status"] == "distinguished"
        assert episode["rival"]["demo_differences"] == [0, 1, 2]
        assert episode["rival"]["query_differs"] is True
        assert episode["setting_selected_once"] is True

        public = prototype.public_challenge(episode)
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        serialized = json.dumps(public)
        assert "inset_divisor" not in serialized
        assert "rule!" not in serialized


def test_invalid_seed_and_parameter_are_rejected():
    prototype = load_prototype()
    canonical = prototype.canonical_program(ROOT)
    for value in (True, False, 4.0, "4", 2, 5):
        with pytest.raises((TypeError, ValueError)):
            prototype.render_program(canonical, value)
    for seed in (True, False, 1.0, "1"):
        with pytest.raises(TypeError):
            prototype.generate_episode(seed)


def test_materialized_gallery_retains_racket_provenance_and_masks_queries(tmp_path):
    prototype = load_prototype()
    out = tmp_path / "gallery"
    report = prototype.materialize(out, seed=481)
    assert report["status"] == "prototype"
    assert report["default_program_exact_canonical"] is True
    assert report["canonical_pairs_all_match"] is True
    assert report["complete_episodes"] == 2
    assert report["all_labels_and_rivals_executed_in_racket"] is True
    assert report["all_demonstrations_refute_other_declared_setting"] is True
    assert report["all_queries_distinguish_other_declared_setting"] is True
    assert set(report["episode_parameters"]) == {"3", "4"}
    assert set(report["source_sha256"]) == {
        "generators/04ec2218e2d8/workspace/parametric/prototype.py",
        "generators/04ec2218e2d8/workspace/parametric/README.md",
        "generators/04ec2218e2d8/tests/test_parametric_inset.py",
    }

    private = [
        json.loads(path.read_text())
        for path in sorted((out / "private").glob("episode-*.json"))
    ]
    assert {
        row["parameters"]["inset_divisor"]
        for row in private
    } == {3, 4}
    assert (out / "private" / "setting-difference-witness.json").is_file()
    assert (out / "private" / "canonical-default-check.json").is_file()
    assert (out / "private" / "program-inset-4.rkt").is_file()
    assert (out / "private" / "program-inset-3.rkt").is_file()
    for path in sorted((out / "public").glob("episode-*.json")):
        public = json.loads(path.read_text())
        assert all(set(pair) == {"input"} for pair in public["test"])
        serialized = json.dumps(public)
        assert "inset_divisor" not in serialized
        assert "rule!" not in serialized
