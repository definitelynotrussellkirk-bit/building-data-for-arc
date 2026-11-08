"""Proposed task-local square/diamond ring episodes; Racket produces every label.

This does not register a generator or change the canonical production rule.
Python constructs inputs and named rival predictions only. See README.md.
"""
from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
import shlex
import sys

HERE = Path(__file__).resolve()
TASK_ID = "2e663d812b7a"
ALLOWED_METRICS = ("chebyshev", "manhattan")
DEFAULT_METRIC = "chebyshev"
DEFAULT_SEEDS = (2026102300, 2026102301)
SOURCE_DISTANCE = "(max (abs (- r seed-r)) (abs (- c seed-c)))"
DIAMOND_DISTANCE = "(+ (abs (- r seed-r)) (abs (- c seed-c)))"
SEMANTIC_RIVALS = (
    "top_is_row_zero", "bottom_only", "last_only", "gray_active_zeros",
    "drop_zero_keys", "deduplicate_key", "leave_header_unchanged",
    "use_marked_key", "complete_rings_only",
)

# Resolve only dependencies in this file's own repository or copied runtime.
for ancestor in HERE.parents:
    support = next((p for p in (ancestor, ancestor / "shared/runtime")
                    if (p / "reviewer_support.py").is_file()), None)
    if support is not None:
        sys.path.insert(0, str(support))
        break
else:
    raise FileNotFoundError("No reviewer_support.py in this prototype's source tree")

from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid
from arc_repl.racket_bridge import RacketBridge

ROOT = find_root(HERE)


def sha256(value):
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def grid_hash(grid):
    return sha256(json.dumps(grid, separators=(",", ":")))


@lru_cache(maxsize=1)
def canonical_program():
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError("Expected one unambiguous canonical Racket authority")
    program = programs.pop()
    if program.count(SOURCE_DISTANCE) != 1:
        raise ValueError("Canonical body-distance expression changed; review this prototype")
    return program


def materialize_program(ring_metric=DEFAULT_METRIC):
    if ring_metric not in ALLOWED_METRICS:
        raise ValueError(f"ring_metric must be one of {ALLOWED_METRICS}")
    program = canonical_program()
    if ring_metric == "manhattan":
        return program.replace(SOURCE_DISTANCE, DIAMOND_DISTANCE, 1)
    return program


def checked_seed(seed):
    if type(seed) is not int or seed < 0:
        raise ValueError("episode seed must be a nonnegative integer")
    return seed


def parse_input(grid):
    grid = normalize_grid(grid)
    h, w = len(grid), len(grid[0])
    if not (9 <= h <= 30 and 9 <= w <= 30):
        raise ValueError("prototype dimensions must be 9..30")
    if grid[1] != [5] * w:
        raise ValueError("row 1 must be the gray separator")
    if grid[0][0] in (0, 5) or 5 in grid[0]:
        raise ValueError("the key needs a nonzero first color and excludes gray")
    end = max(c for c, color in enumerate(grid[0]) if color != 0) + 1
    key = grid[0][:end]
    if not 1 <= len(key) <= min(20, w) or len(set(key) - {0}) > 6:
        raise ValueError("prototype key length is 1..20 with at most six nonzero colors")
    seeds = [(r, c) for r in range(2, h) for c in range(w) if grid[r][c] != 0]
    if len(seeds) != 1:
        raise ValueError("exactly one lower seed is required")
    sr, sc = seeds[0]
    if grid[sr][sc] != key[0]:
        raise ValueError("seed color must match the first key entry")
    return {"height": h, "width": w, "key": key, "seed_r": sr, "seed_c": sc,
            "complete_radius": min(sr - 2, h - 1 - sr, sc, w - 1 - sc)}


def make_input(height, width, key, seed):
    if any(type(v) is not int or not 9 <= v <= 30 for v in (height, width)):
        raise ValueError("prototype dimensions must be integers in 9..30")
    if (not isinstance(key, (list, tuple)) or not key or len(key) > min(20, width)
            or any(type(v) is not int or not 0 <= v <= 9 or v == 5 for v in key)
            or key[0] == 0 or key[-1] == 0):
        raise ValueError("key must have nonzero endpoints, legal colors, and fit the width")
    if (not isinstance(seed, (list, tuple)) or len(seed) != 2
            or any(type(v) is not int for v in seed)
            or not (2 <= seed[0] < height and 0 <= seed[1] < width)):
        raise ValueError("seed must be a lower-canvas coordinate")
    grid = [[0] * width for _ in range(height)]
    grid[0][:len(key)] = key
    grid[1] = [5] * width
    grid[seed[0]][seed[1]] = key[0]
    parse_input(grid)
    return grid


