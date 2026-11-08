"""Proposed X/cross neighborhood family with constructive lessons and Racket checks.

Canonical generation is untouched. ``generate`` makes Python label claims for
the native adapter; ``write_batch`` executes and verifies every retained label.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

from reviewer_support import public_challenge_bytes, public_challenge_id


TASK_ID = "7cda20c438b7"
HERE = Path(__file__).resolve().parent
NEIGHBORHOODS = {
    "diagonal": ((-1, -1), (-1, 1), (1, -1), (1, 1)),
    "orthogonal": ((-1, 0), (0, -1), (0, 1), (1, 0)),
}
DEMO_SHAPES = ((13, 17), (17, 13), (13, 17), (17, 13), (13, 17), (17, 13))
QUERY_SHAPES = ((7, 7), (16, 20), (23, 29), (30, 30))


def _integer(value, label, minimum=None, maximum=None):
    if type(value) is not int or (minimum is not None and value < minimum) or (
            maximum is not None and value > maximum):
        raise ValueError(f"{label} must be an exact integer in {minimum}..{maximum}")
    return value


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"neighborhood"}:
        raise ValueError("settings must contain exactly neighborhood")
    value = settings["neighborhood"]
    if type(value) is not str or value not in NEIGHBORHOODS:
        raise ValueError("neighborhood must be diagonal or orthogonal")
    return value


def _grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width or
           any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def program(settings):
    """Return exact source, including the byte-preserved canonical default."""
    return (HERE / (_setting(settings) + ".rkt")).read_text(encoding="utf-8")


def centers(grid, settings):
    _grid(grid)
    offsets = NEIGHBORHOODS[_setting(settings)]
    return [(r, c) for r in range(1, len(grid) - 1)
            for c in range(1, len(grid[0]) - 1)
            if grid[r][c] == 0 and all(grid[r + dr][c + dc] == 3 for dr, dc in offsets)]


def transform(grid, settings):
    """Python claims only; the authoring writer independently executes Racket."""
    result = deepcopy(_grid(grid))
    for r, c in centers(grid, settings):
        result[r][c] = 4
    return result


def _rng(seed, stream, index):
    key = json.dumps([seed, stream, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(key).digest(), "big"))


def _motif(kind, rng):
    """Independent 5x5 patches; each needed contrast is constructed, not hoped for."""
    g = [[0] * 5 for _ in range(5)]
    if kind == 0:  # Two X centers share two arms.
        for r in (1, 3):
            for c in (0, 2, 4):
                g[r][c] = 3
    elif kind == 1:  # Two cross centers share one arm.
        for r, c in ((1, 1), (3, 1), (2, 0), (2, 2), (1, 3), (3, 3), (2, 4)):
            g[r][c] = 3
    elif kind in (2, 3, 4, 5, 6, 7, 9, 10):
        neighborhood = "diagonal" if kind in (2, 4, 6, 9) else "orthogonal"
        offsets = list(NEIGHBORHOODS[neighborhood])
        if kind in (2, 3):
            offsets.pop(rng.randrange(4))
        color = rng.choice((1, 2, 5, 6, 7, 8, 9)) if kind in (6, 7) else 3
        for dr, dc in offsets:
            g[2 + dr][2 + dc] = color
        if kind in (4, 5):
            g[2][2] = rng.choice((1, 2, 5, 6, 7, 8, 9))
    elif kind == 8:  # Both geometries: shared context is preserved.
        for dr, dc in (*NEIGHBORHOODS["diagonal"], *NEIGHBORHOODS["orthogonal"]):
            g[2 + dr][2 + dc] = 3
    else:
        for r in range(5):
            for c in range(5):
                if rng.random() < 0.24:
                    g[r][c] = rng.choice((0, 3, 3, 2, 6))
    for _ in range(rng.randrange(4)):
        g = [list(row) for row in zip(*g[::-1])]
    if rng.randrange(2):
        g = [row[::-1] for row in g]
    return g


def _starts(length, rng):
    count = (length + 1) // 6
    if count == 1:
        return [rng.randrange(length - 4)]
    return [i * (length - 5) // (count - 1) for i in range(count)]


def sample_input(seed, stream, index, height, width, motif_ids=None):
    """Sample the same lawful input independently of hidden rule settings.

    The grammar is 7..30 on each side. Large grids carry motifs throughout the
    canvas; patches and their zero separators prevent accidental cross-tile
    changes from erasing a constructed demonstration witness.
    """
    _integer(seed, "seed")
    _integer(index, "index", 0)
    _integer(height, "height", 7, 30)
    _integer(width, "width", 7, 30)
    if type(stream) is not str or not stream:
        raise ValueError("stream must be a nonempty string")
    rng = _rng(seed, stream, index)
    row_starts, col_starts = _starts(height, rng), _starts(width, rng)
    positions = [(r, c) for r in row_starts for c in col_starts]
    ids = list(range(12)) if motif_ids is None else list(motif_ids)
    if not ids or any(type(x) is not int or x not in range(12) for x in ids):
        raise ValueError("motif_ids must be nonempty integers 0..11")
    if motif_ids is not None and len(ids) > len(positions):
        raise ValueError("canvas cannot hold the requested constructive motifs")
    rng.shuffle(ids)
    order = [ids[i % len(ids)] for i in range(len(positions))]
    rng.shuffle(order)
    g = [[0] * width for _ in range(height)]
    for (r0, c0), kind in zip(positions, order):
        patch = _motif(kind, rng)
        for r, row in enumerate(patch):
            g[r0 + r][c0:c0 + 5] = row
    # Clipped boundary cues: a border zero can never qualify under either rule.
    # Only corners outside every 5x5 patch are touched, preserving all witnesses.
    occupied = {(r, c) for r0, c0 in positions
                for r in range(r0, r0 + 5) for c in range(c0, c0 + 5)}
    for r, c in ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)):
        if (r, c) not in occupied:
            g[r][c] = rng.choice((0, 2, 3, 6))
    if rng.randrange(2):
        g.reverse()
    if rng.randrange(2):
        g = [row[::-1] for row in g]
    return g


def generate(seed, settings, demos, queries):
    """Native adapter contract: deterministic, episode-fixed and count-independent."""
    _integer(seed, "seed")
    _setting(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    result = {"train": [], "test": [], "program_solution": program(settings),
              "settings": dict(settings), "seed": seed, "prototype": True}
    seen = set()
    for split, shapes in (("train", DEMO_SHAPES[:demos]), ("test", QUERY_SHAPES[:queries])):
        for index, (height, width) in enumerate(shapes):
            # The first two demos jointly cover overlap, partials, occupied
            # centers, wrong-color arms, intersection and isolated patterns.
            motifs = list(range(6)) if split == "train" and index % 2 == 0 else (
                list(range(6, 12)) if split == "train" else None)
            grid = sample_input(seed, split, index, height, width, motifs)
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise ValueError("deterministic sampler produced duplicate inputs")
            seen.add(key)
            result[split].append({"input": grid, "output": transform(grid, settings)})
    return result


def _predicate(neighborhood, *, center_zero=True, minimum=4, nonzero=False):
    checks = [f"({'not' if nonzero else '='} "
              f"{('(= ' if nonzero else '')}(at g (+ r {dr}) (+ c {dc})) "
              f"{('0))' if nonzero else '3)')}" for dr, dc in NEIGHBORHOODS[neighborhood]]
    # Keep the intended threshold explicit in executable Racket.
    arms = "(>= (+ " + " ".join(f"(if {item} 1 0)" for item in checks) + f") {minimum})"
    return f"(and (= (at g r c) 0) {arms})" if center_zero else arms


def _scan(predicate):
    return ("(rule! (for*/fold ((out g)) ((r (in-range 1 (- (rows g) 1))) "
            "(c (in-range 1 (- (cols g) 1)))) "
            f"(if {predicate} (set-cell out r c 4) out)))")


def hypotheses(settings):
    """Finite declared setting and shortcut family; no completeness claim."""
    chosen = _setting(settings)
    offsets = NEIGHBORHOODS[chosen]
    ds = "'(" + " ".join(f"({dr} {dc})" for dr, dc in offsets) + ")"
    pred = _predicate(chosen)
    isolated = f"""(rule! (let* ((ds {ds})
      (cs (for*/list ((r (in-range 1 (- (rows g) 1)))
                     (c (in-range 1 (- (cols g) 1))) #:when {pred}) (list r c)))
      (arms (for*/list ((p (in-list cs)) (d (in-list ds)))
              (list (+ (first p) (first d)) (+ (second p) (second d))))))
      (for/fold ((out g)) ((p (in-list cs)))
        (if (for/and ((d (in-list ds)))
              (let ((a (list (+ (first p) (first d)) (+ (second p) (second d)))))
                (= 1 (for/sum ((other (in-list arms))) (if (equal? a other) 1 0)))))
            (set-cell out (first p) (second p) 4) out))))"""
    return {
        **{"setting:" + value: program({"neighborhood": value}) for value in NEIGHBORHOODS},
        "identity": "(rule! (lambda (g) g))",
        "both_neighborhoods": _scan(f"(or {_predicate('diagonal')} {_predicate('orthogonal')})"),
        "three_arms": _scan(_predicate(chosen, minimum=3)),
        "overwrite_occupied": _scan(_predicate(chosen, center_zero=False)),
        "any_nonzero_arms": _scan(_predicate(chosen, nonzero=True)),
        "isolated_only": isolated,
    }


class Reference:
    """A single owned protected-Racket process, reusable across a bounded study."""
    def __init__(self):
        from arc_repl.racket_bridge import RacketBridge
        self.bridge = RacketBridge(timeout=10.0)
        self.names = {}
        self.calls = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.bridge.shutdown()

    def apply(self, source, grid):
        from puzzle_generators.rule_wrap import wrap_rule
        _grid(grid)
        if source not in self.names:
            name = "neighborhood_rule_" + str(len(self.names))
            self.bridge.eval_text(f"(define {name} {wrap_rule(source)})")
            self.names[source] = name
        self.bridge.define_grid("neighborhood_input", grid)
        output = self.bridge.eval_text(f"({self.names[source]} neighborhood_input)")
        self.calls += 1
        return _grid(output)


def fit_demonstrations(train, settings, reference):
    """Fit to demos only. Query inputs and outputs are deliberately not arguments."""
    programs = hypotheses(settings)
    survivors, rejected = [], {}
    for name, source in programs.items():
        mismatches = []
        for index, pair in enumerate(train):
            # Runtime errors abort; they never count as a distinguishing demo.
            if reference.apply(source, pair["input"]) != pair["output"]:
                mismatches.append(index)
        if mismatches:
            rejected[name] = mismatches
        else:
            survivors.append(name)
    return {"survivors": survivors, "rejected_by_demo": rejected,
            "program_sha256": {name: hashlib.sha256(src.encode()).hexdigest()
                               for name, src in programs.items()}}


def verify_episode(episode, reference):
    """Reject malformed requests, false labels, repeats and unidentifiable queries."""
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    settings = episode.get("settings")
    chosen = _setting(settings)
    if episode.get("program_solution") != program(settings):
        raise ValueError("episode program differs from its fixed setting")
    seen = set()
    for split, minimum, maximum in (("train", 2, 6), ("test", 1, 4)):
        pairs = episode.get(split)
        if type(pairs) is not list or not minimum <= len(pairs) <= maximum:
            raise ValueError(f"{split} count must be in {minimum}..{maximum}")
        for pair in pairs:
            if type(pair) is not dict or "input" not in pair or "output" not in pair:
                raise ValueError("every private pair needs input and output")
            _grid(pair["input"])
            _grid(pair["output"])
            key = json.dumps(pair["input"], separators=(",", ":"))
            if key in seen:
                raise ValueError("duplicate demonstration/query input")
            seen.add(key)
            if reference.apply(program(settings), pair["input"]) != pair["output"]:
                raise ValueError("claimed output differs from executed Racket")
    fit = fit_demonstrations(episode["train"], settings, reference)
    if "setting:" + chosen not in fit["survivors"]:
        raise ValueError("chosen setting does not fit demonstrations")
    programs = hypotheses(settings)
    checks = []
    for index, pair in enumerate(episode["test"]):
        for name in fit["survivors"]:
            if reference.apply(programs[name], pair["input"]) != pair["output"]:
                raise ValueError(f"demonstrations do not identify query {index}: {name}")
        checks.append({"query_index": index, "identified_from_demonstrations": True})
    return {"schema": "x-neighborhood-finite-rivals-v1", **fit,
            "fit_uses": "demonstrations_only", "query_checks": checks,
            "limit": "Only the two declared settings and six named shortcuts are tested."}


def source_bindings():
    files = [HERE / name for name in ("prototype.py", "adapter.py", "promotion.json",
                                     "diagonal.rkt", "orthogonal.rkt")]
    files.append(HERE.parents[1] / "generator.py")
    return {str(path.relative_to(HERE.parents[3])): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files}


def write_batch(episodes, destination, reference):
    """Validate completely before creating a fresh public/private output directory."""
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    if type(episodes) is not list or not episodes:
        raise ValueError("a nonempty episode list is required")
    prepared, seen = [], set()
    for episode in episodes:
        visible = public_challenge_bytes(episode)
        identity = public_challenge_id(episode)
        if identity in seen:
            raise ValueError("duplicate visible challenge in batch")
        seen.add(identity)
        prepared.append((identity, visible, deepcopy(episode)))
    bindings = source_bindings()
    rows = []
    for identity, visible, episode in sorted(prepared, key=lambda item: item[0]):
        certificate = verify_episode(episode, reference)
        rows.append((identity, visible, {"id": identity, "episode": episode,
                    "certificate": certificate, "source_sha256": bindings,
                    "program_sha256": hashlib.sha256(episode["program_solution"].encode()).hexdigest()}))
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "public").mkdir()
    for identity, visible, _ in rows:
        (destination / "public" / (identity + ".json")).write_bytes(visible)
    private = b"".join((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
                       for _, _, row in rows)
    (destination / "private.jsonl").write_bytes(private)
    manifest = {"schema": "x-neighborhood-authoring-batch-v1", "task_id": TASK_ID,
                "status": "proposed_unaccepted", "training_admitted": False,
                "episode_count": len(rows), "ids": [row[0] for row in rows],
                "private_sha256": hashlib.sha256(private).hexdigest(),
                "source_sha256": bindings, "runtime": reference.bridge.runtime_identity}
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", action="append", type=int)
    parser.add_argument("--setting", action="append", choices=tuple(NEIGHBORHOODS))
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    episodes = [generate(seed, {"neighborhood": setting}, args.demos, args.queries)
                for seed in (args.seed or [0, 17]) for setting in (args.setting or list(NEIGHBORHOODS))]
    with Reference() as reference:
        manifest = write_batch(episodes, args.out, reference)
        print(json.dumps({"status": manifest["status"], "episodes": len(episodes),
                          "racket_applications": reference.calls, "output": str(args.out)}))


if __name__ == "__main__":
    main()
