"""Independent semantic checks; no prototype or sampler imports are used here."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def _review_module():
    path = HOME / "rivals.py"
    assert path.is_file(), "the independent semantic reviewer has not been implemented"
    spec = importlib.util.spec_from_file_location("_033db13a9d37_independent_rivals", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_literal_first_canopy_is_inclusive_and_echo_uses_original_color():
    r = _review_module()
    grid = [[0, 0, 0, 0], [0, 0, 3, 0], [7, 0, 0, 0]]
    assert r.intended(grid, "first") == [[4, 0, 4, 0], [4, 0, 4, 0], [0, 0, 3, 0]]


def test_literal_relay_skips_wrong_parity_then_renders_the_selected_marker():
    r = _review_module()
    grid = [[0, 0, 3, 0, 0], [0, 5, 0, 0, 0], [0, 0, 0, 0, 8],
            [2, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
    assert r.intended(grid, "parity_relay") == [
        [4, 0, 4, 0, 4], [4, 0, 4, 0, 4], [4, 0, 4, 0, 4],
        [0, 0, 0, 0, 8], [0, 0, 0, 0, 0]]


def test_stage_b_consumes_the_supplied_mask_and_falls_back_to_origin():
    r = _review_module()
    grid = [[0, 7, 0], [2, 0, 0], [0, 3, 0], [0, 0, 0]]
    origin, mask = r.stage_a(grid)
    assert origin == (0, 1, 7)
    assert mask == [[0, 0, 0], [0, 1, 0], [0, 1, 0], [0, 1, 0]]
    assert r.stage_b(grid, origin, mask) == (2, 1, 3)
    wrong_parity = [[int(rr > 0 and cc % 2 == 0) for cc in range(3)] for rr in range(4)]
    assert r.stage_b(grid, origin, wrong_parity) == (1, 0, 2)
    assert r.stage_b(grid, origin, [[1] * 3 for _ in range(4)]) == origin
    assert r.stage_b(grid, origin, [[0] * 3 for _ in range(4)]) == origin
    expected = r.intended(grid, "parity_relay")
    assert r.bank("parity_relay")["opposite_lane_parity"](grid) != expected
    assert r.bank("parity_relay")["ignore_lane_mask"](grid) != expected


@pytest.mark.parametrize("mode", ["first", "parity_relay"])
def test_bottom_seed_and_one_cell_semantic_domain(mode):
    r = _review_module()
    assert r.intended([[9]], mode) == [[4]]
    assert r.intended([[0], [0], [5]], mode) == [[4], [4], [4]]
    assert r.intended([[0, 0, 8]], mode) == [[4, 0, 4]]


@pytest.mark.parametrize("bad", [
    None, [], [[]], ((1,),), [(1,)], [[1], [0, 0]], [[True]], [[1.0]],
    [[4]], [[10]], [[-1]], [[0]], [[1] * 31], [[1] for _ in range(31)],
])
def test_strict_semantic_domain_rejects_malformed_or_reserved_color(bad):
    with pytest.raises(ValueError):
        _review_module().intended(bad, "first")


@pytest.mark.parametrize("mode", ["last", "relay", None, True])
def test_unknown_mode_is_rejected(mode):
    with pytest.raises(ValueError):
        _review_module().intended([[1]], mode)


def test_fixtures_separate_all_named_rivals_and_do_not_contain_aliases():
    r = _review_module()
    grids = list(r.fixtures().values())
    assert any((len(g), len(g[0])) == (30, 30) for g in grids)
    assert any(sum(v != 0 for row in g for v in row) > 100 for g in grids)
    for mode in r.MODES:
        expected = tuple(str(r.intended(g, mode)) for g in grids)
        signatures = {}
        for name, rival in r.bank(mode).items():
            signature = tuple(str(rival(g)) for g in grids)
            assert signature != expected, (mode, name, "not refuted by fixtures")
            assert signature not in signatures, (mode, name, "alias", signatures.get(signature))
            signatures[signature] = name


def test_evaluation_is_pure_and_feature_summary_describes_actual_targets():
    r = _review_module()
    for name, grid in r.fixtures().items():
        original = deepcopy(grid)
        for mode in r.MODES:
            r.intended(grid, mode)
            for rival in r.bank(mode).values():
                rival(grid)
        feature = r.feature_summary(grid)
        assert feature["shape"] == [len(grid), len(grid[0])], name
        assert feature["markers"] == sum(v != 0 for row in grid for v in row), name
        assert feature["mode_changes_output"] == (r.intended(grid, "first") != r.intended(grid, "parity_relay"))
        assert grid == original, name


def test_racket_rules_are_complete_and_unknown_rivals_are_rejected():
    r = _review_module()
    for mode in r.MODES:
        for name in [None, *r.bank(mode)]:
            program = r.racket(mode, name)
            assert program.startswith("(rule! ")
            assert program.count("(") == program.count(")")
    with pytest.raises(ValueError):
        r.racket("first", "nonexistent")


def test_audit_stress_inputs_are_independent_large_and_semantically_valid():
    path = HOME / "audit.py"
    assert path.is_file(), "the bounded independent audit has not been implemented"
    spec = importlib.util.spec_from_file_location("_033db13a9d37_independent_audit", path)
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    grids = audit.stress_inputs()
    assert len(grids) == 32
    assert len({str(g) for g in grids}) == 32
    r = _review_module()
    for grid in grids:
        assert (len(grid), len(grid[0])) == (30, 30)
        r.validate_grid(grid)
    features = [r.feature_summary(grid) for grid in grids]
    assert sum(f["markers"] > 100 for f in features) >= 16
    assert any(f["origin_bottom"] for f in features)
    assert any(f["relay_active"] for f in features)
    assert any(f["relay_fallback"] for f in features)


def test_relay_direction_clipping_and_color_controls_have_literal_witnesses():
    r = _review_module()
    rivals = r.bank("parity_relay")
    active = r.fixtures()["odd_active"]
    for name in ("rightward_only", "target_min_color", "target_max_color"):
        assert name in rivals, "the independently confirmed relay control is missing"
        assert rivals[name](active) != r.intended(active, "parity_relay")
    bottom = r.fixtures()["bottom_target"]
    expected = r.intended(bottom, "parity_relay")
    assert expected == [[0, 4, 0, 4, 0, 4] for _ in range(5)]
    assert rivals["echo_visible_only"](bottom) != expected
    wrapped = deepcopy(expected)
    wrapped[0][1] = 9
    assert rivals["echo_wrap"](bottom) == wrapped
    clamped = deepcopy(expected)
    clamped[-1][1] = 9
    assert rivals["echo_clamp"](bottom) == clamped


def test_nearest_eligible_uses_euclidean_distance_and_row_major_ties():
    r = _review_module()
    rivals = r.bank("parity_relay")
    assert "nearest_eligible" in rivals, "the confirmed nearest-marker rival is missing"
    grid = [[3, 0, 0, 0, 0], [0, 0, 0, 0, 3], [0, 0, 3, 0, 0]]
    assert r.intended(grid, "parity_relay") == [
        [4, 0, 4, 0, 4], [4, 0, 4, 0, 4], [0, 0, 0, 0, 3]]
    assert rivals["nearest_eligible"](grid) == [[4, 0, 4, 0, 4] for _ in range(3)]
    tied = [[0, 0, 3, 0, 0], [7, 0, 0, 0, 8], [0, 0, 0, 0, 0]]
    assert rivals["nearest_eligible"](tied) == [
        [4, 0, 4, 0, 4], [4, 0, 4, 0, 4], [7, 0, 0, 0, 0]]