def episode_inputs(seed):
    """Four fresh input draws; geometry never depends on the hidden metric."""
    rng = random.Random(checked_seed(seed) ^ 0x9356391F)

    def key(length):
        a, b, c, d = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 4)
        result = [a, b, b, 0, c, d]
        result += [rng.choice([0, a, b, c, d]) for _ in range(length - 6)]
        if result[-1] == 0:
            result[-1] = rng.choice([a, b, c, d])
        return result

    return [
        make_input(16, 16, key(rng.randint(6, 8)), (3, rng.randint(6, 9))),
        make_input(19, 21, key(rng.randint(6, 9)), (10, 10)),
        make_input(23, 27, key(rng.randint(10, 13)), (rng.randint(18, 20), 24)),
        make_input(30, 30, key(rng.randint(16, 20)), (13, 14)),
    ]


class ReferenceRunner:
    """Execute the retained exact program via the included protected Racket bridge."""

    def __init__(self):
        self.bridge = RacketBridge(timeout=20.0)
        self.records = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.bridge.close()

    def run(self, program, grid, label="example"):
        parse_input(grid)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        # rule! is the ARC surface registration form. The local lexical binding
        # returns its lambda so the complete retained program is evaluated intact.
        expression = f"(let ((rule! (lambda (f) f))) ({program} {literal}))"
        record = {"index": len(self.records), "label": label,
                  "program_sha256": sha256(program), "input_sha256": grid_hash(grid)}
        try:
            output = normalize_grid(self.bridge.eval_text(expression))
            if (len(output), len(output[0])) != (len(grid), len(grid[0])):
                raise ValueError("Reference output dimensions differ from the input")
        except Exception as exc:
            record.update(status="fail", error=str(exc))
            self.records.append(record)
            raise
        record.update(status="pass", output_sha256=grid_hash(output))
        self.records.append(record)
        return output


def rival_model(grid, ring_metric, mode="canonical"):
    """Analysis-only predictions; never used to supply an episode output label."""
    if ring_metric not in ALLOWED_METRICS:
        raise ValueError("unknown ring_metric")
    if mode not in ("canonical", *SEMANTIC_RIVALS):
        raise ValueError("unknown rival mode")
    p = parse_input(grid)
    h, w, key, sr, sc = (p[k] for k in ("height", "width", "key", "seed_r", "seed_c"))
    radius = p["complete_radius"]
    if mode == "top_is_row_zero":
        radius = min(sr, h - 1 - sr, sc, w - 1 - sc)
    elif mode == "bottom_only":
        radius = h - 1 - sr
    out = [list(row) for row in grid]
    if mode != "leave_header_unchanged":
        for c in range(radius + 1, len(key)):
            if mode == "last_only" and c != len(key) - 1:
                continue
            if key[c] != 0 or mode == "gray_active_zeros":
                out[0][c] = 5
    body_key = key
    if mode == "drop_zero_keys":
        body_key = [v for v in key if v != 0]
    elif mode == "deduplicate_key":
        body_key = list(dict.fromkeys(key))
    elif mode == "use_marked_key":
        body_key = out[0][:len(key)]
    for r in range(2, h):
        for c in range(w):
            dr, dc = abs(r - sr), abs(c - sc)
            distance = max(dr, dc) if ring_metric == "chebyshev" else dr + dc
            if distance < len(body_key) and (mode != "complete_rings_only" or distance <= radius):
                out[r][c] = body_key[distance]
    return out


def identifiability(inputs, outputs_by_metric, ring_metric):
    expected = outputs_by_metric[ring_metric]
    predictions = {f"setting:{m}": outputs_by_metric[m]
                   for m in ALLOWED_METRICS if m != ring_metric}
    predictions.update({name: [rival_model(g, ring_metric, name) for g in inputs]
                        for name in SEMANTIC_RIVALS})
    records = {}
    survivors = []
    for name, outputs in predictions.items():
        refuted = [i for i in range(len(inputs) - 1) if outputs[i] != expected[i]]
        query_differs = outputs[-1] != expected[-1]
        records[name] = {"refuting_demo_indices": refuted,
                         "fits_all_demos": not refuted, "query_differs": query_differs}
        if not refuted and query_differs:
            survivors.append(name)
    return {"status": "ambiguous" if survivors else "pass",
            "rivals": records, "query_changing_survivors": survivors,
            "refuted_rival_count": sum(bool(r["refuting_demo_indices"]) for r in records.values()),
            "scope": "One alternative metric executed in Racket plus nine named Python semantic rivals; finite evidence only."}


