"""Portable regression tests for review-ddffbf0bc93a430d repairs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "6d33e42a400d"
ROOT = find_root(__file__)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _canonical_row() -> dict:
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    rows.append(row)
    assert rows, TASK_ID
    programs = {row["program_solution"] for row in rows}
    assert len(programs) == 1
    return rows[0]


@pytest.mark.parametrize(
    ("kwargs", "axis"),
    [
        ({"seed": True}, "seed"),
        ({"seed": False}, "seed"),
        ({"seed": 1.0}, "seed"),
        ({"seed": "1"}, "seed"),
        ({"sample_index": True}, "sample_index"),
        ({"sample_index": 1.0}, "sample_index"),
        ({"sample_index": "1"}, "sample_index"),
        ({"sample_index": -1}, "sample_index"),
        ({"difficulty": True}, "difficulty"),
        ({"difficulty": 0}, "difficulty"),
        ({"difficulty": 1.0}, "difficulty"),
        ({"difficulty": "__invalid_difficulty__"}, "difficulty"),
    ],
)
def test_generate_rejects_invalid_call_scalars(kwargs: dict, axis: str) -> None:
    call = {"seed": 7, "sample_index": 11, "difficulty": "easy"}
    call.update(kwargs)
    with pytest.raises(ValueError, match=axis):
        GEN.generate(**call)


def test_semantic_contract_is_executable_on_targeted_witnesses() -> None:
    assert GEN.strict_canonical_like is not GEN.self_check
    assert set(GEN.SEMANTIC_RIVALS) == {
        "copy_in_source_color",
        "copy_only_marker_coordinates",
    }
    assert set(GEN.SEMANTIC_WITNESSES) == {
        "paint_role_controls_copy_color",
        "full_terrain_profile_is_copied",
    }
    assert GEN.WITNESS_RIVALS == {
        "paint_role_controls_copy_color": ["copy_in_source_color"],
        "full_terrain_profile_is_copied": ["copy_only_marker_coordinates"],
    }
    assert GEN.LESSON_COMPETITORS == GEN.SEMANTIC_RIVALS

    cases = {
        "paint_role_controls_copy_color": ("public_h8", 0),
        "full_terrain_profile_is_copied": ("public_v8", 0),
    }
    for index, (witness_name, (profile, orientation)) in enumerate(cases.items()):
        grid = GEN.generate(
            91_000 + index,
            17,
            difficulty="hard",
            scene_profile=profile,
            orientation=orientation,
        )
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.SEMANTIC_WITNESSES[witness_name](grid) is True
        expected = GEN.solve_python(grid)
        assert any(
            GEN.SEMANTIC_RIVALS[name](grid) != expected
            for name in GEN.WITNESS_RIVALS[witness_name]
        )


def test_semantic_witnesses_are_sparse_but_cover_every_band() -> None:
    for band in ("easy", "medium", "hard"):
        counts = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
        for index in range(200):
            seed = int(
                hashlib.sha256(
                    f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
                ).hexdigest()[:12],
                16,
            )
            grid = GEN.generate(seed, index, difficulty=band)
            for name, predicate in GEN.SEMANTIC_WITNESSES.items():
                counts[name] += predicate(grid) is True
        assert all(1 <= count <= 20 for count in counts.values()), counts


def test_declared_rivals_are_refuted_by_each_complete_lesson() -> None:
    pairs = []
    for index in range(4):
        grid = GEN.generate(
            92_000,
            index,
            difficulty="medium",
            scene_profile=GEN.SCENE_PROFILES[index],
            orientation=index,
        )
        pairs.append({"input": grid, "output": GEN.solve_python(grid)})

    for query_index in range(len(pairs)):
        query = pairs[query_index]
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert GEN.lesson_identifiable(demos, query) == []
        for rival in GEN.LESSON_COMPETITORS.values():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def test_selected_authority_is_exact_and_archival_raw_code_is_preserved() -> None:
    program = _canonical_row()["program_solution"]
    archival_hash = "da48e42d4503abc714374aeba882dae09960d9807f0ff8619a680823882d13e5"
    relatives = (
        "shared/data/base/solutions/training/66ac4c3b__6d33e42a400d.json",
        "shared/data/base/solutions/augmented/66ac4c3b__c657675720c8.json",
    )
    for relative in relatives:
        base = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        target = base["racket_target"]
        assert target["target_code"] == program
        assert hashlib.sha256(target["raw_code"].encode()).hexdigest() == archival_hash
        assert target["raw_code"] != target["target_code"]
