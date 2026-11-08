"""Separate parametric family: semantic, request, and public-view regressions."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes

HOME = Path(__file__).resolve().parents[1]


def load(name="adapter"):
    path = HOME / "workspace" / "parametric" / f"{name}.py"
    assert path.is_file(), "The native parametric implementation is missing"
    spec = importlib.util.spec_from_file_location("row_crop_test_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_is_exact_canonical_and_variant_uses_selected_header():
    a = load()
    records = [json.loads(line) for line in canonical_path(find_root(__file__)).read_text().splitlines()]
    canonical = next(row for row in records if row["task_id"] == "2ca60ab198d6")
    assert a.program({"selection": "rows"}) == canonical["program_solution"]
    assert a.program({"selection": "rows_then_columns"}) != canonical["program_solution"]
    p = load("prototype")
    grid = [
        [6, 0, 7, 7, 0, 7, 0],
        [7, 7, 0, 4, 7, 0, 7],
        [7, 1, 2, 3, 4, 5, 6],
        [0, 7, 7, 2, 0, 1, 0],
        [7, 6, 5, 4, 3, 2, 1],
        [4, 0, 1, 7, 7, 2, 0],
    ]
    assert p.interpret(grid, "rows_then_columns") == [[1, 4, 6], [6, 3, 1]]
    assert p.interpret(grid, "rows") == [grid[i][1:] for i in (1, 2, 4)]


@pytest.mark.parametrize("demos", [2, 3, 4, 5, 6])
@pytest.mark.parametrize("selection", ["rows", "rows_then_columns"])
def test_counts_distinctness_and_two_demo_teaching(demos, selection):
    a, p = load(), load("prototype")
    for seed in (0, 17):
        episode = a.generate(seed, {"selection": selection}, demos, 4)
        assert len(episode["train"]) == demos and len(episode["test"]) == 4
        pairs = episode["train"] + episode["test"]
        assert len({json.dumps(pair["input"]) for pair in pairs}) == demos + 4
        assert all(p.domain_errors(pair["input"]) == [] for pair in pairs)
        assert p.teaching_check(episode["train"], episode["test"], selection)["query_ambiguities"] == []
        assert episode["program_solution"] == a.program({"selection": selection})
        assert any(len(pair["input"]) == len(pair["input"][0]) == 30 for pair in episode["test"])


def test_inputs_matched_across_settings_and_first_query_independent_of_counts():
    a = load()
    rows = a.generate(31, {"selection": "rows"}, 3, 4)
    nested = a.generate(31, {"selection": "rows_then_columns"}, 3, 4)
    for split in ("train", "test"):
        assert [p["input"] for p in rows[split]] == [p["input"] for p in nested[split]]
    one = a.generate(31, {"selection": "rows_then_columns"}, 3, 1)
    assert one["train"] == nested["train"]
    assert one["test"] == nested["test"][:1]
    fewer_demos = a.generate(31, {"selection": "rows_then_columns"}, 2, 4)
    assert fewer_demos["train"] == nested["train"][:2]
    assert fewer_demos["test"] == nested["test"]
    view = {"train": nested["train"], "test": nested["test"][:1]}
    assert public_challenge_bytes(view) == public_challenge_bytes(one)
    changed = copy.deepcopy(one)
    changed.update(seed=99, settings={"selection": "secret"}, program_solution="secret")
    changed["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(changed) == public_challenge_bytes(one)


def test_determinism_and_no_global_rng_or_shared_mutation():
    a = load()
    random.seed(20261024)
    before = random.getstate()
    first = a.generate(44, {"selection": "rows_then_columns"}, 2, 4)
    second = a.generate(44, {"selection": "rows_then_columns"}, 2, 4)
    assert first == second and random.getstate() == before
    first["train"][0]["input"][0][0] = 9
    assert first != second


@pytest.mark.parametrize("settings", [{}, {"selection": "bad"}, {"selection": True}, {"selection": "rows", "extra": 1}])
def test_bad_settings_rejected(settings):
    a = load()
    with pytest.raises((ValueError, TypeError)):
        a.generate(0, settings, 3, 4)
    with pytest.raises((ValueError, TypeError)):
        a.program(settings)


@pytest.mark.parametrize("seed,demos,queries", [(True, 3, 4), (-1, 3, 4), (2**63, 3, 4), (0, 1, 4), (0, 7, 4), (0, True, 4), (0, 3, 0), (0, 3, 5), (0, 3, 1.0)])
def test_request_bounds_fail_closed(seed, demos, queries):
    with pytest.raises((ValueError, TypeError)):
        load().generate(seed, {"selection": "rows"}, demos, queries)


def test_domain_rejects_malformed_grids_and_missing_nested_cues():
    p = load("prototype")
    for bad in ([], [[True]], [[0], [1, 2]], [[0] * 7 for _ in range(6)]):
        assert p.domain_errors(bad)


def test_two_demos_refute_sorting_output_rows_seed44_regression():
    """Previously ascending sorting fit both demos but changed three queries."""
    a = load()
    for mode in ("rows", "rows_then_columns"):
        episode = a.generate(44, {"selection": mode}, 2, 4)
        for reverse in (False, True):
            fits = all(sorted(pair["output"], key=lambda row: row[0], reverse=reverse)
                       == pair["output"] for pair in episode["train"])
            assert not fits, f"sorting output rows survives both demonstrations: {mode=} {reverse=}"

