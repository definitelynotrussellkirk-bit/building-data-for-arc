"""Official labels, digital-topology controls, and strict native boundaries."""
from pathlib import Path
from collections import Counter
import copy
import ast
import hashlib
import importlib.util
import json
import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]


@pytest.fixture(scope="module")
def native():
    spec = importlib.util.spec_from_file_location("topology_native_test", HOME / "workspace/parametric/native_family.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def originals():
    raw = ROOT / "shared/data/raw"
    task = json.loads((raw / "arc-agi_evaluation_challenges.json").read_text())["aa4ec2a5"]
    gold = json.loads((raw / "arc-agi_evaluation_solutions.json").read_text())["aa4ec2a5"]
    return task["train"] + [{"input": p["input"], "output": o} for p, o in zip(task["test"], gold)]


@pytest.mark.parametrize("index", range(4))
def test_all_provided_official_gold(native, index):
    pair = originals()[index]
    before = copy.deepcopy(pair["input"])
    assert native.solve(pair["input"], 4) == pair["output"]
    assert native.solve(pair["input"], 8) == pair["output"]
    assert pair["input"] == before
    assert len(native.plan(pair["input"], 4)["objects"]) == (3, 4, 3, 4)[index]


def inset(rows, top=2, left=2, size=9):
    grid = [[4] * size for _ in range(size)]
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            grid[top + r][left + c] = int(value)
    return grid


def test_diagonal_only_access_changes_topology(native):
    grid = inset(["411", "141", "111"])
    four, eight = native.solve(grid, 4), native.solve(grid, 8)
    assert four[3][3] == 6 and eight[3][3] == 2
    assert four[4][4] == 8 and eight[4][4] == 1
    assert four[2][2] == eight[2][2] == 2


def test_open_channel_and_solid_dot_do_not_gain_hole_color(native):
    grid = inset(["141", "141", "111"])
    assert not native.plan(grid, 4)["holes"]
    assert native.solve(grid)[3][3] == 2
    dot = inset(["1"])
    expected = [[4] * 9 for _ in range(9)]
    for r in range(1, 4):
        for c in range(1, 4):
            expected[r][c] = 1 if (r, c) == (2, 2) else 2
    assert native.solve(dot) == expected


def test_entire_holed_object_and_distant_arm_recolored(native):
    grid = inset(["111111", "141444", "111444"], size=12)
    output = native.solve(grid)
    assert output[2][7] == 8 and output[3][3] == 6
    assert len(native.plan(grid, 4)["holes"]) == 1


def test_border_clipping_and_overlapping_outlines(native):
    grid = [[4] * 8 for _ in range(8)]
    grid[0][0] = grid[0][2] = 1
    output = native.solve(grid)
    assert output[0][:4] == [1, 2, 1, 2]
    assert output[1][:4] == [2, 2, 2, 2]
    assert len(output) == len(output[0]) == 8


def test_excluded_diagonal_component_contact(native):
    grid = inset(["14", "41"])
    with pytest.raises(ValueError):
        native.plan(grid, 4)


def test_excluded_nested_foreground(native):
    grid = inset(["11111", "14441", "14141", "14441", "11111"], size=13)
    with pytest.raises(ValueError):
        native.plan(grid, 4)


@pytest.mark.parametrize("settings", [None, {}, {"hole_connectivity": True}, {"hole_connectivity": 4.0}, {"hole_connectivity": 6}, {"hole_connectivity": 4, "extra": 1}])
def test_bad_program_settings(native, settings):
    with pytest.raises(ValueError):
        native.program(settings)


def test_default_program_exactly_matches_both_canonical_files(native):
    data = (HOME / "reference.rkt").read_bytes()
    assert native.program({"hole_connectivity": 4}).encode() == data
    assert (HOME / "workspace/parametric/canonical.rkt").read_bytes() == data
    assert native.program({"hole_connectivity": 8}) != native.CANONICAL


@pytest.mark.parametrize("grid", [[], [[]], [[True]], [[10]], [[4], [4, 1]], [[4.0]], ((4, 1), (4, 4)), [[4, 1], [1, 4]], [[4] * 31], [[4, 4, 2]], [[4, 4, 1, 3]]])
def test_invalid_grid_boundaries(native, grid):
    with pytest.raises(ValueError):
        native.plan(grid, 4)


@pytest.mark.parametrize("seed", [0, 17, 43])
def test_matched_parameter_inputs_determinism_and_count_prefixes(native, seed):
    settings = {"hole_connectivity": 4}
    full = native.generate(seed, settings, 6, 4)
    alternate = native.generate(seed, {"hole_connectivity": 8}, 6, 4)
    assert full == native.generate(seed, settings, 6, 4)
    left, right = full["train"] + full["test"], alternate["train"] + alternate["test"]
    assert [p["input"] for p in left] == [p["input"] for p in right]
    assert len({json.dumps(p["input"]) for p in left}) == 10
    assert all(a["output"] != b["output"] for a, b in zip(full["train"][:2], alternate["train"][:2]))
    for demos, queries in ((2, 1), (3, 4), (6, 2)):
        short = native.generate(seed, settings, demos, queries)
        assert short["train"] == full["train"][:demos] and short["test"] == full["test"][:queries]
    assert len(native.generate(seed, settings)["train"]) == 3
    pristine = copy.deepcopy(full)
    full["train"][0]["input"][0][0] = 99
    assert native.generate(seed, settings, 6, 4) == pristine


@pytest.mark.parametrize("kwargs", [{"seed": True}, {"seed": -1}, {"seed": 2**63}, {"demos": 1}, {"demos": 7}, {"demos": 2.0}, {"queries": 0}, {"queries": 5}, {"queries": False}, {"settings": {}}, {"settings": {"hole_connectivity": True}}])
def test_invalid_episode_boundaries(native, kwargs):
    with pytest.raises(ValueError):
        native.generate(**{"seed": 17, **kwargs})


@pytest.mark.parametrize("seed", [0, 17, 43])
def test_large_profiles_have_substantive_topology(native, seed):
    train, test = native.input_bank(seed)
    large = [g for g in train + test if len(g) == len(g[0]) == 30]
    assert len(large) == 2 and large[0] != large[1]
    for grid in large:
        four, eight = native.plan(grid, 4), native.plan(grid, 8)
        assert len(four["source_cells"]) >= 300
        assert len(four["objects"]) >= 4
        assert len(four["holes"]) > len(eight["holes"]) >= 20


def test_query_presentation_order_varies(native):
    orders = {tuple(tuple(sorted((len(g), len(g[0])))) for g in native.input_bank(s)[1]) for s in range(5)}
    assert len(orders) > 1


def test_required_teaching_cores_have_distinct_palette_roles(native):
    demos, _ = native.input_bank(15)
    roles = [tuple(color for color, _ in Counter(v for row in grid for v in row).most_common())
             for grid in demos[:2]]
    assert roles[0][0] != roles[1][0], "The first two modal background colors must differ"
    assert roles[0][1] != roles[1][1], "The first two foreground colors must differ"


def test_selected_generator_and_literal_rule_identity():
    path = HOME / "generator.py"
    assert path.is_file()
    tree = ast.parse(path.read_text())
    declared = [node.value.value for node in tree.body if isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "RULE_TASK_ID" for t in node.targets)
                and isinstance(node.value, ast.Constant)]
    assert declared == ["ee_aa4ec2a5"]
    spec = importlib.util.spec_from_file_location("selected_topology_test", path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    assert module.RULE_HASH == hashlib.sha256(" ".join((HOME / "reference.rkt").read_text().split()).encode()).hexdigest()[:12]
    grid = module.generate(seed=17, sample_index=0, difficulty="hard")
    assert module.self_check(grid) == []
    assert grid == module.generate(seed=17, sample_index=0, difficulty="hard")
    assert grid != module.generate(seed=17, sample_index=1)
    with pytest.raises(ValueError):
        module.generate(seed=17, unknown=1)
