#!/usr/bin/env python3
"""Source-bound mirror lesson diagnostics and public-reference verification.

Search compares Python hypotheses, not freshly executed Racket labels. Verify
either executes Catalog.apply through the packet's review.py run wrapper, or
checks a saved public apply receipt. Embedded self-tests use literal fixtures.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import types


TASK_ID = "f8b3586f1d58"


def colored_cells(grid):
    return [(r, c, value) for r, row in enumerate(grid)
            for c, value in enumerate(row) if value != 0]


def mirror_selected(grid, cells):
    out = deepcopy(grid)
    width = len(grid[0])
    for r, c, value in cells:
        out[r][width - 1 - c] = value
    return out


def mirror_all(grid):
    """Python diagnostic of the original-read, every-nonzero Racket fold."""
    return mirror_selected(grid, colored_cells(grid))


def first_color(grid):
    seen, selected = set(), []
    for r, c, value in colored_cells(grid):
        if value not in seen:
            seen.add(value)
            selected.append((r, c, value))
    return mirror_selected(grid, selected)


def first_row(grid):
    seen, selected = set(), []
    for r, c, value in colored_cells(grid):
        if r not in seen:
            seen.add(r)
            selected.append((r, c, value))
    return mirror_selected(grid, selected)


def first_three(grid):
    return mirror_selected(grid, colored_cells(grid)[:3])


def isolated(grid):
    """Mirror only cells with no orthogonal nonzero neighbor of any color."""
    height, width = len(grid), len(grid[0])
    selected = [(r, c, value) for r, c, value in colored_cells(grid)
                if not any(0 <= r + dr < height and 0 <= c + dc < width
                           and grid[r + dr][c + dc] != 0
                           for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))]
    return mirror_selected(grid, selected)


def left_only(grid):
    return mirror_selected(grid, [(r, c, v) for r, c, v in colored_cells(grid)
                                  if c < (len(grid[0]) + 1) // 2])


def right_only(grid):
    return mirror_selected(grid, [(r, c, v) for r, c, v in colored_cells(grid)
                                  if c >= len(grid[0]) // 2])


RIVALS = {fn.__name__: fn for fn in
          (first_color, first_row, first_three, isolated, left_only, right_only)}


def lesson_status(pairs, rival):
    if not all(rival(pair["input"]) == pair["output"] for pair in pairs[:-1]):
        return "demonstrations_refute"
    return "survived_all" if rival(pairs[-1]["input"]) == pairs[-1]["output"] else "ambiguous_query"


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def digest_grid(value):
    return digest_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def support_imports():
    for parent in Path(__file__).resolve().parents:
        for directory in (parent / "shared/runtime", parent):
            if (directory / "reviewer_support.py").is_file():
                sys.path.insert(0, str(directory))
                from reviewer_support import canonical_pairs, find_root
                return find_root(__file__), canonical_pairs
    raise FileNotFoundError("reviewer_support.py not found in this file's tree")


def load_generator(root, requested_source=None):
    candidates = [Path(requested_source)] if requested_source else [
        root / "generators" / TASK_ID / "generator.py",
        root / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py"]
    path = next((path.resolve() for path in candidates if path.is_file()), None)
    if path is None:
        raise FileNotFoundError("Generator source not found")
    source = path.read_bytes()
    module = types.ModuleType(f"mirror_probe_{TASK_ID}")
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module, path, source


def grid_features(grid):
    cells = colored_cells(grid)
    width = len(grid[0])
    return {
        "three_cells": len(cells) == 3,
        "repeated_color": len({v for _, _, v in cells}) < len(cells),
        "multiple_cells_in_row": len({r for r, _, _ in cells}) < len(cells),
        "adjacent_nonzero_4": any(abs(r - rr) + abs(c - cc) == 1
                                  for i, (r, c, _) in enumerate(cells)
                                  for rr, cc, _ in cells[i + 1:]),
        "left_occupied": any(2 * c < width - 1 for _, c, _ in cells),
        "right_occupied": any(2 * c > width - 1 for _, c, _ in cells),
        "center_occupied": any(2 * c == width - 1 for _, c, _ in cells),
        "odd_width": width % 2 == 1,
        "different_color_mirror_collision": any(grid[r][width - 1 - c] not in (0, v)
                                               for r, c, v in cells),
        "identity_under_python_mirror": mirror_all(grid) == grid,
    }


def search(args):
    root, canonical_pairs = support_imports()
    generator, path, source = load_generator(root, args.source)
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    if not canonical:
        raise ValueError("No labeled canonical pairs")
    rival_counts = {name: Counter(pair_matches_python_mirror=0, lessons_fit_demos=0,
                                 demonstrations_refute=0, survived_all=0, ambiguous_query=0)
                    for name in RIVALS}
    feature_counts, cell_counts, counts = Counter(), Counter(), Counter()
    lessons, errors = {}, []
    for seed in range(args.seed_start, args.seed_start + args.seeds):
        pairs = []
        try:
            for index in range(args.sample_index, args.sample_index + 4):
                grid = generator.generate(seed, index, difficulty=args.difficulty)
                pairs.append({"seed": seed, "sample_index": index, "difficulty": args.difficulty,
                              "overrides": {}, "role": "demo" if len(pairs) < 3 else "query",
                              "input": grid, "input_sha256": digest_grid(grid),
                              "output": mirror_all(grid)})
        except Exception as exc:
            counts["generation_errors"] += 1
            if not errors:
                errors.append({"seed": seed, "error": f"{type(exc).__name__}: {exc}"})
            continue
        counts["lessons"] += 1
        counts["pairs"] += len(pairs)
        counts["lessons_with_duplicate_inputs"] += len({p["input_sha256"] for p in pairs}) < 4
        counts["lessons_with_identity_pair"] += any(p["input"] == p["output"] for p in pairs)
        for pair in pairs:
            feature_counts.update(name for name, holds in grid_features(pair["input"]).items() if holds)
            cell_counts[str(len(colored_cells(pair["input"])))] += 1
        for name, rival in RIVALS.items():
            status = lesson_status(pairs, rival)
            rival_counts[name][status] += 1
            rival_counts[name]["lessons_fit_demos"] += status != "demonstrations_refute"
            rival_counts[name]["pair_matches_python_mirror"] += sum(
                rival(pair["input"]) == pair["output"] for pair in pairs)
            if status == "ambiguous_query" and name not in lessons:
                # Keep only the first seed; labels stay clearly Python diagnostics.
                saved = [{**pair, "python_mirror_output": pair["output"]} for pair in pairs]
                for pair in saved:
                    del pair["output"]
                lessons[name] = {"seed": seed, "rival": name, "pairs": saved}
    return {
        "schema": "arcpuzzles-mirror-curriculum-probe-v1", "task_id": TASK_ID,
        "origin_generator_sha256": digest_bytes(source), "generator_version": generator.VERSION,
        "generator_path": str(path), "probe_sha256": digest_bytes(Path(__file__).read_bytes()),
        "argv": sys.argv, "arguments": vars(args),
        "sample_policy": "Each seed uses four consecutive indices: first three demos, fourth query. No overrides, retries, or resampling.",
        "evidence_basis": "Python mirror diagnostic, not Racket execution. Canonical fit uses existing public ledger labels.",
        "counts": dict(counts), "cell_count_histogram": dict(sorted(cell_counts.items(), key=lambda item: int(item[0]))),
        "feature_pair_counts": dict(feature_counts),
        "canonical": {"pair_count": len(canonical), "normalized_pairs_sha256": digest_grid(canonical),
                      "python_mirror_fits": sum(mirror_all(p["input"]) == p["output"] for p in canonical),
                      "rival_pairs_fit": {name: sum(fn(p["input"]) == p["output"] for p in canonical)
                                          for name, fn in RIVALS.items()}},
        "rival_counts": {name: dict(value) for name, value in rival_counts.items()},
        "lessons": list(lessons.values()), "first_errors": errors,
    }


def verify(args):
    capture_path = Path(args.capture)
    capture = json.loads(capture_path.read_text())
    if capture["task_id"] != TASK_ID:
        raise ValueError("Captured task differs")
    lessons = capture["lessons"]
    if not lessons or any(len(lesson["pairs"]) != 4 for lesson in lessons):
        raise ValueError("Expected nonempty captured 3-demo/1-query lessons")
    pairs = [pair for lesson in lessons for pair in lesson["pairs"]]
    grids = [pair["input"] for pair in pairs]
    if any(digest_grid(pair["input"]) != pair["input_sha256"] for pair in pairs):
        raise ValueError("Captured input hash differs")
    if args.receipt:
        receipt_path = Path(args.receipt)
        receipt = json.loads(receipt_path.read_text())
        receipt_identity = {"path": str(receipt_path), "sha256": digest_bytes(receipt_path.read_bytes())}
        basis = "Saved public Catalog.apply receipt, independently checked against exact captured inputs."
    else:
        root, _ = support_imports()
        sys.path.insert(0, str(root / "src"))
        from arcpuzzles import Catalog
        receipt = Catalog(root).apply(TASK_ID, grids, reference="canonical", timeout=args.timeout)
        receipt_identity = {"embedded_public_apply_receipt": receipt}
        basis = "Fresh public Catalog.apply execution of the canonical Racket authority."
    if (receipt["task_id"] != TASK_ID or receipt["reference"] != "canonical"
            or receipt["rule_hash_matches_catalog"] is not True):
        raise ValueError("Reference identity does not match canonical task authority")
    rows = receipt["results"]
    if len(rows) != len(pairs):
        raise ValueError("Reference result count differs")
    for pair, row in zip(pairs, rows):
        if (row["error"] is not None or row["valid_output"] is not True
                or row["input"] != pair["input"] or row["input_sha256"] != pair["input_sha256"]
                or digest_grid(row["output"]) != row["output_sha256"]):
            raise ValueError("Reference result is invalid or does not match captured input/output hashes")
    findings = []
    for index, lesson in enumerate(lessons):
        labeled = rows[index * 4:index * 4 + 4]
        rival = RIVALS[lesson["rival"]]
        predicted = rival(labeled[-1]["input"])
        differences = [{"row": r, "col": c, "rival": predicted[r][c], "canonical": value}
                       for r, row in enumerate(labeled[-1]["output"]) for c, value in enumerate(row)
                       if predicted[r][c] != value]
        findings.append({"seed": lesson["seed"], "rival": lesson["rival"],
                         "sample_indices": [p["sample_index"] for p in lesson["pairs"]],
                         "status": lesson_status(labeled, rival),
                         "rival_matches": [rival(p["input"]) == p["output"] for p in labeled],
                         "python_mirror_matches_authority": all(mirror_all(p["input"]) == p["output"] for p in labeled),
                         "query_differences": differences,
                         "input_sha256s": [p["input_sha256"] for p in labeled],
                         "output_sha256s": [p["output_sha256"] for p in labeled]})
    return {"schema": "arcpuzzles-mirror-verified-lessons-v1", "task_id": TASK_ID,
            "capture_path": str(capture_path), "capture_sha256": digest_bytes(capture_path.read_bytes()),
            "origin_generator_sha256": capture["origin_generator_sha256"],
            "reference_generator_sha256": receipt["generator_sha256"],
            "reference_generator_matches_origin": receipt["generator_sha256"] == capture["origin_generator_sha256"],
            "reference_identity": {key: receipt[key] for key in
                                   ("reference", "catalog_rule_hash", "executed_rule_hash", "rule_text_sha256", "rule_hash_matches_catalog")},
            "evidence_basis": basis, "receipt": receipt_identity, "findings": findings,
            "probe_sha256": digest_bytes(Path(__file__).read_bytes()), "argv": sys.argv, "arguments": vars(args)}


def self_test():
    # Detect missing copies, off-by-one axes, selection mistakes, and mutation.
    grid = [[1, 2, 0, 0, 0, 0], [0, 0, 3, 0, 0, 0],
            [1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 4, 0]]
    original = deepcopy(grid)
    assert mirror_all(grid) == [[1, 2, 0, 0, 2, 1], [0, 0, 3, 3, 0, 0],
                                [1, 0, 0, 0, 0, 1], [0, 4, 0, 0, 4, 0]]
    assert first_row(grid) == [[1, 2, 0, 0, 0, 1], [0, 0, 3, 3, 0, 0],
                               [1, 0, 0, 0, 0, 1], [0, 4, 0, 0, 4, 0]]
    assert first_color(grid) == [[1, 2, 0, 0, 2, 1], [0, 0, 3, 3, 0, 0],
                                 [1, 0, 0, 0, 0, 0], [0, 4, 0, 0, 4, 0]]
    assert first_three(grid) == [[1, 2, 0, 0, 2, 1], [0, 0, 3, 3, 0, 0],
                                 [1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 4, 0]]
    assert isolated(grid) == [[1, 2, 0, 0, 0, 0], [0, 0, 3, 3, 0, 0],
                              [1, 0, 0, 0, 0, 1], [0, 4, 0, 0, 4, 0]]
    assert left_only(grid) == [[1, 2, 0, 0, 2, 1], [0, 0, 3, 3, 0, 0],
                               [1, 0, 0, 0, 0, 1], [0, 0, 0, 0, 4, 0]]
    assert right_only(grid) == [[1, 2, 0, 0, 0, 0], [0, 0, 3, 0, 0, 0],
                                [1, 0, 0, 0, 0, 0], [0, 4, 0, 0, 4, 0]]
    assert grid == original
    assert mirror_all([[0, 5, 0], [6, 0, 0]]) == [[0, 5, 0], [6, 0, 6]]
    # The authority reads the original input throughout its fold: collisions swap.
    assert mirror_all([[1, 0, 2]]) == [[2, 0, 1]]
    demos = [{"input": [[1, 0, 0]], "output": [[1, 0, 1]]}] * 3
    query = {"input": [[1, 0, 0], [1, 0, 0]], "output": [[1, 0, 1], [1, 0, 1]]}
    assert lesson_status(demos + [query], first_color) == "ambiguous_query"
    assert lesson_status(demos + [query], mirror_all) == "survived_all"
    assert lesson_status([query] + demos, first_color) == "demonstrations_refute"
    return {"self_test": "pass", "rivals": list(RIVALS), "literal_fixtures_only": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("self-test", help="Check deterministic literal mirror/rival fixtures")
    sampling = commands.add_parser("search", help="Search fixed four-pair windows with Python diagnostics")
    sampling.add_argument("--seed-start", type=int, default=0)
    sampling.add_argument("--seeds", type=int, default=600)
    sampling.add_argument("--sample-index", type=int, default=0)
    sampling.add_argument("--difficulty", choices=("easy", "medium", "hard"))
    sampling.add_argument("--source", help="Optional explicit source snapshot, resolved from cwd")
    sampling.add_argument("--out", required=True, help="New JSON report path")
    checking = commands.add_parser("verify", help="Verify captured lessons against public canonical labels")
    checking.add_argument("--capture", required=True)
    checking.add_argument("--receipt", help="Use this existing public apply receipt; otherwise execute Catalog.apply")
    checking.add_argument("--timeout", type=int, default=300)
    checking.add_argument("--out", required=True, help="New JSON report path")
    args = parser.parse_args()
    if args.command == "self-test":
        print(json.dumps(self_test(), sort_keys=True))
        return 0
    if args.command == "search" and (args.seeds < 1 or args.sample_index < 0):
        parser.error("--seeds must be positive; --sample-index must be nonnegative")
    report = search(args) if args.command == "search" else verify(args)
    with Path(args.out).open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"out": args.out, "origin_generator_sha256": report["origin_generator_sha256"],
                      "counts": report.get("counts"), "rival_counts": report.get("rival_counts"),
                      "verified_lessons": len(report.get("findings", []))}, sort_keys=True))
    return int(bool(report.get("first_errors")) or any(
        row["status"] != "ambiguous_query" or not row["python_mirror_matches_authority"]
        for row in report.get("findings", [])))


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
