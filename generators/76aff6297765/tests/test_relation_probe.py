from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_probe():
    path = Path(__file__).resolve().parents[1] / "workspace" / "probe_relation_curriculum.py"
    spec = importlib.util.spec_from_file_location("probe_relation_curriculum_76", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_checks_canonical_shortcuts_truth_tables_and_all_rotations(tmp_path):
    probe = _load_probe()
    report = probe.run_probe(seeds=(0,), difficulties=("easy",))

    assert report["passed"] is True
    assert report["canonical"]["declared_matches_actual"] is True
    assert report["canonical"]["actual_fits"] == [
        "equal_cells",
        "profile_gated_count_only",
    ]
    assert report["schedule"]["windows_checked"] == 6
    assert report["schedule"]["rotations_checked"] == 36
    assert report["schedule"]["ambiguous_rotations"] == 0
    assert report["relations"]["grids_checked"] == 36
    assert report["relations"]["non_unique_truth_tables"] == 0
    assert report["relations"]["row_major_collisions"] == 0

    out = tmp_path / "report.json"
    probe.write_report(report, out)
    assert out.exists()
    assert '"passed": true' in out.read_text()


def test_probe_generator_loader_falls_back_to_sibling_source(monkeypatch):
    probe = _load_probe()

    def unavailable(_name):
        raise ModuleNotFoundError("simulated unstaged repository")

    monkeypatch.setattr(probe.importlib, "import_module", unavailable)
    loaded = probe._load_generator()
    assert loaded.TASK_ID == "76aff6297765"
    assert Path(loaded.__file__).resolve().name == "generator.py"
