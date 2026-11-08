"""Literal independent controls for D4 matching and transformation transfer."""
import importlib.util
from pathlib import Path
import pytest

SOURCE = Path(__file__).parents[1] / "workspace/parametric/audit_native.py"


def test_audit_exists():
    assert SOURCE.is_file(), "transfer audit has not been implemented"


@pytest.fixture(scope="module")
def audit():
    spec = importlib.util.spec_from_file_location("transfer_audit_tests", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def racket(audit):
    with audit._local_imports(audit.RUNTIME, audit.HOME):
        apply, identity, bridge = audit._real_evaluator(audit.RUNTIME)
        assert identity["protected"] is True and identity["backend"] == "racket"
        try:
            yield apply
        finally:
            bridge.close()


X = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 1))
Y = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0))
RX = ((0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 2))
MY = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 2))


def scene(shapes, colors=(2, 3, 4), tail=0):
    h, p = 8, 6
    grid = [[0] * (3 * p + 2 + tail) for _ in range(h)]
    for row in grid:
        row[p] = row[2 * p + 1] = 8
    for i, (cells, color) in enumerate(zip(shapes, colors)):
        for r, c in cells:
            grid[r + i + 1][i * (p + 1) + c + 1] = color
    return grid


ROTATION = scene((X, Y, RX), tail=1)
REFLECTION8 = scene((X, Y, MY), colors=(4, 6, 8), tail=2)


@pytest.mark.parametrize("mode,expected", [
    ("prototype", [[4, 4, 4], [4, 4, 0], [0, 4, 0]]),
    ("transfer", [[4, 4, 4], [0, 0, 4], [0, 4, 4]]),
])
def test_rot90_literal_outputs(audit, racket, mode, expected):
    settings = {"mode": mode}
    assert audit.reference(ROTATION, settings) == expected
    assert racket(audit.rival_program(settings, "reference"), ROTATION) == expected


def test_transform_codes_and_inverses(audit):
    assert audit.transform(X, "rot90") == tuple(sorted(RX))
    assert audit.transform(Y, "flip-h") == tuple(sorted(MY))
    assert len({audit.transform(X, name) for name in audit.NAMES}) == 8
    for name in audit.NAMES:
        assert audit.transform(audit.transform(X, name), audit.inverse(name)) == X


@pytest.mark.parametrize("mode", ["prototype", "transfer"])
@pytest.mark.parametrize("name", [
    "identity", "fixed_match0", "fixed_match1", "rotations_match0", "rotations_match1",
    "reflections_match0", "reflections_match1", "query_display", "other_display", "inverse_transfer",
    "fixed_rot90", "fixed_rot180", "fixed_rot270", "fixed_flip-h", "fixed_flip-v",
    "fixed_transpose", "fixed_anti-transpose", "prototype_color", "color8", "color2",
    "ignore_color8", "area_match0", "area_match1", "bbox_match0", "bbox_match1",
    "full_panel", "canonical_output",
])
def test_each_rival_matches_independent_python(audit, racket, mode, name):
    settings = {"mode": mode}
    for grid in (ROTATION, REFLECTION8):
        assert racket(audit.rival_program(settings, name), grid) == audit.rival_reference(grid, settings, name)


@pytest.mark.parametrize("mode", ["prototype", "transfer"])
def test_total_blank_small_and_missing_panel_support(audit, racket, mode):
    settings = {"mode": mode}
    for grid in ([[0]], [[0] * 8], [[2, 8, 3, 8, 0]]):
        for name in ("reference", *audit.RIVALS):
            assert racket(audit.rival_program(settings, name), grid) == audit.rival_reference(grid, settings, name)


def test_color8_is_real_query_support(audit):
    for mode in ("prototype", "transfer"):
        correct = audit.reference(REFLECTION8, {"mode": mode})
        assert any(8 in row for row in correct)
        assert audit.rival_reference(REFLECTION8, {"mode": mode}, "ignore_color8") != correct


def test_transfer_is_not_query_or_other_display(audit):
    settings = {"mode": "transfer"}
    correct = audit.reference(ROTATION, settings)
    for name in ("query_display", "other_display", "inverse_transfer", "canonical_output"):
        assert audit.rival_reference(ROTATION, settings, name) != correct


def test_four_demo_fitting_ignores_later_labels(audit):
    calls = []
    def evaluate(program, grid):
        calls.append(grid)
        return [[8]]
    demos = [{"input": [[i]], "output": [[8]]} for i in (2, 3, 4, 5)] + [object()]
    assert audit.fit_hypothesis(evaluate, "program", demos)["survives_demonstrations"]
    assert calls == [[[2]], [[3]], [[4]], [[5]]]


def test_candidate_error_is_not_refutation(audit):
    def fail(program, grid):
        raise RuntimeError("candidate failed")
    with pytest.raises(RuntimeError, match="candidate failed"):
        audit.fit_hypothesis(fail, "program", [{"input": [[2]], "output": [[0]]}] * 4)


def test_unknown_controls_rejected(audit):
    with pytest.raises(ValueError):
        audit.rival_program({"mode": "bad"}, "identity")
    with pytest.raises(ValueError):
        audit.rival_reference([[0]], {"mode": "transfer"}, "unknown")
