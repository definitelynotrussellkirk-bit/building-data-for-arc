"""Focused semantic and regression tests for generator 0994294912bf."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import random
from pathlib import Path

import pytest

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs as load_canonical_pairs, find_root

TASK_ID = "0994294912bf"
ROOT = find_root(__file__)


def _load_generator():
    candidates = (
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        raise FileNotFoundError(f"generator not found under {ROOT}")
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
CATALOG = Catalog(ROOT)


def canonical_row() -> dict:
    rows = CATALOG.get(gen.TASK_ID)["variants"]
    assert len(rows) == 1
    return rows[0]


def canonical_pairs() -> list[dict]:
    return load_canonical_pairs(gen.TASK_ID, root=ROOT)


def normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_rule_hash_authority_and_canonical_pairs() -> None:
    row = canonical_row()
    source = row["program_solution"]
    assert gen.RULE_HASH == normalized_hash(source) == "ebb564e19380"
    assert CATALOG.describe(gen.TASK_ID)["rule_hash"] == gen.RULE_HASH

    pairs = canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen._mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_canonical_racket_exact_input_pure_and_a_b_a() -> None:
    pairs = canonical_pairs()
    inputs = [pairs[0]["input"], pairs[1]["input"], pairs[0]["input"]]
    originals = copy.deepcopy(inputs)
    applied = CATALOG.apply(gen.TASK_ID, inputs, timeout=120)
    assert applied["rule_hash_matches_catalog"]
    assert [row["output"] for row in applied["results"]] == [
        pairs[0]["output"],
        pairs[1]["output"],
        pairs[0]["output"],
    ]
    assert inputs == originals


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(994294912)
    before = random.getstate()
    first = gen.generate(71, 19, difficulty="hard")
    assert random.getstate() == before
    second = gen.generate(71, 19, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 9
    assert gen.generate(71, 19, difficulty="hard") == second
    assert gen.generate(72, 19, difficulty="hard") != second
    assert gen.generate(71, 20, difficulty="hard") != second


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exact_override_boundaries_and_observer(difficulty: str) -> None:
    index = 0
    for h in (8, 20):
        for w in (8, 20):
            for texture in gen._ALL_TEXTURES:
                grid = gen.generate(
                    1000 + index,
                    17,
                    difficulty=difficulty,
                    grid_h=h,
                    grid_w=w,
                    texture=texture,
                )
                assert gen.self_check(grid, difficulty=difficulty) == []
                assert gen.observe_overrides(grid) == {
                    "grid_h": h,
                    "grid_w": w,
                    "texture": texture,
                }
                index += 1


def test_four_profile_schedule_matches_the_demo_count() -> None:
    expected = ["solid", "multicolor", "br_decoy", "clip"]
    assert list(gen._LESSON_TEXTURES) == expected
    assert len(gen._LESSON_TEXTURES) == gen.EXAMPLES_NEEDED
    for band in ("easy", "medium", "hard"):
        grids = [
            gen.generate(42, i, difficulty=band)
            for i in range(gen.EXAMPLES_NEEDED + 1)
        ]
        observed = [gen.observe_overrides(grid)["texture"] for grid in grids]
        assert observed == expected + [expected[0]]
        demos = [{"input": grid, "output": gen._mirror(grid)} for grid in grids[:-1]]
        query = {"input": grids[-1], "output": gen._mirror(grids[-1])}
        assert gen.lesson_identifiable(demos, query) == []


def test_canonical_anchor_cadence_aligns_with_solid_schedule() -> None:
    for sample_index in range(0, 32, 4):
        grid = gen.generate(42, sample_index, difficulty="medium")
        assert gen.schedule_profile(42, sample_index, "medium") == "solid"
        assert gen.observe_overrides(grid)["texture"] == "solid"
        assert gen.strict_canonical_like(grid) == []


def test_br_decoy_slots_anchor_the_canonical_dimension_palette_envelope() -> None:
    for sample_index in range(2, 20, 4):
        grid = gen.generate(42, sample_index, difficulty="medium")
        assert gen.schedule_profile(42, sample_index, "medium") == "br_decoy"
        assert gen.observe_overrides(grid)["texture"] == "br_decoy"
        assert (len(grid), len(grid[0])) in {(9, 9), (11, 11)}
        assert len({value for row in grid for value in row}) == 4


def test_lawful_no_shape_is_accepted_identity() -> None:
    grid = gen.generate(87, 2, difficulty="medium", texture="no_shape")
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid)["texture"] == "no_shape"
    assert gen._mirror(grid) == grid
    assert "no_shape" in gen.LAWFUL_DEGENERATE_TEXTURES


def test_self_check_rejects_targeted_grammar_mutations() -> None:
    grid = gen.generate(4888, 12, difficulty="hard", grid_h=20, grid_w=20, texture="plain")
    analysis = gen._analyze(grid)
    assert analysis["errors"] == []
    gr, gc = analysis["gr"], analysis["gc"]

    broken_cross = copy.deepcopy(grid)
    broken_cross[gr][0] = 0
    assert any("full color-9" in err for err in gen.self_check(broken_cross))

    off_cross_nine = copy.deepcopy(grid)
    off_cross_nine[0][0] = 9
    assert any("splitting cross" in err for err in gen.self_check(off_cross_nine))

    broken_demo = copy.deepcopy(grid)
    tr_r, tr_c, _ = analysis["tr"][0]
    broken_demo[tr_r][gc + 1 + tr_c] = 0
    assert any("cardinal outline" in err for err in gen.self_check(broken_demo))

    disconnected_bl = copy.deepcopy(grid)
    occupied = {(r, c) for r, c, _ in analysis["bl"]}
    candidate = next(
        (r, c)
        for r in range(gr + 1, len(grid))
        for c in range(gc)
        if grid[r][c] == 0
        and all((r - (gr + 1) + dr, c + dc) not in occupied for dr, dc in gen._DIR4)
    )
    source_color = analysis["bl"][0][2]
    disconnected_bl[candidate[0]][candidate[1]] = source_color
    assert any("4-connected" in err for err in gen.self_check(disconnected_bl))

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 1, palette_kind="warm")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 1, difficulty="extreme")


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_cyclic_four_demo_window_is_identifiable(difficulty: str) -> None:
    """Any production-aligned start must teach every query-changing shortcut."""
    seed = 424242
    for start in range(len(gen._LESSON_TEXTURES)):
        pairs = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(seed, sample_index, difficulty=difficulty)
            pairs.append({"input": grid, "output": gen._mirror(grid)})
        reasons = gen.lesson_identifiable(pairs[:-1], pairs[-1])
        assert reasons == [], (
            f"difficulty={difficulty} start={start} "
            f"textures={[gen.observe_overrides(pair['input'])['texture'] for pair in pairs]} "
            f"reasons={reasons}"
        )


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_declared_competitors_are_refuted_in_every_cyclic_window(difficulty: str) -> None:
    expected = {
        "copy_whole_bl_shape",
        "preserve_per_cell_bl_colors",
        "use_modal_bl_color",
        "stamp_only_into_empty_br",
        "refuse_clipped_stamps",
        "encode_outline_count_only",
        "copy_worked_top_right_answer",
    }
    assert set(gen.LESSON_COMPETITORS) == expected
    seed = 424242
    for start in range(len(gen._LESSON_TEXTURES)):
        demos = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(seed, sample_index, difficulty=difficulty)
            demos.append({"input": grid, "output": gen._mirror(grid)})
        survivors = [
            name
            for name, rival in gen.LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
        ]
        assert survivors == [], (
            f"difficulty={difficulty} start={start} "
            f"textures={[gen.observe_overrides(pair['input'])['texture'] for pair in demos]} "
            f"survivors={survivors}"
        )


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_query_rotation_remains_identifiable(difficulty: str) -> None:
    seed = 919191
    for start in range(len(gen._LESSON_TEXTURES)):
        pairs = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(seed, sample_index, difficulty=difficulty)
            pairs.append({"input": grid, "output": gen._mirror(grid)})
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            survivors = [
                name
                for name, rival in gen.LESSON_COMPETITORS.items()
                if all(rival(pair["input"]) == pair["output"] for pair in demos)
            ]
            assert survivors == [], (
                f"difficulty={difficulty} start={start} query_index={query_index} "
                f"textures={[gen.observe_overrides(pair['input'])['texture'] for pair in pairs]} "
                f"survivors={survivors}"
            )
            assert gen.lesson_identifiable(demos, query) == []


def test_reusable_cyclic_probe_reports_source_bound_success() -> None:
    path = ROOT / "generators" / TASK_ID / "workspace" / "probe_cyclic_lessons.py"
    spec = importlib.util.spec_from_file_location("probe_cyclic_lessons", path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    report = probe.run_probe(seeds=(17,), starts=4, bands=("easy",))
    assert report["all_windows_identifiable"]
    assert report["generator_sha256"] == hashlib.sha256(
        (ROOT / "generators" / TASK_ID / "generator.py").read_bytes()
    ).hexdigest()
    assert report["bands"]["easy"]["identifiable_windows"] == 4
    assert report["bands"]["easy"]["identifiable_rotations"] == 20
