"""Official labels, literal beam shadows, and native request boundaries."""
from pathlib import Path
import ast
import copy
import hashlib
import importlib.util
import json
import pytest


HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
NATIVE_PATH = HOME / "workspace/parametric/native_family.py"


@pytest.fixture(scope="module")
def native():
    assert NATIVE_PATH.is_file(), "Native implementation has not been authored"
    spec = importlib.util.spec_from_file_location("nozzle_native_test", NATIVE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def official_pairs():
    raw = ROOT / "shared/data/raw"
    challenge = json.loads((raw / "arc-agi_evaluation_challenges.json").read_text())["b9e38dc0"]
    gold = json.loads((raw / "arc-agi_evaluation_solutions.json").read_text())["b9e38dc0"]
    return challenge["train"] + [{"input": pair["input"], "output": output}
                                  for pair, output in zip(challenge["test"], gold)]


def test_native_module_exists():
    assert NATIVE_PATH.is_file()


@pytest.mark.parametrize("index", range(4))
def test_all_provided_official_gold(native, index):
    pair = official_pairs()[index]
    before = copy.deepcopy(pair["input"])
    assert native.solve(pair["input"], "opaque") == pair["output"]
    assert pair["input"] == before


# Fixed expected grids, established from these explicit row intervals and
# parallel blocker columns. Neither expected grid calls the candidate solver.
LITERAL_INPUT = (
    "0000050000000",
    "0000111110000",
    "0000102010000",
    "0000100010000",
    "0050010100000",
    "0000100010000",
    "0001003001000",
    "0000000000000",
    "0000000004000",
    "0000000000000",
    "0000004000000",
    "0000000000000",
)
LITERAL_OPAQUE = (
    "0000050000000",
    "0000111110000",
    "0000122210000",
    "0000122210000",
    "0050012100000",
    "0000122210000",
    "0001223221000",
    "0002220222000",
    "0022220224200",
    "0222220220220",
    "2222224220222",
    "2222220220222",
)
LITERAL_TRANSPARENT = (
    "0000050000000",
    "0000111110000",
    "0000122210000",
    "0000122210000",
    "0050012100000",
    "0000122210000",
    "0001223221000",
    "0002222222000",
    "0022222224200",
    "0222222222220",
    "2222224222222",
    "2222222222222",
)


def decode(rows):
    return [[int(v) for v in row] for row in rows]


@pytest.mark.parametrize("mode, expected", [("opaque", LITERAL_OPAQUE), ("transparent", LITERAL_TRANSPARENT)])
def test_literal_parallel_shadows_preserve_markers_and_ignore_outside_decoys(native, mode, expected):
    grid = decode(LITERAL_INPUT)
    before = copy.deepcopy(grid)
    assert native.solve(grid, mode) == decode(expected)
    assert grid == before


def test_literal_plan_uses_first_reached_blocker_and_not_outside_colors(native):
    grid = decode(LITERAL_INPUT)
    state = native.plan(grid, "opaque")
    assert state["turns"] == 0
    assert (state["background"], state["wall_color"], state["fill_color"]) == (0, 1, 2)
    assert set(state["blockers"]) == {(6, 6), (8, 9), (10, 6)}
    assert state["frontiers"][6] == 6 and state["frontiers"][9] == 8
    assert (7, 6) in state["shadow"] and (9, 9) in state["shadow"]
    assert (0, 5) not in state["interior"] and (4, 2) not in state["interior"]
    assert (8, 2) in state["interior"] and (8, 2) not in state["shadow"]
    assert not native.plan(grid, "transparent")["shadow"]


def stride_two_fixture():
    grid = [[0] * 15 for _ in range(16)]
    for c in range(4, 11):
        grid[1][c] = 1
    rails = [(2, 4, 10), (3, 4, 10), (4, 5, 9), (5, 6, 8), (6, 6, 8),
             (7, 5, 9), (8, 5, 9), (9, 4, 10), (10, 4, 10)]
    for r, left, right in rails:
        grid[r][left] = grid[r][right] = 1
    grid[2][7] = 2
    return grid


def test_stride_two_phase_and_unpainted_virtual_edges(native):
    grid = stride_two_fixture()
    assert [record["stride"] for record in native.plan(grid)["endpoints"]] == [2, 2]
    out = native.solve(grid)
    assert out[11] == out[12] == [0] * 4 + [2] * 7 + [0] * 4
    assert out[13] == out[14] == [0] * 3 + [2] * 9 + [0] * 3
    assert out[15] == [0] * 2 + [2] * 11 + [0] * 2


def test_partial_terminal_runs_are_outside_the_domain(native):
    grid = stride_two_fixture()
    grid[10][4] = grid[10][10] = 0
    # Both tips now have one cell, so equality of left/right tips alone is not
    # enough: each must also match the preceding complete two-cell run.
    with pytest.raises(ValueError):
        native.plan(grid)


def transform(grid, turns, reflected):
    grid = [row[::-1] if reflected else row[:] for row in grid]
    for _ in range(turns):
        grid = [list(row) for row in zip(*grid[::-1])]
    return grid


@pytest.mark.parametrize("turns, reflected", [(t, r) for t in range(4) for r in (False, True)])
@pytest.mark.parametrize("mode, expected", [("opaque", LITERAL_OPAQUE), ("transparent", LITERAL_TRANSPARENT)])
def test_d4_and_palette_equivariance_on_literal_labels(native, turns, reflected, mode, expected):
    palette = {0: 7, 1: 0, 2: 9, 3: 4, 4: 2, 5: 3}
    def changed(rows):
        grid = [[palette[v] for v in row] for row in decode(rows)]
        return transform(grid, turns, reflected)
    assert native.solve(changed(LITERAL_INPUT), mode) == changed(expected)


@pytest.mark.parametrize("settings", [None, {}, [], {"obstacle_mode": True}, {"obstacle_mode": 1},
                                     {"obstacle_mode": "solid"}, {"obstacle_mode": "opaque", "extra": 1}])
def test_invalid_program_settings(native, settings):
    with pytest.raises(ValueError):
        native.program(settings)


@pytest.mark.parametrize("mode", [None, True, False, 1, "solid", {}])
def test_invalid_plan_mode(native, mode):
    with pytest.raises(ValueError):
        native.plan(decode(LITERAL_INPUT), mode)


@pytest.mark.parametrize("grid", [[], [[]], [[True]], [[10]], [[0], [0, 1]], [[1.0]],
                                  ((0, 1), (0, 2)), [[0] * 31], [[0]] * 31,
                                  [[0, 0, 1, 1, 2]], [[0, 0, 0, 1, 2]], [[0, 0, 0]]])
def test_invalid_grid_boundaries_and_role_frequency_ties(native, grid):
    with pytest.raises(ValueError):
        native.plan(grid)


def test_ambiguous_earliest_interior_dye_is_rejected(native):
    grid = decode(LITERAL_INPUT)
    grid[2][5] = 3
    with pytest.raises(ValueError):
        native.plan(grid)


def test_exact_canonical_resource_and_finite_parameter_contract(native):
    canonical = (HOME / "reference.rkt").read_bytes()
    assert (HOME / "workspace/parametric/canonical.rkt").read_bytes() == canonical
    assert native.program({"obstacle_mode": "opaque"}).encode() == canonical
    assert native.program({"obstacle_mode": "transparent"}) != native.CANONICAL
    assert native.PARAMETERS == {"obstacle_mode": ["opaque", "transparent"]}
    assert native.DEFAULT == {"obstacle_mode": "opaque"}
    assert native.LIMITS == {"demos": [2, 6], "queries": [1, 4]}
    assert native.solve(decode(LITERAL_INPUT)) == decode(LITERAL_OPAQUE)


def selected_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("selected_nozzle_generator_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_literal_registration_identity_and_normalized_rule_hash():
    tree = ast.parse((HOME / "generator.py").read_text())
    identities = [node.value.value for node in tree.body if isinstance(node, ast.Assign)
                  and any(isinstance(target, ast.Name) and target.id == "RULE_TASK_ID" for target in node.targets)
                  and isinstance(node.value, ast.Constant)]
    assert identities == ["ee_b9e38dc0"]
    program = " ".join((HOME / "reference.rkt").read_text().split())
    assert selected_generator().RULE_HASH == hashlib.sha256(program.encode()).hexdigest()[:12]


def test_adapter_contract_uses_minimum_lesson_and_adjacent_resources(native):
    folder = HOME / "workspace/parametric"
    contract = json.loads((folder / "promotion.json").read_text())
    assert contract["parameters"] == native.PARAMETERS
    assert contract["default"] == native.DEFAULT
    assert contract["limits"] == native.LIMITS
    assert contract["qualification_demos"] == 2
    assert (ROOT / contract["adapter"]).resolve() == (folder / "adapter.py").resolve()
    for resource in contract["resources"]:
        path = (ROOT / resource).resolve()
        assert path.is_file() and path.is_relative_to(folder.resolve())


@pytest.mark.parametrize("seed", [0, 17, 43])
def test_matched_parameter_inputs_deterministic_prefixes_and_freshness(native, seed):
    opaque = {"obstacle_mode": "opaque"}
    full = native.generate(seed, opaque, 6, 4)
    alternate = native.generate(seed, {"obstacle_mode": "transparent"}, 6, 4)
    assert full == native.generate(seed, opaque, 6, 4)
    pairs, other = full["train"] + full["test"], alternate["train"] + alternate["test"]
    assert [pair["input"] for pair in pairs] == [pair["input"] for pair in other]
    assert len({json.dumps(pair["input"]) for pair in pairs}) == 10
    assert all(a["output"] != b["output"] for a, b in zip(full["train"][:2], alternate["train"][:2]))
    assert full["program_solution"] == native.program(opaque)
    for demos, queries in ((2, 1), (3, 4), (6, 2)):
        short = native.generate(seed, opaque, demos, queries)
        assert short["train"] == full["train"][:demos]
        assert short["test"] == full["test"][:queries]
    ordinary = native.generate(seed, opaque)
    assert (len(ordinary["train"]), len(ordinary["test"])) == (3, 4)
    automatic = native.generate(seed)
    assert automatic == native.generate(seed)
    assert automatic["program_solution"] in {native.program({"obstacle_mode": mode}) for mode in ("opaque", "transparent")}
    pristine = copy.deepcopy(full)
    full["train"][0]["input"][0][0] = 99
    full["test"][0]["output"][0][0] = 99
    assert native.generate(seed, opaque, 6, 4) == pristine


@pytest.mark.parametrize("seed", [0, 15, 17])
def test_required_teaching_pair_changes_all_inferred_role_colors(native, seed):
    demos, _ = native.input_bank(seed)
    roles = [native.plan(grid) for grid in demos[:2]]
    for name in ("background", "wall_color", "fill_color"):
        assert roles[0][name] != roles[1][name], name


def test_required_teaching_pair_has_distinct_flow_directions(native):
    demos, _ = native.input_bank(1)
    flows = [native.plan(grid)["flow"] for grid in demos[:2]]
    assert flows[0] != flows[1], "The required demonstrations must teach distinct flow directions"


@pytest.mark.parametrize("seed", [0, 17, 43])
def test_large_profiles_have_long_walls_large_interiors_and_active_shadows(native, seed):
    demos, queries = native.input_bank(seed)
    large = [grid for grid in demos + queries if len(grid) == len(grid[0]) == 30]
    assert len(large) == 2 and large[0] != large[1]
    strides = set()
    for grid in large:
        state = native.plan(grid)
        assert len(state["wall_cells"]) >= 45
        assert len(state["interior"]) >= 240
        assert len(state["blockers"]) >= 6 and len(state["shadow"]) >= 40
        wall_rows = [r for r, c in state["wall_cells"]]
        assert max(wall_rows) - min(wall_rows) + 1 >= 18
        assert len(state["grid"]) - 1 - max(record["endpoint"][0] for record in state["endpoints"]) >= 5
        strides.add(state["endpoints"][0]["stride"])
    assert strides == {2, 3}


@pytest.mark.parametrize("kwargs", [{"seed": True}, {"seed": -1}, {"seed": 2**63},
                                    {"demos": 1}, {"demos": 7}, {"demos": 2.0},
                                    {"queries": 0}, {"queries": 5}, {"queries": False},
                                    {"settings": {}}, {"settings": {"obstacle_mode": True}}])
def test_invalid_episode_boundaries(native, kwargs):
    with pytest.raises(ValueError):
        native.generate(**{"seed": 17, **kwargs})


def test_query_presentation_order_varies(native):
    orders = {tuple(tuple(sorted((len(grid), len(grid[0])))) for grid in native.input_bank(seed)[1])
              for seed in range(5)}
    assert len(orders) > 1


def test_selected_generator_returns_lawful_deterministic_inputs():
    module = selected_generator()
    grid = module.generate(seed=17, sample_index=0, difficulty="hard")
    assert module.self_check(grid) == []
    assert grid == module.generate(seed=17, sample_index=0, difficulty="hard")
    assert grid != module.generate(seed=17, sample_index=1)
    assert module.self_check([[True]])
    with pytest.raises(ValueError):
        module.generate(seed=17, unknown=1)

