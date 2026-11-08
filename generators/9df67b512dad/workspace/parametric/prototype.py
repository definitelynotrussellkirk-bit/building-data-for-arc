"""Proposed task-local zone compression variants, labeled by protected Racket."""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
import sys

# Bootstrap only this source tree, supporting repository and staged runtime layouts.
for _ancestor in Path(__file__).resolve().parents:
    for _candidate in (_ancestor / "shared/runtime", _ancestor):
        if (_candidate / "reviewer_support.py").is_file():
            sys.path.insert(0, str(_candidate))
            break
    else:
        continue
    break

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_path, find_root, public_challenge_bytes, public_challenge_id,
)

ROOT = find_root(__file__)
TASK_ID = "9df67b512dad"
PARAMETERS = {"scan_order": ("row_major", "column_major"), "pick": ("first", "last")}
DEFAULT_SETTINGS = {"scan_order": "row_major", "pick": "last"}
_SETTING_PAIRS = (
    ("row_major", "last"), ("row_major", "first"),
    ("column_major", "last"), ("column_major", "first"),
)
LIMITATIONS = [
    "Prototype only; no parametric API acceptance or training admission is claimed.",
    "Identifiability covers the four declared settings and a global-first occupancy rival; arbitrary program uniqueness is unproved.",
    "Sampler uses 5..14 rows, 7..16 columns, 4..8 occupied zones, five sampled foreground colors, and a four-point interior witness diamond.",
    "At least one top boundary zone is occupied; no solid foreground 2x2 block is admitted.",
    "Input dimensions match the selected generator's range; the five-color palette extends its current 1..3-color sampling range.",
    "Demonstration and query counts each range from 1 to 8; uniqueness sampling is bounded at 128 attempts per input.",
    "Bounded retained seeds are evidence, not a census of all seeds or a measured learning benefit.",
]


def all_settings():
    return [{"scan_order": order, "pick": pick} for order, pick in _SETTING_PAIRS]


def _settings(value=None):
    if value is None:
        return dict(DEFAULT_SETTINGS)
    if type(value) is not dict or set(value) != set(PARAMETERS):
        raise ValueError("settings require exactly scan_order and pick")
    if any(type(value[key]) is not str or value[key] not in allowed
           for key, allowed in PARAMETERS.items()):
        raise ValueError("scan_order must be row_major/column_major; pick must be first/last")
    return dict(value)


def _integer(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a literal integer in {low}..{high}")
    return value


def _grid(value, *, heights, widths, name):
    if type(value) is not list or not heights[0] <= len(value) <= heights[1]:
        raise ValueError(f"{name} must have {heights[0]}..{heights[1]} list rows")
    if type(value[0]) is not list or not widths[0] <= len(value[0]) <= widths[1]:
        raise ValueError(f"{name} must have {widths[0]}..{widths[1]} columns")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width or
           any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in value):
        raise ValueError(f"{name} must be rectangular with literal integer colors 0..9")
    return value


def _zones(height, width):
    rows = ([0], list(range(1, height - 1)), [height - 1])
    cols = ([0], list(range(1, width - 1)), [width - 1])
    return [[(r, c) for r in rs for c in cs] for rs in rows for cs in cols]


def validate_input(grid):
    _grid(grid, heights=(5, 14), widths=(7, 16), name="input")
    height, width = len(grid), len(grid[0])
    occupied = sum(any(grid[r][c] for r, c in zone) for zone in _zones(height, width))
    if not 4 <= occupied <= 8:
        raise ValueError("input must occupy 4..8 of the nine zones")
    if any(all(grid[r + dr][c + dc] for dr in (0, 1) for dc in (0, 1))
           for r in range(height - 1) for c in range(width - 1)):
        raise ValueError("solid foreground 2x2 blocks are outside the sparse marker grammar")


@lru_cache(maxsize=1)
def _canonical_program():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    selected = [row for row in rows if row.get("task_id") == TASK_ID]
    if len(selected) != 1:
        raise ValueError("expected exactly one source-bound canonical row")
    return selected[0]["program_solution"]


