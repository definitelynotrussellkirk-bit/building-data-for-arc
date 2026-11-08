"""Focused regressions for real mirror rivals, query rotation, and diagnostics."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "72f0b65569a4"
ROOT = find_root(__file__)
PROBE_PATH = ROOT / "generators" / TASK_ID / "workspace/mirror_contract_probe.py"
SPEC = importlib.util.spec_from_file_location("mirror_contract_probe_for_tests", PROBE_PATH)
assert SPEC is not None and SPEC.loader is not None
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


@pytest.fixture(scope="module")
def selected():
    return load_selected_generator(TASK_ID, root=ROOT)


@pytest.fixture(scope="module")
def labeled(selected):
    """One small authoritative batch is shared by all semantic assertions."""
    from arcpuzzles import Catalog

    gen, _source, digest = selected
    records = {}
    canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    for index, pair in enumerate(canonical):
        records[("canonical", index)] = pair
    records[("weak_axis",)] = {"input": PROBE.weak_axis_scene()}
    for band in ("easy", "medium", "hard"):
        for seed in (0, 2):
            for si in range(6 + gen.EXAMPLES_NEEDED):
                records[(band, seed, si)] = {"input": gen.generate(seed, si, difficulty=band)}
    keys = list(records)
    for first in range(0, len(keys), 64):
        subset = keys[first:first + 64]
        result = Catalog(ROOT).apply(TASK_ID, [records[key]["input"] for key in subset], timeout=120)
        assert result["generator_sha256"] == digest
        assert result["rule_hash_matches_catalog"]
        for key, row in zip(subset, result["results"], strict=True):
            assert row["error"] is None, (key, row["error"])
            if key[0] == "canonical":
                assert records[key]["output"] == row["output"]
            records[key]["output"] = row["output"]
    return records


@pytest.mark.parametrize("hook_name", ["self_check", "strict_canonical_like"])
@pytest.mark.parametrize("case_name", sorted(PROBE.outside_marker_cases()))
def test_outside_yellow_mark_returns_reason_instead_of_indexing_unbounded_mirror(selected, hook_name, case_name):
    gen, _source, _digest = selected
    grid = PROBE.outside_marker_cases()[case_name]
    before = copy.deepcopy(grid)
    reasons = getattr(gen, hook_name)(grid)
    assert isinstance(reasons, list)
    assert any("outside" in reason for reason in reasons)
    assert grid == before


def test_offset_frame_is_not_itself_a_counterexample_to_the_whole_grid_rival(selected, labeled):
    gen, _source, _digest = selected
    pair = labeled[("weak_axis",)]
    assert gen.self_check(pair["input"]) == []
    assert PROBE.whole_grid_empty(pair["input"]) == pair["output"]
    assert gen.SEMANTIC_WITNESSES["frame_local_not_global_axis"](pair["input"]) is False


def test_declared_canonical_shortcuts_fit_every_labeled_pair(selected, labeled):
    gen, _source, _digest = selected
    shortcuts = getattr(gen, "CANONICAL_SHORTCUTS", {})
    assert {"overwrite_nonaxis_yellow", "recolor_axis_yellow", "whole_grid_empty"} <= shortcuts.keys()
    for name, rival in shortcuts.items():
        for key, pair in labeled.items():
            if key[0] == "canonical":
                assert rival(copy.deepcopy(pair["input"])) == pair["output"], (name, key)


def test_every_firing_refutation_witness_disagrees_with_a_named_rival(selected, labeled):
    gen, _source, _digest = selected
    claims = getattr(gen, "WITNESS_RIVALS", {})
    rivals = getattr(gen, "SEMANTIC_RIVALS", {})
    assert set(gen.SEMANTIC_WITNESSES) <= claims.keys()
    for witness_name, predicate in gen.SEMANTIC_WITNESSES.items():
        names = claims[witness_name]
        names = [names] if isinstance(names, str) else list(names)
        assert names and set(names) <= rivals.keys()
        for key, pair in labeled.items():
            if predicate(copy.deepcopy(pair["input"])):
                assert any(rivals[name](copy.deepcopy(pair["input"])) != pair["output"] for name in names), (witness_name, key)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("seed", [0, 2])
def test_every_query_rotation_defeats_live_and_independent_rivals(selected, labeled, seed, band):
    gen, _source, _digest = selected
    rivals = {**PROBE.diagnostic_rivals(), **PROBE.declared_rivals(gen)}
    predictions = {
        (name, si): rival(copy.deepcopy(labeled[(band, seed, si)]["input"]))
        for name, rival in rivals.items()
        for si in range(6 + gen.EXAMPLES_NEEDED)
    }
    for start in range(6):
        indices = list(range(start, start + gen.EXAMPLES_NEEDED + 1))
        for query_index in indices:
            query = labeled[(band, seed, query_index)]
            demo_indices = [si for si in indices if si != query_index]
            demos = [labeled[(band, seed, si)] for si in demo_indices]
            assert gen.lesson_identifiable(copy.deepcopy(demos), copy.deepcopy(query)) == [], (band, seed, start, query_index)
            for name in rivals:
                fits_demos = all(predictions[name, si] == labeled[(band, seed, si)]["output"] for si in demo_indices)
                assert not fits_demos or predictions[name, query_index] == query["output"], (band, seed, start, query_index, name)
