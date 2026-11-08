"""Behavior contracts for the task-local parametric mirror family."""
from __future__ import annotations

import importlib.util
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

HOME = Path(__file__).resolve().parents[1]


def adapter():
    path = HOME / "workspace" / "parametric" / "adapter.py"
    assert path.is_file(), "missing task-local parametric mirror adapter"
    name = "_mirror_parametric_adapter_" + str(abs(hash(str(path))))
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def test_adapter_exposes_both_program_modes():
    module = adapter()
    default = module.program({"mode": "closure"})
    variant = module.program({"mode": "largest_after"})
    assert isinstance(default, str) and default.strip()
    assert isinstance(variant, str) and variant.strip()
    assert default != variant


# These expectations are hand-derived. The small middle shape becomes larger
# only after mirroring joins its original pieces; diagonal edge cells stay 7.
WITNESS = [
    [0, 7, 4, 7, 8, 0, 7, 0, 0],
    [0, 0, 7, 0, 8, 7, 0, 7, 0],
    [7, 0, 0, 0, 8, 0, 0, 0, 0],
    [0, 0, 0, 0, 8, 0, 0, 0, 0],
    [0, 7, 7, 0, 8, 0, 0, 0, 0],
    [0, 7, 0, 0, 8, 0, 0, 0, 0],
    [0, 0, 0, 5, 8, 0, 0, 0, 0],
    [0, 0, 0, 0, 8, 0, 0, 0, 0],
]
CLOSURE = [
    [0, 7, 7, 7, 8, 7, 7, 7, 0],
    [0, 7, 7, 7, 8, 7, 7, 7, 0],
    [7, 0, 0, 0, 8, 0, 0, 0, 7],
    [0, 0, 0, 0, 8, 0, 0, 0, 0],
    [0, 7, 7, 0, 8, 0, 7, 7, 0],
    [0, 7, 0, 0, 8, 0, 0, 7, 0],
    [0, 0, 0, 5, 8, 0, 0, 0, 0],
    [0, 0, 0, 0, 8, 0, 0, 0, 0],
]
LARGEST = [
    [0, 2, 2, 2, 8, 2, 2, 2, 0],
    [0, 2, 2, 2, 8, 2, 2, 2, 0],
    [7, 0, 0, 0, 8, 0, 0, 0, 7],
    [0, 0, 0, 0, 8, 0, 0, 0, 0],
    [0, 7, 7, 0, 8, 0, 7, 7, 0],
    [0, 7, 0, 0, 8, 0, 0, 7, 0],
    [0, 0, 0, 5, 8, 0, 0, 0, 0],
    [0, 0, 0, 0, 8, 0, 0, 0, 0],
]
CLIPPED_INPUT = [
    [0, 7, 8, 4, 0, 0, 0, 7],
    [0, 0, 8, 0, 0, 0, 0, 0],
    [0, 0, 8, 0, 0, 0, 0, 0],
    [0, 0, 8, 0, 0, 0, 0, 0],
    [0, 0, 8, 0, 0, 0, 0, 0],
    [0, 0, 8, 0, 0, 0, 0, 0],
    [0, 0, 8, 0, 5, 0, 0, 0],
    [0, 0, 8, 0, 0, 0, 0, 0],
]
CLIPPED_CLOSURE = [
    [0, 7, 8, 7, 0, 0, 0, 7],
    [0, 0, 8, 0, 0, 0, 0, 0],
    [0, 0, 8, 0, 0, 0, 0, 0],
    [0, 0, 8, 0, 0, 0, 0, 0],
    [0, 0, 8, 0, 0, 0, 0, 0],
    [0, 0, 8, 0, 0, 0, 0, 0],
    [0, 0, 8, 0, 5, 0, 0, 0],
    [0, 0, 8, 0, 0, 0, 0, 0],
]
CLIPPED_LARGEST = [
    [0, 2, 8, 2, 0, 0, 0, 2],
    [0, 0, 8, 0, 0, 0, 0, 0],
    [0, 0, 8, 0, 0, 0, 0, 0],
    [0, 0, 8, 0, 0, 0, 0, 0],
    [0, 0, 8, 0, 0, 0, 0, 0],
    [0, 0, 8, 0, 0, 0, 0, 0],
    [0, 0, 8, 0, 5, 0, 0, 0],
    [0, 0, 8, 0, 0, 0, 0, 0],
]


