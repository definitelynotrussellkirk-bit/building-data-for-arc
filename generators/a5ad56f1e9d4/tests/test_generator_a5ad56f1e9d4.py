from __future__ import annotations

import importlib
import importlib.util
import hashlib
import itertools
import random
import json
import subprocess
import sys
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "a5ad56f1e9d4"


def _load_generator():
    local = Path(__file__).resolve().parents[1] / "generator.py"
    if local.exists():
        spec = importlib.util.spec_from_file_location(f"task_generator_{TASK_ID}", local)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


gen = _load_generator()
ROOT = find_root(__file__)


def _pairs():
    return canonical_pairs(TASK_ID, root=ROOT)


def _rect_and_markers(grid):
    fives = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5]
    assert fives
    r1 = min(r for r, _ in fives)
    r2 = max(r for r, _ in fives)
    c1 = min(c for _, c in fives)
    c2 = max(c for _, c in fives)
    markers = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]
    return (r1, c1, r2, c2), markers


def test_canonical_inputs_are_owned_and_python_mirror_matches_authority():
    pairs = _pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_rule_hash_and_all_exact_axes_round_trip_for_every_combination():
    assert gen.RULE_HASH == "7cf87a6a8bce"
    values = {
        "rect_h": (2, 3, 4),
        "rect_w": (2, 3, 4),
        "contact_mode": ("touching", "gapped"),
        "tie_mode": ("avoid", "include"),
        "marker_order": ("lower_first", "lower_second"),
    }
    for index, combination in enumerate(itertools.product(*values.values())):
        overrides = dict(zip(values, combination))
        grid = gen.generate(81173, index, difficulty=("easy", "medium", "hard")[index % 3], **overrides)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == overrides


@pytest.mark.parametrize("unknown", ["texture", "grid_h", "palette_kind", "typo_axis"])
def test_unknown_overrides_fail_loudly(unknown):
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, **{unknown: "anything"})


def test_default_schedule_has_profile_support_semantic_witnesses_and_rotation_safe_lessons():
    for band in ("easy", "medium", "hard"):
        pairs = []
        strict_hits = 0
        for sample_index in range(15):
            grid = gen.generate(20261006, sample_index, difficulty=band)
            assert gen.self_check(grid) == []
            strict_hits += gen.strict_canonical_like(grid) == []
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        assert strict_hits >= 4

        for start in range(len(pairs) - 3):
            window = pairs[start : start + 4]
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(window) if index != query_index]
                assert gen.lesson_identifiable(demos, window[query_index]) == []

        for witness_name in ("euclidean_metric_rebutted", "reading_order_tie_rebutted"):
            assert sum(gen.SEMANTIC_WITNESSES[witness_name](p["input"]) for p in pairs) >= 8


def test_default_distribution_varies_marker_sides_contact_and_rectangle_geometry():
    sides = set()
    contacts = set()
    shapes = set()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for sample_index in range(30):
            grid = gen.generate(101 + band_index, sample_index, difficulty=band)
            rect, markers = _rect_and_markers(grid)
            r1, c1, r2, c2 = rect
            shapes.add((r2 - r1 + 1, c2 - c1 + 1))
            contacts.add(gen.observe_overrides(grid)["contact_mode"])
            for r, c, _ in markers:
                if r < r1:
                    sides.add("top")
                if r > r2:
                    sides.add("bottom")
                if c < c1:
                    sides.add("left")
                if c > c2:
                    sides.add("right")
    assert sides == {"top", "right", "bottom", "left"}
    assert contacts == {"touching", "gapped"}
    assert {(2, 3), (3, 3), (3, 4)} <= shapes


def test_declared_canonical_shortcuts_really_fit_canonical_pairs_and_are_generated_against():
    pairs = _pairs()
    assert {"euclidean_distance", "reading_order_tie"} <= set(gen.CANONICAL_SHORTCUTS)
    for rival in gen.CANONICAL_SHORTCUTS.values():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs)

    generated = [gen.generate(73, index) for index in range(12)]
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert any(rival(grid) != gen.rule_mirror(grid) for grid in generated), name


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(4815162342)
    state = random.getstate()
    first = gen.generate(44, 7, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(44, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == gen.generate(44, 7, difficulty="medium")


def test_workspace_curriculum_probe_is_replayable(tmp_path):
    script = Path(__file__).resolve().parents[1] / "workspace" / "probe_curriculum.py"
    report = tmp_path / "probe.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--samples-per-band",
            "8",
            "--output",
            str(report),
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(report.read_text())
    assert payload["generator_sha256"] == hashlib.sha256(
        Path(gen.__file__).read_bytes()
    ).hexdigest()
    assert payload["canonical"]["owned_and_mirrored"] == "3/3"
    assert payload["exact_axes"]["passed"] == payload["exact_axes"]["requested"] == 72
    assert payload["lessons"]["ambiguous_rotations"] == 0
    assert payload["lessons"]["checked_rotations"] == 60
