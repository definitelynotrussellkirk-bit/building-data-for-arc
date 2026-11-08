"""Native panel-operation contract, exercised through the protected Racket runtime.

Hand-labeled fixtures distinguish right-panel four-neighbor components from
left-panel fill, diagonal fill, overlap-only output, and one-step expansion.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from arc_repl.racket_bridge import RacketBridge
from arcpuzzles.catalog import Catalog
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_pairs, find_root


TASK = "79353e95283d"
ROOT = find_root(__file__)
NATIVE = Path(__file__).resolve().parents[1] / "workspace/parametric/native.py"
OPERATIONS = ("and", "or", "xor", "overlap_components")
TRUTH_TABLE = [
    [0, 0, 1, 5, 0, 1, 0],
    [1, 0, 0, 5, 1, 0, 0],
]


def _load_native():
    assert NATIVE.is_file(), "native.py must implement the admitted panel-operation adapter"
    spec = importlib.util.spec_from_file_location("task_79353e95283d_native_tests", NATIVE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def native():
    return _load_native()


@pytest.fixture(scope="module")
def racket():
    with RacketBridge(timeout=20, max_calls_before_restart=128) as bridge:
        yield bridge


@pytest.fixture(scope="module")
def episodes(native):
    return {
        operation: native.generate(217, {"operation": operation}, demos=2, queries=4)
        for operation in OPERATIONS
    }


def _execute(racket, program, grids):
    # Only serialize test data here; the protected Racket program computes labels.
    data = json.dumps(grids).translate(str.maketrans({"[": "(", "]": ")", ",": " "}))
    return racket.eval_text("(map " + wrap_rule(program) + " '" + data + ")")


def _assert_input_grammar(grid):
    assert type(grid) is list and 1 <= len(grid) <= 30
    assert all(type(row) is list and len(row) == 7 for row in grid)
    separator = grid[0][3]
    assert type(separator) is int and 2 <= separator <= 9
    for row in grid:
        assert row[3] == separator and type(row[3]) is int
        assert all(type(cell) is int and cell in (0, 1) for cell in row[:3] + row[4:])


def test_canonical_and_program_remains_exact_selected_authority():
    # Keep this first so an unimplemented adapter produces a direct RED assertion.
    module = _load_native()
    selected = Catalog(ROOT).get(TASK)["variants"][0]["program_solution"]
    assert module.program({"operation": "and"}) == selected


@pytest.mark.parametrize("operation,expected", [
    ("and", [[0, 0, 0], [2, 0, 0]]),
    ("or", [[0, 2, 2], [2, 0, 0]]),
    ("xor", [[0, 2, 2], [0, 0, 0]]),
])
def test_existing_boolean_truth_tables_are_preserved(native, racket, operation, expected):
    assert _execute(racket, native.program({"operation": operation}), [TRUTH_TABLE]) == [expected]


def test_canonical_and_still_replays_all_usable_labels(native, racket):
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert pairs
    actual = _execute(racket, native.program({"operation": "and"}), [p["input"] for p in pairs])
    assert actual == [p["output"] for p in pairs]


@pytest.mark.parametrize("grid,expected", [
    pytest.param(
        [[1, 1, 0, 7, 1, 1, 1],
         [1, 0, 0, 7, 0, 0, 1],
         [0, 0, 0, 7, 1, 0, 1]],
        [[2, 2, 2], [0, 0, 2], [0, 0, 2]],
        id="right-panel-fill-excludes-left-only-and-unseeded-components",
    ),
    pytest.param(
        [[1, 0, 0, 2, 1, 0, 0],
         [0, 0, 0, 2, 0, 1, 0],
         [0, 0, 0, 2, 0, 0, 1]],
        [[2, 0, 0], [0, 0, 0], [0, 0, 0]],
        id="diagonal-only-neighbors-stay-isolated",
    ),
    pytest.param(
        [[1, 0, 0, 6, 1, 1, 0],
         [0, 0, 0, 6, 0, 1, 0],
         [0, 0, 0, 6, 0, 1, 1],
         [0, 0, 0, 6, 0, 0, 1]],
        [[2, 2, 0], [0, 2, 0], [0, 2, 2], [0, 0, 2]],
        id="bent-path-requires-more-than-one-hop",
    ),
    pytest.param(
        [[1, 0, 1, 9, 0, 1, 0],
         [0, 1, 0, 9, 1, 0, 1]],
        [[0, 0, 0], [0, 0, 0]],
        id="empty-overlap-does-not-seed-any-component",
    ),
    pytest.param(
        [[1, 0, 0, 4, 1, 1, 0],
         [0, 0, 0, 4, 0, 0, 0],
         [0, 0, 1, 4, 0, 1, 1]],
        [[2, 2, 0], [0, 0, 0], [0, 2, 2]],
        id="all-seeded-components-are-filled",
    ),
    pytest.param(
        [[1, 0, 0, 3, 1, 1, 1]],
        [[2, 2, 2]],
        id="single-row-input",
    ),
])
def test_overlap_components_literal_semantics(native, racket, grid, expected):
    before = deepcopy(grid)
    _assert_input_grammar(grid)
    actual = _execute(racket, native.program({"operation": "overlap_components"}), [grid])
    assert actual == [expected]
    assert grid == before


@pytest.mark.parametrize("seed_row", [0, 29], ids=["top-boundary", "bottom-boundary"])
def test_overlap_components_reaches_entire_thirty_row_path(native, racket, seed_row):
    grid = [[0, 0, 0, 8, 0, 1, 0] for _ in range(30)]
    grid[seed_row][1] = 1
    expected = [[0, 2, 0] for _ in range(30)]
    assert _execute(racket, native.program({"operation": "overlap_components"}), [grid]) == [expected]


@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (6, 1), (6, 4)])
def test_sample_count_boundaries_are_independent(native, demos, queries):
    train, test = native.sample_inputs(2**63 - 1, demos, queries)
    assert len(train) == demos and len(test) == queries
    for grid in train + test:
        _assert_input_grammar(grid)
    assert len({json.dumps(grid) for grid in train + test}) == demos + queries


def test_generated_episodes_share_inputs_and_replay_exact_programs(native, racket, episodes):
    train, test = native.sample_inputs(217, 2, 4)
    assert len({json.dumps(grid) for grid in train + test}) == 6
    for operation, episode in episodes.items():
        assert set(episode) == {"train", "test", "program_solution"}
        assert all(set(pair) == {"input", "output"} for pair in episode["train"] + episode["test"])
        assert [pair["input"] for pair in episode["train"]] == train
        assert [pair["input"] for pair in episode["test"]] == test
        assert episode["program_solution"] == native.program({"operation": operation})
        actual = _execute(racket, episode["program_solution"], train + test)
        assert actual == [pair["output"] for pair in episode["train"] + episode["test"]]


def test_demonstrations_alone_identify_each_declared_operation(native, racket, episodes):
    train_inputs = [pair["input"] for pair in episodes["and"]["train"]]
    predictions = {
        operation: _execute(racket, native.program({"operation": operation}), train_inputs)
        for operation in OPERATIONS
    }
    for operation, episode in episodes.items():
        demo_outputs = [pair["output"] for pair in episode["train"]]
        survivors = [name for name, outputs in predictions.items() if outputs == demo_outputs]
        assert survivors == [operation]


def test_mandatory_demonstrations_refute_exactly_one_overlap_rival(native, racket):
    # Removing the multiply seeded lesson must fail this behavior check. Before
    # repair, the rival fit even seed 0's three default demos and failed query 2.
    rival = """(rule! (lambda (g)
      (let* ((right (build-grid (rows g) 3 (r c) (at g r (+ c 4))))
             (selected
               (filter
                 (lambda (obj)
                   (= 1 (length
                     (filter (lambda (cell)
                               (= 1 (at g (first cell) (second cell))))
                             (obj-cells obj)))))
                 (objects right 0)))
             (reached (apply append (map obj-cells selected))))
        (build-grid (rows g) 3 (r c)
          (if (member (list r c) reached) 2 0)))))"""
    train, _ = native.sample_inputs(0, demos=2, queries=4)
    expected = _execute(racket, native.program({"operation": "overlap_components"}), train)
    assert _execute(racket, rival, train) != expected


def test_mandatory_demonstrations_refute_left_growth_for_and(native, racket):
    # A connected left-only mark must distinguish left propagation from AND.
    rival = """(rule! (lambda (g)
      (let* ((left (build-grid (rows g) 3 (r c) (at g r c)))
             (selected (filter
               (lambda (obj)
                 (ormap (lambda (p) (= 1 (at g (first p) (+ 4 (second p)))))
                        (obj-cells obj))) (objects left 0)))
             (reached (apply append (map obj-cells selected))))
        (build-grid (rows g) 3 (r c)
          (if (member (list r c) reached) 2 0)))))"""
    train, _ = native.sample_inputs(0, demos=2, queries=4)
    expected = _execute(racket, native.program({"operation": "and"}), train)
    assert _execute(racket, rival, train) != expected


def test_mandatory_and_demonstrations_refute_three_row_cap(native, racket):
    # Inspect a small deterministic range for all endpoint/reflection choices.
    # Every lesson must visibly teach that AND applies below row index two.
    samples = [native.sample_inputs(seed, 2, 1)[0][1] for seed in range(8)]
    outputs = _execute(racket, native.program({"operation": "and"}), samples)
    assert all(any(cell == 2 for row in output[3:] for cell in row)
               for output in outputs)


def test_query_count_extends_a_fixed_stream_and_default_counts_are_three_four(native):
    short_train, short_test = native.sample_inputs(0, 3, 1)
    long_train, long_test = native.sample_inputs(0, 3, 4)
    assert short_train == long_train
    assert short_test == long_test[:1]
    episode = native.generate(0, {"operation": "overlap_components"})
    assert [pair["input"] for pair in episode["train"]] == long_train
    assert [pair["input"] for pair in episode["test"]] == long_test
    assert len(episode["train"]) == 3 and len(episode["test"]) == 4


def test_generation_is_repeatable_and_returned_grids_are_not_shared(native):
    settings = {"operation": "overlap_components"}
    before = deepcopy(settings)
    episode = native.generate(42, settings, demos=6, queries=1)
    expected = deepcopy(episode)
    assert settings == before
    assert episode == native.generate(42, settings, demos=6, queries=1)
    assert len(episode["train"]) == 6 and len(episode["test"]) == 1
    episode["train"][0]["input"][0][0] = 9
    episode["train"][0]["output"][0][0] = 9
    assert native.generate(42, settings, demos=6, queries=1) == expected
    sampled = native.sample_inputs(42, 6, 1)
    assert sampled == (
        [pair["input"] for pair in expected["train"]],
        [pair["input"] for pair in expected["test"]],
    )


@pytest.mark.parametrize("field,bad", [
    ("demos", 1), ("demos", 7), ("demos", True), ("demos", 2.0), ("demos", "2"),
    ("queries", 0), ("queries", 5), ("queries", True), ("queries", 1.0), ("queries", "1"),
])
def test_counts_reject_out_of_range_and_coercible_nonintegers(native, field, bad):
    counts = {"demos": 3, "queries": 2, field: bad}
    with pytest.raises((TypeError, ValueError)):
        native.sample_inputs(0, **counts)
    with pytest.raises((TypeError, ValueError)):
        native.generate(0, {"operation": "and"}, **counts)


@pytest.mark.parametrize("seed", [-1, 2**63, True, 1.0, "1", None])
def test_seed_requires_exact_integer_in_signed_63_bit_range(native, seed):
    with pytest.raises((TypeError, ValueError)):
        native.sample_inputs(seed, 2, 1)
    with pytest.raises((TypeError, ValueError)):
        native.generate(seed, {"operation": "and"}, demos=2, queries=1)


@pytest.mark.parametrize("settings", [
    None, {}, [("operation", "and")], {"operation": "and", "extra": 0},
    {"operation": "AND"}, {"operation": "nand"}, {"operation": True}, {"operation": 1},
])
def test_settings_require_exact_operation_mapping(native, settings):
    before = deepcopy(settings)
    with pytest.raises((TypeError, ValueError)):
        native.program(settings)
    with pytest.raises((TypeError, ValueError)):
        native.generate(0, settings, demos=2, queries=1)
    assert settings == before
