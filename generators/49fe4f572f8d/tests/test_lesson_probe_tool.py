from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

GENERATOR_PATH = REPO_ROOT / "generators" / "49fe4f572f8d" / "generator.py"
GEN_SPEC = importlib.util.spec_from_file_location("probe_generator_49fe4f572f8d", GENERATOR_PATH)
assert GEN_SPEC is not None and GEN_SPEC.loader is not None
GEN = importlib.util.module_from_spec(GEN_SPEC)
GEN_SPEC.loader.exec_module(GEN)

PROBE_PATH = REPO_ROOT / "generators" / "49fe4f572f8d" / "workspace" / "lesson_probe.py"
PROBE_SPEC = importlib.util.spec_from_file_location("lesson_probe_49fe4f572f8d", PROBE_PATH)
assert PROBE_SPEC is not None and PROBE_SPEC.loader is not None
PROBE = importlib.util.module_from_spec(PROBE_SPEC)
PROBE_SPEC.loader.exec_module(PROBE)


def _pair(seed: int, sample_index: int, band: str) -> dict:
    grid = GEN.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": GEN._gravity_down(grid)}


def test_pinned_seed_matches_shared_profile_floor_recipe():
    expected = int(
        hashlib.sha256(
            b"profile-floor:v1:49fe4f572f8d:lesson:easy:0"
        ).hexdigest()[:12],
        16,
    )
    assert PROBE.pinned_seed("49fe4f572f8d", "easy", 0) == expected


def test_analysis_counts_unique_inputs_and_declared_competitors():
    pairs = [_pair(11, index, "easy") for index in range(6)]
    lesson = {
        "band": "easy",
        "seed": 11,
        "sample_index": 0,
        "demos": pairs[:5],
        "query": pairs[5],
    }
    report = PROBE.analyze_lessons(GEN, [lesson], canonical_pairs=[])

    assert report["lessons"] == 1
    assert report["unique_inputs"] == 6
    assert report["identifiable"] == 1
    assert report["unidentifiable"] == 0
    assert report["competitors_declared"] == sorted(GEN.LESSON_COMPETITORS)
    assert all(
        row["survived_demos"] == 0
        for row in report["competitors"].values()
    )


def test_canonical_rule_source_matches_generator_pin():
    source, label = PROBE.load_canonical_rule_source()
    assert label.endswith("puzzles.jsonl:program_solution")
    assert PROBE.normalized_rule_hash(source) == GEN.RULE_HASH


def test_tools_namespace_exposes_runtime_wrap_dependencies():
    PROBE.install_tools_namespace()
    from scripts.comment_solutions import parse_racket

    parsed = parse_racket('(rule! (gravity g "down"))')
    assert parsed is not None
