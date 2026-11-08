"""Findings-only beam audit; writes evidence outside the audited repository.

The rival reads only the first mirror's reflection. Later mirrors follow a
two-same/two-opposite relative-turn schedule, regardless of their colors.
All labeled evidence is obtained with the public arcpuzzles apply command.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import importlib.util
from itertools import product
import json
from pathlib import Path
import re
import subprocess
import sys
from time import monotonic


TASK = "764b6b9e7771"
VECTORS = ((-1, 0), (0, 1), (1, 0), (0, -1))
REFLECTIONS = {4: (1, 0, 3, 2), 6: (3, 2, 1, 0)}


def digest(value):
    return sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def trace(grid, *, schedule_only=False):
    """Independent direction-table simulation; production helpers are unused."""
    sources = [(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color == 2]
    arrows = [(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color == 1]
    assert len(sources) == len(arrows) == 1
    r, c = sources[0]
    heading = VECTORS.index((arrows[0][0] - r, arrows[0][1] - c))
    output = deepcopy(grid)
    visited, mirrors, first_turn = set(), [], None
    while True:
        state = (r, c, heading, len(mirrors) % 4 if schedule_only else 0,
                 first_turn if schedule_only else 0)
        if state in visited:
            stop = "loop"
            break
        visited.add(state)
        dr, dc = VECTORS[heading]
        nr, nc = r + dr, c + dc
        if not (0 <= nr < len(grid) and 0 <= nc < len(grid[0])):
            stop = "edge"
            break
        color = grid[nr][nc]
        if color == 5:
            stop = "wall"
            break
        if color == 0:
            output[nr][nc] = 8
        if color in REFLECTIONS:
            reflected = REFLECTIONS[color][heading]
            if first_turn is None:
                first_turn = 1 if (reflected - heading) % 4 == 1 else -1
            if schedule_only:
                side = first_turn if (len(mirrors) // 2) % 2 == 0 else -first_turn
                heading = (heading + side) % 4
            else:
                heading = reflected
            mirrors.append([nr, nc, color])
        r, c = nr, nc
    return output, {"stop": stop, "mirrors": mirrors, "states": len(visited)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo, output = args.repo.resolve(), args.out.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if (output / "audit_result.json").exists():
        raise FileExistsError("Use a new audit output directory for a replay")
    source = repo / "generators" / TASK / "generator.py"
    source_hash = sha256(source.read_bytes()).hexdigest()
    sys.path.insert(0, str(repo / "shared/runtime"))
    from reviewer_support import canonical_pairs
    spec = importlib.util.spec_from_file_location("audited_beam_generator", source)
    generator = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = generator
    spec.loader.exec_module(generator)
    canonical = canonical_pairs(TASK, root=repo, labeled_only=True)
    with (repo / "shared/data/canonical/puzzles.jsonl").open() as handle:
        row = next(json.loads(line) for line in handle if json.loads(line).get("task_id") == TASK)
    program = row["program_solution"]
    rule_hash = sha256(" ".join(re.sub(r";[^\n]*", "", program).split()).encode()).hexdigest()[:12]
    write(output / "rule_binding.json", {"task_id": TASK, "generator_sha256": source_hash,
          "rule_hash": rule_hash, "rule_text_sha256": sha256(program.encode()).hexdigest(),
          "program_solution": program})

    records = []
    for band_index, difficulty in enumerate(("easy", "medium", "hard")):
        for local_seed in range(50):
            records.append({"kind": "default", "seed": band_index * 1000 + local_seed,
                            "sample_index": local_seed % 5, "difficulty": difficulty, "overrides": {}})
    for index, (difficulty, direction, side, mirrors, walls) in enumerate(product(
        ("easy", "medium", "hard"), ("up", "down", "left", "right"),
        ("left", "right"), (2, 6), (0, 6),
    )):
        records.append({"kind": "minimum_canvas_boundary", "seed": 5000 + index,
                        "sample_index": index % 5, "difficulty": difficulty,
                        "overrides": {"grid_h": 9, "grid_w": 12, "direction": direction,
                                      "turn_side": side, "n_mirrors": mirrors, "n_walls": walls}})

    for item in records:
        grid = generator.generate(item["seed"], item["sample_index"],
                                  difficulty=item["difficulty"], **item["overrides"])
        item["input"] = grid
        item["input_sha256"] = digest(grid)
        item["self_check"] = generator.self_check(grid)
        item["observed_axes"] = generator.observe_overrides(grid)
        item["independent_output"], item["independent_trace"] = trace(grid)
        item["rival_output"], item["rival_trace"] = trace(grid, schedule_only=True)

    mutation_attempts = 0
    for original in records:
        hits = original["independent_trace"]["mirrors"]
        if len(hits) < 3:
            continue
        mutation_attempts += 1
        mr, mc, previous = hits[2]
        changed = deepcopy(original["input"])
        changed[mr][mc] = 10 - previous
        actual, report = trace(changed)
        rival, rival_report = trace(changed, schedule_only=True)
        differing_cells = [[r, c, a, b] for r, (arow, brow) in enumerate(zip(actual, rival))
                           for c, (a, b) in enumerate(zip(arow, brow)) if a != b]
        errors = generator.self_check(changed)
        if not errors and len(differing_cells) >= 6:
            break
    else:
        raise RuntimeError("No lawful discriminating third-mirror recoloring in the bounded search")
    witness = {"base_draw": {key: original[key] for key in ("kind", "seed", "sample_index", "difficulty", "overrides")},
               "mutation": {"row": mr, "column": mc, "old_color": previous, "new_color": 10 - previous,
                            "encounter_index_one_based": 3},
               "mutation_candidates_checked": mutation_attempts,
               "original_input": original["input"], "input": changed,
               "original_self_check": original["self_check"], "self_check": errors,
               "independent_output": actual, "independent_trace": report,
               "rival_output": rival, "rival_trace": rival_report,
               "differing_cells": differing_cells}
    write(output / "witness.json", witness)
    write(output / "input.json", {"inputs": [original["input"], changed]})
    for pair in canonical:
        records.append({"kind": "canonical", "identity": {key: pair[key] for key in ("variant", "split", "pair_index")},
                        "input": pair["input"], "input_sha256": digest(pair["input"]),
                        "canonical_output": pair["output"], "self_check": generator.self_check(pair["input"]),
                        "independent_output": trace(pair["input"])[0],
                        "rival_output": trace(pair["input"], schedule_only=True)[0]})
    write(output / "population.json", records)
    batches = []
    for begin in range(0, len(records), 64):
        index = len(batches)
        path = output / f"batch-{index:02d}-input.json"
        write(path, {"inputs": [item["input"] for item in records[begin:begin + 64]]})
        batches.append((path, output / f"batch-{index:02d}-racket.json", begin))

    receipt = {"task_id": TASK, "status": "running", "generator_sha256": source_hash,
               "rule_hash": rule_hash, "rival_name": "first_mirror_then_two_same_two_opposite",
               "commands": [], "batches": []}
    for input_path, racket_path, begin in [(output / "input.json", output / "racket.json", None), *batches]:
        command = ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
                   "--input", str(input_path.relative_to(repo.parent)).replace("checks/", "../checks/", 1),
                   "--out", str(racket_path.relative_to(repo.parent)).replace("checks/", "../checks/", 1)]
        log = output / (racket_path.stem + ".log")
        start = monotonic()
        with log.open("w") as handle:
            completed = subprocess.run(command, cwd=repo.parent, stdout=handle, stderr=subprocess.STDOUT)
        receipt["commands"].append({"argv": command, "cwd": str(repo.parent),
                                    "effective_payload_cwd": str(repo), "exit_code": completed.returncode,
                                    "elapsed_seconds": round(monotonic() - start, 3), "log": log.name})
        write(output / "audit_result.json", receipt)
        if completed.returncode:
            raise RuntimeError(f"Reference command failed; see {log}")
        applied = json.loads(racket_path.read_text())
        assert applied["generator_sha256"] == source_hash
        assert applied["executed_rule_hash"] == rule_hash == applied["catalog_rule_hash"]
        assert all(item["error"] is None for item in applied["results"])
        if begin is not None:
            for item, labeled in zip(records[begin:begin + 64], applied["results"], strict=True):
                item["racket_output"] = labeled["output"]
                item["racket_output_sha256"] = labeled["output_sha256"]
            receipt["batches"].append({"file": racket_path.name, "begin": begin, "count": len(applied["results"])})
        print(f"Applied {len(applied['results'])} inputs: {racket_path.name}", flush=True)

    write(output / "population.json", records)
    exact = json.loads((output / "racket.json").read_text())
    assert exact["results"][0]["output"] == original["independent_output"] == original["rival_output"]
    witness["racket_output"] = exact["results"][1]["output"]
    witness["racket_output_sha256"] = exact["results"][1]["output_sha256"]
    assert witness["racket_output"] == actual != rival
    write(output / "witness.json", witness)
    receipt.update({"status": "complete", "classification": "reproduced support shortcut with a lawful off-support counterexample",
                    "generated_draws": sum(item["kind"] != "canonical" for item in records),
                    "default_draws": sum(item["kind"] == "default" for item in records),
                    "minimum_canvas_boundary_draws": sum(item["kind"] == "minimum_canvas_boundary" for item in records),
                    "canonical_pairs": sum(item["kind"] == "canonical" for item in records),
                    "unique_generated_inputs": len({item["input_sha256"] for item in records if item["kind"] != "canonical"}),
                    "self_check_failures": sum(bool(item["self_check"]) for item in records),
                    "independent_trace_racket_mismatches": sum(item["independent_output"] != item["racket_output"] for item in records),
                    "rival_racket_mismatches_on_population": sum(item["rival_output"] != item["racket_output"] for item in records),
                    "canonical_label_mismatches": sum(item["kind"] == "canonical" and item["canonical_output"] != item["racket_output"] for item in records),
                    "witness_differing_cells": len(differing_cells), "source_unchanged": sha256(source.read_bytes()).hexdigest() == source_hash,
                    "audit_command": {"argv": ["python3", str(Path(__file__).resolve()), *sys.argv[1:]],
                                      "cwd": str(Path.cwd()), "exit_code": 0}})
    write(output / "audit_result.json", receipt)
    print(json.dumps({key: value for key, value in receipt.items() if key not in ("commands", "batches")}, indent=2))


if __name__ == "__main__":
    main()
