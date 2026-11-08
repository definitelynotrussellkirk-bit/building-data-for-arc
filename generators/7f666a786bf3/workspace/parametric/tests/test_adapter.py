from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
ADAPTER = HERE / "adapter.py"


def load_adapter():
    spec = importlib.util.spec_from_file_location("parametric_7f666a786bf3", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    root = Path(__file__).resolve().parents[5]
    path = root / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record.get("task_id") == "7f666a786bf3":
            return record["program_solution"]
    raise AssertionError("canonical task missing")


def test_default_program_is_byte_exact_canonical():
    adapter = load_adapter()
    assert adapter.program({"finish": "fill_only"}) == canonical_program()
    assert adapter.program({"finish": "fill_only"}).encode() == (HERE / "canonical.rkt").read_bytes()


def test_settings_and_counts_are_strictly_typed():
    adapter = load_adapter()
    bad_settings = [None, {}, {"finish": "unknown"}, {"finish": 1}, {"finish": "fill_only", "x": 1}]
    for settings in bad_settings:
        with pytest.raises(ValueError):
            adapter.program(settings)
    for name, value in (("seed", True), ("demos", True), ("queries", True)):
        kwargs = {"seed": 0, "settings": {"finish": "fill_only"}, "demos": 3, "queries": 4}
        kwargs[name] = value
        with pytest.raises(ValueError):
            adapter.generate(**kwargs)
    for demos in (1, 7):
        with pytest.raises(ValueError):
            adapter.generate(0, {"finish": "fill_only"}, demos, 4)
    for queries in (0, 5):
        with pytest.raises(ValueError):
            adapter.generate(0, {"finish": "fill_only"}, 3, queries)


def test_counts_are_prefix_stable_and_inputs_match_across_settings():
    adapter = load_adapter()
    small = adapter.generate(17, {"finish": "fill_only"}, 2, 1)
    large = adapter.generate(17, {"finish": "fill_only"}, 6, 4)
    alternate = adapter.generate(17, {"finish": "highlight_largest_filled"}, 6, 4)
    assert small["train"] == large["train"][:2]
    assert small["test"] == large["test"][:1]
    assert [p["input"] for p in large["train"]] == [p["input"] for p in alternate["train"]]
    assert [p["input"] for p in large["test"]] == [p["input"] for p in alternate["test"]]
    keys = [json.dumps(p["input"], separators=(",", ":")) for p in large["train"] + large["test"]]
    assert len(keys) == len(set(keys))


def test_python_claims_match_both_declared_rules():
    adapter = load_adapter()
    for seed in (0, 17, 97):
        for finish in adapter.SETTINGS:
            episode = adapter.generate(seed, {"finish": finish}, 6, 4)
            assert episode["program_solution"] == adapter.program({"finish": finish})
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == adapter.predict(pair["input"], finish)
                assert adapter.observe(pair["input"])["winner_count"] == 1


def test_two_demonstrations_reject_every_declared_rival():
    adapter = load_adapter()
    for seed in range(32):
        for finish in adapter.SETTINGS:
            episode = adapter.generate(seed, {"finish": finish}, 2, 4)
            certificate = adapter.certificate(episode["train"], [p["input"] for p in episode["test"]])
            assert certificate["survivors"] == [finish]
            assert set(certificate["query_disagreements"]) == set(adapter.HYPOTHESES) - {finish}


def test_query_bank_contains_substantive_30_by_30_stress():
    adapter = load_adapter()
    for seed in (0, 3, 17, 41):
        episode = adapter.generate(seed, {"finish": "highlight_largest_filled"}, 3, 4)
        stress = [p for p in episode["test"] if len(p["input"]) == 30 and len(p["input"][0]) == 30]
        assert len(stress) == 1
        info = adapter.observe(stress[0]["input"])
        assert info["colors"] == 4
        assert info["foreground_cells"] >= 10
        assert info["filled_cells"] >= 180
        assert info["touches"] == ["bottom", "left", "right", "top"]
        assert max(info["areas"]) >= 70


def test_dependency_explanation_and_wrong_intermediate_change_output():
    adapter = load_adapter()
    episode = adapter.generate(0, {"finish": "highlight_largest_filled"}, 3, 4)
    candidates = episode["train"] + episode["test"]
    witness = next(pair for pair in candidates if adapter.predict(pair["input"], "highlight_largest_perimeter") != pair["output"])
    explanation = adapter.explain_dependency(witness["input"])
    assert explanation["step_a"]
    assert explanation["intermediate"] == adapter.predict(witness["input"], "fill_only")
    assert explanation["step_b"]
    assert explanation["largest_area_color"] != explanation["largest_perimeter_color"]
    assert adapter.predict(witness["input"], "highlight_largest_perimeter") != witness["output"]
