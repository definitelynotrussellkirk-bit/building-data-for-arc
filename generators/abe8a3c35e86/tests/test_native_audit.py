"""Independent reflection literals, clipping controls and four-demo isolation."""
import importlib.util
from pathlib import Path
import pytest

SOURCE = Path(__file__).parents[1] / "workspace/parametric/audit_native.py"


def test_audit_module_exists():
    assert SOURCE.is_file(), "independent reflection audit is not implemented"


@pytest.fixture(scope="module")
def audit():
    spec = importlib.util.spec_from_file_location("reflection_independent_audit", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def racket(audit):
    with audit._local_imports(audit.RUNTIME, audit.HOME):
        apply, identity, bridge = audit._real_evaluator(audit.RUNTIME)
        assert identity["protected"] and identity["backend"] == "racket"
        try:
            yield apply
        finally:
            bridge.close()


def scene(h, w, pivot, cells):
    g = [[0] * w for _ in range(h)]
    g[pivot[0]][pivot[1]] = 9
    for r, c, color in cells:
        g[r][c] = color
    return g


QCELLS = [(1, 2, 2), (1, 3, 3), (2, 2, 4)]
Q = scene(7, 9, (3, 4), QCELLS)
CLIPCELLS = [(0, 2, 2), (1, 2, 3), (1, 3, 4), (2, 4, 5)]
CLIP = scene(6, 7, (3, 1), CLIPCELLS)
BLOCKED = scene(7, 9, (4, 1), [(1, 4, 2), (2, 4, 3), (2, 5, 4)])
ROW = scene(7, 9, (4, 4), [(1, 2, 2), (1, 5, 3), (2, 5, 3)])
COLUMN = scene(7, 9, (3, 4), [(1, 1, 2), (3, 2, 3), (4, 1, 4)])
NEITHER = scene(7, 9, (3, 4), [(1, 2, 2), (4, 5, 3)])
RIVALS = (
    "identity", "row_priority", "column_only", "row_only", "always_column", "always_row",
    "else_row", "else_column", "both_original", "geometric_fourfold", "rotate180",
    "global_center", "center_row", "center_col", "pivot_plus_row", "pivot_plus_col",
    "per_color", "per_component", "largest_component_only", "fixed_copies2", "first_color_copies",
    "drop_pivot", "move_copy", "reject_clipped", "wrap", "clamp", "erase_clipped_sources", "crop_result",
)


@pytest.mark.parametrize("passes", [1, 2])
def test_literal_quadrant_state_changes_selected_axis(audit, racket, passes):
    cells = QCELLS + [(1, 6, 2), (1, 5, 3), (2, 6, 4)]
    if passes == 2:
        cells += [(5, 2, 2), (5, 3, 3), (4, 2, 4), (5, 6, 2), (5, 5, 3), (4, 6, 4)]
    expected = scene(7, 9, (3, 4), cells)
    assert audit.reference(Q, {"passes": passes}) == expected
    assert racket(audit.rival_program({"passes": passes}, "reference"), Q) == expected


def test_literal_partial_clipping_keeps_sources(audit, racket):
    expected = scene(6, 7, (3, 1), CLIPCELLS + [(0, 0, 2), (1, 0, 3),
        (5, 0, 3), (5, 2, 3), (5, 3, 4), (4, 4, 5)])
    assert audit.reference(CLIP, {"passes": 2}) == expected
    assert racket(audit.rival_program({"passes": 2}, "reference"), CLIP) == expected


def test_fully_clipped_first_axis_is_not_direct_fourfold(audit, racket):
    for passes in (1, 2):
        settings = {"passes": passes}
        assert audit.reference(BLOCKED, settings) == BLOCKED
        assert racket(audit.rival_program(settings, "reference"), BLOCKED) == BLOCKED
        assert audit.rival_reference(BLOCKED, settings, "row_priority") != BLOCKED
        assert audit.rival_reference(BLOCKED, settings, "geometric_fourfold") != BLOCKED


@pytest.mark.parametrize("passes", [1, 2])
@pytest.mark.parametrize("name", RIVALS)
def test_complete_candidate_matches_independent_python(audit, racket, passes, name):
    settings = {"passes": passes}
    for g in (Q, CLIP, BLOCKED, NEITHER):
        assert racket(audit.rival_program(settings, name), g) == audit.rival_reference(g, settings, name)


@pytest.mark.parametrize("passes", [1, 2])
def test_candidate_totality_no_pivot_singleton_and_multiple_pivots(audit, racket, passes):
    settings = {"passes": passes}
    for g in ([[0]], [[9]], [[9, 2, 9]]):
        for name in ("reference", *audit.RIVALS):
            assert racket(audit.rival_program(settings, name), g) == audit.rival_reference(g, settings, name)


def test_three_demo_else_row_hole_is_repaired_by_fourth(audit, racket):
    settings = {"passes": 2}
    intended = audit.rival_program(settings, "reference")
    rival = audit.rival_program(settings, "else_row")
    for g in (CLIP, BLOCKED, ROW):
        assert racket(intended, g) == racket(rival, g)
    assert racket(intended, COLUMN) != racket(rival, COLUMN)
    assert racket(intended, NEITHER) != racket(rival, NEITHER)


def test_fit_reads_exactly_four_demos(audit):
    calls = []
    def apply(program, grid):
        calls.append(grid)
        return [[8]]
    demos = [{"input": [[v]], "output": [[8]]} for v in (1, 2, 3, 4)] + [object()]
    assert audit.fit_hypothesis(apply, "program", demos)["survives_demonstrations"]
    assert calls == [[[1]], [[2]], [[3]], [[4]]]


def test_errors_are_not_refutations(audit):
    def apply(program, grid):
        raise RuntimeError("candidate unavailable")
    with pytest.raises(RuntimeError, match="candidate unavailable"):
        audit.fit_hypothesis(apply, "program", [{"input": [[9]], "output": [[9]]}] * 4)


@pytest.mark.parametrize("settings", [{"passes": True}, {"passes": 1.0}, {"passes": 3}, {"passes": "2"}, {}])
def test_exact_settings(audit, settings):
    with pytest.raises(ValueError):
        audit.rival_program(settings, "identity")
