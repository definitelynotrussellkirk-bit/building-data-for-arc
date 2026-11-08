"""Source-bound regressions for the canonical repair and proposed direction prototype.

These tests distinguish production canonical-generator requirements from the
separate, non-approved episode-level parametric prototype.
"""
from __future__ import annotations

from functools import cache
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "a4863798ed70"
ROOT = find_root(__file__)
GEN, SELECTED_SOURCE, SELECTED_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _prototype_path() -> Path:
    identity = f"generators/{TASK_ID}/workspace/parametric/prototype.py"
    manifest = ROOT / "RUNTIME_MANIFEST.json"
    if manifest.is_file():
        entries = [
            row
            for row in json.loads(manifest.read_text(encoding="utf-8"))["files"]
            if row.get("library_path") == identity
        ]
        entries.sort(key=lambda row: row.get("runtime_path") == identity)
        assert entries, "runtime manifest must transport the parametric prototype"
        return ROOT / entries[0]["runtime_path"]
    return SELECTED_SOURCE.parent / "workspace/parametric/prototype.py"


@cache
def _load_prototype():
    path = _prototype_path()
    assert path.is_file(), "cycle-direction parametric prototype is not implemented"
    spec = importlib.util.spec_from_file_location("a4863798ed70_parametric_prototype", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_nonliteral_integer_seed(bad_seed):
    with pytest.raises(TypeError, match="seed"):
        GEN.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_nonliteral_integer_sample_index(bad_index):
    with pytest.raises(TypeError, match="sample_index"):
        GEN.generate(0, bad_index)


def test_generate_rejects_negative_sample_index():
    with pytest.raises(ValueError, match="sample_index"):
        GEN.generate(0, -1)


def test_noncanonical_rivals_are_lesson_competitors_not_canonical_shortcuts():
    assert GEN.CANONICAL_SHORTCUTS == {}
    assert set(GEN.LESSON_COMPETITORS) == set(GEN.SEMANTIC_RIVALS)
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    for name, rival in GEN.SEMANTIC_RIVALS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in pairs), name


def _grid_sha256(grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


@pytest.mark.parametrize(
    "seed,sample_index,difficulty,profile,expected",
    [
        (1700, 70, None, "canonical_3x5_20x22", "54773000ba0cd8e4c553d85aeb9773cfcf1528fff55f940f55f99b1b3e70200f"),
        (1701, 71, "easy", "canonical_4x5_22x21", "fbea1997b240eeeb6cd36a96a8014d31707f549ecea582a9c2bcf0cce61b87ff"),
        (1704, 74, "medium", "generalized_4x7_25x24", "af7b8f175cafb8a125cb037cde77cff739b47f1b5d444a77459e021d6e6ab979"),
        (1705, 75, "hard", "canonical_5x7_27x27", "d8adf8d24e7153690a4d103e93de71d35a349eb2d1fc281ef28855ded02b5b5c"),
    ],
)
def test_repair_preserves_valid_generation_bytes(seed, sample_index, difficulty, profile, expected):
    grid = GEN.generate(seed, sample_index, difficulty=difficulty, scene_profile=profile)
    assert _grid_sha256(grid) == expected


def test_prototype_declares_bounded_episode_level_direction_parameter():
    p = _load_prototype()
    assert p.PARAMETER == {
        "name": "cycle_direction",
        "values": ["clockwise", "counterclockwise"],
        "default": "clockwise",
        "input_constraints": "unchanged; 3..5 distinct-color framed icons",
    }
    assert p.program_for() == p.canonical_record()["program_solution"]
    assert p.program_for("counterclockwise") != p.program_for()
    with pytest.raises(ValueError, match="cycle_direction"):
        p.program_for("random")


def test_default_parametric_program_matches_all_canonical_pairs_through_racket():
    p = _load_prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
            assert p.execute(bridge, p.program_for(), pair["input"]) == pair["output"]


@pytest.mark.parametrize("seed,expected_direction", [(0, "clockwise"), (1, "counterclockwise")])
def test_complete_episode_is_deterministic_private_and_parameter_identifiable(seed, expected_direction):
    p = _load_prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        public, private = p.generate_episode(seed, bridge)
        public_again, private_again = p.generate_episode(seed, bridge)

        assert public == public_again
        assert private == private_again
        assert private["parameter"] == {"cycle_direction": expected_direction}
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == GEN.EXAMPLES_NEEDED
        assert len(public["test"]) == 1
        assert set(public["test"][0]) == {"input"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])

        rival = next(value for value in p.DIRECTIONS if value != expected_direction)
        assert private["rival_checks"][expected_direction]["matches_all_demonstrations"]
        assert not private["rival_checks"][rival]["matches_all_demonstrations"]
        assert private["rival_checks"][rival]["distinguishing_demo_indices"] == [0, 1, 2]
        assert len(private["query_answers"]) == 1

        selected_program = p.program_for(expected_direction)
        rival_program = p.program_for(rival)
        for pair in public["train"]:
            assert p.execute(bridge, selected_program, pair["input"]) == pair["output"]
            assert p.execute(bridge, rival_program, pair["input"]) != pair["output"]
        assert p.execute(bridge, selected_program, public["test"][0]["input"]) == private["query_answers"][0]
        assert p.execute(bridge, selected_program, public["test"][0]["input"]) != p.execute(
            bridge, rival_program, public["test"][0]["input"]
        )


def test_materialized_public_challenges_omit_hidden_rule_and_query_answer(tmp_path):
    p = _load_prototype()
    manifest = p.write_evidence(tmp_path, seeds=[0, 1])
    assert manifest["status"] == "proposed prototype; not production-approved"
    assert manifest["parameter"] == p.PARAMETER
    assert len(list((tmp_path / "rules").glob("*.rkt"))) == 2
    assert len(list((tmp_path / "public").glob("*.json"))) == 2
    assert len(list((tmp_path / "private").glob("*.json"))) == 2

    for path in (tmp_path / "public").glob("*.json"):
        public_text = path.read_text(encoding="utf-8")
        public = json.loads(public_text)
        assert "cycle_direction" not in public_text
        assert "program" not in public_text
        assert set(public["test"][0]) == {"input"}

    for direction in p.DIRECTIONS:
        code = (tmp_path / "rules" / f"{direction}.rkt").read_text(encoding="utf-8")
        assert code == p.program_for(direction)
        assert hashlib.sha256(code.encode()).hexdigest() == manifest["program_sha256"][direction]
