from __future__ import annotations

import importlib.util
from pathlib import Path


TASK_ROOT = Path(__file__).resolve().parents[1]
PROBE_PATH = TASK_ROOT / "workspace" / "lesson_probe.py"
GENERATOR_PATH = TASK_ROOT / "generator.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("lesson_probe_7213d98ef029", PROBE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_small_probe_is_source_bound_and_refutes_every_declared_rival():
    probe = _load_probe()
    report = probe.run_probe(
        generator_path=GENERATOR_PATH,
        lessons_per_band=3,
        seed_base=8128,
    )

    assert report["task_id"] == "7213d98ef029"
    assert len(report["generator_sha256"]) == 64
    assert report["rule_hash"] == "e5bbb5dc0c42"
    assert report["sampler"]["lesson_width"] == 4
    assert report["domain_limits"]["incompatible_override_combinations"]

    for band in ("easy", "medium", "hard"):
        census = report["bands"][band]
        assert census["lessons"] == 3
        assert census["identifiable_lessons"] == 3
        assert census["total_demos"] == 12
        assert census["unique_inputs"] == 12
        assert all(count == 3 for count in census["rival_refuted_lessons"].values())
