"""Focused regressions for the size-rank recoloring generator."""
from __future__ import annotations

import importlib
import importlib.util
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "2243e48c880b"


def _load_generator():
    try:
        return importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
    except ModuleNotFoundError:
        source = Path(__file__).resolve().parents[1] / "generator.py"
        spec = importlib.util.spec_from_file_location(f"task_generator_{TASK_ID}", source)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


gen = _load_generator()
ROOT = find_root(__file__)


def _objects(grid):
    """Racket-compatible row-major, monochromatic 4-connected components."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            queue = [(r, c)]
            seen.add((r, c))
            cells = []
            while queue:
                cr, cc = queue.pop(0)
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append({"color": color, "cells": cells, "size": len(cells)})
    return result


def _intended(grid):
    out = [[0 for _ in row] for row in grid]
    for color, obj in zip((2, 4, 8), sorted(_objects(grid), key=lambda item: item["size"])):
        for r, c in obj["cells"]:
            out[r][c] = color
    return out


def _color_total_rival(grid):
    totals = {}
    for obj in _objects(grid):
        totals[obj["color"]] = totals.get(obj["color"], 0) + obj["size"]
    out = [[0 for _ in row] for row in grid]
    ordered = sorted(_objects(grid), key=lambda item: totals[item["color"]])
    for color, obj in zip((2, 4, 8), ordered):
        for r, c in obj["cells"]:
            out[r][c] = color
    return out


def _repeated_color_witness():
    grid = [[0] * 9 for _ in range(8)]
    for c in (1, 2):
        grid[1][c] = 1             # size 2
    for c in (1, 2, 3):
        grid[3][c] = 2             # size 3
    for c in (1, 2, 3, 4):
        grid[5][c] = 1             # size 4, same input color as size 2
    return grid


def test_rule_hash_and_all_canonical_pairs_match_the_stable_size_oracle():
    assert gen.RULE_HASH == "d78310e1c969"
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert _intended(pair["input"]) == pair["output"]


def test_canonical_equal_size_objects_are_lawful_and_use_row_major_stable_ties():
    tied = canonical_pairs(TASK_ID, root=ROOT)[2]
    sizes = [obj["size"] for obj in _objects(tied["input"])]
    assert sizes == [4, 5, 5]
    assert gen.self_check(tied["input"]) == []
    assert _intended(tied["input"]) == tied["output"]


@pytest.mark.parametrize("size_pattern", ["distinct", "smallest_tie", "largest_tie", "all_tied"])
@pytest.mark.parametrize("palette_size", [1, 2, 3])
@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exact_overrides_round_trip(size_pattern, palette_size, difficulty):
    overrides = {
        "grid_h": 8,
        "grid_w": 9,
        "size_pattern": size_pattern,
        "palette_size": palette_size,
    }
    grid = gen.generate(1701, 9, difficulty=difficulty, **overrides)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == overrides


@pytest.mark.parametrize(
    "key,value",
    [
        ("unknown_axis", 1),
        ("grid_h", 7),
        ("grid_h", True),
        ("grid_w", 15),
        ("palette_size", 0),
        ("palette_size", 4),
        ("palette_size", "2"),
        ("size_pattern", "two_objects"),
    ],
)
def test_bad_overrides_fail_loudly(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, **{key: value})


def test_generation_is_deterministic_rng_pure_and_always_three_components():
    exact = set()
    patterns = set()
    palettes = set()
    for difficulty in ("easy", "medium", "hard"):
        for index in range(80):
            seed = 50_000 + index
            before = random.getstate()
            grid = gen.generate(seed, index, difficulty=difficulty)
            assert random.getstate() == before
            assert grid == gen.generate(seed, index, difficulty=difficulty)
            assert gen.self_check(grid) == []
            assert len(_objects(grid)) == 3
            observed = gen.observe_overrides(grid)
            patterns.add(observed["size_pattern"])
            palettes.add(observed["palette_size"])
            exact.add(tuple(tuple(row) for row in grid))
    # Defaults implement a three-slot curriculum. Less common lawful values
    # remain covered by the exact-override matrix above.
    assert patterns == {"distinct", "smallest_tie", "largest_tie"}
    assert palettes == {2, 3}
    assert len(exact) >= 150


def test_strongest_canonical_shortcut_fits_public_pairs_but_witness_refutes_it():
    rival = gen.CANONICAL_SHORTCUTS["color_total_frequency"]
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        assert rival(pair["input"]) == pair["output"]

    grid = _repeated_color_witness()
    assert gen.self_check(grid) == []
    assert rival(grid) == _color_total_rival(grid)
    assert rival(grid) != _intended(grid)
    assert gen.SEMANTIC_WITNESSES["color_total_counterexample"](grid)


def test_default_distribution_supplies_every_declared_rival_counterexample():
    grids = [gen.generate(720_000, i, difficulty="medium") for i in range(180)]
    for name, witness in gen.SEMANTIC_WITNESSES.items():
        assert any(witness(grid) for grid in grids), name
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witness = gen.SEMANTIC_WITNESSES[witness_name]
        for rival_name in rival_names:
            rival = gen.SEMANTIC_RIVALS[rival_name]
            assert any(witness(grid) and rival(grid) != _intended(grid) for grid in grids)


def test_combined_generated_demonstrations_refute_every_declared_competitor():
    pairs = []
    for i in range(90):
        grid = gen.generate(880_031, i, difficulty="hard")
        pairs.append({"input": grid, "output": _intended(grid)})
    assert gen.lesson_identifiable(pairs, {"input": pairs[0]["input"]}) == []
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in pairs), name


def test_self_check_rejects_wrong_component_counts_and_malformed_grids():
    bad = [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 9 for _ in range(8)],
        [[0] * 9 for _ in range(8)],
    ]
    two = [[0] * 9 for _ in range(8)]
    two[1][1] = 1
    two[5][5] = 2
    bad.append(two)
    for grid in bad:
        assert gen.self_check(grid)


def test_default_schedule_balances_rotation_safe_witnesses_and_canonical_anchors():
    canonical_profiles = {(8, 10, 3), (9, 9, 3), (8, 11, 3), (9, 10, 3)}
    for difficulty in ("easy", "medium", "hard"):
        for index in range(18):
            grid = gen.generate(991_337, index, difficulty=difficulty)
            observed = gen.observe_overrides(grid)
            if index % 3 == 2:
                assert (observed["grid_h"], observed["grid_w"], observed["palette_size"]) in canonical_profiles
                assert observed["size_pattern"] == "distinct"
            else:
                assert observed["palette_size"] == 2
                assert observed["size_pattern"] in {"smallest_tie", "largest_tie"}
                for rival in gen.LESSON_COMPETITORS.values():
                    assert rival(grid) != _intended(grid)


def test_every_consecutive_lesson_and_query_rotation_refutes_declared_rivals():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = []
            for index in range(start, start + 4):
                grid = gen.generate(661_029, index, difficulty=difficulty)
                pairs.append({"input": grid, "output": _intended(grid)})
            assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                query = pairs[query_index]
                assert gen.lesson_identifiable(demos, query) == []


def test_workspace_lesson_probe_is_source_bound_and_rotation_clean(tmp_path):
    import json
    import os
    import subprocess
    import sys

    script = Path(__file__).resolve().parents[1] / "workspace" / "lesson_probe.py"
    report_path = tmp_path / "lesson-probe.json"
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT / "shared" / "runtime"), str(ROOT / "shared"), env.get("PYTHONPATH", "")]
    )
    completed = subprocess.run(
        [sys.executable, str(script), "--starts", "3", "--seed", "404", "--out", str(report_path)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads(report_path.read_text())
    assert report["generator_sha256"]
    assert report["declared_competitors"] == sorted(gen.LESSON_COMPETITORS)
    assert report["canonical_shortcuts"]["color_total_frequency"]["fits_all"] is True
    assert report["counts"]["lessons"] == 9
    assert report["counts"]["rotations"] == 36
    assert report["counts"]["ambiguous_rotations"] == 0
    assert report["counts"]["hook_failures"] == 0


def test_retained_color_total_counterexample_matches_current_source_and_oracles():
    import hashlib
    import json

    task_dir = Path(__file__).resolve().parents[1]
    record = json.loads((task_dir / "counterexamples" / "color_total_frequency.json").read_text())
    grid = record["input"]
    source_hash = hashlib.sha256((task_dir / "generator.py").read_bytes()).hexdigest()
    assert record["generator_sha256"] == source_hash
    assert record["rule_hash"] == gen.RULE_HASH
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == record["racket_output"]
    assert gen.CANONICAL_SHORTCUTS[record["rival_name"]](grid) == record["rival_output"]
    assert record["rival_output"] != record["racket_output"]
