"""Contract and teaching tests for the row-fill/bridge parametric family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAM = HOME / "workspace" / "parametric"


def _load(name="prototype.py"):
    path = PARAM / name
    spec = importlib.util.spec_from_file_location("row_parametric", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_missing_implementation_red_gate():
    assert (PARAM / "prototype.py").is_file(), "parametric prototype has not been implemented"


def test_default_program_is_exact_canonical_and_alternate_is_distinct():
    mod = _load()
    canonical = (
        "(rule!\n"
        "  (grid-from-fn (rows g) (cols g)\n"
        "    (lambda (r c)\n"
        "      (let ((colors (filter (lambda (v) (not (= v 0))) (row-at g r))))\n"
        "        (if (empty? colors) 0 (first colors))))))"
    )
    assert mod.program({"row_policy": "first_fill"}) == canonical
    assert mod.program({"row_policy": "bridge_equal"}) != canonical


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_counts_outputs_and_setting_neutral_prefixes(demos, queries):
    mod = _load()
    a = mod.generate(17, {"row_policy": "first_fill"}, demos=demos, queries=queries)
    b = mod.generate(17, {"row_policy": "bridge_equal"}, demos=demos, queries=queries)
    assert len(a["train"]) == len(b["train"]) == demos
    assert len(a["test"]) == len(b["test"]) == queries
    assert [p["input"] for p in a["train"] + a["test"]] == [p["input"] for p in b["train"] + b["test"]]
    assert len({str(p["input"]) for p in a["train"] + a["test"]}) == demos + queries
    for settings, episode in [({"row_policy": "first_fill"}, a), ({"row_policy": "bridge_equal"}, b)]:
        assert episode["program_solution"] == mod.program(settings)
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == mod.transform(pair["input"], settings)
    assert all(x["input"] == y["input"] for x, y in zip(
        mod.generate(17, {"row_policy": "first_fill"}, 2, 1)["train"], a["train"][:2]
    ))


def test_four_query_bank_contains_substantive_30x30_case():
    mod = _load()
    episode = mod.generate(97, {"row_policy": "bridge_equal"}, demos=2, queries=4)
    shapes = {(len(p["input"]), len(p["input"][0])) for p in episode["test"]}
    assert (30, 30) in shapes
    large = next(p["input"] for p in episode["test"] if len(p["input"]) == 30 and len(p["input"][0]) == 30)
    assert sum(value != 0 for row in large for value in row) >= 30
    assert sum(any(value != 0 for value in row) for row in large) >= 10


def test_bridge_depends_on_first_fill_intermediate_and_wrong_intermediate_changes_output():
    mod = _load()
    grid = [
        [2, 0, 0, 0, 7, 0],
        [0, 0, 0, 0, 0, 0],
        [2, 0, 0, 0, 3, 0],
        [0, 0, 0, 0, 0, 0],
        [4, 0, 0, 0, 2, 0],
    ]
    canonical = mod.transform(grid, {"row_policy": "first_fill"})
    bridged = mod.transform(grid, {"row_policy": "bridge_equal"})
    wrong = mod.transform_rightmost_bridge(grid)
    assert canonical[1] == [0] * 6
    assert bridged[1] == [2] * 6
    assert bridged[3] == [0] * 6
    assert wrong != bridged


def test_two_demonstrations_identify_setting_and_refute_declared_rivals():
    mod = _load()
    for seed in (0, 17, 97):
        for policy in mod.POLICIES:
            episode = mod.generate(seed, {"row_policy": policy}, demos=2, queries=4)
            report = mod.teaching_check(episode, {"row_policy": policy})
            assert report["survivors"] == [{"row_policy": policy}]
            assert report["surviving_rivals"] == []


@pytest.mark.parametrize(
    "args",
    [
        (-1, {"row_policy": "first_fill"}, 2, 4),
        (0, {"row_policy": "bad"}, 2, 4),
        (0, {"extra": "first_fill"}, 2, 4),
        (0, {"row_policy": "first_fill"}, 1, 4),
        (0, {"row_policy": "first_fill"}, 7, 4),
        (0, {"row_policy": "first_fill"}, 2, 0),
        (0, {"row_policy": "first_fill"}, 2, 5),
    ],
)
def test_rejects_invalid_requests(args):
    mod = _load()
    with pytest.raises(ValueError):
        mod.generate(*args)


def test_reusable_audit_tool_covers_boundaries_and_rivals_without_racket():
    path = PARAM / "audit.py"
    spec = importlib.util.spec_from_file_location("row_audit", path)
    assert spec and spec.loader
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    report = audit.build_report(seeds=(0, 17), use_racket=False)
    assert report["status"] == "PASS"
    assert report["requests"] == 2 * 2 * 2 * 2
    assert report["surviving_rivals"] == []