def program(settings=None):
    """Return exact canonical text at the default; materialize other rules."""
    selected = _settings(settings)
    if selected == DEFAULT_SETTINGS:
        return _canonical_program()
    if selected["scan_order"] == "row_major":
        outer, outer_cells, inner, inner_cells = "r", "rs", "c", "cs"
    else:
        outer, outer_cells, inner, inner_cells = "c", "cs", "r", "rs"
    condition = "(!= v 0)" if selected["pick"] == "last" else "(and (= a 0) (!= v 0))"
    return f"""(rule! (lambda (g)
  (let* ((h (rows g)) (w (cols g)))
    (build-grid 3 3 (or oc)
      (let ((rs (if (= or 0) (list 0)
                    (if (= or 2) (list (- h 1)) (range 1 (- h 1)))))
            (cs (if (= oc 0) (list 0)
                    (if (= oc 2) (list (- w 1)) (range 1 (- w 1))))))
        (reduce (lambda (acc {outer})
                  (reduce (lambda (a {inner})
                            (let ((v (at g r c))) (if {condition} v a)))
                          acc {inner_cells}))
                0 {outer_cells}))))))"""


_OCCUPANCY_PROGRAM = """(rule! (lambda (g)
  (let* ((h (rows g)) (w (cols g))
         (color (reduce (lambda (acc r)
                          (reduce (lambda (a c)
                                    (let ((v (at g r c)))
                                      (if (and (= a 0) (!= v 0)) v a)))
                                  acc (range 0 w)))
                        0 (range 0 h))))
    (build-grid 3 3 (or oc)
      (let ((rs (if (= or 0) (list 0)
                    (if (= or 2) (list (- h 1)) (range 1 (- h 1)))))
            (cs (if (= oc 0) (list 0)
                    (if (= oc 2) (list (- w 1)) (range 1 (- w 1))))))
        (reduce (lambda (acc r)
                  (reduce (lambda (a c) (if (!= (at g r c) 0) color a))
                          acc cs))
                0 rs))))))"""


class RacketOracle:
    """One protected included bridge, reused for a bounded batch."""

    def __init__(self):
        self.bridge = RacketBridge(timeout=5.0, startup_timeout=30.0)
        try:
            self.runtime_identity = self.bridge.runtime_identity
            if self.runtime_identity.get("protected") is not True:
                raise RuntimeError("the prototype requires protected Racket")
            self.functions = {}
            for index, settings in enumerate(all_settings()):
                name = f"__zone_parametric_{index}"
                self.bridge.eval_text(f"(define {name} {wrap_rule(program(settings))})")
                self.functions[(settings["scan_order"], settings["pick"])] = name
            self.bridge.eval_text(
                f"(define __zone_occupancy {wrap_rule(_OCCUPANCY_PROGRAM)})"
            )
        except BaseException:
            self.bridge.shutdown()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.bridge.shutdown()

    def _apply(self, grid, name):
        validate_input(grid)
        self.bridge.define_grid("__zone_input", grid)
        output = self.bridge.eval_text(f"({name} __zone_input)")
        _grid(output, heights=(3, 3), widths=(3, 3), name="Racket output")
        return output

    def label(self, grid, settings=None):
        selected = _settings(settings)
        return self._apply(grid, self.functions[(selected["scan_order"], selected["pick"])])

    def occupancy_label(self, grid):
        return self._apply(grid, "__zone_occupancy")


def _runner(oracle):
    return nullcontext(oracle) if oracle is not None else RacketOracle()


def infer_from_demonstrations(demos, *, oracle=None):
    """Fit the finite rival set to demos only. This API accepts no query data."""
    if type(demos) is not list or not 1 <= len(demos) <= 8:
        raise ValueError("demonstrations must be a list of 1..8 labeled pairs")
    for pair in demos:
        if type(pair) is not dict or "input" not in pair or "output" not in pair:
            raise ValueError("demonstrations require input and output")
        validate_input(pair["input"])
        _grid(pair["output"], heights=(3, 3), widths=(3, 3), name="demo output")
    survivors, rejected = [], {}
    with _runner(oracle) as active:
        for settings in all_settings():
            predictions = [active.label(pair["input"], settings) for pair in demos]
            mismatch = [i for i, (pred, pair) in enumerate(zip(predictions, demos))
                        if pred != pair["output"]]
            if mismatch:
                rejected[f"{settings['scan_order']}/{settings['pick']}"] = mismatch
            else:
                survivors.append(settings)
        occupancy = [active.occupancy_label(pair["input"]) for pair in demos]
    return {
        "evidence_source": "demonstrations_only",
        "demo_count": len(demos),
        "survivors": survivors,
        "rejected_on_demo_indices": rejected,
        "global_occupancy_survives": all(
            pred == pair["output"] for pred, pair in zip(occupancy, demos)
        ),
        "scope": "four declared settings and occupied-zone/global-first-color rival",
    }


