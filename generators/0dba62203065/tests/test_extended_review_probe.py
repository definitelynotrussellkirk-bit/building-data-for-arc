from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


TASK_DIR = Path(__file__).resolve().parents[1]
PROBE = TASK_DIR / "workspace" / "review_probe.py"
REPO_ROOT = TASK_DIR.parents[1]


def test_review_probe_reports_source_bound_uniqueness_and_cycle_shortcut(tmp_path: Path) -> None:
    report_path = tmp_path / "probe.json"
    result = subprocess.run(
        [
            sys.executable,
            str(PROBE),
            "--samples-per-band",
            "4",
            "--json-out",
            str(report_path),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report == json.loads(report_path.read_text(encoding="utf-8"))
    assert len(report["generator_sha256"]) == 64
    assert report["canonical"]["cycle_from_first_two_fits_all_public"] is True
    assert report["randomized"]["unique_inputs_by_band"] == {
        "easy": 4,
        "medium": 4,
        "hard": 4,
    }
    assert report["randomized"]["overall_unique_inputs"] == 12
    assert report["randomized"]["legend_profile_counts"] == {
        "cyclic": 6,
        "anchor_swap": 6,
    }
    assert report["randomized"]["rival_refutations"]["cycle_from_first_two"] == 6
    assert report["randomized"]["sampler"]["sample_index_range"] == "0..3"
    assert report["randomized"]["sampler"]["seed_formula"] == (
        "100000 + band_index*10000 + sample_index"
    )
