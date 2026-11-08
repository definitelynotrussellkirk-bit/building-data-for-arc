from __future__ import annotations

import importlib.util
from pathlib import Path


GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("repair_7fe59337a0b4", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


EXPECTED_SECTORS = {
    "north",
    "northeast",
    "east",
    "southeast",
    "south",
    "southwest",
    "west",
    "northwest",
}
CARDINAL_SECTORS = {"north", "east", "south", "west"}
DIAGONAL_SECTORS = EXPECTED_SECTORS - CARDINAL_SECTORS


def _pair(seed: int, index: int, band: str) -> dict[str, list[list[int]]]:
    grid = gen.generate(seed, index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_default_schedule_covers_all_eight_source_sectors():
    assert gen.EXAMPLES_NEEDED == 8
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            analyses = [
                gen._analyze(gen.generate(5107, index, difficulty=band))
                for index in range(start, start + gen.EXAMPLES_NEEDED)
            ]
            assert {analysis["source_sector"] for analysis in analyses} == EXPECTED_SECTORS
            assert {analysis["scene_profile"] for analysis in analyses} == set(
                gen.SCENE_PROFILES
            )


def test_canonical_north_profile_is_exact_observable_and_strict():
    for size in (9, 15):
        grid = gen.generate(
            5108,
            0,
            difficulty="hard",
            canvas_size=size,
            motif_color=8,
            scene_profile="canonical_north_l3",
        )
        analysis = gen._analyze(grid)
        assert analysis["errors"] == []
        assert analysis["source_sector"] == "north"
        assert analysis["scene_profile"] == "canonical_north_l3"
        assert gen.observe_overrides(grid) == {
            "canvas_size": size,
            "motif_color": 8,
            "scene_profile": "canonical_north_l3",
        }
        if size in (9, 11):
            assert gen.strict_canonical_like(grid) == []


def test_every_profile_is_exact_at_canvas_boundaries():
    for size in (9, 15):
        for index, profile in enumerate(gen.SCENE_PROFILES):
            grid = gen.generate(
                5200 + index,
                index,
                difficulty="hard",
                canvas_size=size,
                motif_color=1 + index % 8,
                scene_profile=profile,
            )
            analysis = gen._analyze(grid)
            assert analysis["errors"] == []
            assert analysis["scene_profile"] == profile
            assert analysis["source_sector"] == gen._PROFILE_SECTORS[profile]
            assert gen.observe_overrides(grid)["scene_profile"] == profile


def test_diagonal_only_shortcut_is_executable_and_refuted_by_each_lesson():
    rival = gen.SEMANTIC_RIVALS["diagonal_source_only"]
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            demos = [_pair(5301, index, band) for index in range(start, start + 8)]
            assert any(
                rival(demo["input"]) != demo["output"] for demo in demos
            ), (band, start)
            diagonal = next(
                demo
                for demo in demos
                if gen._analyze(demo["input"])["source_sector"] in DIAGONAL_SECTORS
            )
            cardinal = next(
                demo
                for demo in demos
                if gen._analyze(demo["input"])["source_sector"] in CARDINAL_SECTORS
            )
            assert rival(diagonal["input"]) == diagonal["output"]
            assert rival(cardinal["input"]) != cardinal["output"]


def test_every_single_query_rotation_is_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            bundle = [_pair(5402, index, band) for index in range(start, start + 9)]
            for query_index in range(len(bundle)):
                query = bundle[query_index]
                demos = bundle[:query_index] + bundle[query_index + 1 :]
                assert gen.lesson_identifiable(demos, query) == [], (
                    band,
                    start,
                    query_index,
                )
                sectors = {
                    gen._analyze(demo["input"])["source_sector"] for demo in demos
                }
                assert sectors & CARDINAL_SECTORS
                assert sectors & DIAGONAL_SECTORS
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(
                        rival(demo["input"]) != demo["output"] for demo in demos
                    ), (band, start, query_index, name)


def test_every_declared_witness_names_a_rival_disagreement():
    for name in gen.SEMANTIC_WITNESSES:
        assert gen.WITNESS_RIVALS.get(name), name


def test_retained_diagonal_only_counterexample_replays():
    import hashlib
    import json

    path = Path(__file__).resolve().parents[1] / "counterexamples" / "diagonal_only_shortcut.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    source_hash = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    assert record["schema"] == "7fe59337a0b4-counterexample-v1"
    assert record["generator_sha256"] == source_hash
    grid = gen.generate(**record["reproducer"])
    assert grid == record["input"]
    assert gen.rule_mirror(grid) == record["canonical_output"]
    assert gen.SEMANTIC_RIVALS["diagonal_source_only"](grid) == record["rival_output"]
    assert record["canonical_output"] != record["rival_output"]
    assert gen._analyze(grid)["source_sector"] == "north"
