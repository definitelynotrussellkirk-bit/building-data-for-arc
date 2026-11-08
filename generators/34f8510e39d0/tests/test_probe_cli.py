"""CLI destinations must preserve the probe's witness hash bindings."""
from pathlib import Path
import json
import subprocess
import sys

import pytest
from reviewer_support import find_root


def _probe_source():
    root = find_root(__file__)
    relative = "generators/34f8510e39d0/workspace/probe_color_roles.py"
    manifest = root / "RUNTIME_MANIFEST.json"
    if manifest.is_file():
        paths = {item["runtime_path"] for item in json.loads(manifest.read_text())["files"]
                 if item["library_path"] == relative}
        assert len(paths) == 1, "staged manifest must bind exactly one workspace probe"
        source = root / paths.pop()
    else:
        source = root / relative
    assert source.is_file(), f"Selected probe missing: {source}"
    return source


@pytest.mark.parametrize("relative_alias", (False, True))
def test_probe_rejects_equal_resolved_output_destinations_before_writing(tmp_path, relative_alias):
    destination = tmp_path / "collided.json"
    # Spell the second path differently to exercise resolved-path equality.
    witness_destination = tmp_path / "alias" / ".." / destination.name if relative_alias else destination
    run = subprocess.run(
        [sys.executable, str(_probe_source()), "--seeds", "0", "--indices", "1",
         "--bands", "easy", "--out", str(destination), "--witness-inputs", str(witness_destination)],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert run.returncode != 0, "CLI accepted overlapping report and witness destinations"
    assert "distinct" in run.stderr
    assert not destination.exists(), "Rejected arguments must not create the destination"
    assert not (tmp_path / "alias").exists(), "Rejected arguments must not create parent directories"
