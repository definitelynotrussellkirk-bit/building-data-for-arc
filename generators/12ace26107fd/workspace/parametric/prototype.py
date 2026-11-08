#!/usr/bin/env python3
"""Proposed episode-level shell histogram order; never selected by production.

All labels, including rival predictions, are evaluated by RacketBridge using
the supported rule_wrap normalization. No Python histogram implementation.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import tempfile

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_pairs, canonical_path, find_root


TASK_ID = "12ace26107fd"
ROOT = find_root(__file__)
ORDERS = ("outer_to_inner", "inner_to_outer")
DEFAULT_ORDER = ORDERS[0]
STATUS = "proposed prototype; not production-approved"
_TOOL_STAGE = None


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def resolve_source(identity, *, root=None):
    """Locate an owned source through its actual runtime-manifest mapping.

    A library has the documented repository layout. A runtime must identify
    copied sources in its manifest; a library-layout mirror is only a fallback
    after an execution-layout entry. All paths remain inside the selected tree.
    """
    root = Path(ROOT if root is None else root).resolve()
    manifest = root / "RUNTIME_MANIFEST.json"
    if manifest.is_file():
        files = json.loads(manifest.read_text())["files"]
        entries = [entry for entry in files if entry["library_path"] == identity]
        if not entries:
            # Controller Python is recorded as <controller>/arcpuzzles/...,
            # while its declared copied location is src/arcpuzzles/....
            entries = [entry for entry in files if entry["runtime_path"] == identity]
        entries.sort(key=lambda entry: entry["runtime_path"] == identity)
        candidates = [root / entry["runtime_path"] for entry in entries]
    else:
        candidates = [root / identity]
    for candidate in candidates:
        if candidate.is_file() and candidate.resolve().is_relative_to(root):
            return candidate
    raise FileNotFoundError(f"No retained source for {identity} under {root}")


def canonical_record():
    with canonical_path(ROOT).open() as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise ValueError(f"canonical task not found: {TASK_ID}")


def program_for(output_order=DEFAULT_ORDER):
    if output_order not in ORDERS:
        raise ValueError(f"output_order must be one of {ORDERS}")
    canonical = canonical_record()["program_solution"]
    if output_order == DEFAULT_ORDER:
        return canonical
    # Refuse to mutate a different future authority accidentally.
    suffix = "(list (depth-hist g))))"
    if not canonical.endswith(suffix) or canonical.count(suffix) != 1:
        raise ValueError("canonical final expression changed; prototype needs review")
    return canonical[:-len(suffix)] + "(list (reverse (depth-hist g)))))"


def application(program, grid):
    global _TOOL_STAGE
    # The packet exposes shared/runtime directly, but rule_wrap also imports
    # mapped scripts. Use the public runtime copier rather than fabricate an
    # alternate scripts namespace or duplicate the Racket normalization.
    try:
        have_scripts = importlib.util.find_spec("scripts.comment_solutions") is not None
    except ModuleNotFoundError:
        have_scripts = False
    if not have_scripts:
        from arcpuzzles.catalog import Catalog
        from arcpuzzles.runtime import prepare_runtime
        _TOOL_STAGE = tempfile.TemporaryDirectory(prefix="layer-parametric-runtime-")
        prepare_runtime(Catalog(ROOT), Path(_TOOL_STAGE.name), TASK_ID)
        sys.path.insert(0, _TOOL_STAGE.name)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return f"({wrap_rule(program)} {literal})"


def execute(bridge, program, grid):
    return bridge.eval_text(application(program, grid))


def shared_input():
    """Canonical lawful radius-two diamond: shells contain 8, 4, 1 cells."""
    return [[2 if abs(r - 3) + abs(c - 3) <= 2 else 0 for c in range(7)]
            for r in range(7)]


def _input_draws(seed):
    # Independent layout stream: the parameter is never resampled per pair.
    layout_seed = int(digest(f"{TASK_ID}:layout:{seed}".encode()), 16)
    rng = random.Random(layout_seed)
    shapes = (
        [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
        [(r, c) for r in range(3) for c in range(3)],
        [(r, c) for r in range(5) for c in range(5) if abs(r - 2) + abs(c - 2) <= 2],
    )
    grids = []
    for cells in shapes:
        h, w = rng.randint(7, 12), rng.randint(7, 12)
        sh = max(r for r, _ in cells) + 1
        sw = max(c for _, c in cells) + 1
        top, left = rng.randint(1, h - sh - 1), rng.randint(1, w - sw - 1)
        color = rng.choice(tuple(range(1, 9)))
        grid = [[0] * w for _ in range(h)]
        for r, c in cells:
            grid[top + r][left + c] = color
        grids.append(grid)
    return grids


def generate_episode(seed, bridge):
    """Return model-visible challenge and separate evaluator-only record."""
    output_order = random.Random(seed).choice(ORDERS)  # exactly once per episode
    program = program_for(output_order)
    grids = _input_draws(seed)
    outputs = [execute(bridge, program, grid) for grid in grids]
    public = {
        "train": [{"input": grid, "output": out} for grid, out in zip(grids[:2], outputs[:2])],
        "test": [{"input": grids[2]}],
    }
    rivals = {}
    executions = []
    for rival in ORDERS:
        rival_program = program_for(rival)
        predictions = []
        for index, grid in enumerate(grids):
            prediction = execute(bridge, rival_program, grid)
            predictions.append(prediction)
            executions.append({
                "output_order": rival, "pair_index": index,
                "expression": application(rival_program, grid), "output": prediction,
            })
        differing = [i for i in range(2) if predictions[i] != outputs[i]]
        rivals[rival] = {
            "matches_all_demonstrations": not differing,
            "distinguishing_demo_indices": differing,
            "demonstration_predictions": predictions[:2],
            "query_predictions": predictions[2:],
        }
    surviving = [name for name, check in rivals.items() if check["matches_all_demonstrations"]]
    if surviving != [output_order]:
        raise ValueError(f"demonstrations do not uniquely distinguish declared settings: {surviving}")
    return public, {
        "status": STATUS, "task_id": TASK_ID, "parameter_seed": seed,
        "parameter": {"output_order": output_order},
        "program": program, "program_sha256": digest(program.encode()),
        "query_answers": outputs[2:], "rival_checks": rivals,
        "executions": executions,
    }


def _write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_evidence(out, *, seeds):
    out = Path(out)
    for folder in ("public", "private", "rules"):
        (out / folder).mkdir(parents=True, exist_ok=True)
    programs = {order: program_for(order) for order in ORDERS}
    for order, program in programs.items():
        (out / "rules" / (order + ".rkt")).write_text(program)
    with RacketBridge() as bridge:
        runtime = bridge.runtime_identity
        episode_rows = []
        for index, seed in enumerate(seeds):
            public, private = generate_episode(seed, bridge)
            name = f"episode-{index:03d}.json"
            _write_json(out / "public" / name, public)
            _write_json(out / "private" / name, private)
            episode_rows.append({"file": name, "seed": seed, "parameter": private["parameter"]})
        witness = shared_input()
        witness_outputs = {order: execute(bridge, program, witness) for order, program in programs.items()}
        if witness_outputs[ORDERS[0]] == witness_outputs[ORDERS[1]]:
            raise ValueError("shared input failed to distinguish output order")
        _write_json(out / "private/shared-witness.json", {
            "input": witness, "outputs": witness_outputs,
            "expressions": {order: application(program, witness) for order, program in programs.items()},
        })
        canonical = canonical_record()
        canonical_checks = []
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
            actual = execute(bridge, programs[DEFAULT_ORDER], pair["input"])
            if actual != pair["output"]:
                raise ValueError("default program failed canonical example")
            canonical_checks.append({"input": pair["input"], "expected": pair["output"], "actual": actual})
        _write_json(out / "private/canonical-checks.json", canonical_checks)
    source_identities = [
        f"generators/{TASK_ID}/workspace/parametric/prototype.py",
        f"generators/{TASK_ID}/tests/test_parametric.py",
        "shared/runtime/puzzle_generators/rule_wrap.py",
        "shared/runtime/arc_repl/racket_bridge.py",
        "shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt",
        "shared/runtime/reviewer_support.py",
        "shared/tools/comment_solutions.py",
        "src/arcpuzzles/runtime.py",
    ]
    source_paths = {identity: resolve_source(identity) for identity in source_identities}
    manifest = {
        "status": STATUS, "task_id": TASK_ID,
        "parameter": {"name": "output_order", "allowed": list(ORDERS), "default": DEFAULT_ORDER},
        "episodes": episode_rows, "program_sha256": {order: digest(program.encode()) for order, program in programs.items()},
        "canonical_record_sha256": digest(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()),
        "source_sha256": {identity: digest(path.read_bytes()) for identity, path in source_paths.items()},
        "source_paths": {identity: str(path.relative_to(ROOT)) for identity, path in source_paths.items()},
        "canonical_path": str(canonical_path(ROOT).relative_to(ROOT)),
        "runtime_identity": runtime, "payload_argv": sys.argv,
        "canonical_examples_passed": len(canonical_checks),
        "limits": [
            "Only the two declared order settings and explicitly retained seeds are exercised.",
            "Input support is three connected hole-free mask shapes, translated and recolored; no general distribution claim.",
            "No parameter-dependent input constraint: both settings use the same lawful input support.",
            "Demonstrations distinguish the declared two-setting family; arbitrary alternative rules remain possible.",
            "This workspace prototype is excluded from production generation and approval; no training admission implied.",
        ],
    }
    _write_json(out / "private/manifest.json", manifest)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 0])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    manifest = write_evidence(args.out, seeds=args.seeds)
    print(json.dumps({"status": STATUS, "episodes": manifest["episodes"],
                      "program_sha256": manifest["program_sha256"], "out": str(args.out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
