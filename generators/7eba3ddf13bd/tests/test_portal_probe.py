"""The portable probe CLI must validate arguments before executing any checks."""
from pathlib import Path
import subprocess
import sys

PROBE = Path(__file__).resolve().parents[1] / "workspace/portal_probe.py"


def test_probe_help_is_runnable_without_racket():
    assert PROBE.is_file(), "portable probe has not been implemented"
    result = subprocess.run([sys.executable, str(PROBE), "--help"], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert "--generator" in result.stdout and "--seeds" in result.stdout


def test_probe_rejects_zero_samples_before_creating_output(tmp_path):
    assert PROBE.is_file(), "portable probe has not been implemented"
    out = tmp_path / "report"
    result = subprocess.run([sys.executable, str(PROBE), "--seeds", "0", "--out", str(out)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert not out.exists()
