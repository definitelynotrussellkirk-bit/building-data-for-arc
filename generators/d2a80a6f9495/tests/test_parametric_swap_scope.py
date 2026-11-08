from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root

TASK_ID = "d2a80a6f9495"
TASK_DIR = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PROTOTYPE_PATH = TASK_DIR / "workspace" / "parametric" / "prototype.py"
ADAPTER_PATH = TASK_DIR / "workspace" / "parametric" / "adapter.py"
PROMOTION_PATH = TASK_DIR / "workspace" / "parametric" / "promotion.json"
AUDIT_PATH = TASK_DIR / "workspace" / "parametric" / "audit.py"
SCOPES = ("all_two_color", "repeated_pair")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_source() -> str:
    rows = [
        json.loads(line)
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    matches = [row for row in rows if row.get("task_id") == TASK_ID]
    assert len(matches) == 1
    return matches[0]["program_solution"]


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _fixture():
    grid = [[0 for _ in range(16)] for _ in range(10)]
    # Two separated objects with pair (1,2).
    for r, c, v in ((0, 0, 1), (0, 1, 2), (1, 0, 2), (1, 1, 1)):
        grid[r][c] = v
    for r, c, v in ((0, 5, 2), (0, 6, 1), (1, 5, 1), (1, 6, 2)):
        grid[r][c] = v
    # One unique two-color pair (3,4).
    for r, c, v in ((0, 10, 3), (0, 11, 4), (1, 10, 3), (1, 11, 4)):
        grid[r][c] = v
    # One-color and three-color negative controls.
    for r in (5, 6):
        for c in (0, 1):
            grid[r][c] = 5
    for r, c, v in ((5, 5, 6), (5, 6, 7), (6, 5, 8), (6, 6, 6)):
        grid[r][c] = v
    return grid


def test_prototype_exports_exact_default_and_distinct_alternate_program():
    prototype = _load(PROTOTYPE_PATH, "swap_scope_prototype")

    for name in (
        "canonical_program",
        "program_for",
        "apply_scope",
        "object_facts",
        "episode_inputs",
        "generate_episode",
        "public_turn",
    ):
        assert callable(getattr(prototype, name))
    assert prototype.SCOPES == SCOPES
    assert prototype.DEFAULT_SCOPE == "all_two_color"
    assert prototype.canonical_program() == _canonical_source()
    assert prototype.program_for("all_two_color") == _canonical_source()
    assert prototype.program_for("repeated_pair") != _canonical_source()
    assert prototype.program_for("repeated_pair").startswith("(rule!")


def test_repeated_pair_scope_consumes_global_pair_multiplicities():
    prototype = _load(PROTOTYPE_PATH, "swap_scope_fixture")
    grid = _fixture()
    facts = prototype.object_facts(grid)

    assert facts["pair_counts"] == {"1,2": 2, "3,4": 1}
    assert facts["repeated_pairs"] == [[1, 2]]
    all_swapped = prototype.apply_scope(grid, "all_two_color")
    repeated = prototype.apply_scope(grid, "repeated_pair")
    assert all_swapped != repeated

    # Repeated pair objects swap under both settings.
    assert all_swapped[0][0] == repeated[0][0] == 2
    assert all_swapped[0][1] == repeated[0][1] == 1
    # Unique pair swaps only in the canonical setting.
    assert all_swapped[0][10:12] == [4, 3]
    assert repeated[0][10:12] == [3, 4]
    # Negative controls stay unchanged.
    assert all_swapped[5][0:2] == repeated[5][0:2] == [5, 5]
    assert all_swapped[5][5:7] == repeated[5][5:7] == [6, 7]


def test_counts_are_independent_prefix_stable_and_queries_reach_30x30():
    prototype = _load(PROTOTYPE_PATH, "swap_scope_counts")
    minimum = prototype.episode_inputs(7, demos=2, queries=1)
    maximum = prototype.episode_inputs(7, demos=6, queries=4)

    assert len(minimum) == 3
    assert len(maximum) == 10
    assert minimum == maximum[:2] + [maximum[6]]
    assert len({_freeze(grid) for grid in maximum}) == 10
    assert [(len(g), len(g[0])) for g in maximum[6:]] == [
        (14, 16),
        (20, 22),
        (26, 28),
        (30, 30),
    ]
    large = maximum[-1]
    assert sum(cell != 0 for row in large for cell in row) >= 120


def test_minimum_demos_teach_repeated_pair_not_most_frequent_or_shape_identity():
    prototype = _load(PROTOTYPE_PATH, "swap_scope_teaching")
    first, second = prototype.episode_inputs(11, demos=2, queries=1)[:2]

    for grid in (first, second):
        facts = prototype.object_facts(grid)
        counts = sorted(facts["pair_counts"].values(), reverse=True)
        assert len(counts) >= 2 and all(count >= 2 for count in counts[:2])
        assert 1 in counts
        assert len(facts["two_color_objects"]) >= 5
        assert facts["negative_object_count"] >= 2
        assert prototype.apply_scope(grid, "all_two_color") != prototype.apply_scope(
            grid, "repeated_pair"
        )


def test_two_demos_identify_each_scope_and_inputs_are_setting_matched():
    prototype = _load(PROTOTYPE_PATH, "swap_scope_identification")
    episodes = {
        scope: prototype.generate_episode(29, scope, demos=2, queries=4)
        for scope in SCOPES
    }
    assert [p["input"] for p in episodes[SCOPES[0]]["train"] + episodes[SCOPES[0]]["test"]] == [
        p["input"] for p in episodes[SCOPES[1]]["train"] + episodes[SCOPES[1]]["test"]
    ]

    for selected, episode in episodes.items():
        assert set(episode) == {"train", "test", "program_solution"}
        survivors = [
            candidate
            for candidate in SCOPES
            if all(
                prototype.apply_scope(pair["input"], candidate) == pair["output"]
                for pair in episode["train"]
            )
        ]
        assert survivors == [selected]
        assert all(
            pair["output"] == prototype.apply_scope(pair["input"], selected)
            for pair in episode["train"] + episode["test"]
        )


def test_seed_scope_and_count_validation_is_strict():
    prototype = _load(PROTOTYPE_PATH, "swap_scope_validation")

    for bad_seed in (True, -1, 2**63, 1.0, "17"):
        with pytest.raises((TypeError, ValueError)):
            prototype.episode_inputs(bad_seed, demos=2, queries=4)
    for bad_demos in (True, 1, 7, 2.0, "2"):
        with pytest.raises((TypeError, ValueError)):
            prototype.episode_inputs(0, demos=bad_demos, queries=4)
    for bad_queries in (False, 0, 5, 4.0, "4"):
        with pytest.raises((TypeError, ValueError)):
            prototype.episode_inputs(0, demos=2, queries=bad_queries)
    for bad_scope in (None, True, "", "largest_pair", 0):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(0, bad_scope, demos=2, queries=4)


def test_protected_racket_matches_python_on_demo_and_30x30_query():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    prototype = _load(PROTOTYPE_PATH, "swap_scope_racket")
    inputs = prototype.episode_inputs(41, demos=2, queries=4)
    witnesses = (inputs[0], inputs[-1])
    assert [(len(g), len(g[0])) for g in witnesses] == [(12, 14), (30, 30)]

    with RacketBridge(timeout=30, max_calls_before_restart=16) as bridge:
        for index, grid in enumerate(witnesses):
            name = f"g{index}"
            bridge.define_grid(name, grid)
            for scope in SCOPES:
                actual = bridge.eval_text(f"({wrap_rule(prototype.program_for(scope))} {name})")
                assert actual == prototype.apply_scope(grid, scope)
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True


def test_native_adapter_and_contract_have_exact_bounded_surface():
    prototype = _load(PROTOTYPE_PATH, "swap_scope_contract_prototype")
    adapter = _load(ADAPTER_PATH, "swap_scope_contract_adapter")
    contract = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))

    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/d2a80a6f9495/workspace/parametric/adapter.py",
        "parameters": {"swap_scope": list(SCOPES)},
        "default": {"swap_scope": "all_two_color"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 3,
        "resources": ["generators/d2a80a6f9495/workspace/parametric/canonical.rkt"],
    }
    for scope in SCOPES:
        settings = {"swap_scope": scope}
        assert adapter.program(settings) == prototype.program_for(scope)
        assert adapter.generate(53, settings, 2, 4) == prototype.generate_episode(
            53, scope, 2, 4
        )


