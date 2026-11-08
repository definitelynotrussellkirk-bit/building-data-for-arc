"""Exercise evidence recovery and destination safety with real temporary files."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys

import pytest

from reviewer_support import find_root


SCRIPT = (find_root(__file__) / "generators" / "0eb4eaa46003" /
          "workspace" / "compact_evidence.py")


def run_tool(operation, source, root, *extra):
    return subprocess.run([sys.executable, "-B", str(SCRIPT), operation,
                           str(source), "--root", str(root), *extra],
                          capture_output=True, text=True)


def test_lossless_removal_and_idempotent_restore(tmp_path):
    source = tmp_path / "report.json"
    raw = b'{"retained_failure":true}\n' * 100
    source.write_bytes(raw)
    result = run_tool("compress", source, tmp_path, "--remove-original")
    assert result.returncode == 0, result.stderr
    assert not source.exists()
    sidecar = tmp_path / "report.json.compression.json"
    metadata = json.loads(sidecar.read_text())
    assert metadata["original_sha256"] == hashlib.sha256(raw).hexdigest()
    for _ in range(2):
        result = run_tool("restore", sidecar, tmp_path)
        assert result.returncode == 0, result.stderr
        assert source.read_bytes() == raw


@pytest.mark.parametrize("suffix", [".gz", ".compression.json"])
def test_compress_rejects_dangling_destination_symlink(tmp_path, suffix):
    root = tmp_path / "evidence"
    root.mkdir()
    source = root / "report.json"
    source.write_bytes(b"retain original")
    outside = tmp_path / "outside.txt"
    destination = root / (source.name + suffix)
    destination.symlink_to(outside)
    result = run_tool("compress", source, root, "--remove-original")
    assert result.returncode != 0
    assert not outside.exists()
    assert source.read_bytes() == b"retain original"


def test_restore_refuses_differing_existing_evidence(tmp_path):
    source = tmp_path / "report.json"
    source.write_bytes(b"original")
    assert run_tool("compress", source, tmp_path).returncode == 0
    source.write_bytes(b"newer evidence")
    result = run_tool("restore", tmp_path / "report.json.compression.json", tmp_path)
    assert result.returncode != 0
    assert source.read_bytes() == b"newer evidence"


def test_restore_rejects_corrupted_archive_before_writing(tmp_path):
    source = tmp_path / "report.json"
    source.write_bytes(b"original")
    assert run_tool("compress", source, tmp_path, "--remove-original").returncode == 0
    (tmp_path / "report.json.gz").write_bytes(b"corrupted")
    result = run_tool("restore", tmp_path / "report.json.compression.json", tmp_path)
    assert result.returncode != 0
    assert not source.exists()
