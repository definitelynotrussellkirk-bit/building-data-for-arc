"""Source-bound, public-CLI probe of bar-rotation teaching shortcuts.

Run through the packet's public ``review.py run`` wrapper.  The probe loads
canonical authoring pairs only after a blind solve and obtains every comparison
label by invoking ``python -m arcpuzzles apply``.  No private runner imports.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys

TASK_ID = "44e865b6a43e"


def profile(grid):
    """Read geometry independently of the selected generator's mirror."""
    rows, width = len(grid), len(grid[0])
    colors, heights = [], []
    for col in range(1, width, 2):
        occupied = [r for r in range(rows) if grid[r][col] != 7]
        colors.append(grid[occupied[0]][col])
        heights.append(len(occupied))
    return rows, colors, heights


def render(rows, colors, heights):
    out = [[7] * (2 * len(colors) + 1) for _ in range(rows)]
    for i, (color, height) in enumerate(zip(colors, heights)):
        for row in range(max(0, rows - height), rows):
            out[row][2 * i + 1] = color
    return out


def rotate(values, amount):
    amount %= len(values)
    return values[-amount:] + values[:-amount] if amount else list(values)


def shifted(grid, color_shift=1, height_shift=-1):
    rows, colors, heights = profile(grid)
    return render(rows, rotate(colors, color_shift), rotate(heights, height_shift))


def nearest_equal_height_association(grid):
    """Infer moved-shape identities by a nearest one-to-one association.

    First move the height sequence one place left.  Match each resulting shape
    to an equally tall original shape, requiring every shape to move and
    minimizing total horizontal displacement (lexicographic tie breaking).
    Recolor it from the source two positions to its left.  This matches the
    intended transformation when shape identity is unambiguous, but swaps the
    identities of some equal-height shapes to avoid a long wraparound move.

    The rule uses only local scene attributes, with no canonical grid lookup,
    color table, learned sample threshold, or special-case task dimensions.
    """
    rows, colors, heights = profile(grid)
    n = len(colors)
    moved = rotate(heights, -1)
    candidates = (
        p for p in itertools.permutations(range(n))
        if all(p[i] != i and heights[p[i]] == moved[i] for i in range(n))
    )
    donors = min(candidates, key=lambda p: (sum(abs(p[i] - i) for i in range(n)), p))
    return render(rows, [colors[(j - 2) % n] for j in donors], moved)


def square_canvas(grid):
    _rows, colors, heights = profile(grid)
    return render(len(grid[0]), rotate(colors, 1), rotate(heights, -1))


