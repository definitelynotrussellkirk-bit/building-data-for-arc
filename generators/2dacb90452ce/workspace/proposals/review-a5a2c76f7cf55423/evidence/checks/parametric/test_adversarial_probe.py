from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

WORK = Path(__file__).resolve().parents[2]
REPO = WORK / "repo"
SCRIPT = WORK / "checks" / "parametric" / "adversarial_probe.py"


def test_probe_writes_parseable_source_bound_json(tmp_path):
    out = tmp_path / "adversarial.json"
    env = os.environ.copy()
    pythonpath = [str(REPO / "shared" / "runtime"), str(REPO / "src")]
    if env.get("PYTHONPATH"):
        pythonpath.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--out", str(out)],
        cwd=REPO,
        env=env,
        text=True,
        capture_output=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["status"] == "no_findings"
    assert report["findings"] == []
    assert report["sampler_cases"] == 96
    assert report["sampler_inputs"] == 672
    assert report["racket_episodes"] == 16
    assert report["racket_labels"] == 96
    assert report["counterfactual_labels"] == 96
    assert report["public_projection_checks"] == 16
    assert report["sources"]["generator_sha256"] == (
        "b972fe9cc491907d1193818efe9a68c28202c3cb355cf31fc1b0c7dd2779d4c0"
    )
