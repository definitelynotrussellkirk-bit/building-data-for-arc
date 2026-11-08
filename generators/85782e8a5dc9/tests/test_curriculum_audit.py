from __future__ import annotations

import importlib.util
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parents[1]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_curriculum_audit_finds_no_schedule_or_rival_failures() -> None:
    generator = _load(TASK_DIR / "generator.py", "audit_test_generator")
    audit = _load(TASK_DIR / "workspace" / "curriculum_audit.py", "curriculum_audit")
    report = audit.audit_curriculum(
        generator,
        seeds=range(4),
        starts=range(10),
        bands=("easy", "medium", "hard"),
    )
    assert report["status"] == "pass"
    assert report["failures"] == []
    assert set(report["profiles_seen"]) == set(generator.SCENE_PROFILES)
    assert set(report["transforms_seen"]) == {
        "rot90",
        "rot180",
        "flip_lr",
        "flip_ud",
        "transpose",
        "anti_transpose",
    }
    assert report["surviving_lesson_rivals"] == {}
    assert report["rotation_count"] == report["lesson_count"] * (
        generator.EXAMPLES_NEEDED + 1
    )
    assert report["surviving_rotated_lesson_rivals"] == {}
    assert report["canonical_shortcuts_that_fit_all"] == [
        "infer_transform_from_occupancy_only"
    ]
    assert report["generated_counterexamples_by_shortcut"][
        "infer_transform_from_occupancy_only"
    ] > 0
