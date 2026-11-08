"""Independent literal controls for D4 grouping, selection and output pose."""
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/audit_native.py"


@pytest.fixture(scope="module")
def audit():
    assert PATH.is_file(), "The independent polyomino audit is missing"
    spec = spec_from_file_location("_polyomino_native_audit_tests", PATH)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scene(h, w, objects):
    grid = [[0] * w for _ in range(h)]
    for cells, (top, left) in objects:
        for r, c in cells:
            grid[top + r][left + c] = 2
    return grid


F = ((0, 1), (0, 2), (1, 0), (1, 1), (2, 1))
MF = ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1))
P180 = ((0, 1), (1, 0), (1, 1), (2, 0), (2, 1))
T = ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1))
F_CANONICAL = [[8, 8, 0], [0, 8, 8], [0, 8, 0]]
F_OBSERVED = [[0, 8, 8], [8, 8, 0], [0, 8, 0]]
P_CANONICAL = [[8, 8, 8], [8, 8, 0]]
P_OBSERVED = [[0, 8], [8, 8], [8, 8]]
CHIRAL = scene(9, 10, [(F, (0, 0)), (MF, (0, 5)), (P180, (5, 0))])
MIDDLE = scene(9, 10, [(F, (0, 0)), (P180, (0, 5)), (MF, (5, 0))])
SAME_BBOX = scene(9, 10, [(F, (0, 0)), (MF, (0, 5)), (T, (5, 0))])
F_RARE = scene(6, 8, [(F, (0, 0)), (((0, 0),), (5, 0)), (((0, 0),), (5, 3))])
DIAGONAL_TOUCH = [[2, 0, 0, 0, 2], [0, 2, 0, 0, 2],
                  [0, 0, 0, 0, 0], [2, 0, 0, 0, 0]]

