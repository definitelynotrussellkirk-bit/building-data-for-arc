"""Native-admission tests for the corner-copy direction family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_pairs, find_root, public_challenge_bytes  # noqa: E402

TASK_ID = "61c0bcd32328"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str, filename: str):
    path = PARAMETRIC / filename
    assert path.is_file(), f"missing native parametric source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def native():
    return _load(f"_native_{TASK_ID}", "native.py")


def adapter():
    return _load(f"_adapter_{TASK_ID}", "adapter.py")


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def _changed_cells(pair):
    return [
        (r, c)
        for r, row in enumerate(pair["input"])
        for c, value in enumerate(row)
        if pair["output"][r][c] != value
    ]


def test_native_adapter_preserves_exact_canonical_default_and_exposes_alternate():
    module = native()
    shim = adapter()
    canonical = (PARAMETRIC / "canonical.rkt").read_text(encoding="utf-8")
    counterclockwise = (PARAMETRIC / "counterclockwise.rkt").read_text(encoding="utf-8")

    assert module.program({"direction": "clockwise"}) == canonical
    assert module.program({"direction": "counterclockwise"}) == counterclockwise
    assert canonical != counterclockwise
    assert shim.program({"direction": "clockwise"}) == canonical

    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert module.solve_python(pair["input"], {"direction": "clockwise"}) == pair["output"]


def test_generate_supports_independent_count_bounds_and_prefix_stability():
    module = native()
    for direction in module.DIRECTIONS:
        setting = {"direction": direction}
        shortest = module.generate(17, setting, 2, 1)
        longest = module.generate(17, setting, 6, 4)
        assert shortest["train"] == longest["train"][:2]
        assert shortest["test"] == longest["test"][:1]
        assert len(longest["train"]) == 6
        assert len(longest["test"]) == 4
        assert longest["program_solution"] == module.program(setting)
        assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(longest)}) == 10


def test_settings_use_matched_inputs_and_first_two_demos_teach_only_selected_rule():
    module = native()
    for seed in (0, 17, 91):
        clockwise = module.generate(seed, {"direction": "clockwise"}, 2, 4)
        counter = module.generate(seed, {"direction": "counterclockwise"}, 2, 4)
        assert _inputs(clockwise) == _inputs(counter)
        assert module.teaching_certificate(clockwise) == {
            "setting_survivors": ["clockwise"],
            "plausible_rival_survivors": [],
            "demonstrations_checked": 2,
        }
        assert module.teaching_certificate(counter) == {
            "setting_survivors": ["counterclockwise"],
            "plausible_rival_survivors": [],
            "demonstrations_checked": 2,
        }


def test_fourth_query_is_substantive_thirty_by_thirty_boundary_stress():
    module = native()
    for direction in module.DIRECTIONS:
        episode = module.generate(23, {"direction": direction}, 3, 4)
        pair = episode["test"][3]
        grid = pair["input"]
        assert (len(grid), len(grid[0])) == (30, 30)
        info = module.analyze(grid)
        assert info["background_count"] >= 600
        assert info["foreground_count"] >= 80
        assert set(info["corner_labels"]) == {"tl", "br"}
        changed = _changed_cells(pair)
        assert len(changed) >= 12
        assert max(r for r, _ in changed) - min(r for r, _ in changed) >= 24
        assert max(c for _, c in changed) - min(c for _, c in changed) >= 24


def test_public_turn_hides_settings_program_answers_and_total_query_count():
    module = native()
    full = module.generate(5, {"direction": "clockwise"}, 3, 4)
    one = module.generate(5, {"direction": "clockwise"}, 3, 1)
    visible = module.public_turn(full, 0)
    assert visible == module.public_turn(one, 0)
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in visible["train"])
    assert set(visible["test"][0]) == {"input"}
    payload = public_challenge_bytes(visible)

    private_changed = deepcopy(full)
    private_changed["program_solution"] = "private replacement"
    private_changed["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(module.public_turn(private_changed, 0)) == payload


def test_wrong_intermediate_and_skip_a_change_final_output():
    module = native()
    witness = module.dependency_witness()
    assert witness["schema"] == "61c0bcd32328-causal-draft-v1"
    assert witness["ablation"] == "wrong_intermediate"
    assert witness["correct_output"] != witness["counterfactual_output"]
    assert witness["correct_output"] != witness["skip_a_output"]
    assert witness["intermediate_value"]["corner"] == "tl"
    assert witness["wrong_intermediate_value"]["corner"] == "tr"
    assert module.solve_python(witness["input"], witness["settings"]) == witness["correct_output"]


@pytest.mark.parametrize(
    "call",
    [
        lambda module: module.program({}),
        lambda module: module.program({"direction": "sideways"}),
        lambda module: module.generate(-1, {"direction": "clockwise"}, 2, 4),
        lambda module: module.generate(0, {"direction": "clockwise"}, 1, 4),
        lambda module: module.generate(0, {"direction": "clockwise"}, 7, 4),
        lambda module: module.generate(0, {"direction": "clockwise"}, 2, 0),
        lambda module: module.generate(0, {"direction": "clockwise"}, 2, 5),
        lambda module: module.generate(True, {"direction": "clockwise"}, 2, 4),
    ],
)
def test_invalid_native_requests_fail_loudly(call):
    with pytest.raises(ValueError):
        call(native())


def test_reusable_python_audit_covers_counts_rivals_and_thirty_by_thirty():
    audit = _load(f"_audit_{TASK_ID}", "self_audit.py")
    report = audit.python_audit(stress_seeds=3)
    assert report["status"] == "passed"
    assert report["episodes"] == 24
    assert report["matched_input_checks"] == 12
    assert report["prefix_checks"] == 24
    assert report["finite_rival_fits"] == 0
    assert report["thirty_by_thirty_pairs"] == 12


def test_wrong_corner_label_uses_the_selected_labels_translation_formula():
    module = native()
    witness = module.dependency_witness()
    color = witness["intermediate_value"]["color"]
    height = len(witness["input"])
    width = len(witness["input"][0])
    # Reclassifying the TL singleton as TR makes the canonical TR formula move it
    # down only; it does not recompute a geometrically valid BR alignment.
    assert witness["counterfactual_output"][height - 1][0] == color
    assert witness["counterfactual_output"][height - 1][width - 1] != color
