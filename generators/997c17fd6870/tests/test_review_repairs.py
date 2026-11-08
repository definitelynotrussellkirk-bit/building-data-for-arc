from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK_ID = "997c17fd6870"
ROOT = find_root(__file__)
MODULE, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
RAW_AUTHORITY_SHA256 = "7ac779229e5e82c5a23b5d390e28bfbb71b3647626342788df44a30ed612f976"
BASE_RELATIVES = (
    "base/solutions/training/8ee62060__997c17fd6870.json",
    "base/solutions/augmented/8ee62060__68aa988b8901.json",
)


def _data_path(relative: str) -> Path:
    for prefix in (Path("shared/data"), Path("data")):
        candidate = Path(ROOT) / prefix / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(relative)


def _canonical_source() -> str:
    sources = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    sources.append(row["program_solution"])
    assert sources and len(set(sources)) == 1
    return sources[0]


def _episode() -> tuple[list[dict[str, list[list[int]]]], dict[str, list[list[int]]]]:
    grids = [
        MODULE.generate(91_000 + index, 137 + index, scene_profile=profile)
        for index, profile in enumerate(MODULE.SCENE_PROFILES[:4])
    ]
    pairs = [
        {"input": grid, "output": MODULE.rule_mirror(grid)}
        for grid in grids
    ]
    return pairs[:3], pairs[3]


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1", None])
def test_generate_rejects_nonliteral_integer_seed(bad_seed):
    with pytest.raises(TypeError, match="seed"):
        MODULE.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", None])
def test_generate_rejects_nonliteral_integer_sample_index(bad_index):
    with pytest.raises(TypeError, match="sample_index"):
        MODULE.generate(1, bad_index)


def test_generate_rejects_negative_sample_index_but_keeps_integer_seed_domain():
    with pytest.raises(ValueError, match="non-negative"):
        MODULE.generate(1, -1)
    assert MODULE.self_check(MODULE.generate(-1, 0)) == []


def test_semantic_contract_is_explicit_and_every_lawful_draw_refutes_rivals():
    assert MODULE.EXAMPLES_NEEDED == 3
    assert MODULE.MIN_STRICT_FRAC == 1.0
    assert set(MODULE.SEMANTIC_RIVALS) == {"identity", "whole_row_reflection"}
    assert MODULE.LESSON_COMPETITORS == MODULE.SEMANTIC_RIVALS
    assert MODULE.CANONICAL_SHORTCUTS == {}
    assert set(MODULE.SEMANTIC_WITNESSES) == {
        "tile_order_changes",
        "internal_tile_order_is_preserved",
    }
    assert MODULE.WITNESS_RIVALS == {
        "tile_order_changes": ["identity"],
        "internal_tile_order_is_preserved": ["whole_row_reflection"],
    }

    for profile in MODULE.SCENE_PROFILES:
        grid = MODULE.generate(77_000 + len(profile), len(profile), scene_profile=profile)
        expected = MODULE.rule_mirror(grid)
        assert MODULE.strict_canonical_like(grid) == []
        assert all(witness(grid) for witness in MODULE.SEMANTIC_WITNESSES.values())
        assert all(rival(grid) != expected for rival in MODULE.SEMANTIC_RIVALS.values())


def test_lesson_identifiability_accepts_valid_episode_and_rejects_bad_labels():
    demos, query = _episode()
    assert MODULE.lesson_identifiable(demos, query) == []
    assert MODULE.lesson_identifiable(demos[:2], query) == [
        "at least 3 demonstrations are required"
    ]

    corrupted = deepcopy(demos)
    corrupted[0]["output"] = deepcopy(corrupted[0]["input"])
    reasons = MODULE.lesson_identifiable(corrupted, query)
    assert any("demo 0 output differs from the selected rule" in reason for reason in reasons)


def test_canonical_inputs_are_strict_and_refute_each_declared_rival():
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        grid = pair["input"]
        expected = pair["output"]
        assert MODULE.strict_canonical_like(grid) == []
        assert MODULE.rule_mirror(grid) == expected
        assert all(rival(grid) != expected for rival in MODULE.SEMANTIC_RIVALS.values())


def test_selected_authorities_match_canonical_exactly_while_raw_archive_is_unchanged():
    source = _canonical_source()
    assert hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12] == MODULE.RULE_HASH
    for relative in BASE_RELATIVES:
        record = json.loads(_data_path(relative).read_text(encoding="utf-8"))
        raw = record["racket_target"]["raw_code"]
        target = record["racket_target"]["target_code"]
        assert hashlib.sha256(raw.encode()).hexdigest() == RAW_AUTHORITY_SHA256
        assert " ".join(raw.split()) == " ".join(source.split())
        assert target == source
