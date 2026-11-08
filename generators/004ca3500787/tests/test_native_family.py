"""Native shape-class selection and observed/canonical pose contracts."""
import importlib.util
import json
from pathlib import Path

import pytest

SOURCE = Path(__file__).parents[1] / "workspace/parametric/native_family.py"


def test_native_module_exists():
    assert SOURCE.is_file(), "native pose family has not been implemented"


@pytest.fixture(scope="module")
def native():
    spec = importlib.util.spec_from_file_location("shape_pose_native_under_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_canonical_and_ordinary_default(native):
    assert native.program({"pose": "canonical"}) == (SOURCE.parent / "canonical.rkt").read_text()
    assert native.program({"pose": "observed"}).startswith("(rule!")
    assert native.program({"pose": "canonical"}) != native.program({"pose": "observed"})
    assert json.loads((SOURCE.parent / "promotion.json").read_text())["qualification_demos"] == 3


def test_string_order_is_authority_for_two_digit_coordinates(native):
    grid = [[2] * 10 + [0], [2] + [0] * 8 + [2, 2], [0] * 11, [2, 0, 2] + [0] * 8]
    expected = [[8, 8] + [0] * 8 + [8], [0] + [8] * 10]
    assert native.solve(grid, "canonical") == expected
    assert native.solve(grid, "observed") == [[8] * 10 + [0], [8] + [0] * 8 + [8, 8]]


def test_minimum_axis_and_reflection_classification(native):
    assert native.solve([[2, 0, 2, 0, 2, 2]], "canonical") == [[8, 8]]
    assert native.solve([[2], [0], [2], [0], [2], [2]], "observed") == [[8], [8]]
    f = native.SHAPES["F5"]
    assert len(native.variants(f)) == 8
    assert native.canonical(f) == native.canonical(native.pose(f, 4))


@pytest.mark.parametrize("grid", [[], [[]], [[0], [0, 2]], [[True]], [[2.0]], [[3]], [[2]], [[2, 0, 2]], [[2, 0, 2, 0, 2]], [[0] * 31], [[0]] * 31])
def test_grid_domain_rejections(native, grid):
    with pytest.raises(ValueError):
        native.solve(grid)


@pytest.mark.parametrize("settings", [{}, {"pose": "bad"}, {"pose": 1}, {"pose": True}, {"pose": "canonical", "x": 2}, None])
def test_reject_invalid_settings(native, settings):
    with pytest.raises(ValueError):
        native.program(settings)


@pytest.mark.parametrize("kwargs", [{"seed": True}, {"seed": -1}, {"seed": 2**63}, {"seed": 2.0}, {"demos": 1}, {"demos": 7}, {"demos": True}, {"queries": 0}, {"queries": 5}, {"queries": 1.0}])
def test_strict_request_controls(native, kwargs):
    args = {"seed": 0, "settings": {"pose": "canonical"}, "demos": 3, "queries": 4}
    args.update(kwargs)
    with pytest.raises(ValueError):
        native.generate(**args)


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_banks_are_matched_distinct_fresh_and_count_stable(native, seed):
    canonical = native.generate(seed, {"pose": "canonical"}, 6, 4)
    observed = native.generate(seed, {"pose": "observed"}, 6, 4)
    for split in ("train", "test"):
        assert [p["input"] for p in canonical[split]] == [p["input"] for p in observed[split]]
    assert all(a["output"] != b["output"] for a, b in zip(canonical["train"][:2], observed["train"][:2]))
    assert len({tuple(map(tuple, p["input"])) for p in canonical["train"] + canonical["test"]}) == 10
    short = native.generate(seed, {"pose": "canonical"}, 2, 1)
    assert short["train"] == canonical["train"][:2]
    assert short["test"] == canonical["test"][:1]
    canonical["train"][0]["input"][0][0] = 9
    assert native.generate(seed, {"pose": "canonical"}, 2, 1) == short


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_cores_teach_bbox_string_order_and_vary_output_pose(native, seed):
    train, _ = native.input_bank(seed)
    records_a, odd_a = native.analyze(train[0])
    records_b, odd_b = native.analyze(train[1])
    assert len({(max(r for r, c in obj) - min(r for r, c in obj), max(c for r, c in obj) - min(c for r, c in obj)) for obj in records_a}) == 1
    assert native.canonical(odd_b) != min(native.variants(odd_b))
    assert not any(native.pose(native.canonical(odd_a), k) == native.normalize(odd_a)
                   and native.pose(native.canonical(odd_b), k) == native.normalize(odd_b)
                   for k in range(8))
    assert len(records_b) == 3
    labels = {cell: index for index, obj in enumerate(records_b) for cell in obj}
    assert any(labels.get((r + dr, c + dc), index) != index
               for (r, c), index in labels.items() for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)))


def test_large_profiles_are_substantive_and_distinct(native):
    episode = native.generate(0, {"pose": "observed"}, 6, 4)
    large = [p["input"] for p in episode["train"] + episode["test"] if len(p["input"]) == len(p["input"][0]) == 30]
    assert [sum(v == 2 for row in grid for v in row) for grid in large] == [405, 320]
    for grid in large:
        for r in (0, 15):
            for c in (0, 15):
                assert sum(grid[y][x] == 2 for y in range(r, r + 15) for x in range(c, c + 15)) >= 40
