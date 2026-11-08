"""Focused tests for the non-production alignment-anchor prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

for _ancestor in Path(__file__).resolve().parents:
    _runtime = _ancestor / "shared" / "runtime"
    if (_runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(_runtime))
        break

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root

ROOT = find_root(__file__)
SOURCE = ROOT / "generators/659980b6f715/workspace/parametric/alignment_anchor.py"
SPEC = importlib.util.spec_from_file_location("alignment_anchor_prototype", SOURCE)
PROTO = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(PROTO)


def canonical_program():
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == "659980b6f715":
                return row["program_solution"]
    raise AssertionError("canonical task missing")


def test_default_setting_is_exact_canonical_program():
    assert PROTO.DEFAULT_ALIGNMENT == "top_left"
    assert PROTO.materialize_program("top_left", root=ROOT) == canonical_program()
    assert PROTO.materialize_program("bottom_right", root=ROOT) != canonical_program()


def test_seeded_parameter_is_resolved_once_and_deterministically():
    assert PROTO.choose_alignment(41, "seeded") == PROTO.choose_alignment(41, "seeded")
    assert {PROTO.choose_alignment(seed, "seeded") for seed in range(20)} == set(PROTO.ALIGNMENTS)


def test_each_setting_executes_a_complete_identifiable_episode_in_racket():
    with RacketBridge(timeout=10, startup_timeout=60) as bridge:
        for index, alignment in enumerate(PROTO.ALIGNMENTS):
            episode = PROTO.generate_episode(700 + index, alignment=alignment, root=ROOT, bridge=bridge)
            assert episode["parameter"] == {"alignment_anchor": alignment}
            assert len(episode["train"]) == 3 and len(episode["test"]) == 1
            assert episode["assessment"]["identified"] is True
            rival = next(name for name in PROTO.ALIGNMENTS if name != alignment)
            assert episode["assessment"]["rivals"][rival]["demo_refutations"]
            assert episode["assessment"]["rivals"][rival]["query_differs"] is True


def test_evidence_export_separates_public_challenges_from_private_answers(tmp_path):
    report = PROTO.build_evidence(900, tmp_path, root=ROOT)
    assert report["status"] == "pass"
    assert report["episodes_identified"] == 2
    for path in sorted((tmp_path / "public").glob("*.json")):
        public = json.loads(path.read_text())
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        serialized = path.read_text()
        assert "alignment_anchor" not in serialized
        assert "program" not in serialized
