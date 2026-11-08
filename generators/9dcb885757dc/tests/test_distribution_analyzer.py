from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_distribution_analyzer_reports_branch_and_shortcut_coverage(tmp_path: Path) -> None:
    generator_dir = Path(__file__).resolve().parents[1]
    script = generator_dir / "workspace" / "analyze_contact_graph_distribution.py"
    output = tmp_path / "analysis.json"
    run = subprocess.run(
        [
            sys.executable,
            str(script),
            "--samples-per-band",
            "5",
            "--json-out",
            str(output),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    report = json.loads(output.read_text())
    assert report["task_id"] == "9dcb885757dc"
    assert set(report["per_band"]) == {"easy", "medium", "hard"}
    assert report["pooled"]["degrees_seen"] == [0, 1, 2, 3, 4, 5]
    assert report["pooled"]["invalid_draws"] == 0
    assert report["pooled"]["shortcut_survival"]["all_objects_isolated"] < 1.0
    assert report["pooled"]["shortcut_survival"]["count_nearby_cells"] < 1.0
    assert "degree coverage: 0,1,2,3,4,5" in run.stdout
