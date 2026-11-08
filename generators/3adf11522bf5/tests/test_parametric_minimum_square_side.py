"""Racket-backed contract tests for the isolated minimum-side prototype."""
from __future__ import annotations

from functools import lru_cache
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root

TASK_ID = "3adf11522bf5"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)


@lru_cache(maxsize=1)
def prototype():
    assert PROTOTYPE_PATH.is_file(), "minimum-side parametric prototype is not implemented"
    spec = importlib.util.spec_from_file_location(
        "arc3adf_minimum_side_prototype", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(max_calls_before_restart=128) as instance:
        yield instance


def test_default_program_is_exact_canonical_and_parameter_is_strict():
    p = prototype()
    canonical = p.canonical_program(root=ROOT)
    assert p.DEFAULT_MIN_SIDE == 2
    assert p.ALLOWED_MIN_SIDES == (2, 3)
    assert p.render_program(2, root=ROOT) == canonical
    assert p.render_program(3, root=ROOT) != canonical
    for invalid in (None, True, 1, 4, 2.0, "2"):
        with pytest.raises(ValueError, match="minimum_disjoint_square_side"):
            p.render_program(invalid, root=ROOT)


def test_default_program_matches_every_canonical_label(bridge):
    p = prototype()
    source = p.render_program(2, root=ROOT)
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 4
    for pair in pairs:
        assert p.execute(bridge, source, pair["input"]) == pair["output"]


def test_shared_lawful_witness_distinguishes_thresholds(bridge):
    p = prototype()
    grid = p.distinguishing_witness(root=ROOT)
    outputs = {
        value: p.execute(bridge, p.render_program(value, root=ROOT), grid)
        for value in p.ALLOWED_MIN_SIDES
    }
    assert outputs[2] != outputs[3]


@pytest.mark.parametrize("minimum_side", [2, 3])
def test_episode_uses_one_setting_and_demonstrations_refute_the_rival(
    bridge, minimum_side
):
    p = prototype()
    public, private = p.generate_episode(
        17,
        bridge=bridge,
        root=ROOT,
        minimum_disjoint_square_side=minimum_side,
    )
    assert private["parameters"][p.PARAMETER] == minimum_side
    assert private["input_profiles"] == ["canonical2", "teaching", "teaching", "teaching"]
    assert len(public["train"]) == 3
    assert len(public["test"]) == 1
    assert set(public["test"][0]) == {"input"}
    assert private["parameter_rival"]["status"] == "refuted_on_demonstrations"
    assert private["parameter_rival"]["refuting_demonstration_indices"]
    assert private["parameter_rival"]["query_differs"] is True
    assert p.PARAMETER not in json.dumps(public)


def test_input_schedule_is_independent_of_selected_parameter(bridge):
    p = prototype()
    public_two, _ = p.generate_episode(
        29,
        bridge=bridge,
        root=ROOT,
        minimum_disjoint_square_side=2,
    )
    public_three, _ = p.generate_episode(
        29,
        bridge=bridge,
        root=ROOT,
        minimum_disjoint_square_side=3,
    )
    assert [pair["input"] for pair in public_two["train"]] == [
        pair["input"] for pair in public_three["train"]
    ]
    assert public_two["test"][0]["input"] == public_three["test"][0]["input"]
    assert [pair["output"] for pair in public_two["train"]] != [
        pair["output"] for pair in public_three["train"]
    ]


def test_materialized_evidence_is_racket_derived_and_public_safe(bridge, tmp_path):
    p = prototype()
    out = tmp_path / "evidence"
    report = p.write_evidence(
        out,
        seed_start=7300,
        bridge=bridge,
        root=ROOT,
    )
    assert report["status"] == "proposed_prototype"
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["settings_exercised"] == 2
    assert report["counts"]["canonical_labels_checked"] == 4
    assert report["counts"]["ambiguous_parameter_rivals"] == 0
    assert {row["parameters"][p.PARAMETER] for row in report["episodes"]} == {2, 3}
    for row in report["episodes"]:
        public = json.loads((out / row["public_path"]).read_text())
        assert p.PARAMETER not in json.dumps(public)
        assert set(public["test"][0]) == {"input"}
