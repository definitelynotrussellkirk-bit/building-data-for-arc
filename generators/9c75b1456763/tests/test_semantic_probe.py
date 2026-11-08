from __future__ import annotations

import importlib.util
from pathlib import Path


HOME = Path(__file__).resolve().parents[1]
PROBE = HOME / "workspace" / "semantic_probe.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("semantic_probe_9c75b1456763", PROBE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_is_source_bound_and_checks_every_cyclic_lesson():
    probe = _load_probe()
    report = probe.run_probe(per_band=4, seed_base=17000)
    assert report["schema"] == "9c75b1456763-semantic-probe-v1"
    assert len(report["source_binding"]["generator_sha256"]) == 64
    assert report["sampler"]["per_band"] == 4
    for band in ("easy", "medium", "hard"):
        row = report["bands"][band]
        assert row["draws"] == 4
        assert row["strict_pass"] == 4
        assert row["lessons"]["checked_cyclic_starts"] == 4
        assert row["lessons"]["identifiable"] == 4
        assert all(count == 4 for count in row["witness_hits"].values())
        assert all(count == 4 for count in row["rival_disagreements"].values())
