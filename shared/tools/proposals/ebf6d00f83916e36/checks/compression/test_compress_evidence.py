"""Real CLI probes for preserving completed evidence and refusing collisions."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest
from reviewer_support import find_root

ROOT = find_root(__file__)
UTILITY = ROOT / "generators/48283e01e8ab/workspace/review_tools/compress_evidence.py"
RAW = b'{\r\n  "schema": "test-receipt-v1", "value": [1, 2], "note": "\\u00e9"\r\n}\r\n'


def invoke(path):
    return subprocess.run([sys.executable, str(UTILITY), str(path)], capture_output=True, text=True)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def test_preserves_exact_bytes_and_writes_deterministic_native_receipts(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "renamed.json"
    first.write_bytes(RAW)
    second.write_bytes(RAW)
    outputs = []
    for source in (first, second):
        process = invoke(source)
        assert process.returncode == 0, process.stderr
        outcome = json.loads(process.stdout)
        assert outcome["status"] == "compressed_verified"
        assert outcome["source_preserved"] is True
        assert source.read_bytes() == RAW
        packed_path = Path(str(source) + ".gz")
        packed = packed_path.read_bytes()
        manifest = json.loads(source.with_suffix(".compression.json").read_text())
        assert gzip.decompress(packed) == RAW
        assert packed[4:8] == b"\0\0\0\0", "gzip must have mtime zero"
        assert manifest["schema"] == "arcpuzzles-evidence-gzip-v1"
        assert manifest["compression"] == "gzip"
        assert manifest["files"] == [{
            "path": source.name, "compressed_path": source.name + ".gz",
            "raw_size": len(RAW), "raw_sha256": digest(RAW),
            "compressed_size": len(packed), "compressed_sha256": digest(packed),
        }]
        assert manifest["restore_argv"] == ["python3", "-m", "gzip", "-d", source.name + ".gz"]
        outputs.append(packed)
    assert outputs[0] == outputs[1], "gzip must not embed the source filename"


@pytest.mark.parametrize("existing_suffix", [".json.gz", ".compression.json"])
def test_refuses_existing_neighbor_without_changing_source_or_other_paths(tmp_path, existing_suffix):
    source = tmp_path / "receipt.json"
    source.write_bytes(RAW)
    existing = source.with_suffix(existing_suffix)
    existing.write_bytes(b"do not replace this artifact\n")
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    process = invoke(source)
    assert process.returncode != 0
    assert "already exists" in process.stderr.lower(), process.stderr
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


def test_rejects_non_json_before_creating_outputs(tmp_path):
    source = tmp_path / "broken.json"
    source.write_bytes(b"this is not JSON\n")
    process = invoke(source)
    assert process.returncode != 0
    assert "json" in process.stderr.lower()
    assert list(tmp_path.iterdir()) == [source]
    assert source.read_bytes() == b"this is not JSON\n"
