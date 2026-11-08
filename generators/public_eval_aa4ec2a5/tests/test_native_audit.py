"""Independent topology, rendering, isolation, and executable-rival tests."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import pytest

TASK = Path(__file__).resolve().parents[1]
HOME = TASK / "workspace/parametric"
ROOT = TASK.parents[1]


def rows(*values):
    return [[int(v) for v in row] for row in values]


APERTURE = rows("4444444", "4444444", "4441144", "4414144", "4411144", "4444444", "4444444")
APERTURE4 = rows("4444444", "4422224", "4228824", "4286824", "4288824", "4222224", "4444444")
APERTURE8 = rows("4444444", "4422224", "4221124", "4212124", "4211124", "4222224", "4444444")
LITERALS = [
    (rows("444", "414", "444"), rows("222", "212", "222")),
    (rows("114", "114", "444"), rows("112", "112", "222")),
    (rows("44444", "41114", "41444", "41114", "44444"), rows("22222", "21112", "21222", "21112", "22222")),
    (rows("44444444", "41111114", "41414444", "41114444", "44444444"),
     rows("22222222", "28888882", "28682222", "28882444", "22222444")),
    (rows("4444444", "4444444", "4414144", "4444444", "4444444"),
     rows("4444444", "4222224", "4212124", "4222224", "4444444")),
    (rows("4444444", "4111114", "4141414", "4111114", "4444444"),
     rows("2222222", "2888882", "2868682", "2888882", "2222222")),
]


def test_audit_module_exists():
    assert (HOME / "audit_native.py").is_file()


@pytest.fixture(scope="module")
def audit():
    spec = importlib.util.spec_from_file_location("_aa4ec2a5_independent_audit_test", HOME / "audit_native.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@pytest.fixture(scope="module")
def originals():
    base = ROOT / "shared/data/raw"
    task = json.loads((base / "arc-agi_evaluation_challenges.json").read_text())["aa4ec2a5"]
    gold = json.loads((base / "arc-agi_evaluation_solutions.json").read_text())["aa4ec2a5"]
    return task["train"] + [{"input": p["input"], "output": out} for p, out in zip(task["test"], gold)]


@pytest.fixture(scope="module")
def racket(audit):
    with audit._local_imports(audit.RUNTIME, audit.HOME):
        apply, identity, bridge = audit._real_evaluator(audit.RUNTIME)
        try:
            assert identity["backend"] == "racket" and identity["protected"] is True
            yield apply
        finally:
            bridge.close()


@pytest.mark.parametrize("index", range(4))
@pytest.mark.parametrize("connectivity", [4, 8])
def test_all_official_labels(audit, originals, index, connectivity):
    pair = originals[index]
    assert audit.reference(pair["input"], {"hole_connectivity": connectivity}) == pair["output"]


@pytest.mark.parametrize("pair", LITERALS)
@pytest.mark.parametrize("connectivity", [4, 8])
def test_literal_rendering(audit, pair, connectivity):
    assert audit.reference(pair[0], {"hole_connectivity": connectivity}) == pair[1]


def test_diagonal_aperture_changes_the_entire_object_class(audit):
    assert audit.reference(APERTURE, {"hole_connectivity": 4}) == APERTURE4
    assert audit.reference(APERTURE, {"hole_connectivity": 8}) == APERTURE8


def test_deep_cavity_center_is_filled(audit):
    grid = [[4] * 7 for _ in range(7)]
    for r in range(1, 6):
        for c in range(1, 6):
            if r in (1, 5) or c in (1, 5):
                grid[r][c] = 1
    actual = audit.reference(grid, {"hole_connectivity": 4})
    assert actual[3][3] == 6
    assert actual[1][1] == 8
    assert actual[0][0] == 2


def test_foreground_zero_and_changed_background(audit):
    grid = [[7 if v == 4 else 0 for v in row] for row in LITERALS[0][0]]
    assert audit.reference(grid, {"hole_connectivity": 4}) == rows("222", "202", "222")


@pytest.mark.parametrize("bg, fg", [(9, 4), (7, 4), (1, 5), (7, 0), (0, 7), (5, 3)])
@pytest.mark.parametrize("connectivity", [4, 8])
def test_learned_role_constants_have_complete_executable_semantics(audit, racket, bg, fg, connectivity):
    recolor = lambda grid: [[bg if v == 4 else fg if v == 1 else v for v in row] for row in grid]
    grid = recolor(APERTURE)
    expected = recolor(APERTURE4 if connectivity == 4 else APERTURE8)
    settings = {"hole_connectivity": connectivity}
    for name in (f"fixed_background{bg}", f"fixed_foreground{fg}"):
        assert audit.rival_reference(grid, settings, name) == expected
        assert racket(audit.rival_program(settings, name), grid) == expected
    absent = next(v for v in (0, 1, 3, 4, 5, 7, 9) if v not in (bg, fg))
    for name in (f"fixed_background{absent}", f"fixed_foreground{absent}"):
        assert audit.rival_reference(grid, settings, name) == grid
        assert racket(audit.rival_program(settings, name), grid) == grid


def test_learned_constants_read_only_demo0_input(audit):
    class Poison:
        def __getitem__(self, key):
            raise AssertionError("Read a label or a later demonstration")
    first = {"input": APERTURE, "output": Poison()}
    assert audit.learned_role_names([first, Poison()]) == ["fixed_background4", "fixed_foreground1"]


def test_excludes_diagonal_foreground_contacts(audit):
    with pytest.raises(ValueError):
        audit.scene(rows("4444", "4144", "4414", "4444"), 4)


@pytest.mark.parametrize("connectivity", [4, 8])
def test_excludes_nested_foreground_for_both_settings(audit, connectivity):
    grid = [[4] * 7 for _ in range(7)]
    for r in range(1, 6):
        for c in range(1, 6):
            if r in (1, 5) or c in (1, 5):
                grid[r][c] = 1
    grid[3][3] = 1
    with pytest.raises(ValueError):
        audit.scene(grid, connectivity)


@pytest.mark.parametrize("connectivity", [4, 8])
@pytest.mark.parametrize("name", [
    "reference", "identity", "invert_roles", "fixed_background4", "fixed_foreground1",
    "bbox_cavities", "global_bbox_cavities", "largest_component_only", "first_component_only",
    "largest_hole_only", "singleton_holes_only", "deep_hole_border_only", "outline4",
    "outline_radius2", "outline_bbox", "outline_holes_too", "no_outline", "no_fill",
    "no_recolor", "recolor_all", "recolor_near_holes", "only_holed_outline",
    "only_solid_outline", "swap_hole_body_colors", "fill_same_as_body", "crop_result",
])
def test_complete_racket_matches_independent_python(audit, racket, originals, connectivity, name):
    settings = {"hole_connectivity": connectivity}
    program = audit.rival_program(settings, name)
    for grid in [pair["input"] for pair in originals] + [APERTURE]:
        assert racket(program, deepcopy(grid)) == audit.rival_reference(grid, settings, name)


@pytest.mark.parametrize("connectivity", [4, 8])
def test_total_rivals_outside_the_admitted_geometry(audit, racket, connectivity):
    settings = {"hole_connectivity": connectivity}
    for name in ("reference", *audit.RIVALS):
        for grid in ([[0]], [[9]], [[1, 4], [4, 1]]):
            assert racket(audit.rival_program(settings, name), grid) == audit.rival_reference(grid, settings, name)


def test_fit_reads_only_two_demonstrations(audit):
    class Poison:
        def __getitem__(self, key):
            raise AssertionError("Read a later demonstration")
    calls = []
    def execute(program, grid):
        calls.append(grid)
        return grid
    pairs = [{"input": [[0]], "output": [[0]]}, {"input": [[1]], "output": [[1]]}, Poison()]
    fit = audit.fit_hypothesis(execute, "test", pairs)
    assert fit["survives_demonstrations"] and fit["executed_demo_indices"] == [0, 1]
    assert calls == [[[0]], [[1]]]


def test_execution_error_is_not_a_refutation(audit):
    def broken(program, grid):
        raise RuntimeError("deliberate failure")
    with pytest.raises(RuntimeError, match="deliberate failure"):
        audit.fit_hypothesis(broken, "bad", [{"input": [[0]], "output": [[0]]}] * 2)


@pytest.mark.parametrize("bad", [{}, {"hole_connectivity": True}, {"hole_connectivity": 4.0},
    {"hole_connectivity": 6}, {"hole_connectivity": 4, "extra": 0}])
def test_exact_setting_validation(audit, bad):
    with pytest.raises(ValueError):
        audit.setting(bad)