def require_identifiable(demos, settings=None, *, oracle=None):
    selected = _settings(settings)
    certificate = infer_from_demonstrations(demos, oracle=oracle)
    if selected not in certificate["survivors"]:
        raise ValueError("demonstration output does not match the selected Racket rule")
    if certificate["survivors"] != [selected] or certificate["global_occupancy_survives"]:
        raise ValueError("underidentified demonstrations: a declared rival survives")
    return certificate


def _sample_input(rng):
    height, width = rng.randint(5, 14), rng.randint(7, 16)
    grid = [[0] * width for _ in range(height)]
    colors = rng.sample(range(1, 10), 5)
    points = ((1, width // 2), (height // 2, 1),
              (height // 2, width - 2), (height - 2, width // 2))
    for (r, c), color in zip(points, colors):
        grid[r][c] = color
    boundary = [0, 1, 2, 3, 5, 6, 7, 8]
    occupied = rng.sample(boundary, rng.randint(3, 7))
    if not set(occupied).intersection((0, 1, 2)):
        occupied[0] = rng.choice((0, 1, 2))
    zones = _zones(height, width)
    for index in sorted(occupied):
        cells = zones[index]
        for r, c in rng.sample(cells, rng.randint(1, min(3, len(cells)))):
            # The distinct top-boundary color refutes global-first occupancy.
            grid[r][c] = colors[4] if index in (0, 1, 2) else rng.choice(colors)
    validate_input(grid)
    return grid


def _source_hashes():
    paths = [Path(__file__), Path(__file__).with_name("README.md")]
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths if path.is_file()}


def generate_episode(seed=0, *, settings=None, input_seed=None, demos=2, queries=4, oracle=None):
    """Generate a fixed-rule episode; omitted settings select the canonical default."""
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 1, 8)
    _integer("queries", queries, 1, 8)
    selected = _settings(settings)
    input_seed = seed if input_seed is None else _integer("input_seed", input_seed, 0, 2**63 - 1)
    rng = random.Random(input_seed)
    inputs, seen = [], set()
    for _ in range(demos + queries):
        for attempt in range(128):
            grid = _sample_input(rng)
            key = tuple(tuple(row) for row in grid)
            if key not in seen:
                seen.add(key)
                inputs.append(grid)
                break
        else:
            raise ValueError("could not sample enough distinct inputs within 128 attempts")
    with _runner(oracle) as active:
        train = [{"input": grid, "output": active.label(grid, selected)} for grid in inputs[:demos]]
        # Certify the lesson before executing or consulting any query answer.
        certificate = require_identifiable(train, selected, oracle=active)
        test = [{"input": grid, "output": active.label(grid, selected)} for grid in inputs[demos:]]
        runtime_identity = dict(active.runtime_identity)
    source = program(selected)
    return {
        "train": train, "test": test,
        "_private": {
            "schema": "zone-parametric-prototype-v1", "status": "prototype",
            "task_id": TASK_ID, "settings": selected, "seed": seed, "input_seed": input_seed,
            "program_solution": source, "program_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "source_sha256": _source_hashes(), "demonstration_certificate": certificate,
            "runtime_identity": runtime_identity,
        },
    }


def _validated_episode(episode, active):
    if type(episode) is not dict or type(episode.get("_private")) is not dict:
        raise ValueError("an episode requires private provenance")
    private = episode["_private"]
    if type(private.get("settings")) is not dict:
        raise ValueError("an episode requires explicit private settings")
    settings = _settings(private["settings"])
    _integer("private seed", private.get("seed"), 0, 2**63 - 1)
    _integer("private input_seed", private.get("input_seed"), 0, 2**63 - 1)
    source = program(settings)
    if private.get("program_solution") != source:
        raise ValueError("private program does not match the declared setting")
    if private.get("program_sha256") != hashlib.sha256(source.encode()).hexdigest():
        raise ValueError("private program SHA-256 does not match its exact source")
    # This check intentionally precedes all query label validation.
    certificate = require_identifiable(episode.get("train"), settings, oracle=active)
    tests = episode.get("test")
    if type(tests) is not list or not 1 <= len(tests) <= 8:
        raise ValueError("queries must be a list of 1..8 pairs")
    keys = set()
    for pair in episode["train"] + tests:
        if type(pair) is not dict or "input" not in pair:
            raise ValueError("pairs require input grids")
        validate_input(pair["input"])
        key = tuple(tuple(row) for row in pair["input"])
        if key in keys:
            raise ValueError("all demonstration and query inputs must be distinct")
        keys.add(key)
    for index, pair in enumerate(tests):
        actual = active.label(pair["input"], settings)
        if pair.get("output") != actual:
            raise ValueError(f"query {index} label does not match Racket")
        _grid(pair["output"], heights=(3, 3), widths=(3, 3), name="query output")
    # Snapshot and refresh execution evidence; supplied certificates are not trusted.
    checked = json.loads(json.dumps(episode))
    checked["_private"]["demonstration_certificate"] = certificate
    checked["_private"]["runtime_identity"] = dict(active.runtime_identity)
    checked["_private"]["source_sha256"] = _source_hashes()
    return checked


def write_export(episodes, out, *, oracle=None, command=None):
    """Replay labels, then write opaque public files and separate private evidence."""
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"output directory already exists: {out}")
    if type(episodes) is not list or not episodes:
        raise ValueError("export requires a nonempty list of episodes")
    ids = [public_challenge_id(episode) for episode in episodes]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate visible payload in export batch")
    with _runner(oracle) as active:
        checked = [(public_id, _validated_episode(episode, active))
                   for public_id, episode in zip(ids, episodes)]
    checked.sort(key=lambda item: item[0])
    manifest = {
        "schema": "zone-parametric-export-v1", "status": "prototype", "task_id": TASK_ID,
        "parameters": PARAMETERS, "default": DEFAULT_SETTINGS,
        "source_sha256": _source_hashes(), "command": command,
        "episodes": [], "programs": {}, "limitations": LIMITATIONS,
    }
    # All validation and duplicate detection finish before creating the destination.
    (out / "public").mkdir(parents=True)
    (out / "private/episodes").mkdir(parents=True)
    (out / "private/rules").mkdir()
    for public_id, episode in checked:
        visible = public_challenge_bytes(episode)
        (out / "public" / f"{public_id}.json").write_bytes(visible)
        (out / "private/episodes" / f"{public_id}.json").write_text(
            json.dumps(episode, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        private = episode["_private"]
        digest = private["program_sha256"]
        (out / "private/rules" / f"{digest}.rkt").write_text(
            private["program_solution"], encoding="utf-8"
        )
        manifest["programs"][digest] = private["settings"]
        manifest["episodes"].append({
            "public_id": public_id, "settings": private["settings"],
            "seed": private["seed"], "input_seed": private["input_seed"],
            "program_sha256": digest, "demos": len(episode["train"]), "queries": len(episode["test"]),
        })
    (out / "public/index.json").write_text(
        json.dumps([public_id for public_id, _ in checked], indent=2) + "\n", encoding="utf-8"
    )
    (out / "private/manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "status": "prototype", "episodes": len(checked),
        "demonstrations": sum(len(e["train"]) for _, e in checked),
        "queries": sum(len(e["test"]) for _, e in checked),
        "public_ids": [public_id for public_id, _ in checked],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--input-seed", type=int)
    parser.add_argument("--demos", type=int, default=2)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--scan-order", choices=PARAMETERS["scan_order"], default="row_major")
    parser.add_argument("--pick", choices=PARAMETERS["pick"], default="last")
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    chosen = all_settings() if args.all_settings else [{"scan_order": args.scan_order, "pick": args.pick}]
    with RacketOracle() as oracle:
        episodes = [
            generate_episode(args.seed, settings=settings, input_seed=args.input_seed,
                             demos=args.demos, queries=args.queries, oracle=oracle)
            for settings in chosen
        ]
        summary = write_export(episodes, args.out, oracle=oracle, command=list(sys.argv))
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
