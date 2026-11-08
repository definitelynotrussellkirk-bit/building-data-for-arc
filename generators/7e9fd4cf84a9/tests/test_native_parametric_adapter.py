from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "7e9fd4cf84a9"
HERE = Path(__file__).resolve().parents[1]
PARAM = HERE / "workspace/parametric"
REPO = HERE.parents[1]
SETTINGS = (
    {"fill_scope": "all_rectangles"},
    {"fill_scope": "largest_only"},
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _adapter():
    return _load(PARAM / "adapter.py", "_arc_7e_adapter")


def _base():
    return _load(HERE / "generator.py", "_arc_7e_base")


def _canonical_program():
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("content_hash") == TASK:
            return row["program_solution"]
    raise AssertionError("canonical task missing")


def test_promotion_contract_and_exact_canonical_default():
    promotion = json.loads((PARAM / "promotion.json").read_text())
    assert promotion["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert promotion["parameters"] == {"fill_scope": ["all_rectangles", "largest_only"]}
    assert promotion["default"] == {"fill_scope": "all_rectangles"}
    assert promotion["limits"] == {"demos": [2, 6], "queries": [4, 4]}
    assert promotion["qualification_demos"] == 2
    adapter = _adapter()
    canonical = _canonical_program()
    assert adapter.program(SETTINGS[0]) == canonical
    assert hashlib.sha256(adapter.program(SETTINGS[0]).encode()).hexdigest() == "07676e3503c60ec8cbbc0294a21a5f8eb4eb33ae9e4f515c0af8bd554b977d2f"
    assert adapter.program(SETTINGS[1]) != canonical


def test_native_range_labels_and_exact_four_queries():
    adapter = _adapter()
    for setting in SETTINGS:
        for demos in range(2, 7):
            episode = adapter.generate(17, setting, demos, 4)
            assert len(episode["train"]) == demos
            assert len(episode["test"]) == 4
            assert episode["program_solution"] == adapter.program(setting)
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == adapter.solve(pair["input"], setting)


def test_demo_prefix_query_bank_and_inputs_are_setting_independent():
    adapter = _adapter()
    short = adapter.generate(99, SETTINGS[0], 2, 4)
    long = adapter.generate(99, SETTINGS[0], 6, 4)
    other = adapter.generate(99, SETTINGS[1], 6, 4)
    assert short["train"] == long["train"][:2]
    assert [p["input"] for p in short["test"]] == [p["input"] for p in long["test"]]
    assert [p["input"] for p in long["train"] + long["test"]] == [p["input"] for p in other["train"] + other["test"]]


def test_two_demos_identify_the_setting_and_largest_scope_is_causal():
    adapter = _adapter()
    for setting in SETTINGS:
        episode = adapter.generate(5, setting, 2, 4)
        survivors = []
        for candidate in SETTINGS:
            if all(adapter.solve(pair["input"], candidate) == pair["output"] for pair in episode["train"]):
                survivors.append(candidate)
        assert survivors == [setting]
        for pair in episode["train"]:
            all_out = adapter.solve(pair["input"], SETTINGS[0])
            largest_out = adapter.solve(pair["input"], SETTINGS[1])
            assert all_out != largest_out


def test_stress_query_is_30x30_unique_largest_and_preserves_distractors():
    adapter = _adapter()
    base = _base()
    episode = adapter.generate(123, SETTINGS[0], 2, 4)
    stress = [pair for pair in episode["test"] if len(pair["input"]) == len(pair["input"][0]) == 30]
    assert len(stress) == 1
    pair = stress[0]
    analysis = base.analyze_scene(pair["input"])
    areas = [h * w for h, w in analysis["rectangle_shapes"]]
    assert len(areas) >= 5 and areas.count(max(areas)) == 1
    assert analysis["distractor_cell_count"] >= 5
    assert sum(v != 0 for row in pair["input"] for v in row) >= 100
    for r, c, color in analysis["distractor_cells"]:
        assert pair["output"][r][c] == color


def test_invalid_contract_values_are_rejected():
    adapter = _adapter()
    bad_calls = (
        lambda: adapter.program({}),
        lambda: adapter.program({"fill_scope": "all"}),
        lambda: adapter.program({"fill_scope": "all_rectangles", "extra": 1}),
        lambda: adapter.generate(True, SETTINGS[0], 2, 4),
        lambda: adapter.generate(0, SETTINGS[0], 1, 4),
        lambda: adapter.generate(0, SETTINGS[0], 2, 3),
    )
    for call in bad_calls:
        try:
            call()
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError("invalid native contract call was accepted")


def test_reusable_bounded_audit_tool_passes_small_census(tmp_path):
    audit = _load(PARAM / "audit_native.py", "_arc_7e_audit")
    report = audit.run_audit(seed_count=2)
    assert report["status"] == "passed"
    assert report["episodes"] == 2 * len(SETTINGS) * 5
    assert report["labeled_pairs"] == sum((demos + 4) for demos in range(2, 7)) * 2 * len(SETTINGS)
    assert report["substantive_30x30_cases"] == report["episodes"]
    assert report["failures"] == []
