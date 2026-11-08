"""Independent geometry/orientation and executable-rival checks."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import pytest

TASK = Path(__file__).resolve().parents[1]
HOME = TASK / "workspace/parametric"
ROOT = TASK.parents[1]


def test_audit_module_exists():
    assert (HOME / "audit_native.py").is_file()


@pytest.fixture(scope="module")
def audit():
    spec = importlib.util.spec_from_file_location("_a25697e4_independent_audit_test", HOME / "audit_native.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@pytest.fixture(scope="module")
def originals():
    base = ROOT / "shared/data/raw"
    challenge = json.loads((base / "arc-agi_evaluation_challenges.json").read_text())["a25697e4"]
    gold = json.loads((base / "arc-agi_evaluation_solutions.json").read_text())["a25697e4"]
    return challenge["train"] + [{"input": item["input"], "output": output}
        for item, output in zip(challenge["test"], gold)]


@pytest.fixture(scope="module")
def racket(audit):
    with audit._local_imports(audit.RUNTIME, audit.HOME):
        apply, identity, bridge = audit._real_evaluator(audit.RUNTIME)
        try:
            assert identity["backend"] == "racket" and identity["protected"] is True
            yield apply
        finally:
            bridge.close()


@pytest.mark.parametrize("index", range(5))
def test_all_original_labels_independent_python(audit, originals, index):
    pair = originals[index]
    assert audit.reference(pair["input"], {"reflection_colors": "swap"}) == pair["output"]


def test_reflection_swaps_both_region_colors(audit, originals):
    pair = originals[0]
    expected = [[4 if v == 3 else 3 if v == 4 else v for v in row] for row in pair["output"]]
    assert audit.reference(pair["input"], {"reflection_colors": "preserve"}) == expected


@pytest.mark.parametrize("index", [1, 2])
def test_proper_transform_preserves_colors(audit, originals, index):
    pair = originals[index]
    assert audit.reference(pair["input"], {"reflection_colors": "preserve"}) == pair["output"]


def test_reflection_and_rotation_have_distinct_parity(audit):
    assert [audit.transformed((2, 3), k) for k in range(8)] == [
        (2, 3), (3, -2), (-2, -3), (-3, 2),
        (2, -3), (-3, -2), (-2, 3), (3, 2)]


def test_matching_half_alone_does_not_resolve_tail_collision(audit, originals):
    pair = originals[2]
    proper = audit.rival_reference(pair["input"], {"reflection_colors": "swap"}, "reference")
    assert proper == pair["output"]
    info = audit.scene(pair["input"])
    legal = audit.candidates(pair["input"], info)
    relaxed = audit.candidates(pair["input"], info, name="ignore_collision")
    assert len(relaxed) > len(legal)


@pytest.mark.parametrize("setting", ["swap", "preserve"])
@pytest.mark.parametrize("name", [
    "reference", "identity", "rotations_only", "reflections_only", "translation_only",
    "global_color_sockets", "component_sockets", "fixed_background0", "fixed_background1",
    "ignore_collision", "ignore_bounds", "always_swap", "swap_proper", "swap_odd_turns",
    "swap_by_color_order", "matching_half_only", "tail_only", "copy_sources",
    "first_key_only", "largest_key_only", "first_socket_only", "paint_plug_anchor",
    "paint_all_anchor", "paint_all_part", "paint_all_other",
])
def test_complete_racket_candidate_matches_python(audit, racket, originals, setting, name):
    settings = {"reflection_colors": setting}
    program = audit.rival_program(settings, name)
    for pair in originals:
        expected = audit.rival_reference(pair["input"], settings, name)
        assert racket(program, deepcopy(pair["input"])) == expected


@pytest.mark.parametrize("setting", ["swap", "preserve"])
def test_wrong_programs_are_total_on_small_valid_arc_grids(audit, racket, setting):
    for name in ("reference", *audit.RIVALS):
        for grid in ([[0]], [[9]], [[0, 1], [2, 3]]):
            settings = {"reflection_colors": setting}
            assert racket(audit.rival_program(settings, name), grid) == audit.rival_reference(grid, settings, name)


def test_fit_reads_only_two_demonstrations(audit):
    class Poison:
        def __getitem__(self, key):
            raise AssertionError("a later demonstration was read")
    pairs = [{"input": [[0]], "output": [[0]]}, {"input": [[1]], "output": [[1]]}, Poison()]
    calls = []
    def execute(program, grid):
        calls.append(deepcopy(grid))
        return grid
    fit = audit.fit_hypothesis(execute, "independent-program", pairs)
    assert fit["survives_demonstrations"] is True
    assert fit["executed_demo_indices"] == [0, 1]
    assert calls == [[[0]], [[1]]]


def test_execution_errors_are_not_refutations(audit):
    def broken(program, grid):
        raise RuntimeError("deliberate runtime failure")
    with pytest.raises(RuntimeError, match="deliberate runtime failure"):
        audit.fit_hypothesis(broken, "bad", [{"input": [[0]], "output": [[0]]}] * 2)


@pytest.mark.parametrize("bad", [{}, {"reflection_colors": 1}, {"reflection_colors": True},
    {"reflection_colors": "swap", "extra": 1}, {"reflection_colors": "rotate"}])
def test_exact_setting_validation(audit, bad):
    with pytest.raises(ValueError):
        audit.setting(bad)
