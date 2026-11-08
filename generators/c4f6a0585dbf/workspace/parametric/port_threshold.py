"""Proposed task-local port-threshold variant; not a production generator API."""
from __future__ import annotations

import argparse
import copy
from functools import lru_cache
import hashlib
from itertools import combinations
import json
from pathlib import Path
import random
import sys

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "shared/runtime"))
from reviewer_support import (canonical_pairs, load_selected_generator,
                              public_challenge_bytes, public_challenge_id)
from arc_repl.racket_bridge import RacketBridge

TASK_ID = "c4f6a0585dbf"
ALLOWED_THRESHOLDS = (2, 3)
CANONICAL_PROGRAM_SHA256 = "34aea00434c1a498289ad35c068b9cca102078c262cc65b41c7b71871a563975"
THRESHOLD_EXPRESSION = "(>= (length placed4) 2)"


class SamplingExhausted(RuntimeError):
    """A bounded draw could not provide all requested distinct inputs."""


def _integer(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _threshold(value):
    if type(value) is not int or value not in ALLOWED_THRESHOLDS:
        raise ValueError("min_visible_ports must be the exact integer 2 or 3")
    return value


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(v) is not int or not 0 <= v <= 9 for v in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def grid_sha256(grid):
    return hashlib.sha256(json.dumps(_grid(grid), separators=(",", ":")).encode()).hexdigest()


@lru_cache(maxsize=1)
def canonical_program():
    programs = set()
    with (REPO_ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError("expected one exact canonical program across task rows")
    program = programs.pop()
    if hashlib.sha256(program.encode()).hexdigest() != CANONICAL_PROGRAM_SHA256:
        raise ValueError("canonical authority changed; review this prototype before use")
    if program.count(THRESHOLD_EXPRESSION) != 1:
        raise ValueError("canonical threshold expression is not unambiguous")
    return program


def materialize_program(min_visible_ports=2):
    threshold = _threshold(min_visible_ports)
    canonical = canonical_program()
    return canonical if threshold == 2 else canonical.replace(
        THRESHOLD_EXPRESSION, "(>= (length placed4) 3)")


@lru_cache(maxsize=1)
def _selected():
    return load_selected_generator(TASK_ID, root=REPO_ROOT)


def selected_generator():
    return _selected()[0]


def source_hashes():
    relative_paths = [
        Path(__file__).resolve().relative_to(REPO_ROOT),
        Path("shared/runtime/reviewer_support.py"),
        Path("shared/runtime/arc_repl/racket_bridge.py"),
        Path("shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt"),
    ]
    result = {str(path): hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest()
              for path in relative_paths}
    _, path, digest = _selected()
    result[str(path.relative_to(REPO_ROOT))] = digest
    return result


class RacketOracle:
    """Exact emitted programs, evaluated by the included protected bridge."""
    def __init__(self):
        self.programs = {value: materialize_program(value) for value in ALLOWED_THRESHOLDS}
        self.bridge = RacketBridge(timeout=20.0)
        self._cache = {}
        self.evaluations = 0

    def evaluate(self, grid, min_visible_ports):
        threshold = _threshold(min_visible_ports)
        identity = (threshold, grid_sha256(grid))
        if identity not in self._cache:
            program = self.programs[threshold]
            if not program.startswith("(rule! ") or not program.endswith(")"):
                raise ValueError("expected canonical rule! wrapper")
            expression = program[len("(rule! "):-1]
            literal = "(" + " ".join("(" + " ".join(map(str, row)) + ")"
                                       for row in grid) + ")"
            output = self.bridge.eval_text(f"({expression} '{literal})")
            _grid(output)
            if (len(output), len(output[0])) != (len(grid), len(grid[0])):
                raise ValueError("Racket changed output dimensions")
            self._cache[identity] = output
            self.evaluations += 1
        return copy.deepcopy(self._cache[identity])

    def close(self):
        self.bridge.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()


def _transform(r, c, index):
    return ((r, c), (c, -r), (-r, -c), (-c, r),
            (r, -c), (-c, -r), (-r, c), (c, r))[index]


def _entries_after(entries, index):
    raw = [(*_transform(r, c, index), value) for r, c, value in entries]
    mr, mc = min(r for r, _, _ in raw), min(c for _, c, _ in raw)
    return [(r - mr, c - mc, value) for r, c, value in raw]


def simulate(grid, min_visible_ports=2):
    """Sampling mirror only. Final labels and certificates always use Racket."""
    threshold = _threshold(min_visible_ports)
    _grid(grid)
    h, w = len(grid), len(grid[0])
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    if not ones:
        raise ValueError("canonical rule requires a nonempty source of color 1")
    r0, r1 = min(r for r, _ in ones), max(r for r, _ in ones)
    c0, c1 = min(c for _, c in ones), max(c for _, c in ones)
    base = [(r-r0, c-c0, grid[r][c]) for r in range(r0, r1+1)
            for c in range(c0, c1+1) if grid[r][c] in (1, 4)]
    all4 = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4}
    painted = set()
    for index in range(8):
        entries = _entries_after(base, index)
        ports = [(r, c) for r, c, value in entries if value == 4]
        cells = [(r, c) for r, c, value in entries if value == 1]
        # A valid candidate has a matched visible port. Enumerating its possible
        # anchors is equivalent to the canonical rectangular anchor scan.
        anchors = {(r-pr, c-pc) for r, c in all4 for pr, pc in ports}
        for ar, ac in anchors:
            visible4 = [(ar+r, ac+c) for r, c in ports
                        if 0 <= ar+r < h and 0 <= ac+c < w]
            if len(visible4) < threshold or any(p not in all4 for p in visible4):
                continue
            visible1 = [(ar+r, ac+c) for r, c in cells
                        if 0 <= ar+r < h and 0 <= ac+c < w]
            if any(grid[r][c] not in (0, 1) for r, c in visible1):
                continue
            painted.update((r, c) for r, c in visible1 if grid[r][c] == 0)
    output = [row[:] for row in grid]
    for r, c in painted:
        output[r][c] = 1
    return output


@lru_cache(maxsize=None)
def _port_choices(height, width):
    interior = [(r, c) for r in range(1, height-1) for c in range(1, width-1)]
    return tuple(ports for ports in combinations(interior, 3)
                 if sum(abs(r-s)+abs(c-t) == 1
                        for (r, c), (s, t) in combinations(ports, 2)) <= 1)


def _make_scene(rng):
    """Original-shaped scenes: source, full copy, clipped copy, scattered ports."""
    h, w = rng.randint(18, 30), rng.randint(18, 30)
    bh, bw = rng.choice(((4, 5), (5, 4), (5, 5)))
    ports = set(rng.choice(_port_choices(bh, bw)))
    base = [(r, c, 4 if (r, c) in ports else 1)
            for r in range(bh) for c in range(bw)]
    grid = [[0] * w for _ in range(h)]
    sr, sc = rng.randint(3, 5), rng.randint(3, 5)
    reserved = set()
    for r, c, value in base:
        grid[sr+r][sc+c] = value
        reserved.add((sr+r, sc+c))
    full = _entries_after(base, rng.randrange(8))
    fr, fc = h-max(r for r, _, _ in full)-3, w-max(c for _, c, _ in full)-3
    clips = []
    for index in range(8):
        entries = _entries_after(base, index)
        for cut in range(1, max(r for r, _, _ in entries)+1):
            if sum(value == 4 and r >= cut for r, _, value in entries) == 2:
                clips.append((entries, cut))
    clipped, cut = rng.choice(clips)
    cr, cc = -cut, w-max(c for _, c, _ in clipped)-3
    evidence = {}
    for name, entries, ar, ac in (("full", full, fr, fc),
                                   ("clipped", clipped, cr, cc)):
        evidence[name + "_visible_ports"] = []
        evidence[name + "_stamp_cells"] = []
        for r, c, value in entries:
            if 0 <= ar+r < h and 0 <= ac+c < w:
                cell = (ar+r, ac+c)
                if cell in reserved:
                    raise ValueError("constructed target footprints overlap")
                reserved.add(cell)
                evidence[name + ("_visible_ports" if value == 4 else "_stamp_cells")].append(cell)
                if value == 4:
                    grid[ar+r][ac+c] = 4
    target_count = rng.randint(17, 47)
    remaining = target_count - sum(value == 4 for row in grid for value in row)
    available = [(r, c) for r in range(h) for c in range(w)
                 if (r, c) not in reserved and grid[r][c] == 0]
    rng.shuffle(available)
    for r, c in available:
        if not remaining:
            break
        if any(0 <= r+dr < h and 0 <= c+dc < w and grid[r+dr][c+dc] == 4
               for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))):
            continue
        grid[r][c] = 4
        remaining -= 1
    if remaining:
        raise ValueError("finite scatter pass could not place requested ports")
    index = rng.randrange(8)
    corners = [_transform(r, c, index) for r, c in ((0, 0), (h-1, 0), (0, w-1), (h-1, w-1))]
    mr, mc = min(r for r, _ in corners), min(c for _, c in corners)
    def mapped(r, c):
        a, b = _transform(r, c, index)
        return a-mr, b-mc
    nh, nw = max(r for r, _ in corners)-mr+1, max(c for _, c in corners)-mc+1
    transformed = [[0] * nw for _ in range(nh)]
    for r in range(h):
        for c in range(w):
            a, b = mapped(r, c)
            transformed[a][b] = grid[r][c]
    evidence = {key: [list(p) for p in sorted(mapped(r, c) for r, c in cells)]
                for key, cells in evidence.items()}
    return transformed, evidence