def build_episode(seed, runner, *, ring_metric=None):
    checked_seed(seed)
    # Exactly one choice per episode. Never use the example index to choose it.
    chosen = ALLOWED_METRICS[seed % len(ALLOWED_METRICS)] if ring_metric is None else ring_metric
    materialize_program(chosen)  # Reject unsupported explicit settings before generating inputs.
    inputs = episode_inputs(seed)
    outputs = {metric: [runner.run(materialize_program(metric), grid,
                                  f"episode:{seed}:{metric}:{index}")
                        for index, grid in enumerate(inputs)]
               for metric in ALLOWED_METRICS}
    for metric in ALLOWED_METRICS:
        for grid, actual in zip(inputs, outputs[metric]):
            if rival_model(grid, metric) != actual:
                raise AssertionError("Analysis model disagrees with the Racket reference")
    identifiable = identifiability(inputs, outputs, chosen)
    if identifiable["status"] != "pass":
        raise AssertionError(f"Unidentifiable episode: {identifiable['query_changing_survivors']}")
    return {"schema": "2e663d812b7a-parametric-episode-v1", "status": "prototype",
            "seed": seed, "ring_metric": chosen,
            "setting_policy": "explicit" if ring_metric is not None else "seed modulo 2, chosen once",
            "program_sha256": sha256(materialize_program(chosen)),
            "pairs": [{"input": grid, "output": output} for grid, output in zip(inputs, outputs[chosen])],
            "outputs_by_metric": outputs, "identifiability": identifiable,
            "input_observations": [parse_input(grid) for grid in inputs],
            "input_draws": 4, "rejected_draws": 0}


def public_challenge(episode):
    return {"train": episode["pairs"][:-1],
            "test": [{"input": episode["pairs"][-1]["input"]}]}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def source_hashes():
    paths = [HERE, HERE.with_name("README.md"),
             HERE.parents[2] / "tests/test_parametric_prototype.py", canonical_path(ROOT)]
    # Record the current selected generator as provenance, not a dependency.
    generator = ROOT / "generators" / TASK_ID / "generator.py"
    if generator.is_file():
        paths.append(generator)
    return {str(p.relative_to(ROOT)): sha256(p.read_bytes()) for p in paths}


