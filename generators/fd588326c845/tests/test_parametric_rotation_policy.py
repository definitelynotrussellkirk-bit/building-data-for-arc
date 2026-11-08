"""Native rotation-policy prototype: setting-neutral inputs and Racket labels."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import random

import pytest


HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]


def adapter():
    source = HOME / "workspace/parametric/adapter.py"
    spec = importlib.util.spec_from_file_location(
        "_fd588326c845_rotation_policy_adapter_test", source
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    with RacketBridge(timeout=10) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True

        def apply(program, grid):
            bridge.define_grid("rotation-policy-test-grid", grid)
            return bridge.eval_text(
                "(" + wrap_rule(program) + " rotation-policy-test-grid)"
            )

        yield apply


def all_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_exact_canonical_authority():
    programs = {
        row["program_solution"]
        for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
        if (row := json.loads(line))["task_id"] == "fd588326c845"
    }
    module = adapter()
    assert programs == {module.program({"rotation_policy": "clockwise"})}
    assert module.program({"rotation_policy": "anchor_directed"}) not in programs


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_inputs_are_setting_neutral_deterministic_distinct_and_rng_local(demos):
    module = adapter()
    before = random.getstate()
    clockwise = module.generate(
        17, {"rotation_policy": "clockwise"}, demos, 4
    )
    anchor = module.generate(
        17, {"rotation_policy": "anchor_directed"}, demos, 4
    )
    assert all_inputs(clockwise) == all_inputs(anchor)
    assert clockwise == module.generate(
        17, {"rotation_policy": "clockwise"}, demos, 4
    )
    assert random.getstate() == before
    assert len(clockwise["train"]) == demos
    assert len(clockwise["test"]) == 4
    visible = [json.dumps(grid, separators=(",", ":")) for grid in all_inputs(clockwise)]
    assert len(visible) == len(set(visible)) == demos + 4


def test_two_demos_teach_the_conditional_policy_and_four_queries_cover_both_branches():
    module = adapter()
    fixed = module.generate(91, {"rotation_policy": "clockwise"}, 2, 4)
    conditional = module.generate(
        91, {"rotation_policy": "anchor_directed"}, 2, 4
    )
    demo_sides = [module.observe(pair["input"])["anchor_side"] for pair in fixed["train"]]
    query_sides = [module.observe(pair["input"])["anchor_side"] for pair in fixed["test"]]
    assert demo_sides == ["bottom", "top"]
    assert query_sides == ["bottom", "top", "bottom", "top"]
    assert fixed["train"][0]["output"] != conditional["train"][0]["output"]
    assert fixed["train"][1]["output"] == conditional["train"][1]["output"]
    assert [module.direction(pair["input"], "anchor_directed") for pair in fixed["train"]] == [
        "counterclockwise",
        "clockwise",
    ]
    for policy, episode in [
        ("clockwise", fixed),
        ("anchor_directed", conditional),
    ]:
        for pair in episode["train"] + episode["test"]:
            assert module.transform(pair["input"], policy) == pair["output"]


def test_last_query_is_substantive_30x30_and_spans_all_boundaries():
    module = adapter()
    episode = module.generate(7, {"rotation_policy": "anchor_directed"}, 3, 4)
    grid = episode["test"][-1]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    occupied = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    assert {min(row for row, _ in occupied), max(row for row, _ in occupied)} == {0, 29}
    assert {min(col for _, col in occupied), max(col for _, col in occupied)} == {0, 29}
    observed = module.observe(grid)
    assert observed["key_size"] == 4
    assert (observed["scale_h"], observed["scale_w"]) == (5, 5)
    assert observed["occupancy_180_symmetric"] is True


@pytest.mark.parametrize("policy", ["clockwise", "anchor_directed"])
def test_demonstrations_alone_eliminate_declared_shortcuts(policy):
    module = adapter()
    episode = module.generate(123, {"rotation_policy": policy}, 2, 4)
    certificate = module.certificate(
        episode["train"], [pair["input"] for pair in episode["test"]]
    )
    assert certificate["survivors"] == [policy]
    assert certificate["demos"] == 2
    assert certificate["queries"] == 4
    assert certificate["anchor_sides"] == ["bottom", "top"]
    assert len(certificate["predicted_query_sha256"]) == 4
    assert "anchor_inverted" in certificate["declared_hypotheses"]
    assert "half_turn" in certificate["declared_hypotheses"]


@pytest.mark.parametrize("policy", ["clockwise", "anchor_directed"])
def test_generated_labels_match_protected_racket(policy, racket):
    module = adapter()
    episode = module.generate(5, {"rotation_policy": policy}, 2, 4)
    program = module.program({"rotation_policy": policy})
    for pair in episode["train"] + episode["test"]:
        assert racket(program, pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    "seed,settings,demos,queries",
    [
        (True, {"rotation_policy": "clockwise"}, 2, 4),
        (0, {"rotation_policy": "wrong"}, 2, 4),
        (0, {"rotation_policy": "clockwise", "extra": 1}, 2, 4),
        (0, {"rotation_policy": "clockwise"}, 1, 4),
        (0, {"rotation_policy": "clockwise"}, 7, 4),
        (0, {"rotation_policy": "clockwise"}, 2, 3),
        (0, {"rotation_policy": "clockwise"}, 2, 5),
        (0, {"rotation_policy": "clockwise"}, 2, True),
    ],
)
def test_invalid_requests_fail_explicitly(seed, settings, demos, queries):
    with pytest.raises(ValueError):
        adapter().generate(seed, settings, demos, queries)


def test_observer_rejects_boolean_cells_and_broken_occupancy_symmetry():
    module = adapter()
    grid = module.generate(13, {"rotation_policy": "clockwise"}, 2, 4)["train"][0]["input"]
    boolean = [row[:] for row in grid]
    boolean[0][0] = False
    with pytest.raises(ValueError):
        module.observe(boolean)

    observed = module.observe(grid)
    key_r1, key_c1, key_r2, key_c2 = observed["key_box"]
    broken = [row[:] for row in grid]
    for row in range(key_r1, key_r2 + 1):
        for col in range(key_c1, key_c2 + 1):
            opposite = (key_r1 + key_r2 - row, key_c1 + key_c2 - col)
            if broken[row][col] != 0 and broken[opposite[0]][opposite[1]] != 0:
                broken[row][col] = 0
                with pytest.raises(ValueError):
                    module.observe(broken)
                return
    raise AssertionError("expected an occupied symmetric pair")
