"""Focused tests for the once/twice framed-transform parametric family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_path, find_root


TASK_ID = "85782e8a5dc9"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)


def adapter():
    source = HOME / "workspace/parametric/adapter.py"
    spec = importlib.util.spec_from_file_location("_framed_transfer_count_adapter_test", source)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["task_id"] == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical program missing")


def map_square(grid: list[list[int]], name: str) -> list[list[int]]:
    size = len(grid)
    output = [[0] * size for _ in range(size)]
    for row in range(size):
        for col in range(size):
            if name == "identity":
                target = row, col
            elif name == "rot90":
                target = col, size - 1 - row
            elif name == "rot180":
                target = size - 1 - row, size - 1 - col
            elif name == "rot270":
                target = size - 1 - col, row
            elif name == "transpose":
                target = col, row
            elif name == "flip_lr":
                target = row, size - 1 - col
            elif name == "flip_ud":
                target = size - 1 - row, col
            elif name == "anti_transpose":
                target = size - 1 - col, size - 1 - row
            else:
                raise AssertionError(name)
            output[target[0]][target[1]] = grid[row][col]
    return output


def render(a: list[list[int]], b: list[list[int]], c: list[list[int]]) -> list[list[int]]:
    size = len(a) + 2
    width = 3 * size + 2
    value = [[0] * width for _ in range(size)]
    for index, pattern in enumerate((a, b, c)):
        start = index * (size + 1)
        stop = start + size - 1
        for col in range(start, stop + 1):
            value[0][col] = value[-1][col] = 5
        for row in range(size):
            value[row][start] = value[row][stop] = 5
        for row, cells in enumerate(pattern, start=1):
            value[row][start + 1 : stop] = cells
    return value


def literal_rot90_scene() -> list[list[int]]:
    a = [
        [1, 2, 0, 0],
        [3, 0, 0, 0],
        [0, 0, 4, 0],
        [0, 0, 0, 0],
    ]
    c = [
        [6, 0, 0, 0],
        [6, 7, 0, 0],
        [0, 7, 8, 0],
        [0, 0, 8, 9],
    ]
    return render(a, map_square(a, "rot90"), c)


@pytest.fixture(scope="module")
def racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    with RacketBridge(timeout=10) as bridge:
        assert bridge.runtime_identity["protected"] is True

        def apply(program: str, value: list[list[int]]) -> list[list[int]]:
            bridge.define_grid("framed-transfer-count-test-grid", value)
            return bridge.eval_text(f"({wrap_rule(program)} framed-transfer-count-test-grid)")

        yield apply


def episode_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_setting_is_exact_canonical_program():
    assert adapter().program({"applications": "once"}) == canonical_program()


def test_each_declared_program_is_one_complete_rule_expression():
    from arc_repl.parser import Symbol, parse_all

    module = adapter()
    for applications in module.APPLICATIONS:
        forms = parse_all(module.program({"applications": applications}))
        assert len(forms) == 1
        assert isinstance(forms[0], list)
        assert forms[0][0] == Symbol("rule!")


def test_literal_scene_infers_transform_and_applies_it_once_or_twice(racket):
    module = adapter()
    value = literal_rot90_scene()
    observed = module.observe(value)
    assert observed["transform"] == "rot90"
    c = observed["c"]
    assert module.transform(value, "once") == map_square(c, "rot90")
    assert module.transform(value, "twice") == map_square(c, "rot180")
    assert racket(module.program({"applications": "once"}), value) == module.transform(value, "once")
    assert racket(module.program({"applications": "twice"}), value) == module.transform(value, "twice")


def test_wrong_inferred_transform_changes_twice_output():
    module = adapter()
    value = literal_rot90_scene()
    correct = module.transform(value, "twice")
    wrong = module.predict(value, "fixed_rot180_twice")
    assert correct != wrong
    assert module.observe(value)["transform"] == "rot90"


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_generated_inputs_are_matched_distinct_deterministic_and_include_30x30(demos):
    module = adapter()
    once = module.generate(17, {"applications": "once"}, demos, 4)
    twice = module.generate(17, {"applications": "twice"}, demos, 4)
    assert episode_inputs(once) == episode_inputs(twice)
    assert once == module.generate(17, {"applications": "once"}, demos, 4)
    assert len(once["train"]) == demos
    assert len(once["test"]) == 4
    assert len({json.dumps(value, separators=(",", ":")) for value in episode_inputs(once)}) == demos + 4
    stress = once["test"][-1]
    assert (len(stress["input"]), len(stress["input"][0])) == (30, 30)
    assert (len(stress["output"]), len(stress["output"][0])) == (28, 7)
    assert sum(cell != 0 for row in stress["input"] for cell in row) > 220
    assert sum(cell != 0 for row in stress["output"] for cell in row) > 60
    assert all(pair["output"] == module.transform(pair["input"], "once") for pair in once["train"] + once["test"])
    assert all(pair["output"] == module.transform(pair["input"], "twice") for pair in twice["train"] + twice["test"])


def test_query_prefixes_are_stable_across_query_and_demo_counts():
    module = adapter()
    full = module.generate(31, {"applications": "once"}, 6, 4)
    for demos in (2, 3, 6):
        for queries in (1, 2, 3, 4):
            episode = module.generate(31, {"applications": "once"}, demos, queries)
            assert [pair["input"] for pair in episode["test"]] == [
                pair["input"] for pair in full["test"][:queries]
            ]


def test_fresh_seeds_vary_inputs_without_touching_global_rng():
    module = adapter()
    random.seed(9157)
    before = random.getstate()
    first = module.generate(0, {"applications": "once"}, 3, 4)
    second = module.generate(17, {"applications": "once"}, 3, 4)
    assert random.getstate() == before
    assert episode_inputs(first) != episode_inputs(second)


@pytest.mark.parametrize("applications", ["once", "twice"])
def test_two_demos_identify_setting_against_declared_rivals(applications):
    module = adapter()
    episode = module.generate(17, {"applications": applications}, 2, 4)
    certificate = module.certificate(
        episode["train"], [pair["input"] for pair in episode["test"]]
    )
    assert certificate["survivors"] == [applications]
    assert certificate["demos"] == 2
    assert certificate["queries"] == 4
    witness = certificate["causal_witness"]
    assert witness["inferred_transform"] == "rot90"
    assert witness["correct_output_sha256"] != witness["wrong_intermediate_output_sha256"]


@pytest.mark.parametrize("applications", ["once", "twice"])
def test_generated_labels_match_protected_racket(racket, applications):
    module = adapter()
    episode = module.generate(23, {"applications": applications}, 3, 4)
    program = module.program({"applications": applications})
    for pair in episode["train"] + episode["test"]:
        assert racket(program, pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    "seed,settings,demos,queries",
    [
        (True, {"applications": "once"}, 3, 4),
        (0, {"applications": "wrong"}, 3, 4),
        (0, {"applications": "once", "unknown": 1}, 3, 4),
        (0, {"applications": "once"}, 1, 4),
        (0, {"applications": "once"}, 7, 4),
        (0, {"applications": "once"}, 3, 0),
        (0, {"applications": "once"}, 3, 5),
        (0, {"applications": "once"}, 3, True),
    ],
)
def test_bad_generation_requests_fail_explicitly(seed, settings, demos, queries):
    with pytest.raises(ValueError):
        adapter().generate(seed, settings, demos, queries)


def test_boolean_grid_cells_are_rejected():
    value = literal_rot90_scene()
    value[0][0] = False
    with pytest.raises(ValueError):
        adapter().transform(value, "once")


def test_reusable_self_audit_covers_minimum_and_maximum_lessons():
    source = HOME / "workspace/parametric/self_audit.py"
    spec = importlib.util.spec_from_file_location("_framed_transfer_count_audit_test", source)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    report = module.run_audit(seeds=2)
    assert report["status"] == "passed"
    assert report["episodes"] == 12
    assert report["demo_counts"] == [2, 3, 6]
    assert report["settings"] == ["once", "twice"]
    assert report["stress_30x30"] == 12
    assert report["failures"] == []
