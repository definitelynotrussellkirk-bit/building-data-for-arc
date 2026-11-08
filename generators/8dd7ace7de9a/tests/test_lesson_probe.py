"""Regression tests for the retained source-bound lesson census tool."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
PROBE_PATH = HOME / "workspace" / "lesson_probe.py"
GENERATOR_PATH = HOME / "generator.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("lesson_probe_under_test", PROBE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_small_probe_is_source_bound_complete_and_deterministic(tmp_path):
    probe = _load_probe()
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"

    first = probe.run_probe(
        generator_path=GENERATOR_PATH,
        lessons_per_band=3,
        output_path=first_path,
    )
    second = probe.run_probe(
        generator_path=GENERATOR_PATH,
        lessons_per_band=3,
        output_path=second_path,
    )

    assert first == second
    assert json.loads(first_path.read_text(encoding="utf-8")) == first
    assert json.loads(second_path.read_text(encoding="utf-8")) == second
    assert first["schema"] == "8dd7ace7de9a-lesson-probe-v1"
    assert first["source"]["task_id"] == "8dd7ace7de9a"
    assert first["source"]["rule_hash"] == "0f05e4e27969"
    assert len(first["source"]["generator_sha256"]) == 64
    assert first["sampler"]["lesson_sample_stride"] == 11
    assert first["sampler"]["n_demos"] == 3
    assert first["sampler"]["n_queries"] == 1
    assert first["sampler"]["actual_generator_declarations"] == {
        "canonical_shortcuts": ["periods_at_most_three", "square_period_only"],
        "lesson_competitors": [
            "literal_top_left_tile",
            "periods_at_most_three",
            "square_period_only",
        ],
    }

    assert first["canonical_shortcut_fit"] == {
        "pairs": 3,
        "all_fit": True,
        "per_shortcut": {
            "periods_at_most_three": {"fit": 3, "total": 3},
            "square_period_only": {"fit": 3, "total": 3},
        },
    }
    assert first["totals"] == {
        "bands": 3,
        "lessons": 9,
        "demonstrations": 27,
        "queries": 9,
        "generated_inputs": 36,
        "identifiable": 9,
        "unidentifiable": 0,
        "hook_errors": 0,
        "competitor_errors": 0,
    }
    assert first["all_passed"] is True
    assert first["failures"] == []

    for band in ("easy", "medium", "hard"):
        row = first["per_band"][band]
        assert row["lessons"] == 3
        assert row["identifiable"] == 3
        assert row["unidentifiable"] == 0
        assert row["cyclic_start_residues"] == {"0": 1, "1": 1, "2": 1}
        assert row["unique_inputs"] == 12
        assert row["domain_limits"]["grid_h"] == {"min": 12, "max": 16}
        assert row["domain_limits"]["grid_w"] == {"min": 12, "max": 19}
        for competitor in (
            "literal_top_left_tile",
            "periods_at_most_three",
            "square_period_only",
        ):
            assert row["competitors"][competitor] == {
                "lessons_refuted_by_demos": 3,
                "lessons_surviving_demos": 0,
                "lessons_surviving_all": 0,
                "errors": 0,
            }
