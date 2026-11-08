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


def test_composed_hypothesis_auditor_eliminates_all_canonical_fit_shortcuts():
    path = TASK_DIR / "workspace" / "audit_hypotheses.py"
    assert path.is_file(), "missing reusable composed-hypothesis auditor"
    audit = _load(path, "cadfb_hypothesis_audit_test")

    report = audit.run_audit(
        starts=range(8),
        bands=("easy", "medium", "hard"),
        seed_base=91_000,
    )
    assert report["hypotheses_enumerated"] == 36
    assert report["canonical_fit_hypotheses"] == 30
    assert report["non_authority_canonical_fit_hypotheses"] == 29
    assert report["windows_tested"] == 24
    assert report["all_non_authority_hypotheses_killed"] is True
    assert report["surviving_hypotheses"] == []
    assert report["authority"] == {
        "symmetry": "exact",
        "holes": "regions",
        "order": "top_left",
        "precedence": "symmetry_first",
    }
