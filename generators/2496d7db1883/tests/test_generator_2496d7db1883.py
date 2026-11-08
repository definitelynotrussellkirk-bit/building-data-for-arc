"""Focused semantic and contract regressions for generator 2496d7db1883."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


TASK_ID = "2496d7db1883"
ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
sys.path.insert(0, str(ROOT / "shared" / "runtime"))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"generator_{TASK_ID}_under_test", GENERATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _canonical_pairs() -> list[dict]:
    with (ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            test = row["test"]
            tests = test if isinstance(test, list) else [test]
            return [*row["train"], *tests]
    raise AssertionError("canonical task row missing")


def test_canonical_pairs_are_accepted_and_python_mirror_matches() -> None:
    for pair in _canonical_pairs():
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.expected_output(source) == pair["output"]
        assert source == pair["input"]


def test_known_hard_seed_stays_inside_generated_arc_limit() -> None:
    grid = GEN.generate(0, 1, difficulty="hard")
    assert 1 <= len(grid) <= 30
    assert 1 <= len(grid[0]) <= 30
    assert GEN.self_check(grid, difficulty="hard") == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_axes_are_observable_in_every_difficulty_band(band: str | None) -> None:
    requested = {
        "room_h": 4,
        "room_w": 5,
        "motif_size": 4,
        "layout": "grid",
        "role_order": "grouped",
        "mapping_order": "reverse",
        "motif_relation": "same_shape_shifted",
    }
    grid = GEN.generate(417, 29, difficulty=band, **requested)
    assert GEN.observe_overrides(grid) == requested
    assert GEN.self_check(grid, difficulty=band, meta={"overrides": requested}) == []



def test_each_difficulty_band_has_a_pinned_canonical_profile_anchor() -> None:
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]),
         len({value for row in pair["input"] for value in row}))
        for pair in _canonical_pairs()
    }
    for band in ("easy", "medium", "hard"):
        hits = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            hits += profile in canonical_profiles
        assert hits >= 1, band

def test_unknown_override_is_rejected_instead_of_silently_ignored() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, typoed_mapping_order="reverse")


def test_scheduled_octet_covers_each_shortcut_rebuttal_branch() -> None:
    observed = [GEN.observe_overrides(GEN.generate(812, index, difficulty="hard"))
                for index in range(8)]
    assert {item["layout"] for item in observed} == {"row", "grid"}
    assert {item["role_order"] for item in observed} == {"grouped", "interleaved"}
    assert {item["mapping_order"] for item in observed} == {"same", "reverse"}
    assert {item["motif_relation"] for item in observed} == {
        "different_shapes",
        "same_shape_shifted",
    }
    assert {GEN.schedule_profile(812, index, "hard") for index in range(8)} == set(
        GEN.SCHEDULE_PROFILES
    )


def test_explicit_cases_disagree_with_order_and_offset_shortcuts() -> None:
    reverse_shifted = GEN.generate(
        33,
        7,
        difficulty="hard",
        room_h=4,
        room_w=5,
        motif_size=4,
        layout="grid",
        role_order="grouped",
        mapping_order="reverse",
        motif_relation="same_shape_shifted",
    )
    intended = GEN.expected_output(reverse_shifted)
    assert GEN.SEMANTIC_RIVALS["same_reading_order"](reverse_shifted) != intended
    assert GEN.SEMANTIC_RIVALS["motif_shape_ignores_room_offset"](reverse_shifted) != intended
    assert GEN.SEMANTIC_RIVALS["nearest_example"](reverse_shifted) != intended

    same = GEN.generate(
        34,
        8,
        difficulty="easy",
        room_h=3,
        room_w=4,
        motif_size=3,
        layout="row",
        role_order="interleaved",
        mapping_order="same",
        motif_relation="different_shapes",
    )
    assert GEN.SEMANTIC_RIVALS["reverse_reading_order"](same) != GEN.expected_output(same)


def test_self_check_rejects_an_unmatched_query_motif() -> None:
    grid = GEN.generate(
        91,
        5,
        room_h=4,
        room_w=5,
        motif_size=4,
        layout="row",
        role_order="grouped",
        mapping_order="same",
        motif_relation="different_shapes",
    )
    info = GEN._analyze(grid)
    query = info["queries"][0]
    changed = copy.deepcopy(grid)
    for row, col in query["motif_abs"]:
        changed[row][col] = 0
    row0, col0, row1, col1 = query["bbox"]
    replacement = next(
        (row, col)
        for row in range(row0, row1 + 1)
        for col in range(col0, col1 + 1)
        if changed[row][col] == 0
        and (row - row0, col - col0) not in {key["motif"][0] for key in info["keys"]}
    )
    changed[replacement[0]][replacement[1]] = 6
    assert any("match" in reason for reason in GEN.self_check(changed))


def test_generation_is_replayable_fresh_and_global_rng_pure() -> None:
    random.seed(99173)
    before = random.getstate()
    first = GEN.generate(19, 7, difficulty="medium")
    after = random.getstate()
    second = GEN.generate(19, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert before == after
    first[0][0] = 7
    assert GEN.generate(19, 7, difficulty="medium") == second
