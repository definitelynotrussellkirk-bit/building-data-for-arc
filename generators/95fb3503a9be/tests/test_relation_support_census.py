from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path


LIBRARY = next((p for p in Path(__file__).resolve().parents if (p / "shared/runtime").is_dir()), None)
if LIBRARY is None:
    gen = importlib.import_module("puzzle_generators.per_puzzle.95fb3503a9be.generator")
else:
    sys.path.insert(0, str(LIBRARY / "shared/runtime"))
    gen_spec = importlib.util.spec_from_file_location(
        "review_95fb3503a9be_census", LIBRARY / "generators/95fb3503a9be/generator.py"
    )
    assert gen_spec is not None and gen_spec.loader is not None
    gen = importlib.util.module_from_spec(gen_spec)
    gen_spec.loader.exec_module(gen)
PROBE_PATH = Path(__file__).resolve().parents[1] / "workspace/relation_support_census.py"
spec = importlib.util.spec_from_file_location("relation_support_census", PROBE_PATH)
assert spec is not None and spec.loader is not None
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_relation_signature_exposes_the_repaired_schedule_cell():
    ordinary = gen.generate(17, 0, difficulty="medium")
    repaired = gen.generate(17, 1, difficulty="medium")

    ordinary_sig = probe.grid_signature(ordinary, gen._object_records)
    repaired_sig = probe.grid_signature(repaired, gen._object_records)

    assert ordinary_sig["occupied_column_runs"] == 3
    assert ordinary_sig["overlapping_bbox_columns"] is False
    assert ordinary_sig["max_crop_width"] <= 3

    assert repaired_sig["overlapping_bbox_columns"] is True
    assert repaired_sig["max_crop_width"] == 4
    assert gen.SEMANTIC_RIVALS["column_bands"](repaired) != gen.rule_mirror(repaired)


def test_census_checks_every_four_sample_lesson_not_only_pooled_counts():
    report = probe.census_variant(
        gen,
        seeds=8,
        bands=("easy", "medium", "hard"),
        schedule_size=4,
    )

    assert report["scenes"] == 8 * 3 * 4
    assert report["self_check_failures"] == 0
    assert report["lesson_coverage"] == {
        "lessons": 24,
        "overlapping_bbox_columns": 24,
        "max_crop_width_at_least_4": 24,
    }
    assert report["rival_disagreements"]["column_bands"] == 24
    assert report["rival_disagreements"]["crop_width_three"] == 24
