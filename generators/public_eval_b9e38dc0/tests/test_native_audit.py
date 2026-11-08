"""Literal nozzle geometry, blocker semantics, and demonstration isolation."""
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


# Hand-derived stride-one nozzle with a narrowed throat, two blocker colors,
# an off-band side marker, and two markers behind the closed cap.
NOZZLE = rows(
    "0000000990000", "0000555550000", "0005022005000", "0000500050000",
    "0000050500000", "0030500050000", "0005007005000", "0000000000000",
    "0000900000000", "0000000000000")
OPAQUE = rows(
    "0000000990000", "0000555550000", "0005222225000", "0000522250000",
    "0000052500000", "0030522250000", "0005227225000", "0002220222000",
    "0022920222200", "0222020222220")
TRANSPARENT = rows(
    "0000000990000", "0000555550000", "0005222225000", "0000522250000",
    "0000052500000", "0030522250000", "0005227225000", "0002222222000",
    "0022922222200", "0222222222220")


def test_independent_audit_exists():
    assert (HOME / "audit_native.py").is_file()


@pytest.fixture(scope="module")
def audit():
    spec = importlib.util.spec_from_file_location("_b9e38dc0_independent_audit_test", HOME / "audit_native.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@pytest.fixture(scope="module")
def originals():
    raw = ROOT / "shared/data/raw"
    task = json.loads((raw / "arc-agi_evaluation_challenges.json").read_text())["b9e38dc0"]
    gold = json.loads((raw / "arc-agi_evaluation_solutions.json").read_text())["b9e38dc0"]
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
def test_official_opaque_gold(audit, originals, index):
    pair = originals[index]
    assert audit.reference(pair["input"], {"obstacle_mode": "opaque"}) == pair["output"]


@pytest.mark.parametrize("mode,expected", [("opaque", OPAQUE), ("transparent", TRANSPARENT)])
@pytest.mark.parametrize("turns", range(4))
def test_literal_geometry_and_axis_shadows(audit, mode, expected, turns):
    grid, want = deepcopy(NOZZLE), deepcopy(expected)
    for _ in range(turns):
        grid = [list(row) for row in zip(*grid[::-1])]
        want = [list(row) for row in zip(*want[::-1])]
    before = deepcopy(grid)
    assert audit.reference(grid, {"obstacle_mode": mode}) == want
    assert grid == before


def test_outside_markers_do_not_shadow_later_band_entry(audit):
    actual = audit.reference(NOZZLE, {"obstacle_mode": "opaque"})
    assert actual[9][2] == 2  # Side marker at (5,2) was never in the band.
    assert actual[9][7] == 2  # Behind-cap markers at (0,7..8) are irrelevant.
    assert actual[9][6] == 0  # In-band blocker at (6,6) does cast a shadow.
    assert actual[9][4] == 0  # Different-color blocker at (8,4) also casts one.


def test_two_step_cadence_continues_beyond_flat_final_pixel_step(audit, originals):
    state = audit.scene(originals[2]["input"])
    assert [r["stride"] for r in state["records"]] == [2, 2]
    actual = audit.reference(originals[2]["input"], {"obstacle_mode": "opaque"})
    assert actual[0][3] == 3 and actual[0][2] == 7
    assert actual[0][9] == 3  # Foreign8 behind the cap must not shadow this ray.


def test_independently_clipped_mouth_tips(audit, originals):
    state = audit.scene(originals[1]["input"])
    assert state["records"][0]["endpoint"][0] != state["records"][1]["endpoint"][0]
    actual = audit.reference(originals[1]["input"], {"obstacle_mode": "opaque"})
    assert actual[0][:6] == [4, 4, 4, 4, 4, 0]


@pytest.mark.parametrize("mode", ["opaque", "transparent"])
def test_arbitrary_palette_including_zero_dye(audit, mode):
    palette = [7, 1, 0, 3, 4, 6, 5, 8, 9, 2]
    recolor = lambda g: [[palette[v] for v in row] for row in g]
    want = OPAQUE if mode == "opaque" else TRANSPARENT
    assert audit.reference(recolor(NOZZLE), {"obstacle_mode": mode}) == recolor(want)


def test_partial_terminal_run_is_outside_the_shared_domain(audit, originals):
    grid = deepcopy(originals[2]["input"])
    grid[3][4] = 7
    with pytest.raises(ValueError):
        audit.scene(grid)


def test_different_colors_on_first_marker_row_are_ambiguous(audit):
    grid = deepcopy(NOZZLE)
    grid[2][5] = 3
    with pytest.raises(ValueError):
        audit.scene(grid)


@pytest.mark.parametrize("mode", ["opaque", "transparent"])
@pytest.mark.parametrize("name", [
    "reference", "identity", "body_only", "outlet_only", "stride1", "stride2",
    "freeze_rails", "include_virtual_rails", "symmetric_mouth_only", "largest_dye",
    "minimum_dye", "first_scan_dye", "global_shadows", "wall_shadows",
    "whole_cross_section_shadow", "slanted_shadows", "backward_shadows",
    "overwrite_blockers", "one_blocker_color", "source_as_blocker", "crop_result",
])
def test_complete_racket_meaning_matches_independent_python(audit, racket, originals, mode, name):
    settings = {"obstacle_mode": mode}
    program = audit.rival_program(settings, name)
    for grid in (NOZZLE, originals[1]["input"], originals[2]["input"]):
        assert racket(program, deepcopy(grid)) == audit.rival_reference(grid, settings, name)


@pytest.mark.parametrize("mode", ["opaque", "transparent"])
def test_total_candidate_outputs_outside_nozzle_domain(audit, racket, mode):
    settings = {"obstacle_mode": mode}
    for name in ("reference", *audit.RIVALS):
        for grid in ([[0]], [[1, 2], [3, 4]]):
            assert racket(audit.rival_program(settings, name), grid) == grid


@pytest.mark.parametrize("mode", ["opaque", "transparent"])
def test_learned_constants_guard_actual_role_and_are_executable(audit, racket, mode):
    settings = {"obstacle_mode": mode}
    expected = OPAQUE if mode == "opaque" else TRANSPARENT
    for name in ("fixed_background0", "fixed_wall5", "fixed_dye2"):
        assert audit.rival_reference(NOZZLE, settings, name) == expected
        assert racket(audit.rival_program(settings, name), NOZZLE) == expected
    for name in ("fixed_background5", "fixed_wall2", "fixed_dye0"):
        assert audit.rival_reference(NOZZLE, settings, name) == NOZZLE
        assert racket(audit.rival_program(settings, name), NOZZLE) == NOZZLE


@pytest.mark.parametrize("mode", ["opaque", "transparent"])
@pytest.mark.parametrize("turns", range(4))
def test_learned_flow_constant_has_complete_executable_semantics(audit, racket, mode, turns):
    grid = deepcopy(NOZZLE)
    expected = deepcopy(OPAQUE if mode == "opaque" else TRANSPARENT)
    for _ in range(turns):
        grid = [list(row) for row in zip(*grid[::-1])]
        expected = [list(row) for row in zip(*expected[::-1])]
    normalization = (-turns) % 4
    settings = {"obstacle_mode": mode}
    matches = f"fixed_flow{normalization}"
    wrong = f"fixed_flow{(normalization + 1) % 4}"
    assert audit.rival_reference(grid, settings, matches) == expected
    assert racket(audit.rival_program(settings, matches), grid) == expected
    assert audit.rival_reference(grid, settings, wrong) == grid
    assert racket(audit.rival_program(settings, wrong), grid) == grid


def test_role_learning_reads_only_first_demonstration_input(audit):
    class Poison:
        def __getitem__(self, key):
            raise AssertionError("Read a label or later example")
    assert audit.learned_role_names([{"input": NOZZLE, "output": Poison()}, Poison()]) == [
        "fixed_background0", "fixed_wall5", "fixed_dye2", "fixed_flow0"]


def test_fit_uses_only_first_two_demonstrations(audit):
    class Poison:
        def __getitem__(self, key):
            raise AssertionError("Read a later example")
    calls = []
    def identity(program, grid):
        calls.append(deepcopy(grid))
        return grid
    pairs = [{"input": [[0]], "output": [[0]]}, {"input": [[1]], "output": [[1]]}, Poison()]
    fitted = audit.fit_hypothesis(identity, "identity", pairs)
    assert fitted["survives_demonstrations"] and fitted["executed_demo_indices"] == [0, 1]
    assert calls == [[[0]], [[1]]]


def test_execution_error_is_not_refutation(audit):
    def broken(program, grid):
        raise RuntimeError("deliberate execution failure")
    with pytest.raises(RuntimeError, match="deliberate execution failure"):
        audit.fit_hypothesis(broken, "bad", [{"input": [[0]], "output": [[0]]}] * 2)


@pytest.mark.parametrize("bad", [{}, {"obstacle_mode": True}, {"obstacle_mode": 1},
    {"obstacle_mode": "other"}, {"obstacle_mode": "opaque", "extra": 0}])
def test_setting_validation(audit, bad):
    with pytest.raises(ValueError):
        audit.setting(bad)
