from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parents[1]
REPO = TASK_DIR.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_curriculum_auditor_certifies_declared_rivals_and_canonical_shortcuts():
    path = TASK_DIR / "workspace" / "audit_curriculum.py"
    assert path.is_file(), "missing reusable curriculum shortcut auditor"
    audit = _load(path, "cadfb_curriculum_audit_test")

    report = audit.run_audit(
        starts=range(6),
        bands=("easy", "medium", "hard"),
        seed_base=71_000,
    )
    assert report["all_declared_rivals_killed"] is True
    assert report["windows_tested"] == 18
    assert set(report["rivals"]) == set(audit.GEN.SEMANTIC_RIVALS)
    assert all(item["surviving_windows"] == 0 for item in report["rivals"].values())
    assert all(report["canonical_shortcuts"].values())
    assert report["all_canonical_shortcuts_fit"] is True
    assert report["audit_passed"] is True