def test_adapter_rejects_wrong_setting_shapes_and_values():
    adapter = _load(ADAPTER_PATH, "swap_scope_adapter_validation")

    for bad in (None, [], {}, {"swap_scope": "all_two_color", "extra": 1}, {"scope": "all_two_color"}):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, bad, 2, 4)
    for bad_value in (None, True, "", "largest_pair", 0):
        with pytest.raises((TypeError, ValueError)):
            adapter.program({"swap_scope": bad_value})


def test_sequential_public_turn_reveals_one_query_without_private_hints():
    prototype = _load(PROTOTYPE_PATH, "swap_scope_public")
    full = prototype.generate_episode(83, "repeated_pair", 3, 4)
    single = prototype.generate_episode(83, "repeated_pair", 3, 1)

    first = prototype.public_turn(full, 0)
    assert first == prototype.public_turn(single, 0)
    assert set(first) == {"train", "test"}
    assert len(first["train"]) == 3
    assert first["test"] == [{"input": full["test"][0]["input"]}]
    assert all(set(pair) == {"input", "output"} for pair in first["train"])
    text = json.dumps(first, sort_keys=True)
    for forbidden in ("repeated_pair", "swap_scope", "program_solution", "query_count", "remaining"):
        assert forbidden not in text
    for index in range(4):
        assert prototype.public_turn(full, index)["test"] == [
            {"input": full["test"][index]["input"]}
        ]


def test_finite_rival_audit_has_no_harmful_survivor():
    audit = _load(AUDIT_PATH, "swap_scope_audit")
    report = audit.run_audit(seeds=(0, 17), demo_counts=(2, 3, 6), queries=4)

    assert report["schema"] == "arcpuzzles-parametric-swap-scope-audit-v1"
    assert report["episodes"] == 12
    assert report["queries_checked"] == 48
    assert report["harmful_survivors"] == []
    assert report["input_failures"] == []
    assert set(report["settings_checked"]) == set(SCOPES)
    assert len(report["rival_names"]) >= 9
