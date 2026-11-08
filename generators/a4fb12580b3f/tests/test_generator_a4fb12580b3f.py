from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

from puzzle_generators.per_puzzle.a4fb12580b3f import generator as gen

ROOT = Path(__file__).resolve().parents[1]


def _canonical_row() -> dict:
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        if '"task_id": "a4fb12580b3f"' in line:
            return json.loads(line)
    raise AssertionError("canonical task row not found")


def _roles(grid):
    components = gen._components(grid)
    anchor = next(cells for color, cells in components if color == 1)
    touching = [(color, cells) for color, cells in components if color != 1 and gen._touches(anchor, cells)]
    distractors = [(color, cells) for color, cells in components if color != 1 and not gen._touches(anchor, cells)]
    return anchor, touching, distractors


def test_rule_hash_matches_normalized_canonical_program() -> None:
    src = _canonical_row()["program_solution"]
    actual = hashlib.sha256(" ".join(src.split()).encode()).hexdigest()[:12]
    assert gen.RULE_HASH == actual == "c58ce5ec72e9"


def test_self_check_accepts_every_canonical_input() -> None:
    row = _canonical_row()
    pairs = list(row["train"]) + [row["test"]]
    assert len(pairs) == 3
    assert [gen.self_check(pair["input"]) for pair in pairs] == [[], [], []]


def test_boundary_overrides_are_exact_and_replayable() -> None:
    for band in ("easy", "medium", "hard"):
        for h, w, neighbors, distractors, shape, palette in (
            (7, 8, 2, 2, "dot", "default"),
            (15, 16, 4, 4, "elbow", "varied"),
            (7, 16, 4, 2, "domino", "cool"),
        ):
            kwargs = dict(
                difficulty=band,
                grid_h=h,
                grid_w=w,
                neighbor_count=neighbors,
                distractor_count=distractors,
                anchor_shape=shape,
                palette_kind=palette,
            )
            first = gen.generate(91, 7, **kwargs)
            second = gen.generate(91, 7, **kwargs)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            assert gen.observe_overrides(first) == {
                "grid_h": h,
                "grid_w": w,
                "neighbor_count": neighbors,
                "distractor_count": distractors,
            }
            assert gen.self_check(first) == []


def test_generation_preserves_process_global_rng_state() -> None:
    random.seed(20260724)
    before = random.getstate()
    gen.generate(123, 4, difficulty="hard")
    after = random.getstate()
    assert after == before


def test_self_check_rejects_targeted_structural_impostors() -> None:
    grid = gen.generate(220, 3, difficulty="hard", neighbor_count=4, distractor_count=4)
    anchor, touching, distractors = _roles(grid)

    no_anchor = copy.deepcopy(grid)
    for r, c in anchor:
        no_anchor[r][c] = 0
    assert gen.self_check(no_anchor)

    duplicate_anchor = copy.deepcopy(grid)
    for r, row in enumerate(duplicate_anchor):
        for c, value in enumerate(row):
            if value == 0 and all(abs(r - ar) + abs(c - ac) > 1 for ar, ac in anchor):
                duplicate_anchor[r][c] = 1
                break
        else:
            continue
        break
    assert any("exactly one" in msg for msg in gen.self_check(duplicate_anchor))

    no_neighbors = copy.deepcopy(grid)
    for _, cells in touching:
        for r, c in cells:
            no_neighbors[r][c] = 0
    assert any("edge-touching" in msg for msg in gen.self_check(no_neighbors))

    no_distractors = copy.deepcopy(grid)
    for _, cells in distractors:
        for r, c in cells:
            no_distractors[r][c] = 0
    assert any("separated" in msg for msg in gen.self_check(no_distractors))

    hidden_transform = copy.deepcopy(grid)
    for _, cells in touching:
        for r, c in cells:
            hidden_transform[r][c] = 4
    assert any("visibly change" in msg for msg in gen.self_check(hidden_transform))


def test_distribution_rebuts_color_global_and_fixed_marker_shortcuts() -> None:
    anchor_sizes = set()
    anchor_positions = set()
    neighbor_counts = set()
    output_neighbor_indices = []
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for sample_index in range(25):
            grid = gen.generate(500 + 100 * band_index + sample_index, sample_index, difficulty=band)
            anchor, touching, distractors = _roles(grid)
            anchor_sizes.add(len(anchor))
            anchor_positions.add(min(anchor))
            neighbor_counts.add(len(touching))
            touching_colors = {color for color, _ in touching}
            distractor_colors = {color for color, _ in distractors}
            assert touching_colors & distractor_colors, "same-color non-neighbor witness missing"
            assert any(color != 4 for color, _ in touching)
            if band == "medium" and any(color == 4 for color, _ in touching):
                output_neighbor_indices.append(sample_index)
    assert anchor_sizes == {1, 2, 3}
    assert len(anchor_positions) >= 10
    assert neighbor_counts == {2, 3, 4}
    assert output_neighbor_indices == [1, 6, 11, 16, 21]
