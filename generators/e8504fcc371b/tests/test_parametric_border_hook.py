"""Native parametric regressions for the commanded-ray/border-hook family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root, public_challenge_bytes

TASK_ID = "e8504fcc371b"
ROOT = find_root(__file__)
HOME = ROOT / f"generators/{TASK_ID}"
SOURCE = HOME / "workspace/parametric/prototype.py"


def _load():
    assert SOURCE.is_file(), "task-local border-hook prototype is missing"
    spec = importlib.util.spec_from_file_location("parametric_e850_border_hook", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return _load()


@pytest.fixture(scope="module")
def engine(proto):
    with proto.RacketEngine() as runtime:
        yield runtime


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_exact_canonical(proto):
    from arcpuzzles import Catalog

    record = Catalog(ROOT).get(TASK_ID)
    sources = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert sources == {proto.program({"trail_mode": "straight_to_border"})}


def test_border_hook_consumes_ray_endpoint_and_length(proto):
    grid = proto.sample_input(19, "train", 0, 16, 18)
    intermediate = proto.intermediate_value(grid)
    assert set(intermediate) == {"endpoint", "ray_length"}
    assert intermediate["ray_length"] >= 2
    assert tuple(intermediate["endpoint"]) in proto.perimeter(grid)
    straight = proto.transform(grid, {"trail_mode": "straight_to_border"})
    hooked = proto.transform(grid, {"trail_mode": "border_hook"})
    assert straight != hooked
    assert proto.changed_cells(grid, straight) == set(proto.ray_cells(grid))
    assert set(proto.ray_cells(grid)) < proto.changed_cells(grid, hooked)
    assert len(proto.hook_cells(grid, intermediate["ray_length"])) == intermediate["ray_length"]


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_matched_inputs_identification_and_four_queries(proto, engine, demos):
    episodes = [
        proto.generate(17, {"trail_mode": mode}, demos, 4)
        for mode in ("straight_to_border", "border_hook")
    ]
    assert _inputs(episodes[0]) == _inputs(episodes[1])
    for episode in episodes:
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(episode)}) == demos + 4
        certificate = proto.verify_episode(episode, engine=engine)
        assert certificate["survivors"] == [episode["settings"]]
        assert certificate["fit_scope"] == "demonstrations_only"
        assert len(certificate["query_checks"]) == 4


def test_real_racket_labels_and_30_square_span_the_canvas(proto, engine):
    for mode in ("straight_to_border", "border_hook"):
        settings = {"trail_mode": mode}
        episode = proto.generate(23, settings, 3, 4)
        for pair in episode["train"] + episode["test"]:
            assert engine.apply(proto.program(settings), pair["input"]) == pair["output"]

    episode = proto.generate(23, {"trail_mode": "border_hook"}, 3, 4)
    pair = episode["test"][-1]
    source, output = pair["input"], pair["output"]
    assert (len(source), len(source[0])) == (30, 30)
    assert sum(cell != 0 for row in source for cell in row) == 2
    changed = proto.changed_cells(source, output)
    assert len(changed) >= 40
    rows = [row for row, _ in changed]
    cols = [col for _, col in changed]
    assert max(rows) - min(rows) >= 20
    assert max(cols) - min(cols) >= 20
    assert sum(
        output[row][col] != 0
        for row in range(30)
        for col in range(30)
        if row in (0, 29) or col in (0, 29)
    ) >= 20


def test_two_demo_lessons_vary_command_and_ray_length(proto):
    for seed in range(12):
        episode = proto.generate(seed, {"trail_mode": "border_hook"}, 2, 1)
        values = [proto.scene_facts(pair["input"]) for pair in episode["train"]]
        assert len({item["code"] for item in values}) == 2
        assert len({item["ray_length"] for item in values}) == 2


def test_query_prefix_and_public_first_turn_are_count_independent(proto):
    one = proto.generate(31, {"trail_mode": "border_hook"}, 2, 1)
    four = proto.generate(31, {"trail_mode": "border_hook"}, 6, 4)
    assert one["test"] == four["test"][:1]
    first = {"train": one["train"], "test": [{"input": one["test"][0]["input"]}]}
    comparison = {"train": one["train"], "test": [{"input": four["test"][0]["input"]}]}
    assert public_challenge_bytes(first) == public_challenge_bytes(comparison)


def test_wrong_intermediate_counterfactual_changes_final_output(proto, engine):
    settings = {"trail_mode": "border_hook"}
    episode = proto.generate(7, settings, 3, 4)
    pair = next(
        pair for pair in episode["test"]
        if proto.intermediate_value(pair["input"])["ray_length"] > 2
    )
    actual = engine.apply(proto.program(settings), pair["input"])
    counterfactual = engine.apply(proto.counterfactual_program(1), pair["input"])
    assert actual == pair["output"]
    assert actual != counterfactual
    assert len(proto.changed_cells(pair["input"], counterfactual)) < len(proto.changed_cells(pair["input"], actual))


@pytest.mark.parametrize(
    "mutation",
    [
        {"seed": True},
        {"demos": 1},
        {"demos": 7},
        {"queries": 0},
        {"queries": 5},
        {"settings": {"trail_mode": "unknown"}},
        {"settings": {"trail_mode": "straight_to_border", "extra": 1}},
    ],
)
def test_invalid_requests_fail_closed(proto, mutation):
    kwargs = {
        "seed": 0,
        "settings": {"trail_mode": "straight_to_border"},
        "demos": 3,
        "queries": 4,
    }
    kwargs.update(mutation)
    with pytest.raises(ValueError):
        proto.generate(**kwargs)


def test_verifier_rejects_corrupt_labels_duplicate_inputs_and_program(proto, engine):
    episode = proto.generate(11, {"trail_mode": "straight_to_border"}, 2, 4)
    corruptions = []
    bad = deepcopy(episode)
    bad["test"][0]["output"][0][0] = 9
    corruptions.append(bad)
    bad = deepcopy(episode)
    bad["test"][0] = deepcopy(bad["train"][0])
    corruptions.append(bad)
    bad = deepcopy(episode)
    bad["program_solution"] = proto.program({"trail_mode": "border_hook"})
    corruptions.append(bad)
    bad = deepcopy(episode)
    bad["train"][0]["input"][0][0] = True
    corruptions.append(bad)
    for bad in corruptions:
        with pytest.raises(ValueError):
            proto.verify_episode(bad, engine=engine)
