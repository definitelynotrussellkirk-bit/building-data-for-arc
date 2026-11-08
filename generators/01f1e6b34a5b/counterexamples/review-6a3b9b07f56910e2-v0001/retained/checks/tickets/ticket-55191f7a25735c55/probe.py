"""One bounded adversarial witness for the pinned 01f1e6b34a5b source.

Constructed legal lesson, not a claim about ordinary consecutive random draws.
Run once with the packet-selected Racket runtime; no generator files are edited.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import random
import signal
import sys
import time


HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK_ID = "01f1e6b34a5b"
TICKET_ID = "ticket-55191f7a25735c55"
SEED = "8c2cb8ff756dcb5c2e883319626e38d617273dd898c7996b74760162935a3bf1"
EXPECTED_SOURCE = "e4941959b42ae8ea13014eff9cf03b6d0e3bea94e92856cfe14069396abad52d"
EXPECTED_RULE = "528f702b8b50"
COMMAND = (
    "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=shared/runtime:src "
    "timeout 120s python3 ../checks/tickets/" + TICKET_ID + "/probe.py"
)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def make_input(rng, codes, color, motif, height=6, width=5):
    grid = [[0] * width for _ in range(height)]
    for column, code in zip(sorted(rng.sample(range(width), len(codes))), codes):
        grid[0][column] = code
    row0 = rng.randint(1, height - len(motif))
    col0 = rng.randint(0, width - len(motif[0]))
    for r, row in enumerate(motif):
        for c, occupied in enumerate(row):
            if occupied:
                grid[row0 + r][col0 + c] = color
    return grid


def main():
    started = time.monotonic()
    result = {
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "status": "unknown",
        "probe_seed": SEED,
        "seed_interpretation": "random.Random(int(probe_seed, 16)) for colors and placements",
        "command": COMMAND,
        "working_directory": str(REPO),
        "budget": {"targeted_probes": 1, "max_seconds": 120},
        "scope": "Four constructed legal demonstrations and one query; two Racket rules",
        "ordinary_sampling_frequency": "not_measured",
        "construction_limitation": (
            "Inputs satisfy the documented ordinary construction domain, self_check, "
            "and the generator's implemented asymmetry filter. They are deliberately "
            "constructed, not the ordinary outputs for consecutive sample indices."
        ),
    }
    bridge = None
    try:
        sys.path.insert(0, str(REPO / "shared/runtime"))
        sys.path.insert(0, str(REPO / "src"))
        from reviewer_support import load_selected_generator, normalize_grid
        from arc_repl.racket_bridge import RacketBridge

        generator, source_path, source_hash = load_selected_generator(TASK_ID, root=REPO)
        result["generator_source"] = str(source_path.relative_to(REPO))
        result["generator_sha256"] = source_hash
        result["expected_generator_sha256"] = EXPECTED_SOURCE
        if source_hash != EXPECTED_SOURCE:
            raise ValueError("Pinned generator source does not match current bytes")
        with (REPO / "shared/data/canonical/puzzles.jsonl").open() as handle:
            row = next(row for line in handle
                       if (row := json.loads(line)).get("task_id") == TASK_ID)
        program = row["program_solution"]
        rule_hash = sha(" ".join(program.split()).encode())[:12]
        result["canonical_rule_hash"] = rule_hash
        result["canonical_program_sha256"] = sha(program.encode())
        if rule_hash != EXPECTED_RULE:
            raise ValueError("Pinned canonical rule hash does not match current bytes")
        original = "[(= code 4) (flip-ud motif)]"
        replacement = "[(= code 4) (rotate-cw motif)]"
        if program.count(original) != 1:
            raise ValueError("Expected one explicit code4 transform site")
        rival = program.replace(original, replacement, 1)
        result["rival"] = "Treat code4 as code2 (rotate clockwise), retaining all other behavior"
        result["rival_program_sha256"] = sha(rival.encode())
        result["rival_rule_hash"] = sha(" ".join(rival.split()).encode())[:12]
        result["current_audit_index_exists"] = (source_path.parent / "evidence/review_index.json").exists()

        rng = random.Random(int(SEED, 16))
        colors = rng.sample(range(1, 10), 5)
        codes = ((2, 4), (4, 2), (1, 4, 2), (3, 2, 4, 1))
        demonstrations = [make_input(rng, order, colors[i], [[1, 1], [0, 1]])
                          for i, order in enumerate(codes)]
        query = make_input(rng, (4, 1), colors[-1], [[1, 0, 0], [1, 1, 1]])
        inputs = demonstrations + [query]
        lawfulness = []
        for grid in inputs:
            cells = [(r, c, value) for r, row_values in enumerate(grid[1:], 1)
                     for c, value in enumerate(row_values) if value]
            base, variants = generator._motif_variants(cells)
            lawfulness.append({
                "self_check_errors": generator.self_check(grid),
                "implemented_asymmetry_filter_passes": base not in variants,
                "clockwise_equals_flip_ud": variants[0] == variants[2],
                "codes": [value for value in grid[0] if value in (1, 2, 3, 4)],
                "motif_nonzero_cells": len(cells),
                "normalized_motif": base,
            })
        result["lawfulness"] = lawfulness
        if not all(not item["self_check_errors"] and item["implemented_asymmetry_filter_passes"]
                   for item in lawfulness):
            raise ValueError("Constructed witness failed the actual generator checks")
        if not all(item["clockwise_equals_flip_ud"] for item in lawfulness[:-1]):
            raise ValueError("A demonstration does not have the intended transform collision")
        if lawfulness[-1]["clockwise_equals_flip_ud"]:
            raise ValueError("Query does not distinguish the rival")
        if len({json.dumps(grid) for grid in inputs}) != 5:
            raise ValueError("Witness inputs are not distinct")

        compiler_path = REPO / "generators/1f3e27c86f7a/workspace/parametric/prototype.py"
        result["compiler_helper"] = str(compiler_path.relative_to(REPO))
        result["compiler_helper_sha256"] = sha(compiler_path.read_bytes())
        spec = importlib.util.spec_from_file_location("_witness_compiler_support", compiler_path)
        compiler = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = compiler
        spec.loader.exec_module(compiler)
        canonical_wrapped = compiler._wrapped_program(program)
        rival_wrapped = compiler._wrapped_program(rival)
        (HERE / "canonical.rkt").write_text(program)
        (HERE / "rival.rkt").write_text(rival)

        bridge = RacketBridge(timeout=8.0, startup_timeout=20.0)
        bridge.eval_text(f"(define ticket_canonical {canonical_wrapped})")
        bridge.eval_text(f"(define ticket_rival {rival_wrapped})")
        pairs = []
        for index, grid in enumerate(inputs):
            bridge.define_grid("ticket_input", grid)
            canonical = normalize_grid(bridge.eval_text("(ticket_canonical ticket_input)"))
            competing = normalize_grid(bridge.eval_text("(ticket_rival ticket_input)"))
            pairs.append({
                "split": "train" if index < 4 else "test",
                "index": index if index < 4 else 0,
                "input": grid,
                "canonical_output": canonical,
                "rival_output": competing,
                "outputs_equal": canonical == competing,
            })
        fits = all(pair["outputs_equal"] for pair in pairs[:-1])
        disagrees = not pairs[-1]["outputs_equal"]
        result["demonstration_count"] = 4
        result["query_count"] = 1
        result["rival_fits_every_demonstration"] = fits
        result["query_disagreement"] = disagrees
        result["query_answers_used_to_select_rival"] = False
        result["canonical_query_shape"] = [len(pairs[-1]["canonical_output"]), len(pairs[-1]["canonical_output"][0])]
        result["rival_query_shape"] = [len(pairs[-1]["rival_output"]), len(pairs[-1]["rival_output"][0])]
        result["status"] = "finding" if fits and disagrees else "unknown"
        result["summary"] = (
            "The implemented asymmetry check permits CW==flip-UD. The code4-as-CW "
            "rival fits four legal demonstrations but disagrees on a legal query."
            if result["status"] == "finding" else
            "The bounded constructed lesson did not demonstrate the selected shortcut."
        )
        save("witness.json", {"source_bound_result": result, "pairs": pairs})
    except BaseException as error:
        result["status"] = "blocked" if isinstance(error, (ImportError, FileNotFoundError)) else "unknown"
        result["error"] = f"{type(error).__name__}: {error}"
    finally:
        if bridge is not None:
            bridge.shutdown()
        result["elapsed_seconds"] = round(time.monotonic() - started, 6)
        save("result.json", result)
        print(json.dumps({key: result.get(key) for key in (
            "ticket_id", "status", "summary", "error", "rival_fits_every_demonstration",
            "query_disagreement", "canonical_query_shape", "rival_query_shape", "elapsed_seconds",
        )}, sort_keys=True))


if __name__ == "__main__":
    def bounded_timeout(signum, frame):
        raise TimeoutError("Internal 110-second bound reached")
    signal.signal(signal.SIGALRM, bounded_timeout)
    signal.alarm(110)
    main()
