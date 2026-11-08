from __future__ import annotations

import copy
import importlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

TASK_ID = "8118155d8959"
HERE = Path(__file__).resolve()
LIBRARY = next(
    (p for p in HERE.parents if (p / "shared/runtime").is_dir()),
    None,
)
if LIBRARY is None:
    gen = importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )
    REPO = Path.cwd()
else:
    sys.path.insert(0, str(LIBRARY / "shared/runtime"))
    spec = importlib.util.spec_from_file_location(
        f"review_{TASK_ID}", LIBRARY / f"generators/{TASK_ID}/generator.py"
    )
    assert spec is not None and spec.loader is not None
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    REPO = LIBRARY

CANONICAL = REPO / "shared/data/canonical/puzzles.jsonl"
AUTHORITY = (
    REPO
    / "shared/data/base/solutions/banks/e2825ca16ace/M67__8118155d8959.json"
)


def _canonical_row() -> dict:
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical row missing")


def _grid(value):
    if value and isinstance(value[0], str):
        return [[int(ch) for ch in row] for row in value]
    return copy.deepcopy(value)


def _pairs():
    row = _canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [
        (_grid(pair["input"]), _grid(pair["output"]))
        for pair in [*row["train"], *test]
    ]


def _profile(grid):
    return len(grid), len(grid[0]), len({v for row in grid for v in row})


def _explicit_bbox_counterexample():
    """Cell-count and bbox-area rankings swap the size-4 and size-5 objects."""
    grid = [[0 for _ in range(11)] for _ in range(10)]

    # Four-cell T, bbox area 6. Intended middle (green), bbox rival largest (cyan).
    for r, c in ((1, 0), (1, 1), (1, 2), (2, 1)):
        grid[r][c] = 1

    # Three-cell line, bbox area 3. Smallest under both rules (red).
    for c in (7, 8, 9):
        grid[1][c] = 1

    # Five-cell line, bbox area 5. Intended largest (cyan), bbox rival middle (green).
    for c in (3, 4, 5, 6, 7):
        grid[8][c] = 1

    # Three preserved distractor colors, giving canonical profile (10, 11, 5).
    grid[4][0] = grid[4][1] = 5
    grid[4][4] = grid[4][5] = 6
    grid[4][9] = grid[4][10] = 9
    return grid


def test_rule_hash_is_pinned_to_selected_canonical_authority():
    assert gen.RULE_HASH == "ed7a95a7119d"


def test_base_target_code_is_byte_identical_to_selected_canonical_source():
    row = _canonical_row()
    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    assert authority["racket_target"]["raw_code"] == row["program_solution"]
    assert authority["racket_target"]["target_code"] == row["program_solution"]


def test_all_canonical_pairs_are_accepted_and_mirrored_exactly():
    for inp, out in _pairs():
        before = copy.deepcopy(inp)
        assert gen.self_check(inp) == []
        assert gen.strict_canonical_like(inp) == []
        assert gen.rule_mirror(inp) == out
        assert inp == before


def test_bbox_area_shortcut_fits_all_canonical_pairs_but_fails_exact_witness():
    for inp, out in _pairs():
        assert gen.CANONICAL_SHORTCUTS["bbox_area"](inp) == out

    witness = _explicit_bbox_counterexample()
    assert gen.self_check(witness) == []
    intended = gen.rule_mirror(witness)
    rival = gen.CANONICAL_SHORTCUTS["bbox_area"](witness)
    assert rival != intended

    # The T and five-cell line are exactly the two objects whose ranks swap.
    assert intended[1][0] == 3 and rival[1][0] == 8
    assert intended[8][3] == 8 and rival[8][3] == 3
    assert intended[4][0] == rival[4][0] == 5


def test_every_declared_scene_profile_override_is_exact_and_observable():
    assert set(gen.AXES) == {"scene_profile"}
    for band in ("easy", "medium", "hard"):
        for profile in gen.SCENE_PROFILES:
            grid = gen.generate(
                991,
                1,
                difficulty=band,
                scene_profile=profile,
            )
            assert gen.observe_overrides(grid) == {"scene_profile": profile}
            assert gen.self_check(grid) == []

    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(11, 0, difficulty="medium", grid_width=12)
    with pytest.raises(ValueError):
        gen.generate(11, 0, difficulty="medium", scene_profile="not-a-profile")


