"""One source-bound adversarial witness; exactly one generation and Racket apply."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import signal
import time

from reviewer_support import canonical_path, find_root, load_selected_generator
from puzzle_generators.rule_wrap import wrap_rule
from arc_repl.racket_bridge import RacketBridge

OUT = Path(__file__).resolve().parent
ROOT = find_root(__file__)
TASK = "1aa3cbf99113"
PIN = "4191b4dfb59a84201e339c9abcf3f24ce084116de9c87050a7de140bc1f263e7"
RULE_PIN = "1121b582d471"
SEED_HEX = "0cee698b31eff3af08d0cbd9d4f1b864325081319f9dbecf42e2c4953fef5611"


def sha(value):
    return hashlib.sha256(value).hexdigest()


def components(grid):
    seen, result = set(), []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0 or (r, c) in seen:
                continue
            stack, cells = [(r, c)], []
            seen.add((r, c))
            while stack:
                a, b = stack.pop()
                cells.append([a, b])
                for x, y in ((a - 1, b), (a + 1, b), (a, b - 1), (a, b + 1)):
                    if (0 <= x < len(grid) and 0 <= y < len(row)
                            and (x, y) not in seen and grid[x][y] == value):
                        seen.add((x, y))
                        stack.append((x, y))
            result.append({"color": value, "size": len(cells), "cells": sorted(cells)})
    return result


def deadline(signum, frame):
    raise TimeoutError("Single targeted probe exceeded its 110-second internal deadline")


def main():
    started = time.monotonic()
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(110)
    receipt = {
        "ticket_id": "ticket-a90db1c3dd0a378c",
        "type": "adversarial_witness",
        "task_id": TASK,
        "rule_task_id": TASK,
        "seed_hex": SEED_HEX,
        "seed_conversion": "int(seed_hex, 16)",
        "seed": int(SEED_HEX, 16),
        "targeted_probe_limit_seconds": 120,
        "generation_count": 0,
        "rule_application_count": 0,
        "shortcut": {
            "name": "threshold_total_color_frequency",
            "description": "For each nonzero input color, count its cells over the entire grid; recolor that color to 2 if its total count is at most 3, otherwise to 8. This ignores connected components.",
            "plausibility": "On all-distinct-color draws with one connected object per color, global color frequency equals object size. The declared same_color mode can separate them.",
        },
        "scope": "One supported nondegenerate override configuration, one generated input, one actual Racket application. No seed sweep, peer battery, or lesson assembly.",
        "status": "unknown",
    }
    try:
        gen, source, digest = load_selected_generator(TASK, root=ROOT)
        receipt["generator"] = {"path": "repo/" + str(source.relative_to(ROOT)), "sha256": digest}
        if digest != PIN:
            raise ValueError("Generator pin mismatch; generate() was not called")
        rows = []
        for line in canonical_path(ROOT).read_text().splitlines():
            row = json.loads(line)
            if row.get("task_id") == TASK:
                rows.append(row)
        if len(rows) != 1 or rows[0].get("source") != "custom":
            raise ValueError("Unexpected canonical task/source selection")
        row = rows[0]
        program = row["program_solution"]
        rule_hash = sha(" ".join(program.split()).encode())[:12]
        if rule_hash != RULE_PIN:
            raise ValueError("Canonical rule pin mismatch; Racket was not called")
        callable_text = wrap_rule(program)
        receipt["rule"] = {
            "task_id": TASK, "source": row["source"], "rule_hash": rule_hash,
            "raw_program_sha256": sha(program.encode()),
            "callable_text_sha256": sha(callable_text.encode()),
            "canonical_row_count": len(rows),
            "canonical_pair_count": sum(len(row.get(split, [])) for split in ("train", "test")),
        }
        config = {
            "difficulty": None, "grid_h": 16, "grid_w": 16,
            "n_small_objects": 1, "n_large_objects": 1,
            "small_kind": "single", "large_kind": "rect",
            "size_progression": "linear", "placement": "corners",
            "input_palette_mode": "same_color",
        }
        receipt["configuration"] = {"sample_index": 0, **config}
        receipt["generation_count"] += 1
        grid = gen.generate(int(SEED_HEX, 16), 0, **config)
        shapes = components(grid)
        errors = gen.self_check(grid, difficulty=None, meta=config)
        counts = Counter(value for values in grid for value in values if value)
        legal = (len(grid) == 16 and all(len(values) == 16 for values in grid)
                 and all(type(v) is int and 0 <= v <= 9 for values in grid for v in values)
                 and len(counts) == 1 and not (set(counts) & {2, 8})
                 and sorted(shape["size"] for shape in shapes) == [1, 16]
                 and not errors)
        receipt["lawfulness"] = {
            "supported_non_degenerate_overrides": True,
            "self_check_errors": errors,
            "independent_domain_checks_pass": legal,
            "component_sizes": sorted(shape["size"] for shape in shapes),
            "input_color_counts": dict(counts),
            "details": "Supported 16x16 ordinary canvas; one singleton and one 4x4 rectangle, same allowed input color, disconnected components, both required threshold branches, no degenerate texture.",
        }
        if not legal:
            raise ValueError("The one draw did not produce the planned lawful contrast; no retry allowed")
        rival = [[(2 if counts[v] <= 3 else 8) if v else 0 for v in values] for values in grid]
        literal = "'(" + " ".join("(" + " ".join(map(str, values)) + ")" for values in grid) + ")"
        with RacketBridge(timeout=20.0, startup_timeout=30.0) as bridge:
            receipt["runtime_identity"] = bridge.runtime_identity
            receipt["rule_application_count"] += 1
            output = bridge.eval_text("(" + callable_text + " " + literal + ")")
        independent = [list(values) for values in grid]
        for shape in shapes:
            for r, c in shape["cells"]:
                independent[r][c] = 2 if shape["size"] <= 3 else 8
        if output != independent:
            raise ValueError("Racket disagreed with independent connected-component oracle")
        differences = [{"row": r, "col": c, "rule": output[r][c], "shortcut": rival[r][c]}
                       for r in range(16) for c in range(16) if output[r][c] != rival[r][c]]
        witness = {
            "input": grid, "reference_output": output, "shortcut_output": rival,
            "components": shapes, "differences": differences,
        }
        raw = (json.dumps(witness, indent=2) + "\n").encode()
        (OUT / "witness.json").write_bytes(raw)
        receipt["witness"] = {
            "path": "checks/tickets/ticket-a90db1c3dd0a378c/witness.json",
            "sha256": sha(raw), "dimensions": [16, 16],
            "differing_cells": len(differences), "differences": differences,
            "racket_matches_independent_component_oracle": True,
            "shortcut_defeated": bool(differences),
        }
        receipt["status"] = "completed" if differences else "unknown"
        receipt["conclusion"] = (
            "One lawful current-generator witness defeats global color-frequency classification. This is useful adversarial evidence, not a new generator safety finding."
            if differences else "The single lawful draw did not defeat the shortcut."
        )
        receipt["limits"] = (
            "No canonical pairs are present, so canonical-example fit cannot be assessed. "
            "No production lesson frequencies, other palette modes, or general quality claims were measured. "
            "The existing needs_triage easy-draw branch-loss report remains separately open and was not rerun."
        )
    except Exception as exc:
        receipt["error"] = type(exc).__name__ + ": " + str(exc)
    finally:
        signal.alarm(0)
        receipt["probe_elapsed_seconds"] = round(time.monotonic() - started, 6)
        (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(json.dumps({k: receipt[k] for k in (
            "ticket_id", "status", "generation_count", "rule_application_count", "probe_elapsed_seconds")}
            | {"component_sizes": receipt.get("lawfulness", {}).get("component_sizes"),
               "witness_difference_cells": receipt.get("witness", {}).get("differing_cells"),
               "error": receipt.get("error")}))
    return 0 if receipt["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