def _difference(first, second):
    return sum(a != b for row1, row2 in zip(first, second) for a, b in zip(row1, row2))


def certify_episode(train, queries, oracle):
    """Infer survivors from demonstrations; query answers are never consulted."""
    if not train or not queries:
        raise ValueError("nonempty demonstrations and queries are required")
    checks = []
    for threshold in ALLOWED_THRESHOLDS:
        rejected_by = [i for i, pair in enumerate(train)
                       if oracle.evaluate(pair["input"], threshold) != pair["output"]]
        checks.append({"min_visible_ports": threshold, "compatible": not rejected_by,
                       "rejected_by_demonstrations": rejected_by})
    survivors = [check["min_visible_ports"] for check in checks if check["compatible"]]
    query_checks = []
    for pair in queries:
        predictions = {value: oracle.evaluate(pair["input"], value)
                       for value in ALLOWED_THRESHOLDS}
        prediction_hashes = {str(value): grid_sha256(output)
                             for value, output in predictions.items()}
        surviving_hashes = {prediction_hashes[str(value)] for value in survivors}
        identified = len(surviving_hashes) == 1
        query_checks.append({
            "input_sha256": grid_sha256(pair["input"]), "identified": identified,
            "prediction_sha256_by_threshold": prediction_hashes,
            "surviving_prediction_sha256": next(iter(surviving_hashes)) if identified else None,
            "rival_disagreement_cells": _difference(predictions[2], predictions[3]),
        })
    return {"evidence_source": "demonstrations_only",
            "claim_scope": "declared finite family {2,3}; not universal rule uniqueness",
            "surviving_parameters": survivors, "demonstrations": checks,
            "queries": query_checks}


