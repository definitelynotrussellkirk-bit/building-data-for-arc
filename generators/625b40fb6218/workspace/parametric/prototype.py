#!/usr/bin/env python3
"""Proposed conflict-policy family for ARC d47aa2ff; never selected automatically."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

from reviewer_support import (find_root, load_selected_generator,
                              public_challenge_bytes, public_challenge_id)

TASK_ID = "625b40fb6218"
POLICIES = ("left", "right", "erase")
COLORS = (3, 4, 6, 7, 8, 9)
ROOT = find_root(__file__)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
CANONICAL_PROGRAM = """(rule! (zip-halves g
                   (lambda (lv rv)
                     (cond
                       ((and (!= lv 0) (zero? rv)) 2)
                       ((and (zero? lv) (!= rv 0)) 1)
                       (else lv)))
                   5))"""


def _integer(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _policy(value):
    if type(value) is not str or value not in POLICIES:
        raise ValueError("conflict_policy must be left, right, or erase")
    return value


def grid_key(grid):
    return json.dumps(grid, separators=(",", ":"))


def _valid_input(grid):
    errors = GEN.self_check(grid)
    if errors:
        raise ValueError("invalid input: " + "; ".join(errors))


def materialize_program(policy="left"):
    """Return the exact runnable rule! form; left is the registered authority."""
    _policy(policy)
    if policy == "left":
        return CANONICAL_PROGRAM
    expression = "rv" if policy == "right" else "0"
    return CANONICAL_PROGRAM.replace(
        "                       (else lv)",
        "                       ((and (!= lv 0) (!= rv 0) (!= lv rv)) "
        + expression + ")\n                       (else lv)")


def mirror(grid, policy="left"):
    """Diagnostic Python prediction; saved labels always come from Racket."""
    _policy(policy)
    _valid_input(grid)
    out = GEN.rule_mirror(grid)
    half = len(grid[0]) // 2
    for row, values in enumerate(grid):
        for col in range(half):
            left, right = values[col], values[half + 1 + col]
            if left and right and left != right:
                out[row][col] = left if policy == "left" else right if policy == "right" else 0
    return out


class RacketLabeler:
    """Protected persistent Racket; explicitly closed by its owner."""
    def __init__(self):
        from arc_repl.racket_bridge import RacketBridge
        self.bridge = RacketBridge(timeout=10)
        self.identity = self.bridge.runtime_identity
        if not self.identity.get("protected"):
            self.bridge.close()
            raise RuntimeError("protected Racket runtime required")
        self.calls = 0

    def apply(self, grid, policy="left"):
        _valid_input(grid)
        program = materialize_program(policy)
        body = program[len("(rule! "):-1]
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        result = self.bridge.eval_text("(let ([g " + literal + "]) " + body + ")")
        self.calls += 1
        if result != mirror(grid, policy):
            raise ValueError("Racket/Python disagreement")
        # Reuse the public exact-integer grid validator on the actual Racket result.
        public_challenge_bytes({"train": [{"input": grid, "output": result}],
                                "test": [{"input": grid}]})
        return result

    def close(self):
        self.bridge.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def _teaching_input(seed, index, palette):
    grid = GEN.generate(seed, index, palette_size=3, n_left_only=1,
                        n_right_only=1, n_shared_equal=3, n_shared_conflict=3)
    existing = sorted({v for row in grid for v in row} - {0, 5})
    recolor = dict(zip(existing, palette))
    grid = [[recolor.get(v, v) for v in row] for row in grid]
    half = len(grid[0]) // 2
    conflicts = [(r, c) for r, row in enumerate(grid) for c in range(half)
                 if row[c] and row[half + 1 + c] and row[c] != row[half + 1 + c]]
    for i, (row, col) in enumerate(conflicts):
        grid[row][col] = palette[i % 3]
        grid[row][half + 1 + col] = palette[(i + 1) % 3]
    _valid_input(grid)
    return grid


def sample_inputs(input_seed, *, n_demos=2, n_queries=4, max_attempts=256):
    """Two directed color cycles teach all six colors; extra inputs are distinct."""
    _integer("input_seed", input_seed, 0, 2**64 - 1)
    _integer("n_demos", n_demos, 2, 8)
    _integer("n_queries", n_queries, 1, 16)
    _integer("max_attempts", max_attempts, n_demos + n_queries, 4096)
    palette = list(COLORS)
    random.Random(input_seed).shuffle(palette)
    grids = [_teaching_input(input_seed, 0, palette[:3]),
             _teaching_input(input_seed, 1, palette[3:])]
    seen = {grid_key(g) for g in grids}
    for index in range(2, max_attempts):
        if len(grids) == n_demos + n_queries:
            break
        candidate = GEN.generate(input_seed, index)
        key = grid_key(candidate)
        if key not in seen:
            grids.append(candidate)
            seen.add(key)
    if len(grids) != n_demos + n_queries:
        raise ValueError(f"distinct-input attempt budget exhausted: {max_attempts}")
    return grids[:n_demos], grids[n_demos:]


def _candidates(grid, selected):
    predictions = {"policy:" + p: mirror(grid, p) for p in POLICIES}
    base = mirror(grid, selected)
    half = len(grid[0]) // 2
    for color in COLORS:
        out = deepcopy(base)
        for r, row in enumerate(grid):
            for c in range(half):
                left, right = row[c], row[half + 1 + c]
                if left and right and left != right and color in (left, right):
                    out[r][c] = color
        predictions[f"favorite:{color}"] = out
    for name, choose in (("numeric:min", min), ("numeric:max", max)):
        out = deepcopy(base)
        for r, row in enumerate(grid):
            for c in range(half):
                left, right = row[c], row[half + 1 + c]
                if left and right and left != right:
                    out[r][c] = choose(left, right)
        predictions[name] = out
    swapped = deepcopy(base)
    for r, row in enumerate(grid):
        for c in range(half):
            left, right = row[c], row[half + 1 + c]
            if left and not right:
                swapped[r][c] = 1
            elif right and not left:
                swapped[r][c] = 2
    predictions["swap:exclusive"] = swapped
    predictions["copy:left"] = [row[:half] for row in grid]
    predictions["copy:right"] = [row[half + 1:] for row in grid]
    return predictions


def lesson_certificate(demos, query_inputs, policy="left"):
    """Fit rivals using demos only; query answers are neither accepted nor read."""
    _policy(policy)
    public_challenge_bytes({"train": demos, "test": [{"input": g} for g in query_inputs]})
    all_predictions = []
    for demo in demos:
        _valid_input(demo["input"])
        if mirror(demo["input"], policy) != demo["output"]:
            raise ValueError("demonstration output disagrees with selected policy")
        all_predictions.append(_candidates(demo["input"], policy))
    names = sorted(all_predictions[0])
    refutations = {name: [i for i, predictions in enumerate(all_predictions)
                         if predictions[name] != demos[i]["output"]] for name in names}
    survivors = [name for name in names if not refutations[name]]
    queries = []
    for index, grid in enumerate(query_inputs):
        selected = mirror(grid, policy)
        predictions = _candidates(grid, policy)
        ambiguous = [name for name in survivors if predictions[name] != selected]
        queries.append({"index": index, "ambiguous_rivals": ambiguous})
    return {"schema": "625b40fb6218-lesson-certificate-v1",
            "comparison_basis": "demonstrations plus query inputs only",
            "rival_count": len(names), "survivors": survivors,
            "refuted_by_demo_indices": refutations, "per_query": queries,
            "identifiable": all(not q["ambiguous_rivals"] for q in queries),
            "limit": "Finite declared policies and shortcuts; not unique induction over all programs."}


def generate_episode(seed, *, policy="left", input_seed=None,
                     n_demos=2, n_queries=4, labeler=None):
    _integer("seed", seed, 0, 2**64 - 1)
    _policy(policy)
    input_seed = seed if input_seed is None else input_seed
    demos, queries = sample_inputs(input_seed, n_demos=n_demos, n_queries=n_queries)
    if labeler is None:
        with RacketLabeler() as oracle:
            return generate_episode(seed, policy=policy, input_seed=input_seed,
                                    n_demos=n_demos, n_queries=n_queries, labeler=oracle)
    challenge = {
        "train": [{"input": g, "output": labeler.apply(g, policy)} for g in demos],
        "test": [{"input": g, "output": labeler.apply(g, policy)} for g in queries]}
    certificate = lesson_certificate(challenge["train"], queries, policy)
    if not certificate["identifiable"]:
        raise ValueError("constructed demonstrations do not identify every query")
    program = materialize_program(policy)
    return {"schema": "625b40fb6218-parametric-episode-v1", "status": "proposed",
            "training_admitted": False, "task_id": TASK_ID,
            "parent": {"source_split": "training", "source_task_id": "d47aa2ff"},
            "params": {"conflict_policy": policy}, "seed": seed, "input_seed": input_seed,
            "counts": {"demos": n_demos, "queries": n_queries},
            "program": program, "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
            "generator_sha256": GENERATOR_SHA256,
            "prototype_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "runtime": labeler.identity, "challenge": challenge, "certificate": certificate}


def verify_episode(episode, *, labeler=None):
    """Re-execute labels and recompute the certificate instead of trusting it."""
    if type(episode) is not dict or episode.get("schema") != "625b40fb6218-parametric-episode-v1":
        raise ValueError("wrong episode schema")
    if episode.get("parent") != {"source_split": "training", "source_task_id": "d47aa2ff"}:
        raise ValueError("wrong original-task lineage")
    if episode.get("status") != "proposed" or episode.get("training_admitted") is not False:
        raise ValueError("prototype status or training boundary changed")
    if episode.get("task_id") != TASK_ID or set(episode.get("params", {})) != {"conflict_policy"}:
        raise ValueError("wrong task or parameter fields")
    policy = _policy(episode["params"]["conflict_policy"])
    _integer("seed", episode["seed"], 0, 2**64 - 1)
    _integer("input_seed", episode["input_seed"], 0, 2**64 - 1)
    counts = episode["counts"]
    _integer("demos", counts["demos"], 2, 8)
    _integer("queries", counts["queries"], 1, 16)
    challenge = episode["challenge"]
    public_challenge_bytes(challenge)
    if len(challenge["train"]) != counts["demos"] or len(challenge["test"]) != counts["queries"]:
        raise ValueError("pair counts differ from the request")
    pairs = challenge["train"] + challenge["test"]
    keys = [grid_key(pair["input"]) for pair in pairs]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate input within episode")
    for pair in pairs:
        _valid_input(pair["input"])
        # Query outputs are private, but must satisfy the same strict numeric contract.
        public_challenge_bytes({"train": [pair], "test": [{"input": pair["input"]}]})
    program = materialize_program(policy)
    if (episode["program"] != program or
            episode["program_sha256"] != hashlib.sha256(program.encode()).hexdigest()):
        raise ValueError("program does not match the fixed policy")
    if episode.get("generator_sha256") != GENERATOR_SHA256 or episode.get("prototype_sha256") != hashlib.sha256(Path(__file__).read_bytes()).hexdigest():
        raise ValueError("episode source binding is stale")
    certificate = lesson_certificate(challenge["train"], [p["input"] for p in challenge["test"]], policy)
    if not certificate["identifiable"] or episode["certificate"] != certificate:
        raise ValueError("invalid or unidentifiable lesson certificate")
    if labeler is None:
        with RacketLabeler() as oracle:
            return verify_episode(episode, labeler=oracle)
    recorded_runtime = episode.get("runtime")
    if type(recorded_runtime) is not dict or set(recorded_runtime) != set(labeler.identity):
        raise ValueError("runtime identity fields are incomplete or unknown")
    # Paths change on relocation; executable/prelude/bridge/policy hashes and
    # every security claim must still match the live protected runtime.
    path_fields = {"binary_path", "prelude_path", "bridge_path"}
    if any(type(recorded_runtime[key]) is not str for key in path_fields):
        raise ValueError("runtime paths must be strings")
    recorded_binding = {k: v for k, v in recorded_runtime.items() if k not in path_fields}
    live_binding = {k: v for k, v in labeler.identity.items() if k not in path_fields}
    if json.dumps(recorded_binding, sort_keys=True) != json.dumps(live_binding, sort_keys=True):
        raise ValueError("stored runtime identity differs from the live protected runtime")
    for pair in pairs:
        if labeler.apply(pair["input"], policy) != pair["output"]:
            raise ValueError("stored output disagrees with executed Racket")
    return True


def write_batch(episodes, out, *, labeler=None):
    """Validate first, then write sorted opaque public files and private metadata."""
    if not episodes:
        raise ValueError("episode batch must be nonempty")
    if labeler is None:
        with RacketLabeler() as oracle:
            return write_batch(episodes, out, labeler=oracle)
    prepared = []
    seen = set()
    for episode in episodes:
        verify_episode(episode, labeler=labeler)
        raw = public_challenge_bytes(episode["challenge"])
        public_id = public_challenge_id(episode["challenge"])
        if public_id in seen:
            raise ValueError("duplicate visible payload in batch")
        seen.add(public_id)
        prepared.append((public_id, raw, episode))
    prepared.sort(key=lambda item: item[0])
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    (out / "private").mkdir()
    rows = []
    private_rows = []
    for public_id, raw, episode in prepared:
        (out / "public" / (public_id + ".json")).write_bytes(raw)
        private_rows.append({"public_id": public_id, "episode": episode})
        rows.append({"public_id": public_id, "visible_bytes": len(raw),
                     "demonstrations": episode["counts"]["demos"],
                     "queries": episode["counts"]["queries"],
                     "params": episode["params"],
                     "program_sha256": episode["program_sha256"]})
    (out / "private/episodes.jsonl").write_text(
        "".join(json.dumps(x, sort_keys=True, separators=(",", ":")) + "\n" for x in private_rows))
    report = {"schema": "625b40fb6218-parametric-batch-v1", "status": "proposed",
              "training_admitted": False, "episodes": rows,
              "racket_calls_in_session": labeler.calls,
              "runtime": labeler.identity, "generator_sha256": GENERATOR_SHA256,
              "prototype_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "limits": ["Two constructive demos; demo counts 2..8, query counts 1..16.",
                         "Canonical sampler is unchanged; this is an opt-in prototype.",
                         "Finite 14-candidate lesson check is not universal identifiability.",
                         "Do not publish the private directory or this private report."]}
    (out / "private/report.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--input-seed", type=int)
    parser.add_argument("--policy", choices=("all", *POLICIES), default="all")
    parser.add_argument("--demos", type=int, default=2)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    policies = POLICIES if args.policy == "all" else (args.policy,)
    with RacketLabeler() as oracle:
        episodes = [generate_episode(args.seed, policy=p, input_seed=args.input_seed,
                                     n_demos=args.demos, n_queries=args.queries, labeler=oracle)
                    for p in policies]
        report = write_batch(episodes, args.out, labeler=oracle)
    print(json.dumps({"status": "proposed", "episodes": len(report["episodes"]),
                      "queries": sum(x["queries"] for x in report["episodes"]),
                      "racket_calls": report["racket_calls_in_session"],
                      "out": str(args.out)}, sort_keys=True))


if __name__ == "__main__":
    main()
