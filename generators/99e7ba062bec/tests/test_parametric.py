"""Native parametric-family contract for 99e7ba062bec."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
HOME = REPO / "generators/99e7ba062bec/workspace/parametric"
CODES = range(1, 8)


def _load_adapter():
    path = HOME / "adapter.py"
    assert path.exists(), "parametric adapter has not been implemented"
    spec = importlib.util.spec_from_file_location("parametric_99e7ba062bec", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _apply(grid, code):
    if code == 1:
        return [row[:] for row in grid]
    if code == 2:
        return [list(col) for col in zip(*grid[::-1])]
    if code == 3:
        return [row[::-1] for row in grid[::-1]]
    if code == 4:
        return [list(col) for col in zip(*grid)][::-1]
    if code == 5:
        return [row[::-1] for row in grid]
    if code == 6:
        return [row[:] for row in grid[::-1]]
    if code == 7:
        return [list(col) for col in zip(*grid)]
    raise AssertionError(code)


def _crop(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert cells
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _bands(grid):
    width = len(grid[0])
    result = []
    c = 0
    while c < width:
        while c < width and all(row[c] == 0 for row in grid):
            c += 1
        if c >= width:
            break
        start = c
        while c < width and any(row[c] != 0 for row in grid):
            c += 1
        result.append((start, c))
    return result


def _panels(grid):
    return [_crop([row[start:stop] for row in grid]) for start, stop in _bands(grid)]


def _mask(panel):
    return [[int(value != 0) for value in row] for row in panel]


def _command(grid):
    a, b, _ = _panels(grid)
    matches = [code for code in CODES if _crop(_apply(_mask(a), code)) == _mask(b)]
    assert len(matches) == 1
    return matches[0]


def _expected(grid, application):
    _, _, c = _panels(grid)
    code = _command(grid)
    if application == "inverse":
        code = {2: 4, 4: 2}.get(code, code)
    return _crop(_apply(c, code))


def _inputs(episode, split):
    return [pair["input"] for pair in episode[split]]


def test_default_program_is_exact_and_settings_are_strict():
    adapter = _load_adapter()
    canonical = (HOME / "canonical.rkt").read_text(encoding="utf-8")
    assert adapter.program({"application": "forward"}) == canonical
    assert adapter.program({"application": "inverse"}) == (
        HOME / "inverse.rkt"
    ).read_text(encoding="utf-8")
    for bad in (
        {},
        {"application": "forward", "extra": 1},
        {"application": "backward"},
        {"application": 1},
        None,
    ):
        with pytest.raises(ValueError):
            adapter.program(bad)


def test_inputs_are_setting_matched_and_count_prefixes_are_independent():
    adapter = _load_adapter()
    forward = adapter.generate(17, {"application": "forward"}, 3, 4)
    inverse = adapter.generate(17, {"application": "inverse"}, 3, 4)
    assert _inputs(forward, "train") == _inputs(inverse, "train")
    assert _inputs(forward, "test") == _inputs(inverse, "test")

    two = adapter.generate(17, {"application": "forward"}, 2, 4)
    six = adapter.generate(17, {"application": "forward"}, 6, 4)
    one_query = adapter.generate(17, {"application": "forward"}, 3, 1)
    assert _inputs(two, "train") == _inputs(six, "train")[:2]
    assert _inputs(two, "test") == _inputs(six, "test")
    assert _inputs(one_query, "test") == _inputs(forward, "test")[:1]
    all_inputs = _inputs(six, "train") + _inputs(six, "test")
    assert len({repr(grid) for grid in all_inputs}) == len(all_inputs)


@pytest.mark.parametrize("seed", [0, 17, 991])
def test_labels_match_forward_and_inverse_and_two_demos_identify_setting(seed):
    adapter = _load_adapter()
    forward = adapter.generate(seed, {"application": "forward"}, 2, 4)
    inverse = adapter.generate(seed, {"application": "inverse"}, 2, 4)
    assert [_command(pair["input"]) for pair in forward["train"]] == [2, 4]

    for left, right in zip(forward["train"] + forward["test"], inverse["train"] + inverse["test"]):
        assert left["input"] == right["input"]
        assert left["output"] == _expected(left["input"], "forward")
        assert right["output"] == _expected(right["input"], "inverse")
        c_color = next(value for row in _panels(left["input"])[2] for value in row if value)
        assert {value for row in left["output"] for value in row if value} == {c_color}
        assert {value for row in right["output"] for value in row if value} == {c_color}

    assert all(
        left["output"] != right["output"]
        for left, right in zip(forward["train"], inverse["train"])
    )


@pytest.mark.parametrize("seed", [42, 84])
@pytest.mark.parametrize("application", ["forward", "inverse"])
def test_four_queries_include_substantive_30x30_transform_scene(seed, application):
    adapter = _load_adapter()
    episode = adapter.generate(seed, {"application": application}, 3, 4)
    assert len(episode["test"]) == 4
    large = episode["test"][-1]
    grid = large["input"]
    assert len(grid) == 30 and all(len(row) == 30 for row in grid)
    panels = _panels(grid)
    assert len(panels) == 3
    assert sum(value != 0 for row in grid for value in row) >= 90
    assert min(sum(value != 0 for row in panel for value in row) for panel in panels) >= 25
    occupied_rows = {r for r, row in enumerate(grid) if any(row)}
    assert len(occupied_rows) >= 15
    assert _command(grid) in (2, 4)
    assert large["output"] == _expected(grid, application)


def test_seed_and_counts_reject_bool_fraction_and_out_of_range_values():
    adapter = _load_adapter()
    settings = {"application": "forward"}
    for args in (
        (True, settings, 3, 4),
        (0, settings, 1, 4),
        (0, settings, 7, 4),
        (0, settings, 3, 0),
        (0, settings, 3, 5),
        (0, settings, 3.0, 4),
        (-1, settings, 3, 4),
    ):
        with pytest.raises(ValueError):
            adapter.generate(*args)


def test_self_audit_refutes_every_named_shortcut_at_minimum_demo_count():
    path = HOME / "audit.py"
    assert path.exists(), "parametric self-audit has not been implemented"
    spec = importlib.util.spec_from_file_location("audit_99e7ba062bec", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.run(seeds=(0, 17, 991))
    assert report["schema"] == "arcpuzzles-parametric-self-audit-v1"
    assert report["status"] == "passed"
    assert report["surviving_rivals"] == []
    assert report["episodes_checked"] == 6
    assert report["has_30x30"] is True
