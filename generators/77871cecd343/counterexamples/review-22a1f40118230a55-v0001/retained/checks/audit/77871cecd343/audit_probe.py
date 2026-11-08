#!/usr/bin/env python3
"""Reproduce a canvas-size / cross-offset shortcut through public Racket apply.

All writes stay in the assigned audit directory. No private runner API is used.
Existing evidence is preserved: reruns require a fresh --out directory.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


TASK = "77871cecd343"
SELECTED_GENERATOR = "5e1fdbc628e7c565974c9cfeacef0d6fbe5b412ce9ab23a6f45a94ffe4ff0aca"
SELECTED_RULE = "1bad9bf6a465"

# Each canvas size identifies sample_index % 3 in every default difficulty.
SIZE_PHASE = {
    (9, 9): 0, (11, 11): 0, (13, 13): 0,
    (9, 11): 1, (13, 9): 1, (13, 11): 1, (15, 13): 1,
    (11, 9): 2, (9, 13): 2, (11, 13): 2, (13, 15): 2,
}
COL_FROM_PHASE_AND_ROW = {
    0: {-1: 1, 0: 0, 1: -1},
    1: {-1: -1, 0: -1, 1: 0},
    2: {-1: 0, 0: 1, 1: 1},
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def grid_hash(grid):
    return digest(json.dumps(grid, separators=(",", ":")).encode())


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def axes(grid):
    rows = [r for r, row in enumerate(grid) if all(v == 9 for v in row)]
    cols = [c for c in range(len(grid[0])) if all(row[c] == 9 for row in grid)]
    assert len(rows) == len(cols) == 1
    return rows[0], cols[0]


def reflected(grid, axis_r, axis_c):
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 1:
                for rr, cc in ((r, 2 * axis_c - c),
                               (2 * axis_r - r, c),
                               (2 * axis_r - r, 2 * axis_c - c)):
                    if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] != 9:
                        out[rr][cc] = 8
    return out


def reflection_oracle(grid):
    """Supplementary independent Python geometry, never reference authority."""
    return reflected(grid, *axes(grid))


def size_row_shortcut(grid):
    """Canonical-fitting rival: look up an off-center vertical divider by size.

    It locates only the horizontal divider. Centered crosses are a special case;
    otherwise it never searches for the vertical divider's actual position.
    """
    h, w = len(grid), len(grid[0])
    axis_r = next(r for r, row in enumerate(grid) if all(v == 9 for v in row))
    if axis_r == h // 2 and all(row[w // 2] == 9 for row in grid):
        axis_c = w // 2
    else:
        phase = SIZE_PHASE.get((h, w))
        offset = COL_FROM_PHASE_AND_ROW[phase][axis_r - h // 2] if phase is not None else 0
        axis_c = w // 2 + offset
    return reflected(grid, axis_r, axis_c)


def run(args):
    packet = args.packet_root.resolve()
    repo = packet / "repo"
    out = (packet / args.out).resolve()
    if not out.is_relative_to(packet / "checks/audit" / TASK):
        raise ValueError("--out must be under the assigned audit directory")
    out.mkdir(parents=True, exist_ok=True)
    if (out / "summary.json").exists() or (out / "racket.json").exists():
        raise FileExistsError("Use a fresh --out subdirectory to preserve existing evidence")
    sys.path.insert(0, str(repo / "shared/runtime"))
    sys.path.insert(0, str(repo / "src"))
    from reviewer_support import find_root, canonical_path, canonical_pairs
    from arcpuzzles import Catalog

    root = find_root(repo)
    source = root / "generators" / TASK / "generator.py"
    source_sha = digest(source.read_bytes())
    assert source_sha == SELECTED_GENERATOR, source_sha
    catalog = Catalog(root).describe(TASK)
    assert catalog["generator_sha256"] == source_sha
    assert catalog["rule_hash"] == SELECTED_RULE
    spec = importlib.util.spec_from_file_location("audit_target_77871cecd343", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)

    selected_rows = []
    for line_number, line in enumerate(canonical_path(root).read_text().splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK:
            selected_rows.append((line_number, line, row))
    assert len(selected_rows) == 1
    line_number, line, selected = selected_rows[0]
    rule_text = selected["program_solution"]
    assert digest(" ".join(rule_text.split()).encode())[:12] == SELECTED_RULE
    write_json(out / "selected_canonical.json", selected)
    pairs = canonical_pairs(TASK, root=root)
    assert len(pairs) == 5

    report = {
        "task_id": TASK,
        "finding_id": "A778-1",
        "classification": "Reproduced default-distribution shortcut",
        "phase": "audit of unchanged selected source",
        "generator_sha256": source_sha,
        "version": gen.VERSION,
        "rule_hash": SELECTED_RULE,
        "rule_text_sha256": digest(rule_text.encode()),
        "probe_sha256": digest(Path(__file__).read_bytes()),
        "canonical_selection": {
            "path": "repo/shared/data/canonical/puzzles.jsonl",
            "line": line_number,
            "variants": 1,
            "exact_row_sha256_without_newline": digest(line.encode()),
            "usable_pairs": len(pairs),
        },
        "sampling": {
            "count_per_band": args.count,
            "sample_index_inclusive": [0, args.count - 1],
            "seed_formula": "seed_start + sample_index",
            "seed_inclusive": [args.seed_start, args.seed_start + args.count - 1],
            "overrides": {},
        },
        "canonical": {
            "self_check_passes": sum(not gen.self_check(p["input"]) for p in pairs),
            "oracle_matches": sum(reflection_oracle(p["input"]) == p["output"] for p in pairs),
            "new_rival_matches": sum(size_row_shortcut(p["input"]) == p["output"] for p in pairs),
            "declared_canonical_shortcut_matches": {
                name: sum(rival(p["input"]) == p["output"] for p in pairs)
                for name, rival in gen.CANONICAL_SHORTCUTS.items()
            },
        },
        "bands": {},
    }
    samples = {}
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(args.seed_start + i, i, difficulty=band) for i in range(args.count)]
        samples[band] = grids
        labels = [reflection_oracle(grid) for grid in grids]
        report["bands"][band] = {
            "draws": len(grids),
            "unique_inputs": len({grid_hash(g) for g in grids}),
            "invalid": sum(bool(gen.self_check(g)) for g in grids),
            "nondeterministic": sum(g != gen.generate(args.seed_start + i, i, difficulty=band)
                                    for i, g in enumerate(grids)),
            "new_rival_matches_python_oracle": sum(size_row_shortcut(g) == y for g, y in zip(grids, labels)),
            "declared_rival_refutations_python_oracle": {
                name: sum(rival(g) != y for g, y in zip(grids, labels))
                for name, rival in gen.LESSON_COMPETITORS.items()
            },
            "dimensions": sorted({(len(g), len(g[0])) for g in grids}),
            "cross_offsets": sorted({(r - len(g) // 2, c - len(g[0]) // 2)
                                      for g in grids for r, c in [axes(g)]}),
        }
        write_json(out / f"{band}_input.json", grids)

    # Four demonstrations and the next query, at every cyclic start of the
    # 36-phase default schedule. These labels are explicitly Python diagnostics.
    lesson_counts = Counter()
    per_declared_rival = Counter()
    lesson_unique = set()
    for band in ("easy", "medium", "hard"):
        for start in range(36):
            lesson = []
            for offset in range(5):
                grid = gen.generate(7787300 + start, start + offset, difficulty=band)
                lesson_unique.add(grid_hash(grid))
                lesson.append({"input": grid, "output": reflection_oracle(grid)})
            lesson_counts["windows"] += 1
            lesson_counts["pair_occurrences"] += len(lesson)
            lesson_counts["new_rival_fits_all_five"] += all(size_row_shortcut(p["input"]) == p["output"]
                                                          for p in lesson)
            lesson_counts["declared_validator_errors"] += bool(gen.lesson_identifiable(lesson[:4], lesson[4]))
            for name, rival in gen.LESSON_COMPETITORS.items():
                per_declared_rival[name] += any(rival(p["input"]) != p["output"] for p in lesson[:4])
    report["lesson_diagnostic"] = {
        "labels": "independent Python reflection diagnostic; not an additional Racket-labelled census",
        "policy": "four consecutive demos, fifth input query; same seed per window",
        "bands": ["easy", "medium", "hard"],
        "start_inclusive": [0, 35],
        "seed_formula": "7787300 + start",
        "sample_index_formula": "start + offset, offset=0..4",
        "overrides": {},
        **lesson_counts,
        "unique_inputs": len(lesson_unique),
        "declared_rival_demo_refuting_windows": dict(per_declared_rival),
    }

    witness_meta = {"seed": 7787199, "sample_index": 1, "difficulty": "medium", "overrides": {"grid_w": 9}}
    witness = gen.generate(witness_meta["seed"], witness_meta["sample_index"],
                           difficulty=witness_meta["difficulty"], **witness_meta["overrides"])
    assert gen.self_check(witness) == []
    assert size_row_shortcut(witness) != reflection_oracle(witness)
    write_json(out / "input.json", [witness] + [p["input"] for p in pairs])

    commands = []
    for label in ("witness_and_canonical", "easy", "medium", "hard"):
        in_name = "input.json" if label == "witness_and_canonical" else f"{label}_input.json"
        out_name = "racket.json" if label == "witness_and_canonical" else f"{label}_racket.json"
        relative = out.relative_to(packet)
        argv = ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
                "--input", f"../{relative}/{in_name}", "--out", f"../{relative}/{out_name}"]
        result = subprocess.run(argv, cwd=packet, text=True, capture_output=True)
        log_name = f"{label}_apply.log"
        (out / log_name).write_text(result.stdout + result.stderr)
        commands.append({"cwd": "packet_root", "effective_cwd": "repo", "argv": argv,
                         "exit_code": result.returncode,
                         "evidence_paths": [str(relative / in_name), str(relative / out_name), str(relative / log_name)]})
        write_json(out / "commands.json", {"verification_commands": commands})
        if result.returncode:
            raise RuntimeError(f"Public apply failed: {label}; see {log_name}")
        applied = json.loads((out / out_name).read_text())
        assert applied["generator_sha256"] == source_sha
        assert applied["executed_rule_hash"] == SELECTED_RULE
        assert applied["rule_hash_matches_catalog"] is True
        assert all(not item["error"] for item in applied["results"])
        actuals = [item["output"] for item in applied["results"]]
        inputs = [item["input"] for item in applied["results"]]
        assert all(reflection_oracle(g) == y for g, y in zip(inputs, actuals))
        if label == "witness_and_canonical":
            assert actuals[1:] == [p["output"] for p in pairs]
            rival = size_row_shortcut(witness)
            differences = [{"row": r, "col": c, "racket": actuals[0][r][c], "rival": rival[r][c]}
                           for r in range(len(witness)) for c in range(len(witness[0]))
                           if actuals[0][r][c] != rival[r][c]]
            write_json(out / "counterexample.json", {
                "task_id": TASK, "finding_id": "A778-1", "generator_sha256": source_sha,
                "rule_hash": SELECTED_RULE, "rule_text_sha256": applied["rule_text_sha256"],
                **witness_meta, "input": witness, "input_sha256": grid_hash(witness),
                "self_check": gen.self_check(witness), "documented_domain": True,
                "domain_basis": "Generated with the advertised exact grid_w=9 override; 9x9 dimensions, offsets (-1,-1), 5 connected source cells in top_right, all reflected targets in bounds and background.",
                "observable_axes": gen.observe_overrides(witness),
                "actual_racket_output": actuals[0], "rival_output": rival,
                "rival_name": "assume_column_offset_from_dimensions_and_row",
                "actual_axes": list(axes(witness)), "rival_axes": [3, 5],
                "different_cells": differences, "command": commands[-1],
                "racket_result_index": 0,
            })
            report["counterexample"] = {**witness_meta, "self_check": [], "documented_domain": True,
                                        "different_cells": len(differences), "racket_result_index": 0}
            report["canonical"]["racket_matches_stored_labels"] = sum(a == p["output"] for a, p in zip(actuals[1:], pairs))
        else:
            assert len(actuals) == args.count
            report["bands"][label]["racket_outputs"] = len(actuals)
            report["bands"][label]["python_oracle_matches_racket"] = sum(reflection_oracle(g) == y for g, y in zip(inputs, actuals))
            report["bands"][label]["new_rival_matches_racket"] = sum(size_row_shortcut(g) == y for g, y in zip(inputs, actuals))
        print(json.dumps({"public_apply": label, "exit_code": result.returncode, "grids": len(actuals)}), flush=True)

    assert digest(source.read_bytes()) == source_sha
    assert report["canonical"]["new_rival_matches"] == len(pairs)
    assert all(v == len(pairs) for v in report["canonical"]["declared_canonical_shortcut_matches"].values())
    assert all(band["new_rival_matches_racket"] == args.count and band["invalid"] == band["nondeterministic"] == 0
               for band in report["bands"].values())
    report["racket_total_grids"] = 3 * args.count + 6
    report["unchanged_generator_sha256_after"] = digest(source.read_bytes())
    write_json(out / "summary.json", report)
    relative = out.relative_to(packet)
    commands.append({"cwd": "packet_root", "argv": ["python3", *sys.argv], "exit_code": 0,
                     "evidence_paths": [str(relative / name) for name in
                                        ("audit_probe.py", "summary.json", "counterexample.json", "selected_canonical.json")]})
    write_json(out / "commands.json", {"verification_commands": commands})
    print(json.dumps({"status": "reproduced", "finding_id": "A778-1", "racket_total_grids": report["racket_total_grids"],
                      "summary": str(relative / "summary.json")}), flush=True)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path(f"checks/audit/{TASK}"))
    parser.add_argument("--count", type=int, default=64)
    parser.add_argument("--seed-start", type=int, default=7787100)
    args = parser.parse_args()
    if not 1 <= args.count <= 64:
        parser.error("count must be 1..64 for a compact public-apply batch per band")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
