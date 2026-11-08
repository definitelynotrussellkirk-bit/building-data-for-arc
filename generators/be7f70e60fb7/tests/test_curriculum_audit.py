from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parents[1]
RUNTIME = Path(__file__).resolve().parents[3] / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_audit_report_covers_each_band_profile_and_rival() -> None:
    audit = _load("be7f70e60fb7_curriculum_audit", TASK_DIR / "workspace" / "audit_curriculum.py")
    generator = _load("be7f70e60fb7_generator_for_audit", TASK_DIR / "generator.py")

    report = audit.build_report(generator, seeds=range(3))

    assert report["ok"] is True
    assert report["generated_cases"] == 3 * 3 * len(generator.SCENE_PROFILES)
    assert report["profiles"] == {
        profile: 3 * 3 for profile in generator.SCENE_PROFILES
    }
    assert report["failures"] == []
    assert set(report["rivals_refuted"]) == set(generator.LESSON_COMPETITORS)
    assert all(report["rivals_refuted"].values())


def test_cli_writes_machine_readable_report(tmp_path: Path) -> None:
    audit = _load("be7f70e60fb7_curriculum_audit_cli", TASK_DIR / "workspace" / "audit_curriculum.py")
    destination = tmp_path / "audit.json"

    exit_code = audit.main(["--seeds", "2", "--json", str(destination)])

    assert exit_code == 0
    payload = json.loads(destination.read_text())
    assert payload["ok"] is True
    assert payload["generated_cases"] == 2 * 3 * 4
