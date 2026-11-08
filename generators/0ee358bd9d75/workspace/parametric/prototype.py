"""Proposed section-frequency variant; no production generator API changes.

All episode labels are executed by the existing Racket bridge. Sampling never
consults the episode's selection, so the rule is learned from demonstrations.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import public_challenge_bytes, public_challenge_id


TASK_ID = "0ee358bd9d75"
FAMILY = "training:780d0b14"
VERSION = "prototype-2"
SELECTIONS = ("most_frequent", "least_frequent")
DEFAULT_SELECTION = "most_frequent"
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)
HERE = Path(__file__).resolve().parent


def digest(value):
    """Stable hash for JSON data; program hashes use their exact UTF-8 text."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _check_seed(seed):
    if type(seed) is not int:
        raise ValueError("seed must be an integer, excluding booleans")


def _check_counts(demos, queries):
    for name, count, limits in (("demos", demos, DEMO_LIMITS), ("queries", queries, QUERY_LIMITS)):
        if type(count) is not int or not limits[0] <= count <= limits[1]:
            raise ValueError(f"{name} must be an integer in {limits[0]}..{limits[1]}, excluding booleans")


def _rng(seed, label):
    _check_seed(seed)
    identity = f"{TASK_ID}:{VERSION}:{seed}:{label}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(identity).digest(), "big"))


def choose_selection(seed):
    """Optional automatic choice: one deterministic draw for the whole episode."""
    return _rng(seed, "episode-selection").choice(SELECTIONS)


def materialize_program(selection=DEFAULT_SELECTION):
    if selection not in SELECTIONS:
        raise ValueError(f"selection must be one of {SELECTIONS}")
    return (HERE / "programs" / (selection + ".rkt")).read_text(encoding="utf-8")


def _spans(length, dividers):
    edges = [-1, *dividers, length]
    return [(left + 1, right) for left, right in zip(edges, edges[1:])]


def validate_input(grid, *, require_mixed=False):
    """Recover and check the common domain from cells, without hidden metadata."""
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        raise ValueError("grid must be a nonempty list of rows")
    h, w = len(grid), len(grid[0])
    if not 8 <= h <= 30 or not 8 <= w <= 30 or any(len(row) != w for row in grid):
        raise ValueError("grid must be rectangular with each dimension in 8..30")
    if any(type(color) is not int or not 0 <= color <= 9 for row in grid for color in row):
        raise ValueError("grid cells must be integer ARC colors 0..9")
    zero_rows = [r for r, row in enumerate(grid) if not any(row)]
    zero_cols = [c for c in range(w) if not any(grid[r][c] for r in range(h))]
    for label, dividers, length in (("row", zero_rows, h), ("column", zero_cols, w)):
        if not 1 <= len(dividers) <= 3:
            raise ValueError(f"need 1..3 full-zero {label} dividers")
        if dividers[0] == 0 or dividers[-1] == length - 1:
            raise ValueError(f"edge {label} divider")
    row_spans, col_spans = _spans(h, zero_rows), _spans(w, zero_cols)
    if any(end - start < 2 for start, end in row_spans + col_spans):
        raise ValueError("each section side must be at least two cells")
    sections = []
    for r0, r1 in row_spans:
        for c0, c1 in col_spans:
            cells = [grid[r][c] for r in range(r0, r1) for c in range(c0, c1)]
            counts = Counter(color for color in cells if color)
            if not counts or len(counts) > 3 or 0 not in cells:
                raise ValueError("each section needs zero nuisance cells and 1..3 nonzero colors")
            if require_mixed and len(counts) < 2:
                raise ValueError("teaching sections must contain at least two nonzero colors")
            if any(not any(grid[r][c] for c in range(c0, c1)) for r in range(r0, r1)):
                raise ValueError("empty local section row")
            if any(not any(grid[r][c] for r in range(r0, r1)) for c in range(c0, c1)):
                raise ValueError("empty local section column")
            most = [color for color, count in counts.items() if count == max(counts.values())]
            least = [color for color, count in counts.items() if count == min(counts.values())]
            if len(most) != 1 or len(least) != 1:
                raise ValueError("both nonzero frequency extrema must be unique")
            sections.append({
                "span": [r0, r1, c0, c1], "counts": dict(sorted(counts.items())),
                "most_frequent": most[0], "least_frequent": least[0],
            })
    return {"height": h, "width": w, "zero_rows": zero_rows, "zero_cols": zero_cols,
            "output_shape": [len(row_spans), len(col_spans)], "sections": sections}