def transpose(grid):
    return [list(row) for row in zip(*grid)]


def pixel_oracle(grid, mode):
    """Independent original-pixel reflection and orthogonal flood fill."""
    height, width = len(grid), len(grid[0])
    axes = [("row", r) for r, row in enumerate(grid) if all(v == 8 for v in row)]
    axes += [("col", c) for c in range(width) if all(row[c] == 8 for row in grid)]
    assert len(axes) == 1
    orientation, axis = axes[0]
    result = deepcopy(grid)
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 7:
                rr, cc = (2 * axis - r, c) if orientation == "row" else (r, 2 * axis - c)
                if 0 <= rr < height and 0 <= cc < width:
                    result[rr][cc] = 7
    if mode == "closure":
        return result
    unseen = {(r, c) for r in range(height) for c in range(width) if result[r][c] == 7}
    components = []
    while unseen:
        start = unseen.pop()
        component, pending = {start}, [start]
        while pending:
            r, c = pending.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    pending.append(neighbor)
        components.append(component)
    maximum = max(map(len, components), default=0)
    for component in components:
        if len(component) == maximum:
            for r, c in component:
                result[r][c] = 2
    return result


def assert_grid(grid):
    assert type(grid) is list and 8 <= len(grid) <= 30
    assert type(grid[0]) is list and 8 <= len(grid[0]) <= 30
    assert all(type(row) is list and len(row) == len(grid[0]) for row in grid)
    assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)


def test_default_program_preserves_selected_canonical_string():
    root = find_root(__file__)
    records = [json.loads(line) for line in canonical_path(root).read_text().splitlines()]
    selected = [row for row in records if row.get("task_id") == "8b6543be4517"]
    assert len(selected) == 1
    assert adapter().program({"mode": "closure"}) == selected[0]["program_solution"]


@pytest.fixture(scope="module")
def boundary_inputs():
    family = adapter().family
    return [family.sample_input(17, index, height=size, width=size,
                                orientation=orientation, profile=profile)
            for index, (size, orientation, profile) in enumerate([
                (8, "col", "merge"), (8, "row", "clipped"),
                (30, "col", "tie"), (30, "row", "stable")])]


def test_sampler_uses_minimum_and_substantive_maximum_canvas(boundary_inputs):
    for grid, size, orientation in zip(boundary_inputs, [8, 8, 30, 30], ["col", "row", "col", "row"]):
        assert_grid(grid)
        assert (len(grid), len(grid[0])) == (size, size)
        full_rows = [r for r, row in enumerate(grid) if all(value == 8 for value in row)]
        full_cols = [c for c in range(size) if all(row[c] == 8 for row in grid)]
        assert (len(full_rows), len(full_cols)) == ((1, 0) if orientation == "row" else (0, 1))
    for grid in boundary_inputs[2:]:
        occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                    if value not in (0, 8)]
        assert len(occupied) >= 80
        assert min(r for r, _ in occupied) <= 2
        assert max(r for r, _ in occupied) >= 27
        assert min(c for _, c in occupied) <= 2
        assert max(c for _, c in occupied) >= 27


def test_large_clipped_scene_scales_meaningful_source_content():
    # Regression: the long clipped stripe must accompany substantial reflected
    # objects, rather than carrying an almost empty large-canvas example alone.
    grid = adapter().family.sample_input(97, 3, height=30, width=30, profile="clipped")
    assert sum(value == 7 for row in grid for value in row) >= 50


@pytest.mark.parametrize("mode,expected", [("closure", CLOSURE), ("largest_after", LARGEST)])
def test_protected_execution_recomputes_after_merge_and_recolors_all_maxima(mode, expected, boundary_inputs):
    module = adapter()
    inputs = [deepcopy(WITNESS), transpose(WITNESS), deepcopy(CLIPPED_INPUT)] + deepcopy(boundary_inputs)
    before = deepcopy(inputs)
    outputs, identity = module.family.execute(module.program({"mode": mode}), inputs)
    assert identity["protected"] is True
    assert outputs[:2] == [expected, transpose(expected)]
    assert outputs[2] == (CLIPPED_CLOSURE if mode == "closure" else CLIPPED_LARGEST)
    assert outputs[3:] == [pixel_oracle(grid, mode) for grid in boundary_inputs]
    assert inputs == before


