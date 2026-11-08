from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

TASK_HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_shortcut_audit_covers_canonical_and_every_generated_window():
    generator = _load(TASK_HOME / "generator.py", "reviewed_c4d63d8b4567")
    audit = _load(Path(__file__).with_name("shortcut_audit.py"), "shortcut_audit")

    report = audit.build_report(generator, seeds=range(2))

    assert report["ok"] is True
    assert report["canonical"]["pair_count"] == 5
    assert report["canonical"]["rival_matches"] == 5
    assert report["generated"]["case_count"] == 24
    assert report["generated"]["repeated_witnesses"] == 6
    assert report["generated"]["rival_disagreements"] == 6
    assert report["generated"]["windows_without_refutation"] == []
    assert report["first_generated_witness"]["max_global_multiplicity"] == 3
