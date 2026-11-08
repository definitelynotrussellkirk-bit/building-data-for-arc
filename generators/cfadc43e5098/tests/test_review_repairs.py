from __future__ import annotations

import hashlib
import json

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK_ID = "cfadc43e5098"
ROOT = find_root(__file__)
MODULE, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
_BASE_ROOT = next(
    path for path in (ROOT / "data" / "base", ROOT / "shared" / "data" / "base")
    if path.is_dir()
)
BASE_PATHS = (
    _BASE_ROOT / "solutions" / "training" / "f3b10344__cfadc43e5098.json",
    _BASE_ROOT / "solutions" / "augmented" / "f3b10344__2849735f278d.json",
)


def canonical_rows():
    rows = []
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            rows.append(row)
    assert [(row["source"], len(row["train"]), len(row["test"])) for row in rows] == [
        ("training", 3, 1),
        ("augmented", 4, 0),
    ]
    identities = [
        (pair["variant"], pair["split"], pair["pair_index"])
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    ]
    assert identities == [
        (0, "train", 0), (0, "train", 1), (0, "train", 2), (0, "test", 0),
        (1, "train", 0), (1, "train", 1), (1, "train", 2), (1, "train", 3),
    ]
    return rows


def normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def test_selected_authorities_match_canonical_and_archival_code_is_preserved():
    source = canonical_rows()[0]["program_solution"]
    for path in BASE_PATHS:
        base = json.loads(path.read_text(encoding="utf-8"))
        raw_code = base["racket_target"]["raw_code"]
        assert raw_code != source
        assert normalized_hash(raw_code) == normalized_hash(source)
        assert base["racket_target"]["target_code"] == source


@pytest.mark.parametrize("seed", [True, False, 1.5, "1", None])
def test_seed_must_be_a_literal_integer(seed):
    with pytest.raises(TypeError):
        MODULE.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, 1.5, "1", None])
def test_sample_index_must_be_a_literal_integer(sample_index):
    with pytest.raises(TypeError):
        MODULE.generate(1, sample_index)


def test_sample_index_must_be_nonnegative():
    with pytest.raises(ValueError):
        MODULE.generate(1, -1)


def test_any_color_blocker_shortcut_fits_canonical_but_generated_witness_refutes_it():
    rival = MODULE.SEMANTIC_RIVALS["any_color_blocks"]
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert rival(pair["input"]) == pair["output"]

    witness = MODULE.generate(810_000, 16, scene_profile="horizontal_pair")
    name = "different_color_obstacle_does_not_block"
    assert MODULE.SEMANTIC_WITNESSES[name](witness) is True
    assert rival(witness) != MODULE.rule_mirror(witness)
    assert MODULE.WITNESS_RIVALS[name] == ["any_color_blocks"]


def test_normal_schedule_refutes_any_color_shortcut_in_every_three_demo_window_and_rotation():
    """Every cyclic 3-demo window must contain a shortcut-refuting pair."""
    rival = MODULE.SEMANTIC_RIVALS["any_color_blocks"]
    period = len(MODULE.SCENE_PROFILES)
    assert MODULE.LESSON_SCHEDULE_PERIOD == period == 12
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(4):
            for start in range(period):
                pairs = []
                for offset in range(4):
                    grid = MODULE.generate(seed, start + offset, difficulty=difficulty)
                    pairs.append({"input": grid, "output": MODULE.rule_mirror(grid)})
                # Production: first three are demos and the fourth is query.
                assert any(rival(pair["input"]) != pair["output"] for pair in pairs[:3]), (
                    difficulty, seed, start
                )
                # One-query rotations: holding out any pair leaves three demos.
                for held_out in range(4):
                    demos = [pair for index, pair in enumerate(pairs) if index != held_out]
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                        difficulty, seed, start, held_out
                    )
