from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_probe():
    path = Path(__file__).resolve().parents[1] / "workspace" / "lesson_rival_probe.py"
    spec = importlib.util.spec_from_file_location("lesson_rival_probe", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_lesson_plan_is_deterministic_nonoverlapping_and_covers_all_starts():
    probe = _load_probe()
    first = probe.build_lesson_plan(
        task_id="bc5e668b7668",
        band="easy",
        lessons=8,
        examples_per_lesson=5,
        schedule_period=4,
    )
    second = probe.build_lesson_plan(
        task_id="bc5e668b7668",
        band="easy",
        lessons=8,
        examples_per_lesson=5,
        schedule_period=4,
    )
    assert first == second
    assert [row["start_residue"] for row in first] == [0, 1, 2, 3, 0, 1, 2, 3]
    indices = [index for lesson in first for index in lesson["sample_indices"]]
    assert len(indices) == len(set(indices)) == 40
    assert all(len(lesson["sample_indices"]) == 5 for lesson in first)
    assert all(type(lesson["seed"]) is int for lesson in first)
