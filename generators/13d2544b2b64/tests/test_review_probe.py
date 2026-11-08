from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from review_diagnostics import compare_structure
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "13d2544b2b64"
ROOT = find_root(__file__)
TASK_DIR = ROOT / "generators" / TASK_ID


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_report_covers_profiles_rivals_and_canonical_parity() -> None:
    probe = _load("probe_13d2544b2b64", TASK_DIR / "workspace" / "review_probe.py")
    generator, _source, _digest = load_selected_generator(TASK_ID, root=ROOT)

    report = probe.build_report(generator, seeds=range(3))

    assert report["ok"] is True
    assert report["generated_cases"] == 3 * 3 * len(generator.SCENE_PROFILES)
    assert report["canonical_pairs_checked"] == 4
    assert report["canonical_parity_failures"] == []
    assert report["profile_counts"] == {
        profile: 3 * 3 for profile in generator.SCENE_PROFILES
    }
    assert set(report["canonical_shortcuts"]) == set(generator.CANONICAL_SHORTCUTS)
    assert all(report["canonical_shortcuts"].values())
    assert all(report["generated_counterexamples"].values())
    assert report["failures"] == []


def test_probe_cli_writes_json(tmp_path: Path) -> None:
    probe = _load("probe_13d2544b2b64_cli", TASK_DIR / "workspace" / "review_probe.py")
    destination = tmp_path / "probe.json"
    exit_code = probe.main(["--seeds", "2", "--json", str(destination)])
    assert exit_code == 0
    payload = json.loads(destination.read_text())
    assert payload["ok"] is True
    assert payload["generated_cases"] == 2 * 3 * 4


def test_probe_reports_dynamic_rivals_without_merging_namespaces() -> None:
    probe = _load("probe_13d2544b2b64_rivals", TASK_DIR / "workspace" / "review_probe.py")
    generator, _source, _digest = load_selected_generator(TASK_ID, root=ROOT)
    name = "added_after_probe"
    generator.SEMANTIC_RIVALS = {**generator.SEMANTIC_RIVALS, name: generator.rule_mirror}
    generator.LESSON_COMPETITORS = {
        **generator.LESSON_COMPETITORS, name: lambda grid: [row[:] for row in grid]
    }
    generator.CANONICAL_SHORTCUTS = {
        **generator.CANONICAL_SHORTCUTS,
        name: generator.CANONICAL_SHORTCUTS["vertical_priority"],
    }

    report = probe.build_report(generator, seeds=range(1))

    assert set(report["rivals"]) == {
        f"{declaration}.{rival}"
        for declaration in ("SEMANTIC_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS")
        for rival in getattr(generator, declaration)
    }
    semantic = report["rivals"][f"SEMANTIC_RIVALS.{name}"]
    competitor = report["rivals"][f"LESSON_COMPETITORS.{name}"]
    shortcut = report["rivals"][f"CANONICAL_SHORTCUTS.{name}"]
    assert semantic["canonical_fit"] is True
    assert semantic["generated_counterexamples"] == 0
    assert competitor["canonical_fit"] is False
    assert competitor["generated_counterexamples"] == report["generated_cases"]
    assert shortcut["canonical_fit"] is True
    assert shortcut["generated_counterexamples"] > 0
    assert all(not result["errors"] for result in (semantic, competitor, shortcut))


@pytest.mark.parametrize("declaration", ("SEMANTIC_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"))
def test_probe_reports_generated_rival_errors_without_counting_them_as_witnesses(declaration: str) -> None:
    probe = _load("probe_13d2544b2b64_errors", TASK_DIR / "workspace" / "review_probe.py")
    generator, _source, _digest = load_selected_generator(TASK_ID, root=ROOT)
    canonical_inputs = {
        tuple(map(tuple, pair["input"])) for pair in canonical_pairs(TASK_ID, root=ROOT)
    }

    def fails_only_on_generated_inputs(grid):
        if tuple(map(tuple, grid)) in canonical_inputs:
            return generator.rule_mirror(grid)
        raise RuntimeError("generated rival sentinel")

    setattr(generator, declaration, {
        **getattr(generator, declaration), "generated_failure": fails_only_on_generated_inputs
    })
    report = probe.build_report(generator, seeds=range(1))

    result = report["rivals"][f"{declaration}.generated_failure"]
    assert result["canonical_fit"] is True
    assert result["generated_counterexamples"] == 0
    assert len(result["errors"]) == report["generated_cases"]
    assert all("generated rival sentinel" in error for error in result["errors"])
    if declaration == "CANONICAL_SHORTCUTS":
        assert report["generated_counterexamples"]["generated_failure"] is False
    assert report["ok"] is False
    assert any("generated rival sentinel" in failure for failure in report["failures"])


def test_probe_structure_uses_only_canonical_training_pairs() -> None:
    probe = _load("probe_13d2544b2b64_structure", TASK_DIR / "workspace" / "review_probe.py")
    generator, _source, _digest = load_selected_generator(TASK_ID, root=ROOT)
    training = [pair for pair in canonical_pairs(TASK_ID, root=ROOT) if pair["split"] == "train"]
    generated = []
    for band in ("easy", "medium", "hard"):
        for index, profile in enumerate(generator.SCENE_PROFILES):
            grid = generator.generate(0, index, difficulty=band, scene_profile=profile)
            generated.append({"input": grid, "output": generator.rule_mirror(grid)})

    report = probe.build_report(generator, seeds=range(1))

    structure = report["structural_support"]
    assert structure["canonical_split"] == "train"
    assert structure["canonical_pairs_checked"] == len(training)
    assert structure["generated_label_source"] == "python_rule_mirror"
    assert structure["comparison"] == compare_structure(training, generated)
