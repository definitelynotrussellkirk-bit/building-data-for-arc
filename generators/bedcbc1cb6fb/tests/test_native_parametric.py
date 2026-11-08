"""Source-bound behavioral checks for the separate native parametric family.

Literal expectations below are hand-derived, not produced by a rule mirror.
The independent Racket call checks delivered labels against their exact source.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
SOURCE = HOME / "workspace/parametric/prototype.py"
RINGS = {"rule": "rings"}
AREA = {"rule": "ring_area_fill"}


def prototype():
    # Deliberately inside test execution: absence is a missing-feature failure,
    # never an import-time collection error or skip.
    assert SOURCE.is_file(), "native parametric prototype.py has not been implemented"
    name = "_bedcbc1cb6fb_native_test_" + hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, SOURCE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def rows(*lines):
    return [[int(cell) for cell in line] for line in lines]


def literal_scene():
    # Two distinct diagonal markers at indices 0 and 2. The 3x3 innermost
    # region has area 9 only AFTER canonical filling. The 4-colored key has
    # 9 occupied cells but bbox area 12; the other key areas are 3 and 5.
    return rows(
        "200000000000055000", "000000000000050000", "003000000000000000",
        "000011111110000000", "000010000010000000", "000010000010006660",
        "000010000010006060", "000010000010000000", "000010000010000000",
        "000011111110000000", "000000000000000000", "044440000000000000",
        "040040000000000000", "044400000000000000", "000000000000000000",
        "000000000000000000",
    )


def literal_rings():
    return rows(
        "200000000000055000", "000000000000050000", "003000000000000000",
        "000011111110000000", "000012222210000000", "000012333210006660",
        "000012333210006060", "000012333210000000", "000012222210000000",
        "000011111110000000", "000000000000000000", "044440000000000000",
        "040040000000000000", "044400000000000000", "000000000000000000",
        "000000000000000000",
    )


def literal_area():
    return rows(
        "200000000000055000", "000000000000050000", "003000000000000000",
        "000011111110000000", "000012222210000000", "000012333210006660",
        "000012333210006060", "000012333210000000", "000012222210000000",
        "000011111110000000", "000000000000000000", "033330000000000000",
        "033330000000000000", "033330000000000000", "000000000000000000",
        "000000000000000000",
    )


def racket(source, grid, bridge):
    from puzzle_generators.rule_wrap import strip_rule_wrapper

    expression = strip_rule_wrapper(source)
    datum = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({expression} {datum})")


def components(grid, predicate):
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                 if predicate(r, c, value)}
    result = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        stack, found = [start], {start}
        remaining.remove(start)
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining and grid[point[0]][point[1]] == color:
                    remaining.remove(point)
                    found.add(point)
                    stack.append(point)
        result.append(found)
    return result


def bounds(points):
    return (min(r for r, c in points), min(c for r, c in points),
            max(r for r, c in points), max(c for r, c in points))


def analyze_scene(grid):
    assert type(grid) is list and 1 <= len(grid) <= 30
    width = len(grid[0])
    assert 1 <= width <= 30
    assert all(type(row) is list and len(row) == width for row in grid)
    assert all(type(v) is int and 0 <= v <= 9 for row in grid for v in row)
    markers = [(i, grid[i][i]) for i in range(min(len(grid), width)) if grid[i][i] not in (0, 1)]
    palette = [v for i, v in markers]
    assert 2 <= len(palette) <= 5 and len(set(palette)) == len(palette)
    blue = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1}
    r1, c1, r2, c2 = bounds(blue)
    assert blue == {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
                    if r in (r1, r2) or c in (c1, c2)}
    assert all(grid[r][c] == 0 for r in range(r1 + 1, r2) for c in range(c1 + 1, c2))
    keys = components(grid, lambda r, c, v: v not in (0, 1) and r != c)
    assert len(keys) == 3
    for key in keys:
        assert all(not (r1 <= r <= r2 and c1 <= c <= c2) for r, c in key)
        assert all(grid[r][c] not in palette for r, c in key)
        a, b, d, e = bounds(key)
        assert len(key) < (d - a + 1) * (e - b + 1), "keys must require reconstruction"
    # Every palette pixel is a true diagonal marker: no hidden colored noise.
    assert all(r == c for r, row in enumerate(grid) for c, v in enumerate(row) if v in palette)
    return markers, (r1, c1, r2, c2), keys


def test_default_program_preserves_exact_canonical_authority():
    p = prototype()
    sources = {row["program_solution"] for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
               if (row := json.loads(line)).get("task_id") == "bedcbc1cb6fb"}
    assert len(sources) == 1
    assert p.canonical_source() == sources.pop() == p.program(RINGS)
    assert tuple(p.SETTINGS) == (RINGS, AREA)
    assert p.program(AREA) != p.program(RINGS)


def test_literal_rings_ignores_outside_colors_and_accepts_marker_gap():
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    grid = literal_scene()
    snapshot = copy.deepcopy(grid)
    with RacketBridge() as bridge:
        assert racket(p.program(RINGS), grid, bridge) == literal_rings()
        assert p.execute(p.program(RINGS), grid, bridge=bridge) == literal_rings()
    assert grid == snapshot


def test_literal_area_consumes_filled_center_count_and_reconstructs_only_matching_key():
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    grid = literal_scene()
    with RacketBridge() as bridge:
        assert racket(p.program(AREA), grid, bridge) == literal_area()
        assert p.execute(p.program(AREA), grid, bridge=bridge) == literal_area()
    assert grid == literal_scene()


def test_seed_validation_rejects_coercion_and_out_of_range_values():
    p = prototype()
    for seed in (True, False, 1.0, -1, 2**63, "17", None):
        with pytest.raises((ValueError, TypeError)):
            p.sample_inputs(seed)
        with pytest.raises((ValueError, TypeError)):
            p.generate(seed, RINGS)
    for seed in (0, 2**63 - 1):
        assert len(p.sample_inputs(seed, demos=2, queries=1)["test"]) == 1


def test_counts_and_settings_reject_invalid_controls():
    p = prototype()
    for field, values in (("demos", (1, 7, True, 3.0)), ("queries", (0, 5, False, 1.0))):
        for value in values:
            with pytest.raises((ValueError, TypeError)):
                p.sample_inputs(17, **{field: value})
            with pytest.raises((ValueError, TypeError)):
                p.generate(17, AREA, **{field: value})
    for settings in ({}, {"rule": "unknown"}, {"rule": "rings", "extra": 1}, None, "rings"):
        with pytest.raises((ValueError, TypeError)):
            p.program(settings)
        with pytest.raises((ValueError, TypeError)):
            p.generate(17, settings)


def test_split_prefixes_are_stable_when_counts_change():
    p = prototype()
    full = p.sample_inputs(17, demos=6, queries=4)
    assert set(full) == {"train", "test"}
    assert len(full["train"]) == 6 and len(full["test"]) == 4
    for demos, queries in ((2, 1), (3, 4), (6, 1)):
        small = p.sample_inputs(17, demos=demos, queries=queries)
        assert small["train"] == full["train"][:demos]
        assert small["test"] == full["test"][:queries]


def test_sampler_is_deterministic_fresh_and_does_not_consume_global_rng():
    p = prototype()
    random.seed(412)
    state = random.getstate()
    first = p.sample_inputs(17)
    assert random.getstate() == state
    second = p.sample_inputs(17)
    assert first == second
    first["train"][0][0][0] = (first["train"][0][0][0] + 1) % 10
    assert p.sample_inputs(17) == second
    assert p.sample_inputs(0) != second


def test_maximum_episode_has_ten_distinct_novel_inputs():
    p = prototype()
    from reviewer_support import canonical_pairs

    canonical = {json.dumps(pair["input"]) for pair in canonical_pairs("bedcbc1cb6fb", root=REPO)}
    for seed in (0, 17):
        inputs = p.sample_inputs(seed, demos=6, queries=4)
        serialized = [json.dumps(grid) for split in ("train", "test") for grid in inputs[split]]
        assert len(serialized) == len(set(serialized)) == 10
        assert not canonical.intersection(serialized)


def test_sampled_scenes_obey_shared_grammar_with_real_content_spread():
    p = prototype()
    counts, gaps = set(), []
    for seed in (0, 17):
        sample = p.sample_inputs(seed, demos=6, queries=4)
        for grid in sample["train"] + sample["test"]:
            markers, frame, keys = analyze_scene(grid)
            counts.add(len(markers))
            gaps.append(any(b[0] - a[0] > 1 for a, b in zip(markers, markers[1:])))
    assert counts == {2, 3, 4, 5}
    assert any(gaps), "the new grammar should exercise noncontiguous markers"


def test_generated_pairs_match_shared_inputs_and_exact_protected_racket_labels():
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    sample = p.sample_inputs(17)
    with RacketBridge() as bridge:
        for settings in (RINGS, AREA):
            episode = p.generate(17, settings)
            assert episode["program_solution"] == p.program(settings)
            for split, count in (("train", 3), ("test", 4)):
                assert len(episode[split]) == count
                assert [pair["input"] for pair in episode[split]] == sample[split]
                for pair in episode[split]:
                    assert pair["output"] == racket(episode["program_solution"], pair["input"], bridge)
            if settings == AREA:
                assert any(pair["output"] != racket(p.program(RINGS), pair["input"], bridge)
                           for pair in episode["train"])


def test_30_by_30_query_has_substantive_frame_and_racket_transformation():
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    sample = p.sample_inputs(17)
    big = [grid for grid in sample["test"] if len(grid) == len(grid[0]) == 30]
    assert big, "four-query examples must exercise the legal 30x30 boundary"
    markers, (r1, c1, r2, c2), keys = analyze_scene(big[0])
    assert r2 - r1 >= 10 and c2 - c1 >= 10, "padding a tiny scene is not a boundary case"
    assert sum(len(key) for key in keys) >= 12
    with RacketBridge() as bridge:
        output = racket(p.program(AREA), big[0], bridge)
    assert sum(a != b for old, new in zip(big[0], output) for a, b in zip(old, new)) >= 81


def test_public_turn_strips_enriched_pairs_and_all_future_query_information():
    p = prototype()
    episode = {"train": [{"input": [[2]], "output": [[3]], "settings": AREA}],
               "test": [{"input": [[4]], "output": [[5]], "private": "first"},
                        {"input": [[6]], "output": [[7]], "private": "future"}],
               "settings": AREA, "program_solution": "SECRET", "query_count": 2}
    before = copy.deepcopy(episode)
    expected = {"train": [{"input": [[2]], "output": [[3]]}], "test": [{"input": [[6]]}]}
    assert p.public_turn(episode, query_index=1) == expected
    assert episode == before
    for index in (-1, 2, True, 0.0):
        with pytest.raises((ValueError, TypeError, IndexError)):
            p.public_turn(episode, query_index=index)


def test_first_turn_public_bytes_are_identical_for_one_or_four_queries():
    p = prototype()
    from reviewer_support import public_challenge_bytes

    for settings in (RINGS, AREA):
        one = p.generate(17, settings, demos=2, queries=1)
        four = p.generate(17, settings, demos=2, queries=4)
        assert public_challenge_bytes(p.public_turn(one)) == public_challenge_bytes(p.public_turn(four))
        assert len(p.public_turn(four)["test"]) == 1


def test_saved_examples_hash_exact_public_bytes_and_keep_four_labels_private(tmp_path):
    p = prototype()
    from reviewer_support import public_challenge_bytes

    p.write_examples(tmp_path, seed=17, demos=3)
    public_files = sorted((tmp_path / "public").glob("challenge-*.json"))
    assert len(public_files) == 2
    expected = {public_challenge_bytes(p.public_turn(p.generate(17, settings))) for settings in (RINGS, AREA)}
    observed = set()
    for path in public_files:
        data = path.read_bytes()
        assert path.name == f"challenge-{hashlib.sha256(data).hexdigest()}.json"
        visible = json.loads(data)
        assert data == public_challenge_bytes(visible)
        assert set(visible) == {"train", "test"} and len(visible["test"]) == 1
        assert all(set(pair) == {"input", "output"} for pair in visible["train"])
        assert all(set(pair) == {"input"} for pair in visible["test"])
        observed.add(data)
    assert observed == expected
    private = [json.loads(path.read_text()) for path in tmp_path.rglob("*.json")
               if path not in public_files]
    for settings in (RINGS, AREA):
        matches = [item for item in private if isinstance(item, dict)
                   and item.get("program_solution") == p.program(settings)]
        assert len(matches) == 1, "retain one labeled private example per setting"
        assert len(matches[0]["train"]) == 3 and len(matches[0]["test"]) == 4
        assert all("output" in pair for pair in matches[0]["test"])


def test_two_demonstrations_refute_truncating_the_palette_to_three_markers():
    """A shallow prefix must teach that every diagonal marker can matter."""
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        for seed in (0, 17):
            demos = p.sample_inputs(seed, demos=2, queries=1)["train"]
            for settings in (RINGS, AREA):
                source = p.program(settings)
                assert source.count("(ms markers)") == 1
                wrong = source.replace("(ms markers)", "(ms (take markers (min 3 (length markers))))")
                if settings == AREA:
                    wrong = wrong.replace("(define palette\n", "(define raw-palette\n")
                    wrong = wrong.replace("(define center-color (last palette))",
                        "(define palette (take raw-palette (min 3 (length raw-palette))))\n"
                        "  (define center-color (last palette))")
                assert any(p.execute(source, grid, bridge=bridge) != p.execute(wrong, grid, bridge=bridge)
                           for grid in demos), (seed, settings, "three-marker truncation fits every demo")


def test_two_demonstrations_refute_observed_finite_palette_and_selection_shortcuts():
    """Pin actual initial seed0/17 teaching holes without consulting any query."""
    p = prototype()
    path = SOURCE.with_name("rivals.py")
    spec = importlib.util.spec_from_file_location("_bed_finite_rivals_test", path)
    rivals = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rivals)
    survivors = []
    for seed in (0, 17):
        demos = p.sample_inputs(seed, demos=2, queries=1)["train"]
        for settings in (RINGS, AREA):
            rule = settings["rule"]
            for name in rivals.active_rivals(rule):
                if all(rivals.predict(grid, rule) == rivals.predict(grid, rule, name) for grid in demos):
                    survivors.append((seed, rule, name))
    assert survivors == []


def test_two_demonstrations_refute_independent_shape_salience_and_position_shortcuts():
    """Actual Racket regressions for independent review's seed17/max-seed gaps."""
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    source = p.program(AREA)
    marker = "(define matches (filter (lambda (o) (= (obj-size o) key-area)) keys))"
    assert source.count(marker) == 1
    most_holes = """(define (hole-area o) (- (* (obj-h o) (obj-w o)) (obj-size o)))
  (define matches (filter (lambda (o) (= (hole-area o) (max-of hole-area keys))) keys))"""
    rightmost = "(define matches (filter (lambda (o) (= (obj-c2 o) (max-of obj-c2 keys))) keys))"
    survivors = []
    with RacketBridge() as bridge:
        for seed, name, replacement in ((17, "most_holes", most_holes),
                                         (2**63-1, "rightmost_key", rightmost)):
            demos = p.sample_inputs(seed, demos=2, queries=1)["train"]
            wrong = source.replace(marker, replacement)
            if all(p.execute(source, grid, bridge=bridge) == p.execute(wrong, grid, bridge=bridge)
                   for grid in demos):
                survivors.append((seed, name))
    assert survivors == []


def test_writer_refuses_nonempty_destination_before_overwriting_private_evidence(tmp_path):
    p = prototype()
    (tmp_path / "public").mkdir()
    stale = tmp_path / "public/challenge-stale.json"
    stale.write_bytes(b"old public evidence\n")
    (tmp_path / "private").mkdir()
    private = tmp_path / "private/episode-0.json"
    private.write_bytes(b"old private evidence\n")
    with pytest.raises((FileExistsError, ValueError)):
        p.write_examples(tmp_path, seed=17, demos=3)
    assert stale.read_bytes() == b"old public evidence\n"
    assert private.read_bytes() == b"old private evidence\n"
    assert sorted(x.name for x in (tmp_path / "public").iterdir()) == [stale.name]