def build_bundle(out, seeds, ring_metric=None):
    out = Path(out).resolve()
    if out == ROOT or ROOT.is_relative_to(out):
        raise ValueError("evidence directory must not contain the source repository")
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"evidence output directory is not empty: {out}; choose a fresh or empty directory")
    (out / "private/rules").mkdir(parents=True, exist_ok=True)
    for metric in ALLOWED_METRICS:
        (out / f"private/rules/{metric}.rkt").write_text(materialize_program(metric), encoding="utf-8")
    equivalence = []
    with ReferenceRunner() as runner:
        episodes = []
        for index, seed in enumerate(seeds):
            episode = build_episode(seed, runner, ring_metric=ring_metric)
            episodes.append(episode)
            public_path = f"public/episode-{index:04d}.json"
            private_path = f"private/episode-{index:04d}.json"
            write_json(out / public_path, public_challenge(episode))
            write_json(out / private_path, episode)
            for pi, pair in enumerate(episode["pairs"]):
                actual = runner.run(canonical_program(), pair["input"], f"canonical:episode:{seed}:{pi}")
                match = actual == episode["outputs_by_metric"][DEFAULT_METRIC][pi]
                equivalence.append({"kind": "prototype_input", "seed": seed, "pair_index": pi,
                                    "input_sha256": grid_hash(pair["input"]),
                                    "output_sha256": grid_hash(actual), "matches": match})
                if not match:
                    raise AssertionError("Default variant differs from canonical Racket")
        for pair in canonical_pairs(TASK_ID, root=ROOT):
            actual = runner.run(canonical_program(), pair["input"], "canonical:stored")
            default = runner.run(materialize_program(DEFAULT_METRIC), pair["input"], "default:stored")
            match = actual == default == pair["output"]
            equivalence.append({"kind": "stored_canonical", "variant": pair["variant"],
                                "split": pair["split"], "pair_index": pair["pair_index"],
                                "input_sha256": grid_hash(pair["input"]),
                                "output_sha256": grid_hash(actual), "matches": match})
            if not match:
                raise AssertionError("Default variant or stored label differs from canonical Racket")

        witness_input = make_input(16, 16, [2, 3, 3, 0, 4, 6], (3, 8))
        witness_outputs = {m: runner.run(materialize_program(m), witness_input, f"witness:{m}")
                           for m in ALLOWED_METRICS}
        differences = [[r, c, witness_outputs["chebyshev"][r][c], witness_outputs["manhattan"][r][c]]
                       for r in range(16) for c in range(16)
                       if witness_outputs["chebyshev"][r][c] != witness_outputs["manhattan"][r][c]]
        if not differences:
            raise AssertionError("The same-input witness does not distinguish settings")
        write_json(out / "private/witness.json", {"input": witness_input, "outputs": witness_outputs,
                   "different_cells": len(differences), "first_differences": differences[:12],
                   "header_equal": witness_outputs["chebyshev"][0] == witness_outputs["manhattan"][0]})

        boundaries = []
        for h, w, position in ((9, 9, (2, 0)), (30, 30, (29, 29)), (30, 9, (15, 4))):
            grid = make_input(h, w, [2, 3, 0, 4, 6], position)
            outputs = {m: runner.run(materialize_program(m), grid, f"boundary:{h}x{w}:{m}")
                       for m in ALLOWED_METRICS}
            actual = runner.run(canonical_program(), grid, f"canonical:boundary:{h}x{w}")
            if outputs[DEFAULT_METRIC] != actual:
                raise AssertionError("Boundary default differs from canonical Racket")
            boundaries.append({"input": grid, "outputs": outputs, "default_matches_canonical": True})
        write_json(out / "private/boundary-cases.json", boundaries)
        write_json(out / "private/authority-equivalence.json", {
            "status": "pass", "default_program_byte_identical": materialize_program() == canonical_program(),
            "comparisons": equivalence, "boundary_comparisons": len(boundaries),
            "unique_stored_canonical_inputs": len({r["input_sha256"] for r in equivalence if r["kind"] == "stored_canonical"})})
        sizes = Counter(f"{len(p['input'])}x{len(p['input'][0])}" for e in episodes for p in e["pairs"])
        report = {
            "schema": "2e663d812b7a-parametric-evidence-v1", "status": "pass", "admission": "prototype only",
            "task_id": TASK_ID, "parent": "training:9356391f", "seeds": list(seeds),
            "parameter": {"name": "ring_metric", "allowed_values": list(ALLOWED_METRICS), "default": DEFAULT_METRIC,
                          "selected_once_per_episode": True, "input_constraints_depend_on_setting": False},
            "source_sha256": source_hashes(),
            "programs": {m: {"path": f"private/rules/{m}.rkt", "sha256": sha256(materialize_program(m))}
                         for m in ALLOWED_METRICS},
            "episodes": [{"seed": e["seed"], "ring_metric": e["ring_metric"],
                          "public_path": f"public/episode-{i:04d}.json", "private_path": f"private/episode-{i:04d}.json",
                          "identifiability": e["identifiability"]} for i, e in enumerate(episodes)],
            "coverage": {"episode_count": len(episodes), "demonstration_count": 3 * len(episodes),
                         "query_count": len(episodes), "sizes": dict(sorted(sizes.items())),
                         "settings_observed": sorted({e["ring_metric"] for e in episodes}),
                         "same_input_witness_different_cells": len(differences),
                         "reference_execution_count": len(runner.records),
                         "canonical_pair_comparisons": sum(r["kind"] == "stored_canonical" for r in equivalence),
                         "prototype_default_comparisons": sum(r["kind"] == "prototype_input" for r in equivalence),
                         "boundary_default_comparisons": len(boundaries)},
            "runtime": runner.bridge.runtime_identity, "execution_records": runner.records,
            "command": {"cwd": str(Path.cwd()), "payload_argv": [sys.executable, *sys.argv],
                        "payload_command": shlex.join([sys.executable, *sys.argv]), "exit_status": 0},
            "limitations": [
                "Two allowed metrics; finite supplied seeds and nine named semantic rivals do not prove universal identifiability.",
                "Prototype input bounds are 9..30 per side and key length 1..20; long keys above 10 are outside the canonical generator's advertised key domain.",
                "The parameter is inferred from demonstrations and is not encoded in query pixels.",
                "No production API, canonical rule, approval hash, training admission, or model performance claim is changed.",
            ],
        }
    write_json(out / "report.json", report)
    members = {}
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            members[str(path.relative_to(out))] = {"sha256": sha256(path.read_bytes()), "bytes": path.stat().st_size}
    write_json(out / "manifest.json", {"schema": "2e663d812b7a-parametric-manifest-v1", "files": members})
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    parser.add_argument("--ring-metric", choices=ALLOWED_METRICS, default=None,
                        help="Choose once explicitly; omitted uses each episode seed modulo 2")
    args = parser.parse_args(argv)
    report = build_bundle(args.out, args.seeds, args.ring_metric)
    print(json.dumps({"status": report["status"], "admission": report["admission"],
                      "coverage": report["coverage"], "evidence": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