# The third pair "(0 10)" precedes "(0 2)" as decimal text, despite 10 > 2.
# Two monominoes make this a lawful (2 common, 1 rare) three-object input.
STRING_WITNESS = [[2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0],
                  [2, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                  [2, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0]]
STRING_MASK = [[8, 8, 0, 0, 0, 0, 0, 0, 0, 0, 8],
               [0, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8]]
NUMERIC_MASK = [[8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 0],
                [8, 0, 0, 0, 0, 0, 0, 0, 0, 8, 8]]


CASES = [
    ("canonical", "reference", CHIRAL, P_CANONICAL),
    ("observed", "reference", CHIRAL, P_OBSERVED),
    ("canonical", "reference", SAME_BBOX, [[8, 8, 8], [0, 8, 0], [0, 8, 0]]),
    ("canonical", "reference", STRING_WITNESS, STRING_MASK),
    ("observed", "reference", STRING_WITNESS, NUMERIC_MASK),
    ("canonical", "identity", [[2, 0, 2, 0, 2, 2]], [[2, 0, 2, 0, 2, 2]]),
    ("canonical", "rotation_group", CHIRAL, F_CANONICAL),
    ("canonical", "translation_group", CHIRAL, F_CANONICAL),
    ("canonical", "area_group", CHIRAL, F_CANONICAL),
    ("canonical", "bbox_group", SAME_BBOX, F_CANONICAL),
    ("canonical", "common_class", CHIRAL, F_CANONICAL),
    ("canonical", "smallest_area", CHIRAL, F_CANONICAL),
    ("canonical", "largest_area", CHIRAL, F_CANONICAL),
    ("canonical", "smallest_bbox", SAME_BBOX, F_CANONICAL),
    ("canonical", "largest_bbox", CHIRAL, F_CANONICAL),
    ("canonical", "first", CHIRAL, F_CANONICAL),
    ("canonical", "middle", CHIRAL, F_CANONICAL),
    ("canonical", "last", MIDDLE, F_CANONICAL),
    ("canonical", "leftmost", CHIRAL, F_CANONICAL),
    ("canonical", "rightmost", CHIRAL, F_CANONICAL),
    ("canonical", "connectivity8", DIAGONAL_TOUCH, [[8, 0], [0, 8]]),
    ("canonical", "reference", DIAGONAL_TOUCH, [[8, 8]]),
    ("canonical", "choose_F", CHIRAL, F_CANONICAL),
    ("canonical", "choose_P", SAME_BBOX, F_CANONICAL),
    ("canonical", "rotation_output", F_RARE, [[8, 0, 0], [8, 8, 8], [0, 8, 0]]),
    ("canonical", "numeric_output", STRING_WITNESS, NUMERIC_MASK),
    ("canonical", "solid_box", CHIRAL, [[8, 8, 8], [8, 8, 8]]),
    ("observed", "solid_box", CHIRAL, [[8, 8], [8, 8], [8, 8]]),
    ("canonical", "color2", CHIRAL, [[2, 2, 2], [2, 2, 0]]),
    ("observed", "fixed_r90", F_RARE, [[0, 8, 0], [8, 8, 8], [0, 0, 8]]),
    ("observed", "fixed_r180", F_RARE, [[0, 8, 0], [0, 8, 8], [8, 8, 0]]),
    ("observed", "fixed_r270", F_RARE, [[8, 0, 0], [8, 8, 8], [0, 8, 0]]),
    ("observed", "fixed_m0", F_RARE, F_CANONICAL),
    ("observed", "fixed_m90", F_RARE, [[0, 0, 8], [8, 8, 8], [0, 8, 0]]),
    ("observed", "fixed_m180", F_RARE, [[0, 8, 0], [8, 8, 0], [0, 8, 8]]),
    ("observed", "fixed_m270", F_RARE, [[0, 8, 0], [8, 8, 8], [8, 0, 0]]),
]


@pytest.mark.parametrize("pose,name,grid,want", CASES)
def test_python_meanings_against_literal_outputs(audit, pose, name, grid, want):
    original = deepcopy(grid)
    assert audit.rival_reference(grid, {"pose": pose}, name) == want
    assert grid == original


@pytest.fixture(scope="module")
def protected(audit):
    with audit._local_imports(audit.RUNTIME, audit.HOME):
        apply, identity, bridge = audit._real_evaluator(audit.RUNTIME)
        assert identity["backend"] == "racket" and identity["protected"] is True
        try:
            yield apply
        finally:
            bridge.close()


@pytest.mark.parametrize("pose,name,grid,want", CASES)
def test_protected_racket_meanings_against_literal_outputs(audit, protected, pose, name, grid, want):
    assert protected(audit.rival_program({"pose": pose}, name), grid) == want


def test_racket_shape_key_sorts_coordinates_numerically_before_formatting(audit):
    assert audit.shape_key(((7, 12), (7, 4), (7, 2))) == "((0 0) (0 2) (0 10))"


def test_all_extra_rivals_have_a_literal_control(audit):
    assert set(audit.RIVALS) <= {case[1] for case in CASES}


@pytest.mark.parametrize("pose", ["canonical", "observed"])
def test_every_rival_is_total_on_empty_red_and_thin_arc_grids(audit, protected, pose):
    for name in ("reference", *audit.RIVALS):
        for grid in ([[0]], [[0] * 30], [[0] for _ in range(30)]):
            expected = grid if name == "identity" else [[0]]
            assert audit.rival_reference(grid, {"pose": pose}, name) == expected
            assert protected(audit.rival_program({"pose": pose}, name), grid) == expected
        expected = [[2]] if name in {"identity", "color2"} else [[8]]
        assert audit.rival_reference([[2]], {"pose": pose}, name) == expected
        assert protected(audit.rival_program({"pose": pose}, name), [[2]]) == expected


@pytest.mark.parametrize("bad", [[], [[]], [[True]], [[1.0]], [[10]], [[-1]], [[0], [0, 1]], [[0] * 31]])
def test_oracle_rejects_invalid_arc_values(audit, bad):
    with pytest.raises(ValueError):
        audit.reference(bad, {"pose": "canonical"})


@pytest.mark.parametrize("bad", [{}, {"pose": False}, {"pose": "numeric"}, {"pose": "observed", "extra": 1}])
def test_oracle_rejects_undeclared_pose_settings(audit, bad):
    with pytest.raises(ValueError):
        audit.reference([[2]], bad)


def test_fit_uses_only_first_two_demonstrations(audit, protected):
    train = [{"input": [[1]], "output": [[1]]}, {"input": [[2]], "output": [[2]]},
             {"input": [[3]], "output": [[4]]}]
    fit = audit.fit_hypothesis(protected, audit.rival_program({"pose": "canonical"}, "identity"), train, lambda g: g)
    assert fit["survives_demonstrations"] is True
    assert fit["executed_demo_indices"] == [0, 1]


def test_racket_python_disagreement_is_an_error_not_a_refutation(audit, protected):
    with pytest.raises(ValueError, match="meaning mismatch"):
        audit.fit_hypothesis(protected, audit.rival_program({"pose": "canonical"}, "identity"),
                             [{"input": [[1]], "output": [[1]]}] * 2, lambda g: [[2]])


def test_execution_error_is_never_a_refutation(audit):
    def fail(program, grid):
        raise RuntimeError("controlled execution error")
    with pytest.raises(RuntimeError, match="controlled execution error"):
        audit.fit_hypothesis(fail, "p", [{"input": [[1]], "output": [[1]]}] * 2)


def test_cache_preserves_exact_arguments_and_output_isolation(audit):
    calls = []
    def apply(program, grid):
        calls.append((program, deepcopy(grid)))
        return grid
    cached = audit.CachedEvaluator(apply)
    result = cached("a", [[1]])
    result[0][0] = 9
    assert cached("a", [[1]]) == [[1]]
    assert cached("b", [[1]]) == [[1]]
    assert cached("a", [[2]]) == [[2]]
    assert calls == [("a", [[1]]), ("b", [[1]]), ("a", [[2]])]
    assert (cached.requests, cached.evaluations, cached.cache_hits) == (4, 3, 1)


def test_existing_output_cannot_be_overwritten(audit, tmp_path):
    marker = tmp_path / "retained.txt"
    marker.write_text("keep")
    with pytest.raises(FileExistsError):
        audit.run(tmp_path)
    assert marker.read_text() == "keep"