def _partition(length, rng):
    n_dividers = rng.randint(1, min(3, (length - 2) // 3))
    sizes = [2] * (n_dividers + 1)
    for _ in range(length - n_dividers - sum(sizes)):
        sizes[rng.randrange(len(sizes))] += 1
    spans, cursor = [], 0
    for size in sizes:
        spans.append((cursor, cursor + size))
        cursor += size + 1
    return spans


def _sample_input(seed, pair_index, *, role, attempt):
    rng = _rng(seed, f"{role}-{pair_index}-attempt-{attempt}")
    bands = {"demo": ((8, 8), (12, 20), (16, 24), (8, 15), (18, 26), (22, 30)),
             "query": ((30, 30), (22, 30), (16, 24), (12, 20))}
    low, high = bands[role][pair_index]
    h, w = rng.randint(low, high), rng.randint(low, high)
    grid = [[0] * w for _ in range(h)]
    for r0, r1 in _partition(h, rng):
        # Reuse one column partition across every row of sections.
        if r0 == 0:
            col_spans = _partition(w, rng)
        for c0, c1 in col_spans:
            height, width = r1 - r0, c1 - c0
            area = height * width
            # Every section is substantive, including at the 30x30 boundary.
            occupied = rng.randint(max(3, height, width, (2 * area + 4) // 5), area - 1)
            rows, cols = list(range(r0, r1)), list(range(c0, c1))
            rng.shuffle(rows)
            rng.shuffle(cols)
            coverage = {(rows[i % height], cols[i % width]) for i in range(max(height, width))}
            remaining = [(r, c) for r in range(r0, r1) for c in range(c0, c1) if (r, c) not in coverage]
            rng.shuffle(remaining)
            positions = sorted(coverage) + remaining[:occupied - len(coverage)]
            rng.shuffle(positions)
            if occupied >= 6 and rng.choice((False, True)):
                rare = rng.randint(1, (occupied - 3) // 3)
                middle = rng.randint(rare + 1, (occupied - rare - 1) // 2)
                counts = (rare, middle, occupied - rare - middle)
            else:
                rare = rng.randint(1, (occupied - 1) // 2)
                counts = (rare, occupied - rare)
            colors = rng.sample(range(1, 10), len(counts))
            values = [color for color, count in zip(colors, counts) for _ in range(count)]
            rng.shuffle(values)
            for (r, c), color in zip(positions, values):
                grid[r][c] = color
    validate_input(grid, require_mixed=True)
    return grid


def _teaches_both_settings(grid):
    """Reject finite positional/color shortcuts using demonstrations alone.

    These pixel-derived predictions select inputs; emitted labels still come
    exclusively from Racket. Requiring both settings keeps sampling independent
    of the episode parameter and allows the legacy single-query rotations.
    """
    predictions = {name: [] for name in (*SELECTIONS, "first", "last", "min", "max")}
    for section in validate_input(grid, require_mixed=True)["sections"]:
        r0, r1, c0, c1 = section["span"]
        cells = [grid[r][c] for r in range(r0, r1) for c in range(c0, c1) if grid[r][c]]
        for setting in SELECTIONS:
            predictions[setting].append(section[setting])
        for name, value in (("first", cells[0]), ("last", cells[-1]),
                            ("min", min(cells)), ("max", max(cells))):
            predictions[name].append(value)
    return all(predictions[setting] != answer
               for setting in SELECTIONS for rival, answer in predictions.items() if rival != setting)


def sample_inputs(seed, *, demos=3, queries=1):
    """Independent 2..6 demo and 1..4 query prefixes, matched across settings.

    The bounded full pool is built independently of requested counts, so adding
    demonstrations never changes a query and stopping after query one never
    changes the first public turn. No query output is used to select a demo.
    """
    _check_seed(seed)
    _check_counts(demos, queries)
    pools, seen = {}, set()
    for role, maximum in (("demo", DEMO_LIMITS[1]), ("query", QUERY_LIMITS[1])):
        pool = []
        for index in range(maximum):
            for attempt in range(256):
                grid = _sample_input(seed, index, role=role, attempt=attempt)
                identity = digest(grid)
                if identity not in seen and _teaches_both_settings(grid):
                    pool.append(grid)
                    seen.add(identity)
                    break
            else:
                raise RuntimeError(f"bounded sampler exhausted for {role} {index}")
        pools[role] = pool
    return pools["demo"][:demos] + pools["query"][:queries]


def execute_program(program, inputs, *, bridge=None):
    """Execute the materialized lambda in the supplied offline Racket runtime."""
    text = program.strip()
    if not text.startswith("(rule! (lambda ") or not text.endswith(")"):
        raise ValueError("expected the task's materialized (rule! (lambda ...)) program")
    expression = text[len("(rule! "):-1]
    own_bridge = bridge is None
    bridge = RacketBridge() if own_bridge else bridge
    try:
        outputs = []
        for grid in inputs:
            validate_input(grid)
            literal = "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            output = bridge.eval_text(f"(let ((parametric-rule {expression})) (parametric-rule '{literal}))")
            if not isinstance(output, list) or not output or not all(isinstance(row, list) for row in output):
                raise RuntimeError("Racket returned a non-grid label")
            outputs.append(output)
        return outputs
    finally:
        if own_bridge:
            bridge.close()


def generate_episode(seed, *, selection=DEFAULT_SELECTION, demos=3, queries=1, bridge=None):
    """Build independently requested demonstrations and queries with one rule.

    The omitted/default selection is canonical. Passing None explicitly requests
    a seed-derived automatic setting; it is resolved once, before any pair.
    """
    _check_seed(seed)
    _check_counts(demos, queries)
    chosen = choose_selection(seed) if selection is None else selection
    program = materialize_program(chosen)
    inputs = sample_inputs(seed, demos=demos, queries=queries)
    outputs = execute_program(program, inputs, bridge=bridge)
    pairs = [{"input": source, "output": target} for source, target in zip(inputs, outputs)]
    return {
        "schema": "section-frequency-parametric-prototype-v1", "status": "prototype",
        "generator_id": TASK_ID, "family": FAMILY, "version": VERSION,
        "seed": seed, "selection": chosen, "requested_selection": "auto" if selection is None else selection,
        "program": program, "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "prototype_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "label_source": "RacketBridge", "train_pair_indices": list(range(demos)),
        "query_pair_indices": list(range(demos, demos + queries)),
        "query_pair_index": demos if queries == 1 else None,
        "train": pairs[:demos], "test": pairs[demos:],
    }


def rotate_episode(episode, query_index):
    """Legacy 3-demo/1-query API: move one of four executed pairs to query."""
    if type(query_index) is not int or not 0 <= query_index < 4:
        raise ValueError("query_index must be an integer in 0..3")
    if len(episode["train"]) != 3 or len(episode["test"]) != 1:
        raise ValueError("rotate_episode requires exactly three demonstrations and one query")
    result = deepcopy(episode)
    indexed = dict(zip(episode["train_pair_indices"], episode["train"]))
    indexed[episode["query_pair_index"]] = episode["test"][0]
    demo_indices = [index for index in range(4) if index != query_index]
    result["train_pair_indices"], result["query_pair_index"] = demo_indices, query_index
    result["query_pair_indices"] = [query_index]
    result["train"] = [deepcopy(indexed[index]) for index in demo_indices]
    result["test"] = [deepcopy(indexed[query_index])]
    return result


def public_challenge(episode):
    """Whole-episode compatibility projection; use public_turn for a solver."""
    return json.loads(public_challenge_bytes(episode))


def public_turn(episode, query_index=0):
    """Current query only; a private controller advances after the prior answer.

    The projection deliberately contains no index, count, future input, final
    flag, setting, program, or query label. Previous answers remain controller
    state, so they cannot accidentally become mislabeled demonstrations.
    """
    if type(query_index) is not int or not 0 <= query_index < len(episode["test"]):
        raise ValueError("query_index must identify one available query")
    return json.loads(public_challenge_bytes({"train": episode["train"],
                                             "test": [episode["test"][query_index]]}))


def write_episode(episode, output):
    """Publish only the first turn; retain all answers and later inputs privately."""
    first = public_turn(episode)
    visible_bytes = public_challenge_bytes(first)
    identity = public_challenge_id(first)
    private_bytes = (json.dumps(episode, indent=2, sort_keys=True) + "\n").encode("utf-8")
    program_bytes = episode["program"].encode("utf-8")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / "public").mkdir()
    (output / "private").mkdir()
    (output / "public" / (identity + ".json")).write_bytes(visible_bytes)
    (output / "private" / "episode.json").write_bytes(private_bytes)
    (output / "private" / "program.rkt").write_bytes(program_bytes)
    return identity


def differing_witness():
    return [
        [1, 1, 0, 0, 3, 3, 0, 3],
        [1, 0, 1, 0, 4, 0, 3, 3],
        [2, 2, 1, 0, 3, 4, 3, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [5, 5, 0, 0, 7, 7, 7, 0],
        [6, 5, 5, 0, 8, 7, 0, 7],
        [0, 6, 5, 0, 7, 0, 8, 7],
        [5, 0, 5, 0, 0, 8, 7, 7],
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--selection", choices=(*SELECTIONS, "auto"), default=DEFAULT_SELECTION)
    parser.add_argument("--demos", type=int, choices=range(2, 7), default=3)
    parser.add_argument("--queries", type=int, choices=range(1, 5), default=1)
    parser.add_argument("--query-index", type=int, choices=range(4), default=None,
                        help="legacy holdout rotation; requires --demos 3 --queries 1")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("--out must be a new directory")
    if args.query_index is not None and (args.demos, args.queries) != (3, 1):
        parser.error("--query-index requires --demos 3 --queries 1")
    episode = generate_episode(args.seed, selection=None if args.selection == "auto" else args.selection,
                               demos=args.demos, queries=args.queries)
    if args.query_index is not None:
        episode = rotate_episode(episode, args.query_index)
    identity = write_episode(episode, args.out)
    print(json.dumps({"status": "prototype", "out": str(args.out), "seed": args.seed,
                      "selection": episode["selection"], "racket_labels": args.demos + args.queries,
                      "first_turn_public_id": identity}))


if __name__ == "__main__":
    main()
