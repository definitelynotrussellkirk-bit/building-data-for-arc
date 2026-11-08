"""Independent distribution probe for cc8c719680e6; reference labels use CLI apply.

Only generator.generate/self_check/lesson_identifiable are producer calls. Object
extraction, rivals, and morphology are independently implemented here. The census
does not retain Python-derived output labels. inputs.json is intended for the
supported arcpuzzles apply command, which retains authoritative Racket labels.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
TASK = "cc8c719680e6"
sys.path.insert(0, str(ROOT / "shared/runtime"))
spec = importlib.util.spec_from_file_location("reviewed_generator", HERE / "baseline_generator.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def components(grid, *, diagonal=False, colorblind=False):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c]}
    objects = []
    steps = tuple(
        (dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
        if (dr or dc) and (diagonal or abs(dr) + abs(dc) == 1)
    )
    while unseen:
        first = min(unseen)
        todo, found = [first], {first}
        unseen.remove(first)
        color = grid[first[0]][first[1]]
        while todo:
            r, c = todo.pop()
            for dr, dc in steps:
                candidate = (r + dr, c + dc)
                if candidate in unseen and (colorblind or grid[r + dr][c + dc] == color):
                    unseen.remove(candidate)
                    found.add(candidate)
                    todo.append(candidate)
        objects.append((color, found))
    return objects


def outline(grid, objects):
    out = [[0] * len(grid[0]) for _ in grid]
    for color, cells in objects:
        r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
        c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if r in (r0, r1) or c in (c0, c1):
                    out[r][c] = color
    return out


def morphology(grid):
    result = []
    for color, cells in components(grid):
        r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
        c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
        bh, bw = r1 - r0 + 1, c1 - c0 + 1
        inside = sum(r0 < r < r1 and c0 < c < c1 for r, c in cells)
        result.append((len(cells), min(bh, bw), max(bh, bw), bh * bw - len(cells), inside))
    return tuple(sorted(result))


def rivals(grid):
    return {
        "same_color_8_connected": outline(grid, components(grid, diagonal=True)),
        "color_blind_4_connected_first_color": outline(grid, components(grid, colorblind=True)),
    }


def make_case(h, w, placements):
    grid = [[0] * w for _ in range(h)]
    for color, r0, c0, shape in placements:
        for dr, dc in shape:
            assert grid[r0 + dr][c0 + dc] == 0
            grid[r0 + dr][c0 + dc] = color
    return grid


def prepare_lessons():
    census = json.loads((HERE / "census.json").read_text())
    lesson_inputs, lesson_meta = [], []
    for name, replay in census["natural_discriminator_replays"].items():
        query_index = replay["sample_index"]
        indexes = list(range(query_index - 4, query_index + 1))
        grids = [gen.generate(replay["seed"], index, difficulty=replay["difficulty"]) for index in indexes]
        independent_pairs = [{"input": grid, "output": outline(grid, components(grid))} for grid in grids]
        assert all(rivals(pair["input"])[name] == pair["output"] for pair in independent_pairs[:4])
        assert rivals(grids[4])[name] != independent_pairs[4]["output"]
        offset = len(lesson_inputs)
        lesson_inputs.extend(grids)
        lesson_meta.append({"rival": name, "seed": replay["seed"],
                            "difficulty": replay["difficulty"], "demo_indexes": indexes[:4],
                            "query_index": indexes[4], "reference_result_indexes": list(range(offset, offset + 5)),
                            "baseline_lesson_hook_errors": gen.lesson_identifiable(independent_pairs[:4], independent_pairs[4])})
    (HERE / "lesson_inputs.json").write_text(json.dumps({"inputs": lesson_inputs}, indent=2) + "\n")
    (HERE / "lesson_meta.json").write_text(json.dumps(lesson_meta, indent=2) + "\n")
    print(json.dumps(lesson_meta, indent=2))


def verify_reference():
    census = json.loads((HERE / "census.json").read_text())
    receipt = json.loads((HERE / "racket.json").read_text())
    assert receipt["executed_rule_hash"] == "8f9e53b42241"
    assert len(receipt["results"]) == len(census["retained_inputs"])
    mismatches, rows = [], []
    for result, meta in zip(receipt["results"], census["retained_inputs"]):
        assert result["error"] is None and result["valid_output"]
        grid, expected = result["input"], result["output"]
        if outline(grid, components(grid)) != expected:
            mismatches.append(result["index"])
        rows.append({**meta, "rival_matches_racket": {name: out == expected for name, out in rivals(grid).items()}})
    lesson_receipt = json.loads((HERE / "lesson_racket.json").read_text())
    assert lesson_receipt["executed_rule_hash"] == "8f9e53b42241"
    lessons = json.loads((HERE / "lesson_meta.json").read_text())
    for lesson in lessons:
        pairs = [lesson_receipt["results"][index] for index in lesson["reference_result_indexes"]]
        assert all(pair["error"] is None and pair["valid_output"] for pair in pairs)
        name = lesson["rival"]
        lesson["rival_fits_all_racket_demos"] = all(rivals(pair["input"])[name] == pair["output"] for pair in pairs[:4])
        lesson["rival_disagrees_with_racket_query"] = rivals(pairs[4]["input"])[name] != pairs[4]["output"]
        lesson["baseline_lesson_hook_errors_using_racket_labels"] = gen.lesson_identifiable(pairs[:4], pairs[4])
    verification = {"task_id": TASK, "generator_source_sha256": census["generator_sha256"],
                    "executed_rule_hash": receipt["executed_rule_hash"],
                    "racket_results": len(rows), "independent_mirror_mismatch_indexes": mismatches,
                    "reference_receipt_sha256": hashlib.sha256((HERE / "racket.json").read_bytes()).hexdigest(),
                    "lesson_reference_receipt_sha256": hashlib.sha256((HERE / "lesson_racket.json").read_bytes()).hexdigest(),
                    "retained_input_rival_results": rows, "contiguous_accepted_ambiguous_lessons": lessons}
    (HERE / "reference_verification.json").write_text(json.dumps(verification, indent=2) + "\n")
    print(json.dumps({key: value for key, value in verification.items() if key != "retained_input_rival_results"}, indent=2))


def main():
    retained, retained_meta = [], []
    def retain(grid, meta):
        retained.append(grid)
        retained_meta.append({"input_index": len(retained) - 1, **meta})

    canonical = []
    for line in (ROOT / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") != TASK:
            continue
        for split in ("train", "test"):
            pairs = row[split] if isinstance(row[split], list) else [row[split]]
            for pair_index, pair in enumerate(pairs):
                inp = pair["input"]
                facts = {"split": split, "pair_index": pair_index,
                         "morphology": morphology(inp),
                         "rival_matches_canonical_label": {name: out == pair["output"] for name, out in rivals(inp).items()}}
                canonical.append(facts)
                retain(inp, {"kind": "canonical", "split": split, "pair_index": pair_index})

    bands, examples = {}, {}
    for band_i, band in enumerate(("easy", "medium", "hard")):
        counts, morph_counts = Counter(), Counter()
        lesson_failures = Counter()
        for repetition in range(1000):
            seed = 810_000 + 10_000 * band_i + repetition
            disagreements = Counter()
            for slot in range(4):
                index = 4 * repetition + slot
                grid = gen.generate(seed, index, difficulty=band)
                assert gen.self_check(grid) == []
                expected = outline(grid, components(grid))
                morph_counts[str(morphology(grid))] += 1
                counts["inputs"] += 1
                for name, output in rivals(grid).items():
                    if output != expected:
                        counts[name + ":discriminators"] += 1
                        disagreements[name] += 1
                        if name not in examples:
                            examples[name] = {"seed": seed, "sample_index": index, "difficulty": band}
                            retain(grid, {"kind": "natural_discriminator", "rival": name, **examples[name]})
                if repetition < 4:
                    retain(grid, {"kind": "natural", "seed": seed, "sample_index": index, "difficulty": band})
            for name in ("same_color_8_connected", "color_blind_4_connected_first_color"):
                if disagreements[name] == 0:
                    lesson_failures[name] += 1
        bands[band] = {"counts": dict(counts), "four_demo_lessons": 1000,
                       "lessons_with_rival_surviving_all_demos": dict(lesson_failures),
                       "joint_morphology_counts": dict(morph_counts)}

    override_counts = Counter()
    for i, values in enumerate(itertools.product(
        ("canonical_7", "canonical_9", "wide_9x13", "tall_13x9"),
        (2, 3, 4), ("distinct", "one_repeat"), ("interior", "touching"),
        ("low", "high", "mixed"),
    )):
        ov = dict(zip(("scene_profile", "n_blobs", "color_relation", "edge_mode", "palette_kind"), values))
        grid = gen.generate(930_000 + i, i, difficulty="hard", **ov)
        assert gen.self_check(grid) == []
        expected = outline(grid, components(grid))
        override_counts["inputs"] += 1
        for name, output in rivals(grid).items():
            if output != expected:
                override_counts[name + ":discriminators"] += 1

    plus = {(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)}
    stair = {(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)}
    ell = {(0, 0), (0, 1), (1, 0)}
    contact_cases = {
        "orthogonal_different_color": make_case(9, 13, [
            (6, 0, 0, plus), (7, 1, 3, ell), (8, 6, 0, ell), (9, 6, 10, ell),
        ]),
        "diagonal_same_color": make_case(13, 9, [
            (2, 1, 1, stair), (2, 4, 4, ell), (3, 9, 1, ell),
        ]),
    }
    contacts = {}
    for name, grid in contact_cases.items():
        errors = gen.self_check(grid)
        assert not errors, errors
        expected = outline(grid, components(grid))
        contacts[name] = {"self_check_errors": errors,
                          "rival_diff_cells": {r: sum(a != b for row1, row2 in zip(out, expected) for a, b in zip(row1, row2)) for r, out in rivals(grid).items()}}
        retain(grid, {"kind": "authored_contact", "case": name})

    result = {
        "schema": "cc8c719680e6-independent-distribution-review-v1",
        "task_id": TASK,
        "generator_sha256": hashlib.sha256((HERE / "baseline_generator.py").read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "label_basis": "Census counts use independent Python object partitions and bbox outlines, not generator-owned semantic helpers. Retained authoritative labels must be created by supported arcpuzzles apply on inputs.json.",
        "canonical": canonical,
        "natural": bands,
        "override_cartesian_one_seed_each": dict(override_counts),
        "natural_discriminator_replays": examples,
        "authored_contact_cases": contacts,
        "retained_inputs": retained_meta,
    }
    (HERE / "inputs.json").write_text(json.dumps({"inputs": retained}, indent=2) + "\n")
    (HERE / "census.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"generator_sha256": result["generator_sha256"],
                      "natural": {band: {k: v for k, v in data.items() if k != "joint_morphology_counts"} for band, data in bands.items()},
                      "overrides": dict(override_counts), "contacts": contacts,
                      "retained_inputs": len(retained)}, indent=2))


if __name__ == "__main__":
    if "--prepare-lessons" in sys.argv:
        prepare_lessons()
    elif "--verify-reference" in sys.argv:
        verify_reference()
    else:
        main()