RIVALS = {
    "nearest_equal_height_association": nearest_equal_height_association,
    "square_canvas": square_canvas,
    "whole_bars_right": lambda g: shifted(g, 1, 1),
    "colors_left_heights_left": lambda g: shifted(g, -1, -1),
    "colors_left_heights_fixed": lambda g: shifted(g, -1, 0),
    "colors_left_heights_right": lambda g: shifted(g, -1, 1),
    "colors_right_heights_fixed": lambda g: shifted(g, 1, 0),
    "colors_fixed_heights_left": lambda g: shifted(g, 0, -1),
    "colors_fixed_heights_right": lambda g: shifted(g, 0, 1),
    "identity": lambda g: [list(row) for row in g],
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def color_substitution_conflicts(pairs, *, move_bars_left=False):
    assignments = defaultdict(list)
    for pair in pairs:
        _rows, colors, _heights = profile(pair["input"])
        _rows, output_colors, _heights = profile(pair["output"])
        if move_bars_left:
            colors = rotate(colors, -1)
        for source, target in zip(colors, output_colors):
            assignments[source].append({
                "target": target,
                "split": pair["split"],
                "pair_index": pair["pair_index"],
            })
    return {str(c): rows for c, rows in assignments.items()
            if len({row["target"] for row in rows}) > 1}


def support_facts(grid):
    rows, colors, heights = profile(grid)
    counts = Counter(heights)
    pairs = [[i, j] for i in range(len(heights)) for j in range(i + 1, len(heights))
             if heights[i] == heights[j]]
    return {
        "grid_h": rows, "grid_w": len(grid[0]), "n_bars": len(colors),
        "colors": colors, "heights": heights,
        "repeated_pairs": pairs,
        "nonminimum_repeat": any(count > 1 and h != min(heights) for h, count in counts.items()),
        "nonendpoint_repeat": any(pair != [0, len(heights) - 1] for pair in pairs),
        "interior_repeat": any(0 < i < j < len(heights) - 1 for i, j in pairs),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--per-band", type=int, default=120)
    parser.add_argument("--seed", type=int, default=73000)
    parser.add_argument("--resume", action="store_true", help="Label retained source-bound subjects without drawing again")
    args = parser.parse_args()
    if args.per_band < 1:
        parser.error("--per-band must be positive")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=args.resume)

    # Bind the helper to this probe's owning tree, never an unrelated checkout.
    for candidate in Path(__file__).resolve().parents:
        helper = candidate / "shared/runtime/reviewer_support.py"
        if helper.is_file():
            sys.path.insert(0, str(helper.parent))
            break
    from reviewer_support import canonical_pairs, find_root, load_selected_generator
    root = find_root(__file__)
    generator, source, source_sha = load_selected_generator(TASK_ID, root=root)
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    if not args.resume:
        (out / "generator_source.py").write_bytes(source.read_bytes())
    source_sha = hashlib.sha256((out / "generator_source.py").read_bytes()).hexdigest()
    (out / "probe_source.py").write_bytes(Path(__file__).read_bytes())

    subjects = []
    if args.resume:
        subjects = json.loads((out / "subjects.json").read_text())
        if any(subject["input_sha256"] != digest(subject["input"]) for subject in subjects):
            raise ValueError("Retained subject hash mismatch")
    else:
        for pair in canonical:
            subjects.append({"kind": "canonical", "variant": pair["variant"],
                             "split": pair["split"], "pair_index": pair["pair_index"],
                             "input": pair["input"], "retained_label": pair["output"]})
        subjects.extend([
            {"kind": "counterexample", "name": "interior_duplicate_on_square_canvas",
             "input": render(9, [1, 2, 3, 4], [1, 2, 1, 3])},
            {"kind": "counterexample", "name": "rectangular_distinct_heights",
             "input": render(8, [1, 2, 3], [1, 2, 3])},
            {"kind": "counterexample", "name": "one_demo_refutes_both_canonical_fitting_rivals",
             "input": render(7, [1, 2, 3, 4], [1, 2, 1, 3])},
        ])
        for band in ("easy", "medium", "hard"):
            for i in range(args.per_band):
                seed = args.seed + i
                index = i * 37 + 5
                grid = generator.generate(seed, index, difficulty=band)
                subjects.append({"kind": "production", "difficulty": band,
                                 "seed": seed, "sample_index": index, "input": grid})
            for index in range(8):
                grid = generator.generate(args.seed, index, difficulty=band)
                subjects.append({"kind": "lesson_window", "difficulty": band,
                                 "seed": args.seed, "sample_index": index, "input": grid})
        for subject in subjects:
            subject["input_sha256"] = digest(subject["input"])
            subject["profile"] = support_facts(subject["input"])
            subject["self_check"] = generator.self_check(subject["input"])
        (out / "subjects.json").write_text(json.dumps(subjects, indent=2) + "\n")
    input_path = out / "inputs.json"
    input_path.write_text(json.dumps({"inputs": [s["input"] for s in subjects]}) + "\n")
    receipt = out / "racket_labels.json"
    commands, batches, result_rows = [], [], []
    for start in range(0, len(subjects), 64):
        batch_input = out / f"inputs-{start // 64:03d}.json"
        batch_receipt = out / f"racket-labels-{start // 64:03d}.json"
        batch_input.write_text(json.dumps({"inputs": [s["input"] for s in subjects[start:start + 64]]}) + "\n")
        command = [sys.executable, "-m", "arcpuzzles", "apply", TASK_ID,
                   "--input", str(batch_input), "--reference", "canonical",
                   "--check-generator-domain", "--timeout", "120", "--out", str(batch_receipt)]
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=180)
        commands.append({"command": command, "cwd": str(root), "exit_code": result.returncode,
                         "stdout": result.stdout, "stderr": result.stderr})
        (out / "commands.json").write_text(json.dumps(commands, indent=2) + "\n")
        if result.returncode:
            print(result.stdout, end="")
            print(result.stderr, end="", file=sys.stderr)
            raise SystemExit(result.returncode)
        raw = json.loads(batch_receipt.read_text())
        # Keep parsing explicit; a changed public receipt must fail visibly.
        result_rows.extend(raw["results"])
        batches.append({"first_subject": start, "count": len(raw["results"]),
                        "path": batch_receipt.name, "sha256": hashlib.sha256(batch_receipt.read_bytes()).hexdigest()})
    receipt.write_text(json.dumps({"schema": "public-apply-batch-aggregate-v1",
                                   "batches": batches, "results": result_rows}, indent=2) + "\n")
    if len(result_rows) != len(subjects):
        raise ValueError("Racket receipt subject count mismatch")
    scores = []
    for subject, label in zip(subjects, result_rows):
        expected = label["output"]
        if subject["kind"] == "canonical" and expected != subject["retained_label"]:
            raise ValueError("Canonical runtime disagrees with retained canonical label")
        if shifted(subject["input"]) != expected:
            raise ValueError("Independent positional reconstruction disagrees with Racket")
        predictions = {name: fn(subject["input"]) for name, fn in RIVALS.items()}
        if not args.resume and hasattr(generator, "LESSON_COMPETITORS"):
            if set(generator.LESSON_COMPETITORS) != set(RIVALS):
                raise ValueError("Probe and selected lesson rival inventories differ")
            if any(generator.LESSON_COMPETITORS[name](subject["input"]) != pred
                   for name, pred in predictions.items()):
                raise ValueError("Independent probe and selected rival implementations differ")
        scores.append({**subject, "output": expected,
                       "rivals": {name: {"matches": pred == expected,
                                         "prediction": pred}
                                  for name, pred in predictions.items()}})
    fit = {name: all(row["rivals"][name]["matches"] for row in scores if row["kind"] == "canonical")
           for name in RIVALS}
    production = {}
    for band in ("easy", "medium", "hard"):
        selected = [row for row in scores if row.get("difficulty") == band and row["kind"] == "production"]
        production[band] = {
            "count": len(selected),
            "rival_matches": {name: sum(row["rivals"][name]["matches"] for row in selected) for name in RIVALS},
            "support_counts": {fact: sum(bool(row["profile"][fact]) for row in selected)
                               for fact in ("repeated_pairs", "nonminimum_repeat", "nonendpoint_repeat", "interior_repeat")},
            "first_counterexamples": {
                name: next(({key: row[key] for key in ("seed", "sample_index", "profile", "input_sha256")}
                            for row in selected if not row["rivals"][name]["matches"]), None)
                for name in RIVALS},
        }
    lesson_windows = []
    for band in ("easy", "medium", "hard"):
        selected = [row for row in scores if row.get("difficulty") == band and row["kind"] == "lesson_window"]
        for n_train in (1, 2, 3):
            for start in range(len(selected) - n_train):
                window = selected[start:start + n_train + 1]
                for query_position, query in enumerate(window):
                    demos = [row for i, row in enumerate(window) if i != query_position]
                    survivors = [name for name in RIVALS if all(row["rivals"][name]["matches"] for row in demos)]
                    ambiguous = [name for name in survivors if not query["rivals"][name]["matches"]]
                    lesson_windows.append({
                        "difficulty": band, "n_train": n_train, "requested_start": start,
                        "seed": args.seed, "query_index": query["sample_index"],
                        "demo_indices": [row["sample_index"] for row in demos],
                        "query_input_sha256": query["input_sha256"],
                        "demo_input_sha256": [row["input_sha256"] for row in demos],
                        "surviving_rivals": survivors, "ambiguous_rivals": ambiguous,
                    })
    minimality = {
        str(n): {"rotations": sum(row["n_train"] == n for row in lesson_windows),
                 "ambiguous_rotations": sum(row["n_train"] == n and bool(row["ambiguous_rivals"]) for row in lesson_windows),
                 "first_ambiguity": next((row for row in lesson_windows if row["n_train"] == n and row["ambiguous_rivals"]), None)}
        for n in (1, 2, 3)
    }
    summary = {
        "schema": "44e865b6a43e-rotation-rivals-v1", "task_id": TASK_ID,
        "generator_sha256": source_sha, "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "canonical_pairs_sha256": digest(canonical), "racket_receipt_sha256": hashlib.sha256(receipt.read_bytes()).hexdigest(),
        "canonical_fits": fit, "production": production,
        "global_color_substitution_conflicts": color_substitution_conflicts(canonical),
        "left_shift_then_global_substitution_conflicts": color_substitution_conflicts(canonical, move_bars_left=True),
        "counterexamples": [row for row in scores if row["kind"] == "counterexample"],
        "schedule_minimality": minimality,
        "racket_command_exit": result.returncode,
        "racket_command_count": len(commands),
        "generator_changed_during_probe": hashlib.sha256(source.read_bytes()).hexdigest() != source_sha,
        "limits": "Finite source-bound sample; no universal lesson-identifiability claim. Every reported output was executed through the canonical public Racket apply command.",
    }
    (out / "scored_subjects.json").write_text(json.dumps(scores, indent=2) + "\n")
    (out / "lesson_windows.json").write_text(json.dumps(lesson_windows, indent=2) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    compact_production = {band: {key: data[key] for key in ("count", "rival_matches", "support_counts")}
                          for band, data in production.items()}
    print(json.dumps({"generator_sha256": source_sha, "canonical_fits": fit,
                      "production": compact_production, "schedule_minimality": minimality,
                      "summary": str(out / "summary.json")}, indent=2))


if __name__ == "__main__":
    main()