def generate_episode(*, seed, min_visible_ports=None, n_train=2, n_test=4,
                     max_attempts=128, oracle=None):
    _integer("seed", seed, 0, 2**64-1)
    _integer("n_train", n_train, 1, 16)
    _integer("n_test", n_test, 1, 16)
    _integer("max_attempts", max_attempts, 1, 4096)
    threshold = (random.Random(seed ^ 0xC4F6A0585DBF).choice(ALLOWED_THRESHOLDS)
                 if min_visible_ports is None else _threshold(min_visible_ports))
    rng = random.Random(seed)
    need, accepted, seen, rejections = n_train+n_test, [], set(), {}
    for draw_index in range(max_attempts):
        try:
            grid, witness = _make_scene(rng)
            failures = selected_generator().self_check(grid)
            if failures:
                raise ValueError("structural self_check: " + "; ".join(failures))
            identity = grid_sha256(grid)
            if identity in seen:
                raise ValueError("duplicate input")
            predictions = {value: simulate(grid, value) for value in ALLOWED_THRESHOLDS}
            difference = _difference(predictions[2], predictions[3])
            full_changes = sum(grid[r][c] == 0 and predictions[3][r][c] == 1
                               for r, c in witness["full_stamp_cells"])
            if not difference or not full_changes:
                raise ValueError("missing observable threshold or full-stamp witness")
        except ValueError as error:
            reason = str(error)
            rejections[reason] = rejections.get(reason, 0) + 1
            continue
        seen.add(identity)
        witness = dict(witness, draw_index=draw_index, input_sha256=identity,
                       height=len(grid), width=len(grid[0]),
                       threshold_disagreement_cells=difference,
                       full_stamp_changed_cells_at_3=full_changes)
        accepted.append((grid, predictions, witness))
        if len(accepted) == need:
            break
    if len(accepted) != need:
        raise SamplingExhausted(f"accepted {len(accepted)} of {need} inputs in "
                                f"{max_attempts} attempts; rejections={rejections}")
    owns_oracle = oracle is None
    oracle = oracle or RacketOracle()
    try:
        pairs, label_evidence = [], []
        for grid, predictions, witness in accepted:
            outputs = {value: oracle.evaluate(grid, value) for value in ALLOWED_THRESHOLDS}
            if outputs != predictions:
                raise RuntimeError("Python sampling mirror disagrees with matching Racket")
            pairs.append({"input": grid, "output": outputs[threshold]})
            label_evidence.append({"input_sha256": witness["input_sha256"],
                                   "racket_outputs_by_threshold":
                                       {str(value): outputs[value] for value in ALLOWED_THRESHOLDS}})
        train, test = pairs[:n_train], pairs[n_train:]
        certificate = certify_episode(train, test, oracle)
        if certificate["surviving_parameters"] != [threshold] or not all(
                row["identified"] for row in certificate["queries"]):
            raise RuntimeError("demonstrations did not identify the declared threshold")
        program = materialize_program(threshold)
        return {"schema": "c4f6a0585dbf-port-threshold-prototype-v1",
                "status": "proposed", "task_id": TASK_ID, "parent": "training:7df24a62",
                "seed": seed, "parameters": {"min_visible_ports": threshold},
                "canonical_program_sha256": CANONICAL_PROGRAM_SHA256,
                "program_solution": program,
                "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
                "source_hashes": source_hashes(), "train": train, "test": test,
                "sampling": {"max_attempts": max_attempts,
                             "attempts": accepted[-1][2]["draw_index"]+1,
                             "rejections": rejections,
                             "accepted": [row[2] for row in accepted]},
                "label_evidence": label_evidence, "certificate": certificate}
    finally:
        if owns_oracle:
            oracle.close()


