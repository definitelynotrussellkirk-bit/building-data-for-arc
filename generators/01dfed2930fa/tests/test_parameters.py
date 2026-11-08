"""Behavioral tests for the proposed room-fill policy family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes


HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = HOME / "workspace/parametric/prototype.py"


def load_prototype():
    assert PROTOTYPE.is_file(), "The assigned runnable parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("room_fill_policy_test_subject", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def p():
    return load_prototype()


@pytest.fixture(scope="module")
def reference(p):
    with p.Reference() as runtime:
        yield runtime


def test_runnable_prototype_exists():
    load_prototype()


def test_default_is_exact_canonical_program(p):
    rows = [json.loads(line) for line in canonical_path(find_root(__file__)).read_text().splitlines()]
    sources = {row["program_solution"] for row in rows if row["task_id"] == "01dfed2930fa"}
    assert sources == {p.program({"fill_policy": "unique_color"})}


def test_hand_derived_unique_and_majority_semantics_have_racket_parity(p, reference):
    grid = [
        [8, 8, 8, 8, 8, 8, 8],
        [8, 2, 0, 8, 4, 0, 8],
        [8, 0, 2, 8, 4, 5, 8],
        [8, 8, 8, 8, 8, 8, 8],
        [8, 6, 0, 8, 1, 3, 8],
        [8, 0, 0, 8, 1, 1, 8],
        [8, 8, 8, 8, 8, 8, 8],
    ]
    unique = [
        [8, 8, 8, 8, 8, 8, 8],
        [8, 2, 2, 8, 4, 0, 8],
        [8, 2, 2, 8, 4, 5, 8],
        [8, 8, 8, 8, 8, 8, 8],
        [8, 6, 6, 8, 1, 3, 8],
        [8, 6, 6, 8, 1, 1, 8],
        [8, 8, 8, 8, 8, 8, 8],
    ]
    majority = [
        [8, 8, 8, 8, 8, 8, 8],
        [8, 2, 2, 8, 4, 4, 8],
        [8, 2, 2, 8, 4, 5, 8],
        [8, 8, 8, 8, 8, 8, 8],
        [8, 6, 6, 8, 1, 3, 8],
        [8, 6, 6, 8, 1, 1, 8],
        [8, 8, 8, 8, 8, 8, 8],
    ]
    for mode, want in (("unique_color", unique), ("strict_majority", majority)):
        settings = {"fill_policy": mode}
        assert p.transform(grid, settings) == want
        assert reference.apply(p.program(settings), grid) == want


def test_count_intermediate_controls_fill_and_first_seed_ablation(p, reference):
    grid = p.sample_input(0, "train", 0)
    state = p.strict_majority_state(grid)
    causal_rooms = [
        room for room in state["rooms"]
        if room["winner"] is not None and len(room["seed_counts"]) >= 2
    ]
    assert causal_rooms
    room = causal_rooms[0]
    first_seed = room["seed_sequence"][0]
    assert first_seed != room["winner"]
    assert room["seed_counts"][str(room["winner"])] * 2 > room["seed_total"]

    settings = {"fill_policy": "strict_majority"}
    correct = p.transform(grid, settings)
    wrong = p.transform_first_seed(grid)
    assert correct != wrong
    assert reference.apply(p.program(settings), grid) == correct
    assert reference.apply(p.hypotheses(settings)["first_seed"], grid) == wrong


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_and_demo_only_identifiability(p, reference, demos):
    for mode in p.MODES:
        settings = {"fill_policy": mode}
        episode = p.generate(17, settings, demos, 4)
        certificate = p.verify_episode(episode, reference)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert certificate["survivors"] == ["setting:" + mode]
        assert len(certificate["query_checks"]) == 4
        assert all(item["identified_from_demonstrations"] for item in certificate["query_checks"])


def test_inputs_are_setting_independent_and_first_turn_count_independent(p):
    unique = p.generate(23, {"fill_policy": "unique_color"}, 3, 4)
    majority = p.generate(23, {"fill_policy": "strict_majority"}, 3, 4)
    one = p.generate(23, {"fill_policy": "strict_majority"}, 3, 1)
    for split in ("train", "test"):
        assert [pair["input"] for pair in unique[split]] == [pair["input"] for pair in majority[split]]
    assert unique["train"] != majority["train"]
    first = {"train": majority["train"], "test": [{"input": majority["test"][0]["input"]}]}
    assert public_challenge_bytes(first) == public_challenge_bytes(one)


def test_query_bank_is_seed_shuffled_and_covers_real_boundaries(p):
    first_shapes = set()
    expected = sorted([[14, 18], [19, 23], [25, 27], [30, 30]])
    for seed in range(12):
        episode = p.generate(seed, {"fill_policy": "strict_majority"}, 2, 4)
        shapes = [[len(pair["input"]), len(pair["input"][0])] for pair in episode["test"]]
        assert sorted(shapes) == expected
        first_shapes.add(tuple(shapes[0]))
    assert len(first_shapes) >= 3


def test_30_by_30_stress_scene_is_substantive_across_canvas(p, reference):
    episode = p.generate(9, {"fill_policy": "strict_majority"}, 2, 4)
    pair = next(pair for pair in episode["test"] if len(pair["input"]) == 30)
    grid = pair["input"]
    output = pair["output"]
    assert len(grid) == len(output) == 30
    assert all(len(row) == 30 for row in grid + output)
    for r0 in (0, 15):
        for c0 in (0, 15):
            patch = [row[c0:c0 + 15] for row in grid[r0:r0 + 15]]
            assert len({cell for row in patch for cell in row}) >= 3
            assert any(cell == 0 for row in patch for cell in row)
            assert any(cell == 8 for row in patch for cell in row)
    assert output != grid
    assert reference.apply(episode["program_solution"], grid) == output


@pytest.mark.parametrize(
    ("mode", "shortcut"),
    [
        ("unique_color", "seed_count_lookup"),
        ("strict_majority", "three_of_four_only"),
    ],
)
def test_seed_cardinality_shortcuts_are_rejected_by_two_demos(
    p, reference, mode, shortcut
):
    settings = {"fill_policy": mode}
    episode = p.generate(8, settings, 2, 4)
    programs = p.hypotheses(settings)
    assert shortcut in programs
    fit = p.fit_demonstrations(episode["train"], settings, reference)
    assert shortcut in fit["rejected_by_demo"]
    assert any(
        reference.apply(programs[shortcut], pair["input"]) != pair["output"]
        for pair in episode["test"]
    )


def test_first_seed_plurality_identity_and_one_cell_shortcuts_are_rejected(p, reference):
    for mode in p.MODES:
        settings = {"fill_policy": mode}
        episode = p.generate(8, settings, 2, 4)
        fit = p.fit_demonstrations(episode["train"], settings, reference)
        assert fit["survivors"] == ["setting:" + mode]
        for name in ("first_seed", "plurality", "identity", "exactly_one_seed_cell"):
            assert name in fit["rejected_by_demo"]


@pytest.mark.parametrize("kwargs", [
    {"demos": 1}, {"demos": 7}, {"demos": True},
    {"queries": 0}, {"queries": 5}, {"queries": 1.0}, {"seed": True},
    {"settings": {"fill_policy": "wrong"}},
    {"settings": {"fill_policy": "unique_color", "unknown": 1}},
])
def test_invalid_requests_are_rejected(p, kwargs):
    request = {"seed": 0, "settings": {"fill_policy": "unique_color"}, "demos": 3, "queries": 4}
    request.update(kwargs)
    with pytest.raises(ValueError):
        p.generate(**request)


def test_verifier_rejects_corruption_repetition_and_underteaching(p, reference):
    original = p.generate(8, {"fill_policy": "strict_majority"}, 2, 4)
    candidates = []
    bad = deepcopy(original)
    bad["test"][0]["output"][1][1] = (bad["test"][0]["output"][1][1] + 1) % 10
    candidates.append(bad)
    bad = deepcopy(original)
    bad["test"][0]["input"][0][0] = True
    candidates.append(bad)
    bad = deepcopy(original)
    bad["test"][0] = deepcopy(bad["train"][0])
    candidates.append(bad)
    bad = deepcopy(original)
    bad["program_solution"] = p.program({"fill_policy": "unique_color"})
    candidates.append(bad)
    bad = deepcopy(original)
    plain = [[8, 8, 8, 8], [8, 2, 0, 8], [8, 0, 0, 8], [8, 8, 8, 8]]
    bad["train"] = [{"input": deepcopy(plain), "output": p.transform(plain, {"fill_policy": "strict_majority"})} for _ in range(2)]
    candidates.append(bad)
    for candidate in candidates:
        with pytest.raises(ValueError):
            p.verify_episode(candidate, reference)


def test_native_adapter_loads_adjacent_implementation_not_cached_module(p):
    import sys
    import types

    previous = sys.modules.get("prototype")
    sys.modules["prototype"] = types.ModuleType("prototype")
    try:
        spec = importlib.util.spec_from_file_location(
            "room_fill_native_adapter_test", HOME / "workspace/parametric/adapter.py"
        )
        adapter = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(adapter)
        settings = {"fill_policy": "strict_majority"}
        assert adapter.program(settings) == p.program(settings)
        assert adapter.generate(6, settings, 2, 4) == p.generate(6, settings, 2, 4)
    finally:
        if previous is None:
            sys.modules.pop("prototype", None)
        else:
            sys.modules["prototype"] = previous


def test_bounded_probe_reports_source_bound_racket_results(p, reference):
    probe_path = HOME / "workspace/parametric/probe.py"
    assert probe_path.is_file(), "The bounded reusable authoring probe is missing"
    spec = importlib.util.spec_from_file_location("room_fill_probe_test", probe_path)
    probe = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(probe)
    report = probe.build_report(p, reference)
    assert report["schema"] == "room-fill-policy-probe-v1"
    assert report["status"] == "passed"
    assert report["task_id"] == "01dfed2930fa"
    assert report["failures"] == []
    assert report["case_count"] == 12
    assert report["causal_case"]["first_seed_changes_output"] is True
    assert report["shortcut_cases"]["seed_count_lookup"]["rejected_by_demo"] is True
    assert report["shortcut_cases"]["three_of_four_only"]["rejected_by_demo"] is True
    assert report["cardinality_collisions"]["5"] == [
        [False, False], [False, True], [True, True]
    ]
    assert sorted(report["boundary"]["query_shapes"]) == sorted([[14, 18], [19, 23], [25, 27], [30, 30]])
    assert report["source_sha256"] == p.source_bindings()