@pytest.fixture(scope="module")
def episodes():
    module = adapter()
    return {(seed, mode): module.generate(seed, {"mode": mode}, demos, 4)
            for seed, demos in [(0, 2), (17, 6)]
            for mode in ("closure", "largest_after")}


@pytest.mark.parametrize("seed,demos", [(0, 2), (17, 6)])
def test_requested_counts_distinct_matched_inputs_and_correct_labels(episodes, seed, demos):
    for mode in ("closure", "largest_after"):
        episode = episodes[seed, mode]
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == adapter().program({"mode": mode})
        pairs = episode["train"] + episode["test"]
        inputs = [pair["input"] for pair in pairs]
        assert len({json.dumps(grid) for grid in inputs}) == demos + 4
        for pair in pairs:
            assert_grid(pair["input"])
            assert_grid(pair["output"])
            assert pair["output"] == pixel_oracle(pair["input"], mode)
    closure, largest = episodes[seed, "closure"], episodes[seed, "largest_after"]
    assert [p["input"] for p in closure["train"] + closure["test"]] == [
        p["input"] for p in largest["train"] + largest["test"]]
    assert closure["train"] != largest["train"]


@pytest.mark.parametrize("mode", ["closure", "largest_after"])
def test_public_turn_hides_answers_private_data_and_future_queries(episodes, mode):
    episode = episodes[0, mode]
    public = adapter().family.public_turn(episode)
    assert public == {"train": episode["train"], "test": [{"input": episode["test"][0]["input"]}]}
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert set(public["test"][0]) == {"input"}
    changed = deepcopy(episode)
    changed.update(settings={"mode": "secret"}, seed=999, program_solution="secret",
                   runtime={"secret": True}, teaching={"secret": True})
    for pair in changed["test"]:
        pair["output"] = [[True]]
    for pair in changed["test"][1:]:
        pair["input"] = [[False]]
    changed_public = adapter().family.public_turn(changed)
    assert public_challenge_bytes(public) == public_challenge_bytes(changed_public)
    assert public_challenge_id(public) == public_challenge_id(changed_public)
    # Projection must not expose live references into private episode storage.
    public["train"][0]["input"][0][0] = 99
    assert episode["train"][0]["input"][0][0] != 99


@pytest.mark.parametrize("mode", ["closure", "largest_after"])
def test_query_count_does_not_change_demos_or_first_public_turn(episodes, mode):
    one = adapter().generate(0, {"mode": mode}, 2, 1)
    four = episodes[0, mode]
    assert one["train"] == four["train"]
    assert one["test"] == four["test"][:1]
    assert public_challenge_bytes(adapter().family.public_turn(one)) == public_challenge_bytes(
        adapter().family.public_turn(four))


@pytest.mark.parametrize("settings", [None, [], {}, {"mode": True}, {"mode": "other"},
    {"mode": "closure", "extra": 1}])
def test_invalid_settings_rejected_by_program_and_generation(settings):
    with pytest.raises(ValueError):
        adapter().program(settings)
    with pytest.raises(ValueError):
        adapter().generate(0, settings, 2, 1)


@pytest.mark.parametrize("seed,demos,queries", [
    (True, 2, 1), (-1, 2, 1), (2 ** 63, 2, 1), (0.0, 2, 1), ("0", 2, 1),
    (0, True, 1), (0, 1, 1), (0, 7, 1), (0, 2.0, 1),
    (0, 2, False), (0, 2, 0), (0, 2, 5), (0, 2, 1.0),
])
def test_invalid_seed_and_counts_fail_before_execution(seed, demos, queries):
    with pytest.raises(ValueError):
        adapter().generate(seed, {"mode": "closure"}, demos, queries)