def test_default_generation_stays_on_canonical_profiles_in_every_band():
    canonical_profiles = {_profile(inp) for inp, _ in _pairs()}
    for band in ("easy", "medium", "hard"):
        observed = []
        for index in range(20):
            grid = gen.generate(10_000 + index, index * 17 + 3, difficulty=band)
            assert gen.self_check(grid) == []
            observed.append(_profile(grid))
        assert set(observed) <= canonical_profiles
        assert len(set(observed)) >= 3


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    state = random.getstate()
    first = gen.generate(314159, 2, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(314159, 2, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 7
    assert gen.generate(314159, 2, difficulty="hard") == second


def test_each_three_example_lesson_refutes_every_declared_competitor():
    assert set(gen.SEMANTIC_WITNESSES) == set(gen.WITNESS_RIVALS)
    assert set(gen.LESSON_COMPETITORS) == set(gen.SEMANTIC_RIVALS)
    assert "bbox_area" in gen.SEMANTIC_RIVALS

    for start in range(9):
        demos = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
            inp = gen.generate(4321, sample_index, difficulty="medium")
            demos.append({"input": inp, "output": gen.rule_mirror(inp)})
        query_in = gen.generate(
            4321,
            start + gen.EXAMPLES_NEEDED,
            difficulty="medium",
        )
        query = {"input": query_in, "output": gen.rule_mirror(query_in)}
        assert gen.lesson_identifiable(demos, query) == []
        for name, competitor in gen.LESSON_COMPETITORS.items():
            assert any(
                competitor(demo["input"]) != demo["output"]
                for demo in demos
            ), (start, name)


def test_every_public_witness_fires_and_its_named_rival_really_disagrees():
    fired = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            for sample_index in range(3):
                grid = gen.generate(seed, sample_index, difficulty=band)
                intended = gen.rule_mirror(grid)
                for witness_name, predicate in gen.SEMANTIC_WITNESSES.items():
                    if not predicate(grid):
                        continue
                    fired[witness_name] += 1
                    assert any(
                        gen.SEMANTIC_RIVALS[rival_name](grid) != intended
                        for rival_name in gen.WITNESS_RIVALS[witness_name]
                    ), (witness_name, band, seed, sample_index)
    assert all(count > 0 for count in fired.values()), fired


def test_self_check_rejects_targeted_structural_impostors():
    valid = _explicit_bbox_counterexample()

    missing_blue = copy.deepcopy(valid)
    for c in (7, 8, 9):
        missing_blue[1][c] = 0
    assert any("3 blue" in reason for reason in gen.self_check(missing_blue))

    illegal_input_color = copy.deepcopy(valid)
    illegal_input_color[4][0] = illegal_input_color[4][1] = 2
    assert any("input palette" in reason for reason in gen.self_check(illegal_input_color))

    wrong_size_profile = copy.deepcopy(valid)
    wrong_size_profile[2][0] = 1  # T grows from 4 to 5, colliding with size-5 rank.
    assert any("size" in reason for reason in gen.self_check(wrong_size_profile))

    wrong_dimensions = [row[:-1] for row in valid]
    assert gen.self_check(wrong_dimensions)


def test_axes_metadata_is_literal_for_static_linter():
    import ast

    source_path = REPO / f"generators/{TASK_ID}/generator.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "AXES" for target in node.targets)
    )
    assert ast.literal_eval(assignment.value) == gen.AXES


def test_workspace_shortcut_probe_reports_canonical_fit_and_generated_refutation():
    probe_path = REPO / f"generators/{TASK_ID}/workspace/shortcut_probe.py"
    spec = importlib.util.spec_from_file_location(
        f"shortcut_probe_{TASK_ID}", probe_path
    )
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.build_report(per_band=2, lesson_starts=3)
    assert report["task_id"] == TASK_ID
    assert report["canonical_pairs"] == len(_pairs())
    bbox = report["canonical_shortcuts"]["bbox_area"]
    assert bbox["fits"] == bbox["pairs"] == len(_pairs())
    assert report["generated_rival_disagreements"]["bbox_area"] > 0
    assert report["lesson_windows"]["unrefuted"] == []
    assert report["first_generated_counterexample"]["bbox_area"] is not None


def test_every_lesson_refutes_a_shape_morphology_lookup_shortcut():
    """A learner must not solve generated lessons with a shape-to-color table."""

    def shape_signature(cells):
        normalized = []
        for code in range(8):
            transformed = []
            for row, col in cells:
                if code == 1:
                    transformed.append((col, -row))
                elif code == 2:
                    transformed.append((-row, -col))
                elif code == 3:
                    transformed.append((-col, row))
                elif code == 4:
                    transformed.append((row, -col))
                elif code == 5:
                    transformed.append((-row, col))
                elif code == 6:
                    transformed.append((col, row))
                elif code == 7:
                    transformed.append((-col, -row))
                else:
                    transformed.append((row, col))
            min_row = min(r for r, _ in transformed)
            min_col = min(c for _, c in transformed)
            normalized.append(
                tuple(sorted((r - min_row, c - min_col) for r, c in transformed))
            )
        return min(normalized)

    assert "morphology_lookup" in gen.LESSON_COMPETITORS
    for start in range(9):
        colors_by_shape = {}
        demos = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(6143, sample_index, difficulty="medium")
            output = gen.rule_mirror(grid)
            demos.append({"input": grid, "output": output})
            for record in gen._blue_records(grid):
                signature = shape_signature(record["cells"])
                colors = {output[row][col] for row, col in record["cells"]}
                assert len(colors) == 1
                colors_by_shape.setdefault(signature, set()).update(colors)

        assert any(len(colors) > 1 for colors in colors_by_shape.values()), start
        rival = gen.LESSON_COMPETITORS["morphology_lookup"]
        assert any(rival(demo["input"]) != demo["output"] for demo in demos)
