from __future__ import annotations

import importlib
import json
from collections import Counter
from pathlib import Path


TASK_ID = "48bda9528e71"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[3]


def _canonical_pairs():
    pairs = []
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        for split in ("train", "test"):
            for pair in row.get(split, []):
                pairs.append(pair)
    return pairs


def test_official_signature_bank_is_complete_and_exact():
    pairs = _canonical_pairs()
    assert len(pairs) == 6
    signatures = {MODULE.profile_signature(pair["input"]) for pair in pairs}
    assert len(signatures) == 3
    assert signatures == set(MODULE.CANONICAL_PROFILE_SIGNATURES)
    assert all(MODULE.canonical_profile_signature(pair["input"]) for pair in pairs)


def test_python_rule_mirror_matches_every_official_output():
    for pair in _canonical_pairs():
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]


def test_canonical_prior_reaches_every_profile_in_every_band():
    for band in ("easy", "medium", "hard"):
        counts = Counter()
        for seed in range(300):
            grid = MODULE.generate(seed, seed * 17 + 3, difficulty=band)
            signature = MODULE.canonical_profile_signature(grid)
            if signature is not None:
                counts[signature] += 1
        assert set(counts) == set(MODULE.CANONICAL_PROFILE_SIGNATURES)
        assert sum(counts.values()) >= 75


def test_recombined_official_features_are_not_strict_profile():
    seven = next(
        pair["input"]
        for pair in _canonical_pairs()
        if len(pair["input"]) == 7
    )
    recombined = [row[:] for row in seven]
    non_bg = Counter(value for row in recombined for value in row if value != 8)
    rare_color = min(non_bg, key=non_bg.get)
    common_color = max(non_bg, key=non_bg.get)
    rare_cells = [
        (row, col)
        for row, values in enumerate(recombined)
        for col, value in enumerate(values)
        if value == rare_color
    ]
    # Combine the official 7x7 geometry with the official 5x5 rare-count=1
    # profile.  The task grammar remains valid, but the complete linked
    # empirical profile must reject this independently recombined near-miss.
    for row, col in rare_cells[1:]:
        recombined[row][col] = common_color

    assert MODULE.self_check(recombined) == []
    assert MODULE.canonical_profile_signature(recombined) is None
