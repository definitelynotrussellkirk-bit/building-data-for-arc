"""Independent literal and isolation controls for the finite native audit."""
import importlib.util
from pathlib import Path

import pytest

SOURCE = Path(__file__).parents[1] / "workspace/parametric/audit_native.py"


def test_audit_module_exists():
    assert SOURCE.is_file(), "independent native audit is not implemented"


@pytest.fixture(scope="module")
def audit():
    spec = importlib.util.spec_from_file_location("xor_independent_audit_tests", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scene(a, b, *, origins=((1, 1), (2, 8)), colors=(2, 3), h=9, w=14):
    grid = [[0] * w for _ in range(h)]
    for cells, (r0, c0), color in zip((a, b), origins, colors):
        for r, c in cells:
            assert grid[r + r0][c + c0] == 0
            grid[r + r0][c + c0] = color
    return grid


SQUARE = {(r, c) for r in range(4) for c in range(4)}
A = SQUARE - {(2, 1)}
B = SQUARE - {(1, 1)}
FRAME = scene(A, B)
UNEQUAL = scene({(0, 0), (1, 0), (1, 1)}, {(0, 0), (0, 1), (0, 2), (1, 0)},
                origins=((4, 6), (1, 1)))


@pytest.fixture(scope="module")
def racket(audit):
    with audit._local_imports(audit.RUNTIME, audit.HOME):
        apply, identity, bridge = audit._real_evaluator(audit.RUNTIME)
        assert identity["protected"] is True and identity["backend"] == "racket"
        try:
            yield apply
        finally:
            bridge.close()


@pytest.mark.parametrize("mode,expected", [
    ("xor", [[0, 0], [0, 8], [0, 8]]),
    ("difference", [[0, 0], [0, 8]]),
])
def test_independent_origin_and_trailing_frame_literals(audit, racket, mode, expected):
    assert audit.reference(FRAME, {"combine": mode}) == expected
    assert racket(audit.rival_program({"combine": mode}, "reference"), FRAME) == expected


@pytest.mark.parametrize("mode", ["xor", "difference"])
def test_empty_result_is_single_background_cell(audit, racket, mode):
    grid = [[2, 0, 3]]
    assert audit.reference(grid, {"combine": mode}) == [[0]]
    assert racket(audit.rival_program({"combine": mode}, "reference"), grid) == [[0]]


@pytest.mark.parametrize("mode", ["xor", "difference"])
@pytest.mark.parametrize("name", [
    "identity", "recrop_all", "recrop_rows", "recrop_cols", "union_frame",
    "union", "intersection", "reverse_operands", "observed_coordinates",
    "joint_normalize", "normalize_first_only", "normalize_second_only",
    "position_order", "area_order", "area_descending", "first_shape", "second_shape",
    "solid_box", "color2", "input_colors", "reflect_second", "rotate_second",
    "transpose_second", "bbox_shapes",
])
def test_each_complete_racket_rival_matches_independent_python(audit, racket, mode, name):
    settings = {"combine": mode}
    for grid in (FRAME, UNEQUAL):
        assert racket(audit.rival_program(settings, name), grid) == audit.rival_reference(grid, settings, name)


@pytest.mark.parametrize("mode", ["xor", "difference"])
def test_total_empty_and_single_component_controls(audit, racket, mode):
    settings = {"combine": mode}
    for grid in ([[0]], [[2, 2]]):
        for name in ("reference", *audit.RIVALS):
            assert racket(audit.rival_program(settings, name), grid) == audit.rival_reference(grid, settings, name)


def test_specific_shortcuts_have_distinct_literal_meanings(audit):
    settings = {"combine": "difference"}
    assert audit.rival_reference(FRAME, settings, "recrop_all") == [[8]]
    assert audit.rival_reference(FRAME, settings, "recrop_rows") == [[0, 8]]
    assert audit.rival_reference(FRAME, settings, "recrop_cols") == [[0], [8]]
    assert audit.rival_reference(FRAME, settings, "union_frame") == [[0] * 4, [0, 8, 0, 0], [0] * 4, [0] * 4]
    assert audit.rival_reference(FRAME, settings, "reverse_operands") == [[0, 0], [0, 0], [0, 8]]
    assert audit.rival_reference(FRAME, settings, "bbox_shapes") == [[0]]
    assert audit.rival_reference(UNEQUAL, settings, "position_order") != audit.reference(UNEQUAL, settings)
    assert audit.rival_reference(UNEQUAL, settings, "area_descending") != audit.reference(UNEQUAL, settings)


def test_commutativity_alias_is_explicit(audit):
    for name in ("reverse_operands", "position_order", "area_order", "area_descending"):
        assert name in audit.equivalent_aliases({"combine": "xor"})
        assert name not in audit.equivalent_aliases({"combine": "difference"})
        assert audit.rival_reference(UNEQUAL, {"combine": "xor"}, name) == audit.reference(UNEQUAL, {"combine": "xor"})


def test_fitting_never_reads_third_demo_or_query(audit):
    calls = []
    def evaluator(program, grid):
        calls.append(grid)
        return [[8]]
    demos = [{"input": [[2]], "output": [[8]]}, {"input": [[3]], "output": [[8]]}, object()]
    assert audit.fit_hypothesis(evaluator, "program", demos)["survives_demonstrations"]
    assert calls == [[[2]], [[3]]]


def test_candidate_error_is_not_a_refutation(audit):
    def fail(program, grid):
        raise RuntimeError("literal candidate failure")
    with pytest.raises(RuntimeError, match="literal candidate failure"):
        audit.fit_hypothesis(fail, "program", [{"input": [[2]], "output": [[0]]}] * 2)


def test_unknown_controls_rejected(audit):
    with pytest.raises(ValueError):
        audit.rival_program({"combine": "or"}, "identity")
    with pytest.raises(ValueError):
        audit.rival_reference([[0]], {"combine": "xor"}, "unknown")
