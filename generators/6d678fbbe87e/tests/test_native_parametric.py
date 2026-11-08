"""Focused contract for the opt-in completion-route parametric family."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PARAMETRIC = HOME / "workspace/parametric"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    path = PARAMETRIC / "adapter.py"
    assert path.is_file(), "native adapter is missing"
    return _load(path, "_test_6d678fbbe87e_adapter")


def settings(rule: str = "complete_only") -> dict[str, str]:
    return {"finish_rule": rule}


def canonical_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    programs = {
        row["program_solution"]
        for row in rows
        if row.get("task_id") == HOME.name and isinstance(row.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def fingerprint(grid):
    return tuple(tuple(row) for row in grid)


def _interior_segment(a, b):
    (r1, c1), (r2, c2) = a, b
    if r1 == r2:
        lo, hi = sorted((c1, c2))
        return [(r1, c) for c in range(lo + 1, hi)]
    if c1 == c2:
        lo, hi = sorted((r1, r2))
        return [(r, c1) for r in range(lo + 1, hi)]
    return []


def test_native_contract_and_exact_canonical_default(adapter):
    contract = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/6d678fbbe87e/workspace/parametric/adapter.py",
        "parameters": {"finish_rule": ["complete_only", "route_dominant"]},
        "default": settings(),
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": ["generators/6d678fbbe87e/workspace/parametric/canonical.rkt"],
    }
    expected = canonical_program()
    assert (PARAMETRIC / "canonical.rkt").read_text(encoding="utf-8") == expected
    assert adapter.program(settings()) == expected
    assert adapter.program(settings("route_dominant")) != expected


@pytest.mark.parametrize("rule", ["complete_only", "route_dominant"])
def test_programs_are_complete_rule_expressions(adapter, rule):
    from puzzle_generators.rule_wrap import wrap_rule

    wrapped = wrap_rule(adapter.program(settings(rule)))
    assert isinstance(wrapped, str) and wrapped.strip()


@pytest.mark.parametrize(
    "bad",
    [None, {}, {"finish_rule": "other"}, {"finish_rule": True},
     {"finish_rule": 1}, {"finish_rule": "complete_only", "extra": 3}],
)
def test_invalid_settings_are_rejected(adapter, bad):
    with pytest.raises((TypeError, ValueError)):
        adapter.program(bad)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, bad, 3, 4)


@pytest.mark.parametrize("seed", [True, -1, 2**63, 1.0, "0"])
def test_seed_boundary_is_strict(adapter, seed):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, settings(), 3, 4)


@pytest.mark.parametrize(
    "demos,queries",
    [(1, 4), (7, 4), (True, 4), (3.0, 4), (3, 0), (3, 5), (3, True), (3, 4.0)],
)
def test_count_boundaries_are_strict(adapter, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, settings(), demos, queries)


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_counts_are_independent_prefixes_and_inputs_are_matched(adapter, seed):
    short = adapter.generate(seed, settings(), 2, 1)
    long = adapter.generate(seed, settings(), 6, 4)
    alternate = adapter.generate(seed, settings("route_dominant"), 6, 4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    assert len(long["train"]) == 6 and len(long["test"]) == 4
    inputs = [pair["input"] for split in ("train", "test") for pair in long[split]]
    assert len({fingerprint(grid) for grid in inputs}) == 10
    for split in ("train", "test"):
        assert [pair["input"] for pair in long[split]] == [
            pair["input"] for pair in alternate[split]
        ]
    assert all(
        a["output"] != b["output"]
        for a, b in zip(long["train"][:2], alternate["train"][:2])
    )


@pytest.mark.parametrize("seed,split,index", [(0, "train", 0), (17, "train", 1), (17, "test", 3)])
def test_scene_teaches_completion_counts_then_routes_only_the_unique_dominant(adapter, seed, split, index):
    grid = adapter.sample_input(seed, split, index)
    analysis = adapter.completion_analysis(grid)
    assert sorted(analysis["counts"].values()) == [1, 2, 3]
    winner = analysis["dominant_color"]
    assert analysis["counts"][winner] == 3
    targets = analysis["targets_by_color"][winner]
    assert len(targets) == 3
    assert any(a[0] == b[0] for i, a in enumerate(targets) for b in targets[i + 1 :])
    assert any(a[1] == b[1] for i, a in enumerate(targets) for b in targets[i + 1 :])

    # The most common input color is deliberately not the fill-count winner.
    input_counts = {color: sum(cell == color for row in grid for cell in row)
                    for color in analysis["counts"]}
    assert max(input_counts, key=input_counts.get) != winner

    canonical = adapter.transform(grid, settings())
    routed = adapter.transform(grid, settings("route_dominant"))
    assert canonical != routed
    changed = {(r, c) for r, row in enumerate(routed) for c, value in enumerate(row)
               if value != canonical[r][c]}
    assert changed
    assert all(routed[r][c] == winner and canonical[r][c] == 0 for r, c in changed)

    runner = next(color for color, count in analysis["counts"].items() if count == 2)
    runner_targets = analysis["targets_by_color"][runner]
    runner_interior = _interior_segment(*runner_targets)
    assert runner_interior and any(canonical[r][c] == 0 for r, c in runner_interior)
    assert all(routed[r][c] == canonical[r][c] for r, c in runner_interior)


@pytest.mark.parametrize("height,width", [(8, 10), (8, 30), (30, 10), (30, 30)])
def test_minimum_and_maximum_canvases_are_substantive(adapter, height, width):
    grid = adapter.sample_input(17, "test", 3, height=height, width=width)
    assert len(grid) == height and all(len(row) == width for row in grid)
    nonzero = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    assert min(r for r, _ in nonzero) == 0 and max(r for r, _ in nonzero) == height - 1
    assert min(c for _, c in nonzero) == 0 and max(c for _, c in nonzero) == width - 1
    assert {(int(r >= height / 2), int(c >= width / 2)) for r, c in nonzero} == {
        (0, 0), (0, 1), (1, 0), (1, 1)
    }
    if height == width == 30:
        assert len(nonzero) >= 100
    analysis = adapter.completion_analysis(grid)
    assert sorted(analysis["counts"].values()) == [1, 2, 3]
    assert adapter.transform(grid, settings()) != adapter.transform(grid, settings("route_dominant"))


def test_fourth_query_is_exact_30_by_30(adapter):
    episode = adapter.generate(17, settings("route_dominant"), 3, 4)
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)


def test_rng_and_return_values_are_isolated(adapter):
    random.seed(512)
    before = random.getstate()
    first = adapter.generate(31, settings("route_dominant"), 3, 4)
    assert random.getstate() == before
    expected = adapter.generate(31, settings("route_dominant"), 3, 4)
    assert first == expected
    first["train"][0]["input"][0][0] = 9
    first["test"][0]["output"][0][0] = 9
    assert adapter.generate(31, settings("route_dominant"), 3, 4) == expected


def test_public_projection_has_one_query_and_content_only_id(adapter):
    episode = adapter.generate(17, settings("route_dominant"), 3, 4)
    view = {"train": episode["train"], "test": episode["test"][:1]}
    raw = public_challenge_bytes(view)
    public = json.loads(raw)
    assert set(public) == {"train", "test"}
    assert len(public["test"]) == 1 and set(public["test"][0]) == {"input"}
    assert raw == public_challenge_bytes(adapter.generate(17, settings("route_dominant"), 3, 1))
    assert public_challenge_id(view) == hashlib.sha256(raw).hexdigest()
    view["settings"] = {"secret": 812}
    view["program_solution"] = "secret"
    view["test"][0]["output"] = [[0]]
    assert public_challenge_bytes(view) == raw


def test_audit_distinguishes_checked_equivalence_from_query_ambiguity():
    audit = _load(PARAMETRIC / "audit.py", "_test_6d678fbbe87e_audit")
    assert audit.survivor_status([]) == "equivalent_on_checked_pairs"
    assert audit.survivor_status([{"query_index": 0}]) == "survives_demos_disagrees_query"