def write_batch(episodes, out):
    """Write visible bytes/IDs from shared helpers; keep all other data private."""
    if type(episodes) is not list or not episodes:
        raise ValueError("episodes must be a nonempty list")
    prepared, seen = [], set()
    for episode in episodes:
        payload = public_challenge_bytes(episode)
        identity = public_challenge_id(episode)
        if identity in seen:
            raise ValueError("duplicate visible challenge payload")
        seen.add(identity)
        prepared.append((identity, payload, episode))
    prepared.sort(key=lambda row: row[0])
    for _, _, episode in prepared:
        program = episode["program_solution"]
        if hashlib.sha256(program.encode()).hexdigest() != episode["program_sha256"]:
            raise ValueError("private program digest does not match its exact bytes")
        if program != materialize_program(episode["parameters"]["min_visible_ports"]):
            raise ValueError("private program does not match the declared setting")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    (out / "private/programs").mkdir(parents=True)
    private_rows = []
    for identity, payload, episode in prepared:
        (out / "public" / (identity + ".json")).write_bytes(payload)
        program_path = out / "private/programs" / (episode["program_sha256"] + ".rkt")
        program_path.write_text(episode["program_solution"])
        private_rows.append(dict(episode, public_id=identity))
    (out / "private/episodes.jsonl").write_text("".join(
        json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
        for row in private_rows))
    receipt = {"schema": "c4f6a0585dbf-port-threshold-export-v1", "status": "proposed",
               "public_ids": [identity for identity, _, _ in prepared],
               "episodes": len(prepared), "public_identifier_source": "exact visible challenge bytes",
               "program_sha256": sorted({episode["program_sha256"] for _, _, episode in prepared})}
    (out / "private/export.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--settings", type=int, nargs="+", choices=ALLOWED_THRESHOLDS,
                        default=list(ALLOWED_THRESHOLDS))
    parser.add_argument("--train", type=int, default=2)
    parser.add_argument("--test", type=int, default=4)
    parser.add_argument("--max-attempts", type=int, default=128)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    with RacketOracle() as oracle:
        episodes = [generate_episode(seed=args.seed, min_visible_ports=value,
                    n_train=args.train, n_test=args.test, max_attempts=args.max_attempts,
                    oracle=oracle) for value in args.settings]
        receipt = write_batch(episodes, args.out)
        receipt.update({"command": [sys.executable] + sys.argv, "cwd": str(Path.cwd()),
                        "racket_evaluations": oracle.evaluations,
                        "runtime_identity": oracle.bridge.runtime_identity,
                        "source_hashes": source_hashes(),
                        "pair_counts": [{"public_id": public_challenge_id(ep),
                                         "train": len(ep["train"]), "test": len(ep["test"])}
                                        for ep in sorted(episodes, key=public_challenge_id)]})
        (args.out / "private/export.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": "proposed", "episodes": receipt["episodes"],
                      "public_ids": receipt["public_ids"],
                      "racket_evaluations": receipt["racket_evaluations"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
